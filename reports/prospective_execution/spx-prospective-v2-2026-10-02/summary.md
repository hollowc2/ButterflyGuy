# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-27T01:34:53.356485+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 16
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 94.1%
- Deferred sessions: 2026-10-26
- Eligible trades: 16
- Cash-settled trades: 4

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 16 | $587.20 | $36.70 | 1.213 | 25.0% | $-192.70 | $1,423.80 | $512.69 | 40.7% | 96.1% |
| marketable | 16 | $1,147.20 | $71.70 | 1.500 | 25.0% | $-152.70 | $1,163.80 | $539.86 | 39.9% | 95.1% |
| corrected_midpoint | 16 | $1,592.20 | $99.51 | 1.827 | 25.0% | $-111.70 | $1,012.40 | $573.94 | 38.3% | 94.3% |

## Coverage

- stressed_marketable: eligible=16 priced=16 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=16 priced=16 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=16 priced=16 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 8 | $707.60 | $88.45 | 1.589 | 25.0% |
| second_half | 8 | $-120.40 | $-15.05 | 0.923 | 25.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| intraday_exit | 12 | $-2,297.40 | $-191.45 | 0.053 | 8.3% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 8 | $622.60 | $77.83 | 1.484 | 25.0% |
| PUT | 8 | $-35.40 | $-4.42 | 0.976 | 25.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 16 | $587.20 | $36.70 | 1.213 | 25.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| drawdown_afternoon | 2 | $-25.40 | $-12.70 | 0.836 | 50.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 8 | $-1,636.60 | $-204.57 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 16/120 (not met)
- cash_settled_trades: 4/20 (not met)
- stressed_winners: 4/15 (not met)
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
