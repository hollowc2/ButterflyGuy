# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-14T01:37:13.305530+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 7
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 87.5%
- Deferred sessions: 2026-10-13
- Eligible trades: 7
- Cash-settled trades: 2

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 7 | $862.80 | $123.26 | 1.825 | 28.6% | $-185.20 | $645.60 | $494.14 | 55.2% | 100.0% |
| marketable | 7 | $1,102.80 | $157.54 | 2.304 | 28.6% | $-145.20 | $525.60 | $522.71 | 53.3% | 100.0% |
| corrected_midpoint | 7 | $1,273.80 | $181.97 | 2.794 | 28.6% | $-110.20 | $454.60 | $551.83 | 51.4% | 100.0% |

## Coverage

- stressed_marketable: eligible=7 priced=7 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=7 priced=7 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=7 priced=7 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 4 | $951.80 | $237.95 | 2.521 | 25.0% |
| second_half | 3 | $-89.00 | $-29.67 | 0.788 | 33.3% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $1,908.80 | $954.40 | 999.000 | 100.0% |
| intraday_exit | 5 | $-1,046.00 | $-209.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 5 | $1,348.20 | $269.64 | 3.405 | 40.0% |
| PUT | 2 | $-485.40 | $-242.70 | 0.000 | 0.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 7 | $862.80 | $123.26 | 1.825 | 28.6% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 2 | $1,908.80 | $954.40 | 999.000 | 100.0% |
| drawdown_late_morning | 1 | $-280.20 | $-280.20 | 0.000 | 0.0% |
| drawdown_morning | 4 | $-765.80 | $-191.45 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 7/120 (not met)
- cash_settled_trades: 2/20 (not met)
- stressed_winners: 2/15 (not met)
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
