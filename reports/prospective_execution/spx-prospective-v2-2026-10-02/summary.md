# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-15T01:33:11.491710+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 8
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 88.9%
- Deferred sessions: 2026-10-14
- Eligible trades: 8
- Cash-settled trades: 2

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 8 | $707.60 | $88.45 | 1.589 | 25.0% | $-172.70 | $684.60 | $492.35 | 48.5% | 100.0% |
| marketable | 8 | $987.60 | $123.45 | 2.027 | 25.0% | $-132.70 | $525.60 | $522.35 | 46.6% | 100.0% |
| corrected_midpoint | 8 | $1,184.60 | $148.07 | 2.482 | 25.0% | $-104.20 | $454.60 | $552.02 | 44.9% | 100.0% |

## Coverage

- stressed_marketable: eligible=8 priced=8 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=8 priced=8 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=8 priced=8 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 4 | $951.80 | $237.95 | 2.521 | 25.0% |
| second_half | 4 | $-244.20 | $-61.05 | 0.576 | 25.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $1,908.80 | $954.40 | 999.000 | 100.0% |
| intraday_exit | 6 | $-1,201.20 | $-200.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 5 | $1,348.20 | $269.64 | 3.405 | 40.0% |
| PUT | 3 | $-640.60 | $-213.53 | 0.000 | 0.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 8 | $707.60 | $88.45 | 1.589 | 25.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $1,908.80 | $954.40 | 999.000 | 100.0% |
| drawdown_afternoon | 1 | $-155.20 | $-155.20 | 0.000 | 0.0% |
| drawdown_late_morning | 1 | $-280.20 | $-280.20 | 0.000 | 0.0% |
| drawdown_morning | 4 | $-765.80 | $-191.45 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 8/120 (not met)
- cash_settled_trades: 2/20 (not met)
- stressed_winners: 2/15 (not met)
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
