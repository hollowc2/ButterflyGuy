# Improving SPX Sharpe: a second research pass

September 13, 2026 · Addendum to [the exit-policy report](REPORT.html)

**Recommendation:** prioritize better entry economics, same-expiry strike placement, and reliable exit signals before tightening profit floors. None of the new ideas below has demonstrated an out-of-sample Sharpe improvement. The existing protector defaults remain rejected; the baseline itself has not established a positive net edge.

This pass reviews the frozen March 17–September 11 evidence, recomputes descriptive diagnostics from the existing replay CSV, inspects local selection logic, and researches primary sources. It does not run a new strategy backtest, acquire market data, or change trading code, configuration, limits, recording, or services. All examined history is development data. This extends the existing report rather than replacing its frozen findings.

## What the evidence actually says

The 33 validated monitoring `mark_v1` trades have baseline net P/L −$533 and protector P/L −$1,156. Sample standard deviation of trade-dollar P/L is $424.16 versus $122.39. Mean divided by sample standard deviation is **−0.0381 versus −0.2862**. These are unannualized trade-dollar diagnostics, not account Sharpe ratios. Reduced variability does not compensate for the protector's more negative mean.

The baseline's $2,288 winner contributes **85.4% of $2,680 gross positive P/L**. Its average win/loss implies a descriptive break-even win rate of **21.0%**, against 18.2% observed. The protector needs **37.2%**, against 21.2% observed. These thresholds hold observed average win/loss fixed and are not forecasts. Increasing win rate alone is the wrong objective.

At the report's quarter-concession plus 0.05-point exit stress, baseline loses $1,313: $780 more than marks, or **$23.64 per entry averaged over all 33 entries**. Its total break-even improvement is $39.79 per entry under that stress, versus $16.15 at marks. Better execution is material, but recovering that modeled exit drag alone still leaves the original negative expectancy. Entry execution remains fixed, so the stress is incomplete.

The original report's main strengths are baseline parity, visible unresolved outcomes, and its refusal to treat coarse collector results as validation. Its remaining research gaps are calendar-day account returns, marked equity drawdown, executable fills, full-session counterfactual coverage, and independent settlement evidence. The quoted 60-entry prospective window is a useful operational minimum, not a statistical power guarantee for such a concentrated payoff distribution.

## Ranked hypotheses

### 1. Match the center and width to remaining-session movement

**Why:** the checked-in configuration uses VIX anchoring and VIX width buckets. VIX measures 30-day expected volatility; that horizon can differ substantially from today's remaining-session risk. Cboe also explains that VIX1D blends today's and tomorrow's expirations, with weights shifting during the day. Consequently, simply substituting VIX1D into the VIX formula is not a clean solution. [Cboe explanation](https://www.cboe.com/insights/posts/what-the-vix-and-vix-1-d-indices-attempt-to-measure-and-how-they-differ)

**Experiment:** first change only the center's movement estimate to one derived from the same-expiry chain at entry. Keep direction, eligible widths, costs, and exits fixed. Then, in a separate experiment, choose widths relative to that estimate. Record normalized center distance `abs(center − spot) / remaining_move` and width `wing_width / remaining_move`. An ATM straddle is a price-based movement proxy, not automatically one standard deviation; use a consistent model/calibration and exact settlement horizon.

**Falsify it:** reject if the apparent benefit disappears with modest movement-estimate perturbations, realistic spread costs, or removal of one dominant day's influence. Full entry chains and synchronized spot are required; held-leg paths cannot price alternative centers. This is the highest-priority structural hypothesis, not an established edge.

### 2. Rank by expected net payoff rather than target reward/risk

**Why:** `butterfly_selector.py` filters around a target center, then prefers reward/risk nearest its target, with a width tie-break. Reward/risk describes potential payout versus cost; it does not contain the probability of receiving that payout.

