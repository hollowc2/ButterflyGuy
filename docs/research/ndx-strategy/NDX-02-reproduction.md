# Offline NDX-02 execution/accounting audit

Use the [reconciliation and model specification](NDX-02-execution-accounting.md)
for definitions and limitations. This command audits recorded accounting and
diagnostics; it does not replay exits or evaluate strategy variants.

Provision the locked environment once with `uv sync --frozen`. The command below
uses only local evidence and local Git for identity. It requires the private
snapshots and frozen parent runs alongside this checkout; cloning Git alone
does not recover them. Paths may be absolute and evidence may live elsewhere.

Exact final run invocation (already executed; choose a **new** output to repeat):

```bash
uv run --offline --frozen python -m butterfly_guy.research.ndx_execution_audit \
  --evidence evidence/ndx/ndx-r0-20261014 \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/snapshot.json \
  --supplement evidence/ndx/ndx-01-supplement-20261015 \
  --supplement-manifest docs/research/ndx-strategy/evidence/2026-10-15/supplement-manifest.json \
  --inventory evidence/ndx/ndx-continuation-inventory-20261015 \
  --inventory-manifest docs/research/ndx-strategy/evidence/2026-10-15/continuation-inventory-manifest.json \
  --runtime-source evidence/ndx/helios-ndx-source-20261015 \
  --runtime-manifest docs/research/ndx-strategy/evidence/2026-10-15/runtime-source-manifest.json \
  --parent reports/research/ndx-01-20261015/run-03 \
  --config docs/research/ndx-strategy/evidence/2026-10-15/ndx02-execution-final.json \
  --source-lock docs/research/ndx-strategy/evidence/2026-10-15/ndx02-execution-source-lock-final.json \
  --previous-run reports/research/ndx-02-20261015/run-01 \
  --output reports/research/ndx-02-20261015/run-02
```

`--parent` is the frozen baseline whose coverage is reconciled, not a request to
replay it. `--previous-run` identifies the preserved metadata correction parent;
the final contract requires its exact run-manifest hash. A reproduction of the
same contract uses the same previous run. Further corrections must register a
new contract/source lock/run identity and link to the run being corrected.
Never edit a dated contract or source lock to make drift pass.

Each run refuses existing output directories, output inside evidence/parents,
changed manifests, missing or mismatched evidence, changed pinned source, and
changed baseline output hashes. A failed run directory remains evidence; use a
new identity rather than cleaning or overwriting it. The run preserves its
contract, source lock, audit/helper/test source, exact invocation, source/input/
config hashes, Git SHA/dirty status, Python/platform/package versions, correction
parent and output hashes. No timestamp is invented to complete a row.

Outputs:

- `execution-ledger.jsonl`: derived discretionary cohort, one record per trade,
  with separate entry/exit accounting, raw diagnostics, source-identified signal
  marks, null missing times, held-collection bounds, original attributable event
  payloads/write times, entry-selection observations/limits, estimates, fallback
  and floor flags, and separate paper/stress P&Ls.
- `modern-context.jsonl`: all newer recorded trades, including cash settlements,
  to check the frozen 53-trade totals without enlarging the discretionary cohort.
- `summary.json`: coverage denominators, numerical failures, separate drag/spread
  distributions, fallback/floor IDs, diagnostic changes, and write-time offsets.
- `run.json`, `contract.json`, `source-lock.json`, `runner-source/`: reproducibility.

Private-data verification, as executed:

```bash
NDX_EXECUTION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014 \
NDX_SUPPLEMENT=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015 \
uv run --offline --frozen pytest tests/test_ndx_execution_audit.py \
  tests/test_ndx_baseline.py tests/test_state_machine.py tests/test_position_manager.py -q
uv run --offline --frozen ruff check .
```

Result: **57 passed**; repository lint passed. Without the environment arguments,
only the private-snapshot tests skip; independent fixtures still run. Graph update
command, warnings and artifact checks are in
[verification](evidence/2026-10-15/ndx02-verification.json).

Storage remains the accepted Eros-backed filesystem. Existing NDX-01 snapshot,
supplement, inventory, raw bundle and parent runs were verified and preserved.
The new output/source copies provide attributable retention on that filesystem;
they do not establish independent backup or historical runtime parity.
