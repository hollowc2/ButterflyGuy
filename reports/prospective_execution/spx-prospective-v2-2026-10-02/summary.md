# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-10-23T01:32:05.864686+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 14
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 93.3%
- Deferred sessions: 2026-10-22
- Eligible trades: 14
- Cash-settled trades: 4

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 14 | $667.60 | $47.69 | 1.262 | 21.4% | $-192.70 | $1,343.40 | $442.03 | 51.9% | 100.0% |
| marketable | 14 | $1,147.60 | $81.97 | 1.540 | 21.4% | $-152.70 | $1,163.40 | $467.37 | 50.0% | 100.0% |
| corrected_midpoint | 14 | $1,506.60 | $107.61 | 1.832 | 21.4% | $-122.70 | $1,012.40 | $498.30 | 47.6% | 100.0% |

## Coverage

- stressed_marketable: eligible=14 priced=14 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=14 priced=14 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=14 priced=14 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 7 | $862.80 | $123.26 | 1.825 | 28.6% |
| second_half | 7 | $-195.20 | $-27.89 | 0.870 | 14.3% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| intraday_exit | 10 | $-2,217.00 | $-221.70 | 0.000 | 0.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 8 | $622.60 | $77.83 | 1.484 | 25.0% |
| PUT | 6 | $45.00 | $7.50 | 1.036 | 16.7% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 14 | $667.60 | $47.69 | 1.262 | 21.4% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 4 | $2,884.60 | $721.15 | 9.805 | 75.0% |
| drawdown_afternoon | 1 | $-155.20 | $-155.20 | 0.000 | 0.0% |
| drawdown_late_morning | 2 | $-635.40 | $-317.70 | 0.000 | 0.0% |
| drawdown_morning | 7 | $-1,426.40 | $-203.77 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 14/120 (not met)
- cash_settled_trades: 4/20 (not met)
- stressed_winners: 3/15 (not met)
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
