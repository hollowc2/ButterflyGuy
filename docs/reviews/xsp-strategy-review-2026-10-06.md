# XSP isolated strategy review — October 6, 2026

**Decision: refine; insufficient evidence of a durable net-positive edge.**
The [sequential follow-up](../research/xsp-improvements-2026-10-06.md) verifies
the existing September 26 accounting fix, establishes monitor-replay parity,
and records the bounded exit experiment. The findings below preserve the
initial review; the follow-up refines its accounting and width-policy hypotheses.

XSP's latest paper profit is almost entirely consumed by its recorded entry-price
execution diagnostic. Repair the evidence and establish XSP exit parity before
optimizing parameters. No strategy settings, risk limits, secrets, database rows,
or running services were changed for this review.

## Performance through the October 6 close

Source: read-only queries against Helios `butterfly_guy`, filtered exclusively to
`underlying = 'XSP'`. Dollar P&L is `butterfly_trades.pnl * 100 * quantity`.
All 101 rows are closed; all quantities are one. The extraction was performed
after the October 6 close (October 7 UTC). These are recorded strategy results,
not a fresh backtest and not authenticated broker profitability.

- **September 1–October 6:** 20 trades, **+$78**, 30% win rate, $3.90 expectancy,
  1.161 profit factor, $197 maximum drawdown measured at completed trades.
  Average win $93.67; average loss $34.57.
- **Same decisions repriced using recorded marketable entry estimates:**
  **+$4**. Entry drag totals $74 ($3.70/trade); no closing fill or closing fee
  is applied because all 20 trades cash-settled. These synthetic estimates
  use component-leg prices, configured slippage, fees and cent rounding;
  they are not observed complex-order fills.
- **August 1–October 6:** 40 trades, +$120 recorded; **−$42** after $162 of
  recorded entry execution drag. Trade-close drawdown $628.
- **Comparable `mark_v1` paper cohort, July 22–October 6:** 47 trades,
  **−$118 recorded / −$315 repriced**. All 47 cash-settled. This is the most
  useful homogeneous fill-model baseline, though source and market-data
  behavior still changed during the period.
- **Current wider-fly design, June 17–October 6:** 67 trades, +$47.35.
  This is a mixed paper/live/mechanics period, including a manual broker
  close; do not interpret it as a controlled evaluation of the current bot.
- **Entire recorded history, April 2–October 6:** 101 trades, −$169.65,
  19.8% wins, 0.930 profit factor. Historical settings, live canary activity,
  accounting and quote issues make this context rather than a clean baseline.
- October 5 won $202; October 6 lost $33. September alone lost $51.
- Removing the three largest September-onward winners leaves **−$426**.
  This is descriptive concentration evidence, not a replacement performance
  estimate. Twenty trades cannot establish an edge.

Recorded results include the paper fee convention; do not subtract opening fees
again from the marketable estimate. Repricing freezes the chosen trade and
settlement outcome, so it does not model rejection, partial fills, selection
changes, or complex-order price improvement. A further one-cent adverse entry
shift across these 20 trades takes +$4 to −$16. That is sensitivity, not a
simulated executable strategy. No account-capital return is claimed because a
validated XSP-only capital denominator is unavailable. Drawdown excludes open
position marks and is not intraday maximum drawdown.

## Runtime and isolation

Helios `butterfly_xsp_app` was running with zero restarts since October 2;
`/ready` returned ready. Local and deployed XSP YAML agree on paper mode and
`allow_live_trading: false`. The wider widths/debit floor were introduced June
16. They are independent of SPX's configuration.

XSP uses its own config, container, underlying-scoped trade/risk queries,
chain identity and metrics. Shared strategy/position implementations are useful;
separation does not require duplicating those modules. Four substantive runtime
files were hash-matched to the local checkout: entry selection, state machine,
position manager, order manager. The remote checkout commit differs from the
local commit, so this does not establish whole-image source parity.

XSP and SPX still share market exposure. Their separate strategy labels are not
evidence of portfolio diversification.

## Findings, in recommended order

### 1. High — reconcile risk accounting before trusting risk dashboards

Two dates in the homogeneous paper cohort disagree between the ledgers:

