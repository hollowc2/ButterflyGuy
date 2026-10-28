# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-28T01:34:01.441159+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 17
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 94.4%
- Deferred sessions: 2026-10-27
- Eligible trades: 17
- Cash-settled trades: 4

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 17 | $542.00 | $31.88 | 1.194 | 23.5% | $-185.20 | $1,469.00 | $531.05 | 37.0% | 96.1% |
| marketable | 17 | $1,142.00 | $67.18 | 1.497 | 23.5% | $-145.20 | $1,169.00 | $558.98 | 36.2% | 95.1% |
| corrected_midpoint | 17 | $1,612.00 | $94.82 | 1.837 | 29.4% | $-110.20 | $1,012.40 | $593.32 | 35.1% | 93.8% |

## Coverage

- stressed_marketable: eligible=17 priced=17 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=17 priced=17 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=17 priced=17 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 9 | $2,011.00 | $223.44 | 2.674 | 33.3% |
| second_half | 8 | $-1,469.00 | $-183.62 | 0.081 | 12.5% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| intraday_exit | 13 | $-2,342.60 | $-180.20 | 0.052 | 7.7% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 9 | $577.40 | $64.16 | 1.434 | 22.2% |
| PUT | 8 | $-35.40 | $-4.42 | 0.976 | 25.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 17 | $542.00 | $31.88 | 1.194 | 23.5% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| drawdown_afternoon | 3 | $-70.60 | $-23.53 | 0.648 | 33.3% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 8 | $-1,636.60 | $-204.57 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 17/120 (not met)
- cash_settled_trades: 4/20 (not met)
- stressed_winners: 4/15 (not met)
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
