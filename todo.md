# Butterfly Guy Live-Readiness TODO

Updated: 2026-07-15

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

## Remaining tasks

- [x] **Supervised flat-runtime restart proof.** With broker and DB flat, restart
  only the affected service and prove exact leg/order reconciliation, `/health`,
  `/ready`, migrations, and clean logs without any broker write. Evidence:
  `reports/flat_runtime_restart_2026-07-14.md`.
- [ ] **Real partial-fill/cancel-pending evidence.** Requires separate approval,
  supervision, and the risk exception in `partial-fill-test-plan.md`; retain a
  redacted payload and prove the ladder stops, readiness degrades, and the order
  reaches a verified terminal outcome.
- [x] **Critical external-alert delivery and deduplication.** Alertmanager now
  centrally deduplicates broker ambiguity, reconciliation failure, settlement
  failure, and token-expiry alerts. Eight supervised submissions produced four
  successful Discord deliveries with zero transport failures and no identifiers.
  Evidence: `reports/external_alert_delivery_2026-07-15.md`.
- [ ] **Supervised manual-flatten rehearsal.** Follow `docs/live-runbook.md` with
  explicit broker-write approval, two-view leg/order confirmation, broker-flat
  proof, and post-action DB/risk/decision-log reconciliation.
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
