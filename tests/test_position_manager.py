"""Tests for butterfly position valuation helpers."""

from __future__ import annotations

from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.position.position_manager import fly_settlement_value


def make_candidate(direction: str = "PUT") -> ButterflyCandidate:
    return ButterflyCandidate(
        direction=direction,
        wing_width=50,
        center_strike=29120.0,
        lower_strike=29070.0,
        upper_strike=29170.0,
        cost=4.23,
        max_profit=45.77,
        reward_risk=10.8,
        lower_be=29065.0,
        upper_be=29175.0,
        distance_from_spot=100.0,
        spot_price=29221.08,
    )


def test_put_butterfly_settles_to_intrinsic_with_spot_above_all_strikes():
    candidate = make_candidate("PUT")

    assert fly_settlement_value(candidate, 29313.12) == 0.0


def test_call_butterfly_settles_to_intrinsic_with_spot_below_all_strikes():
    candidate = make_candidate("CALL")

    assert fly_settlement_value(candidate, 28900.0) == 0.0


def test_settlement_value_respects_tent_value_inside_the_body():
    candidate = make_candidate("PUT")

    assert fly_settlement_value(candidate, 29120.0) == 50.0
