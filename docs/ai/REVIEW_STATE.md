# ButterflyGuy AI Review State

## Current Objective

Completed five surgical SPX review/fix cycles on complex-order parent/child status mapping and restart reconciliation, using only redacted synthetic fixtures and no broker writes or service changes.

## Current Cycle Checkpoints

- **Cycle 1 review complete:** Reconciliation recursively collects child symbols but only checks the top-level order status. A bot-owned `WORKING` parent with a nested partial-fill or cancel-pending child is therefore allowed. Planned fix: recursively inspect statuses and fail closed on an unsafe descendant. No broker, DB, service, or Docker commands were run.
- **Cycle 1 implementation complete:** Added redacted synthetic nested-partial regressions, confirmed the gap in reconciliation and active fill polling, and added one shared recursive status helper used by both paths.
- **Cycle 1 verification complete:** Focused broker-intent tests pass (`9 passed`), targeted Ruff passes, and `graphify update .` rebuilt the graph (3,439 nodes, 5,733 edges, 274 communities).
- **Cycle 2 review complete:** Intent ownership and broker-status refresh match only the top-level `orderId`. A submitted bot order nested under a broker wrapper is misclassified as unknown and its child payload is not persisted. Planned fix: recursively match order IDs and update the intent from the exact matching node.
- **Cycle 2 implementation complete:** Added a failing synthetic wrapper/child regression, then added a small recursive order walker so nested IDs establish ownership and the exact matching child status/payload updates the intent.
- **Cycle 2 verification complete:** Focused broker-intent tests pass (`10 passed`), targeted Ruff passes, and `graphify update .` rebuilt the graph (3,445 nodes, 5,744 edges, 283 communities).
- **Cycle 3 review complete:** An SPX order with an unrecognized nonempty parent/child status is ignored when positions happen to match. Planned fix: fail closed on any status outside the explicit working, partial, cancel-pending, and terminal sets so new broker states require deliberate mapping.
- **Cycle 3 implementation complete:** Added a failing synthetic unknown-child-status regression and one union check over the existing status sets; any unmapped SPX parent/child status now stops reconciliation with the observed status name.
- **Cycle 3 verification complete:** Focused broker-intent tests pass (`11 passed`), targeted Ruff passes, and `graphify update .` rebuilt the graph (3,449 nodes, 5,749 edges, 262 communities).
- **Cycle 4 review complete:** `_order_statuses()` omits absent values, so a relevant SPX order node with no status bypasses both known-state handling and the new unmapped-state guard. Planned fix: reject relevant parent/child payloads containing a missing status.
- **Cycle 4 implementation complete:** Added a failing synthetic missing-status regression, then made every relevant SPX parent/child node require a nonempty status before classification.
- **Cycle 4 verification complete:** Focused broker-intent tests pass (`12 passed`), targeted Ruff passes, and `graphify update .` rebuilt the graph (3,453 nodes, 5,754 edges, 283 communities).
- **Cycle 5 review complete:** Unknown-order ownership is recursive, but the unknown-working-order predicate still checks only the top-level status. An external SPX wrapper with a terminal parent and a nested working/cancel-pending child can evade the startup block. Planned fix: use the recursive status set in that predicate.
- **Cycle 5 implementation complete:** Added synthetic external-wrapper regressions and changed both reconciliation and active entry blocking to intersect all recursive parent/child statuses and IDs.
- **Cycle 5 verification complete:** Final focused execution/reconciliation tests pass (`78 passed in 1.82s`), targeted Ruff and `git diff --check` pass, and `graphify update .` rebuilt the graph (3,475 nodes, 5,798 edges, 275 communities). The unrelated `run_backtest_db.py` worktree change remains untouched.

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

1. **High — execution/ops — later:** Complex-order status names remain based on anticipated values rather than a completed paper/shadow evidence set. Restart reconciliation now recursively maps parent/child IDs and statuses and fails closed on missing, unmapped, partial, cancel-pending, or unknown working child states. Files: `execution/order_manager.py`, `scripts/run_live.py`, `scripts/report_broker_order_statuses.py`. Next: collect redacted read-only status reports and map only observed additions.
2. **High — ops — later:** `/health` returns 200 based only on the metrics HTTP thread and does not expose DB, broker auth, data freshness, risk halt, or reconciliation gate readiness. Files: `core/metrics.py`, `scripts/run_live.py`, Docker health configuration. Fix as a separate PR with a small thread-safe readiness snapshot owned by the orchestrator.
3. **Medium — backtest/tests — later:** Backtests share selection/profit-policy pieces but cannot prove broker execution parity; modeled fills can remain optimistic relative to complex-order queueing, partial fills, and cancel races. Files: `backtest/simulation_engine.py`, execution/parity reports. Fix: keep this explicit in reports and calibrate models only from observed paper/shadow order lifecycle data.
4. **Medium — ops/tests — later:** Restart, broker outage, DB outage, manual flatten, and rollback procedures are documented but not yet demonstrated by repeatable drills. Files: `prelivecheckout.md` and operational runbook/tests. Fix: execute controlled paper/shadow drills and retain redacted evidence.

