"""O(N*W) butterfly construction and scoring engine."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from butterfly_guy.core.config import StrategySettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote

log = get_logger(__name__)


class ButterflyBuilder:
    """Builds and scores butterfly spreads from an option chain snapshot."""

    def __init__(self, settings: StrategySettings) -> None:
        self.settings = settings

    def build_candidates(
        self,
        quotes: list[OptionQuote],
        spot_price: float,
        direction: Literal["CALL", "PUT"],
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

            for width in self.settings.wing_widths:
                lower = center - width
                upper = center + width

                if lower not in strike_set or upper not in strike_set:
                    continue

                lower_q = by_strike[lower]
                center_q = by_strike[center]
                upper_q = by_strike[upper]

                # Butterfly cost: buy lower + buy upper - 2 * sell center (using mark)
                cost = lower_q.mark - 2 * center_q.mark + upper_q.mark

                if cost < 0.05:  # minimum practical butterfly debit; filters fp-epsilon zeros
                    continue

                max_cost = self.settings.max_cost_per_width.get(width, float("inf"))
                if cost > max_cost:
                    continue

                max_profit = width - cost
                rr = max_profit / cost

                if rr < self.settings.rr_min:
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
