# NDX-02 constituent quote fidelity — 2026-10-15

**Decision: bounded attribution complete; insufficient evidence for causal minute
replay. Full liquidity calibration and strategy promotion remain incomplete.**
No strategy P&L, exit experiment, trading filter, remote acquisition, runtime
change, deployment or credential operation was performed. These are inspected
**development** sessions, not holdout evidence.

## Evidence and identity

Frozen run: `reports/research/ndx-02-fidelity-20261015/run-01/`.
The [contract](evidence/2026-10-15/ndx02-fidelity-contract.json) was registered
before new attribution. It links the continuation run-01, accounting run-02 and
baseline run-03 by SHA-256. All five original snapshot manifests (347 R0 files,
four supplement files, two inventory files, two runtime-source files and 11
continuation files), all three parents' output hashes and current source pins
were verified. Source identity at start: `49da0284d24814ed2bc0838bbd543444b48019b9`;
working tree initially clean. This newer checkout identity does not supersede
historical runtime identity. Source pins from the earlier runs still match.

The runner derives membership from closed `mark_v1` records excluding
`cash_settled`, reconciles inventory and baseline identity/times, rebuilds raw
continuation groups, and compares them against frozen normalized observations,
exclusions and summary. It checks the cohort against accounting records. Counts
are reconciliation results, never cohort-selection constants. See the
[offline command](NDX-02-quote-fidelity-reproduction.md).

Inputs remain private Git-ignored dependencies on Eros. Git alone cannot recover
them; an independent backup is not established. The exact-symbol/session export
covers collection `snapshot_time` in `(recorded exit, regular close]`. It excludes
wrong-expiration rows and unrelated omitted-contract payloads by scope; neither
is evidence of their absence from the database. The earlier 60-second-timeout,
header-only extraction remains preserved and is not quote evidence.

## Observed arithmetic and overlap

The [summary](evidence/2026-10-15/ndx02-fidelity-summary.json) and
[breakdowns](evidence/2026-10-15/ndx02-fidelity-breakdown.jsonl) reconcile:

- 17 trades, 3,364 raw legs, 1,114 complete groups / 3,342 complete-group legs.
  Eleven incomplete groups retain their 22 legs and reasons: five on 317, six
  on 346. No complete group's economic/replay eligibility follows from structure.
- 157/1,114 negative provider composites; 635/1,114 negative leg-market bids;
  816/1,114 reportable composite mark/midpoint differences. All 157 negative
  marks also have negative composite bids. Of the 157, **103** also have a
  reportable difference; 54 do not. There are 713 difference-only observations
  and 244 with neither mark anomaly. Full joint masks also include bid/leg flags.
- 1,537/3,342 individual leg marks differ from their own midpoint beyond
  0.00011 points; **0/3,342 lie outside their own recorded bid/ask**. Every
  leg residual is between −0.005 and +0.005 points inclusive. Differences at
  individual legs can cancel: 923 groups have a reportable individual residual,
  but only 816 have a reportable composite residual.
- Composite residuals range −0.015 to +0.020 points, and equal the weighted
  `+1/−2/+1` leg residuals exactly using decimal arithmetic. All leg residuals
  fit the predeclared half-cent compatibility bound. This supports a limited
  rounding explanation for the small differences; it does **not** establish
  the provider's rounding algorithm, tie-breaking, or original payload precision.
- An independent implementation parses raw JSON directly with `Decimal` and
  confirms that the **same 157 groups also have negative composite midpoints**.
  The negative signs are not explained away by rounding. Marks span −13.97 to
  10.04 points; the negative subset spans −13.97 to −0.02.

Reporting preserves the prior 0.00011-point allowance and one-microsecond
recorded timestamp tolerance. The half-cent bound is a precision diagnostic,
not a threshold for freshness, liquidity or trading. Exact signed values remain
in the ledgers; no negative value is clipped, no midpoint replaces a mark, and
no tolerance was widened to achieve agreement.

