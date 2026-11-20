# XSP independent butterfly research — completed November 11–12, 2026

**Decision: reject the exact completed policies described below. No validated
profitable XSP strategy emerged.** The initial positive early-exit subsets were
incomplete; their complete-cohort settlement-fallback results were negative.

Read this record before proposing another XSP butterfly investigation. Reuse the
existing experiments instead of presenting these hypotheses as new ideas.
Also read the subsequent [quiet-day iron and OTM-body study](xsp-quiet-flies-2026-11-12.md):
its three frozen runs include two zero-signal absolute filters and a 30-session
relative-calm comparison. No cell passed its prechosen robustness screen.
Reproduction, mechanics debugging, or an explicitly requested rerun is fine.
Reopening a rejected idea needs a documented material change in evidence,
execution assumptions, or mechanics; merely changing a threshold on this same
inspected period does not supply independent validation.

The owner requested butterfly-only ideas independent of the SPX strategy, with
research reports delivered as standalone HTML. This campaign changed no runtime
configuration, trading limits, routing, credentials, or services.

## Scope and shared assumptions

- Instrument: genuine XSP 0-DTE option quotes; symmetric long butterflies,
  `+1 lower / -2 body / +1 upper`, calls or puts, widths **2 and 4 XSP points**.
- Window: **2026-01-02 through 2026-09-28 inclusive**, 185 archive sessions.
  Every result is retrospective development evidence. The same dates informed
  later exit hypotheses and the selected MR2/width-four follow-up. They must
  never be described as an untouched holdout.
- One butterfly per entry/candidate/session. Equal lots have unequal dollar
  risk; no funded-account return or portfolio-diversification claim was made.
- Signals use an approximate zero-carry forward derived from XSP option
  midpoints: median `K + call_mid - put_mid`, at least three of up to five
  lowest-straddle-cost pairs, maximum cross-pair dispersion 0.50 XSP points.
  This is **not observed official intraday XSP spot**.
- Five-minute signals use completed `[start, end)` observations and are known
  at the ending boundary. Entries use a strictly later usable snapshot within
  two minutes. Missing required prefixes are exclusions, not no-trade days.
- Entry debit must be positive and below width. The nearest listed center is
  used, lower strike on a tie; no outcome-based alternative-strike search.
- Original exit: first usable snapshot at/after entry plus 60 minutes, or
  calendar close minus 15 minutes if earlier, within the two-minute window
  and strictly capped at the scheduled liquidation deadline.
- Component entry: wing asks minus twice the body bid. Liquidation: wing bids
  minus twice the body ask. Preserve signed negative liquidation values; never
  clip a payable close to zero. These are modeled component prices, **not
  demonstrated executable complex-order fills or a guaranteed cost bound**.
- The frozen quality filter requires both bid and ask sizes at every leg:
  one contract per wing and two at the body. Its unnecessarily restrictive
  unused-side requirements were diagnosed, not relaxed during these tests.
- Assumed fees: $0.65 per contract per side, or $2.60 per butterfly transaction.
  Additional adverse stress: $0.05 per whole butterfly per transaction, or $5.
  Thus liquidations pay $5.20 fees plus $10 additional stress per round trip;
  cash settlement has only opening fees and $5 opening stress.
- Midpoint after fees is diagnostic, not a fill model. Drawdown is measured
  at terminal trade outcomes, not continuously or intraday.

## 1. Entry hypotheses already tested

Exact coverage and signal definitions are frozen in
[`mean_reversion.py`](../../tools/research_studies/xsp_independent/mean_reversion.py)
and [`trend_range.py`](../../tools/research_studies/xsp_independent/trend_range.py).
Do not silently reinterpret these descriptions as a new backtest.

- **MR1 — failed breakout:** after a post-10:00 completed five-minute close
  outside the opening range, enter on the first later close back inside.
  Center at the opening-range midpoint; cutoff 13:00 ET.
- **MR2 — excursion reversal:** arm after a completed close at least one full
  opening-range width away from its midpoint. Confirm on the first later close
  moving toward that midpoint while still on the armed side. No rearm. Center
  at the opening midpoint; cutoff 13:00 ET.
- **T1 — opening-range continuation:** first completed five-minute close
  outside the sampled 09:31–09:59 opening range, 10:05–13:00 ET. Center half an
  opening-range width ahead of the signal estimate.
- **T2 — late compression:** at 14:00 ET, the prior hour's range is no wider
  than the opening range and its absolute net change is at most 25% of its
  range. Center at that hour's midrange; calls fixed.

Call/put choice in same-center symmetric butterflies does not create a distinct
expiry-direction payoff. Their observed component quote costs can differ.

All eight entry/width cells lost even at midpoint after fees. Initial stressed
totals on **completed, covered timed-exit trades only** were:

- MR1: width 2 **−$4,104.20** (96 records); width 4 **−$5,512.80** (94).
- MR2: width 2 **−$3,160.80** (104); width 4 **−$4,707.20** (101).
- T1: width 2 **−$5,545.40** (157); width 4 **−$7,084.40** (152).
- T2: width 2 **−$1,667.00** (30); width 4 **−$1,477.60** (18).

