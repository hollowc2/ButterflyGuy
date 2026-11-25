# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-25T02:33:04.341544+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 37
- No signal: 1
- Incomplete data: 1
- Session completion coverage: 97.4%
- Deferred sessions: 2026-11-24
- Eligible trades: 36
- Cash-settled trades: 7

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 36 | $-2,636.00 | $-73.22 | 0.705 | 16.7% | $-202.70 | $5,615.40 | $468.62 | 37.2% | 79.1% |
| marketable | 36 | $-1,336.00 | $-37.11 | 0.828 | 19.4% | $-162.70 | $5,040.20 | $496.52 | 36.0% | 78.2% |
| corrected_midpoint | 36 | $1,821.00 | $50.58 | 1.379 | 25.0% | $-135.20 | $2,470.20 | $554.04 | 33.2% | 76.7% |

## Coverage

- stressed_marketable: eligible=36 priced=36 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=36 priced=36 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=36 priced=36 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 18 | $1,394.40 | $77.47 | 1.498 | 27.8% |
| second_half | 18 | $-4,030.40 | $-223.91 | 0.342 | 5.6% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| intraday_exit | 29 | $-8,090.80 | $-278.99 | 0.016 | 3.5% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 20 | $-1,214.60 | $-60.73 | 0.695 | 15.0% |
| PUT | 16 | $-1,421.40 | $-88.84 | 0.713 | 18.8% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 15 | $-5,615.40 | $-374.36 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| drawdown_afternoon | 7 | $-1,351.40 | $-193.06 | 0.088 | 14.3% |
| drawdown_late_morning | 4 | $-3,100.80 | $-775.20 | 0.000 | 0.0% |
| drawdown_morning | 18 | $-3,638.60 | $-202.14 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 36/120 (not met)
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
