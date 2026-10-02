# Prospective execution validation — spx-prospective-2026-09-22

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-09-22
- Generated: 2026-10-02T01:35:46.986939+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 7
- No signal: 0
- Incomplete data: 0
- Eligible trades: 7
- Cash-settled trades: 2

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 7 | $-174.20 | $-24.89 | 0.870 | 14.3% | $-225.20 | $1,113.40 | $399.14 | 41.7% | 100.0% |
| marketable | 7 | $65.80 | $9.40 | 1.059 | 14.3% | $-185.20 | $933.40 | $433.40 | 39.0% | 100.0% |
| corrected_midpoint | 7 | $223.80 | $31.97 | 1.230 | 14.3% | $-158.20 | $814.40 | $463.77 | 36.9% | 100.0% |

## Coverage

- stressed_marketable: eligible=7 priced=7 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=7 priced=7 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=7 priced=7 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 4 | $503.80 | $125.95 | 1.763 | 25.0% |
| second_half | 3 | $-678.00 | $-226.00 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $846.80 | $423.40 | 3.666 | 50.0% |
| intraday_exit | 5 | $-1,021.00 | $-204.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 4 | $-968.20 | $-242.05 | 0.000 | 0.0% |
| PUT | 3 | $794.00 | $264.67 | 3.144 | 33.3% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09 | 7 | $-174.20 | $-24.89 | 0.870 | 14.3% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $846.80 | $423.40 | 3.666 | 50.0% |
| drawdown_afternoon | 2 | $-265.40 | $-132.70 | 0.000 | 0.0% |
| drawdown_late_morning | 2 | $-530.40 | $-265.20 | 0.000 | 0.0% |
| drawdown_morning | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 7/120 (not met)
- cash_settled_trades: 2/20 (not met)
- stressed_winners: 1/15 (not met)
- Endpoint reached: no

## Decision gates

- stressed_net_pnl_positive: fail
- stressed_expectancy_positive: fail
- stressed_profit_factor_above_one: fail
- marketable_positive_in_both_halves: fail
- executable_entry_coverage: pass
- top3_within_limit: fail
- drawdown_within_limit: pass
- Entry coverage: 100.0%
- Edge classification: **no_executable_edge**

Conclusion is provisional until the registered endpoint is reached.
