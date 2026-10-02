# SPXW session quality evidence ledger — 2026-10-02

The research CLI now consolidates existing inventory, import, eligibility, quality,
and optional E0 evidence into one record per requested calendar date. It runs
entirely offline. No strategy evaluation, new quality assessment, download,
configuration change, or source-data cleaning is performed.

Implementation checkout: `.worktrees/spx-session-quality-ledger`, branch
`feat/spx-session-quality-ledger`, based on `origin/main` at `f4fad7d`.
The [inventory documentation](../data-management.md) was carried from `0a3e4b3`.
The active dirty checkout and frozen execution checkout remain preserved.

## Private artifacts and reconciliation

Canonical outputs live under
[`../../reports/data_management/session_quality/2026-10-02/`](../../reports/data_management/session_quality/2026-10-02/).
Each content-addressed directory contains `ledger.jsonl`, `summary.json`,
`provenance.json`, and `report.md`; none is tracked in Git.

Development artifact:
[`spx_0dte_local_durable_development_20261001/session-quality-ledger/0c4c5f58ce6f/`](../../reports/data_management/session_quality/2026-10-02/spx_0dte_local_durable_development_20261001/session-quality-ledger/0c4c5f58ce6f/).

- 908 calendar dates: 258 weekends, 25 holidays, 31 documented non-expiration
  weekdays, and 594 successful option sessions.
- 594 option sessions: 585 accepted, seven missing supporting observations,
  and two approved quality exclusions (2022-02-22 and 2022-06-02).
- Linked existing E0 overlay: 362 traded + 223 no-trade = 585 accepted.
- No missing-source files, conflicting sessions, or unresolved reconciliation issues.
- Result SHA-256: `0c4c5f58ce6f55ca261d85c2c0369675890f2dafbc2fed4226d1bb9aca2d8b3a`.
- JSONL SHA-256: `59035877fb8012f7c2ed5c97b7d766497ec87dfe56a0acf865cb53092d7b9661`.
- Summary SHA-256: `b8af3237bd445d92b5e8d67b7ee7bb73c62408f81b303ed899857e7f1db216a6`.

Validation artifact:
[`spx_0dte_local_durable_validation_20261001/session-quality-ledger/49ab90e06349/`](../../reports/data_management/session_quality/2026-10-02/spx_0dte_local_durable_validation_20261001/session-quality-ledger/49ab90e06349/).

- 197 calendar dates: 56 weekends, five holidays, and 136 candidate option sessions.
- 136 option sessions: 128 accepted + eight exclusions.
- Missing VIX: 2026-03-13, 03-16, 03-18, 04-27, 05-04, 05-18, and 06-02.
  Missing SPX observations: 2026-06-01.
- No replay overlay is required; its absence does not fail a data check.
- No missing-source files, conflicting sessions, or unresolved reconciliation issues.
- Result SHA-256: `49ab90e063495be9842b3d45302e18135aa2bd05bc64b64af0813735c041e6fe`.
- JSONL SHA-256: `8ecc910f4ea29d71e0aa3dd974ca2fd3fa2bf381e95e9dc8f4243b2700f99ae1`.
- Summary SHA-256: `b1211c49c46e2c87688fd5a09253e5b709c7265d93f29dc9cc627f596f1c3865`.

## Interpretation

`primary_classification` is mutually exclusive; calendar, option availability,
supporting inputs, normalization, quality, and research outcomes remain separate.
Multiple original exclusion reasons retain their evidence locations. Summary
reason counts count a reason code once per date, even if two sources establish it.
The optional overlay is tied to the inventoried E0 ledger, its audit, and the
hash-verified E0 results/provenance; it never causes a strategy replay.

Quality gates have **dataset scope**. Development inherits Q1–Q6 pass; validation
inherits Q1–Q4/Q6 pass and Q5 **not_evaluable**. Existing per-session measurements
are attached only where recorded. Unassessed gates remain `unassessed`; neither
aggregate passes nor missing measurements become new session-level passes.
The independent minute-file daily OHLC cross-check was not acquired.

A usable development audit establishes the checked supporting fields. Importer
acceptance alone establishes SPX/VIX availability; opening/prior-close and
settlement fields remain unknown without an audit. Validation therefore retains
197 unknown entries for each opening/prior-close/settlement field, 68 unknown SPX
entries, and 62 unknown VIX entries, including non-session dates. Unknown is a
statement about evidence scope, not a new exclusion threshold.

