# Independent Pre-Live Audit of Butterfly Guy

Audit date: 2026-06-25
Scope: `/opt/butterflyguy` source, configs, tests, Docker/monitoring files, live container status, and read-only aggregate TimescaleDB queries.
Mode: original audit was read-only; remediation updates modified local source, tests, config comments, graphify artifacts, and documentation. No broker order APIs, restarts, or DB writes were performed. The safety-gate remediation was committed and pushed as `47eacd0`; the broker order-intent lifecycle layer was committed and pushed as `cb95d00`.

## 1. Executive Summary

Butterfly Guy is a Dockerized automated 0-DTE index-options butterfly system for SPX, NDX, and XSP. It collects Schwab option chains, selects directional OTM long butterflies, enters paper or live orders through Schwab, monitors position mark values, exits on profit-protection/drawdown rules, and cash-settles remaining index butterflies after the close.

The strongest parts are the paper-first default, structured decision logging, DB-backed risk state, persistent open-trade recovery from local `butterfly_trades`, a useful Prometheus/Grafana base, and a local test suite that currently passes (`311 passed in 5.33s`). There is also live/backtest parity tooling and stored metadata for newer trades.

The original audit found serious weaknesses in live-order lifecycle safety, broker reconciliation, idempotency, and concurrency. The duplicate-working-order guard, single-submit order placement, exit post-cancel fill check, startup broker mismatch checks, live entry advisory lock, DB open-trade uniqueness migration, durable broker order-intent/order-ID persistence, known partial-fill fail-closed handling, runtime unknown-state entry gating, conservative restart repair for unambiguous bot-owned filled states, deploy gates, and first-pass runbook have since been added or mitigated. The remaining serious weaknesses are unproven Schwab complex-order status mapping, deeper health readiness, tested operational drills, and account-level live confirmation.

Historical performance is not enough to justify live trading. Stored closed trades show SPX positive over 58 trades (+$5,176), but only 12 wins and 46 losses; removing the best three SPX trades turns net P&L negative (-$1,452). NDX is materially negative over 48 trades (-$15,961.52), and XSP is slightly negative over 39 trades (-$93). These are small, regime-dependent samples with concentrated winners and incomplete metadata in older rows.

Operationally, the platform is still not ready to trade real money today. The system has durable broker-order intent tracking and runtime unknown-state gating now, but it has not proven all real Schwab complex-order status edge cases, health/readiness depth, account-level live confirmation, or operator drills.

## 2. Final Recommendation

**NO-GO**

This recommendation permits continued broker paper trading, read-only shadow mode, historical replay, and deterministic simulations. It does not permit live-money automated order placement. A limited live pilot should wait until the release-blocking findings are fixed and verified with failure-injection tests.

## 2A. What Is Left

These are the remaining blockers after commit `cb95d00`:

| Priority | Remaining work | Why it still blocks live money | Done when |
|---|---|---|---|
| P0 | Real Schwab complex-order status mapping | Known partial/cancel-pending statuses fail closed and a read-only status report exists, but real Schwab paper/live complex-spread payloads have not been observed enough to trust every status and child-order case. | Paper/shadow runs collect statuses; partial, cancel-pending, rejected, expired, filled, and child-order cases are mapped from observed payloads and covered by tests. |
| P0 | Restart reconciliation proof drill | Startup has conservative repair for unambiguous bot-owned filled entry/exit intents, but it has not been exercised against real Schwab paper payloads or a tabletop crash drill. | Simulated and paper/shadow restart drills prove filled-entry, filled-exit, broker-flat, partial-fill, missing-fill-price, and mismatched-leg outcomes. |
| P1 | Deeper `/health` readiness | Current health is process-level plus deploy smoke, not DB/broker/data/risk readiness. | `/health` or a readiness endpoint reports DB, Schwab auth, fresh chain/VIX, broker/DB reconciliation, and risk-state status. |
| P1 | Tested operator drills | A first-pass runbook exists, but flatten/restart/outage procedures have not been exercised. | Startup, manual flatten, restart recovery, broker outage, DB outage, and rollback are tabletop-tested and updated with exact commands. |
| P1 | Account-level live confirmation | Live mode is SPX-only and env-gated, but not yet tied to an explicit account/risk confirmation. | Live startup verifies the expected Schwab account, $20,000 allocation assumption, and $500 daily account-loss cap before enabling entries. |

