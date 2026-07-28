# Graph Report - Butterflyguy  (2026-07-28)

## Corpus Check
- 228 files · ~245,648 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3315 nodes · 8888 edges · 167 communities (154 shown, 13 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 875 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8f345a2d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- models.py
- schwab_client.py
- test_order_manager.py
- AppConfig
- SchwabClientWrapper
- ButterflyChartSpec
- load_date_data
- test_run_live.py
- discover_options_strategy.py
- main
- MarketSnapshot
- test_position_manager.py
- CsvDataLoader
- CandidateRegistry
- forex_calendar.py
- run_single
- MinuteBar
- feed.py
- test_comparison_stats.py
- DiscordNotifier
- EquityScanSettings
- 4. Detailed findings
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- core/config.py
- services/daily_report_card.py
- ButterflyCandidate
- run_entry_analysis.py
- SnapshotUnavailableError
- Domain Model and Ingestion Boundaries
- ProfitStateMachine
- test_risk_engine.py
- test_black_scholes.py
- news.py
- symbol_directory
- is_market_open
- record_equity_market_data.py
- time_utils.py
- state_machine.py
- SessionClose
- DatabasePool
- AtomicSnapshotStore
- CandidateEvaluator
- StrategySettings
- SchwabDataLoader
- equity_trade_chart.py
- run_morning_scan.py
- str
- black_scholes.py
- live_performance.py
- entry_loop
- ButterflyGuy AI Review State
- test_trade_chart.py
- load_config
- Database Compatibility
- weekend_review.py
- dict
- daily_reset_loop
- TradeRecord
- RiskQueries
- generate_live_performance.py
- test_synthetic_chain.py
- synthetic_chain.py
- ReadOnlySchwabMarketDataClient
- universes.py
- test_candidate_evaluator_accounting.py
- DbDataLoader
- _MetricsHandler
- GapRegimeFilter
- test_candidate_provider.py
- Behavioral Specification
- setup_logging
- run_classifier_sweep.py
- ChainDay
- scanner.py
- report_broker_order_statuses.py
- position_service.py
- 1. Charles Schwab API
- run_backtest_db.py
- test_daily_report_card.py
- test_weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- .generate_chain
- .collect_snapshot
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- resolve_db_dsn
- report_exit_mark_parity.py
- ButterflyGuy Fable 5 Refactor Plan
- 2026-07-14 — data audit and research design
- TradeService
- OrderIntentQueries
- performance_chart.py
- ButterflyOrderBuilder
- test_candidate_variants.py
- _print_same_entry_comparison_table
- FakeProvider
- PositionManager
- select_cross_width_candidate
- test_schwab_token_keepalive.py
- test_candidate_settlement.py
- 9) Capture equity candles and Level II for trade review
- report_trade_ladders.py
- .reset
- bs_gamma
- health_monitor.py
- AGENTS.md
- ButterflyGuy Code Review State
- 2. Other external and public sources
- 5. Local files and backtest inputs
- Butterfly Guy
- _patch_chain_cache
- OptionQuote
- Strategy Settings
- XSP Partial-Fill Evidence Plan
- order_manager.py
- Width Selection
- Acceptance Tests
- BacktestDataLoader
- ButterflyGuy data sources and data types
- Equity candles and order-book recording
- butterfly mark
- test_run_migrations.py
- Configuration Matrix
- Live Runbook
- Layered Risk Management
- Geometric butterfly icon
- 7. Operational and observability data
- report_selection_parity.py
- 3) Start the SPX stack in Docker
- Fixture Manifest
- Offline safety-drill record — 2026-07-13
- ButterflyGuy data sources — representative samples
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- Butterfly Guy Live-Readiness TODO
- XSP Flat-Runtime Restart Proof - 2026-07-14
- Critical External-Alert Delivery Proof - 2026-07-15
- test_performance_dashboard.py
- auth_init.py
- conftest.py
- butterfly_guy/__init__.py
- equity_scan/__init__.py
- reports/__init__.py
- run_live_performance_cron.sh
- run_morning_scan_cron.sh
- Compare Real vs Synthetic Chains
- butterfly-guy

## God Nodes (most connected - your core abstractions)
1. `ButterflyCandidate` - 110 edges
2. `OptionQuote` - 99 edges
3. `SchwabClientWrapper` - 78 edges
4. `AppConfig` - 76 edges
5. `make_settings()` - 71 edges
6. `make_candidate()` - 71 edges
7. `make_order_manager()` - 71 edges
8. `MinuteBar` - 70 edges
9. `MarketSnapshot` - 63 edges
10. `DatabasePool` - 59 edges

## Surprising Connections (you probably didn't know these)
- `test_broker_option_position_symbols_filters_same_underlying_options()` --calls--> `_broker_option_position_symbols()`  [INFERRED]
  tests/test_run_live.py → src/butterfly_guy/scripts/run_live.py
