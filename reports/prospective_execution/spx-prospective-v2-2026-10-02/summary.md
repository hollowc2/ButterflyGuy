# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-22T01:34:31.432338+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 13
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 92.9%
- Deferred sessions: 2026-10-21
- Eligible trades: 13
- Cash-settled trades: 4

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 13 | $867.80 | $66.75 | 1.370 | 23.1% | $-185.20 | $1,143.20 | $476.03 | 51.9% | 100.0% |
| marketable | 13 | $1,307.80 | $100.60 | 1.666 | 23.1% | $-145.20 | $1,003.20 | $503.32 | 50.0% | 100.0% |
| corrected_midpoint | 13 | $1,641.80 | $126.29 | 1.979 | 23.1% | $-110.20 | $877.20 | $535.68 | 47.6% | 100.0% |

## Coverage

- stressed_marketable: eligible=13 priced=13 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=13 priced=13 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=13 priced=13 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 7 | $862.80 | $123.26 | 1.825 | 28.6% |
| second_half | 6 | $5.00 | $0.83 | 1.004 | 16.7% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| intraday_exit | 9 | $-2,016.80 | $-224.09 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 7 | $822.80 | $117.54 | 1.758 | 28.6% |
| PUT | 6 | $45.00 | $7.50 | 1.036 | 16.7% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 13 | $867.80 | $66.75 | 1.370 | 23.1% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| drawdown_afternoon | 1 | $-155.20 | $-155.20 | 0.000 | 0.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 6 | $-1,226.20 | $-204.37 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 13/120 (not met)
- cash_settled_trades: 4/20 (not met)
- stressed_winners: 3/15 (not met)
- Endpoint reached: no

## Decision gates

- session_data_complete: fail
- stressed_net_pnl_positive: pass
- stressed_expectancy_positive: pass
- stressed_profit_factor_above_one: pass
- marketable_positive_in_both_halves: pass
- executable_entry_coverage: pass
- top3_within_limit: fail
- drawdown_within_limit: pass
- Entry coverage: 100.0%
- Edge classification: **no_executable_edge**

Conclusion is provisional until the registered endpoint is reached.
