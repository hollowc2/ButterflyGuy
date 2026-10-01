# Prospective execution validation — spx-prospective-2026-09-22

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-09-22
- Generated: 2026-10-01T01:36:38.836277+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 6
- No signal: 0
- Incomplete data: 0
- Eligible trades: 6
- Cash-settled trades: 2

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 6 | $86.00 | $14.33 | 1.080 | 16.7% | $-195.20 | $853.20 | $457.37 | 42.4% | 100.0% |
| marketable | 6 | $286.00 | $47.67 | 1.318 | 16.7% | $-155.20 | $713.20 | $490.67 | 40.2% | 100.0% |
| corrected_midpoint | 6 | $421.00 | $70.17 | 1.543 | 16.7% | $-130.20 | $617.20 | $521.17 | 38.3% | 100.0% |

## Coverage

- stressed_marketable: eligible=6 priced=6 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=6 priced=6 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=6 priced=6 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 3 | $669.00 | $223.00 | 2.350 | 33.3% |
| second_half | 3 | $-583.00 | $-194.33 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $846.80 | $423.40 | 3.666 | 50.0% |
| intraday_exit | 4 | $-760.80 | $-190.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 3 | $-708.00 | $-236.00 | 0.000 | 0.0% |
| PUT | 3 | $794.00 | $264.67 | 3.144 | 33.3% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09 | 6 | $86.00 | $14.33 | 1.080 | 16.7% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $846.80 | $423.40 | 3.666 | 50.0% |
| drawdown_afternoon | 2 | $-265.40 | $-132.70 | 0.000 | 0.0% |
| drawdown_late_morning | 1 | $-270.20 | $-270.20 | 0.000 | 0.0% |
| drawdown_morning | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 6/120 (not met)
- cash_settled_trades: 2/20 (not met)
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
