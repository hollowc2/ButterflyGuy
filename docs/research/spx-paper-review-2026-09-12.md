# SPX paper-trade review — September 12, 2026

## Evidence and scope

Read-only extraction from Helios, `/opt/butterflyguy`, running `butterfly_spx_app`, TimescaleDB `butterfly_trades`, underlying SPX. The remote checked-in SPX config specifies paper trading and the same trailing thresholds described below. All 108 returned trades are CLOSED, March 17–September 11, 2026; no open SPX rows were returned. Historical per-row paper/live identity is not independently attested for legacy records. Remote checkout SHA: `9294299`; local checkout: `e2ba77284370b7edc7c7e94d659fe707a226f834`. A checkout SHA does not attest the running image's source. The extraction helper's bare `load_config()` uses defaults (empty regimes), so its configuration output is not evidence of the orchestrator's effective loaded YAML.

Latest stored SPX spot: 7,654.88 at September 11, 2026 19:59:34 UTC (15:59:34 Eastern), source label `schwab`. This is a stored observation, not a real-time Saturday quote or official settlement. Querying `spot_prices` for the literal underlying `VIX` returned no rows; this does not establish that VIX data under other identifiers/tables is absent. SPX metrics endpoint responded and its container was running.

Sanitized extracted fields: `/tmp/spx-paper-trades-2026-09-12.json`; SHA-256 `69d21d7514e4610439d97abe4d65fb9163c74519df9e94ae465948e1c6a72515`. Query: select trade IDs, dates, direction, width, center, entry/exit prices and timestamps, exit reason, P/L, peak, quantity, status, and metadata fill-model/VIX fields from SPX trades, ordered by date and entry time. Extraction script: `/tmp/spx_research_read.py`. No credentials or account identifiers exported. Dates below are ledger trade dates; session interpretation is US Eastern.

## Findings

- Full ledger: 108 trades, 20 wins, 88 losses; 18.52% win rate; recorded P/L +$1,835; expectancy +$16.99/trade; profit factor 1.139; average winner $749.85 and average loser −$149.57. Closed-trade cumulative-P/L maximum drawdown: $4,213, including zero starting P/L as the initial high-water mark.
- Remove August 3 (+$2,288) and June 22 (+$2,258): remaining P/L −$2,711. This is a concentration diagnostic, not a forecast or reason to discard legitimate winners.
- Newer `mark_v1` cohort, July 22–September 11: 33 trades, six wins, 18.18% win rate, −$533 total, −$16.15/trade expectancy, 0.834 profit factor, $446.67 average win, −$119 average loss, $2,053 closed-trade drawdown. Without its biggest winner, this cohort loses $2,821.
- Monthly recorded P/L: March −$990; April +$578; May +$2,042; June +$2,650; July −$2,702; August +$657; September through the 11th −$400. August without its August 3 winner is −$1,631.
- Morning drawdown exits: 51 trades, three winners, −$6,378 total. Late-morning drawdown exits: ten trades, −$1,366. Afternoon drawdown exits: 22 trades, −$1,441. These are outcome-conditioned groups: they do not establish that removing stops would improve performance.
- Twenty-two losing trades recorded peak value at least twice entry cost; six belong to `mark_v1`. September 9 recorded entry 2.07, peak 6.92 and exit 1.67: a quoted peak gain of $485 followed by a recorded $40 loss. July 23 recorded a $708 peak gain and a $178 loss. Peaks alone do not establish valid quotes, achievable execution, or an alternative strategy's returns.

P/L formula follows the existing dashboard: `pnl * 100 * quantity`. The mark fill implementation incorporates commission into entry/exit prices; do not subtract it a second time. Full historical commission attribution is not established. All quantities in this extraction are one. Account-level percentage return, intratrade drawdown, and capital exposure are not established by this extract. Reported drawdown is in dollars, not a percentage of account equity.

## Mechanism worth testing

The checked-in `peakvaluetrailer` configuration allows 60%, 90%, and 75% drawdown from peak spread value by session regime. This is drawdown from total value, not a fraction of profit. For a $2 entry and $4 peak, a 60% drawdown threshold triggers near $1.60: a trade that doubled can still close at a loss. At a 90% threshold, a $10 peak can fall to $1 before triggering. Quote sampling, commissions and fills can move actual exits further.

An existing `profitprotector` policy provides break-even and profit floors and tighter large-peak trailing. Its activation settings are absolute option-price points, while the large-peak ratio is multiplicative. Testing it requires no new runtime strategy implementation. It could also cut off eventual large winners; improved win rate alone is insufficient.

## Research pipeline and proposed experiment

1. `run_backtest_db.py`: primary config-backed shared-selection replay, including paper commissions and optional per-spread slippage. Explicitly use `--direction auto` for gap-based direction; do not rely on a fixed-direction default. Confirm deployed config/image parity and option-chain/monitoring coverage before replay.
2. `report_selection_parity.py` and `report_exit_mark_parity.py`: diagnose differences between recorded decisions/exits and historical replay, especially the six recent doubled-then-lost trades and August 3 winner.
3. `run_paper_replay.py`: mechanics diagnostic with independent hard-coded width, timing and drawdown defaults; not a frozen current-strategy baseline.
4. `discover_options_strategy.py`: chronological train/validation/test discovery using crossed spreads and commissions. The July study rejected its best candidate for instability; its historical results are not evidence about the current September cohort.

Hypothesis: the existing profit-protection policy reduces profitable-to-losing reversals enough to improve net expectancy and drawdown without destroying the right tail. Compare only `peakvaluetrailer` versus the already-defined `profitprotector`, with identical SPX entry decisions, widths, quantity, data, fees and execution assumptions. First replay actual recorded entries to isolate exits, then check config-backed selection end to end. Preserve the full winner set.

Use the observed March 17–September 11 history for development/diagnosis, segment by fill-model and configuration history, and freeze the candidate before future sessions. Because this entire ledger has now been examined, September is not an untouched holdout. Use a future chronological paper observation window for confirmation. Stress fills using the recorded spread and bounded slippage; evaluate expectancy, profit factor, win/loss size, drawdown, exposure and top-winner concentration. Reject a candidate that merely raises win rate while lowering cost-adjusted expectancy or depending on one parameter setting.

This review computes observed ledger statistics; it does not claim a new backtest or validated improvement. No strategy, risk, execution, configuration, services or broker state were changed. A broad sweep was not launched on the running host; its observed load average was 13.76 during retrieval. The next evidence needed is chronological quote-path coverage and deployed-config parity, not more parameter combinations.
