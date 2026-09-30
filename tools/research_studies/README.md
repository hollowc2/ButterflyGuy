# Development-window studies

`dev_studies.py` reproduces the ad hoc studies behind
`docs/research/registration-decision-2026-09-29.md`. It reads a committed run's `trades.jsonl`
(default `7d7f91ad9ba5`, git `6891317`) and the dataset's development-window session list, and
uses `protocol.calibrate_gate1` and `protocol.gates` unchanged. It replays nothing and never
reads a holdout session.

| Command | Package section | Reproduces |
|---|---|---|
| `check` | §2, §3 | arm totals (E0 −9,922; HTS1 −2,283) |
| `random-skip --rule R` | §3 "What trading less is worth" | shares exactly (12%, 1.8%, 62%, 79%); means within sampling noise |
| `calibrate --rule R --sessions N` | §6.2 | exactly (HTS1 at 358: 17.7% at the drafted 10%; levels 2.5%, 0.25%; k ≥ 3 not reached) |
| `power --rule R --sessions N --k K` | §4 | see below |

**Power does not match the package's null rows.** Run on 2026-09-29 (HTS1, k = 1, 358 sessions, 1,000
simulations, 10,000 bootstrap reps):

| Scenario | This tool: gates 1–4 / all | Package §4 |
|---|---|---|
| development effect | 30% / 16% | 36% (33% in a second run) / 18% |
| half effect | 18% / 6.8% | 27% / 8% |
| no effect (constant shift) | 9.5% / 2.7% | "no mechanism, E0 losing": 16% / 4.7% |
| no effect, E0 breaking even | 9.5% / 5.8% | 13% / 13% |

This tool builds each scenario as §9 describes it: it shifts the paired difference by a
constant per session. The package's labels ("half the skip pattern replaced by an unrelated
one", "no mechanism") point to a different construction in the lost scratch script, one that
kept the skip filter's sparse, skewed shape. That would explain why its null rows sit higher. It
also used 2,000 bootstrap reps where this tool uses 10,000. The development-effect row agrees
within the run-to-run spread.

Runtime is about 1.5 minutes for `calibrate` and 4 minutes for `power`.