Completed execution/risk items: exact broker/DB leg-symbol equality, signed Schwab quantity normalization, DB-derived `+quantity/-2 * quantity/+quantity` comparison, and explicit zero-quantity rejection at startup, runtime, and filled-entry repair.

## Active Work Item

Completed: synthetic parent/child restart reconciliation now recursively matches broker order IDs, persists the exact matched child payload, blocks unsafe nested states, and fails closed on missing or unmapped statuses. The next unfinished item is collecting redacted read-only paper/shadow evidence for the real Schwab status vocabulary.

## Changes Made This Session

- Added one shared recursive order walker for nested IDs and statuses; reconciliation reuses it for symbols and exact child matching.
- Applied recursive unsafe-state checks to active order polling, post-cancel checks, and entry blocking as well as restart/runtime reconciliation.
- Updated intent refresh to match and persist the exact nested broker order node.
- Made restart/runtime reconciliation fail closed on nested partial/cancel-pending states, unmapped statuses, missing statuses, and unknown nested working orders.
- Added seven focused redacted synthetic regressions; six were confirmed failing before their fixes.
- Ran `graphify update .` after every code cycle and after the final cleanup.

## Commands Run

- Read the ponytail skill instructions.
- Searched review-related memory registry entries without reading secrets.
- Read `graphify-out/GRAPH_REPORT.md` and checked for the graph wiki index.
- Queried graphify for the SPX live entry/order-intent/reconciliation path.
- Read the required repo docs and traced the shared startup/runtime assertion, filled-entry repair, Schwab position fields, DB trade quantity, order-builder ratio, and focused callers/tests.
- Checked git status and found a pre-existing unrelated modification to `src/butterfly_guy/scripts/run_backtest_db.py`; it will remain untouched.
- Ran six parent/child status regressions before implementation and confirmed each failed.
- Repeated focused `tests/test_broker_order_intents.py` verification after each cycle.
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_order_manager.py tests/test_broker_order_intents.py tests/test_run_live.py -q`
- `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/butterfly_guy/execution/order_manager.py src/butterfly_guy/scripts/run_live.py tests/test_order_manager.py tests/test_broker_order_intents.py tests/test_run_live.py`
- Repeated `/home/billy/.local/bin/graphify update .` after code changes.
- `git status --short`
- `git diff --check`
- Inspected the scoped diff and repository diff stat.

## Tests / Verification

- PASS: 78 focused tests in `tests/test_order_manager.py`, `tests/test_broker_order_intents.py`, and `tests/test_run_live.py` (`78 passed in 1.82s`).
- PASS: targeted Ruff check for the changed live runner and focused tests.
- PASS: `git diff --check`.
- PASS: final graphify AST update rebuilt the code graph (3,475 nodes, 5,798 edges, 275 communities).
- Not run: full test suite, Docker/runtime checks, DB queries, or Schwab calls; they were unnecessary for this isolated mocked reconciliation change and could expand operational risk/scope.

## Decisions Made

- Limit this session to five small source/test cycles on the highest-priority status/restart item.
- Do not run the application, Docker services, migrations, or any command capable of broker writes.
- Treat exact broker-vs-DB signed quantity equality as the conservative invariant. Any missing, extra, wrong-sign, partial, or oversized SPX option leg is unsafe.
- Treat every missing or unmapped relevant broker status as unsafe until read-only evidence supports an explicit mapping.
- Use only redacted synthetic broker payloads; do not inspect account payloads.
- Keep this cycle source/test-only; do not rebuild or restart services while the worktree contains unrelated user work.

## Deferred / Avoided Changes

- No broad health/readiness framework, speculative order-status expansion, backtest fill redesign, or operational drill in these cycles.
- Do not touch the user's existing `run_backtest_db.py` modification.

## Remaining Risks

- Real Schwab complex-order parent/child status vocabulary remains unproven; synthetic restart behavior is now fail-closed.
- Health is process-level rather than dependency/readiness-level.
- Operational recovery drills remain unproven.
- Historical fill modeling cannot reproduce all live broker lifecycle states.

## Recommended Next PRs

1. Collect a redacted read-only complex-order status report and add only observed status mappings/fixtures.
2. Add an orchestrator-owned readiness snapshot for DB, broker auth, data freshness, risk halt, and broker reconciliation.
3. Execute and document controlled restart/outage/manual-flatten/rollback drills.

## Next Session Launch Prompt

Read `docs/ai/REVIEW_STATE.md` first and summarize it. Then collect or review one redacted read-only paper/shadow complex-order status report for SPX and perform one surgical mapping/fix cycle only if the evidence exposes an unmapped state. Make no broker writes or service changes, preserve unrelated worktree changes, add a focused synthetic fixture for any observed mapping, run the narrowest verification, run `graphify update .` after code changes, and update `docs/ai/REVIEW_STATE.md` at every required checkpoint.
