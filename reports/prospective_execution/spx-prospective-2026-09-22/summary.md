# Prospective execution validation — spx-prospective-2026-09-22

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-09-22
- Generated: 2026-09-25T01:36:22.631618+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 2
- No signal: 0
- Incomplete data: 0
- Eligible trades: 2
- Cash-settled trades: 1

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 2 | $939.20 | $469.60 | 5.171 | 50.0% | $469.60 | $225.20 | $847.40 | 68.7% | 100.0% |
| marketable | 2 | $999.20 | $499.60 | 6.395 | 50.0% | $499.60 | $185.20 | $887.30 | 66.7% | 100.0% |
| corrected_midpoint | 2 | $1,038.20 | $519.10 | 7.563 | 50.0% | $519.10 | $158.20 | $925.90 | 64.6% | 100.0% |

## Coverage

- stressed_marketable: eligible=2 priced=2 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=2 priced=2 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=2 priced=2 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |
| second_half | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |
| intraday_exit | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |
| PUT | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09 | 2 | $939.20 | $469.60 | 5.171 | 50.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,164.40 | $1,164.40 | 999.000 | 100.0% |
| drawdown_morning | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 2/120 (not met)
- cash_settled_trades: 1/20 (not met)
- stressed_winners: 1/15 (not met)
- Endpoint reached: no

## Decision gates

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
