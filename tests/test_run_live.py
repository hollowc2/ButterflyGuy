from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from butterfly_guy.scripts.run_live import (
    _assert_broker_state_matches_db,
    _broker_option_position_symbols,
    _order_symbols,
)


def test_broker_option_position_symbols_filters_same_underlying_options():
    snapshot = {
        "securitiesAccount": {
            "positions": [
                {
                    "longQuantity": 1,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625C06000000",
                    },
                },
                {
                    "longQuantity": 1,
                    "instrument": {"assetType": "EQUITY", "symbol": "SPY"},
                },
                {
                    "longQuantity": 0,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625P05900000",
                    },
                },
            ]
        }
    }

    assert _broker_option_position_symbols(snapshot, "SPX") == {
        "SPXW  260625C06000000"
    }


def test_order_symbols_walks_child_orders():
    order = {
        "orderLegCollection": [
            {"instrument": {"symbol": "SPXW  260625C06000000"}}
        ],
        "childOrderStrategies": [
            {
                "orderLegCollection": [
                    {"instrument": {"symbol": "SPXW  260625C06100000"}}
                ]
            }
        ],
    }

    assert _order_symbols(order) == {
        "SPXW  260625C06000000",
        "SPXW  260625C06100000",
    }


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_broker_position_without_open_trade():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {
        "securitiesAccount": {
            "positions": [
                {
                    "longQuantity": 1,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625C06000000",
                    },
                }
            ]
        }
    }
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="DB has no OPEN trade"):
        await _assert_broker_state_matches_db(schwab, "SPX", [])


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_open_trade_when_broker_flat():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="broker is flat"):
        await _assert_broker_state_matches_db(
            schwab,
            "SPX",
            [{"lower_symbol": "SPXW  260625C06000000"}],
        )
