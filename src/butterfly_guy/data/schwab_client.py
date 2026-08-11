"""Async Schwab API client wrapper with retry logic."""

from __future__ import annotations

import asyncio
import datetime as dt
import math
from collections.abc import Mapping
from typing import Any

import httpx

from butterfly_guy.core.config import SchwabSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import schwab_api_calls, schwab_api_errors
from butterfly_guy.core.time_utils import EASTERN, market_close_time, now_eastern, session_date

log = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]

# The gateway and the keepalive both write this same document under a shared lock.
# schwab-py's default file writer truncates in place and takes no lock, so a concurrent
# gateway os.replace could leave a torn document on disk. Persist through the same
# AtomicFileTokenStore instead. Kept short: this blocks the event loop while held.
TOKEN_LOCK_TIMEOUT = 10.0

# Maps strategy underlying → Schwab API symbol for spot price quotes
SCHWAB_SPOT_SYMBOLS: dict[str, str] = {"SPX": "$SPX", "NDX": "$NDX", "XSP": "$XSP"}
# Maps strategy underlying → Schwab API symbol for options chain requests
SCHWAB_CHAIN_SYMBOLS: dict[str, str] = {"SPX": "$SPX", "NDX": "$NDX", "XSP": "$XSP"}


def _creation_timestamp(document: object) -> float | None:
    if not isinstance(document, Mapping):
        return None
    value = document.get("creation_timestamp")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    timestamp = float(value)
    return timestamp if math.isfinite(timestamp) and timestamp > 0 else None


