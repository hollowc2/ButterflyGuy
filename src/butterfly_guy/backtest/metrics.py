"""Shared metrics for backtest sweep scripts."""

from __future__ import annotations

import statistics


def sharpe(pnls: list[float]) -> float:
    if len(pnls) < 2:
        return 0.0
    mean = statistics.mean(pnls)
    stdev = statistics.stdev(pnls)
    return round(mean / stdev * (252**0.5), 3) if stdev > 0 else 0.0


def max_drawdown(pnls: list[float]) -> float:
    equity = peak = max_dd = 0.0
    for p in pnls:
        equity += p
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def profit_factor(pnls: list[float]) -> float:
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    return round(gross_profit / gross_loss, 3) if gross_loss > 0 else 999.0


def max_consecutive_losses(pnls: list[float]) -> int:
    max_streak = streak = 0
    for p in pnls:
        if p < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


def win_pct(pnls: list[float]) -> float:
    if not pnls:
        return 0.0
    return round(sum(1 for p in pnls if p > 0) / len(pnls) * 100, 1)
