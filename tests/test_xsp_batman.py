"""Causal lifecycle and independent leg-cash fixtures for the bounded study."""

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from tools.research_studies.xsp_independent.batman import (
    account,
    component,
    geometry_ok,
    inside,
    lifecycle,
    movement,
    payoff,
    profit_zones,
    reach_diagnostic,
    select_centers,
    simulate,
)
from tools.research_studies.xsp_independent.quiet_flies import features

DAY = dt.date(2026, 1, 5)


def at(time):
    return pd.Timestamp(f"{DAY} {time}", tz="America/New_York")


def snapshot(time="10:31"):
    # Distinct mixed-right legs, asks on wings; .40 per fly to open.
    rows = []
    for right, center in (("PUT", 98), ("CALL", 102)):
        for strike in (center - 4, center, center + 4):
            rows.append({"timestamp": at(time), "right": right, "strike": strike,
                         "bid": .90 if strike == center else 1.0,
                         "ask": 1.0 if strike == center else 1.10,
                         "bid_size": 2 if strike == center else 1,
                         "ask_size": 2 if strike == center else 1})
    return pd.DataFrame(rows)


def position():
    return {"entry_time": at("10:31"), "entry_debit": .8, "entry_mark": .4,
            "centers": [98., 102.], "profit_zones": [[94.952, 105.048]],
            "signal_proxy": 100., "signal_drift": 1.}


def proxy(first="10:30", last="15:44", value=100.):
    stamps = pd.date_range(at(first), at(last), freq="min")
    return pd.DataFrame({"timestamp": stamps, "forward_proxy": value})


def test_mixed_open_and_close_need_only_transaction_sides_and_full_sizes():
    q = snapshot()
    q.loc[q.strike == 94, ["bid", "bid_size"]] = 0
    assert component(q, [98, 102], True)["price"] == pytest.approx(.8)
    assert component(q, [98, 102], False) is None
    q = snapshot()
    q.loc[(q.right == "PUT") & (q.strike == 98), "bid_size"] = 1
    assert component(q, [98, 102], True) is None
    assert component(q, [98, 102], False) is not None


def test_signed_payable_close_is_preserved():
    q = snapshot()
    q.loc[q.strike.isin([98, 102]) & (q.bid_size == 2), "ask"] = 3.
    assert component(q, [98, 102], False)["price"] == pytest.approx(-8.)


@pytest.mark.parametrize("settlement", [90., 97., 98., 100., 102., 105., 110.])
def test_combined_settlement_independently_sums_six_option_cashflows(settlement):
    # PUT94-2PUT98+PUT102 + CALL98-2CALL102+CALL106.
    put = max(94-settlement, 0) - 2*max(98-settlement, 0) + max(102-settlement, 0)
    call = max(settlement-98, 0) - 2*max(settlement-102, 0) + max(settlement-106, 0)
    row = position() | {"terminal": "settlement"}
    cash = account(row, settlement, DAY)
    assert cash["stressed"] == pytest.approx(100*(put+call)-80-5.20-10)
    assert cash["initial_risk"] == pytest.approx(95.20)
    assert payoff([98, 102], settlement) == pytest.approx(put+call)


def test_liquidation_accounts_for_both_flies_and_both_transaction_costs():
    row = position() | {"terminal": "liquidation", "exit_price": -.2,
                        "exit_mark": .1, "exit_time": at("11:00")}
    result = account(row, None, DAY)
    assert result["stressed"] == pytest.approx(-100-10.40-20)
    assert result["fee"] == 10.40
    assert account(position() | {"terminal": "settlement"}, None, DAY) == {
        "status": "unresolved_settlement"}


def test_profit_intervals_account_for_both_debits_and_overlap():
    assert profit_zones([94., 106.], 4.1) == []
    assert profit_zones([94., 106.], 1.) == [[91., 97.], [103., 109.]]
    assert profit_zones([98., 102.], 1.) == [[95., 105.]]
    assert not inside(95., [[95., 105.]])
    for x in np.arange(88, 112, .125):
        assert inside(x, profit_zones([98., 102.], 2.)) == (payoff([98, 102], x) > 2.)


