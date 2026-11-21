# Codex review handoff: concurrent paper/live SPX review fixes

- **PR:** #103, branch `fix/spx-live-review-20261120`, against `main` at `33062cb`.
- **Asked of you:** a read-only code review before merge. Report findings; do not push to
  this branch, merge, deploy, restart services, call Schwab write APIs, touch secrets, or
  change trading limits or paper/live settings.
- **Read first:** `AGENTS.md` (authoritative), then `deploy/spx-live/README.md` and
  `docs/operations/concurrent-paper-live-spx-design.md` for the session scripts.

## Why this PR exists

A read-only review of the concurrent paper/live SPX feature on 2026-11-20 found six missing
failure combinations (no existing test failed). PR #101 (merged `fe051d6`) holds the
2026-11-19 live-halt hardening. It must stay intact; please flag anything here that weakens it.
The real-money context: one 0DTE SPX fly a day, max debit 4.00, the bot runs beside paper in
its own container (`butterfly_spx_live_app`) with `restart: on-failure:3`.

The guiding rule for every fix: **a position the bot may hold must never be left unmanaged
because of a non-critical failure, and a failure must never leave uncontrolled new entries
enabled.** Critical fill persistence still fails closed (halt, restart, startup reconcile).

## The six fixes, where to look, and what to challenge

### 1. P1: post-fill audit failure strands a confirmed fill
`src/butterfly_guy/services/trade_service.py:633-730`

Before: after the fill was persisted, an exception from `trade_entered` /
`entry_ladder_trace` `log_event` escaped `attempt_entry`. `entry_loop` treated it as a
generic, retryable error and never started the monitor; reconciliation then accepted the
broker/DB match, so the fly was open and unmonitored.

Now: `TradeRecord` is built immediately after the persistence block (line 636). After that,
the entry-lock release, the Prometheus metrics block, and each audit event are wrapped and
log at error (`entry_lock_release_failed_after_fill`, `entry_metrics_failed_after_fill`,
`post_fill_audit_failed`). The persistence block (`insert_trade`, `link_trade`,
`record_trade`) is unchanged and still raises `AmbiguousOrderError`.

Challenge:
- Is anything else on the path from persistence to `return record, best` able to raise?
  (Payload construction such as `fill["fill_time"].isoformat()` is inside the try.)
- Is a failed advisory-lock release after a fill acceptable to log only? The connection is
  still released in `_release_entry_lock`'s `finally`; a session advisory lock dies with the
  pooled connection's reset. Confirm against asyncpg's pool reset behavior.
- A `CancelledError` (SIGTERM) during these awaits still drops the record; restart recovery
  owns that case. Agree?

### 2. P1: activation rollback stopped an open position's manager
`deploy/spx-live/activate.sh:47-70`, `src/butterfly_guy/scripts/spx_live_db.py:257` (`halt_entries`), `:349`, `:398`

Before: a failed post-start verification (120 s after `compose up`, orders enabled) always
called `stop_live`, even if a fly had filled in the meantime.

Now, on failed verification:
1. `db_tool halt-entries --date "$DATE"`: an upsert setting `daily_risk_state.halted = TRUE`
   for SPX on the live DB only (`target_name` refuses the paper DB). `RiskEngine.can_trade`
   reads it before every entry; exits and settlement never read it. Every writer of the flag
   only ORs it true, so nothing clears it that day.
2. `broker_flat --ignore-expired && db_tool check`: same flatness predicate as `stop-live.sh`.
   If both pass, `stop_live` as before.
3. Otherwise (not flat, or a check errored, e.g. auth): leave live running, touch
   `VERIFY_FAILED`, and post a 🚨 alert that says whether the entry halt succeeded.

`health.sh:16` now also runs when `VERIFY_FAILED` exists, so an unverified bot left managing
a fly is watched (repeat alerts on a dead/halted bot with an open DB trade).

Challenge:
- **Race:** an entry that passed `can_trade` (under the entry lock) just before the halt but
  has not yet created its order intent when the flatness check runs looks flat and gets
  stopped mid-submit. The broker check runs before the DB check, so anything past intent
  creation is caught. Is the remaining window acceptable, or is there an existing mechanism
  (the entry advisory lock?) the script should wait on?
- **Halt fails and not flat:** the bot stays up with entries possibly enabled. Today that is
  bounded by `RISK__MAX_TRADES_PER_DAY=1` (verified env) and the bot holding its open trade,
  and is alerted. If verification failed *because* the env is wrong, that bound may not
  hold. Is keeping management the right trade-off versus stopping?
- Is a new DB write subcommand justified, versus an existing mechanism? (OBSERVE mode needs a
  recreate, which would stop management.) It sets `halted` but not `max_loss_hit`
  (`set_halted` sets both); nothing outside `db/queries.py` reads `max_loss_hit` today.
- **Deploy dependency:** `db_tool` runs in the release image `$CAND`. Updated scripts with an
  older image make `halt-entries` fail (argparse error), which is reported as "entry halt
  FAILED", and the flatness check still decides. Should activation gate on this up front?

