# Graph Report - .  (2026-05-07)

## Corpus Check
- 121 files · ~279,912 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1193 nodes · 2193 edges · 86 communities (70 shown, 16 thin omitted)
- Extraction: 69% EXTRACTED · 31% INFERRED · 0% AMBIGUOUS · INFERRED: 679 edges (avg confidence: 0.7)
- Token cost: 8,165 input · 30,495 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Runtime Configs|Runtime Configs]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Runtime Configs|Runtime Configs]]
- [[_COMMUNITY_Runtime Configs|Runtime Configs]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Schwab API|Schwab API]]
- [[_COMMUNITY_Schwab API|Schwab API]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Backtest Research|Backtest Research]]
- [[_COMMUNITY_Runtime Configs|Runtime Configs]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Backtest Research|Backtest Research]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Risk Controls|Risk Controls]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Strategy Selection|Strategy Selection]]
- [[_COMMUNITY_Strategy Selection|Strategy Selection]]
- [[_COMMUNITY_Strategy Selection|Strategy Selection]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Init Queries Decisionqueries|Init Queries Decisionqueries]]
- [[_COMMUNITY_Logging Metrics Main|Logging Metrics Main]]
- [[_COMMUNITY_Strategy Selection|Strategy Selection]]
- [[_COMMUNITY_Backtest Research|Backtest Research]]
- [[_COMMUNITY_Backtest Research|Backtest Research]]
- [[_COMMUNITY_Strategy Selection|Strategy Selection]]
- [[_COMMUNITY_Notify Discordnotifier Post|Notify Discordnotifier Post]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Risk Controls|Risk Controls]]
- [[_COMMUNITY_Database Layer|Database Layer]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Strategy Selection|Strategy Selection]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Strategy Selection|Strategy Selection]]
- [[_COMMUNITY_Backtest Research|Backtest Research]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Direction Filter Call|Direction Filter Call]]
- [[_COMMUNITY_Notifications|Notifications]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Ohlc Selected Bar|Ohlc Selected Bar]]
- [[_COMMUNITY_Breakout Post Pullback|Breakout Post Pullback]]
- [[_COMMUNITY_Option Chain Data|Option Chain Data]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Schwab API|Schwab API]]
- [[_COMMUNITY_Schwab API|Schwab API]]
- [[_COMMUNITY_Strategy Selection|Strategy Selection]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Premarket Overnight Session|Premarket Overnight Session]]
- [[_COMMUNITY_Order Execution|Order Execution]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Test Coverage|Test Coverage]]
- [[_COMMUNITY_Price Volume Weighted|Price Volume Weighted]]
- [[_COMMUNITY_High Low Opening|High Low Opening]]
- [[_COMMUNITY_Exponential Moving Average|Exponential Moving Average]]
- [[_COMMUNITY_Regular Market Open|Regular Market Open]]

## God Nodes (most connected - your core abstractions)
1. `make_settings()` - 42 edges
2. `make_candidate()` - 42 edges
3. `make_order_manager()` - 41 edges
4. `MinuteBar` - 38 edges
5. `SimulationEngine` - 36 edges
6. `ButterflyBuilder` - 34 edges
7. `SimulationParams` - 32 edges
8. `main()` - 32 edges
9. `StrategySettings` - 30 edges
10. `OptionQuote` - 28 edges

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

## Communities (86 total, 16 thin omitted)

### Community 0 - "Runtime Configs"
Cohesion: 0.07
Nodes (47): BaseModel, CollectorSettings, DatabaseSettings, EntrySettings, ExecutionSettings, MonitoringSettings, ProfitManagementSettings, QuoteQualitySettings (+39 more)

### Community 1 - "Test Coverage"
Cohesion: 0.06
Nodes (48): get_0dte_expiration(), get_time_regime(), is_market_open(), is_trading_day(), minutes_since_open(), minutes_to_close(), now_eastern(), now_pacific() (+40 more)

### Community 2 - "Order Execution"
Cohesion: 0.06
Nodes (32): DbDataLoader, DB-backed data loader for historical SPX + VIX data.  Reads from the live Timesc, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*., Loads SPX + VIX data from TimescaleDB and serves DayData objects.      Connects, Return DayData for *date*, or None if no bars found. (+24 more)

