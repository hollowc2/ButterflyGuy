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
