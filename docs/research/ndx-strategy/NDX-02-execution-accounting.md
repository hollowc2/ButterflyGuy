# NDX-02 execution/accounting audit — 2026-10-15

**Decision: execution/accounting attribution complete for this bounded cohort;
refine evidence before further experiments.** This completes one part of NDX-02,
not liquidity calibration, continuation validation, or strategy development.
No strategy parameters, rejected variants, services, orders or credentials changed.

## Evidence, identity and scope

Final output: `reports/research/ndx-02-20261015/run-02/`, with immutable
`run-01/` retained. Versionable [ledger](evidence/2026-10-15/ndx02-execution-ledger.jsonl),
[summary](evidence/2026-10-15/ndx02-summary.json),
[run manifest](evidence/2026-10-15/ndx02-run-02.json),
[final contract](evidence/2026-10-15/ndx02-execution-final.json), and
[verification](evidence/2026-10-15/ndx02-verification.json) identify the result.
The [living plan](../ndx-strategy-development.md) remains the authoritative handoff.

Before interpreting prices, verified all 347 original snapshot files, four
identity/settlement supplement files, two continuation inventory files, two saved
runtime-source files, all 12 NDX-01/run-03 outputs, and all 138 pinned NDX-01
source/dependency/test files against the current checkout. Starting HEAD remains
`6a33d170c09f7ff68d7edb733b74c087b27c0227`. Audit source/test hashes and actual
Python/package/platform information are separately pinned and preserved in each
run. Source identity is current **local** identity plus the saved October 15
runtime observation; no fresh remote inspection or historical deployment
attestation is claimed. Eros retention is accepted; independent backup remains
unestablished.

Inputs, all read locally:

- `evidence/ndx/ndx-r0-20261014/raw/{trades,events,paths}.csv`: recorded fills,
  diagnostics, event payloads and held-monitor collection timestamps. The
  [snapshot manifest](evidence/2026-10-15/snapshot.json) pins their bytes.
- `evidence/ndx/ndx-01-supplement-20261015/supplement.csv`: recorded contract
  identities and paper-settlement source times; [manifest](evidence/2026-10-15/supplement-manifest.json).
- `evidence/ndx/ndx-continuation-inventory-20261015/extract.csv`: inventory only,
  with [query](sql/continuation-inventory.sql) and
  [manifest](evidence/2026-10-15/continuation-inventory-manifest.json).
- `reports/research/ndx-01-20261015/run-03/{run.json,coverage.jsonl}` and all its
  hashed outputs: frozen parent evidence, never rewritten or replayed here.
- `evidence/ndx/helios-ndx-source-20261015/container-source.tar.gz`: inspected
  saved order-manager/position-service source, under its verified
  [manifest](evidence/2026-10-15/runtime-source-manifest.json). The order manager
  matches local source; the service differs. See the existing
  [source comparison](evidence/2026-10-15/source-comparison.json).

Cohort selection is **closed `mark_v1` records whose exit reason is not
`cash_settled`**, derived from the verified records, not a count or ID constant.
The resulting IDs are 194, 226, 233, 236, 245, 248, 249, 254, 258, 267, 294,
306, 316, 317, 339, 343 and 346, July 23–October 13. Membership, session dates,
exit times and verified contract identity reconcile with the NDX-01 coverage and
independent continuation inventory. Every quantity is one. `modern-context.jsonl`
additionally audits all 53 newer records, including 36 paper settlements; this
context is not an enlarged discretionary-exit experiment.

## Predeclared tolerances

The initial [contract](evidence/2026-10-15/ndx02-execution-contract.json) was
written before numerical assessment: 0.00011 unrounded option points for stored
four-decimal composites; 0.000001 points for two-decimal prices (floating-point
noise only, far below a one-cent price difference); $0.01 per trade for dollar
accounting; one microsecond for timestamp equality. Individual discrepancies
remain visible. No timing tolerance measures acceptable fill latency. Missing
timestamps have no pass condition and remain null. These tolerances were not widened.

## What the recorded prices measure

