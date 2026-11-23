# SPX readiness fix evidence

All runtime/broker observations are read-only. The running application was not
changed. This packet does not authorize orders, migration, deployment or restart.

- `before/`: archived probes against the original checkout; both reported defects
  fail, nine other checks pass. `network.json` reports zero network attempts.
- `after/`: JUnit/logs, guarded scenario traces and final local build/graph/lint
  receipts. Test runs overlap; do not add their counts as unique coverage.
- `candidate-release.json`, `image-receipt.json`: exact base/overlay/config hashes
  and the locally built Python 3.12 image's source comparison. No deployment.
- `source-changes.patch`: code/test-only patch, verified to apply cleanly to
  b3150ad75fdc01a7080e6bad42b9445bbc4c3a89. Documentation is delivered separately.
- `runtime-audit*.json`, `ledger-audit.json`, `runtime-services*.json`: timestamped
  sanitized broker, DB and systemd/container observations. No account/order IDs.
- `schema-validation.json`: exact-version scratch migration, schema comparison
  and logical dump/restore. Extra paper tables/indexes are unrelated and preserved.
- `capture-reconciliation.json`: hashes, trade/risk and observation-gap checks
  against the newly copied capture-20261123T175437Z (a partial intraday export).
- `graphify-before-update.tar.gz`: exact graph directory before our AST updates,
  preserving the workspace's pre-existing modified graph output.
- `runtime-and-schema-probes.tar.gz` and `.py.txt`: source bytes of the one-off
  read-only/isolated probes. Read before use; database tests must target only
  disposable infrastructure. Their hardcoded `/tmp`/output names need fresh paths.
- `archived-probes-after.tar.gz`: the original profit/quote/manual/settlement probes
  with output redirected and input set to the newer capture. Extract to scratch
  and redirect OUT again before rerunning; never overwrite earlier evidence.

The old exit-alert probe expects inline delivery from the monitor. The new design
queues delivery atomically and runs it independently, so its old immediate-call
expectation is superseded, not declared successful. Normal regressions are
`tests/test_exit_notifications.py`, `tests/test_paper_fee_units.py`,
`tests/test_spx_rehearsal_regressions.py`, and
`tests/integration/test_exit_notifications_db.py`.

For PostgreSQL tests create a new scratch **database for each full suite run**.
Some existing smoke tests intentionally seed their CI_DATABASE_URL database and
expect it initially empty. One retained intermediate rerun reused that DB and
failed with -$500 rather than -$250; the final run uses a new database. Never set
CI_DATABASE_URL to a live, production, regular-paper or active rehearsal DB.

The original verification-20261123T1640Z packet was not overwritten; all 28 hashes
in its manifest were checked again. The scheduled 21:10/21:15/21:20 UTC jobs had
not executed during this investigation. Read actual later results before closing
the end-of-day readiness gate. `deliberate_closeout_verified` alone is insufficient.
