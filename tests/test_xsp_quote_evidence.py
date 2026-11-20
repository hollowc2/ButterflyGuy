"""Diagnostic attribution must separate missing buyers from unused-side censoring."""
import pandas as pd
import pytest

from tools.research_studies.xsp_independent.quote_evidence import (
    counts,
    event_times,
    leg_evidence,
    proxy_evidence,
    snapshot_evidence,
)


def ts(value):
    return pd.Timestamp(f"2026-01-02 {value}", tz="America/New_York")


def quote(strike, bid, ask, bid_size=10, ask_size=10, right="CALL"):
    return {"timestamp": ts("15:45"), "strike": strike, "right": right,
            "bid": bid, "ask": ask, "bid_size": bid_size, "ask_size": ask_size}


def test_body_zero_bid_no_size_is_unused_for_buy_to_close():
    evidence = leg_evidence(pd.Series(quote(600, 0, .1, bid_size=0, ask_size=2)), role="body")
    assert evidence["close_side_valid"]
    assert not evidence["both_sides_valid"]
    assert "unused_side_undersized" in evidence["labels"]
    assert "unused_side_zero_bid_no_size" in evidence["labels"]


def test_wing_zero_bid_no_size_has_no_displayed_buyer():
    evidence = leg_evidence(pd.Series(quote(596, 0, .1, bid_size=0)), role="lower")
    assert not evidence["close_side_valid"]
    assert evidence["primary_reason"] == "required_side_zero_bid_no_size"


def test_all_legs_must_have_necessary_closing_sides_for_unused_only_classification():
    entry = {"center": 600, "width": 4, "right": "CALL"}
    frame = pd.DataFrame([quote(596, 1, 1.1, ask_size=0),
                          quote(600, .4, .5), quote(604, .1, .2)])
    got = snapshot_evidence(frame, entry, ts("15:45"))
    assert got["solely_unused_side_rejection"]
    assert got["primary_reason"] == "solely_unused_side_size_filter"
    frame.loc[frame.strike == 604, "bid_size"] = 0
    got = snapshot_evidence(frame, entry, ts("15:45"))
    assert not got["solely_unused_side_rejection"]
    assert got["primary_reason"] == "required_side_undersized"


def test_signed_payable_close_is_never_called_unsellable_or_floored():
    frame = pd.DataFrame([quote(596, .9, 1), quote(600, .5, .6), quote(604, .1, .2)])
    got = snapshot_evidence(frame, {"center": 600, "width": 4, "right": "CALL"}, ts("15:45"))
    assert got["signed_component_close_value"] == pytest.approx(-.2)
    assert got["component_value_class"] == "payable_close"
    assert not got["complex_fill_demonstrated"]


@pytest.mark.parametrize("bad, reason", [(None, "absent_row"),
    (quote(600, float("nan"), .2), "nonfinite_price"),
    (quote(600, .3, .2), "crossed_market"), (quote(600, 0, 0), "zero_zero")])
def test_missing_invalid_and_no_quote_are_different_reasons(bad, reason):
    result = leg_evidence(pd.Series(bad) if bad is not None else None, role="lower")
    assert result["primary_reason"] == reason
    assert not result["close_side_valid"]


def test_prefix_gap_audits_missing_minutes_not_recovery_timestamp():
    row = {"status": "excluded_profit_prefix_gap", "cutoff": ts("15:45"),
           "gap_time": ts("11:04"), "gap_seconds": 180}
    assert event_times(row) == [ts("11:02"), ts("11:03")]
    row["status"] = "excluded_profit_terminal_gap"
    row["gap_time"] = ts("15:45")
    assert event_times(row) == [ts("15:43"), ts("15:44"), ts("15:45")]


def test_missing_first_trigger_fill_does_not_use_trigger_or_after_cutoff():
    row = {"status": "excluded_trigger_exit_quote", "cutoff": ts("15:45"),
           "trigger_time": ts("15:44")}
    assert event_times(row) == [ts("15:45")]


def test_proxy_missing_pairs_is_not_inferred_from_held_leg_validity():
    frame = pd.DataFrame([quote(596, 1, 1.1), quote(600, .4, .5), quote(604, .1, .2)])
    result = proxy_evidence(frame, ts("15:45"))
    assert result["primary_reason"] == "insufficient_usable_call_put_pairs"
    assert not result["proxy_valid"]


def test_reason_counts_are_snapshot_not_multiplied_by_legs():
    frame = pd.DataFrame([quote(596, 0, .1, bid_size=0),
                          quote(600, .4, .5), quote(604, 0, .2, bid_size=0)])
    row = snapshot_evidence(frame, {"center": 600, "width": 4, "right": "CALL"}, ts("15:45"))
    result = counts([row])
    assert result["multi_label_snapshots"]["required_side_zero_bid_no_size"] == 1
    assert result["per_leg"]["lower"]["multi_labels"]["required_side_zero_bid_no_size"] == 1
    assert result["per_leg"]["upper"]["multi_labels"]["required_side_zero_bid_no_size"] == 1