The independent audit reads recorded fields and uses arithmetic; it does not call
the runtime fill helper or replay a strategy. Source references are
[`OrderManager._commission`, `_mark_paper_fill`, `_try_entry_at_price`, `execute_exit`](../../../src/butterfly_guy/execution/order_manager.py),
[`PositionService` signal/fill/log flow](../../../src/butterfly_guy/services/position_service.py),
and [`TradeService` entry-attempt recording](../../../src/butterfly_guy/services/trade_service.py).
The saved container copy verifies the paper-fill helper and demonstrates the
current log-after-fill service ordering. Historical events independently check
prices without assuming that ordering existed on every date.

For recorded quantity `q`, the runtime embeds `c(q)=4×q×$0.65/100` points into
prices and uses Python `round(..., 2)`:

- Entry paper price: `round(fetched composite mark + c(q), 2)`. Entry selection
  and its limit are earlier observations, retained in `entry_selection_observations`
  where logged. They are not the subsequent fill quote. The source refuses a
  paper entry when its fill spread fetch fails; no entry fallback occurs here.
- Exit paper price: `round(signal mark − c(q), 2)`. A separately fetched spread
  supplies the exit diagnostic mark/bid/ask; it does not replace the signal mark
  in that paper fill. The helper itself does not floor the paper price.
- Stored entry estimate: `round(composite ask + stored slippage + c(q), 2)`.
  Stored discretionary exit estimate: `round(composite bid − stored slippage − c(q), 2)`.
  Stored slippage is 0.05 points on these rows. Missing spread quotes use the
  supplied mark in the helper, explicitly labelled as fallback. These estimates
  are independently recomputed from each row's diagnostics.
- Recorded P&L: `(exit price − entry price)×100×q`; DB `pnl` is points per fly.
  Both prices already include commissions. No further fee deduction is made.
  At `q=1`, a 0.026-point configured fee produces a 0.03-point price adjustment
  in these checked fills; rounding is preserved.
- Historical stored stress: use embedded entry estimate and
  `max(0, stored exit estimate)` for discretionary exits. The producer stores
  the raw estimate without flooring. Cash settlement instead uses the recorded
  payoff at its stored precision, with **no closing fee, slippage or rounding
  to two decimals**. This remains an attributed paper proxy, not official XQC.

The runtime's quantity-dependent embedded fee convention is preserved, including
in an independent quantity-two fixture. This all-quantity-one sample does not
validate multi-quantity economic fee calibration or authorize changing it.

The ledger retains raw signed leg-composite bids and raw stored estimates. R0's
separate replay helper clips a negative raw bid before deducting costs and then
floors negative proceeds. This audit never substitutes that replay estimate for
a stored estimate. **Zero of 17 discretionary stored exits and zero of 53 modern
context exits exercise the proceeds floor; benefit is $0.** Negative entry
composite bids occur in two of 17 (194, 317), and 13 of 53 context entries; this
does not make their ask-based entry estimates zero. Fixtures separately verify
negative raw bids, positive bids yielding negative proceeds, and floor benefit.
Paying to close at a negative credit is excluded by the historical stress floor,
which can make stress optimistic outside this sample.

The fetched mark is the `+1/−2/+1` composite of provider leg **marks**, not a
freshly recomputed midpoint of the composite bid/ask. For example, trade 306's
diagnostic mark is 3.39 while `(2.90+3.90)/2=3.40`. Provider-mark rounding and
different observations are preserved; the audit never replaces them with a
synthetic midpoint.

## Independent reconciliation and measured drag

All 17 entry fills reconcile to their diagnostic mark plus rounded fee; all 17
stored entry and 17 stored exit estimates reconcile independently. All recorded
P&Ls reconcile. Seven exported `trade_exited` events provide independent exit
signal marks, event fills and matching signal-event marks; all seven reconcile.
The other ten have no exported independent signal event, so their signal-mark
fill check remains **unknown**, even where the diagnostic mark happens to imply
the recorded fill. There is no unexplained numerical discrepancy in an available
check, and no aggregate netting is used to conceal individual failures.

For the 17 discretionary exits:

