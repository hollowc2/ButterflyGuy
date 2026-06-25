# Independent Pre-Live Audit of Butterfly Guy

Audit date: 2026-06-25
Scope: `/opt/butterflyguy` source, configs, tests, Docker/monitoring files, live container status, and read-only aggregate TimescaleDB queries.
Mode: original audit was read-only; remediation updates in this document modified local source, tests, config comments, and graphify artifacts. No broker order APIs, restarts, DB writes, commits, or pushes were performed.

## 1. Executive Summary

Butterfly Guy is a Dockerized automated 0-DTE index-options butterfly system for SPX, NDX, and XSP. It collects Schwab option chains, selects directional OTM long butterflies, enters paper or live orders through Schwab, monitors position mark values, exits on profit-protection/drawdown rules, and cash-settles remaining index butterflies after the close.

The strongest parts are the paper-first default, structured decision logging, DB-backed risk state, persistent open-trade recovery from local `butterfly_trades`, a useful Prometheus/Grafana base, and a local test suite that currently passes (`311 passed in 5.33s`). There is also live/backtest parity tooling and stored metadata for newer trades.

The original audit found serious weaknesses in live-order lifecycle safety, broker reconciliation, idempotency, and concurrency. The duplicate-working-order guard, single-submit order placement, exit post-cancel fill check, startup broker mismatch checks, and live entry advisory lock have since been added or mitigated. The remaining serious weaknesses are continuous broker reconciliation, durable broker order-intent/order-ID persistence, automatic restart reconciliation of broker-filled/flat states, partial-fill handling, DB-level open-trade uniqueness, and operational runbooks.

Historical performance is not enough to justify live trading. Stored closed trades show SPX positive over 58 trades (+$5,176), but only 12 wins and 46 losses; removing the best three SPX trades turns net P&L negative (-$1,452). NDX is materially negative over 48 trades (-$15,961.52), and XSP is slightly negative over 39 trades (-$93). These are small, regime-dependent samples with concentrated winners and incomplete metadata in older rows.

Operationally, the platform is still not ready to trade real money today. The system has stronger entry/exit guards now, but can still lose durable awareness of broker-accepted orders during crash windows, lacks continuous broker reconciliation, and has not proven safe handling for partial fills or complex-order status edge cases.

## 2. Final Recommendation

**NO-GO**

This recommendation permits continued broker paper trading, read-only shadow mode, historical replay, and deterministic simulations. It does not permit live-money automated order placement. A limited live pilot should wait until the release-blocking findings are fixed and verified with failure-injection tests.

## 3. Release-Blocking Findings

### Finding ID: BLOCKER-001

* **Title:** Actual live entry path bypasses duplicate working-order guard
* **Severity:** Critical
* **Category:** Order management / duplicate-order prevention
* **Affected components:** `TradeService`, `OrderManager`, Schwab order lifecycle
* **Evidence:** `src/butterfly_guy/services/trade_service.py:428` calls `execute_single_attempt()`. The open-order guard is only in `src/butterfly_guy/execution/order_manager.py:250-267` inside `execute_entry()`, which is not the production entry path.
* **Failure scenario:** Schwab accepts an order, response is delayed/lost, or another working opening order exists; the next step submits another opening butterfly.
* **Potential financial impact:** Duplicate positions, doubled max loss, unexpected margin/buying-power usage.
* **Likelihood:** Medium in live trading; network and broker latency are normal events.
* **Detectability:** Low before fill unless Schwab open orders are reconciled.
* **Recommended remediation:** Put the working-order guard in the shared single-attempt path or before every live `place_order()` call.
* **Required verification test:** `TradeService.attempt_entry()` must block when Schwab reports same-day working opening orders.

### Finding ID: BLOCKER-002

* **Title:** `place_order()` retries are not idempotent
* **Severity:** Critical
* **Category:** Broker/API integration
* **Affected components:** `SchwabClientWrapper.place_order()`, `ButterflyOrderBuilder`
* **Evidence:** `_retry()` retries all exceptions up to 3 times in `src/butterfly_guy/data/schwab_client.py:84-107`; `place_order()` uses it at `src/butterfly_guy/data/schwab_client.py:135-144`. Order specs in `src/butterfly_guy/execution/order_builder.py:51-84` contain no client order ID/idempotency key.
* **Failure scenario:** Schwab accepts attempt 1 but the client times out or loses the `Location` header; attempt 2 submits a second order.
* **Potential financial impact:** Duplicate broker positions or unintended exposure.
* **Likelihood:** Medium.
* **Detectability:** Medium after the fact; poor before fill.
* **Recommended remediation:** Do not blindly retry non-idempotent order placement. Add broker-supported client order IDs if available, otherwise reconcile open orders after ambiguous placement before retrying.
* **Required verification test:** Simulate accepted order plus lost response and assert no second submit occurs without reconciliation.

