# Prospective execution validation — spx-prospective-2026-09-22

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-09-22
- Generated: 2026-09-24T01:32:34.692886+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 1
- No signal: 0
- Incomplete data: 0
- Eligible trades: 1
- Cash-settled trades: 0

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% | $-225.20 | $225.20 | $0.00 | 0.0% | 0.0% |
| marketable | 1 | $-185.20 | $-185.20 | 0.000 | 0.0% | $-185.20 | $185.20 | $39.80 | 0.0% | 0.0% |
| corrected_midpoint | 1 | $-158.20 | $-158.20 | 0.000 | 0.0% | $-158.20 | $158.20 | $70.40 | 0.0% | 0.0% |

## Coverage

- stressed_marketable: eligible=1 priced=1 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=1 priced=1 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=1 priced=1 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| intraday_exit | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09 | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| drawdown_morning | 1 | $-225.20 | $-225.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 1/120 (not met)
- cash_settled_trades: 0/20 (not met)
- stressed_winners: 0/15 (not met)
- Endpoint reached: no

## Decision gates

- stressed_net_pnl_positive: fail
- stressed_expectancy_positive: fail
- stressed_profit_factor_above_one: fail
- marketable_positive_in_both_halves: fail
- executable_entry_coverage: pass
- top3_within_limit: pass
- drawdown_within_limit: pass
- Entry coverage: 100.0%
- Edge classification: **no_executable_edge**

Conclusion is provisional until the registered endpoint is reached.
