# Behavioral Specification

This document formalizes the current open-position monitoring, profit-state,
and exit-execution behavior for the 0-DTE butterfly system.

The current implementation does not use a single persisted
`ENTERED -> TRAILING -> EXITING` state machine. It has two separate concerns:

- Profit classification in `ProfitStateMachine`: `LOSS`, `NEAR_LONG`,
  `PROFIT_TENT`.
- Trade lifecycle in `PositionService`: open-position polling, exit signal
  evaluation, exit-order execution, DB closure, or cash settlement.

Any refactor should keep those concerns explicit or intentionally merge them
with clear persistence and idempotency rules.

## Runtime Inputs

| Input | Source | Notes |
| --- | --- | --- |
| Latest Schwab option chain | `PositionService.monitor_loop` | Polled while market is open. |
| Leg quotes for lower/center/upper strikes | `PositionService._extract_quotes` | Used to compute mark, bid, ask, and quote quality. |
| Position mark value | `PositionManager.update_position_value` | `fly_mark_value(lower, center, upper)`, floored at `0.0`. |
| Position bid value | `PositionManager.update_position_value` | `lower.bid + upper.bid - 2 * center.ask`, floored at `0.0`. |
| Entry price | `TradeRecord.entry_price` | Loaded from the open trade. |
| Peak value | `PositionManager` plus persisted `trade.peak_value` | Restored on monitor startup and persisted when a new accepted peak is reached. |
| Time regime | `get_time_regime(minutes_since_open)` | Selects morning, late-morning, or afternoon settings. |
| Minutes to close | `minutes_to_close()` | Used only if pre-close exit is explicitly enabled. |
| Position age | `PositionService` | Used for regime `min_hold_minutes`. |
| Profit-management config | `configs/config*.yaml` | Controls drawdown thresholds, confirmation polls, quote-quality gates, and optional loss stops. |

## Profit State Invariants

`ProfitStateMachine` derives its state from current PnL relative to entry cost.
These states are mark-to-entry classifications, not order lifecycle states.

| Profit State | Invariant | Side Effects |
| --- | --- | --- |
| `LOSS` | `entry_price <= 0` or `pnl / entry_price < 0` | Does not clear `_ever_in_profit` once it was set. |
| `NEAR_LONG` | `0 <= pnl / entry_price < 0.5` | Sets `_ever_in_profit = true`. |
| `PROFIT_TENT` | `pnl / entry_price >= 0.5` | Sets `_ever_in_profit = true`. |

## Position Tracking Invariants

| Field | Invariant |
| --- | --- |
| `current_value` | Current butterfly mark, rounded to 4 decimals. Missing quotes fall back to current accepted peak value. |
| `peak_value` | Highest accepted mark value since entry or restored persisted peak. |
| `drawdown_from_peak` | `(peak_value - current_value) / peak_value` when peak is positive, otherwise `0.0`. |
| `spread_bid` | Current executable bid estimate for the fly, or `None` if quotes are missing. |
| `spread_ask` | Current executable ask estimate for the fly, or `None` if quotes are missing. |
| `bid_to_mark_ratio` | `spread_bid / current_value` when both values are available and mark is positive. |
| `peak_bid` | Highest observed fly bid since entry. |
| `pending_peak_value` | Candidate new peak waiting for peak-confirmation polls. |
| `peak_update_rejected` | True when a possible new peak is rejected by mark minimum, quote quality, jump guard, or pending confirmation. |

## Peak Acceptance Matrix

This matrix governs whether a higher mark becomes the accepted `peak_value`.

| Current Condition | Guard | Result | Action |
| --- | --- | --- | --- |
| `current_value <= peak_value` | Always | Peak unchanged | Clear pending peak candidate. |
| `current_value > peak_value` | `current_value < quote_quality.min_mark_value` | Peak rejected | Clear pending peak; reason `mark_below_minimum`. |
| `current_value > peak_value` | `peak_tracking.require_quote_quality` and quote quality fails | Peak rejected | Clear pending peak; reason `quote_quality`. |
| `current_value > peak_value` | Jump exceeds both `max_jump_ratio` and `max_jump_abs` | Peak rejected | Clear pending peak; reason `mark_jump`. |
| `current_value > peak_value` | `peak_tracking.confirmation_polls == 1` | Peak accepted | Set `peak_value = current_value`. |
| `current_value > peak_value` | No pending peak or current falls below pending tolerance | Pending | Set pending peak and count `1`; reason `pending_confirmation`. |
| `current_value > peak_value` | Pending confirmation count below required polls | Pending | Update pending peak max and increment count; reason `pending_confirmation`. |
| `current_value > peak_value` | Pending confirmation count reaches required polls | Peak accepted | Set `peak_value = pending_peak_value`; clear pending. |

