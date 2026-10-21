# Persistent collector phases (development only)

SPX launch remains NO-GO. Deploy nothing as part of this investigation.

The runtime's two-second phase delay is a startup delay. SPX subsequently aligns
its collector to a minute grid, whereas NDX/XSP used sleep-after-pass loops and
therefore drifted with execution time. Startup phasing does not establish stable
ongoing staggering. Use the existing minute-grid implementation for NDX at +2s
and XSP at +4s; retain SPX at +0s and each 60-second sampling cadence. These small
phases separate ordinary ~1.3s modeled collector bursts without using large parts
of the minute's freshness allowance. Missed ticks are skipped, never caught up.
Open/close checks and all freshness/risk/entry/position-monitor settings are retained.
Aligned timed snapshots use the existing chain-first path. This intentionally makes
NDX/XSP chain timing match SPX; no strategy or entry logic changes.

`uv run pytest tests/test_collector_phase_replay.py -q -s` reproduces a diagnostic
single-slot FIFO model with three simultaneous collectors (spot .55s, chain .35s,
history .4s) and three .2s monitors every two seconds for ten minutes. These are
synthetic durations, not fitted October 21 traces. Baseline/candidate: 990 upstream
attempts each; queue p95 2.9/1.5s, end-to-end p95 3.35/1.7s, maximum 4.5/1.9s.
Monitor arrival times are identical. Collector ticks remain 60s apart. Candidate
still fails the 1s target in this deliberately burst-heavy model; this is evidence
for reducing collision risk, not a production improvement or acceptance proof.
History is modeled on every tick as a conservative burst, though daily warmup work
is not generally repeated at that frequency. No cache or TTL benefit is assumed.

Collector request keys are predominantly different underlyings; VIX collection is
already SPX-only, and gateway option-chain reads already single-flight and cache.
Broad new single-flight machinery is therefore deferred: no measured duplicate
spot/history/quote volume justifies its cancellation and priority complexity.

Future approved rollout: gateway metrics first; separately deploy the exact
consumer image one paper service at a time using retained-image rollback procedures.
Validate distinct recurring collector phases, fresh snapshots, unchanged two-second
monitor cadence, entry-halt monitoring and zero new failures across a full session.
Do not touch the frozen prospective-v2 checkout or its updater. Roll back only the
affected service to its recorded image if freshness or monitoring regresses.


Validation: full suite 1,366 passed, 37 skipped (30 need NDX_POSTGRES_BIN,
six need private NDX snapshots, one needs CI_DATABASE_URL). The isolated local
TimescaleDB migration/risk-read smoke separately passed with synthetic test data.
Ruff, actual base Compose rendering and the paper overlay render passed. Overlay
rendering used --no-env-resolution and synthetic inputs; production env files were
not accessed. Graph refresh is a separate commit; SQL extraction was unavailable
because tree_sitter_sql is not installed. No real-provider validation was performed.

The paper cutover overlay bind-mounts configs from /opt/butterflyguy/configs;
a replacement image alone will not activate these settings. A future approved
rollout must record and back up each service's actual mounted config, verify it
is the mutable paper config rather than the frozen prospective-v2 path, stage the
reviewed two collector fields, and recreate only that named paper service using
its exact approved image and existing guards. Validate the recurring phase before
the next service. Rollback restores that service's config bytes and retained image;
never replace the shared config directory or frozen checkout. The historical
cutover runbook documents database/broker flatness gates; use a newly recorded
baseline rather than its historical image IDs.
