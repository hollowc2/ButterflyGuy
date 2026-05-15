# Graph Report - butterflyguy  (2026-05-15)

## Corpus Check
- 108 files · ~282,268 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1562 nodes · 2652 edges · 118 communities (101 shown, 17 thin omitted)
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 738 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f39ab323`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 114|Community 114]]
- [[_COMMUNITY_Community 115|Community 115]]
- [[_COMMUNITY_Community 116|Community 116]]
- [[_COMMUNITY_Community 117|Community 117]]

## God Nodes (most connected - your core abstractions)
1. `make_settings()` - 42 edges
2. `make_candidate()` - 42 edges
3. `make_order_manager()` - 41 edges
4. `SimulationEngine` - 39 edges
5. `MinuteBar` - 39 edges
6. `SimulationParams` - 36 edges
7. `ButterflyBuilder` - 36 edges
8. `StrategySettings` - 34 edges
9. `main()` - 32 edges
10. `ButterflySelector` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Compare Synthetic Same Entry Design` --semantically_similar_to--> `Compare Real vs Synthetic Chains`  [INFERRED] [semantically similar]
  docs/superpowers/specs/2026-04-25-compare-synthetic-same-entry-design.md → README.md
- `TestEma` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestEma` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestEma` --uses--> `SimulationEngine`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/simulation_engine.py
- `TestEma` --uses--> `SimulationParams`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/simulation_engine.py

## Hyperedges (group relationships)
- **Multi-Asset Runtime Configurations** — config_spx_runtime, config_ndx_runtime, config_xsp_runtime, README_butterfly_guy [EXTRACTED 1.00]
- **Monitoring Stack** — prometheus_butterfly_scrapes, datasources_prometheus, datasources_timescaledb, dashboards_butterfly_provider [INFERRED 0.86]
- **Synthetic Backtest Research Lineage** — 2026_04_21_synthetic_comparison_design, 2026_04_25_real_vs_synthetic_stats_design, 2026_04_25_same_entry_design, 2026_04_25_comparison_stats_plan, README_compare_synthetic [INFERRED 0.90]
- **he_option_chain_context** — ui_underlying_spx, ui_option_chain, ui_expiration_20mar26_weekly, ui_calls_side, ui_puts_side [EXTRACTED 1.00]
- **he_butterfly_candidate_selection** — ui_butterfly_spread_mode, ui_15wide_butterfly_rows, ui_put_butterfly_strike_format, ui_liquidity_metrics, ui_entry_window_region [INFERRED 0.75]
- **hyperedge:butterfly_chain_ui_model** — underlying:SPX, expiration:2026_03_20_weekly, spread:butterfly, panel:calls, panel:puts, column:strike_triplet, column:bid, column:ask, column:volume, column:open_interest [INFERRED 0.90]
- **hyperedge:near_money_15_wide_candidates** — ui:highlighted_atm_region, strike_triplet:6555_6570_6585, strike_triplet:6560_6575_6590, strike_triplet:6565_6580_6595, strike_triplet:6570_6585_6600, strike_triplet:6575_6590_6605, strike_triplet:6580_6595_6610, market:spx_last_6581_10 [INFERRED 0.82]
- **hyperedge:execution_screening_inputs** — spread:15_wide_butterfly, concept:bid_ask_spread, concept:liquidity_screening, concept:paper_fill_reference, time:market_open [INFERRED 0.70]
- **Selected Bar Measurement Context** — vertical_crosshair_at_1030, chart_timestamp_2026_03_19_1030, visible_ohlc_metrics, selected_bar_ohlc_values [EXTRACTED 1.00]
- **SPX Quote Context** — spx_symbol, current_spx_quote_6577_69, daily_change_negative_28_80, bid_ask_quote [EXTRACTED 1.00]
- **Visible Intraday Trend Sequence** — overnight_or_premarket_session, regular_market_open_region, sharp_midday_upside_breakout, post_breakout_pullback, last_visible_red_candle [INFERRED 0.75]
- **Chart Navigation Context** — candlestick_price_chart, right_side_price_axis, bottom_time_axis, future_or_expansion_area, thinkorswim_side_panels [EXTRACTED 1.00]
- **hyperedge:put_butterfly_6525_6505_6485** — leg:buy_put_6525, leg:sell_put_6505_x2, leg:buy_put_6485, strike:upper_6525, strike:center_6505, strike:lower_6485, width:20_point_wings [EXTRACTED 0.97]
- **hyperedge:put_butterfly_order_ticket** — order:butterfly_debit_limit, strategy:put_butterfly, expiration:2026-03-20_weekly, price:debit_1_95, underlying:spx [EXTRACTED 0.96]
- **hyperedge_put_butterfly_structure** — put_leg_6485_long, put_leg_6505_short, put_leg_6525_long [EXTRACTED 0.98]
- **hyperedge_chain_context_for_position** — spx_underlying_quote, weekly_expiration_2026_03_20, option_chain_puts_side, spx_put_butterfly_position [INFERRED 0.86]
- **hyperedge:put_butterfly_6525_6505_6485** — order_leg:buy_6525_put, order_leg:sell_6505_put_x2, order_leg:buy_6485_put [EXTRACTED 0.96]
- **hyperedge:visible_chain_context** — option_chain:spx_20_mar_26_weeklys, chain_columns:bid_ask_volume_open_interest, order_ticket:virtual_order_entry_tools, order:butterfly_put_debit [EXTRACTED 0.91]
- **hyperedge_20wide_entry_window_selection** — spx_underlying, spx_last_6554_75, option_chain_spread_butterfly, butterfly_strike_triplets, twenty_wide_butterfly_spacing, entry_window_highlighted_rows, near_money_fly_candidates [INFERRED 0.80]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]

