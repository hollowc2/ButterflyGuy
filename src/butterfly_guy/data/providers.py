"""Narrow read-only provider boundaries for Schwab market data."""

from __future__ import annotations

import datetime as dt
from typing import Any, Protocol

from butterfly_guy.data.schwab_client import SchwabClientWrapper


class SpotPriceProvider(Protocol):
    async def get_spot_price(self, symbol: str = "$SPX") -> float: ...


class OptionChainProvider(Protocol):
    async def get_option_chain(
        self, symbol: str, expiration: dt.date
    ) -> dict[str, Any]: ...


class PriceHistoryProvider(Protocol):
    async def get_intraday_bars(
        self, symbol: str = "$SPX", days_back: int = 1
    ) -> list[dict]: ...

    async def get_intraday_bars_for_day(
        self,
        symbol: str,
        day: dt.date,
        *,
        include_extended_hours: bool = True,
    ) -> list[dict]: ...

    async def get_daily_bars(
        self, symbol: str, days_back: int = 10
    ) -> list[dict]: ...


class EquityQuoteProvider(Protocol):
    async def get_equity_quotes(
        self, symbols: list[str], *, batch_size: int = 150
    ) -> dict[str, dict[str, Any]]: ...


class MarketMoversProvider(Protocol):
    async def get_market_movers(
        self,
        index: str,
        *,
        sort_order: str = "PERCENT_CHANGE_UP",
        frequency: int | None = None,
    ) -> list[dict[str, Any]]: ...


class CollectorMarketDataProvider(
    SpotPriceProvider,
    OptionChainProvider,
    PriceHistoryProvider,
    Protocol,
):
    """The read-only surface required by ``OptionChainCollector``."""


class DirectSchwabMarketDataProvider:
    """Delegate to the current client without owning its lifecycle or changing data."""

    def __init__(self, client: SchwabClientWrapper) -> None:
        self._client = client

    async def get_spot_price(self, symbol: str = "$SPX") -> float:
        return await self._client.get_spot_price(symbol)

    async def get_option_chain(
        self, symbol: str, expiration: dt.date
    ) -> dict[str, Any]:
        return await self._client.get_option_chain(symbol, expiration)

    async def get_intraday_bars(
        self, symbol: str = "$SPX", days_back: int = 1
    ) -> list[dict]:
        return await self._client.get_intraday_bars(symbol, days_back)

    async def get_intraday_bars_for_day(
        self,
        symbol: str,
        day: dt.date,
        *,
        include_extended_hours: bool = True,
    ) -> list[dict]:
        return await self._client.get_intraday_bars_for_day(
            symbol,
            day,
            include_extended_hours=include_extended_hours,
        )

    async def get_daily_bars(
        self, symbol: str, days_back: int = 10
    ) -> list[dict]:
        return await self._client.get_daily_bars(symbol, days_back)

    async def get_equity_quotes(
        self, symbols: list[str], *, batch_size: int = 150
    ) -> dict[str, dict[str, Any]]:
        return await self._client.get_equity_quotes(symbols, batch_size=batch_size)

    async def get_market_movers(
        self,
        index: str,
        *,
        sort_order: str = "PERCENT_CHANGE_UP",
        frequency: int | None = None,
    ) -> list[dict[str, Any]]:
        return await self._client.get_market_movers(
            index,
            sort_order=sort_order,
            frequency=frequency,
        )
