# Acceptance Tests

This document defines the behavior-level acceptance suite for a complete Fable refactor.
It is intentionally implementation-agnostic: Fable may choose a new internal design, but
the rebuilt system should not move to the next phase until the relevant checks pass.

Use this file with:

- `FABLE_REFACTOR_PLAN.md` for phase order.
- `DATABASE_COMPATIBILITY.md` for historical data contracts.
- `DOMAIN_MODEL.md` for typed model expectations.
- `CONFIG_MATRIX.md` for current profile defaults.
- `BEHAVIORAL_SPEC.md` for strategy, execution, lifecycle, and live-gating rules.
- `FIXTURE_MANIFEST.md` for exact deterministic fixture identifiers and expected
  candidate outputs.

## Test Data Package

Fable should build a small deterministic fixture package before implementing strategy
logic. Do not depend on a full live database dump for unit tests.
The exact initial fixture ids, snapshot timestamps, trade ids, config hashes, and
expected selected candidates are defined in `FIXTURE_MANIFEST.md`.

Required fixtures:

| Fixture | Required Contents | Purpose |
| --- | --- | --- |
| SPX chain snapshot | One full 0-DTE row-oriented chain, matching spot tick, and daily bars | Baseline DB adapter and candidate tests. |
| NDX chain snapshot | One full 0-DTE row-oriented chain | Validates NDX symbol root and 10-point-compatible widths. |
| XSP chain snapshot | One full 0-DTE row-oriented chain | Validates XSP scale, minimum debit, quote quality, and narrow ticks. |
| Monitoring quote sequence | Lower, center, upper leg quotes across multiple timestamps for one open trade | Peak tracking, drawdown, quote quality, and lifecycle tests. |
| Trade rows | Open, closed, cash-settled, and failed-exit/retry examples with secrets redacted | Trade reconstruction and lifecycle tests. |
| Decision events | Candidate selected, candidate rejected, risk blocked, exit signalled, settlement event | Observability and audit compatibility. |
| Config profiles | Redacted SPX, NDX, and XSP YAML profiles | Config loader and per-asset behavior tests. |

Secrets, account ids, and token values must not appear in fixtures.

## Phase 1: Database Adapter Acceptance

The adapter is accepted when it proves read-only compatibility with the current
TimescaleDB market-data shape.

Required tests:

| Behavior | Expected Result |
| --- | --- |
| Connect with read-only credentials or read-only mode | Adapter can run market-data queries without write permissions. |
| Load one exact chain timestamp | Returns all rows for one `underlying`, `expiration`, and `snapshot_time`. |
| Load nearest-at-or-before chain timestamp | Selects the latest snapshot at or before the requested timestamp. |
| Load nearest-at-or-before spot | Returns the correct spot tick for the requested underlying and time. |
| Load daily bars | Returns prior daily bars keyed by `date` and `underlying`. |
| Timezone filtering | ET calendar-day filters work from UTC `TIMESTAMPTZ` columns. |
| Decimal conversion | Numeric prices, strikes, and greeks do not round through binary floats. |
| Nullable columns | Nullable bid, ask, mark, greeks, and extended quote fields are handled deliberately. |
| Row-oriented chain shape | Adapter does not expect JSON blobs, `id`, or `chain_data` in live tables. |
| Read-only guarantee | Tests fail if adapter attempts to insert, update, delete, migrate, or create tables. |

Minimum smoke cases:

- SPX exact snapshot load.
- NDX exact snapshot load.
- XSP exact snapshot load.
- `$VIX` spot lookup.
- One missing-data lookup that returns a typed empty result or typed error.

## Phase 2: Domain And Selection Acceptance

The domain layer is accepted when typed data can drive deterministic butterfly candidate
construction and selection.

Required tests:

