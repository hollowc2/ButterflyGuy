"""Independent hand-calculated contracts for XSP value-realization research."""

from decimal import ROUND_HALF_EVEN, Decimal

import pandas as pd
import pytest

from tools.research_studies.xsp_independent import realization, settlement_data


@pytest.mark.parametrize(
    "spot", [597.995, 598.0, 598.005, 599.995, 600.0, 600.005, 601.995, 602.0, 602.005]
)
def test_symmetric_tent_matches_both_three_leg_intrinsic_ledgers(spot):
    s, lower, body, upper = map(Decimal, map(str, (spot, 598.0, 600.0, 602.0)))
    call = max(s - lower, 0) - 2 * max(s - body, 0) + max(s - upper, 0)
    put = max(lower - s, 0) - 2 * max(body - s, 0) + max(upper - s, 0)
    actual = settlement_data.tent_value(600.0, 2.0, spot)
    assert actual == pytest.approx(float(call))
    assert actual == pytest.approx(float(put))


@pytest.mark.parametrize(
    "spot", ["597.995", "598.004", "598.005", "599.995", "600.005", "601.995", "602.004", "602.005"]
)
def test_unconfirmed_two_vs_three_decimal_rounding_changes_intrinsic_at_most_half_dollar(spot):
    exact = Decimal(spot)
    rounded = exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    exact_payoff = settlement_data.tent_value(600.0, 2.0, float(exact))
    rounded_payoff = settlement_data.tent_value(600.0, 2.0, float(rounded))
    assert 100 * abs(exact_payoff - rounded_payoff) <= 0.5 + 1e-10


def test_cash_settlement_has_opening_fee_and_entry_stress_only():
    assert settlement_data.cash_settlement_pnl(0.5, 600.0, 2.0, 600.0) == pytest.approx(147.4)
    assert settlement_data.cash_settlement_pnl(
        0.5, 600.0, 2.0, 600.0, entry_stress=0.05
    ) == pytest.approx(142.4)
    assert settlement_data.cash_settlement_pnl(0.5, 600.0, 2.0, 602.0) == pytest.approx(-52.6)


def stamp(clock):
    return pd.Timestamp(f"2026-04-01 {clock}", tz="America/New_York")


def research_entry():
    return {
        "date": "2026-04-01",
        "entry_time": stamp("10:01"),
        "cutoff": stamp("10:07"),
        "entry_ask": 0.50,
        "entry_mark": 0.45,
        "center": 600.0,
        "width": 2.0,
        "initial_risk_dollars": 52.60,
        "stressed_initial_risk_dollars": 57.60,
    }


def fly_path(clocks, bids):
    return pd.DataFrame(
        {
            "timestamp": [stamp(t) for t in clocks],
            "liquidation_bid": bids,
            "mark": bids,
            "entry_ask": bids,
        }
    )


def test_profit_threshold_includes_both_fees_and_later_fill_can_miss_target():
    path = fly_path(["10:01", "10:02", "10:03", "10:04"], [0.4, 0.68, 0.69, 0.60])
    trigger = realization.first_profit(path, research_entry())
    assert trigger["trigger_time"] == stamp("10:03")
    assert trigger["profit_threshold_dollars"] == pytest.approx(13.15)
    assert trigger["trigger_net_dollars"] == pytest.approx(13.80)
    actual = realization.evaluate_policy(research_entry(), path, pd.DataFrame(), "net_profit_25pct")
    assert actual["exit_time"] == stamp("10:04")
    assert actual["marketable_net"] == pytest.approx(4.80)
    assert actual["stressed_net"] == pytest.approx(-5.20)


def test_unobserved_entry_side_cannot_assert_cross_occurred_after_entry():
    proxy = pd.DataFrame(
        {"timestamp": [stamp("10:00"), stamp("10:02")], "forward_proxy": [599.0, 601.0]}
    )
    result = realization.first_cross(proxy, research_entry())
    assert result["status"].startswith("excluded_center_anchor")


def test_geometry_reports_internal_parquet_microsecond_gap_in_seconds():
    proxy = pd.DataFrame(
        {
            "timestamp": [stamp("10:01"), stamp("10:02"), stamp("10:06"), stamp("10:07")],
            "forward_proxy": [599.0, 599.0, 599.0, 599.0],
        }
    )
    proxy["timestamp"] = proxy.timestamp.dt.as_unit("us")
    result = realization.geometry(proxy, research_entry())
    assert result["geometry_status"] == "gapped"
    assert result["max_proxy_gap_seconds"] == 240.0


def test_accepted_entry_without_old_exit_remains_eligible_for_center_realization():
    path = fly_path(["10:01", "10:02", "10:03"], [0.4, 0.6, 0.6])
    proxy = pd.DataFrame(
        {"timestamp": [stamp("10:01"), stamp("10:02")], "forward_proxy": [599.0, 601.0]}
    )
    baseline = realization.evaluate_policy(research_entry(), path, proxy, "baseline_60m")
    candidate = realization.evaluate_policy(research_entry(), path, proxy, "center_cross")
    assert baseline["status"].startswith("excluded")
    assert candidate["status"] == "completed"
    assert candidate["exit_time"] == stamp("10:03")


def test_pairing_does_not_turn_missing_baseline_or_candidate_into_zero():
    rows = [
        {"date": "2026-04-01", "policy": "baseline_60m", "status": "excluded"},
        {
            "date": "2026-04-01",
            "policy": "center_cross",
            "status": "completed",
            "stressed_net": 1000.0,
            "marketable_net": 1010.0,
        },
        {
            "date": "2026-04-02",
            "policy": "baseline_60m",
            "status": "completed",
            "stressed_net": -10.0,
            "marketable_net": 0.0,
        },
        {
            "date": "2026-04-02",
            "policy": "center_cross",
            "status": "completed",
            "stressed_net": 5.0,
            "marketable_net": 15.0,
        },
        {
            "date": "2026-04-03",
            "policy": "baseline_60m",
            "status": "completed",
            "stressed_net": -2000.0,
            "marketable_net": -1990.0,
        },
        {"date": "2026-04-03", "policy": "center_cross", "status": "excluded"},
    ]
    result = realization.paired(rows, "center_cross")
    assert result["common_completed_entries"] == 1
    assert result["stressed_difference"] == 15.0
    assert result["baseline_missing_but_candidate_completed"] == 1
