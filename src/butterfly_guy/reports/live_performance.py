"""Live trading performance report — stats, drawdown, and HTML rendering."""

# Generated HTML/CSS/JS strings in this module intentionally exceed 100 columns.
# ruff: noqa: E501

from __future__ import annotations

import datetime as dt
import html
import json
import math
from dataclasses import dataclass
from typing import Any

from butterfly_guy.backtest.metrics import max_drawdown, profit_factor
from butterfly_guy.core.time_utils import EASTERN, PACIFIC

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


def trade_point_from_row(row: dict[str, Any]) -> TradePoint:
    metadata = _parse_metadata(row.get("metadata"))
    exit_parity = metadata.get("exit_mark_parity") or {}
    dd_at_exit = exit_parity.get("live_drawdown_pct")
    pnl = row.get("pnl")
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
        })
    return payload


def _money(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    if signed:
        return f"${value:+.0f}"
    return f"${value:.2f}"


def _pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"


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


def _spoken_money(value: float) -> str:
    """Signed dollars written out for a screen reader ("minus $1,336")."""
    rounded = round(value)
    if rounded == 0:
        return "$0"
    sign = "minus " if rounded < 0 else "plus "
    return f"{sign}${abs(rounded):,}"


def _spoken_pct(value: float) -> str:
    return f"{value:.0f} percent"


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


# The three canvas aria-labels below are the only description a screen reader gets
# for the charts, so they are computed from the same payload the charts draw rather
# than written by hand — a hand-written label goes stale on the next cron run.


def equity_chart_description(chart_data: list[dict[str, Any]]) -> str:
    if not chart_data:
        return "Line chart of cumulative paper profit and loss. No trades yet."
    low = min(chart_data, key=lambda d: d["equity"])
    high = max(chart_data, key=lambda d: d["equity"])
    final = chart_data[-1]
    parts = [
        f"Line chart of cumulative paper profit and loss across all "
        f"{_plural(len(chart_data), 'trade')}, {chart_data[0]['date']} to {final['date']}."
    ]
    if low is high:
        parts.append(f"The curve ends at {_spoken_money(final['equity'])}.")
    elif low["index"] < high["index"]:
        parts.append(
            f"The curve falls to a low of {_spoken_money(low['equity'])} on {low['date']}, "
            f"then climbs to a peak of {_spoken_money(high['equity'])} on {high['date']}, "
            f"and ends at {_spoken_money(final['equity'])}."
        )
    else:
        parts.append(
            f"The curve rises to a peak of {_spoken_money(high['equity'])} on {high['date']}, "
            f"then falls to a low of {_spoken_money(low['equity'])} on {low['date']}, "
            f"and ends at {_spoken_money(final['equity'])}."
        )
    parts.append("Every plotted trade is listed in the trade log table below.")
    return " ".join(parts)


def drawdown_episodes(chart_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deepest point of each unbroken run of non-zero drawdown."""
    episodes: list[dict[str, Any]] = []
    worst: dict[str, Any] | None = None
    for point in chart_data:
        if point["drawdown_pct"] > 0:
            if worst is None or point["drawdown_pct"] > worst["drawdown_pct"]:
                worst = point
        elif worst is not None:
            episodes.append(worst)
            worst = None
    if worst is not None:
        episodes.append(worst)
    return episodes


def drawdown_chart_description(chart_data: list[dict[str, Any]]) -> str:
    opening = (
        "Line chart of how far cumulative paper PnL has fallen below its own running "
        "peak, as a percentage of that peak."
    )
    if not chart_data:
        return f"{opening} No trades yet."
    parts = [opening]
    flat_lead = 0
    for point in chart_data:
        if point["drawdown_pct"] > 0:
            break
        flat_lead += 1
    episodes = drawdown_episodes(chart_data)
    if episodes:
        lead = (
            f"It stays flat at zero for the first {_plural(flat_lead, 'trade')}, then runs "
            if flat_lead
            else "It runs "
        )
        parts.append(
            f"{lead}through {_plural(len(episodes), 'drawdown episode')}, each ended by a "
            "reset to zero when a new peak in cumulative PnL is set."
        )
        deepest = max(episodes, key=lambda d: d["drawdown_pct"])
        parts.append(
            f"The deepest reaches {_spoken_pct(deepest['drawdown_pct'])} "
            f"(${deepest['drawdown_dollars']:,.0f}) on {deepest['date']}."
        )
    else:
        parts.append("It never falls below its running peak.")
    final_dd = chart_data[-1]["drawdown_pct"]
    parts.append(
        # Below half a percent _spoken_pct would round to "0 percent below the peak".
        "It finishes at its peak."
        if final_dd < 0.5
        else f"It finishes {_spoken_pct(final_dd)} below the peak."
    )
    parts.append("The underlying trades are listed in the trade log table below.")
    return " ".join(parts)


def return_distribution_description(
    chart_data: list[dict[str, Any]], bucket_size: int = 250
) -> str:
    opening = (
        f"Bar chart counting trades by dollar PnL, in ${bucket_size}-wide buckets by default."
    )
    if not chart_data:
        return f"{opening} No trades yet."
    pnls = [d["pnl"] for d in chart_data]
    losers = sum(1 for p in pnls if p < 0)
    winners = sum(1 for p in pnls if p > 0)
    # Same bucketing as buildReturnDistribution() in the page script.
    counts: dict[int, int] = {}
    for pnl in pnls:
        start = math.floor(pnl / bucket_size) * bucket_size
        counts[start] = counts.get(start, 0) + 1
    modal_start = max(counts, key=lambda start: (counts[start], -start))

    def span(start: int) -> str:
        return f"{_spoken_money(start)} to {_spoken_money(start + bucket_size)}"

    parts = [
        opening,
        f"Of {_plural(len(pnls), 'trade')}, {losers} lose and {winners} win.",
        f"The tallest bar holds {_plural(counts[modal_start], 'trade')} in the single "
        f"bucket from {span(modal_start)}.",
    ]
    winning_starts = sorted(start for start in counts if start >= 0)
    if len(winning_starts) > 1:
        parts.append(
            f"The winners spread thinly to the right, from "
            f"{_plural(counts[winning_starts[0]], 'trade')} in the bucket from "
            f"{span(winning_starts[0])} out to the bucket from {span(winning_starts[-1])}."
        )
    parts.append("Per-trade PnL values are listed in the trade log table below.")
    return " ".join(parts)


def render_trade_table_rows(trades: list[TradePoint], no_trade_days: list[NoTradeDay]) -> str:
    rows: list[tuple[dt.date, str]] = []
    for trade in trades:
        rows.append((trade.trade_date, _render_trade_row(trade)))
    for day in no_trade_days:
        rows.append((
            day.trade_date,
            (
                "<tr class='muted no-trade-row' data-row-type='no-trade'>"
                f"<td>{day.trade_date.isoformat()}</td>"
                f"<td>{html.escape(day.status)}</td>"
                "<td>—</td><td>—</td><td>—</td><td>—</td>"
                "<td>—</td><td>—</td><td>—</td><td>—</td><td>—</td>"
                "<td>—</td><td>—</td><td>—</td><td>—</td>"
                f"<td>{html.escape(day.reason)}</td>"
                "<td>—</td><td>—</td>"
                "</tr>"
            ),
        ))
    rows.sort(key=lambda item: item[0])
    return "".join(row for _, row in rows)


def _render_trade_row(trade: TradePoint) -> str:
    pnl_class = "pos" if trade.pnl_dollars >= 0 else "neg"
    dd_cell = _pct(trade.dd_at_exit_pct) if is_drawdown_exit(trade.exit_reason) else "—"
    duration = duration_minutes(trade.entry_time, trade.exit_time)
    vix_cell = f"{trade.vix:.1f}" if trade.vix is not None else "—"
    spot_cell = f"{trade.entry_spot:.0f}" if trade.entry_spot is not None else "—"
    return (
        "<tr data-row-type='trade'>"
        f"<td>{trade.trade_date.isoformat()}</td>"
        "<td>Trade</td>"
        f"<td>{html.escape(trade.paper_fill_model)}</td>"
        f"<td>{html.escape(trade.direction)}</td>"
        f"<td>{trade.wing_width}W</td>"
        f"<td>{trade.center_strike:.0f}</td>"
        f"<td>{trade.lower_strike:.0f} / {trade.center_strike:.0f} / {trade.upper_strike:.0f}</td>"
        f"<td>{vix_cell}</td>"
        f"<td>{spot_cell}</td>"
        f"<td>{format_et_time(trade.entry_time)}</td>"
        f"<td>{format_et_time(trade.exit_time)}</td>"
        f"<td>{duration if duration is not None else '—'}</td>"
        f"<td>{_money(trade.entry_price)}</td>"
        f"<td>{_money(trade.peak_value)}</td>"
        f"<td>{_money(trade.exit_price)}</td>"
        f"<td>{html.escape(trade.exit_reason or '—')}</td>"
        f"<td>{dd_cell}</td>"
        f"<td class='{pnl_class}'>{_money(trade.pnl_dollars, signed=True)}</td>"
        "</tr>"
    )


def render_placeholder_html(*, underlying: str, generated_at: dt.datetime) -> str:
    stamp = generated_at.astimezone(PACIFIC).strftime("%Y-%m-%d %H:%M %Z")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Butterfly Guy — {html.escape(underlying)} Live Performance</title>
  <style>{_BASE_CSS}</style>
</head>
<body>
<main>
  <h1>Butterfly Guy — {html.escape(underlying)} Live Performance</h1>
  <div class="sub">Paper trading · Last updated {html.escape(stamp)}</div>
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
    pnls = [t.pnl_dollars for t in trades]
    stats = compute_stats(pnls)
    chart_data = chart_payload(trades)
    table_rows = render_trade_table_rows(trades, no_trade_days)
    stamp = generated_at.astimezone(PACIFIC).strftime("%Y-%m-%d %H:%M %Z")
    date_end = trades[-1].trade_date.isoformat()
    max_dd_pct = max((p["drawdown_pct"] for p in chart_data), default=0.0)
    equity_desc = equity_chart_description(chart_data)
    drawdown_desc = drawdown_chart_description(chart_data)
    distribution_desc = return_distribution_description(chart_data)
    chart_json = _json_data_block(
        {"trades": chart_data, "maxDdPct": round(max_dd_pct, 4)}
    )
    cohorts: dict[str, list[TradePoint]] = {}
    for trade in trades:
        cohorts.setdefault(trade.paper_fill_model, []).append(trade)
    cohort_cards = "".join(
        (
            "<div class='stat'>"
            f"<div class='label'>{html.escape(model)}</div>"
            f"<div class='value'>{len(model_trades)} trades</div>"
            f"<div class='sub'>PnL ${sum(t.pnl_dollars for t in model_trades):+.0f}</div>"
            "</div>"
        )
        for model, model_trades in cohorts.items()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Butterfly Guy — {html.escape(underlying)} Paper Performance</title>
  <link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fonts/inter-var-latin.woff2">
  <link rel="stylesheet" href="/assets/fonts.css">
  <script src="/assets/vendor/chart.umd.min.js"></script>
  <style>{_BASE_CSS}</style>
</head>
<body>
<main>
  <a class="site-link" href="/"><span aria-hidden="true">←</span>billybitcoin.cloud</a>

  <header class="hero">
    <div>
      <h1>Butterfly Guy — {html.escape(underlying)} Paper Performance</h1>
      <div class="sub">
        <span class="badge">Paper Trading</span>
        Entire history · {stats.trade_count} trades · Paper results through {date_end} · Static snapshot regenerated after each session, last built {html.escape(stamp)}
      </div>
    </div>
  </header>

  <section class="stats">
    <div class="stat"><div class="label">Total PnL</div><div class="value {'pos' if stats.total_pnl >= 0 else 'neg'}">${stats.total_pnl:+.0f}</div></div>
    <div class="stat"><div class="label">Win Rate</div><div class="value">{stats.win_rate:.0f}%</div></div>
    <div class="stat"><div class="label">Average</div><div class="value">${stats.average:+.0f}</div></div>
    <div class="stat"><div class="label">Best</div><div class="value pos">${stats.best:+.0f}</div></div>
    <div class="stat"><div class="label">Worst</div><div class="value neg">${stats.worst:+.0f}</div></div>
    <div class="stat"><div class="label">Profit Factor</div><div class="value">{stats.profit_factor:.2f}</div></div>
    <div class="stat"><div class="label">Max Drawdown</div><div class="value neg">${stats.max_drawdown:.0f}</div></div>
  </section>

  <h2>Fill Model Cohorts</h2>
  <section class="stats">{cohort_cards}</section>

  <h2>Equity Curve</h2>
  <section class="panel chart-panel">
    <canvas id="equityChart" height="120" role="img" aria-label="{html.escape(equity_desc)}"></canvas>
    <div class="chart-legend" aria-label="Equity curve marker legend">
      <span class="legend-item"><span class="legend-dot legend-dot-standard"></span> End of Day exit</span>
      <span class="legend-item"><span class="legend-dot legend-dot-drawdown"></span> Drawdown exit</span>
    </div>
  </section>

  <h2>Drawdown from peak PnL</h2>
  <section class="panel chart-panel">
    <canvas id="drawdownChart" height="90" role="img" aria-label="{html.escape(drawdown_desc)}"></canvas>
    <p class="chart-note">
      <b id="drawdownNoteFigures"></b>
      This is drawdown against the highest cumulative <em>paper profit</em> reached, not against
      account capital — the equity series starts at zero and tracks PnL only. A figure here means
      giving back that share of accumulated open gains; it does not mean losing that share of an
      account.
    </p>
  </section>

  <h2>Return Distribution</h2>
  <section class="panel chart-panel">
    <div class="chart-tools" aria-label="Return distribution controls">
      <div class="segmented" role="group" aria-label="Bucket size">
        <button type="button" class="bucket-control" data-bucket="100">$100</button>
        <button type="button" class="bucket-control active" data-bucket="250">$250</button>
        <button type="button" class="bucket-control" data-bucket="500">$500</button>
      </div>
      <label class="toggle"><input type="checkbox" id="fitCurveToggle" checked> Fit curve</label>
    </div>
    <canvas id="returnDistributionChart" height="95" role="img" aria-label="{html.escape(distribution_desc)}"></canvas>
  </section>

  <details class="panel trade-log-panel" open>
    <summary class="section-summary">
      <span>Trade Log</span>
      <span class="summary-meta">{stats.trade_count} trades</span>
    </summary>
    <div class="table-tools">
      <label class="toggle"><input type="checkbox" id="hideNoTradesToggle"> Hide no trades</label>
    </div>
    <table>
      <thead>
        <tr>
          <th>Date</th><th>Status</th><th>Fill Model</th><th>Dir</th><th>Width</th><th>Center</th><th>Strikes</th>
          <th>VIX</th><th>Spot</th><th>Entry</th><th>Exit</th><th>Min</th>
          <th>Entry$</th><th>Peak$</th><th>Exit$</th><th>Exit Reason</th><th>DD at Exit</th><th>PnL</th>
        </tr>
      </thead>
      <tbody>{table_rows}</tbody>
    </table>
  </details>
</main>
<!-- Generator-emitted data. Kept in a non-executable application/json
     block so the CSP hash of the script below stays stable when the
     numbers are regenerated. CSP script-src does not apply to data
     blocks, so this needs no hash of its own. -->
<script type="application/json" id="chart-data">
{chart_json}
</script>
<script>
const __chartPayload = JSON.parse(
    document.getElementById('chart-data').textContent);
const chartData = __chartPayload.trades;
// Emitted by the generator; retained for downstream use even though the
// drawdown caption now derives its figures from chartData directly.
const maxDdPct = __chartPayload.maxDdPct;

const labels = chartData.map((d) => d.date);
const equityValues = chartData.map((d) => d.equity);
const drawdownValues = chartData.map((d) => -d.drawdown_pct);
const maxDdIndex = drawdownValues.indexOf(Math.min(...drawdownValues));
const maxDdPoint = chartData[maxDdIndex];
// One marked point at the trough instead of a full-width dashed rule at the
// extreme: the rule duplicated the curve's own minimum and pinned the axis there.
const maxDdMarker = drawdownValues.map((v, i) => (i === maxDdIndex ? v : null));
const returnValues = chartData.map((d) => d.pnl);
const pointRadii = chartData.map((d) => d.is_drawdown_exit ? 6 : 3);
const pointColors = chartData.map((d) => d.is_drawdown_exit ? '#cc5555' : '#c8922a');

function equityTooltip(context) {{
  const d = chartData[context.dataIndex];
  const lines = [
    `${{d.date}} · ${{d.direction}}`,
    d.strikes,
    `Entry ${{d.entry_price?.toFixed(2)}} → Exit ${{d.exit_price?.toFixed(2)}} · Peak ${{d.peak_value?.toFixed(2) ?? '—'}}`,
    `${{d.entry_time}} → ${{d.exit_time}} (${{d.duration_min ?? '—'}} min)`,
    `Exit: ${{d.exit_reason}}`,
  ];
  if (d.dd_at_exit_pct != null) lines.push(`DD at exit: ${{d.dd_at_exit_pct.toFixed(1)}}%`);
  lines.push(`Trade PnL: ${{d.pnl >= 0 ? '+' : ''}}$${{d.pnl.toFixed(0)}}`);
  lines.push(`Cumulative: ${{d.equity >= 0 ? '+' : ''}}$${{d.equity.toFixed(0)}}`);
  return lines;
}}

function drawdownTooltip(context) {{
  const d = chartData[context.dataIndex];
  return [
    d.date,
    `Drawdown: ${{d.drawdown_pct.toFixed(1)}}% ($${{d.drawdown_dollars.toFixed(0)}})`,
    `Equity: ${{d.equity >= 0 ? '+' : ''}}$${{d.equity.toFixed(0)}} · Peak: $${{d.peak_equity.toFixed(0)}}`,
  ];
}}

function bucketLabel(start, bucketSize) {{
  const end = start + bucketSize;
  return `$${{start.toFixed(0)}} to $${{end.toFixed(0)}}`;
}}

function buildReturnDistribution(bucketSize) {{
  if (!returnValues.length) return {{ labels: [], counts: [], curve: [], buckets: [] }};
  const minBucket = Math.floor(Math.min(...returnValues) / bucketSize) * bucketSize;
  const maxBucket = Math.floor(Math.max(...returnValues) / bucketSize) * bucketSize;
  const buckets = [];
  for (let start = minBucket; start <= maxBucket; start += bucketSize) {{
    buckets.push({{ start, end: start + bucketSize, count: 0, trades: [] }});
  }}
  returnValues.forEach((value, index) => {{
    const bucketStart = Math.floor(value / bucketSize) * bucketSize;
    const rawIndex = Math.round((bucketStart - minBucket) / bucketSize);
    const bucketIndex = Math.max(0, Math.min(buckets.length - 1, rawIndex));
    buckets[bucketIndex].count += 1;
    buckets[bucketIndex].trades.push(chartData[index]);
  }});

  const counts = buckets.map((bucket) => bucket.count);
  const maxCount = Math.max(...counts, 1);
  const mean = returnValues.reduce((sum, value) => sum + value, 0) / returnValues.length;
  const variance = returnValues.reduce(
    (sum, value) => sum + Math.pow(value - mean, 2),
    0,
  ) / returnValues.length;
  const stdDev = Math.sqrt(variance) || bucketSize;
  const rawCurve = buckets.map((bucket) => {{
    const midpoint = bucket.start + bucketSize / 2;
    return Math.exp(-0.5 * Math.pow((midpoint - mean) / stdDev, 2));
  }});
  const maxCurve = Math.max(...rawCurve, 1);
  const curve = rawCurve.map((value) => value / maxCurve * maxCount);

  return {{
    labels: buckets.map((bucket) => bucketLabel(bucket.start, bucketSize)),
    counts,
    curve,
    buckets,
  }};
}}

function returnDistributionTooltip(context, distribution) {{
  const bucket = distribution.buckets[context.dataIndex];
  const pnls = bucket.trades.map((trade) => trade.pnl);
  const total = pnls.reduce((sum, value) => sum + value, 0);
  return [
    bucketLabel(bucket.start, bucket.end - bucket.start),
    `${{bucket.count}} trade${{bucket.count === 1 ? '' : 's'}}`,
    `Bucket PnL: ${{total >= 0 ? '+' : ''}}$${{total.toFixed(0)}}`,
  ];
}}

function returnBucketFillColor(bucket) {{
  if (bucket.end <= 0) return 'rgba(204,85,85,0.55)';
  if (bucket.start >= 0) return 'rgba(106,170,120,0.55)';
  return 'rgba(200,146,42,0.55)';
}}

function returnBucketBorderColor(bucket) {{
  if (bucket.end <= 0) return '#cc5555';
  if (bucket.start >= 0) return '#6aaa78';
  return '#c8922a';
}}

const chartDefaults = {{
  responsive: true,
  maintainAspectRatio: true,
  interaction: {{ mode: 'index', intersect: false }},
  plugins: {{
    legend: {{ display: false }},
    tooltip: {{
      backgroundColor: '#161616',
      borderColor: 'rgba(232,226,214,0.15)',
      borderWidth: 1,
      titleColor: '#e8e2d6',
      bodyColor: '#e8e2d6',
      padding: 12,
    }},
  }},
  scales: {{
    x: {{
      ticks: {{ color: '#948d87', maxRotation: 0, autoSkip: true, maxTicksLimit: 12 }},
      grid: {{ color: 'rgba(232,226,214,0.06)' }},
    }},
  }},
}};

new Chart(document.getElementById('equityChart'), {{
  type: 'line',
  data: {{
    labels,
    datasets: [{{
      label: 'Equity',
      data: equityValues,
      borderColor: '#c8922a',
      backgroundColor: 'rgba(200,146,42,0.08)',
      pointBackgroundColor: pointColors,
      pointBorderColor: pointColors,
      pointRadius: pointRadii,
      pointHoverRadius: 8,
      borderWidth: 2,
      tension: 0.15,
      fill: true,
    }}],
  }},
  options: {{
    ...chartDefaults,
    plugins: {{
      ...chartDefaults.plugins,
      tooltip: {{
        ...chartDefaults.plugins.tooltip,
        callbacks: {{
          title: (items) => items.length ? chartData[items[0].dataIndex].date : '',
          label: () => '',
          afterBody: (items) => items.length ? equityTooltip(items[0]) : [],
        }},
      }},
    }},
    scales: {{
      ...chartDefaults.scales,
      y: {{
        ticks: {{
          color: '#948d87',
          callback: (v) => `${{v >= 0 ? '+' : ''}}$${{v}}`,
        }},
        grid: {{ color: 'rgba(232,226,214,0.06)' }},
      }},
    }},
  }},
}});

new Chart(document.getElementById('drawdownChart'), {{
  type: 'line',
  data: {{
    labels,
    datasets: [
      {{
        label: 'Drawdown %',
        data: drawdownValues,
        borderColor: '#cc5555',
        backgroundColor: 'rgba(204,85,85,0.25)',
        pointRadius: 0,
        borderWidth: 1.5,
        fill: true,
      }},
      {{
        label: 'Deepest drawdown',
        data: maxDdMarker,
        showLine: false,
        borderColor: '#e8e2d6',
        backgroundColor: '#cc5555',
        pointRadius: 5,
        pointHoverRadius: 5,
        pointBorderWidth: 1.5,
        fill: false,
      }},
    ],
  }},
  options: {{
    ...chartDefaults,
    plugins: {{
      ...chartDefaults.plugins,
      tooltip: {{
        ...chartDefaults.plugins.tooltip,
        filter: (item) => item.datasetIndex === 0,
        callbacks: {{
          title: (items) => items.length ? chartData[items[0].dataIndex].date : '',
          label: () => '',
          afterBody: (items) => items.length ? drawdownTooltip(items[0]) : [],
        }},
      }},
    }},
    scales: {{
      ...chartDefaults.scales,
      y: {{
        max: 0,
        ticks: {{
          color: '#948d87',
          callback: (v) => `${{v}}%`,
        }},
        grid: {{ color: 'rgba(232,226,214,0.06)' }},
      }},
    }},
  }},
}});

// Caption for the marked trough. Derived from chartData so it stays true when the
// page is regenerated.
const drawdownNoteFigures = document.getElementById('drawdownNoteFigures');
if (drawdownNoteFigures && maxDdPoint) {{
  const money = (n) => `$${{Math.round(Math.abs(n)).toLocaleString('en-US')}}`;
  drawdownNoteFigures.textContent = (
    `Marked point: the deepest give-back of the run, ${{maxDdPoint.drawdown_pct.toFixed(1)}}% `
    + `(${{money(maxDdPoint.drawdown_dollars)}}) on ${{maxDdPoint.date}}, measured from a peak of `
    + `+${{money(maxDdPoint.peak_equity)}} in cumulative PnL.`
  );
}}

let activeBucketSize = 250;
let showFitCurve = true;
let returnDistribution = buildReturnDistribution(activeBucketSize);

const returnDistributionChart = new Chart(document.getElementById('returnDistributionChart'), {{
  type: 'bar',
  data: {{
    labels: returnDistribution.labels,
    datasets: [
      {{
        type: 'bar',
        label: 'Trades',
        data: returnDistribution.counts,
        backgroundColor: returnDistribution.buckets.map(returnBucketFillColor),
        borderColor: returnDistribution.buckets.map(returnBucketBorderColor),
        borderWidth: 1,
        borderRadius: 4,
      }},
      {{
        type: 'line',
        label: 'Fit curve',
        data: returnDistribution.curve,
        borderColor: '#e8e2d6',
        backgroundColor: 'transparent',
        pointRadius: 0,
        borderWidth: 2,
        tension: 0.35,
        hidden: !showFitCurve,
      }},
    ],
  }},
  options: {{
    ...chartDefaults,
    plugins: {{
      ...chartDefaults.plugins,
      tooltip: {{
        ...chartDefaults.plugins.tooltip,
        callbacks: {{
          title: (items) => items.length ? returnDistribution.labels[items[0].dataIndex] : '',
          label: () => '',
          afterBody: (items) => (
            items.length ? returnDistributionTooltip(items[0], returnDistribution) : []
          ),
        }},
      }},
    }},
    scales: {{
      ...chartDefaults.scales,
      y: {{
        beginAtZero: true,
        ticks: {{
          color: '#948d87',
          precision: 0,
        }},
        grid: {{ color: 'rgba(232,226,214,0.06)' }},
      }},
    }},
  }},
}});

function updateReturnDistribution() {{
  returnDistribution = buildReturnDistribution(activeBucketSize);
  returnDistributionChart.data.labels = returnDistribution.labels;
  returnDistributionChart.data.datasets[0].data = returnDistribution.counts;
  returnDistributionChart.data.datasets[0].backgroundColor = (
    returnDistribution.buckets.map(returnBucketFillColor)
  );
  returnDistributionChart.data.datasets[0].borderColor = (
    returnDistribution.buckets.map(returnBucketBorderColor)
  );
  returnDistributionChart.data.datasets[1].data = returnDistribution.curve;
  returnDistributionChart.data.datasets[1].hidden = !showFitCurve;
  returnDistributionChart.update();
}}

document.querySelectorAll('.bucket-control').forEach((button) => {{
  button.addEventListener('click', () => {{
    activeBucketSize = Number(button.dataset.bucket);
    document.querySelectorAll('.bucket-control').forEach((item) => {{
      item.classList.toggle('active', item === button);
    }});
    updateReturnDistribution();
  }});
}});

document.getElementById('fitCurveToggle').addEventListener('change', (event) => {{
  showFitCurve = event.target.checked;
  updateReturnDistribution();
}});

document.getElementById('hideNoTradesToggle').addEventListener('change', (event) => {{
  const hideNoTrades = event.target.checked;
  document.querySelectorAll('.no-trade-row').forEach((row) => {{
    row.hidden = hideNoTrades;
  }});
}});
</script>
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
.site-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
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
