# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-12T02:36:29.892158+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 28
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 96.5%
- Deferred sessions: 2026-11-11
- Eligible trades: 28
- Cash-settled trades: 6

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 28 | $958.00 | $34.21 | 1.180 | 21.4% | $-192.70 | $2,021.40 | $590.39 | 38.0% | 79.1% |
| marketable | 28 | $1,958.00 | $69.93 | 1.438 | 25.0% | $-152.70 | $1,746.20 | $621.09 | 37.0% | 78.2% |
| corrected_midpoint | 28 | $3,460.00 | $123.57 | 2.095 | 32.1% | $-111.70 | $1,012.40 | $671.85 | 35.2% | 76.7% |

## Coverage

- stressed_marketable: eligible=28 priced=28 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=28 priced=28 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=28 priced=28 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 14 | $667.60 | $47.69 | 1.262 | 21.4% |
| second_half | 14 | $290.40 | $20.74 | 1.104 | 21.4% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| intraday_exit | 22 | $-4,869.40 | $-221.34 | 0.026 | 4.5% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 16 | $-16.40 | $-1.02 | 0.994 | 18.8% |
| PUT | 12 | $974.40 | $81.20 | 1.382 | 25.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 7 | $-2,021.40 | $-288.77 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 6 | $5,827.40 | $971.23 | 18.788 | 83.3% |
| drawdown_afternoon | 7 | $-1,351.40 | $-193.06 | 0.088 | 14.3% |
| drawdown_late_morning | 3 | $-1,405.60 | $-468.53 | 0.000 | 0.0% |
| drawdown_morning | 12 | $-2,112.40 | $-176.03 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 28/120 (not met)
- cash_settled_trades: 6/20 (not met)
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
