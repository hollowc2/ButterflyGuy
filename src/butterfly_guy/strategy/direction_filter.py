"""Direction filter — determines CALL or PUT based on open vs previous close."""

from __future__ import annotations

from typing import Literal

from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)


def determine_direction(
    current_price: float, previous_close: float
) -> Literal["CALL", "PUT"]:
    """CALL if price >= previous close (bullish gap), PUT otherwise."""
    direction: Literal["CALL", "PUT"] = "CALL" if current_price >= previous_close else "PUT"
    log.info(
        "direction_determined",
        direction=direction,
        current=current_price,
        prev_close=previous_close,
        gap_pct=round((current_price - previous_close) / previous_close * 100, 3),
    )
    return direction


# Backwards-compatible alias so callers that still use the class form work unchanged.
class DirectionFilter:
    def get_direction(
        self, current_price: float, previous_close: float
    ) -> Literal["CALL", "PUT"]:
        return determine_direction(current_price, previous_close)
