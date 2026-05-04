# AGENTS.md

Repository instructions for Codex and other coding agents working in this tree.

## Project Context

Butterfly Guy is an automated 0-DTE butterfly options trading system for SPX, NDX, and XSP using the Charles Schwab API. It is currently configured for paper trading and runs with Docker, TimescaleDB, Prometheus, and Grafana.

This code can affect live trading behavior. Treat strategy, execution, risk, token, and configuration changes as high-impact even when paper trading is enabled.

## First Reads

- `README.md` is the user-facing overview and has the current research/backtest commands.
- `CLAUDE.md` contains a detailed architecture map and historical agent guidance. Use it as supporting context, but follow this `AGENTS.md` first for Codex behavior.
- Main source lives under `src/butterfly_guy/`.
- Runtime configs live under `configs/`.
- Docker and monitoring config live under `infra/`.
- Tests live under `tests/`.

## Common Commands

Install or refresh dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
uv run pytest tests/test_strategy.py -v
```

Run lint checks:

```bash
uv run ruff check .
```

Run a DB backtest:

```bash
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2025-01-15 2025-01-15 --asset SPX
uv run python src/butterfly_guy/scripts/run_backtest_db.py --asset SPX --sweep
```

Inspect historical entry selection:

```bash
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03
uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --method VIX
```

Docker stack:

```bash
docker compose -f infra/docker-compose.yml --profile spx up -d
docker compose -f infra/docker-compose.yml --profile ndx up -d
docker compose -f infra/docker-compose.yml --profile xsp up -d
docker compose -f infra/docker-compose.yml ps
```

Useful container names:

- `butterfly_spx_app`
- `butterfly_ndx_app`
- `butterfly_xsp_app`

## Architecture Map

- `core/`: config loading, logging, metrics, time utilities.
- `data/`: Schwab API client, option chain collection, schemas.
- `db/`: asyncpg pool, migrations, SQL queries.
- `strategy/`: butterfly construction/selection, direction filters, VIX anchoring, regime classification.
- `execution/`: order construction and price ladder retry logic.
- `position/`: mark polling, profit state machine, exit signals.
- `risk/`: daily trade count, loss limits, halt logic, account/buying-power guards.
- `services/`: entry and position orchestration, notifications.
- `quant_engine/`: pricing, IV skew, synthetic chain generation.
- `backtest/`: simulation engine, sweeps, loaders.
- `scripts/`: runnable entry points.

## Configuration Notes

- `configs/config.yaml`: default SPX config.
- `configs/config_ndx.yaml`: NDX-specific config.
- `configs/config_xsp.yaml`: XSP-specific config.
- `.env` and `tokens.json` are local/runtime secrets. Do not print, commit, rewrite, or summarize their secret values.
- Paper fills are intended to use mark price `(bid + ask) / 2`, matching the project convention.

## Working Rules

- Make surgical changes. Touch only files needed for the request.
- Do not refactor adjacent code or reformat unrelated files.
- Prefer existing project patterns over new abstractions.
- For behavioral changes, add or update focused tests when practical.
- For bug fixes, prefer a failing test or reproduction before changing behavior.
- Keep strategy, risk, and execution changes conservative and explicit.
- Do not change trading limits, paper/live mode, account guards, order routing, or token handling unless the user directly asks.
- If a command may place orders, call Schwab write APIs, or alter live services, state the risk before running it.
- Never use destructive git commands unless the user explicitly asks.

## Verification Expectations

Choose the narrowest useful verification for the change:

- Pure docs/config explanation: no tests required.
- Python logic: run the relevant `uv run pytest ...` target.
- Broad shared behavior: run `uv run pytest`.
- Formatting/import changes: run `uv run ruff check .`.
- Docker/runtime changes: inspect `docker compose -f infra/docker-compose.yml ps` and relevant container logs when needed.

If verification cannot be run because dependencies, services, database, network, or credentials are unavailable, say exactly what was skipped and why.