Timed coverage is 148 groups / 444 legs on 339 (23), 343 (24), 346 (101): 12
negative marks, 62 negative bids, 105 midpoint differences, eight overlapping
mark anomalies. Untimed coverage is 966 groups / 2,898 legs on 14 trades: 145
negative marks, 573 negative bids, 711 differences, 95 overlapping mark anomalies.
The breakdown ledger supplies full per-trade, per-session and per-timing-subset
denominators and overlap masks; unknown is a category, not clean or zero.

## Traceable examples

[Examples](evidence/2026-10-15/ndx02-fidelity-examples.jsonl) link exact original
CSV **data-record ordinals** (one-based, excluding the header), symbols, raw JSON,
events, ages, sizes and metadata. Duplicate selections are intentional when the
same observation explains multiple mechanics. All timestamps below are UTC.

- **Most negative:** trade 339, October 9 19:59:38.995554, raw records
  **2975–2977**, calls at 30940/31040/31140. Leg bid/ask/mark triples are
  `(0, .05, .03)`, `(0, 15, 7.50)`, `(0, 2, 1.00)`.
  Provider composite `.03 − 15 + 1 = −13.97`; leg-market bid −30, ask 2.05,
  midpoint −13.975, residual +0.005. The broad center ask produces a center midpoint exceeding the
  wings under the butterfly weights; all three
  marks are inside their own markets. Event dispersion is 31.263 seconds;
  reported ages are 3.243838/31.458838/34.506840 seconds. This is recorded
  inconsistent cross-strike valuation, not a verified negative executable fill.
- **Closest-to-zero negative / largest dispersion / oldest reported leg:** trade
  346, October 13 19:45:19.602425, records **3323–3325**, puts at
  30260/30360/30460. Triples `(0,.10,.05)`, `(0,.50,.25)`, `(.20,.65,.43)`
  yield `.05 − .50 + .43 = −.02`, midpoint −.025 and residual +.005.
  Dispersion is **268.471 seconds**; reported ages
  269.157070/.686081/2.684081 seconds. The oldest leg has zero bid size.
  One event follows pass start, but precedes fetch completion. This demonstrates
  unequal recorded event times and an old reported quote on that observation;
  it does not prove why the negative composite arose.
- **Largest absolute composite residual, untimed:** trade 236, August 13
  18:11:11.903171, records **631–633**, calls at 30210/30310/30410.
  Marks 1.78/.52/.33 versus midpoints 1.775/.525/.325 give residuals
  +.005/−.005/+.005. Weighted discrepancy `.005 − 2(−.005) + .005 = .020`;
  composite mark 1.07 versus midpoint 1.05. Clocks are unknown.
- **Largest timed residual:** trade 346, October 13 19:07:24.775206,
  records **3215–3217**. Marks .48/.57/2.73 versus midpoints
  .475/.575/2.725 produce the same +.020 discrepancy: 2.07 versus 2.05.
  Dispersion is 5.845 seconds. Neither selecting these examples nor reporting
  age extremes defines an economic filter.

A negative leg-market bid is a signed diagnostic cost to close across separate
leg markets. It can occur with perfectly nonnegative individual prices and is
not silently a zero-valued observation. Displayed sizes do not establish
simultaneous liquidity, complex-order execution or capacity. An option's
nonnegative payoff does not make an asynchronous composite of independent
recorded quotes an admissible executable value.

## Clocks, source behavior and unresolved causes

For all 148 fully timed groups, event dispersion is 0.001–268.471 seconds,
median 9.378, nearest-rank p95 138.629. Their oldest reported leg ages have
median 10.825449 seconds and maximum 269.157070. All 444 event-to-local-fetch
completion differences are positive, 0.563559–269.238356 seconds. There are
145 events after pass start and zero after recorded fetch completion using the
one-microsecond ordering allowance. No clock-synchronization claim follows.

Reported age minus `(local completion − event)` ranges −.243720 to −.049013
seconds (median −.0718685). This is a descriptive difference between recorded
numbers with an unattested historical age-reference clock. It neither proves
bad timestamps nor reconstructs a missing reference timestamp. Gateway receive,
fetch start/completion, chain event/age/source/flags are recorded on these 148
groups; scheduled, commit, publication and consumer availability remain absent.
The 14 other trades have no constituent timing coverage. No claim about their
freshness, synchronized updates or age is justified.

