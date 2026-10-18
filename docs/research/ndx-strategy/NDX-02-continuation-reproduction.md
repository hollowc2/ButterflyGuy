# Reproduce the NDX minute-continuation audit

Read the [findings and eligibility decision](NDX-02-continuation.md) first.
This is a data import and quality audit, with no signals or economic replay.
The private raw snapshots and prior runs are required in addition to Git.

The final offline command, as executed below, uses the locked existing Python
environment. It verifies the new snapshot, original inventory, parent outputs
and source/config pins. It opens no broker/database/network connection and uses
only local Git subprocesses for run identity. Replace `--output` with a **new**
directory when reproducing; the recorded path already exists and must refuse.

```bash
uv run --offline --frozen python -m butterfly_guy.research.ndx_continuation \
  --evidence evidence/ndx/ndx-minute-continuation-20261015-v2 \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/ndx02-continuation-snapshot.json \
  --inventory evidence/ndx/ndx-continuation-inventory-20261015 \
  --inventory-manifest docs/research/ndx-strategy/evidence/2026-10-15/continuation-inventory-manifest.json \
  --execution-parent reports/research/ndx-02-20261015/run-02 \
  --baseline-parent reports/research/ndx-01-20261015/run-03 \
  --config docs/research/ndx-strategy/evidence/2026-10-15/ndx02-continuation-contract-v2.json \
  --source-lock docs/research/ndx-strategy/evidence/2026-10-15/ndx02-continuation-source-lock.json \
  --output reports/research/ndx-02-continuation-20261015/run-01
```

Evidence and parent paths may be absolute and outside the checkout. Dependency
installation, if needed elsewhere, is a separate `uv sync --frozen`; no empty-cache
installation was repeated here. Changed inputs/mechanics need a new snapshot or
contract, new output identity and parent link, preserving prior artifacts. Do not
edit source locks to bypass drift. `run.json` preserves the exact command,
environment, all source hashes, source-lock/config/manifest hashes, parent hashes,
input file maps and output hashes. Audit/helper/test source copies are retained.

Outputs are `observations.jsonl` (complete normalized leg groups with signed raw
composites), `rejected-groups.jsonl` (all rejected groups and reasons),
`coverage.jsonl` (inventory reconciliation, raw/complete intervals, missing minute
buckets, source boundaries, price flags, actual timing/size coverage and explicit
eligibility exclusions), `summary.json`, and reproducibility records.

Separate acquisition uses only versioned read-only SQL over SSH/psql:

```bash
# Equivalent explicit CLI for a NEW export; never target an existing snapshot.
uv run --offline --frozen python -m butterfly_guy.research.ndx_evidence extract \
  --query docs/research/ndx-strategy/sql/continuation-prices-v2.sql \
  --output evidence/ndx/my-new-continuation-snapshot/prices \
  --host billy@helios
```

The actual acquisition invoked the same `ndx_evidence.extract()` function from a
local Python wrapper that recorded start/completion UTC JSON before/after the
call. Its arguments were the versioned query above,
`evidence/ndx/ndx-minute-continuation-20261015-v2/prices`, and `billy@helios`.
The wrapper, frozen cohort, schema extraction, contract, failure history and
snapshot file hashes are described in the raw acquisition records and report.
Every extract uses a new directory and a fixed 60-second statement timeout.
Before another acquisition, read the VPS skill, verify Helios/repository/disk
and register a new attributed contract; this example alone does not assemble a
complete audit snapshot. A later DB extract is a new evidence identity.

Verification, as executed:

```bash
NDX_CONTINUATION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-minute-continuation-20261015-v2 \
NDX_EXECUTION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014 \
NDX_SUPPLEMENT=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015 \
uv run --offline --frozen pytest tests/test_ndx_continuation.py \
  tests/test_ndx_execution_audit.py tests/test_ndx_baseline.py \
  tests/test_state_machine.py tests/test_position_manager.py -q
uv run --offline --frozen ruff check .
/home/corey/.cache/uv/archive-v0/Yo1tT0lFfjWucooJ/bin/graphify update .
```

Result: **72 passed**, lint passed, AST graph updated. Independent fixtures cover
signed composites/provider marks, missing/nonfinite/crossed legs, wrong identity,
duplicates/incomplete groups, boundary timestamps, strict gap thresholds, partial
minutes/bucket gaps, singleton paths, inventory discrepancy, actual timing versus
availability, checksum drift and overwrite refusal. Full private-snapshot tests
block network sockets and restrict subprocesses to local Git. Without the private
evidence environment variables, only private-snapshot tests skip.
