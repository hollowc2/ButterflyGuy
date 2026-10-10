# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-10T01:35:46.077182+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 5
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 83.3%
- Deferred sessions: 2026-10-09
- Eligible trades: 5
- Cash-settled trades: 1

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 5 | $746.60 | $149.32 | 1.899 | 20.0% | $-185.20 | $645.60 | $469.84 | 67.2% | 100.0% |
| marketable | 5 | $926.60 | $185.32 | 2.381 | 20.0% | $-145.20 | $525.60 | $501.84 | 63.7% | 100.0% |
| corrected_midpoint | 5 | $1,054.60 | $210.92 | 2.867 | 20.0% | $-110.20 | $454.60 | $532.80 | 60.8% | 100.0% |

## Coverage

- stressed_marketable: eligible=5 priced=5 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=5 priced=5 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=5 priced=5 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 3 | $1,232.00 | $410.67 | 4.567 | 33.3% |
| second_half | 2 | $-485.40 | $-242.70 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |
| intraday_exit | 4 | $-830.80 | $-207.70 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 3 | $1,232.00 | $410.67 | 4.567 | 33.3% |
| PUT | 2 | $-485.40 | $-242.70 | 0.000 | 0.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 5 | $746.60 | $149.32 | 1.899 | 20.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |
| drawdown_late_morning | 1 | $-280.20 | $-280.20 | 0.000 | 0.0% |
| drawdown_morning | 3 | $-550.60 | $-183.53 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 5/120 (not met)
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
