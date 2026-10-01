# Research workflow unification plan — 2026-09-29

- **Branch:** `research/workflow-unification`, cut from `research/unified-core` @ `fa9d34e`.
- **Inputs:** `docs/reviews/2026-09-27-research-pipeline-review.md` (committed here for
  the first time), `docs/research/research-core.md`, and
  `docs/research/registration-decision-2026-09-29.md`.
- **Starting state:** `uv run pytest` on `fa9d34e`: 1,046 passed, 1 skipped.
  `research/unified-core` merges cleanly onto `origin/main` @ `7d5952d`.
- **Scope:** how research moves from an idea to a live config change, and which code
  paths it uses on the way. Nothing here changes live trading, paper/live mode, limits
  or order routing.

## Why a plan is still needed

The research core on `research/unified-core` already delivers most of the 2026-09-27
review:

- one simulator with decision profiles;
- stressed, delayed-exit and floored accounting;
- a paired block bootstrap;
- tie-set scoring by default;
- a hash-chained variant registry;
- cohort shadow;
- the event calendar and VIX-family features;
- the ThetaData adapter and data-quality gates;
- the sealed holdout and the holdout command.

What is still not unified:

1. **It is not on `main`.** Twenty commits and about 17.8k lines sit on a branch. Thirteen
   of them (`a1c86c4` through `fa9d34e`) are not pushed. `main` still presents
   `run_backtest_db.py --sweep` as the research tool.
2. **There are three copies of the exit loop:** `SimulationEngine.simulate_day`,
   `SimulationEngine.simulate_day_from_entry`, and `research/exits.py`, which "mirrors"
   the second. The live parity reference and the research core can drift apart silently.
3. **There are several research entry points with overlapping jobs** (the table below).
4. **The stages are not linked by code.**
   - Idea → development run → registration → holdout → cohort → paper config: each hand-off
     is a person copying hashes between Markdown files.
   - The cohort manifest does not reference a registry record.
   - The decision packages are hand-written.
5. **Scratch analysis is back.** Per §9 of the decision package, the random-skip null, the
   power simulation and the breakdowns behind the 2026-09-29 decision package are
   uncommitted scratch scripts. That is the review's §3.1 finding again.
6. **The cohort ledger has two homes.** `main` stops at 2026-09-24, and the cohort branch
   runs through 2026-09-28. The branch conflicts with `main` on 7 files (add/add).

## Target workflow

```text
 Helios export ──┐                                     ┌── registry/development/*.jsonl
 vendor history ─┼─> hashed Parquet dataset ──> research core ──> development run ──> decision package
 (ThetaData,     │   (dataset.py, aux/)          (research/)       (paired, stressed,    (generated)
  gateway 1-min) ┘                                    │             tie-set, k-aware)          │
                                                      │                                  owner decision
                        one shared exit kernel <──────┤                                        │
                        (backtest + research)         │                          register (clean tree, pinned)
                                 │                    │                                        │
              SimulationEngine / run_backtest_db      │                     sealed holdout: pull once, evaluate once
              (live-parity reference only)            │                                        │
                                                      └── shadow <── prospective cohort (pinned worktree,
                                                                     manifest cites the registry record)
                                                                                               │
                                                                              owner: paper config change
```

The rules this plan holds to:

- **One simulator for research, one reference for live parity.** They share one exit
  kernel.
- **Every stage transition is a CLI command that refuses when its preconditions fail**
  and writes a registry or ledger record. No transition happens by hand.
- **Anything a written conclusion depends on is committed code** and produces a hashed
  artifact.
- **Frozen things stay frozen:**
  - the cohort at `6ffbfe7`;
  - the parity ledger `b83c2a18` (`trades.jsonl` `b5b732ad…`);
  - both registry chains;
  - the development runs `7d7f91ad9ba5` and `9971c5db1313`.

  Each refactor below must reproduce them exactly.

## Entry-point inventory and fate