## Exit Signal Matrix

This matrix describes `ProfitStateMachine.evaluate(pos)`.

| Current Profit State | Trigger Event | Condition / Guard | Next Signal State | Action to Execute |
| --- | --- | --- | --- | --- |
| Any | New mark snapshot | `exit_before_close_minutes > 0` and `minutes_to_close <= exit_before_close_minutes` | `EXIT_SIGNALLED` | Return `ExitSignal(reason="end_of_day", target_credit=current_value, urgency="immediate")`. |
| Any | New mark snapshot | `use_absolute_loss_stop` and `(entry_price - current_value) / entry_price >= max_loss_from_cost` | `EXIT_SIGNALLED` | Return `ExitSignal(reason="absolute_loss_stop", target_credit=current_value, urgency="high")`. |
| Any | New mark snapshot | No config for current `time_regime` | Remain open | Return no signal. |
| Any | New mark snapshot | `min_hold_minutes > 0` and `position_age_minutes < min_hold_minutes` | Remain open | Reset pending drawdown confirmation; return no signal. |
| `LOSS` | New mark snapshot | Never reached profit, or accepted peak below `entry_price * min_peak_profit_ratio` | Remain open | Reset pending drawdown confirmation; return no signal. |
| `NEAR_LONG` or `PROFIT_TENT` | New mark snapshot | `_ever_in_profit` false | Remain open | Reset pending drawdown confirmation; return no signal. |
| `NEAR_LONG` or `PROFIT_TENT` | New mark snapshot | `peak_value < entry_price * min_peak_profit_ratio` | Remain open | Reset pending drawdown confirmation; return no signal. |
| `NEAR_LONG` or `PROFIT_TENT` | New mark snapshot | Strategy is `profitprotector`, profit-lock activation reached, and `current_value <= entry_price + profit_lock_floor_profit` | `EXIT_SIGNALLED` | Return `ExitSignal(reason="profitprotector_profit_floor", target_credit=current_value, urgency="high")`. |
| `NEAR_LONG` or `PROFIT_TENT` | New mark snapshot | Strategy is `profitprotector`, breakeven activation reached, and `current_value <= entry_price + breakeven_floor_profit` | `EXIT_SIGNALLED` | Return `ExitSignal(reason="profitprotector_breakeven_floor", target_credit=current_value, urgency="high")`. |
| `NEAR_LONG` or `PROFIT_TENT` | New mark snapshot | `drawdown_from_peak < effective_drawdown_threshold` | Remain open | Reset pending drawdown confirmation; return no signal. |
| `NEAR_LONG` or `PROFIT_TENT` | New mark snapshot | `drawdown_from_peak >= effective_drawdown_threshold` and quote quality fails | Remain open | Log `drawdown_exit_blocked_quote_quality`; reset pending drawdown confirmation; return no signal. |
| `NEAR_LONG` or `PROFIT_TENT` | New mark snapshot | Drawdown guard passes but `confirmation_polls` not met | Remain open | Log `drawdown_exit_pending_confirmation`; increment pending drawdown confirmation; return no signal. |
| `NEAR_LONG` or `PROFIT_TENT` | New mark snapshot | Drawdown guard passes and confirmation polls met | `EXIT_SIGNALLED` | Return `ExitSignal(reason="drawdown_{time_regime}", target_credit=current_value, urgency="high")`. |

## Effective Drawdown Threshold

| Strategy | Condition | Effective Threshold |
| --- | --- | --- |
| `peakvaluetrailer` | Always | Current regime `drawdown_threshold`. |
| `profitprotector` | `peak_value < entry_price * large_peak_profit_ratio` | Current regime `drawdown_threshold`. |
| `profitprotector` | `peak_value >= entry_price * large_peak_profit_ratio` | `min(regime.drawdown_threshold, large_peak_drawdown_threshold)`. |

