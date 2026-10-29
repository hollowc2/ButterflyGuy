# Gap direction, VIX agreement and VIX regime — out-of-sample pre-registration

**Status: APPROVED by the owner 2026-10-29, as written, including the three proposed
exclusions. Nothing run.** This commit fixes the plan. Its hash is quoted in the results,
and each test runs once. Any later change must be marked in this file as a revision, with
the reason, before results are reported.

## Why

Three exploratory studies on the 2022-01 → 2026-09 vendor data (1,070 sessions) produced
three post hoc leads:

- **Gap direction is the edge.** Gap-direction flies beat opposite-direction flies by
  +$57k at mid (96th percentile of coin flips). Source: `tools/research_studies/direction_study.py`.
- **VIX agreement.** On days when VIX's move from the prior close to 10:00 ET goes against
  the gap (gap up with VIX lower, or gap down with VIX higher), gap minus fade was +$79k,
  positive in every year. On the other days it was −$22k, negative in every year. Source:
  `tools/research_studies/direction_features_study.py`.
- **VIX regime.** X1 (E0 held to settlement) lost money on stressed fills at VIX < 17 in
  every year. Skipping those days kept all of X1's mid P&L.

All three came from scanning about 70 buckets of the same data they are scored on, so they
need data that played no part in finding them.

## What has and has not been seen

- **2020-01-02 → 2021-12-31 SPXW 0DTE options (Test A).** These have never been imported
  into a research dataset, and no strategy has been run on them.
  - The import `spx_0dte_local_durable_pre2022_20261029` uses the exact inputs the
    spent-holdout dataset used. It runs normalization and the vendor-quality gates only;
    no replay, entry or P&L.
  - SPXW expired only on Mondays, Wednesdays and Fridays then. The import (hash
    `2dccf629…`) has 314 sessions. Five were skipped for stale index minutes:
    2021-03-24, 05-10, 07-14, 08-20 and 12-03.
  - Vendor quality run `8fb1d702e13c`: Q2–Q6 pass. Q1 (coverage ≥ 99% on every session)
    fails on three sessions:
    - 2020-03-09 (95.4%) and 2020-03-16 (95.9%): market-wide circuit-breaker halts, with
      quotes back by 09:52 and 09:46 ET.
    - 2020-05-01 (85.8%): vendor quotes missing until 10:24 ET, which covers the entry
      time.
  - **Proposed:** exclude all three with `exclude-sessions` before any replay, as was done
    for 2025-11-28 on the spent holdout. That leaves 311 sessions. The decision is made
    on data quality alone, before any outcome is seen.
- **2003-07-01 → 2019-12-31 SPX/VIX minutes (Test B).** The owner minute CSVs
  (`data/spx_1min.csv`, `data/vix_1min.csv`) fed earlier, unrelated backtests (the old CSV
  backtester and classifier sweep).
  - Per the repo records, none of the three leads above has been evaluated on them.
  - The CSVs are therefore not pristine data, but they are untouched for these questions.
- **Fly geometry for Test B was measured on the 2022–2026 in-sample E0 entries.** That
  data is already seen.
  - Median center distance is 0.93 × the VIX-implied daily move (EM). The zone medians
    are 0.97 / 0.92 / 0.84 for VIX ≤17 / 17–24.5 / 24.5–32.
  - Median wing width is 0.57 × EM. The zone medians are 0.58 / 0.56 / 0.47.

## Definitions (shared)

- **EM** = SPX at 10:00 ET × VIX at 10:00 ET / 100 / √252.
- **Gap direction** = CALL if the official open ≥ the prior session's Cboe SPX close, else
  PUT (as in `gap_direction`).
- **VIX overnight** = VIX at 10:00 ET / prior SPX session's Cboe VIX close − 1. The prior
  close comes from `aux/vol_index_daily.parquet`, via `DailyVol`.
- **VIX agrees**:
  - CALL with VIX overnight < 0, or PUT with VIX overnight > 0.
  - A move of exactly zero counts as not agreeing.
- **Regime**: high = VIX at 10:00 ET ≥ 17, else low.
- **Combined**: high regime and VIX agrees.
- **Years**: calendar years. Test B's partial 2003 is included in the totals but not in
  the per-year counts.

## Test A — real options, 2020-01-02 → 2021-12-31

