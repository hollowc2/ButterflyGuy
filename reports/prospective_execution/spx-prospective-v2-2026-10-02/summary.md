# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-04T02:33:15.524523+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 22
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 95.7%
- Deferred sessions: 2026-11-03
- Eligible trades: 22
- Cash-settled trades: 6

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 22 | $2,944.20 | $133.83 | 1.881 | 27.3% | $-177.70 | $1,469.00 | $656.00 | 43.5% | 79.1% |
| marketable | 22 | $3,704.20 | $168.37 | 2.359 | 31.8% | $-137.70 | $1,169.00 | $685.98 | 42.6% | 78.2% |
| corrected_midpoint | 22 | $4,291.20 | $195.05 | 2.867 | 36.4% | $-107.70 | $1,012.40 | $723.11 | 41.4% | 77.1% |

## Coverage

- stressed_marketable: eligible=22 priced=22 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=22 priced=22 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=22 priced=22 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 11 | $1,513.20 | $137.56 | 1.891 | 27.3% |
| second_half | 11 | $1,431.00 | $130.09 | 1.872 | 27.3% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| intraday_exit | 16 | $-2,883.20 | $-180.20 | 0.043 | 6.2% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 12 | $1,089.40 | $90.78 | 1.652 | 25.0% |
| PUT | 10 | $1,854.80 | $185.48 | 2.111 | 30.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 1 | $-35.20 | $-35.20 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| drawdown_afternoon | 4 | $-375.80 | $-93.95 | 0.257 | 25.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 10 | $-1,872.00 | $-187.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 22/120 (not met)
- cash_settled_trades: 6/20 (not met)
- stressed_winners: 6/15 (not met)
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
