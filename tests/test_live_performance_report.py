"""Tests for live performance report generation."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.backtest.metrics import max_drawdown
from butterfly_guy.reports.live_performance import (
    DrawdownPoint,
    NoTradeDay,
    TradePoint,
    chart_payload,
    compute_stats,
    cumulative_equity,
    drawdown_series,
    is_drawdown_exit,
    no_trade_reason,
    render_placeholder_html,
    render_report_html,
    render_trade_table_rows,
    trade_pnl_dollars,
)


def _trade(
    *,
    trade_date: dt.date,
    pnl_dollars: float,
    exit_reason: str = "end_of_day",
    dd_at_exit_pct: float | None = None,
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
        dd_at_exit_pct=dd_at_exit_pct,
    )


def test_trade_pnl_dollars_multiplies_by_contract_size() -> None:
    assert trade_pnl_dollars(-2.29) == -229.0


def test_compute_stats() -> None:
    stats = compute_stats([100.0, -50.0, 200.0, -25.0])
    assert stats.total_pnl == 225.0
    assert stats.win_rate == 50.0
    assert stats.average == 56.25
    assert stats.best == 200.0
    assert stats.worst == -50.0
    assert stats.profit_factor == 4.0
    assert stats.trade_count == 4


def test_cumulative_equity_and_drawdown_series() -> None:
    pnls = [100.0, -50.0, 25.0]
    assert cumulative_equity(pnls) == [100.0, 50.0, 75.0]
    series = drawdown_series(pnls)
    assert series == [
        DrawdownPoint(0.0, 0.0, 100.0, 100.0),
        DrawdownPoint(50.0, 50.0, 50.0, 100.0),
        DrawdownPoint(25.0, 25.0, 75.0, 100.0),
    ]
    assert max_drawdown(pnls) == 50.0


def test_is_drawdown_exit() -> None:
    assert is_drawdown_exit("drawdown_morning")
    assert is_drawdown_exit("drawdown_afternoon")
    assert not is_drawdown_exit("end_of_day")


def test_no_trade_reason_mapping() -> None:
    assert no_trade_reason(halted=True, event_type=None, event_data=None) == (
        "Halted",
        "Daily loss limit reached",
    )
    assert no_trade_reason(
        halted=False,
        event_type="entry_blocked",
        event_data={"reason": "max_trades_reached (1)"},
    ) == ("No trade", "max_trades_reached (1)")
    assert no_trade_reason(halted=False, event_type="no_candidates", event_data={}) == (
        "No trade",
        "No candidates found",
    )


def test_chart_payload_includes_drawdown_fields() -> None:
    trades = [
        _trade(trade_date=dt.date(2026, 3, 17), pnl_dollars=100.0),
        _trade(
            trade_date=dt.date(2026, 3, 18),
            pnl_dollars=-60.0,
            exit_reason="drawdown_morning",
            dd_at_exit_pct=61.1,
        ),
    ]
    payload = chart_payload(trades)
    assert payload[0]["equity"] == 100.0
    assert payload[1]["drawdown_dollars"] == 60.0
    assert payload[1]["is_drawdown_exit"] is True
    assert payload[1]["dd_at_exit_pct"] == 61.1


def test_render_report_html_contains_sections() -> None:
    trades = [
        _trade(trade_date=dt.date(2026, 3, 17), pnl_dollars=100.0),
        _trade(trade_date=dt.date(2026, 3, 18), pnl_dollars=-50.0),
    ]
    no_trade_days = [
        NoTradeDay(dt.date(2026, 3, 19), "No trade", "max_trades_reached (1)"),
    ]
    html_doc = render_report_html(
        underlying="SPX",
        trades=trades,
        no_trade_days=no_trade_days,
        generated_at=dt.datetime(2026, 6, 6, 13, 15, tzinfo=dt.timezone.utc),
    )
    assert "Equity Curve" in html_doc
    assert "Portfolio Drawdown" in html_doc
    assert "Return Distribution" in html_doc
    assert "Trade Log" in html_doc
    assert "Paper Trading" in html_doc
    assert "drawdownChart" in html_doc
    assert "returnDistributionChart" in html_doc
    assert 'data-bucket="250"' in html_doc
    assert "Fit curve" in html_doc
    assert "max_trades_reached (1)" in html_doc


def test_render_trade_table_rows_include_no_trade_day() -> None:
    trades = [_trade(trade_date=dt.date(2026, 3, 17), pnl_dollars=100.0)]
    no_trade_days = [NoTradeDay(dt.date(2026, 3, 18), "Halted", "Daily loss limit reached")]
    rows = render_trade_table_rows(trades, no_trade_days)
    assert "Daily loss limit reached" in rows
    assert "Halted" in rows


def test_render_placeholder_html() -> None:
    html_doc = render_placeholder_html(
        underlying="SPX",
        generated_at=dt.datetime(2026, 6, 6, 13, 15, tzinfo=dt.timezone.utc),
    )
    assert "No closed trades yet" in html_doc
