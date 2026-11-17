import numpy as np
import pandas as pd
import pytest

from butterfly_guy.core.exit_pricing import exit_limit
from butterfly_guy.research import exit_pricing as ep

KW = dict(ladder_step=0.10, ladder_steps=4, underlying="SPX")


@pytest.mark.parametrize("name", ["R2", "R3", "R1"])
def test_candidates_offer_the_natural_no_later_than_today(name):
    """Plan criterion 5: the first step priced at the bid comes no later than R0's."""

    def first_natural_seconds(c):
        for step in range(20):
            if exit_limit(c.rule, step, 1.00, 1.90, **KW) == 1.00:
                return step * c.interval
        raise AssertionError

    assert first_natural_seconds(ep.CANDIDATES[name]) <= first_natural_seconds(
        ep.CANDIDATES["R0"]
    )


def _static(bid, mid, end=120.0):
    t = np.arange(0.0, end + 1e-9, 2.5)
    return ep.Path(t=t, bid=np.full_like(t, bid), mid=np.full_like(t, mid))


def test_static_narrow_spread_today_waits_forty_seconds_for_mid():
    path = _static(1.00, 1.10)
    r0 = ep.simulate(path, ep.CANDIDATES["R0"], 1.0, horizon=90)
    assert r0.limits[:4] == (1.30, 1.20, 1.10, 1.00)
    assert r0.expected_credit == pytest.approx(1.10) and r0.expected_fill_seconds == 40
    r2 = ep.simulate(path, ep.CANDIDATES["R2"], 1.0, horizon=90)
    assert r2.expected_credit == pytest.approx(1.10) and r2.expected_fill_seconds == 0


def test_touch_model_fills_only_at_the_bid():
    r0 = ep.simulate(_static(1.00, 1.10), ep.CANDIDATES["R0"], 0.0, horizon=90)
    assert r0.expected_credit == pytest.approx(1.00) and r0.expected_fill_seconds == 60


def test_partial_probability_compounds_across_steps():
    # mid_walk at 20 s on bid 1.00 / mid 1.90: limits 1.90, 1.60, 1.30, 1.00.
    out = ep.simulate(_static(1.00, 1.90), ep.CANDIDATES["R3"], 0.5, horizon=90)
    # 1.90 at mid (p 0.5); 1.60 and 1.30 above the bid and below mid (no mid touch: mid 1.90
    # >= them, so p 0.5 each); 1.00 certain.
    expected = 0.5 * 1.90 + 0.25 * 1.60 + 0.125 * 1.30 + 0.125 * 1.00
    assert out.expected_credit == pytest.approx(expected)
    assert out.p_filled == pytest.approx(1.0)


def test_unfilled_remainder_is_valued_at_the_bid_at_the_horizon():
    t = np.array([0.0, 30.0, 60.0, 90.0])
    path = ep.Path(t=t, bid=np.array([1.0, 0.6, 0.4, 0.2]), mid=np.array([1.1, 0.7, 0.5, 0.3]))
    out = ep.simulate(path, ep.CANDIDATES["R0"], 0.0, horizon=90)
    assert out.p_filled == 0.0 and out.expected_credit == pytest.approx(0.2)


def test_later_bid_rise_fills_a_resting_limit():
    t = np.array([0.0, 5.0, 25.0])
    path = ep.Path(t=t, bid=np.array([1.0, 1.35, 1.35]), mid=np.array([1.1, 1.45, 1.45]))
    out = ep.simulate(path, ep.CANDIDATES["R0"], 0.0, horizon=20)
    assert out.expected_credit == pytest.approx(1.30) and out.expected_fill_seconds == 5


def test_fly_quotes_and_stand_in_signals():
    trades = pd.DataFrame({"id": [1], "lower_strike": [100.0], "center_strike": [110.0],
                           "upper_strike": [120.0]})
    ts = pd.date_range("2026-08-03 14:00", periods=200, freq="3s", tz="UTC")
    dd = np.r_[np.full(10, 10.0), np.full(20, 35.0), np.full(10, 10.0), np.full(160, 40.0)]
    rows = []
    for k, t in enumerate(ts):
        for strike, bid, ask in ((100.0, 5.0, 5.2), (110.0, 2.0, 2.1), (120.0, 0.5, 0.6)):
            rows.append({"trade_id": 1, "ts": t, "strike": strike, "bid": bid, "ask": ask,
                         "drawdown_pct": dd[k]})
    flies = ep.fly_quotes(pd.DataFrame(rows), trades)
    assert flies.bid.iloc[0] == pytest.approx(5.0 + 0.5 - 4.2)
    assert flies.ask.iloc[0] == pytest.approx(5.2 + 0.6 - 4.0)
    sig = ep.stand_in_signals(flies)
    # crossings at polls 10 and 40 (90 s apart, inside the 300 s spacing) -> one signal
    assert list(sig.ts) == [ts[10]]
    path = ep.path_from(flies, ts[10])
    assert path.t[0] == 0 and path.t[1] == 3


def test_summary_and_selection():
    dates = ["2026-08-03", "2026-08-03", "2026-08-04"] * 10
    s = ep.summarize(dates, [1.0, 3.0, 2.0] * 10, reps=200)
    assert s.mean == pytest.approx(2.0) and s.n_sessions == 2 and s.worst == 1.0
    assert ep.select({"R1": 5.0, "R3": 4.5}) == "R3"
    assert ep.select({"R1": 5.0, "R3": 3.0}) == "R1"
    assert ep.select({}) is None


@pytest.mark.parametrize("name", list(ep.CANDIDATES))
@pytest.mark.parametrize("p_mid", [0.0, 0.5, 1.0])
@pytest.mark.parametrize(("bid", "mid"), [(1.00, 1.10), (1.00, 1.85), (1.02, 1.13), (2.30, 2.30)])
def test_replay_on_a_static_quote_equals_the_paper_live_rule_estimate(name, p_mid, bid, mid):
    """Research/live parity: the paper exit's live-rule estimate is the replay on one quote."""
    from butterfly_guy.core.exit_pricing import static_quote_estimate

    cand = ep.CANDIDATES[name]
    one_pass = ep.LADDER_STEPS * cand.interval
    replay = ep.simulate(_static(bid, mid, end=one_pass), cand, p_mid, horizon=one_pass)
    assert replay.expected_credit == pytest.approx(static_quote_estimate(
        cand.rule, bid, mid, p_mid=p_mid, ladder_step=ep.LADDER_STEP,
        ladder_steps=ep.LADDER_STEPS, underlying="SPX",
    ))