| Behavior | Expected Result |
| --- | --- |
| OCC/Schwab symbol parsing | Parses padded roots, `YYMMDD`, option type, and encoded strikes. |
| Underlying vs symbol root | Allows `SPX` with `SPXW`, `NDX` with `NDXP`, and `XSP` with `XSP`. |
| Model valuation field | Keeps broker mark, computed mid, and model mark separate. |
| Symmetric spread construction | Uses lower = center - width and upper = center + width by default. |
| Missing leg rejection | Rejects candidates when any of lower, center, or upper quote is missing. |
| Bad quote rejection | Rejects negative prices, `ask < bid`, zero/negative fly cost, and malformed strikes. |
| Debit floor | Rejects costs below configured `min_debit`. |
| Cost ceiling | Rejects costs above `max_cost_per_width`. |
| Reward/risk floor | Rejects candidates below `rr_min`. |
| Breakeven math | Lower and upper breakevens bracket the center strike. |
| VIX bucket resolution | Resolves SPX and XSP width buckets from VIX. |
| NDX static widths | Uses `[80, 100, 150]` without VIX buckets. |
| VIX target center | Places CALL centers above spot and PUT centers below spot. |
| Cross-width selection | Uses deterministic tie-breaking and XSP first-width preference where required. |
| Research mode separation | Rejected candidates can appear only in explicit research/audit mode. |

Property-based coverage should include:

- Missing strikes around the target center.
- Zero, negative, or missing VIX.
- 0-DTE and late-day DTE floor cases.
- Very wide bid/ask spreads.
- Equal reward/risk ties.
- Asset-specific strike increments.

## Phase 3: Paper Execution And Lifecycle Acceptance

The paper engine is accepted when it can replay position updates, record realistic fills,
and manage exits without broker writes.

Required tests:

| Behavior | Expected Result |
| --- | --- |
| Paper entry fill | Uses mark-based convention with configured buffer, slippage, and commissions. |
| Paper exit fill | Uses live spread when available and falls back only as specified. |
| Spread warning penalty | Degrades fill price when spread is above warning threshold. |
| Spread hard block | Refuses paper fills when leg or composite spread quality fails. |
| Forced exit fallback | Records forced exits explicitly with spread-quality fields. |
| Profit regimes | Classifies `LOSS`, `NEAR_LONG`, and `PROFIT_TENT` from mark vs entry. |
| Peak acceptance | Applies mark minimum, quote quality, jump guard, and confirmation polls. |
| Drawdown exit | Requires min peak, min hold, quote quality, and confirmation rules. |
| Profit protector floors | Exits only when activation and floor conditions are met. |
| Absolute loss stop | Fires only when enabled and threshold is crossed. |
| Pre-close exit | Fires only when enabled and close-time threshold is crossed. |
| Cash settlement | Closes cash-settled index positions after market close without routing liquidation orders. |
| Idempotent exit attempts | Does not double-close or double-fill on retry, timeout, or restart. |
| Terminal close | Rejects any transition from `CLOSED` back to open or exiting states. |

Lifecycle states to test:

- `OPEN_MONITORING`
- `EXIT_SIGNALLED`
- `EXITING`
- `EXIT_FAILED_RETRYABLE`
- `CASH_SETTLING`
- `CLOSED`

## Phase 4: Risk And Runtime Acceptance

Risk behavior is accepted when every entry path passes account, quantity, daily, weekly,
and fail-safe checks before any execution attempt.

Required tests:

| Behavior | Expected Result |
| --- | --- |
| Max trades per day | Blocks entries after the configured daily count. |
| Max daily loss | Blocks entries after daily loss threshold. |
| Max weekly loss | Blocks XSP when rolling weekly loss threshold is reached. |
| Consecutive losses | Blocks XSP after configured consecutive-loss threshold. |
| Max position size | Rejects quantity above configured maximum. |
| Buying power | Blocks when available buying power is below minimum. |
| Balance API failure | Fails closed when configured to do so. |
| Decision logging | Emits structured risk-block event with exact failed guard. |
| No side effects on block | Does not build or route orders after a risk block. |

## Phase 5: Live Boundary Acceptance

Live broker integration is accepted only after the paper/replay system passes. These
tests must use mocks or a non-ordering broker test double.

Required tests:

