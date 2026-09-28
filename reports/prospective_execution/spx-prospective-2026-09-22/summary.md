# Prospective execution validation — spx-prospective-2026-09-22

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-09-22
- Generated: 2026-09-28T00:26:16.366305+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 3
- No signal: 0
- Incomplete data: 0
- Eligible trades: 3
- Cash-settled trades: 1

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 3 | $669.00 | $223.00 | 2.350 | 33.3% | $-225.20 | $270.20 | $626.53 | 62.0% | 100.0% |
| marketable | 3 | $769.00 | $256.33 | 2.851 | 33.3% | $-185.20 | $230.20 | $666.47 | 59.2% | 100.0% |
| corrected_midpoint | 3 | $833.00 | $277.67 | 3.292 | 33.3% | $-158.20 | $205.20 | $703.40 | 56.7% | 100.0% |

## Coverage

- stressed_marketable: eligible=3 priced=3 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=3 priced=3 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=3 priced=3 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 2 | $939.20 | $469.60 | 5.171 | 50.0% |
| second_half | 1 | $-270.20 | $-270.20 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |
| intraday_exit | 2 | $-495.40 | $-247.70 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |
| PUT | 2 | $894.20 | $447.10 | 4.309 | 50.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09 | 3 | $669.00 | $223.00 | 2.350 | 33.3% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |
| drawdown_late_morning | 1 | $-270.20 | $-270.20 | 0.000 | 0.0% |
| drawdown_morning | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 3/120 (not met)
- cash_settled_trades: 1/20 (not met)
- stressed_winners: 1/15 (not met)
- Endpoint reached: no

## Decision gates

- stressed_net_pnl_positive: pass
- stressed_expectancy_positive: pass
- stressed_profit_factor_above_one: pass
- marketable_positive_in_both_halves: fail
- executable_entry_coverage: pass
- top3_within_limit: fail
- drawdown_within_limit: pass
- Entry coverage: 100.0%
- Edge classification: **no_executable_edge**

Conclusion is provisional until the registered endpoint is reached.
