"""Causal known-at attribution and immutable priced results for completion audit."""

import pandas as pd
import pytest

from tools.research_studies.xsp_independent.fallback import fallback_event, settlement_cash


def stamp(time):
    return pd.Timestamp(f"2026-01-02 {time}", tz="America/New_York")


def trace(status):
    return {"entry_time": stamp("10:01"), "cutoff": stamp("15:45"), "status": status}


def test_gap_is_known_on_scheduled_third_minute_not_future_recovery():
    row = {**trace("excluded_profit_prefix_gap"), "gap_time": stamp("11:00"),
           "gap_seconds": 30 * 60}
    result = fallback_event(row)
    assert result["last_usable_observation_time"] == stamp("10:30")
    assert result["fallback_known_at"] == stamp("10:33")
    assert result["fallback_irrevocable"] is True


def test_missing_entry_proxy_locks_at_entry_without_future_data():
    result = fallback_event(trace("excluded_center_anchor_missing"))
    assert result["fallback_known_at"] == stamp("10:01")


def test_missing_trigger_fill_window_expires_once_and_never_retries():
    row = {**trace("excluded_trigger_exit_quote"), "trigger_time": stamp("10:10")}
    result = fallback_event(row)
    assert result["fallback_known_at"] == stamp("10:12")
    assert result["fallback_irrevocable"] is True


def test_fill_window_is_capped_at_last_scheduled_liquidation():
    row = {**trace("excluded_trigger_exit_quote"), "trigger_time": stamp("15:44")}
    assert fallback_event(row)["fallback_known_at"] == stamp("15:45")


def test_timed_fill_failure_and_cutoff_failure_have_different_known_times():
    row = {**trace("excluded_baseline_exit_quote"), "exit_deadline": stamp("11:01")}
    assert fallback_event(row)["fallback_known_at"] == stamp("11:03")
    cutoff_failure = fallback_event(trace("excluded_fallback_exit_quote"))
    assert cutoff_failure["fallback_known_at"] == stamp("15:45")


def test_unknown_failure_status_fails_closed_instead_of_imputing_pnl():
    with pytest.raises(ValueError, match="Unrecognized"):
        fallback_event(trace("new_unknown_failure"))


def test_native_settlement_has_opening_fee_and_stress_only():
    e = {"entry_time": stamp("10:01"), "width": 4, "center": 100., "entry_ask": .50,
         "entry_mark": .45, "initial_risk_dollars": 52.60, "stressed_initial_risk_dollars": 57.60}
    s = {"settlement": 101., "source_type": "cboe_native_xsp_published_settlement"}
    result = settlement_cash(e, s, stamp("16:00"))
    # Intrinsic$300 minus entry$50 minus OPENfee2.60; adverse entryonly$5.
    assert result["marketable_net"] == pytest.approx(247.40)
    assert result["stressed_net"] == pytest.approx(242.40)
    assert result["closing_fee_dollars"] == result["closing_stress_dollars"] == 0.
