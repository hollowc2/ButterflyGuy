# Butterfly Guy Live-Readiness TODO

Updated: 2026-07-16

## Current gate

Do not restart, deploy, run a broker-write drill, or approve another live pilot
until the database has zero `OPEN` trades, Schwab has no working/unknown orders,
and broker positions reconcile with the database. The 2026-07-14 post-close XSP
restart proof passed with flat DB/broker state; re-check the gate immediately
before every later drill.

All safe local work is complete: BG-002/BG-003, fixture/mock failure matrices,
readiness checks, invalid-quote rejection, settlement replay, manual-flatten and
token-recovery tabletops, and critical-alert routing. Verification: the full
local suite is `434 passed, 1 skipped` (the skipped test requires its isolated
CI TimescaleDB).

The 2026-07-15 hardening pass also made repeated entry failures degrade
readiness with metric/audit evidence and a live Prometheus alert rule, added a
real-Timescale migration/risk-query CI smoke test, and extended the manual
deployment gate/rebuild/readiness checks to SPX, NDX, and XSP. The supervised
external-alert and exact-SHA rollback drills passed on 2026-07-15.

On 2026-07-16 the owner rejected manufacturing a quantity-two partial fill as
unnecessary live risk. Synthetic fail-closed coverage is the readiness gate;
real Schwab partial/cancel-pending evidence is now opportunistic and nonblocking.
The supervised manual-flatten rehearsal passed on a normal one-contract XSP
canary, including post-action DB/risk/audit reconciliation and the paper-mode
XSP recreate.

The XSP 744/748/752 PUT butterfly entry and operator-owned complex close both
filled. Schwab showed all three legs flat and no working XSP order afterward.
The runtime correctly failed closed because the external close had no bot-owned
EXIT intent. After broker evidence was reverified, XSP was stopped, trade `182`
was closed at `$0.07`, XSP realized P&L was updated to `-$26`, and a dedicated
audit event was recorded atomically. XSP was then rebuilt/recreated paper-only;
broker and DB are flat, `/ready` is ready, and restart count is zero.

## Remaining tasks

- [x] **Supervised flat-runtime restart proof.** With broker and DB flat, restart
  only the affected service and prove exact leg/order reconciliation, `/health`,
  `/ready`, migrations, and clean logs without any broker write. Evidence:
  `reports/flat_runtime_restart_2026-07-14.md`.
- [x] **Partial-fill/cancel-pending safety coverage.** Synthetic parent/child
  cases prove that the runtime persists evidence, stops entry, degrades
  readiness, and fails closed. A real broker occurrence cannot be reliably or
  safely manufactured; collect it only if it occurs naturally, following
  `partial-fill-test-plan.md`.
- [x] **Critical external-alert delivery and deduplication.** Alertmanager now
  centrally deduplicates broker ambiguity, reconciliation failure, settlement
  failure, and token-expiry alerts. Eight supervised submissions produced four
  successful Discord deliveries with zero transport failures and no identifiers.
  Evidence: `reports/external_alert_delivery_2026-07-15.md`.
- [x] **Supervised manual-flatten rehearsal.** Follow `docs/live-runbook.md` with
  explicit broker-write approval, two-view leg/order confirmation, broker-flat
  proof, and post-action DB/risk/decision-log reconciliation. The broker action,
  flatness proof, redacted status report, fail-closed readiness response, and
  critical alert passed on 2026-07-16. Trade `182`, risk state, and decision log
  were then reconciled from the verified fill; XSP was rebuilt paper-only and
  passed flat broker/DB, `/health`, `/ready`, restart-count, and log checks.
  Evidence: `reports/xsp_manual_flatten_2026-07-16.md`.
- [x] **Exact-SHA deployment and rollback drill.** The deployment half passed at
  `ce3b785`; the follow-up drill rolled all three paper services back to exact
  SHA `3d25e4a`, repeated the full flat/readiness/migration/log checks, restored
  exact SHA `2a8ca01`, and repeated them again. Evidence:
  `reports/exact_sha_deployment_2026-07-15.md`.

## Safety boundaries

- Any broker write, external test alert, service restart, or deployment requires
  explicit approval immediately before execution.
- Never restart or deploy while a strategy trade or working/unknown broker order
  exists.
- Keep raw broker payloads local and redacted; never print or commit secrets or
  account identifiers.
- Evidence belongs in `reports/`; operational commands remain in
  `docs/live-runbook.md`.
