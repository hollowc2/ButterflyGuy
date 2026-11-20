# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-20T02:32:36.990419+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 34
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 97.1%
- Deferred sessions: 2026-11-19
- Eligible trades: 34
- Cash-settled trades: 7

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 34 | $-630.60 | $-18.55 | 0.909 | 17.6% | $-200.20 | $3,610.00 | $496.19 | 37.2% | 79.1% |
| marketable | 34 | $589.40 | $17.34 | 1.101 | 20.6% | $-160.20 | $3,114.80 | $525.00 | 36.0% | 78.2% |
| corrected_midpoint | 34 | $2,394.40 | $70.42 | 1.567 | 26.5% | $-126.20 | $1,896.80 | $573.02 | 34.0% | 76.7% |

## Coverage

- stressed_marketable: eligible=34 priced=34 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=34 priced=34 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=34 priced=34 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 17 | $542.00 | $31.88 | 1.194 | 23.5% |
| second_half | 17 | $-1,172.60 | $-68.98 | 0.715 | 11.8% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| intraday_exit | 27 | $-6,085.40 | $-225.39 | 0.021 | 3.7% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 19 | $-904.40 | $-47.60 | 0.753 | 15.8% |
| PUT | 15 | $273.80 | $18.25 | 1.084 | 20.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 13 | $-3,610.00 | $-277.69 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| drawdown_afternoon | 7 | $-1,351.40 | $-193.06 | 0.088 | 14.3% |
| drawdown_late_morning | 3 | $-1,405.60 | $-468.53 | 0.000 | 0.0% |
| drawdown_morning | 17 | $-3,328.40 | $-195.79 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 34/120 (not met)
- cash_settled_trades: 7/20 (not met)
- stressed_winners: 6/15 (not met)
- Endpoint reached: no

## Decision gates

- session_data_complete: fail
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