### 3. P1: restart forgot permanent operator exit ownership
`src/butterfly_guy/services/position_service.py:435-462`, `:780-786`, `:1546-1590`;
`src/butterfly_guy/scripts/run_live.py:269` (`_recovered_trade_record`), `:1349`;
`src/butterfly_guy/data/schemas.py:94` (`TradeRecord.operator_exit`)

Before: `operator_exit` was a local in `_monitor_loop`. After a takeover, the operator
cancelled their order, the bot crashed/restarted, reconciliation passed, and bot exits
resumed, contradicting the "no more exit orders for this trade" notification.

Now: both takeover triggers (a Schwab order/leg change seen by `_manual_close_fill`, and
`OperatorExitTakeoverError` from the exit ladder) go through `_announce_operator_exit`,
which first persists `metadata.operator_exit = {reason, handed_at}` via `merge_metadata`,
then logs and notifies. Startup restores it into `TradeRecord.operator_exit`, and
`_monitor_loop` starts with `operator_exit = trade.operator_exit`. If the write fails, the
in-memory handoff holds, the write is retried at the top of every poll, and the notification
warns that a restart before it saves would resume bot exits. Nothing releases ownership.

Challenge:
- Is there any automated exit path outside `_monitor_loop` that should also honor the flag?
  (I found none: the reconcilers never place orders; settlement is not an order.)
- Persist-before-notify ordering, and retry-forever on failure. Should a persistently
  failing write also set readiness or a critical alert?
- `manual_exit_signal` (the first suppressed bot signal) is not persisted, so after a
  restart the close metadata records the first signal seen after the restart. Acceptable?
- `_recovered_trade_record` uses `_json_dict(row["metadata"])`, so malformed metadata JSON
  would crash startup. Postgres `jsonb` should make that impossible.

### 4. P2: failed stop permanently suppressed session health
`deploy/spx-live/common.sh:240-249` (`stop_live`)

`STOPPED` is now written only after `running "$LIVE_C"` reports 0. A dry run still prints the
touch and writes nothing. Known side effect: a health run landing between a confirmed stop and
the touch can post one spurious "not running" alert. Check that `closeout.sh` and
`stop-live.sh` still behave (both call `stop_live` and branch on its status).

### 5. P2: position monitor outlived its supervisor during shutdown
`src/butterfly_guy/scripts/run_live.py:864-999` (`entry_loop`; the diff is mostly
re-indentation, so use `git diff -w`)

The monitor is created with `asyncio.create_task` outside `main()`'s TaskGroup. `entry_loop`'s
body is now in `try/finally`; the `finally` cancels a still-running monitor and
`await asyncio.wait([monitor_task])` before returning, so SIGTERM (via
`install_shutdown_handler`) or a sibling task failure stops the monitor before
`_close_runtime_resources` closes the broker client and DB.

Challenge:
- `asyncio.wait` does not re-raise the monitor's exception or cancellation, and does
  propagate a second cancel of `entry_loop`. Is that the right primitive?
- Monitor failure propagation (`LiveTradingHaltedError`, critical alerts) runs in the loop
  body before the `finally`, where the monitor is already done. Confirm nothing double-fires.
- **Not fixed:** `PositionService._post_exit_task` (post-exit leg-quote recording) and the
  `_background_tasks` (pending-exit metadata) can still run during resource cleanup. They only
  record and never place orders. Worth a follow-up?
