# Executed SPX exit trials

Read [REPORT.html](REPORT.html) for the results, and [PLAN.md](PLAN.md) for the
experiment fixed before execution. This extends the parent research record.
No trading settings or live services were changed.

The 60/60/75 trailer improves 33-entry mark P/L from −$533 to +$122, but gives
−$664 under the moderate spread stress. The 50% loss stop gives −$847 at marks;
its relative performance improves under spread stresses but remains negative.
The five-second confirmation test has 32 unresolved outcomes. None is promoted.

## Reproduce

From the repository root using the existing project environment:

```bash
.venv/bin/python docs/research/spx-exits-2026-09-12/exit_trials/run_trials.py
.venv/bin/python docs/research/spx-exits-2026-09-12/exit_trials/build_report.py
uv run pytest docs/research/spx-exits-2026-09-12/exit_trials/test_exit_trials.py docs/research/spx-exits-2026-09-12/test_replay.py -q
uv run ruff check docs/research/spx-exits-2026-09-12/exit_trials
```

No secret environment values, database connections, or broker requests are needed.
The runner checks the original raw/source hashes before evaluating the 33 trades.
It imports the parent's frozen deployed package and copies the parent's replay
mechanics, wrapping only signal evaluation for elapsed-time confirmation. All
165 baseline scenario statuses and resolved results must match the prior replay;
all 33 mark baseline P/L and reasons must match the ledger. The original replay
script and original evidence files remain unchanged.

`configs.json` records all ten settings (baseline, three primary alternatives,
six sensitivities). `results/trade_results.csv` includes all 1,650 attempted
variant/stress/trade combinations, including censored outcomes. Paired summaries
always compare identical resolved IDs. Incomplete samples must not be interpreted
as complete strategy results. `results/breakdowns.json` holds monthly and
directional metrics; `results/coverage.csv` gives source coverage per trade.

`manifest.json` records input/output hashes, the runner hash, Python version,
dependency-lock hash, checkout, acquisition provenance, and command. It does not
assert that the local checkout is the running image revision. `verification.txt`
records checks and limitations. The report is generated from the saved output;
its editorial assertions intentionally fail if key results change on a rerun.

The original 108-trade history mixes execution models; this study intentionally
uses only the 33 previously validated `mark_v1` entries. Earlier trades and
collector quotes are not substituted to repair missing confirmation outcomes.
There is no untouched out-of-sample test or account Sharpe estimate in this study.