All timed chain-source strings are `schwab_rest_option_chain`; all 148 chain
flags contain `stale_contracts_present`. That is chain-level metadata, not a
per-leg stale label: the export omits unrelated omitted-contract payloads and
the three selected legs need not explain a chain-wide flag.

[Source trace](evidence/2026-10-15/ndx02-fidelity-source-trace.json) pins inspected
local source and enumerates the selected saved runtime bundle:

- Local [collector](../../../src/butterfly_guy/data/collector.py) copies supplied
  bid/ask/mark using `.get`, without midpoint replacement or zero defaults for
  these fields. It maps auxiliary provider fields verbatim. A negative recorded
  `intrinsic_value` is a provider-labelled field, not our recomputed payoff;
  `last`, theoretical and time-value fields likewise do not establish fills.
- Local [gateway adapter](../../../src/butterfly_guy/data/providers.py) requires
  finite nonnegative bid/ask/mark and uncrossed individual markets, copies the
  supplied mark, and maps contract clocks separately. It can omit unusable
  contracts; other auxiliary fields have defaults. No identified local mark
  default explains these records. The direct adapter lacks observed contract
  clocks. A source label alone does not establish which adapter was deployed.
- The timed collector stamps pass start before requests, records fetch times,
  maps per-contract event/age, writes quote rows, then attempts metadata.
  Metadata failure is tolerated separately. The unaligned loop sleeps after
  collection, a possible explanation for drifting cadence. Neither mechanism
  is attested for each historical session by the saved deployment evidence.
- [Database insertion](../../../src/butterfly_guy/db/queries.py) copies supplied
  columns into the table. Checked-in migrations declare four-decimal numeric
  prices and nullable clocks; the captured schema confirms numeric price and
  nullable clock types, but did not export numeric scale. The schema contains
  no commit/consumer timestamps. Source behavior is not an original response.
- The saved October 15 container tar contains seven selected position/execution/
  config/time modules, NDX config and dependency files; it contains **no
  collector, provider adapter or DB insertion source**. Its known image identity
  is not a per-trade deployment history or gateway implementation attestation.

**Supported deduction:** the negative composite is exactly the arithmetic of
recorded center and wing marks; the small midpoint discrepancies are exactly
weighted constituent residuals consistent with cent-level rounding. Timed
records establish unequal constituent event stamps, including old quoted legs.
**Unresolved:** provider rounding implementation, original payload values,
upstream normalization, whether old/asynchronous legs caused a given negative,
clock synchronization/skew, and complete historical code/config deployment.
The 14 untimed trades cannot resolve timing attribution. Source code offers
possible mechanisms, not proof that one generated a historical row. No minimal
DB query could recover absent original responses or missing deployment history,
so no additional remote acquisition was made.

Cadence remains the parent result: 1,097 intervals all exceed 60 seconds,
median 63.101178, four gaps over 120 seconds and 67 missing full-minute buckets.
Collection cadence is distinct from constituent freshness. No regular grid,
interpolation, forward-fill or R0 substitution is justified.

## Verification and next action

[Verification record](evidence/2026-10-15/ndx02-fidelity-verification.json) retains
commands, results and failed fixture development. The primary private suite
blocks sockets and allows only local Git subprocesses. A second raw-JSON test
independently checks exact decimal composites, anomaly masks, raw-row links,
negative-midpoint membership and retention of all excluded legs. All **82 focused tests passed with zero skips**, repository lint and whitespace
checks passed, and graphify AST update completed (optional SQL-parser and stale
label warnings remain). Original parents and contracts remain unchanged. See the
[causal-use specification](NDX-02-causal-minute-specification.md).

**Next bounded action:** design a separately reviewable prospective provenance
recording contract, covering original response identity, gateway clock/age
semantics, collector build/config, DB persistence and consumer receipt. Define
clock synchronization evidence and ex-ante missing/negative/gap handling before
collecting or implementing replay. This is a specification task, not capture
activation or deployment. Current R0 and minute eligibility remain **0/17**.