Resolved locally after that commit:

* `broker_order_intents` now persists live entry/exit order intent before submit and records Schwab order IDs immediately after `Location`.
* Runtime broker reconciliation now gates new entries on unknown positions/orders while allowing bot-owned intent-backed working orders.
* Startup can conservatively repair bot-owned filled entry/exit states only when broker legs and fill price/time are unambiguous; otherwise it halts.
* VIX center tolerance now blocks selection when no candidate is within tolerance instead of falling back to all candidates.
* 2026 NYSE early-close dates currently listed by NYSE are represented in market-open, minutes-to-close, session chart, intraday-bar, and EOD-chart timing paths.
* `PositionService.monitor_loop()` docstring now matches the 2-second poll interval.

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
| BLOCKER-006 | Resolved in source | Design risk | Live entry uses an advisory lock and risk re-check; migration `008_one_open_trade_per_underlying_day.sql` adds DB-level open-trade uniqueness. |
| HIGH-001 | Resolved | Documentation/behavior mismatch | Owner confirmed consecutive losses are warning-only; config comments now match behavior. |
| HIGH-002 | Mitigated | Data freshness | VIX-based entries now age-gate `$VIX`; live entries also require a recent collector chain snapshot. Broker response timestamp freshness remains unverified. |
| HIGH-003 | Resolved in source | Strategy rule mismatch | VIX center tolerance now blocks when no candidate is within tolerance. |
| HIGH-004 | High | Observability | `/health` is process-only, not DB/broker/data/trading health. |
| HIGH-005 | Resolved in source | Deployment | Deploy workflow now runs pytest, ruff, compose config validation, and SPX health check. |
| HIGH-006 | Mitigated | Config safety | Live enablement now fails closed for non-SPX configs; account confirmation remains config/env owned. |
| MED-001 | Medium | Documentation mismatch | AGENTS/CLAUDE paper-fill description conflicts with ask/bid-based paper code. |
| MED-002 | Medium | Historical data quality | Older trade rows have missing leg symbols: NDX 10, SPX 16, XSP 6. |
| MED-003 | Medium | Backtest parity | Backtest still has separate/default paths that can drift from runtime selection. |
| MED-004 | Resolved for 2026 | Time/calendar | 2026 NYSE early closes currently listed by NYSE are represented; future-year calendars still need annual updates. |
| MED-005 | Medium | Security | Shared `tokens.json` is mounted into all app containers without `:ro`. |
| LOW-001 | Resolved | Documentation | `PositionService.monitor_loop()` docstring now says 2s. |
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
| Stale market data rejection | Partial | Missing quotes, stale VIX, and stale collector chain snapshots block live entry | Broker payload timestamps unavailable | Partial | Mixed | PARTIAL |
| Quote width/quality | Partial | Position drawdown exits for NDX/XSP | Config | Yes | Disabled for SPX | PARTIAL |
| End-of-day handling | Yes | Cash settlement after close | DB | Partial | Depends on valuation fallback | PARTIAL |
| Emergency flatten | Runbook only | `docs/live-runbook.md` | No | No | Manual fail-closed | PARTIAL |
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
* Full Schwab complex-order status mapping beyond known partial-fill fail-closed statuses.
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
* Manual flatten procedure verification.
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
| Duplicate orders are prevented | PASS |
| Partial fills and rejected orders handled safely | PARTIAL |
| Broker positions/orders reconciled at startup and continuously | PARTIAL |
| Unknown broker/app state stops entries | PASS |
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
* BLOCKER-006: Added a same-underlying/same-day PostgreSQL advisory lock around live entry submit and DB insert, with a risk re-check after lock acquisition. Added migration `008_one_open_trade_per_underlying_day.sql` for DB-level uniqueness on one OPEN trade per underlying/date.
* P1 VIX freshness: Added `entry.max_vix_age_seconds` and made VIX-based entries fail closed when `$VIX` is unavailable or stale before the option-chain scan.
* P1 consecutive-loss semantics: Owner confirmed warning-only behavior; config comments now match the existing risk-engine behavior.
* P1 chain freshness: Added live-only collector snapshot age gating before entry.
* P1 deploy gates: Added pytest, ruff, compose config validation, and SPX `/health` check to the deploy workflow.
* P1 runbooks: Added `docs/live-runbook.md` covering startup, session watch, manual flatten, and rollback.
* Partial-fill safety: Known partial-fill statuses now raise a hard unknown-state error and stop entry retries instead of continuing the order ladder.
* Order lifecycle safety: Added `broker_order_intents`, live entry/exit intent writes before submit, immediate broker order ID persistence after Schwab `Location`, and runtime broker-state entry gating.
* Config safety: Live-money mode now refuses non-SPX configs.
* HIGH-003: VIX center-tolerance selection now fails closed when no candidate is near the VIX target; the shared entry-selection fallback no longer bypasses that VIX rule.
* MED-004: Added 2026 NYSE early-close handling for market-open checks, minutes-to-close, Schwab intraday bar windows, position settlement close selection, trade charts, and deferred EOD chart timing.
* LOW-001: Corrected the position monitor docstring from 10s to 2s.

