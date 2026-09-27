"""Tests for weekend review date windows and orchestration."""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, patch

import pytest

from butterfly_guy.reports.live_performance import TradePoint, trade_point_from_row
from butterfly_guy.services.weekend_review import (
    ReviewWindows,
    calendar_month_to_date,
    format_executable_pnl,
    format_performance_caption,
    format_review_header,
    format_trade_recap,
    latest_fill_model_cohort,
    previous_mon_fri,
    review_windows,
    send_weekend_review,
    trades_in_range,
    trades_in_range_rows,
)


def _trade_point(
    trade_date: dt.date, pnl: float = 100.0, executable: float | None = None
) -> TradePoint:
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
        executable_pnl_dollars=executable,
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


def _row(**overrides) -> dict:
    row = {
        "id": 7,
        "underlying": "NDX",
        "trade_date": dt.date(2026, 9, 21),
        "direction": "CALL",
        "wing_width": 100,
        "lower_strike": 20000.0,
        "center_strike": 20100.0,
        "upper_strike": 20200.0,
        "entry_price": 7.53,
        "exit_price": 3.71,
        "pnl": -3.82,
        "peak_value": 8.0,
        "exit_reason": "drawdown_afternoon",
        "metadata": {
            "paper_fill_model": "mark_v1",
            "entry_execution_diagnostics": {"marketable_entry_estimate": 11.08},
            "exit_execution_diagnostics": {"marketable_exit_estimate": 2.82},
        },
    }
    row.update(overrides)
    return row


def test_executable_pnl_uses_marketable_entry_and_exit() -> None:
    point = trade_point_from_row(_row())
    assert point.pnl_dollars == pytest.approx(-382.0)
    assert point.executable_pnl_dollars == pytest.approx((2.82 - 11.08) * 100)


def test_cash_settled_exit_uses_settlement_value() -> None:
    row = _row(
        exit_reason="cash_settled",
        exit_price=0.0,
        pnl=-7.53,
        metadata={
            "paper_fill_model": "mark_v1",
            "entry_execution_diagnostics": {"marketable_entry_estimate": 11.08},
        },
    )
    assert trade_point_from_row(row).executable_pnl_dollars == pytest.approx(-1108.0)


def test_executable_pnl_is_none_without_recorded_prices() -> None:
    assert trade_point_from_row(_row(metadata={})).executable_pnl_dollars is None
    exit_only = _row(metadata={"exit_execution_diagnostics": {"marketable_exit_estimate": 2.0}})
    assert trade_point_from_row(exit_only).executable_pnl_dollars is None


def test_format_executable_pnl_counts_unpriced_trades() -> None:
    day = dt.date(2026, 9, 21)
    assert format_executable_pnl([_trade_point(day, executable=-50.0)]) == "-$50.00"
    assert format_executable_pnl(
        [_trade_point(day, executable=-50.0), _trade_point(day, executable=None)]
    ) == "-$50.00 (1 unpriced)"
    assert format_executable_pnl([_trade_point(day)]) == "n/a"


def test_caption_and_recap_show_paper_and_executable_side_by_side() -> None:
    day = dt.date(2026, 9, 21)
    caption = format_performance_caption(
        "Weekly", [_trade_point(day, pnl=100.0, executable=-25.0)]
    )
    assert "Paper P&L: **+$100.00**" in caption
    assert "Executable: **-$25.00**" in caption

    recap = format_trade_recap(_row(), tent_hit=None)
    assert "**NDX #7**" in recap
    assert "Paper P&L: **-$382.00**" in recap
    assert "Executable: **-$826.00**" in recap


def test_review_header_names_the_underlying() -> None:
    windows = review_windows(dt.date(2026, 9, 26))
    assert "**XSP Weekend Review**" in format_review_header(windows, 5, "XSP")


@pytest.mark.asyncio
async def test_summary_only_review_skips_trade_recaps(tmp_path) -> None:
    rows = [_row(trade_date=dt.date(2026, 9, 21)), _row(id=8, trade_date=dt.date(2026, 9, 22))]
    chart = AsyncMock(return_value=(b"png", True))
    with (
        patch(
            "butterfly_guy.services.weekend_review.fetch_closed_trades",
            new=AsyncMock(return_value=rows),
        ),
        patch("butterfly_guy.services.weekend_review.build_eod_chart_for_row", new=chart),
        patch(
            "butterfly_guy.services.weekend_review.build_combined_performance_chart_png",
            return_value=b"png",
        ),
    ):
        result = await send_weekend_review(
            AsyncMock(),
            underlying="NDX",
            reference=dt.date(2026, 9, 26),
            notifier=None,
            dry_run=True,
            dry_run_dir=tmp_path,
            include_trade_recaps=False,
        )

    assert result.weekly_trade_count == 2
    assert result.messages_sent == 2
    chart.assert_not_awaited()
