# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-30T01:34:53.395852+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 19
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 95.0%
- Deferred sessions: 2026-10-29
- Eligible trades: 19
- Cash-settled trades: 5

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 19 | $1,089.20 | $57.33 | 1.351 | 26.3% | $-185.20 | $1,469.00 | $596.18 | 37.0% | 89.0% |
| marketable | 19 | $1,749.20 | $92.06 | 1.682 | 26.3% | $-145.20 | $1,169.00 | $625.38 | 36.3% | 87.9% |
| corrected_midpoint | 19 | $2,257.20 | $118.80 | 2.044 | 31.6% | $-110.20 | $1,012.40 | $660.75 | 35.2% | 86.8% |

## Coverage

- stressed_marketable: eligible=19 priced=19 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=19 priced=19 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=19 priced=19 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 10 | $1,683.40 | $168.34 | 2.101 | 30.0% |
| second_half | 9 | $-594.20 | $-66.02 | 0.623 | 22.2% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 5 | $3,737.00 | $747.40 | 12.407 | 80.0% |
| intraday_exit | 14 | $-2,647.80 | $-189.13 | 0.047 | 7.1% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 11 | $1,124.60 | $102.24 | 1.687 | 27.3% |
| PUT | 8 | $-35.40 | $-4.42 | 0.976 | 25.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 19 | $1,089.20 | $57.33 | 1.351 | 26.3% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 5 | $3,737.00 | $747.40 | 12.407 | 80.0% |
| drawdown_afternoon | 4 | $-375.80 | $-93.95 | 0.257 | 25.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 8 | $-1,636.60 | $-204.57 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 19/120 (not met)
- cash_settled_trades: 5/20 (not met)
- stressed_winners: 5/15 (not met)
- Endpoint reached: no

## Decision gates

- session_data_complete: fail
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
