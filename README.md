# Butterfly Guy

![Butterfly Guy Logo](data/images/butterflyguy_logo2.png)

Butterfly Guy is an automated 0-DTE butterfly options trading system and research platform for Schwab + TimescaleDB.

It can also consume freshness-gated, venue-specific Level II snapshots from
SchwabGateway over authenticated HTTP and WebSocket connections. See
[`docs/gateway-order-books.md`](docs/gateway-order-books.md).

SPX is the primary product and the main runtime path.

NDX and XSP are experimental. Treat them as separate tuning paths, not as production parity with SPX.

## What this repo does

At a high level, the system:

- collects option-chain and spot snapshots into TimescaleDB,
- selects 0-DTE butterfly entries using configurable width, regime, and risk rules,
- manages open positions with profit and drawdown logic,
- supports paper trading and controlled live trading,
- replays historical data for backtests and parity checks,
- publishes metrics and dashboards for monitoring.

The runtime is split so you can run collection, trading, or the full stack.

This README covers the Butterfly Guy options system only. The repository also
contains personal equity-research utilities that reuse the local Schwab OAuth
authentication; they are not part of Butterfly Guy, its strategy, or its
runtime.

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
| `src/butterfly_guy/core/` | Config loading, logging, and shared settings |
| `src/butterfly_guy/db/` | TimescaleDB connection pool, migrations, and queries |
| `src/butterfly_guy/quant_engine/` | Black-Scholes pricer and IV/skew modeling |
| `src/butterfly_guy/services/` | Trade and position service orchestration, notifications |
| `src/butterfly_guy/reports/` | Report and dashboard generation |
| `src/butterfly_guy/equity_scan/` | Personal equity-research scanner (not part of the butterfly strategy) |
| `src/butterfly_guy/gateway_client/` | Default-off shadow comparison around the standalone SchwabGateway SDK |
| `configs/` | SPX, NDX, and XSP configuration files |
| `infra/` | Docker compose and observability wiring |
| `docs/architecture/`, `docs/runbooks/` | Design notes, migration plans, and operational runbooks |
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

Secrets and runtime credentials live in `.env` and `tokens.json`. Do not commit those values. Copy `.env.example` to `.env` to start.

Docker Compose also requires `SCHWAB_GATEWAY_TOKEN_DIR` in its interpolation environment (normally
`infra/.env`). Set it to an absolute, dedicated host directory containing `tokens.json`, not to the
repository root and not to the token document itself:

```dotenv
SCHWAB_GATEWAY_TOKEN_DIR=/absolute/path/to/schwab-token-directory
```

The directory must be writable by the configured trading/gateway uid because token refresh uses a
sibling lock and atomic replacement. Compose fails closed while the variable is unset.

## Live-money readiness gate

Treat SPX, NDX, and XSP as paper-only unless the owner explicitly authorizes a supervised live
canary. Before any restart, deploy, or live pilot, follow `docs/live-runbook.md`, which requires
zero `OPEN` trades in the database, no working/unknown Schwab orders, and broker/DB reconciliation.

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

## Schwab gateway (standalone operational service)

The read-only gateway is maintained and deployed from
[`hollowc2/SchwabGateway`](https://github.com/hollowc2/SchwabGateway). Butterfly Guy pins the
standalone `schwab-gateway-sdk` to the immutable v0.4.4 commit recorded in `pyproject.toml` and
`uv.lock`, while `schwab-token-store` remains pinned to `v0.1.0`. Butterfly Guy no longer contains
the gateway server, operator CLIs, Compose file, or alert rules. The standalone service supports
history, movers, full option chains, and order books, in addition to bounded quote and spot reads;
account and order-write surfaces remain outside the gateway.

The deployed PAPER SPX, NDX, and XSP strategies use gateway market data as the authoritative read
path, including history and option-chain reads. Their direct Schwab client remains authoritative for
account, order, transaction, reconciliation, and token operations. The repository's base Compose file
keeps gateway access opt-in for local/rollback safety; the deployed PAPER overlay enables it with
`SCHWAB_ACCESS_MODE=gateway` and disables shadow reads. No account operation or order is routed
through the gateway.

For the current ownership and deployment status, see
`docs/architecture/schwab-gateway-current-status.md`. Historical extraction evidence is indexed in
`docs/archive/schwab-gateway/`; standalone build, deployment, monitoring, and key-management
instructions live in the SchwabGateway repository.

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

### 7) Generate or compare reports

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