### Community 3 - "Test Coverage"
Cohesion: 0.07
Nodes (41): _build_bars(), _build_prev_close(), _build_recent_closes(), _build_vix(), _build_vix_bars(), CsvDataLoader, CSV-based data loader for historical SPX + VIX 1-minute data.  Reads two CSV fil, Loads SPX + VIX 1-minute CSVs and serves DayData objects.      Loads both files (+33 more)

### Community 4 - "Order Execution"
Cohesion: 0.15
Nodes (47): make_candidate(), make_chain_data_with_oi(), make_chain_data_with_spread(), make_order_manager(), make_quote(), make_settings(), Tests for OrderManager live mark repricing., When the exit ladder times out, it should force-fill at bid (not return None). (+39 more)

### Community 5 - "Runtime Configs"
Cohesion: 0.06
Nodes (38): BaseSettings, AppConfig, load_config(), Load configuration from YAML file and environment variables., OptionChainCollector, Option chain collector — fetches and stores SPX chain snapshots., Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Collects option chain snapshots at regular intervals. (+30 more)

### Community 6 - "Runtime Configs"
Cohesion: 0.12
Nodes (33): StrategySettings, ButterflyCandidate, A butterfly spread candidate identified by the scanner., Select the best butterfly candidate for a single wing width., Cross-width selection., select_for_width(), select_live_width(), EntryDecision (+25 more)

### Community 7 - "Option Chain Data"
Cohesion: 0.08
Nodes (37): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+29 more)

### Community 8 - "Schwab API"
Cohesion: 0.07
Nodes (21): day_cache_path(), load_day(), JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).  Sch, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day. (+13 more)

### Community 9 - "Schwab API"
Cohesion: 0.11
Nodes (25): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), _et(), load_bars_from_db(), load_chains_from_db(), main() (+17 more)

### Community 10 - "Order Execution"
Cohesion: 0.07
Nodes (32): SPX weekly puts option chain, Bid, ask, volume, and open interest columns, Calls side, Puts side, 20 MAR 26 weekly expiration, Buy 1 SPX 6485 put, Buy 1 SPX 6525 put, Sell 2 SPX 6505 puts (+24 more)

### Community 11 - "Order Execution"
Cohesion: 0.08
Nodes (16): Async Schwab API client wrapper with retry logic., Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order and return the order ID., Get the status of an order., Cancel an existing order., Fetch 1-minute bars for today (and optionally prior days) from Schwab., Fetch daily OHLCV bars for the given symbol. (+8 more)

### Community 12 - "Test Coverage"
Cohesion: 0.12
Nodes (16): MinuteBar, Fetch today's 1-min bars from Schwab and run BiasScoreFilter., BiasScoreFilter, Scores market direction using 4 signals; returns CALL, PUT, or None., make_bar(), make_pre_entry_bars(), Unit tests for BiasScoreFilter., Bars that produce strong bullish score: rising price, above OR high. (+8 more)

### Community 13 - "Backtest Research"
Cohesion: 0.11
Nodes (26): _dd_schedule_label(), discover_dates(), _find_bar_at(), _force_synthetic_for_date(), main(), merge_chains(), nearest_snapshot(), parse_args() (+18 more)

### Community 14 - "Runtime Configs"
Cohesion: 0.1
Nodes (29): Gap Regime Filter Design, High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Butterfly Guy (+21 more)

### Community 15 - "Option Chain Data"
Cohesion: 0.08
Nodes (28): Ask price column, Bid price column, Open interest column, Strike triplet column, Volume column, Bid-ask spread, Liquidity screening, Mark-price fill reference (+20 more)

### Community 16 - "Order Execution"
Cohesion: 0.13
Nodes (21): ButterflyOrderBuilder, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure.  These tests check th, Realistic SPX butterfly candidate. (+13 more)

### Community 17 - "Backtest Research"
Cohesion: 0.11
Nodes (20): IVModel, Implied volatility model with VIX scaling and skew adjustment., Models implied volatility with VIX scaling and volatility skew., Convert VIX index value to 0-DTE ATM IV estimate.          VIX is the 30-day imp, Compute skew-adjusted IV for a given strike.          OTM puts have elevated IV, Synthetic option chain generator using Black-Scholes + VIX IV model., Minutes until market close on expiration day., Generates a synthetic SPX option chain from spot + VIX. (+12 more)