| Entry point | Job today | Fate |
|---|---|---|
| `python -m butterfly_guy.research` | Research core CLI | **Canonical** for all rule research |
| `run_backtest_db.py` (single, range, `--execution-accounting-report`, live-pinned replay, selection parity) | Replay through live components | **Keep** as the live-parity reference |
| `run_backtest_db.py --sweep` | Midpoint grid, Sharpe-ranked | **Retire.** It exits with a pointer to `research run` |
| `discover_options_strategy.py` | Chronological split discovery (July) | **Legacy.** The holdout protocol supersedes it. Keep for its recorded reports |
| `run_paper_replay.py` | `OrderManager` ladder mechanics on history | **Keep**, relabelled as an execution-mechanics diagnostic, not research |
| `run_prospective_execution.py` | Cohort ledger | **Keep.** It is extended in Phase 4 |
| `run_entry_analysis.py`, `run_classifier_sweep.py`, `inspect_entry.py <pre-2026-03-13>`, `SimulationEngine.simulate_day` | Synthetic Black–Scholes paths | **Legacy**, labelled in the README and AGENTS (review §6). Retire `simulate_day` in Phase 2 |
| `docs/research/spx-idea-sweep-2026-09-25/*.py`, `spx-exits-2026-09-12/*.py` | Frozen experiment code | **Keep as evidence.** Each README gets a line saying the core is canonical and the variants are ported |
| Scratch scripts (2026-09-25 robust/rb_eval/call-filter; 2026-09-29 skip null, power, breakdowns) | Behind journal conclusions | **Commit them into the core** (Phase 3) |

## Phases

### Phase 0: land what exists

No behaviour change. One PR each.

1. **Push `research/unified-core`** (13 unpushed commits), and open a PR into `main`.
   - Review it module by module, following `research-core.md`'s module table.
   - Verification:
     - `uv run pytest`;
     - `uv run ruff check .`;
     - `uv run pytest -m research_data`, with the cache present, for the 118-trade parity;
     - `python -m butterfly_guy.research verify` on `spx_0dte` and `spx_0dte_thetadata`.
2. **Settle the cohort ledger's home** (owner decision O1).
   - **Recommended:** the ledger lives only on `cohort/spx-prospective-2026-09-22`, as
     `shadow` already assumes (`git show origin/cohort/<id>:…`). `main` takes the branch's
     `tools/cohort_daily_update.sh` and `infra/systemd/*`, and drops or freezes its stale
     ledger copy with a README pointer.
   - **Alternative:** merge the cohort branch into `main`, taking the cohort side on all
     7 conflicting files, and repeat that merge periodically.
3. **Commit the 2026-09-27 review** (this branch), and add the missing journal entry
   about the runner moving to a pinned worktree and the `f933117` labelling issue.
4. **Documentation surface.**
   - The README's research section points at `research-core.md`.
   - AGENTS.md's `inspect_entry.py 2025-06-03` example gets a date with stored chains.
   - The legacy paths are labelled.

**Exit criterion:** `main` contains the core, and the full local suite passes on it.
CI (`.github/workflows/database-smoke.yml`) runs only the database smoke test, so it
does not cover this work.

### Phase 1: one command surface

1. **Retire `--sweep` for SPX (O3).** `run_backtest_db.py --sweep --asset SPX` prints the
   equivalent `research run` invocation and exits non-zero.
   - NDX and XSP keep the sweep, labelled legacy (midpoint, Sharpe-ranked, hypotheses
     only), because the core exports SPX only. `run_sweep` and `_summarize_combo` are
     deleted once the core covers those assets.
   - A grid parameter needed for SPX research (for example a drawdown schedule) becomes
     a named core variant first.
2. **Add a `research catalog` command** that lists variants, their hashes, registry stage
   and data sets. It replaces reading `variants.py` and the JSONL registry by hand.
3. **Mark `discover_options_strategy.py` and the synthetic scripts legacy** in their
   module docstrings and `--help`.

**Exit criterion:** every research question in the README runs through
`python -m butterfly_guy.research`.

### Phase 2: one exit kernel

1. **Extract the per-minute exit state machine** into one pure module, for example
   `backtest/exit_kernel.py`. It takes a mark and a time and holds the state: peak,
   pending drawdown confirmation, regime thresholds, the profit-protector trailer and the
   15:00 incomplete-data rule. It also covers the held-to-close settlement path.
   - `SimulationEngine.simulate_day_from_entry` and `research/exits.py` both call it.
   - `simulate_day` is deleted (synthetic and legacy), or kept only as a thin caller.
   - `simulate_day_adaptive` is checked and treated the same way.
2. **Fix the two latent parity gaps while there** (review §5). Both are inert under the
   current config, so the tests must show no change:
   - pass the configured regime bounds (`simulation_engine.py:148`);
   - carry per-regime `confirmation_polls`, `min_peak_profit_ratio` and `min_hold_minutes`
     instead of collapsing them to their maximum (`_sim_parity_fields`, and the
     `exits.py` equivalent).
3. **Parity gates.** The change is refused unless all of these hold:
   - the frozen-replay `trades.jsonl` is byte-identical (`b5b732ad…`);
   - `test_research_sweep_ports.py` passes;
   - `test_simulation_parity.py` passes;
   - `shadow` reproduces every cohort E0 trade;
   - the development runs `7d7f91ad9ba5` and `9971c5db1313` reproduce their
     `results.json` hashes.