## Communities (118 total, 17 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (64): BaseModel, CollectorSettings, DatabaseSettings, EntrySettings, ExecutionSettings, MonitoringSettings, ProfitManagementSettings, ProfitProtectorSettings (+56 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (45): BaseSettings, AppConfig, load_config(), Load configuration from YAML file and environment variables., Load configuration from YAML file and environment variables., get_logger(), Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs. (+37 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (41): _build_bars(), _build_prev_close(), _build_recent_closes(), _build_vix(), _build_vix_bars(), CsvDataLoader, CSV-based data loader for historical SPX + VIX 1-minute data.  Reads two CSV fil, Loads SPX + VIX 1-minute CSVs and serves DayData objects.      Loads both files (+33 more)

### Community 3 - "Community 3"
Cohesion: 0.15
Nodes (47): make_candidate(), make_chain_data_with_oi(), make_chain_data_with_spread(), make_order_manager(), make_quote(), make_settings(), Tests for OrderManager live mark repricing., When the exit ladder times out, it should force-fill at bid (not return None). (+39 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (37): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+29 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (27): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), _et(), load_bars_from_db(), load_chains_from_db(), main() (+19 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (21): day_cache_path(), load_day(), JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).  Sch, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day. (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (30): fmt_candidate(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args(), parse_date(), print_day_header() (+22 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (32): SPX weekly puts option chain, Bid, ask, volume, and open interest columns, Calls side, Puts side, 20 MAR 26 weekly expiration, Buy 1 SPX 6485 put, Buy 1 SPX 6525 put, Sell 2 SPX 6505 puts (+24 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (16): Async Schwab API client wrapper with retry logic., Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order and return the order ID., Get the status of an order., Cancel an existing order., Fetch 1-minute bars for today (and optionally prior days) from Schwab., Fetch daily OHLCV bars for the given symbol. (+8 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (26): ButterflyCandidate, OptionQuote, Pydantic models for option data and trade records., A single option quote from a chain snapshot., A butterfly spread candidate identified by the scanner., A trade record for tracking entry/exit., TradeRecord, main() (+18 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (31): 📈 Backtesting, 🦋 Butterfly Guy, code:yaml (risk:), code:bash (# Skip days where the absolute gap is below 0.25%), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (# Full test suite), code:bash (# Start the SPX stack), code:yaml (entry:) (+23 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (29): _fitted_density_counts(), _print_pnl_histogram(), Use the first regular-session snapshot for gap direction., Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets. (+21 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (15): MinuteBar, BiasScoreFilter, Scores market direction using 4 signals; returns CALL, PUT, or None., make_bar(), make_pre_entry_bars(), Unit tests for BiasScoreFilter., Bars that produce strong bullish score: rising price, above OR high., Bars that produce strong bearish score: falling price, below OR low. (+7 more)

### Community 14 - "Community 14"
Cohesion: 0.1
Nodes (29): Gap Regime Filter Design, High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Butterfly Guy (+21 more)

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (15): DbDataLoader, DB-backed data loader for historical SPX + VIX data.  Reads from the live Timesc, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*., Loads SPX + VIX data from TimescaleDB and serves DayData objects.      Connects, Return DayData for *date*, or None if no bars found. (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (28): Ask price column, Bid price column, Open interest column, Strike triplet column, Volume column, Bid-ask spread, Liquidity screening, Mark-price fill reference (+20 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (20): IVModel, Implied volatility model with VIX scaling and skew adjustment., Models implied volatility with VIX scaling and volatility skew., Convert VIX index value to 0-DTE ATM IV estimate.          VIX is the 30-day imp, Compute skew-adjusted IV for a given strike.          OTM puts have elevated IV, Synthetic option chain generator using Black-Scholes + VIX IV model., Minutes until market close on expiration day., Generates a synthetic SPX option chain from spot + VIX. (+12 more)

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (21): ButterflyOrderBuilder, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure.  These tests check th, Realistic SPX butterfly candidate. (+13 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (19): DayData, Backtest data loader — fetches SPX 1-min bars and VIX from Polygon.io., DrawdownWindow, Runs full strategy on a single day using synthetic options., Runs full strategy on a single day using synthetic options., SimulationEngine, SimulationParams, TimeRegime (+11 more)

### Community 20 - "Community 20"
Cohesion: 0.16
Nodes (15): now_utc(), LiveSpread, OrderManager, Order execution with price ladder logic., Place one butterfly order at limit_price. Wait for fill; cancel if unfilled., Execute entry with price ladder: reprice from live mark each step,         step, Execute exit with reverse price ladder: reprice from live mark each step,, Manages order execution with price ladder and fill monitoring. (+7 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (17): Risk management engine — enforces daily limits and trading rules., Record that a trade was executed., Overwrite realized_pnl in risk state (SET, not ADD).         Used at startup to, Manually sync the trade count in the risk state table.         Used at startup t, Enforces risk constraints before allowing trades., RiskEngine, make_risk_engine(), Tests for the risk engine. (+9 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (21): is_market_open(), is_trading_day(), Check if the market is currently open., Check if a given date is a trading day (weekday, not a holiday)., Check if current time is within the given window (HH:MM strings)., time_in_window(), Check all risk conditions. Returns (allowed, reason).          account_value and, et() (+13 more)

### Community 23 - "Community 23"
Cohesion: 0.16
Nodes (18): _dd_schedule_label(), _find_bar_at(), _live_width_label(), load_asset_config(), main(), nearest_snapshot(), parse_args(), _parse_config_time() (+10 more)

### Community 24 - "Community 24"
Cohesion: 0.2
Nodes (17): StrategySettings, ButterflyBuilder, Builds and scores butterfly spreads from an option chain snapshot., Builds and scores butterfly spreads from an option chain snapshot., make_chain(), make_quote(), Tests for the butterfly builder scanner., Generate a synthetic chain of call quotes around spot. (+9 more)

### Community 25 - "Community 25"
Cohesion: 0.1
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (8): GapRegimeFilter, Regime, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct, TestSkipBeforeOverride

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (20): Bid and ask quote columns, Butterfly chain rows expose bid/ask values usable for mid-price marking, Butterfly spread mode, Highlighted active trade region, Calls side, Option Chain panel, Puts side, POS marker (+12 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (17): ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log n, load_chains_from_db(), load_entry_chains(), load_monitoring_chains(), Load only the entry-window snapshots (09:30–10:45 ET) for butterfly selection., Load only the entry-window snapshots (09:30–10:45 ET) for butterfly selection., Load only the entry-window snapshots (09:30–10:45 ET) for butterfly selection. (+9 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (14): SweepConfig, DayResult, _drawdown_rule(), _profit_exit_reason(), Single-day simulation engine using synthetic option chains., Simulate one trading day., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (16): 1. `strategy/gap_regime_filter.py` (new file), 2. `core/config.py` — `EntrySettings`, 3. Live path, 4. Backtest path (`run_backtest_db.py`), code:python (@dataclass), code:python (bull_call_bias: bool = False   # Override to CALL in BULL re), code:python (if self.gap_regime_filter:), code:block5 (--bull-call-bias      Override to CALL in BULL regime on gap) (+8 more)

### Community 31 - "Community 31"
Cohesion: 0.14
Nodes (13): get_0dte_expiration(), now_eastern(), Current time in US/Eastern., Get today's date as the 0-DTE expiration (SPX has daily expirations)., Fetch current chain and store snapshot. Returns row count., Main collector loop — runs while market is open., Full entry flow from eligibility checks through entry fill., Fetch today's first regular-session open from Schwab intraday bars. (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.17
Nodes (14): compute_tent_boundaries(), fly_bid_value(), fly_settlement_value(), Position value tracking and management., Butterfly value at market bid (what a MM pays to buy it from you)., Butterfly value at market bid (what a MM pays to buy it from you)., Butterfly cash-settlement value from the underlying index close., Find the two spot prices where the fly's BS mark equals entry cost.      These a (+6 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (14): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ), Common Commands (+6 more)

### Community 34 - "Community 34"
Cohesion: 0.17
Nodes (16): 20 Wide Butterfly Candidate Rows, At The Money Strike Region, Bid And Ask Columns, Calls Side Option Chain Table, Entry Window Selection Context, Highlighted Candidate Band Near Underlying Price, 20 Wide Fly Chain At Entry Window Screenshot, 20 Mar 2026 Weekly Expiration (+8 more)

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (15): Butterfly strike triplets, Calls side, Call butterfly rows in entry window, Entry-window highlighted rows, Put butterfly rows in entry window, 20 MAR 26 weekly expiration, Near-money butterfly candidates, Option chain spread: Butterfly (+7 more)

### Community 36 - "Community 36"
Cohesion: 0.13
Nodes (15): Select the best butterfly candidate for a single wing width., Select the best butterfly candidate for a single wing width., Select the best butterfly candidate for a single wing width., Cross-width selection., Select the best butterfly candidate for a single wing width., Cross-width selection., Cross-width selection., Cross-width selection. (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.13
Nodes (13): 1. `SimulationEngine.simulate_day_from_entry()`, 2. `run_backtest_db.py` changes, 3. Output, Architecture, code:block2 (--compare-synthetic-same-entry   Run a BS-only intraday pass), code:python (same_entry_result = None), code:block4 (.venv/bin/python -m butterfly_guy.scripts.run_backtest_db --), Design: --compare-synthetic-same-entry Mode (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (14): 1. New CLI flag, 2. New helper function, 3. Modified `run_single` per-date loop, 4. Output, Approach, Changes, code:block1 (--compare-synthetic   Run a second synthetic-only pass and p), code:python (def _force_synthetic_for_date(date: dt.date):) (+6 more)

### Community 39 - "Community 39"
Cohesion: 0.22
Nodes (12): chain_cache_path(), load_chain_day(), nearest_snapshot(), Real option chain cache — per-day JSON snapshots from the live collector.  Forma, Load all chain snapshots for a day.      Returns dict of UTC datetime -> list[Op, Return quotes from the most recent snapshot at or before bar_ts., Append one chain snapshot to the day's cache file.      Called by the collector, save_snapshot() (+4 more)

### Community 40 - "Community 40"
Cohesion: 0.18
Nodes (11): get_time_regime(), minutes_since_open(), minutes_to_close(), now_pacific(), Market timezone helpers for 0-DTE trading., Current time in US/Pacific., Minutes remaining until market close., Classify minutes since open into a named time regime. (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (13): get_recent_closes(), get_vix_prev_close(), Up to *n* daily closes strictly before *date*, chronological order., Up to *n* daily closes strictly before *date*, chronological order., Return VIX daily close strictly before *date* from daily_bars., Return VIX daily close strictly before *date* from daily_bars., Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains., Up to *n* daily closes strictly before *date*, chronological order. (+5 more)

### Community 42 - "Community 42"
Cohesion: 0.28
Nodes (12): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+4 more)

### Community 43 - "Community 43"
Cohesion: 0.17
Nodes (9): PositionManager, Tracks position value from chain data and manages peak tracking., Reset for a new position. Optionally restore a persisted peak (e.g. after restar, Tracks position value from chain data and manages peak tracking., Reset for a new position. Optionally restore a persisted peak (e.g. after restar, PositionService, Position monitoring service — runs state machine on open positions., Monitors open positions and manages exits via the profit state machine. (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.21
Nodes (13): 15-wide fly chain at entry window screenshot, 15-wide butterfly strike rows, Bid/ask color coding, Butterfly spread mode, Calls side, Entry-window candidate region, 20 MAR 26 weekly expiration, Liquidity metrics (+5 more)

### Community 45 - "Community 45"
Cohesion: 0.21
Nodes (6): BacktestDataLoader, Load all data needed for a single backtest day., Loads historical data from Polygon.io for backtesting., Fetch SPX 1-minute bars for a given date from Polygon., Fetch VIX close for a given date from Polygon., Fetch the actual previous trading day's SPX close for a given date.

### Community 46 - "Community 46"
Cohesion: 0.21
Nodes (3): Backtest data loader using yfinance (free, no API key required).  Uses hourly ba, Loads historical SPX + VIX data via yfinance. No API key required., YFinanceDataLoader

### Community 47 - "Community 47"
Cohesion: 0.18
Nodes (9): iter_chain_options(), Shared utilities for parsing Schwab option chain responses., Yield (strike, option_type, opt_dict) for each option matching the expiration., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects. (+1 more)

### Community 48 - "Community 48"
Cohesion: 0.18
Nodes (11): print_thinkback_checklist(), Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist. (+3 more)

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (11): _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday (+3 more)

### Community 50 - "Community 50"
Cohesion: 0.18
Nodes (11): get_vix_at(), load_bars_from_db(), load_date_data(), Load all data for one date. Returns None if insufficient data., Load all data for one date. Returns None if insufficient data., Load all data for one date. Returns None if insufficient data., Load all data for one date. Returns None if insufficient data., Load all data for one date. Returns None if insufficient data. (+3 more)

### Community 51 - "Community 51"
Cohesion: 0.18
Nodes (5): CandidateQueries, Database query helpers for all tables., Queries for butterfly_candidates table., Queries for spot_prices table., SpotQueries

### Community 52 - "Community 52"
Cohesion: 0.2
Nodes (10): BUTTERFLYGUY, connectivity visual association, precision visual association, technology visual association, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.29
Nodes (3): DiscordNotifier, Discord webhook notifications., Sends trading notifications to Discord via webhook.

### Community 54 - "Community 54"
Cohesion: 0.2
Nodes (10): _force_synthetic_for_date(), Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Inject DB chains into the chain cache for `date`. Returns restore callable., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback. (+2 more)

### Community 55 - "Community 55"
Cohesion: 0.22
Nodes (3): Queries for trades table., TradeQueries, dict

### Community 56 - "Community 56"
Cohesion: 0.2
Nodes (4): Queries for daily_risk_state table., Sum of realized PnL for the rolling 7-day window (closed trades only)., PnL of the last N closed trades (most recent first), for consecutive loss detect, RiskQueries

### Community 57 - "Community 57"
Cohesion: 0.2
Nodes (9): code:python ("""Tests for _print_comparison_table aggregate stats."""), code:bash (cd /opt/butterflyguy && .venv/bin/python -m pytest tests/tes), code:python (def _print_comparison_table(day_rows: list[dict]) -> None:), code:bash (cd /opt/butterflyguy && .venv/bin/python -m pytest tests/tes), code:bash (cd /opt/butterflyguy && git add tests/test_comparison_stats.), code:bash (cd /opt/butterflyguy && .venv/bin/python -m butterfly_guy.sc), Real vs Synthetic Comparison Stats Implementation Plan, Task 1: Add stats block to `_print_comparison_table` (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (6): Record trade exit metrics and update risk engine., Extract the three butterfly leg quotes from the chain for position valuation., Record trade exit metrics and update risk engine., Extract the three butterfly leg quotes from the chain for position valuation., Monitor position every 10s, evaluate state machine, trigger exit if needed., Monitor position every 10s, evaluate state machine, trigger exit if needed.

### Community 59 - "Community 59"
Cohesion: 0.36
Nodes (7): Trade service — orchestrates entry flow., Return the first regular-session open for the requested Eastern date., _session_open_from_intraday_candles(), _candle(), test_session_open_ignores_premarket_and_missing_open_values(), test_session_open_returns_none_when_no_regular_session_bar_exists(), test_session_open_uses_first_regular_session_bar_for_requested_date()

### Community 60 - "Community 60"
Cohesion: 0.22
Nodes (9): _asset_drawdowns(), Resolve the DB connection string for local backtests.      Backtests follow the, Resolve the DB connection string for local backtests.      Backtests follow the, Resolve the DB connection string for local backtests.      Backtests follow the, Return live morning/late/afternoon drawdown thresholds., Return live morning/late/afternoon drawdown thresholds., Resolve the DB connection string for local backtests.      Backtests follow the, Resolve the DB connection string for local backtests.      Backtests follow the (+1 more)

### Community 61 - "Community 61"
Cohesion: 0.22
Nodes (9): _patch_chain_cache(), Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable. (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.22
Nodes (4): DatabasePool, Async database connection pool using asyncpg., Manages an asyncpg connection pool for TimescaleDB., Create the connection pool.

### Community 63 - "Community 63"
Cohesion: 0.25
Nodes (5): Intraday VIX regime filter — skips entry when volatility is too elevated., Filter entries based on intraday VIX level at the time of entry., Most recent VIX bar close at or before entry_ts. None if no bars., True = safe to trade. False = skip (VIX too high).          Returns True if no V, RegimeFilter

### Community 64 - "Community 64"
Cohesion: 0.22
Nodes (8): Butterfly Guy — Implementation Plan, Context, Phase 1: Infrastructure + TimescaleDB + Option Chain Collector, Phase 2: Butterfly Scanner, Phase 3: Paper Trading Execution, Phase 4: Profit Management State Machine, Phase 5: Synthetic Engine + Backtesting, Phase 6: Dashboard + Monitoring + Discord

### Community 65 - "Community 65"
Cohesion: 0.22
Nodes (8): code:block1 (═══════════════════════════════════════════════════════════), code:bash (.venv/bin/python -m butterfly_guy.scripts.run_backtest_db --), Goal, Implementation, Real vs Synthetic Backtest Comparison — Design Spec, Run Command, Scope, Stats Block

### Community 66 - "Community 66"
Cohesion: 0.22
Nodes (9): Bid Ask Quote, Bottom Time Axis, Candlestick Price Chart, Right Side Price Axis, SPX Symbol, 10 Minute Timeframe, Thinkorswim Side Panels, 3 Day Chart Range (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 68 - "Community 68"
Cohesion: 0.25
Nodes (7): daily_reset_loop(), entry_loop(), Main orchestrator: runs collector + trading + position monitor concurrently., Reset daily risk state at market open., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Reset daily risk state at market open.

### Community 69 - "Community 69"
Cohesion: 0.25
Nodes (6): Classify regime then delegate to simulate_day() with matching params.          R, Classify regime then delegate to simulate_day() with matching params.          R, Classify regime then delegate to simulate_day() with matching params.          R, Maps Regime → SimulationParams for use with simulate_day_adaptive().      Per-re, Maps Regime → SimulationParams for use with simulate_day_adaptive().      Per-re, RegimeDispatch

### Community 70 - "Community 70"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 71 - "Community 71"
Cohesion: 0.29
Nodes (6): Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter.

### Community 72 - "Community 72"
Cohesion: 0.29
Nodes (7): get_prev_close(), Return the last spot price at or before 16:00 ET on the previous trading day., Return the last spot price at or before 16:00 ET on the previous trading day., Return the last spot price at or before 16:00 ET on the previous trading day., Return the last spot price at or before 16:00 ET on the previous trading day., Return the last spot price at or before 16:00 ET on the previous trading day., Return the last spot price at or before 16:00 ET on the previous trading day.

### Community 73 - "Community 73"
Cohesion: 0.29
Nodes (7): discover_dates(), All dates in [start, end] with >= 50 snapshots for `underlying`., All dates in [start, end] with >= 50 snapshots for `underlying`., All dates in [start, end] with >= 50 snapshots for `underlying`., All dates in [start, end] with >= 50 snapshots for `underlying`., All dates in [start, end] with >= 50 snapshots for `underlying`., All dates in [start, end] with >= 50 snapshots for `underlying`.

### Community 74 - "Community 74"
Cohesion: 0.29
Nodes (4): DailyBarQueries, Queries for daily_bars table., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict., Return the last `days` daily closes in chronological order (oldest first).

### Community 75 - "Community 75"
Cohesion: 0.29
Nodes (3): ChainQueries, Queries for option_chain_snapshots table., Bulk insert option chain snapshot rows using COPY.

### Community 77 - "Community 77"
Cohesion: 0.48
Nodes (6): make_candidate(), Tests for butterfly candidate selection., test_regular_best_rr_selection_still_uses_rr_target(), test_vix_centered_selection_uses_rr_target_after_center_filter(), test_vix_farthest_otm_ignores_rr_target_after_builder_price_filters(), test_vix_selection_rejects_cheap_extreme_rr_tail_candidate()

### Community 78 - "Community 78"
Cohesion: 0.38
Nodes (5): _compute_or(), _compute_vwap(), _ema(), Multi-signal directional bias filter for 0-DTE butterfly entries., Compute bias score from 4 signals:           gap          : +1 if entry_close >

### Community 79 - "Community 79"
Cohesion: 0.33
Nodes (7): Synthetic vs Real Backtest Comparison Design, Comparison Stats Implementation Plan, Real vs Synthetic Aggregate Stats Design, Compare Synthetic Same Entry Design, Compare Real vs Synthetic Chains, DB Backtesting, Phase 5 Synthetic Engine and Backtesting

### Community 80 - "Community 80"
Cohesion: 0.33
Nodes (6): merge_chains(), Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains., Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains., Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains., Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains., Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains.

### Community 82 - "Community 82"
Cohesion: 0.4
Nodes (3): determine_direction(), Direction filter — determines CALL or PUT based on open vs previous close., CALL if price >= previous close (bullish gap), PUT otherwise.

### Community 83 - "Community 83"
Cohesion: 0.5
Nodes (3): Lightweight Telegram notifier — project-agnostic.  Usage:     from notify import, Send a Telegram message. Returns True on success, False on failure., send()

### Community 86 - "Community 86"
Cohesion: 0.5
Nodes (4): D: 3/19/26 10:30 AM, Selected Bar OHLC Values, Vertical Crosshair at 10:30, Visible OHLC Metrics

### Community 87 - "Community 87"
Cohesion: 0.5
Nodes (4): Right-Side Future Expansion Area, Horizontal Price Line 6625.96, Post Breakout Pullback, Sharp Upside Breakout Around Noon

### Community 89 - "Community 89"
Cohesion: 0.67
Nodes (3): Current SPX Quote 6577.69, Daily Change -28.80 (-0.44%), Last Visible Red Candle

## Ambiguous Edges - Review These
- `SPX put butterfly debit order` → `During-fill option-chain review context`  [AMBIGUOUS]
  data/ToS_examples/chainduringgfill.gif · relation: appears_to_contextualize
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **629 isolated node(s):** `Root conftest — adds tools/ to sys.path so 'notify' is importable in tests.`, `Unit tests for BiasScoreFilter.`, `Build n bars starting at 09:30 ET, incrementing by 1 minute each.`, `Bars that produce strong bullish score: rising price, above OR high.`, `Bars that produce strong bearish score: falling price, below OR low.` (+624 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `SPX put butterfly debit order` and `During-fill option-chain review context`?**
  _Edge tagged AMBIGUOUS (relation: appears_to_contextualize) - confidence is low._
- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `OptionQuote` connect `Community 10` to `Community 0`, `Community 3`, `Community 4`, `Community 5`, `Community 39`, `Community 7`, `Community 43`, `Community 15`, `Community 47`, `Community 17`, `Community 24`, `Community 58`, `Community 28`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `TradeService` connect `Community 10` to `Community 1`, `Community 71`, `Community 9`, `Community 75`, `Community 13`, `Community 47`, `Community 51`, `Community 20`, `Community 85`, `Community 21`, `Community 55`, `Community 53`, `Community 24`, `Community 26`, `Community 59`, `Community 31`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 10` to `Community 1`, `Community 9`, `Community 18`, `Community 19`, `Community 20`, `Community 21`, `Community 24`, `Community 26`, `Community 43`, `Community 51`, `Community 53`, `Community 55`, `Community 56`, `Community 62`, `Community 68`, `Community 74`, `Community 75`, `Community 84`, `Community 85`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `str` (e.g. with `make_chain_data()` and `make_chain_data_with_spread()`) actually correct?**
  _`str` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `make_settings()` (e.g. with `dict` and `ExecutionSettings`) actually correct?**
  _`make_settings()` has 2 INFERRED edges - model-reasoned connections that need verification._