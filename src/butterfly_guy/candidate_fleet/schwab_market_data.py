"""Schwab market-data client deliberately lacking every account/order operation."""

from __future__ import annotations

import asyncio
import datetime as dt
import inspect
from typing import Any, Awaitable, Callable

import httpx

from butterfly_guy.core.config import SchwabSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import schwab_api_calls, schwab_api_errors

log = get_logger(__name__)

TOKEN_LOCK_TIMEOUT = 1.0
TOKEN_RELOAD_VALIDATION_SYMBOL = "$SPX"


class ReadOnlySchwabMarketDataClient:
    """Authenticate a Schwab client without resolving or retaining an account."""

    def __init__(self, settings: SchwabSettings) -> None:
        self._settings = settings
        self._client: Any = None
        self._token_store: Any = None
        self._creation_timestamp: Any = None
        self._retired_client: Any = None

    async def initialize(self) -> None:
        from butterfly_guy.schwab_gateway.token_manager import AtomicFileTokenStore

        self._token_store = AtomicFileTokenStore(self._settings.token_path)
        self._client, self._creation_timestamp = self._build_client()
        log.info("candidate_market_data_client_initialized")

    def _build_client(self) -> tuple[Any, Any]:
        """Build one client with an isolated in-memory refresh-token callback."""
        from schwab.auth import client_from_access_functions

        document = self._read_token_document()
        token_state = {"document": document}

        def read_token() -> object:
            return token_state["document"]

        def retain_token(token: object, *_args: Any, **_kwargs: Any) -> None:
            # The feed is intentionally not a persistent writer. Each live/retired
            # client gets a separate closure so an in-flight refresh on the old client
            # cannot overwrite the new client's in-memory document after a hot swap.
            token_state["document"] = token

        client = client_from_access_functions(
            api_key=self._settings.api_key,
            app_secret=self._settings.secret_key,
            token_read_func=read_token,
            token_write_func=retain_token,
            asyncio=True,
            enforce_enums=False,
        )
        creation = document.get("creation_timestamp") if isinstance(document, dict) else None
        return client, creation

    def _read_token_document(self) -> object:
        if self._token_store is None:
            raise RuntimeError("market-data token store is not initialized")
        with self._token_store.read_locked(TOKEN_LOCK_TIMEOUT) as transaction:
            return transaction.read()

    def _read_creation_timestamp(self) -> Any:
        document = self._read_token_document()
        if isinstance(document, dict):
            return document.get("creation_timestamp")
        return None

    async def reload_if_reauthorized(self) -> bool:
        """Validate and install a client built from a newly authorized token document."""
        creation = self._read_creation_timestamp()
        if creation is None or creation == self._creation_timestamp:
            return False
        if self._creation_timestamp is None:
            self._creation_timestamp = creation
            return False

        candidate, candidate_creation = self._build_client()
        try:
            await self._validate_reload_candidate(candidate)
        except Exception:
            try:
                await self._close_client(candidate)
            except Exception as exc:
                log.warning(
                    "candidate_reload_session_close_failed",
                    reason=type(exc).__name__,
                )
            raise

        await self._close_retired_client()
        self._retired_client = self._client
        self._client = candidate
        self._creation_timestamp = candidate_creation
        log.info("candidate_market_data_token_reloaded")
        return True

    async def _validate_reload_candidate(self, candidate: Any) -> None:
        """Prove the replacement credential with one bounded read-only Schwab call."""
        endpoint = "candidate_token_reload_validation"
        schwab_api_calls.labels(endpoint=endpoint).inc()
        try:
            response = await candidate.get_quote(TOKEN_RELOAD_VALIDATION_SYMBOL)
        except Exception:
            schwab_api_errors.labels(endpoint=endpoint).inc()
            raise RuntimeError("candidate token reload validation request failed") from None
        status = getattr(response, "status_code", None)
        if status != httpx.codes.OK:
            schwab_api_errors.labels(endpoint=endpoint).inc()
            raise RuntimeError(
                f"candidate token reload validation returned status {status}"
            )

    async def _close_client(self, client: Any) -> None:
        close = getattr(client, "close_async_session", None)
        if close is None:
            close = getattr(getattr(client, "session", None), "aclose", None)
        if close is None:
            return
        result = close()
        if inspect.isawaitable(result):
            await result

    async def _close_retired_client(self) -> None:
        if self._retired_client is None:
            return
        retired, self._retired_client = self._retired_client, None
        try:
            await self._close_client(retired)
        except Exception as exc:
            log.warning(
                "candidate_retired_session_close_failed",
                reason=type(exc).__name__,
            )

    @property
    def client(self) -> Any:
        if self._client is None:
            raise RuntimeError("market-data client is not initialized")
        return self._client

    async def option_chain(self, expiration: dt.date) -> dict[str, Any]:
        response = await self._retry(
            self.client.get_option_chain,
            "$SPX",
            from_date=expiration,
            to_date=expiration,
            endpoint="candidate_option_chain",
        )
        return response.json()

    async def quote(self, symbol: str) -> float:
        response = await self._retry(
            self.client.get_quote,
            symbol,
            endpoint=f"candidate_quote_{symbol.lstrip('$').lower()}",
        )
        payload = response.json()
        quote = payload.get(symbol, payload.get(symbol.lstrip("$"), {}))
        quote = quote.get("quote", quote)
        price = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
        if not price:
            raise ValueError(f"missing quote price for {symbol}")
        return float(price)

    async def intraday_bars(self, day: dt.date) -> list[dict[str, Any]]:
        response = await self._retry(
            self.client.get_price_history,
            "$SPX",
            period_type=self.client.PriceHistory.PeriodType.DAY,
            period=1,
            frequency_type=self.client.PriceHistory.FrequencyType.MINUTE,
            frequency=self.client.PriceHistory.Frequency.EVERY_MINUTE,
            start_datetime=dt.datetime.combine(day, dt.time.min),
            end_datetime=dt.datetime.combine(day, dt.time.max),
            endpoint="candidate_spx_intraday",
        )
        return list(response.json().get("candles", []))

    async def daily_bars(self) -> list[dict[str, Any]]:
        response = await self._retry(
            self.client.get_price_history,
            "$SPX",
            period_type=self.client.PriceHistory.PeriodType.MONTH,
            period=1,
            frequency_type=self.client.PriceHistory.FrequencyType.DAILY,
            endpoint="candidate_spx_daily",
        )
        return list(response.json().get("candles", []))

    async def close(self) -> None:
        await self._close_retired_client()
        client, self._client = self._client, None
        if client is not None:
            await self._close_client(client)

    async def _retry(
        self,
        operation: Callable[..., Awaitable[Any]],
        *args: object,
        endpoint: str,
        **kwargs: object,
    ) -> Any:
        last_error: Exception | None = None
        for attempt, delay in enumerate((1, 2, 4)):
            try:
                schwab_api_calls.labels(endpoint=endpoint).inc()
                response = await operation(*args, **kwargs)
                if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                    schwab_api_errors.labels(endpoint=endpoint).inc()
                    log.warning("candidate_feed_schwab_429", endpoint=endpoint)
                else:
                    response.raise_for_status()
                    return response
            except Exception as exc:
                schwab_api_errors.labels(endpoint=endpoint).inc()
                last_error = exc
            if attempt < 2:
                await asyncio.sleep(delay)
        raise RuntimeError(f"{endpoint} failed after retries: {last_error}")
