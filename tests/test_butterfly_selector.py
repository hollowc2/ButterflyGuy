"""Tests for butterfly candidate selection."""

from butterfly_guy.core.config import StrategySettings
from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.strategy.butterfly_selector import ButterflySelector


def make_candidate(
    center: float,
    distance: float,
    reward_risk: float,
    cost: float = 3.0,
    wing_width: int = 50,
) -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="CALL",
        wing_width=wing_width,
        center_strike=center,
        lower_strike=center - wing_width,
        upper_strike=center + wing_width,
        cost=cost,
        max_profit=wing_width - cost,
        reward_risk=reward_risk,
        lower_be=center - wing_width + cost,
        upper_be=center + wing_width - cost,
        distance_from_spot=distance,
        spot_price=center - distance,
    )


def test_vix_centered_selection_uses_rr_target_after_center_filter():
    selector = ButterflySelector(StrategySettings(rr_target=10.0, rr_max=12.0))
    candidates = [
        make_candidate(center=29220, distance=152.7, reward_risk=11.65),
        make_candidate(center=29270, distance=202.7, reward_risk=16.54),
        make_candidate(center=29310, distance=242.7, reward_risk=16.54),
    ]

    best = selector.select_best(
        candidates,
        target_center=29235,
        center_tolerance=100,
    )

    assert best is not None
    assert best.center_strike == 29220


def test_regular_best_rr_selection_still_uses_rr_target():
    selector = ButterflySelector(StrategySettings(rr_target=10.0, rr_max=12.0))
    candidates = [
        make_candidate(center=29220, distance=152.7, reward_risk=11.65),
        make_candidate(center=29310, distance=242.7, reward_risk=16.54),
    ]

    best = selector.select_best(
        candidates,
        target_center=29235,
        center_tolerance=100,
    )

    assert best is not None
    assert best.center_strike == 29220


def test_vix_selection_rejects_cheap_extreme_rr_tail_candidate():
    selector = ButterflySelector(StrategySettings(rr_target=10.0, rr_max=12.0))
    candidates = [
        make_candidate(
            center=7530,
            distance=64.55,
            reward_risk=11.0968,
            cost=2.48,
            wing_width=30,
        ),
        make_candidate(
            center=7565,
            distance=99.55,
            reward_risk=108.375,
            cost=0.32,
            wing_width=35,
        ),
    ]

    best = selector.select_best(
        candidates,
        target_center=7565,
        center_tolerance=40,
    )

    assert best is not None
    assert best.center_strike == 7530
    assert best.wing_width == 30


def test_vix_centered_selection_blocks_when_no_candidate_near_target():
    selector = ButterflySelector(StrategySettings(rr_target=10.0, rr_max=12.0))
    candidates = [
        make_candidate(center=29220, distance=152.7, reward_risk=11.65),
    ]

    best = selector.select_best(
        candidates,
        target_center=29400,
        center_tolerance=15,
    )

    assert best is None
