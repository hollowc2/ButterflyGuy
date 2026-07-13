# Butterfly Guy Failure Drills

## Latest offline run

The 2026-07-13 fixture/mock/tabletop run is recorded in
`reports/offline_drills_2026-07-13.md`. It found and fixed retryable ambiguous
entry/exit outcomes plus missing readiness degradation. The full suite passes
with 399 tests. Checklist items remain open where live exit evidence, external
alert delivery, a complete fault matrix, or a flat-runtime drill is still required.

## Master checklist

Evidence means a dated log, redacted fixture, test name/result, or tabletop record. Do not mark a drill complete from code inspection alone.

- [x] Clean XSP live entry payload captured — trade 177, 2026-07-13.
- [ ] Clean XSP closing-order payload or cash-settlement evidence captured and reconciled.
- [ ] Authoritative fill parser fixture drill.
- [ ] Entry crash-window matrix.
- [ ] Exit crash-window and duplicate-close matrix.
- [ ] Restart reconciliation matrix.
- [ ] Synthetic partial-fill/cancel-pending fail-closed drill.
- [ ] Real partial-fill/cancel-pending payload observed under separate approval.
- [ ] Rejected-order drill.
- [ ] Expired-order drill.
- [ ] Broker timeout/ambiguous-submit drill.
- [ ] Broker authentication outage drill.
- [ ] Database outage matrix.
- [ ] Stale chain and stale VIX drill.
- [ ] Missing/invalid leg-quote drill.
- [ ] Missing settlement-evidence drill.
- [ ] Readiness and critical-alert delivery drill.
- [ ] Manual-flatten tabletop and supervised rehearsal.
- [ ] Exact-SHA deployment and rollback drill.
- [ ] Token-expiry recovery tabletop.
- [ ] XSP configuration returned to paper mode and runtime verified.

## Safety rules for every drill

1. Start with unit tests or replayed redacted fixtures. Never create a real failure when a deterministic test proves the same behavior.
2. Do not restart, deploy, stop a database, expire a token, cancel an order, or submit an order while any strategy trade or working order is active.
3. Any broker write requires explicit approval immediately before execution.
4. Repo paper mode simulates fills locally; it cannot produce real Schwab lifecycle payloads.
5. Real payload collection defaults to a supervised, one-contract XSP canary with the configured `$50` daily-loss cap. A quantity-two partial-fill attempt requires the separate risk exception in `partial-fill-test-plan.md`. Return XSP to paper mode afterward.
6. Stop on unknown broker state, mismatched legs, unexpected exposure, missing supervision, or failed alert delivery.
7. Raw payloads stay local and redacted. Never commit account IDs, tokens, or unredacted broker data.

Record for every drill:

- date and operator;
- commit SHA and running image/revision;
- paper, replay, tabletop, or approved live-canary mode;
- initial DB, broker, and service state;
- injected failure and exact boundary;
- observed logs, alerts, DB rows, intents, and broker status;
- pass/fail result; and
- cleanup/reconciliation proof.

## Drill 1: Authoritative fill parsing

Mode: redacted fixture; no broker writes.

1. Replay trade 177's redacted entry payload through the shared fill parser.
2. Assert the execution legs produce the broker net fill rather than the submitted limit.
3. Repeat with a captured closing-order payload when one is available. Cash-settlement evidence does not substitute for a closing-order fill.
4. Remove price, time, execution, and quantity fields one at a time.
5. Add multiple activities and a nested child order.

Pass when valid payloads return one unambiguous price/time/quantity result and every ambiguous payload fails closed.

## Drill 2: Entry crash windows

Mode: mocks plus DB test transaction; no broker writes.

Inject a process failure at each boundary:

1. before intent creation;
2. after intent creation but before submit;
3. after submit with no `Location`/order ID;
4. after broker order ID persistence;
5. after broker fill but before `butterfly_trades` insert; and
6. after trade insert but before risk-state update.

Pass when restart/reconciliation never submits a duplicate entry, repairs only an unambiguous filled intent, and halts every ambiguous case.

## Drill 3: Exit crash windows

Mode: mocks plus DB test transaction; no broker writes.

Inject failure:

1. before exit intent creation;
2. after intent but before submit;
3. after submit with no order ID;
4. after order ID persistence;
5. after broker fill but before DB close;
6. after DB close but before risk update; and
7. during metrics, decision logging, charting, and notification.

Pass when every scenario makes at most one broker exit call, the first close cannot be overwritten, and secondary work can be retried without another order.

## Drill 4: Restart reconciliation matrix

Mode: captured fixtures first; supervised service restart only when broker and DB are flat.

Cover:

- matching open DB trade and broker legs;
- unknown broker position;
- unknown working parent or child order;
- bot-owned working intent;
- filled entry with matching versus mismatched legs;
- filled exit with broker flat versus remaining legs;
- missing fill price/time;
- zero quantity and wrong butterfly ratio; and
- partial or cancel-pending parent/child status.

Pass when only exact, unambiguous states repair automatically and every other state degrades `/ready`, blocks entry, and alerts the operator.

## Drill 5: Partial fill and cancel pending

Run all synthetic status/quantity cases first. The separately approved live-canary procedure is documented in `partial-fill-test-plan.md`.

