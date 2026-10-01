# Butterfly Guy Research and Backtest Pipeline Review — 2026-09-27

- **Base:** `main` @ `c0b229e` (local), `origin/main` @ `df0a484`; checkout on
  `feat/weekend-review-executable-pnl` @ `bb0408f`.
- **Scope:** the research and backtest pipeline: `run_backtest_db.py`,
  `backtest/simulation_engine.py`, `backtest/execution_accounting.py`,
  `backtest/prospective_execution.py` and its cohort automation, the entry-selection
  path, `backtest/metrics.py`, the research packages under `docs/research/`, and the
  strategy-discovery journal through 2026-09-25.
- **Changes made:** none to source, config, or runtime on `main`. This file is the
  only addition to the main checkout. The cohort remediation in progress is described
  under [Cohort remediation status](#cohort-remediation-status).
- **Purpose:** plan the next research phase now that the SPX paper stack is stable.

## Executive summary

The research practice is strong. The journal has pre-registration, frozen source
hashes, settlement parity against Cboe, a no-imputation quote policy, tie-set
robustness checks, and it reports failures honestly. The weak points are:

1. **The prospective cohort had stalled.** It could no longer append (details below).
2. **Statistical power.** At the observed payoff shape, 120 trades cannot separate
   the measured edge from zero, and small rule changes cannot be validated forward
   in any practical time. This should shape all further research.
3. **Fragmented research infrastructure.** Several independent simulators, sweeps
   that rank on midpoint accounting and a per-trade Sharpe, and key conclusions
   resting on uncommitted scratch code.

## 1. The prospective cohort's daily update was failing (P0)

`butterfly-cohort-update.service` failed on 2026-09-25 18:31 PT:

> cohort spx-prospective-2026-09-22 is frozen against a different research version …
> Changed: source changed: src/butterfly_guy/scripts/run_backtest_db.py

Since the frozen commit `6ffbfe7`, four of the sixteen tracked sources changed on
main:

- `run_backtest_db.py`: `deb32dd` (`--direction-ma`) and `67ba7ce` (official gap
  inputs);
- `chain_cache.py`, `position_manager.py` and `butterfly_builder.py`: #27.

`configs/config.yaml` is unchanged (SHA-256 `d120b63f…`).

The ledger held 2 sessions (2026-09-22, 2026-09-23). 2026-09-24 has complete data but
was never recorded. 2026-09-25 is still waiting for its `daily_bars` close, which was
absent as of 2026-09-27. Both are recoverable because the replay data is still in the
DB and deferral is built in.

Independently of the drift, `tools/cohort_daily_update.sh` skips whenever the
checkout is not on `main`, so ordinary feature-branch work also stops the cohort.

**Root cause:** the cohort runs from the developer's working tree. Any research
commit to the 3,000-line backtest CLI, or to shared strategy modules, stops it.

**Fix:** run cohort updates from a dedicated worktree pinned to the frozen commit,
with the ledger committed to a cohort branch rather than `main`.

**Note for the record:** the cohort keeps the pre-`67ba7ce` snapshot-based gap
inputs, which the 2026-09-25 journal entry found flip direction relative to live on
about 5% of sessions. That does not threaten the cohort's integrity, since it tests
the frozen rule. It does mean the cohort rule, the current backtest and live now
differ.

### Cohort remediation status

Completed on 2026-09-27. The cohort appends again.

- **Worktree and branch.** `/mnt/Repos/Trading/Butterflyguy-cohort` is on branch
  `cohort/spx-prospective-2026-09-22`, created at `6ffbfe7`. It has its own `.venv`
  from the frozen `uv.lock`, and its `.env` is a symlink to the main checkout's.
- **Branch commits** (pushed to `origin/cohort/spx-prospective-2026-09-22`):
  - `ae6a50f`: ledger through the 2026-09-24 run, copied from `origin/main`.
  - `6ef4386`: the updater runs from the worktree, commits only on the cohort branch,
    and pushes to `HEAD:cohort/spx-prospective-2026-09-22`. The systemd unit points
    at the worktree.
  - `f933117`: a systemd README note. **It also contains the 2026-09-24 session
    record** (`daily_runs.jsonl` and `trades.jsonl`, one line each). That record came
    from the owner's manual `update` run from the worktree (trade
    `b87c47309d12f05c`), and `git commit -a` swept it into this commit. The message does not say so. The branch was already pushed, so the
    history was left as is.
  - `70ccb8e`: the first automated run from the new unit. It regenerated the
    summary, found 2026-09-24 already recorded and reproduced it identically
    (appending nothing), and deferred 2026-09-25 pending its official close.