**Engine.** It uses the research core unchanged:

- profile `vendor_1m` and the current `configs/config.yaml`
- E0 entry (gap direction, first qualifying fly in 07:00–07:45 PT)
- accounting models `midpoint` and `stressed`
- per-session vectors where a skipped day counts as 0
- `EvalParams()` defaults for the bootstrap (5,000 reps, block 5, seed 1)

Sessions the dataset or loader excludes stay excluded and are counted in the report.

**Arms.** All arms use the X1 exit (held to settlement):

| Arm | Trades when |
|---|---|
| A0 | every E0 entry (baseline X1) |
| A-VA | E0 entry and VIX agrees |
| A-RG | E0 entry and high regime |
| A-CB | E0 entry and combined |
| Fade | the opposite-direction fly the same selector picks (`BaselineEntry(direction=...)`) |

## Test B — synthetic settlement payoff, 2003-07-01 → 2019-12-31

No option prices. For each eligible day, it builds two flies at 10:00 ET and scores them
at settlement.

- **Gap fly:** center = SPX₁₀ + s × 0.93 × EM, where s = +1 for CALL and −1 for PUT.
- **Fade fly:** the same center distance on the other side.
- **Wings:** ±0.57 × EM. No strike rounding.
- **Payoff fraction:** p = max(0, 1 − |close − center| / (0.57 × EM)), where close is the
  Cboe SPX daily close.
- **Inputs:**
  - The CSVs are Chicago time, bar end.
  - SPX₁₀ and VIX₁₀ are the closes of the bars stamped 09:00 Chicago time.
  - The open is the first bar's open.
- **Exclusions:**
  - days in either CSV's `stale_days_excluded` list (as recorded in the dataset
    manifests)
  - days missing a 10:00 bar, a Cboe close or a prior Cboe close
  - Cboe early-close days

**Direction excess (cost-neutral).** Comparing gap to fade would also compare more call
flies to more put flies, so the null instead keeps each stratum's call/put mix.

- For day i in stratum S (calendar year × subset under test), with q_S = S's share of
  CALL gaps:
  excess_i = p_gap,i − [q_S × p_call,i + (1 − q_S) × p_put,i]
- This is the gap rule's payoff minus its expectation under shuffling gap directions
  within S. Any cost that depends only on call/put and the day cancels in expectation.

**Uncertainty.** Moving-block bootstrap over days (block 5, 10,000 reps, seed 1).

- For a difference between two subsets, each subset is resampled separately and the
  difference of means is taken.
- p means the share of reps with the stated sign.

## Hypotheses and pass criteria

H-VA1 is primary. The others are secondary.

| ID | Claim | Passes only if all hold |
|---|---|---|
| **H-VA1** (primary) | Gap direction carries information only when VIX agrees | **A1** A-VA − A0, stressed, paired bootstrap p_better ≥ 0.80<br>**A2** mean gap − fade per session (midpoint) is higher on agree days than on disagree days<br>**B1** mean excess on agree days − mean excess on disagree days > 0, p ≥ 0.95<br>**B2** that difference is > 0 in ≥ 10 of the 16 years 2004–2019 |
| H-GD1 | Gap direction beats a direction-blind fly | **A3** Σ(gap − fade), midpoint > 0<br>**B3** mean excess over all days > 0, p ≥ 0.95 |
| H-RG1 | Low VIX is where the strategy fails | **A4** A-RG − A0, stressed, p_better ≥ 0.80<br>**B4** mean excess in the high regime − mean excess in the low regime > 0, p ≥ 0.90<br>**B5** mean gap-fly payoff fraction is lower in the low regime than in the high regime |
| H-CB1 | Combined rule | **A5** A-CB stressed total > 0 and A-CB − A0 p_better ≥ 0.80 |

- **Thin sample.** If Test A has fewer than 30 low-regime E0 entries, A4 is reported but
  not scored, and H-RG1 rests on B4 and B5.
- **What Test B can't show.** It tests information and payoff shape, not profit after
  costs, so A-criteria are the only ones about money.

## Decision rule (fixed now)

- **H-VA1 passes:** VIX agreement goes to a forward test (shadow scoring on paper; no
  change to live trading, config or limits). The rule is "trade the gap only when VIX
  agrees", exactly as defined above.
