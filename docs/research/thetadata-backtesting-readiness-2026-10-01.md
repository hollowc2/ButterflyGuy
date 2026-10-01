# ThetaData backtesting readiness and completion plan

Checked 2026-10-01. **SPXW is ready for offline backtesting on eligible,
normalized sessions. The entire downloaded archive and all instruments are not
ready for a broad research run.** The remaining work is primarily checkout,
storage, coverage, and experiment preparation; the local adapter already exists.

This check covered local files and research code. It did not change strategy
parameters, raw data, live services, or historical registration records.

## What is ready

- Local `origin/main` is `02cdec7`, containing the ThetaData implementation merged
  in PR #37 (`66ff18e`). Local branch `main` is older (`7d5952d`). The active dirty
  checkout is `feat/weekend-review-executable-pnl` at `bb0408f` and does not contain
  the research package. Updating the execution checkout is necessary; rebuilding
  the adapter is not.
- The clean implementation worktree is
  `/tmp/butterfly-thetadata-implementation`, branch `feat/thetadata-local-replay`,
  commit `cf8da0e`. Fresh verification ran there using the existing research
  virtual environment, `PYTHONPATH=src`, and `uv run --no-sync`.
- Compared with that tested implementation, `origin/main` has identical local
  import, lifecycle, accounting, configuration, and dependency files. Its only
  research-package differences are catalog/history additions in `cli.py` and
  `registry.py`. This check did not run the full suite on `origin/main`.
- **SPXW 0-DTE:** the approved local validation dataset has 128 normalized sessions
  over 2026-03-13 through 2026-09-25. Six-session replay, 2026-03-19 through
  2026-03-26, resolved all six trades, including three cash settlements, and
  reproduced the existing replay artifact exactly.
- **SPXW development:** local archive normalization currently covers only
  2023-11-22 and 2023-11-24. Both replayed successfully, including the scheduled
  early close. The canonical `research run --variants E0 --profile vendor_1m`
  command also completed on those two sessions with `--no-registry`.
- **SPXW 1-DTE mechanics:** fresh intraday replay resolved the 2026-03-19 position;
  carry replay preserved the same 2026-03-20 expiration and resolved through
  settlement, with 750 monitoring observations across both sessions. This is
  independent one-fly lifecycle verification, not a portfolio or validated 1-DTE
  strategy.
- **Tests:** 81 focused local-source, ThetaData, holdout, protocol, quality, and
  parity tests passed, including the cached full frozen replay parity test.
  Targeted research lint passed. Both local 0-DTE dataset manifests verified.
  Full validation import resumption also passed, checking unchanged raw and
  supporting inputs without rewriting the published dataset.

## Data inventory and remaining limits

Fresh catalog/file reconciliation found **23,040 Parquet files**,
**5,835,648,113 bytes** (about 5.44 GiB), and 23,044 catalog requests. There were
no catalog conflicts, missing successful files, or incomplete unprotected files.
16,264 unprotected Parquet footers matched the recorded row counts; 6,776
protected files were counted/stat-ed without opening their footers or prices.
This is catalog consistency, not independent proof of every expected expiration.

Unprotected quote-file coverage is:

- SPXW 0-DTE: 1,050 files, 2020-01-03 through 2026-09-28.
- SPXW 1-DTE: 1,050 files, trade dates 2020-01-02 through 2026-09-25.
- NDXP 0-DTE: 955 files, 2020-01-03 through 2026-09-28; vendor `no_data` on
  2022-12-16 for all four kinds.
- XSP 0-DTE: 1,011 files, 2020-01-03 through 2026-09-28.

These counts exclude the protected interval and include historical dates before
daily expirations existed. File date ranges do not imply continuous coverage.

The archive has no underlying index levels, IV, or Greeks. The current observed
price workflow uses separate SPX/VIX observations and attributed daily settlement
inputs. Greek-dependent strategies are unsupported with this archive alone.

