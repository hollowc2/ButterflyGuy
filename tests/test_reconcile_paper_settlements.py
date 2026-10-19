from __future__ import annotations

import pytest

from butterfly_guy.scripts.reconcile_paper_settlements import official_settlement


def _trade(**overrides):
    trade = {
        "direction": "PUT",
        "lower_strike": 7670,
        "center_strike": 7695,
        "upper_strike": 7720,
        "entry_price": 2.01,
        "exit_price": 11.45,
        "pnl": 9.44,
        "metadata": {
            "settlement_source": "market_data_final_regular_session_1m_close",
            "settlement_spot": 7708.55,
            "settlement_spot_time": "2026-09-23T15:59:00-04:00",
        },
    }
    trade.update(overrides)
    return trade


def test_revalues_settlement_at_official_close_and_keeps_originals():
    change = official_settlement(_trade(), 7706.03)

    assert change is not None
    assert change["exit_price"] == pytest.approx(13.97)
    assert change["pnl"] == pytest.approx(11.96)
    metadata = change["metadata"]
    assert metadata["settlement_source"] == "official_daily_close"
    assert metadata["settlement_spot"] == 7706.03
    correction = metadata["settlement_correction"]
    assert correction["original_exit_price"] == 11.45
    assert correction["original_pnl"] == 9.44
    assert correction["original_settlement_spot"] == 7708.55


def test_no_change_when_provisional_value_already_matches():
    assert official_settlement(_trade(exit_price=13.97, pnl=11.96), 7706.03) is None
