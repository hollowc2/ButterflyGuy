# ButterflyGuy AI Review State

## Current Objective

Keep all three strategies paper-only while closing the remaining operational observability, CI, deployment-gate, and documentation gaps.

## Historical Cycle Checkpoints

These checkpoints record prior canary states and are not current runtime instructions; use the objective and active work item below for current truth.

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
- **Evidence cycle 1 review complete:** The report recursively collects symbols but records only immediate child statuses, so deeper Schwab wrapper/child states are absent from the evidence. Planned fix: reuse the shared recursive order walker and report every descendant status. No broker, DB, service, or Docker commands were run.
- **Evidence cycle 1 implementation complete:** Added a synthetic grandchild-status regression, confirmed it failed, and reused the execution path's shared recursive order walker so all descendant statuses are included.
- **Evidence cycle 1 verification complete:** Focused report tests pass (`2 passed`), targeted Ruff passes, and `graphify update .` rebuilt the graph (3,475 nodes, 5,799 edges, 278 communities).
- **Evidence cycle 2 review complete:** Top-level `status_counts` and `status_category_counts` count only parent summaries, so child-only broker states are hidden from the report totals. Planned fix: build the payload in a small pure helper and aggregate parent plus recursive descendant statuses.
- **Evidence cycle 2 implementation complete:** Added a failing parent/child/grandchild count regression and routed payload construction through one pure helper that counts every recursively collected status and category.
- **Evidence cycle 2 verification complete:** Focused report tests pass (`3 passed`), targeted Ruff passes, and `graphify update .` rebuilt the graph (3,477 nodes, 5,805 edges, 270 communities).
- **Evidence cycle 3 review complete:** The SPX evidence script summarizes every account order returned for the day, so unrelated equity, NDX, or XSP statuses can be mistaken for SPX complex-order vocabulary. Planned fix: retain only orders containing exact SPX/SPXW option roots before summarizing or counting.
- **Evidence cycle 3 implementation complete:** Added a failing mixed SPX/equity/XSP regression and filtered payload construction to orders with exact `SPX` or `SPXW` symbol roots.
- **Evidence cycle 3 verification complete:** Focused report tests pass (`4 passed`), targeted Ruff passes, and `graphify update .` rebuilt the graph (3,478 nodes, 5,808 edges, 263 communities).
- **Evidence cycle 4 review complete:** The supposedly redacted evidence payload embeds `raw_orders`, preserving every field returned by the account endpoint and bypassing the explicit summary allowlist. Planned fix: omit raw broker payloads entirely and retain only the purpose-built status summary.
- **Evidence cycle 4 implementation complete:** Added a failing redaction assertion and removed the full raw broker payload from the generated report.
- **Evidence cycle 4 verification complete:** Focused report tests pass (`4 passed`), targeted Ruff passes, and `graphify update .` rebuilt the graph (3,478 nodes, 5,808 edges, 267 communities).
- **Evidence cycle 5 review complete:** The allowlisted summaries still expose real broker order IDs and full option contract symbols, neither of which is required to validate status vocabulary or nesting. Planned fix: omit broker order IDs and reduce contract symbols to unique SPX/SPXW roots.
- **Evidence cycle 5 implementation complete:** Added a failing identifier-redaction regression, removed broker order IDs and full contracts from summaries, and retained only unique `SPX`/`SPXW` roots.
- **Evidence cycle 5 verification complete:** Final focused report tests pass (`4 passed in 0.28s`), targeted Ruff and `git diff --check` pass, and `graphify update .` rebuilt the graph (3,478 nodes, 5,808 edges, 263 communities). The unrelated `run_backtest_db.py` worktree change remains untouched.
- **Evidence cycle 5 final review addendum:** Final diff inspection showed that a missing descendant status mixed with a named status creates `None` and string count keys, causing sorted JSON serialization to fail. Planned fix: use an explicit redacted missing-status label in raw status counts while preserving the existing `missing` category.
- **Evidence cycle 5 final implementation addendum:** Added a failing mixed missing/named-status serialization regression and normalized absent raw status-count keys to `<missing>`.
- **Evidence cycle 5 final verification addendum:** Focused report tests pass (`4 passed in 0.27s`), targeted Ruff and `git diff --check` pass, and the final `graphify update .` rebuilt the graph (3,478 nodes, 5,809 edges, 263 communities).
- **Live evidence cycle 1 review complete:** The prior `2026-06-26` artifact uses the obsolete raw-payload format and contains zero orders, so it cannot validate Schwab status vocabulary. Planned action: collect the last completed session (`2026-07-10`) through only account-number resolution and the read-only account-orders endpoint, isolate any OAuth refresh to a mode-600 temporary token copy, and review only the current redacted output. Add a mapping only if the report contains an unknown or missing status; make no broker writes or service changes.
- **Live evidence cycle 1 implementation checkpoint:** The redacted `2026-07-10` report was collected successfully but contains zero SPX orders and empty status counts. The live DB also has no SPX broker-order intents with broker IDs to identify a better bot-submitted date. No source, status mapping, broker, DB, service, or Docker change was made.
- **Live evidence cycle 1 verification complete:** Focused report tests pass (`4 passed in 0.33s`), targeted Ruff and `git diff --check` pass, and the generated report contains only the current redacted schema. `graphify update .` was not rerun because this cycle changed no code; the prior code changes are already reflected in the current graph (3,478 nodes, 5,809 edges, 263 communities).
- **Live evidence cycle 2 review complete:** The single `2026-07-10` report was empty, but the live DB identifies 20 recent dates with local SPX paper trades. Planned action: authenticate once with an isolated mode-600 token copy, query those dates newest-first through only the read-only account-orders endpoint, redact each response in memory, and stop at the first SPX/SPXW order.
- **Live evidence cycle 2 implementation checkpoint:** Schwab returned no SPX/SPXW orders across all 20 dates from `2026-06-11` through `2026-07-10`. No source, mapping, broker, DB, service, or Docker change was made; local paper fills do not provide broker lifecycle evidence.
- **Live evidence cycle 2 verification complete:** The bounded search returned the sanitized result `none` with `20` dates checked, emitted no raw payload or identifiers, and left no temporary token/error files. `graphify update .` was not run because no code changed.
- **XSP canary cycle 1 review complete:** XSP is paper-only and explicitly rejected by the SPX-only live guard, while the redacted status collector intentionally excludes XSP. Enabling the existing XSP service directly would bypass the stated experimental boundary without producing usable evidence. Planned fix: retain paper mode today, add a dedicated `LIVE_XSP_CANARY=true` confirmation plus XSP's existing one-contract and `$50` daily-loss constraints, generalize the redacted collector to an explicit underlying, and require a supervised Monday preflight before changing `paper_trading` or restarting the service.
- **XSP canary cycle 1 implementation complete:** Added XSP live eligibility behind `LIVE_XSP_CANARY=true`, preserved account/allocation confirmation, enforced XSP `max_position_size=1` and `max_daily_loss=50`, and kept NDX blocked. The redacted collector now accepts explicit SPX or XSP filtering and uses an XSP-specific filename. `configs/config_xsp.yaml` remains `paper_trading: true` but declares live approval, and the runbook requires a supervised Monday flip/restart, immediate abort conditions, evidence collection, and restoration to paper mode. No service was rebuilt or restarted and no broker write was made.
- **XSP canary cycle 1 verification complete:** Focused live-runner and report tests pass (`22 passed in 1.77s`), targeted Ruff, guarded XSP config assertions, Compose rendering, and `git diff --check` pass. The running XSP container remains unchanged and paper-only with recent `market_closed_waiting` logs. `graphify update .` rebuilt the graph (3,484 nodes, 5,831 edges, 277 communities). All four live confirmation keys remain absent from `.env`; Monday activation must supply them without exposing the account ID, flip only `paper_trading`, rebuild/restart only XSP, and remain supervised.
- **XSP canary activation review complete:** The owner explicitly authorized live readiness and requested the XSP paper-mode flip and rebuild. XSP has zero OPEN DB trades and zero active broker intents. Planned activation: preserve `.env` untouched, derive the exact-account confirmation from the existing `SCHWAB_ACCOUNT_ID` through XSP-only Compose environment wiring, set the three non-secret canary confirmations, change only XSP `paper_trading` to false, verify silently, and rebuild only `butterfly_xsp_app`. This can place one real XSP order during the configured Monday entry window.
- **XSP canary activation implementation complete:** Changed XSP to `paper_trading: false`; added XSP-only canary allocation/loss confirmations; and deferred the exact-account confirmation inside the container from its existing `SCHWAB_ACCOUNT_ID`, without copying or printing the value. Compose renders cleanly with the XSP profile, the focused tests remain green, and SPX/NDX configuration is unchanged. Rebuild/recreate and runtime reconciliation verification are next.
- **XSP canary activation verification complete:** Rebuilt and recreated only `butterfly_xsp_app`, then restored its canonical container name after Docker's recreate conflict. The new image is running with restart count `0`, emitted `live_trading_starting` for XSP, completed authentication/startup reconciliation far enough to run the collector, and is repeatedly logging `market_closed_waiting`. Live DB checks show zero OPEN XSP trades and zero active intents; no broker-state error or traceback was observed. XSP is now live-enabled and can submit one real order during Monday's configured entry window.
- **Historical XSP evidence review complete:** A redacted read-only Schwab history query for `2026-04-02` through `2026-07-10` found 236 broker-visible XSP orders: 10 `FILLED` and 226 `REJECTED`, concentrated on April 13-14, with no child statuses. Both names are already mapped, but the rejection volume exposed a live retry bug: `_wait_for_fill()` returns false for `REJECTED`, after which the ladder attempts to cancel the terminal order, catches the failure, and submits again. Planned safety action: restore XSP paper mode and rebuild before Monday, then add a focused regression and stop entry/exit ladders immediately on terminal rejection/expiry.
- **Historical XSP evidence implementation checkpoint:** No status mapping changed because all observed statuses are known. Restored `configs/config_xsp.yaml` to `paper_trading: true` and restarted only `butterfly_xsp_app` before market open, removing the rejection-storm risk from Monday while retaining the canary gates and XSP redacted collector.
- **Historical XSP evidence verification complete:** The XSP container is running with restart count `0`, loaded `paper_trading=True`, and resumed `market_closed_waiting`; no broker write occurred during the rollback. The redacted evidence summary is 236 orders: April 13 has 6 filled butterflies, 1 filled custom order, 1 filled single order, and 226 rejected butterflies; April 14 has 2 filled butterflies. No child status was observed.
- **Terminal retry fix review complete:** `_wait_for_fill()` persists the broker payload but returns the same false value for `REJECTED`/`EXPIRED`, `CANCELED`, and ordinary timeouts. All three live callers then enter cancel/reprice handling; cancel failures can overwrite the exact terminal intent status with `UNKNOWN_ABORTED`, and the entry/exit services can submit again. Planned fix: add focused failing entry, exit, service, and intent regressions, then raise one dedicated terminal-order exception only for `REJECTED`/`EXPIRED` so it bypasses cancel/reprice while preserving FILLED, timeout, CANCELED, partial-fill, and cancel-pending behavior. XSP remains paper-only.
- **Terminal retry fix implementation complete:** Added five failing regressions first, then added `TerminalOrderError` at the shared fill poller and propagated it through single-attempt entry, the OrderManager entry/exit ladders, and PositionService. `REJECTED`/`EXPIRED` now persist their exact payload/status and raise before cancel, while TradeService releases its entry lock and propagates the failure instead of advancing its retry loop. Six focused terminal regressions now pass; no risk, account, quantity, reconciliation, canary, or XSP paper-mode setting changed.
- **Terminal retry fix verification complete:** The focused OrderManager, TradeService, PositionService, and live-runner set passes (`82 passed in 2.17s`); targeted Ruff and `git diff --check` pass. `graphify update .` rebuilt the graph with 3,508 nodes, 5,878 edges, and 267 communities. XSP remains `paper_trading: true` pending the separate live DB, broker-intent, exact-account, canary, runtime-image, and startup-reconciliation reactivation gate.
- **Terminal retry reactivation review complete:** The live DB reports zero OPEN XSP trades and zero active XSP broker intents. Silent runtime checks confirm exact-account matching, `LIVE_ACCOUNT_ALLOCATION=20000`, `LIVE_MAX_ACCOUNT_DAILY_LOSS=50`, and `LIVE_XSP_CANARY=true`; XSP config remains live-approved with `max_position_size=1`, `max_trades_per_day=1`, and `max_daily_loss=50`. The existing paper container is running with restart count `0` and repeated `market_closed_waiting`; the market is closed, so rebuilding now cannot enter the supervised strategy window. Approved action: change only XSP `paper_trading` to false and rebuild/recreate only `butterfly_xsp_app`, then restore paper immediately on any unsafe startup evidence.
- **Terminal retry reactivation implementation complete:** Changed only `configs/config_xsp.yaml` from `paper_trading: true` to `false` for activation and rebuilt/recreated only `butterfly_xsp_app`. Final diff review added and confirmed one more failing regression for a contradictory FILLED parent with a REJECTED child; terminal failure classification now precedes FILLED classification, and the final XSP-only image was rebuilt again with that fail-closed ordering.
- **Terminal retry reactivation verification complete:** Final focused OrderManager, TradeService, PositionService, and live-runner tests pass (`83 passed in 1.85s`); targeted Ruff and `git diff --check` pass. Final `graphify update .` rebuilt 3,510 nodes, 5,883 edges, and 275 communities. The deployed XSP image is running live mode with restart count `0`, the terminal exception is importable in-container, exact-account/allocation/loss/canary checks pass, Schwab `accountNumbers` authentication returned `200`, startup reconciliation completed before the task group reached `market_closed_waiting`, and post-start DB checks remain zero OPEN XSP trades and zero active XSP intents. No test order or Schwab write call was made because the configured market window was closed; no unsafe status, mismatch, traceback, or restart loop was observed.

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
- **Operations:** Docker runs separate SPX, NDX, and XSP app services with TimescaleDB and Prometheus/Grafana integration. `/health` is liveness; `/ready` reports orchestrator safety state. All three current configs are paper-only.

