# XSP quiet-day iron and OTM-body research — November 12, 2026

**Decision: reject the exact completed relative-calm policies under the frozen
screen. Preserve ATM four-point iron flies as a fragile observation, not a
validated edge or a paper-trade candidate.** No runtime settings, orders, tokens,
or services were changed.

This follows the [completed independent XSP research](xsp-independent-research-2026-11-12.md).
The owner explicitly added credit iron flies, ATM entries on expected mellow days,
and both directional and neutral OTM targets. These are new construction and
fixed-time quiet-regime hypotheses, not reruns of MR1/MR2/T1/T2.

## Bounded experiments and changes in evidence

All three runs use genuine XSP 0-DTE minute option quotes for January 2 through
September 28, 2026, with native published Cboe XSP settlements. All dates are
previously inspected development evidence. Neither chronological splits nor
rolling feature thresholds make this a fresh holdout.

1. **`run-01`: parity-price signal, absolute realized/implied gate.** Require a
   first-hour volatility forecast no greater than 75% of the implied remaining
   move, little net drift, and no named scheduled major release. Of 185 archive
   sessions, 162 have covered signal prefixes; **zero quiet days** qualify.
2. **`run-02-spx`: independent observed SPX/10 signal, unchanged absolute gate.**
   Material new evidence: the first filter cannot test the proposed strategies,
   and independent recorded SPX prices can distinguish proxy artifacts from the
   quiet-rule restriction. The preserved `local_support_v1` snapshot covers
   March 13–September 25. Of 185 archive sessions, 122 have covered prefixes;
   again **zero quiet days** qualify. The minimum ratio belongs to an excluded
   FOMC day. This does not establish that parity noise caused the first failure.
3. **`run-03-relative`: final, separately frozen relative-calm hypothesis.**
   “Mellow” now means normalized first-hour volatility no higher than the lower
   tercile of the **prior 20 feature-covered sessions**, still with little net
   drift and no named major release. This removes the distinct implied-premium
   overpricing condition rather than tuning its threshold. Twenty covered
   sessions become warmup; 63 lack sufficient independent-price prefixes;
   **102** remain eligible, including **30 quiet days** and 72 valid no-signals.
   Scored quiet trades run April 15–September 22. The campaign stops here.

Every run froze its rules before evaluation and retains its manifest, features,
journal and summary. Three runs × 24 cells = **72 correlated cells**, not 72
independent ideas. The first two runs supply no quiet-day profitability evidence.
Frozen source copies preserve their earlier runner implementations.

## Exact shared mechanics

- Signal at **10:30 ET**, using completed `[09:31,10:30)` observations, at least
  54 of 59 minutes, boundary/internal gaps no greater than two minutes, and an
  observed last minute at 10:29. SPX ticks are divided by ten, grouped to the last
  observation per minute, labeled at minute start and available at minute end.
  This is a cross-index proxy, **not native intraday XSP spot**.
- Squared price increments divided by elapsed minutes estimate the first-hour
  variance rate; no missing minute is interpolated. Normalize volatility by
  the last index proxy before comparing prior-session rates. The current
  observation is appended to history only after deciding its threshold.
- Quiet requires absolute first-to-last change divided by total absolute
  increments at most 30%, and no calendar-visible CPI, NFP, PCE or FOMC date.
  The event table does not establish an absence of other catalysts.
- Four arms: unconditional ATM benchmark, quiet ATM, quiet directional OTM body,
  quiet neutral pair. Direction follows the first-hour signed drift; the target
  offset is half the 10:29 ATM XSP straddle midpoint. The pair places one body on
  each side. Choose the nearest listed strike, lower on ties, constrained to be
  strictly on the intended side of the signal proxy. No alternative strike
  search. **OTM describes the body; wings can be ITM.**
- Two symmetric widths, 2 and 4 XSP points; compare CALL, PUT and credit IRON
  constructions at the same centers. Each iron buys a lower put and upper call
  and sells one call and put at the center. Its terminal cash is the long-fly
  tent minus width. Its effective debit is `width - opening_credit`.
- Entry is the first usable simultaneous snapshot strictly after 10:30 and by
  10:32. Require transaction-needed displayed sizes, aggregated by contract and
  buy/sell side for pairs. Purchased wings can have zero bid/size if asks are
  valid and sufficiently sized. Sold legs need positive bids and bid size.
  Crossed, negative or nonfinite prices are rejected. Each debit/credit must
  lie strictly between zero and width before stress.
- Always hold accepted positions to **native published cash settlement**.
  No closing fill, fee, target, stop or future quote admission filter. A missing
  settlement remains unresolved; the final run has none.
