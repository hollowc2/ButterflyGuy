"""Tests for butterfly position valuation helpers."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.core.config import (
    PeakTrackingSettings,
    ProfitManagementSettings,
    QuoteQualitySettings,
)
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.position.position_manager import PositionManager, fly_settlement_value


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


def make_xsp_candidate() -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="PUT",
        wing_width=3,
        center_strike=740.0,
        lower_strike=737.0,
        upper_strike=743.0,
        cost=0.25,
        max_profit=2.75,
        reward_risk=11.0,
        lower_be=737.25,
        upper_be=742.75,
        distance_from_spot=3.0,
        spot_price=743.0,
    )


def make_quote(
    strike: float,
    mark: float,
    bid: float | None = None,
    ask: float | None = None,
) -> OptionQuote:
    return OptionQuote(
        symbol=f"XSP{strike}",
        underlying="XSP",
        expiration=dt.date(2026, 6, 19),
        strike=strike,
        option_type="PUT",
        bid=mark if bid is None else bid,
        ask=mark if ask is None else ask,
        mark=mark,
    )


def quote_map(mark_value: float) -> dict[float, OptionQuote]:
    return {
        737.0: make_quote(737.0, 1.0),
        740.0: make_quote(740.0, 0.5),
        743.0: make_quote(743.0, mark_value),
    }


def test_put_butterfly_settles_to_intrinsic_with_spot_above_all_strikes():
    candidate = make_candidate("PUT")

    assert fly_settlement_value(candidate, 29313.12) == 0.0


def test_call_butterfly_settles_to_intrinsic_with_spot_below_all_strikes():
    candidate = make_candidate("CALL")

    assert fly_settlement_value(candidate, 28900.0) == 0.0


def test_settlement_value_respects_tent_value_inside_the_body():
    candidate = make_candidate("PUT")

    assert fly_settlement_value(candidate, 29120.0) == 50.0


def test_peak_tracking_requires_confirming_polls():
    settings = ProfitManagementSettings(
        peak_tracking=PeakTrackingSettings(confirmation_polls=2)
    )
    manager = PositionManager("XSP", settings)
    manager.reset(entry_price=0.25)
    candidate = make_xsp_candidate()

    first = manager.update_position_value(candidate, quote_map(0.4))
    second = manager.update_position_value(candidate, quote_map(0.41))

    assert first.peak_value == 0.25
    assert first.peak_update_rejected is True
    assert first.peak_rejection_reason == "pending_confirmation"
    assert second.peak_value == 0.41


def test_peak_tracking_rejects_bad_quote_quality():
    settings = ProfitManagementSettings(
        quote_quality=QuoteQualitySettings(
            enabled=True,
            min_bid_to_mark_ratio=0.75,
            max_spread_width_ratio=0.50,
        ),
        peak_tracking=PeakTrackingSettings(
            confirmation_polls=1,
            require_quote_quality=True,
        ),
    )
    manager = PositionManager("XSP", settings)
    manager.reset(entry_price=0.25)
    candidate = make_xsp_candidate()
    bad_quotes = {
        737.0: make_quote(737.0, 1.0, bid=1.0, ask=1.0),
        740.0: make_quote(740.0, 0.5, bid=0.1, ask=0.9),
        743.0: make_quote(743.0, 0.4, bid=0.4, ask=0.4),
    }

    state = manager.update_position_value(candidate, bad_quotes)

    assert state.current_value == 0.4
    assert state.peak_value == 0.25
    assert state.peak_update_rejected is True
    assert state.peak_rejection_reason == "quote_quality"