The validation import excluded eight of its 136 candidate option sessions:
2026-03-13, 03-16, 03-18, 04-27, 05-04, 05-18, and 06-02 for missing VIX;
2026-06-01 for missing SPX observations. Its existing approved quality result
passes Q1–Q4 and Q6. Q5 is not evaluable on recorded index ticks because they are
not exact-minute prints; the two-session development check passes Q5 at lag zero.
This check read those quality results and verified the dataset; it did not rerun
the whole quality computation.

The SPX/VIX owner CSVs use America/Chicago bar-end timestamps and exclude stale
sessions; their documented last usable date is 2025-12-09. Their original source
is unknown. Later recorded input coverage must be checked session by session;
neither the CSV tail nor the option archive end date proves usable coverage.

Fresh NDXP/XSP audits on 2026-03-19 found zero usable sessions because each lacks
its own index observations, prior close, opening input, and attributed settlement.
They are fixture-supported but remain blocked for real-data backtesting.

The existing derived cache is `/tmp/thetadata-cache` (169 MiB), daily receipts
are `/tmp/thetadata-daily`, and prior artifacts are `/tmp/thetadata-artifacts`.
**`/tmp` is tmpfs on this machine: these working inputs are not durable.**

The 2024-07-01 through 2026-03-12 interval is already exposed in the prior
registered experiment: the three-record H-TS1 registry verifies, and evaluation
`ce91c4a08efd` records failure of gates 2 and 6. It cannot become an unseen holdout
again. Local import/replay guards still block general access. No protected prices
or another holdout evaluation were used for this check.

## Defined steps to complete broad SPXW backtesting

1. **Use a durable checkout of the current research code.** Create an isolated
   worktree from the current verified `origin/main`, preserving the dirty active
   checkout and frozen experiment worktrees. Install its locked dependencies
   with `uv sync`. Run the 81-test target below there, plus `uv run ruff check .`;
   run the full suite if integration changes shared behavior.
   **Done when:** `python -m butterfly_guy.research --help` exposes `inventory-local`,
   `audit-local`, `import-local`, `vendor-quality`, `replay-local`, and `run`, and
   the relevant checks pass on the exact commit selected for the experiment.

2. **Preserve the working cache and provenance outside `/tmp`.** Choose private,
   gitignored storage on the persistent volume. Copy the normalized cache,
   supporting snapshot, public daily CSVs/receipts, and prior artifacts, retaining
   original hashes. Check embedded absolute paths: if relocation changes an
   input receipt or source description, create a new receipt and dataset identity
   and repeat validation; do not edit a published manifest or inherit an approval
   for a different source identity.
   **Done when:** durable dataset verification succeeds and the smoke replay can
   run from durable inputs without requiring any file under `/tmp`.

3. **Audit the full unprotected development window before importing it.** Use
   `audit-local --set spxw_0dte --start 2022-01-03 --end 2024-06-28`, with the
   archive, supporting snapshot, correctly interpreted owner minute files, and
   daily receipt supplied explicitly. Retain approved data exclusions
   (2022-02-22 and 2022-06-02), report per-session missing inputs and required
   interval gaps, and distinguish non-expiration days from failed downloads.
   Audit any additional requested dates separately; do not silently expand this
   range or cross the protected interval.
   **Done when:** there is an exact eligible-session list and exclusion ledger,
   with requested, available, eligible, and excluded counts reconciled.

4. **Normalize the eligible development archive and check quality.** Run
   `import-local` into a new SPX local dataset, supplying `--quality-dataset` for
   a passing full-window local validation dataset with the same source/mapping.
   If step 2 changed that identity, import the validation window and run
   `vendor-quality` first. Process sessions individually, keep raw data unchanged,
   and run `verify` and unchanged-input resumption. Run development quality checks,
   including the SPX/option timestamp lag check that is evaluable on owner minutes.
   **Done when:** every accepted session is normalized, exclusions are retained,
   applicable quality gates pass, and a repeat import preserves all dataset hashes.

