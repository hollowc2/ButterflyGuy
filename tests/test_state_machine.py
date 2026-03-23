"""Tests for the profit management state machine."""

import pytest

from butterfly_guy.core.config import ProfitManagementSettings, TimeRegime
from butterfly_guy.position.position_manager import PositionState
from butterfly_guy.position.state_machine import ProfitState, ProfitStateMachine


def make_settings() -> ProfitManagementSettings:
    return ProfitManagementSettings(
        regimes={
            "morning": TimeRegime(
                start_minutes_after_open=0,
                end_minutes_after_open=120,
                drawdown_threshold=0.50,
            ),
            "late_morning": TimeRegime(
                start_minutes_after_open=120,
                end_minutes_after_open=240,
                drawdown_threshold=0.40,
            ),
            "afternoon": TimeRegime(
                start_minutes_after_open=240,
                end_minutes_after_open=390,
                drawdown_threshold=0.30,
            ),
        },
        exit_before_close_minutes=5,
    )


def make_pos(
    entry=1.0,
    current=1.0,
    peak=1.0,
    pnl=0.0,
    drawdown=0.0,
    regime="morning",
    mins_to_close=120.0,
    mins_since_open=30.0,
) -> PositionState:
    return PositionState(
        entry_price=entry,
        current_value=current,
        peak_value=peak,
        pnl=pnl,
        drawdown_from_peak=drawdown,
        time_regime=regime,
        minutes_to_close=mins_to_close,
        minutes_since_open=mins_since_open,
    )


def test_no_exit_when_not_in_profit_tent():
    """Drawdown-from-peak exit should NOT fire if position was never in profit tent."""
    sm = ProfitStateMachine(make_settings())
    # 25% loss — below absolute stop threshold (50%), so only drawdown gate applies
    pos = make_pos(entry=1.0, current=0.75, peak=1.0, pnl=-0.25, drawdown=0.25)
    signal = sm.evaluate(pos)
    assert signal is None


def test_absolute_loss_stop_fires_without_profit_tent():
    """Absolute loss stop should fire even if position was never in profit tent."""
    sm = ProfitStateMachine(make_settings())
    # 55% loss — exceeds absolute stop threshold (50%)
    pos = make_pos(entry=1.0, current=0.45, peak=1.0, pnl=-0.55, drawdown=0.55)
    signal = sm.evaluate(pos)
    assert signal is not None
    assert signal.reason == "absolute_loss_stop"
    assert signal.urgency == "high"


def test_exit_on_end_of_day():
    """Should always signal exit when minutes_to_close <= 5."""
    sm = ProfitStateMachine(make_settings())
    pos = make_pos(mins_to_close=4.0)
    signal = sm.evaluate(pos)
    assert signal is not None
    assert signal.reason == "end_of_day"
    assert signal.urgency == "immediate"


def test_no_exit_in_profit_tent_no_drawdown():
    """In profit tent with no drawdown → no exit."""
    sm = ProfitStateMachine(make_settings())
    # Build up to profit tent
    pos_profit = make_pos(entry=1.0, current=2.0, peak=2.0, pnl=1.0, drawdown=0.0)
    sm.evaluate(pos_profit)
    assert sm.state == ProfitState.PROFIT_TENT

    pos = make_pos(entry=1.0, current=1.95, peak=2.0, pnl=0.95, drawdown=0.025)
    signal = sm.evaluate(pos)
    assert signal is None


def test_exit_on_morning_drawdown():
    """Should exit when in profit tent + 50% drawdown in morning."""
    sm = ProfitStateMachine(make_settings())

    # Drive into profit tent
    sm.evaluate(make_pos(entry=1.0, current=3.0, peak=3.0, pnl=2.0, drawdown=0.0))
    assert sm.state == ProfitState.PROFIT_TENT

    # 55% drawdown in morning
    pos = make_pos(
        entry=1.0, current=1.35, peak=3.0, pnl=0.35,
        drawdown=0.55, regime="morning"
    )
    signal = sm.evaluate(pos)
    assert signal is not None
    assert "morning" in signal.reason


def test_exit_on_afternoon_drawdown_lower_threshold():
    """Afternoon threshold is 30%, lower than morning's 50%."""
    sm = ProfitStateMachine(make_settings())
    sm.evaluate(make_pos(entry=1.0, current=3.0, peak=3.0, pnl=2.0, drawdown=0.0))

    pos = make_pos(
        entry=1.0, current=2.0, peak=3.0, pnl=1.0,
        drawdown=0.333, regime="afternoon", mins_since_open=300.0
    )
    signal = sm.evaluate(pos)
    assert signal is not None
    assert "afternoon" in signal.reason


def test_state_transitions():
    sm = ProfitStateMachine(make_settings())
    assert sm.state == ProfitState.LOSS

    # 10% profit → NEAR_LONG
    sm.evaluate(make_pos(entry=1.0, current=1.1, peak=1.1, pnl=0.1))
    assert sm.state == ProfitState.NEAR_LONG

    # 60% profit → PROFIT_TENT
    sm.evaluate(make_pos(entry=1.0, current=1.6, peak=1.6, pnl=0.6))
    assert sm.state == ProfitState.PROFIT_TENT

    # Back to loss
    sm.evaluate(make_pos(entry=1.0, current=0.9, peak=1.6, pnl=-0.1))
    assert sm.state == ProfitState.LOSS


def test_reset_clears_state():
    sm = ProfitStateMachine(make_settings())
    sm.evaluate(make_pos(entry=1.0, current=2.0, peak=2.0, pnl=1.0))
    sm.reset()
    assert sm.state == ProfitState.LOSS
