# Graph Report - Butterflyguy  (2026-07-23)

## Corpus Check
- 221 files · ~236,838 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3548 nodes · 8712 edges · 171 communities (159 shown, 12 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 851 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4bf1f8cf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_order_manager.py
- OptionQuote
- run_backtest_db.py
- _print_pnl_histogram
- ButterflyCandidate
- ButterflyChartSpec
- DiscordNotifier
- Typical workflow
- 4. Detailed findings
- test_black_scholes.py
- Domain Model and Ingestion Boundaries
- forex_calendar.py
- resolve_db_dsn
- _assert_broker_state_matches_db
- discover_options_strategy.py
- MarketSnapshot
- OrderManager
- .record_trade
- AtomicSnapshotStore
- _patch_chain_cache
- load_config
- report.py
- daily_reset_loop
- load_entry_chains
- eod_chart_loop
- load_date_data
- load_monitoring_chains
- candidatectl.py
- entry_loop
- EquityScanSettings
- MinuteBar
- evaluator.py
- TradeQueries
- equity_trade_chart.py
- Database Compatibility
- Width Selection
- reports/daily_report_card.py
- feed.py
- ButterflyOrderBuilder
- scanner.py
- test_synthetic_chain.py
- ProfitStateMachine
- TradeService
- daily_report_card_format.py
- report_exit_mark_parity.py
- resolve_wing_widths_for_vix
- ButterflySelector
- Behavioral Specification
- DbDataLoader
- BacktestDataLoader
- StrategySettings
- health_monitor.py
- ._session_open_price
- _print_same_entry_comparison_table
- main
- run_morning_scan.py
- ._wait_for_fill
- str
- ._bias_direction
- .get_recent_closed_pnls
- simulation_engine.py
- HttpMarketDataProvider
- select_live_width
- news.py
- ._record_exit_metrics
- ._extract_quotes
- ._parse_chain_to_quotes
- performance_chart.py
- print_thinkback_checklist
- volume.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Butterfly Guy
- SchwabDataLoader
- chain_cache.py
- GapRegimeFilter
- run_entry_analysis.py
- ChainDay
- ._exit_mark_parity_report
- ._record_monitoring_leg_quotes
- is_market_open
- black_scholes.py
- 2. Other external and public sources
- SnapshotUnavailableError
- .bulk_upsert
- ReadOnlySchwabMarketDataClient
- test_weekend_review.py
- ButterflyGuy Fable 5 Refactor Plan
- 1. Charles Schwab API
- ButterflyGuy AI Review State
- PositionService
- .send_pending_eod_charts
- parse_trade_transactions
- weekend_review.py
- TelegramNotifier
- universes.py
- LeaseRegistry
- synthetic_chain.py
- ._settlement_spot_price
- run_live.py
- core/config.py
- test_risk_engine.py
- AGENTS.md
- ButterflyGuy Code Review State
- 5. Local files and backtest inputs
- ._check_post_cancel_fill
- date
- test_collector.py
- ._entry_selection_parity_report
- Layered Risk Management
- position_manager.py
- test_candidate_snapshot.py
- Strategy Settings
- .execute_entry
- FakeProvider
- 8) Generate or compare reports
- 2.5 SEC company ticker map and submissions
- .execute_single_attempt
- conftest.py
- live_performance.py
- now_pacific
- run_live_performance_cron.sh
- XSP Partial-Fill Evidence Plan
- run_morning_scan_cron.sh
- BrokerFillError
- butterfly-guy
- generate_live_performance.py
- run_classifier_sweep.py
- Acceptance Tests
- ButterflyGuy data sources and data types
- Options strategy discovery report
- butterfly mark
- test_trade_service.py
- Configuration Matrix
- Live Runbook
- 2026-07-14 — data audit and research design
- Any
- Geometric butterfly icon
- services/daily_report_card.py
- test_comparison_stats.py
- 7. Operational and observability data
- test_run_migrations.py
- send_alertmanager
- Fixture Manifest
- Offline safety-drill record — 2026-07-13
- Compare Real vs Synthetic Chains
- ButterflyGuy data sources — representative samples
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- Butterfly Guy Live-Readiness TODO
- XSP Flat-Runtime Restart Proof - 2026-07-14
- Critical External-Alert Delivery Proof - 2026-07-15
- test_performance_dashboard.py
- auth_init.py
- butterfly_guy/__init__.py
- reports/__init__.py
- equity_scan/__init__.py

## God Nodes (most connected - your core abstractions)
1. `ButterflyCandidate` - 106 edges
2. `OptionQuote` - 97 edges
3. `SchwabClientWrapper` - 73 edges
4. `AppConfig` - 71 edges
5. `make_settings()` - 71 edges
6. `make_candidate()` - 71 edges
7. `make_order_manager()` - 71 edges
8. `MinuteBar` - 70 edges
9. `MarketSnapshot` - 59 edges
10. `DatabasePool` - 59 edges

## Surprising Connections (you probably didn't know these)
- `TestEma` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestEma` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestBiasScore` --uses--> `SimulationParams`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/simulation_engine.py
- `TestComputeOr` --uses--> `SimulationParams`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/simulation_engine.py
- `TestComputeVwap` --uses--> `SimulationParams`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/simulation_engine.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]

## Communities (171 total, 12 thin omitted)

### Community 0 - "test_order_manager.py"
Cohesion: 0.08
Nodes (92): LiveSpread, NamedTuple, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+84 more)

### Community 1 - "OptionQuote"
Cohesion: 0.39
Nodes (7): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes()