5. **Freeze and run the baseline before comparing ideas.** Pin the code, data
   hashes, config, development range, profile, and chronological comparison split.
   Use `replay-local` to inspect several traces, including an early close,
   drawdown exit, settlement, and a missing-input session. Then run the existing
   E0 baseline over the eligible development dataset through
   `research run --variants E0 --profile vendor_1m`. Supply the split explicitly;
   the default split is a 2026 date and is unsuitable for this 2022–2024 window.
   Use `--no-registry` for infrastructure smoke checks and a distinct development
   dataset/registry for actual research. Freeze any candidate and define a new
   evaluation design before examining further data; preserve the previous
   registration and its failed holdout result.
   **Done when:** outputs identify every evaluated, excluded, no-trade, unpriced,
   and unresolved session and include trade traces, costs, P&L, drawdown, count,
   win rate, expectancy, profit factor, average win/loss, exposure, and cost drag.
   Report dollar results per fly until a capital model is defined.

SPXW 0-DTE completion means steps 1–5 pass on the agreed eligible range. Missing
supporting observations remain explicit exclusions; they do not require a new
subscription or fabricated data.

## Separate extensions

- **Broader SPXW 1-DTE:** audit/import a specified range, import matching expiry-day
  0-DTE sessions, and replay `intraday` and `carry` separately with explicit
  `--entry-spec borrowed-0dte-controls`. Verify Friday/Monday and holiday gaps,
  persistent overnight exit state, missing expiry data, and unresolved positions.
  Add a defined capital/overlap model before claiming portfolio returns.
- **NDXP/XSP:** locate or separately acquire actual instrument-specific intraday,
  opening, prior-close, and settlement observations. Attribute NDX settlement
  to the required XQC input and XSP settlement to its documented source. Audit,
  import, and replay a real session before expanding the range. Do not substitute
  SPX levels or scaled ETFs. These gaps do not block SPXW research.
- **IV/Greek strategies:** obtain suitable observed inputs or define a separately
  authorized estimation study. Existing archive-only capability checks must
  continue to reject these modes.

## Working smoke command and evidence

The following reproduces the confirmed SPXW smoke check now, using existing
temporary inputs. It is not the durable workflow required by step 2:

```bash
cd /tmp/butterfly-thetadata-implementation
export PYTHONPATH=src
export UV_PROJECT_ENVIRONMENT=/mnt/Repos/Trading/Butterflyguy-research/.venv
export UV_CACHE_DIR=/tmp/thetadata-readiness-uv-cache
uv run --no-sync python -m butterfly_guy.research \
  --cache /tmp/thetadata-cache --dataset spx_0dte_local_final_validation \
  replay-local --start 2026-03-19 --end 2026-03-26 --lifecycle 0dte \
  --out /tmp/thetadata-readiness-2026-10-01
```

Focused verification target:

```bash
uv run pytest tests/test_research_local.py tests/test_research_thetadata.py \
  tests/test_research_holdout.py tests/test_research_protocol.py \
  tests/test_research_quality.py tests/test_research_parity.py -q
```

Fresh private evidence is preserved under
`reports/thetadata_readiness/2026-10-01/` in this checkout, which is gitignored.
`readiness-summary.json` records checks and artifact SHA-256 hashes. The canonical
E0 smoke run is `spx_0dte_local_development/549b757e57f2`; two sessions establish
command functionality only. The six-session replay is
`spx_0dte_local_final_validation/replay/f7ed9a085057/replay.json`.

The full application suite, CI/database smoke, remote market-data coverage, and
independent expiration-list verification were not rerun: this was a focused
offline readiness check. No repository Python code was changed, so no graph
update was needed. Preserve vendor quote traces as private data.

## Execution follow-through

Steps 1–5 were subsequently completed on 2026-10-01 for **585 eligible SPXW
0-DTE sessions**, 2022-01-03 through 2024-06-28. The isolated durable checkout,
relocated-input validation, full development quality checks, import resumption,
frozen E0 baseline, session reconciliation, and reproduction commands are recorded
in [the completion record](thetadata-backtesting-completion-2026-10-01.md).
This readiness check remains the earlier snapshot; the completion record contains
the subsequent execution evidence and results.