### Finding ID: BLOCKER-003

* **Title:** Startup does not reconcile broker positions or open orders
* **Severity:** Critical
* **Category:** Restart safety / broker reconciliation
* **Affected components:** `run_live.py`, `SchwabClientWrapper`, `TradeQueries`
* **Evidence:** Startup recovers only local open DB rows at `src/butterfly_guy/scripts/run_live.py:295-340`. Broker account/order APIs exist at `src/butterfly_guy/data/schwab_client.py:275-336` but are not used for startup gating.
* **Failure scenario:** Process crashes after broker fill but before `butterfly_trades` insert; on restart no local `OPEN` row exists, and the app can enter another position.
* **Potential financial impact:** Untracked live position, duplicate entry, unmanaged exit risk.
* **Likelihood:** Medium.
* **Detectability:** Low without explicit reconciliation alerts.
* **Recommended remediation:** On startup and periodically, compare broker positions/open orders to DB state. Unknown broker state must block new entries.
* **Required verification test:** Broker position with no DB row must halt entries and raise an alert.

### Finding ID: BLOCKER-004

* **Title:** Crash after exit fill but before DB close can trigger duplicate close attempts
* **Severity:** Critical
* **Category:** State management / restart safety
* **Affected components:** `PositionService`, `TradeQueries`
* **Evidence:** `PositionService` executes exit at `src/butterfly_guy/services/position_service.py:252-257`, then later closes the DB row at `src/butterfly_guy/services/position_service.py:284-297`. Restart recovery uses still-open DB rows at `src/butterfly_guy/scripts/run_live.py:295`.
* **Failure scenario:** Exit order fills, process dies before DB update, restart sees local trade as `OPEN` and attempts another close.
* **Potential financial impact:** Reversal/naked exposure if a second close order is accepted against an already-closed position.
* **Likelihood:** Low to medium, high impact.
* **Detectability:** Medium after broker reconciliation; currently weak.
* **Recommended remediation:** Persist order intent/order IDs before submit, reconcile broker state before exit retry, and make close flow restart-safe.
* **Required verification test:** Local `OPEN` trade with broker-flat state must reconcile closed or halt, not send another close.

### Finding ID: BLOCKER-005

* **Title:** Live exit cancel path does not check for post-cancel fills
* **Severity:** High
* **Category:** Order lifecycle
* **Affected components:** `OrderManager.execute_exit()`
* **Evidence:** Entry cancel calls `_check_post_cancel_fill()` at `src/butterfly_guy/execution/order_manager.py:186-190` and `308-312`; exit cancel at `src/butterfly_guy/execution/order_manager.py:495` does not.
* **Failure scenario:** Exit fills while cancel is racing, app misses it, and a later ladder step submits another close.
* **Potential financial impact:** Duplicate close/reversal.
* **Likelihood:** Medium near fast markets or close.
* **Detectability:** Low without broker reconciliation.
* **Recommended remediation:** Apply the same post-cancel fill check to exits and reconcile current broker position before further close attempts.
* **Required verification test:** Cancel-then-filled exit status must stop the ladder and close local state exactly once.

### Finding ID: BLOCKER-006

* **Title:** Multiple same-underlying processes can pass risk and submit concurrently
* **Severity:** High
* **Category:** Concurrency / risk controls
* **Affected components:** `RiskEngine`, `TradeQueries`, DB schema
* **Evidence:** Risk checks read `daily_risk_state` at `src/butterfly_guy/risk/risk_engine.py:63-80`; trade insert happens later at `src/butterfly_guy/db/queries.py:221-238`; trade count increments after insert at `src/butterfly_guy/services/trade_service.py:468`. Schema has no unique one-open-trade constraint in `src/butterfly_guy/db/migrations/001_initial.sql:45-69`.
* **Failure scenario:** Two app instances or overlapping invocations both pass risk before either increments count.
* **Potential financial impact:** Multiple entries despite `max_trades_per_day: 1`.
* **Likelihood:** Low in normal Compose, higher during deploy/restart incidents.
* **Detectability:** Medium after entries.
* **Recommended remediation:** Add a DB transaction/advisory lock or partial unique constraint for open trade per underlying/date.
* **Required verification test:** Two concurrent entry attempts produce one order max.

## 4. Complete Findings Register

