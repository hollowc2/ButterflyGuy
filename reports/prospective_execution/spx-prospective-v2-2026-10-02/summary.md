# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-03T02:37:22.526684+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 21
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 95.5%
- Deferred sessions: 2026-11-02
- Eligible trades: 21
- Cash-settled trades: 6

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% | $-185.20 | $1,469.00 | $663.44 | 45.1% | 79.1% |
| marketable | 21 | $3,699.40 | $176.16 | 2.357 | 28.6% | $-145.20 | $1,169.00 | $692.94 | 44.1% | 78.3% |
| corrected_midpoint | 21 | $4,246.40 | $202.21 | 2.848 | 33.3% | $-110.20 | $1,012.40 | $729.33 | 42.7% | 77.6% |

## Coverage

- stressed_marketable: eligible=21 priced=21 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=21 priced=21 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=21 priced=21 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 11 | $1,513.20 | $137.56 | 1.891 | 27.3% |
| second_half | 10 | $1,466.20 | $146.62 | 1.913 | 30.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| intraday_exit | 15 | $-2,848.00 | $-189.87 | 0.044 | 6.7% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 11 | $1,124.60 | $102.24 | 1.687 | 27.3% |
| PUT | 10 | $1,854.80 | $185.48 | 2.111 | 30.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| drawdown_afternoon | 4 | $-375.80 | $-93.95 | 0.257 | 25.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 9 | $-1,836.80 | $-204.09 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 21/120 (not met)
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