- Recorded paper P&L **−$9,316**; historical stored stress **−$20,060**.
- Entry drag **$9,017**, median **$405**, range **$300–$1,287** per recorded trade.
- Exit drag **$1,727**, median **$96**, range **$5–$197**. Entry plus exit drag
  exactly explains the **$10,744** P&L difference within the fixed tolerance.
- Entry composite ask-minus-bid: 17 observations, median **8.00 points**, range
  **5.90–25.65**; median spread/diagnostic-mark ratio **1.1688**.
- Exit composite ask-minus-bid: 16 observations, median **1.85 points**, range
  **0.90–3.45**; median spread/diagnostic-mark ratio **1.2032**.
- Mark fallback: **0/17 entries; 1/17 exits (5.88%)**, trade **194**. Its bid and
  ask are null. Its stored mark 3.92 is the supplied-mark fallback, **not an
  independently fetched diagnostic quote**; `round(3.92−0.05−0.026,2)=3.84`.
  Missing spread and time fields stay null. This is neither a bid observation
  nor evidence of a complex-order fill.

These differences measure accounting-model drag, not realized implementation
shortfall. Exit drag can combine spread/cost assumptions with signal-to-diagnostic
price change. Separating a causal market-movement component requires missing
quote/event/availability times. The stored clipped `estimated_execution_drag`
metadata also reconciles; the audit retains signed price differences separately.

As a context check, all 53 newer records reproduce **+$9,254.84** paper and
**−$30,978.16** stored stress. Entry drag is **$38,506** and exit drag **$1,727**;
settlement has zero closing drag. These are recorded-entry accounting comparisons,
not portfolio returns or strategy experiments.

The three previously material differences are verified directly against
`trade_exited.mark_at_signal`, `fill_price`, `spread_mark`, and stored diagnostics:

- **294:** signal 1.32 → paper 1.29; diagnostic 1.48 → diagnostic-based paper
  counterfactual 1.45 (**+$16** per fly versus recorded).
- **306:** signal 3.74 → paper 3.71; diagnostic 3.39 → counterfactual 3.36 (**−$35**).
- **316:** signal 2.82 → paper 2.79; diagnostic 2.62 → counterfactual 2.59 (**−$20**).

Among the seven independently observed signal marks, three change materially
at the diagnostic read; changes range −0.35 to +0.16 points, sum **−0.39 points**.
The other four match within tolerance. The −$39 combined counterfactual difference
is price-observation attribution, not an extra commission. For trade 346,
`(2.77−7.28)×100=−$451`; its stored stress is `(1.02−11.18)×100=−$1,016`.
Context trade 349 retains settlement precision:
`(30.7966−7.83)×100=+$2,296.66`, with no closing commission.

## Timing coverage and its limits

All 17 have recorded entry and exit fill timestamps and complete held-monitor
collection observations. The final held collection precedes recorded exit by
0.053338–1.129377 seconds. This is a collection-to-recorded-fill interval, **not
identified signal latency or exchange quote age**. A matching price alone does
not identify a signal observation.

Seven have entry-attempt chain-fetch completion, spot-fetch, VIX and DB-snapshot
timestamps, selection marks and limits in the exported `entry_ladder_trace`.
They remain attached to those attempts; no selected-chain timestamp is assigned
to the later paper-fill diagnostic. Seven entry events explicitly repeat fill
time, and all agree to microsecond precision. No constituent option quote-event
or publication/availability timestamp, diagnostic-fetch timestamp, or independent
exit signal observation timestamp is available in these exports. Those fields
remain null throughout. The entry attempt's local fetch completion is recorded
collection evidence, not proof of constituent freshness.

All seven `trade_exited` writes occur **11.814–93.679 ms after** recorded fill
(median 25.740 ms). Entry writes occur **15.168–93.500 ms after** recorded fill
on the seven cohort entries with logs (median 30.772 ms). `exit_signal_fired`
write-minus-fill offsets are −0.667547, −0.957800, −0.893130 and −0.637133 seconds
for 294/306/316/317, but **+0.060588/+0.057979/+0.047748 seconds** for
339/343/346. These are write offsets only. Do not reinterpret either sign as
submission, execution or signal latency; historical source/deployment ordering
is incompletely attributed.

