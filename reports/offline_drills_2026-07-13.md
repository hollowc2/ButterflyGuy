# Offline safety-drill record — 2026-07-13

- Operator: Codex, supervised by repository owner
- Base commit: `d112dcba0a71b5090cf574d08aa7a19ff6eee7c0`
- Mode: redacted fixture, mocks, and tabletop only
- Initial state: SPX trade 176 and XSP trade 177 were `OPEN`; XSP had one
  `FILLED` entry intent and no exit intent; deployed `/health` returned `200`
  while `/ready` returned `404`.
- Safety boundary: no broker write, cancel, restart, deploy, configuration change,
  credential change, or external alert was attempted.

## Result

| Drill | Offline result | Evidence or remaining gap |
|---|---|---|
| 1. Authoritative fill parsing | Partial pass | Captured trade 177 entry reproduces `$0.41`; multiple activities/children and missing price, time, executions, quantities, and ratio fail closed. Closing-order fixture remains unavailable. |
| 2. Entry crash windows | Partial pass | Intent-before-submit, missing `Location`, ambiguous submit, and unsafe top-level stop pass. Direct fault injection after fill/before trade insert and after trade insert/before risk update remains. |
| 3. Exit crash windows | Partial pass | Exit fill is irreversible, DB close is one-shot for `UPDATE 1/0/2`, secondary-work failure cannot resubmit, and restart repair requires one exact OPEN close. Remaining boundaries need a single explicit matrix record. |
| 4. Restart reconciliation | Partial pass | Exact legs, wrong ratios, missing/extra legs, unknown orders, filled-entry repair, filled-exit repair, and unsafe readiness pass. A supervised process restart remains blocked while trades are open. |
| 5. Partial/cancel-pending | Partial pass | Parent and child `PARTIALLY_FILLED` and `CANCEL_PENDING` stop entry/reconciliation and degrade readiness. External alert delivery and verified terminal cleanup remain. |
| 6. Rejected/expired | Partial pass | Entry and exit ladders stop after one submit, child rejection is detected, intent status is retained, and entry orchestration stops. External alert delivery remains. |
| 7. Timeout/ambiguous submit | Partial pass | Missing `Location`, ambiguous entry/exit submit, and failed post-cancel status verification stop without resubmission and retain an unsafe intent. The full timeout/cancel recovery matrix remains. |
| 8. Authentication outage | Partial pass | Reconciler broker-read failure degrades readiness. Startup authentication, open-monitor data-read failure, recovery ordering, and alert delivery remain. |
| 9. Database outage | Partial pass | Reconciler DB failure degrades readiness; confirmed-exit secondary-work failure remains one-shot. Intent creation, order-ID persistence, entry insert, peak, and settlement injection remain. |
| 10. Stale/invalid market data | Partial pass | Stale chain, stale VIX, missing strikes, nonpositive marks, and missing settlement evidence fail closed. Stale spot, crossed quotes, negative leg quotes, and backward timestamps remain. |
| 11. Missing settlement evidence | Partial pass | Loss of both valuation sources leaves the trade OPEN and sets `/ready` reason `settlement_evidence_unavailable`. Restored-evidence replay remains. |
| 12. Readiness and alerts | Partial pass | `/health` remains `200`; `/ready` becomes `503` for broker-order, reconciliation, dependency, and settlement failures. No external alert was sent, so delivery/deduplication remains. |
| 13. Manual flatten | Tabletop only | Procedure requires entry disable, two-view leg/order agreement, human-confirmed close, broker-flat proof, then local reconciliation. Supervised rehearsal remains blocked. |
| 14. Exact-SHA deploy/rollback | Blocked | Requires no OPEN trades or working orders. |
| 15. Token-expiry recovery | Tabletop only | Existing keepalive warns before expiry; reauthentication requires the owner/browser; mounted-token verification and broker reads must precede readiness. Mocked expiry and alert delivery remain. |

## Drill findings fixed

1. Ambiguous broker outcomes were retryable in sibling paths. `AmbiguousOrderError`
   now stops entry, exit, post-cancel verification, monitor orchestration, and the
   top-level entry loop instead of allowing another order submission.
2. Unsafe order failures stopped work but did not immediately degrade readiness.
   They now set `broker_order_state_unsafe`.
3. The fill parser drill added missing negative cases for price, execution
   collection, remaining quantity, and cancel-pending parent/child states.

## Verification

- Safety-focused suite: `111 passed` before the final additions.
- Ambiguous-order slice: `8 passed`.
- Dependency/readiness slice: `34 passed`.
- Full suite: `399 passed`, one third-party `websockets.legacy` deprecation warning.
- Changed-file Ruff: passed.
- `git diff --check`: passed.
- `graphify update .`: rebuilt the code graph without an API call.

## Remaining do-now work

The remaining mock-only work is the explicit entry/exit/DB fault-injection matrix,
restored-settlement replay, invalid-quote/timestamp cases, and mocked token expiry.
External alert delivery requires separate approval because it sends messages.
Runtime and real-broker work remain blocked whenever any strategy trade is open
or broker/DB state is not reconciled.

## Follow-up — 2026-07-14

- Trade 177 is `CLOSED`; retained Schwab expiration transactions reconcile its
  `$3.47` cash settlement and `$303.35` net realized P&L.
- The focused safety suite passed `140` tests after adding one shared
  fail-closed check for negative or crossed option-leg quotes.
- Existing executed regressions now satisfy the fixture/mock portions of the
  authoritative-fill, exit idempotency, restart reconciliation,
  partial/cancel-pending, rejected/expired, ambiguous-submit, readiness, and
  settlement drills.
- The manual-flatten and token-recovery tabletops are now recorded in
  `docs/live-runbook.md`.
- The full suite passes `417` tests; targeted Ruff, `git diff --check`, and
  `graphify update .` pass.
- Direct fault injection now proves that DB insert, intent-link, and risk-state
  failures after a broker entry fill raise one reconciliation stop and release
  the entry lock without another submission.
- Durable-intent DB failures now prove no entry or exit broker write occurs;
  peak persistence cannot reach exit submission; cash-settlement close failure
  makes exactly one DB attempt; startup/runtime authentication failures fail
  closed.
- The real keepalive script passes mocked near-expiry and expired-token cases
  using only an in-memory synthetic token, fake clock, fake broker response, and
  fake Telegram sender.
- Still open: external alert delivery, real partial-fill observation,
  supervised flatten/restart, and exact-SHA deploy/rollback.
