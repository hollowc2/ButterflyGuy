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
