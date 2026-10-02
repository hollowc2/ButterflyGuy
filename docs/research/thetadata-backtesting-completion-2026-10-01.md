# ThetaData durable backtesting execution — 2026-10-01

Execution record for the [readiness plan](thetadata-backtesting-readiness-2026-10-01.md).
Scope is offline SPXW 0-DTE, 2022-01-03 through 2024-06-28 inclusive, using observed
ThetaData minute bid/ask quotes, actual SPX/VIX observations, and attributed daily
closes. This execution preserves strategy configuration, raw data, live services,
the dirty active checkout, and the previous failed H-TS1 evaluation.

## Code and experiment freeze

The isolated, durable execution checkout is
`.worktrees/thetadata-readiness-2026-10-01`, detached at `02cdec7` (`origin/main`
when this work began). `uv sync --locked` installed its own virtual environment.
The readiness document's six-file target passed **81 tests** on this checkout;
`uv run --no-sync ruff check .` passed across the repository. The CLI exposes all
six required commands. No adapter reconstruction or strategy changes were needed.

Before baseline execution, `experiment-plan.json` froze the E0 variant,
`vendor_1m` profile, code/config/lock hashes, date range, accounting assumptions,
and a **2023-03-31** chronological comparison split. H1 includes that date; H2
starts after it. Both halves are development data, not unseen evaluation data.
Results are dollars per independent fly; no capital or portfolio model is defined.
The existing unfloored accounting models remain in use, with commission and
adverse execution/latency stresses. No candidate search is part of this run.

## Persistent inputs and provenance

Private evidence lives under `reports/thetadata_completion/2026-10-01/` on the
persistent `/mnt/Repos` volume. The parent directory is mode `0700` and gitignored.
`preservation.json` reconciles **645 original files, 177,428,256 bytes**, copied
from the original cache, daily inputs/receipts, and artifacts, with matching SHA-256
hashes. The recorded reference dataset and prior research artifacts/registries
were preserved separately. Published original manifests were not edited.

Moving the daily CSVs changed their absolute source paths. The new daily receipt
is `thetadata-daily/9f7d847ae966.json`; it retains the original CSV hashes and
retrieval/source attribution. This required a new dataset identity and a fresh
full-window quality run. The active supporting snapshot is `local_support_v1`.
Older preserved manifests can retain historical `/tmp` references; they are
evidence of previous runs, not the active import source.

The original provider of the owner minute CSVs remains unknown, as recorded in
their source descriptions. Offline quality uses the preserved Cboe daily CSV;
the separate, report-only independent minute-file daily OHLC cross-check was not
acquired. No observations are synthesized to fill missing sessions.

The newly normalized validation dataset is
`spx_0dte_local_durable_validation_20261001`, with **128 accepted sessions** over
2026-03-13 through 2026-09-25. Fresh quality run `b3c6482ea210` passes Q1–Q4 and
Q6; Q5 is not evaluable on irregular recorded SPX ticks. Full unchanged-input
resumption leaves every published file byte-identical. The six-session durable
replay, 2026-03-19 through 2026-03-26, resolves all six positions: three morning
drawdown exits and three cash settlements. Its active source requires no `/tmp`
input files.

## Full development eligibility audit

Durable audit `8fd1f7fa698d` covers all **908 calendar dates** in the specified
development window. `eligibility-ledger.json` reconciles them as follows:

- 258 weekend dates and 25 market holidays.
- 31 non-expiration weekdays before regular Tuesday/Thursday expirations began.
- 594 available, successful requested option sessions.
- Seven sessions excluded for missing supporting observations: SPX on 2022-02-25,
  2022-03-04, 2022-05-06, and 2024-05-30; VIX on 2022-10-25, 2022-10-28, and
  2024-01-31.
- Two previously approved quote-quality exclusions: 2022-02-22 and 2022-06-02.
- **585 eligible sessions** after those nine exclusions.