### Community 18 - "Test Coverage"
Cohesion: 0.14
Nodes (18): DayData, Backtest data loader — fetches SPX 1-min bars and VIX from Polygon.io., SweepConfig, DrawdownWindow, Runs full strategy on a single day using synthetic options., SimulationEngine, SimulationParams, Market regime classifier for 0-DTE butterfly parameter dispatch.  Classifies eac (+10 more)

### Community 19 - "Test Coverage"
Cohesion: 0.1
Nodes (16): DayResult, _drawdown_rule(), Single-day simulation engine using synthetic option chains., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry., Classify regime then delegate to simulate_day() with matching params.          R, Maps Regime → SimulationParams for use with simulate_day_adaptive().      Per-re, RegimeDispatch (+8 more)

### Community 20 - "Risk Controls"
Cohesion: 0.11
Nodes (17): Risk management engine — enforces daily limits and trading rules., Record that a trade was executed., Overwrite realized_pnl in risk state (SET, not ADD).         Used at startup to, Manually sync the trade count in the risk state table.         Used at startup t, Enforces risk constraints before allowing trades., RiskEngine, make_risk_engine(), Tests for the risk engine. (+9 more)

### Community 21 - "Order Execution"
Cohesion: 0.11
Nodes (20): Bid and ask quote columns, Butterfly chain rows expose bid/ask values usable for mid-price marking, Butterfly spread mode, Highlighted active trade region, Calls side, Option Chain panel, Puts side, POS marker (+12 more)

### Community 22 - "Test Coverage"
Cohesion: 0.18
Nodes (7): GapRegimeFilter, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct, TestSkipBeforeOverride

