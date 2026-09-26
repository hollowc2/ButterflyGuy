# Butterfly Guy

![Butterfly Guy Logo](data/images/butterflyguy_logo2.png)

Butterfly Guy is an automated 0-DTE butterfly options trading system and research platform, built on the Charles Schwab API and TimescaleDB.

- **SPX** is the primary product.
- **NDX** and **XSP** are experimental. Each has its own configuration and tuning; none of them simply copies SPX.
- **Paper trading** is the default. Live trading requires an explicit guard.

## What it does

- Collects option-chain and spot snapshots into TimescaleDB.
- Selects 0-DTE butterfly entries using width, regime, and risk rules.
- Manages open positions with profit and drawdown exits.
- Replays stored data for backtests and live-parity checks.
- Publishes metrics, dashboards, and notifications.

```text
Schwab API
   ├─ option/spot collector ──> TimescaleDB ──> backtests and parity reports
   └─ live quotes/orders ─────> entry selection ──> order manager ──> position monitor
                                   │
                                   └────────────> risk engine + metrics + notifications
```

The live orchestrator, `run_live.py`, runs collection, entry and order management, and position monitoring together.

## Quick start

```bash
uv sync                      # install dependencies
cp .env.example .env         # then fill in credentials
uv run pytest                # tests
uv run ruff check .          # lint
```

### Run with Docker

SPX starts by default. NDX and XSP are opt-in profiles.

```bash
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml --profile ndx --profile xsp up -d
docker compose -f infra/docker-compose.yml ps
```

| Asset | Container | Metrics |
|---|---|---|
| SPX | `butterfly_spx_app` | `127.0.0.1:8000` |
| NDX | `butterfly_ndx_app` | `127.0.0.1:8001` |
| XSP | `butterfly_xsp_app` | `127.0.0.1:8003` |

Check logs with `docker logs --tail 100 <container>`.

### Run on the host

```bash
uv run python src/butterfly_guy/scripts/run_live.py --config configs/config.yaml
uv run python src/butterfly_guy/scripts/run_live.py --config configs/config_ndx.yaml
uv run python src/butterfly_guy/scripts/run_live.py --config configs/config_xsp.yaml
```

## Configuration

| File | Role |
|---|---|
| `configs/config.yaml` | SPX (default) |
| `configs/config_ndx.yaml` | NDX (experimental) |
| `configs/config_xsp.yaml` | XSP (experimental) |

Credentials live in `.env` and `tokens.json`. Never commit them.

Docker Compose also needs `SCHWAB_GATEWAY_TOKEN_DIR`, normally set in `infra/.env`. Point it to a dedicated host directory that contains `tokens.json`. Don't point it at the repository root or at the token file itself.

```dotenv
SCHWAB_GATEWAY_TOKEN_DIR=/absolute/path/to/schwab-token-directory
```

The trading/gateway uid must be able to write to this directory, because token refresh uses a sibling lock file and an atomic replace. Compose refuses to start while the variable is unset.

## Before trading real money

All three assets are paper-only unless the owner explicitly authorizes a supervised live canary. Before any restart, deploy, or live pilot, follow [`docs/live-runbook.md`](docs/live-runbook.md). The runbook requires:

- zero `OPEN` trades in the database,
- no working or unknown Schwab orders,
- a clean broker/database reconciliation.

## Schwab gateway