- September 1: one closed trade lost $33; `daily_risk_state` records −$66
  and `halted = true`.
- September 24: one closed trade lost $39; risk state records −$78
  and `halted = true`.

Other days in that cohort reconcile within one cent. The doubled losses are
consistent with duplicate booking, but the cause is not established by this
snapshot. Performance above comes from the trade ledger, not risk state.

`PositionService._record_exit_metrics` converts points to dollars, then
`RiskEngine.record_pnl` calls an additive SQL update. The XSP config comment
describing the daily limit as raw credit units is stale: current runtime risk
accounting uses dollars. This is a documentation issue, not permission to alter
the $50 limit.

**Improvement:** reproduce interrupted close/secondary-work recovery; make
realized-risk posting attributable and idempotent for a trade, with a regression
that retrying a close preserves one P&L booking. Investigate false halt state
separately. Any shared fix must retain SPX/NDX behavior and needs their tests.
No historical rows were corrected during this review.

Evidence: `services/position_service.py:954`, `risk/risk_engine.py:151`,
`db/queries.py:552`; preserved `evidence.jsonl` risk and trade sections.

### 2. High — the trailer and exit-quality floor conflict for modest peaks

All 47 `mark_v1` trades held to settlement. Recent runtime logs contain 3,262
`drawdown_exit_blocked_quote_quality` events in the extracted 120-hour window,
and no pending-confirmation or triggered-drawdown events. Event counts are
poll counts, not independent trades or proven lost exit opportunities.

The state machine first waits for an 80%, 90%, or 85% drawdown from peak, then
requires current mark at least $0.25, adequate bid/mark and acceptable spreads.
For an afternoon peak of $1.31, an 85% drawdown triggers at $0.1965 or below.
The $0.25 gate therefore makes the afternoon trailing exit impossible for that
peak, even with otherwise perfect quotes. To have any overlap between trigger
and mark floor, peak must reach at least $1.25 morning, $2.50 late morning,
or $1.6667 afternoon. Other quote gates can narrow the overlap further.

September 1, 9, 14 and 25 lost money despite recorded confirmed peaks at least
twice the entry debit. This supports an exit-mechanics investigation; it does
not establish that selling at those peaks was possible or optimal. Poor quotes
near zero legitimately cannot be sold. Simply disabling quality safeguards
would create optimistic exits.

**Improvement:** first capture each blocking reason with executable bid and
remaining tent geometry. Replay one XSP-only candidate that arms protection
earlier, before value collapses below the sellable range, against an explicit
hold-to-settlement baseline. Price exits at available bids plus fees and stress;
keep freshness and spread safeguards. Profitprotector parameters in the YAML
are currently inactive because the selected policy is `peakvaluetrailer`.
`max_loss_from_cost: 0.50` is also inactive with the absolute stop disabled.

Evidence: `position/state_machine.py:98,214`, XSP YAML, runtime exit evidence.

### 3. High — the existing DB replay is not complete XSP exit parity

