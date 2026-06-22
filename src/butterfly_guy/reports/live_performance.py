"""Live trading performance report — stats, drawdown, and HTML rendering."""

# Generated HTML/CSS/JS strings in this module intentionally exceed 100 columns.
# ruff: noqa: E501

from __future__ import annotations

import datetime as dt
import html
import json
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
                "<td>—</td><td>—</td><td>—</td>"
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
    date_start = trades[0].trade_date.isoformat()
    date_end = trades[-1].trade_date.isoformat()
    max_dd_pct = max((p["drawdown_pct"] for p in chart_data), default=0.0)
    chart_json = json.dumps(chart_data)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Butterfly Guy — {html.escape(underlying)} Live Performance</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>{_BASE_CSS}</style>
</head>
<body>
<main>
  <header class="hero">
    <div>
      <h1>Butterfly Guy — {html.escape(underlying)} Live Performance</h1>
      <div class="sub">
        <span class="badge">Paper Trading</span>
        {stats.trade_count} trades · {date_start} to {date_end} · Updated {html.escape(stamp)}
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

  <h2>Equity Curve</h2>
  <section class="panel chart-panel">
    <canvas id="equityChart" height="120"></canvas>
    <div class="chart-legend" aria-label="Equity curve marker legend">
      <span class="legend-item"><span class="legend-dot legend-dot-standard"></span> Standard exit</span>
      <span class="legend-item"><span class="legend-dot legend-dot-drawdown"></span> Drawdown exit</span>
    </div>
  </section>

  <h2>Portfolio Drawdown</h2>
  <section class="panel chart-panel"><canvas id="drawdownChart" height="90"></canvas></section>

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
    <canvas id="returnDistributionChart" height="95"></canvas>
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
          <th>Date</th><th>Status</th><th>Dir</th><th>Width</th><th>Center</th><th>Strikes</th>
          <th>VIX</th><th>Spot</th><th>Entry</th><th>Exit</th><th>Min</th>
          <th>Entry$</th><th>Peak$</th><th>Exit$</th><th>Exit Reason</th><th>DD at Exit</th><th>PnL</th>
        </tr>
      </thead>
      <tbody>{table_rows}</tbody>
    </table>
  </details>
</main>
<script>
const chartData = {chart_json};
const maxDdPct = {max_dd_pct:.4f};

const labels = chartData.map((d) => d.date);
const equityValues = chartData.map((d) => d.equity);
const drawdownValues = chartData.map((d) => -d.drawdown_pct);
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
      ticks: {{ color: '#6a6460', maxRotation: 0, autoSkip: true, maxTicksLimit: 12 }},
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
          color: '#6a6460',
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
        label: 'Max drawdown',
        data: labels.map(() => -maxDdPct),
        borderColor: 'rgba(204,85,85,0.55)',
        borderDash: [6, 4],
        pointRadius: 0,
        borderWidth: 1,
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
          color: '#6a6460',
          callback: (v) => `${{v}}%`,
        }},
        grid: {{ color: 'rgba(232,226,214,0.06)' }},
      }},
    }},
  }},
}});

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
          color: '#6a6460',
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
  --muted: #6a6460;
  --border: rgba(232, 226, 214, 0.1);
  --up: #6aaa78;
  --down: #cc5555;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
}
body { margin: 0; }
main { max-width: 1320px; margin: 0 auto; padding: 28px 24px 48px; }
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
.stats {
  display: grid;
  grid-template-columns: repeat(7, minmax(110px, 1fr));
  gap: 10px;
  margin-top: 22px;
}
.stat {
  background: #121212;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
}
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
@media (max-width: 980px) {
  main { padding: 16px; }
  .stats { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
}
"""
