# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-29T01:37:37.092591+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 18
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 94.7%
- Deferred sessions: 2026-10-28
- Eligible trades: 18
- Cash-settled trades: 5

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 18 | $1,394.40 | $77.47 | 1.498 | 27.8% | $-177.70 | $1,469.00 | $616.53 | 37.8% | 89.0% |
| marketable | 18 | $2,014.40 | $111.91 | 1.876 | 27.8% | $-137.70 | $1,169.00 | $645.13 | 37.1% | 87.9% |
| corrected_midpoint | 18 | $2,495.40 | $138.63 | 2.296 | 33.3% | $-107.70 | $1,012.40 | $680.10 | 36.1% | 86.8% |

## Coverage

- stressed_marketable: eligible=18 priced=18 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=18 priced=18 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=18 priced=18 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 9 | $2,011.00 | $223.44 | 2.674 | 33.3% |
| second_half | 9 | $-616.60 | $-68.51 | 0.614 | 22.2% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 5 | $3,737.00 | $747.40 | 12.407 | 80.0% |
| intraday_exit | 13 | $-2,342.60 | $-180.20 | 0.052 | 7.7% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 10 | $1,429.80 | $142.98 | 2.074 | 30.0% |
| PUT | 8 | $-35.40 | $-4.42 | 0.976 | 25.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 18 | $1,394.40 | $77.47 | 1.498 | 27.8% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 5 | $3,737.00 | $747.40 | 12.407 | 80.0% |
| drawdown_afternoon | 3 | $-70.60 | $-23.53 | 0.648 | 33.3% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 8 | $-1,636.60 | $-204.57 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 18/120 (not met)
- cash_settled_trades: 5/20 (not met)
- stressed_winners: 5/15 (not met)
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