The calendar uses America/New_York and the existing holiday/event conventions.
Documented non-expiration classifications are inherited from the development
eligibility audit; available EOM and holiday-shift expirations are preserved.
An independent full expiration-list snapshot remains absent. Source file counts
are never substituted for session counts. Owner minute-file provider attribution
remains unknown; America/Chicago bar-end semantics and the 2025-12-09 last usable
date remain in provenance. Zero-quote/no-trade conventions are unchanged.

`reconciled` means the existing evidence agrees. It is not a fresh quality or
backtesting-readiness assessment. Contradictions and missing successful-request
files produce a blocked artifact and exit status 1; changed pinned identities,
missing required evidence, or unmatched quality/source mappings stop generation
with exit status 2. Protected-range requests stop before evidence I/O; raw path
dates are guarded separately before hashing. Catalog metadata may be read, but
protected option payloads remain unopened.

Generation timestamps and code revision/dirty state live in provenance. JSONL
and summary are deterministic, and their hashes determine the artifact directory.
An unchanged rerun verifies and preserves every existing artifact byte, including
its original provenance. A changed unpinned metadata identity creates a distinct
artifact; a changed pinned source is rejected. Existing prototype output directories
from implementation verification remain preserved outside the dated canonical output.

## Reproduce offline

Explicit dataset, cache, range, inventory, evidence root, and output are required.
The range must match the inventoried immutable import. The two ranges remain
separate; the intervening protected period is not traversed.

```bash
cd /mnt/Repos/Trading/Butterflyguy/.worktrees/spx-session-quality-ledger
BASE=/mnt/Repos/Trading/Butterflyguy
EVIDENCE="$BASE/reports/thetadata_completion/2026-10-01"
CACHE="$EVIDENCE/thetadata-cache"
INVENTORY="$BASE/reports/data_management/2026-10-01/inventory.json"
OUTPUT="$BASE/reports/data_management/session_quality/2026-10-02"

UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run --no-sync python -m butterfly_guy.research \
  --cache "$CACHE" --dataset spx_0dte_local_durable_development_20261001 \
  session-quality-ledger --start 2022-01-03 --end 2024-06-28 \
  --inventory "$INVENTORY" --evidence-root "$EVIDENCE" \
  --eligibility "$EVIDENCE/eligibility-ledger.json" \
  --replay-ledger "$EVIDENCE/session-ledger.json" \
  --catalog "$BASE/data/thetadata/catalog.jsonl" \
  --catalog "$BASE/data/thetadata_sealed/catalog.jsonl" --out "$OUTPUT"

UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run --no-sync python -m butterfly_guy.research \
  --cache "$CACHE" --dataset spx_0dte_local_durable_validation_20261001 \
  session-quality-ledger --start 2026-03-13 --end 2026-09-25 \
  --inventory "$INVENTORY" --evidence-root "$EVIDENCE" \
  --catalog "$BASE/data/thetadata/catalog.jsonl" \
  --catalog "$BASE/data/thetadata_sealed/catalog.jsonl" --out "$OUTPUT"

# Run before and after generation; neither command recomputes quality gates.
UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run --no-sync python -m butterfly_guy.research \
  --cache "$CACHE" --registry "$EVIDENCE/registry" \
  --dataset spx_0dte_local_durable_development_20261001 verify
UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run --no-sync python -m butterfly_guy.research \
  --cache "$CACHE" --registry "$EVIDENCE/registry" \
  --dataset spx_0dte_local_durable_validation_20261001 verify

UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run --no-sync pytest \
  tests/test_research_session_ledger.py tests/test_research_local.py \
  tests/test_research_calendar.py tests/test_research_holdout.py -q
UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run --no-sync ruff check .
UV_CACHE_DIR=/tmp/butterfly-graphify-uv-cache \
  UV_TOOL_DIR=/tmp/butterfly-uv-tools UV_TOOL_BIN_DIR=/tmp/butterfly-uv-bin \
  uvx --offline --from graphifyy graphify update .
```

Verification: **76 tests passed** and repository lint passed. Both canonical
inputs passed the existing verifier before and after generation, retaining the
published dataset hashes and 1,173/259 manifest-listed files. Both artifact sets
passed output/provenance verification and byte-identical unchanged-input reruns.
Graphify refreshed the graph with AST extraction only; SQL extraction reports
its pre-existing missing `tree_sitter_sql` dependency. No runtime tests, remote
operations, or fresh strategy/quality evaluations are part of this change.

Remote database/capture continuity, NDX/XSP readiness, independent backups and
restore drills, scheduling, and broader archive imports remain follow-ups.
