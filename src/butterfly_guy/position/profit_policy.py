"""Shared profit-management policy helpers for live trading and backtests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from butterfly_guy.core.config import ProfitProtectorSettings, TimeRegime

ProfitManagementStrategy = Literal["peakvaluetrailer", "profitprotector"]


@dataclass(frozen=True)
class ProfitPolicyDecision:
    reason: str
    urgency: str = "high"


def profitprotector_floor_decision(
    *,
    entry_price: float,
    current_value: float,
    peak_value: float,
    settings: ProfitProtectorSettings,
) -> ProfitPolicyDecision | None:
    """Return a profit-floor exit once a configured peak gain has been reached."""
    if entry_price <= 0:
        return None

    if peak_value >= entry_price + settings.profit_lock_activation_profit:
        floor = entry_price + settings.profit_lock_floor_profit
        if current_value <= floor:
            return ProfitPolicyDecision("profitprotector_profit_floor")

    if peak_value >= entry_price + settings.breakeven_activation_profit:
        floor = entry_price + settings.breakeven_floor_profit
        if current_value <= floor:
            return ProfitPolicyDecision("profitprotector_breakeven_floor")

    return None


def effective_drawdown_threshold(
    *,
    strategy: ProfitManagementStrategy,
    entry_price: float,
    peak_value: float,
    regime_config: TimeRegime,
    protector_settings: ProfitProtectorSettings,
) -> float:
    """Return the active trailing drawdown threshold for the selected policy."""
    threshold = regime_config.drawdown_threshold
    if (
        strategy == "profitprotector"
        and entry_price > 0
        and peak_value >= entry_price * protector_settings.large_peak_profit_ratio
    ):
        threshold = min(threshold, protector_settings.large_peak_drawdown_threshold)
    return threshold
