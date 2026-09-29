# Prospective execution validation — spx-prospective-2026-09-22

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-09-22
- Generated: 2026-09-29T01:36:31.142247+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 4
- No signal: 0
- Incomplete data: 0
- Eligible trades: 4
- Cash-settled trades: 1

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 4 | $503.80 | $125.95 | 1.763 | 25.0% | $-195.20 | $435.40 | $561.10 | 51.9% | 100.0% |
| marketable | 4 | $643.80 | $160.95 | 2.191 | 25.0% | $-155.20 | $355.40 | $601.05 | 49.3% | 100.0% |
| corrected_midpoint | 4 | $730.80 | $182.70 | 2.570 | 25.0% | $-130.20 | $307.40 | $636.15 | 47.0% | 100.0% |

## Coverage

- stressed_marketable: eligible=4 priced=4 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=4 priced=4 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=4 priced=4 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 2 | $939.20 | $469.60 | 5.171 | 50.0% |
| second_half | 2 | $-435.40 | $-217.70 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |
| intraday_exit | 3 | $-660.60 | $-220.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 2 | $-390.40 | $-195.20 | 0.000 | 0.0% |
| PUT | 2 | $894.20 | $447.10 | 4.309 | 50.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09 | 4 | $503.80 | $125.95 | 1.763 | 25.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |
| drawdown_afternoon | 1 | $-165.20 | $-165.20 | 0.000 | 0.0% |
| drawdown_late_morning | 1 | $-270.20 | $-270.20 | 0.000 | 0.0% |
| drawdown_morning | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 4/120 (not met)
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
