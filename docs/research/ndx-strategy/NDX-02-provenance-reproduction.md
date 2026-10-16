# Reproduce NDX-provenance-v1 offline checks

Read the [proposed specification](NDX-02-prospective-provenance.md) and
[remaining gates](NDX-remaining-roadmap.md). Provision dependencies separately
with `uv sync --frozen` if needed; this session used the existing locked environment.
No broker, DB or network is required. The command verifies all five private
snapshot manifests and four frozen parent runs. Git alone cannot restore these;
missing evidence is an error, not fixture-only private verification. Snapshot and
parent paths are explicitly registered relative to checkout in `contract.json`;
restored paths require a new named contract/source lock, preserving v1.

Registered package: `docs/research/ndx-strategy/provenance-v1/`. The contract was
written before assessing fixture results. Schema and fixture-manifest hashes are
bound in the contract; the source lock binds the contract and implementation,
test, source-trace files and dependency locks. Do not edit these frozen files to
make drift pass; corrections need a new identity and correction-parent link.

Exact invocation already executed (use a **new output directory** to repeat):

```bash
uv run --offline --frozen python -m butterfly_guy.research.ndx_provenance \
  --input docs/research/ndx-strategy/provenance-v1/fixtures.jsonl \
  --config docs/research/ndx-strategy/provenance-v1/contract.json \
  --source-lock docs/research/ndx-strategy/provenance-v1/source-lock.json \
  --output reports/research/ndx-02-provenance-20261015/run-01
```

The 18 synthetic records cover all twelve requested cases, with separate incomplete,
duplicate-leg, mismatched-identity, reversed-order, discontinuity and restart-domain
cases, plus failed read and historical-shaped missing evidence. The latter is
explicitly synthetic too. `expectations.json` provides human-readable expected
categories and reason substrings independently of the checker. Each referenced
response/publication file is explicitly synthetic and SHA-256 bound. These are
illustrations of recording semantics, never historical rows or additional coverage.

Results: **6 sufficient asserted receipt chains, 8 insufficient, 4 rejected**.
The negative-mark example independently checks −4.02 provider composite, −4.40
signed bid, −3.60 ask and −4.00 midpoint. A sufficient after-close chain produces
no decision or fill. Every result retains false freshness/replay eligibility,
null earliest availability, null decision/fill. No policy threshold is registered.

Private run outputs: `results.jsonl`, `summary.json`, copied contract/source lock,
fixture records/schema/manifest, pinned `source/`, and `run.json`. The latter records
UTC, exact invocation, starting SHA/dirty state, Python/platform/dependencies,
all verified snapshot file maps, parent/source/input/config/output hashes.
`run.json` cannot hash itself; the versioned verification record binds it. Original
fixture response bytes stay in the versioned input package with its manifest.
Small copied run/summary and verification records live under
`evidence/2026-10-15/ndx02-provenance-*.json` relative to this guide.

Full verification command, with explicit private-evidence environment:

```bash
NDX_FIDELITY_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_CONTINUATION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-minute-continuation-20261015-v2 \
NDX_EXECUTION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014 \
NDX_SUPPLEMENT=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015 \
uv run --offline --frozen pytest tests/test_ndx_provenance.py \
  tests/test_ndx_quote_fidelity.py tests/test_ndx_quote_fidelity_raw.py \
  tests/test_ndx_continuation.py tests/test_ndx_execution_audit.py \
  tests/test_ndx_baseline.py tests/test_state_machine.py tests/test_position_manager.py -q
uv run --offline --frozen ruff check .
git diff --check
/home/corey/.cache/uv/archive-v0/Yo1tT0lFfjWucooJ/bin/graphify update .
```

The new full verification test blocks sockets, verifies all five snapshot manifests,
four parents and source pins, checks generated hashes, refuses existing outputs and
output nested in inputs. Focused mutations cover changed config, payload/publication
hashes, unsafe paths, identity mismatch, nonfinite prices, naive time, event after
fetch and monotonic reversal. Tests do not contact Schwab or mutate live services.
With no private evidence environment variables, private tests explicitly skip;
that is not a private-data verification. See the versioned verification record
for executed results and graph limitations.

Preparatory corrections before registration: the registration script initially
passed a string to a Path-only helper and failed before creating contract/output;
fixed to use Path. New-code lint found two long lines and one unused test import,
all corrected before the source lock. No frozen run failed or was overwritten.
The preserved prior header-only extraction and all superseded baseline runs remain
unchanged. Starting HEAD was `49da0284d24814ed2bc0838bbd543444b48019b9`;
existing fidelity/docs/graph work was already dirty and was preserved.

Next action: review the proposed contract, DB protocol and upstream ownership;
under separately scoped Stage B implementation work prepare recording integration,
isolated failure/resource tests and an activation/rollback plan. Operational
activation and economic comparisons remain separate gates. All 17 historical
paths remain ineligible; full NDX-02, actual execution and official XQC stay open.
