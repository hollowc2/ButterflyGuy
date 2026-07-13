# Do-Now Live-Safety Gap Plan

## Goal

Close the two remaining high-severity execution gaps, prove them with captured Schwab evidence, and deploy the already-completed safety work before any further live pilot.

## Current hold

As of 2026-07-13, SPX trade 176 and XSP trade 177 are open. Do not restart, rebuild, deploy, or run a broker-write drill until both trades reach a verified terminal outcome. The running apps return `404` for `/ready`, so the checkout's newer readiness behavior is not deployed.

## Implementation status — 2026-07-13 16:40 UTC

Completed in the checkout:

- BG-003 implementation now derives net fills from all broker execution legs and
  activities, validates broker time, requested/filled/remaining quantities, and the
  `1:-2:1` butterfly ratio, and uses the same parser for normal polling,
  post-cancel fills, and restart repair.
- A redacted trade 177 entry fixture reproduces the broker-derived `$0.41` debit;
  the submitted and previously persisted limit was `$0.44`.
- Broker fill price, time, quantities, and redacted evidence now flow into trade
  persistence, P&L, entry metrics, and decision metadata.
- BG-002 implementation makes `close_trade()` update only an `OPEN` row and return
  exact success, marks the broker exit irreversible before secondary work, and
  persists `exit_secondary_work_pending` until risk/metrics/logging/notification
  work completes.
- Verification passed: 100 focused tests, 384 full tests, targeted Ruff, Compose
  rendering, `git diff --check`, and `graphify update .`.

Still undone or blocked:

- Trades 176 and 177 are still `OPEN`; no service was restarted, rebuilt, or
  deployed.
- Trade 177 has no exit order or cash-settlement evidence yet, so the exit fixture
  and full lifecycle reconciliation remain pending.
- XSP is still `paper_trading: false` in both the checkout and running container.
  Restore and restart only after both open trades are terminal and broker state is
  verified safe.
- The full-repo Ruff command still reports 112 pre-existing errors outside the
  changed safety files; targeted Ruff for this implementation passes.
- Deploy, runtime `/ready` proof, and the blocking drills remain pending. The
  safety work was pushed as `65f1b2b`, followed by deployment-gate fix
  `2398b15`. CI passed all 399 tests and intentionally skipped deployment.

## Offline drill update — 2026-07-13 18:43 UTC

The safe fixture/mock/tabletop batch is recorded in
`reports/offline_drills_2026-07-13.md`.

- The drill run found that ambiguous broker outcomes could still be retried by
  sibling entry, exit, post-cancel, monitor, and top-level orchestration paths.
  They now raise one fail-closed ambiguity signal and degrade readiness instead
  of allowing another submission.
- Added negative coverage for missing fill price/executions, remaining quantity,
  cancel-pending parent/child orders, ambiguous entry/exit submission,
  post-cancel status failure, dependency outages, exact DB-close row counts, and
  `/health` versus degraded `/ready` behavior.
- Verification now passes 399 full tests, targeted Ruff, `git diff --check`, and
  `graphify update .`.
- Pushes now validate without deploying. Deployment requires manual workflow
  dispatch and fails closed unless the DB has zero `OPEN` trades and zero
  nonterminal broker intents.
- The blocking-drill checklist remains open where an exit fixture, complete fault
  matrix, external alert delivery, or flat-runtime restart/deploy proof is still
  required. No broker write, restart, deployment, configuration change, or
  external alert was performed.

## Checklist

- [ ] Allow trades 176 and 177 to finish naturally.
- [ ] Save and redact trade 177's entry plus its exit broker payload or cash-settlement evidence. Entry fixture saved; exit evidence pending.
- [ ] Reconcile its broker executions with `broker_order_intents`, `butterfly_trades`, `daily_risk_state`, and `decision_log`. Entry mismatch documented; exit reconciliation pending.
- [ ] Restore `configs/config_xsp.yaml` to `paper_trading: true` after the canary and verify the running XSP service uses it.
- [ ] Complete BG-003: authoritative broker fill evidence. Code and entry fixture complete; exit fixture/live proof pending.
- [x] Complete BG-002: idempotent exit completion.
- [x] Run the focused and full verification gates. Full tests pass; full-repo Ruff has unrelated baseline failures noted above.
- [x] Commit only the intended safety changes; keep generated universe churn separate. Commits `65f1b2b` and `2398b15` are pushed; CI is green and universe/backtest-tool churn remains local.
- [ ] Deploy the exact tested SHA after confirming no open trades or working orders.
- [ ] Verify `/ready`, broker reconciliation, migrations, logs, and DB state in the running containers.
- [ ] Complete the blocking drills in `drill.md` before approving another live pilot.

