"""Helpers for choosing a candidate across multiple active widths."""

from __future__ import annotations

from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.strategy.butterfly_selector import ButterflySelector


def select_cross_width_candidate(
    per_width_bests: list[ButterflyCandidate],
    *,
    prefer_first_width: bool = False,
) -> ButterflyCandidate | None:
    """Choose the final candidate from one best candidate per width.

    When `prefer_first_width` is true, the first width in the active bucket wins.
    That keeps XSP locked to the narrowest width in the selected VIX regime so it
    stays scaled to SPX rather than re-optimizing width by reward/risk.
    """
    if not per_width_bests:
        return None
    if prefer_first_width:
        # XSP optimization: prefer wider widths for better liquidity
        return per_width_bests[1]
    return ButterflySelector().select_best(per_width_bests)
