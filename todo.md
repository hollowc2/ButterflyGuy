# Butterfly Guy Live-Readiness TODO

Updated: 2026-07-14

## Current gate

Do not restart, deploy, run a broker-write drill, or approve another live pilot
until the database has zero `OPEN` trades, Schwab has no working/unknown orders,
and broker positions reconcile with the database. The 2026-07-14 post-close XSP
restart proof passed with flat DB/broker state; re-check the gate immediately
before every later drill.

All safe local work is complete: BG-002/BG-003, fixture/mock failure matrices,
readiness checks, invalid-quote rejection, settlement replay, manual-flatten and
token-recovery tabletops, and synthetic token-expiry coverage. Verification:
`140` focused safety tests and `417` full tests pass.

## Remaining tasks

- [x] **Supervised flat-runtime restart proof.** With broker and DB flat, restart
  only the affected service and prove exact leg/order reconciliation, `/health`,
  `/ready`, migrations, and clean logs without any broker write. Evidence:
  `reports/flat_runtime_restart_2026-07-14.md`.
- [ ] **Real partial-fill/cancel-pending evidence.** Requires separate approval,
  supervision, and the risk exception in `partial-fill-test-plan.md`; retain a
  redacted payload and prove the ladder stops, readiness degrades, and the order
  reaches a verified terminal outcome.
- [ ] **Critical external-alert delivery and deduplication.** Send approved test
  alerts for broker ambiguity, reconciliation failure, settlement failure, and
  token expiry; prove each actionable condition arrives once without identifiers.
- [ ] **Supervised manual-flatten rehearsal.** Follow `docs/live-runbook.md` with
  explicit broker-write approval, two-view leg/order confirmation, broker-flat
  proof, and post-action DB/risk/decision-log reconciliation.
- [ ] **Exact-SHA deployment and rollback drill.** Deploy only from a flat state,
  prove the running revision and migrations, verify broker/DB reconciliation,
  `/health`, `/ready`, and logs, then roll back and repeat the same checks.

## Safety boundaries

- Any broker write, external test alert, service restart, or deployment requires
  explicit approval immediately before execution.
- Never restart or deploy while a strategy trade or working/unknown broker order
  exists.
- Keep raw broker payloads local and redacted; never print or commit secrets or
  account identifiers.
- Evidence belongs in `reports/`; operational commands remain in
  `docs/live-runbook.md`.