- **Installed unit.** `~/.config/systemd/user/butterfly-cohort-update.service` was
  reinstalled from the branch and `daemon-reload` was run. The timer is unchanged
  (next firing Monday 2026-09-28 18:30 PT).
- **Ledger state:** 3 sessions and 3 eligible trades (2026-09-22 to 2026-09-24).
  Stressed-marketable net is $669 with 1 cash settlement. `verify` reports integrity
  OK.

Follow-ups:

- `main` still has the old `tools/cohort_daily_update.sh` and
  `infra/systemd/butterfly-cohort-update.service`, and its ledger stops at 2026-09-24.
  Merge the cohort branch into `main` when you want them current. The branch changes
  only `reports/prospective_execution/`, `tools/cohort_daily_update.sh` and
  `infra/systemd/` relative to `main`'s versions of those paths.
- Add a journal entry, when convenient, recording that the runner moved to a pinned
  worktree on 2026-09-27, and the `f933117` labeling issue.

## 2. Statistical power (P0 for research planning)

The frozen-sample figures are: stressed-marketable expectancy of about $85 per trade,
a 14–15% win rate, a negative median, and all aggregate profit coming from about 20
cash-settled landings.

- **Per-trade standard deviation is about $820–920.** Two independent derivations
  agree: the journal's 63-trade resample (a −$6,607 or worse tail at 3.2%) implies
  about $816, and the PF/win-rate split implies about $920.
- **At the 120-trade endpoint**, the standard error is about $80, so the true edge
  sits about 1.1 SE from zero.
- **If the true edge is zero**, stressed net > 0 still happens about 50% of the time.
  Adding the both-halves-positive and top-3 gates gives a false-pass rate of roughly
  20%.
- **If the true edge is $85**, the full gate set passes only about 55% of the time.
- **To separate $85 from zero at t ≈ 2** you need about 400 trades, roughly 1.7 years
  of sessions.

Implications:

1. **Forward-validating a single configuration cannot resolve small rule changes.**
   H-LV1, the MA rules and the call-only filters all sit inside the ±$2–3k band
   already measured for fly-choice noise alone.
2. **Paired comparisons are the efficient instrument.** Scoring variants on the same
   sessions (shadow variants on the cohort's entries, exit ablations on frozen
   entries) removes most session-level variance. Build the research loop around
   paired differences with day-block bootstrap CIs, not standalone totals.
3. **More history is the largest available lever.** SPX chains start 2026-03-13,
   which is about 133 sessions spanning two volatility regimes. SPXW has had
   expirations every weekday since 2022, so vendor intraday 0-DTE quote history
   could provide about 1,000 sessions across 2022's bear market, 2023's low
   volatility and 2025's shock. Candidate vendors are ThetaData, Databento (OPRA)
   and Cboe DataShop; check coverage, granularity and licensing. The H1/H2 diagnosis
   (the edge depends on realized-vs-implied movement after 10:00) cannot be settled
   on 130 sessions.

## 3. Research infrastructure (P1)

### 3.1 Consolidate the simulators

Current results come from at least:

- `SimulationEngine`, driven by `run_backtest_db.py` (3,047 lines);
- the numpy harness in `docs/research/spx-idea-sweep-2026-09-25/sim.py`;
- the exits replay (`spx-exits-2026-09-12/replay.py`) and its trial runners
  (`exit_trials/run_trials.py`, `all_history_trials/run_all_history.py`);
- `discover_options_strategy.py`;
- `run_paper_replay.py`;
- uncommitted scratch scripts behind the 2026-09-25 journal entries: `robust.py`,
  `rb_eval.py`, the FRED-close wrapper, and the call-filter scorer.

The idea sweep reimplemented the strategy because the official sweep could not do
stressed accounting or run fast enough. Its parity with the frozen replay (a 0.3%
residual from the decision clock) was checked once, by hand.

Recommendation:

- Promote the dense per-day arrays built by `prep.py` (stored as Parquet) and the
  `sim.py` engine into `src/` as the research core.
- Add a committed parity test against a frozen fixture, with an explicit tolerance.
- Keep `SimulationEngine` as the live-parity reference, not the sweep engine.
- Commit research code that journal conclusions depend on.

