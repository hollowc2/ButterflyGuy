"""Profit management state machine for butterfly positions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from butterfly_guy.core.config import ProfitManagementSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.position.position_manager import PositionState
from butterfly_guy.position.profit_policy import (
    effective_drawdown_threshold,
    profitprotector_floor_decision,
)

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
        self._ever_in_profit: bool = False
        self._pending_drawdown_reason: str | None = None
        self._pending_drawdown_count: int = 0

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
        if self.settings.use_absolute_loss_stop and pos.entry_price > 0:
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

        threshold = effective_drawdown_threshold(
            strategy=self.settings.strategy,
            entry_price=pos.entry_price,
            peak_value=pos.peak_value,
            regime_config=regime_config,
            protector_settings=self.settings.profitprotector,
        )
        confirmation_polls = max(1, regime_config.confirmation_polls)
        min_peak_value = pos.entry_price * regime_config.min_peak_profit_ratio

        # Only exit on drawdown if position has ever been above entry
        if self._ever_in_profit and pos.peak_value >= min_peak_value:
            if self.settings.strategy == "profitprotector":
                floor_decision = profitprotector_floor_decision(
                    entry_price=pos.entry_price,
                    current_value=pos.current_value,
                    peak_value=pos.peak_value,
                    settings=self.settings.profitprotector,
                )
                if floor_decision is not None:
                    log.info(
                        "profitprotector_floor_triggered",
                        reason=floor_decision.reason,
                        peak=pos.peak_value,
                        current=pos.current_value,
                        entry=pos.entry_price,
                    )
                    return ExitSignal(
                        reason=floor_decision.reason,
                        target_credit=pos.current_value,
                        urgency=floor_decision.urgency,
                    )

            if pos.drawdown_from_peak >= threshold:
                reason = f"drawdown_{pos.time_regime}"
                if not self._quote_quality_ok(pos):
                    log.info(
                        "drawdown_exit_blocked_quote_quality",
                        drawdown=pos.drawdown_from_peak,
                        threshold=threshold,
                        regime=pos.time_regime,
                        spread_bid=pos.spread_bid,
                        spread_ask=pos.spread_ask,
                        bid_to_mark_ratio=pos.bid_to_mark_ratio,
                    )
                    self._reset_pending_drawdown()
                    return None

                if self._pending_drawdown_reason == reason:
                    self._pending_drawdown_count += 1
                else:
                    self._pending_drawdown_reason = reason
                    self._pending_drawdown_count = 1

                if self._pending_drawdown_count < confirmation_polls:
                    log.info(
                        "drawdown_exit_pending_confirmation",
                        drawdown=pos.drawdown_from_peak,
                        threshold=threshold,
                        regime=pos.time_regime,
                        confirmation_count=self._pending_drawdown_count,
                        confirmation_required=confirmation_polls,
                    )
                    return None

                log.info(
                    "drawdown_exit_triggered",
                    drawdown=pos.drawdown_from_peak,
                    threshold=threshold,
                    confirmation_count=self._pending_drawdown_count,
                    confirmation_required=confirmation_polls,
                    regime=pos.time_regime,
                    peak=pos.peak_value,
                    current=pos.current_value,
                    spread_bid=pos.spread_bid,
                    peak_bid=pos.peak_bid,
                    bid_to_mark_ratio=pos.bid_to_mark_ratio,
                )
                return ExitSignal(
                    reason=reason,
                    target_credit=pos.current_value,
                    urgency="high",
                )
            self._reset_pending_drawdown()
        else:
            self._reset_pending_drawdown()

        return None

    def _quote_quality_ok(self, pos: PositionState) -> bool:
        settings = self.settings.quote_quality
        if not settings.enabled:
            return True

        if (
            pos.spread_bid is None
            or pos.spread_ask is None
            or pos.bid_to_mark_ratio is None
        ):
            return False

        if pos.spread_bid <= 0:
            return False

        if pos.bid_to_mark_ratio < settings.min_bid_to_mark_ratio:
            return False

        if settings.max_spread_width_ratio is not None and pos.current_value > 0:
            spread_width_ratio = (pos.spread_ask - pos.spread_bid) / pos.current_value
            if spread_width_ratio > settings.max_spread_width_ratio:
                return False

        return True

    def _reset_pending_drawdown(self) -> None:
        self._pending_drawdown_reason = None
        self._pending_drawdown_count = 0

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
            log.info(
                "state_transition",
                old=self._state.name,
                new=new_state.name,
                pnl_ratio=pnl_ratio,
            )
            self._state = new_state
        if self._state != ProfitState.LOSS:
            self._ever_in_profit = True

    def reset(self) -> None:
        """Reset state machine for a new position."""
        self._state = ProfitState.LOSS
        self._ever_in_profit = False
        self._reset_pending_drawdown()
