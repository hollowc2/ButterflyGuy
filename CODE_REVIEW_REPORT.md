# ButterflyGuy Senior Code Quality, Architecture, and Safety Review

Reviewed branch: `main`
Reviewed commit: `d112dcba0a71b5090cf574d08aa7a19ff6eee7c0`
Review date: 2026-07-12 UTC

## 1. Executive summary

ButterflyGuy has a clear package layout, typed configuration, strong pure-logic tests, conservative live-startup gates, durable broker order intents, recursive broker-state reconciliation, an advisory entry lock, and database uniqueness for one open trade per underlying/day. The entry-selection path has also made real progress toward live/backtest reuse through `strategy.entry_selection.select_entry_candidate()`.

The repository is understandable, but it is not ready for unattended live trading. Seven P1 findings remain in execution, position closure, fill authority, settlement, market-date handling, and CI/deployment. The largest immediate risks are that terminal broker failures can be retried by the outer runtime loop, an exit can be submitted again after a successful fill if post-fill persistence fails, and normal live trades record the submitted limit rather than broker execution details. Current XSP configuration is live-enabled, so live trading should be returned to disabled/paper mode until the immediate safety corrections and failure-injection tests are complete.

Strongest areas:

- Pure strategy, valuation, time, and state-machine logic has focused deterministic tests.
- Live order submission is deliberately not wrapped in the generic retry helper.
- Broker intent persistence occurs before live submit, with order ID/status persistence and recursive child-order handling.
- Startup/runtime reconciliation fails closed on unknown, missing, partial, cancel-pending, and mismatched broker state.
- PostgreSQL advisory locking plus a partial unique index reduces concurrent duplicate entry risk.

Five highest-value improvements:

1. Stop the top-level entry loop on `TerminalOrderError` and `PartialFillError`, with a regression at the actual runtime boundary.
2. Make exit completion idempotent: once a fill is confirmed, prevent any further exit submission even if DB/risk/reporting work fails.
3. Persist broker-reported fill price, execution time, quantity, and fill evidence instead of submitted limits/local timestamps.
4. Fail closed when cash-settlement valuation is unavailable; never close a trade with an invented zero value.
5. Make CI validate the exact revision/image it deploys, remove autonomous untested LLM writes/auto-merge, and avoid rebuilding live-enabled services on unrelated pushes.

## Remediation tracker

This checklist is the cross-session handoff. Work the first unchecked P1 unless its dependency or owner decision blocks it. XSP live mode is an owner-approved, Monday-only canary for gathering real market-hours order data; do not disable it as part of these fixes. Return it to `paper_trading: true` after that test.

- [x] BG-001 — Stop the entry loop after terminal broker failures. Completed 2026-07-12; focused runtime-boundary regression passes.
- [ ] BG-002 — Make confirmed exit completion idempotent. Blocked by BG-003.
- [ ] BG-003 — Persist authoritative broker fill evidence. Requires redacted market-hours XSP fixtures.
- [x] BG-004 — Fail closed when settlement evidence is unavailable. Completed 2026-07-12; failed valuation preserves the OPEN trade, degrades readiness, and stops entry orchestration.
- [x] BG-005 — Use one explicit Eastern session date across safety paths. Completed 2026-07-12; focused date/reconciliation/risk regressions pass.
- [x] BG-006 — Validate and deploy the same revision; scope live-service rebuilds. Completed 2026-07-13; pushes validate only, while manual deployment requires a flat DB and preserves exact-SHA/readiness checks.
- [x] BG-007 — Make AI review read-only and require deterministic/human gates. Completed 2026-07-12; workflow is read-only, cannot patch/merge, and fails on deterministic or AI findings.
- [x] BG-008 — Separate liveness from readiness. Completed 2026-07-12; `/ready` tracks startup, shutdown, and live broker-gate safety and deployment consumes it.
- [x] BG-009 — Reject unknown and unsafe trading configuration. Completed 2026-07-12; nested extras fail closed and core selection/execution/risk invariants are validated.
- [x] BG-010 — Remove or clearly label conflicting legacy research rules. Completed 2026-07-12; README labels independent legacy paths and parity output uses configured RR target.
- [x] BG-011 — Add an applied-migration ledger. Completed 2026-07-12; locked checksum ledger runs immutable migrations once and fails closed on drift.
- [x] BG-012 — Remove the account-hash prefix from logs. Completed 2026-07-12; initialization logs no account identifier and focused regression passes.
- [x] BG-013 — Verify dependency timeouts, then own explicit broker deadlines if needed. Completed 2026-07-12; installed schwab-py uses Authlib AsyncOAuth2Client with HTTPX's bounded 5-second default.
- [x] BG-014 — Establish blocking deterministic quality gates incrementally. Completed 2026-07-12; tests, Compose rendering, and changed-file Ruff are blocking in PR and deployment workflows.

## 2. Architecture map

### Runtime components and dependency direction

```text
YAML + selected environment values
        |
        v
core.config.AppConfig
        |
        v
scripts.run_live.main
  |-- DatabasePool -> migrations -> query objects
  |-- SchwabClientWrapper -> account-scoped read/write adapter
  |-- OptionChainCollector -> chain/spot/daily-bar persistence
  |-- TradeService -> entry orchestration
  |     |-- RiskEngine
  |     |-- shared entry_selection
  |     |-- OrderManager -> ButterflyOrderBuilder -> Schwab
  |     `-- trade/candidate/decision queries
  |-- PositionService -> PositionManager -> ProfitStateMachine
  |     |-- OrderManager for exits
  |     `-- trade/risk/monitoring/tent/decision queries
  `-- BrokerStateGate + periodic reconciliation
