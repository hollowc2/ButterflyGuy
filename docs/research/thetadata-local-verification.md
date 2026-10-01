# ThetaData local implementation verification

Baseline: `research/unified-core` `9ac0fbb`. Implementation branch:
`feat/thetadata-local-replay`, worktree `/tmp/butterfly-thetadata-implementation`.
Raw data and ledgers were preserved; the H-TS1 registry still verifies with three
records. No broker write, live DB dependency, service restart or holdout evaluation
was performed.

Validation used the existing research environment with `PYTHONPATH=src` and
`uv run --no-sync`, keeping the other worktree's dependencies unchanged. A normal
fresh checkout can use `uv sync` followed by the documented `uv run` commands.

- Full suite: **1,075 passed, 1 skipped**, with three existing dependency/runtime
  deprecation warnings. The skipped test is `tests/integration/test_database_smoke.py`, because
  `CI_DATABASE_URL` is unset; no live database was required.
- Frozen parity: the committed mini fixtures and full cached **118-trade** replay
  passed with the original per-trade selections, exits and accounting totals.
- Final focused local/protocol/parity suite: **41 passed**.
- `uv run --no-sync ruff check .`: **passed**.
- `git diff --check`: **passed**.
- `graphify update .`: **completed** using
  `uvx --from graphifyy graphify update .`. The prescribed
  `/home/billy/.local/bin/graphify` does not exist on this workstation. SQL extraction
  was skipped because the optional `tree_sitter_sql` dependency is absent; Python
  AST extraction and graph regeneration completed.

An initial full run found five CLI protocol regressions from overly broad error
handling introduced during implementation. Error translation was restricted to
the new local commands; protocol tests and subsequent full runs passed. These
were fixed regressions, not attributed to the baseline.

Local fixtures cover timezone-aware conversions, naive/wrong-date rejection,
missing/crossed/zero-bid quotes, unknown Greeks, sizes, fractional XSP strikes,
contract identity isolation, duplicate contract observations, malformed Parquet,
partial publication recovery, unchanged-input resumption, changed raw/supporting/
cached daily inputs, protected access before I/O, protected expiration on the
preceding trade date, quality refusal, schema 3, early-close cutoff, intraday and
carry 1-DTE, Friday/Monday and holiday gaps, expiry exits, persistent peak/trailer
state, missing expiry input, unresolved ranges, multiplier and instrument-specific
fixture settlement. Existing accounting/holdout/causality tests also passed.

## Real private artifacts

`/tmp/thetadata-artifacts` contains separately hashed inventory, input audits,
supporting-input provenance, normalization, quality and replay results.
`/tmp/thetadata-cache` contains derived datasets; no vendor data is committed.

- Inventory: `archive_inventory/inventory/d7ca000be1d8/inventory.json`.
- Final validation quality:
  `spx_0dte_local_final_validation/quality/6da7b68181e8/quality.json`: PASS,
  128 usable sessions, Q1–Q4/Q6 pass, Q5 n/a under the existing approved convention.
- Final validation replay:
  `spx_0dte_local_final_validation/replay/f7ed9a085057/replay.json`: six resolved
  sessions, 2026-03-19 through 03-26, including three cash settlements.
- Final input intersection:
  `spx_0dte_local_final_validation/input-audit/fa808e4cedcd/input-audit.json`.
- Development replay:
  `spx_0dte_local_development/replay/fc0d183f9e59/replay.json`, 2023-11-22 / 11-24.
- Development quality:
  `spx_0dte_local_development/quality/eaa62d419951/quality.json`: PASS, Q5 lag 0
  on both observed sessions; no network acquisition during this check.
- Real intraday 1-DTE:
  `spx_1dte_local_example/replay/18b8aafd1b91/replay.json`.
- Real two-session carry/settlement:
  `spx_1dte_local_v1/replay/c1374865aa34/replay.json`, 2026-03-19 → 03-20,
  750 monitoring observations, expiry settlement 38.52 option points.
- Real NDX/XSP audits: `ndx_input_audit/input-audit/90a84bb46d39/` and
  `xsp_input_audit/input-audit/1c248c8a4171/`. Missing real index/open/prior-close/
  settlement inputs prevent a real historical replay; deterministic independent
  instrument fixtures pass. No index subscription was bought.

The final schema-3 validation dataset hash is
`0f1fbcc08fda0059c044532308871fb6434396d5d73e76f4b9f5d919c276e4d5`.
The development dataset hash is
`d7ab113d09453fe06f3fc208791cf748436083f01e03851050742709e545ef19`.
Both verify against their manifests.

Timing and peak RSS: one session 5.13 s / 298,252 KiB; six sessions 16.49 s /
384,388 KiB. Whole validation-window resumption with both owner CSVs loaded:
47.29 s / 1,048,680 KiB. The owner's minute loader holds whole supporting series;
raw quote normalization remains bounded per session. No performance target was
invented.

Remaining evidence limits: protected raw footers were not opened; no independently
cached vendor expiration-list snapshot was found; minute-file origin/licence is
unknown; NDX/XSP supporting observations are missing; optional independent daily
OHLC cross-check acquisition was not repeated; one-minute NBBO cannot prove actual
complex-order fills or overnight marks. These limits are disclosed in artifacts
and do not constitute authorization to deploy a strategy.