## Phase 1: Preserve today's evidence

1. After XSP trade 177 closes, run the existing redacted status reporter for 2026-07-13.
2. Keep raw broker payloads local under `reports/`; never commit account identifiers or raw secrets.
3. Create the smallest redacted fixture that preserves:
   - parent and child statuses;
   - order quantity, filled quantity, and remaining quantity;
   - execution-leg instruction, quantity, price, and time;
   - multiple activities/executions if Schwab returns them; and
   - entry versus exit side.
4. Record the reconciliation result. Today's entry already proves the submitted `$0.44` limit differs from the `$0.41` net of the reported execution legs.
5. If the trade cash-settles, preserve the settlement source and broker-flat evidence. That proves settlement, but it does not replace a real closing-order fill fixture.

Done when the fixture can reproduce the broker-derived net fill without reading the live DB or calling Schwab.

## Phase 2: BG-003 — authoritative fills

Status: code complete in the checkout; live acceptance remains blocked on trade
177 exit/cash-settlement evidence and runtime deployment.

Use the existing broker parsing/restart-repair behavior instead of creating a second fill model.

1. Move the minimum reusable parsing logic behind the normal order-polling path.
2. Replace `_wait_for_fill()`'s boolean result with a fill result containing:
   - broker order ID;
   - net fill price;
   - broker execution time;
   - requested, filled, and remaining quantity; and
   - the redacted evidence needed for audit/reconciliation.
3. Derive the net debit/credit from all execution legs and activities with the correct BUY/SELL signs. Do not use the submitted limit as the execution price.
4. Fail closed when a `FILLED` payload has missing time, missing executions, inconsistent leg ratios, or a quantity mismatch.
5. Use the same parser for normal fills, post-cancel fills, and restart repair.
6. Persist the broker result through entry, exit, P&L, daily risk, metrics, and decision logs.

Focused tests:

- captured trade 177 entry fixture and an exit fixture when a closing order is observed;
- price improvement versus submitted limit;
- multiple execution activities;
- nested/child fills;
- missing price or time;
- requested/filled quantity mismatch;
- incorrect butterfly leg ratio;
- post-cancel fill; and
- normal-path/restart-repair equivalence.

Done when the live path never substitutes a submitted limit or local clock for available broker execution evidence.

## Phase 3: BG-002 — idempotent exits

Status: complete in the checkout and covered by focused plus full tests.

1. Make `TradeQueries.close_trade()` update only `status='OPEN'` and return whether it closed exactly one row.
2. Treat a confirmed broker fill as the irreversible boundary: the monitor must never submit another exit for that trade.
3. Mark local exit completion before fallible risk, metric, decision-log, chart, or notification work.
4. Persist secondary-work failures for retry without reopening broker execution.
5. On an already-closed row or ambiguous DB result, reconcile and stop rather than submitting another close.

Focused tests:

- risk-state failure after broker fill produces one exit call;
- DB close succeeds but metrics/notification fails;
- repeated `close_trade()` cannot overwrite the first close;
- DB close returns zero or multiple affected rows;
- restart after exit fill/before DB close; and
- restart after DB close/before risk update.

Done when every failure injected after a broker fill still results in exactly one broker exit submission.

## Phase 4: Verification and deploy

Status: local verification, scoped publication, and push validation are complete
at `2398b15`. Deployment was intentionally skipped and remains blocked by the
two open trades and live XSP mode.

Run, in order:

```bash
uv run pytest tests/test_order_manager.py tests/test_broker_order_intents.py \
  tests/test_position_service_settlement.py tests/test_run_live.py -q
uv run pytest -q
uv run ruff check <changed-python-files>
docker compose -f infra/docker-compose.yml --profile ndx --profile xsp config -q
git diff --check
graphify update .
```

Before deployment:

1. Confirm no OPEN DB trades and no working/unknown broker orders.
2. Confirm XSP is back in paper mode.
3. Commit and test the exact SHA that will be deployed.
4. Rebuild only affected services.

After deployment, require:

- `/health` returns `200` for liveness;
- `/ready` exists and returns the expected market-state-aware result;
- the running image/revision matches the tested SHA;
- migration checksums are accepted;
- Schwab authentication and broker reconciliation succeed;
- no restart loop or unknown broker state appears in logs; and
- DB open trades and broker positions/orders agree.

## Promotion rule

Do not approve another supervised one-contract live pilot until BG-002 and BG-003 are complete, the blocking simulator/replay drills in `drill.md` pass, XSP has been restored to paper mode, and the deployed runtime proves `/ready` and broker/DB reconciliation.
