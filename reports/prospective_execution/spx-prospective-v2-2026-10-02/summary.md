# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-24T01:36:59.195509+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 15
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 93.8%
- Deferred sessions: 2026-10-23
- Eligible trades: 15
- Cash-settled trades: 4

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 15 | $797.40 | $53.16 | 1.313 | 26.7% | $-185.20 | $1,343.40 | $535.21 | 41.6% | 96.1% |
| marketable | 15 | $1,317.40 | $87.83 | 1.620 | 26.7% | $-145.20 | $1,163.40 | $561.53 | 40.9% | 95.1% |
| corrected_midpoint | 15 | $1,705.40 | $113.69 | 1.941 | 26.7% | $-110.20 | $1,012.40 | $593.17 | 39.5% | 94.3% |

## Coverage

- stressed_marketable: eligible=15 priced=15 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=15 priced=15 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=15 priced=15 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 8 | $707.60 | $88.45 | 1.589 | 25.0% |
| second_half | 7 | $89.80 | $12.83 | 1.067 | 28.6% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| intraday_exit | 11 | $-2,087.20 | $-189.75 | 0.059 | 9.1% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 8 | $622.60 | $77.83 | 1.484 | 25.0% |
| PUT | 7 | $174.80 | $24.97 | 1.139 | 28.6% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 15 | $797.40 | $53.16 | 1.313 | 26.7% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| drawdown_afternoon | 2 | $-25.40 | $-12.70 | 0.836 | 50.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 7 | $-1,426.40 | $-203.77 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 15/120 (not met)
- cash_settled_trades: 4/20 (not met)
- stressed_winners: 4/15 (not met)
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