### Community 23 - "Option Chain Data"
Cohesion: 0.2
Nodes (14): fmt_candidate(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args(), parse_date(), print_day_header() (+6 more)

### Community 24 - "Option Chain Data"
Cohesion: 0.13
Nodes (6): ChainQueries, Queries for option_chain_snapshots table., Bulk insert option chain snapshot rows using COPY., Queries for trades table., TradeQueries, dict

### Community 25 - "Strategy Selection"
Cohesion: 0.17
Nodes (16): 20 Wide Butterfly Candidate Rows, At The Money Strike Region, Bid And Ask Columns, Calls Side Option Chain Table, Entry Window Selection Context, Highlighted Candidate Band Near Underlying Price, 20 Wide Fly Chain At Entry Window Screenshot, 20 Mar 2026 Weekly Expiration (+8 more)

### Community 26 - "Strategy Selection"
Cohesion: 0.13
Nodes (15): Butterfly strike triplets, Calls side, Call butterfly rows in entry window, Entry-window highlighted rows, Put butterfly rows in entry window, 20 MAR 26 weekly expiration, Near-money butterfly candidates, Option chain spread: Butterfly (+7 more)

### Community 27 - "Strategy Selection"
Cohesion: 0.17
Nodes (13): main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date.  Replicates the synthet, Walk the 10:00-10:30 ET window and record every bar's entry signals., scan_entry_window(), O(N*W) butterfly construction and scoring engine., Return (widths, sigma_fractions) for the active VIX bucket.      Buckets are pro (+5 more)

### Community 28 - "Option Chain Data"
Cohesion: 0.18
Nodes (9): Pydantic models for option data and trade records., A trade record for tracking entry/exit., TradeRecord, main(), Trade service — orchestrates entry flow., Orchestrates the full entry/exit trading flow., Parse Schwab chain response into OptionQuote objects., Full entry flow: time → balance → risk → direction (once) → retry loop (re-scan (+1 more)

### Community 29 - "Option Chain Data"
Cohesion: 0.15
Nodes (8): PositionManager, Tracks position value from chain data and manages peak tracking., Reset for a new position. Optionally restore a persisted peak (e.g. after restar, PositionService, Position monitoring service — runs state machine on open positions., Monitors open positions and manages exits via the profit state machine., Record trade exit metrics and update risk engine., Extract the three butterfly leg quotes from the chain for position valuation.

### Community 30 - "Option Chain Data"
Cohesion: 0.22
Nodes (12): chain_cache_path(), load_chain_day(), nearest_snapshot(), Real option chain cache — per-day JSON snapshots from the live collector.  Forma, Load all chain snapshots for a day.      Returns dict of UTC datetime -> list[Op, Return quotes from the most recent snapshot at or before bar_ts., Append one chain snapshot to the day's cache file.      Called by the collector, save_snapshot() (+4 more)

### Community 31 - "Init Queries Decisionqueries"
Cohesion: 0.14
Nodes (7): CandidateQueries, DecisionQueries, Database query helpers for all tables., Queries for decision_log table., Queries for tent_boundaries table., Queries for butterfly_candidates table., TentQueries

### Community 32 - "Logging Metrics Main"
Cohesion: 0.15
Nodes (10): get_logger(), Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs., Get a structlog logger with optional name., setup_logging(), Prometheus metrics for monitoring., Start the Prometheus metrics HTTP server., start_metrics_server() (+2 more)

### Community 33 - "Strategy Selection"
Cohesion: 0.21
Nodes (13): 15-wide fly chain at entry window screenshot, 15-wide butterfly strike rows, Bid/ask color coding, Butterfly spread mode, Calls side, Entry-window candidate region, 20 MAR 26 weekly expiration, Liquidity metrics (+5 more)

### Community 34 - "Backtest Research"
Cohesion: 0.21
Nodes (6): BacktestDataLoader, Load all data needed for a single backtest day., Loads historical data from Polygon.io for backtesting., Fetch SPX 1-minute bars for a given date from Polygon., Fetch VIX close for a given date from Polygon., Fetch the actual previous trading day's SPX close for a given date.

### Community 35 - "Backtest Research"
Cohesion: 0.21
Nodes (3): Backtest data loader using yfinance (free, no API key required).  Uses hourly ba, Loads historical SPX + VIX data via yfinance. No API key required., YFinanceDataLoader

### Community 36 - "Strategy Selection"
Cohesion: 0.2
Nodes (10): BUTTERFLYGUY, connectivity visual association, precision visual association, technology visual association, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background (+2 more)

### Community 37 - "Notify Discordnotifier Post"
Cohesion: 0.29
Nodes (3): DiscordNotifier, Discord webhook notifications., Sends trading notifications to Discord via webhook.

### Community 38 - "Order Execution"
Cohesion: 0.2
Nodes (10): get_prev_close(), get_recent_closes(), get_vix_at(), get_vix_prev_close(), load_bars_from_db(), load_date_data(), Return the last spot price at or before 16:00 ET on the previous trading day., Up to *n* daily closes strictly before *date*, chronological order. (+2 more)

### Community 39 - "Option Chain Data"
Cohesion: 0.27
Nodes (9): ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log n, OptionQuote, A single option quote from a chain snapshot., load_chains_from_db(), load_entry_chains(), load_monitoring_chains(), Load only the entry-window snapshots (09:30–10:45 ET) for butterfly selection. (+1 more)

### Community 40 - "Risk Controls"
Cohesion: 0.2
Nodes (4): Queries for daily_risk_state table., Sum of realized PnL for the rolling 7-day window (closed trades only)., PnL of the last N closed trades (most recent first), for consecutive loss detect, RiskQueries

### Community 41 - "Database Layer"
Cohesion: 0.22
Nodes (4): DatabasePool, Async database connection pool using asyncpg., Manages an asyncpg connection pool for TimescaleDB., Create the connection pool.

### Community 42 - "Option Chain Data"
Cohesion: 0.22
Nodes (9): Bid Ask Quote, Bottom Time Axis, Candlestick Price Chart, Right Side Price Axis, SPX Symbol, 10 Minute Timeframe, Thinkorswim Side Panels, 3 Day Chart Range (+1 more)

### Community 43 - "Strategy Selection"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 45 - "Test Coverage"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 46 - "Order Execution"
Cohesion: 0.29
Nodes (4): DailyBarQueries, Queries for daily_bars table., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict., Return the last `days` daily closes in chronological order (oldest first).

### Community 47 - "Strategy Selection"
Cohesion: 0.38
Nodes (5): _compute_or(), _compute_vwap(), _ema(), Multi-signal directional bias filter for 0-DTE butterfly entries., Compute bias score from 4 signals:           gap          : +1 if entry_close >

### Community 48 - "Backtest Research"
Cohesion: 0.33
Nodes (7): Synthetic vs Real Backtest Comparison Design, Comparison Stats Implementation Plan, Real vs Synthetic Aggregate Stats Design, Compare Synthetic Same Entry Design, Compare Real vs Synthetic Chains, DB Backtesting, Phase 5 Synthetic Engine and Backtesting

### Community 51 - "Direction Filter Call"
Cohesion: 0.4
Nodes (3): determine_direction(), Direction filter — determines CALL or PUT based on open vs previous close., CALL if price >= previous close (bullish gap), PUT otherwise.

### Community 52 - "Notifications"
Cohesion: 0.5
Nodes (3): Lightweight Telegram notifier — project-agnostic.  Usage:     from notify import, Send a Telegram message. Returns True on success, False on failure., send()

### Community 53 - "Test Coverage"
Cohesion: 0.5
Nodes (4): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets.

### Community 54 - "Ohlc Selected Bar"
Cohesion: 0.5
Nodes (4): D: 3/19/26 10:30 AM, Selected Bar OHLC Values, Vertical Crosshair at 10:30, Visible OHLC Metrics

### Community 55 - "Breakout Post Pullback"
Cohesion: 0.5
Nodes (4): Right-Side Future Expansion Area, Horizontal Price Line 6625.96, Post Breakout Pullback, Sharp Upside Breakout Around Noon

### Community 57 - "Option Chain Data"
Cohesion: 0.67
Nodes (3): Current SPX Quote 6577.69, Daily Change -28.80 (-0.44%), Last Visible Red Candle

## Ambiguous Edges - Review These
- `SPX put butterfly debit order` → `During-fill option-chain review context`  [AMBIGUOUS]
  data/ToS_examples/chainduringgfill.gif · relation: appears_to_contextualize
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **375 isolated node(s):** `Root conftest — adds tools/ to sys.path so 'notify' is importable in tests.`, `Unit tests for BiasScoreFilter.`, `Build n bars starting at 09:30 ET, incrementing by 1 minute each.`, `Bars that produce strong bullish score: rising price, above OR high.`, `Bars that produce strong bearish score: falling price, below OR low.` (+370 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `SPX put butterfly debit order` and `During-fill option-chain review context`?**
  _Edge tagged AMBIGUOUS (relation: appears_to_contextualize) - confidence is low._
- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `OptionQuote` connect `Option Chain Data` to `Runtime Configs`, `Order Execution`, `Order Execution`, `Runtime Configs`, `Option Chain Data`, `Schwab API`, `Backtest Research`, `Option Chain Data`, `Option Chain Data`, `Option Chain Data`, `Option Chain Data`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `main()` connect `Option Chain Data` to `Logging Metrics Main`, `Test Coverage`, `Order Execution`, `Runtime Configs`, `Notify Discordnotifier Post`, `Runtime Configs`, `Risk Controls`, `Database Layer`, `Order Execution`, `Order Execution`, `Order Execution`, `Test Coverage`, `Test Coverage`, `Risk Controls`, `Test Coverage`, `Option Chain Data`, `Option Chain Data`, `Init Queries Decisionqueries`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `TradeService` connect `Option Chain Data` to `Order Execution`, `Runtime Configs`, `Runtime Configs`, `Option Chain Data`, `Notify Discordnotifier Post`, `Order Execution`, `Test Coverage`, `Test Coverage`, `Risk Controls`, `Test Coverage`, `Option Chain Data`, `Init Queries Decisionqueries`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `make_settings()` (e.g. with `dict` and `ExecutionSettings`) actually correct?**
  _`make_settings()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 38 inferred relationships involving `str` (e.g. with `make_chain_data()` and `make_chain_data_with_spread()`) actually correct?**
  _`str` has 38 INFERRED edges - model-reasoned connections that need verification._