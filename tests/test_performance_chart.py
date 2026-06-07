"""Tests for Discord performance chart PNG generation."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.reports.live_performance import TradePoint, compute_stats
from butterfly_guy.reports.performance_chart import (
    build_combined_performance_chart_png,
    build_performance_chart_png,
)


def _trade(
    trade_date: dt.date,
    pnl_dollars: float,
    *,
    exit_reason: str = "end_of_day",
) -> TradePoint:
    return TradePoint(
        trade_date=trade_date,
        direction="CALL",
        wing_width=30,
        center_strike=5000.0,
        lower_strike=4970.0,
        upper_strike=5030.0,
        entry_price=2.5,
        entry_time=dt.datetime(2026, 3, 17, 14, 0, tzinfo=dt.timezone.utc),
        exit_price=1.0,
        exit_time=dt.datetime(2026, 3, 17, 20, 0, tzinfo=dt.timezone.utc),
        exit_reason=exit_reason,
        pnl_dollars=pnl_dollars,
        peak_value=4.0,
        vix=18.0,
        entry_spot=4980.0,
        dd_at_exit_pct=None,
    )


def test_build_performance_chart_png_returns_png_bytes() -> None:
    trades = [
        _trade(dt.date(2026, 3, 17), 100.0),
        _trade(dt.date(2026, 3, 18), -50.0, exit_reason="drawdown_morning"),
        _trade(dt.date(2026, 3, 19), 75.0),
    ]
    png = build_performance_chart_png(trades, title="SPX Weekly", period_label="Weekly")
    assert png.startswith(b"\x89PNG\r\n")
    assert len(png) > 1000


def test_build_combined_performance_chart_png_returns_png_bytes() -> None:
    weekly = [_trade(dt.date(2026, 6, 3), -125.0)]
    monthly = weekly + [_trade(dt.date(2026, 6, 4), -229.0)]
    all_time = [
        _trade(dt.date(2026, 3, 17), 100.0),
        _trade(dt.date(2026, 3, 18), -50.0, exit_reason="drawdown_morning"),
        _trade(dt.date(2026, 3, 19), 75.0),
    ]
    periods = [("Weekly", weekly), ("Monthly", monthly), ("All-Time", all_time)]
    png = build_combined_performance_chart_png(periods)
    assert png.startswith(b"\x89PNG\r\n")
    assert len(png) > 1000


def test_build_performance_chart_png_empty_trades() -> None:
    png = build_performance_chart_png([], title="SPX Weekly", period_label="Weekly")
    assert png.startswith(b"\x89PNG\r\n")
    stats = compute_stats([])
    assert stats.trade_count == 0
