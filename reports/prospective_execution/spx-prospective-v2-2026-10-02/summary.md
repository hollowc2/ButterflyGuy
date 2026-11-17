# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-17T02:33:37.955478+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 31
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 96.9%
- Deferred sessions: 2026-11-16
- Eligible trades: 31
- Cash-settled trades: 7

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 31 | $120.00 | $3.87 | 1.019 | 19.4% | $-200.20 | $2,859.40 | $536.64 | 37.8% | 79.1% |
| marketable | 31 | $1,220.00 | $39.35 | 1.234 | 22.6% | $-160.20 | $2,484.20 | $565.66 | 36.7% | 78.2% |
| corrected_midpoint | 31 | $2,807.00 | $90.55 | 1.736 | 29.0% | $-135.20 | $1,484.20 | $613.92 | 34.8% | 76.7% |

## Coverage

- stressed_marketable: eligible=31 priced=31 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=31 priced=31 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=31 priced=31 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 16 | $587.20 | $36.70 | 1.213 | 25.0% |
| second_half | 15 | $-467.20 | $-31.15 | 0.863 | 13.3% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| intraday_exit | 24 | $-5,334.80 | $-222.28 | 0.024 | 4.2% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 18 | $-604.20 | $-33.57 | 0.820 | 16.7% |
| PUT | 13 | $724.20 | $55.71 | 1.259 | 23.1% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 10 | $-2,859.40 | $-285.94 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| drawdown_afternoon | 7 | $-1,351.40 | $-193.06 | 0.088 | 14.3% |
| drawdown_late_morning | 3 | $-1,405.60 | $-468.53 | 0.000 | 0.0% |
| drawdown_morning | 14 | $-2,577.80 | $-184.13 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 31/120 (not met)
- cash_settled_trades: 7/20 (not met)
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
