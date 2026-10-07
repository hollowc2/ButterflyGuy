# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-07T01:36:52.066285+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 2
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 66.7%
- Deferred sessions: 2026-10-06
- Eligible trades: 2
- Cash-settled trades: 1

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 2 | $1,392.20 | $696.10 | 8.517 | 50.0% | $696.10 | $185.20 | $1,132.30 | 69.7% | 100.0% |
| marketable | 2 | $1,452.20 | $726.10 | 11.001 | 50.0% | $726.10 | $145.20 | $1,172.30 | 68.1% | 100.0% |
| corrected_midpoint | 2 | $1,509.20 | $754.60 | 14.695 | 50.0% | $754.60 | $110.20 | $1,218.40 | 66.5% | 100.0% |

## Coverage

- stressed_marketable: eligible=2 priced=2 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=2 priced=2 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=2 priced=2 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 1 | $-185.20 | $-185.20 | 0.000 | 0.0% |
| second_half | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |
| intraday_exit | 1 | $-185.20 | $-185.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 2 | $1,392.20 | $696.10 | 8.517 | 50.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 2 | $1,392.20 | $696.10 | 8.517 | 50.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |
| drawdown_morning | 1 | $-185.20 | $-185.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 2/120 (not met)
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