| ID | Status | Type | Finding |
|---|---|---|---|
| BLOCKER-001 | Resolved | Confirmed defect | Production live entry path now checks same-day working orders before submit. |
| BLOCKER-002 | Resolved | Confirmed defect | Non-idempotent order placement now submits once and does not use generic retry. |
| BLOCKER-003 | Mitigated | Design risk | Startup now blocks broker/DB mismatches; continuous reconciliation still open. |
| BLOCKER-004 | Mitigated | Design risk | Pending-exit metadata and startup broker-flat blocking reduce duplicate-close risk; automatic close reconciliation still open. |
| BLOCKER-005 | Resolved | Confirmed defect | Exit cancel path now checks for post-cancel fills. |
| BLOCKER-006 | Mitigated | Design risk | Live entry uses an advisory lock and risk re-check; DB-level uniqueness still open. |
| HIGH-001 | Resolved | Documentation/behavior mismatch | Owner confirmed consecutive losses are warning-only; config comments now match behavior. |
| HIGH-002 | Mitigated | Data freshness | VIX-based entries now age-gate `$VIX`; broader spot/chain freshness remains partial. |
| HIGH-003 | High | Strategy rule mismatch | VIX center tolerance falls back to all candidates instead of blocking. |
| HIGH-004 | High | Observability | `/health` is process-only, not DB/broker/data/trading health. |
| HIGH-005 | High | Deployment | Deploy workflow lacks test/config/health gates. |
| HIGH-006 | High | Config safety | Live enablement lacks account/underlying hard confirmation beyond config/env. |
| MED-001 | Medium | Documentation mismatch | AGENTS/CLAUDE paper-fill description conflicts with ask/bid-based paper code. |
| MED-002 | Medium | Historical data quality | Older trade rows have missing leg symbols: NDX 10, SPX 16, XSP 6. |
| MED-003 | Medium | Backtest parity | Backtest still has separate/default paths that can drift from runtime selection. |
| MED-004 | Medium | Time/calendar | Market calendar is computed for holidays but early closes are not represented. |
| MED-005 | Medium | Security | Shared `tokens.json` is mounted into all app containers without `:ro`. |
| LOW-001 | Low | Documentation | `PositionService.monitor_loop()` docstring says 10s but code polls every 2s. |
| INFO-001 | Informational | Strength | Local suite passes: `311 passed in 5.33s`. |

## 5. Strategy-versus-Implementation Matrix

| Rule | Documented behavior | Implemented behavior | Evidence | Difference | Risk |
|---|---|---|---|---|---|
| Instruments | SPX, NDX, XSP 0-DTE butterflies | Confirmed | `configs/config*.yaml`, `run_live.py` | None material | Low |
| Paper fills | Mark/mid convention per AGENTS/CLAUDE | Entry uses composite ask plus slippage/commission; exit uses bid/forced mark logic | `AGENTS.md`, `order_manager.py:139-150`, `trade_service.py:389` | Docs stale | Performance estimates may be misunderstood |
| Consecutive losses | Warning after N losses | Warning only, trading allowed | `config.py:120`, `risk_engine.py:100-125` | None after owner confirmation | Low |
| VIX freshness | VIX anchored selection implies current VIX | VIX-based entries require `$VIX` within `entry.max_vix_age_seconds` | `trade_service.py`, `collector.py:157-164` | Broader spot/chain age gates still open | Medium |
| Center tolerance | Candidate must be within tolerance | Falls back to all candidates if none near target | `config.yaml:35`, `butterfly_selector.py:46-66` | Rule not mandatory | High |
| EOD handling | CLAUDE says exit 5 minutes before close | Config disables pre-close exit and cash-settles after close | `config.yaml:71`, `position_service.py:364-415` | Docs stale | Medium |
| NDX widths | CLAUDE says 25/50/75 | Config uses 80/100/150 | `CLAUDE.md`, `config_ndx.yaml:7` | Docs stale | Medium |
| Max daily trades | 1 per underlying/day | DB risk state plus live entry advisory lock | `risk_engine.py:68`, `trade_service.py` | No DB unique constraint yet | Medium |
| Live duplicate order prevention | Same-day working order guard before submit | Guard runs in actual single-attempt entry path | `order_manager.py`, `trade_service.py` | Runtime reconciliation still needed | Medium |

## 6. Historical Performance Analysis

Data source: read-only SQL against `butterfly_trades` in `butterfly_timescaledb`.

Aggregate closed-trade results:

