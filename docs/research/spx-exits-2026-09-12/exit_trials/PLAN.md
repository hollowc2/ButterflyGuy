# Exit trials fixed before execution — September 13, 2026

Research only: SPX same-day long debit butterflies, Schwab paper monitoring quotes,
July 22–September 11, 2026 inclusive. All 33 `mark_v1` entries; original direction,
strikes, one-lot quantity and fee-inclusive entry held fixed. No live changes.
History is already examined development data, not out-of-sample evidence.

Baseline: frozen deployed `peakvaluetrailer` 60%/90%/75%, no absolute stop.
First require exact baseline P/L/reason parity against the ledger and original
replay CSV. Reuse immutable source and raw files from the parent research folder.

Primary, isolated alternatives:
1. `trail_60`: change only late-morning peak drawdown from 90% to 60%.
2. `stop_50`: enable the existing 50% debit loss stop; retain baseline trailer.
3. `confirm_5`: require the same discretionary drawdown reason to remain observed
   for at least 5 seconds, with at least two observations and no consecutive gap
   over 10 seconds. Recovery or regime/reason change resets the timer. This is
   confirmation of observed breaches, not proof of continuous market prices.
   Hard stops and end-of-day exits bypass confirmation. Baseline trailer retained.

Predeclared one-dimensional sensitivities, not additional primary candidates:
late-morning drawdown 50% and 70%; absolute loss 40% and 60%; confirmation 2 and
10 seconds. No combinations or parameter tuning after seeing the results.

Fill assumptions: original mark, 25% and 50% of positive mark-to-synthetic-bid
concession plus 0.05 points, full concession plus 0.10 points, and next-observation
50% concession plus 0.05 latency diagnostic. Exit commission 4 × $0.65, rounded
as in deployed paper code; entry commissions already embedded. No extra exit
commission for conditionally reused recorded settlement. Costs are assumptions,
not measured fills; synthetic negative fills in harsh stresses are diagnostic.
Report an additional $5.20/entry fee sensitivity, not an attested historical bill.

Never fill at the threshold, interpolate missing quotes, append a final-quote
liquidation, or substitute collector paths. Reuse recorded settlement only under
the original near-close coverage rule. Missing later paths and post-signal fills
remain censored. Report all attempted entries and paired resolved ID coverage;
an incomplete comparison cannot establish full-cohort candidate performance.

Report P/L, expectancy, sample trade-P/L variability (not account Sharpe), win
rate, profit factor, average win/loss, realized drawdown, holding exposure, costs,
monthly and directional breakdowns, largest-winner concentration, and same-ID
baseline top-five tail retention. Account returns, daily Sharpe and marked equity
drawdown are unavailable. For complete primary comparisons only, descriptive
paired-day bootstrap mean P/L differences (10,000 draws; seed 20260913) illustrate
uncertainty; no multiple-test correction or confirmatory inference is claimed.

Reject observed deterioration; retain any apparent improvement only as a research
candidate. A future untouched window and complete recording are required before
promotion. All experiments and sensitivity results remain visible.

Verification: synthetic tests for threshold changes, never-profitable stops,
confirmation recovery/gaps/regime changes, hard-exit bypass, fee/latency behavior,
and censoring; complete historical baseline regression; focused pytest and Ruff.
Run graphify update after code edits. Preserve existing unrelated workspace work.