Entry selection is shared, but the exit simulator updates its peak as the
maximum mark. It does not apply the runtime's quote-quality peak filter,
three-poll peak confirmation, jump rejection, or exit-quality gates.
`_sim_parity_fields` also collapses regime-specific minimum hold times to their
maximum (45 minutes instead of XSP's 30-minute morning value). Three minute
samples are not automatically equivalent to three runtime monitor polls.

An apparent improvement from the legacy XSP sweep can consequently come from
exits that runtime would block. The current research core is SPX-only; use of
its experiment identifiers does not make an XSP evaluation valid.

**Improvement:** replay fixed XSP entries using the actual PositionManager and
ProfitStateMachine policies, aligned observation cadence, quality/freshness and
attributed settlement. Require agreement on peak acceptance, first eligible
exit and dollars on representative sessions before parameter comparisons.
No optimization backtest was run in this review because this gap is material.

Evidence: `scripts/run_backtest_db.py:133,2484`,
`backtest/simulation_engine.py:568,609`, `position/position_manager.py:294`.

### 4. Medium — SPX proxy selection policy still governs XSP widths

`select_entry_candidate` hardcodes first-eligible-width preference for XSP.
The helper explicitly describes keeping XSP scaled to SPX. If a narrower
eligible width exists, a wider candidate is never compared on its merits.
This is tested behavior, not an accidental regression. It conflicts with the
rationale of independently evaluating XSP, but removing it is an unproven
strategy experiment, not a safe profitability fix.

The VIX center anchors also depend on position in the width bucket, not just
width. Changing bucket membership changes center placement as well as widths.
For example width 4 is assigned sigma 0.75 in `[3,4]`, 0.50 in `[3,4,5]`,
and 0.25 in `[4,5]`. Keep that confound explicit in comparisons.

**Improvement:** compare fixed width/center policies one at a time, holding the
other constant; rank only after verified net-cost and near-tied-fly stability
checks. Preserve the current selection as the frozen baseline.

Evidence: `strategy/entry_selection.py:125`, `strategy/width_selection.py:16`,
`strategy/butterfly_builder.py:46`; existing first-width regression test.

### 5. Medium — execution and settlement need their own evidence gates

Recent entry drag averages $3.70 on a recorded $3.90 per-trade edge. Treat a
mark-only winner as provisional. Cboe specifies a $100 multiplier and $0.01
minimum tick, and permits $0.50 strike intervals for XSP weeklies. The center
anchor currently rounds small widths to integer strikes although actual chain
candidates may have half-point strikes; study rounding as an isolated
hypothesis rather than assuming finer placement helps.

Recent settlement metadata uses the final regular-session one-minute XSP close.
That is an attributed market-data proxy. Cboe defines exercise settlement as
one tenth of the official S&P 500 closing price; a last intraday bar is not
independent proof of the official settlement. All recent results depend on this
terminal value. Small terminal-price differences can matter near a fly wing.

**Improvement:** retain both mark and marketable diagnostics, refuse missing or
crossed quote evidence in research, and reconcile terminal valuations against
official settlement observations. Do not relabel SPX intraday data as XSP or
claim these paper estimates are actual broker executions.

Primary source: [Cboe XSP specifications](https://www.cboe.com/tradable_products/sp_500/mini_spx_options/specifications).
Code: `execution/order_manager.py:355`, `services/position_service.py:921`,
`strategy/butterfly_builder.py:120`.

## Proposed evaluation sequence

1. Fix/reconcile evidence mechanics: risk posting, XSP exit-policy parity, and
   terminal valuation attribution. Freeze current config and data hashes.
2. Replay exactly the same observed XSP entries with current management and
   hold-to-settlement. Verify known historical outcomes before considering a
   candidate. Retain no-entry sessions and observation gaps explicitly.
3. Evaluate one earlier protection policy; then, separately, one width/anchor
   policy. Score net expectancy, trade-close and sampled open-position drawdown,
   paired daily P&L, top-three-removed results and near-tied selection sensitivity.
   Keep the existing position/trade limits unchanged.
4. Treat all data inspected here as development evidence. Register candidates
   before looking at a new forward cohort. A candidate must beat the baseline
   after fees and adverse pricing, avoid a material drawdown deterioration and
   remain competitive after removing its three largest wins. Failure means
   reject/refine, not activation. No sample size is claimed sufficient in advance.

Recent CALLs are +$151 over 12 trades; PUTs are −$73 over eight. This is too
small and winner-concentrated to justify switching to CALL-only. No new capital,
trading activation or deployment is recommended from this review.

## Verification and artifacts

- Focused existing entry-selection, state-machine, position-manager and risk
  tests: **46 passed**. They verify current mechanics; they do not prove edge,
  close-side idempotency, or runtime/replay parity.
- Runtime readiness, mode, restart count and four source hashes checked.
- Queries ran inside an explicit read-only transaction with a statement timeout.
- No new parameter backtest, broker account read, order write, service restart
  or production mutation was performed.
- Local source commit: `334994a8a8421e7c3410abf8045ac87a92da0417`.
  Remote checkout: `288d6cb321e611a94acc819fa96fc5e429ff836e`.
- Preserved JSON evidence, extraction SQL, derived metrics, manifest and a
  standalone visual report: `reports/research/xsp-review-2026-10-06/`.
  Research reports are ignored by Git; this review document is tracked normally.

The managed Canvas project directory could not be identified for this Linux
workspace. The standalone HTML report is the visual deliverable instead.