| Underlying | Trades | Date range | Net P&L | Avg | Median | Wins | Losses | Profit factor | Worst | Best |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SPX | 58 | 2026-03-17 to 2026-06-24 | +$5,176.00 | +$89.24 | -$120.00 | 12 | 46 | 1.74 | -$311 | +$2,258 |
| NDX | 48 | 2026-03-30 to 2026-06-22 | -$15,961.52 | -$332.53 | -$282.00 | 6 | 42 | 0.18 | -$2,168 | +$2,265.48 |
| XSP | 39 | 2026-04-02 to 2026-06-24 | -$93.00 | -$2.38 | -$12.00 | 6 | 33 | 0.84 | -$44 | +$221 |

Data-quality findings:

| Check | Result |
|---|---|
| Open DB trades | None |
| Missing exit time/price/P&L | None in current closed rows |
| Missing leg symbols | NDX 10, SPX 16, XSP 6 |
| Duplicate trade dates | NDX had 2 trades on 2026-03-31 |
| Weekend trade dates | None |
| Metadata completeness | Entry attempts and parity fields exist mostly for newer rows only |

Concentration and fragility:

| Underlying | Net | Without best 1 | Without best 3 | Without best 5 |
|---|---:|---:|---:|---:|
| SPX | +$5,176.00 | +$2,918.00 | -$1,452.00 | -$4,754.00 |
| NDX | -$15,961.52 | -$18,227.00 | -$19,312.00 | -$19,513.00 |
| XSP | -$93.00 | -$314.00 | -$567.00 | -$589.00 |

Daily distribution:

| Underlying | Days | Net | Avg day | Worst day | Best day | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| SPX | 58 | +$5,176.00 | +$89.24 | -$311 | +$2,258 | -$2,480 |
| NDX | 47 | -$15,961.52 | -$339.61 | -$2,168 | +$2,265.48 | -$15,930.52 |
| XSP | 39 | -$93.00 | -$2.38 | -$44 | +$221 | -$421 |

Segmentation by direction:

| Underlying | Direction | Trades | Net | Avg | Wins |
|---|---|---:|---:|---:|---:|
| SPX | CALL | 35 | +$2,446 | +$69.89 | 8 |
| SPX | PUT | 23 | +$2,730 | +$118.70 | 4 |
| NDX | CALL | 34 | -$9,087.52 | -$267.28 | 5 |
| NDX | PUT | 14 | -$6,874 | -$491.00 | 1 |
| XSP | CALL | 23 | -$117 | -$5.09 | 4 |
| XSP | PUT | 16 | +$24 | +$1.50 | 2 |

Sensitivity to additional round-trip slippage:

| Underlying | Current net | -$5/trade | -$10/trade | -$25/trade |
|---|---:|---:|---:|---:|
| SPX | +$5,176 | +$4,886 | +$4,596 | +$3,726 |
| NDX | -$15,961.52 | -$16,201.52 | -$16,441.52 | -$17,161.52 |
| XSP | -$93 | -$288 | -$483 | -$1,068 |

Statistical limitations:

* The sample is small and recent: about 39-58 closed trades per product.
* Outcomes are not independent; trades repeat the same strategy, same daily window, same broker, and similar market regimes.
* SPX profitability is concentrated in a few cash-settled winners.
* NDX and XSP do not show credible positive expectancy in stored records.
* Sharpe/Sortino estimates would be unstable and are not decision-grade here.
* Stored rows do not prove broker-confirmed executable fills; paper/live parity remains an open validation requirement.

## 7. Risk-Control Matrix

| Control | Present | Enforced where | Persistent | Tested | Fail-open/fail-closed | Status |
|---|---|---|---|---|---|---|
| Paper default | Yes | `config.py`, configs | Config | Partial | Fail-closed by default | PASS |
| Live trading gate | Yes | `run_live.py:154-157` | Config/env | Partial | Fail-closed unless changed | PARTIAL |
| Max trades/day | Yes | `RiskEngine.can_trade()` | `daily_risk_state` | Yes | Race-prone | PARTIAL |
| Max position size | Yes | `RiskEngine.can_trade()` | Config only | Yes | Fail-closed per call | PARTIAL |
| Daily loss halt | Yes | `RiskEngine` + `daily_risk_state` | Yes | Yes | Fail-closed | PASS |
| Weekly loss halt | Yes | Closed-trade query | DB-derived | Partial | Fail-closed | PASS |
| Consecutive losses | Yes | `RiskEngine` warning | DB-derived | Yes | Warning-only by policy | PASS |
| Buying power | Live only | `TradeService` then `RiskEngine` | No | Partial | Default fail-closed on balance error | PARTIAL |
| Duplicate open orders | Yes | `execute_single_attempt()` | Broker-derived | Yes | Fail-closed if open-order check fails | PASS |
| Broker position reconciliation | Partial | Startup check | No | Yes | Fail-closed at startup, no runtime loop | PARTIAL |
| Open DB trade recovery | Yes | `run_live.py:295-340` | DB | Partial | Local-only | PARTIAL |
| Stale market data rejection | Partial | Missing quotes and stale VIX block some paths | No comprehensive spot/live chain age gate | Partial | Mixed | PARTIAL |
| Quote width/quality | Partial | Position drawdown exits for NDX/XSP | Config | Yes | Disabled for SPX | PARTIAL |
| End-of-day handling | Yes | Cash settlement after close | DB | Partial | Depends on valuation fallback | PARTIAL |
| Emergency flatten | Not verified | No tested runbook found | No | No | Unknown | FAIL |
| Health endpoint | Yes | Metrics thread | No | No | Fail-open | FAIL |
| Alerts | Partial | Logs, notify on collector failures, Discord/Telegram | External | Partial | Some failures log-only | PARTIAL |

