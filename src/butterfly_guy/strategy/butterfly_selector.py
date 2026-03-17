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
        self,
        candidates: list[ButterflyCandidate],
        target_center: float | None = None,
        center_tolerance: float = 15.0,
    ) -> ButterflyCandidate | None:
        """Select the best butterfly candidate.

        When `target_center` is provided (derived from VIX), candidates are
        first filtered to those whose center strike falls within `center_tolerance`
        points of that target. This lets VIX anchor WHERE the fly is placed while
        R/R selects the best WIDTH around that anchor.

        Without `target_center`, falls back to the original R/R-closest-to-target
        behaviour across all candidates.

        Args:
            candidates: All valid butterfly candidates from the builder.
            target_center: VIX-implied ideal center strike (optional).
            center_tolerance: Max distance a candidate's center can be from
                              target_center to still be considered (default ±15pts).
        """
        if not candidates:
            log.warning("no_candidates_to_select")
            return None

        pool = candidates

        if target_center is not None:
            near_center = [
                c for c in candidates
                if abs(c.center_strike - target_center) <= center_tolerance
            ]
            if near_center:
                pool = near_center
                log.debug(
                    "center_filter_applied",
                    target_center=target_center,
                    tolerance=center_tolerance,
                    before=len(candidates),
                    after=len(pool),
                )
            else:
                log.warning(
                    "no_candidates_near_target_center",
                    target_center=target_center,
                    tolerance=center_tolerance,
                    falling_back_to="all candidates",
                )

        # Filter out unrealistically high R/R (too far OTM, nearly worthless)
        filtered = [c for c in pool if c.reward_risk <= self.settings.rr_max]
        if not filtered:
            filtered = pool

        # Among remaining, pick closest to target R/R
        best = min(filtered, key=lambda c: abs(c.reward_risk - self.settings.rr_target))

        log.info(
            "candidate_selected",
            center=best.center_strike,
            width=best.wing_width,
            rr=best.reward_risk,
            cost=best.cost,
            distance=best.distance_from_spot,
            target_center=target_center,
        )
        return best
