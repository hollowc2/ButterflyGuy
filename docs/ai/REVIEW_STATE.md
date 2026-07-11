# ButterflyGuy AI Review State

## Current Objective

Completed one surgical SPX pre-live review/fix cycle: startup, runtime, and filled-entry repair reconciliation now require exact signed broker quantities and the DB-derived `+1/-2/+1` butterfly ratio.

## Current Cycle Checkpoints

- **Review complete:** The shared startup/runtime reconciliation path currently reduces Schwab positions to a symbol set and adds `longQuantity + shortQuantity`, so matching symbols with a wrong sign, partial fill, or oversized ratio can pass. The existing daily report parser confirms the repo convention is signed `longQuantity - shortQuantity`. Planned fix: compare one shared broker quantity map against DB-derived lower `+quantity`, center `-2 * quantity`, and upper `+quantity`, including filled-entry repair. No broker, DB, service, or Docker commands were run.
- **Implementation complete:** Added redacted synthetic Schwab payload coverage that first failed at import because the signed-position helper did not exist. Replaced symbol-only parsing with a net signed quantity map, derived exact lower/center/upper quantities from each OPEN trade, and made the shared startup/runtime assertion report missing, unexpected, and wrong-quantity legs. Filled-entry intent repair now requires the same exact ratio before inserting a recovered trade. The focused runner and broker-intent tests pass (`18 passed`).
- **Verification complete:** Expanded the focused coverage to prove startup rejection of wrong-sign, partial, oversized, and incomplete butterflies; exact multi-lot acceptance; runtime gate closure; and filled-entry repair rejection. Final narrow verification passed (`21 passed`), targeted Ruff and `git diff --check` passed, and `graphify update .` rebuilt the code graph (3,429 nodes, 5,717 edges, 289 communities). The unrelated `run_backtest_db.py` worktree change remains untouched.

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

1. **Critical — execution/risk — change now:** Broker/DB reconciliation accepts extra unknown SPX option positions when all three DB legs are also present because it checks only `expected_symbols.issubset(broker_symbols)`. An unrelated or partially orphaned SPX position can therefore leave the entry gate clear. File: `scripts/run_live.py`. Fix: require exact leg-symbol equality and report extra/missing symbols; add a focused regression test.
2. **High — execution/risk — completed:** Reconciliation now nets Schwab `longQuantity - shortQuantity` by symbol and compares the exact broker map with DB-derived lower `+quantity`, center `-2 * quantity`, and upper `+quantity` positions. Matching symbols with a wrong sign, partial fill, or oversized ratio fail closed at startup, runtime, and filled-entry repair. Files: `scripts/run_live.py`, focused redacted synthetic fixtures/tests.
3. **High — execution/ops — later:** Complex-order status and child-order mappings remain based on anticipated status names rather than a completed paper/shadow evidence set. Files: `execution/order_manager.py`, `scripts/run_live.py`, `scripts/report_broker_order_statuses.py`. Fix: collect redacted read-only status reports, encode observed parent/child cases, and add fixtures for partial/cancel/reject/expire/fill transitions.
4. **High — ops — later:** `/health` returns 200 based only on the metrics HTTP thread and does not expose DB, broker auth, data freshness, risk halt, or reconciliation gate readiness. Files: `core/metrics.py`, `scripts/run_live.py`, Docker health configuration. Fix as a separate PR with a small thread-safe readiness snapshot owned by the orchestrator.
5. **Medium — backtest/tests — later:** Backtests share selection/profit-policy pieces but cannot prove broker execution parity; modeled fills can remain optimistic relative to complex-order queueing, partial fills, and cancel races. Files: `backtest/simulation_engine.py`, execution/parity reports. Fix: keep this explicit in reports and calibrate models only from observed paper/shadow order lifecycle data.
6. **Medium — ops/tests — later:** Restart, broker outage, DB outage, manual flatten, and rollback procedures are documented but not yet demonstrated by repeatable drills. Files: `prelivecheckout.md` and operational runbook/tests. Fix: execute controlled paper/shadow drills and retain redacted evidence.

## Active Work Item

Completed: exact signed broker-position quantity and `+1/-2/+1` butterfly-ratio reconciliation using redacted synthetic Schwab fixtures. The next unfinished item is observed complex-order parent/child status mapping and restart reconciliation evidence.

## Changes Made This Session

- Replaced broker symbol-set extraction with signed quantity normalization using `longQuantity - shortQuantity`, netted by option symbol.
- Derived exact expected positions from each OPEN DB trade as lower `+quantity`, center `-2 * quantity`, and upper `+quantity`.
- Made incomplete, duplicate-symbol, or non-positive-quantity DB butterflies fail closed instead of accepting a reduced leg map.
- Made the shared startup/runtime assertion report missing, unexpected, and wrong-quantity legs and fail closed on any mismatch.
- Applied the same exact ratio invariant before filled-entry intent repair can insert a recovered DB trade.
- Added focused redacted synthetic fixtures/tests for exact multi-lot acceptance, wrong-sign/partial/oversized rejection, runtime gate closure, and repair rejection.
- Ran `graphify update .`; generated graph artifacts were refreshed as required by `AGENTS.md`.

## Commands Run

- Read the ponytail skill instructions.
- Searched review-related memory registry entries without reading secrets.
- Read `graphify-out/GRAPH_REPORT.md` and checked for the graph wiki index.
- Queried graphify for the SPX live entry/order-intent/reconciliation path.
- Read the required repo docs and traced the shared startup/runtime assertion, filled-entry repair, Schwab position fields, DB trade quantity, order-builder ratio, and focused callers/tests.
- Checked git status and found a pre-existing unrelated modification to `src/butterfly_guy/scripts/run_backtest_db.py`; it will remain untouched.
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_run_live.py tests/test_broker_order_intents.py -q`
- `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/butterfly_guy/scripts/run_live.py tests/test_run_live.py tests/test_broker_order_intents.py`
- `/home/billy/.local/bin/graphify update .`
- `git status --short`
- `git diff --check`
- Inspected the scoped diff and repository diff stat.

## Tests / Verification

- PASS: 21 focused tests in `tests/test_run_live.py` and `tests/test_broker_order_intents.py` (`21 passed in 1.66s`).
- PASS: targeted Ruff check for the changed live runner and focused tests.
- PASS: `git diff --check`.
- PASS: graphify AST update rebuilt the code graph (3,429 nodes, 5,717 edges, 289 communities).
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
