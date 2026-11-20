"""Independent reviewer must reject corrupt cash/timing and preserve missingness."""
import pytest

from tools.research_studies.xsp_independent.review_results import (
    cell_metrics,
    paired_metrics,
    validate_cash_and_clock,
)


def trade():
    return {"date": "2026-09-25", "status": "completed", "width": 2,
            "signal_ts": "2026-09-25 10:05-04:00", "entry_ts": "2026-09-25 10:06-04:00",
            "exit_ts": "2026-09-25 11:06-04:00", "entry_ask": .30,
            "liquidation_bid": -.10, "entry_mark": .20, "exit_mark": .05,
            "pnl_marketable": -45.20, "pnl_stressed": -55.20, "pnl_mark": -20.20,
            "initial_risk": 32.60}


def test_reviewer_reconciles_signed_cash_and_detects_missing_fee():
    row = trade()
    validate_cash_and_clock(row)
    row["pnl_marketable"] += 2.60
    with pytest.raises(AssertionError):
        validate_cash_and_clock(row)


def test_reviewer_detects_signal_snapshot_fill():
    row = trade()
    row["entry_ts"] = row["signal_ts"]
    with pytest.raises(AssertionError):
        validate_cash_and_clock(row)


def test_reviewer_detects_corrupt_initial_risk_denominator():
    row = trade()
    row["initial_risk"] = 1.0
    with pytest.raises(AssertionError):
        validate_cash_and_clock(row)


def test_removing_top_winners_does_not_remove_losses():
    result = cell_metrics([trade()], "2026-05-18")
    assert result["top3_positive_wins_removed_stressed"] == pytest.approx(-55.20)


def test_paired_no_signal_is_zero_but_missing_execution_is_excluded():
    candidate = [{"date": "2026-09-24", "status": "no_signal"},
                 {"date": "2026-09-25", "status": "missing_exit"}]
    baseline = [{"date": d, "status": "completed", "pnl_stressed": -10.0}
                for d in ("2026-09-24", "2026-09-25")]
    result = paired_metrics(candidate, baseline)
    assert result["eligible_days"] == 1
    assert result["candidate_no_signal_days"] == 1
    assert result["stressed_difference"] == 10.0