These are alternative cells with differing exclusions; do not sum them as a
portfolio. They total **752 candidate baseline records**, plus benchmark
records; the initial review reconciled 1,576 candidate/benchmark records.
Fixed time-entry benchmarks and zero on valid no-signal days were included.
Beating a worse negative benchmark did not establish profitability.

## 2. Value-realization extension already tested

All four entry families and both widths were retained: eight timed baselines
plus **24 additional correlated exit comparisons**. Entry admission was rebuilt
without conditioning on a usable future timed exit: 784 accepted entry instances,
including 32 whose original timed exits were unavailable.

The alternatives were:

1. **Center crossing:** exact entry-time proxy anchor, then first post-entry
   sampled equality or sign change about the center. Observe first, fill at a
   strictly later usable snapshot within two minutes and by the deadline.
2. **25% net-profit target:** observe nominal component liquidation net profit,
   after both transaction fees, at least 25% of opening debit plus opening fee.
   Fill strictly later. The realized fill can miss the target; stress reprices
   the same decisions rather than changing the trigger.
3. **Hold to published cash settlement.** All eight constructions lost after
   modeled component opening costs and stress, despite complete settlement
   coverage for every accepted entry.

Center/profit policies required their respective input prefix with gaps no
larger than 120 seconds. Without an earlier trigger, they attempted liquidation
at close minus 15 minutes. Missing inputs or quotes remained unresolved in this
stage. No missing value became zero, and no missing path was interpolated.

**The misleading lead:** MR2 width 4 had center-exit **+$493.20** on 39 of 105
entries, and target-exit **+$501.00** on 20 of 105, after modeled stress. The
unpriced 66/85 entries made these conditional results insufficient evidence.
Both passed numeric screens on the priced subset, including positive halves
and positive top-three-winners-removed results. That did not repair censoring.
Do not resurrect either subset as a profitable strategy.

The lifecycle review reconciled 2,153 completed policy records, reproduced all
752 original candidate baselines exactly, and checked 64 raw-price examples.

## 3. Completed MR2 width-four fallback audit — final decision

The follow-up fixed the same **105 accepted entries**, with no new entry,
geometry, target, price-quality, or size tuning. It kept all original 101 timed,
39 center, and 20 target priced exits exactly unchanged.

On the first required anchor/prefix failure or failed first fill window, the
specified research policy irrevocably holds to native published settlement.
It never reactivates an exit search when later quotes recover. A missing
scheduled cutoff exit also leads to settlement. This supplies a terminal
contract outcome, not an invented earlier liquidation price.

A gap is known at the scheduled minute `last_usable + 3 minutes`, first beyond
the 120-second tolerance, not at the future recovery timestamp. Missing exact
entry anchors are known at entry. Failed fill windows expire after two minutes,
capped at the scheduled cutoff. Settlement is never an intraday signal input.

**Complete-cohort stressed results, 105 entries per policy:**

- Timed exit + settlement fallback: **−$4,640.60** (101 liquidations / 4 settlements).
- Center crossing + fallback: **−$2,978.40** (39 / 66).
- 25% profit target + fallback: **−$2,343.00** (20 / 85).
- Always hold to settlement: **−$1,750.00** (0 / 105).

The previously excluded center cohort contributes **−$3,471.60**; the excluded
target cohort contributes **−$2,844.00** under the explicit settlement fallback.
Both early-exit policies lose in both chronological halves and after removing
their three largest positive winners. Both also underperform always settling
the same entries. **Reject these exact completed policies.** Other outage or
execution responses have not been evaluated; this is not a rejection of every
possible butterfly strategy.

Independent review reconciled all **420 policy records**: 160 priced liquidations
and 260 settlements. They reuse 105 entries, not 420 independent trades.

## Quote and settlement findings to retain

- All **57** missing center-policy no-trigger cutoff exits had a required wing
  with zero bid and zero displayed bid size, with a positive ask. None became
  usable by checking only transaction-needed closing sizes. This is a recorded
  absence of a displayed leg buyer, not proof a complex order cannot fill or
  that the entire butterfly is worthless.
- Across all 105 cutoff snapshots: **95** primary zero-bid/no-size failures,
  **3** other required-size failures, **1** unused-side-only rejection, and
  **6** valid under the original filter; **7** have sufficient closing-side sizes.
- Of 85 profit-policy unresolved events, **32** first missing snapshots fail
  solely on an unused side; **28** fail required sizes and **25** lack required
  displayed buyers. Of 76 nonterminal prefix events, 48 have some closing-side
  usable snapshot and 25 are closing-side usable throughout their missing
  interval. These are diagnostics, not alternative fills or profitability tests.
- The audit covered 105 cutoff observations and 151 unresolved policy events,
  preserving **1,192 raw snapshots**. No absent-row/crossed/nonfinite/zero-zero
  primary classification occurred in this scoped event audit; do not generalize
  that finding to the entire archive.
