"""Tests for the profit management state machine."""

from butterfly_guy.core.config import ProfitManagementSettings, QuoteQualitySettings, TimeRegime
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
        exit_before_close_minutes=0,
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
    spread_bid=None,
    spread_ask=None,
    bid_to_mark_ratio=None,
    position_age_minutes=None,
    max_leg_spread_to_mark_ratio=None,
    max_leg_spread_abs=None,
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
        spread_bid=spread_bid,
        spread_ask=spread_ask,
        bid_to_mark_ratio=bid_to_mark_ratio,
        position_age_minutes=position_age_minutes,
        max_leg_spread_to_mark_ratio=max_leg_spread_to_mark_ratio,
        max_leg_spread_abs=max_leg_spread_abs,
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
    from butterfly_guy.core.config import ProfitManagementSettings
    settings = make_settings()
    settings = ProfitManagementSettings(
        regimes=settings.regimes,
        exit_before_close_minutes=settings.exit_before_close_minutes,
        use_absolute_loss_stop=True,
        max_loss_from_cost=0.50,
    )
    sm = ProfitStateMachine(settings)
    # 55% loss — exceeds absolute stop threshold (50%)
    pos = make_pos(entry=1.0, current=0.45, peak=1.0, pnl=-0.55, drawdown=0.55)
    signal = sm.evaluate(pos)
    assert signal is not None
    assert signal.reason == "absolute_loss_stop"
    assert signal.urgency == "high"


def test_no_end_of_day_exit_when_pre_close_exit_disabled():
    """Cash-settled butterflies should keep running into the close by default."""
    sm = ProfitStateMachine(make_settings())
    pos = make_pos(mins_to_close=4.0)
    signal = sm.evaluate(pos)
    assert signal is None


def test_exit_on_end_of_day_when_pre_close_exit_configured():
    """Pre-close exit remains available when explicitly configured."""
    settings = make_settings()
    settings.exit_before_close_minutes = 5
    sm = ProfitStateMachine(settings)
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


def test_peakvaluetrailer_allows_large_peak_to_retrace_to_loss():
    settings = make_settings()
    settings.regimes["afternoon"].drawdown_threshold = 0.75
    sm = ProfitStateMachine(settings)
    sm.evaluate(make_pos(entry=2.8, current=7.51, peak=7.51, pnl=4.71, drawdown=0.0))

    signal = sm.evaluate(
        make_pos(
            entry=2.8,
            current=2.78,
            peak=7.51,
            pnl=-0.02,
            drawdown=(7.51 - 2.78) / 7.51,
            regime="afternoon",
            mins_since_open=300.0,
        )
    )

    assert signal is None


def test_profitprotector_exits_at_profit_floor():
    settings = make_settings()
    settings.strategy = "profitprotector"
    sm = ProfitStateMachine(settings)
    sm.evaluate(make_pos(entry=2.8, current=7.51, peak=7.51, pnl=4.71, drawdown=0.0))

    signal = sm.evaluate(
        make_pos(
            entry=2.8,
            current=3.50,
            peak=7.51,
            pnl=0.70,
            drawdown=(7.51 - 3.50) / 7.51,
            regime="afternoon",
            mins_since_open=300.0,
        )
    )

    assert signal is not None
    assert signal.reason == "profitprotector_profit_floor"


def test_profitprotector_tightens_large_peak_drawdown():
    settings = make_settings()
    settings.strategy = "profitprotector"
    settings.regimes["afternoon"].drawdown_threshold = 0.75
    settings.profitprotector.profit_lock_activation_profit = 10.0
    settings.profitprotector.breakeven_activation_profit = 10.0
    sm = ProfitStateMachine(settings)
    sm.evaluate(make_pos(entry=2.8, current=6.0, peak=6.0, pnl=3.2, drawdown=0.0))

    signal = sm.evaluate(
        make_pos(
            entry=2.8,
            current=3.7,
            peak=6.0,
            pnl=0.9,
            drawdown=(6.0 - 3.7) / 6.0,
            regime="afternoon",
            mins_since_open=300.0,
        )
    )
    assert signal is None

    signal = sm.evaluate(
        make_pos(
            entry=2.8,
            current=2.9,
            peak=6.0,
            pnl=0.1,
            drawdown=(6.0 - 2.9) / 6.0,
            regime="afternoon",
            mins_since_open=300.0,
        )
    )

    assert signal is not None
    assert signal.reason == "drawdown_afternoon"


def test_default_drawdown_confirmation_is_immediate():
    """Default confirmation_polls=1 preserves existing behavior."""
    sm = ProfitStateMachine(make_settings())
    sm.evaluate(make_pos(entry=1.0, current=3.0, peak=3.0, pnl=2.0, drawdown=0.0))

    signal = sm.evaluate(
        make_pos(entry=1.0, current=1.35, peak=3.0, pnl=0.35, drawdown=0.55)
    )

    assert signal is not None
    assert signal.reason == "drawdown_morning"


