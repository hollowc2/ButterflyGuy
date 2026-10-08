# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-08T01:37:46.618120+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 3
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 75.0%
- Deferred sessions: 2026-10-07
- Eligible trades: 3
- Cash-settled trades: 1

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 3 | $1,232.00 | $410.67 | 4.567 | 33.3% | $-160.20 | $185.20 | $763.13 | 68.9% | 100.0% |
| marketable | 3 | $1,332.00 | $444.00 | 6.019 | 33.3% | $-120.20 | $145.20 | $803.13 | 66.3% | 100.0% |
| corrected_midpoint | 3 | $1,411.00 | $470.33 | 7.771 | 33.3% | $-98.20 | $110.20 | $843.07 | 64.0% | 100.0% |

## Coverage

- stressed_marketable: eligible=3 priced=3 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=3 priced=3 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=3 priced=3 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 2 | $1,392.20 | $696.10 | 8.517 | 50.0% |
| second_half | 1 | $-160.20 | $-160.20 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |
| intraday_exit | 2 | $-345.40 | $-172.70 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 3 | $1,232.00 | $410.67 | 4.567 | 33.3% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 3 | $1,232.00 | $410.67 | 4.567 | 33.3% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |
| drawdown_morning | 2 | $-345.40 | $-172.70 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 3/120 (not met)
- cash_settled_trades: 1/20 (not met)
- stressed_winners: 1/15 (not met)
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