4. **Out of scope:** having live `position_manager.py` call the kernel. It already
   shares `profit_policy`. Moving the rest is a live-behaviour change and needs its own
   proposal.

**Sequencing constraint.** The holdout command compares `src/` and `configs/` against
recorded commits. To avoid tying code work to the registration timetable, run register →
holdout pull → holdout evaluation from a **pinned worktree at the registration commit**,
the same pattern as the cohort. With that in place, Phase 2 can land on `main` at any
time. Without it, Phase 2 must land before registration or after the holdout evaluation.

### Phase 3: commit the analysis that decisions rest on

1. **Promote the 2026-09-29 scratch analyses into the core:**
   - `research power` for block-resampled gate pass rates under no, half and full effect;
   - `research null-skip` for the random-skip null of a given size, which D4 needs;
   - the E0 breakdowns, as `diagnose` cells.

   Each writes a hashed artifact under `reports/research/`.
2. **Recover or re-derive the 2026-09-25 scratch scorers** (robust, `rb_eval`, the FRED
   close wrapper, the call-filter scorer), or mark the journal conclusions that rest on
   them as unreproduced.
3. **Generate decision packages** (`research decision-package --runs …`): tables, hashes,
   variant counts and the power table come from artifacts. The prose stays hand-written.
4. **Rule going forward:** a journal or decision-package figure must cite a run id or an
   artifact hash.

**Exit criterion:** every figure in `registration-decision-2026-09-29.md` §§2–5 and §9
can be regenerated by a command.

### Phase 4: link the stages

1. **Registration.** Add `research register-pin`, which creates the pinned worktree and
   refuses a dirty tree (the provenance checks exist; the worktree step does not).
2. **Holdout.** `holdout` runs from that worktree only, and its record cites the worktree
   commit.
3. **Cohort.** Add `run_prospective_execution.py create --from-registration <dataset>:<seq>`,
   which writes the cohort manifest with:
   - the registry record's definition hash, fitted values and `git_sha`;
   - the pinned-worktree setup, generalised from `tools/cohort_daily_update.sh` to a
     cohort id argument, with one systemd unit per cohort.

   Later cohorts are then provably the rule that passed the holdout.
4. **Shadow.** Run `shadow` after each cohort append (a hook in the cohort updater, with
   exploratory output only) instead of by hand.
5. **Paper promotion** remains an owner decision. The cohort `evaluate_gates` output and
   the shadow table are its inputs.

**Exit criterion:** you can walk the chain from any config change back to a cohort, a
holdout run, a registration and a development run by following record ids.

### Phase 5: data upkeep

1. **Schedule the Helios export** after each session, and `--bars-only` the next
   evening for the late official close. This is a timer next to the cohort updater
   (the Helios cron is UTC-only). It keeps `spx_0dte` current without manual stage
   refreshes, and appends manifest history as it does now.
2. **Wire the gateway minute archive into `history.py`.** The monthly Helios job on
   `feat/gateway-minute-backfill` is the source for SPX/VIX 1-minute bars after the
   owner CSVs end (2025-12-09). This decides the SPX index path for sessions ThetaData
   Indices would otherwise fill (D6).
3. **Settlement close source.** `daily_bars` lands at least one session late. Decide
   whether `export --bars-only` may fall back to Cboe's published close, which the
   2026-09-28 check matched exactly, and record the source per session.

## Open owner decisions

| # | Decision | Needed before |
|---|---|---|
| O1 | Where the cohort ledger lives (Phase 0.2) | Phase 0 |
| O2 | Pinned-worktree registration (Phase 2 constraint), or freeze `src/` between register and holdout | Phase 2 |
| O3 | How to retire `--sweep` | **Decided 2026-09-29:** refuse it for SPX (pointing to `research run`); keep it for NDX/XSP, labelled legacy, until the core supports them. The core is SPX-only and has no parameter grid |
| D2, D4, D5, D6, D7 | As listed in `registration-decision-2026-09-29.md` §8 | Registration |

## What unification does not change

The pipeline's current answer is unfavourable:

- **Development window.** E0 is −$9,685 stressed (floored) over 361 trades on
  2022-01 → 2024-06.
- **Helios sample.** It is positive only through H1 2026.
- **H-TS1** is the one candidate that beats E0 by more than fly-choice noise. Even so, it
  lost money in its own right.

The work above makes the next answer cheaper and more trustworthy. It does not make it
more favourable. Keep Phases 0–1 small, so the pipeline work does not delay the D2/D4/D5
decisions that the next real test depends on.
