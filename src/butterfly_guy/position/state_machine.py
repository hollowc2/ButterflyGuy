"""Profit management state machine for butterfly positions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from butterfly_guy.core.config import ProfitManagementSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.position.position_manager import PositionState

log = get_logger(__name__)


class ProfitState(Enum):
    LOSS = auto()
    NEAR_LONG = auto()
    PROFIT_TENT = auto()


@dataclass
class ExitSignal:
    reason: str
    target_credit: float
    urgency: str  # "normal", "high", "immediate"


class ProfitStateMachine:
    """
    Evaluates position state and determines exit signals.

    States:
    - LOSS: position below entry
    - NEAR_LONG: position near entry, small profit
    - PROFIT_TENT: position well above entry, protecting gains
    """

    def __init__(self, settings: ProfitManagementSettings) -> None:
        self.settings = settings
        self._state = ProfitState.LOSS
        self._ever_in_tent: bool = False

    @property
    def state(self) -> ProfitState:
        return self._state

    def evaluate(self, pos: PositionState) -> ExitSignal | None:
        """
        Evaluate position and return ExitSignal if we should exit, else None.
        """
        # Hard exits first
        if pos.minutes_to_close <= self.settings.exit_before_close_minutes:
            return ExitSignal(
                reason="end_of_day",
                target_credit=pos.current_value,
                urgency="immediate",
            )

        # Update internal state
        self._update_state(pos)

        # Absolute loss stop — fires regardless of whether position ever gained
        if pos.entry_price > 0:
            loss_from_cost = (pos.entry_price - pos.current_value) / pos.entry_price
            if loss_from_cost >= self.settings.max_loss_from_cost:
                log.info(
                    "absolute_loss_stop_triggered",
                    loss_pct=loss_from_cost,
                    threshold=self.settings.max_loss_from_cost,
                    entry=pos.entry_price,
                    current=pos.current_value,
                )
                return ExitSignal(
                    reason="absolute_loss_stop",
                    target_credit=pos.current_value,
                    urgency="high",
                )

        # Get drawdown threshold for current regime
        regime_config = self.settings.regimes.get(pos.time_regime)
        if not regime_config:
            return None

        threshold = regime_config.drawdown_threshold

        # Only exit on drawdown if position ever reached profit tent
        if self._ever_in_tent:
            if pos.drawdown_from_peak >= threshold:
                log.info(
                    "drawdown_exit_triggered",
                    drawdown=pos.drawdown_from_peak,
                    threshold=threshold,
                    regime=pos.time_regime,
                    peak=pos.peak_value,
                    current=pos.current_value,
                )
                return ExitSignal(
                    reason=f"drawdown_{pos.time_regime}",
                    target_credit=pos.current_value,
                    urgency="high",
                )

        return None

    def _update_state(self, pos: PositionState) -> None:
        """Transition between profit states."""
        pnl_ratio = pos.pnl / pos.entry_price if pos.entry_price > 0 else 0

        if pnl_ratio < 0:
            new_state = ProfitState.LOSS
        elif pnl_ratio < 0.5:
            new_state = ProfitState.NEAR_LONG
        else:
            new_state = ProfitState.PROFIT_TENT

        if new_state != self._state:
            log.info("state_transition", old=self._state.name, new=new_state.name, pnl_ratio=pnl_ratio)
            self._state = new_state
        if self._state == ProfitState.PROFIT_TENT:
            self._ever_in_tent = True

    def reset(self) -> None:
        """Reset state machine for a new position."""
        self._state = ProfitState.LOSS
        self._ever_in_tent = False