## 8. Failure-Mode and Effects Analysis

| Failure mode | Cause | Current behavior | Financial effect | Detection | Mitigation | Residual risk |
|---|---|---|---|---|---|---|
| Crash before order submission | Process dies before broker call | No order; DB no trade | None | Logs/process health | Supervisor restart | Low |
| Crash after order submission before DB insert | Accepted broker order, no local row | Startup sees no open DB trade | Unmanaged position, duplicate entry | Weak | Add broker reconciliation | Critical |
| Crash after partial fill | Multi-leg spread state uncertain | No explicit partial-fill lifecycle | Naked/partial exposure possible | Weak | Persist order state and reconcile | Critical |
| Crash during exit order | Exit may fill but DB stays open | Restart may close again | Reversal/duplicate close | Weak | Exit reconciliation | Critical |
| Broker accepts order but API times out | Generic retry | May submit duplicate | Duplicate position | Weak | Idempotent placement | Critical |
| DB unavailable | Queries fail/log; task may continue loops | Entries likely fail, monitoring may lose state | Unknown state | Logs only | Fail closed on DB health | High |
| Market-data feed freezes | No comprehensive freshness gate | Latest/stale VIX or chain may be used | Wrong strikes/widths | Some logs | Age-bound all inputs | High |
| Internet disconnects | API errors | Retry/log | Missed exits or late entries | Logs | Halt on unknown broker/data state | High |
| Broker websocket disconnects | REST polling only | Not applicable/unknown | Missed events | Not verified | REST reconciliation loop | Medium |
| Restart with open position | Local DB recovery only | Monitors DB open row | Good if DB matches broker | Logs | Broker reconciliation | High |
| Two instances start | No leader lock | Both can pass risk | Duplicate entries | After trade | DB lock/constraint | High |
| Wrong timezone/clock | Host time used | Market checks rely on local clock/ZoneInfo | Trades outside intended window | Weak | NTP and exchange calendar checks | Medium |
| Early market close | Calendar lacks early closes | Uses 16:00 close | Late/unmanaged exit behavior | Weak | Calendar library/early-close table | Medium |
| Unexpected broker position | Not reconciled at startup | May still enter | Exposure stacking | Weak | Block on unknown positions | Critical |
| Entry fills after window closes | Order remains day/normal until cancel path completes | Can still fill if accepted | Late exposure | Broker status/log | Time-bound order policy/reconcile | Medium |

## 9. Test Coverage Assessment

Current coverage is broad for pure logic: selection, builder, risk engine, order manager paper/live unit paths, state machine, position valuation, reports, time utilities, and backtest defaults. The safe local command `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q` passed: `311 passed in 5.33s`.

Current coverage now includes the actual `execute_single_attempt()` entry path, single-submit order placement, startup broker mismatch checks, exit post-cancel fill detection, and stale-VIX blocking.

Critical missing tests before live:

* Ambiguous `place_order()` timeout after broker acceptance.
* Partial fill and rejected multi-leg order handling.
* Two simultaneous same-underlying entry attempts.
* Spot and option-chain staleness rejection.
* Early market close behavior.
* DB failure during entry insert and exit close.
* Emergency flatten dry-run/paper test.

## 10. Operational Runbook Gaps

Missing or not verified:

* Startup checklist that reconciles DB, broker positions, broker open orders, data freshness, and risk state.
* Pre-market go/no-go checklist.
* Live supervision procedure with exact dashboards and alert expectations.
* Manual flatten procedure and verification.
* Broker outage response.
* Market-data outage response.
* DB outage response.
* Restart recovery procedure.
* End-of-day reconciliation between Schwab transactions, DB rows, and notifications.
* Incident response and escalation.
* Rollback procedure after a bad deploy.

