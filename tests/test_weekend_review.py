"""Tests for weekend review date windows and orchestration."""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, patch

import pytest

from butterfly_guy.reports.live_performance import TradePoint
from butterfly_guy.services.weekend_review import (
    ReviewWindows,
    calendar_month_to_date,
    format_performance_caption,
    latest_fill_model_cohort,
    previous_mon_fri,
    review_windows,
    send_weekend_review,
    trades_in_range,
    trades_in_range_rows,
)


def _trade_point(trade_date: dt.date, pnl: float = 100.0) -> TradePoint:
    return TradePoint(
        trade_date=trade_date,
        direction="CALL",
        wing_width=30,
        center_strike=5000.0,
        lower_strike=4970.0,
        upper_strike=5030.0,
        entry_price=2.5,
        entry_time=dt.datetime(2026, 6, 2, 14, 0, tzinfo=dt.timezone.utc),
        exit_price=1.0,
        exit_time=dt.datetime(2026, 6, 2, 20, 0, tzinfo=dt.timezone.utc),
        exit_reason="end_of_day",
        pnl_dollars=pnl,
        peak_value=4.0,
        vix=18.0,
        entry_spot=4980.0,
        dd_at_exit_pct=None,
    )


def test_previous_mon_fri_from_saturday() -> None:
    saturday = dt.date(2026, 6, 6)
    monday, friday = previous_mon_fri(saturday)
    assert monday == dt.date(2026, 6, 1)
    assert friday == dt.date(2026, 6, 5)


def test_previous_mon_fri_from_friday() -> None:
    friday = dt.date(2026, 6, 5)
    monday, end_friday = previous_mon_fri(friday)
    assert monday == dt.date(2026, 6, 1)
    assert end_friday == dt.date(2026, 6, 5)


def test_calendar_month_to_date() -> None:
    start, end = calendar_month_to_date(dt.date(2026, 6, 6))
    assert start == dt.date(2026, 6, 1)
    assert end == dt.date(2026, 6, 6)


def test_review_windows_from_saturday() -> None:
    windows = review_windows(dt.date(2026, 6, 6))
    assert windows == ReviewWindows(
        week_start=dt.date(2026, 6, 1),
        week_end=dt.date(2026, 6, 5),
        month_start=dt.date(2026, 6, 1),
        month_end=dt.date(2026, 6, 5),
    )


def test_trades_in_range_filters_by_trade_date() -> None:
    trades = [
        _trade_point(dt.date(2026, 6, 2)),
        _trade_point(dt.date(2026, 6, 3)),
        _trade_point(dt.date(2026, 5, 30)),
    ]
    filtered = trades_in_range(trades, dt.date(2026, 6, 2), dt.date(2026, 6, 6))
    assert [t.trade_date for t in filtered] == [dt.date(2026, 6, 2), dt.date(2026, 6, 3)]


def test_trades_in_range_rows() -> None:
    rows = [
        {"trade_date": dt.date(2026, 6, 2), "id": 1},
        {"trade_date": dt.date(2026, 6, 6), "id": 2},
        {"trade_date": dt.date(2026, 5, 30), "id": 3},
    ]
    filtered = trades_in_range_rows(rows, dt.date(2026, 6, 2), dt.date(2026, 6, 6))
    assert [row["id"] for row in filtered] == [1, 2]


def test_format_performance_caption_includes_stats() -> None:
    trades = [_trade_point(dt.date(2026, 6, 2), 150.0), _trade_point(dt.date(2026, 6, 3), -50.0)]
    caption = format_performance_caption("Weekly", trades)
    assert "Weekly Performance" in caption
    assert "Trades: 2" in caption
    assert "Win rate: 50%" in caption


def test_latest_fill_model_cohort_does_not_mix_legacy_and_mark_v1() -> None:
    legacy = _trade_point(dt.date(2026, 7, 20), 500.0)
    mark = TradePoint(
        **{
            **_trade_point(dt.date(2026, 7, 21), -50.0).__dict__,
            "paper_fill_model": "mark_v1",
        }
    )

    assert latest_fill_model_cohort([legacy, mark]) == [mark]


@pytest.mark.asyncio
async def test_send_weekend_review_skips_when_no_weekly_trades() -> None:
    db = AsyncMock()
    with patch(
        "butterfly_guy.services.weekend_review.fetch_closed_trades",
        new=AsyncMock(return_value=[]),
    ):
        result = await send_weekend_review(
            db,
            underlying="SPX",
            reference=dt.date(2026, 6, 6),
            notifier=None,
            dry_run=True,
        )
    assert result.skipped is True
    assert result.reason == "no_weekly_trades"
    assert result.messages_sent == 0


@pytest.mark.asyncio
async def test_send_weekend_review_dry_run_with_weekly_trades(tmp_path) -> None:
    db = AsyncMock()
    weekly_row = {
        "id": 42,
        "underlying": "SPX",
        "trade_date": dt.date(2026, 6, 3),
        "direction": "CALL",
        "wing_width": 30,
        "lower_strike": 4970.0,
        "center_strike": 5000.0,
        "upper_strike": 5030.0,
        "entry_price": 2.5,
        "exit_price": 1.0,
        "pnl": 1.5,
        "peak_value": 4.0,
        "entry_time": dt.datetime(2026, 6, 3, 14, 0, tzinfo=dt.timezone.utc),
        "exit_time": dt.datetime(2026, 6, 3, 20, 0, tzinfo=dt.timezone.utc),
        "exit_reason": "end_of_day",
        "metadata": {"entry_spot": 4980.0},
    }
    older_row = {**weekly_row, "id": 1, "trade_date": dt.date(2026, 5, 1), "pnl": -1.0}
    all_rows = [older_row, weekly_row]

    fake_png = b"\x89PNG\r\n"
    with (
        patch(
            "butterfly_guy.services.weekend_review.fetch_closed_trades",
            new=AsyncMock(return_value=all_rows),
        ),
        patch(
            "butterfly_guy.services.weekend_review.build_eod_chart_for_row",
            new=AsyncMock(return_value=(fake_png, True)),
        ),
        patch(
            "butterfly_guy.services.weekend_review.build_combined_performance_chart_png",
            return_value=fake_png,
        ),
        patch(
            "butterfly_guy.services.weekend_review.asyncio.sleep",
            new=AsyncMock(),
        ),
    ):
        result = await send_weekend_review(
            db,
            underlying="SPX",
            reference=dt.date(2026, 6, 6),
            notifier=None,
            dry_run=True,
            dry_run_dir=tmp_path,
        )

    assert result.skipped is False
    assert result.weekly_trade_count == 1
    assert result.messages_sent == 3
    png_files = list(tmp_path.glob("*.png"))
    assert len(png_files) == 2
