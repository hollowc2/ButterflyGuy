"""O(N*W) butterfly construction and scoring engine."""

from __future__ import annotations

import math
from typing import Literal

from butterfly_guy.core.config import StrategySettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, fly_mark_value

log = get_logger(__name__)

# Fraction of the expected daily move used to derive wing width.
# 0.15 calibrated so that:
#   VIX ~15  → ~10-wide   (low-vol, tight tent)
#   VIX ~20  → ~10-wide
#   VIX ~25  → ~15 → snaps to 20-wide
#   VIX ~35  → ~20-wide
#   VIX ~50  → ~30-wide
_TRADING_DAYS_PER_YEAR = 252

# Per-width sigma fractions for VIX-anchored center placement.
# Wider wings need to be placed further OTM to remain cost-effective and
# to capture the large moves required for the tent to be hit.
#   10-wide: close to ATM — cheap, profits from small OTM drifts
#   20-wide: moderate OTM — mid-range move required
#   30-wide: further OTM — needs a bigger push, but pays ~3x a 10-wide when it hits
VIX_SIGMA_BY_WIDTH: dict[int, float] = {
    10: 0.25,
    20: 0.50,
    30: 0.75,
    25: 0.25,  # NDX narrow
    50: 0.50,  # NDX mid
    75: 0.75,  # NDX wide
    1: 0.25,   # XSP narrow
    2: 0.50,   # XSP mid
    3: 0.75,   # XSP wide
}
_VIX_SIGMA_DEFAULT = 0.50  # fallback for unlisted widths
_BUCKET_SIGMAS = (0.25, 0.50, 0.75)  # narrow / mid / wide within any VIX bucket


def _bucket_sigmas(width_count: int) -> tuple[float, ...]:
    """Return sigma anchors spanning narrow to wide for the bucket size."""
    if width_count <= 0:
        return ()
    if width_count == 1:
        return (_VIX_SIGMA_DEFAULT,)
    if width_count == len(_BUCKET_SIGMAS):
        return _BUCKET_SIGMAS

    first = _BUCKET_SIGMAS[0]
    last = _BUCKET_SIGMAS[-1]
    step = (last - first) / (width_count - 1)
    return tuple(first + step * i for i in range(width_count))


def resolve_wing_widths_for_vix(vix: float, buckets: list) -> tuple[list[int], tuple[float, ...]]:
    """Return (widths, sigma_fractions) for the active VIX bucket.

    Buckets are processed in ascending vix_max order; first match wins.
    Sigma fractions are positional so that a width like 30 can be "wide" (0.75) in a
    low-VIX bucket and "narrow" (0.25) in a higher-VIX bucket without ambiguity.
    """
    for bucket in sorted(buckets, key=lambda b: b.vix_max):
        if vix < bucket.vix_max:
            return bucket.widths, _bucket_sigmas(len(bucket.widths))
    return buckets[-1].widths, _bucket_sigmas(len(buckets[-1].widths))


def vix_expected_move(vix: float, spot: float) -> float:
    """Return the expected 1-sigma daily SPX move implied by VIX."""
    return spot * (vix / 100) / math.sqrt(_TRADING_DAYS_PER_YEAR)


def vix_target_center(
    vix: float,
    spot: float,
    direction: str,
    wing_width: int | None = None,
    sigma_fraction: float | None = None,
    strike_step: int | None = None,
) -> float:
    """Derive the ideal center strike from VIX.

    Places the center at `sigma_fraction` × expected_daily_move above spot
    (CALL) or below spot (PUT), rounded to the nearest strike_step.

    Sigma fraction is resolved in this order:
      1. Explicit `sigma_fraction` argument
      2. `VIX_SIGMA_BY_WIDTH[wing_width]` lookup
      3. `_VIX_SIGMA_DEFAULT` fallback

    Args:
        vix: Current VIX level.
        spot: Current SPX spot price.
        direction: "CALL" or "PUT".
        wing_width: Wing width to look up sigma in VIX_SIGMA_BY_WIDTH.
        sigma_fraction: Override sigma directly (takes precedence over wing_width).
        strike_step: Round center to this increment (defaults to 1 for widths <=5, else 5).

    Returns:
        Target center strike as a float.
    """
    if sigma_fraction is None:
        sigma_fraction = VIX_SIGMA_BY_WIDTH.get(wing_width, _VIX_SIGMA_DEFAULT) \
            if wing_width is not None else _VIX_SIGMA_DEFAULT

    if strike_step is None:
        strike_step = 1 if wing_width is not None and wing_width <= 5 else 5

    move = vix_expected_move(vix, spot)
    offset = move * sigma_fraction
    raw = (spot + offset) if direction == "CALL" else (spot - offset)
    return round(raw / strike_step) * strike_step


