from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.strategy.width_selection import select_cross_width_candidate


def _candidate(width: int, rr: float) -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="PUT",
        wing_width=width,
        center_strike=float(width * 10),
        lower_strike=float(width * 10 - width),
        upper_strike=float(width * 10 + width),
        cost=1.0,
        max_profit=10.0,
        reward_risk=rr,
        lower_be=0.0,
        upper_be=0.0,
        distance_from_spot=0.0,
        spot_price=0.0,
    )


def test_cross_width_selection_can_prefer_first_bucket_width():
    best = select_cross_width_candidate(
        [_candidate(2, 12.0), _candidate(4, 9.0)],
        prefer_first_width=True,
    )

    assert best is not None
    assert best.wing_width == 2


def test_cross_width_selection_returns_none_for_empty_pool():
    assert select_cross_width_candidate([], prefer_first_width=True) is None
