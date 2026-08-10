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
| `src/butterfly_guy/candidate_fleet/` | Shared-feed paper candidate evaluators (see below) |
| `src/butterfly_guy/core/` | Config loading, logging, and shared settings |
| `src/butterfly_guy/db/` | TimescaleDB connection pool, migrations, and queries |
| `src/butterfly_guy/quant_engine/` | Black-Scholes pricer and IV/skew modeling |
| `src/butterfly_guy/services/` | Trade and position service orchestration, notifications |
| `src/butterfly_guy/reports/` | Report and dashboard generation |
| `src/butterfly_guy/equity_scan/` | Personal equity-research scanner (not part of the butterfly strategy) |
| `src/butterfly_guy/schwab_gateway/` | Deployed read-only Schwab OAuth/REST gateway; consumer migration remains opt-in (see below) |
| `src/butterfly_guy/gateway_client/` | Client for consuming the Schwab gateway |
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
sibling lock and atomic replacement. The candidate feed receives the same directory read-only.
Compose fails closed while the variable is unset.

## Live-money readiness gate

This repo is not cleared for live-money automation until `todo.md` is complete. Before any restart, deploy, or live pilot, check the current gate in `todo.md` and follow `docs/live-runbook.md`, which requires zero `OPEN` trades in the database, no working/unknown Schwab orders, and broker/DB reconciliation.

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

## Shared SPX candidate fleet

The candidate fleet is a separate, paper-only runtime. The primary SPX service
continues to read Schwab directly and does not depend on the fleet.

`configs/candidates.yaml` is the source of truth for up to ten YAML variants.
Each enabled candidate has its own container and PostgreSQL database. Slots
`0` through `9` map to host metrics ports `8100` through `8109`. The existing
BEST_RR database is registered as `butterfly_guy_spx_candidate`; its preserved
history now continues under the fleet-native `best-rr` evaluator in slot 0.
Five additional evaluators are enabled: `vix-center`,
`target-cost`, `gap-conviction`, `peak-trailer`, and `absolute-stop`. They use
slots 1–5, isolated databases, and the same shared feed.

Validate and inspect generated runtime changes:

```bash
uv run candidatectl validate
uv run candidatectl render
uv run candidatectl plan
```

Generated Compose, Prometheus file-discovery, and Grafana datasource files live
under ignored `infra/generated/`. `apply` creates missing databases and starts
enabled services; it never drops databases. Disabled containers are stopped
only when explicitly requested:

```bash
uv run candidatectl apply
uv run candidatectl apply --stop-disabled
```

The shared `spx_candidate_feed` performs candidate-side Schwab reads and keeps a
full immutable snapshot. It polls every 60 seconds while idle and every two
seconds while an evaluator has an entry or position lease. Candidate containers
have no project `.env`, Schwab credentials, token mount, account ID, broker
client, or live-order executor. Paper entries are accepted only after the feed
snapshot has been pinned in `butterfly_guy_candidate_market`; position monitors
request and persist only their three leg quotes.
Paper fills use the canonical `mark_v1` cohort. At expiration, the shared feed
serves one cached final regular-session SPX close so evaluators can cash-settle
without Schwab credentials. Review progress counts only closed `mark_v1` trades,
with a minimum gate of 20 closed trades per candidate.

All six evaluators use the shared feed and isolated candidate runtime. The
legacy `app_spx_candidate` Compose profile remains stopped and available for
one rollback cycle; it must not run concurrently with the fleet-native
`best-rr` evaluator because both use the preserved BEST_RR database.

## Schwab gateway (deployed read-only; consumer migration in progress)

`src/butterfly_guy/schwab_gateway/` is deployed on Helios as an internal read-only service. Its
readiness, authenticated Schwab access, Prometheus scrape, alerting, and crash recovery have been
proven. It exposes bounded quote, spot, and option-chain reads; history, account, and order surfaces
remain absent.

The trading applications still use direct Schwab access as the authoritative path, and no deployed
consumer depends on the gateway. XSP contains the deployed shadow canary, but its flag defaults off
and remains disabled; enabling it for a market-session observation is a separate operator decision. See
`docs/architecture/schwab-gateway-migration.md` and `infra/docker-compose.gateway.yml` for the
design and rollout boundaries.

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
- Live-money automation is gated by `todo.md`; check it before any restart, deploy, or live pilot.

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