Exit parity payloads retain independent DB snapshot timestamps and reported lags
(5.960324–56.903124 seconds). These describe comparison snapshots, not exchange
quote-event time or the later diagnostic fetch. No timestamp is reverse-engineered
from a reported lag. Sizes, order acceptance, partial fills, cancels and rejects
are not established for this cohort. Paper event labels and empty ladder traces
are not actual broker fills. Leg quotes and displayed size, if later obtained,
cannot establish complex-order executability.

## Bounded execution-model specification

**Supported:** preserve fixed recorded entries, exits, reasons and quantities;
use the embedded/rounded paper accounting above; retain raw stored leg-market
stress and its fallback/floor flags as a separate model; report timing coverage
and missingness; retain settlement precision without a closing fee. The evidence
supports these accounting statements, not a probability of filling at mark.

**Unsupported:** simultaneous executable constituent quotes; midpoint execution
probability; complex-order depth or capacity; marketable-estimate fills; fill
latency, adverse selection or slippage calibrated from telemetry writes; exact
historical runtime parity; rejected/unfilled opportunity economics; official XQC;
and holding beyond the recorded exit using the R0 monitor path.

**Additional evidence needed:** attributed complex-order journals with instrument,
quantity, side, limit, submission/acceptance times, executions/partial fills,
cancel/reject/unfilled outcomes, fees, and paper/broker identity; synchronised
constituent quote-event/collection/availability timestamps with source/cache age;
effective per-trade policy/deployment provenance. Any future capture/instrumentation
is a separate authorized implementation and activation task. No live orders are
needed or authorized to complete this audit. No liquidity threshold is selected.

## Exact next bounded task

**Import and audit the inventoried independent minute continuation evidence,
without replaying hold-after-exit rules.** First register a new snapshot and
cadence contract, parented to NDX-01/run-03 and this audit. Use the cohort ledger
to define exact symbols, direction, expiration and dates. Export original
three-leg rows only in `(recorded exit, regular-session close]`, preserving raw
bid/ask/mark, available sizes and every actually recorded timestamp under a
read-only query, with provider/schema/query/source hashes and retrieval time.
Verify the inventory's per-trade counts and first/last timestamps against the
new extract; report any later-DB discrepancy instead of changing the old inventory.

Normalize by exact symbol and snapshot timestamp; reject/report duplicate keys,
wrong root/date/expiration/type, incomplete groups, nonfinite values, negative
leg quotes and crossed markets. Preserve raw negative **composite** bids, provider
marks and missing event/availability fields. Do not replace marks with midpoints,
forward-fill, interpolate, or join minute rows onto R0 monitor polls.

Audit nominal 60-second cadence separately: every adjacent interval, median/p95/max,
scheduled minute buckets, missing/duplicate buckets, intervals above 30/60/90/120
seconds, exit-to-first and last-to-close gaps, session boundaries and cross-source
overlap where present. A complete timestamp inventory alone is insufficient.
Write per-trade coverage/exclusion ledgers and price/mark sanity checks. All such
paths remain ineligible for R0's 30-second continuation semantics; a future
minute-based replay needs its own causal signal/fill/gap policy and eligibility
decision before any hypothesis is evaluated. This task must not test longer holds
or select a cadence/threshold by inspecting P&L.

## Reproduction and verification

The [command guide](NDX-02-reproduction.md) supplies the exact offline invocation.
Output paths must be new; changed source pins or input hashes refuse a run.
Run-01 is preserved with its source/contract. Its first full offline integration
test rejected `platform.platform()` spawning `uname`; run-02 records process-free
platform fields, a new source lock and an explicit run-01 correction-parent hash.
Accounting/ledger/summary outputs are identical between runs. The only initial
fixture correction was replacing exact binary-float fee equality with `approx`;
production tolerances were unchanged. Earlier failed test output locations and
final checks are recorded in the verification record.

**57 tests passed:** 13 audit tests including a full private-snapshot run with
network sockets blocked and subprocesses restricted to local Git, plus the 44
NDX-01/state-machine/position-manager tests. Full repository Ruff passed. Graph
refresh and artifact/hash checks are recorded in verification. No network, broker,
database, credential or service access was required by this audit.
