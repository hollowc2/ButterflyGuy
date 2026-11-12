"""Live trading performance report — stats, drawdown, and HTML rendering.

The page script ships as a separate same-origin file (``performance.js``) so the
site's ``script-src 'self'`` CSP covers it without an inline-script hash; every
per-run number travels in the page's non-executable JSON data block.
"""

# Generated HTML/CSS strings in this module intentionally exceed 100 columns.
# ruff: noqa: E501

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from butterfly_guy.backtest.metrics import max_drawdown, profit_factor
from butterfly_guy.core.time_utils import EASTERN, PACIFIC

PERFORMANCE_SCRIPT_NAME = "performance.js"
_ASSET_DIR = Path(__file__).with_name("performance_page")

NO_TRADE_EVENTS = frozenset({
    "entry_blocked",
    "gap_regime_skip",
    "no_candidates",
    "entry_exhausted",
})


@dataclass(frozen=True)
class TradePoint:
    trade_date: dt.date
    direction: str
    wing_width: int
    center_strike: float
    lower_strike: float
    upper_strike: float
    entry_price: float
    entry_time: dt.datetime | None
    exit_price: float | None
    exit_time: dt.datetime | None
    exit_reason: str | None
    pnl_dollars: float
    peak_value: float | None
    vix: float | None
    entry_spot: float | None
    dd_at_exit_pct: float | None
    paper_fill_model: str = "legacy"
    # P&L at the marketable prices observed at fill time; None when not recorded.
    executable_pnl_dollars: float | None = None


@dataclass(frozen=True)
class NoTradeDay:
    trade_date: dt.date
    status: str
    reason: str


@dataclass(frozen=True)
class ReportStats:
    total_pnl: float
    win_rate: float
    average: float
    best: float
    worst: float
    profit_factor: float
    max_drawdown: float
    trade_count: int


@dataclass(frozen=True)
class DrawdownPoint:
    drawdown_dollars: float
    drawdown_pct: float
    equity: float
    peak_equity: float


def trade_pnl_dollars(pnl: float | int, quantity: int = 1) -> float:
    return float(pnl) * 100.0 * quantity


def is_drawdown_exit(exit_reason: str | None) -> bool:
    return bool(exit_reason and exit_reason.startswith("drawdown_"))


def cumulative_equity(pnls: list[float]) -> list[float]:
    running = 0.0
    equity: list[float] = []
    for pnl in pnls:
        running += pnl
        equity.append(running)
    return equity


def drawdown_series(pnls: list[float]) -> list[DrawdownPoint]:
    points: list[DrawdownPoint] = []
    equity = 0.0
    peak = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        dd_dollars = peak - equity
        dd_pct = (dd_dollars / peak * 100.0) if peak > 0 else 0.0
        points.append(
            DrawdownPoint(
                drawdown_dollars=dd_dollars,
                drawdown_pct=dd_pct,
                equity=equity,
                peak_equity=peak,
            )
        )
    return points


def compute_stats(pnls: list[float]) -> ReportStats:
    if not pnls:
        return ReportStats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)
    wins = [p for p in pnls if p > 0]
    total = sum(pnls)
    return ReportStats(
        total_pnl=total,
        win_rate=len(wins) / len(pnls) * 100.0,
        average=total / len(pnls),
        best=max(pnls),
        worst=min(pnls),
        profit_factor=profit_factor(pnls),
        max_drawdown=max_drawdown(pnls),
        trade_count=len(pnls),
    )


