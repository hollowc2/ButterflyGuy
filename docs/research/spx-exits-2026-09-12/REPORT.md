# SPX exit-policy research — September 12, 2026

**Decision: reject the existing `profitprotector` defaults as a replacement.**
They reduce realized drawdown at paper marks, but lower cost-adjusted expectancy
in the fully reproduced `mark_v1` cohort and eliminate its dominant winner.
The wider history is useful development evidence, but cannot validate a change:
its execution models, quote coverage, and historical settings are inconsistent.
No candidate was enabled, deployed, or tuned; live settings and services were unchanged.

**The most reliable comparison is all 33 `mark_v1` trades, July 22–September 11.**
Monitoring-quote replay matches every recorded baseline P/L and exit reason;
all exit timestamps are within ten seconds. One terminal cash-settlement payoff
is reused from the ledger, not independently re-derived from broker settlement.
Entries, strikes, quantity, quote path, and fee treatment are identical between
the policies. The only change is the exit-policy selector.

- Baseline → protector net P/L: **−$533 → −$1,156**; expectancy:
  **−$16.15 → −$35.03/trade**, a deterioration of $18.88/trade.
- Win rate: 18.18% → 21.21%; profit factor: 0.834 → 0.455.
  Average win: $446.67 → $138.00; average loss: −$119.00 → −$81.62.
- Closed-trade dollar drawdown: $2,053 → $1,264, down 38.4%.
  Holding exposure: 60.18 → 27.15 hours; mean hold: 109.42 → 49.37 minutes.
- Excluding each policy's largest one/two/five positive winners gives baseline
  P/L −$2,821/−$3,069/−$3,204 and protector −$1,500/−$1,767/−$2,017.
  Removing the **same baseline winner IDs** instead gives protector
  −$1,144/−$1,192/−$1,892. These diagnostics expose concentration; they do not
  justify discarding the legitimate winner in the primary comparison.

**The six doubled-then-lost trades save only $464 in aggregate.** Their original
P/L totals −$449; the protector produces +$15. Individual baseline → protector
results are July 23 −$178 → −$24; July 29 −$176 → −$176; August 6 −$51 → −$3;
August 13 −$1 → +$89; August 26 −$3 → +$72; September 9 −$40 → +$57.
Identification uses recorded peaks; all simulated peaks and fills use chronological
leg quotes. A floor is a trigger, not a guaranteed fill price.

August 3, trade 212, is decisive: entry 2.09, recorded settlement 24.97,
baseline +$2,288. After an observed peak of 3.22, monitoring quotes fall to 2.00
at **10:04:09.964 ET** (synthetic bid 1.90, ask 2.10). The protector's break-even
floor exits at 1.97 after commission, **−$12**. Quotes rebound to 2.17 about
2.6 seconds later. The slower collector misses this dip and incorrectly suggests
the protector retains the winner. July 31's +$248 becomes +$48. June 22's
+$2,258 survives both policies, conditional on the recorded settlement payoff.
June 16's recorded +$2,040 has a protector quote exit of −$8, but its current-policy
baseline is unresolved; it is explicitly excluded from paired aggregates.
The ten largest recorded winners, including unavailable early monitoring paths,
are all listed in [focus_trades.csv](results/focus_trades.csv).

**Execution costs do not rescue the validated comparison.** Recorded entry prices
retain embedded commissions; each simulated quote exit deducts only its own
four-contract commission ($2.60 before deployed fill rounding). Settlement has
no added exit commission, matching paper code. Using 25% of the mark-to-synthetic-bid
concession plus 0.05 points gives net P/L −$1,313 → −$1,934. At 50% plus 0.05,
it is −$1,951 → −$2,563, and drawdown **worsens** from $2,322 to $2,613.
Full legwise crossing plus 0.10 produces −$3,374 → −$3,979.
These are bounded assumptions, not measured complex-order fills. Negative synthetic
bids make full crossing particularly severe. Entry execution is held fixed by design.

