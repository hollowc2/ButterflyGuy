# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-06T02:32:28.883911+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 24
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 96.0%
- Deferred sessions: 2026-11-05
- Eligible trades: 24
- Cash-settled trades: 6

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 24 | $2,448.80 | $102.03 | 1.638 | 25.0% | $-192.70 | $1,469.00 | $610.07 | 42.9% | 79.1% |
| marketable | 24 | $3,288.80 | $137.03 | 2.047 | 29.2% | $-152.70 | $1,169.00 | $640.88 | 41.8% | 78.2% |
| corrected_midpoint | 24 | $3,933.80 | $163.91 | 2.481 | 33.3% | $-111.70 | $1,012.40 | $677.76 | 40.5% | 77.1% |

## Coverage

- stressed_marketable: eligible=24 priced=24 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=24 priced=24 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=24 priced=24 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 12 | $1,158.00 | $96.50 | 1.564 | 25.0% |
| second_half | 12 | $1,290.80 | $107.57 | 1.724 | 25.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| intraday_exit | 18 | $-3,378.60 | $-187.70 | 0.037 | 5.6% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 14 | $594.00 | $42.43 | 1.274 | 21.4% |
| PUT | 10 | $1,854.80 | $185.48 | 2.111 | 30.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 3 | $-530.60 | $-176.87 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| drawdown_afternoon | 5 | $-671.00 | $-134.20 | 0.162 | 20.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 11 | $-2,072.20 | $-188.38 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 24/120 (not met)
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
