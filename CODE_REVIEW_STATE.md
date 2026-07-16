# ButterflyGuy Code Review State

## Repository identity

- Branch: `main`
- Commit reviewed: `d112dcba0a71b5090cf574d08aa7a19ff6eee7c0`
- Review started: 2026-07-12 UTC
- Pre-existing worktree changes (preserve; not created by this review):
  - `configs/universes/liquid.txt`
  - `configs/universes/liquid_meta.json`
  - `src/butterfly_guy/scripts/run_backtest_db.py`

## Review objective

Principal-level engineering, architecture, reliability, and trading-safety audit, emphasizing single sources of truth, order/position safety, async and database correctness, deterministic backtest/paper/live behavior, defensive failure handling, testability, and maintainability. Strategy profitability changes are out of scope.

## Current phase

BG-001 through BG-014 are complete and verified. The durable cross-session checklist is in `CODE_REVIEW_REPORT.md` under **Remediation tracker**. Current work closes follow-up observability, real-DB CI, and deployment-gate gaps without changing paper/live mode.

## Architecture map

- Configuration: `core.config.load_config()` merges YAML with selected environment values into `AppConfig`; the asset YAML is the runtime strategy/risk source, while `run_live._assert_live_config_supported()` adds hard-coded live-policy confirmations.
- Startup: `scripts.run_live.main()` validates live mode, starts metrics, initializes the asyncpg pool, reruns migrations, authenticates Schwab, classifies regime, constructs query/service objects, reconciles live broker/DB state, reconstructs one open trade, restores risk counters, then starts an `asyncio.TaskGroup`.
- Market data: `OptionChainCollector` polls Schwab and persists chains/spot/daily bars; `TradeService` independently fetches a current chain and spot for entry; `PositionService` independently polls three-leg chain data for monitoring.
- Entry: `entry_loop()` -> `TradeService.attempt_entry()` -> time/risk/freshness checks -> shared `strategy.entry_selection.select_entry_candidate()` -> DB candidate/decision audit -> advisory lock and risk recheck -> `OrderManager.execute_single_attempt()`.
- Order submission: `OrderManager` persists `broker_order_intents` before live submission; `SchwabClientWrapper.place_order()` submits once without generic retry; order ID is persisted from `Location`; recursive statuses classify filled/working/partial/cancel-pending/terminal states.
- Position creation: after a reported fill, `TradeService` inserts `butterfly_trades`, links the intent, increments daily risk state, emits metrics/events, and starts `PositionService.monitor_loop()`.
- Position/exit: `PositionManager` computes mark/bid/quote quality and persisted peak; `ProfitStateMachine` owns exit signals; `PositionService` writes pending-exit metadata, calls `OrderManager.execute_exit()`, closes the DB trade, updates risk/metrics, and reports.
- Settlement: after market close, `PositionService` tries Schwab's final regular-session one-minute close, then a chain/spot fallback, computes cash settlement, closes the trade, and records risk/reporting.
- Restart/recovery: startup and a 15-second live reconciler compare exact DB legs/ratios with broker positions and recursive order states; filled entry/exit intents may repair missing trade transitions when explicit broker fill price/time exists.
- Backtest: `run_backtest_db.py` loads the asset YAML and uses shared `select_entry_candidate()` for its primary DB replay, then hands the chosen entry to `SimulationEngine`; legacy `SimulationEngine.simulate_day()` and `run_entry_analysis.py` retain independent selection/default paths.
- Authentication: `SchwabClientWrapper.initialize()` builds the async Schwab client from the token file, requires an explicit account ID, and resolves its account hash; token refresh is external in `tools/`.
- Metrics/notifications: Prometheus globals plus `/metrics`, liveness-only `/health`, and safety-aware `/ready`; Discord for SPX trade events, Telegram for risk/token operational alerts, Prometheus/Alertmanager for runtime failures, and DB `decision_log` for audit events.
- Asset differences: all repo configs and running services are paper-only. The completed XSP canary is broker/DB flat after verified manual-close reconciliation and an XSP-only recreate.

## Files and directories reviewed