- **H-VA1 and H-RG1 both pass:** the forward test uses the combined rule instead, if H-CB1
  also passes.
- **H-VA1 fails:** VIX agreement is dropped. None of the report-only cuts below is
  promoted in its place.
- **H-GD1 fails** while H-VA1 passes: report it as a contradiction and run no forward
  test until it's understood.
- **The forward test** needs its own short plan before it starts: start date, rule hash,
  and a minimum of 60 qualifying trades before any verdict. At about 65 combined-rule
  trades a year, that is roughly a year.

## Report-only (no pass/fail)

- Mondays excluded (the in-sample Monday reversal is likely a weekend VIX artifact). This
  matters more in Test A, where about a third of sessions are Mondays.
- VIX agreement of at least 1% instead of > 0%.
- The E0 trailing exit instead of X1, and the `marketable` accounting model.
- Per-year tables for every arm and subset, trade counts, max drawdown.
- Test B by VIX zone (≤17, 17–24.5, 24.5–32, >32) and by |gap| bucket (<0.1%, 0.1–0.25%,
  0.25–0.5%, 0.5–1%, >1%).

## Procedure

1. Owner approves or edits this file, including the three proposed exclusions; it is
   committed. The exclusions are applied with `exclude-sessions`, and the vendor-quality
   gates are rerun and must pass Q1–Q6 before step 2.
2. One script, `tools/research_studies/direction_oos_test.py`, runs both tests and writes
   `reports/research/spx-direction-oos-<date>/` (results JSON, tables, the commit hash of
   this file).
3. All results are reported, pass or fail.
4. **Bugs.** A bug found after running may be fixed and the run repeated, with a revision
   note here describing the bug and both results. Criteria, thresholds, geometry and
   definitions do not change.

## Results (run 2026-10-29, once; plan commit 4c72a35)

Script `tools/research_studies/direction_oos_test.py`; output
`reports/research/spx-direction-oos-20261029/results.json`.

- **Test A data:** dataset hash `a5d3b5e7…` (after the three approved exclusions; quality
  run `d63a3f4a002d` passes Q1–Q6). 308 sessions scored (3 more excluded by the loader),
  215 E0 entries, 51 of them at VIX < 17.
- **Test B data:** 4,090 days, after dropping 27 stale-CSV days and 38 early closes. Early
  closes were detected as days whose last SPX bar is before 13:30 Chicago time; all 38 are
  holiday eves. The two subsets in a difference use bootstrap seeds 1 and 2.

| Criterion | Result | Pass |
|---|---|---|
| A1 A-VA − A0, stressed | −$5,407 (A-VA −$15,500 vs A0 −$10,093), p_better 0.22 | no |
| A2 mean gap − fade per session, mid | agree −$64, disagree +$21 | no |
| A3 Σ(gap − fade), mid | −$13,540 | no |
| A4 A-RG − A0, stressed (51 low-regime entries, scored) | +$6,744, p_better 0.99 | yes |
| A5 A-CB stressed total | −$9,808, p_better vs A0 0.55 | no |
| B1 excess, agree − disagree | +0.0133 of max payoff (CI90 +0.0046…+0.0224), p 0.99 | yes |
| B2 years with agree > disagree | 11 of 16 | yes |
| B3 mean excess, all days | +0.0074 (CI90 +0.0031…+0.0119), p 0.998 | yes |
| B4 excess, high − low regime | +0.0159 (CI90 +0.0071…+0.0253), p 0.999 | yes |
| B5 mean gap payoff, low vs high regime | 0.092 vs 0.129 | yes |

**Verdict.**

| Hypothesis | Result | Failed on |
|---|---|---|
| H-VA1 | **FAIL** | A1, A2 |
| H-GD1 | FAIL | A3 |
| H-RG1 | **PASS** | — |
| H-CB1 | FAIL | A5 |

Per the decision rule, VIX agreement is dropped, and no report-only cut is promoted.

**Not covered by the plan.** It names no forward-test path for H-RG1 passing alone. Any
such test is a new owner decision.

**Notes.**

- On real 2020–21 options the fade beat the gap.
  - At mid, the fade fly made +$16.2k and the gap fly (A0) +$2.7k.
  - The reversal was concentrated on VIX-agree days.
- In the 2003–2019 synthetic payoffs, all three effects appear, at roughly 40% of the
  in-sample size per day.