### Community 2 - "run_backtest_db.py"
Cohesion: 0.08
Nodes (63): backtest_entry_price(), candidate_from_trade_row(), day_with_monitoring_bars(), _dd_schedule_label(), _duration_min(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window() (+55 more)

### Community 3 - "_print_pnl_histogram"
Cohesion: 0.13
Nodes (15): _print_pnl_histogram(), ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets. (+7 more)

### Community 4 - "ButterflyCandidate"
Cohesion: 0.17
Nodes (21): detect_complete_days(), _elapsed(), _et(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main() (+13 more)

### Community 5 - "ButterflyChartSpec"
Cohesion: 0.08
Nodes (49): _load_spot_series(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., _spot_rows_to_candles(), load_spot_series(), date, Load spot price series from TimescaleDB for chart generation. (+41 more)

### Community 6 - "DiscordNotifier"
Cohesion: 0.18
Nodes (6): DiscordNotifier, date, Sends centrally deduplicated critical alerts through Alertmanager., Post one or more plain-text messages (e.g. morning equity scan)., Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook.

### Community 7 - "Typical workflow"
Cohesion: 0.13
Nodes (20): 3) Start the SPX stack in Docker, 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202) (+12 more)

### Community 8 - "4. Detailed findings"
Cohesion: 0.05
Nodes (47): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Findings summary, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix (+39 more)

### Community 9 - "test_black_scholes.py"
Cohesion: 0.36
Nodes (5): SchwabSettings, test_initialize_does_not_log_account_identifiers(), test_initialize_fails_closed_when_authentication_fails(), test_place_order_missing_location_does_not_retry(), test_place_order_submits_once_without_retry_wrapper()

### Community 10 - "Domain Model and Ingestion Boundaries"
Cohesion: 0.05
Nodes (40): Actual Schwab Symbol Formats, Backtest Database Chain Rows to Strategy, Broker Mark Versus Computed Mid, ButterflyCandidate, Candidate, Spot, and Daily Bars, code:python (fly_mark_value(lower, center, upper) = lower.mark - 2 * cent), code:text (OptionQuote[]), code:text (External API / asyncpg row / JSON cache) (+32 more)

### Community 11 - "forex_calendar.py"
Cohesion: 0.11
Nodes (31): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), is_sunday_startup_window() (+23 more)

### Community 12 - "resolve_db_dsn"
Cohesion: 0.08
Nodes (26): _asset_drawdowns(), _parse_config_time(), Resolve the DB connection string for local backtests.      Backtests follow the, Resolve the DB connection string for local backtests.      Backtests follow the, Resolve the DB connection string for local backtests.      Backtests follow the, Return live morning/late/afternoon drawdown thresholds., Shared live/backtest parity fields from runtime config., Parse an HH:MM config time. (+18 more)

### Community 13 - "_assert_broker_state_matches_db"
Cohesion: 0.08
Nodes (57): order_ids(), order_statuses(), walk_orders(), _assert_broker_state_matches_db(), _broker_option_position_symbols(), _broker_option_positions(), _expired_trade_has_broker_settlement(), _explicit_fill_details() (+49 more)

### Community 14 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 15 - "MarketSnapshot"
Cohesion: 0.18
Nodes (12): OptionQuote, A single option quote from a chain snapshot., _compute_spread(), EntryDecision, find_entry_candidate(), LiveSpread, MonitorResult, NamedTuple (+4 more)

### Community 16 - "OrderManager"
Cohesion: 0.12
Nodes (22): ButterflyOrderBuilder, Any, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure.  These tests check th (+14 more)

### Community 17 - ".record_trade"
Cohesion: 0.24
Nodes (15): ButterflyBuilder, Builds and scores butterfly spreads from an option chain snapshot., make_chain(), make_quote(), Tests for the butterfly builder scanner., Generate a synthetic chain of call quotes around spot., test_builder_breakevens_valid(), test_builder_cost_filter() (+7 more)

### Community 18 - "AtomicSnapshotStore"
Cohesion: 0.12
Nodes (10): AtomicSnapshotStore, Condition-guarded pointer swap; readers never observe partial snapshots., SnapshotArchive, FakeArchive, FakeDb, FakeMarket, FakePool, date (+2 more)

### Community 19 - "_patch_chain_cache"
Cohesion: 0.13
Nodes (15): _patch_chain_cache(), Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable., Inject DB chains into the chain cache for `date`. Returns restore callable. (+7 more)

### Community 20 - "load_config"
Cohesion: 0.05
Nodes (66): load_config(), Path, Load configuration from YAML file and environment variables., Load configuration from YAML file and environment variables., Load configuration from YAML file and environment variables., Load configuration from YAML file and environment variables., analyze_manual(), analyze_trade() (+58 more)

### Community 21 - "report.py"
Cohesion: 0.14
Nodes (36): build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes() (+28 more)

### Community 22 - "daily_reset_loop"
Cohesion: 0.07
Nodes (28): daily_reset_loop(), Send deferred full-session EOD charts after the cash close., Reset daily risk state at market open., Reset daily risk state at market open., Reset daily risk state at market open., Reset daily risk state at market open., Reset daily risk state at market open., Reset daily risk state at market open. (+20 more)

### Community 23 - "load_entry_chains"
Cohesion: 0.25
Nodes (14): Generates a synthetic SPX option chain from spot + VIX., SyntheticChainGenerator, make_snapshot_time(), datetime, Tests for the synthetic chain generator., Option price should decrease as expiration approaches., Create a snapshot time N minutes before 4pm ET., Volatility skew: OTM puts should have higher IV than equidistant OTM calls. (+6 more)

### Community 24 - "eod_chart_loop"
Cohesion: 0.07
Nodes (27): eod_chart_loop(), Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close. (+19 more)

