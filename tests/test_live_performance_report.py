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
    no_trade_payload,
    no_trade_reason,
    performance_script,
    render_placeholder_html,
    render_report_html,
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
    assert (payload[1]["width"], payload[1]["vix"], payload[1]["spot"]) == (30, 18.0, 4980.0)


def _page_data(html_doc: str) -> dict:
    import json
    import re

    block = re.search(
        r'<script type="application/json" id="page-data">(.*?)</script>', html_doc, re.DOTALL
    )
    assert block is not None
    return json.loads(block.group(1))


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
        generated_at=dt.datetime(2026, 6, 6, 20, 30, tzinfo=dt.timezone.utc),
    )
    # Summary blocks, then the running total, then the detail sections.
    order = ['id="netPnl"', 'id="latest"', 'id="equityChart"', 'id="ddChart"',
             'id="sortedChart"', 'id="bdTable"', 'id="cal"', 'id="logBody"']
    positions = [html_doc.index(marker) for marker in order]
    assert positions == sorted(positions)
    assert "Reading the numbers" not in html_doc
    assert 'href="strategy/"' in html_doc
    assert '<script src="/assets/vendor/chart.umd.min.js"></script>' in html_doc
    assert '<script src="performance.js?v=' in html_doc

    data = _page_data(html_doc)
    assert [t["pnl"] for t in data["trades"]] == [100.0, -50.0]
    assert data["noTrade"] == [
        {"date": "2026-03-19", "status": "No trade", "reason": "max_trades_reached (1)"}
    ]
    assert data["builtAt"] == "Jun 6, 1:30 PM PDT"


def test_performance_report_keeps_fill_model_per_trade() -> None:
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

    models = [t["paper_fill_model"] for t in _page_data(html_doc)["trades"]]
    assert models == ["legacy", "mark_v1"]


def test_page_script_reads_every_element_it_renders_into() -> None:
    import re

    html_doc = render_report_html(
        underlying="SPX",
        trades=[_trade(trade_date=dt.date(2026, 3, 17), pnl_dollars=100.0)],
        no_trade_days=[],
        generated_at=dt.datetime(2026, 6, 6, tzinfo=dt.timezone.utc),
    )
    ids = set(re.findall(r"getElementById\('([A-Za-z]+)'\)", performance_script()))
    assert ids, "expected the page script to look up elements by id"
    missing = sorted(i for i in ids if f'id="{i}"' not in html_doc)
    assert missing == []


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


def test_no_trade_payload_drops_weekends() -> None:
    days = [
        NoTradeDay(dt.date(2026, 3, 20), "Halted", "Daily loss limit reached"),  # Friday
        NoTradeDay(dt.date(2026, 3, 21), "No trade", "No trade"),  # Saturday
        NoTradeDay(dt.date(2026, 3, 22), "No trade", "No trade"),  # Sunday
    ]
    assert no_trade_payload(days) == [
        {"date": "2026-03-20", "status": "Halted", "reason": "Daily loss limit reached"}
    ]


def test_render_placeholder_html() -> None:
    html_doc = render_placeholder_html(
        underlying="SPX",
        generated_at=dt.datetime(2026, 6, 6, 13, 15, tzinfo=dt.timezone.utc),
    )
    assert "No closed trades yet" in html_doc
    # The placeholder is a real published page when there are no closed trades,
    # so it has to honour the same audit fixes as the main report: no
    # third-party origins (the site CSP blocks them), a way back to the site,
    # and no wording that implies a live feed.
    assert "Paper Performance" in html_doc
    assert "Live Performance" not in html_doc
    assert '<a class="site-link" href="/">' in html_doc
    assert 'href="https://github.com/hollowc2/ButterflyGuy"' in html_doc
    assert 'href="strategy/"' in html_doc
    assert "/assets/fonts.css" in html_doc
    for origin in ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net"):
        assert origin not in html_doc


def test_regenerated_data_stays_out_of_executable_script() -> None:
    """Per-run data must stay in the non-executable JSON block.

    The published page's CSP allows inline scripts only by sha256 hash and does
    not permit 'unsafe-inline'. The page therefore ships no executable inline
    script at all: its code is the same-origin performance.js, and CSP script-src
    does not apply to a <script type="application/json"> block, so the numbers
    can change freely there. If data or code is inlined into an executable
    script instead, the browser silently refuses to run it and the page renders
    empty with no visible error. This pins the invariant.
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
    for doc in (first, second):
        inline = [
            m.group("body")
            for m in pattern.finditer(doc)
            if "src=" not in m.group("attrs")
            and "application/json" not in m.group("attrs")
            and m.group("body").strip()
        ]
        assert inline == [], "executable inline script found; it would need a CSP hash"

    # The script reference is versioned by the file's content, not the data.
    tag = re.compile(r'<script src="performance\.js\?v=[0-9a-f]{10}"></script>')
    assert tag.findall(first) == tag.findall(second) != []

    # The data must actually be present, in exactly one data block.
    assert first.count('id="page-data"') == 1
    data_block = re.search(
        r'<script type="application/json" id="page-data">(.*?)</script>',
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