## Quote Quality Guard

When `quote_quality.enabled` is false, drawdown exits are not blocked by quote
quality. When enabled, all of these must pass:

| Guard | Required Condition |
| --- | --- |
| Quote fields present | `spread_bid`, `spread_ask`, and `bid_to_mark_ratio` are not `None`. |
| Positive bid | `spread_bid > 0`. |
| Bid-to-mark | `bid_to_mark_ratio >= min_bid_to_mark_ratio`. |
| Mark minimum | `current_value >= min_mark_value`. |
| Spread width ratio | If configured and `current_value > 0`, `(spread_ask - spread_bid) / current_value <= max_spread_width_ratio`. |
| Leg spread ratio | If configured, `max_leg_spread_to_mark_ratio <= configured maximum`. |
| Leg spread absolute | If configured, `max_leg_spread_abs <= configured maximum`. |

## Strategy Guardrails And Candidate Validation

This section defines target strategy-selection behavior for the refactor. The
current code uses configured `wing_widths` or `vix_width_buckets`, then anchors
candidate center strikes with VIX-implied expected move. The new platform core
may keep the current bucket model, but if it introduces dynamic width selection,
the formula and fallbacks below must be explicit and test-covered.

### Current Width And Center Selection Data

| Concept | Current Source | Current Behavior |
| --- | --- | --- |
| Static widths | `strategy.wing_widths` | Used when no VIX bucket override is active, and for sweeps/backtests. |
| VIX width buckets | `strategy.vix_width_buckets` | Runtime VIX selection resolves the first bucket where `vix < vix_max`; bucket widths are scanned narrow to wide. |
| VIX expected move | `vix_expected_move(vix, spot)` | Computes `spot * (vix / 100) / sqrt(252)` for a one-trading-day expected move. |
| Target center | `vix_target_center(...)` | Places CALL centers above spot and PUT centers below spot by a sigma fraction of expected move. |
| Sigma fractions | Bucket position or `VIX_SIGMA_BY_WIDTH` | Narrow/mid/wide candidates use fractions around `0.25`, `0.50`, and `0.75`. |
| Cross-width selection | `select_cross_width_candidate` | Chooses among one best candidate per width; XSP prefers the first width in the active bucket. |

Current configured width sets:

| Asset | Current Width Source | Widths / Buckets |
| --- | --- | --- |
| SPX | VIX buckets | `<17: [20,25,30]`, `<24.5: [20,30,40]`, `<32: [40,45,50]`, catch-all `[50,55,65]`. |
| NDX | Static widths | `[80, 100, 150]`, with 10-point grid constraint. |
| XSP | VIX buckets | `<17: [3,4]`, `<24.5: [3,4,5]`, `<32: [4,5]`, catch-all `[4,5]`. |

### Dynamic Wing Width Formula

If dynamic width calculation replaces or supplements configured width buckets,
calculate the raw target width from annualized volatility and remaining DTE:

```text
raw_expected_move = underlying_spot * (vix / 100) * sqrt(clamped_dte_days / 365)
target_width_raw = raw_expected_move * width_multiplier
target_width = round_to_valid_strike_increment(target_width_raw)
```

Required definitions:

| Term | Required Definition |
| --- | --- |
| `underlying_spot` | Current underlying index spot used for the option-chain snapshot. |
| `vix` | Current VIX value as a percentage, e.g. `18.0` means `18%`. |
| `dte_days` | Calendar days to expiration, expressed as a positive float. For same-day expiration, use remaining minutes divided by `1440`. |
| `clamped_dte_days` | `max(dte_days, min_dte_floor_days)`. The default floor should be `0.5` day unless asset-specific tests justify another value. |
| `width_multiplier` | Configurable fraction of expected move used for wing width. This must be explicit per asset or strategy profile. |
| `round_to_valid_strike_increment` | Rounds to the closest valid width supported by the underlying's listed strikes. NDX must remain on a 10-point-compatible grid. |

Do not allow DTE to collapse the width toward zero intraday. 0-DTE contracts
approach expiration continuously, so a formula without a floor will produce
unstable, too-narrow flies late in the session.

Fallback rules:

