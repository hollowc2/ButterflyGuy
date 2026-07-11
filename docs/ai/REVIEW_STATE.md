# ButterflyGuy AI Review State

## Current Objective

Completed one surgical follow-up SPX pre-live review/fix cycle: explicit zero DB/intent quantities now fail closed instead of being reconciled as one-lot `+1/-2/+1` butterflies.

## Current Cycle Checkpoints

- **Review complete:** The committed signed broker-position map and exact `+quantity/-2 * quantity/+quantity` comparison correctly cover startup, runtime, extra legs, and filled-entry repair, but `_open_trade_positions()` converts an explicit DB quantity of zero to one via `row.get("quantity") or 1`. That contradicts its non-positive-quantity guard and can let corrupt zero-quantity OPEN state reconcile as a one-lot butterfly. Planned fix: preserve the established default only when quantity is absent/`None`, then reject zero through the shared helper. No broker, DB, service, or Docker commands were run.
- **Implementation complete:** Added redacted synthetic startup and filled-entry repair regressions that both failed before the fix. `_open_trade_positions()` now defaults only absent/`None` quantity to one and rejects explicit zero through its existing non-positive guard; filled-entry repair preserves the same quantity through validation and insertion. The focused reconciliation tests pass (`23 passed`).
- **Verification complete:** Final narrow verification passed (`23 passed in 1.71s`), targeted Ruff and `git diff --check` passed, and `graphify update .` rebuilt the code graph (3,434 nodes, 5,725 edges, 276 communities). The unrelated `run_backtest_db.py` worktree change remains untouched.

## Non-Negotiable Rules

- Never place live trades or invoke Schwab write APIs.
- Never inspect, print, rewrite, or summarize credentials, tokens, account IDs, or secret values.
- Do not remove or weaken risk controls.
- Do not change strategy behavior without an explicit justification and focused regression tests.
- Keep changes small, reviewable, SPX-first, and limited to this review cycle.
- Treat NDX and XSP as experimental, not production-equivalent.

## Repo Context

ButterflyGuy is a Python 0-DTE butterfly trading and research system using Schwab, TimescaleDB, Docker, Prometheus, and Grafana. SPX is the primary production path; NDX and XSP are experimental.

## Architecture Map

- **Configuration/startup:** `scripts/run_live.py` loads `AppConfig`, applies an SPX-only live-money/account confirmation guard, starts metrics, initializes TimescaleDB/migrations and Schwab, and constructs query/service objects.
- **Market data:** `OptionChainCollector` polls Schwab only during trading sessions and persists option-chain, spot, VIX, and daily-bar data. `TradeService` also fetches fresh broker chain/spot data for each entry attempt and requires a recent persisted chain snapshot in live mode.
- **Entry/strategy:** `TradeService.attempt_entry()` applies time, risk, balance, chain/VIX freshness, direction/regime, width, candidate, and quote constraints. Shared `strategy.entry_selection` helpers are used by live selection and parity tooling.
- **Execution:** `OrderManager` builds complex butterfly orders. Paper mode uses modeled fills; live mode checks working orders, persists a broker intent before its single non-retried submit, records the broker order ID/status, polls, cancels unfilled orders, and fails closed on partial/cancel-pending states.
- **Persistence/recovery:** `butterfly_trades`, `decision_log`, `daily_risk_state`, and `broker_order_intents` hold local lifecycle state. `run_live.py` reconciles broker positions/orders with DB state at startup and every 15 seconds; unambiguous filled intents can repair missing entry/exit DB transitions.
- **Position/exit:** `PositionService` restores an open DB trade, polls fresh chains, updates `PositionManager` and `ProfitStateMachine`, persists peak state, and routes exit orders through `OrderManager`; index positions are cash-settled from the final regular-session close after market close.
- **Risk:** `RiskEngine` checks market/trading day, halt state, daily trade count/loss, position size, buying power, weekly loss, and consecutive-loss warning policy. Live entry rechecks risk under a PostgreSQL advisory lock immediately before submit.
- **Backtest/parity:** `SimulationEngine` and DB loaders replay historical snapshots with shared selection and profit-policy components, while order execution/fill modeling remains separate from the broker live path. Selection and exit-mark parity reports compare stored/live decisions.
- **Operations:** Docker runs separate SPX, NDX, and XSP app services with TimescaleDB and Prometheus/Grafana integration. `/health` currently proves only that the metrics thread/process is serving HTTP.

## Important Files Reviewed

- `AGENTS.md`
- `README.md`
- `CLAUDE.md`
- `prelivecheckout.md`
- `pyproject.toml`
- `configs/config.yaml`
- `infra/docker-compose.yml`
- `graphify-out/GRAPH_REPORT.md`
- `src/butterfly_guy/scripts/run_live.py`
- `src/butterfly_guy/services/trade_service.py`
- `src/butterfly_guy/services/position_service.py`
- `src/butterfly_guy/execution/order_manager.py`
- `src/butterfly_guy/data/{collector,schwab_client,schemas}.py`
- `src/butterfly_guy/risk/risk_engine.py`
- `src/butterfly_guy/position/{position_manager,state_machine,profit_policy}.py`
- `src/butterfly_guy/strategy/` selection, builder, selector, and width modules
- `src/butterfly_guy/backtest/{simulation_engine,db_loader,data_loader}.py`
- Focused execution, live runner, risk, position, strategy, data, and parity tests under `tests/`

## Ranked Issues