### Community 25 - "load_date_data"
Cohesion: 0.14
Nodes (14): _fitted_density_counts(), Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit., Return bucket-height estimates from a Gaussian KDE fit. (+6 more)

### Community 26 - "load_monitoring_chains"
Cohesion: 0.02
Nodes (110): discover_dates(), get_prev_close(), get_recent_closes(), get_vix_prev_close(), load_bars_from_db(), load_chains_from_db(), load_date_data(), load_entry_chains() (+102 more)

### Community 27 - "candidatectl.py"
Cohesion: 0.16
Nodes (26): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime(), RenderedRuntime (+18 more)

### Community 28 - "entry_loop"
Cohesion: 0.06
Nodes (46): clear_readiness(), Add a not-ready reason; ``None`` explicitly resets all reasons., Set readiness; ``None`` means the service is ready., readiness_snapshot(), set_readiness(), broker_reconciler_loop(), BrokerStateGate, entry_loop() (+38 more)

### Community 29 - "EquityScanSettings"
Cohesion: 0.18
Nodes (34): EquityScanSettings, build_snapshots(), passes_filters(), rank_catalyst_watch(), rank_scan_results(), build_symbol_map(), Map each symbol to the universes it belongs to., _market_open_et() (+26 more)

### Community 30 - "MinuteBar"
Cohesion: 0.06
Nodes (41): load_day(), JSON cache helpers for DayData — shared across Schwab and future loaders., DayData, MinuteBar, Shared backtest market-data models., DB-backed data loader for historical SPX + VIX data.  Reads from the live Timesc, Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).  Sch, DayResult (+33 more)

### Community 31 - "evaluator.py"
Cohesion: 0.05
Nodes (51): assert_candidate_safety(), CandidateAuditContext, CandidateDecisionQueries, CandidateEvaluator, CandidatePaperExecutor, config_sha256(), Any, Path (+43 more)

### Community 32 - "TradeQueries"
Cohesion: 0.06
Nodes (29): dict, Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Sum of realized PnL for the rolling 7-day window (closed trades only)., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict., Return the last `days` daily closes in chronological order (oldest first). (+21 more)

### Community 33 - "equity_trade_chart.py"
Cohesion: 0.17
Nodes (31): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+23 more)

