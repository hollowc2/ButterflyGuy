"""Near-tie detection for fly-choice robustness."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.research.tieset import draw_keys, promotion_shift, selector_pool


def _cand(width: int, center: float, cost: float) -> ButterflyCandidate:
    rr = (width - cost) / cost
    return ButterflyCandidate(
        direction="CALL", wing_width=width, center_strike=center, lower_strike=center - width,
        upper_strike=center + width, cost=cost, max_profit=width - cost, reward_risk=rr,
        lower_be=0, upper_be=0, distance_from_spot=0, spot_price=6000,
    )


def test_promotion_shift_is_rr_gap_over_combined_cost_sensitivity():
    winner = _cand(20, 6040, 20 / 11)  # RR exactly 10
    other = _cand(30, 6050, 30 / 12.5)  # RR 11.5
    gap = abs(other.reward_risk - 10) - abs(winner.reward_risk - 10)
    sens = 30 / other.cost**2 + 20 / winner.cost**2
    assert promotion_shift(other, winner, 10.0) == pytest.approx(gap / sens)
    assert promotion_shift(winner, winner, 10.0) == 0.0
    # A shift of about 0.23 points separates them: inside the $0.25 tie set, not $0.10.
    assert 0.10 < promotion_shift(other, winner, 10.0) < 0.25


def test_selector_pool_applies_center_tolerance_and_rr_max_per_width():
    cands = [_cand(20, 6040, 1.8), _cand(20, 6100, 1.8), _cand(30, 6060, 2.5),
             _cand(30, 6060 + 5, 1.0)]  # RR 29: removed by rr_max while others remain
    pool = selector_pool(cands, vix=18.0, spot=6000.0, direction="CALL", widths=(20, 30),
                         sigmas=(0.5, 0.75), center_tolerance=15.0, rr_max=12.0)
    centers = sorted((c.wing_width, c.center_strike) for c in pool)
    assert centers == [(20, 6040.0), (30, 6060.0)]


def test_draws_are_keyed_by_session_and_direction():
    d = dt.date(2026, 6, 10)
    assert np.array_equal(draw_keys(d, "CALL", 100, 7), draw_keys(d, "CALL", 100, 7))
    assert not np.array_equal(draw_keys(d, "CALL", 100, 7), draw_keys(d, "PUT", 100, 7))


def test_run_scores_tie_sets_unless_told_not_to():
    from butterfly_guy.research.cli import build_parser

    assert build_parser().parse_args(["run", "--variants", "E0"]).no_tieset is False
    assert build_parser().parse_args(["run", "--variants", "E0", "--no-tieset"]).no_tieset


def _session(snapshot_ts, clock_ts, clock_spot, vix_by_ts):
    from types import SimpleNamespace

    def vix_at_or_before(ts, max_age_s=None):
        known = [t for t in vix_by_ts if t <= ts]
        return (vix_by_ts[max(known)], max(known)) if known else None

    return SimpleNamespace(
        market=SimpleNamespace(ts=np.array(snapshot_ts)),
        clock_ts=np.array(clock_ts), clock_spot=np.array(clock_spot),
        clock_index=lambda ts: int(np.searchsorted(np.array(clock_ts), ts, side="right")) - 1,
        vix=SimpleNamespace(at_or_before=vix_at_or_before),
    )


def _entry(index):
    from butterfly_guy.research.entry import Entry
    from butterfly_guy.research.market import Fly

    cand = _cand(20, 6040, 1.8)
    return Entry(Fly.from_candidate(cand), 200, index, cand.cost, "CALL", vix=18.0,
                 spot=6000.0, candidate=cand)


def test_neighbor_entry_uses_the_neighbor_snapshot_spot_and_vix():
    from types import SimpleNamespace

    from butterfly_guy.research.tieset import neighbor_entry

    s = _session([100, 200, 300], [50, 150, 250, 350], [5990.0, 5995.0, 6000.0, 6010.0],
                 {100: 17.0, 300: 19.0})
    ctx = SimpleNamespace(max_vix_age_s=None)
    e = _entry(1)
    assert neighbor_entry(s, ctx, e, 0) is e
    before, after = neighbor_entry(s, ctx, e, -1), neighbor_entry(s, ctx, e, 1)
    assert (before.ts_us, before.index, before.spot, before.vix) == (100, 0, 5990.0, 17.0)
    assert (after.ts_us, after.index, after.spot, after.vix) == (300, 2, 6000.0, 19.0)
    assert after.candidate is e.candidate
    assert neighbor_entry(s, ctx, _entry(2), 1) is None  # past the last snapshot


def test_neighbor_entry_needs_a_vix_and_clamps_spot_before_the_first_clock_tick():
    from types import SimpleNamespace

    from butterfly_guy.research.tieset import neighbor_entry

    ctx = SimpleNamespace(max_vix_age_s=None)
    s = _session([100, 200], [150, 250], [6000.0, 6010.0], {200: 18.0})
    assert neighbor_entry(s, ctx, _entry(1), -1) is None  # no VIX at or before 100
    s = _session([100, 200], [150, 250], [6000.0, 6010.0], {50: 18.0})
    assert neighbor_entry(s, ctx, _entry(1), -1).spot == 6000.0  # not the last clock spot


def test_two_stage_pick_with_one_neighbor_matches_the_single_stage_draw():
    from butterfly_guy.research.tieset import two_stage_pick

    d = dt.date(2026, 6, 10)
    pnl = np.array([-100.0, 50.0, 900.0])
    u = draw_keys(d, "CALL", 1000, 7)
    single = pnl[np.minimum((u * len(pnl)).astype(int), len(pnl) - 1)]
    assert np.array_equal(two_stage_pick([pnl], draw_keys(d, "CALL:neighbor", 1000, 7), u),
                          single)


def test_two_stage_pick_chooses_the_neighbor_then_its_fly():
    from butterfly_guy.research.tieset import two_stage_pick

    picks = two_stage_pick([np.array([1.0]), np.array([2.0, 3.0])],
                           np.array([0.1, 0.9, 0.9]), np.array([0.9, 0.1, 0.9]))
    assert picks.tolist() == [1.0, 2.0, 3.0]


def test_neighbor_rows_average_neighbors_equally_and_leave_base_rows_alone():
    from butterfly_guy.research.tieset import TiesetScorer

    d = dt.date(2026, 6, 10)
    scorer = TiesetScorer(thresholds=(0.10,), draws=200, neighbors=(-1, 0, 1))
    scorer.rows[("E0", 0.10)] = [(d, "CALL", {"stressed": np.array([100.0])})]
    scorer.neighbor_rows[("E0", 0.10)] = [(d, "CALL", {"stressed": [
        np.array([100.0]), np.array([0.0, 300.0])]})]
    out = scorer.summary(["E0"], [d])["E0"]
    assert out["0.10"]["stressed"]["tieset_avg"] == 100.0
    nbr = out["nbr 0.10"]
    assert nbr["stressed"]["tieset_avg"] == 125.0  # mean of 100 and mean(0, 300)
    assert (nbr["mean_neighbors"], nbr["mean_tie_size"]) == (2.0, 3.0)


def test_neighbor_offsets_are_recorded_only_when_set():
    from butterfly_guy.research.tieset import NEIGHBOR_OFFSETS, TiesetScorer

    assert "neighbor_offsets" not in TiesetScorer().params()
    assert TiesetScorer(neighbors=NEIGHBOR_OFFSETS).params()["neighbor_offsets"] == [-1, 0, 1]