def format_et_time(value: dt.datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone(EASTERN).strftime("%H:%M")


def duration_minutes(start: dt.datetime | None, end: dt.datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return round((end - start).total_seconds() / 60)


def no_trade_reason(*, halted: bool, event_type: str | None, event_data: dict[str, Any] | None) -> tuple[str, str]:
    if halted:
        return "Halted", "Daily loss limit reached"
    if event_type == "entry_blocked":
        reason = (event_data or {}).get("reason", "Entry blocked")
        return "No trade", str(reason)
    if event_type == "gap_regime_skip":
        reason = (event_data or {}).get("reason", "Gap regime skip")
        return "No trade", str(reason)
    if event_type == "no_candidates":
        return "No trade", "No candidates found"
    if event_type == "entry_exhausted":
        return "No trade", "Entry ladder exhausted"
    return "No trade", "No trade"


def _parse_metadata(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def executable_pnl_points(row: dict[str, Any], metadata: dict[str, Any]) -> float | None:
    """Per-contract P&L at marketable prices, or None when the trade did not record them.

    Entry uses the ask-side estimate (ask + slippage + commission) and exit the
    bid-side estimate (bid - slippage - commission). A cash-settled exit has no
    execution cost, so its settlement value is used as-is.
    """
    entry = (metadata.get("entry_execution_diagnostics") or {}).get(
        "marketable_entry_estimate"
    )
    exit_value = (metadata.get("exit_execution_diagnostics") or {}).get(
        "marketable_exit_estimate"
    )
    if (
        exit_value is None
        and row.get("exit_reason") == "cash_settled"
        and row.get("exit_price") is not None
    ):
        exit_value = row["exit_price"]
    if entry is None or exit_value is None:
        return None
    return float(exit_value) - float(entry)


def trade_point_from_row(row: dict[str, Any]) -> TradePoint:
    metadata = _parse_metadata(row.get("metadata"))
    exit_parity = metadata.get("exit_mark_parity") or {}
    dd_at_exit = exit_parity.get("live_drawdown_pct")
    pnl = row.get("pnl")
    executable = executable_pnl_points(row, metadata)
    return TradePoint(
        trade_date=row["trade_date"],
        direction=str(row["direction"]),
        wing_width=int(row["wing_width"]),
        center_strike=float(row["center_strike"]),
        lower_strike=float(row["lower_strike"]),
        upper_strike=float(row["upper_strike"]),
        entry_price=float(row["entry_price"]),
        entry_time=row.get("entry_time"),
        exit_price=float(row["exit_price"]) if row.get("exit_price") is not None else None,
        exit_time=row.get("exit_time"),
        exit_reason=row.get("exit_reason"),
        pnl_dollars=(
            trade_pnl_dollars(float(pnl), int(row.get("quantity") or 1))
            if pnl is not None
            else 0.0
        ),
        peak_value=float(row["peak_value"]) if row.get("peak_value") is not None else None,
        vix=float(metadata["vix"]) if metadata.get("vix") is not None else None,
        entry_spot=float(metadata["entry_spot"]) if metadata.get("entry_spot") is not None else None,
        dd_at_exit_pct=float(dd_at_exit) if dd_at_exit is not None else None,
        paper_fill_model=str(metadata.get("paper_fill_model") or "legacy"),
        executable_pnl_dollars=(
            trade_pnl_dollars(executable, int(row.get("quantity") or 1))
            if executable is not None
            else None
        ),
    )


def chart_payload(trades: list[TradePoint]) -> list[dict[str, Any]]:
    equity = 0.0
    dd_points = drawdown_series([t.pnl_dollars for t in trades])
    payload: list[dict[str, Any]] = []
    for idx, (trade, dd) in enumerate(zip(trades, dd_points, strict=True)):
        equity += trade.pnl_dollars
        payload.append({
            "index": idx + 1,
            "date": trade.trade_date.isoformat(),
            "direction": trade.direction,
            "strikes": f"{trade.lower_strike:.0f} / {trade.center_strike:.0f} / {trade.upper_strike:.0f}",
            "entry_price": trade.entry_price,
            "peak_value": trade.peak_value,
            "exit_price": trade.exit_price,
            "entry_time": format_et_time(trade.entry_time),
            "exit_time": format_et_time(trade.exit_time),
            "duration_min": duration_minutes(trade.entry_time, trade.exit_time),
            "exit_reason": trade.exit_reason or "—",
            "dd_at_exit_pct": trade.dd_at_exit_pct,
            "is_drawdown_exit": is_drawdown_exit(trade.exit_reason),
            "paper_fill_model": trade.paper_fill_model,
            "pnl": trade.pnl_dollars,
            "equity": equity,
            "drawdown_dollars": dd.drawdown_dollars,
            "drawdown_pct": dd.drawdown_pct,
            "peak_equity": dd.peak_equity,
            "width": trade.wing_width,
            "vix": trade.vix,
            "spot": trade.entry_spot,
        })
    return payload


def no_trade_payload(days: list[NoTradeDay]) -> list[dict[str, str]]:
    """Weekday sessions without a trade; weekends are not sessions, so they are dropped."""
    return [
        {"date": day.trade_date.isoformat(), "status": day.status, "reason": day.reason}
        for day in days
        if day.trade_date.weekday() < 5
    ]


def performance_script() -> str:
    return (_ASSET_DIR / PERFORMANCE_SCRIPT_NAME).read_text(encoding="utf-8")


def _script_version() -> str:
    return hashlib.sha256(performance_script().encode("utf-8")).hexdigest()[:10]


def _built_at(generated_at: dt.datetime) -> str:
    local = generated_at.astimezone(PACIFIC)
    return f"{local:%b} {local.day}, {local.hour % 12 or 12}:{local:%M %p %Z}"


def _json_data_block(payload: dict[str, Any]) -> str:
    """Serialise payload for a <script type="application/json"> block.

    A script element's content is raw text, so HTML entities are never decoded
    inside it and the one real hazard is a "</script" sequence in the data. JSON
    \\uXXXX escapes for < > & remove that hazard while still round-tripping through
    JSON.parse() unchanged, which HTML entity escaping would not.
    """
    encoded = json.dumps(payload)
    return (
        encoded.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    )


_SOURCE_URL = "https://github.com/hollowc2/ButterflyGuy"


def render_placeholder_html(*, underlying: str, generated_at: dt.datetime) -> str:
    stamp = generated_at.astimezone(PACIFIC).strftime("%Y-%m-%d %H:%M %Z")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Butterfly Guy — {html.escape(underlying)} Paper Performance</title>
  <link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fonts/inter-var-latin.woff2">
  <link rel="stylesheet" href="/assets/fonts.css">
  <style>{_BASE_CSS}</style>
</head>
<body>
<main>
  <nav class="site-nav">
    <a class="site-link" href="/"><span aria-hidden="true">←</span>billybitcoin.cloud</a>
    <a class="site-link" href="{_SOURCE_URL}" target="_blank" rel="noopener noreferrer">source on GitHub<span aria-hidden="true">↗</span></a>
    <a class="site-link site-link-feature" href="strategy/">strategy explained<span aria-hidden="true">→</span></a>
  </nav>

  <h1>Butterfly Guy — {html.escape(underlying)} Paper Performance</h1>
  <div class="sub">Paper trading · Static snapshot, last built {html.escape(stamp)}</div>
  <section class="panel empty">No closed trades yet.</section>
</main>
</body>
</html>"""


def render_report_html(
    *,
    underlying: str,
    trades: list[TradePoint],
    no_trade_days: list[NoTradeDay],
    generated_at: dt.datetime,
) -> str:
    page_json = _json_data_block({
        "trades": chart_payload(trades),
        "noTrade": no_trade_payload(no_trade_days),
        "builtAt": _built_at(generated_at),
    })

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Butterfly Guy — {html.escape(underlying)} Paper Performance</title>
  <link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fonts/inter-var-latin.woff2">
  <link rel="stylesheet" href="/assets/fonts.css">
  <script src="/assets/vendor/chart.umd.min.js"></script>
  <style>{_REPORT_CSS}</style>
</head>
<body>
<main>
  <nav class="site-nav">
    <a class="site-link" href="/"><span aria-hidden="true">←</span>billybitcoin.cloud</a>
    <a class="site-link" href="{_SOURCE_URL}" target="_blank" rel="noopener noreferrer">source on GitHub<span aria-hidden="true">↗</span></a>
    <a class="site-link site-link-feature" href="strategy/">how the strategy works<span aria-hidden="true">→</span></a>
  </nav>

  <header>
    <div class="eyebrow">Butterfly Guy · paper trading</div>
    <h1>{html.escape(underlying)} 0DTE butterfly, one trade a day</h1>
    <p class="lede">Each session the bot buys one same-day {html.escape(underlying)} butterfly a little away from the market, in the morning. Most days it loses part of the small debit it paid. Now and then {html.escape(underlying)} finishes near the center strike and the fly pays many times its cost. Those few days are the whole strategy.</p>
    <div class="meta" id="meta"></div>
  </header>

  <div class="hero">
    <div class="panel">
      <div class="label">Net paper P&amp;L</div>
      <div class="big" id="netPnl"></div>
      <div class="big-sub" id="netSub"></div>
      <div class="kpis" id="kpis"></div>
    </div>
    <div class="panel" id="latest"></div>
  </div>

  <section aria-labelledby="h-equity">
    <h2 id="h-equity">Running total</h2>
    <p class="section-lede" id="equityLede"></p>
    <div class="panel">
      <div class="chart-box"><canvas id="equityChart" role="img"></canvas></div>
      <div class="legend"><span><i class="sw" style="background:var(--accent)"></i>Cumulative P&amp;L</span><span><i class="sw" style="background:var(--up);border-radius:50%"></i>Single-day gain over $1,000</span></div>
      <div class="label" style="margin-top:22px">Below the running high</div>
      <div class="chart-box short"><canvas id="ddChart" role="img"></canvas></div>
      <p class="chart-caption" id="ddCaption"></p>
    </div>
  </section>

  <section aria-labelledby="h-shape">
    <h2 id="h-shape">Lots of small losses, a few big wins</h2>
    <p class="section-lede" id="shapeLede"></p>
    <div class="split">
      <div class="panel">
        <div class="share-row"><span>Trades</span><div class="share-bar" id="shareCount"></div></div>
        <div class="share-row"><span>Dollars</span><div class="share-bar" id="shareDollars"></div></div>
        <div class="legend"><span><i class="sw" style="background:var(--up-mark)"></i>Winners</span><span><i class="sw" style="background:var(--down-mark)"></i>Losers</span></div>
      </div>
      <div class="panel"><p class="callout" id="concentration"></p></div>
    </div>
    <div class="panel">
      <div class="chart-box"><canvas id="sortedChart" role="img"></canvas></div>
      <p class="chart-caption">Each bar is one trade's P&amp;L for one contract, sorted from worst to best. Hover a bar for the date and details.</p>
    </div>
  </section>


  <section aria-labelledby="h-where">
    <h2 id="h-where">Where the money comes from</h2>
    <p class="section-lede">Split the trades by how they ended, by month, by fly width, by direction or by VIX at entry.</p>
    <div class="panel">
      <div class="seg" role="group" aria-label="Group trades by" id="bdControls">
        <button type="button" data-key="exit" aria-pressed="true">How it ended</button>
        <button type="button" data-key="month" aria-pressed="false">Month</button>
        <button type="button" data-key="width" aria-pressed="false">Width</button>
        <button type="button" data-key="dir" aria-pressed="false">Direction</button>
        <button type="button" data-key="vix" aria-pressed="false">VIX</button>
      </div>
      <div class="table-wrap" style="margin-top:0"><table class="bd" id="bdTable"></table></div>
    </div>
  </section>

  <section aria-labelledby="h-cal">
    <h2 id="h-cal">Every session</h2>
    <p class="section-lede">One square per weekday. Click a trading day to jump to it in the log.</p>
    <div class="panel">
      <div class="cal-wrap"><div class="cal" id="cal"></div></div>
      <div class="cal-legend">
        <span>Loss<span class="ramp" id="rampNeg"></span></span>
        <span><span class="ramp" id="rampPos"></span>Gain</span>
        <span><i class="cell" style="display:inline-block;width:12px;height:12px"></i>No trade</span>
        <span><i class="cell halt" style="display:inline-block;width:12px;height:12px"></i>Halted by daily loss limit</span>
      </div>
    </div>
  </section>

  <section aria-labelledby="h-log">
    <h2 id="h-log">Trade log</h2>
    <p class="section-lede">Newest first. <b>Peak</b> and <b>Exit</b> are shown as multiples of what the fly cost, so 8.3× means it was worth 8.3 times the debit paid.</p>
    <div class="panel">
      <div class="log-tools">
        <div class="seg" role="group" aria-label="Filter trades" id="logFilter">
          <button type="button" data-f="all" aria-pressed="true">All</button>
          <button type="button" data-f="win" aria-pressed="false">Winners</button>
          <button type="button" data-f="loss" aria-pressed="false">Losers</button>
          <button type="button" data-f="held" aria-pressed="false">Held to the close</button>
          <button type="button" data-f="stop" aria-pressed="false">Trailing stop</button>
        </div>
        <span class="count" id="logCount"></span>
      </div>
      <div class="table-wrap">
        <table class="log">
          <thead><tr>
            <th>Date</th><th>Fly</th><th class="r">VIX</th><th>Held (ET)</th>
            <th class="r">Paid</th><th class="r">Peak</th><th class="r">Exit</th><th>How it ended</th><th class="r">P&amp;L</th>
          </tr></thead>
          <tbody id="logBody"></tbody>
        </table>
      </div>
      <button type="button" class="more" id="logMore"></button>
    </div>
  </section>

</main>

<div class="tip" id="tip" hidden></div>

<!-- Generator-emitted data. A non-executable application/json block, so CSP
     script-src does not apply and regenerating the numbers never needs a hash. -->
<script type="application/json" id="page-data">
{page_json}
</script>
<script src="{PERFORMANCE_SCRIPT_NAME}?v={_script_version()}"></script>
</body>
</html>"""


_BASE_CSS = """
:root {
  color-scheme: dark;
  --bg: #0c0c0c;
  --text: #e8e2d6;
  --accent: #c8922a;
  /* --muted carries every stat label, section heading and table header, so it has
     to clear WCAG AA for body text (4.5:1). #948d87 is 5.98:1 on --bg and 5.73:1
     on the #121212 panels; the previous #6a6460 was only 3.36:1 / 3.22:1. */
  --muted: #948d87;
  --border: rgba(232, 226, 214, 0.1);
  --up: #6aaa78;
  /* #cc5555 is 4.46:1 on the #121212 panels — just under AA for the 13px table
     cells. #d66a6a is 5.47:1. Chart strokes keep the deeper red (graphics only
     need 3:1). */
  --down: #d66a6a;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
}
body { margin: 0; }
main { max-width: 1320px; margin: 0 auto; padding: 28px 24px 48px; }
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.site-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}
.site-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 13px 6px 11px;
  background: #121212;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--muted);
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px;
  letter-spacing: 0.02em;
  text-decoration: none;
  transition: color 120ms ease, border-color 120ms ease;
}
.site-link:hover,
.site-link:focus-visible {
  color: var(--text);
  border-color: rgba(200, 146, 42, 0.45);
}
.site-link span { color: var(--accent); }
.site-link-feature {
  color: var(--accent);
  background: rgba(200, 146, 42, 0.1);
  border-color: rgba(200, 146, 42, 0.4);
}
.site-link-feature:hover,
.site-link-feature:focus-visible {
  color: var(--text);
  background: rgba(200, 146, 42, 0.18);
  border-color: var(--accent);
}
h1 { font-size: 28px; margin: 0 0 8px; font-weight: 600; }
h2 { font-size: 15px; margin: 28px 0 10px; color: var(--muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
.sub { color: var(--muted); font-size: 14px; }
.badge {
  display: inline-block;
  background: rgba(200, 146, 42, 0.15);
  color: var(--accent);
  border: 1px solid rgba(200, 146, 42, 0.35);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
  margin-right: 8px;
}
/* A wrapping flex row rather than a fixed 7-column track list. Seven tiles can
   never divide evenly into 2-6 columns, so a grid always strands the last tile at
   partial width. With flex the tiles left on the final row grow to fill it, so the
   row reads as deliberate at every viewport and needs no breakpoint. */
.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}
.stat {
  flex: 1 1 140px;
  background: #121212;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
}
/* The cohort row (the only .stats following an h2) holds two tiles; cap them so
   they do not stretch to half the page each. */
h2 + .stats .stat { max-width: 240px; }
.label { color: var(--muted); font-size: 12px; }
.value {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 20px;
  font-weight: 500;
  margin-top: 6px;
}
.panel {
  background: #121212;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  overflow-x: auto;
}
.chart-panel { min-height: 220px; }
.chart-tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.legend-dot {
  display: inline-block;
  flex: 0 0 auto;
  border-radius: 999px;
}
.legend-dot-standard {
  width: 8px;
  height: 8px;
  background: #c8922a;
}
.legend-dot-drawdown {
  width: 12px;
  height: 12px;
  background: #cc5555;
}
.segmented {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  background: #0f0f0f;
  border: 1px solid var(--border);
  border-radius: 8px;
}
.bucket-control {
  color: var(--muted);
  background: transparent;
  border: 0;
  border-radius: 6px;
  padding: 7px 11px;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px;
  cursor: pointer;
}
.bucket-control.active {
  color: var(--text);
  background: rgba(200, 146, 42, 0.18);
}
.toggle {
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
}
.toggle input { accent-color: var(--accent); }
.trade-log-panel {
  padding-top: 10px;
}
.section-summary {
  list-style: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 15px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  user-select: none;
}
.section-summary::-webkit-details-marker { display: none; }
.section-summary::before {
  content: "▾";
  color: var(--accent);
  font-size: 13px;
  margin-right: 8px;
}
.trade-log-panel:not([open]) .section-summary::before {
  content: "▸";
}
.section-summary > span:first-child {
  display: inline-flex;
  align-items: center;
}
.summary-meta {
  color: var(--muted);
  font-size: 12px;
  text-transform: none;
  letter-spacing: 0;
}
.table-tools {
  display: flex;
  justify-content: flex-end;
  margin: 12px 0 10px;
}
.empty { padding: 40px; text-align: center; color: var(--muted); }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  white-space: nowrap;
}
th, td {
  border-bottom: 1px solid var(--border);
  padding: 8px 10px;
  text-align: right;
}
th {
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  background: #0f0f0f;
  position: sticky;
  top: 0;
}
td:first-child, th:first-child,
td:nth-child(2), th:nth-child(2),
td:nth-child(3), th:nth-child(3),
td:nth-child(5), th:nth-child(5),
td:nth-child(6), th:nth-child(6),
td:nth-child(15), th:nth-child(15) { text-align: left; }
.pos { color: var(--up); font-weight: 600; }
.neg { color: var(--down); font-weight: 600; }
tr.muted td { color: var(--muted); }
.chart-note {
  margin: 12px 2px 0;
  max-width: 80ch;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.55;
}
.chart-note b {
  color: var(--text);
  font-weight: 500;
}
@media (max-width: 980px) {
  main { padding: 16px; }
}
"""


_REPORT_CSS = """
:root {
  color-scheme: dark;
  --bg: #0c0c0c;
  --panel: #131211;
  --panel-2: #0f0f0e;
  --text: #e8e2d6;
  --muted: #948d87;
  --faint: #5e5852;
  --border: rgba(232, 226, 214, 0.1);
  --accent: #c8922a;
  --up: #6aaa78;
  --down: #d66a6a;
  --up-mark: #5f9e6d;
  --down-mark: #cc5555;
  --none: #24221f;
  --sans: Inter, ui-sans-serif, system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, monospace;
  font-family: var(--sans);
  background: var(--bg);
  color: var(--text);
}
body { margin: 0; background: var(--bg); color: var(--text); }
main { max-width: 1120px; margin: 0 auto; padding-inline: 20px; padding-block: 28px 64px; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.num, td.r, .value { font-variant-numeric: tabular-nums; }
.pos { color: var(--up); }
.neg { color: var(--down); }

.site-nav { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }
.site-link {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 13px 6px 11px; background: var(--panel);
  border: 1px solid var(--border); border-radius: 999px; color: var(--muted);
  font-family: var(--mono); font-size: 12px; text-decoration: none;
}
.site-link span { color: var(--accent); }
.site-link:hover { color: var(--text); border-color: rgba(200,146,42,.45); }
.site-link-feature { color: var(--accent); background: rgba(200,146,42,.1); border-color: rgba(200,146,42,.4); }

.eyebrow { font-family: var(--mono); font-size: 12px; color: var(--accent); letter-spacing: .06em; text-transform: uppercase; }
h1 { font-size: clamp(26px, 4vw, 34px); font-weight: 600; margin: 8px 0 10px; text-wrap: balance; letter-spacing: -.01em; }
.lede { font-size: 16px; line-height: 1.55; color: #cfc8bb; max-width: 68ch; margin: 0; }
.meta { margin-top: 12px; color: var(--muted); font-size: 13px; }
.meta b { color: var(--text); font-weight: 500; }

section { margin-top: 44px; }
h2 { font-size: 19px; font-weight: 600; margin: 0 0 6px; text-wrap: balance; }
.section-lede { color: var(--muted); font-size: 14px; line-height: 1.55; margin: 0 0 16px; max-width: 72ch; }
.section-lede b { color: var(--text); font-weight: 500; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 18px; min-width: 0; }

/* Hero */
.hero { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: 14px; margin-top: 28px; }
.label { color: var(--muted); font-size: 12px; letter-spacing: .03em; text-transform: uppercase; }
.big { font-family: var(--mono); font-size: clamp(38px, 6vw, 54px); font-weight: 500; letter-spacing: -.02em; margin: 6px 0 2px; }
.big-sub { color: var(--muted); font-size: 13px; }
.kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px 12px; margin-top: 20px; padding-top: 18px; border-top: 1px solid var(--border); }
.kpi .value { font-family: var(--mono); font-size: 18px; font-weight: 500; margin-top: 4px; }
.kpi .hint { color: var(--faint); font-size: 12px; margin-top: 2px; }

.latest-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.latest-pnl { font-family: var(--mono); font-size: 28px; font-weight: 500; }
.latest-title { font-size: 15px; margin: 8px 0 2px; font-weight: 500; }
.latest-sub { color: var(--muted); font-size: 13px; }
.path { margin-top: 22px; }
.path-track { position: relative; height: 10px; background: var(--panel-2); border: 1px solid var(--border); border-radius: 999px; }
.path-fill { position: absolute; left: 0; top: 0; bottom: 0; background: rgba(200,146,42,.28); border-radius: 999px; }
.path-mark { position: absolute; top: 50%; width: 12px; height: 12px; margin: -6px 0 0 -6px; border-radius: 50%; border: 2px solid var(--panel); }
.path-mark.paid { background: var(--muted); }
.path-mark.peak { background: var(--accent); }
.path-mark.exit { background: var(--text); }
.path-legend { display: flex; justify-content: space-between; gap: 8px; margin-top: 12px; font-size: 12px; color: var(--muted); }
.path-legend div { display: flex; flex-direction: column; gap: 2px; }
.path-legend b { font-family: var(--mono); color: var(--text); font-weight: 500; font-size: 14px; }
.path-legend i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.latest-note { margin: 16px 0 0; font-size: 13.5px; line-height: 1.55; color: #cfc8bb; }

/* Payoff */
.split { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; margin-bottom: 14px; }
.share-row { display: grid; grid-template-columns: 74px minmax(0, 1fr); align-items: center; gap: 10px; font-size: 12px; color: var(--muted); }
.share-row + .share-row { margin-top: 10px; }
.share-bar { display: flex; height: 26px; border-radius: 4px; overflow: hidden; gap: 2px; }
.share-bar div { display: flex; align-items: center; padding: 0 8px; font-family: var(--mono); font-size: 12px; color: #0c0c0c; white-space: nowrap; overflow: hidden; }
.share-bar .w { background: var(--up-mark); }
.share-bar .l { background: var(--down-mark); }
.callout { font-size: 15px; line-height: 1.55; margin: 0; }
.callout b { font-family: var(--mono); font-weight: 500; }
.chart-box { position: relative; height: 260px; }
.chart-box.short { height: 150px; }
.chart-caption { color: var(--muted); font-size: 12.5px; line-height: 1.5; margin: 10px 0 0; }
.chart-caption b { color: var(--text); font-weight: 500; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: var(--muted); margin-top: 10px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.sw { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }

/* Breakdown */
.seg { display: inline-flex; flex-wrap: wrap; gap: 2px; padding: 3px; background: var(--panel-2); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 14px; }
.seg button { color: var(--muted); background: transparent; border: 0; border-radius: 6px; padding: 7px 12px; font: 500 13px var(--sans); cursor: pointer; }
.seg button:hover { color: var(--text); }
.seg button[aria-pressed="true"] { color: var(--text); background: rgba(200,146,42,.18); }
.bd { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.bd th { text-align: left; color: var(--muted); font-weight: 500; font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; padding: 0 10px 8px; border-bottom: 1px solid var(--border); }
.bd td { padding: 10px; border-bottom: 1px solid var(--border); vertical-align: middle; }
.bd tr:last-child td { border-bottom: 0; }
.bd th.r, .bd td.r { text-align: right; font-family: var(--mono); }
.bd .what { min-width: 160px; }
.bd .what small { display: block; color: var(--faint); font-size: 12px; margin-top: 2px; }
.bd .barcell { width: 38%; min-width: 160px; }
.dbar { position: relative; height: 16px; }
.dbar::before { content: ""; position: absolute; left: var(--zero); top: -4px; bottom: -4px; width: 1px; background: var(--faint); }
.dbar div { position: absolute; top: 0; bottom: 0; border-radius: 3px; }
.dbar .p { background: var(--up-mark); }
.dbar .n { background: var(--down-mark); }

/* Calendar */
.cal-wrap { overflow-x: auto; padding-bottom: 4px; }
.cal { display: grid; grid-auto-flow: column; grid-template-rows: 16px repeat(5, 18px); grid-auto-columns: 18px; gap: 4px; width: max-content; }
.cal .dow { font-size: 10px; color: var(--faint); line-height: 18px; padding-right: 6px; }
.cal .mon { font-size: 11px; color: var(--muted); white-space: nowrap; overflow: visible; }
.cell { width: 18px; height: 18px; border-radius: 3px; background: var(--none); border: 0; padding: 0; cursor: default; }
.cell.trade { cursor: pointer; }
.cell.empty { background: transparent; box-shadow: inset 0 0 0 1px rgba(232,226,214,.06); }
.cell.halt { background: repeating-linear-gradient(135deg, #3a2a22 0 3px, #24221f 3px 6px); }
.cell:hover, .cell:focus-visible { outline: 2px solid var(--text); outline-offset: 1px; }
.cal-legend { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; margin-top: 14px; font-size: 12px; color: var(--muted); }
.cal-legend .ramp { display: inline-flex; gap: 2px; margin: 0 6px; }
.cal-legend .ramp i { width: 12px; height: 12px; border-radius: 2px; display: inline-block; }
.cal-legend span { display: inline-flex; align-items: center; gap: 6px; }

.tip { position: fixed; z-index: 10; pointer-events: none; background: #1b1a18; border: 1px solid rgba(232,226,214,.15); border-radius: 8px; padding: 10px 12px; font-size: 12.5px; line-height: 1.5; max-width: 280px; box-shadow: 0 8px 24px rgba(0,0,0,.5); }
.tip b { font-weight: 600; }
.tip .m { font-family: var(--mono); }

/* Log */
.log-tools { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 4px; }
.log-tools .seg { margin-bottom: 0; }
.count { color: var(--muted); font-size: 13px; }
.table-wrap { overflow-x: auto; margin-top: 10px; }
.log { width: 100%; border-collapse: collapse; font-size: 13px; white-space: nowrap; }
.log th { text-align: left; color: var(--muted); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; padding: 8px 10px; border-bottom: 1px solid var(--border); background: var(--panel); position: sticky; top: 0; }
.log td { padding: 9px 10px; border-bottom: 1px solid var(--border); }
.log th.r, .log td.r { text-align: right; }
.log td.r { font-family: var(--mono); }
.log tr.flash td { background: rgba(200,146,42,.14); }
.log .fly small { color: var(--faint); margin-left: 6px; }
.dir { display: inline-block; width: 34px; font-family: var(--mono); font-size: 11px; color: var(--muted); }
.mult { color: var(--muted); }
.mult.hi { color: var(--accent); }
.how { color: #cfc8bb; }
.more { margin-top: 12px; background: transparent; border: 1px solid var(--border); color: var(--text); padding: 8px 14px; border-radius: 8px; font: 500 13px var(--sans); cursor: pointer; }
.more:hover { border-color: rgba(200,146,42,.5); }

@media (max-width: 820px) {
  .hero, .split { grid-template-columns: minmax(0, 1fr); }
  main { padding-inline: 16px; }
}
@media (max-width: 480px) {
  .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
"""
