# Prospective execution validation — spx-prospective-2026-09-22

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-09-22
- Generated: 2026-09-23T03:24:33.392714+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 0
- No signal: 0
- Incomplete data: 0
- Eligible trades: 0
- Cash-settled trades: 0

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 0 | $0.00 | $0.00 | 0.000 | 0.0% | $0.00 | $0.00 | $0.00 | 0.0% | 0.0% |
| marketable | 0 | $0.00 | $0.00 | 0.000 | 0.0% | $0.00 | $0.00 | $0.00 | 0.0% | 0.0% |
| corrected_midpoint | 0 | $0.00 | $0.00 | 0.000 | 0.0% | $0.00 | $0.00 | $0.00 | 0.0% | 0.0% |

## Coverage

- stressed_marketable: eligible=0 priced=0 unpriced=0 coverage=0.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=0 priced=0 unpriced=0 coverage=0.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=0 priced=0 unpriced=0 coverage=0.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

_No priced trades yet._

## stressed_marketable by settlement

_No priced trades yet._

## stressed_marketable by direction

_No priced trades yet._

## stressed_marketable by month

_No priced trades yet._

## stressed_marketable by exit_reason

_No priced trades yet._

## Registered endpoint

- eligible_trades: 0/120 (not met)
- cash_settled_trades: 0/20 (not met)
- stressed_winners: 0/15 (not met)
- Endpoint reached: no

## Decision gates

- stressed_net_pnl_positive: fail
- stressed_expectancy_positive: fail
- stressed_profit_factor_above_one: fail
- marketable_positive_in_both_halves: fail
- executable_entry_coverage: fail
- top3_within_limit: pass
- drawdown_within_limit: pass
- Entry coverage: 0.0%
- Edge classification: **insufficient_data**

Conclusion is provisional until the registered endpoint is reached.