Market data comes through the standalone, read-only [SchwabGateway](https://github.com/hollowc2/SchwabGateway) service. Butterfly Guy pins `schwab-gateway-sdk` 0.5.0 and `schwab-token-store` v0.1.0 in `pyproject.toml` and `uv.lock`.

| Path | Market data | Accounts, orders, tokens |
|---|---|---|
| Deployed paper strategies (`infra/docker-compose.gateway-paper-cutover.yml` overlay) | Gateway | Direct Schwab client |
| Base Compose file (local use and rollback) | Direct Schwab client (gateway is opt-in) | Direct Schwab client |

The gateway never routes orders or account operations. Real-money trading may not use gateway market data until a reviewed force-fresh option-chain policy exists.

This repo keeps two consumer-side checks:

- `tools/butterfly_gateway_acceptance.py` checks paper-strategy readiness and environment invariants.
- `tools/gateway_cutover_flatness_audit.py` runs the authenticated broker/database flatness gate.

Everything else about the gateway (building, deploying, monitoring, keys, rollback) lives in the SchwabGateway repo. For the current status, see [`docs/architecture/schwab-gateway-current-status.md`](docs/architecture/schwab-gateway-current-status.md). For history, see [`docs/archive/schwab-gateway/`](docs/archive/schwab-gateway/). For Level II order books, see [`docs/gateway-order-books.md`](docs/gateway-order-books.md).

## Backtesting and research

`run_backtest_db.py` replays TimescaleDB history through the same strategy components the live system uses.

```bash
# One day, or a date range
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2025-01-15 2025-01-15 --asset SPX
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2025-01-01 2025-03-31 --asset SPX

# Compare midpoint, executable bid/ask, and bid/ask plus $0.05 slippage
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2025-01-01 2025-03-31 \
  --asset SPX --execution-accounting-report

# Parameter sweep
uv run python src/butterfly_guy/scripts/run_backtest_db.py --asset SPX --sweep

# Same backtest inside the running container
docker exec butterfly_spx_app python -m butterfly_guy.scripts.run_backtest_db 2026-05-05 2026-05-05 --asset SPX
```

`--asset NDX` and `--asset XSP` also work, but treat them as experimental.

> `run_entry_analysis.py` and `SimulationEngine.simulate_day()` are legacy paths with their own defaults. They are not live-parity evidence. Use `run_backtest_db.py` instead.

### Safeguards against misleading results

- **No lookahead.** VIX inputs are limited to values known at the simulated decision time.
- **Asset identity.** Chain caches are partitioned by asset, so SPX, NDX, and XSP data never mix.
- **Incomplete sessions.** Sessions that end before 15:00 ET are excluded rather than given a made-up exit.
- **Cash settlement.** Positions held to the close settle at intrinsic value against the official index close, using the same function as the paper runtime. Settlement has no exit fill, slippage, or closing commission.
- **Missing settlement.** A held position with no same-session close is excluded. `--legacy-end-of-day-mark` restores the old final-mark fallback, for diagnostic comparison only.
- **Execution accounting.** `--execution-accounting-report` keeps decisions on the midpoint model, then:
  - prices entries at the outer-leg asks and twice the center bid,
  - prices exits at the outer-leg bids and twice the center ask,
  - charges $0.65 per contract per side.

  The stress case moves every fill $0.05 against you. Missing or crossed markets are reported and excluded, never filled at the midpoint.
- **Reproducibility.** Sweep CSVs record the Git SHA, command, config, data coverage, exposure, expectancy, average win and loss, and cost drag.

A sweep ranks the same sample it evaluates, so treat its winners as hypotheses. Freeze a candidate and confirm it on chronological holdouts before considering it for paper trading.

The discovery runner handles that holdout step. It crosses the recorded spread, includes commissions, reports train, validation, and test splits in chronological order, and writes reproducible artifacts to `reports/strategy_discovery/`:

```bash
uv run python src/butterfly_guy/scripts/discover_options_strategy.py
```

### Inspection and reports

```bash
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --method VIX
uv run python src/butterfly_guy/scripts/report_trade_ladders.py 2026-05-20 --underlying SPX
uv run python src/butterfly_guy/scripts/report_selection_parity.py 2026-05-15 2026-05-29 --asset SPX
uv run python src/butterfly_guy/scripts/report_exit_mark_parity.py --trade-id 87
uv run python src/butterfly_guy/scripts/generate_live_performance.py
```

## Repository layout

| Path | Purpose |
|---|---|
| `src/butterfly_guy/scripts/` | Command-line entry points |
| `src/butterfly_guy/strategy/` | Butterfly and width selection, regimes, entry filters |
| `src/butterfly_guy/execution/` | Order building and price-ladder retries |
| `src/butterfly_guy/position/` | Position monitoring and exit state machine |
| `src/butterfly_guy/risk/` | Loss limits, trade caps, buying-power guards |
| `src/butterfly_guy/data/` | Schwab client, chain collection, data models |
| `src/butterfly_guy/backtest/` | Replay and simulation engine |
| `src/butterfly_guy/core/` | Config, logging, shared settings |
| `src/butterfly_guy/db/` | TimescaleDB pool, migrations, queries |
| `src/butterfly_guy/quant_engine/` | Black-Scholes pricing and IV/skew modeling |
| `src/butterfly_guy/services/` | Trade and position orchestration, notifications |
| `src/butterfly_guy/reports/` | Reports and published pages |
| `src/butterfly_guy/gateway_client/` | Default-off shadow comparison against SchwabGateway |
| `configs/` | Per-asset configuration |
| `infra/` | Docker Compose and observability |
| `docs/` | Architecture notes, runbooks, research |
| `tests/` | Tests |

New to the code? Read these in order:

1. `configs/config.yaml`
2. `src/butterfly_guy/scripts/run_live.py`
3. `src/butterfly_guy/strategy/`
4. `src/butterfly_guy/execution/`
5. `src/butterfly_guy/position/`

## Contributing

- Keep changes small and focused. Broad refactors rarely pay off here.
- Add or update focused tests for behavior changes, and run the narrowest useful check.
- Compare backtests against the config for the same asset.
- Leave unrelated configs and assets alone.

## License

MIT
