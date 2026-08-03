from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock

import pytest

from butterfly_guy.data.providers import DirectSchwabMarketDataProvider


@pytest.mark.asyncio
async def test_direct_provider_delegates_without_transforming_results() -> None:
    expiration = dt.date(2026, 8, 3)
    day = dt.date(2026, 7, 31)
    client = AsyncMock()
    client.get_spot_price.return_value = 6301.25
    client.get_option_chain.return_value = {"callExpDateMap": {}}
    client.get_intraday_bars.return_value = [{"datetime": 1}]
    client.get_intraday_bars_for_day.return_value = [{"datetime": 2}]
    client.get_daily_bars.return_value = [{"datetime": 3}]
    client.get_equity_quotes.return_value = {"AAPL": {"quote": {}}}
    client.get_market_movers.return_value = [{"symbol": "AAPL"}]
    provider = DirectSchwabMarketDataProvider(client)

    assert await provider.get_spot_price("$SPX") == 6301.25
    assert await provider.get_option_chain("$SPX", expiration) == {
        "callExpDateMap": {}
    }
    assert await provider.get_intraday_bars("$SPX", 2) == [{"datetime": 1}]
    assert await provider.get_intraday_bars_for_day(
        "AAPL", day, include_extended_hours=False
    ) == [{"datetime": 2}]
    assert await provider.get_daily_bars("$VIX", 20) == [{"datetime": 3}]
    assert await provider.get_equity_quotes(["AAPL"], batch_size=25) == {
        "AAPL": {"quote": {}}
    }
    assert await provider.get_market_movers(
        "$SPX", sort_order="PERCENT_CHANGE_DOWN", frequency=5
    ) == [{"symbol": "AAPL"}]

    client.get_spot_price.assert_awaited_once_with("$SPX")
    client.get_option_chain.assert_awaited_once_with("$SPX", expiration)
    client.get_intraday_bars.assert_awaited_once_with("$SPX", 2)
    client.get_intraday_bars_for_day.assert_awaited_once_with(
        "AAPL", day, include_extended_hours=False
    )
    client.get_daily_bars.assert_awaited_once_with("$VIX", 20)
    client.get_equity_quotes.assert_awaited_once_with(["AAPL"], batch_size=25)
    client.get_market_movers.assert_awaited_once_with(
        "$SPX", sort_order="PERCENT_CHANGE_DOWN", frequency=5
    )