class SchwabClientWrapper:
    """Async wrapper around schwab-py with retry and metrics."""

    def __init__(self, settings: SchwabSettings) -> None:
        self.settings = settings
        self._client: Any = None
        self._account_hash: str | None = None
        self._token_store: Any = None
        self._creation_timestamp: Any = None
        # The client displaced by the most recent reload. Held rather than closed so
        # that requests still in flight against it can finish; see reload_if_reauthorized.
        self._retired_client: Any = None

    def _read_token(self) -> object:
        with self._token_store.locked(TOKEN_LOCK_TIMEOUT) as transaction:
            return transaction.read()

    def _write_token(self, token: Any, *_args: Any, **_kwargs: Any) -> None:
        from schwab_token_store import TokenManagerError

        try:
            with self._token_store.locked(TOKEN_LOCK_TIMEOUT) as transaction:
                current_creation = _creation_timestamp(transaction.read())
                incoming_creation = _creation_timestamp(token)
                if (
                    current_creation is not None
                    and incoming_creation is not None
                    and incoming_creation < current_creation
                ):
                    # A client built before a manual re-authorization can finish an
                    # access-token refresh before the five-minute reload notices the
                    # new document. The lock prevents a torn write, but only this
                    # monotonic marker check prevents that old client from atomically
                    # restoring its obsolete refresh-token lineage.
                    log.warning("schwab_token_stale_persist_rejected")
                    return
                transaction.write(token)
        except TokenManagerError:
            # The refreshed access token is already live in memory and the keepalive
            # rewrites this document hourly, so a failed persist is recoverable. Losing
            # the trading loop to a transient lock conflict would not be.
            log.error("schwab_token_persist_failed")

    def _build_client(self) -> Any:
        from schwab.auth import client_from_access_functions

        return client_from_access_functions(
            api_key=self.settings.api_key,
            app_secret=self.settings.secret_key,
            token_read_func=self._read_token,
            token_write_func=self._write_token,
            asyncio=True,
            enforce_enums=False,
        )

    def _read_creation_timestamp(self) -> Any:
        """Read the document's re-authorization marker.

        `creation_timestamp` changes only when the token is re-authorized: schwab-py
        preserves it across ordinary access-token refreshes, verified by watching a
        keepalive rewrite the document in place on 2026-08-09. It is also not a
        credential, so it can be compared and logged freely -- unlike the refresh
        token, which would work equally well as a marker but must never be read.
        """
        return _creation_timestamp(self._read_token())

    async def _resolve_account_hash(self, client: Any) -> str:
        resp = await client.get_account_numbers()
        if resp.status_code != httpx.codes.OK:
            raise RuntimeError(f"Failed to get account numbers: {resp.status_code}")

        accounts = resp.json()
        target_id = self.settings.account_id
        if not target_id:
            raise RuntimeError(
                "SCHWAB_ACCOUNT_ID must be configured; refusing to select a default account"
            )

        for acct in accounts:
            if acct.get("accountNumber") == target_id:
                return str(acct["hashValue"])

        raise RuntimeError("Configured SCHWAB_ACCOUNT_ID was not found in Schwab account list")

    async def initialize(self) -> None:
        """Authenticate and resolve account hash."""
        from schwab_token_store import AtomicFileTokenStore

        self._token_store = AtomicFileTokenStore(self.settings.token_path)
        self._client = self._build_client()
        # The reload marker is an optimisation, not a credential requirement: a client
        # that authenticates must start even if the marker cannot be read. An unknown
        # marker is adopted on the first reload check rather than forcing a rebuild.
        try:
            self._creation_timestamp = self._read_creation_timestamp()
        except Exception as exc:
            log.warning("schwab_token_marker_unreadable", error=str(exc))
            self._creation_timestamp = None
        self._account_hash = await self._resolve_account_hash(self._client)
        log.info("schwab_client_initialized")

    async def reload_if_reauthorized(self) -> bool:
        """Rebuild the client if the token document has been re-authorized.

        schwab-py reads the token exactly once, when the client is constructed
        (`client_from_access_functions` calls `token_read_func()` and hands the result
        to the session), and then holds it in memory for the process lifetime. It
        never re-reads the document. That single read is the only thing a container
        restart accomplishes, and it is why a re-authorization has required restarting
        every token consumer.

        The new client is proven against Schwab *before* it is installed, so a bad
        document leaves the process on its working client rather than silently
        breaking it. The displaced client is not closed here: call sites resolve
        `self.client.<method>` eagerly, so a request already in flight completes
        against the object it started on, and closing that session underneath it
        would abort it. It is closed at the next reload or at `close()`.
        """
        creation = self._read_creation_timestamp()
        if creation is None or creation == self._creation_timestamp:
            return False
        if self._creation_timestamp is None:
            # Marker unreadable at startup. Adopt it now rather than treating the first
            # successful read as a re-authorization and rebuilding a working client.
            self._creation_timestamp = creation
            return False

        candidate = self._build_client()
        try:
            account_hash = await self._resolve_account_hash(candidate)
        except Exception:
            try:
                await candidate.close_async_session()
            except Exception as exc:
                log.warning("schwab_candidate_session_close_failed", error=str(exc))
            raise

        await self._close_retired_client()
        self._retired_client = self._client
        self._client = candidate
        self._account_hash = account_hash
        self._creation_timestamp = creation
        log.info("schwab_token_reloaded")
        return True

    async def _close_retired_client(self) -> None:
        if self._retired_client is None:
            return
        retired, self._retired_client = self._retired_client, None
        try:
            await retired.close_async_session()
        except Exception as exc:  # a stale session is not worth failing a reload over
            log.warning("schwab_retired_session_close_failed", error=str(exc))

    @property
    def client(self) -> Any:
        if self._client is None:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        return self._client

    @property
    def account_hash(self) -> str:
        if self._account_hash is None:
            raise RuntimeError("Account hash not resolved. Call initialize() first.")
        return self._account_hash

    async def _retry(self, func, *args, endpoint: str = "unknown", **kwargs) -> Any:
        """Execute with exponential backoff retry."""
        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                schwab_api_calls.labels(endpoint=endpoint).inc()
                resp = await func(*args, **kwargs)
                if resp.status_code == 429:
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                    log.warning("rate_limited", endpoint=endpoint, wait=wait)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except Exception as e:
                schwab_api_errors.labels(endpoint=endpoint).inc()
                last_err = e
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF[attempt]
                    log.warning(
                        "api_retry", endpoint=endpoint, attempt=attempt + 1, error=str(e), wait=wait
                    )
                    await asyncio.sleep(wait)
        raise RuntimeError(f"API call failed after {MAX_RETRIES} retries: {last_err}")

    async def get_option_chain(self, symbol: str, expiration: dt.date) -> dict[str, Any]:
        """Fetch option chain for a specific symbol and expiration."""
        resp = await self._retry(
            self.client.get_option_chain,
            symbol,
            from_date=expiration,
            to_date=expiration,
            endpoint="get_option_chain",
        )
        return resp.json()

    async def get_spot_price(self, symbol: str = "$SPX") -> float:
        """Get current spot price for SPX."""
        resp = await self._retry(
            self.client.get_quote, symbol, endpoint="get_quote"
        )
        data = resp.json()
        # Schwab returns {symbol: {quote: {lastPrice: ...}}} or {symbol: {lastPrice: ...}}
        quote = data.get(symbol, data.get(symbol.lstrip("$"), {}))
        if "quote" in quote:
            quote = quote["quote"]
        price = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
        if not price:
            raise ValueError(f"Could not extract spot price from response for {symbol}")
        return float(price)

    async def place_order(self, order_spec: dict[str, Any]) -> str:
        """Place an order once and return the order ID.

        Order placement is not retried because Schwab may accept the first submit
        even if the response is lost.
        """
        endpoint = "place_order"
        schwab_api_calls.labels(endpoint=endpoint).inc()
        try:
            resp = await self.client.place_order(self.account_hash, order_spec)
            resp.raise_for_status()
        except Exception:
            schwab_api_errors.labels(endpoint=endpoint).inc()
            raise

        # Order ID is in the Location header
        location = resp.headers.get("Location", "")
        if not location:
            raise RuntimeError(
                "Order placement response missing Location; refusing to retry submit"
            )
        order_id = location.split("/")[-1] if location else ""
        log.info("order_placed", order_id=order_id)
        return order_id

    async def get_order_status(self, order_id: str) -> dict[str, Any]:
        """Get the status of an order."""
        resp = await self._retry(
            self.client.get_order,
            order_id,
            self.account_hash,
            endpoint="get_order",
        )
        return resp.json()

    async def cancel_order(self, order_id: str) -> None:
        """Cancel an existing order."""
        await self._retry(
            self.client.cancel_order,
            order_id,
            self.account_hash,
            endpoint="cancel_order",
        )
        log.info("order_cancelled", order_id=order_id)

    async def get_intraday_bars(
        self, symbol: str = "$SPX", days_back: int = 1
    ) -> list[dict]:
        """Fetch 1-minute bars for today (and optionally prior days) from Schwab."""
        import datetime as dt

        today = dt.date.today()
        start = today - dt.timedelta(days=days_back)
        resp = await self._retry(
            self.client.get_price_history,
            symbol,
            period_type=self.client.PriceHistory.PeriodType.DAY,
            period=days_back,
            frequency_type=self.client.PriceHistory.FrequencyType.MINUTE,
            frequency=self.client.PriceHistory.Frequency.EVERY_MINUTE,
            start_datetime=dt.datetime.combine(start, dt.time.min),
            end_datetime=dt.datetime.combine(today, dt.time.max),
            endpoint="get_price_history",
        )
        data = resp.json()
        return data.get("candles", [])

    async def get_intraday_bars_for_day(
        self,
        symbol: str,
        day: dt.date,
        *,
        include_extended_hours: bool = True,
    ) -> list[dict]:
        """Fetch 1-minute bars for one session."""
        start = dt.datetime.combine(day, dt.time(6, 0), tzinfo=EASTERN)
        close = dt.datetime.combine(day, market_close_time(day), tzinfo=EASTERN)
        now = now_eastern()
        end = min(now, close) if now.date() == day else close
        resp = await self._retry(
            self.client.get_price_history,
            symbol,
            period_type=self.client.PriceHistory.PeriodType.DAY,
            period=1,
            frequency_type=self.client.PriceHistory.FrequencyType.MINUTE,
            frequency=self.client.PriceHistory.Frequency.EVERY_MINUTE,
            start_datetime=start,
            end_datetime=end,
            need_extended_hours_data=include_extended_hours,
            endpoint="get_price_history",
        )
        data = resp.json()
        return data.get("candles", [])

    async def get_daily_bars(self, symbol: str, days_back: int = 10) -> list[dict]:
        """Fetch daily OHLCV bars for the given symbol."""
        resp = await self._retry(
            self.client.get_price_history,
            symbol,
            period_type=self.client.PriceHistory.PeriodType.MONTH,
            period=1,
            frequency_type=self.client.PriceHistory.FrequencyType.DAILY,
            endpoint="get_daily_bars",
        )
        data = resp.json()
        return data.get("candles", [])

    async def get_equity_quotes(
        self,
        symbols: list[str],
        *,
        batch_size: int = 150,
    ) -> dict[str, dict[str, Any]]:
        """Fetch regular + extended quote fields for equities in batches."""
        if not symbols:
            return {}

        fields = [
            self.client.Quote.Fields.QUOTE,
            self.client.Quote.Fields.EXTENDED,
        ]
        results: dict[str, dict[str, Any]] = {}
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            resp = await self._retry(
                self.client.get_quotes,
                batch,
                fields=fields,
                endpoint="get_equity_quotes",
            )
            payload = resp.json()
            if isinstance(payload, dict):
                results.update(payload)
        return results

    async def get_market_movers(
        self,
        index: str,
        *,
        sort_order: str = "PERCENT_CHANGE_UP",
        frequency: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return Schwab's top movers list for an index/exchange bucket."""
        from schwab.client import Client

        sort = getattr(Client.Movers.SortOrder, sort_order, sort_order)
        kwargs: dict[str, Any] = {"sort_order": sort}
        if frequency is not None:
            kwargs["frequency"] = frequency

        resp = await self._retry(
            self.client.get_movers,
            index,
            endpoint="get_market_movers",
            **kwargs,
        )
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("screeners", data.get("movers", []))

    async def get_orders_for_day(self, day: dt.date) -> list[dict[str, Any]]:
        """Fetch all orders entered on a given date from Schwab."""
        resp = await self._retry(
            self.client.get_orders_for_account,
            self.account_hash,
            from_entered_datetime=dt.datetime.combine(day, dt.time.min),
            to_entered_datetime=dt.datetime.combine(day, dt.time.max),
            endpoint="get_orders_for_day",
        )
        data = resp.json()
        return data if isinstance(data, list) else []

    async def get_todays_orders(self) -> list[dict[str, Any]]:
        """Fetch all orders entered on the current Eastern session date."""
        return await self.get_orders_for_day(session_date())

    async def get_transactions_for_day(
        self,
        day: dt.date,
        *,
        transaction_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch account transactions for a given date."""
        from schwab.client import Client

        kwargs: dict[str, Any] = {
            "start_date": dt.datetime.combine(day, dt.time.min),
            "end_date": dt.datetime.combine(day, dt.time.max),
        }
        if transaction_types:
            kwargs["transaction_types"] = [
                getattr(Client.Transactions.TransactionType, t, t)
                for t in transaction_types
            ]
        resp = await self._retry(
            self.client.get_transactions,
            self.account_hash,
            endpoint="get_transactions_for_day",
            **kwargs,
        )
        data = resp.json()
        return data if isinstance(data, list) else []

    async def get_account_snapshot(self) -> dict[str, Any]:
        """Fetch full account snapshot: balances, metadata, and positions."""
        resp = await self._retry(
            self.client.get_account,
            self.account_hash,
            fields=[self.client.Account.Fields.POSITIONS],
            endpoint="get_account_snapshot",
        )
        return resp.json()

    async def get_positions(self) -> dict:
        """Fetch account positions and buying power."""
        resp = await self._retry(
            self.client.get_account,
            self.account_hash,
            fields=[self.client.Account.Fields.POSITIONS],
            endpoint="get_account",
        )
        return resp.json()

    async def get_account_balances(self) -> dict[str, float]:
        """Fetch account balances including liquidation value and buying power."""
        resp = await self._retry(
            self.client.get_account,
            self.account_hash,
            endpoint="get_account_balances",
        )
        data = resp.json()
        balances = (
            data.get("securitiesAccount", {})
                .get("currentBalances", {})
        )
        return {
            "liquidation_value": float(balances.get("liquidationValue", 0.0)),
            "buying_power": float(balances.get("buyingPowerNonMarginableTrade", 0.0)),
            "available_funds": float(balances.get("availableFunds", 0.0)),
        }

    async def close(self) -> None:
        """Close the client session."""
        await self._close_retired_client()
        if self._client is not None:
            await self._client.close_async_session()
            self._client = None
            log.info("schwab_client_closed")