| Behavior | Expected Result |
| --- | --- |
| Default mode | Live routing disabled by default. |
| Config-only approval | Fails closed before broker order submission. |
| Environment-only approval | Fails closed before broker order submission. |
| Typo confirmation | Fails closed before broker order submission. |
| Both approvals present | Allows construction of live execution module. |
| Pre-submit recheck | Rechecks both approvals immediately before every place-order call. |
| Paper isolation | Paper execution cannot import or call Schwab place-order methods. |
| Token secrecy | Logs do not include tokens, account ids, or secret values. |
| Order idempotency | Retry path reconciles existing broker order status before submitting another close order. |

No acceptance test should place a real Schwab order.

## Observability Acceptance

The rebuilt system must make decisions auditable without relying on ad hoc debugging.

Required structured events:

| Event | Required Fields |
| --- | --- |
| Candidate selected | asset, direction, width, center, cost, reward/risk, spot, VIX, selection method. |
| Candidate rejected | asset, direction, width, center, failed guard, quote fields, cost, reward/risk. |
| Risk blocked | asset, trade date, failed guard, configured threshold, observed value. |
| Paper fill accepted | trade id, side, limit, fill price, spread fields, penalty fields, forced flag. |
| Paper fill blocked | trade id or candidate id, failed spread guard, quote fields, threshold. |
| Profit state transition | trade id, old state, new state, entry price, current mark, peak. |
| Peak update | trade id, old peak, candidate peak, accepted flag, rejection reason. |
| Exit signal | trade id, reason, urgency, target credit, current mark, peak, drawdown. |
| Exit attempt | trade id, attempt id, mode, order id if present, result, retryable flag. |
| Cash settlement | trade id, settlement value, expiration, close timestamp. |

## Golden Replay Requirements

Before a complete refactor is considered usable, define at least these golden replay
cases from redacted historical data:

| Case | Purpose |
| --- | --- |
| SPX normal entry day | Proves baseline VIX bucket selection, candidate ranking, and paper entry. |
| NDX wide-strike day | Proves static NDX widths, larger center tolerance, and quote-quality behavior. |
| XSP min-hold day | Proves XSP scale, min debit, min hold, and strict quote-quality behavior. |
| Quote-quality blocked exit | Proves drawdown exit can be blocked by bad quotes. |
| Cash-settled position | Proves market-close cash settlement without liquidation order routing. |
| No-trade day | Proves the system can reject all candidates or risk-block without side effects. |

Each golden case should record:

- Input config profile.
- Market-data fixture identifiers.
- Source trade id or decision-log id where applicable.
- Config hash.
- Expected active widths.
- Expected selected candidate or expected no-trade reason.
- Expected fill or fill-block decision.
- Expected lifecycle transitions.
- Expected final trade status and PnL convention.

## Current Reference Test Map

These current Python tests identify behavior that should be represented in Fable's own
test suite. They are references, not implementation to copy.

| Behavior Area | Current Reference Tests |
| --- | --- |
| Config loading | `tests/test_config.py` |
| Candidate construction | `tests/test_butterfly_builder.py`, `tests/test_butterfly_selector.py` |
| Entry selection and parity | `tests/test_entry_selection.py`, `tests/test_entry_selection_parity.py` |
| Width selection | `tests/test_width_selection.py` |
| Direction and gap filters | `tests/test_bias_filter.py`, `tests/test_gap_regime_filter.py` |
| Order construction and execution | `tests/test_order_builder.py`, `tests/test_order_manager.py` |
| Profit state machine | `tests/test_state_machine.py` |
| Peak and quote tracking | `tests/test_position_manager.py`, `tests/test_monitoring_leg_replay.py` |
| Cash settlement | `tests/test_position_service_settlement.py` |
| Risk gates | `tests/test_risk_engine.py` |
| DB-backed replay/backtest | `tests/test_run_backtest_db.py`, `tests/test_run_backtest_db_defaults.py` |
| Simulation parity | `tests/test_simulation_parity.py`, `tests/test_exit_mark_parity.py` |
| Reporting | `tests/test_live_performance_report.py`, `tests/test_daily_report_card.py` |

## Completion Gate

The Fable refactor is not complete until:

- Every phase-level acceptance group passes.
- Golden replay cases are deterministic.
- Live broker routing remains disabled by default.
- Runtime writes are isolated from current production tables.
- Observability events are sufficient to explain every entry, rejection, fill, exit, and
  risk block without inspecting raw code.