- Model $0.65 per gross opening contract and $0.05 adverse opening price stress
  per fly: $2.60 fees + $5 stress for one fly, doubled for the pair. No netting.
  Two overlapping tents may produce a plateau; a netted condor implementation
  has not been tested. Broker/exchange/exercise charges are unverified.

## Final relative-calm findings

The strongest candidate is **ATM IRON, four-point wings**: 30 completed trades,
**+$405 stressed net**, +$13.50 per trade, 60% winners, profit factor 1.29.
Average stressed initial risk is $224.33 per fly; mean trade risk units are
+0.0638 R. This is not a funded-account return. Terminal-outcome drawdown is
$389.40; intraday drawdown is not measured.

This cell fails the prechosen checks:

- First archive half: **−$44.40**, nine trades; second: **+$449.40**, 21 trades.
  The fixed split is May 15, not the median accepted trade date.
- Removing the three largest winners changes +$405 to **−$171.20**. Those wins
  are May 29 (+$207.40), April 20 (+$192.40) and July 22 (+$176.40).
- The same-form/width unconditional ATM benchmark loses $877.20 over 102
  eligible sessions. The quiet strategy improves the paired daily total by
  $1,282.20, including 72 valid no-trade days. On the 30 traded dates its
  construction is identical to the benchmark; this tests participation.

Other IRON cells on the same 30 quiet dates:

- ATM, width 2: **−$18.00**.
- Directional OTM, width 2: **−$419.00**; width 4: **−$351.00**.
- Neutral OTM pair, width 2: **−$519.00**; width 4: **+$36.00**. The latter has
  **−$562.40** after removing its three biggest winners, a −$561.80 first half,
  $426.93 average initial risk and $739.20 terminal drawdown. It uses two flies.

All CALL and PUT quiet-day cells lose after stress. None of the 18 final
candidate cells passes the frozen screen. On 29 exactly matched quiet ATM
width-four snapshots, IRON improves net by $393 versus CALL and $410 versus PUT
in aggregate. Those are modeled component opening-cost differences, not
demonstrated package fills. Different admissions make unpaired cell totals
inappropriate evidence for a construction advantage.

## Verification, artifacts and next work

All **1,140 completed final-run cash records** reconcile independently to raw
opening quote sides/sizes and individual option intrinsic settlement cash.
The final journal has 4,440 records including no-signals and exclusions. Earlier
run cash reviews reconcile another 960 and 726 completed records; these reuse
dates and are not independent samples.

- [Standalone interactive report](../../reports/research/xsp-quiet-flies-2026-11-12/index.html).
- [Small retained decision receipt](xsp-quiet-flies-2026-11-12.summary.json).
- Final [frozen specification](../../reports/research/xsp-quiet-flies-2026-11-12/run-03-relative/specification.json),
  [summary](../../reports/research/xsp-quiet-flies-2026-11-12/run-03-relative/summary.json),
  and [cash review](../../reports/research/xsp-quiet-flies-2026-11-12/run-03-relative/cash-review.json).

Recorded checks: **24 focused tests** and full-repository Ruff pass. Graphify
AST update retains its pre-existing missing SQL-parser dependency warning; this
campaign changes no SQL. Browser layout/control checks are recorded with the
private report artifacts.

Do not tune width, thresholds or exits on these 30 outcomes and present that as
new validation. A useful subsequent experiment needs fresh signal/quote data or
observed complex-order fill evidence with complete costs. The quiet ATM iron
observation merits retaining, but the exact policy is not a paper-trade candidate
under this study's gates. Research does not authorize runtime activation.

Owner follow-up: the specifically mixed **lower put fly + upper call fly**
“Batman” idea is [queued in the discovery journal](strategy-discovery-journal.md#2026-11-12--quiet-day-xsp-flies-retained-mixed-callput-batman-idea-queued).
Completed neutral-pair cells used CALL/CALL, PUT/PUT or IRON/IRON, not this mixed
construction. Matching strikes gives the same gross expiry payoff shape, but
the mixed quote costs and a prospective move-regime entry remain untested.

Reproduce with fresh output paths, preserving the three separate rules:

```bash
uv run python -m tools.research_studies.xsp_independent.quiet_flies --out /tmp/xsp-parity-new --freeze --run
uv run python -m tools.research_studies.xsp_independent.quiet_flies --out /tmp/xsp-spx-new --signal-source spx --freeze --run
uv run python -m tools.research_studies.xsp_independent.quiet_flies --out /tmp/xsp-relative-new --signal-source spx --quiet-gate relative --freeze --run
uv run python -m tools.research_studies.xsp_independent.review_quiet_flies --run /tmp/xsp-relative-new
uv run pytest tests/test_xsp_quiet_flies.py -q
```