Pass when the order ladder stops, no replacement order is submitted, the intent retains the raw status, `/ready` degrades, an alert arrives, and the remaining quantity reaches a verified terminal outcome.

Do not repeatedly submit orders trying to manufacture a partial fill. A one-lot parent cannot be partially filled by quantity; any real observation needs quantity two or greater and explicit risk approval.

## Drill 6: Rejected and expired orders

Mode: fixture/mock first.

1. Return `REJECTED` and `EXPIRED` at parent and child levels.
2. Exercise entry and exit ladders plus their top-level orchestration loops.
3. Confirm terminal details persist in `broker_order_intents`.

Pass when one terminal result causes no cancel/resubmit loop, entry stops for the session, exits halt for reconciliation, and the operator receives an actionable alert.

## Drill 7: Broker timeout and ambiguous submit

Mode: mock transport; never create a real network outage.

Cover timeout before acceptance, acceptance followed by lost response, missing `Location`, polling timeout, cancel timeout, and status lookup recovery.

Pass when a possibly accepted write is never blindly retried, intent state becomes unknown, reconciliation searches by durable evidence, and new entries remain blocked.

## Drill 8: Authentication outage

Mode: mock invalid/expired credentials plus tabletop; do not damage the real token.

1. Fail startup authentication.
2. Fail account/order reads during reconciliation.
3. Fail market-data reads during an open-position monitor.
4. Restore authentication and verify recovery order.

Pass when startup or `/ready` fails closed, entries stop, open positions remain visible for manual supervision, alerts arrive, and recovery does not submit an order.

## Drill 9: Database outage matrix

Mode: test database or mocked pool; never stop the production database during a trading session.

Inject failure during intent creation, broker-order-ID persistence, trade insert, peak update, exit close, risk update, decision logging, and settlement.

Pass when no broker write occurs without durable intent, confirmed exits are not repeated, unknown states halt, and recovery reconciles broker truth before resuming.

## Drill 10: Stale or invalid market data

Mode: fixtures/mocks.

Cover stale chain snapshots, stale/missing VIX, stale spot, crossed markets, missing bid/ask, missing one or more butterfly legs, zero/negative prices, and quote timestamps moving backward.

Pass when entry fails closed; monitoring never invents a mark; exits or settlement degrade readiness and alert rather than corrupting trade state.

## Drill 11: Settlement evidence unavailable

Mode: fixture/mock.

1. Fail the final regular-session bar lookup.
2. Allow fallback evidence and verify the correct intrinsic value.
3. Fail both primary and fallback evidence.
4. Restore evidence and replay settlement.

Pass when double failure leaves the trade OPEN, sets `/ready` to `settlement_evidence_unavailable`, stops entry orchestration, alerts the operator, and later settlement closes exactly once.

## Drill 12: Readiness and alerts

Mode: local/runtime-safe fault injection.

Trigger startup, shutdown, broker-reconciliation, settlement-evidence, stale-data, unknown-order, partial-fill, rejected-exit, and DB-failure conditions.

Pass when `/health` continues to represent process liveness, `/ready` returns `503` with the expected reason, and every operator-action condition reaches the configured alert destination once without leaking identifiers.

## Drill 13: Manual flatten

Mode: tabletop first. A supervised rehearsal requires explicit approval and a known position.

1. Disable further entry without destroying evidence.
2. Identify the exact broker legs, quantities, working orders, and DB trade.
3. Cancel only confirmed working orders.
4. Construct the exact closing action in Schwab and require human confirmation.
5. Verify broker flatness before changing local state.
6. Reconcile the intent, trade, risk state, decision log, and alert record.

Pass when two independent views agree on the legs before action, broker flatness is proven afterward, and no automated order resumes during reconciliation.

## Drill 14: Exact-SHA deployment and rollback

Mode: no open positions or working orders.

1. Record the tested commit SHA.
2. Prove the built/running revision matches it.
3. Rebuild only affected services.
4. Verify migrations, `/health`, `/ready`, logs, Schwab authentication, and broker/DB reconciliation.
5. Roll back to the recorded prior SHA and repeat the checks.

Pass when both deploy and rollback preserve exact revision identity, do not restart unrelated live-enabled services, and leave broker/DB state unchanged.

## Drill 15: Token-expiry recovery

Mode: tabletop plus mocked expiry; do not print or modify the real token during the drill.

Cover warning threshold, expired refresh token, failed startup, supervised re-authentication, mounted-file verification, and post-recovery broker reads.

Pass when expiry alerts before the session, all live apps fail closed, recovery verifies the shared mount without exposing secrets, and no service is called ready until Schwab account/order reads succeed.

## Completion gate

Another normal strategy live pilot requires BG-002/BG-003 to be deployed, the simulator/replay portions of drills 1-12 plus drill 14 to pass, and XSP to be verified in paper mode before any separately approved session. A supervised canary whose sole purpose is collecting an otherwise unavailable broker status may proceed only under its specific plan and approval; it does not count as live-readiness promotion. All checklist items, including real broker evidence plus the manual-flatten and token-recovery drills, must pass before unattended operation. Any unknown broker state, duplicate order, missed critical alert, or unreconciled P&L resets the relevant item to incomplete.