### Community 34 - "Database Compatibility"
Cohesion: 0.09
Nodes (25): `001_initial.sql`: `option_chain_snapshots`, `001_initial.sql`: `spot_prices`, `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, `005_add_daily_bars.sql`, Anonymized Synchronized Data Slice, code:sql (CREATE TABLE IF NOT EXISTS option_chain_snapshots (), code:sql (CREATE TABLE IF NOT EXISTS spot_prices () (+17 more)

### Community 35 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 36 - "reports/daily_report_card.py"
Cohesion: 0.15
Nodes (30): Path, AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, count_rejected_orders(), detect_problems(), _extract_order_id() (+22 more)

### Community 37 - "feed.py"
Cohesion: 0.28
Nodes (15): Application, Request, _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs() (+7 more)

### Community 38 - "ButterflyOrderBuilder"
Cohesion: 0.06
Nodes (53): _candidate_mark(), ButterflyCandidate, fly_mark_value(), Pydantic models for option data and trade records., Butterfly value at mark: lower.mark - 2*center.mark + upper.mark., A butterfly spread candidate identified by the scanner., Trade service — orchestrates entry flow., Orchestrates the full entry/exit trading flow. (+45 more)

### Community 39 - "scanner.py"
Cohesion: 0.14
Nodes (28): _as_float(), _as_int(), _dedupe_premarket(), filter_movers(), _is_duplicate_premarket(), _live_price(), MarketContext, _mid_bid_ask() (+20 more)

### Community 40 - "test_synthetic_chain.py"
Cohesion: 0.14
Nodes (14): _force_synthetic_for_date(), Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., ASCII histogram with a fitted density curve overlaid on the trade buckets., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., Patch load_chain_day to return None for `date`, forcing BS synthetic fallback. (+6 more)

### Community 41 - "ProfitStateMachine"
Cohesion: 0.07
Nodes (56): ProfitManagementSettings, QuoteQualitySettings, fly_settlement_value(), PositionState, Butterfly cash-settlement value from the underlying index close., Current state of an open position., ExitSignal, ProfitState (+48 more)

### Community 42 - "TradeService"
Cohesion: 0.10
Nodes (20): _age_seconds(), Any, date, datetime, Full entry flow from eligibility checks through entry fill., Full entry flow from eligibility checks through entry fill., Full entry flow from eligibility checks through entry fill., Fetch today's 1-min bars from Schwab and run BiasScoreFilter. (+12 more)

### Community 43 - "daily_report_card_format.py"
Cohesion: 0.27
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 44 - "report_exit_mark_parity.py"
Cohesion: 0.08
Nodes (20): Paper-only SPX candidate fleet fed by a shared market-data service., _aware_utc(), MarketSnapshot, Any, datetime, Immutable normalized market snapshots shared by candidate evaluators., One atomically published, replayable view of candidate market data., SnapshotIdentity (+12 more)

### Community 45 - "resolve_wing_widths_for_vix"
Cohesion: 0.21
Nodes (12): _as_int(), avg_daily_volume(), compute_rvol(), prior_session_pct_change(), Relative volume helpers using Schwab daily bar history., Average daily volume from completed sessions (excludes today)., Close-to-close percent change for the last completed daily session., Symbols with premarket volume — only these need avg-volume for RVOL filter. (+4 more)

### Community 46 - "ButterflySelector"
Cohesion: 0.24
Nodes (10): _butterfly_value(), monitor_position(), Serves chain snapshots sequentially, advancing with each ladder step., Mark-based mid value of the butterfly (used for P&L monitoring)., Return (regime_name, drawdown_threshold) for minutes since open., Walk forward through snapshots after entry fill, computing butterfly value     a, _regime_for(), replay_entry_ladder() (+2 more)

### Community 47 - "Behavioral Specification"
Cohesion: 0.08
Nodes (23): Algorithmic Refinements For 0-DTE Robustness, Behavioral Specification, Bid-Ask Spread Penalization, Candidate Construction Invariants, code:text (raw_expected_move = underlying_spot * (vix / 100) * sqrt(cla), Current Config Defaults, Current Width And Center Selection Data, Double-Factor Live Gating (+15 more)

### Community 48 - "DbDataLoader"
Cohesion: 0.07
Nodes (33): DataFrame, _build_bars(), _build_prev_close(), _build_recent_closes(), _build_vix(), _build_vix_bars(), CsvDataLoader, date (+25 more)

### Community 49 - "BacktestDataLoader"
Cohesion: 0.21
Nodes (6): BacktestDataLoader, Load all data needed for a single backtest day., Loads historical data from Polygon.io for backtesting., Fetch SPX 1-minute bars for a given date from Polygon., Fetch VIX close for a given date from Polygon., Fetch the actual previous trading day's SPX close for a given date.

### Community 50 - "StrategySettings"
Cohesion: 0.32
Nodes (12): BaseSettings, AppConfig, ExecutionSettings, _assert_live_config_supported(), test_live_config_allows_confirmed_xsp_canary(), test_live_config_allows_spx_live_when_explicitly_confirmed(), test_live_config_allows_spx_live_when_explicitly_enabled(), test_live_config_rejects_non_spx_live_money() (+4 more)

### Community 51 - "health_monitor.py"
Cohesion: 0.18
Nodes (15): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), Derive a human-readable service name from a health URL.      Prefers the ``servi, Post a message to Discord webhook., Run one full check cycle across all URLs. Returns list of results. (+7 more)

### Community 52 - "._session_open_price"
Cohesion: 0.11
Nodes (17): Fetch today's first regular-session open from Schwab intraday bars., Fetch today's first regular-session open from Schwab intraday bars., Fetch today's first regular-session open from Schwab intraday bars., Fetch today's first regular-session open from Schwab intraday bars., Fetch today's first regular-session open from Schwab intraday bars., Fetch today's first regular-session open from Schwab intraday bars., Fetch today's first regular-session open from Schwab intraday bars., Fetch today's first regular-session open from Schwab intraday bars. (+9 more)

### Community 53 - "_print_same_entry_comparison_table"
Cohesion: 0.11
Nodes (19): _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday (+11 more)

### Community 54 - "main"
Cohesion: 0.06
Nodes (44): BoundLogger, Pool, get_logger(), Structured logging setup with structlog., Get a structlog logger with optional name., Prometheus metrics for monitoring., Start HTTP server serving /metrics (Prometheus) and /health on *port*.      Runs, Start the Prometheus metrics HTTP server. (+36 more)

### Community 55 - "run_morning_scan.py"
Cohesion: 0.14
Nodes (20): load_equity_scan_config(), Path, Load equity scan settings from YAML., Load equity scan settings from YAML., archive_report(), archive_report_json(), Path, Write the scan report to a dated markdown file under report_dir. (+12 more)

### Community 56 - "._wait_for_fill"
Cohesion: 0.26
Nodes (12): bs_call_price(), bs_put_price(), bs_theta(), _d1(), _d2(), Black-Scholes option pricing and Greeks., Black-Scholes European call price.      Args:         S: Spot price         K: S, Black-Scholes European put price. (+4 more)

### Community 57 - "str"
Cohesion: 0.15
Nodes (13): Use the first regular-session snapshot for gap direction., Use the first regular-session snapshot for gap direction., Use the first regular-session snapshot for gap direction., Use the first regular-session snapshot for gap direction., Use the first regular-session snapshot for gap direction., Load all data for one date. Returns None if insufficient data., Use the first regular-session snapshot for gap direction., Use the first regular-session snapshot for gap direction. (+5 more)

### Community 58 - "._bias_direction"
Cohesion: 0.11
Nodes (17): Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter. (+9 more)

### Community 59 - ".get_recent_closed_pnls"
Cohesion: 0.50
Nodes (8): Return the first regular-session open for the requested Eastern date., _session_open_from_intraday_candles(), _candle(), datetime, test_filled_entry_persistence_failure_stops_for_reconciliation(), test_session_open_ignores_premarket_and_missing_open_values(), test_session_open_returns_none_when_no_regular_session_bar_exists(), test_session_open_uses_first_regular_session_bar_for_requested_date()

### Community 60 - "simulation_engine.py"
Cohesion: 0.09
Nodes (36): ProfitManagementStrategy, _drawdown_rule(), DrawdownWindow, _profit_exit_reason(), datetime, Single-day simulation engine using synthetic option chains., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. (+28 more)

### Community 61 - "HttpMarketDataProvider"
Cohesion: 0.23
Nodes (4): HttpMarketDataProvider, AsyncClient, Response, Fail-closed client for the internal candidate feed.

### Community 62 - "select_live_width"
Cohesion: 0.20
Nodes (10): bs_gamma(), bs_vega(), Gamma — rate of change of delta wrt spot., Vega — sensitivity to 1% change in IV., date, datetime, Minutes until market close on expiration day., Generate full synthetic option chain for one expiration.          Args: (+2 more)

### Community 63 - "news.py"
Cohesion: 0.16
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 64 - "._record_exit_metrics"
Cohesion: 0.12
Nodes (15): Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine. (+7 more)

### Community 65 - "._extract_quotes"
Cohesion: 0.11
Nodes (17): Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation. (+9 more)

### Community 66 - "._parse_chain_to_quotes"
Cohesion: 0.11
Nodes (17): Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects., Parse Schwab chain response into OptionQuote objects. (+9 more)

### Community 67 - "performance_chart.py"
Cohesion: 0.18
Nodes (20): compute_stats(), ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels() (+12 more)

### Community 68 - "print_thinkback_checklist"
Cohesion: 0.12
Nodes (17): print_thinkback_checklist(), Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist. (+9 more)

### Community 69 - "volume.py"
Cohesion: 0.30
Nodes (11): date, Tests for live performance report generation., test_chart_payload_includes_drawdown_fields(), test_is_drawdown_exit(), test_no_trade_reason_mapping(), test_performance_report_segments_fill_model_cohorts(), test_render_placeholder_html(), test_render_report_html_contains_sections() (+3 more)

### Community 70 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 71 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.10
Nodes (21): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+13 more)

### Community 72 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 73 - "SchwabDataLoader"
Cohesion: 0.10
Nodes (20): day_cache_path(), date, Path, save_day(), date, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day. (+12 more)

### Community 74 - "chain_cache.py"
Cohesion: 0.16
Nodes (21): chain_cache_path(), ChainDay, load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.  Forma (+13 more)

### Community 75 - "GapRegimeFilter"
Cohesion: 0.11
Nodes (17): Enum, Classify regime then delegate to simulate_day() with matching params.          R, Classify regime then delegate to simulate_day() with matching params.          R, Classify regime then delegate to simulate_day() with matching params.          R, Classify regime then delegate to simulate_day() with matching params.          R, Maps Regime → SimulationParams for use with simulate_day_adaptive().      Per-re, RegimeDispatch, GapRegimeFilter (+9 more)

### Community 76 - "run_entry_analysis.py"
Cohesion: 0.13
Nodes (29): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+21 more)

### Community 77 - "ChainDay"
Cohesion: 0.50
Nodes (4): main(), parse_reference_date(), date, Send SPX weekend review to Discord #weekend-review.  Cron: Saturday 9:00 AM PT

### Community 78 - "._exit_mark_parity_report"
Cohesion: 0.12
Nodes (16): Record trade exit metrics and update risk engine., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot. (+8 more)

### Community 79 - "._record_monitoring_leg_quotes"
Cohesion: 0.12
Nodes (15): Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing., Record trade exit metrics and update risk engine., Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing. (+7 more)

### Community 80 - "is_market_open"
Cohesion: 0.23
Nodes (17): is_market_open(), Check if the market is currently open., et(), datetime, Tests for market time utilities., test_get_0dte_expiration(), test_market_closed_after_close(), test_market_closed_after_early_close() (+9 more)

### Community 81 - "black_scholes.py"
Cohesion: 0.13
Nodes (16): bs_delta(), Delta — rate of change of price wrt spot., Tests for Black-Scholes pricing and Greeks., ATM call price should be approximately S * sigma * sqrt(T/2pi)., Deep ITM call should be approximately S - K * exp(-rT)., Deep ITM put should be approximately K - S., Expired call should equal intrinsic value., Put-call delta parity: call_delta - put_delta = 1. (+8 more)

### Community 82 - "2. Other external and public sources"
Cohesion: 0.11
Nodes (19): 2.1 Yahoo Finance (`yfinance`), 2.2 S&P 500 constituent dataset on GitHub, 2.3 Wikipedia Nasdaq-100 page, 2.4 Nasdaq Trader symbol directories, 2.5 SEC company ticker map and submissions, 2.6 Alpha Vantage earnings calendar and news sentiment, 2.7 Forex Factory economic calendar, 2.8 Local market calendar and clock (+11 more)

### Community 83 - "SnapshotUnavailableError"
Cohesion: 0.22
Nodes (6): Any, date, datetime, Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Main collector loop — runs while market is open., Parse Schwab callExpDateMap/putExpDateMap into flat rows.

### Community 84 - ".bulk_upsert"
Cohesion: 0.27
Nodes (5): Lease, LeaseRegistry, datetime, LeaseKind, test_new_lease_wakes_idle_feed()

### Community 85 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.20
Nodes (7): Any, date, Schwab market-data client deliberately lacking every account/order operation., Authenticate a Schwab client without resolving or retaining an account., ReadOnlySchwabMarketDataClient, main(), Run the demand-aware shared SPX candidate market-data feed.

### Community 86 - "test_weekend_review.py"
Cohesion: 0.29
Nodes (13): date, Tests for weekend review date windows and orchestration., test_calendar_month_to_date(), test_format_performance_caption_includes_stats(), test_latest_fill_model_cohort_does_not_mix_legacy_and_mark_v1(), test_previous_mon_fri_from_friday(), test_previous_mon_fri_from_saturday(), test_review_windows_from_saturday() (+5 more)

### Community 87 - "ButterflyGuy Fable 5 Refactor Plan"
Cohesion: 0.11
Nodes (18): ButterflyGuy Fable 5 Refactor Plan, Closed Design Decisions, code:text (Use FABLE_REFACTOR_PLAN.md as the project entry point. Start), code:text (Phase 1 is complete. Now read DOMAIN_MODEL.md and the candid), code:text (Phase 2 is complete. Now read BEHAVIORAL_SPEC.md in full. Im), code:text (Phase 3 is complete. Implement the live broker boundary only), Completion Definition, Document Map (+10 more)

### Community 88 - "1. Charles Schwab API"
Cohesion: 0.15
Nodes (16): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+8 more)

### Community 89 - "ButterflyGuy AI Review State"
Cohesion: 0.11
Nodes (18): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Changes Made This Session, Commands Run, Current Cycle Checkpoints, Current Objective, Decisions Made (+10 more)

### Community 91 - ".send_pending_eod_charts"
Cohesion: 0.14
Nodes (13): Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close., Record trade exit metrics and update risk engine., Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close. (+5 more)

### Community 92 - "parse_trade_transactions"
Cohesion: 0.14
Nodes (19): parse_trade_transactions(), rank_trades(), Parse TRADE transactions into ranked trade results., Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options). (+11 more)

### Community 93 - "weekend_review.py"
Cohesion: 0.19
Nodes (26): TradePoint, build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_performance_caption(), format_review_header() (+18 more)

### Community 94 - "TelegramNotifier"
Cohesion: 0.12
Nodes (14): Trading and risk notifications., Sends risk notifications through the existing Telegram notify helper., Sends risk notifications through the existing Telegram notify helper., Sends risk notifications through the existing Telegram notify helper., Sends risk notifications through the existing Telegram notify helper., Sends risk notifications through the existing Telegram notify helper., Sends risk notifications through the existing Telegram notify helper., Sends risk notifications through the existing Telegram notify helper. (+6 more)

### Community 95 - "universes.py"
Cohesion: 0.05
Nodes (68): _as_float(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_exchange_seed_symbols(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols() (+60 more)

### Community 96 - "LeaseRegistry"
Cohesion: 0.29
Nodes (9): CandidateFeed, _previous_close(), Any, date, _session_open(), SessionContext, RuntimeError, No complete snapshot is currently available. (+1 more)

### Community 97 - "synthetic_chain.py"
Cohesion: 0.20
Nodes (6): IVModel, Implied volatility model with VIX scaling and skew adjustment., Models implied volatility with VIX scaling and volatility skew., Convert VIX index value to 0-DTE ATM IV estimate.          VIX is the 30-day imp, Compute skew-adjusted IV for a given strike.          OTM puts have elevated IV, Synthetic option chain generator using Black-Scholes + VIX IV model.

### Community 98 - "._settlement_spot_price"
Cohesion: 0.15
Nodes (12): Use Schwab's final regular-session 1-minute close for cash settlement., Use Schwab's final regular-session 1-minute close for cash settlement., Use Schwab's final regular-session 1-minute close for cash settlement., Use Schwab's final regular-session 1-minute close for cash settlement., Use Schwab's final regular-session 1-minute close for cash settlement., Use Schwab's final regular-session 1-minute close for cash settlement., Use Schwab's final regular-session 1-minute close for cash settlement., Use Schwab's final regular-session 1-minute close for cash settlement. (+4 more)

### Community 99 - "run_live.py"
Cohesion: 0.22
Nodes (17): _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_premarket_window(), is_trading_day(), _last_weekday(), market_close_time(), _nth_weekday() (+9 more)

### Community 100 - "core/config.py"
Cohesion: 0.31
Nodes (5): BaseHTTPRequestHandler, _MetricsHandler, Clear only the recovered subsystem's not-ready reason., HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 101 - "test_risk_engine.py"
Cohesion: 0.23
Nodes (15): make_risk_engine(), Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed(), test_can_trade_max_loss() (+7 more)

### Community 102 - "AGENTS.md"
Cohesion: 0.13
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 103 - "ButterflyGuy Code Review State"
Cohesion: 0.12
Nodes (16): Architecture map, ButterflyGuy Code Review State, Changes implemented, Commands executed, Confirmed findings, Current phase, Decisions already made, Exact next actions (+8 more)

### Community 104 - "5. Local files and backtest inputs"
Cohesion: 0.12
Nodes (17): 5.1 Application YAML configuration, 5.2 Environment variables and `.env`, 5.3 `tokens.json`, 5.4 Universe and metadata files, 5.5 Historical minute CSVs, 5.6 Local daily bar cache, 5.7 Local option-chain cache, 5. Local files and backtest inputs (+9 more)

### Community 105 - "._check_post_cancel_fill"
Cohesion: 0.40
Nodes (8): StrategySettings, make_candidate(), Tests for butterfly candidate selection., test_regular_best_rr_selection_still_uses_rr_target(), test_vix_centered_selection_blocks_when_no_candidate_near_target(), test_vix_centered_selection_uses_rr_target_after_center_filter(), test_vix_farthest_otm_ignores_rr_target_after_builder_price_filters(), test_vix_selection_rejects_cheap_extreme_rr_tail_candidate()

### Community 106 - "date"
Cohesion: 0.20
Nodes (6): date, Overwrite realized_pnl in risk state (SET, not ADD).         Used at startup to, Record that a trade was executed., Record realized dollar PnL., Overwrite dollar realized_pnl in risk state (SET, not ADD).         Used at star, Manually sync the trade count in the risk state table.         Used at startup t

### Community 107 - "test_collector.py"
Cohesion: 0.20
Nodes (9): Integration tests for the option chain collector (requires live Schwab token)., A local JSON cache failure should not fail a DB-backed snapshot., A corrupt optional chain cache should not fail a DB-backed snapshot., Collector should parse chain response into rows., Parsed rows should have the expected fields., test_collect_snapshot_parses_chain(), test_collect_snapshot_row_fields(), test_collect_snapshot_succeeds_when_chain_cache_is_corrupt() (+1 more)

### Community 108 - "._entry_selection_parity_report"
Cohesion: 0.42
Nodes (8): EntrySettings, VixWidthBucket, _quote(), test_entry_selection_config_applies_only_explicit_overrides(), test_entry_strategy_snapshot_records_live_selection_profile(), test_vix_entry_selection_does_not_fallback_outside_center_tolerance(), test_vix_entry_selection_prefers_first_width_for_xsp(), test_attempt_entry_blocks_stale_vix_before_chain_fetch()

### Community 109 - "Layered Risk Management"
Cohesion: 0.22
Nodes (9): High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy (+1 more)

### Community 110 - "position_manager.py"
Cohesion: 0.25
Nodes (8): compute_tent_boundaries(), fly_bid_value(), _max_leg_spread_to_mark_ratio(), Position value tracking and management., Butterfly value at market bid (what a MM pays to buy it from you)., Find the two spot prices where the fly's BS mark equals entry cost.      These a, implied_vol(), Back-solve for implied volatility given an option market price.      Returns Non

### Community 111 - "test_candidate_snapshot.py"
Cohesion: 0.44
Nodes (8): datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry(), test_long_poll_never_replays_same_sequence(), test_snapshot_rejects_stale_data(), test_snapshot_round_trip_and_immutable_indexes()

### Community 112 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 115 - "FakeProvider"
Cohesion: 0.39
Nodes (6): candidate(), FakeProvider, market(), test_candidate_entry_is_blocked_when_pin_fails(), test_candidate_entry_pins_before_mark_fill(), test_candidate_safety_rejects_live_or_credentialed_runtime()

### Community 116 - "8) Generate or compare reports"
Cohesion: 0.27
Nodes (6): 8) Generate or compare reports, code:bash (uv run python src/butterfly_guy/scripts/report_trade_ladders), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), Inspecting Historical Entries, 📊 Research and Inspection, 🐳 Running with Docker

### Community 119 - "2.5 SEC company ticker map and submissions"
Cohesion: 0.18
Nodes (12): DailyReportCardSettings, load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds, _match_round_trips_fifo(), Pair OPENING and CLOSING legs into round-trip realized P&L. (+4 more)

### Community 121 - ".execute_single_attempt"
Cohesion: 0.03
Nodes (85): NamedTuple, now_utc(), iter_chain_options(), date, Shared utilities for parsing Schwab option chain responses., Yield (strike, option_type, opt_dict) for each option matching the expiration., OrderIntentQueries, Queries for durable broker order intents. (+77 more)

### Community 124 - "live_performance.py"
Cohesion: 0.28
Nodes (15): chart_payload(), cumulative_equity(), drawdown_series(), DrawdownPoint, duration_minutes(), format_et_time(), is_drawdown_exit(), _money() (+7 more)

### Community 126 - "now_pacific"
Cohesion: 0.18
Nodes (16): get_0dte_expiration(), minutes_since_open(), minutes_to_close(), now_eastern(), now_pacific(), datetime, Current time in US/Eastern., Calendar date for the US/Eastern trading session. (+8 more)

### Community 129 - "XSP Partial-Fill Evidence Plan"
Cohesion: 0.16
Nodes (13): code:bash (uv run python src/butterfly_guy/scripts/report_broker_order_), Completion, Controlled test, Current evidence, Decision, Done criteria, If one occurs naturally, Preconditions (+5 more)

### Community 131 - "BrokerFillError"
Cohesion: 0.07
Nodes (55): RuntimeError, A trade record for tracking entry/exit., TradeRecord, account_hash(), client(), Authenticate and resolve account hash., pool(), AmbiguousOrderError (+47 more)

### Community 136 - "generate_live_performance.py"
Cohesion: 0.17
Nodes (20): no_trade_reason(), NoTradeDay, _parse_metadata(), Any, render_placeholder_html(), trade_pnl_dollars(), trade_point_from_row(), build_report() (+12 more)

### Community 139 - "run_classifier_sweep.py"
Cohesion: 0.18
Nodes (18): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _summarize_combo(), main() (+10 more)

### Community 151 - "Acceptance Tests"
Cohesion: 0.17
Nodes (11): Acceptance Tests, Completion Gate, Current Reference Test Map, Golden Replay Requirements, Observability Acceptance, Phase 1: Database Adapter Acceptance, Phase 2: Domain And Selection Acceptance, Phase 3: Paper Execution And Lifecycle Acceptance (+3 more)

### Community 157 - "ButterflyGuy data sources and data types"
Cohesion: 0.18
Nodes (10): 10. Repository evidence map, 4. Shared database tables visible to the same DB account, 6. Canonical and derived analytical data types, 8. Reports, archives, charts, and outbound destinations, 9. Practical limitations and safety notes, At a glance, ButterflyGuy data sources and data types, code:json ({"symbol":"SYNTH_C6315","underlying":"SPX","expiration":"202) (+2 more)

### Community 158 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 159 - "butterfly mark"
Cohesion: 0.20
Nodes (10): BUTTERFLYGUY, connectivity visual association, precision visual association, technology visual association, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background (+2 more)

### Community 163 - "test_trade_service.py"
Cohesion: 0.18
Nodes (13): BaseModel, Protocol, CollectorSettings, ConfigModel, DatabaseSettings, MonitoringSettings, PeakTrackingSettings, BaseModel (+5 more)

### Community 164 - "Configuration Matrix"
Cohesion: 0.20
Nodes (9): Configuration Matrix, Execution And Risk Differences, Max Cost Per Width, Profit Management Regimes, Quote Quality And Peak Tracking, Refactor Requirements, Shared Defaults, Strategy Profile (+1 more)

### Community 165 - "Live Runbook"
Cohesion: 0.22
Nodes (9): code:bash (uv run python src/butterfly_guy/scripts/report_broker_order_), code:bash (docker logs -f --tail=100 butterfly_spx_app), During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery (+1 more)

### Community 166 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 172 - "Any"
Cohesion: 0.07
Nodes (22): Any, date, Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order once and return the order ID.          Order placement is not ret, Place an order and return the order ID., Get the status of an order., Cancel an existing order. (+14 more)

### Community 179 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 181 - "services/daily_report_card.py"
Cohesion: 0.26
Nodes (12): archive_report(), date, Path, chartable_equity_trades(), format_equity_trade_chart_caption(), date, datetime, Path (+4 more)

### Community 182 - "test_comparison_stats.py"
Cohesion: 0.46
Nodes (7): _print_comparison_table(), _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 183 - "7. Operational and observability data"
Cohesion: 0.25
Nodes (8): 7.1 Prometheus metrics, 7.2 Health and readiness endpoints, 7.3 Structured application logs, 7. Operational and observability data, code:text (butterfly_chain_snapshot_rows{underlying="SPX"} 487), code:json ({"status":"ok","service":"SPX","timestamp":"2026-07-13T18:00), code:json ({"status":"not_ready","reason":"initializing_schwab"}), code:json ({"underlying":"SPX","rows":487,"event":"snapshot_collected",)

### Community 187 - "test_run_migrations.py"
Cohesion: 0.33
Nodes (4): fake_db(), FakeConnection, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 188 - "send_alertmanager"
Cohesion: 0.12
Nodes (12): Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_notify_entry_includes_trade_stats(), test_notify_exit_formats_contract_pnl_as_dollars(), test_token_keepalive_reports_alertmanager_state(), Lightweight Telegram and ButterflyGuy Alertmanager helpers.  Usage:     from not, Send a Telegram message. Returns True on success, False on failure. (+4 more)

### Community 193 - "Fixture Manifest"
Cohesion: 0.29
Nodes (6): Config Hashes, Export Rules, Fixture Manifest, Golden Replay Cases, Phase 1 Market-Data Fixtures, Selection Fixtures

### Community 194 - "Offline safety-drill record — 2026-07-13"
Cohesion: 0.29
Nodes (6): Drill findings fixed, Follow-up — 2026-07-14, Offline safety-drill record — 2026-07-13, Remaining do-now work, Result, Verification

### Community 198 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 199 - "Exact-SHA Deployment Proof - 2026-07-15"
Cohesion: 0.33
Nodes (5): Deployment and verification, Exact-SHA Deployment Proof - 2026-07-15, Follow-up rollback and restore drill, Preconditions and validation, Scope

### Community 200 - "XSP Manual-Flatten Evidence - 2026-07-16"
Cohesion: 0.33
Nodes (5): Fail-closed proof, Post-action reconciliation and paper restore, Redacted evidence, Result, XSP Manual-Flatten Evidence - 2026-07-16

### Community 211 - "Butterfly Guy Live-Readiness TODO"
Cohesion: 0.40
Nodes (4): Butterfly Guy Live-Readiness TODO, Current gate, Remaining tasks, Safety boundaries

### Community 212 - "XSP Flat-Runtime Restart Proof - 2026-07-14"
Cohesion: 0.40
Nodes (4): Preconditions, Restart and verification, Scope, XSP Flat-Runtime Restart Proof - 2026-07-14

### Community 213 - "Critical External-Alert Delivery Proof - 2026-07-15"
Cohesion: 0.40
Nodes (4): Critical External-Alert Delivery Proof - 2026-07-15, Implementation reviewed, Scope, Supervised delivery and deduplication result

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **309 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `External sources`, `Local durable data` (+304 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `OptionQuote` connect `MarketSnapshot` to `test_order_manager.py`, `OptionQuote`, `run_backtest_db.py`, `BrokerFillError`, `ButterflyCandidate`, `.record_trade`, `AtomicSnapshotStore`, `load_config`, `load_entry_chains`, `load_monitoring_chains`, `MinuteBar`, `evaluator.py`, `feed.py`, `ButterflyOrderBuilder`, `ProfitStateMachine`, `report_exit_mark_parity.py`, `ButterflySelector`, `DbDataLoader`, `main`, `select_live_width`, `._extract_quotes`, `._parse_chain_to_quotes`, `chain_cache.py`, `run_entry_analysis.py`, `._exit_mark_parity_report`, `._record_monitoring_leg_quotes`, `.bulk_upsert`, `LeaseRegistry`, `synthetic_chain.py`, `._entry_selection_parity_report`, `position_manager.py`, `test_candidate_snapshot.py`, `FakeProvider`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `ButterflyOrderBuilder` to `test_order_manager.py`, `run_backtest_db.py`, `BrokerFillError`, `ButterflyCandidate`, `ButterflyChartSpec`, `_assert_broker_state_matches_db`, `MarketSnapshot`, `OrderManager`, `.record_trade`, `entry_loop`, `MinuteBar`, `evaluator.py`, `ProfitStateMachine`, `TradeService`, `ButterflySelector`, `main`, `simulation_engine.py`, `._extract_quotes`, `GapRegimeFilter`, `._exit_mark_parity_report`, `._record_monitoring_leg_quotes`, `._check_post_cancel_fill`, `position_manager.py`, `FakeProvider`, `.execute_single_attempt`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `MinuteBar` connect `MinuteBar` to `run_backtest_db.py`, `ButterflyCandidate`, `._bias_direction`, `ButterflyOrderBuilder`, `SchwabDataLoader`, `chain_cache.py`, `GapRegimeFilter`, `run_entry_analysis.py`, `resolve_db_dsn`, `ButterflySelector`, `MarketSnapshot`, `DbDataLoader`, `BacktestDataLoader`, `.execute_entry`, `str`, `load_monitoring_chains`, `simulation_engine.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 107 inferred relationships involving `str` (e.g. with `.__init__()` and `._get_prev_close()`) actually correct?**
  _`str` has 107 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 28 INFERRED edges - model-reasoned connections that need verification._