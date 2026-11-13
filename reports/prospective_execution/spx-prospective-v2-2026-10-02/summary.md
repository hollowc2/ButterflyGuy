# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-13T02:34:56.289142+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 29
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 96.7%
- Deferred sessions: 2026-11-12
- Eligible trades: 29
- Cash-settled trades: 6

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 29 | $742.80 | $25.61 | 1.134 | 20.7% | $-200.20 | $2,236.60 | $570.03 | 38.0% | 79.1% |
| marketable | 29 | $1,782.80 | $61.48 | 1.384 | 24.1% | $-160.20 | $1,921.40 | $599.68 | 37.0% | 78.2% |
| corrected_midpoint | 29 | $3,311.80 | $114.20 | 2.001 | 31.0% | $-113.20 | $1,012.40 | $649.42 | 35.1% | 76.7% |

## Coverage

- stressed_marketable: eligible=29 priced=29 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=29 priced=29 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=29 priced=29 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 15 | $797.40 | $53.16 | 1.313 | 26.7% |
| second_half | 14 | $-54.60 | $-3.90 | 0.982 | 14.3% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| intraday_exit | 23 | $-5,084.60 | $-221.07 | 0.025 | 4.3% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 17 | $-231.60 | $-13.62 | 0.923 | 17.6% |
| PUT | 12 | $974.40 | $81.20 | 1.382 | 25.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 8 | $-2,236.60 | $-279.57 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| drawdown_afternoon | 7 | $-1,351.40 | $-193.06 | 0.088 | 14.3% |
| drawdown_late_morning | 3 | $-1,405.60 | $-468.53 | 0.000 | 0.0% |
| drawdown_morning | 13 | $-2,327.60 | $-179.05 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 29/120 (not met)
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
