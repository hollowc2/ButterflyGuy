# Graph Report - butterflyguy  (2026-05-13)

## Corpus Check
- 108 files · ~281,819 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1488 nodes · 2546 edges · 108 communities (93 shown, 15 thin omitted)
- Extraction: 71% EXTRACTED · 29% INFERRED · 0% AMBIGUOUS · INFERRED: 726 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0ec1e34d`
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
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 107|Community 107]]

## God Nodes (most connected - your core abstractions)
1. `make_settings()` - 42 edges
2. `make_candidate()` - 42 edges
3. `make_order_manager()` - 41 edges
4. `SimulationEngine` - 39 edges
5. `MinuteBar` - 38 edges
6. `SimulationParams` - 36 edges
7. `ButterflyBuilder` - 36 edges
8. `StrategySettings` - 32 edges
9. `main()` - 32 edges
10. `ButterflySelector` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Compare Synthetic Same Entry Design` --semantically_similar_to--> `Compare Real vs Synthetic Chains`  [INFERRED] [semantically similar]
  docs/superpowers/specs/2026-04-25-compare-synthetic-same-entry-design.md → README.md
- `make_bar()` --calls--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestEma` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestEma` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestEma` --uses--> `SimulationEngine`  [INFERRED]
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

## Communities (108 total, 15 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (72): _drawdown_rule(), _profit_exit_reason(), Simulate intraday using BS pricing, pinned to a pre-selected real entry., Simulate intraday using BS pricing, pinned to a pre-selected real entry., Simulate intraday using BS pricing, pinned to a pre-selected real entry., BaseModel, CollectorSettings, DatabaseSettings (+64 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (54): get_0dte_expiration(), is_market_open(), is_trading_day(), minutes_since_open(), minutes_to_close(), now_eastern(), now_pacific(), Market timezone helpers for 0-DTE trading. (+46 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (47): make_candidate(), make_chain_data_with_oi(), make_chain_data_with_spread(), make_order_manager(), make_quote(), make_settings(), Tests for OrderManager live mark repricing., When the exit ladder times out, it should force-fill at bid (not return None). (+39 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (36): _build_bars(), _build_prev_close(), _build_recent_closes(), _build_vix(), _build_vix_bars(), CsvDataLoader, CSV-based data loader for historical SPX + VIX 1-minute data.  Reads two CSV fil, Loads SPX + VIX 1-minute CSVs and serves DayData objects.      Loads both files (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (34): MinuteBar, OptionQuote, A single option quote from a chain snapshot., _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), _et() (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (37): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (21): day_cache_path(), load_day(), JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).  Sch, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day. (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (32): SPX weekly puts option chain, Bid, ask, volume, and open interest columns, Calls side, Puts side, 20 MAR 26 weekly expiration, Buy 1 SPX 6485 put, Buy 1 SPX 6525 put, Sell 2 SPX 6505 puts (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (16): Async Schwab API client wrapper with retry logic., Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order and return the order ID., Get the status of an order., Cancel an existing order., Fetch 1-minute bars for today (and optionally prior days) from Schwab., Fetch daily OHLCV bars for the given symbol. (+8 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (22): A trade record for tracking entry/exit., TradeRecord, CandidateQueries, DecisionQueries, Database query helpers for all tables., Queries for decision_log table., Queries for tent_boundaries table., Queries for butterfly_candidates table. (+14 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (31): 📈 Backtesting, 🦋 Butterfly Guy, code:yaml (risk:), code:bash (# Skip days where the absolute gap is below 0.25%), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (# Full test suite), code:bash (# Start the SPX stack), code:yaml (entry:) (+23 more)

### Community 11 - "Community 11"
Cohesion: 0.1
Nodes (26): fmt_candidate(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args(), parse_date(), print_day_header() (+18 more)

### Community 12 - "Community 12"
Cohesion: 0.1
Nodes (29): Gap Regime Filter Design, High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Butterfly Guy (+21 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (28): Ask price column, Bid price column, Open interest column, Strike triplet column, Volume column, Bid-ask spread, Liquidity screening, Mark-price fill reference (+20 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (21): ButterflyOrderBuilder, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure.  These tests check th, Realistic SPX butterfly candidate. (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (20): IVModel, Implied volatility model with VIX scaling and skew adjustment., Models implied volatility with VIX scaling and volatility skew., Convert VIX index value to 0-DTE ATM IV estimate.          VIX is the 30-day imp, Compute skew-adjusted IV for a given strike.          OTM puts have elevated IV, Synthetic option chain generator using Black-Scholes + VIX IV model., Minutes until market close on expiration day., Generates a synthetic SPX option chain from spot + VIX. (+12 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (21): compute_tent_boundaries(), fly_bid_value(), fly_settlement_value(), PositionManager, Position value tracking and management., Tracks position value from chain data and manages peak tracking., Reset for a new position. Optionally restore a persisted peak (e.g. after restar, Tracks position value from chain data and manages peak tracking. (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.16
Nodes (15): now_utc(), LiveSpread, OrderManager, Order execution with price ladder logic., Place one butterfly order at limit_price. Wait for fill; cancel if unfilled., Execute entry with price ladder: reprice from live mark each step,         step, Execute exit with reverse price ladder: reprice from live mark each step,, Manages order execution with price ladder and fill monitoring. (+7 more)

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (17): Risk management engine — enforces daily limits and trading rules., Record that a trade was executed., Overwrite realized_pnl in risk state (SET, not ADD).         Used at startup to, Manually sync the trade count in the risk state table.         Used at startup t, Enforces risk constraints before allowing trades., RiskEngine, make_risk_engine(), Tests for the risk engine. (+9 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (18): BaseSettings, AppConfig, OptionChainCollector, Option chain collector — fetches and stores SPX chain snapshots., Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Collects option chain snapshots at regular intervals., Parse Schwab callExpDateMap/putExpDateMap into flat rows., Integration tests for the option chain collector (requires live Schwab token). (+10 more)

### Community 20 - "Community 20"
Cohesion: 0.09
Nodes (15): get_logger(), Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs., Get a structlog logger with optional name., setup_logging(), Prometheus metrics for monitoring., Start the Prometheus metrics HTTP server., start_metrics_server() (+7 more)

### Community 21 - "Community 21"
Cohesion: 0.13
Nodes (11): DbDataLoader, DB-backed data loader for historical SPX + VIX data.  Reads from the live Timesc, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*., Loads SPX + VIX data from TimescaleDB and serves DayData objects.      Connects, Return DayData for *date*, or None if no bars found. (+3 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (9): GapRegimeFilter, Market regime classifier for 0-DTE butterfly parameter dispatch.  Classifies eac, Regime, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.11
Nodes (15): DayResult, DrawdownWindow, Simulate one trading day., Simulate one trading day., Maps Regime → SimulationParams for use with simulate_day_adaptive().      Per-re, Maps Regime → SimulationParams for use with simulate_day_adaptive().      Per-re, RegimeDispatch, Classifies market regime from SPX recent closes and daily VIX level. (+7 more)

### Community 24 - "Community 24"
Cohesion: 0.16
Nodes (16): _dd_schedule_label(), discover_dates(), _find_bar_at(), main(), nearest_snapshot(), parse_args(), _parse_dd_schedule(), _print_comparison_table() (+8 more)

### Community 25 - "Community 25"
Cohesion: 0.1
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 26 - "Community 26"
Cohesion: 0.22
Nodes (17): StrategySettings, ButterflyBuilder, Builds and scores butterfly spreads from an option chain snapshot., Builds and scores butterfly spreads from an option chain snapshot., make_chain(), make_quote(), Tests for the butterfly builder scanner., Generate a synthetic chain of call quotes around spot. (+9 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (20): Bid and ask quote columns, Butterfly chain rows expose bid/ask values usable for mid-price marking, Butterfly spread mode, Highlighted active trade region, Calls side, Option Chain panel, Puts side, POS marker (+12 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (17): main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date.  Replicates the synthet, Select the best butterfly candidate for a single wing width., Select the best butterfly candidate for a single wing width., Select the best butterfly candidate for a single wing width., Cross-width selection. (+9 more)

### Community 29 - "Community 29"
Cohesion: 0.11
Nodes (16): 1. `strategy/gap_regime_filter.py` (new file), 2. `core/config.py` — `EntrySettings`, 3. Live path, 4. Backtest path (`run_backtest_db.py`), code:python (@dataclass), code:python (bull_call_bias: bool = False   # Override to CALL in BULL re), code:python (if self.gap_regime_filter:), code:block5 (--bull-call-bias      Override to CALL in BULL regime on gap) (+8 more)

### Community 30 - "Community 30"
Cohesion: 0.16
Nodes (12): _date_range(), ParameterSweeper, Parameter sweep engine for backtesting across date ranges., Runs grid search over simulation parameters across a date range., Run full parameter sweep. Returns a polars DataFrame., SweepConfig, Single-day simulation engine using synthetic option chains., SimulationParams (+4 more)

### Community 31 - "Community 31"
Cohesion: 0.14
Nodes (11): ButterflySelector, Butterfly selector — picks the best candidate from a list., Selects the best butterfly candidate., Select the candidate whose cost is closest to its max_cost_per_width., Select the best butterfly candidate.          When `target_center` is provided (, Select the candidate whose cost is closest to its max_cost_per_width., Select the farthest OTM candidate from the already-valid candidate set., make_candidate() (+3 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (6): ChainQueries, Queries for option_chain_snapshots table., Bulk insert option chain snapshot rows using COPY., Queries for trades table., TradeQueries, dict

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (8): DatabasePool, Async database connection pool using asyncpg., Manages an asyncpg connection pool for TimescaleDB., Create the connection pool., DailyBarQueries, Queries for daily_bars table., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict., Return the last `days` daily closes in chronological order (oldest first).

### Community 34 - "Community 34"
Cohesion: 0.12
Nodes (16): get_prev_close(), get_vix_at(), get_vix_prev_close(), load_bars_from_db(), load_date_data(), Return the last spot price at or before 16:00 ET on the previous trading day., Return the last spot price at or before 16:00 ET on the previous trading day., Return the last spot price at or before 16:00 ET on the previous trading day. (+8 more)

### Community 35 - "Community 35"
Cohesion: 0.12
Nodes (15): ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log n, load_chains_from_db(), load_entry_chains(), load_monitoring_chains(), merge_chains(), Load only the entry-window snapshots (09:30–10:45 ET) for butterfly selection., Load only the entry-window snapshots (09:30–10:45 ET) for butterfly selection. (+7 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (14): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ), Common Commands (+6 more)

### Community 37 - "Community 37"
Cohesion: 0.17
Nodes (16): 20 Wide Butterfly Candidate Rows, At The Money Strike Region, Bid And Ask Columns, Calls Side Option Chain Table, Entry Window Selection Context, Highlighted Candidate Band Near Underlying Price, 20 Wide Fly Chain At Entry Window Screenshot, 20 Mar 2026 Weekly Expiration (+8 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (15): Butterfly strike triplets, Calls side, Call butterfly rows in entry window, Entry-window highlighted rows, Put butterfly rows in entry window, 20 MAR 26 weekly expiration, Near-money butterfly candidates, Option chain spread: Butterfly (+7 more)

### Community 39 - "Community 39"
Cohesion: 0.2
Nodes (8): BiasScoreFilter, Scores market direction using 4 signals; returns CALL, PUT, or None., Bars that produce strong bullish score: rising price, above OR high., Bars that produce strong bearish score: falling price, below OR low., OR signal is ±2 — alone it meets the ±2 threshold., Gap signal only contributes +1, below the ±2 threshold., Conflicting signals that cancel out → None., TestBiasScore

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (13): 1. `SimulationEngine.simulate_day_from_entry()`, 2. `run_backtest_db.py` changes, 3. Output, Architecture, code:block2 (--compare-synthetic-same-entry   Run a BS-only intraday pass), code:python (same_entry_result = None), code:block4 (.venv/bin/python -m butterfly_guy.scripts.run_backtest_db --), Design: --compare-synthetic-same-entry Mode (+5 more)

### Community 41 - "Community 41"
Cohesion: 0.13
Nodes (14): 1. New CLI flag, 2. New helper function, 3. Modified `run_single` per-date loop, 4. Output, Approach, Changes, code:block1 (--compare-synthetic   Run a second synthetic-only pass and p), code:python (def _force_synthetic_for_date(date: dt.date):) (+6 more)

### Community 42 - "Community 42"
Cohesion: 0.18
Nodes (7): BacktestDataLoader, Backtest data loader — fetches SPX 1-min bars and VIX from Polygon.io., Load all data needed for a single backtest day., Loads historical data from Polygon.io for backtesting., Fetch SPX 1-minute bars for a given date from Polygon., Fetch VIX close for a given date from Polygon., Fetch the actual previous trading day's SPX close for a given date.

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (14): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets., Return bucket-height estimates from a Gaussian KDE fit. (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.22
Nodes (12): chain_cache_path(), load_chain_day(), nearest_snapshot(), Real option chain cache — per-day JSON snapshots from the live collector.  Forma, Load all chain snapshots for a day.      Returns dict of UTC datetime -> list[Op, Return quotes from the most recent snapshot at or before bar_ts., Append one chain snapshot to the day's cache file.      Called by the collector, save_snapshot() (+4 more)

### Community 45 - "Community 45"
Cohesion: 0.23
Nodes (6): make_bar(), make_pre_entry_bars(), Unit tests for BiasScoreFilter., Build n bars starting at 09:30 ET, incrementing by 1 minute each., TestComputeOr, TestComputeVwap

### Community 46 - "Community 46"
Cohesion: 0.21
Nodes (12): load_config(), Load configuration from YAML file and environment variables., Load configuration from YAML file and environment variables., Tests for configuration loading., Config values from YAML should override defaults., Loading config with no files should return sensible defaults., test_allow_live_trading_requires_explicit_env(), test_database_password_falls_back_to_compose_env() (+4 more)

### Community 47 - "Community 47"
Cohesion: 0.28
Nodes (12): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+4 more)

### Community 48 - "Community 48"
Cohesion: 0.21
Nodes (13): 15-wide fly chain at entry window screenshot, 15-wide butterfly strike rows, Bid/ask color coding, Butterfly spread mode, Calls side, Entry-window candidate region, 20 MAR 26 weekly expiration, Liquidity metrics (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.29
Nodes (8): DayData, Runs full strategy on a single day using synthetic options., Runs full strategy on a single day using synthetic options., SimulationEngine, use_bias_filter=True should produce a trade result (direction set by bias)., direction_override takes precedence over use_bias_filter., When bias filter always returns None, day should be untraded., TestEngineIntegration

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (3): Backtest data loader using yfinance (free, no API key required).  Uses hourly ba, Loads historical SPX + VIX data via yfinance. No API key required., YFinanceDataLoader

### Community 51 - "Community 51"
Cohesion: 0.18
Nodes (11): _force_synthetic_for_date(), _patch_chain_cache(), Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable. (+3 more)

### Community 52 - "Community 52"
Cohesion: 0.2
Nodes (10): BUTTERFLYGUY, connectivity visual association, precision visual association, technology visual association, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.2
Nodes (4): Queries for daily_risk_state table., Sum of realized PnL for the rolling 7-day window (closed trades only)., PnL of the last N closed trades (most recent first), for consecutive loss detect, RiskQueries

### Community 54 - "Community 54"
Cohesion: 0.29
Nodes (3): DiscordNotifier, Discord webhook notifications., Sends trading notifications to Discord via webhook.

### Community 55 - "Community 55"
Cohesion: 0.2
Nodes (9): code:python ("""Tests for _print_comparison_table aggregate stats."""), code:bash (cd /opt/butterflyguy && .venv/bin/python -m pytest tests/tes), code:python (def _print_comparison_table(day_rows: list[dict]) -> None:), code:bash (cd /opt/butterflyguy && .venv/bin/python -m pytest tests/tes), code:bash (cd /opt/butterflyguy && git add tests/test_comparison_stats.), code:bash (cd /opt/butterflyguy && .venv/bin/python -m butterfly_guy.sc), Real vs Synthetic Comparison Stats Implementation Plan, Task 1: Add stats block to `_print_comparison_table` (+1 more)

### Community 56 - "Community 56"
Cohesion: 0.25
Nodes (7): ButterflyCandidate, fly_mark_value(), Pydantic models for option data and trade records., Butterfly value at mark: lower.mark - 2*center.mark + upper.mark., A butterfly spread candidate identified by the scanner., O(N*W) scan: for each center strike within spot_range, for each wing_width,, O(N*W) scan: for each center strike within spot_range, for each wing_width,

### Community 57 - "Community 57"
Cohesion: 0.28
Nodes (7): EntryDecision, find_entry_candidate(), Find best candidate in the 10:00–10:30 ET window, returning full decision contex, determine_direction(), DirectionFilter, Direction filter — determines CALL or PUT based on open vs previous close., CALL if price >= previous close (bullish gap), PUT otherwise.

### Community 58 - "Community 58"
Cohesion: 0.36
Nodes (7): Trade service — orchestrates entry flow., Return the first regular-session open for the requested Eastern date., _session_open_from_intraday_candles(), _candle(), test_session_open_ignores_premarket_and_missing_open_values(), test_session_open_returns_none_when_no_regular_session_bar_exists(), test_session_open_uses_first_regular_session_bar_for_requested_date()

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (8): Butterfly Guy — Implementation Plan, Context, Phase 1: Infrastructure + TimescaleDB + Option Chain Collector, Phase 2: Butterfly Scanner, Phase 3: Paper Trading Execution, Phase 4: Profit Management State Machine, Phase 5: Synthetic Engine + Backtesting, Phase 6: Dashboard + Monitoring + Discord

### Community 60 - "Community 60"
Cohesion: 0.22
Nodes (8): code:block1 (═══════════════════════════════════════════════════════════), code:bash (.venv/bin/python -m butterfly_guy.scripts.run_backtest_db --), Goal, Implementation, Real vs Synthetic Backtest Comparison — Design Spec, Run Command, Scope, Stats Block

### Community 61 - "Community 61"
Cohesion: 0.22
Nodes (9): Bid Ask Quote, Bottom Time Axis, Candlestick Price Chart, Right Side Price Axis, SPX Symbol, 10 Minute Timeframe, Thinkorswim Side Panels, 3 Day Chart Range (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 63 - "Community 63"
Cohesion: 0.38
Nodes (5): _compute_or(), _compute_vwap(), _ema(), Multi-signal directional bias filter for 0-DTE butterfly entries., Compute bias score from 4 signals:           gap          : +1 if entry_close >

### Community 65 - "Community 65"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 66 - "Community 66"
Cohesion: 0.29
Nodes (7): _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday

### Community 67 - "Community 67"
Cohesion: 0.29
Nodes (7): print_thinkback_checklist(), Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist.

### Community 68 - "Community 68"
Cohesion: 0.33
Nodes (7): Synthetic vs Real Backtest Comparison Design, Comparison Stats Implementation Plan, Real vs Synthetic Aggregate Stats Design, Compare Synthetic Same Entry Design, Compare Real vs Synthetic Chains, DB Backtesting, Phase 5 Synthetic Engine and Backtesting

### Community 69 - "Community 69"
Cohesion: 0.33
Nodes (5): Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter.

### Community 70 - "Community 70"
Cohesion: 0.4
Nodes (3): Classify regime then delegate to simulate_day() with matching params.          R, Classify regime then delegate to simulate_day() with matching params.          R, Classify regime then delegate to simulate_day() with matching params.          R

### Community 72 - "Community 72"
Cohesion: 0.7
Nodes (4): _parse_for_asset(), test_ndx_backtest_drawdown_defaults_match_live_config(), test_spx_backtest_drawdown_defaults_match_live_config(), test_xsp_backtest_drawdown_defaults_match_live_config()

### Community 73 - "Community 73"
Cohesion: 0.5
Nodes (3): Lightweight Telegram notifier — project-agnostic.  Usage:     from notify import, Send a Telegram message. Returns True on success, False on failure., send()

### Community 74 - "Community 74"
Cohesion: 0.5
Nodes (4): Resolve the DB connection string for local backtests.      Backtests follow the, Resolve the DB connection string for local backtests.      Backtests follow the, Resolve the DB connection string for local backtests.      Backtests follow the, resolve_db_dsn()

### Community 75 - "Community 75"
Cohesion: 0.5
Nodes (4): get_recent_closes(), Up to *n* daily closes strictly before *date*, chronological order., Up to *n* daily closes strictly before *date*, chronological order., Up to *n* daily closes strictly before *date*, chronological order.

### Community 76 - "Community 76"
Cohesion: 0.5
Nodes (4): D: 3/19/26 10:30 AM, Selected Bar OHLC Values, Vertical Crosshair at 10:30, Visible OHLC Metrics

### Community 77 - "Community 77"
Cohesion: 0.5
Nodes (4): Right-Side Future Expansion Area, Horizontal Price Line 6625.96, Post Breakout Pullback, Sharp Upside Breakout Around Noon

### Community 79 - "Community 79"
Cohesion: 0.67
Nodes (3): Current SPX Quote 6577.69, Daily Change -28.80 (-0.44%), Last Visible Red Candle

## Ambiguous Edges - Review These
- `SPX put butterfly debit order` → `During-fill option-chain review context`  [AMBIGUOUS]
  data/ToS_examples/chainduringgfill.gif · relation: appears_to_contextualize
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **571 isolated node(s):** `Root conftest — adds tools/ to sys.path so 'notify' is importable in tests.`, `Unit tests for BiasScoreFilter.`, `Build n bars starting at 09:30 ET, incrementing by 1 minute each.`, `Bars that produce strong bullish score: rising price, above OR high.`, `Bars that produce strong bearish score: falling price, below OR low.` (+566 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `SPX put butterfly debit order` and `During-fill option-chain review context`?**
  _Edge tagged AMBIGUOUS (relation: appears_to_contextualize) - confidence is low._
- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `OptionQuote` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`, `Community 35`, `Community 5`, `Community 9`, `Community 11`, `Community 44`, `Community 15`, `Community 16`, `Community 21`, `Community 56`, `Community 57`, `Community 26`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `Community 56` to `Community 0`, `Community 2`, `Community 4`, `Community 9`, `Community 14`, `Community 16`, `Community 49`, `Community 17`, `Community 23`, `Community 57`, `Community 26`, `Community 30`, `Community 31`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 9` to `Community 32`, `Community 33`, `Community 56`, `Community 8`, `Community 46`, `Community 14`, `Community 17`, `Community 18`, `Community 19`, `Community 20`, `Community 53`, `Community 54`, `Community 23`, `Community 22`, `Community 57`, `Community 26`, `Community 31`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `make_settings()` (e.g. with `dict` and `ExecutionSettings`) actually correct?**
  _`make_settings()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `str` (e.g. with `make_chain_data()` and `make_chain_data_with_spread()`) actually correct?**
  _`str` has 41 INFERRED edges - model-reasoned connections that need verification._