## 11. Live-Readiness Checklist

| Item | Status |
|---|---|
| Strategy behavior matches specification | PARTIAL |
| Historical trades reconcile to broker fill records | NOT VERIFIED |
| Maximum risk calculations are correct | PARTIAL |
| Risk limits survive restarts | PARTIAL |
| Duplicate orders are prevented | PARTIAL |
| Partial fills and rejected orders handled safely | FAIL |
| Broker positions/orders reconciled at startup and continuously | PARTIAL |
| Unknown broker/app state stops entries | PARTIAL |
| Market-data freshness enforced | PARTIAL |
| Timezone, holidays, early closes handled correctly | PARTIAL |
| Open positions managed after process restart | PARTIAL |
| Emergency flatten tested | NOT VERIFIED |
| Live and paper configs safely separated | PARTIAL |
| Critical events produce actionable alerts | PARTIAL |
| No unresolved Critical findings | FAIL |
| High financial-safety findings resolved/mitigated | FAIL |
| Limited-capital rollout and rollback procedure exists | NOT VERIFIED |

## 12. Remediation Plan

## 12A. Implementation Status Update

Update date: 2026-06-25

Completed in this implementation:

* BLOCKER-001: Moved the duplicate working-order guard into the actual production entry path, `OrderManager.execute_single_attempt()`. `TradeService.attempt_entry()` now reaches the guard before any live opening order submit.
* BLOCKER-002: Removed generic retry wrapping from `SchwabClientWrapper.place_order()`. Order placement now submits once and refuses to retry if the response is ambiguous or missing an order `Location`.
* BLOCKER-005: Added post-cancel fill detection to the live exit ladder so a cancel/fill race stops the ladder and returns a filled exit result.

Mitigated, but not fully complete:

* BLOCKER-003: Added live startup broker-vs-DB fail-closed checks for same-underlying option positions and same-day working orders. This blocks unsafe startup mismatches but is not continuous broker reconciliation.
* BLOCKER-004: Persisted `pending_exit` metadata before live exit submission and made startup block if DB says `OPEN` while broker is flat. This reduces duplicate-close risk but does not yet persist broker order IDs before submit or reconcile filled exits into closed DB rows automatically.
* BLOCKER-006: Added a same-underlying/same-day PostgreSQL advisory lock around live entry submit and DB insert, with a risk re-check after lock acquisition. This prevents overlapping app processes from submitting concurrently when they use this code path, but there is no DB-level unique open-trade constraint yet.
* P1 VIX freshness: Added `entry.max_vix_age_seconds` and made VIX-based entries fail closed when `$VIX` is unavailable or stale before the option-chain scan.
* P1 consecutive-loss semantics: Owner confirmed warning-only behavior; config comments now match the existing risk-engine behavior.

Verification completed:

* `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_order_manager.py tests/test_schwab_client.py tests/test_run_live.py -q` passed: 51 tests.
* `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q` passed: `311 passed in 5.33s`.
* `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_trade_service.py tests/test_config.py -q` passed: 16 tests.
* Focused Ruff check on current touched source/test files passed.
* `/home/billy/.local/bin/graphify update .` completed.

Still left before live-money trading:

* Full broker reconciliation loop during runtime, not only startup.
* Durable broker order-intent/order-ID persistence before live entry and exit submits.
* Automatic reconciliation of DB `OPEN` rows against broker-filled/flat states after restart.
* DB-level open-trade uniqueness or transactional admission stronger than the app advisory lock.
* Partial-fill handling and Schwab complex-order status mapping.
* P1 items below: broader spot/chain data freshness, health endpoint depth, deploy gates, and live runbooks.

### Before any live order

| Priority | Item | Risk reduction | Affected files/services | Approach | Verification |
|---|---|---|---|---|---|
| P0 | Move duplicate-order guard to actual live entry path | Prevent duplicate entries | `trade_service.py`, `order_manager.py` | Guard before every live order placement | Unit test on `attempt_entry()` |
| P0 | Make order placement idempotent or reconciliation-gated | Prevent duplicate broker accepts | `schwab_client.py`, `order_builder.py` | No blind retry for non-idempotent submit; add client ID if supported | Ambiguous timeout test |
| P0 | Broker reconciliation at startup | Prevent unknown positions | `run_live.py`, Schwab client | Compare broker orders/positions with DB before entries | Startup mismatch tests |
| P0 | Restart-safe exit lifecycle | Prevent duplicate close/reversal | `position_service.py`, DB schema | Persist order intent/order ID before submit; reconcile after restart | Crash-window tests |
| P0 | Exit post-cancel fill check | Prevent duplicate exits | `order_manager.py` | Reuse entry post-cancel logic for exits | Cancel/fill race test |
| P0 | Atomic entry admission | Prevent same-day concurrency race | DB migration, `RiskEngine`/`TradeService` | Advisory lock or unique open-trade constraint | Concurrent entry test |