| Condition | Required Fallback |
| --- | --- |
| `vix` is missing or non-positive | Use configured width buckets/static widths; do not compute dynamic width. |
| `underlying_spot <= 0` | Reject selection pass as bad market data. |
| `dte_days <= 0` before market close | Use `min_dte_floor_days`, not zero. |
| Computed width below minimum listed interval | Clamp to configured asset minimum width. |
| Computed width above maximum allowed width | Clamp or reject according to `max_dynamic_width`; log the decision. |
| Rounded width not present in chain | Snap to nearest configured valid width with all three legs present. |
| Dynamic calculation unavailable | Fall back to current static baseline widths: SPX bucket widths, NDX `[80,100,150]`, XSP bucket widths. |

Suggested dynamic-width config fields:

| Config Field | Meaning |
| --- | --- |
| `dynamic_width.enabled` | Enables formula-based wing-width calculation. |
| `dynamic_width.width_multiplier` | Fraction of expected move used as the wing width. |
| `dynamic_width.min_dte_floor_days` | Minimum DTE used in the square-root term; default `0.5`. |
| `dynamic_width.min_width` | Asset minimum wing width. |
| `dynamic_width.max_width` | Asset maximum wing width. |
| `dynamic_width.valid_widths` | Optional explicit set of widths allowed after rounding. |
| `dynamic_width.strike_increment` | Width rounding increment for the underlying. |
| `dynamic_width.fallback_widths` | Static widths to use when formula inputs are invalid or unavailable. |

### Candidate Construction Invariants

| Invariant | Required Behavior |
| --- | --- |
| Symmetric strikes | Default butterfly construction must set `lower = center - width` and `upper = center + width`. |
| Directional OTM center | CALL centers must be above spot; PUT centers must be below spot. |
| Complete legs | Lower, center, and upper strikes must all exist in the chain for the selected option type. |
| Positive premium | Composite mark cost must be strictly above the configured minimum debit. |
| Bounded cost | Composite mark cost must not exceed `max_cost_per_width[width]` unless an explicit research mode includes rejected candidates. |
| Reward/risk floor | Candidate must satisfy `reward_risk >= rr_min` before entering normal selection. |
| Breakeven consistency | `lower_be = lower + cost`, `upper_be = upper - cost`, and both must bracket the center. |
| Quote retention | Candidate should retain all three `OptionQuote` objects for downstream spread-quality checks. |

### Spread Validation Matrix

Bad quotes and toxic spreads must be discarded before candidates enter the
evaluation engine. This validation belongs in candidate construction or an
immediate post-construction quality gate, before ranking and order execution.

| Metric | Guardrail Constraint | Automated Action |
| --- | --- | --- |
| Individual leg bid-ask spread | If `(ask - bid) / max(mark, tick_floor) > 0.15` on any leg | Toss candidate; log `candidate_rejected_leg_spread`; protect against illiquidity. |
| Individual leg quote sanity | If `bid < 0`, `ask < 0`, `mark < 0`, or `ask < bid` | Reject candidate; flag malformed quote data. |
| Total premium cost | If `total_cost <= 0.00` | Reject candidate; flag as arbitrage or data anomaly. |
| Configured debit floor | If `total_cost < strategy.min_debit` | Reject candidate; treat penny/noise trades as non-tradeable. |
| Width cost ceiling | If `total_cost > max_cost_per_width[width]` | Reject candidate unless research mode explicitly includes all candidates. |
| Symmetry validation | If `lower != center - width` or `upper != center + width` | Reject unless asymmetric mode is explicitly enabled. |
| Asymmetric mode | If asymmetric mode is enabled | Require a separate config flag, separate tests, and explicit max skew bounds. |
| Missing leg | If any of lower, center, or upper leg is unavailable | Reject candidate; do not synthesize missing live quotes. |
| Reward/risk | If `(width - total_cost) / total_cost < rr_min` | Reject candidate before selection. |
| Composite spread | If `(fly_ask - fly_bid) / max(fly_mark, tick_floor)` exceeds configured max | Reject candidate or mark as paper-fill-blocked according to spread-penalty policy. |

Implementation notes:

- The current builder already constructs symmetrical spreads and rejects
  candidates below `min_debit`, above `max_cost_per_width`, or below `rr_min`.
- The 15% individual-leg spread guard is stricter than current builder behavior
  and should be added before candidate ranking if adopted.