class ButterflyBuilder:
    """Builds and scores butterfly spreads from an option chain snapshot."""

    def __init__(self, settings: StrategySettings) -> None:
        self.settings = settings

    def build_candidates(
        self,
        quotes: list[OptionQuote],
        spot_price: float,
        direction: Literal["CALL", "PUT"],
        include_all: bool = False,
    ) -> list[ButterflyCandidate]:
        """
        O(N*W) scan: for each center strike within spot_range, for each wing_width,
        construct a butterfly and filter by cost/RR.
        """
        # Build strike → quote lookup for the given direction
        by_strike: dict[float, OptionQuote] = {}
        for q in quotes:
            if q.option_type == direction:
                by_strike[q.strike] = q

        strikes = sorted(by_strike.keys())
        strike_set = set(strikes)
        candidates: list[ButterflyCandidate] = []

        for center in strikes:
            if abs(center - spot_price) > self.settings.spot_range:
                continue
            # For CALL flies the center must be OTM (above spot);
            # for PUT flies the center must be OTM (below spot).
            if direction == "CALL" and center <= spot_price:
                continue
            if direction == "PUT" and center >= spot_price:
                continue

            for width in self.settings.wing_widths:
                lower = center - width
                upper = center + width

                if lower not in strike_set or upper not in strike_set:
                    continue

                lower_q = by_strike[lower]
                center_q = by_strike[center]
                upper_q = by_strike[upper]

                # Butterfly cost: buy lower + buy upper - 2 * sell center (using mark)
                cost = fly_mark_value(lower_q, center_q, upper_q)
                # Fly ask: real market cost hitting the spread.
                fly_ask = lower_q.ask + upper_q.ask - 2 * center_q.bid

                if cost < 0.05:  # minimum practical butterfly debit; filters fp-epsilon zeros
                    if not include_all:
                        continue

                max_cost = self.settings.max_cost_per_width.get(width, float("inf"))
                if not include_all and cost > max_cost:
                    continue

                max_profit = width - cost
                rr = max_profit / cost

                if not include_all and rr < self.settings.rr_min:
                    continue

                lower_be = lower + cost
                upper_be = upper - cost
                distance = abs(center - spot_price)

                candidates.append(
                    ButterflyCandidate(
                        direction=direction,
                        wing_width=width,
                        center_strike=center,
                        lower_strike=lower,
                        upper_strike=upper,
                        cost=round(cost, 4),
                        ask=round(fly_ask, 4),
                        max_profit=round(max_profit, 4),
                        reward_risk=round(rr, 4),
                        lower_be=round(lower_be, 2),
                        upper_be=round(upper_be, 2),
                        distance_from_spot=round(distance, 2),
                        spot_price=spot_price,
                        lower_symbol=lower_q.symbol,
                        center_symbol=center_q.symbol,
                        upper_symbol=upper_q.symbol,
                        lower_quote=lower_q,
                        center_quote=center_q,
                        upper_quote=upper_q,
                    )
                )

        # Sort by distance from spot (ascending)
        candidates.sort(key=lambda c: c.distance_from_spot)
        log.info("candidates_built", count=len(candidates), direction=direction, spot=spot_price)
        return candidates
