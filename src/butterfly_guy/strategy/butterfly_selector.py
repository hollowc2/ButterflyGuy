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
        Select the best candidate: closest to spot, tiebreak by highest RR.
        Candidates should already be sorted by distance_from_spot.
        """
        if not candidates:
            log.warning("no_candidates_to_select")
            return None

        # Group by minimum distance
        min_distance = candidates[0].distance_from_spot
        closest = [c for c in candidates if c.distance_from_spot == min_distance]

        # Tiebreak: highest reward/risk
        best = max(closest, key=lambda c: c.reward_risk)

        log.info(
            "candidate_selected",
            center=best.center_strike,
            width=best.wing_width,
            rr=best.reward_risk,
            cost=best.cost,
            distance=best.distance_from_spot,
        )
        return best