### 3.2 Sweeps rank on the wrong accounting and the wrong metric

- **Accounting:** `--sweep` supports only midpoint plus commission, and
  `--execution-accounting-report` is rejected in sweep mode (`parse_args`). Midpoint
  overstated the frozen sample's stressed P&L by about 45% ($17.7k vs $9.9k).
- **Metric:** rows are sorted by `metrics.sharpe`, which is per-trade mean/σ × √252.
  - It ignores no-trade days, so a 40-trade filter is annualized as if it traded
    daily.
  - Its noisier small-sample estimate puts low-trade-count combos at the top of the
    ranking (winner's curse).
  - Sharpe penalizes the right tail that this payoff depends on.
- **Rank instead on:**
  - stressed P&L per evaluated session, with zeros on no-trade days;
  - a paired day-block bootstrap CI of the difference from baseline;
  - H1/H2 (or rolling-block) columns;
  - top-3-removed P&L;
  - the number of variants evaluated on the same data. `REGISTRY.md` already tracks
    this by hand; automate it.

### 3.3 Make fly-choice robustness a standard output

The selector (`butterfly_selector.select_best`) takes the reward/risk nearest 10.
On live sessions, a mark change under $0.05 flips the chosen width 41% of the time,
so one backtest run is one draw from selection noise. Report the tie-set average (and
draw quantiles) by default. A smoother, σ-normalized center-and-width rule would lower
backtest variance in its own right and is a reasonable candidate for the next
preregistered cohort. It must not be applied to the open one.

## 4. Data and features known before entry (P1)

- **Event calendar** (FOMC, CPI, NFP, monthly OPEX, quarter-end). The 2026-07-14
  audit found no durable macro-event table, yet event days dominate 0-DTE realized
  volatility.
- **VIX1D and VIX9D, and the term structure.** VIX is a 30-day measure; the idea
  sweep found the chain-implied remaining move is about 0.4× the VIX daily move.
- **Overnight futures move.** This is a cleaner gap signal than the index open.

## 5. Live/backtest parity (P2)

- **Exit timing:** the backtest triggers and fills an exit on the same one-minute
  collector snapshot. Live polls every 2 seconds and works an order ladder. Add a
  one-snapshot exit-latency stress variant, and calibrate it from
  `monitoring_leg_quotes` on recorded paper trades.
- **Fill model:** the $0.05-per-leg stress is not calibrated. Paper fills are at
  mark, so there is no empirical fill evidence for SPX fly complex orders.
  Calibrating it requires real fills, which is an owner decision.
- **Latent: regime boundaries.** `simulation_engine.py:148` calls `get_time_regime()`
  without the configured regime bounds, while live `position_manager.py` passes them
  since #27. This is inert while the config uses the 120/240 defaults.
- **Latent: per-regime settings.** `_sim_parity_fields` in `run_backtest_db.py`
  collapses per-regime `confirmation_polls`, `min_peak_profit_ratio` and
  `min_hold_minutes` to their maximum. This is inert while all regimes are equal.

## 6. Cleanup (P3)

- `AGENTS.md` suggests `inspect_entry.py 2025-06-03`. That date predates any stored
  chain, so its output is synthetic Black–Scholes. `run_classifier_sweep.py`
  ("25 years") is also synthetic. Mark both legacy, as the README already does for
  `run_entry_analysis.py`.
- `SimulationEngine.simulate_day` and `simulate_day_from_entry` duplicate the
  monitoring loop, so they can drift apart.
- `SimulationParams.paper_exit_price` floors exits at 0.05 after commission, and
  `sim.py` does the same for midpoint. This is a small optimistic bias on exits of
  nearly worthless flies.
- Official closes land in `daily_bars` at least one session late (2026-09-25 was
  missing on 2026-09-27). The cohort defers such sessions, so this is handled, but it
  delays every settlement-dependent report.

## Suggested order

1. ~~Finish the cohort remediation.~~ Done 2026-09-27. Merge the cohort branch into
   `main` when convenient.
2. Decide on a history-data vendor.
3. Build a unified research core with stressed accounting, paired day-block
   bootstrap, tie-set scoring and a variant registry.
4. Add the event calendar and VIX1D/VIX9D features.
5. Run the next preregistered idea sweep on the expanded history. Evaluate
   survivors as paired shadow variants against the open cohort's sessions.
