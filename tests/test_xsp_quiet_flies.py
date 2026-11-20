"""Independent cash checks and causal execution boundaries for quiet-day research."""

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from tools.research_studies.xsp_independent.quiet_flies import (
    centers_for,
    entry_price,
    features,
    legs_for,
    outcome,
    relative_calm,
    simulate,
    spx_minutes,
)

DAY = dt.date(2026, 1, 5)


def at(value):
    return pd.Timestamp(f"{DAY} {value}", tz="America/New_York")


def snapshot(stamp=None):
    rows = []
    for strike in range(95, 106):
        for right in ("CALL", "PUT"):
            intrinsic = max(100 - strike, 0) if right == "CALL" else max(strike - 100, 0)
            time_value = max(.05, 1 - .15 * abs(strike - 100))
            mid = intrinsic + time_value
            rows.append({"timestamp": stamp if stamp is not None else at("10:31"),
                         "strike": float(strike), "right": right,
                         "bid": mid - .025, "ask": mid + .025,
                         "bid_size": 20, "ask_size": 20})
    return pd.DataFrame(rows)


@pytest.mark.parametrize("form", ["CALL", "PUT", "IRON"])
@pytest.mark.parametrize("settlement", [95, 99, 100, 101, 105])
def test_settlement_agrees_with_individual_leg_cash(form, settlement):
    entry = {"entry_debit": -1.25 if form == "IRON" else .75,
             "entry_mark": -1.30 if form == "IRON" else .70}
    result = outcome(entry, [100], 2, form, settlement)
    # Independently sum calls/puts, including signed short iron liabilities.
    cash = 0
    for right, strike, qty in legs_for(100, 2, form):
        value = max(settlement - strike, 0) if right == "CALL" else max(strike - settlement, 0)
        cash += qty * value * 100
    assert result["stressed"] == pytest.approx(cash - entry["entry_debit"] * 100 - 7.60)
    assert result["initial_risk"] == pytest.approx(82.60)


def test_iron_and_debit_same_effective_entry_have_identical_net_cash():
    for settlement in [95, 99.3, 100, 103]:
        debit = outcome({"entry_debit": .75, "entry_mark": .70}, [100], 2, "CALL", settlement)
        iron = outcome({"entry_debit": -1.25, "entry_mark": -1.30}, [100], 2, "IRON", settlement)
        assert iron == debit | {"terminal_cash_points": debit["terminal_cash_points"] - 2}


def test_buy_wing_zero_bid_allowed_but_zero_bid_sell_rejected():
    snap = snapshot()
    snap.loc[(snap.right == "CALL") & (snap.strike == 102), ["bid", "bid_size"]] = 0
    assert entry_price(snap, [100], 2, "CALL") is not None
    snap.loc[(snap.right == "CALL") & (snap.strike == 100), "bid_size"] = 0
    assert entry_price(snap, [100], 2, "CALL") is None


def test_pair_shared_wing_requires_two_asks_and_pays_double_fees():
    snap = snapshot()
    snap.loc[(snap.right == "CALL") & (snap.strike == 100), "ask_size"] = 1
    assert entry_price(snap, [98, 102], 2, "CALL") is None
    snap.loc[(snap.right == "CALL") & (snap.strike == 100), "ask_size"] = 2
    entry = entry_price(snap, [98, 102], 2, "CALL")
    assert entry is not None
    result = outcome(entry, [98, 102], 2, "CALL", 100)
    assert result["fee"] == 5.20
    assert result["stress_cost"] == 10
    assert entry["gross_contracts"] == 8


def test_strict_later_entry_and_unresolved_settlement_never_zero():
    f = {"status": "covered", "quiet": True, "signal_time": at("10:30"),
         "atm": 100, "proxy": 100, "straddle": 2, "drift": 1}
    q = pd.concat([snapshot(at("10:29")), snapshot(at("10:30")), snapshot(at("10:32"))])
    result = simulate(q, f, DAY, "atm_quiet", 2, "IRON", None)
    assert result["entry_time"] == at("10:32")
    assert result["status"] == "unresolved_settlement"
    assert "stressed" not in result
    q = pd.concat([snapshot(at("10:29")), snapshot(at("10:30")), snapshot(at("10:33"))])
    assert simulate(q, f, DAY, "atm_quiet", 2, "IRON", 100)["status"] == "excluded_entry"


def test_otm_bodies_strictly_beyond_proxy_even_after_rounding():
    f = {"proxy": 100.4, "straddle": .1, "drift": .1}
    strikes = np.array([99., 100., 101., 102.])
    assert centers_for("otm_pair_quiet", f, strikes) == [100, 101]
    assert centers_for("otm_drift_quiet", f, strikes) == [101]


def test_quiet_features_ignore_all_post_signal_outcomes_and_require_last_minute():
    stamps = pd.date_range(at("09:31"), at("10:29"), freq="min")
    proxy = pd.DataFrame({"timestamp": stamps,
                          "forward_proxy": 100 + .01 * np.sin(np.arange(len(stamps)))})
    q = snapshot(at("10:29"))
    f = features(q, proxy, DAY)
    assert f["status"] == "covered"
    assert f["quiet"] is True
    future = pd.DataFrame({"timestamp": [at("10:30"), at("15:59")],
                           "forward_proxy": [1000, 1]})
    assert features(q, pd.concat([proxy, future]), DAY) == f
    assert features(q, proxy.iloc[:-1], DAY)["status"] == "excluded_prefix"


def test_known_event_day_blocks_quiet_gate():
    day = dt.date(2026, 1, 28)  # published FOMC schedule in versioned calendar
    stamps = pd.date_range(f"{day} 09:31", f"{day} 10:29", freq="min", tz="America/New_York")
    proxy = pd.DataFrame({"timestamp": stamps, "forward_proxy": 100.0})
    f = features(snapshot(stamps[-1]), proxy, day)
    assert "FOMC" in f["event_types"]
    assert f["quiet"] is False


def test_independent_minutes_keep_last_observation_without_filling_gaps():
    times = pd.to_datetime([at("10:28:10"), at("10:28:55"), at("10:30:01")], utc=True)
    ticks = pd.DataFrame({"underlying": ["SPX"] * 3,
                          "ts_us": times.as_unit("us").asi8, "price": [1000, 1001, 1002]})
    result = spx_minutes(ticks)
    assert list(result.timestamp) == [at("10:28"), at("10:30")]
    assert list(result.forward_proxy) == [100.1, 100.2]
    # 10:30 minute is excluded from the decision prefix even though its first tick is early.
    assert len(result[result.timestamp < at("10:30")]) == 1
    with pytest.raises(ValueError, match="Invalid independent"):
        spx_minutes(pd.concat([ticks, ticks.iloc[:1]]))


def test_relative_gate_excludes_warmup_and_does_not_train_on_current_session():
    f = {"status": "covered", "signal_time": at("10:30"), "sigma_forecast": 1.0,
         "proxy": 100., "efficiency": .1, "event_types": [], "quiet": False}
    prior = [.001] * 19
    result, rate = relative_calm(f, prior, DAY)
    assert result["status"] == "excluded_warmup"
    assert result["quiet"] is False
    assert len(prior) == 19
    result, rate = relative_calm(f, prior + [.001], DAY)
    assert result["quiet"] is True
    assert result["prior20_lower_tercile"] == pytest.approx(.001)
    assert relative_calm({**f, "event_types": ["FOMC"]}, prior + [.001], DAY)[0]["quiet"] is False
    # Current observation is not silently inserted into the caller's training history.
    assert len(prior) == 19
