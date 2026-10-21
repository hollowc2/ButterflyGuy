# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-21T01:32:24.678540+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 12
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 92.3%
- Deferred sessions: 2026-10-20
- Eligible trades: 12
- Cash-settled trades: 4

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 12 | $1,158.00 | $96.50 | 1.564 | 25.0% | $-177.70 | $853.00 | $515.70 | 51.9% | 100.0% |
| marketable | 12 | $1,558.00 | $129.83 | 1.909 | 25.0% | $-137.70 | $753.00 | $545.27 | 50.0% | 100.0% |
| corrected_midpoint | 12 | $1,863.00 | $155.25 | 2.280 | 25.0% | $-107.70 | $656.00 | $579.62 | 47.7% | 100.0% |

## Coverage

- stressed_marketable: eligible=12 priced=12 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=12 priced=12 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=12 priced=12 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 6 | $1,078.00 | $179.67 | 2.298 | 33.3% |
| second_half | 6 | $80.00 | $13.33 | 1.065 | 16.7% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| intraday_exit | 8 | $-1,726.60 | $-215.82 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 7 | $822.80 | $117.54 | 1.758 | 28.6% |
| PUT | 5 | $335.20 | $67.04 | 1.346 | 20.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 12 | $1,158.00 | $96.50 | 1.564 | 25.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| drawdown_afternoon | 1 | $-155.20 | $-155.20 | 0.000 | 0.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 5 | $-936.00 | $-187.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 12/120 (not met)
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
