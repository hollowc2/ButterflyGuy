# All 108 historical entries: executed exit experiments

Read [REPORT.html](REPORT.html). Scope and unchanged parameters are recorded in
[PLAN.md](PLAN.md). This extends the 33-trade study without overwriting its files.

Every entry from March 17 through September 11, 2026 was attempted on monitoring
and collector separately. The fixed `best_available` view selects monitoring when
raw monitoring exists (64 entries), otherwise collector (44). Unresolved outcomes
never trigger fallback. No paths are stitched.

The 60/60/75 trailer gives −$679 versus −$1,787 on 98 paired mark outcomes, but
retains only 77.3% of the same baseline top-five winner P/L. May 6's +$2,217 becomes
+$139 on the collector path. The 50% absolute stop gives −$1,020 on those 98 pairs.
Only 39 baseline pairs match the ledger in P/L, reason, and time; these aggregate
results are exploratory. The five-second confirmation has only 18 paired outcomes
and cannot establish full-cohort performance. No setting qualifies for promotion.

## Run locally

From the repository root, with the existing locked project environment:

```bash
.venv/bin/python docs/research/spx-exits-2026-09-12/all_history_trials/run_all_history.py
.venv/bin/python docs/research/spx-exits-2026-09-12/all_history_trials/render_report.py
uv run pytest docs/research/spx-exits-2026-09-12/all_history_trials/test_all_history.py docs/research/spx-exits-2026-09-12/exit_trials/test_exit_trials.py docs/research/spx-exits-2026-09-12/test_replay.py -q
uv run ruff check .
```

No environment secrets, network, broker access, or database are needed. The runner
imports the existing `exit_trials` implementation and frozen deployed state machine.
Since execution stresses do not affect mark-based signals, each policy path is
evaluated once and the five fill scenarios are applied to its signal. Tests check
equivalence with separate replays, including latency, settlement, missing data,
stops and confirmation. Every original baseline source/stress outcome (1,080)
and every prior mark_v1 experiment outcome (1,650) is asserted equal on rerun.

All raw and frozen source hashes are checked, along with prior-study input/output
hashes. `configs.json` is required to equal the previous study's full settings.
No parameters were added, combined, or retuned. The only change in scope is the
full historical entry set and separate quote-source views.

## Outputs

- `results/trade_results.csv`: 16,200 unique source/view × entry × variant × stress
  attempts, including missing outcomes. This is 10,800 source-specific scenarios
  plus 5,400 fixed-choice derived views, not 16,200 independent trades.
- `results/comparisons.json`: full 108, legacy 75, and mark_v1 33 paired metrics,
  source-specific parity counts, excluded IDs, tail retention, cost sensitivities.
- `results/breakdowns.json`: monthly and directional paired metrics.
- `results/baseline_parity.csv`, `parity_summary.json`: all ledger comparisons;
  matching requires P/L within $0.01, the same reason, and time within ten seconds.
- `results/coverage.csv`: row counts, first/last valid observation, entry lag,
  rejected groups, and quote gaps, for each source and entry.
- `results/source_choices.csv`: 108 raw-presence-based composite source choices.
- `results/focus_winners.csv`: each source and variant for the ten largest recorded
  winners, including censored results excluded from aggregates.
- `results/recorded_trades.csv`, `recorded_summary.json`: the actual ledger,
  separately labeled. Its +$1,835 is not the replayed-baseline comparator.
- `manifest.json`: data acquisition provenance, hashes, environment and regression
  counts. The checkout SHA is not asserted to identify the running image.
- `verification.txt`: executed checks and unavailable verification.

All entries are fixed one-lot long debit butterflies. Quote exits use the original
paper commissions and fill rounding. Entry execution is fixed and uncertain for
legacy records. Extra legacy entry fees are an arithmetic sensitivity, not a
reconstruction of altered entry prices or their signal effects. Conditional
settlement reuse is not independent broker attestation. No account return, Sharpe,
marked-equity drawdown, out-of-sample result, or deployable profitability is claimed.

No runtime code, configuration, services, trading limits, or original research
artifacts were changed. The graph was refreshed for the new research code.
