# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-09T01:33:53.873041+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 4
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 80.0%
- Deferred sessions: 2026-10-08
- Eligible trades: 4
- Cash-settled trades: 1

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 4 | $951.80 | $237.95 | 2.521 | 25.0% | $-172.70 | $440.40 | $587.30 | 67.2% | 100.0% |
| marketable | 4 | $1,091.80 | $272.95 | 3.159 | 25.0% | $-132.70 | $360.40 | $627.30 | 63.7% | 100.0% |
| corrected_midpoint | 4 | $1,196.80 | $299.20 | 3.832 | 25.0% | $-104.20 | $312.40 | $664.90 | 60.9% | 100.0% |

## Coverage

- stressed_marketable: eligible=4 priced=4 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=4 priced=4 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=4 priced=4 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 2 | $1,392.20 | $696.10 | 8.517 | 50.0% |
| second_half | 2 | $-440.40 | $-220.20 | 0.000 | 0.0% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |
| intraday_exit | 3 | $-625.60 | $-208.53 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 3 | $1,232.00 | $410.67 | 4.567 | 33.3% |
| PUT | 1 | $-280.20 | $-280.20 | 0.000 | 0.0% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 4 | $951.80 | $237.95 | 2.521 | 25.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 1 | $1,577.40 | $1,577.40 | 999.000 | 100.0% |
| drawdown_late_morning | 1 | $-280.20 | $-280.20 | 0.000 | 0.0% |
| drawdown_morning | 2 | $-345.40 | $-172.70 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 4/120 (not met)
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