## Important Files Reviewed

- `AGENTS.md`
- `README.md`
- `CLAUDE.md`
- `todo.md`
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
2. **High — ops — complete:** `/health` remains liveness and `/ready` now fails on startup/shutdown, unsafe broker state, settlement evidence failure, and repeated entry-loop failures. Entry-loop failures also increment a metric and persist audit events.
3. **Medium — backtest/tests — later:** Backtests share selection/profit-policy pieces but cannot prove broker execution parity; modeled fills can remain optimistic relative to complex-order queueing, partial fills, and cancel races. Files: `backtest/simulation_engine.py`, execution/parity reports. Fix: keep this explicit in reports and calibrate models only from observed paper/shadow order lifecycle data.
4. **Medium — ops/tests — later:** The remaining supervised restart, manual flatten, alert-delivery, and rollback procedures are tracked in `todo.md`. Fix: execute the controlled drills and retain redacted evidence.

Completed execution/risk items: exact broker/DB leg-symbol equality, signed Schwab quantity normalization, DB-derived `+quantity/-2 * quantity/+quantity` comparison, and explicit zero-quantity rejection at startup, runtime, and filled-entry repair.

## Active Work Item

Complete locally: repeated generic entry failures degrade readiness and produce metric/audit evidence; real Timescale CI executes migrations and critical risk reads; manual deploys reconcile Schwab and DB state before rebuilding and checking SPX/NDX/XSP; all current configs remain paper-only.

## Remaining Risks

- Real Schwab complex-order parent/child partial-fill evidence remains unproven; synthetic handling is fail-closed.
- External alert delivery/deduplication and the supervised manual-flatten and exact-SHA rollback drills remain outstanding in `todo.md`.
- Historical fill modeling cannot reproduce all live broker lifecycle states.

## Next Session Launch Prompt

Read `todo.md` and `docs/live-runbook.md`. Treat SPX, NDX, and XSP as paper-only unless the owner explicitly authorizes a supervised live canary. Before any deployment or broker-write drill, require zero open DB trades, zero nonterminal intents, no working/unknown Schwab orders, and exact broker-position/DB reconciliation.
