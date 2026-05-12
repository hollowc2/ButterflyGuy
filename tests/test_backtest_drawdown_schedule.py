from butterfly_guy.backtest.simulation_engine import (
    DrawdownWindow,
    SimulationEngine,
    SimulationParams,
)


def test_drawdown_rule_uses_legacy_regimes_by_default():
    params = SimulationParams(
        morning_drawdown=0.60,
        late_morning_drawdown=0.90,
        afternoon_drawdown=0.75,
    )

    assert SimulationEngine._drawdown_rule(params, 30) == (0.60, "morning", "morning")
    assert SimulationEngine._drawdown_rule(params, 180) == (0.90, "late_morning", "late_morning")
    assert SimulationEngine._drawdown_rule(params, 330) == (0.75, "afternoon", "afternoon")


def test_drawdown_rule_prefers_explicit_schedule_when_present():
    params = SimulationParams(
        morning_drawdown=0.60,
        late_morning_drawdown=0.90,
        afternoon_drawdown=0.75,
        drawdown_schedule=(
            DrawdownWindow(0, 150, 0.60, "early"),
            DrawdownWindow(150, 300, 0.90, "mid"),
            DrawdownWindow(300, 330, 0.75, "noon"),
            DrawdownWindow(330, 390, 0.50, "late"),
        ),
    )

    assert SimulationEngine._drawdown_rule(params, 149.9) == (0.60, "early", "late_morning")
    assert SimulationEngine._drawdown_rule(params, 150) == (0.90, "mid", "late_morning")
    assert SimulationEngine._drawdown_rule(params, 315) == (0.75, "noon", "afternoon")
    assert SimulationEngine._drawdown_rule(params, 330) == (0.50, "late", "afternoon")


def test_profitprotector_backtest_profit_floor_reason():
    params = SimulationParams(profit_management_strategy="profitprotector")

    reason = SimulationEngine._profit_exit_reason(
        params,
        entry_price=2.80,
        current_value=3.50,
        peak_value=7.51,
        drawdown=(7.51 - 3.50) / 7.51,
        drawdown_threshold=0.75,
        drawdown_label="afternoon",
    )

    assert reason == "profitprotector_profit_floor"


def test_profitprotector_backtest_tightens_large_peak_drawdown():
    params = SimulationParams(profit_management_strategy="profitprotector")
    params.profitprotector.profit_lock_activation_profit = 10.0
    params.profitprotector.breakeven_activation_profit = 10.0

    reason = SimulationEngine._profit_exit_reason(
        params,
        entry_price=2.80,
        current_value=2.90,
        peak_value=6.00,
        drawdown=(6.00 - 2.90) / 6.00,
        drawdown_threshold=0.75,
        drawdown_label="afternoon",
    )

    assert reason == "drawdown_afternoon"
