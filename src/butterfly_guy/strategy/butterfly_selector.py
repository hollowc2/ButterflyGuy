"""Butterfly selector — picks the best candidate from a list."""

from __future__ import annotations

from butterfly_guy.core.logging import get_logger
from butterfly_guy.data.schemas import ButterflyCandidate

log = get_logger(__name__)


class ButterflySelector:
    """Selects the best butterfly candidate."""

    def select_best(
        self, candidates: list[ButterflyCandidate]
    ) -> ButterflyCandidate | None:
        """
        Select the best candidate: prioritize the highest Reward/Risk (R/R) ratio.
        This favors OTM geometries rather than forcing At-The-Money setups.
        """
        if not candidates:
            log.warning("no_candidates_to_select")
            return None

        # Sort/select by highest reward/risk ratio
        best = max(candidates, key=lambda c: c.reward_risk)

        log.info(
            "candidate_selected",
            center=best.center_strike,
            width=best.wing_width,
            rr=best.reward_risk,
            cost=best.cost,
            distance=best.distance_from_spot,
        )
        return best