- `include_all=True` should remain a research/audit mode only; live trading and
  normal backtests must not allow rejected candidates into execution.
- Rejection events should include asset, direction, center, width, leg strikes,
  cost, fly bid/ask/mark, and the exact failed guard.

## Execution Lifecycle Matrix

This matrix describes what `PositionService` does after `ProfitStateMachine`
emits an exit signal.

| Current Lifecycle State | Trigger Event | Condition / Guard | Next Lifecycle State | Action to Execute |
| --- | --- | --- | --- | --- |
| `OPEN_MONITORING` | Monitor loop starts | Open trade exists | `OPEN_MONITORING` | Reset `PositionManager`, restore persisted peak, reset `ProfitStateMachine`. |
| `OPEN_MONITORING` | New chain snapshot | Position update succeeds | `OPEN_MONITORING` | Persist monitoring leg quotes, persist accepted peak, persist tent boundaries. |
| `OPEN_MONITORING` | New chain snapshot | Profit state changed | `OPEN_MONITORING` | Log `profit_state_transition`. |
| `OPEN_MONITORING` | Exit signal emitted | Always | `EXIT_SIGNALLED` | Log `exit_signal`; build and log exit-mark parity. |
| `EXIT_SIGNALLED` | Before order routing | Always | `EXITING` | Log `exit_signal_fired`; call `OrderManager.execute_exit(candidate, current_value, quantity, exit_reason)`. |
| `EXITING` | Exit execution returns `None` | Live mode timeout or execution failure | `OPEN_MONITORING` | Log `exit_order_failed`; notify warning; do not close trade; retry on future loop iteration. |
| `EXITING` | Exit execution returns fill | Fill data present | `CLOSED` | Close DB trade, persist ladder trace and exit metadata, record metrics, set local `exited = true`, notify exit. |
| `OPEN_MONITORING` | Market closes before an exit fill | `is_market_open()` becomes false | `CASH_SETTLING` | Do not route liquidation order for cash-settled indexes. Compute settlement value. |
| `CASH_SETTLING` | Settlement value computed | Always | `CLOSED` | Close DB trade with `exit_reason="cash_settled"`, record metrics, notify exit. |

## Exit Order Execution Matrix

| Mode | Trigger | Condition / Guard | Result |
| --- | --- | --- | --- |
| Paper | `exit_reason == "end_of_day"` | Always | Immediate paper fill at adjusted `current_value`; no ladder. |
| Paper | Exit ladder step | Live spread available and `limit_price <= spread.bid - paper_fill_buffer` | Paper fill at limit adjusted for slippage and commissions. |
| Paper | Exit ladder timeout | Deadline reached | Forced paper fill using worst observed bid floor or signal mark, adjusted for buffer, slippage, and commissions. |
| Paper | Live spread unavailable | During ladder | Use signal `current_value` until a live bid floor is observed. |
| Live | Exit ladder step | Live spread available | Start from current bid floor and step down by configured ladder step. |
| Live | Exit ladder step | Live spread unavailable | Fall back to signal `current_value`. |
| Live | Step does not fill | Order placed but not filled | Cancel order and continue ladder. |
| Live | Timeout reached | Deadline reached | Return `None`; caller keeps position open and retries later. |

## Algorithmic Refinements For 0-DTE Robustness

These are target constraints for the refactor. They are stricter than some of
the current implementation and should be treated as product requirements for the
new platform core.

### Bid-Ask Spread Penalization

Current mark pricing uses leg marks for the composite fly mark:
`lower.mark - 2 * center.mark + upper.mark`. This is clean for paper trading and
matches the existing project convention, but it can overstate tradeability when
0-DTE quotes widen during fast markets.

The refactor must add an explicit paper-fill realism gate before any simulated
entry or exit fill is accepted.

| Constraint | Required Behavior |
| --- | --- |
| Leg spread ratio | For each leg, compute `(ask - bid) / max(mark, tick_floor)`. |
| Premium-relative spread ratio | Compute each leg spread as a percentage of the overall fly premium or current fly mark. |
| Composite fly spread ratio | Compute `(fly_ask - fly_bid) / max(fly_mark, tick_floor)`. |
| Soft penalty | If spreads are above the warning threshold but below the hard block threshold, worsen the paper fill by a configurable spread penalty. |
| Hard block | If any leg or composite spread exceeds the hard threshold, block the paper fill and log a structured rejection. |
| Backtest parity | Historical backtests, paper replay, and live paper execution must use the same spread-penalty policy. |
| Auditability | Persist or log the bid, ask, mark, leg spread ratios, composite spread ratio, threshold, and chosen penalty/block decision. |

