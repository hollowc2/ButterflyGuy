from types import SimpleNamespace

import numpy as np
import pandas as pd

from butterfly_guy.research.exits import PeakTrailer
from tools.research_studies.monitor_replay_study import (
    PRIMARY,
    Arm,
    causal_median,
    confirm,
    decide,
    exit_prices,
    post_exit_covered,
    select_arm,
    subsample,
)

S = 1_000_000  # microseconds per second
RULE = PeakTrailer(morning=0.60, late_morning=0.60, afternoon=0.60)


def run(marks, arm, step=2.5, entry=2.0):
    ts = np.arange(len(marks)) * int(step * S) + 600 * S  # 10 minutes after the open
    marks = np.asarray(marks, float)
    return decide(ts, marks, marks - 0.2, entry=entry, entry_us=0, open_us=0,
                  close_us=10**12, rule=RULE, arm=arm)


def test_current_rule_exits_on_first_breach():
    hit = run([2.0, 5.0, 4.0, 1.9, 1.9, 1.9], Arm())
    assert hit["reason"] == "drawdown_morning"
    assert hit["ts_us"] == 600 * S + 3 * int(2.5 * S)


def test_time_confirmation_waits_and_resets_when_value_recovers():
    # breach at poll 3, recovers at 4, breaches again at 5 and holds
    marks = [2.0, 5.0, 4.0, 1.9, 3.0, 1.9, 1.9, 1.9, 1.9, 1.9]
    hit = run(marks, Arm(confirm_seconds=10))
    first_breach = 600 * S + 5 * int(2.5 * S)
    assert hit["ts_us"] == first_breach + 10 * S


def test_time_confirmation_holds_through_a_one_poll_dip():
    assert run([2.0, 5.0, 4.0, 1.9, 4.0, 4.0], Arm(confirm_seconds=5)) is None


def test_quality_peak_ignores_a_one_poll_spike():
    # raw peak 7.0 makes 3.0 a 57% drawdown... at 0.60 no exit; 2.5 is 64% -> exit raw
    marks = [2.0, 4.0, 4.0, 7.0, 4.0, 4.0, 2.5]
    assert run(marks, Arm())["peak"] == 7.0
    assert run(marks, Arm(peak_window_seconds=10)) is None


def test_exit_is_priced_at_the_raw_mark_not_the_smoothed_value():
    marks = [2.0, 5.0, 5.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    hit = run(marks, Arm(value_window_seconds=10))
    assert hit is not None and hit["value"] == 1.0


def test_subsample_keeps_polls_at_least_the_cadence_apart():
    ts = np.array([0, 2, 4, 6, 9, 10, 12]) * S
    assert subsample(ts, 5).tolist() == [True, False, False, True, False, False, True]


def test_causal_median_uses_only_the_trailing_window():
    ts = np.array([0, 2, 4, 6, 20]) * S
    out = causal_median(ts, np.array([1.0, 9.0, 1.0, 1.0, 5.0]), 5)
    assert out.tolist() == [1.0, 5.0, 1.0, 1.0, 5.0]


def test_ladder_price_is_natural_plus_offset_capped_at_mid():
    assert exit_prices(1.85, 1.00) == {"mid": 1.85, "natural": 1.00, "ladder": 1.30}
    assert exit_prices(1.10, 1.00)["ladder"] == 1.10
    assert exit_prices(0.30, -0.40)["ladder"] == 0.05


def _summary(**means):
    return {a: {k: {"mean": means.get(a, -1.0)} for k in ("mid", "natural", "ladder")}
            for a in PRIMARY}


def test_selection_needs_every_price_non_negative_and_picks_best_ladder_mean():
    s = _summary(C1=2.0, C2=5.0)
    s["C2"]["natural"]["mean"] = -0.1
    assert select_arm(s) == "C1"
    assert select_arm(_summary()) is None


def test_confirmation_rule():
    ok = {"ladder": {"mean": 1.0, "lower90_one_sided": -19.0, "worst": -250.0},
          "natural": {"mean": 0.5}}
    assert confirm(ok)["adopt"] is True
    bad = {**ok, "ladder": {**ok["ladder"], "lower90_one_sided": -21.0}}
    assert confirm(bad)["adopt"] is False


def test_post_exit_coverage_rejects_gaps_and_early_stops():
    tr = SimpleNamespace(exit_reason="drawdown_morning",
                         exit_time=pd.Timestamp("2026-11-17 15:00:00", tz="UTC"),
                         entry_time=pd.Timestamp("2026-11-17 14:30:00", tz="UTC"))
    close = pd.Timestamp("2026-11-17 21:00:00", tz="UTC")
    full = pd.DataFrame({"ts": pd.date_range(tr.exit_time + pd.Timedelta(seconds=3),
                                             close, freq="3s")})
    assert post_exit_covered(tr, full)
    assert not post_exit_covered(tr, full.drop(index=range(100, 120)))
    assert not post_exit_covered(tr, full.iloc[:-100])
    assert post_exit_covered(SimpleNamespace(exit_reason="cash_settled"), full.iloc[0:0])
