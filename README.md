# Butterfly Guy

![Butterfly Guy Logo](data/images/butterflyguy_logo2.png)

Butterfly Guy is an automated 0-DTE butterfly options trading system and research platform for Schwab + TimescaleDB.

SPX is the primary product and the main runtime path.

NDX and XSP are experimental. Treat them as separate tuning paths, not as production parity with SPX.

## What this repo does

At a high level, the system:

- collects option-chain and spot snapshots into TimescaleDB,
- selects 0-DTE butterfly entries using configurable width, regime, and risk rules,
- manages open positions with profit and drawdown logic,
- supports paper trading and controlled live trading,
- replays historical data for backtests and parity checks,
- runs equity universe scans for the morning workflow,
- publishes metrics and dashboards for monitoring.

The runtime is split so you can run collection, trading, or the full stack.

## Core repo layout

| Path | Purpose |
|---|---|
| `src/butterfly_guy/scripts/` | Command-line entrypoints for live trading, collection, scans, reports, and backtests |
| `src/butterfly_guy/strategy/` | Butterfly selection, width selection, regime logic, and entry filtering |
| `src/butterfly_guy/execution/` | Order building and retry/ladder execution logic |
| `src/butterfly_guy/position/` | Position monitoring, profit policy, and exit state machine |
| `src/butterfly_guy/risk/` | Daily loss limits, trade caps, and buying-power guards |
| `src/butterfly_guy/data/` | Schwab client, chain collection, and DB-facing data models |
| `src/butterfly_guy/backtest/` | DB replay and simulation engine |
| `src/butterfly_guy/equity_scan/` | Morning stock-universe scan and report generation |
| `configs/` | SPX, NDX, and XSP configuration files |
| `infra/` | Docker compose and observability wiring |
| `tests/` | Focused test coverage |

## Architecture at a glance

```text
Schwab API
   ├─ option/spot collector ──> TimescaleDB ──> backtests and parity reports
   └─ live quotes/orders ─────> entry selection ──> order manager ──> position monitor
                                   │
                                   └────────────> risk engine + metrics + notifications
```

## How the product is organized

SPX is the default operational path.

XSP and NDX are separate configurations, not just smaller or larger SPX clones. They have their own widths, tolerances, quote-quality rules, and risk behavior. Treat them as experimental until you have enough real data to justify changing that label.

The live orchestrator runs three things together:

1. option-chain collection,
2. entry selection and order management,
3. open-position monitoring.

That orchestration is what lives in `run_live.py`.

## Configuration files

| File | Role |
|---|---|
| `configs/config.yaml` | SPX default configuration |
| `configs/config_ndx.yaml` | NDX experimental configuration |
| `configs/config_xsp.yaml` | XSP experimental configuration |

Default runtime settings are paper-trading oriented. Live trading requires the explicit live-trading guard to be enabled.

Secrets and runtime credentials live in `.env` and `tokens.json`. Do not commit those values.

## Typical workflow

### 1) Install dependencies

```bash
uv sync
```

### 2) Run the test and lint pass

```bash
uv run pytest
uv run ruff check .
```

### 3) Start the SPX stack in Docker

SPX is the default service. The compose file starts it without needing a profile.

```bash
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml ps
```

If you want the experimental containers too:

```bash
docker compose -f infra/docker-compose.yml --profile ndx --profile xsp up -d
docker compose -f infra/docker-compose.yml ps
```

Container names:

- `butterfly_spx_app`
- `butterfly_ndx_app`
- `butterfly_xsp_app`

Useful health checks:

```bash
docker logs --tail 100 butterfly_spx_app
docker logs --tail 100 butterfly_ndx_app
docker logs --tail 100 butterfly_xsp_app
```

Metrics ports from the compose file:

- SPX: `127.0.0.1:8000`
- NDX: `127.0.0.1:8001`
- XSP: `127.0.0.1:8003`

### 4) Run the live orchestrator directly

The live runner starts collection, entry logic, and position monitoring together.

```bash
uv run python src/butterfly_guy/scripts/run_live.py --config configs/config.yaml
```

For the experimental configurations:

```bash
uv run python src/butterfly_guy/scripts/run_live.py --config configs/config_ndx.yaml
uv run python src/butterfly_guy/scripts/run_live.py --config configs/config_xsp.yaml
```

### 5) Smoke-test the backtest from Docker

```bash
docker exec butterfly_spx_app python -m butterfly_guy.scripts.run_backtest_db 2026-05-05 2026-05-05 --asset SPX
```

Host equivalent:

```bash
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2026-05-05 2026-05-05 --asset SPX
```

### 6) Inspect a historical entry decision

```bash
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --method VIX
```

### 7) Run the morning equity scan

```bash
uv run python src/butterfly_guy/scripts/run_morning_scan.py --dry-run
uv run python src/butterfly_guy/scripts/refresh_equity_universes.py --dry-run
```

### 8) Generate or compare reports

```bash
uv run python src/butterfly_guy/scripts/report_trade_ladders.py 2026-05-20 --underlying SPX
uv run python src/butterfly_guy/scripts/report_selection_parity.py 2026-05-15 2026-05-29 --asset SPX
uv run python src/butterfly_guy/scripts/report_exit_mark_parity.py --trade-id 87
uv run python src/butterfly_guy/scripts/generate_live_performance.py
```

## Backtesting

> `run_entry_analysis.py` and `SimulationEngine.simulate_day()` are legacy research paths
> with independent asset/selection defaults. Do not treat their output as live-parity
> evidence; use `run_backtest_db.py` for config-backed shared entry selection.

`run_backtest_db.py` replays historical data from TimescaleDB using the same strategy components the live system uses.

Examples:

```bash
# Single day
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2025-01-15 2025-01-15 --asset SPX

# Date range
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2025-01-01 2025-03-31 --asset SPX

# Sweep parameter space
uv run python src/butterfly_guy/scripts/run_backtest_db.py --asset SPX --sweep
```

The same script also supports `--asset NDX` and `--asset XSP`, but those should be treated as experimental comparison paths rather than the main line.

## Repository conventions that matter

- SPX is the primary asset.
- XSP and NDX are experimental.
- Paper trading is the default.
- Backtests should be run against the same config family as the asset you are comparing.
- Docker is the normal way to run the app services.
- TimescaleDB is the historical source of truth for replay and parity work.

## If you are changing the code

Keep changes surgical. The repo is large enough that broad refactors usually buy less than they cost.

When changing behavior:

- update or add focused tests,
- verify the narrowest useful command,
- avoid touching unrelated configs or assets.

If you are only trying to understand the system, start with:

1. `configs/config.yaml`
2. `src/butterfly_guy/scripts/run_live.py`
3. `src/butterfly_guy/strategy/`
4. `src/butterfly_guy/execution/`
5. `src/butterfly_guy/position/`

## License

MIT