- `AGENTS.md`, `README.md`, `CLAUDE.md`, `pyproject.toml`
- `graphify-out/GRAPH_REPORT.md` (stale build from `331e6e92`; used for navigation only) and targeted Graphify queries
- `docs/ai/REVIEW_STATE.md`, relevant `todo.md` sections, `docs/live-runbook.md` graph nodes
- All runtime YAML files and `infra/docker-compose.yml` without reading secret files
- Both GitHub Actions workflows
- All SQL migrations, migration runner, DB pool, and query-layer safety-critical regions
- Runtime/live orchestration, config/time, Schwab client, collector, domain schemas, execution, trade, position, risk, entry selection, and primary/legacy backtest paths
- Complete test inventory plus focused inspection of broker-write isolation and live-safety coverage

## Files still requiring review

- No mandatory repository area remains uninspected. Remaining work is report synthesis, exact line-reference verification, and final state/report cross-check.

## Historical confirmed findings (pre-remediation)

The findings below are retained as the original audit record; BG-001 through
BG-014 are now remediated and the current status is summarized above.

- Terminal broker rejection/expiry stops one order ladder but `entry_loop()` catches it as a generic exception and can start a new full entry attempt 15 seconds later; the top-level loop has no terminal-order regression coverage.
- After a live exit fill and DB close, `PositionService` updates risk before setting local `exited=True`; a risk/DB failure in that interval is swallowed and the monitor can submit another closing order.
- Normal live fill persistence uses submitted limit price and local observation time instead of explicit broker execution price/time; this flows into trades, PnL, risk, and reports.
- Cash settlement initializes value to zero and still closes the trade if both primary and fallback valuation fail.
- Live reconciliation and risk/day initialization use host-local `date.today()` while canonical market date is Eastern; the Compose host/runtime is UTC-oriented, creating a post-20:00 ET date split.
- At the original audit, XSP was configured `paper_trading: false`, was later returned to paper-only, and was re-authorized on 2026-07-16 for one supervised one-contract canary.
- `/health` is process liveness only and remains 200 independent of DB, broker, market-data, risk, reconciler, or monitor state.
- Deployment validates `/opt/butterflyguy` before pulling the pushed commit, then deploys all three apps; validation therefore does not prove the deployed revision and every main push rebuilds the live-enabled XSP canary.
- The PR workflow lets an LLM edit, stages all files, pushes without tests/lint, and can auto-merge after only syntax/LLM review.
- Ruff has 115 violations and is non-blocking in deployment.
- Configuration models lack safety bounds/cross-field validation and silently ignore unknown fields.
- Legacy research/backtest paths duplicate asset defaults and selection logic; `run_entry_analysis.py` has materially stale XSP widths/range/tolerance.
- Migration execution has no applied-version ledger and reruns every migration on every app startup, including primary-key drop/re-add DDL.
- Normal logs disclose an account-hash prefix.

## Suspected findings requiring more evidence

- Schwab client calls have no explicit application-level timeout; confirm schwab-py/httpx effective timeout before classifying hang risk above medium confidence.
- Real Schwab complex-order fill payloads remain insufficient to prove full multi-fill/child fill-price extraction and status vocabulary.

## Decisions already made

- Audit before remediation.
- Do not run broker-write commands or enable live trading.
- Do not inspect or expose `.env`, `tokens.json`, account identifiers, credentials, or deployment secrets.
- Preserve all pre-existing worktree changes.
- Use Graphify for cross-module relationships and verify safety-critical conclusions against source and tests.
- Do not change strategy rules, risk thresholds, order routing, fill assumptions, asset-specific behavior, or live-mode behavior during autonomous remediation.
- The owner-approved 2026-07-16 XSP canary, broker-side manual close, DB/risk/audit reconciliation, and paper-mode XSP recreate completed with retained evidence.

## Commands executed