There are no missing successful catalog requests in this range and no required
entry-interval gaps among the accepted sessions. Cboe's rollout notice identifies
the first regular Tuesday and Thursday expirations as **2022-04-26** and
**2022-05-19**, respectively; listing launch dates are earlier. Available EOM and
holiday-shift expirations remain eligible irrespective of weekday. This
reconciliation combines the observed catalog, market calendar, and rollout
history; it does not claim an independent full vendor expiration-list snapshot.
[Source: Cboe rollout reminder](https://cdn.cboe.com/resources/product_update/2022/Reminder-Cboe-Options-to-List-SP-500-Tuesday-and-Thursday-Expiring-Weekly-Options-2-.pdf).

## Normalization and frozen baseline — completed

**All five readiness steps are complete for the eligible SPXW 0-DTE development
range.** Dataset `spx_0dte_local_durable_development_20261001` contains 585
sessions and 1,173 manifest-listed files, with dataset hash
`98434ab47077456d812a17be785e98d2cfc2c94819c986b0c83df6518a4f6b63`.
Development quality run `25d9a7474ab2` passes **Q1–Q6**. Minimum per-session quote
coverage is 99.992%; Q5 has **lag zero on all 585 sessions**, including the eligible
DST-change-week sessions. All 585 daily closes match the cached Cboe input.
Unchanged-input import resumption preserves every published file hash.

The 2023-11-22/24 lifecycle replay resolves both trades and respects the scheduled
November 24 early close. Inspection of 2022-02-25 retains `no_spx_index` as an
explicit data exclusion; an empty replay of that absent normalized session is not
a no-trade strategy decision. Together with the six-session validation replay,
these checks cover early closes, morning drawdown exits, settlement, and missing
inputs.

Frozen E0 run **`f6717f4b6704`** evaluates all 585 eligible sessions, split into
275 H1 and 310 H2 sessions. The complete `session-ledger.json` reconciles all
908 requested calendar dates: **362 traded, 223 no-trade, nine excluded,
31 non-expiration, and 283 non-session dates**. There are **zero unpriced trades,
zero unresolved positions, and zero additional replay exclusions**. All 362
trades have records in `trades.jsonl`; the exit ledger contains 79 cash settlements
and 283 drawdown exits.

Aggregate net P&L across independent one-fly trades is:

- Midpoint model with fees: **+$18,167.10**.
- Executable bid/ask with fees: **−$423.00**.
- Executable bid/ask with fees and $0.05 adverse slippage per contract per
  executed side: **−$13,323.00**.
- The same stress with one decision-clock exit delay: **−$9,028.80**.

The primary stressed model has 362 priced trades, **13.5% win rate**,
**−$36.80 expectancy**, **0.831 profit factor**, and **$21,128.00 maximum
drawdown**. Average win is $1,339.57; average loss is −$252.27. Average exposure
from entry to exit decision or scheduled settlement cutoff is **174.94 minutes**
across all 362 trades (63,327 fly-minutes total). Nominal modeled commissions are
$1,677.00; cash settlement has no closing commission. Primary cost drag versus
the net midpoint model is $31,490.10. The gross-midpoint comparison and effective
fee/floor distinctions are retained in `baseline-summary.json`.

This result establishes the reproducible baseline and supports further hypothesis
refinement in a separately defined experiment. No candidate search or promotion
is part of this execution. Dollar totals and drawdown are sums across independent
flies; capital-based returns remain undefined.

The infrastructure smoke run uses `--no-registry` and separate outputs. The full
baseline writes exactly **one E0 evaluation** into the distinct development
registry; its hash chain and final dataset verification pass. Supporting input,
code/config/lock, dataset, result, and trace hashes are retained in the private
freeze/provenance records. `completion-summary.json` inventories artifact hashes;
`baseline-summary.json` adds average win/loss, exposure, cost drag, monthly results,
and concentration alongside the canonical metrics.

A server restart interrupted the first import after 479 staged sessions. That
unpublished stage is retained as private evidence. The canonical retry completed;
590 files through 2023-05-01 match the interrupted stage byte-for-byte. The graph
was refreshed with an AST-only update, without an LLM call.

## Reproduce from durable inputs

Use the pinned checkout and explicit persistent
paths. The reproduction run below uses `--no-registry` and a separate output
directory to preserve the recorded experiment.

```bash
cd /mnt/Repos/Trading/Butterflyguy/.worktrees/thetadata-readiness-2026-10-01
THETA_ROOT=/mnt/Repos/Trading/Butterflyguy/reports/thetadata_completion/2026-10-01

.venv/bin/python -m butterfly_guy.research \
  --cache "$THETA_ROOT/thetadata-cache" --registry "$THETA_ROOT/registry" \
  --dataset spx_0dte_local_durable_development_20261001 verify

.venv/bin/python -m butterfly_guy.research \
  --cache "$THETA_ROOT/thetadata-cache" --registry "$THETA_ROOT/registry" \
  --dataset spx_0dte_local_durable_validation_20261001 replay-local \
  --start 2026-03-19 --end 2026-03-26 --lifecycle 0dte \
  --out "$THETA_ROOT/reproduction"

.venv/bin/python -m butterfly_guy.research \
  --cache "$THETA_ROOT/thetadata-cache" --registry "$THETA_ROOT/registry" \
  --dataset spx_0dte_local_durable_development_20261001 run \
  --variants E0 --profile vendor_1m --start 2022-01-03 --end 2024-06-28 \
  --split 2023-03-31 --no-registry --out "$THETA_ROOT/reproduction"
```

## Preserved research boundaries

The copied H-TS1 registry verifies its original three-record hash chain;
evaluation `ce91c4a08efd` remains the previous failed holdout result. No protected
option prices or additional holdout evaluation are used here. The protected
2024-07-01 through 2026-03-12 interval remains guarded and cannot be relabeled
unseen. NDXP/XSP real-data work, broader 1-DTE research, and IV/Greek-dependent
strategies remain separate extensions with the readiness document's prerequisites.

The full application suite, database/CI smoke, and remote/live-service checks are
outside this offline execution; shared trading behavior is unchanged. Vendor
quote traces and bulk data remain private and untracked.