Suggested policy fields:

| Config Field | Meaning |
| --- | --- |
| `paper_spread_penalty.enabled` | Enables spread-aware paper fill realism. |
| `paper_spread_penalty.max_leg_spread_to_premium_ratio` | Hard block if any leg spread is too large relative to the fly premium. |
| `paper_spread_penalty.max_leg_spread_to_mark_ratio` | Hard block if any leg spread is too large relative to that leg's mark. |
| `paper_spread_penalty.max_composite_spread_to_mark_ratio` | Hard block if the composite fly spread is too wide relative to fly mark. |
| `paper_spread_penalty.warning_ratio` | Above this level, apply a penalty but do not block. |
| `paper_spread_penalty.penalty_per_ratio_point` | Incremental fill degradation when the warning threshold is exceeded. |
| `paper_spread_penalty.tick_floor` | Minimum denominator for low-premium options to avoid unstable ratios. |

Paper fill rules after this refinement:

| Mode | Trigger | Spread Condition | Required Result |
| --- | --- | --- | --- |
| Paper entry | Limit crosses fill threshold | Spread policy passes cleanly | Fill at threshold or limit, adjusted for existing buffer, slippage, and commissions. |
| Paper entry | Limit crosses fill threshold | Spread policy in penalty band | Fill only after adding configured spread penalty to cost. |
| Paper entry | Limit crosses fill threshold | Spread policy hard-blocks | No fill; log `paper_entry_blocked_spread_quality`. |
| Paper exit | Limit crosses fill threshold | Spread policy passes cleanly | Fill at threshold or limit, adjusted for existing buffer, slippage, and commissions. |
| Paper exit | Limit crosses fill threshold | Spread policy in penalty band | Fill only after subtracting configured spread penalty from credit. |
| Paper exit | Limit crosses fill threshold | Spread policy hard-blocks | No fill unless an explicit forced-exit policy applies; log `paper_exit_blocked_spread_quality`. |
| Paper forced exit | Timeout reached | Spread policy hard-blocks | Use forced-exit fallback only if the lifecycle requires liquidation; persist `forced=true` and spread-quality fields. |

The implementation should reuse the existing quote-quality concepts where
possible, but paper-fill spread quality must be enforced inside the execution
module, not only inside the profit-state exit guard. This prevents a backtest or
paper replay from recording fills that could not reasonably trade in the quoted
market.

### Double-Factor Live Gating

Current startup safety checks block live mode unless `paper_trading=false` is
paired with `execution.allow_live_trading=true` or an `ALLOW_LIVE_TRADING`
environment override. The refactor must harden this into an isolated live
execution boundary.

Live broker order routing must be impossible unless two independent approvals
are present and verified by the live execution module immediately before order
submission.

| Gate | Required Behavior |
| --- | --- |
| Code isolation | Paper execution and live broker execution must be separate modules/classes behind a narrow execution interface. |
| No shared place-order path | Paper code must not import or call Schwab order-placement methods. |
| Explicit config approval | Application config must contain an explicit live-routing option, e.g. `execution.mode: live` and `execution.allow_live_trading: true`. |
| Explicit environment approval | Environment must contain an exact string, not a loose boolean, e.g. `BUTTERFLY_LIVE_TRADING_CONFIRM=I_UNDERSTAND_THIS_ROUTES_REAL_ORDERS`. |
| Double verification point | The live module must verify both approvals at construction time and again immediately before every broker `place_order` call. |
| Fail closed | Missing, malformed, or mismatched approvals must raise a typed exception before any order spec is submitted. |
| Immutable mode | Execution mode must be resolved once at startup; runtime mutation from paper to live is forbidden. |
| Tests | Unit tests must prove config-only approval fails, env-only approval fails, typo approval fails, paper mode cannot place broker orders, and live mode can place orders only with both approvals. |
| Logs | Startup logs may state live mode is enabled, but must not print secrets or account ids. |

