# SPX Live Performance Site — Design Spec

**Date:** 2026-06-06
**Status:** Approved (pending user review)

## Problem

Butterfly Guy accumulates live SPX trade history in TimescaleDB (46 closed trades as of 2026-06-06), but there is no public-facing page to track cumulative performance. The existing `reports/spx_backtest_all_dates.html` backtest report demonstrates the desired data shape (stats, equity curve, trade table) but is light-themed, static SVG, and generated from backtest output — not live DB trades.

## Solution

A daily-regenerated static HTML page at `https://billybitcoin.cloud/butterfly-spx/`, styled to match the billybitcoin.cloud dark theme. A Python script queries closed SPX trades from TimescaleDB, computes stats and drawdown series, and writes a self-contained HTML file with Chart.js interactive charts.

## Deployment

| Item | Value |
|------|-------|
| URL | `https://billybitcoin.cloud/butterfly-spx/` |
| Visibility | Public (no auth) |
| Web root | `/var/www/billybitcoin.cloud/html/butterfly-spx/index.html` |
| Nginx changes | None (subfolder under existing static root) |
| Regeneration | Cron at 1:15 PM PT, Mon–Fri |

```cron
15 13 * * 1-5 cd /opt/butterflyguy && /opt/butterflyguy/.venv/bin/python src/butterfly_guy/scripts/generate_live_performance.py >> /var/www/billybitcoin.cloud/butterfly-spx/generate.log 2>&1
```

## Architecture

```
Cron → generate_live_performance.py → TimescaleDB → index.html → Nginx
```

No new Docker services. Script uses existing `load_config()` + `DatabasePool` patterns from other report scripts.

## Data Sources

### Trades (`butterfly_trades`)

Query all `CLOSED` rows where `underlying = 'SPX'`, ordered by `trade_date`, `entry_time`.

Fields used directly: `trade_date`, `direction`, `wing_width`, `center_strike`, `lower_strike`, `upper_strike`, `entry_price`, `entry_time`, `exit_price`, `exit_time`, `exit_reason`, `pnl`, `peak_value`, `quantity`, `metadata`.

Enrichment from `metadata` JSONB (graceful fallback to `—` if missing):
- `vix`, `entry_spot`
- `exit_mark_parity.live_drawdown_pct` — drawdown % at exit trigger
- `exit_signal_reason` — fallback exit reason label

**PnL display:** `pnl × 100` dollars per trade (SPX contract multiplier), matching backtest report convention.

### No-trade days (`daily_risk_state` + `decision_log`)

For each trading day from first trade date through last trading day where `daily_risk_state.trade_count = 0`:

| Condition | Display |
|-----------|---------|
| `halted = true` | "Halted" — daily loss limit reached |
| First `decision_log` event that day | Human-readable reason from `entry_blocked`, `gap_regime_skip`, `no_candidates`, `entry_exhausted` |
| No event found | "No trade" |

Weekends and holidays with no `daily_risk_state` row are omitted.

## Page Layout

Styling matches billybitcoin.cloud: background `#0c0c0c`, text `#e8e2d6`, accent `#c8922a`, win `#6aaa78`, loss `#cc5555`, fonts Inter + IBM Plex Mono.

### 1. Header

- Title: "Butterfly Guy — SPX Live Performance"
- "Paper Trading" badge
- Last updated timestamp (generation time, PT)
- Subtitle: trade count + date range

### 2. Stats Row (7 cards)

Total PnL, Win Rate, Average, Best, Worst, Profit Factor, **Max Drawdown**.

Max Drawdown = largest peak-to-trough decline in cumulative equity ($) across the full trade sequence.

### 3. Equity Curve (Chart.js line chart)

