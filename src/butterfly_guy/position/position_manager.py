"""Position value tracking and management."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import position_peak_value, position_pnl, position_value
from butterfly_guy.core.time_utils import get_time_regime, minutes_since_open, minutes_to_close
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord, fly_mark_value

log = get_logger(__name__)


@dataclass
class PositionState:
    """Current state of an open position."""

    entry_price: float
    current_value: float
    peak_value: float
    pnl: float
    drawdown_from_peak: float  # 0.0 to 1.0
    time_regime: str
    minutes_to_close: float
    minutes_since_open: float


class PositionManager:
    """Tracks position value from chain data and manages peak tracking."""

    def __init__(self, underlying: str) -> None:
        self._underlying = underlying
        self._peak_value: float = 0.0
        self._entry_price: float = 0.0

    def reset(self, entry_price: float) -> None:
        """Reset for a new position."""
        self._entry_price = entry_price
        self._peak_value = entry_price

    def update_position_value(
        self,
        candidate: ButterflyCandidate,
        current_quotes: dict[float, OptionQuote],
    ) -> PositionState:
        """
        Calculate current butterfly value from latest chain quotes.
        Value = lower_mark - 2 * center_mark + upper_mark
        """
        lower_q = current_quotes.get(candidate.lower_strike)
        center_q = current_quotes.get(candidate.center_strike)
        upper_q = current_quotes.get(candidate.upper_strike)

        if not all([lower_q, center_q, upper_q]):
            # Use last known value if quotes missing
            current_value = self._peak_value
            log.warning("missing_quotes_for_position")
        else:
            current_value = max(0.0, fly_mark_value(lower_q, center_q, upper_q))

        # Update peak
        if current_value > self._peak_value:
            self._peak_value = current_value

        pnl = current_value - self._entry_price
        drawdown = 0.0
        if self._peak_value > 0:
            drawdown = (self._peak_value - current_value) / self._peak_value

        # Determine time regime
        mins_open = minutes_since_open()
        regime = get_time_regime(mins_open)

        # Update metrics
        position_value.labels(underlying=self._underlying).set(current_value)
        position_peak_value.labels(underlying=self._underlying).set(self._peak_value)
        position_pnl.labels(underlying=self._underlying).set(pnl)

        return PositionState(
            entry_price=self._entry_price,
            current_value=round(current_value, 4),
            peak_value=round(self._peak_value, 4),
            pnl=round(pnl, 4),
            drawdown_from_peak=round(drawdown, 4),
            time_regime=regime,
            minutes_to_close=minutes_to_close(),
            minutes_since_open=mins_open,
        )

