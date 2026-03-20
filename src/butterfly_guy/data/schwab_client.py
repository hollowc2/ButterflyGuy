"""Async Schwab API client wrapper with retry logic."""

from __future__ import annotations

import asyncio
import datetime as dt
from pathlib import Path
from typing import Any

import httpx

from butterfly_guy.core.config import SchwabSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import schwab_api_calls, schwab_api_errors

log = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]

# Maps strategy underlying → Schwab API symbol for spot price quotes
SCHWAB_SPOT_SYMBOLS: dict[str, str] = {"SPX": "$SPX", "NDX": "$NDX"}
# Maps strategy underlying → Schwab API symbol for options chain requests
SCHWAB_CHAIN_SYMBOLS: dict[str, str] = {"SPX": "$SPX", "NDX": "$NDX"}


class SchwabClientWrapper:
    """Async wrapper around schwab-py with retry and metrics."""

    def __init__(self, settings: SchwabSettings) -> None:
        self.settings = settings
        self._client: Any = None
        self._account_hash: str | None = None

    async def initialize(self) -> None:
        """Authenticate and resolve account hash."""
        from schwab.auth import client_from_token_file

        self._client = client_from_token_file(
            token_path=self.settings.token_path,
            api_key=self.settings.api_key,
            app_secret=self.settings.secret_key,
            asyncio=True,
            enforce_enums=False,
        )

        # Resolve account hash
        resp = await self._client.get_account_numbers()
        if resp.status_code != httpx.codes.OK:
            raise RuntimeError(f"Failed to get account numbers: {resp.status_code}")

        accounts = resp.json()
        target_id = self.settings.account_id
        for acct in accounts:
            if acct.get("accountNumber") == target_id:
                self._account_hash = acct["hashValue"]
                break

        if not self._account_hash and accounts:
            self._account_hash = accounts[0]["hashValue"]

        log.info(
            "schwab_client_initialized",
            account_hash=self._account_hash[:8] + "..." if self._account_hash else None,
        )

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
                if resp.status_code == httpx.codes.OK:
                    return resp
                if resp.status_code == 429:
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                    log.warning("rate_limited", endpoint=endpoint, wait=wait)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
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
        """Place an order and return the order ID."""
        resp = await self._retry(
            self.client.place_order, self.account_hash, order_spec, endpoint="place_order"
        )
        # Order ID is in the Location header
        location = resp.headers.get("Location", "")
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

    async def close(self) -> None:
        """Close the client session."""
        if self._client is not None:
            await self._client.close_async_session()
            self._client = None
            log.info("schwab_client_closed")
