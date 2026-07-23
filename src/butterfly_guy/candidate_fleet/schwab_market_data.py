"""Schwab market-data client deliberately lacking every account/order operation."""

from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any, Awaitable, Callable

import httpx

from butterfly_guy.core.config import SchwabSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import schwab_api_calls, schwab_api_errors

log = get_logger(__name__)


class ReadOnlySchwabMarketDataClient:
    """Authenticate a Schwab client without resolving or retaining an account."""

    def __init__(self, settings: SchwabSettings) -> None:
        self._settings = settings
        self._client: Any = None

    async def initialize(self) -> None:
        from schwab.auth import client_from_token_file

        self._client = client_from_token_file(
            token_path=self._settings.token_path,
            api_key=self._settings.api_key,
            app_secret=self._settings.secret_key,
            asyncio=True,
            enforce_enums=False,
        )
        log.info("candidate_market_data_client_initialized")

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
        client = self._client
        self._client = None
        session = getattr(client, "session", None)
        close = getattr(session, "aclose", None)
        if close is not None:
            await close()

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
