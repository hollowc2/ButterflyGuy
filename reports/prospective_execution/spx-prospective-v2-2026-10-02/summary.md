# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-20T01:36:34.909911+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 11
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 91.7%
- Deferred sessions: 2026-10-19
- Eligible trades: 11
- Cash-settled trades: 4

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 11 | $1,513.20 | $137.56 | 1.891 | 27.3% | $-170.20 | $684.60 | $506.24 | 57.7% | 100.0% |
| marketable | 11 | $1,873.20 | $170.29 | 2.339 | 27.3% | $-130.20 | $525.60 | $534.85 | 55.6% | 100.0% |
| corrected_midpoint | 11 | $2,123.20 | $193.02 | 2.777 | 27.3% | $-105.20 | $454.60 | $567.09 | 53.2% | 100.0% |

## Coverage

- stressed_marketable: eligible=11 priced=11 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=11 priced=11 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=11 priced=11 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 6 | $1,078.00 | $179.67 | 2.298 | 33.3% |
| second_half | 5 | $435.20 | $87.04 | 1.501 | 20.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| intraday_exit | 7 | $-1,371.40 | $-195.91 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 6 | $1,178.00 | $196.33 | 2.612 | 33.3% |
| PUT | 5 | $335.20 | $67.04 | 1.346 | 20.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 11 | $1,513.20 | $137.56 | 1.891 | 27.3% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| drawdown_afternoon | 1 | $-155.20 | $-155.20 | 0.000 | 0.0% |
| drawdown_late_morning | 1 | $-280.20 | $-280.20 | 0.000 | 0.0% |
| drawdown_morning | 5 | $-936.00 | $-187.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 11/120 (not met)
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
