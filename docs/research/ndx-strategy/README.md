# NDX-01 reproducible baseline

The reference is **NDX-R0-baseline-approximation-v1**, using snapshot
**ndx-r0-20261014**, not a claim of complete runtime parity. No exit variants are
rerun. The authoritative decision and next action remain in
[the living plan](../ndx-strategy-development.md).

The bounded **NDX-02 execution/accounting audit** is now available separately:
[findings and execution model](NDX-02-execution-accounting.md),
[offline command](NDX-02-reproduction.md). It preserves the NDX-01 reference and
does not complete liquidity calibration or validate continuation paths.

The subsequent [continuation import/cadence audit](NDX-02-continuation.md) now
preserves the independent minute observations in a separate snapshot. Both R0
and minute-replay eligibility remain false; see its
[offline command](NDX-02-continuation-reproduction.md).

[Reconciliation and evidence audit](NDX-01-reconciliation.md) explains the source
identities, trade 222, accounting, coverage and remaining limitations. The
[final contract](evidence/2026-10-15/r0-reproduction-final.json) defines eligibility
and numerical/timing tolerances before replay. The earlier contracts and failed
attempt record are historical; use the final contract for new reproductions.

## Evidence and recovery

The original bundle is unchanged:
`/mnt/Repos/Trading/Butterflyguy/reports/research/ndx-review-2026-10-14/`.
All 29 historical final-file checksums and all 15 input checksums passed before
copying. The historical manifest does not hash itself; the new snapshot does.

Persistent, Git-ignored storage on Eros-backed NFS:

- `/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014/` — `raw/` is an
  exact copy of the whole original bundle. `starting-state/`, the tracked patch
  and status preserve existing source/config/docs and generated graph work.
  [Snapshot manifest](evidence/2026-10-15/snapshot.json): 347 verified files;
  manifest SHA-256 `0599bbd58ea30246c3329113b12b00ca7ac36a0f4944ef7dd8ab785aac114967`.
- `/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015/` —
  read-only DB identity, settlement timestamps and trade-222 state transitions;
  [manifest](evidence/2026-10-15/supplement-manifest.json). This is an attributed
  supplement, never a replacement for the original quotes.
- `/mnt/Repos/Trading/Butterflyguy/evidence/ndx/helios-ndx-source-20261015/` —
  selected current container source/config/lock files and host file hashes;
  [manifest](evidence/2026-10-15/runtime-source-manifest.json). This observes
  October 15 runtime identity, not all historical deployments.
- `/mnt/Repos/Trading/Butterflyguy/reports/research/ndx-01-20261015/run-03/` —
  final reproduction, coverage, accounting audit, environment and runner copies.
  Runs 01 and 02 remain preserved with their own contracts and source copies.
- `/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx01-final-handoff-20261015/` —
  verified final new source/tests/documentation and run-03 copy, for recovery of
  these proposed changes before they are committed. It references the original
  snapshot rather than duplicating raw quotes again.

Protection is **two copies on the same NFS filesystem**, plus verification and
application-level overwrite refusal. The owner accepted Eros retention in this
session. Neither independent backup, ZFS snapshot retention, storage replication,
nor off-site recovery was verified. File permissions do not prevent the owner
from editing these files. Gitignore provides no backup or access control.

To restore elsewhere, use `shutil.copytree(source, destination)` with a **new**
destination; it refuses an existing destination. Copy each named snapshot with
its manifest, preserving relative paths. Run verification below against the
restored roots and the versioned manifests. A restore to `/tmp` and replay can
check usability but does not create durable independent backup protection.
If Eros is lost, no independent recovery source is established. The original
Helios database may permit a new extraction; a later extraction is a new snapshot,
not a guaranteed byte-identical recovery of R0. Missing event/availability times
cannot be reconstructed by rerunning SQL.

## Offline reproduction

From a checkout containing these changes, install the checked-in dependencies
once with `uv sync --frozen`. No pandas dependency or historical script execution
is needed. A provisioned environment then uses only local files:

