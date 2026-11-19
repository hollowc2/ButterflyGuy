# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-19T02:35:27.179975+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 33
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 97.1%
- Deferred sessions: 2026-11-18
- Eligible trades: 33
- Cash-settled trades: 7

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 33 | $-330.40 | $-10.01 | 0.950 | 18.2% | $-200.20 | $3,309.80 | $511.22 | 37.2% | 79.1% |
| marketable | 33 | $849.60 | $25.75 | 1.152 | 21.2% | $-160.20 | $2,854.60 | $540.91 | 36.0% | 78.2% |
| corrected_midpoint | 33 | $2,619.60 | $79.38 | 1.655 | 27.3% | $-117.20 | $1,671.60 | $589.56 | 34.0% | 76.7% |

## Coverage

- stressed_marketable: eligible=33 priced=33 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=33 priced=33 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=33 priced=33 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 17 | $542.00 | $31.88 | 1.194 | 23.5% |
| second_half | 16 | $-872.40 | $-54.52 | 0.771 | 12.5% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| intraday_exit | 26 | $-5,785.20 | $-222.51 | 0.022 | 3.9% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 18 | $-604.20 | $-33.57 | 0.820 | 16.7% |
| PUT | 15 | $273.80 | $18.25 | 1.084 | 20.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 12 | $-3,309.80 | $-275.82 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| drawdown_afternoon | 7 | $-1,351.40 | $-193.06 | 0.088 | 14.3% |
| drawdown_late_morning | 3 | $-1,405.60 | $-468.53 | 0.000 | 0.0% |
| drawdown_morning | 16 | $-3,028.20 | $-189.26 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 33/120 (not met)
- cash_settled_trades: 7/20 (not met)
- stressed_winners: 6/15 (not met)
- Endpoint reached: no

## Decision gates

- session_data_complete: fail
- stressed_net_pnl_positive: fail
- stressed_expectancy_positive: fail
- stressed_profit_factor_above_one: fail
- marketable_positive_in_both_halves: fail
- executable_entry_coverage: pass
- top3_within_limit: fail
- drawdown_within_limit: pass
- Entry coverage: 100.0%
- Edge classification: **no_executable_edge**

Conclusion is provisional until the registered endpoint is reached.
