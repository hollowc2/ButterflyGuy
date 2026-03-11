"""Parameter sweep engine for backtesting across date ranges."""

from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import dataclass
from typing import Any

import polars as pl

from butterfly_guy.backtest.data_loader import BacktestDataLoader
from butterfly_guy.backtest.simulation_engine import DayResult, SimulationEngine, SimulationParams
from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class SweepConfig:
    start_date: dt.date
    end_date: dt.date
    wing_widths: list[int]
    rr_mins: list[float]
    morning_drawdowns: list[float]
    late_morning_drawdowns: list[float]
    afternoon_drawdowns: list[float]


def _sharpe(pnls: list[float]) -> float:
    if len(pnls) < 2:
        return 0.0
    import statistics
    mean = statistics.mean(pnls)
    stdev = statistics.stdev(pnls)
    if stdev == 0:
        return 0.0
    return mean / stdev * (252**0.5)


def _max_drawdown(pnls: list[float]) -> float:
    """Max drawdown on cumulative PnL series."""
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in pnls:
        equity += p
        peak = max(peak, equity)
        dd = peak - equity
        max_dd = max(max_dd, dd)
    return max_dd


def _profit_factor(pnls: list[float]) -> float:
    """Gross profit / gross loss. Returns 0 if no losses."""
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    if gross_loss == 0:
        return 0.0
    return round(gross_profit / gross_loss, 4)


def _max_consecutive_losses(pnls: list[float]) -> int:
    """Longest streak of negative PnL trades."""
    max_streak = 0
    streak = 0
    for p in pnls:
        if p < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


class ParameterSweeper:
    """Runs grid search over simulation parameters across a date range."""

    def __init__(self, loader: BacktestDataLoader) -> None:
        self.loader = loader
        self.engine = SimulationEngine()

    async def sweep(self, config: SweepConfig) -> pl.DataFrame:
        """Run full parameter sweep. Returns a polars DataFrame."""
        # Load all days first
        dates = self._date_range(config.start_date, config.end_date)
        log.info("loading_days", count=len(dates))

        day_data = {}
        for date in dates:
            try:
                data = await self.loader.load_day(date)
                if data:
                    day_data[date] = data
                    log.info("day_loaded", date=str(date))
            except Exception as e:
                log.warning("day_load_failed", date=str(date), error=str(e))

        log.info("days_loaded", count=len(day_data))

        # Build param grid
        results: list[dict[str, Any]] = []

        for wing_width in config.wing_widths:
            for rr_min in config.rr_mins:
                for md in config.morning_drawdowns:
                    for lmd in config.late_morning_drawdowns:
                        for ad in config.afternoon_drawdowns:
                            params = SimulationParams(
                                wing_width=wing_width,
                                rr_min=rr_min,
                                morning_drawdown=md,
                                late_morning_drawdown=lmd,
                                afternoon_drawdown=ad,
                            )
                            day_results = [
                                self.engine.simulate_day(d, params)
                                for d in day_data.values()
                            ]
                            row = self._summarize(params, day_results)
                            results.append(row)
                            log.info(
                                "sweep_point",
                                width=wing_width,
                                rr=rr_min,
                                total_pnl=row["total_pnl"],
                                win_rate=row["win_rate"],
                            )

        if not results:
            return pl.DataFrame()

        return pl.DataFrame(results).sort("sharpe", descending=True)

    def _summarize(
        self, params: SimulationParams, results: list[DayResult]
    ) -> dict[str, Any]:
        traded = [r for r in results if r.traded]
        if not traded:
            return {
                "wing_width": params.wing_width,
                "rr_min": params.rr_min,
                "morning_drawdown": params.morning_drawdown,
                "late_morning_drawdown": params.late_morning_drawdown,
                "afternoon_drawdown": params.afternoon_drawdown,
                "trade_count": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "max_drawdown": 0.0,
                "sharpe": 0.0,
                "profit_factor": 0.0,
                "max_consec_losses": 0,
                "exit_morning_dd": 0,
                "exit_late_morning_dd": 0,
                "exit_afternoon_dd": 0,
                "exit_eod": 0,
                "exit_expired": 0,
            }

        pnls = [r.pnl for r in traded]
        wins = sum(1 for p in pnls if p > 0)

        # Per-regime exit counts
        exit_reasons = [r.exit_reason for r in traded]
        regime_counts = {
            "exit_morning_dd": exit_reasons.count("drawdown_morning"),
            "exit_late_morning_dd": exit_reasons.count("drawdown_late_morning"),
            "exit_afternoon_dd": exit_reasons.count("drawdown_afternoon"),
            "exit_eod": exit_reasons.count("end_of_day"),
            "exit_expired": exit_reasons.count("expired"),
        }

        return {
            "wing_width": params.wing_width,
            "rr_min": params.rr_min,
            "morning_drawdown": params.morning_drawdown,
            "late_morning_drawdown": params.late_morning_drawdown,
            "afternoon_drawdown": params.afternoon_drawdown,
            "trade_count": len(traded),
            "total_pnl": round(sum(pnls), 4),
            "win_rate": round(wins / len(traded), 4),
            "avg_pnl": round(sum(pnls) / len(traded), 4),
            "max_drawdown": round(_max_drawdown(pnls), 4),
            "sharpe": round(_sharpe(pnls), 4),
            "profit_factor": _profit_factor(pnls),
            "max_consec_losses": _max_consecutive_losses(pnls),
            **regime_counts,
        }

    @staticmethod
    def _date_range(start: dt.date, end: dt.date) -> list[dt.date]:
        dates = []
        current = start
        while current <= end:
            if current.weekday() < 5:  # weekdays only
                dates.append(current)
            current += dt.timedelta(days=1)
        return dates
