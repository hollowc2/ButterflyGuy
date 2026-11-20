"""Causal sampled triggers, gap exclusions and independently calculated cashflows."""

import pandas as pd
import pytest

from tools.research_studies.xsp_independent.realization import (
    evaluate_policy,
    first_cross,
    first_profit,
    settle_cash,
)


def stamp(time):
    return pd.Timestamp(f"2026-01-02 {time}", tz="America/New_York")


def entry():
    return {"date": "2026-01-02", "entry_time": stamp("10:01"), "cutoff": stamp("10:07"),
            "entry_ask": .50, "entry_mark": .45, "center": 100., "width": 2,
            "initial_risk_dollars": 52.60, "stressed_initial_risk_dollars": 57.60}


def path(times, bids):
    return pd.DataFrame({"timestamp": [stamp(t) for t in times],
                         "liquidation_bid": bids, "mark": bids, "entry_ask": bids})


def test_profit_observation_is_not_fill_and_later_fill_can_lose():
    p = path(["10:01", "10:02", "10:03", "10:04"], [.40, .80, .20, .90])
    out = evaluate_policy(entry(), p, pd.DataFrame(), "net_profit_25pct")
    assert out["trigger_time"] == stamp("10:02")
    assert out["exit_time"] == stamp("10:03")
    assert out["profit_threshold_dollars"] == pytest.approx(13.15)
    assert out["marketable_net"] == pytest.approx(-35.20)
    assert out["stressed_net"] == pytest.approx(-45.20)


def test_missing_first_profit_fill_excludes_instead_of_retrying_later_trigger():
    p = path(["10:01", "10:02", "10:06"], [.40, .80, .90])
    out = evaluate_policy(entry(), p, pd.DataFrame(), "net_profit_25pct")
    assert out["status"] == "excluded_trigger_exit_quote"
    assert "marketable_net" not in out


def test_quote_prefix_gap_cannot_be_skipped_to_later_profit():
    p = path(["10:01", "10:05", "10:06"], [.40, .80, .90])
    assert first_profit(p, entry())["status"] == "excluded_profit_prefix_gap"


def test_center_prefix_gap_and_entry_at_center_moving_away():
    p = pd.DataFrame({"timestamp": [stamp("10:01"), stamp("10:02"), stamp("10:03")],
                      "forward_proxy": [100., 101., 99.]})
    assert first_cross(p, entry())["trigger_time"] == stamp("10:03")
    p.loc[2, "timestamp"] = stamp("10:06")
    assert first_cross(p, entry())["status"] == "excluded_center_prefix_gap"


def test_no_trigger_fallback_is_scheduled_cutoff_and_keeps_negative_liquidation():
    p = path(["10:01", "10:02", "10:03", "10:04", "10:05", "10:06", "10:07"],
             [.40, .40, .40, .40, .40, .40, -.10])
    out = evaluate_policy(entry(), p, pd.DataFrame(), "net_profit_25pct")
    assert out["exit_reason"] == "scheduled_close_minus_15m"
    assert out["exit_time"] == stamp("10:07")
    assert out["marketable_net"] == pytest.approx(-65.20)


def test_baseline_missing_exit_does_not_remove_entry_from_settlement_policy():
    p = path(["10:01", "10:02"], [.40, .40])
    baseline = evaluate_policy(entry(), p, pd.DataFrame(), "baseline_60m")
    assert baseline["status"].startswith("excluded")
    out = evaluate_policy(entry(), p, pd.DataFrame(), "settlement",
                          {"settlement": 100.5, "source_type": "test_formula"})
    # Intrinsic$150 minus entry$50 minus OPENfee2.60; stressed entryonly5.
    assert out["marketable_net"] == pytest.approx(97.40)
    assert out["stressed_net"] == pytest.approx(92.40)
    assert out["closing_fee_dollars"] == 0
    assert out["closing_stress_dollars"] == 0


def test_missing_settlement_remains_unavailable_and_call_put_intrinsic_is_symmetric():
    assert settle_cash(entry(), None)["status"] == "excluded_missing_settlement"
    low = settle_cash(entry(), {"settlement": 99.5})
    high = settle_cash(entry(), {"settlement": 100.5})
    assert low["settlement_intrinsic"] == high["settlement_intrinsic"] == 1.5


def test_unobserved_profit_terminal_prefix_is_excluded_instead_of_fallback():
    p = path(["10:01", "10:02", "10:03"], [.40, .40, .40])
    assert first_profit(p, entry())["status"] == "excluded_profit_terminal_gap"
