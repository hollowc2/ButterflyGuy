"""Tests for the butterfly builder scanner."""

import datetime as dt

from butterfly_guy.core.config import StrategySettings, VixWidthBucket
from butterfly_guy.data.schemas import OptionQuote
from butterfly_guy.strategy.butterfly_builder import (
    ButterflyBuilder,
    resolve_wing_widths_for_vix,
    vix_target_center,
)


def make_quote(strike: float, option_type: str, mark: float) -> OptionQuote:
    return OptionQuote(
        symbol=f"SPX_{option_type[0]}{int(strike)}",
        underlying="SPX",
        expiration=dt.date.today(),
        strike=strike,
        option_type=option_type,  # type: ignore
        bid=mark - 0.10,
        ask=mark + 0.10,
        mark=mark,
    )


def make_chain(spot: float = 5500.0, step: float = 5.0, n: int = 30) -> list[OptionQuote]:
    """Generate a synthetic chain of call quotes around spot."""
    quotes = []
    for i in range(-n, n + 1):
        strike = spot + i * step
        # Simulate realistic marks: ATM has highest time value
        distance = abs(i) * step
        intrinsic_c = max(0, spot - strike)
        time_val = max(0.05, 2.0 - distance * 0.02)
        call_mark = intrinsic_c + time_val

        intrinsic_p = max(0, strike - spot)
        put_mark = intrinsic_p + time_val

        quotes.append(make_quote(strike, "CALL", call_mark))
        quotes.append(make_quote(strike, "PUT", put_mark))
    return quotes


def test_builder_finds_candidates():
    settings = StrategySettings(
        wing_widths=[5, 10],
        spot_range=40,
        rr_min=1.0,  # low threshold for test
        max_cost_per_width={5: 10.0, 10: 10.0},
    )
    builder = ButterflyBuilder(settings)
    quotes = make_chain(spot=5500.0)
    candidates = builder.build_candidates(quotes, 5500.0, "CALL")
    assert len(candidates) > 0


def test_builder_filters_by_spot_range():
    settings = StrategySettings(
        wing_widths=[5],
        spot_range=10,  # tight range
        rr_min=0.5,
        max_cost_per_width={5: 10.0},
    )
    builder = ButterflyBuilder(settings)
    quotes = make_chain(spot=5500.0, step=5.0, n=50)
    candidates = builder.build_candidates(quotes, 5500.0, "CALL")
    # All centers should be within 10 pts of spot
    for c in candidates:
        assert abs(c.center_strike - 5500.0) <= 10


def test_builder_sorted_by_distance():
    settings = StrategySettings(
        wing_widths=[5, 10],
        spot_range=40,
        rr_min=0.5,
        max_cost_per_width={5: 10.0, 10: 10.0},
    )
    builder = ButterflyBuilder(settings)
    quotes = make_chain(spot=5500.0)
    candidates = builder.build_candidates(quotes, 5500.0, "CALL")
    distances = [c.distance_from_spot for c in candidates]
    assert distances == sorted(distances)


def test_builder_rr_filter():
    settings = StrategySettings(
        wing_widths=[5],
        spot_range=50,
        rr_min=100.0,  # impossibly high
        max_cost_per_width={5: 10.0},
    )
    builder = ButterflyBuilder(settings)
    quotes = make_chain(spot=5500.0)
    candidates = builder.build_candidates(quotes, 5500.0, "CALL")
    assert len(candidates) == 0


def test_builder_cost_filter():
    settings = StrategySettings(
        wing_widths=[5],
        spot_range=50,
        rr_min=0.1,
        max_cost_per_width={5: 0.001},  # impossibly low cost limit
    )
    builder = ButterflyBuilder(settings)
    quotes = make_chain(spot=5500.0)
    candidates = builder.build_candidates(quotes, 5500.0, "CALL")
    assert len(candidates) == 0


def test_builder_respects_configured_min_debit():
    settings = StrategySettings(
        wing_widths=[5],
        spot_range=50,
        min_debit=0.25,
        rr_min=0.1,
        max_cost_per_width={5: 10.0},
    )
    builder = ButterflyBuilder(settings)
    quotes = [
        make_quote(5500, "CALL", 1.0),
        make_quote(5505, "CALL", 0.5),
        make_quote(5510, "CALL", 0.1),
    ]

    candidates = builder.build_candidates(quotes, 5500.0, "CALL")

    assert candidates == []


def test_builder_cost_positive():
    settings = StrategySettings(
        wing_widths=[5, 10],
        spot_range=40,
        rr_min=0.5,
        max_cost_per_width={5: 10.0, 10: 10.0},
    )
    builder = ButterflyBuilder(settings)
    quotes = make_chain(spot=5500.0)
    candidates = builder.build_candidates(quotes, 5500.0, "CALL")
    for c in candidates:
        assert c.cost > 0


def test_builder_breakevens_valid():
    settings = StrategySettings(
        wing_widths=[10],
        spot_range=40,
        rr_min=0.5,
        max_cost_per_width={10: 10.0},
    )
    builder = ButterflyBuilder(settings)
    quotes = make_chain(spot=5500.0)
    candidates = builder.build_candidates(quotes, 5500.0, "CALL")
    for c in candidates:
        assert c.lower_be > c.lower_strike
        assert c.upper_be < c.upper_strike
        assert c.lower_be < c.center_strike
        assert c.upper_be > c.center_strike


def test_vix_target_uses_width_for_strike_step_when_sigma_is_explicit():
    target = vix_target_center(
        vix=18.0,
        spot=739.2,
        direction="CALL",
        wing_width=3,
        sigma_fraction=0.25,
    )

    assert target == 741


def test_two_width_vix_bucket_spans_narrow_and_wide_sigmas():
    widths, sigmas = resolve_wing_widths_for_vix(
        18.0,
        [
            VixWidthBucket(vix_max=17.0, widths=[2, 3]),
            VixWidthBucket(vix_max=24.5, widths=[3, 4]),
        ],
    )

    assert widths == [3, 4]
    assert sigmas == (0.25, 0.75)