Verification completed:

* `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_order_manager.py tests/test_schwab_client.py tests/test_run_live.py -q` passed: 51 tests.
* `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q` passed: `311 passed in 5.33s`.
* `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_trade_service.py tests/test_config.py -q` passed: 16 tests.
* `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_butterfly_selector.py tests/test_entry_selection.py tests/test_time_utils.py tests/test_trade_chart.py tests/test_position_service_settlement.py -q` passed: 33 tests.
* Focused Ruff check on current touched source/test files passed.
* `/home/billy/.local/bin/graphify update .` completed.

Still left before live-money trading:

* Real Schwab complex-order status observation and full mapping from paper/shadow payloads.
* Restart reconciliation proof drill with real or replayed Schwab paper payloads.
* Health endpoint depth beyond process/startup health.
* Tested runbook drills.
* Account-level live confirmation for expected Schwab account, $20,000 allocation, and $500 daily account loss.

### Before any live order

| Priority | Item | Risk reduction | Affected files/services | Approach | Verification |
|---|---|---|---|---|---|
| P0 | Prove restart reconciliation | Prevent duplicate close or unmanaged open position after restart | `run_live.py`, `OrderIntentQueries`, Schwab paper payloads | Tabletop/replay crash windows for filled entry, filled exit, broker flat, missing fill price, and mismatched legs | Restart drill notes plus focused tests using captured payloads |
| P0 | Full complex-order status mapping | Prevent unsafe behavior on broker edge statuses | `order_manager.py`, Schwab status report script | Observe real Schwab statuses and map partial/cancel/reject/child-order cases | Status-matrix unit tests and paper/shadow evidence |

### Before limited-capital pilot

| Priority | Item | Risk reduction | Affected files/services | Approach | Verification |
|---|---|---|---|---|---|
| P1 | Improve `/health` | Operator safety | `metrics.py`, app services | DB/broker/data/risk readiness checks | Health endpoint tests |
| P1 | Test live runbooks | Operator readiness | docs, operator process | Exercise startup, flatten, outage, EOD, and rollback procedures | Tabletop exercise log |
| P1 | Add account-level live confirmation | Prevent wrong-account or wrong-capital live startup | `run_live.py`, config/env | Verify expected account, allocation, and daily account-loss cap before entries | Startup guard tests |

### Before unattended operation

| Priority | Item | Risk reduction | Affected files/services | Approach | Verification |
|---|---|---|---|---|---|
| P2 | Alerting for exit failures and unknown state | Faster response | monitoring/notifier | Page/actionable alert, not log-only | Alert tests |
| P2 | Future-year calendar maintenance | Time safety | `time_utils.py` | Keep annual holiday/early-close dates current or replace the table with a proven calendar source | Annual calendar tests |
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