- Cancelling a monitor mid-`execute_exit` happened before too (at `asyncio.run` teardown,
  after the DB had closed). Now it happens earlier. Restart reconciliation of in-flight exit
  intents (PR #101) handles it. Agree?

### 6. P2: paired report counted settlement fees as execution cost
`src/butterfly_guy/reports/spx_paired.py:129-141`, `:186`, `:337`

Live cash settlements (bot, provisional, finalized true-up, and the
`tools/spx_live_settle_expired.py` settle tool) store Schwab's net P&L, fees included.
Ordinary exits and manual closes store `exit_price - entry_price`. On every path `exit_price`
is the fill or settlement value, so for non-paper rows the report now uses
`exit_price - entry_price` as before-fee P&L, and reports `live_fees_in_db_pnl_usd` =
before-fee minus stored. Paper rows (`paper_fill_model`) keep the existing fee back-out.
`gross_pnl_dollars` metadata is deliberately not used: a finalized true-up leaves the
provisional's value stale.

Challenge: `finalize_provisional_settlement` (`db/queries.py:346`) sets `exit_price` to the
posted settlement value in the same statement as `pnl`. Confirm no other writer changes `pnl`
without `exit_price`. Is 0.00 on ordinary exits clear enough, given that Schwab exit
commissions exist but are not in the DB?

## Tests

New or changed (each fails against `33062cb` source except the controls noted):

| File | Tests |
|---|---|
| `tests/test_trade_service.py` | `test_post_fill_telemetry_failure_still_hands_the_trade_to_the_monitor[trade_entered, entry_ladder_trace, lock_release, metrics]`; `test_post_fill_audit_failure_starts_the_position_monitor` (real `TradeService` into `entry_loop`); the existing persistence-failure test now uses the shared `_filled_live_entry` helper (control, unchanged assertions) |
| `tests/test_spx_live_test.py` | `test_operator_exit_ownership_survives_a_restart[operator_order, ladder_takeover]` (persisted metadata, then the DB row, then `_recovered_trade_record`, then a second monitor: zero exits); `test_restored_operator_exit_still_adopts_the_manual_fill`; `test_recovered_trade_without_a_handoff_keeps_bot_exits`; `test_unsaved_operator_exit_is_retried_and_flagged_without_releasing_it` |
| `tests/test_run_live.py` | `test_sigterm_stops_a_recovered_monitor_before_resource_cleanup`; `test_sibling_failure_stops_a_new_trade_monitor_and_still_propagates`; **rewrote** `test_entry_loop_registers_recovered_monitor_for_reconciler` (its Mock task with `done() == False` can never finish, so it hung once `entry_loop` waits for its monitor; it now uses a real task and also asserts the monitor is gone after its supervisor exits) |
| `tests/test_spx_live_scripts.py` | fake docker gained `after_up` (state applied on `compose up`) and `halt_rc`; `test_failed_verification_halts_entries_before_stopping_a_flat_bot`; `test_failed_verification_keeps_managing_a_fly_that_filled_meanwhile[broker, db, both]` (includes a follow-up `health.sh` alert); `test_failed_entry_halt_is_reported_and_a_held_fly_stays_managed`; `test_failed_entry_halt_on_a_flat_bot_still_stops_it` (control); `test_failed_stop_keeps_health_monitoring_on`; `test_dry_run_stop_records_no_deliberate_stop` (control) |
| `tests/test_spx_paired_report.py` | `test_live_settlement_fees_are_not_counted_as_fill_cost[settle_tool, provisional, finalized]` (synthetic copy of trade 100000: −375.00 before fees, 4.79 fees, −3.00 fill cost); `test_live_exit_fill_pnl_is_unchanged_and_shows_no_db_fees`; `test_paper_rows_never_report_live_db_fees` |
| `tests/integration/test_spx_live_db.py` | `test_halt_entries_blocks_the_risk_gate_and_keeps_the_day_counters` (real DB; real `RiskEngine.can_trade` returns `trading_halted`; restart syncs don't clear it); `test_halt_entries_refuses_the_paper_database` (no DB; stubs `load_config` so the real `.env` is never loaded) |

Results on the author's machine:
- Full suite: 2166 passed, 50 skipped (3 min 39 s). `uv run ruff check .`: clean.
- All of `tests/integration` (25) passed against a disposable local
  `timescale/timescaledb:2.30.1-pg16` (CI's image and credentials), never production.
  `test_database_smoke` is not idempotent: a second run on the same database fails on
  doubled seed rows. Use a fresh database.
- `graphify update .` was run with `uvx --from graphifyy==0.9.105` (the version in
  `.graphify_build_state.json`); the `graphify-out/` churn in the diff is from that.

To reproduce:

```bash
uv run pytest -q tests/test_trade_service.py tests/test_spx_live_test.py tests/test_run_live.py \
  tests/test_spx_live_scripts.py tests/test_spx_paired_report.py tests/test_live_incident_replay.py \
  tests/test_position_monitoring.py tests/test_spx_live_settle_expired.py
uv run pytest -q && uv run ruff check .
# Real DB only against a throwaway database:
CI_DATABASE_URL=postgresql://butterfly:butterfly@127.0.0.1:<port>/butterfly_guy uv run pytest -q tests/integration
```

The original reproduction scripts (not committed) were
`/tmp/test_live_spx_postfill_audit_gap.py`, `/tmp/butterfly_takeover_restart_repro.py`,
`/tmp/test_live_spx_monitor_shutdown_review.py` and `/tmp/test_spx_live_ops_review.py`. The
first three assert the old unsafe behavior and now fail as intended; the last now passes.
The takeover script still prints 3 exits because it hand-builds a fresh `TradeRecord` and
bypasses the startup restore; the committed restart test goes through the real path.

## What to send back

- Findings ranked by severity, each with file:line and a concrete failure scenario.
- An explicit verdict on the two judgment calls: (a) finding 2's keep-running-when-uncertain
  policy and its residual races; (b) finding 3's retry-forever persistence.
- Anything that weakens the PR #101 halt/reconcile behavior.
- Whether this is ready to merge, and anything that must happen before the next live session
  (at least: a release image containing `halt-entries`, and Helios checkout/config drift per
  `docs/operations`).

Operational context only, out of scope here: Helios's live container was stopped during the
review; 2026-11-23 is configured `OBSERVE=1`. The generic target-down alert rule excludes
live. Do not change monitoring config or scheduled sessions.
