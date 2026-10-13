# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-13T01:35:19.830548+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 6
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 85.7%
- Deferred sessions: 2026-10-12
- Eligible trades: 6
- Cash-settled trades: 2

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 6 | $1,078.00 | $179.67 | 2.298 | 33.3% | $-172.70 | $645.60 | $576.50 | 55.2% | 100.0% |
| marketable | 6 | $1,278.00 | $213.00 | 2.905 | 33.3% | $-132.70 | $525.60 | $609.83 | 53.3% | 100.0% |
| corrected_midpoint | 6 | $1,419.00 | $236.50 | 3.512 | 33.3% | $-104.20 | $454.60 | $641.90 | 51.5% | 100.0% |

## Coverage

- stressed_marketable: eligible=6 priced=6 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=6 priced=6 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=6 priced=6 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 3 | $1,232.00 | $410.67 | 4.567 | 33.3% |
| second_half | 3 | $-154.00 | $-51.33 | 0.683 | 33.3% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $1,908.80 | $954.40 | 999.000 | 100.0% |
| intraday_exit | 4 | $-830.80 | $-207.70 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 4 | $1,563.40 | $390.85 | 5.526 | 50.0% |
| PUT | 2 | $-485.40 | $-242.70 | 0.000 | 0.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 6 | $1,078.00 | $179.67 | 2.298 | 33.3% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $1,908.80 | $954.40 | 999.000 | 100.0% |
| drawdown_late_morning | 1 | $-280.20 | $-280.20 | 0.000 | 0.0% |
| drawdown_morning | 3 | $-550.60 | $-183.53 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 6/120 (not met)
- cash_settled_trades: 2/20 (not met)
- stressed_winners: 2/15 (not met)
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
