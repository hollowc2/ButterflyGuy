# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-11T02:36:58.433821+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 27
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 96.4%
- Deferred sessions: 2026-11-10
- Eligible trades: 27
- Cash-settled trades: 6

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 27 | $1,068.20 | $39.56 | 1.205 | 22.2% | $-200.20 | $1,911.20 | $577.82 | 40.3% | 79.1% |
| marketable | 27 | $2,028.20 | $75.12 | 1.461 | 25.9% | $-160.20 | $1,676.00 | $608.18 | 39.2% | 78.2% |
| corrected_midpoint | 27 | $3,501.20 | $129.67 | 2.123 | 33.3% | $-113.20 | $1,012.40 | $658.61 | 37.2% | 76.7% |

## Coverage

- stressed_marketable: eligible=27 priced=27 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=27 priced=27 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=27 priced=27 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 14 | $667.60 | $47.69 | 1.262 | 21.4% |
| second_half | 13 | $400.60 | $30.82 | 1.150 | 23.1% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| intraday_exit | 21 | $-4,759.20 | $-226.63 | 0.027 | 4.8% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 16 | $-16.40 | $-1.02 | 0.994 | 18.8% |
| PUT | 11 | $1,084.60 | $98.60 | 1.445 | 27.3% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 6 | $-1,911.20 | $-318.53 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| drawdown_afternoon | 6 | $-1,241.20 | $-206.87 | 0.095 | 16.7% |
| drawdown_late_morning | 3 | $-1,405.60 | $-468.53 | 0.000 | 0.0% |
| drawdown_morning | 12 | $-2,112.40 | $-176.03 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 27/120 (not met)
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
