# Reproduce the NDX constituent fidelity audit

Use a provisioned locked environment; all commands are offline. Private evidence
must be restored separately from Git. No broker/database connection is used.
Frozen run: `reports/research/ndx-02-fidelity-20261015/run-01/`. Repeat only with
a **new output directory**; existing directories are refused.

```bash
uv run --offline --frozen python -m butterfly_guy.research.ndx_quote_fidelity \
  --evidence-root evidence/ndx \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/ndx02-continuation-snapshot.json \
  --continuation-parent reports/research/ndx-02-continuation-20261015/run-01 \
  --execution-parent reports/research/ndx-02-20261015/run-02 \
  --baseline-parent reports/research/ndx-01-20261015/run-03 \
  --config docs/research/ndx-strategy/evidence/2026-10-15/ndx02-fidelity-contract.json \
  --source-lock docs/research/ndx-strategy/evidence/2026-10-15/ndx02-fidelity-source-lock.json \
  --output reports/research/ndx-02-fidelity-20261015/my-new-run
```

The config explicitly identifies all five snapshot roots, versioned manifest
paths/hashes, required files and three parent run hashes. `--evidence-root` can
be an absolute restored evidence directory. Other manifest paths are resolved
from the checkout and verified against the config. Parent paths are explicit
CLI arguments and may point to restored runs. Checks include all parent outputs
and current parent source pins, cohort identity, inventory counts/bounds, rebuilt
normalized/rejected groups, previous summary, new source-lock/config hashes and
required raw input membership. Different mechanics require a new contract and
source lock linked to the preserved prior run, not editing a dated record.

The run preserves:

- `observations.jsonl`: 1,114 complete-group decimal composites, flags, overlap,
  exact symbols/strikes/widths, known clocks and raw-record pointers.
- `legs.jsonl`: all 3,364 raw rows including the 22 excluded-group legs; original
  quote/meta JSON, raw CSV data-record ordinal, decimal prices/residuals, auxiliary
  recorded fields, price/timing categories and null availability.
- `exclusions.jsonl`: eleven rejected groups and their reasons/raw-record links.
- `breakdown.jsonl`: full overlap masks and denominators by trade, session and
  timing-coverage subset; `examples.jsonl` selects mechanistic extremes under
  the frozen contract, never economic winners/losers.
- `summary.json`, `contract.json`, `source-lock.json`, copies of all pinned source
  files with relative paths preserved, and `run.json` with exact invocation,
  creation UTC, Python/dependency/platform versions, Git SHA/dirty state and
  input/parent/config/source/output hashes. `run.json` cannot hash itself; the
  versioned handoff records its hash separately.

Bulk ledgers and source copies remain private Git-ignored dependencies. Small
summary/breakdown/examples/run/contract/lock/verification records are versionable
under `docs/research/ndx-strategy/evidence/2026-10-15/`. Verify the full private
run before using a copied small derivative. Original source observations remain
in `evidence/ndx/ndx-minute-continuation-20261015-v2/prices/extract.csv`.

```bash
NDX_FIDELITY_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_CONTINUATION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-minute-continuation-20261015-v2 \
NDX_EXECUTION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014 \
NDX_SUPPLEMENT=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015 \
uv run --offline --frozen pytest tests/test_ndx_quote_fidelity.py \
  tests/test_ndx_quote_fidelity_raw.py tests/test_ndx_continuation.py \
  tests/test_ndx_execution_audit.py tests/test_ndx_baseline.py \
  tests/test_state_machine.py tests/test_position_manager.py -q
uv run --offline --frozen ruff check .
/home/corey/.cache/uv/archive-v0/Yo1tT0lFfjWucooJ/bin/graphify update .
```

The primary private-snapshot test blocks network sockets and all subprocesses
except local Git; independent fixtures cover signed arithmetic, residual
cancellation, unknown/zero/invalid fields, incomplete groups, partial clocks,
an old zero-size leg, events between pass start and completion, unavailable
consumer timestamps, overwrite refusal and mismatched config identity. A
second implementation in `test_ndx_quote_fidelity_raw.py` parses original JSON
with `Decimal` and checks the frozen output directly, including every raw row.
Its source is pinned separately in the verification record; it was added after
the immutable run-01 source lock to independently assess that run.

Without the private-data environment variables, private checks skip explicitly;
fixture success alone is not a full snapshot verification. No fresh dependency
installation, broker-connected testing, replay implementation or economic
evaluation is needed or authorized. [Findings](NDX-02-quote-fidelity.md) and
[causal-use requirements](NDX-02-causal-minute-specification.md) state the limits.