- `TestEngineIntegration` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestBiasScore` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestComputeOr` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestComputeVwap` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]

## Communities (167 total, 13 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.11
Nodes (36): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), _et(), find_entry_candidate(), get_prev_close(), get_vix() (+28 more)

### Community 1 - "models.py"
Cohesion: 0.21
Nodes (5): _aware_utc(), from_dict(), datetime, Immutable normalized market snapshots shared by candidate evaluators., StaleSnapshotError

### Community 2 - "schwab_client.py"
Cohesion: 0.14
Nodes (18): RuntimeError, ExecutionSettings, RiskSettings, SchwabSettings, account_hash(), client(), Async Schwab API client wrapper with retry logic., Authenticate and resolve account hash. (+10 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.10
Nodes (86): LiveSpread, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread(), make_order_manager() (+78 more)

### Community 4 - "AppConfig"
Cohesion: 0.13
Nodes (30): BaseSettings, assert_candidate_safety(), candidate_performance_stats(), CandidateAuditContext, CandidateDecisionQueries, CandidatePerformanceStats, config_sha256(), Path (+22 more)

### Community 5 - "SchwabClientWrapper"
Cohesion: 0.07
Nodes (30): Any, date, Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order once and return the order ID. Order placement is not retried…, Place an order and return the order ID., Get the status of an order., Cancel an existing order. (+22 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.15
Nodes (24): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), _exit_chart_series(), _exit_marker_point(), _exit_window_end() (+16 more)

### Community 7 - "load_date_data"
Cohesion: 0.11
Nodes (34): discover_dates(), get_prev_close(), get_recent_closes(), get_vix_prev_close(), load_bars_from_db(), load_chains_from_db(), load_date_data(), load_entry_chains() (+26 more)

### Community 8 - "test_run_live.py"
Cohesion: 0.12
Nodes (34): clear_readiness(), Prometheus metrics for monitoring., Add a not-ready reason; ``None`` explicitly resets all reasons., Set readiness; ``None`` means the service is ready., readiness_snapshot(), set_readiness(), broker_reconciler_loop(), test_health_stays_live_while_ready_reports_degraded() (+26 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "main"
Cohesion: 0.06
Nodes (36): Start HTTP server serving /metrics (Prometheus) and /health on *port*. Runs in…, Start the Prometheus metrics HTTP server., start_metrics_server(), OptionChainCollector, Option chain collector — fetches and stores SPX chain snapshots., Collects option chain snapshots at regular intervals., Execute SQL migration files in order., Run all SQL migration files in order. (+28 more)

### Community 11 - "MarketSnapshot"
Cohesion: 0.08
Nodes (16): Paper-only SPX candidate fleet fed by a shared market-data service., MarketSnapshot, One atomically published, replayable view of candidate market data., SnapshotIdentity, HttpMarketDataProvider, MarketDataProvider, AsyncClient, LeaseKind (+8 more)

### Community 12 - "test_position_manager.py"
Cohesion: 0.28
Nodes (12): fly_settlement_value(), Butterfly cash-settlement value from the underlying index close., make_candidate(), make_quote(), make_xsp_candidate(), quote_map(), Tests for butterfly position valuation helpers., test_call_butterfly_settles_to_intrinsic_with_spot_below_all_strikes() (+4 more)

### Community 13 - "CsvDataLoader"
Cohesion: 0.16
Nodes (15): DataFrame, _build_bars(), _build_prev_close(), _build_recent_closes(), _build_vix(), _build_vix_bars(), CsvDataLoader, date (+7 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.11
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.11
Nodes (31): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), is_sunday_startup_window() (+23 more)

### Community 16 - "run_single"
Cohesion: 0.13
Nodes (33): backtest_entry_price(), _dd_schedule_label(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window(), get_vix_at(), get_vix_snapshot_at(), _live_width_label() (+25 more)

### Community 17 - "MinuteBar"
Cohesion: 0.06
Nodes (31): MinuteBar, Shared backtest market-data models., DB-backed data loader for historical SPX + VIX data. Reads from the live…, Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).…, BiasScoreFilter, _compute_or(), _compute_vwap(), _ema() (+23 more)

### Community 18 - "feed.py"
Cohesion: 0.19
Nodes (20): Application, Request, _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs() (+12 more)

### Community 19 - "test_comparison_stats.py"
Cohesion: 0.46
Nodes (7): _print_comparison_table(), _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 20 - "DiscordNotifier"
Cohesion: 0.08
Nodes (21): AlertmanagerNotifier, DiscordNotifier, date, Trading and risk notifications., Sends centrally deduplicated critical alerts through Alertmanager., Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook., asyncio (+13 more)

### Community 21 - "EquityScanSettings"
Cohesion: 0.13
Nodes (46): EquityScanSettings, attach_news_impacts(), build_snapshots(), _focus_reasons(), OpeningFocusItem, parse_equity_quote(), passes_filters(), datetime (+38 more)

### Community 22 - "4. Detailed findings"
Cohesion: 0.05
Nodes (47): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Findings summary, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix (+39 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.07
Nodes (52): ProfitManagementStrategy, nearest_snapshot(), Return quotes from the most recent snapshot at or before bar_ts., DayData, DayResult, _drawdown_rule(), DrawdownWindow, _profit_exit_reason() (+44 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.14
Nodes (33): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders(), detect_problems(), _extract_order_id() (+25 more)

### Community 25 - "report.py"
Cohesion: 0.17
Nodes (31): build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes() (+23 more)

### Community 26 - "core/config.py"
Cohesion: 0.18
Nodes (15): BaseModel, CollectorSettings, ConfigModel, DatabaseSettings, MonitoringSettings, PeakTrackingSettings, BaseModel, QuoteQualitySettings (+7 more)

### Community 27 - "services/daily_report_card.py"
Cohesion: 0.12
Nodes (21): load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds, archive_report(), date, Path (+13 more)

### Community 28 - "ButterflyCandidate"
Cohesion: 0.11
Nodes (27): BoundLogger, get_logger(), Structured logging setup with structlog., Get a structlog logger with optional name., ButterflyCandidate, Pydantic models for option data and trade records., A butterfly spread candidate identified by the scanner., Builds butterfly spread orders for Schwab API. (+19 more)

### Community 29 - "run_entry_analysis.py"
Cohesion: 0.13
Nodes (29): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+21 more)

### Community 30 - "SnapshotUnavailableError"
Cohesion: 0.15
Nodes (16): _final_regular_session_close(), Lease, _normalize_chain(), _previous_close(), Any, date, datetime, LeaseKind (+8 more)

### Community 31 - "Domain Model and Ingestion Boundaries"
Cohesion: 0.05
Nodes (40): Actual Schwab Symbol Formats, Backtest Database Chain Rows to Strategy, Broker Mark Versus Computed Mid, ButterflyCandidate, Candidate, Spot, and Daily Bars, code:python (fly_mark_value(lower, center, upper) = lower.mark - 2 * cent), code:text (OptionQuote[]), code:text (External API / asyncpg row / JSON cache) (+32 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.17
Nodes (33): ProfitStateMachine, Evaluates position state and determines exit signals. States: - LOSS: position…, make_pos(), make_settings(), Tests for the profit management state machine., Pre-close exit remains available when explicitly configured., In profit tent with no drawdown → no exit., Should exit when in profit tent + 50% drawdown in morning. (+25 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "test_black_scholes.py"
Cohesion: 0.13
Nodes (16): bs_delta(), Delta — rate of change of price wrt spot., Tests for Black-Scholes pricing and Greeks., ATM call price should be approximately S * sigma * sqrt(T/2pi)., Deep ITM call should be approximately S - K * exp(-rT)., Deep ITM put should be approximately K - S., Expired call should equal intrinsic value., Put-call delta parity: call_delta - put_delta = 1. (+8 more)

### Community 35 - "news.py"
Cohesion: 0.22
Nodes (26): EquityNewsSettings, _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts(), _fetch_alpha_news_for_symbol(), _fetch_json(), fetch_news_impacts(), _fetch_sec_impacts() (+18 more)

### Community 36 - "symbol_directory"
Cohesion: 0.15
Nodes (17): Any, date, datetime, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session., Write a deterministic JSON candle snapshot. (+9 more)

### Community 37 - "is_market_open"
Cohesion: 0.19
Nodes (20): is_market_open(), time, Check if the market is currently open., Check if current time is within the given window (HH:MM strings)., time_in_window(), et(), datetime, Tests for market time utilities. (+12 more)

### Community 38 - "record_equity_market_data.py"
Cohesion: 0.20
Nodes (15): JsonlStreamRecorder, Event, Non-blocking stream handlers backed by one JSONL file per Schwab service., Drain queued events until the stop flag is set and the queue is empty., async_main(), _install_signal_handlers(), main(), parse_args() (+7 more)

### Community 39 - "time_utils.py"
Cohesion: 0.15
Nodes (27): _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_premarket_window(), is_trading_day(), _last_weekday(), market_close_time(), minutes_since_open() (+19 more)

### Community 40 - "state_machine.py"
Cohesion: 0.16
Nodes (11): Enum, ProfitManagementSettings, PositionState, Current state of an open position., ExitSignal, ProfitState, Enum, Profit management state machine for butterfly positions. (+3 more)

### Community 41 - "SessionClose"
Cohesion: 0.16
Nodes (16): Any, Auditable final regular-session SPX close supplied by the shared feed., SessionClose, date, asyncio, datetime, quote(), snapshot() (+8 more)

### Community 42 - "DatabasePool"
Cohesion: 0.08
Nodes (21): Pool, DatabasePool, pool(), Async database connection pool using asyncpg., Manages an asyncpg connection pool for TimescaleDB., Create the connection pool., trade_pnl_dollars(), _load_spot_series() (+13 more)

### Community 43 - "AtomicSnapshotStore"
Cohesion: 0.13
Nodes (23): AtomicSnapshotStore, CandidateFeed, LeaseRegistry, Condition-guarded pointer swap; readers never observe partial snapshots., Persist once and return the canonical evidence for this session., SnapshotArchive, No verified final regular-session close is available from the shared feed., SessionCloseUnavailableError (+15 more)

### Community 44 - "CandidateEvaluator"
Cohesion: 0.20
Nodes (8): candidate_fill_parity_failures(), CandidateEvaluator, CandidatePaperExecutor, Any, Count mark_v1 rows whose fills disagree with their recorded evidence., Mark-price fills only; this object intentionally has no broker methods., _restore_trade(), test_candidate_fill_parity_counts_entry_exit_mismatch_or_missing_evidence()

### Community 45 - "StrategySettings"
Cohesion: 0.10
Nodes (38): StrategySettings, main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date. Replicates the…, per_width_selection_winners(), Return the selected candidate inside each width before cross-width selection., EntryDecision (+30 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.09
Nodes (21): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), date, Path (+13 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (33): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+25 more)

### Community 48 - "run_morning_scan.py"
Cohesion: 0.09
Nodes (31): archive_report(), archive_report_json(), Path, Write the scan report to a dated markdown file under report_dir., Write machine-readable scan internals next to the markdown report., load_liquid_meta(), load_sector_map(), Load symbol -> GICS sector mapping written by refresh_equity_universes. (+23 more)

### Community 49 - "str"
Cohesion: 0.12
Nodes (43): _assert_broker_state_matches_db(), _broker_option_position_symbols(), _broker_option_positions(), _expired_trade_has_broker_settlement(), _explicit_fill_details(), _intent_order_ids(), _json_dict(), _matches_underlying() (+35 more)

### Community 50 - "black_scholes.py"
Cohesion: 0.21
Nodes (14): bs_call_price(), bs_put_price(), bs_theta(), _d1(), _d2(), implied_vol(), Black-Scholes option pricing and Greeks., Back-solve for implied volatility given an option market price. Returns None if… (+6 more)

### Community 51 - "live_performance.py"
Cohesion: 0.17
Nodes (27): chart_payload(), cumulative_equity(), drawdown_series(), DrawdownPoint, duration_minutes(), format_et_time(), is_drawdown_exit(), _money() (+19 more)

### Community 52 - "entry_loop"
Cohesion: 0.13
Nodes (15): entry_loop(), Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window. (+7 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.11
Nodes (18): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Changes Made This Session, Commands Run, Current Cycle Checkpoints, Current Objective, Decisions Made (+10 more)

### Community 54 - "test_trade_chart.py"
Cohesion: 0.22
Nodes (16): entry_chart_window(), parse_hhmm(), time, Return [start_time - lookback, max(start_time, fill)] in the entry timezone., date, Tests for Discord trade chart generation., _sample_candles(), test_build_entry_chart_png_returns_png_bytes() (+8 more)

### Community 55 - "load_config"
Cohesion: 0.12
Nodes (24): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+16 more)

### Community 56 - "Database Compatibility"
Cohesion: 0.09
Nodes (25): `001_initial.sql`: `option_chain_snapshots`, `001_initial.sql`: `spot_prices`, `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, `005_add_daily_bars.sql`, Anonymized Synchronized Data Slice, code:sql (CREATE TABLE IF NOT EXISTS option_chain_snapshots (), code:sql (CREATE TABLE IF NOT EXISTS spot_prices () (+17 more)

### Community 57 - "weekend_review.py"
Cohesion: 0.19
Nodes (26): TradePoint, build_combined_performance_chart_png(), Build one image with weekly, monthly, and all-time equity + drawdown panels., build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption() (+18 more)

### Community 58 - "dict"
Cohesion: 0.11
Nodes (10): dict, ChainQueries, Any, date, datetime, Queries for option_chain_snapshots table., Bulk insert option chain snapshot rows using COPY., Sum of realized PnL for the rolling 7-day window (closed trades only). (+2 more)

### Community 59 - "daily_reset_loop"
Cohesion: 0.06
Nodes (33): daily_reset_loop(), eod_chart_loop(), Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Reset daily risk state at market open. (+25 more)

### Community 60 - "TradeRecord"
Cohesion: 0.18
Nodes (23): A trade record for tracking entry/exit., TradeRecord, BrokerCashSettlement, final_regular_session_close_from_candles(), NamedTuple, Return the latest Schwab 1-minute close in the regular session., _candle(), asyncio (+15 more)

### Community 61 - "RiskQueries"
Cohesion: 0.09
Nodes (19): Protocol, PnL of the last N closed trades (most recent first), for consecutive loss detect, Queries for daily_risk_state table., Dollar PnL of the last N closed trades, most recent first., RiskQueries, ConsecutiveLossNotifier, date, Protocol (+11 more)

### Community 62 - "generate_live_performance.py"
Cohesion: 0.20
Nodes (17): no_trade_reason(), _parse_metadata(), Any, trade_point_from_row(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate() (+9 more)

### Community 63 - "test_synthetic_chain.py"
Cohesion: 0.24
Nodes (12): make_snapshot_time(), datetime, Tests for the synthetic chain generator., Create a snapshot time N minutes before 4pm ET., Volatility skew: OTM puts should have higher IV than equidistant OTM calls., Option price should decrease as expiration approaches., test_atm_call_price_reasonable(), test_generate_chain_has_both_types() (+4 more)

### Community 64 - "synthetic_chain.py"
Cohesion: 0.20
Nodes (6): IVModel, Implied volatility model with VIX scaling and skew adjustment., Models implied volatility with VIX scaling and volatility skew., Convert VIX index value to 0-DTE ATM IV estimate. VIX is the 30-day implied vol…, Compute skew-adjusted IV for a given strike. OTM puts have elevated IV…, Synthetic option chain generator using Black-Scholes + VIX IV model.

### Community 65 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.15
Nodes (8): Any, date, Schwab market-data client deliberately lacking every account/order operation., Authenticate a Schwab client without resolving or retaining an account., ReadOnlySchwabMarketDataClient, asyncio, MonkeyPatch, test_token_refresh_is_retained_in_memory_without_writing_file()

### Community 66 - "universes.py"
Cohesion: 0.05
Nodes (68): EquityScanFilters, EquityScanLimits, load_equity_scan_config(), BaseModel, Path, Configuration for the equity morning scan., Load equity scan settings from YAML., _as_float() (+60 more)

### Community 67 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.24
Nodes (8): _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_performance_stats_reports_outlier_dependence(), test_min_gap_filter_logs_no_trade_before_candidate_selection(), test_min_gap_filter_preserves_direction_above_threshold(), test_review_progress_counts_only_closed_mark_v1_trades()

### Community 68 - "DbDataLoader"
Cohesion: 0.16
Nodes (14): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+6 more)

### Community 69 - "_MetricsHandler"
Cohesion: 0.31
Nodes (5): BaseHTTPRequestHandler, _MetricsHandler, Clear only the recovered subsystem's not-ready reason., HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 70 - "GapRegimeFilter"
Cohesion: 0.15
Nodes (9): GapRegimeFilter, Enum, Market regime classifier for 0-DTE butterfly parameter dispatch. Classifies…, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct (+1 more)

### Community 71 - "test_candidate_provider.py"
Cohesion: 0.32
Nodes (10): Build a synchronous schwab-py handler that never blocks the stream., make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close(), test_http_and_schwab_provider_contracts_normalize_equally() (+2 more)

### Community 72 - "Behavioral Specification"
Cohesion: 0.08
Nodes (23): Algorithmic Refinements For 0-DTE Robustness, Behavioral Specification, Bid-Ask Spread Penalization, Candidate Construction Invariants, code:text (raw_expected_move = underlying_spot * (vix / 100) * sqrt(cla), Current Config Defaults, Current Width And Center Selection Data, Double-Factor Live Gating (+15 more)

### Community 73 - "setup_logging"
Cohesion: 0.36
Nodes (9): Configure structlog with JSON output and correlation IDs., setup_logging(), async_main(), main(), parse_args(), Namespace, Path, Backfill one session of one-minute equity candles from Schwab. (+1 more)

### Community 74 - "run_classifier_sweep.py"
Cohesion: 0.24
Nodes (15): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _summarize_combo(), main() (+7 more)

### Community 75 - "ChainDay"
Cohesion: 0.16
Nodes (21): chain_cache_path(), ChainDay, load_chain_day(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->… (+13 more)

### Community 76 - "scanner.py"
Cohesion: 0.21
Nodes (19): _as_float(), _as_int(), _dedupe_premarket(), filter_movers(), _is_duplicate_premarket(), _live_price(), MarketContext, _mid_bid_ask() (+11 more)

### Community 77 - "report_broker_order_statuses.py"
Cohesion: 0.31
Nodes (12): _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses() (+4 more)

### Community 78 - "position_service.py"
Cohesion: 0.07
Nodes (40): session_date(), BrokerFillError, Broker reported FILLED without complete, consistent execution evidence., broker_cash_settlement_from_transactions(), _chain_spot_price(), PositionService, Any, date (+32 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.17
Nodes (15): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+7 more)

### Community 80 - "run_backtest_db.py"
Cohesion: 0.11
Nodes (32): _asset_drawdowns(), candidate_from_trade_row(), _duration_min(), _floatlist(), _format_et(), _intlist(), parse_args(), _parse_config_time() (+24 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.12
Nodes (20): _match_round_trips_fifo(), parse_trade_transactions(), Parse TRADE transactions into ranked trade results., Pair OPENING and CLOSING legs into round-trip realized P&L., Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting. (+12 more)

### Community 82 - "test_weekend_review.py"
Cohesion: 0.23
Nodes (16): previous_mon_fri(), Return Mon–Fri for the week ending on the Friday before reference., asyncio, date, Tests for weekend review date windows and orchestration., test_calendar_month_to_date(), test_format_performance_caption_includes_stats(), test_latest_fill_model_cohort_does_not_mix_legacy_and_mark_v1() (+8 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.10
Nodes (21): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+13 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - ".generate_chain"
Cohesion: 0.28
Nodes (7): bs_vega(), Vega — sensitivity to 1% change in IV., date, datetime, Minutes until market close on expiration day., Generate full synthetic option chain for one expiration. Args: spot: Underlying…, test_vega_positive()

### Community 87 - ".collect_snapshot"
Cohesion: 0.20
Nodes (7): Any, date, datetime, Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Fetch current chain and store snapshot. Returns row count., Main collector loop — runs while market is open., Parse Schwab callExpDateMap/putExpDateMap into flat rows.

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.27
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.35
Nodes (11): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+3 more)

### Community 91 - "resolve_db_dsn"
Cohesion: 0.28
Nodes (8): Resolve the DB connection string for local backtests. Backtests follow the…, resolve_db_dsn(), asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), test_hypothetical_monitoring_load_uses_collector_only(), test_print_pnl_histogram_overlays_fitted_density(), test_resolve_db_dsn_falls_back_to_config(), test_resolve_db_dsn_uses_config_even_if_database_url_is_set()

### Community 92 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 93 - "ButterflyGuy Fable 5 Refactor Plan"
Cohesion: 0.11
Nodes (18): ButterflyGuy Fable 5 Refactor Plan, Closed Design Decisions, code:text (Use FABLE_REFACTOR_PLAN.md as the project entry point. Start), code:text (Phase 1 is complete. Now read DOMAIN_MODEL.md and the candid), code:text (Phase 2 is complete. Now read BEHAVIORAL_SPEC.md in full. Im), code:text (Phase 3 is complete. Implement the live broker boundary only), Completion Definition, Document Map (+10 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "TradeService"
Cohesion: 0.07
Nodes (44): EntrySettings, _age_seconds(), Any, date, datetime, Orchestrates the full entry/exit trading flow., Full entry flow from eligibility checks through entry fill., Fetch today's 1-min bars from Schwab and run BiasScoreFilter. (+36 more)

### Community 97 - "performance_chart.py"
Cohesion: 0.19
Nodes (18): compute_stats(), ReportStats, build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels(), Axes (+10 more)

### Community 98 - "ButterflyOrderBuilder"
Cohesion: 0.14
Nodes (21): ButterflyOrderBuilder, Any, Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate. (+13 more)

### Community 99 - "test_candidate_variants.py"
Cohesion: 0.42
Nodes (9): _candidate(), _config(), MonkeyPatch, _state(), test_absolute_stop_truncates_never_profitable_loss(), test_gap_conviction_threshold_is_wired_into_candidate_evaluator(), test_peak_trailer_retains_winner_that_profitprotector_floors(), test_target_cost_prefers_debit_target_instead_of_best_rr() (+1 more)

### Community 100 - "_print_same_entry_comparison_table"
Cohesion: 0.25
Nodes (8): _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday…

### Community 101 - "FakeProvider"
Cohesion: 0.42
Nodes (6): candidate(), FakeProvider, market(), asyncio, test_candidate_entry_is_blocked_when_pin_fails(), test_candidate_entry_pins_before_mark_fill()

### Community 102 - "PositionManager"
Cohesion: 0.33
Nodes (4): PositionManager, _quote_quality_ok(), Tracks position value from chain data and manages peak tracking., Reset for a new position. Optionally restore a persisted peak (e.g. after…

### Community 103 - "select_cross_width_candidate"
Cohesion: 0.48
Nodes (6): Choose the final candidate from one best candidate per width. When…, select_cross_width_candidate(), _candidate(), test_cross_width_selection_can_prefer_first_bucket_width(), test_cross_width_selection_prefers_wider_wing_on_rr_tie(), test_cross_width_selection_returns_none_for_empty_pool()

### Community 105 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 106 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 107 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 109 - "bs_gamma"
Cohesion: 0.67
Nodes (3): bs_gamma(), Gamma — rate of change of delta wrt spot., test_gamma_positive()

### Community 111 - "health_monitor.py"
Cohesion: 0.18
Nodes (15): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), Derive a human-readable service name from a health URL. Prefers the ``service``…, Post a message to Discord webhook., Run one full check cycle across all URLs. Returns list of results. (+7 more)

### Community 112 - "AGENTS.md"
Cohesion: 0.13
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 113 - "ButterflyGuy Code Review State"
Cohesion: 0.12
Nodes (16): Architecture map, ButterflyGuy Code Review State, Changes implemented, Commands executed, Confirmed findings, Current phase, Decisions already made, Exact next actions (+8 more)

### Community 114 - "2. Other external and public sources"
Cohesion: 0.11
Nodes (18): 2.1 Yahoo Finance (`yfinance`), 2.2 S&P 500 constituent dataset on GitHub, 2.3 Wikipedia Nasdaq-100 page, 2.4 Nasdaq Trader symbol directories, 2.5 SEC company ticker map and submissions, 2.6 Alpha Vantage earnings calendar and news sentiment, 2.7 Forex Factory economic calendar, 2.8 Local market calendar and clock (+10 more)

### Community 115 - "5. Local files and backtest inputs"
Cohesion: 0.13
Nodes (15): 5.1 Application YAML configuration, 5.2 Environment variables and `.env`, 5.3 `tokens.json`, 5.4 Universe and metadata files, 5.5 Historical minute CSVs, 5.6 Local daily bar cache, 5.7 Local option-chain cache, 5. Local files and backtest inputs (+7 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 127 - "_patch_chain_cache"
Cohesion: 0.11
Nodes (25): _fitted_density_counts(), _force_synthetic_for_date(), _patch_chain_cache(), _print_pnl_histogram(), print_thinkback_checklist(), Patch load_chain_day to return None for `date`, forcing BS synthetic fallback.…, Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets. (+17 more)

### Community 129 - "OptionQuote"
Cohesion: 0.10
Nodes (31): _candidate_mark(), _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes() (+23 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 140 - "XSP Partial-Fill Evidence Plan"
Cohesion: 0.16
Nodes (13): code:bash (uv run python src/butterfly_guy/scripts/report_broker_order_), Completion, Controlled test, Current evidence, Decision, Done criteria, If one occurs naturally, Preconditions (+5 more)

### Community 141 - "order_manager.py"
Cohesion: 0.10
Nodes (34): NamedTuple, get_0dte_expiration(), now_utc(), AmbiguousOrderError, _broker_time(), BrokerFill, _fill_result(), order_ids() (+26 more)

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 156 - "Acceptance Tests"
Cohesion: 0.17
Nodes (11): Acceptance Tests, Completion Gate, Current Reference Test Map, Golden Replay Requirements, Observability Acceptance, Phase 1: Database Adapter Acceptance, Phase 2: Domain And Selection Acceptance, Phase 3: Paper Execution And Lifecycle Acceptance (+3 more)

### Community 157 - "BacktestDataLoader"
Cohesion: 0.21
Nodes (6): BacktestDataLoader, Load all data needed for a single backtest day., Loads historical data from Polygon.io for backtesting., Fetch SPX 1-minute bars for a given date from Polygon., Fetch VIX close for a given date from Polygon., Fetch the actual previous trading day's SPX close for a given date.

### Community 162 - "ButterflyGuy data sources and data types"
Cohesion: 0.18
Nodes (10): 10. Repository evidence map, 4. Shared database tables visible to the same DB account, 6. Canonical and derived analytical data types, 8. Reports, archives, charts, and outbound destinations, 9. Practical limitations and safety notes, At a glance, ButterflyGuy data sources and data types, code:json ({"symbol":"SYNTH_C6315","underlying":"SPX","expiration":"202) (+2 more)

### Community 163 - "Equity candles and order-book recording"
Cohesion: 0.20
Nodes (9): Backfill candles, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:text (data/equity_market_data/BMNR/2026-07-23/candles_1m.json), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_), code:text (data/equity_market_data/BMNR/YYYY-MM-DD/chart_equity.jsonl), Equity candles and order-book recording, Historical limitation, Operational caution (+1 more)

### Community 168 - "butterfly mark"
Cohesion: 0.20
Nodes (10): BUTTERFLYGUY, connectivity visual association, precision visual association, technology visual association, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background (+2 more)

### Community 170 - "test_run_migrations.py"
Cohesion: 0.31
Nodes (5): fake_db(), FakeConnection, asyncio, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 174 - "Configuration Matrix"
Cohesion: 0.20
Nodes (9): Configuration Matrix, Execution And Risk Differences, Max Cost Per Width, Profit Management Regimes, Quote Quality And Peak Tracking, Refactor Requirements, Shared Defaults, Strategy Profile (+1 more)

### Community 175 - "Live Runbook"
Cohesion: 0.22
Nodes (9): code:bash (uv run python src/butterfly_guy/scripts/report_broker_order_), code:bash (docker logs -f --tail=100 butterfly_spx_app), During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery (+1 more)

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (9): High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy (+1 more)

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 185 - "7. Operational and observability data"
Cohesion: 0.25
Nodes (8): 7.1 Prometheus metrics, 7.2 Health and readiness endpoints, 7.3 Structured application logs, 7. Operational and observability data, code:text (butterfly_chain_snapshot_rows{underlying="SPX"} 487), code:json ({"status":"ok","service":"SPX","timestamp":"2026-07-13T18:00), code:json ({"status":"not_ready","reason":"initializing_schwab"}), code:json ({"underlying":"SPX","rows":487,"event":"snapshot_collected",)

### Community 189 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run…, run()

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - "Fixture Manifest"
Cohesion: 0.29
Nodes (6): Config Hashes, Export Rules, Fixture Manifest, Golden Replay Cases, Phase 1 Market-Data Fixtures, Selection Fixtures

### Community 193 - "Offline safety-drill record — 2026-07-13"
Cohesion: 0.29
Nodes (6): Drill findings fixed, Follow-up — 2026-07-14, Offline safety-drill record — 2026-07-13, Remaining do-now work, Result, Verification

### Community 196 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 197 - "Exact-SHA Deployment Proof - 2026-07-15"
Cohesion: 0.33
Nodes (5): Deployment and verification, Exact-SHA Deployment Proof - 2026-07-15, Follow-up rollback and restore drill, Preconditions and validation, Scope

### Community 198 - "XSP Manual-Flatten Evidence - 2026-07-16"
Cohesion: 0.33
Nodes (5): Fail-closed proof, Post-action reconciliation and paper restore, Redacted evidence, Result, XSP Manual-Flatten Evidence - 2026-07-16

### Community 200 - "Butterfly Guy Live-Readiness TODO"
Cohesion: 0.40
Nodes (4): Butterfly Guy Live-Readiness TODO, Current gate, Remaining tasks, Safety boundaries

### Community 201 - "XSP Flat-Runtime Restart Proof - 2026-07-14"
Cohesion: 0.40
Nodes (4): Preconditions, Restart and verification, Scope, XSP Flat-Runtime Restart Proof - 2026-07-14

### Community 202 - "Critical External-Alert Delivery Proof - 2026-07-15"
Cohesion: 0.40
Nodes (4): Critical External-Alert Delivery Proof - 2026-07-15, Implementation reviewed, Scope, Supervised delivery and deduplication result

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **315 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `External sources`, `Local durable data` (+310 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `run_paper_replay.py`, `OptionQuote`, `schwab_client.py`, `test_order_manager.py`, `AppConfig`, `main`, `test_position_manager.py`, `order_manager.py`, `run_single`, `simulation_engine.py`, `state_machine.py`, `CandidateEvaluator`, `StrategySettings`, `str`, `entry_loop`, `TradeRecord`, `position_service.py`, `run_backtest_db.py`, `TradeService`, `ButterflyOrderBuilder`, `test_candidate_variants.py`, `FakeProvider`, `PositionManager`, `select_cross_width_candidate`, `test_candidate_settlement.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `models.py`, `test_order_manager.py`, `load_date_data`, `MarketSnapshot`, `test_position_manager.py`, `run_single`, `MinuteBar`, `feed.py`, `simulation_engine.py`, `core/config.py`, `ButterflyCandidate`, `run_entry_analysis.py`, `SnapshotUnavailableError`, `state_machine.py`, `SessionClose`, `AtomicSnapshotStore`, `StrategySettings`, `TradeRecord`, `synthetic_chain.py`, `DbDataLoader`, `test_candidate_provider.py`, `ChainDay`, `position_service.py`, `run_backtest_db.py`, `.generate_chain`, `report_exit_mark_parity.py`, `TradeService`, `FakeProvider`, `PositionManager`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `schwab_client.py`, `test_order_manager.py`, `universes.py`, `AppConfig`, `record_equity_market_data.py`, `test_run_live.py`, `setup_logging`, `main`, `order_manager.py`, `position_service.py`, `report_broker_order_statuses.py`, `run_morning_scan.py`, `str`, `ButterflyCandidate`, `services/daily_report_card.py`, `TradeRecord`, `TradeService`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 120 inferred relationships involving `str` (e.g. with `.__init__()` and `._get_prev_close()`) actually correct?**
  _`str` has 120 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 30 INFERRED edges - model-reasoned connections that need verification._