1. **High — execution/ops — later:** Complex-order status and child-order mappings remain based on anticipated status names rather than a completed paper/shadow evidence set. Files: `execution/order_manager.py`, `scripts/run_live.py`, `scripts/report_broker_order_statuses.py`. Fix: collect redacted read-only status reports, encode observed parent/child cases, and add fixtures for partial/cancel/reject/expire/fill transitions.
2. **High — ops — later:** `/health` returns 200 based only on the metrics HTTP thread and does not expose DB, broker auth, data freshness, risk halt, or reconciliation gate readiness. Files: `core/metrics.py`, `scripts/run_live.py`, Docker health configuration. Fix as a separate PR with a small thread-safe readiness snapshot owned by the orchestrator.
3. **Medium — backtest/tests — later:** Backtests share selection/profit-policy pieces but cannot prove broker execution parity; modeled fills can remain optimistic relative to complex-order queueing, partial fills, and cancel races. Files: `backtest/simulation_engine.py`, execution/parity reports. Fix: keep this explicit in reports and calibrate models only from observed paper/shadow order lifecycle data.
4. **Medium — ops/tests — later:** Restart, broker outage, DB outage, manual flatten, and rollback procedures are documented but not yet demonstrated by repeatable drills. Files: `prelivecheckout.md` and operational runbook/tests. Fix: execute controlled paper/shadow drills and retain redacted evidence.

Completed execution/risk items: exact broker/DB leg-symbol equality, signed Schwab quantity normalization, DB-derived `+quantity/-2 * quantity/+quantity` comparison, and explicit zero-quantity rejection at startup, runtime, and filled-entry repair.

## Active Work Item

Completed: exact signed broker-position quantity and `+1/-2/+1` butterfly-ratio reconciliation, including explicit zero-quantity rejection, using redacted synthetic Schwab fixtures. The next unfinished item is observed complex-order parent/child status mapping and restart reconciliation evidence.

## Changes Made This Session

- Fixed the shared expected-position parser so explicit zero quantity reaches the existing non-positive guard instead of defaulting to one.
- Preserved that validated quantity through filled-entry repair and recovered-trade insertion.
- Added focused redacted synthetic startup and filled-entry repair regressions for zero quantity.
- Ran `graphify update .`; generated graph artifacts were refreshed as required by `AGENTS.md`.

## Commands Run

- Read the ponytail skill instructions.
- Searched review-related memory registry entries without reading secrets.
- Read `graphify-out/GRAPH_REPORT.md` and checked for the graph wiki index.
- Queried graphify for the SPX live entry/order-intent/reconciliation path.
- Read the required repo docs and traced the shared startup/runtime assertion, filled-entry repair, Schwab position fields, DB trade quantity, order-builder ratio, and focused callers/tests.
- Checked git status and found a pre-existing unrelated modification to `src/butterfly_guy/scripts/run_backtest_db.py`; it will remain untouched.
- Ran each new zero-quantity regression before implementation and confirmed it failed.
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_run_live.py tests/test_broker_order_intents.py -q`
- `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/butterfly_guy/scripts/run_live.py tests/test_run_live.py tests/test_broker_order_intents.py`
- `/home/billy/.local/bin/graphify update .`
- `git status --short`
- `git diff --check`
- Inspected the scoped diff and repository diff stat.

## Tests / Verification

- PASS: 23 focused tests in `tests/test_run_live.py` and `tests/test_broker_order_intents.py` (`23 passed in 1.71s`).
- PASS: targeted Ruff check for the changed live runner and focused tests.
- PASS: `git diff --check`.
- PASS: graphify AST update rebuilt the code graph (3,434 nodes, 5,725 edges, 276 communities).
- Not run: full test suite, Docker/runtime checks, DB queries, or Schwab calls; they were unnecessary for this isolated mocked reconciliation change and could expand operational risk/scope.

## Decisions Made

- Limit this session to one review/fix cycle.
- Do not run the application, Docker services, migrations, or any command capable of broker writes.
- Treat exact broker-vs-DB signed quantity equality as the conservative invariant. Any missing, extra, wrong-sign, partial, or oversized SPX option leg is unsafe.
- Use the established Schwab convention `longQuantity - shortQuantity` and only redacted synthetic payloads; do not inspect account payloads.
- Keep this cycle source/test-only; do not rebuild or restart services while the worktree contains unrelated user work.

## Deferred / Avoided Changes

- No broad health/readiness framework, order-status expansion, backtest fill redesign, or operational drill in this cycle.
- Do not touch the user's existing `run_backtest_db.py` modification.

## Remaining Risks

- Real Schwab complex-order parent/child status coverage remains unproven.
- Health is process-level rather than dependency/readiness-level.
- Operational recovery drills remain unproven.
- Historical fill modeling cannot reproduce all live broker lifecycle states.

## Recommended Next PRs

1. Map observed complex-order parent/child statuses and prove restart reconciliation with paper/shadow drills.
2. Add an orchestrator-owned readiness snapshot for DB, broker auth, data freshness, risk halt, and broker reconciliation.
3. Execute and document controlled restart/outage/manual-flatten/rollback drills.

## Next Session Launch Prompt

Read `docs/ai/REVIEW_STATE.md` first and summarize it. Then perform one review/fix cycle on the highest-priority unfinished item: observed complex-order parent/child status mapping and restart reconciliation evidence for SPX. Use only redacted read-only evidence or synthetic fixtures, make no broker writes or service changes, preserve unrelated worktree changes, add focused tests, run the narrowest verification, run `graphify update .` after code changes, and update `docs/ai/REVIEW_STATE.md` at every required checkpoint.