```bash
uv run --offline --frozen python -m butterfly_guy.research.ndx_evidence verify \
  --evidence evidence/ndx/ndx-r0-20261014 \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/snapshot.json

uv run --offline --frozen python -m butterfly_guy.research.ndx_baseline \
  --evidence evidence/ndx/ndx-r0-20261014 \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/snapshot.json \
  --config docs/research/ndx-strategy/evidence/2026-10-15/r0-reproduction-final.json \
  --supplement evidence/ndx/ndx-01-supplement-20261015 \
  --supplement-manifest docs/research/ndx-strategy/evidence/2026-10-15/supplement-manifest.json \
  --output reports/research/ndx-01-20261015/my-new-reproduction
```

Choose a new output path every time. Both evidence roots may be absolute paths
outside the checkout. The named snapshot is private and is **not included by a
Git clone**. A missing/mismatched file, changed pinned source, or existing output
fails rather than silently using a different input or rewriting an earlier run.
For changed mechanics, register a **new contract and parent run**, retain its
source and outputs, and explain the differences. Never relabel the R0 outputs.

`ndx_evidence` performs checksum verification; `normalize` in `ndx_baseline`
rejects duplicate observations and excludes incomplete groups; `replay` handles
only the fixed-entry baseline; coverage, accounting and metrics functions produce
separate outputs. The offline path executes no extraction, network/broker call,
or credential loading. It invokes local Git solely for run identity.

Each run records the exact invocation, Python/platform/package versions,
source/lock/config/input identities, resolved profit settings, parent and output
hashes. Source pins include the whole starting Python source tree, dependencies,
new runner modules and focused tests. The run also preserves the runner source.
The pinned lock and observed environment identify the new reproduction; the
original study did not preserve a complete historical package environment.

## Extraction is separate

The versioned [SQL directory](sql/) preserves historical R0 queries and the new
provenance/inventory queries. Extraction requires explicit invocation and a new
output directory. It reads only the requested fixed historical range; a changed
query/range must be retained under a new snapshot identity.

```bash
uv run python -m butterfly_guy.research.ndx_evidence extract \
  --query docs/research/ndx-strategy/sql/supplement.sql \
  --output evidence/ndx/my-new-provenance-export
```

This uses read-only transactions through SSH/psql on Helios and touches no runtime
configuration or orders. It is not required for offline reproduction. Do not run
historical `extract.py`, `extract_quotes.py`, `replay.py`, `describe.py` or
`build_report.py` against the original directory: they rewrite outputs and some
fall back to `/tmp` scripts. They remain immutable historical evidence.

## Coverage and validation outputs

Versioned small derivatives are under [2026-10-15](evidence/2026-10-15/):

- [sessions.jsonl](evidence/2026-10-15/sessions.jsonl): every exchange weekday in
  the March 30–October 14 export range, including sessions with no trade in the
  export. No-trade/unknown opportunity evidence is not a zero-P&L observation.
- [coverage.jsonl](evidence/2026-10-15/coverage.jsonl): every trade's identity,
  entry diagnostics, complete/incomplete counts, first/final delay, gap intervals,
  timestamp limits, continuation and settlement attribution, eligibility and
  exclusions. The session file links these rows by trade ID.
- [summary.json](evidence/2026-10-15/summary.json),
  [reconciliation.jsonl](evidence/2026-10-15/reconciliation.jsonl),
  [event-accounting.jsonl](evidence/2026-10-15/event-accounting.jsonl), and
  [reinitializations.jsonl](evidence/2026-10-15/reinitializations.jsonl).

These are derived audit records, not bulk quotes. Raw CSVs and intermediate runs
stay ignored. `strict_runtime_parity_eligible` and official settlement eligibility
are false throughout. `R0_exit_analysis_eligible` deliberately permits disclosed
gaps; `complete_observed_exit_replay_eligible` is stricter. Neither establishes
exchange freshness. The historical common cohort is read from frozen metrics;
no candidate selection is performed by this command.

```bash
NDX_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014 \
NDX_SUPPLEMENT=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015 \
uv run --offline --frozen pytest tests/test_ndx_baseline.py \
  tests/test_state_machine.py tests/test_position_manager.py -q
uv run --offline --frozen ruff check .
```

The full-snapshot test blocks network sockets and all external commands except
local Git. Without the two environment arguments it skips only that private-data
test; the independent fixtures still run. See
[verification.json](evidence/2026-10-15/verification.json) for this session's
results, isolated-checkout check and graph update.
