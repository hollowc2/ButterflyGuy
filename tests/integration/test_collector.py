"""Integration tests for the option chain collector (requires live Schwab token)."""

import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import AppConfig, CollectorSettings, StrategySettings
from butterfly_guy.data.collector import OptionChainCollector


SAMPLE_CHAIN_RESPONSE = {
    "callExpDateMap": {
        "2026-03-10:0": {
            "5500.0": [
                {
                    "symbol": "SPXW  260310C05500000",
                    "bid": 1.50,
                    "ask": 1.70,
                    "mark": 1.60,
                    "last": 1.55,
                    "totalVolume": 1200,
                    "openInterest": 500,
                    "volatility": 0.18,
                    "delta": 0.50,
                    "gamma": 0.01,
                    "theta": -2.5,
                    "vega": 0.05,
                }
            ]
        }
    },
    "putExpDateMap": {
        "2026-03-10:0": {
            "5500.0": [
                {
                    "symbol": "SPXW  260310P05500000",
                    "bid": 1.40,
                    "ask": 1.60,
                    "mark": 1.50,
                    "last": 1.45,
                    "totalVolume": 800,
                    "openInterest": 300,
                    "volatility": 0.20,
                    "delta": -0.50,
                    "gamma": 0.01,
                    "theta": -2.4,
                    "vega": 0.05,
                }
            ]
        }
    },
}


@pytest.mark.asyncio
async def test_collect_snapshot_parses_chain():
    """Collector should parse chain response into rows."""
    config = AppConfig()
    schwab = MagicMock()
    schwab.get_spot_price = AsyncMock(return_value=5500.0)
    schwab.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN_RESPONSE)

    chain_queries = MagicMock()
    chain_queries.bulk_insert_snapshot = AsyncMock(return_value=2)
    spot_queries = MagicMock()
    spot_queries.insert = AsyncMock()

    collector = OptionChainCollector(
        config=config,
        schwab=schwab,
        chain_queries=chain_queries,
        spot_queries=spot_queries,
    )

    with patch(
        "butterfly_guy.data.collector.get_0dte_expiration",
        return_value=dt.date(2026, 3, 10),
    ):
        count = await collector.collect_snapshot()

    assert count == 2
    chain_queries.bulk_insert_snapshot.assert_called_once()
    rows = chain_queries.bulk_insert_snapshot.call_args[0][0]
    assert len(rows) == 2  # 1 call + 1 put


@pytest.mark.asyncio
async def test_collect_snapshot_row_fields():
    """Parsed rows should have the expected fields."""
    config = AppConfig()
    schwab = MagicMock()
    schwab.get_spot_price = AsyncMock(return_value=5501.0)
    schwab.get_option_chain = AsyncMock(return_value=SAMPLE_CHAIN_RESPONSE)

    inserted_rows = []

    async def capture(rows):
        inserted_rows.extend(rows)
        return len(rows)

    chain_queries = MagicMock()
    chain_queries.bulk_insert_snapshot = capture
    spot_queries = MagicMock()
    spot_queries.insert = AsyncMock()

    collector = OptionChainCollector(
        config=config, schwab=schwab,
        chain_queries=chain_queries, spot_queries=spot_queries,
    )

    with patch(
        "butterfly_guy.data.collector.get_0dte_expiration",
        return_value=dt.date(2026, 3, 10),
    ):
        await collector.collect_snapshot()

    assert len(inserted_rows) == 2
    call_row = next(r for r in inserted_rows if r["option_type"] == "CALL")
    assert call_row["strike"] == 5500.0
    assert call_row["bid"] == 1.50
    assert call_row["spot_price"] == 5501.0
    assert call_row["symbol"] == "SPXW  260310C05500000"
