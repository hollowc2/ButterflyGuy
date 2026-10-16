# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-16T01:33:45.355054+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 9
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 90.0%
- Deferred sessions: 2026-10-15
- Eligible trades: 9
- Cash-settled trades: 3

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 9 | $2,011.00 | $223.44 | 2.674 | 33.3% | $-160.20 | $684.60 | $618.73 | 57.7% | 100.0% |
| marketable | 9 | $2,311.00 | $256.78 | 3.404 | 33.3% | $-120.20 | $525.60 | $649.84 | 56.0% | 100.0% |
| corrected_midpoint | 9 | $2,519.00 | $279.89 | 4.152 | 33.3% | $-98.20 | $454.60 | $685.18 | 53.8% | 100.0% |

## Coverage

- stressed_marketable: eligible=9 priced=9 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=9 priced=9 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=9 priced=9 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 5 | $746.60 | $149.32 | 1.899 | 20.0% |
| second_half | 4 | $1,264.40 | $316.10 | 4.414 | 50.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 3 | $3,212.20 | $1,070.73 | 999.000 | 100.0% |
| intraday_exit | 6 | $-1,201.20 | $-200.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 5 | $1,348.20 | $269.64 | 3.405 | 40.0% |
| PUT | 4 | $662.80 | $165.70 | 2.035 | 25.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 9 | $2,011.00 | $223.44 | 2.674 | 33.3% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 3 | $3,212.20 | $1,070.73 | 999.000 | 100.0% |
| drawdown_afternoon | 1 | $-155.20 | $-155.20 | 0.000 | 0.0% |
| drawdown_late_morning | 1 | $-280.20 | $-280.20 | 0.000 | 0.0% |
| drawdown_morning | 4 | $-765.80 | $-191.45 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 9/120 (not met)
- cash_settled_trades: 3/20 (not met)
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
