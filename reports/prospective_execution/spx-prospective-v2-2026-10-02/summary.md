# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-26T02:37:35.574477+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 38
- No signal: 1
- Incomplete data: 1
- Session completion coverage: 97.4%
- Deferred sessions: 2026-11-25
- Eligible trades: 37
- Cash-settled trades: 7

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 37 | $-2,981.20 | $-80.57 | 0.678 | 16.2% | $-205.20 | $5,960.60 | $473.92 | 35.8% | 79.1% |
| marketable | 37 | $-1,641.20 | $-44.36 | 0.797 | 18.9% | $-165.20 | $5,345.40 | $502.15 | 34.6% | 78.2% |
| corrected_midpoint | 37 | $1,569.80 | $42.43 | 1.311 | 24.3% | $-135.20 | $2,721.40 | $559.95 | 31.9% | 76.7% |

## Coverage

- stressed_marketable: eligible=37 priced=37 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=37 priced=37 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=37 priced=37 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 19 | $1,089.20 | $57.33 | 1.351 | 26.3% |
| second_half | 18 | $-4,070.40 | $-226.13 | 0.339 | 5.6% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| intraday_exit | 30 | $-8,436.00 | $-281.20 | 0.015 | 3.3% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 20 | $-1,214.60 | $-60.73 | 0.695 | 15.0% |
| PUT | 17 | $-1,766.60 | $-103.92 | 0.666 | 17.6% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 16 | $-5,960.60 | $-372.54 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| drawdown_afternoon | 8 | $-1,696.60 | $-212.07 | 0.071 | 12.5% |
| drawdown_late_morning | 4 | $-3,100.80 | $-775.20 | 0.000 | 0.0% |
| drawdown_morning | 18 | $-3,638.60 | $-202.14 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 37/120 (not met)
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
