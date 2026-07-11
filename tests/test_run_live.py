from __future__ import annotations

import asyncio
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
    BrokerStateGate,
    _assert_broker_state_matches_db,
    _assert_live_config_supported,
    _broker_option_positions,
    _order_symbols,
    broker_reconciler_loop,
)

LOWER = "SPXW  260625C06000000"
CENTER = "SPXW  260625C06050000"
UPPER = "SPXW  260625C06100000"
OPEN_TRADE = {
    "lower_symbol": LOWER,
    "center_symbol": CENTER,
    "upper_symbol": UPPER,
    "quantity": 1,
}


def _synthetic_position(symbol, *, long=0, short=0):
    return {
        "longQuantity": long,
        "shortQuantity": short,
        "instrument": {"assetType": "OPTION", "symbol": symbol},
    }


def _synthetic_butterfly_snapshot(
    *, quantity=1, center_long=0, center_short=None, extra=()
):
    center_short = 2 * quantity if center_short is None else center_short
    return {
        "securitiesAccount": {
            "positions": [
                _synthetic_position(LOWER, long=quantity),
                _synthetic_position(CENTER, long=center_long, short=center_short),
                _synthetic_position(UPPER, long=quantity),
                *extra,
            ]
        }
    }


def test_broker_option_positions_keep_signed_quantity_for_matching_options():
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
                    "shortQuantity": 2,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625P05900000",
                    },
                },
            ]
        }
    }

    assert _broker_option_positions(snapshot, "SPX") == {
        "SPXW  260625C06000000": 1,
        "SPXW  260625P05900000": -2,
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
            [OPEN_TRADE],
        )


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_incomplete_db_butterfly():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {
        "securitiesAccount": {
            "positions": [
                _synthetic_position(LOWER, long=1),
                _synthetic_position(UPPER, long=1),
            ]
        }
    }
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="missing leg symbol"):
        await _assert_broker_state_matches_db(
            schwab,
            "SPX",
            [{"lower_symbol": LOWER, "upper_symbol": UPPER, "quantity": 1}],
        )


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_zero_quantity_db_butterfly():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot()
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="invalid leg symbols or quantity"):
        await _assert_broker_state_matches_db(
            schwab,
            "SPX",
            [{**OPEN_TRADE, "quantity": 0}],
        )


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_extra_broker_leg():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot(
        extra=(_synthetic_position("SPXW  260625C06150000", long=1),)
    )
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="unexpected broker leg symbol"):
        await _assert_broker_state_matches_db(schwab, "SPX", [OPEN_TRADE])


@pytest.mark.asyncio
async def test_startup_reconciliation_allows_exact_signed_butterfly_ratio():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot(quantity=2)
    schwab.get_todays_orders.return_value = []

    await _assert_broker_state_matches_db(
        schwab, "SPX", [{**OPEN_TRADE, "quantity": 2}]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("long_quantity", "short_quantity"),
    [(2, 0), (0, 1), (0, 3)],
    ids=["wrong-sign", "partial", "oversized"],
)
async def test_startup_reconciliation_blocks_wrong_center_quantity(
    long_quantity, short_quantity
):
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot(
        center_long=long_quantity, center_short=short_quantity
    )
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="quantity mismatch"):
        await _assert_broker_state_matches_db(schwab, "SPX", [OPEN_TRADE])


@pytest.mark.asyncio
async def test_runtime_reconciliation_sets_gate_unsafe_for_wrong_ratio(monkeypatch):
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot(
        center_short=1
    )
    schwab.get_todays_orders.return_value = []
    trades = AsyncMock()
    trades.get_open_trades.return_value = [OPEN_TRADE]
    intents = AsyncMock()
    intents.intents_for_day.return_value = []
    gate = BrokerStateGate()

    async def stop_after_one_iteration(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(asyncio, "sleep", stop_after_one_iteration)
    with pytest.raises(asyncio.CancelledError):
        await broker_reconciler_loop(schwab, "SPX", trades, intents, gate)

    assert gate.unsafe
    assert "quantity mismatch" in gate.reason


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