For an equal-wing long butterfly held to settlement, payoff in option points is `max(0, width − abs(S_T − center))`. A research score is `100 × (expected payoff − executable debit) − unembedded fees`. Use a physical return distribution estimated only from prior observations; option-implied probabilities include risk premia and are not a free source of alpha. The Fed explains why option-implied probabilities can differ from actual probabilities. [Federal Reserve discussion](https://www.federalreserve.gov/econresdata/notes/feds-notes/2014/forecasting-stock-market-crashes-is-hard-especially-future-ones-20140507.html)

**Experiment:** compare the existing selector with one simple, regularized score on the same candidates. Include a no-entry outcome if estimated net edge cannot clear costs and estimation uncertainty. For the existing early-exit policy, a settlement score is only an entry proxy: validate complete policy P/L with chronological paths before accepting it. Do not mix a new selector and new exit in the first test.

**Falsify it:** reject if forecast probabilities are poorly calibrated, the improvement requires a complex model fitted to these 33 trades, or selecting ostensibly higher-edge candidates lowers prospective net expectancy. Substantial additional history is needed.

### 3. Require persistent evidence for discretionary profit exits

**Why:** the August 3 dip that triggers the protector reverses approximately 2.6 seconds later. That identifies sensitivity to transient marks, but does not prove that the dip was erroneous or that delaying would generally help.

**Experiment:** compare one predeclared elapsed-time confirmation rule with the same unconfirmed profit policy. Treat confirmation and quote-quality filtering as separate ablations. Fresh synchronized legs, spread plausibility, and executable complex-order quotes should govern signal confidence. A profit-floor trigger remains distinct from its eventual fill. Safety exits retain their existing behavior in any proposed implementation.

**Falsify it:** reject if delayed exits enlarge ordinary losses more than they preserve legitimate winners, or if the improvement exists only on August 3. Do not choose a delay just longer than 2.6 seconds. Monitoring stops at actual exit, so later hypothetical outcomes are censored; full-session observation is required. Confirmation can increase losses during fast moves.

### 4. Exit on deteriorating butterfly geometry, not just a percentage of the peak

**Why:** the same peak drawdown can occur with spot approaching the profitable center or moving away beyond a wing. Their future payoff opportunities differ. A price-only floor ignores this distinction.

**Experiment:** retain the baseline except for one discretionary exit conditioned on normalized center distance and remaining time. For example, test whether continuation becomes unattractive when spot moves persistently away and the estimated remaining movement is small relative to its distance from the profitable region. Choose a small rule family in development; avoid optimizing a large grid of distances and times. Use contemporaneous spot and expiry-specific movement estimates, not eventual highs/lows or settlement.

**Falsify it:** reject if it truncates recoveries or merely shifts losses into settlement. A more ambitious continuation-value model should wait for considerably more data. This idea requires synchronized spot plus paths through close and executable exit evidence.

### 5. Add an execution-cost entry gate

**Why:** the modeled cost penalty is large relative to expectancy. A cheap-looking butterfly can be cheap only at a synthetic mark.

**Experiment:** apply a cost-budget gate to the existing entry candidate, without reranking or changing exits. Record spread concession relative to debit and width, quote age, and available size. Compare all accepted and skipped opportunities on the same calendar. Where available, use complex-order quotes and paper observation of achievable prices; a sum of individual-leg bids is a stress bound, not a demonstrated spread fill.

**Falsify it:** reject if skipped trades contain enough tail winners to erase savings, or if the benefit depends on assuming every passive limit fills. Model unfilled orders and adverse selection explicitly. Existing held-leg evidence does not establish entry liquidity or quote sizes.

### 6. Condition entry on scheduled events and observed directional conviction

**Why:** Federal Reserve research finds higher insurance prices around major scheduled macro releases. This supports distinguishing event regimes; it does not establish that avoiding events improves this butterfly strategy. [Federal Reserve daily-options research](https://www.federalreserve.gov/econres/ifdp/the-price-of-macroeconomic-uncertainty-evidence-from-daily-options.htm)

**Experiment:** test an event-time exclusion first, using release schedules known at entry. Treat already-released morning news separately from an announcement still ahead. Separately test one simple pre-entry direction-confidence gate using only the opening path available at that moment. A directional butterfly can overshoot its center on a strong trend, so “stronger trend” need not mean “better trade.”

**Falsify it:** reject if event exclusions remove the main positive tail or if results hinge on one event class with a handful of trades. Do not optimize dozens of weekdays, clock times, indicators, and event combinations. Missing sessions remain missing, not zero-return days.

### 7. Normalize risk without increasing the position limit

**Why:** one contract does not mean constant dollars at risk across debits and widths. Volatility-managed portfolio research motivates testing conditional risk allocation, but its findings for other portfolios do not establish a benefit for nonlinear 0-DTE butterflies. [Moreira and Muir](https://www.nber.org/papers/w22208)

**Experiment:** under the existing one-contract constraint, study accept/skip decisions based on pre-entry debit risk and uncertainty. Compare at the same fixed capital budget. Do not simulate fractional SPX butterflies, increase size, or introduce XSP as if it had identical execution economics. Constantly scaling all positions changes dollars, but not idealized Sharpe when returns and costs scale proportionally.

**Falsify it:** reject if risk normalization only concentrates the portfolio in cheap, remote butterflies or loses positive expectancy after costs. Lower risk cannot by itself repair a negative edge.

### 8. Diversify only after finding a second net-positive component

**Experiment:** later test a distinct entry-time or payoff component against the baseline on aligned daily net returns, at fixed total capital and without adding to current trading limits. SPX, XSP, and NDX labels do not establish diversification. Dependence on the same market path and joint tail losses matters more than instrument count.

**Falsify it:** reject if covariance benefits disappear after fees or during stressed sessions. Defer this until each component has independent positive net evidence. Partial profit-taking is also deferred: all historical positions are one butterfly, so selling half is not an executable alternative under the current position limit.

## Measure the target correctly

Build daily account excess returns from a fixed, documented research capital allocation and marked equity, with fees, spread costs, cash interest, financing where applicable, and the appropriate cash benchmark. Include verified no-entry sessions. Do not annualize trade observations using `sqrt(252)` or omit skipped days to make an entry filter look better. Report the capital convention alongside annualized Sharpe; serial dependence requires an adjusted uncertainty estimate rather than blind square-root annualization.

Keep net return, expectancy, profit factor, win rate, average win/loss, trade count, exposure, marked and realized drawdown, and tail concentration beside Sharpe. A numerically higher negative Sharpe is not a profitable strategy. Also inspect expected shortfall and the paired performance of the same baseline top-winner IDs.

Maintain a registry of every attempted rule, parameter, and combination. Use paired daily block bootstrap intervals for the candidate-minus-baseline comparison, and account for selection and nonnormal returns; the Deflated Sharpe Ratio literature addresses these specific biases. With only 33 trades and one dominant winner, neither bootstrap nor deflation creates missing tail evidence. [Bailey and López de Prado](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)

## Proposed next research sequence

1. Establish complete full-session quote/spot coverage, post-signal fill observations, settlement attribution, and verified no-entry sessions. Recording changes are a separate implementation task; none was made here.
2. Freeze baseline provenance and costs. Test hypotheses 1, 3, and 5 independently first. Keep hypothesis 2 as the next structural study once distributions and candidate-chain history are adequate. Preserve all failures, censoring, and costs.
3. Use available historical evidence only for development and feasibility. Do not declare September a holdout. Pre-register the selected rule and cost model before a future evaluation window beginning no earlier than September 14, and only after coverage is operational.
4. Retain the prior report's at-least-three-month/60-entry window as a minimum observation floor. Predeclare the analysis date or sample stopping rule and a power-based extension plan; no repeated tuning or stopping when Sharpe turns positive. Fewer entries from filters may require much longer.
5. A candidate should show positive net expectancy under primary and reasonable cost stresses, improved paired daily Sharpe with uncertainty reported, acceptable marked drawdown, and tail retention. The prior 80% same-ID top-five winner retention rule remains a development guardrail; it is not proof of future tail capture. Inconclusive evidence means continue observation, not promote.

**Decision:** refine the entry/geometry and execution hypotheses; do not promote any new policy on this pass. The most promising direction is preserving useful payoff opportunities while avoiding entries whose probability-weighted payout cannot cover their costs.

## Reproducibility and limits

Local checkout: `e2ba77284370b7edc7c7e94d659fe707a226f834`. Existing uncommitted research and graph files were present before this pass. No attribution of that checkout to the running image is implied.

Diagnostic input: `results/trade_results.csv`, SHA-256 `86e52c277f92f4dac0f4d6c210decd6c730b6f47b7ac5c76fee7ad6e075eb9cb`. Filter `source=monitor`, `fill_model=mark_v1`, resolved statuses, and each specified `policy`/`stress`; both policies contain the same 33 IDs. Compute sample standard deviation with denominator `n−1`; concentration is largest positive P/L divided by sum of positive P/L. Descriptive break-even win rate is `abs(average_loss)/(average_win+abs(average_loss))`. Dollar values are after the original replay's commission treatment.

The additional diagnostics were recomputed using Python's standard-library CSV/statistics tools. No new counterfactual exits, alternative entries, Sharpe estimate, or candidate backtest was produced. The original six replay tests were not rerun: the replay, raw evidence, and trading logic were unchanged. This is a research addendum, not a replication of the original raw-data parity audit. External sources were consulted September 13, 2026 and support mechanisms/methodology, not claimed returns for this system.