def test_drawdown_requires_configured_confirmation_polls():
    settings = make_settings()
    settings.regimes["morning"].confirmation_polls = 2
    sm = ProfitStateMachine(settings)
    sm.evaluate(make_pos(entry=1.0, current=3.0, peak=3.0, pnl=2.0, drawdown=0.0))

    first = sm.evaluate(make_pos(entry=1.0, current=1.35, peak=3.0, pnl=0.35, drawdown=0.55))
    second = sm.evaluate(make_pos(entry=1.0, current=1.35, peak=3.0, pnl=0.35, drawdown=0.55))

    assert first is None
    assert second is not None
    assert second.reason == "drawdown_morning"


def test_drawdown_respects_min_hold_minutes():
    settings = make_settings()
    settings.regimes["morning"].min_hold_minutes = 30
    sm = ProfitStateMachine(settings)
    sm.evaluate(make_pos(entry=1.0, current=3.0, peak=3.0, pnl=2.0, drawdown=0.0))

    early = sm.evaluate(
        make_pos(
            entry=1.0,
            current=1.35,
            peak=3.0,
            pnl=0.35,
            drawdown=0.55,
            position_age_minutes=12,
        )
    )
    late = sm.evaluate(
        make_pos(
            entry=1.0,
            current=1.35,
            peak=3.0,
            pnl=0.35,
            drawdown=0.55,
            position_age_minutes=31,
        )
    )

    assert early is None
    assert late is not None
    assert late.reason == "drawdown_morning"


def test_drawdown_requires_min_peak_profit_ratio():
    settings = make_settings()
    settings.regimes["morning"].min_peak_profit_ratio = 1.5
    sm = ProfitStateMachine(settings)
    sm.evaluate(make_pos(entry=1.0, current=1.1, peak=1.1, pnl=0.1, drawdown=0.0))

    signal = sm.evaluate(make_pos(entry=1.0, current=0.5, peak=1.1, pnl=-0.5, drawdown=0.55))

    assert signal is None


def test_quote_quality_guard_blocks_bad_drawdown_exit():
    settings = make_settings()
    settings.quote_quality = QuoteQualitySettings(
        enabled=True,
        min_bid_to_mark_ratio=0.35,
        max_spread_width_ratio=1.5,
    )
    sm = ProfitStateMachine(settings)
    sm.evaluate(
        make_pos(
            entry=1.0,
            current=3.0,
            peak=3.0,
            pnl=2.0,
            drawdown=0.0,
            spread_bid=2.7,
            spread_ask=3.3,
            bid_to_mark_ratio=0.9,
        )
    )

    signal = sm.evaluate(
        make_pos(
            entry=1.0,
            current=1.35,
            peak=3.0,
            pnl=0.35,
            drawdown=0.55,
            spread_bid=0.1,
            spread_ask=4.0,
            bid_to_mark_ratio=0.07,
        )
    )

    assert signal is None


def test_quote_quality_guard_blocks_bad_leg_spread():
    settings = make_settings()
    settings.quote_quality = QuoteQualitySettings(
        enabled=True,
        min_bid_to_mark_ratio=0.35,
        max_spread_width_ratio=1.5,
        min_mark_value=0.25,
        max_leg_spread_to_mark_ratio=1.0,
        max_leg_spread_abs=0.20,
    )
    sm = ProfitStateMachine(settings)
    sm.evaluate(
        make_pos(
            entry=1.0,
            current=3.0,
            peak=3.0,
            pnl=2.0,
            drawdown=0.0,
            spread_bid=2.7,
            spread_ask=3.3,
            bid_to_mark_ratio=0.9,
            max_leg_spread_to_mark_ratio=0.5,
            max_leg_spread_abs=0.1,
        )
    )

    signal = sm.evaluate(
        make_pos(
            entry=1.0,
            current=1.35,
            peak=3.0,
            pnl=0.35,
            drawdown=0.55,
            spread_bid=1.1,
            spread_ask=1.8,
            bid_to_mark_ratio=0.81,
            max_leg_spread_to_mark_ratio=1.5,
            max_leg_spread_abs=0.25,
        )
    )

    assert signal is None


def test_quote_quality_guard_allows_good_drawdown_exit():
    settings = make_settings()
    settings.quote_quality = QuoteQualitySettings(
        enabled=True,
        min_bid_to_mark_ratio=0.35,
        max_spread_width_ratio=1.5,
    )
    sm = ProfitStateMachine(settings)
    sm.evaluate(
        make_pos(
            entry=1.0,
            current=3.0,
            peak=3.0,
            pnl=2.0,
            drawdown=0.0,
            spread_bid=2.7,
            spread_ask=3.3,
            bid_to_mark_ratio=0.9,
        )
    )

    signal = sm.evaluate(
        make_pos(
            entry=1.0,
            current=1.35,
            peak=3.0,
            pnl=0.35,
            drawdown=0.55,
            spread_bid=1.1,
            spread_ask=1.8,
            bid_to_mark_ratio=0.81,
        )
    )

    assert signal is not None
    assert signal.reason == "drawdown_morning"


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