def test_body_and_all_strikes_are_distinct_and_require_listed_wings():
    f = {"proxy": 100., "straddle": 4.}
    strikes = np.arange(85., 116.)
    assert select_centers(f, strikes, "body") == [98., 102.]
    assert select_centers(f, strikes, "all_strikes") == [94., 106.]
    assert geometry_ok([98, 102], 100, "body")
    assert not geometry_ok([98, 102], 100, "all_strikes")
    assert not geometry_ok([94, 106], 98, "all_strikes")  # equality fails
    assert select_centers(f, np.array([94., 98., 100., 102.]), "body") == []


def test_zone_signal_uses_completed_minute_then_strictly_later_combined_fill():
    row = position()
    q = pd.concat([snapshot("10:32"), snapshot("10:33")])
    result = lifecycle(q, proxy(), DAY, row, "zone_exit")
    assert result["trigger_time"] == at("10:32")
    assert result["exit_time"] == at("10:33")
    assert len(result["exit_package_prices"]) == 2


def test_failed_first_exit_window_settles_without_later_recovery():
    result = lifecycle(snapshot("10:35"), proxy(), DAY, position(), "zone_exit")
    assert result["reason"] == "zone_fill_missing"
    assert result["decision_time"] == at("10:34")
    assert result["terminal"] == "settlement"


def test_missing_prefix_known_causally_before_recovery_and_unknown_reach_not_zero():
    row = position() | {"profit_zones": [[110., 111.]]}
    p = proxy(value=100.)
    p = p[~p.timestamp.between(at("10:31"), at("10:40"))]
    result = lifecycle(snapshot("10:42"), p, DAY, row, "zone_exit")
    assert result["decision_time"] == at("10:34")  # last available10:31 +3min
    assert result["reason"] == "signal_gap"
    reach = reach_diagnostic(p, row, DAY)
    assert reach["zone_reach"] is None
    assert reach["observed_zone_reach"] is False


def test_cutoff_cannot_borrow_later_quote():
    row = position() | {"profit_zones": [[110., 111.]]}
    result = lifecycle(snapshot("15:46"), proxy(), DAY, row, "zone_exit")
    assert result["reason"] == "cutoff_fill_missing"
    assert result["decision_time"] == at("15:45")


def test_movement_hypothesis_is_causal_and_does_not_require_quiet():
    f = {"efficiency": .3, "drift": -2., "straddle": 4., "quiet": False}
    assert movement(f)
    assert not movement(f | {"drift": 1.99})
    assert not movement(f | {"efficiency": .299})


def test_signal_features_unchanged_by_future_prices():
    from tests.test_xsp_quiet_flies import snapshot as all_quotes

    p = proxy("09:31", "10:29")
    q = all_quotes(at("10:29"))
    original = features(q, p, DAY)
    future = proxy("10:30", "15:59", 1000.)
    assert features(q, pd.concat([p, future]), DAY) == original


def test_entry_admission_never_depends_on_future_fill_or_settlement():
    f = {"status": "covered", "signal_time": at("10:30"), "proxy": 100.,
         "straddle": 4., "drift": 2., "efficiency": .5}
    q = pd.concat([snapshot("10:29"), snapshot("10:31")])
    result = simulate(q, proxy(), f, DAY, "body", "unconditional", "zone_exit", None)
    assert result["entry_time"] == at("10:31")
    assert result["status"] == "unresolved_settlement"
    assert result["reason"] == "zone_fill_missing"
    assert "stressed" not in result
    result2 = simulate(q, proxy(), f, DAY, "body", "unconditional", "settlement", 100.)
    assert result2["entry_debit"] == result["entry_debit"]
