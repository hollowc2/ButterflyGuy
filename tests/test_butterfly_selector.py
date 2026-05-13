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


def test_vix_farthest_otm_ignores_rr_target_after_builder_price_filters():
    selector = ButterflySelector(StrategySettings(rr_target=10.0, rr_max=12.0))
    candidates = [
        make_candidate(center=29220, distance=152.7, reward_risk=11.65),
        make_candidate(center=29270, distance=202.7, reward_risk=16.54),
        make_candidate(center=29310, distance=242.7, reward_risk=16.54),
    ]

    best = selector.select_farthest_otm(
        candidates,
        target_center=29235,
        center_tolerance=100,
    )

    assert best is not None
    assert best.center_strike == 29310


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
