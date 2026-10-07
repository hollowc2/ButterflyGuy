"""Offline observation clocks must preserve the live XSP exit policy."""

import datetime as dt

import pytest

from butterfly_guy.core.config import load_config
from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.position.position_manager import PositionManager
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.scripts.replay_xsp_exits import replay_trade
from tests.test_position_manager import make_xsp_candidate, quote_map


def test_xsp_replay_uses_observation_clock_and_morning_hold():
    settings = load_config(config_path="configs/config_xsp.yaml").profit_management
    manager = PositionManager("XSP", settings)
    manager.reset(0.30)
    candidate = make_xsp_candidate()
    at = dt.datetime(2026, 9, 25, 10, 45, tzinfo=EASTERN)
    state = manager.update_position_value(
        candidate, quote_map(0.40), at=at, include_tent_boundaries=False
    )
    assert state.minutes_since_open == 75
    assert state.minutes_to_close == 315
    assert state.time_regime == "morning"
    assert settings.regimes[state.time_regime].min_hold_minutes == 30


def test_xsp_replay_rejects_naive_clock():
    manager = PositionManager("XSP")
    manager.reset(0.25)
    with pytest.raises(ValueError, match="timezone-aware"):
        manager.update_position_value(
            make_xsp_candidate(), quote_map(0.40), at=dt.datetime(2026, 9, 25, 10)
        )


def test_xsp_replay_retains_confirmed_peak_and_quality_exit_gate():
    settings = load_config(config_path="configs/config_xsp.yaml").profit_management
    manager = PositionManager("XSP", settings)
    manager.reset(0.30)
    machine = ProfitStateMachine(settings)
    candidate = make_xsp_candidate()
    at = dt.datetime(2026, 9, 25, 14, 0, tzinfo=EASTERN)
    states = []
    for i, mark in enumerate([1.31, 1.31, 1.31, 1.31]):
        state = manager.update_position_value(
            candidate,
            quote_map(mark),
            at=at + dt.timedelta(seconds=3 * i),
            include_tent_boundaries=False,
        )
        state.position_age_minutes = 240
        machine.evaluate(state)
        states.append(state)
    # Three valid polls confirm the peak; a jump may reject the initial one.
    assert states[1].peak_value == pytest.approx(0.30)
    assert states[-1].peak_value == pytest.approx(1.31)
    collapsed = manager.update_position_value(
        candidate,
        quote_map(0.19),
        at=at + dt.timedelta(seconds=12),
        include_tent_boundaries=False,
    )
    collapsed.position_age_minutes = 240
    assert collapsed.drawdown_from_peak > 0.85
    assert machine.evaluate(collapsed) is None


def test_xsp_replay_respects_early_close():
    manager = PositionManager("XSP")
    manager.reset(0.25)
    state = manager.update_position_value(
        make_xsp_candidate(),
        quote_map(0.4),
        at=dt.datetime(2026, 11, 27, 12, 45, tzinfo=EASTERN),
        include_tent_boundaries=False,
    )
    assert state.minutes_to_close == 15


@pytest.mark.parametrize("bad_field", ["missing_leg", "direction", "expiration", "market"])
def test_monitor_replay_refuses_unusable_held_leg_evidence(bad_field):
    at = dt.datetime(2026, 9, 25, 10, 5, tzinfo=EASTERN)
    trade = {
        "id": 1, "trade_date": "2026-09-25", "direction": "PUT",
        "wing_width": 3, "center_strike": 740, "entry_price": 0.30,
        "entry_time": at.isoformat(), "entry_spot": 743,
    }
    batch = [
        {
            "trade_id": "1", "ts": at.isoformat(), "expiration": "2026-09-25",
            "strike": str(q.strike), "option_type": "PUT", "symbol": q.symbol,
            "bid": str(q.bid), "ask": str(q.ask), "mark": str(q.mark),
            "peak_value": "0.30",
        }
        for q in quote_map(0.4).values()
    ]
    if bad_field == "missing_leg":
        batch.pop()
    elif bad_field == "direction":
        batch[0]["option_type"] = "CALL"
    elif bad_field == "expiration":
        batch[0]["expiration"] = "2026-09-28"
    else:
        batch[0]["ask"] = "0.01"
    with pytest.raises(ValueError):
        replay_trade(trade, [batch], load_config(config_path="configs/config_xsp.yaml"))
