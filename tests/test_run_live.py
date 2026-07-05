from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from butterfly_guy.core.config import (
    AppConfig,
    ExecutionSettings,
    RiskSettings,
    SchwabSettings,
    StrategySettings,
)
from butterfly_guy.scripts.run_live import (
    _assert_broker_state_matches_db,
    _assert_live_config_supported,
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


def test_live_config_rejects_non_spx_live_money(monkeypatch):
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "123")
    monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20000")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "500")
    config = AppConfig(
        schwab=SchwabSettings(account_id="123"),
        strategy=StrategySettings(underlying="NDX"),
        execution=ExecutionSettings(paper_trading=False, allow_live_trading=True),
    )

    with pytest.raises(RuntimeError, match="SPX-only"):
        _assert_live_config_supported(config)


def test_live_config_rejects_spx_live_without_account_confirmation(monkeypatch):
    monkeypatch.delenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("LIVE_ACCOUNT_ALLOCATION", raising=False)
    monkeypatch.delenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", raising=False)
    config = AppConfig(
        schwab=SchwabSettings(account_id="123"),
        strategy=StrategySettings(underlying="SPX"),
        execution=ExecutionSettings(paper_trading=False, allow_live_trading=True),
    )

    with pytest.raises(RuntimeError, match="LIVE_EXPECTED_SCHWAB_ACCOUNT_ID"):
        _assert_live_config_supported(config)


def test_live_config_allows_spx_live_when_explicitly_confirmed(monkeypatch):
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "123")
    monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20000")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "500")
    config = AppConfig(
        schwab=SchwabSettings(account_id="123"),
        strategy=StrategySettings(underlying="SPX"),
        execution=ExecutionSettings(paper_trading=False, allow_live_trading=True),
        risk=RiskSettings(max_daily_loss=500.0),
    )

    _assert_live_config_supported(config)
