"""Tests for Discord trade chart generation."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from butterfly_guy.services.trade_chart import (
    ButterflyChartSpec,
    _exit_chart_series,
    _exit_marker_point,
    build_entry_chart_png,
    build_exit_chart_png,
    candles_to_series,
    entry_chart_window,
    summarize_exit_chart,
)

PACIFIC = ZoneInfo("America/Los_Angeles")
EASTERN = ZoneInfo("America/New_York")


def _ts_et(year: int, month: int, day: int, hour: int, minute: int) -> int:
    ts = dt.datetime(year, month, day, hour, minute, tzinfo=EASTERN)
    return int(ts.timestamp() * 1000)


def _sample_candles(session_date: dt.date, base_price: float = 6000.0) -> list[dict]:
    candles: list[dict] = []
    open_dt = dt.datetime.combine(session_date, dt.time(9, 30), tzinfo=EASTERN)
    for i in range(120):
        ts = open_dt + dt.timedelta(minutes=i)
        price = base_price + (i % 10) - 5
        candles.append({"datetime": int(ts.timestamp() * 1000), "close": price})
    return candles


def test_entry_chart_window_uses_start_time_and_fill() -> None:
    session = dt.date(2026, 6, 6)
    fill = dt.datetime(2026, 6, 6, 10, 0, tzinfo=EASTERN)  # 07:00 PT
    start, end = entry_chart_window(session, "07:00", "America/Los_Angeles", fill, 30)
    assert start == dt.datetime(2026, 6, 6, 6, 30, tzinfo=PACIFIC)
    assert end == dt.datetime(2026, 6, 6, 7, 0, tzinfo=PACIFIC)


def test_entry_chart_window_extends_to_late_fill() -> None:
    session = dt.date(2026, 6, 6)
    fill = dt.datetime(2026, 6, 6, 10, 5, tzinfo=EASTERN)  # 07:05 PT
    start, end = entry_chart_window(session, "07:00", "America/Los_Angeles", fill, 30)
    assert start == dt.datetime(2026, 6, 6, 6, 35, tzinfo=PACIFIC)
    assert end == dt.datetime(2026, 6, 6, 7, 5, tzinfo=PACIFIC)


def test_entry_chart_window_caps_end_at_start_when_fill_is_early() -> None:
    session = dt.date(2026, 6, 6)
    fill = dt.datetime(2026, 6, 6, 9, 55, tzinfo=EASTERN)  # 06:55 PT
    start, end = entry_chart_window(session, "07:00", "America/Los_Angeles", fill, 30)
    assert end == dt.datetime(2026, 6, 6, 7, 0, tzinfo=PACIFIC)
    assert start == dt.datetime(2026, 6, 6, 6, 30, tzinfo=PACIFIC)


def test_build_entry_chart_png_returns_png_bytes() -> None:
    session = dt.date(2026, 6, 6)
    fill = dt.datetime(2026, 6, 6, 10, 5, tzinfo=EASTERN)
    spec = ButterflyChartSpec(
        underlying="SPX",
        direction="CALL",
        lower_strike=5990,
        center_strike=6000,
        upper_strike=6010,
        wing_width=10,
        entry_price=1.25,
        entry_time=fill,
        entry_spot=6002.5,
    )
    png = build_entry_chart_png(
        spec,
        _sample_candles(session),
        start_time="07:00",
        timezone="America/Los_Angeles",
    )
    assert png is not None
    assert png[:4] == b"\x89PNG"


def test_build_exit_chart_png_returns_png_bytes() -> None:
    session = dt.date(2026, 6, 6)
    entry = dt.datetime(2026, 6, 6, 10, 5, tzinfo=EASTERN)
    exit_time = dt.datetime(2026, 6, 6, 15, 55, tzinfo=EASTERN)
    spec = ButterflyChartSpec(
        underlying="SPX",
        direction="CALL",
        lower_strike=5990,
        center_strike=6000,
        upper_strike=6010,
        wing_width=10,
        entry_price=1.25,
        entry_time=entry,
        entry_spot=6002.5,
        exit_time=exit_time,
        exit_reason="end_of_day",
    )
    candles = _sample_candles(session, base_price=6001.0)
    png = build_exit_chart_png(spec, candles)
    assert png is not None
    assert png[:4] == b"\x89PNG"


def test_full_session_extends_chart_to_market_close() -> None:
    session = dt.date(2026, 6, 6)
    entry = dt.datetime(2026, 6, 6, 10, 5, tzinfo=EASTERN)
    early_exit = dt.datetime(2026, 6, 6, 11, 0, tzinfo=EASTERN)
    spec = ButterflyChartSpec(
        underlying="SPX",
        direction="CALL",
        lower_strike=5990,
        center_strike=6000,
        upper_strike=6010,
        wing_width=10,
        entry_price=1.25,
        entry_time=entry,
        exit_time=early_exit,
        exit_reason="drawdown",
    )
    candles = _sample_candles(session, base_price=6001.0)
    partial = _exit_chart_series(spec, candles, full_session=False)
    full = _exit_chart_series(spec, candles, full_session=True)
    assert partial is not None and full is not None
    assert len(full) > len(partial)
    assert _exit_marker_point(spec, full)[0] == early_exit


def test_summarize_exit_chart_detects_tent_hit() -> None:
    session = dt.date(2026, 6, 6)
    entry = dt.datetime(2026, 6, 6, 10, 5, tzinfo=EASTERN)
    spec = ButterflyChartSpec(
        underlying="SPX",
        direction="CALL",
        lower_strike=5990,
        center_strike=6000,
        upper_strike=6010,
        wing_width=10,
        entry_price=1.25,
        entry_time=entry,
        entry_spot=6001.0,
        exit_time=dt.datetime(2026, 6, 6, 11, 0, tzinfo=EASTERN),
        exit_reason="drawdown",
    )
    # lower_be=5991.25, upper_be=6008.75 — base 6001 is inside tent
    png, tent_hit = summarize_exit_chart(spec, _sample_candles(session, base_price=6001.0))
    assert png is not None
    assert tent_hit is True


def test_candles_to_series_sorts_and_converts_timezone() -> None:
    candles = [
        {"datetime": _ts_et(2026, 6, 6, 10, 1), "close": 6001.0},
        {"datetime": _ts_et(2026, 6, 6, 10, 0), "close": 6000.0},
    ]
    series = candles_to_series(candles)
    assert len(series) == 2
    assert series[0][1] == 6000.0
    assert series[1][1] == 6001.0
    assert series[0][0].tzinfo == EASTERN