- Read Ponytail skill instructions.
- Read Graphify skill instructions.
- `rg -n "CODE_REVIEW_STATE|review-state|ButterflyGuy.*review|prelivecheckout|broker_order_intents|run_live.py" /home/billy/.codex/memories/MEMORY.md`
- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- Complete mandated-document reads with `sed`.
- Repository inventory with `rg --files` and line counts.
- Three targeted `/home/billy/.local/bin/graphify query ...` traversals for runtime lifecycle, live/backtest parity, and broker-intent/recovery relationships.
- Targeted `rg` audits for broker writes, async/concurrency, dates/timezones, exception handling, environment reads, calculations, and duplicated defaults.
- Numbered source/config/migration/workflow reads with `nl -ba` and `sed`.
- `UV_CACHE_DIR=/tmp/uv-cache uv sync`.
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q --cov=butterfly_guy --cov-report=term-missing`.
- `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`.
- `docker compose -f infra/docker-compose.yml --profile ndx --profile xsp config >/dev/null`.

## Test, lint, and coverage results

- Dependency sync: passed; 84 packages resolved, six unused environment packages removed.
- Tests with coverage: passed, `362 passed in 14.07s`; total coverage 52%.
- Safety-relevant coverage: `order_manager.py` 88%, `risk_engine.py` 79%, `run_live.py` 56%, `trade_service.py` 51%, `position_service.py` 37%, `schwab_client.py` 33%, `db/queries.py` 42%.
- Ruff: failed with 115 violations (17 automatically fixable); mostly existing formatting/naming/import debt, plus unused code/imports.
- Docker Compose render for SPX/NDX/XSP: passed.

## Changes implemented

- Created this review-state ledger.
- Created `CODE_REVIEW_REPORT.md`.
- BG-001: `entry_loop()` now stops after `TerminalOrderError` as well as `PartialFillError`, including errors surfaced by a completed monitor task.
- Added a focused regression proving a terminal rejection causes exactly one `attempt_entry()` call.
- BG-002: confirmed exit fills now end local monitoring before fallible accounting/reporting work, and `close_trade` is conditional on an `OPEN` row.
- BG-003: normal live entry/exit paths parse and persist broker price, time, quantity, and redacted execution evidence; incomplete or contradictory fills fail closed.
- BG-005: added one Eastern `session_date()` source and routed startup reconciliation, broker/intent ownership, daily and weekly risk, reset, and startup metrics through it instead of host/DB-local dates.
- Added a UTC-midnight regression and updated focused risk-query coverage; 113 focused tests and changed-file Ruff pass.
- BG-006: pushes now validate the checked-out SHA without deploying. Manual dispatch requires a flat DB plus read-only Schwab order/position reconciliation, then fast-forwards to the exact SHA, rebuilds paper SPX/NDX/XSP, and checks all three readiness endpoints.
- BG-007: AI PR review is read-only and can only fail the check; autonomous edits, pushes, comments, and auto-merge were removed.
- BG-014: pytest, Compose rendering, and changed-Python Ruff checks are blocking in both PR and deployment workflows.
- BG-012: Schwab initialization no longer logs any account-hash fragment; a focused regression locks the log shape.
- BG-013: verified that the installed schwab-py async client inherits HTTPX's bounded five-second default timeout, so no duplicate application timeout was added.
- BG-011: migrations now record filename/checksum under the existing advisory lock, skip previously applied files, and fail closed if historical SQL changes.
- BG-008: `/health` remains liveness while `/ready` fails during startup/shutdown and unsafe live reconciliation; deployment now checks readiness.
- BG-009: runtime config rejects unknown keys and unsafe selection, execution, freshness, and risk invariants.
- BG-010: README labels legacy independent research paths as non-parity, and parity reporting now uses configured RR target.
- BG-004: settlement now raises a dedicated fail-closed error when primary and fallback evidence both fail, leaving the DB trade OPEN and readiness degraded.
- Repeated generic entry failures now increment `butterfly_entry_loop_errors_total`, persist `entry_loop_error` audit rows, and degrade `/ready`; the live Prometheus rule alerts after three failures in five minutes.
- A dedicated Timescale CI smoke test runs every migration and executes the weekly/recent P&L reads against PostgreSQL.
- Updated Graphify artifacts after the code change.
- No configuration, service, database, credential, or broker state was changed.

## Unresolved risks

- Real partial-fill/cancel-pending broker evidence remains unobserved but is opportunistic, not a pre-live gate; synthetic handling is fail-closed.
- The supervised manual-flatten rehearsal passed end to end; retained evidence is in `reports/xsp_manual_flatten_2026-07-16.md`.
- External alert delivery/deduplication and exact-SHA deployment/rollback drills passed on 2026-07-15; retained evidence is in `reports/`.

## Exact next actions

1. Keep all assets paper-only unless the owner explicitly authorizes a supervised live canary.
2. No active remediation item remains. Any future live canary still requires fresh owner approval and the flat broker/DB gate.
