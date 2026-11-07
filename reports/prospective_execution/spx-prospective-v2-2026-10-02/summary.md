# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-07T02:32:39.743157+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 25
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 96.2%
- Deferred sessions: 2026-11-06
- Eligible trades: 25
- Cash-settled trades: 6

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 25 | $1,678.60 | $67.14 | 1.364 | 24.0% | $-200.20 | $1,469.00 | $600.86 | 41.8% | 79.1% |
| marketable | 25 | $2,558.60 | $102.34 | 1.661 | 28.0% | $-160.20 | $1,169.00 | $632.04 | 40.7% | 78.2% |
| corrected_midpoint | 25 | $3,635.60 | $145.42 | 2.231 | 32.0% | $-113.20 | $1,012.40 | $675.82 | 39.0% | 77.1% |

## Coverage

- stressed_marketable: eligible=25 priced=25 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=25 priced=25 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=25 priced=25 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 13 | $867.80 | $66.75 | 1.370 | 23.1% |
| second_half | 12 | $810.80 | $67.57 | 1.358 | 25.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| intraday_exit | 19 | $-4,148.80 | $-218.36 | 0.030 | 5.3% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 14 | $594.00 | $42.43 | 1.274 | 21.4% |
| PUT | 11 | $1,084.60 | $98.60 | 1.445 | 27.3% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 4 | $-1,300.80 | $-325.20 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| drawdown_afternoon | 5 | $-671.00 | $-134.20 | 0.162 | 20.0% |
| drawdown_late_morning | 3 | $-1,405.60 | $-468.53 | 0.000 | 0.0% |
| drawdown_morning | 11 | $-2,072.20 | $-188.38 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 25/120 (not met)
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
