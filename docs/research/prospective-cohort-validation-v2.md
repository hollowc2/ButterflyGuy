# Prospective cohort validation, version 2

The September 22 SPX cohort is an existing, frozen version 1 experiment. Its six
recorded sessions through September 29 showed $86 net under stressed-marketable
accounting, against $421 under corrected midpoint. These early results do not
establish an executable edge. The registered endpoint remains 120 eligible trades,
20 cash settlements, and 15 stressed winners, with the registered $12,000 drawdown
limit. This change does not amend its manifest, ledgers, trading rules, or updater.

## Corrections for newly registered cohorts

- A selected entry that cannot produce a completed simulation is incomplete data,
  rather than a completed no-signal session. It remains eligible for a later retry.
- Session discovery uses the existing US market calendar, independently of database
  snapshot counts. Weekends, holidays, future dates, and sessions still in progress
  are excluded. The updater stops at the first incomplete session and retries it
  before recording later sessions, keeping the endpoint chronological.
- Each incomplete attempt is appended to `deferred_runs.jsonl`, with the same hash,
  provenance, command, warning, and row-count metadata as a daily run. Completed
  sessions remain in `daily_runs.jsonl`; trades remain in `trades.jsonl`. A later
  successful retry resolves the deferral in the report without deleting audit history.
- Reports distinguish executable entry coverage from session completion coverage.
  The latter counts completed sessions divided by completed plus unresolved deferred
  sessions observed so far; it does not measure tick-level quote completeness or
  dates after the first unresolved outage. Deferred dates are listed explicitly.
- Drawdown and all result breakdowns use chronological decision order, regardless of
  append order. Ledger verification requires existing files, valid record hashes,
  matching manifest metadata, and consistent trade/session references in both directions.
  Invalid ledgers block updates and reports.
- The updater stops immediately when all registered endpoint counts are met. Further
  updates regenerate reports without connecting to the database or adding observations.
  The 20-trade integrity review and 60-trade early-failure review remain operator reviews;
  this change does not redefine those criteria or tune any strategy parameter.
- Source hashes include the pricing, configuration, calendar, and accounting dependencies,
  package initialization files, `pyproject.toml`, and `uv.lock`. Dependency versions
  are attributable to the lockfile; run with `uv sync --locked` / `uv run --locked`.

An unresolved data outage can therefore pause new recording indefinitely. Restore or
backfill the missing evidence, or explicitly close the study as incomplete. Do not
silently skip the session, substitute quotes, or rewrite the manifest to continue.

## Keep the original experiment separate

The existing timer still targets `/mnt/Repos/Trading/Butterflyguy-cohort` and
`cohort/spx-prospective-2026-09-22`. Keep that checkout pinned: do not rebase it onto
this corrected harness or copy edited sources into it. Its version 1 limitations
remain part of the interpretation of its results. Use its pinned CLI for any
version 1 update, report, or verification.

After committing the corrected harness, register version 2 from a clean, dedicated
checkout, with an explicit new cohort ID, a future prospective start, and a drawdown
limit chosen before observing its data. For example:

```bash
uv sync --locked
uv run --locked python -m butterfly_guy.scripts.run_prospective_execution init \
  --asset SPX --cohort-id SPX_NEW_COHORT_ID --max-drawdown CHOSEN_DOLLAR_LIMIT
uv run --locked python -m butterfly_guy.scripts.run_prospective_execution verify \
  --cohort reports/prospective_execution/SPX_NEW_COHORT_ID
uv run --locked python -m butterfly_guy.scripts.run_prospective_execution update \
  --cohort reports/prospective_execution/SPX_NEW_COHORT_ID --through YYYY-MM-DD
```

Do not reuse the version 1 ledger or combine its observations with a version 2 result.
Freeze and reproduce the appropriate baseline before collecting the new cohort. No
version 2 cohort is initialized and no timer or service is changed by this patch.

## Verification

Focused regressions reproduce each reported failure before the fix: incomplete
simulation mislabeled as no signal, $80 drawdown instead of $160 after late backfill,
verification passing with all trades deleted, a one-trade endpoint recording two
trades, an outage absent from date discovery, and undetected pricing/dependency drift.
Tests also cover retries, endpoint idempotency, holidays, early closes, future dates,
and ledger metadata consistency. All database interactions in these tests are mocked;
this is harness verification, not a new profitability backtest or a service deployment.

Validation on 2026-10-01 (Python 3.13.13, dependencies installed from the unchanged
lockfile): 133 tests passed and repository-wide Ruff passed. The checked-in version
1 accounting models and breakdowns are reproduced exactly by the corrected summary
calculation. The original pinned checkout also passed its own ledger verification.

```bash
uv run --locked --no-sync pytest tests/test_prospective_execution.py \
  tests/test_backtest_research_integrity.py tests/test_run_backtest_db_defaults.py \
  tests/test_run_backtest_db.py tests/test_time_utils.py tests/test_research_shadow.py \
  -q -p no:cacheprovider
uv run --locked --no-sync ruff check .
```
