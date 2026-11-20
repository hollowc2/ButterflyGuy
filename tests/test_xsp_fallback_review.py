"""Independent frozen-trace, causal-state and cash-ledger completion checks."""

import copy

import pandas as pd
import pytest

from tools.research_studies.xsp_independent import fallback


def at(clock):
    return pd.Timestamp(f"2026-04-01 {clock}", tz="America/New_York")


def entry():
    return {
        "date": "2026-04-01",
        "family": "MR2",
        "width": 4,
        "center": 600.0,
        "right": "CALL",
        "entry_time": at("10:01"),
        "cutoff": at("15:45"),
        "entry_ask": 0.50,
        "entry_mark": 0.45,
        "initial_risk_dollars": 52.60,
        "stressed_initial_risk_dollars": 57.60,
    }


def native():
    return {"settlement": 601.0, "source_type": "cboe_native_xsp_published_settlement"}


def original_settlement():
    # Independent one-fly cash ledger: intrinsic$300, opening$50+$2.60fee,
    # stressed opening$55+$2.60fee; no closing transaction.
    return {
        **entry(),
        "policy": "settlement",
        "status": "completed",
        "exit_time": at("16:00"),
        "settlement": 601.0,
        "settlement_intrinsic": 3.0,
        "marketable_net": 247.40,
        "stressed_net": 242.40,
        "midpoint_net": 252.40,
        "marketable_r": 247.40 / 52.60,
        "stressed_r": 242.40 / 57.60,
    }


def test_first_gap_locks_at_missing_scheduled_poll_and_later_recovery_cannot_change_it():
    first = {
        **entry(),
        "policy": "center_cross",
        "status": "excluded_center_prefix_gap",
        "gap_time": at("10:30"),
        "gap_seconds": 25 * 60,
    }
    second = {**first, "gap_time": at("11:00"), "gap_seconds": 55 * 60}
    a = fallback.complete_trace(entry(), first, native(), original_settlement())
    b = fallback.complete_trace(entry(), second, native(), original_settlement())
    assert a["fallback_known_at"] == b["fallback_known_at"] == at("10:08")
    assert a["terminal_mode"] == b["terminal_mode"] == "fallback_native_settlement"
    assert a["marketable_net"] == b["marketable_net"] == pytest.approx(247.40)
    assert a["stressed_net"] == b["stressed_net"] == pytest.approx(242.40)
    assert a["exit_time"] == b["exit_time"] == at("16:00")
    assert a["fallback_irrevocable"] is True


def test_original_priced_exit_finance_is_preserved_exactly_instead_of_settlement():
    trace = {
        **entry(),
        "policy": "center_cross",
        "status": "completed",
        "exit_time": at("10:03"),
        "exit_reason": "first_trigger",
        "liquidation_bid": 0.60,
        "exit_mark": 0.60,
        "marketable_net": 4.80,
        "stressed_net": -5.20,
        "midpoint_net": 9.80,
        "marketable_r": 4.80 / 52.60,
        "stressed_r": -5.20 / 57.60,
        "closing_fee_dollars": 2.60,
        "closing_stress_dollars": 5.0,
        "exposure_minutes": 2.0,
    }
    result = fallback.complete_trace(entry(), trace, native(), original_settlement())
    for field in fallback.FINANCE_FIELDS:
        if field in trace:
            assert result[field] == trace[field]
    assert result["original_exit_trace"] == trace
    assert result["terminal_mode"] == "original_priced_exit"
    assert result["fallback_irrevocable"] is False


def test_anchor_missing_is_known_at_entry_and_completion_never_turns_missing_into_zero():
    trace = {**entry(), "policy": "center_cross", "status": "excluded_center_anchor_missing"}
    result = fallback.complete_trace(entry(), trace, native(), original_settlement())
    assert result["fallback_known_at"] == at("10:01")
    assert result["marketable_net"] == pytest.approx(247.40)
    assert result["stressed_net"] == pytest.approx(242.40)
    assert result["closing_fee_dollars"] == result["closing_stress_dollars"] == 0.0


def test_first_failed_fill_is_known_at_deadline_not_later_retry_or_settlement():
    trace = {
        **entry(),
        "policy": "net_profit_25pct",
        "status": "excluded_trigger_exit_quote",
        "trigger_time": at("10:02"),
    }
    result = fallback.complete_trace(entry(), trace, native(), original_settlement())
    assert result["fallback_known_at"] == at("10:04")
    assert result["exit_time"] == at("16:00")
    assert result["terminal_mode"] == "fallback_native_settlement"


def test_completion_rejects_mutated_entry_and_native_terminal_input():
    trace = {**entry(), "policy": "center_cross", "status": "excluded_center_anchor_missing"}
    mutated = copy.deepcopy(trace)
    mutated["center"] = 601.0
    with pytest.raises(ValueError, match="Frozen entry disagreement"):
        fallback.complete_trace(entry(), mutated, native(), original_settlement())
    changed_native = {**native(), "settlement": 602.0}
    with pytest.raises(ValueError, match="settlement cashflow mismatch"):
        fallback.complete_trace(entry(), trace, changed_native, original_settlement())


def test_failure_cannot_be_known_before_entry():
    trace = {
        **entry(),
        "status": "excluded_profit_prefix_gap",
        "gap_time": at("10:00"),
        "gap_seconds": 3 * 60,
    }
    with pytest.raises(ValueError, match="Failure-known time"):
        fallback.fallback_event(trace)