- Native **Cboe-published XSP settlements exist for all 185 dates**. Preserve
  `settlements-native.csv` with `source_type=cboe_native_xsp_published_settlement`
  and its `native-manifest.json` hash receipt. Match both trading and settlement
  symbols to XSP; exclude binary options, NANOS, SET and XSR.
- Do not use the earlier `settlements.csv`/`manifest.json` three-decimal derivation:
  it is explicitly `SUPERSEDED.json`. Cboe's proposed precision change was
  postponed. Published values differ from naive half-up SPX-close/10 rounding
  on July 7 and July 29. Use published values unchanged, not guessed precision.
- The raw quote grid continues to 16:15 even on half-days. Filter by the actual
  exchange calendar; post-expiry rows are not fills. Do not interpolate gaps.
- No native intraday XSP feed or per-leg update age is established here. The
  canonical supporting dataset contains SPX/VIX, not native XSP. The approximate
  forward is not settlement and its dispersion filter does not ensure accuracy.
- Older XSP quote precision/liquidity was not validated for this strategy.
  One 2023 sample had much wider parity uncertainty than the 2026 samples.
  File counts do not establish a backtest-ready multi-year dataset.

## What remains genuinely untested

- A separately specified **transaction-needed quote-size policy**; unused-side
  checks were audited only. Any comparison must preserve all accepted entries
  and explicitly resolve every failed execution or data outage.
- Independent intraday signal-price evidence, trustworthy quote-event age, and
  observed complex-order execution evidence with validated all-in costs.
- Different outage/recovery or partial-execution responses; none is implied
  authorized for runtime by the research above.
- A new, appropriately validated historical or prospective cohort. The inspected
  January–September 2026 sample is development data for all subsequent choices.

These are prerequisites or distinct hypotheses, not evidence of an edge. Do not
restart the four original entry families or tune targets on surviving winners
without stating what material uncertainty the new experiment resolves.

## Evidence, retained summary and reproduction

The small [decision receipt](xsp-independent-research-2026-11-12.summary.json)
retains key results and hashes in a versionable location. It preserves the
decision even if private local artifacts are unavailable in a fresh checkout.
Raw vendor data, large traces and reports remain private and gitignored.

- Final [standalone HTML report](../../reports/research/xsp-fallback-2026-11-12/index.html).
- Initial [eight-cell independent review](../../reports/research/xsp-independent-2026-11-11/root-review-01/review.json),
  [mean-reversion run](../../reports/research/xsp-independent-2026-11-11/mean-reversion/full-01/summary.json),
  and [corrected trend/range run](../../reports/research/xsp-independent-2026-11-11/trend-range/run-02/summary.json).
  Interrupted trend `run-01` is superseded; do not report it as final.
- Lifecycle [summary](../../reports/research/xsp-realization-2026-11-11/realization/run-01/summary.json),
  [independent review](../../reports/research/xsp-realization-2026-11-11/root-review-02/review.json),
  and [native settlement provenance](../../reports/research/xsp-realization-2026-11-11/settlement/native-manifest.json).
- Completion [decision](../../reports/research/xsp-fallback-2026-11-12/decision.json),
  [summary](../../reports/research/xsp-fallback-2026-11-12/replay/run-01/summary.json),
  [420-row CSV](../../reports/research/xsp-fallback-2026-11-12/replay/run-01/journal.csv),
  [quote audit](../../reports/research/xsp-fallback-2026-11-12/quote-audit/summary.json),
  and [independent cash review](../../reports/research/xsp-fallback-2026-11-12/independent-review/cohort-cash-review.json).
- Scripts: [`tools/research_studies/xsp_independent/`](../../tools/research_studies/xsp_independent/).
  Manifests identify the dirty working source; Git SHA `ae123c3b` alone does not
  identify these new helpers. Retain the helpers and focused tests with this
  record when integrating the work.

Reproduction only; use fresh output paths and existing audited inputs:

```bash
uv run python -m tools.research_studies.xsp_independent.mean_reversion --out /tmp/xsp-mr-new --freeze --run
uv run python -m tools.research_studies.xsp_independent.trend_range --out /tmp/xsp-trend-new
uv run python -m tools.research_studies.xsp_independent.realization --out /tmp/xsp-life-new --freeze --run
uv run python -m tools.research_studies.xsp_independent.fallback --out /tmp/xsp-fallback-new --freeze --run
uv run python -m tools.research_studies.xsp_independent.quote_evidence --out /tmp/xsp-quotes-new
uv run python -m tools.research_studies.xsp_independent.render_fallback_report --out /tmp/xsp-report-new.html
```

Default follow-up inputs reference the preserved campaign directories; see each
CLI's `--help` before substituting newly reproduced inputs. Do not overwrite old
evidence or represent a reproduction as a new trial.

Recorded verification: initial study **32 focused tests**, lifecycle/settlement
extension **51**, completion/quote audit **25**. These are separate stage counts,
not a claim of one combined suite run. Scoped Ruff and whitespace checks passed;
the final HTML controls, 420-record download, and layout passed desktop/mobile
Firefox checks. The AST graph was updated after code changes; its pre-existing
SQL extractor dependency was unavailable. No SQL implementation was changed.
