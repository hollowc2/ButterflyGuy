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
    trade_point_from_row,
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
    assert trade_pnl_dollars(-2.29, 2) == -458.0


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
    # Equity is cumulative PnL starting at zero, so this is drawdown against peak
    # profit, not against account capital. The old "Portfolio Drawdown" heading
    # invited the second reading, which overstates the risk considerably.
    assert "Drawdown from peak PnL" in html_doc
    assert "Return Distribution" in html_doc
    assert "Trade Log" in html_doc
    assert "Paper Trading" in html_doc
    assert "drawdownChart" in html_doc
    assert "returnDistributionChart" in html_doc
    assert "End of Day exit" in html_doc
    assert "Drawdown exit" in html_doc
    assert 'data-bucket="100"' in html_doc
    assert 'data-bucket="250"' in html_doc
    assert "Fit curve" in html_doc
    assert "hideNoTradesToggle" in html_doc
    assert "<details class=\"panel trade-log-panel\" open>" in html_doc
    assert "max_trades_reached (1)" in html_doc


def test_performance_report_shows_entire_history_and_fill_model_cohorts() -> None:
    legacy = _trade(trade_date=dt.date(2026, 7, 20), pnl_dollars=500.0)
    mark = TradePoint(
        **{
            **_trade(
                trade_date=dt.date(2026, 7, 21), pnl_dollars=-50.0
            ).__dict__,
            "paper_fill_model": "mark_v1",
        }
    )

    html_doc = render_report_html(
        underlying="SPX",
        trades=[legacy, mark],
        no_trade_days=[],
        generated_at=dt.datetime(2026, 7, 22, tzinfo=dt.timezone.utc),
    )

    # The page is a static snapshot regenerated after each session, so the meta
    # line deliberately no longer reads as a real-time feed.
    assert "Entire history · 2 trades · Paper results through 2026-07-21" in html_doc
    assert "<span class=\"summary-meta\">2 trades</span>" in html_doc
    assert "const chartData = " in html_doc
    assert html_doc.count('"paper_fill_model": "legacy"') == 1
    assert html_doc.count('"paper_fill_model": "mark_v1"') == 1
    assert "Fill Model Cohorts" in html_doc
    assert "legacy" in html_doc
    assert "PnL $+500" in html_doc
    assert "PnL $-50" in html_doc


def test_trade_point_reads_fill_model_from_json_metadata() -> None:
    row = {
        "trade_date": dt.date(2026, 7, 21),
        "direction": "CALL",
        "wing_width": 30,
        "center_strike": 5000.0,
        "lower_strike": 4970.0,
        "upper_strike": 5030.0,
        "entry_price": 2.5,
        "exit_price": 1.0,
        "pnl": -1.5,
        "quantity": 1,
        "metadata": '{"paper_fill_model":"mark_v1"}',
    }

    assert trade_point_from_row(row).paper_fill_model == "mark_v1"


def test_render_trade_table_rows_include_no_trade_day() -> None:
    trades = [_trade(trade_date=dt.date(2026, 3, 17), pnl_dollars=100.0)]
    no_trade_days = [NoTradeDay(dt.date(2026, 3, 18), "Halted", "Daily loss limit reached")]
    rows = render_trade_table_rows(trades, no_trade_days)
    assert "Daily loss limit reached" in rows
    assert "Halted" in rows
    assert "data-row-type='trade'" in rows
    assert "class='muted no-trade-row'" in rows


def test_render_placeholder_html() -> None:
    html_doc = render_placeholder_html(
        underlying="SPX",
        generated_at=dt.datetime(2026, 6, 6, 13, 15, tzinfo=dt.timezone.utc),
    )
    assert "No closed trades yet" in html_doc


def test_regenerated_data_stays_out_of_executable_script() -> None:
    """Per-run data must stay in the non-executable JSON block.

    The published page's CSP allows inline scripts by sha256 hash and does not
    permit 'unsafe-inline'. CSP script-src does not apply to a
    <script type="application/json"> block, so data can change freely there. If
    it is inlined back into the executable script instead, that script's hash
    changes on every regeneration, the browser silently refuses to run it, and
    the page renders empty with no visible error. This pins the invariant.
    """
    import re

    def render(pnls: list[float], start_day: int, generated_day: int) -> str:
        trades = [
            _trade(trade_date=dt.date(2026, 7, start_day + i), pnl_dollars=pnl)
            for i, pnl in enumerate(pnls)
        ]
        return render_report_html(
            underlying="SPX",
            trades=trades,
            no_trade_days=[],
            generated_at=dt.datetime(2026, 7, generated_day, tzinfo=dt.timezone.utc),
        )

    first = render([500.0, -50.0], 20, 22)
    second = render([-125.5, 2280.0, -75.25, 640.0], 6, 30)

    pattern = re.compile(
        r"<script(?P<attrs>(?:\s[^>]*)?)>(?P<body>.*?)</script\s*>", re.DOTALL
    )

    def executable_scripts(doc: str) -> list[str]:
        return [
            m.group("body")
            for m in pattern.finditer(doc)
            if "src=" not in m.group("attrs")
            and "application/json" not in m.group("attrs")
        ]

    first_scripts = executable_scripts(first)
    assert len(first_scripts) == 1, "expected exactly one executable inline script"

    # Different trades, different count, different dates -- the executable
    # script must be byte-identical regardless.
    assert first_scripts[0] == executable_scripts(second)[0], (
        "the executable inline script changed between runs; per-run data has "
        "leaked into it and the deployed CSP hash will no longer match"
    )

    # The data must actually be present, in exactly one data block.
    assert first.count('id="chart-data"') == 1
    data_block = re.search(
        r'<script type="application/json" id="chart-data">(.*?)</script>',
        first,
        re.DOTALL,
    )
    assert data_block is not None

    # A script element's content is raw text, so the only real hazard is a
    # "</script" sequence. These must be \uXXXX-escaped, not HTML entities --
    # entities are never decoded inside a script element and would corrupt the
    # data on the way through JSON.parse().
    for char in ("<", ">", "&"):
        assert char not in data_block.group(1), (
            f"raw {char!r} in the JSON data block; use a \\uXXXX escape"
        )
