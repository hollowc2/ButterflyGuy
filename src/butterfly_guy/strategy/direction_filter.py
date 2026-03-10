"""Direction filter — determines CALL or PUT based on open vs previous close."""

from __future__ import annotations

from typing import Literal

from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)


class DirectionFilter:
    """Determines butterfly direction based on market bias."""

    def get_direction(
        self, current_price: float, previous_close: float
    ) -> Literal["CALL", "PUT"]:
        """
        If price is above previous close, market is bullish → CALL butterflies.
        If below, bearish → PUT butterflies.
        """
        if current_price >= previous_close:
            direction: Literal["CALL", "PUT"] = "CALL"
        else:
            direction = "PUT"

        log.info(
            "direction_determined",
            direction=direction,
            current=current_price,
            prev_close=previous_close,
            gap_pct=round((current_price - previous_close) / previous_close * 100, 3),
        )
        return direction