- One data point per **trade** (not per calendar day)
- X-axis: trade index with date labels on hover
- Y-axis: cumulative PnL ($)
- **Drawdown exit markers:** trades where `exit_reason` starts with `drawdown_` get a distinct point style (larger dot, accent/red color) on the equity line
- **Hover tooltip** shows:
  - Date, direction, strikes (`lower / center / upper`)
  - Entry $, Peak $, Exit $
  - Entry time, Exit time, Duration (min)
  - Exit reason
  - Drawdown at exit % (if drawdown exit and metadata available)
  - Trade PnL, Cumulative PnL

### 4. Drawdown Subplot (Chart.js area chart)

Directly below the equity curve, sharing the same x-axis (one point per trade).

**Portfolio underwater drawdown** — computed from cumulative equity:

```python
equity = running_sum(pnl * 100 for each trade)
peak = running_max(equity)
drawdown_dollars[i] = peak[i] - equity[i]          # always >= 0
drawdown_pct[i] = drawdown_dollars[i] / peak[i] * 100 if peak[i] > 0 else 0
```

- Y-axis: drawdown % (0 at top, negative values downward — classic underwater chart)
- Filled area in muted red (`#cc5555` at ~30% opacity)
- Hover shows: date, drawdown %, drawdown $, cumulative equity, peak equity
- Horizontal reference line at max drawdown % with label

This shows **when** the account was underwater and **how deep**, separate from per-trade exit drawdown triggers.

### 5. Trade Log Table

All trading days in range. Traded days: full columns. No-trade days: date + status + reason only.

| Column | Traded | No-trade |
|--------|--------|----------|
| Date | ✓ | ✓ |
| Status | Trade | No trade / Halted |
| Dir | ✓ | — |
| Width | ✓ | — |
| Center | ✓ | — |
| Strikes | ✓ | — |
| VIX | ✓ | — |
| Spot | ✓ | — |
| Entry | ✓ | — |
| Exit | ✓ | — |
| Min | ✓ | — |
| Entry$ | ✓ | — |
| Peak$ | ✓ | — |
| Exit$ | ✓ | — |
| Exit Reason | ✓ | — |
| DD at Exit | ✓ (if drawdown exit) | — |
| PnL | ✓ | — |

"DD at Exit" column shows `metadata.exit_mark_parity.live_drawdown_pct` formatted as `61.1%` for drawdown exits; `—` otherwise.

## Components

### `src/butterfly_guy/scripts/generate_live_performance.py` (new)

CLI:
- `--underlying` (default `SPX`)
- `--output` (default `/var/www/billybitcoin.cloud/html/butterfly-spx/index.html`)

Responsibilities:
1. Query trades, risk state, decision log
2. Build trade rows + no-trade rows + stats + drawdown series
3. Render self-contained HTML (embedded CSS, Chart.js from CDN, inline JSON data)
4. Atomic write: `.tmp` → rename

Exit codes: 0 on success, 1 on DB/render failure.

### `tests/test_live_performance_report.py` (new)

Unit tests (no DB required):
- Stats math: total PnL, win rate, profit factor
- Cumulative equity and portfolio drawdown series
- Max drawdown calculation
- Drawdown exit detection (`exit_reason.startswith("drawdown_")`)
- No-trade day reason mapping (halted vs decision_log)
- HTML contains expected sections when given fixture data

## Error Handling

| Failure | Behavior |
|---------|----------|
| DB unreachable | Exit 1, log error; previous HTML remains served |
| Zero closed trades | Generate placeholder page ("No trades yet") |
| Missing metadata field | Show `—` in table/tooltip; skip optional fields |
| Output dir missing | Create parent directories before write |

## Out of Scope (v1)

- NDX / XSP underlyings
- Password protection or IP restriction
- Link from main `index.html`
- Real-time / intraday updates
- Per-trade PnL bar chart, return histogram
- Grafana integration

## File Touch List

| File | Action |
|------|--------|
| `src/butterfly_guy/scripts/generate_live_performance.py` | New |
| `tests/test_live_performance_report.py` | New |
| User crontab | Add one line |
| `/var/www/billybitcoin.cloud/html/butterfly-spx/` | Created on first run |
