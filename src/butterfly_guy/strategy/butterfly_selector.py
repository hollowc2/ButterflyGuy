"""Butterfly selector — picks the best candidate from a list."""

from __future__ import annotations

from butterfly_guy.core.config import StrategySettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.data.schemas import ButterflyCandidate

log = get_logger(__name__)


class ButterflySelector:
    """Selects the best butterfly candidate."""

    def __init__(self, settings: StrategySettings | None = None) -> None:
        self.settings = settings or StrategySettings()

    def select_best(
        self, candidates: list[ButterflyCandidate]
    ) -> ButterflyCandidate | None:
        """
        Select the best candidate: prioritize the candidate whose Reward/Risk (R/R) 
        ratio is closest to the strategy target RR (default 10.0), filtering out any 
        that exceed the max permitted RR. This keeps flies OTM but bounds them 
        so they remain mathematically realistic before expiration.
        """
        if not candidates:
            log.warning("no_candidates_to_select")
            return None

        # Filter out combinations that are way too cheap/far OTM
        filtered = [c for c in candidates if c.reward_risk <= self.settings.rr_max]
        if not filtered:
            # Fall back to picking the lowest RR we have (closest to the max limit)
            filtered = candidates

        # Select by closest to target RR
        best = min(filtered, key=lambda c: abs(c.reward_risk - self.settings.rr_target))

        log.info(
            "candidate_selected",
            center=best.center_strike,
            width=best.wing_width,
            rr=best.reward_risk,
            cost=best.cost,
            distance=best.distance_from_spot,
        )
        return best
