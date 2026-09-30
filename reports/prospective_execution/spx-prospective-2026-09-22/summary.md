# Prospective execution validation — spx-prospective-2026-09-22

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-09-22
- Generated: 2026-09-30T01:34:34.147332+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 5
- No signal: 0
- Incomplete data: 0
- Eligible trades: 5
- Cash-settled trades: 1

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 5 | $403.60 | $80.72 | 1.530 | 20.0% | $-165.20 | $535.60 | $548.84 | 42.4% | 100.0% |
| marketable | 5 | $583.60 | $116.72 | 1.971 | 20.0% | $-125.20 | $415.60 | $588.80 | 40.2% | 100.0% |
| corrected_midpoint | 5 | $699.60 | $139.92 | 2.408 | 20.0% | $-102.20 | $338.60 | $625.40 | 38.3% | 100.0% |

## Coverage

- stressed_marketable: eligible=5 priced=5 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=5 priced=5 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=5 priced=5 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 3 | $669.00 | $223.00 | 2.350 | 33.3% |
| second_half | 2 | $-265.40 | $-132.70 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |
| intraday_exit | 4 | $-760.80 | $-190.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 2 | $-390.40 | $-195.20 | 0.000 | 0.0% |
| PUT | 3 | $794.00 | $264.67 | 3.144 | 33.3% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09 | 5 | $403.60 | $80.72 | 1.530 | 20.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |
| drawdown_afternoon | 2 | $-265.40 | $-132.70 | 0.000 | 0.0% |
| drawdown_late_morning | 1 | $-270.20 | $-270.20 | 0.000 | 0.0% |
| drawdown_morning | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 5/120 (not met)
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
