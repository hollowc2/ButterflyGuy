# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An automated 0-DTE (zero days to expiration) butterfly spread options trading system for SPX and NDX, running against the Charles Schwab API. Currently paper trading. Runs in Docker with TimescaleDB, Prometheus, and Grafana for monitoring.

## Running the System

```bash
# Start SPX live trader
docker compose --profile spx up -d butterfly_spx_app

# Start NDX live trader
docker compose --profile ndx up -d butterfly_ndx_app

# Start collector only (no trading)
docker compose --profile spx up -d butterfly_spx_collector

# View logs
docker compose logs -f butterfly_spx_app
```

## Development

```bash
# Install dependencies
uv sync

# Run a script directly (outside Docker)
.venv/bin/python src/butterfly_guy/scripts/run_live.py --config config.yaml

# Run a DB backtest (single day)
.venv/bin/python src/butterfly_guy/scripts/run_backtest_db.py --config config.yaml --date 2025-01-15

# Run a DB backtest sweep (all available days)
.venv/bin/python src/butterfly_guy/scripts/run_all_db_days.py --config config.yaml

# Run drawdown threshold sweep
.venv/bin/python src/butterfly_guy/scripts/run_dd_sweep.py --config config.yaml
```

## Architecture

### Entry Point: `scripts/run_live.py`

Runs three concurrent asyncio tasks:
1. **Collector loop** — fetches Schwab option chains every 60s, writes to TimescaleDB
2. **Entry loop** — scans for butterfly candidates 07:00–07:45 PST, places orders
3. **Daily reset loop** — resets risk state at midnight

On startup: runs DB migrations, classifies market regime (BULL/BEAR/CHOP), recovers open trades from DB, re-seeds Prometheus metrics.

### Source Layout (`src/butterfly_guy/`)

| Package | Responsibility |
|---|---|
| `core/` | Config loading (pydantic-settings), structured logging, Prometheus metrics, time utils |
| `data/` | Schwab API client, option chain collector, data schemas |
| `db/` | asyncpg connection pool, migrations, all SQL queries |
| `strategy/` | Butterfly builder/selector, direction filter, VIX center anchoring, regime classifier |
| `execution/` | Order construction, price ladder retry logic |
| `position/` | Mark-price polling, `ProfitStateMachine` (LOSS/NEAR_LONG/PROFIT_TENT), exit signals |
| `risk/` | Daily trade count, daily loss limit, halt logic |
| `services/` | `TradeService` (entry orchestration), `PositionService` (monitor loop), Discord notifier |
| `quant_engine/` | Black-Scholes pricer, IV skew model, `SyntheticChainGenerator` |
| `backtest/` | `SimulationEngine`, `ParameterSweeper`, data loaders (DB, yfinance, CSV) |
| `scripts/` | All runnable entry points |

### Strategy Pipeline (Entry)

1. **Direction** — spot > prev close → CALL butterfly; else PUT (or `BiasScoreFilter` with 4 signals)
2. **Build** — scan all center strikes within `spot_range` × each `wing_width`; filter by `max_cost` and `rr_min`
3. **VIX anchoring** — compute ideal center = `VIX × sigma_fraction / sqrt(252)` OTM from spot
4. **Select** — pick candidate whose R/R is closest to `rr_target` (default 10.0)
5. **Execute** — price ladder: start at `fly_ask`, step up to 4 times if unfilled

### Exit Logic (`ProfitStateMachine`)

Polls mark price every 2 seconds. Exit triggers:
- **EOD** — 5 min before 4:00 PM ET close
- **Loss stop** — position loses ≥ 50% of entry cost
- **Drawdown from peak** — only after reaching PROFIT_TENT; thresholds 60%/60%/40% by time regime (morning/late_morning/afternoon)

### Database Tables (TimescaleDB)

| Table | Key Info |
|---|---|
| `option_chain_snapshots` | Raw chain data, hypertable on `snapshot_time` |
| `spot_prices` | SPX/VIX spot, hypertable on `ts` |
| `daily_bars` | Daily OHLCV for SPX/VIX, used by regime classifier |
| `trades` | Full trade lifecycle: entry/exit prices, strikes, PnL, peak_value, status |
| `butterfly_candidates` | All scanned candidates at each entry scan |
| `decision_log` | JSONB event log for every significant system action |
| `daily_risk_state` | Per-underlying daily trade count, realized PnL, halted flag |

### Configuration

- `config.yaml` — SPX: wing widths 10/20/30 pts, max cost $1/$2/$3, R/R min 8.0
- `config_ndx.yaml` — NDX: wing widths 25/50/75 pts, spot_range 250, center_tolerance 100
- Both: paper_trading true, $500 max daily loss, 2 trades/day, entry 07:00–07:45 PST

### Infrastructure

- **Docker Compose** (`infra/docker-compose.yml`): 4 containers (spx/ndx × app/collector), external `monitoring_net`
- **Prometheus** scrapes `:8000` (SPX) and `:8001` (NDX) every 15s
- **Grafana** dashboards in `infra/grafana/dashboards/` (symlinked to `/opt/monitoring/grafana/dashboards/`)
- **Cron** (hourly): `schwab_token_keepalive.py` — refreshes OAuth token, Telegram alert if refresh token expiring
- **Notifications**: Telegram (token keepalive, collector alerts) + Discord (trade events, startup)

### Paper Trading

Paper fills use **mark price** `(bid + ask) / 2` to match ToS behavior — not ask for buys or bid for sells.
