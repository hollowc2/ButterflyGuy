"""Independent reviewer catches inappropriate expiry fees and reaction timing."""
import pytest

from tools.research_studies.xsp_independent.review_realization import cash_check, independent_payoff


def settlement_row():
    return {"date": "2026-01-02", "signal_time": "2026-01-02 10:00-05:00",
            "entry_time": "2026-01-02 10:01-05:00", "exit_time": "2026-01-02 16:00-05:00",
            "entry_ask": .50, "entry_mark": .45, "center": 100., "width": 2, "right": "CALL",
            "initial_risk_dollars": 52.60, "stressed_initial_risk_dollars": 57.60,
            "policy": "settlement", "settlement": 100.5,
            "settlement_source": "cboe_native_xsp_published_settlement",
            "closing_fee_dollars": 0., "closing_stress_dollars": 0.,
            "marketable_net": 97.4, "stressed_net": 92.4, "midpoint_net": 102.4}


def test_independent_cash_audit_rejects_closing_fee_at_settlement():
    row = settlement_row()
    cash_check(row, {"2026-01-02": 100.5})
    row["marketable_net"] -= 2.60
    with pytest.raises(AssertionError):
        cash_check(row, {"2026-01-02": 100.5})


def test_independent_cash_audit_rejects_extra_exit_stress_at_settlement():
    row = settlement_row()
    row["stressed_net"] -= 5.
    with pytest.raises(AssertionError):
        cash_check(row, {"2026-01-02": 100.5})


def test_leg_by_leg_call_put_exercise_has_same_cash_payoff():
    assert independent_payoff(100, 2, 100.5, "CALL") == 150.
    assert independent_payoff(100, 2, 100.5, "PUT") == 150.
    assert independent_payoff(100, 2, 104, "CALL") == 0.


def test_independent_cash_audit_rejects_wrong_published_settlement():
    with pytest.raises(AssertionError):
        cash_check(settlement_row(), {"2026-01-02": 100.51})