Next-observation latency cannot be validated across this cohort: monitoring ends
at the actual exit signal, leaving only one paired resolved trade. That row is
not performance evidence. Collector latency results remain available separately,
but inherit failed baseline parity. Historical industry fees are not attested;
[Schwab's pricing guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors)
lists industry fees, including proprietary index-option fees, in addition to
commission. A separate $5.20/trade fee stress and uncertain legacy-entry-fee
sensitivity are included; neither is presented as the actual historical bill.

**The entire March 17–September 11 ledger was attempted, with missing outcomes
kept visible.** It contains 108 closed trades and the prior recorded +$1,835.
The complete original ledger and monthly metrics are preserved. Collector data
contain 117,875 held-leg rows across all 108 entries; 18 incomplete/duplicate
timestamp groups are rejected. Monitoring contains 552,312 rows for 64 entries,
beginning June 4; 44 earlier trades have no monitoring rows. Collector gaps reach
478 seconds; monitoring's largest gap is 269 seconds. In `mark_v1`, monitoring
gaps reach 118 seconds and initial monitoring lag reaches 42.8 seconds. Coverage
is an audit of held-entry quote paths, not a claim of complete chains or no-trade
session coverage.

The explicitly labeled `best_available` aggregate uses monitoring where present,
otherwise collector, without stitching paths or selecting on outcomes. It resolves
**98 paired trades**, producing −$1,787 → −$1,417, expectancy −$18.23 → −$14.46,
and drawdown $3,957 → $2,809. Monthly paired counts and P/L (baseline → protector):
March 8, −$775 → −$260; April 13, −$1,129 → −$453; May 15, +$2,692 → −$128;
June 16, −$409 → +$1,509; July 21, −$2,423 → −$1,536; August 20, +$657 → −$519;
September 5, −$400 → −$30. Every requested monthly metric is in
[summary.csv](results/summary.csv). Ten unresolved pairs prevent a valid
108-trade counterfactual total; excluded historical winners make this aggregate
selection-biased. Its modest improvement cannot override the validated cohort.

Keeping sources separate yields 95 collector pairs (−$200 → +$1,187) and 62
monitor pairs (−$2,575 → −$576). These are diagnostic subsets, not substitutes
for the complete ledger. The collector baseline has material P/L errors over $5
in 71 of 95 resolved trades, including 20 of 30 `mark_v1` trades. Its apparent
positive candidate result fails the required validation gate.

**Material discrepancies were investigated before choosing the evidence tier.**
Of 25 legacy monitoring quote exits, 24 reproduce the recorded signal mark;
their ledger fills differ because the historical exit ladder kept running.
For example, June 4 signals at 1.25 but records 1.12 after a ladder; immediate
current-model replay fills 1.22. June 5 signals at 1.17, but a roughly five-minute
ladder closes at 0.67. June 23 remains unexplained: current replay triggers at
13:21:42 ET, mark 0.72 and reconstructed peak 7.33, whereas the ledger signals
later at 2.20. It is not attributed solely to fees. Historical runtime-state or
config provenance is insufficient to resolve it. Two historical absolute stops
and six pre-close exits also conflict with today's settings; repository history
documents pre-close-setting changes in June. None of these legacy results is
treated as validated current-policy performance.

**The deployed baseline is attributable by image and source content.** Running
image `sha256:ac6d1e93399b7e4b41ca5e7ac70109eab8987b4506066bcfbb7aed22c08077ac`
started September 12 at 21:33:14 UTC, executing `python -m butterfly_guy.scripts.run_live`
in `/app`, whose default loads `configs/config.yaml`. The effective loaded YAML
selects `peakvaluetrailer`, 60%/90%/75% regime drawdowns, and the unchanged protector
defaults. The checkout is `929429978a09c153afb5260771eff84386762ce4`, but **five package
files differ from that checkout**, including position manager/service and live runner.
The image has no revision label. Consequently the checkout SHA is not asserted
as the running source version; all 99 running Python files are hash-frozen.
The local profit/position/execution source matches the running package, while
several local backtest files differ. Full provenance and commands are in
[README.md](README.md) and [manifest.json](manifest.json).

**Prospective plan:** all history through September 11 is examined development
data; September is not a holdout. Preserve this rejected default configuration
as a fixed comparator. Before a separate future study, pre-register a 60-entry,
at-least-three-month observation window beginning no earlier than September 14,
with no interim tuning. Require complete same-frequency held-leg observations
through session close for both hypothetical exits, post-signal fill observations,
and fee/settlement attribution. Existing monitoring stops at actual exit; closing
that coverage gap would require a separately authorized recording change, which
this task did not make. Set a ≥99% expected-observation coverage gate and report
all missing sessions rather than silently replacing them. Evaluate paired net
expectancy, realized and marked drawdown, tail retention, monthly consistency,
and a day-block bootstrap uncertainty interval. A candidate must improve net
expectancy under primary and spread stresses, avoid worse drawdown, and retain
at least 80% of the baseline top-five positive-winner P/L on the same IDs.
These are future decision criteria, not retrospective parameter selection.

The exit-only gate failed, so config-backed `run_backtest_db.py` confirmation was
**not warranted or run**. Explicit `--direction auto` commands for that later,
separate experiment are documented. Six focused tests pass, including all 33
ledger reproductions; repository lint passes with immutable source evidence
excluded. Quote marks remain unproven executable fills, settlement evidence is
conditional, and reported drawdown is closed-trade rather than intratrade equity
drawdown. Nothing here authorizes a trading change.