```

Dependencies generally point inward from scripts/services to pure strategy/position functions and outward through Schwab/DB adapters. The main exceptions are business rules and recovery logic embedded in `run_live.py`, plus legacy research scripts that maintain independent asset defaults and selection behavior.

### Trading lifecycle and authoritative owners

| Lifecycle step | Actual path | Current authoritative owner | Ownership concern |
|---|---|---|---|
| Configuration | `load_config()` -> `AppConfig` | `core/config.py` plus asset YAML | Live confirmation values are separately hard-coded in `run_live.py` and Compose. |
| Runtime startup | `run_live.main()` | `scripts/run_live.py` | Entrypoint owns substantial reconciliation and recovery business logic. |
| Market data | `OptionChainCollector`, direct service reads | `data/collector.py`, `data/schwab_client.py` | Collector freshness gates entry, but entry/monitoring fetch separate live chains. |
| Quote/chain validation | builder, trade service, position manager | Split across `strategy`, `services`, `position`, `execution` | No single quote-validity model with timestamps across all legs. |
| Entry eligibility | time window -> risk -> freshness | `TradeService` and `RiskEngine` | Market/date logic is split between time utilities, host dates, SQL `CURRENT_DATE`, and broker date helpers. |
| Construction/selection | `select_entry_candidate()` | `strategy/entry_selection.py` | Primary live/DB replay is shared; legacy simulation/research paths diverge. |
| Risk approval | `RiskEngine.can_trade()` twice for live | `risk/risk_engine.py` | Enforcement is correctly repeated inside the advisory lock; settlement/exit accounting can still leave state stale. |
| Order intent | `OrderIntentQueries.create_intent()` | `execution/order_manager.py` + DB | Good durable boundary, but normal fill data is reduced to a boolean. |
| Broker/paper execution | `OrderManager` | `execution/order_manager.py` | Paper and live fill semantics differ intentionally; live execution evidence is not preserved accurately. |
| Reconciliation | startup + 15-second loop | `scripts/run_live.py` | Large, safety-critical business rule embedded in entrypoint. |
| Position creation | fill -> `insert_trade()` | `TradeService` | Fill-to-trade-to-risk updates are not one transaction, but restart intent repair mitigates entry crashes. |
| Position monitoring | chain -> `PositionManager` -> state machine | `PositionService` | Broad exception loop can remain alive while degraded. |
| Exit decision | `ProfitStateMachine.evaluate()` | `position/state_machine.py` | Cohesive and well tested. |
| Exit execution | `OrderManager.execute_exit()` | `execution/order_manager.py` | Post-fill completion ordering is not idempotent. |
| Settlement | final bar -> intrinsic value | `PositionService` | Double failure silently becomes a zero-value close. |
| Reporting | metrics, decision log, notifier, reports | Split by adapter | DB remains historical authority, but incorrect normal fill data contaminates all downstream views. |

### Backtest lifecycle

The primary DB replay loads the asset YAML through `load_asset_config()`, uses shared `select_entry_candidate()`, and then simulates monitoring/exits. `SimulationEngine.simulate_day()` remains a separate full selection/monitoring implementation used by older research paths, and `run_entry_analysis.py` has its own asset settings and hard-coded windows. Thus parity is improving but not complete.

### Restart, authentication, metrics, and asset behavior

- Restart: open DB trades are rebuilt into `TradeRecord`/`ButterflyCandidate`; persisted peak is restored; live broker positions and recursive order states are compared every 15 seconds; explicit filled intents can repair missing entry/exit DB transitions.
- Authentication: token-file authentication resolves only the configured account. No default account is selected. The resolved account-hash prefix is logged.
- Metrics: Prometheus is process-global. `/health` reports only process uptime; it is not readiness.
- Notifications: Discord is SPX-only for trades; Telegram carries risk/operational notices; `decision_log` carries audit events.
- Assets: SPX and NDX YAML are paper; XSP is currently live-enabled behind explicit account, allocation, loss, and one-contract canary guards. Widths, tolerances, quote quality, drawdowns, and risk differ intentionally.

## 3. Findings summary

### By severity

| Severity | Count |
|---|---:|
| P0 | 0 |
| P1 | 7 |
| P2 | 7 |
| P3 | 0 |

### By category

| Category | Count |
|---|---:|
| Execution/order lifecycle | 3 |
| Position/settlement | 1 |
| Time/recovery | 1 |
| CI/deployment/tooling | 3 |
| Observability | 1 |
| Configuration | 1 |
| Backtest/live parity | 1 |
| Database/migrations | 1 |
| Security/operations | 1 |
| Async/reliability | 1 |

### By confidence

| Confidence | Count |
|---|---:|
| Confirmed | 13 |
| High confidence | 0 |
| Medium confidence | 1 |
| Needs reproduction | 0 |

### By subsystem

| Subsystem | Count |
|---|---:|
| `run_live.py` | 2 |
| Position/settlement service | 2 |
| Order manager/Schwab adapter | 2 |
| CI/deployment | 3 |
| Config/time/health | 2 |
| Backtest/research | 1 |
| Database migrations | 1 |
| Authentication logging | 1 |

## 4. Detailed findings

### BG-001

ID: BG-001
Title: Terminal broker failures are retried by the outer entry loop
Severity: P1 — High
Confidence: Confirmed
Category: Execution/order lifecycle
Files/symbols: `execution/order_manager.py:TerminalOrderError`, `scripts/run_live.py:entry_loop()`
Evidence: `_wait_for_fill()` raises `TerminalOrderError` for `REJECTED`/`EXPIRED` at `order_manager.py:739-758`, and both order ladders re-raise it. `entry_loop()` catches every exception at `run_live.py:529-533`, but stops only for `PartialFillError`; after 15 seconds it loops and can call `attempt_entry()` again. Coverage reports `run_live.py:484-535` entirely unexecuted.
Current behavior: One ladder stops, but the process-level entry workflow does not.
Failure scenario: A broker rejects an XSP entry. The service submits a fresh order every outer-loop iteration during the entry window, recreating the rejection storm the inner-ladder fix intended to prevent.
Impact: Repeated broker writes, rate-limit pressure, noisy intents, and possible eventual execution after an operator believes a terminal failure stopped trading.
Root cause: Terminal-failure semantics are not propagated through the top-level orchestration boundary.
Recommended fix: Import/handle `TerminalOrderError` beside `PartialFillError` and stop the entry task fail-closed; require operator/reconciliation recovery.
Required tests: `entry_loop()` test proving one terminal error causes exactly one `attempt_entry()` call and task termination; sibling test for partial fill.
Estimated scope: Small, two files including test.
Dependencies: None.
Behavior-changing: yes

### BG-002

ID: BG-002
Title: A post-fill persistence failure can trigger a second exit order
Severity: P1 — High
Confidence: Confirmed
Category: Execution/order lifecycle
Files/symbols: `services/position_service.py:PositionService.monitor_loop()`
Evidence: After `execute_exit()` returns a fill, the code closes the DB trade at lines 300-313, calls `_record_exit_metrics()` at line 315, and only then sets `exited = True` at line 319. Any exception from risk-state persistence at `risk_engine.record_pnl()` is swallowed by the broad handler at lines 374-375; because `exited` is still false, monitoring continues.
Current behavior: Successful broker execution is not the local idempotency boundary.
Failure scenario: Exit fills and the trade row closes; the risk DB update fails transiently. The monitor catches the error, polls again, sees another exit signal, and submits another SELL_TO_CLOSE.
Impact: Duplicate exit submissions, terminal rejections, unknown broker state, or position-management failure during a DB outage.
Root cause: Irreversible broker completion is ordered before local completion, but local completion is marked after fallible secondary work.
Recommended fix: Make confirmed fill/DB close transition idempotent and mark the monitor completed before secondary risk/metrics/notification work. Make `close_trade` conditional on `status='OPEN'` and check the affected row count.
Required tests: Inject failure from `_record_exit_metrics()` after a fill and assert one exit call only; repeated `close_trade` must not overwrite a closed trade.
Estimated scope: Small-to-medium, service/query plus focused tests.
Dependencies: BG-003 for authoritative fill data.
Behavior-changing: yes

### BG-003

ID: BG-003
Title: Normal live fills persist submitted limit price and local time, not broker execution
Severity: P1 — High
Confidence: Confirmed
Category: Execution/order lifecycle
Files/symbols: `execution/order_manager.py:_wait_for_fill()`, `execute_single_attempt()`, `execute_exit()`; `services/trade_service.py`; `services/position_service.py`
Evidence: `_wait_for_fill()` returns only `bool`. On `FILLED`, entry returns `fill_price=limit_price` and `fill_time=now_utc()` at `order_manager.py:301-310`; exit does the same at lines 634-643. Those values become `butterfly_trades.entry_price`, exit price, PnL, daily risk, metrics, and reports (`trade_service.py:529-538`, `position_service.py:295-315`). Restart repair separately requires explicit broker price/time, proving the richer source exists.
Current behavior: Limit-price assumptions are recorded as executions during the normal path.
Failure scenario: Price improvement, multiple fills, or broker execution latency makes actual debit/credit differ from the limit. Stored PnL and loss limits become wrong.
Impact: Materially incorrect financial records, risk state, parity analysis, and audit evidence.
Root cause: Order polling collapses a broker order payload into a boolean.
Recommended fix: Return a typed fill result derived from broker execution details, including quantity and timestamp; fail closed if a FILLED payload cannot produce unambiguous evidence.
Required tests: Price improvement, multiple execution legs, child order fill, missing fill price/time, quantity mismatch, and restart equivalence.
Estimated scope: Medium, execution boundary and consumers.
Dependencies: Real redacted Schwab fill fixtures.
Behavior-changing: yes

### BG-004

ID: BG-004
Title: Settlement data failure closes the trade at an invented zero value
Severity: P1 — High
Confidence: Confirmed
Category: Position/settlement
Files/symbols: `services/position_service.py:PositionService.monitor_loop()` settlement branch
Evidence: `settlement_value` starts at `0.0` at line 386. Primary valuation failure enters a fallback; fallback failure is only logged at lines 415-416. Execution then unconditionally calculates PnL and closes the trade at lines 418-435.
Current behavior: Missing settlement evidence is converted into a full-loss close.
Failure scenario: Schwab bars and option-chain/spot fallback fail during an outage. A profitable cash-settled butterfly is permanently recorded as zero settlement and risk state is debited incorrectly.
Impact: Corrupted historical truth, incorrect loss halts, misleading reports, and no automatic path to correct the close.
Root cause: A sentinel numeric value is used instead of an explicit unavailable state.
Recommended fix: Keep the trade open in a dedicated settlement-pending/unknown state or fail the monitor loudly; close only with validated settlement evidence.
Required tests: Primary failure/fallback success; both fail; invalid/missing spot; later idempotent settlement repair.
Estimated scope: Medium because a durable state/recovery policy is required.
Dependencies: Owner decision on settlement-pending operations.
Behavior-changing: yes

### BG-005

Status: Complete — 2026-07-12. `time_utils.session_date()` now owns the Eastern calendar date; startup reconciliation, broker order lookup, intent ownership, daily risk state, weekly loss queries, reset metrics, and startup candidate metrics use that explicit date instead of host/DB-local dates. Focused suite: 113 passed; changed-file Ruff passed; Graphify refreshed.

ID: BG-005
Title: Host-local dates conflict with canonical Eastern trading dates
Severity: P1 — High
Confidence: Confirmed
Category: Time/recovery
Files/symbols: `run_live.py:_assert_broker_state_matches_db()`, `daily_reset_loop()`, `main()`; `order_manager.py:_entry_blocked_by_working_orders()`; `risk_engine.py`; `schwab_client.py:get_todays_orders()`
Evidence: Canonical helpers use `America/New_York`, but safety paths repeatedly call `dt.date.today()` (`run_live.py:266,575,781`; `order_manager.py:195`; `risk_engine.py:55,129,135,149,166`; `schwab_client.py:303`). The supplied runtime timezone is UTC. After 20:00 ET, UTC is the next calendar date while the Eastern session date has not changed. SQL also uses database `CURRENT_DATE`.
Current behavior: Intent selection, broker-order lookup, risk sync, and daily reset can disagree on the active trade date.
Failure scenario: A restart after 20:00 ET misses the session's intents/orders, misclassifies ownership, or syncs counters into the next date.
Impact: Broken restart reconciliation and audit/risk-state drift.
Root cause: No single market-session date function is passed through safety-critical APIs.
Recommended fix: Use one explicit Eastern `session_date` at orchestration boundaries; pass it to broker, intent, risk, and DB queries. Avoid database/session timezone dependence for business dates.
Required tests: 19:59/20:00 ET across UTC midnight, DST transitions, startup after close, holiday and early-close dates.
Estimated scope: Medium, cross-cutting but mechanical.
Dependencies: None.
Behavior-changing: yes

### BG-006

ID: BG-006
Title: Deployment validates a different revision than it deploys and always rebuilds live XSP
Severity: P1 — High
Confidence: Confirmed
Category: CI/deployment/tooling
Files/symbols: `.github/workflows/deploy.yml`, `configs/config_xsp.yaml`, `infra/docker-compose.yml`
Evidence: Actions checkout occurs in the runner workspace, but validation runs in hard-coded `/opt/butterflyguy` at workflow lines 19-26. Only afterward does deployment `git pull` at line 31, so tests/Compose may cover the old checkout. Line 32 rebuilds all three apps on every main push. XSP has `paper_trading: false` and Compose supplies all canary confirmations. Only SPX `/health` is checked.
Current behavior: A pushed commit can be deployed without that exact commit passing tests; unrelated changes restart a live-enabled canary.
Failure scenario: An untested XSP execution change reaches main, the old tree passes validation, then all services rebuild and XSP resumes live trading.
Impact: Unsafe deployment of trading behavior and avoidable live-process disruption.
Root cause: Validation and deployment are split across different working copies and services are not scoped by changed artifact.
Recommended fix: Validate the checked-out SHA, build immutable images from it, deploy that SHA, verify each enabled service's readiness, and require explicit approval/scoping for live-enabled service restart.
Required tests: Workflow test proving SHA parity; deployment dry run; per-service health/readiness; rollback drill.
Estimated scope: Medium, CI/operations only.
Dependencies: Runner/deployment ownership.
Behavior-changing: yes

### BG-007

ID: BG-007
Title: PR automation can write and auto-merge untested trading-code changes
Severity: P1 — High
Confidence: Confirmed
Category: CI/deployment/tooling
Files/symbols: `.github/workflows/code-review.yml`
Evidence: The workflow grants content write permission, invokes Codex to edit the checkout at lines 111-119, stages everything with `git add -A` at line 126, and pushes without running pytest or Ruff. On the next run, a clean LLM/syntax review auto-merges at lines 134-140. The review prompt checks four narrow patterns, not execution/risk invariants.
Current behavior: Generated fixes are trusted based on syntax and a second model opinion.
Failure scenario: An LLM changes order/risk behavior, syntax passes, the second review emits `NO ISSUES`, and the PR auto-merges into the deployment workflow.
Impact: Unreviewed behavior change in a trading system.
Root cause: Review, remediation, validation, and approval are collapsed into one privileged autonomous job.
Recommended fix: Make AI review read-only; require deterministic test/lint/Compose gates and human approval for generated patches, trading-critical paths, and auto-merge. Stage only intended files.
Required tests: Branch-protection/ruleset verification and a fixture PR proving failed tests block merge.
Estimated scope: Small-to-medium workflow change.
Dependencies: Repository governance.
Behavior-changing: yes

### BG-008

ID: BG-008
Title: `/health` reports green while trading dependencies or reconciliation are unsafe
Severity: P2 — Medium
Confidence: Confirmed
Category: Observability
Files/symbols: `core/metrics.py:_MetricsHandler`
Evidence: `/health` always returns HTTP 200 with uptime at `metrics.py:113-121`. It has no DB, Schwab, market-data freshness, task, risk-halt, broker-gate, or monitor state. Deployment uses only this endpoint.
Current behavior: Liveness is presented and consumed as application health.
Failure scenario: Entry loop has stopped or broker reconciliation is unsafe, yet deployment and monitoring remain green.
Impact: Slow detection and false operator confidence.
Root cause: No separation between liveness and readiness.
Recommended fix: Keep `/health` as liveness and add `/ready` with bounded, cached dependency/task/gate state; deployment should require readiness appropriate to market-open/closed mode.
Required tests: DB down, broker unavailable, stale collector, unsafe broker gate, stopped entry/monitor task, market closed.
Estimated scope: Medium.
Dependencies: A small shared readiness-state object.
Behavior-changing: no

### BG-009

ID: BG-009
Title: Trading configuration silently accepts typos and unsafe ranges
Severity: P2 — Medium
Confidence: Confirmed
Category: Configuration
Files/symbols: `core/config.py` settings models and `load_config()`
Evidence: Models mostly declare plain `int`/`float` fields without positivity, ordering, or cross-field validation; unknown keys are ignored. Examples include ladder counts/steps, time windows, risk limits, wing widths, quote ratios, and VIX bucket ordering. Tests validate precedence/defaults but not malformed high-risk values.
Current behavior: A misspelled key falls back to a default and contradictory values can reach runtime.
Failure scenario: A typo in a risk or quote-quality setting silently activates a broader default; invalid time/bucket ordering changes entry behavior without startup failure.
Impact: Configuration drift and hard-to-audit behavior. Live SPX/XSP guards mitigate only a few exact fields.
Root cause: Typed parsing exists, but semantic validation is incomplete and extras fail open.
Recommended fix: Forbid unknown keys in runtime models and add minimal bounds/cross-field validators for money, quantities, lists, time windows, and ordered VIX buckets.
Required tests: Unknown keys, empty/duplicate widths, missing max cost, negative/zero ladder/risk values, invalid ratios, reversed windows/buckets.
Estimated scope: Medium, config plus tests.
Dependencies: Migration plan for currently tolerated keys.
Behavior-changing: yes

### BG-010

ID: BG-010
Title: Legacy research paths retain conflicting asset and selection rules
Severity: P2 — Medium
Confidence: Confirmed
Category: Backtest/live parity
Files/symbols: `scripts/run_entry_analysis.py`, `backtest/simulation_engine.py:simulate_day()`, `scripts/run_backtest_db.py:ASSET_DEFAULTS`, `strategy/entry_selection_parity.py`
Evidence: Runtime XSP widths are `[3,4,5]`, range `10`, tolerance `1.5`; `run_entry_analysis.py:34-38` defines XSP `[10,20,30]`, range `100`, tolerance `50`. `SimulationEngine.simulate_day()` independently rebuilds selection with `spot_range=100` at lines 240-268. Parity reporting hard-codes `RR_TARGET=10.0` rather than using config.
Current behavior: Primary DB replay shares entry selection, but older research commands can answer a different question under the same asset label.
Failure scenario: A report is treated as live-parity evidence while using stale XSP construction and ranking rules.
Impact: Misleading research conclusions and regression blindness, not direct order risk.
Root cause: Incremental parity work left legacy owners and duplicated defaults in place.
Recommended fix: Label legacy research explicitly or route it through asset YAML plus shared entry selection. Delete duplicated defaults only after call-site verification. Pass configured RR target into parity reporting.
Required tests: Asset-by-asset golden selection using the same snapshot across live/shared replay/research adapters.
Estimated scope: Medium.
Dependencies: Preserve intentional research overrides as explicit CLI arguments.
Behavior-changing: yes

### BG-011

ID: BG-011
Title: Every app startup reruns every migration without an applied-version ledger
Severity: P2 — Medium
Confidence: Confirmed
Category: Database/migrations
Files/symbols: `db/migrations/run_migrations.py`, migrations `001`-`009`
Evidence: `run_migrations()` sorts and executes every SQL file on every startup. There is no schema-version table or checksum. Migration 003 drops and recreates the `daily_risk_state` primary key every run. Three app containers serialize through one advisory lock.
Current behavior: Mostly idempotent DDL is repeatedly applied to the live schema.
Failure scenario: Routine app restart waits on or takes table locks; a modified historical migration silently changes startup behavior; partial operational drift has no authoritative version record.
Impact: Avoidable startup coupling, lock risk, and weak migration auditability.
Root cause: File replay substitutes for migration state management.
Recommended fix: Add a tiny `schema_migrations(version, checksum, applied_at)` ledger and execute each immutable migration once under the existing lock.
Required tests: First apply, no-op second apply, checksum mismatch, concurrent runners, failed migration rollback.
Estimated scope: Small-to-medium.
Dependencies: Confirm current live schema baseline before adopting.
Behavior-changing: no

### BG-012

ID: BG-012
Title: Authentication logs disclose an account-hash prefix
Severity: P2 — Medium
Confidence: Confirmed
Category: Security/operations
Files/symbols: `data/schwab_client.py:SchwabClientWrapper.initialize()`
Evidence: Successful initialization logs `self._account_hash[:8]` at lines 67-70.
Current behavior: A stable account-scoped identifier fragment enters logs.
Failure scenario: Logs are forwarded or shared for diagnostics, unnecessarily broadening account metadata exposure.
Impact: Credential/account metadata exposure; not sufficient alone to authenticate.
Root cause: Debug identification remains in normal structured logging.
Recommended fix: Log only that the configured account was resolved; use an ephemeral correlation ID if differentiation is needed.
Required tests: Logging capture asserting no account number/hash fragments.
Estimated scope: Tiny.
Dependencies: None.
Behavior-changing: no

### BG-013

ID: BG-013
Title: Safety-critical broker awaits have no explicit application deadline
Severity: P2 — Medium
Confidence: Medium confidence
Category: Async/reliability
Files/symbols: `data/schwab_client.py:_retry()` and public methods; `PositionService.monitor_loop()`
Evidence: `_retry()` awaits each schwab-py call directly and backs off only after it returns/raises. No `asyncio.timeout()`/`wait_for()` is applied. A hung chain/status/cancel/account request can hold the position or reconciliation coroutine indefinitely. The effective underlying httpx timeout was not verified in this audit.
Current behavior: Reliability depends on the dependency's implicit client timeout.
Failure scenario: A network half-open stalls position monitoring or broker reconciliation during an open trade.
Impact: Delayed exit/reconciliation and degraded shutdown.
Root cause: Timeout policy is not owned at the adapter boundary.
Recommended fix: Verify schwab-py timeout behavior first; if not bounded to an acceptable value, add explicit per-operation deadlines, with stricter handling for non-idempotent/cancel operations.
Required tests: Never-returning read, status, cancel, and shutdown cancellation; ensure place-order ambiguity is not retried.
Estimated scope: Small after dependency verification.
Dependencies: schwab-py/httpx behavior.
Behavior-changing: yes

### BG-014

ID: BG-014
Title: Deterministic quality gates are incomplete and Ruff is non-blocking
Severity: P2 — Medium
Confidence: Confirmed
Category: CI/deployment/tooling
Files/symbols: `pyproject.toml`, `.github/workflows/deploy.yml`
Evidence: Full Ruff fails with 115 violations, while deployment converts failure to a warning. CI has no type checker, secret scan, dependency audit, migration validation, coverage threshold, or isolated no-broker test environment. Coverage is 52%; `position_service.py` is 37%, `schwab_client.py` 33%, `db/queries.py` 42%, and the outer entry loop is uncovered.
Current behavior: Tests pass, but critical boundaries can regress without a deterministic gate.
Failure scenario: A safety-critical change passes existing tests and deploys despite lint/type/dataflow defects in uncovered code.
Impact: Reduced defect prevention and review signal.
Root cause: Tooling debt is tolerated globally instead of baselined and tightened around high-risk paths.
Recommended fix: First make current Ruff baseline clean or gate only changed files; then make it blocking. Add coverage targets for execution/recovery boundaries. Add dependency/secret scanning and migration tests. Evaluate Pyright for boundary types only after the safety tests above; do not add broad tooling before it blocks a named defect class.
Required tests: CI fixture demonstrating each gate blocks a failing PR; broker-write methods must be patched to fail if invoked in tests.
Estimated scope: Medium, staged.
Dependencies: Cleanup/baseline decision.
Behavior-changing: no

## 5. Single-source-of-truth matrix

| Concept | Current definitions | Current runtime winner | Conflict | Proposed owner | Migration approach |
|---|---|---|---|---|---|
| Runtime configuration | YAML, Pydantic defaults, selected env, Compose env, `run_live` constants | YAML plus manual merge; live constants override policy | Precedence is bespoke; live policy split | `AppConfig` for behavior; one explicit deployment policy object for live confirmation | Document precedence, forbid extras, validate, then remove duplicate defaults. |
| Domain models | Dataclasses for quotes/candidates/trades; dicts for DB/broker/intents/fills | Dicts at external/persistence boundaries | Fill/order/position states lose type and evidence | Typed external response models at Schwab/DB boundary; existing immutable internal dataclasses | Start with `FillResult`/order status because highest risk. |
| Butterfly mark/bid/ask | `fly_mark_value`, `fly_bid_value`, builder/order-manager formulas | Each path's local formula | Equivalent formulas repeated; validation differs | `data.schemas` or small pricing module | Reuse existing helpers; add ask helper and invariant tests, no generic pricing framework. |
| Profit/max loss/breakevens | Builder, notifier, backtest reconstruction, charts | Builder for candidate; local re-derivations later | Rounding and source price can differ | Candidate/fill-derived pure functions | Replace report-only reimplementations after golden tests. |
| PnL dollars | `trade_pnl_dollars`, SQL `pnl*100*quantity`, notifier arithmetic, backtest output | DB points plus consumers multiply | Multiplier hard-coded at 100 | One asset/contract metadata function plus DB points convention | Introduce only when non-100 multiplier or cross-asset need is proven; meanwhile reuse `trade_pnl_dollars`. |
| Time/session date | `time_utils`, `date.today`, SQL `CURRENT_DATE`, broker helper dates | Depends on call site/host | UTC/Eastern split after 20:00 ET | `time_utils.session_date()` passed explicitly | Convert safety paths first; retain UTC persistence. |
| Asset metadata | Three YAMLs, Schwab symbol maps, script dictionaries, live policy constants | YAML for primary runtime | Research scripts conflict, especially XSP | YAML for tunable behavior; one small immutable map for broker symbol/contract facts | Remove script defaults as each command adopts `load_asset_config()`. |
| Risk rules | `RiskSettings`, YAML, live constants, DB risk state, SQL history | `RiskEngine` plus live startup assertions | Live policy and behavior split; date semantics differ | `RiskEngine` for enforcement, validated config for thresholds | Pass explicit session date and keep final pre-submit recheck/DB lock. |
| Order states | Sets in `order_manager.py`, DB terminal set, report categorizer | Runtime sets in order manager | Multiple mappings can drift | One order-status vocabulary in execution module | Make DB/report import the shared categorizer; validate observed unknowns fail closed. |
| Position states | `ProfitState`, DB `OPEN/CLOSED`, pending-exit metadata, broker positions | Different state machines per layer | No durable settlement-pending/exit-filled-but-unaccounted state | DB trade lifecycle plus explicit transition functions | Add only states needed for BG-002/BG-004 recovery. |
| Entry selection | Shared `entry_selection`, legacy `SimulationEngine`, research scripts | Shared path for live and primary DB replay | Legacy paths retain different rules | `select_entry_candidate()` | Adapt or label legacy callers; preserve explicit research overrides. |
| Historical truth | TimescaleDB, JSON chain cache, CSV loaders, reports | DB for primary replay; loaders vary by command | Cache/CSV can silently answer different questions | TimescaleDB for operational history; adapters explicitly labeled | Require provenance in every report and keep cache as optional input only. |

## 6. Duplication map

### Harmful business-rule duplication

- Host/Eastern/SQL definitions of the active trade date.
- Asset widths, ranges, tolerances, and drawdown defaults in YAML, `run_backtest_db.py`, `run_entry_analysis.py`, and simulation defaults.
- Entry-selection logic in shared selection versus legacy `SimulationEngine.simulate_day()`.
- Order-status terminal/category sets across execution, DB queries, and reporting.
- RR-target calculations in parity reporting versus `StrategySettings.rr_target`.
- PnL-dollar conversion across helpers, SQL, notifier, and scripts.

### Acceptable adapter duplication

- DB, CSV, Schwab, and synthetic loaders may differ in I/O while producing common `DayData`/`OptionQuote` structures.
- Paper and live order adapters may differ in fill mechanics; they must return the same authoritative fill contract.
- SPX, NDX, and XSP configuration values should stay explicit because behavior is intentionally different.
- Notification/report formatting can reformat values but should not redefine calculations.

### Superficially similar code that should remain separate

- Entry and exit price ladders have different market sides, urgency, cancel semantics, and failure recovery.
- Quote-quality checks for accepting a new peak and authorizing a drawdown exit serve different decisions even if predicates overlap; centralize only shared pure predicates already present.
- Operational live reconciliation and offline parity reports consume similar broker/DB data but have different side-effect and failure requirements.

## 7. Safety risk register

| Trigger | Failure mode | Existing protection | Protection gap | Detection | Recovery | Recommended mitigation |
|---|---|---|---|---|---|---|
| Broker rejects/expires entry | Repeated fresh submissions | Inner ladder raises terminal exception | Outer entry loop swallows it | Logs/intents, no hard alert | Stop service manually | BG-001 fail-closed task termination and alert. |
| Exit fills, risk DB update fails | Second exit submission | Intent and broker reconciler | Local monitor remains active | Broker gate may catch later | Manual reconciliation | BG-002 idempotent completion ordering. |
| Price improvement/multi-fill | Wrong stored PnL/risk | Broker payload persisted in intent | Normal path discards execution details | Later transaction comparison | Manual correction | BG-003 authoritative fill result. |
| Both settlement sources fail | Trade closed at zero | Two data attempts | Zero sentinel treated as valid | Error log only | Manual DB repair | BG-004 durable settlement-pending state. |
| Restart after 20:00 ET | Wrong order/intent/risk date | Eastern helpers exist elsewhere | `date.today`/`CURRENT_DATE` split | Reconciliation errors may appear | Manual date-specific inspection | BG-005 explicit session date. |
| Main push | Untested SHA and live XSP rebuild | Pushes now validate only; deployment is manual | Remaining risk is operator misuse of manual dispatch | Workflow result and revision checks | Do not dispatch until broker/DB are flat | BG-006 immutable validated deployment. |
| AI reviewer edits PR | Unsafe code auto-merges | Syntax and model re-review | No deterministic post-edit tests/human approval | Post-deploy failures | Revert | BG-007 read-only AI review and branch protection. |
| Broker/DB/data unhealthy | `/health` stays green | Process uptime only | No readiness | External logs/metrics | Operator diagnosis | BG-008 readiness state. |
| Config typo | Unsafe default silently wins | Pydantic type parsing, selected live guards | Extras/ranges ignored | Behavior/log review | Correct config/restart | BG-009 strict semantic validation. |
| Broker await hangs | Monitor/reconciler stalls | Dependency timeout may exist | No explicit owned deadline | No task-age readiness | Restart | Verify then implement BG-013 deadlines. |

## 8. Test-gap analysis

Ranked by financial/operational protection:

1. Top-level terminal-order propagation: actual `entry_loop()` must stop after one rejection/expiry/partial state.
2. Exit fill plus injected DB/risk failure: prove no second broker call and idempotent close transition.
3. Broker execution evidence: price improvement, multiple fills, child fills, missing fields, quantity mismatch, and normal/restart equivalence.
4. Settlement failure/retry: never close at zero without validated evidence.
5. Crash-window table: before submit, after submit/no `Location`, after order ID, after fill/before trade insert, after exit fill/before close, after close/before risk update.
6. Eastern session-date matrix across UTC midnight, DST, holidays, and early closes.
7. Readiness behavior for DB/broker/data/gate/task failures.
8. Strict config tests for extras, bounds, and cross-field invariants.
9. Golden snapshot parity across shared live/DB replay and any retained research adapter for SPX/XSP/NDX.
10. Migration ledger concurrency, checksum, rollback, and no-op repeat application.
11. Async cancellation and never-returning broker calls.
12. CI governance tests proving generated changes cannot merge or deploy without deterministic gates.

The current suite is valuable: 362 tests pass, and execution/state-machine pure logic is well covered. Coverage is not a quality target by itself, but the distribution is risky: the primary missing lines are orchestration, persistence failure, adapter, and shutdown paths rather than harmless formatting code.

## 9. Performance analysis

No micro-optimization is justified from current evidence. The principal measurable candidates are operational:

- Position monitoring fetches a full option chain every two seconds while the collector also fetches full chains every 60 seconds. Measure Schwab calls/minute, payload bytes, p50/p95 latency, rate-limit responses, and event-loop lag during an open position before introducing a cache. Any reuse must carry fetch timestamps and cannot weaken exit freshness.
- Live ladders refetch a full chain per step/attempt. Measure ladder attempts and chain latency; do not parallelize order-side I/O.
- Migrations rerun DDL on every app startup. Measure startup/lock duration; BG-011 removes this deterministic overhead without runtime caching.
- `tent_boundaries` and monitoring-leg writes occur every two seconds. Measure rows/day, DB latency, and retention/index size. Batch only if crash-loss tolerance is explicitly accepted.

No unbounded application cache or obvious N+1 query in the live hot path was confirmed. Correctness and fresh broker state are more valuable than speculative caching.

## 10. Refactoring roadmap

### Immediate safety corrections

Prerequisites: return XSP to paper/disabled mode; preserve redacted broker fixtures; no real broker writes.
Work: BG-001, BG-002, BG-003, BG-004, BG-005.
Risk: High because behavior is safety-critical; use one finding per patch.
Benefit: Stops repeated orders, restores fill/risk authority, and makes restart/settlement deterministic.
Verification: focused failure-injection tests, full execution/recovery suite, full pytest, targeted Ruff, Graphify update, tabletop crash windows.

### Safe foundational cleanup

Prerequisites: Immediate safety tests green.
Work: BG-008 readiness, BG-012 log redaction, baseline changed-file Ruff gate.
Risk: Low-to-medium.
Benefit: Better operator truth and reduced metadata exposure.
Verification: endpoint/log-capture tests and deployment dry run.

### Single-source-of-truth consolidation

Prerequisites: Golden parity snapshots.
Work: BG-009 strict config, shared session date, status vocabulary, configured RR target, remove stale asset defaults.
Risk: Medium; configuration and research outputs may change.
Benefit: Makes silent rule drift harder.
Verification: config matrix plus live/DB/research golden selection.

### Reliability improvements

Prerequisites: Verify dependency timeouts and establish readiness state.
Work: BG-011 migration ledger, BG-013 deadlines/cancellation, explicit durable settlement/exit transition states.
Risk: Medium.
Benefit: Predictable startup, shutdown, and outage recovery.
Verification: concurrency, cancellation, failed migration, and dependency outage tests.

### Performance improvements

Prerequisites: Production metrics proving rate/latency/DB pressure.
Work: Timestamped short-lived chain reuse or focused quote endpoints; bounded write batching/retention.
Risk: Staleness can alter exits.
Benefit: Lower API/DB pressure only if measured.
Verification: before/after calls, latency, rate limits, event-loop lag, and parity.

### Optional long-term architecture work

Keep `run_live.py` as composition root, but move reconciliation/recovery into one cohesive application service only after BG-001 through BG-005 are characterized. Do not create a generic manager/factory/plugin layer. A small typed `FillResult`, explicit trade lifecycle transitions, and a passed `session_date` cover most current risk without a broad rewrite.

## 11. Verification log

| Command | Actual result |
|---|---|
| `git branch --show-current` | `main` |
| `git rev-parse HEAD` | `d112dcba0a71b5090cf574d08aa7a19ff6eee7c0` |
| `git status --short` | Pre-existing changes in `configs/universes/liquid.txt`, `configs/universes/liquid_meta.json`, and `src/butterfly_guy/scripts/run_backtest_db.py`; review added only the two requested review documents. |
| Mandatory `sed`/`nl`/`rg` document and source inspections | Completed; no secret files read or printed. |
| Three targeted Graphify queries | Completed; graph used for navigation. Existing graph is stale from commit `331e6e92` and has low cohesion, so source/tests were authoritative. |
| `UV_CACHE_DIR=/tmp/uv-cache uv sync` | Passed; 84 packages resolved, six unused environment packages removed. |
| `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q --cov=butterfly_guy --cov-report=term-missing` | Passed: `362 passed in 14.07s`; total coverage 52%. |
| `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` | Failed: 115 existing violations; 17 reported automatically fixable. |
| `docker compose -f infra/docker-compose.yml --profile ndx --profile xsp config >/dev/null` | Passed. |

Not executed:

- No broker write, cancel, replace, preview, or live-order command.
- No live-mode change, container restart, deployment, database mutation, or credential inspection.
- No real integration against Schwab or TimescaleDB; the full local test suite used mocks/fakes and completed without broker writes.
- No Graphify update because no code files were modified; the existing graph staleness is explicitly recorded.

## Final production-readiness decision

NO-GO for unattended live trading. Keep live trading disabled until BG-001 through BG-005 and BG-006 have verified fixes, real redacted fill/status evidence exists, and the restart/exit/settlement failure drills pass. The repository is a solid paper/research foundation, but current orchestration and deployment failure modes can still make a dangerous change appear safe.