The target live gate should not accept generic truthy strings such as `true`,
`1`, or `yes`. The exact confirmation string should be long, deliberate, and
documented in one place. If a compile-time or build-time flag is available for
the deployment target, require it in addition to the runtime double gate.

## Current Config Defaults

| Asset | Strategy | Absolute Stop | Pre-Close Exit | Quote Quality | Drawdown Confirmation | Min Peak Ratio | Min Hold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPX | `peakvaluetrailer` | Disabled | Disabled | Disabled | Morning `1`, late morning `1`, afternoon `1` | `1.0` all regimes | `0` all regimes |
| NDX | `peakvaluetrailer` | Disabled | Disabled | Enabled | Morning `3`, late morning `2`, afternoon `2` | `1.5` all regimes | `0` all regimes |
| XSP | `peakvaluetrailer` | Disabled | Disabled | Enabled | Morning `3`, late morning `3`, afternoon `3` | `1.25` all regimes | Morning `30`, late morning `45`, afternoon `45` |

## Idempotency And Double-Fill Notes

The current implementation reduces same-loop duplicate close behavior by setting
the local `exited` flag immediately after the trade is closed in the database
and before notification work. However, `EXITING` is not currently persisted
before routing a live close order.

A refactor should make these behaviors explicit:

- Persist `EXIT_SIGNALLED` or `EXITING` before placing a live close order.
- Store a unique exit-attempt id with the trade id and order id.
- Reconcile Schwab order status before placing another close order after a
  timeout, process restart, or API error.
- Define whether `execute_exit` may have placed an order when it returns `None`.
- Define whether a retry reuses the original signal mark, fetches a fresh mark,
  or requires a fresh state-machine signal.
- Make `CLOSED` terminal and reject any transition from `CLOSED` back to
  `OPEN_MONITORING` or `EXITING`.

## Refactor Target State Names

If the refactor introduces explicit lifecycle states, use names that describe
execution, not mark profitability:

| Proposed Lifecycle State | Meaning |
| --- | --- |
| `OPEN_MONITORING` | Trade is open; service is polling marks and evaluating exits. |
| `EXIT_SIGNALLED` | State machine has emitted an exit signal for the latest snapshot. |
| `EXITING` | An exit order attempt is in progress or has been submitted. |
| `EXIT_FAILED_RETRYABLE` | Previous attempt failed or timed out; position is still open pending reconciliation. |
| `CASH_SETTLING` | Market closed without liquidation; settlement value is being computed. |
| `CLOSED` | Terminal state; trade has exit price, exit time, reason, and PnL persisted. |

Profit regime can remain a separate enum:

| Proposed Profit Regime | Meaning |
| --- | --- |
| `LOSS` | Current mark is below entry. |
| `NEAR_LONG` | Current mark is at or above entry but below 50% gain. |
| `PROFIT_TENT` | Current mark is at least 50% above entry. |

## Source Map

| Behavior | Source |
| --- | --- |
| Profit state enum and exit signal logic | `src/butterfly_guy/position/state_machine.py` |
| Position mark, bid, peak, drawdown, and quote-quality inputs | `src/butterfly_guy/position/position_manager.py` |
| Profit protector floor and effective drawdown helpers | `src/butterfly_guy/position/profit_policy.py` |
| Monitor loop and DB close/cash settlement behavior | `src/butterfly_guy/services/position_service.py` |
| Exit ladder and paper/live execution behavior | `src/butterfly_guy/execution/order_manager.py` |
| Profit-management settings schema | `src/butterfly_guy/core/config.py` |
| VIX width bucket and target center logic | `src/butterfly_guy/strategy/butterfly_builder.py`, `src/butterfly_guy/strategy/entry_selection.py` |
| Cross-width selection behavior | `src/butterfly_guy/strategy/width_selection.py` |
| Current live startup gate | `src/butterfly_guy/scripts/run_live.py` |
| Runtime defaults | `configs/config.yaml`, `configs/config_ndx.yaml`, `configs/config_xsp.yaml` |
| State-machine tests | `tests/test_state_machine.py` |
| Peak-tracking tests | `tests/test_position_manager.py` |
| Exit-order tests | `tests/test_order_manager.py` |
| Candidate validation and width tests | `tests/test_butterfly_builder.py`, `tests/test_entry_selection.py`, `tests/test_config.py` |
