# Prospective execution validation — spx-prospective-v2-2026-10-02

- Asset: SPX
- Cohort label: prospective
- Prospective start: 2026-10-02
- Generated: 2026-11-18T02:33:23.856174+00:00
- Primary result: **stressed_marketable** (corrected midpoint is a comparison baseline only)

## Sessions

- Sessions recorded: 32
- No signal: 0
- Incomplete data: 1
- Session completion coverage: 97.0%
- Deferred sessions: 2026-11-17
- Eligible trades: 32
- Cash-settled trades: 7

## Accounting models

| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | Avg MFE | MFE cap | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stressed_marketable | 32 | $-65.20 | $-2.04 | 0.990 | 18.8% | $-200.20 | $3,044.60 | $526.42 | 37.3% | 79.1% |
| marketable | 32 | $1,074.80 | $33.59 | 1.201 | 21.9% | $-160.20 | $2,629.40 | $555.79 | 36.1% | 78.2% |
| corrected_midpoint | 32 | $2,689.80 | $84.06 | 1.684 | 28.1% | $-126.20 | $1,601.40 | $603.69 | 34.3% | 76.7% |

## Coverage

- stressed_marketable: eligible=32 priced=32 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- marketable: eligible=32 priced=32 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0
- corrected_midpoint: eligible=32 priced=32 unpriced=0 coverage=100.0% missing_entry=0 crossed_entry=0 missing_exit=0 crossed_exit=0 skipped_exit_obs=0 settlement_fallbacks=0

## stressed_marketable by half

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| first_half | 16 | $587.20 | $36.70 | 1.213 | 25.0% |
| second_half | 16 | $-652.40 | $-40.77 | 0.819 | 12.5% |

## stressed_marketable by settlement

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| intraday_exit | 25 | $-5,520.00 | $-220.80 | 0.023 | 4.0% |

## stressed_marketable by direction

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| CALL | 18 | $-604.20 | $-33.57 | 0.820 | 16.7% |
| PUT | 14 | $539.00 | $38.50 | 1.181 | 21.4% |

## stressed_marketable by month

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-10 | 21 | $2,979.40 | $141.88 | 1.901 | 28.6% |
| 2026-11 | 11 | $-3,044.60 | $-276.78 | 0.000 | 0.0% |

## stressed_marketable by exit_reason

| Group | Trades | Net P&L | Expectancy | PF | Win% |
| --- | ---: | ---: | ---: | ---: | ---: |
| cash_settled | 7 | $5,454.80 | $779.26 | 8.790 | 71.4% |
| drawdown_afternoon | 7 | $-1,351.40 | $-193.06 | 0.088 | 14.3% |
| drawdown_late_morning | 3 | $-1,405.60 | $-468.53 | 0.000 | 0.0% |
| drawdown_morning | 15 | $-2,763.00 | $-184.20 | 0.000 | 0.0% |

## Registered endpoint

- eligible_trades: 32/120 (not met)
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