### Before limited-capital pilot

| Priority | Item | Risk reduction | Affected files/services | Approach | Verification |
|---|---|---|---|---|---|
| P1 | Enforce VIX freshness | Avoid stale width/center decisions | `trade_service.py`, `config.py` | Done: `$VIX` max-age gate before VIX-based entries | Stale-VIX test |
| P1 | Enforce spot/chain freshness | Avoid stale strike/price decisions | `trade_service.py`, collector metadata | Max-age checks for spot and option chain | Stale-input tests |
| P1 | Resolve consecutive-loss semantics | Align risk docs/code | `config.py`, configs/tests | Done: warning-only policy documented | Existing risk tests |
| P1 | Improve `/health` | Operator safety | `metrics.py`, app services | DB/broker/data/risk readiness checks | Health endpoint tests |
| P1 | Add deploy gates | Avoid bad rollout | `.github/workflows/deploy.yml` | pytest, ruff, compose config, post-health | CI/deploy dry run |
| P1 | Write live runbooks | Operator readiness | docs | Startup, flatten, outage, EOD, rollback | Tabletop exercise |

### Before unattended operation

| Priority | Item | Risk reduction | Affected files/services | Approach | Verification |
|---|---|---|---|---|---|
| P2 | Continuous broker reconciliation | Detect drift during session | New service or loop in app | Poll open orders/positions and halt on mismatch | Fault-injection tests |
| P2 | Alerting for exit failures and unknown state | Faster response | monitoring/notifier | Page/actionable alert, not log-only | Alert tests |
| P2 | Early-close calendar support | Time safety | `time_utils.py` | Use exchange calendar or table | Early-close tests |
| P2 | Broker transaction reconciliation | P&L and fill authority | reports/services | Match DB to Schwab transactions | Reconciliation report |

### Longer-term improvements

| Priority | Item | Risk reduction | Affected files/services | Approach | Verification |
|---|---|---|---|---|---|
| P3 | Collapse duplicate backtest/live selection paths | Reduce drift | `run_backtest_db.py`, `simulation_engine.py` | Reuse `select_entry_candidate()` | Parity tests |
| P3 | Add richer slippage/fill modeling | Better validation | backtest/paper tools | Scenario analysis by spread/latency | Replay comparison |
| P3 | Read-only token mount where possible | Reduce secret blast radius | `docker-compose.yml` | Mount `tokens.json:ro` if refresh path allows | Token refresh test |

## 13. Proposed Deployment Ladder

1. Historical replay
   Promotion: deterministic replay matches expected entries/exits on fixed fixture dates.
   Rollback: any selection or P&L mismatch unexplained.

2. Deterministic simulation
   Promotion: failure-injection tests pass for timeout, restart, partial fill, stale data, DB failure.
   Rollback: any uncontrolled state transition.

3. Broker paper trading
   Promotion: 20 consecutive trading days with clean reconciliation, no unknown broker/DB mismatch, no missed alerts.
   Rollback: duplicate order, untracked position, stale-data trade, or unreconciled P&L.

4. Shadow mode against live market data
   Promotion: candidate decisions and hypothetical orders are logged without submit; operator can explain every skip/trade.
   Rollback: stale VIX/chain, health false-positive, or unexplained decision.

5. Supervised one-contract live trading
   Promotion: manual approval required before each order; broker/DB reconciliation after entry and exit.
   Rollback: any order-state ambiguity or alert failure.

6. Limited-capital pilot
   Promotion: objective risk limits, daily max loss, weekly max loss, and emergency flatten tested.
   Rollback: drawdown or operational incident threshold breach.

7. Gradual scaling
   Promotion: stable metrics over multiple regimes and continued reconciliation.
   Rollback: performance or operational degradation.

8. Unattended production
   Promotion: no unresolved Critical/High safety findings, tested runbooks, alerts, and rollback.
   Rollback: any unknown broker state or missed critical alert.

## 14. Questions Requiring Owner Confirmation

Owner answers recorded 2026-06-25:

| Question | Owner answer | Status / implication |
|---|---|---|
| Should `max_consecutive_losses` halt trading or only warn? | Only warn. | Config/docs should describe this as a warning control, not a hard halt. |
| Is cash settlement after close intended for all SPX/NDX/XSP cases, or should any products flatten before close? | Cash settlement is intended for all SPX, NDX, and XSP cases. | Keep post-close cash-settlement behavior unless later policy changes. |
| Are stored `butterfly_trades` rows broker-confirmed fills, paper-model fills, or mixed? | Not sure; likely mixed. | Treat historical DB rows as mixed evidence until reconciled against broker records. |
| Are SPX, NDX, and XSP intended to trade simultaneously from the same Schwab account? | No. Only SPX is intended for live; NDX and XSP are research. | Live enablement should be SPX-only unless explicitly changed later. |
| What exact capital allocation and max account-level loss should apply live? | Planned account size is $20,000; max account loss is $500 per day. | Add account-level risk gates before live-money operation. |
| Is there an existing manual flatten procedure outside this repo? | No. | A manual flatten runbook still needs to be written and tested. |
| Should VIX be treated as SPX-only infrastructure, or should each service independently fetch/validate VIX freshness? | Each service needs access to fresh VIX data. | Add per-service VIX freshness validation before VIX-based entries. |
| What Schwab order statuses are observed for complex option spreads in real paper/live runs? | Not sure. | Keep this as an open broker-observation gap; collect statuses during paper/shadow runs. |

## 15. Evidence Appendix

Files and functions reviewed:

* `README.md`, `CLAUDE.md`, `AGENTS.md`
* `graphify-out/GRAPH_REPORT.md`
* `configs/config.yaml`, `configs/config_ndx.yaml`, `configs/config_xsp.yaml`
* `infra/docker-compose.yml`, `infra/prometheus.yml`
* `src/butterfly_guy/scripts/run_live.py`
* `src/butterfly_guy/services/trade_service.py`
* `src/butterfly_guy/services/position_service.py`
* `src/butterfly_guy/execution/order_manager.py`
* `src/butterfly_guy/execution/order_builder.py`
* `src/butterfly_guy/data/schwab_client.py`
* `src/butterfly_guy/data/collector.py`
* `src/butterfly_guy/risk/risk_engine.py`
* `src/butterfly_guy/db/queries.py`
* `src/butterfly_guy/db/migrations/001_initial.sql`
* `src/butterfly_guy/core/config.py`
* `src/butterfly_guy/core/time_utils.py`
* `src/butterfly_guy/strategy/entry_selection.py`
* `src/butterfly_guy/strategy/butterfly_builder.py`
* `src/butterfly_guy/strategy/butterfly_selector.py`
* `src/butterfly_guy/position/state_machine.py`
* `src/butterfly_guy/position/position_manager.py`
* `tests/`

Commands executed:

```bash
git status --short
find . -maxdepth 2 -type f
sed -n '1,220p' graphify-out/GRAPH_REPORT.md
rg -n "prelive|decision_log|daily_risk_state|broker|Schwab|order|risk|paper|live" /home/billy/.codex/memories/MEMORY.md
rg -n "CREATE TABLE|butterfly_trades|decision_log|daily_risk_state|orders|fills|positions|UNIQUE|INDEX" src tests infra configs migrations -g '*.py' -g '*.sql' -g '*.yaml' -g '*.yml'
rg -n "class .*Risk|can_trade|submit|place_order|replace|partial|fill|reconcile|open_orders|positions|paper|live|stale|quote|market_hours|holiday|timezone|America/New_York" src tests configs infra -g '*.py' -g '*.yaml' -g '*.yml'
docker compose -f infra/docker-compose.yml ps
docker ps --format '{{.Names}} {{.Image}} {{.Status}}'
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q
docker exec butterfly_timescaledb psql -U butterfly -d butterfly_guy -c "SELECT ..."
```

Tests executed:

* `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q`
* Result: `311 passed in 5.33s`

Datasets examined:

* `butterfly_trades`
* `decision_log` event counts
* Trade metadata completeness fields
* Live container status

Assumptions:

* SQL aggregates use stored DB trade rows as-is.
* `pnl * 100 * quantity` is the intended dollar conversion for index option spread rows, matching repo query patterns.
* No Schwab broker calls were made during this audit.

Unavailable or not verified:

* Broker-confirmed fill ledger for every trade.
* Schwab open orders/positions at exact audit time.
* Raw account identifiers and secrets, intentionally not inspected or printed.
* Full partial-fill behavior in real Schwab complex orders.
* Emergency flatten procedure.
* Last historical-data subagent did not return before report generation; local read-only SQL evidence was used instead.
