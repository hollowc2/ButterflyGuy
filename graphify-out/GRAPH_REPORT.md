# Graph Report - Butterflyguy  (2026-07-27)

## Corpus Check
- 230 files · ~244,171 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3437 nodes · 8994 edges · 160 communities (150 shown, 10 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 875 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a9dc4a19`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ButterflyCandidate
- run_backtest_db.py
- test_collector.py
- test_order_manager.py
- AppConfig
- SchwabClientWrapper
- ButterflyChartSpec
- MarketSnapshot
- test_run_live.py
- discover_options_strategy.py
- DatabasePool
- SnapshotIdentity
- feed.py
- CsvDataLoader
- CandidateRegistry
- forex_calendar.py
- set_readiness
- MinuteBar
- _print_same_entry_comparison_table
- test_comparison_stats.py
- DiscordNotifier
- EquityScanSettings
- 4. Detailed findings
- core/config.py
- str
- report.py
- test_run_backtest_db_defaults.py
- SnapshotArchive
- TradeService
- run_entry_analysis.py
- .get
- Domain Model and Ingestion Boundaries
- ProfitStateMachine
- test_risk_engine.py
- SyntheticChainGenerator
- news.py
- symbol_directory
- time_utils.py
- record_equity_market_data.py
- report_broker_order_statuses.py
- resolve_db_dsn
- test_candidate_snapshot.py
- select_cross_width_candidate
- AtomicSnapshotStore
- test_candidate_evaluator_accounting.py
- StrategySettings
- SchwabDataLoader
- equity_trade_chart.py
- run_morning_scan.py
- _assert_broker_state_matches_db
- live_performance.py
- 9) Capture equity candles and Level II for trade review
- build_daily_report_card
- ButterflyGuy AI Review State
- send_test_chart.py
- load_config
- Database Compatibility
- weekend_review.py
- RiskQueries
- daily_reset_loop
- LeaseRegistry
- date
- generate_live_performance.py
- TelegramNotifier
- entry_loop
- universes.py
- run_classifier_sweep.py
- DbDataLoader
- _MetricsHandler
- GapRegimeFilter
- Behavioral Specification
- ChainDay
- scanner.py
- backfill_equity_candles.py
- ._parse_chain_response
- 1. Charles Schwab API
- load_date_data
- test_daily_report_card.py
- RuntimeError
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- .monitor_loop
- test_candidate_settlement.py
- Shared SPX candidate fleet
- daily_report_card_format.py
- ._record_exit_metrics
- report_exit_mark_parity.py
- ButterflyGuy Fable 5 Refactor Plan
- 2026-07-14 — data audit and research design
- ._parse_chain_to_quotes
- test_position_service_settlement.py
- TradePoint
- ButterflyOrderBuilder
- ._exit_mark_parity_report
- ._extract_quotes
- FakeProvider
- ._record_monitoring_leg_quotes
- report_trade_ladders.py
- .send_pending_eod_charts
- health_monitor.py
- AGENTS.md
- ButterflyGuy Code Review State
- 2. Other external and public sources
- 5. Local files and backtest inputs
- Butterfly Guy
- _print_pnl_histogram
- _patch_chain_cache
- OptionQuote
- Strategy Settings
- XSP Partial-Fill Evidence Plan
- run_live.py
- Width Selection
- Acceptance Tests
- BacktestDataLoader
- ButterflyGuy data sources and data types
- Equity candles and order-book recording
- services/daily_report_card.py
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
- `TestEngineIntegration` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestBiasScore` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestComputeOr` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestComputeVwap` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestEma` --uses--> `DayData`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]

## Communities (160 total, 10 thin omitted)

### Community 0 - "ButterflyCandidate"
Cohesion: 0.11
Nodes (42): NamedTuple, ButterflyCandidate, A butterfly spread candidate identified by the scanner., _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision (+34 more)

### Community 1 - "run_backtest_db.py"
Cohesion: 0.11
Nodes (48): _asset_drawdowns(), backtest_entry_price(), _dd_schedule_label(), _duration_min(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window(), _floatlist() (+40 more)

### Community 2 - "test_collector.py"
Cohesion: 0.24
Nodes (10): asyncio, Integration tests for the option chain collector (requires live Schwab token)., A local JSON cache failure should not fail a DB-backed snapshot., A corrupt optional chain cache should not fail a DB-backed snapshot., Collector should parse chain response into rows., Parsed rows should have the expected fields., test_collect_snapshot_parses_chain(), test_collect_snapshot_row_fields() (+2 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.10
Nodes (88): LiveSpread, NamedTuple, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+80 more)

### Community 4 - "AppConfig"
Cohesion: 0.11
Nodes (39): BaseSettings, assert_candidate_safety(), CandidateAuditContext, CandidateDecisionQueries, CandidatePaperExecutor, CandidatePerformanceStats, config_sha256(), Path (+31 more)

### Community 5 - "SchwabClientWrapper"
Cohesion: 0.07
Nodes (31): SchwabSettings, Any, date, Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order once and return the order ID.          Order placement is not ret, Place an order and return the order ID., Get the status of an order. (+23 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.10
Nodes (40): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+32 more)

### Community 7 - "MarketSnapshot"
Cohesion: 0.12
Nodes (10): candidate_fill_parity_failures(), _candidate_mark(), CandidateEvaluator, Any, Count mark_v1 rows whose fills disagree with their recorded evidence., _aware_utc(), MarketSnapshot, datetime (+2 more)

### Community 8 - "test_run_live.py"
Cohesion: 0.20
Nodes (23): ExecutionSettings, RiskSettings, _assert_live_config_supported(), asyncio, parametrize, _synthetic_butterfly_snapshot(), _synthetic_position(), test_entry_loop_stops_after_unsafe_order_error() (+15 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "DatabasePool"
Cohesion: 0.06
Nodes (35): Pool, Configure structlog with JSON output and correlation IDs., setup_logging(), Start HTTP server serving /metrics (Prometheus) and /health on *port*.      Runs, Start the Prometheus metrics HTTP server., start_metrics_server(), OptionChainCollector, Option chain collector — fetches and stores SPX chain snapshots. (+27 more)

### Community 11 - "SnapshotIdentity"
Cohesion: 0.05
Nodes (39): Lease, SessionContext, Paper-only SPX candidate fleet fed by a shared market-data service., from_dict(), Any, RuntimeError, Immutable normalized market snapshots shared by candidate evaluators., No complete snapshot is currently available. (+31 more)

### Community 12 - "feed.py"
Cohesion: 0.30
Nodes (16): Application, Request, _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs() (+8 more)

### Community 13 - "CsvDataLoader"
Cohesion: 0.16
Nodes (15): DataFrame, _build_bars(), _build_prev_close(), _build_recent_closes(), _build_vix(), _build_vix_bars(), CsvDataLoader, date (+7 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.11
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.11
Nodes (31): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), is_sunday_startup_window() (+23 more)

### Community 16 - "set_readiness"
Cohesion: 0.17
Nodes (17): clear_readiness(), Prometheus metrics for monitoring., Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., Set readiness; ``None`` means the service is ready., readiness_snapshot(), set_readiness(), broker_reconciler_loop() (+9 more)

### Community 17 - "MinuteBar"
Cohesion: 0.07
Nodes (30): MinuteBar, Shared backtest market-data models., Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).  Sch, BiasScoreFilter, _compute_or(), _compute_vwap(), _ema(), Multi-signal directional bias filter for 0-DTE butterfly entries. (+22 more)

### Community 18 - "_print_same_entry_comparison_table"
Cohesion: 0.15
Nodes (13): _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday (+5 more)

### Community 19 - "test_comparison_stats.py"
Cohesion: 0.46
Nodes (7): _print_comparison_table(), _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 20 - "DiscordNotifier"
Cohesion: 0.08
Nodes (20): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook., asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted() (+12 more)

### Community 21 - "EquityScanSettings"
Cohesion: 0.13
Nodes (46): EquityScanSettings, attach_news_impacts(), build_snapshots(), _focus_reasons(), OpeningFocusItem, parse_equity_quote(), passes_filters(), datetime (+38 more)

### Community 22 - "4. Detailed findings"
Cohesion: 0.05
Nodes (47): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Findings summary, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix (+39 more)

### Community 23 - "core/config.py"
Cohesion: 0.07
Nodes (48): ProfitManagementStrategy, DayData, DayResult, _drawdown_rule(), DrawdownWindow, _profit_exit_reason(), datetime, Single-day simulation engine using synthetic option chains. (+40 more)

### Community 24 - "str"
Cohesion: 0.14
Nodes (28): Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Main collector loop — runs while market is open., count_rejected_orders(), _extract_order_id(), _extract_trade_leg(), _float(), _instrument_label(), _is_currency_instrument() (+20 more)

### Community 25 - "report.py"
Cohesion: 0.19
Nodes (29): build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes() (+21 more)

### Community 26 - "test_run_backtest_db_defaults.py"
Cohesion: 0.31
Nodes (8): candidate_from_trade_row(), _parse_for_asset(), test_backtest_parses_exit_arm_sweep_overrides(), test_candidate_from_trade_row_pins_live_trade_fields(), test_default_entry_bar_lookup_rejects_late_fallback(), test_ndx_backtest_drawdown_defaults_match_live_config(), test_spx_backtest_drawdown_defaults_match_live_config(), test_xsp_backtest_drawdown_defaults_match_live_config()

### Community 27 - "SnapshotArchive"
Cohesion: 0.14
Nodes (8): SnapshotArchive, Any, date, Schwab market-data client deliberately lacking every account/order operation., Authenticate a Schwab client without resolving or retaining an account., ReadOnlySchwabMarketDataClient, main(), Run the demand-aware shared SPX candidate market-data feed.

### Community 28 - "TradeService"
Cohesion: 0.06
Nodes (53): EntrySettings, VixWidthBucket, _age_seconds(), Any, date, datetime, Orchestrates the full entry/exit trading flow., Full entry flow from eligibility checks through entry fill. (+45 more)

### Community 29 - "run_entry_analysis.py"
Cohesion: 0.13
Nodes (29): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+21 more)

### Community 30 - ".get"
Cohesion: 0.23
Nodes (10): _final_regular_session_close(), _normalize_chain(), _previous_close(), Any, date, time, Persist once and return the canonical evidence for this session., Return one cached, verified final regular-session SPX close per date. (+2 more)

### Community 31 - "Domain Model and Ingestion Boundaries"
Cohesion: 0.05
Nodes (40): Actual Schwab Symbol Formats, Backtest Database Chain Rows to Strategy, Broker Mark Versus Computed Mid, ButterflyCandidate, Candidate, Spot, and Daily Bars, code:python (fly_mark_value(lower, center, upper) = lower.mark - 2 * cent), code:text (OptionQuote[]), code:text (External API / asyncpg row / JSON cache) (+32 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.05
Nodes (73): BaseModel, Enum, CollectorSettings, ConfigModel, DatabaseSettings, MonitoringSettings, PeakTrackingSettings, ProfitManagementSettings (+65 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SyntheticChainGenerator"
Cohesion: 0.05
Nodes (58): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+50 more)

### Community 35 - "news.py"
Cohesion: 0.22
Nodes (26): EquityNewsSettings, _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts(), _fetch_alpha_news_for_symbol(), _fetch_json(), fetch_news_impacts(), _fetch_sec_impacts() (+18 more)

### Community 36 - "symbol_directory"
Cohesion: 0.15
Nodes (17): Any, date, datetime, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session., Write a deterministic JSON candle snapshot. (+9 more)

### Community 37 - "time_utils.py"
Cohesion: 0.08
Nodes (51): _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_premarket_window(), is_trading_day(), _last_weekday(), market_close_time() (+43 more)

### Community 38 - "record_equity_market_data.py"
Cohesion: 0.20
Nodes (15): JsonlStreamRecorder, Event, Non-blocking stream handlers backed by one JSONL file per Schwab service., Drain queued events until the stop flag is set and the queue is empty., async_main(), _install_signal_handlers(), main(), parse_args() (+7 more)

### Community 39 - "report_broker_order_statuses.py"
Cohesion: 0.31
Nodes (12): _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses() (+4 more)

### Community 40 - "resolve_db_dsn"
Cohesion: 0.22
Nodes (10): Resolve the DB connection string for local backtests.      Backtests follow the, Resolve the DB connection string for local backtests.      Backtests follow the, resolve_db_dsn(), asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), test_fitted_density_counts_returns_bucket_heights(), test_hypothetical_monitoring_load_uses_collector_only(), test_print_pnl_histogram_overlays_fitted_density() (+2 more)

### Community 41 - "test_candidate_snapshot.py"
Cohesion: 0.36
Nodes (11): asyncio, datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry(), test_long_poll_never_replays_same_sequence(), test_new_lease_wakes_idle_feed() (+3 more)

### Community 42 - "select_cross_width_candidate"
Cohesion: 0.48
Nodes (6): Choose the final candidate from one best candidate per width.      When `prefer_, select_cross_width_candidate(), _candidate(), test_cross_width_selection_can_prefer_first_bucket_width(), test_cross_width_selection_prefers_wider_wing_on_rr_tie(), test_cross_width_selection_returns_none_for_empty_pool()

### Community 43 - "AtomicSnapshotStore"
Cohesion: 0.14
Nodes (16): AtomicSnapshotStore, CandidateFeed, Condition-guarded pointer swap; readers never observe partial snapshots., FakeArchive, FakeDb, FakeMarket, FakePool, asyncio (+8 more)

### Community 44 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.20
Nodes (10): candidate_performance_stats(), Summarize one chronological, closed mark_v1 PnL cohort., _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_performance_stats_reports_outlier_dependence(), test_min_gap_filter_logs_no_trade_before_candidate_selection() (+2 more)

### Community 45 - "StrategySettings"
Cohesion: 0.08
Nodes (41): StrategySettings, main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date.  Replicates the synthet, per_width_selection_winners(), Select the best butterfly candidate for a single wing width., Cross-width selection. (+33 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.09
Nodes (21): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), date, Path (+13 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (32): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+24 more)

### Community 48 - "run_morning_scan.py"
Cohesion: 0.09
Nodes (31): archive_report(), archive_report_json(), Path, Write the scan report to a dated markdown file under report_dir., Write machine-readable scan internals next to the markdown report., load_liquid_meta(), load_sector_map(), Load symbol -> GICS sector mapping written by refresh_equity_universes. (+23 more)

### Community 49 - "_assert_broker_state_matches_db"
Cohesion: 0.14
Nodes (30): _assert_broker_state_matches_db(), _broker_option_position_symbols(), _broker_option_positions(), _expired_trade_has_broker_settlement(), _matches_underlying(), _open_trade_symbols(), date, _reconcile_broker_state() (+22 more)

### Community 50 - "live_performance.py"
Cohesion: 0.15
Nodes (28): max_drawdown(), chart_payload(), cumulative_equity(), DrawdownPoint, duration_minutes(), format_et_time(), is_drawdown_exit(), _money() (+20 more)

### Community 51 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 52 - "build_daily_report_card"
Cohesion: 0.17
Nodes (16): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, load_daily_report_card_config(), BaseModel, Path (+8 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.11
Nodes (18): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Changes Made This Session, Commands Run, Current Cycle Checkpoints, Current Objective, Decisions Made (+10 more)

### Community 54 - "send_test_chart.py"
Cohesion: 0.24
Nodes (11): trade_pnl_dollars(), _load_spot_series(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., _spot_rows_to_candles(), load_spot_series(), date (+3 more)

### Community 55 - "load_config"
Cohesion: 0.12
Nodes (24): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+16 more)

### Community 56 - "Database Compatibility"
Cohesion: 0.09
Nodes (25): `001_initial.sql`: `option_chain_snapshots`, `001_initial.sql`: `spot_prices`, `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, `005_add_daily_bars.sql`, Anonymized Synchronized Data Slice, code:sql (CREATE TABLE IF NOT EXISTS option_chain_snapshots (), code:sql (CREATE TABLE IF NOT EXISTS spot_prices () (+17 more)

### Community 57 - "weekend_review.py"
Cohesion: 0.13
Nodes (36): build_eod_chart_for_row(), calendar_month_to_date(), fetch_closed_trades(), format_review_header(), format_trade_recap(), latest_fill_model_cohort(), _parse_metadata(), _post_with_delay() (+28 more)

### Community 58 - "RiskQueries"
Cohesion: 0.06
Nodes (18): dict, Protocol, OrderIntentQueries, Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Sum of realized PnL for the rolling 7-day window (closed trades only). (+10 more)

### Community 59 - "daily_reset_loop"
Cohesion: 0.05
Nodes (43): daily_reset_loop(), eod_chart_loop(), Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Reset daily risk state at market open. (+35 more)

### Community 60 - "LeaseRegistry"
Cohesion: 0.31
Nodes (3): LeaseRegistry, datetime, LeaseKind

### Community 61 - "date"
Cohesion: 0.20
Nodes (6): date, Overwrite realized_pnl in risk state (SET, not ADD).         Used at startup to, Record that a trade was executed., Record realized dollar PnL., Overwrite dollar realized_pnl in risk state (SET, not ADD).         Used at star, Manually sync the trade count in the risk state table.         Used at startup t

### Community 62 - "generate_live_performance.py"
Cohesion: 0.18
Nodes (18): no_trade_reason(), _parse_metadata(), Any, trade_point_from_row(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate() (+10 more)

### Community 63 - "TelegramNotifier"
Cohesion: 0.50
Nodes (3): Sends risk notifications through the existing Telegram notify helper., Sends risk notifications through the existing Telegram notify helper., TelegramNotifier

### Community 65 - "entry_loop"
Cohesion: 0.08
Nodes (23): entry_loop(), Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window. (+15 more)

### Community 66 - "universes.py"
Cohesion: 0.05
Nodes (68): EquityScanFilters, EquityScanLimits, load_equity_scan_config(), BaseModel, Path, Configuration for the equity morning scan., Load equity scan settings from YAML., _as_float() (+60 more)

### Community 67 - "run_classifier_sweep.py"
Cohesion: 0.19
Nodes (17): max_consecutive_losses(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _summarize_combo(), main(), parse_args() (+9 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.16
Nodes (14): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+6 more)

### Community 69 - "_MetricsHandler"
Cohesion: 0.36
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 70 - "GapRegimeFilter"
Cohesion: 0.15
Nodes (9): GapRegimeFilter, Enum, Market regime classifier for 0-DTE butterfly parameter dispatch.  Classifies eac, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct (+1 more)

### Community 72 - "Behavioral Specification"
Cohesion: 0.08
Nodes (23): Algorithmic Refinements For 0-DTE Robustness, Behavioral Specification, Bid-Ask Spread Penalization, Candidate Construction Invariants, code:text (raw_expected_move = underlying_spot * (vix / 100) * sqrt(cla), Current Config Defaults, Current Width And Center Selection Data, Double-Factor Live Gating (+15 more)

### Community 75 - "ChainDay"
Cohesion: 0.15
Nodes (23): chain_cache_path(), ChainDay, load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.  Forma (+15 more)

### Community 76 - "scanner.py"
Cohesion: 0.18
Nodes (21): _as_float(), _as_int(), _dedupe_premarket(), filter_movers(), _is_duplicate_premarket(), _live_price(), MarketContext, _mid_bid_ask() (+13 more)

### Community 77 - "backfill_equity_candles.py"
Cohesion: 0.46
Nodes (7): async_main(), main(), parse_args(), Namespace, Path, Backfill one session of one-minute equity candles from Schwab., run()

### Community 78 - "._parse_chain_response"
Cohesion: 0.40
Nodes (4): Any, date, datetime, Parse Schwab callExpDateMap/putExpDateMap into flat rows.

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.15
Nodes (16): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+8 more)

### Community 80 - "load_date_data"
Cohesion: 0.06
Nodes (49): discover_dates(), get_prev_close(), get_recent_closes(), get_vix_at(), get_vix_prev_close(), get_vix_snapshot_at(), load_bars_from_db(), load_date_data() (+41 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.15
Nodes (18): parse_trade_transactions(), rank_trades(), Parse TRADE transactions into ranked trade results., Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options). (+10 more)

### Community 82 - "RuntimeError"
Cohesion: 0.16
Nodes (16): RuntimeError, account_hash(), client(), Authenticate and resolve account hash., pool(), _explicit_fill_details(), _intent_order_ids(), _json_dict() (+8 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.10
Nodes (21): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+13 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - ".monitor_loop"
Cohesion: 0.14
Nodes (16): _chain_spot_price(), final_regular_session_close_from_candles(), date, datetime, RuntimeError, Monitor position every 10s, evaluate state machine, trigger exit if needed., Return the latest Schwab 1-minute close in the regular session., Monitors open positions and manages exits via the profit state machine. (+8 more)

### Community 87 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.27
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 91 - "._record_exit_metrics"
Cohesion: 0.18
Nodes (10): Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine., Record trade exit metrics and update risk engine. (+2 more)

### Community 92 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 93 - "ButterflyGuy Fable 5 Refactor Plan"
Cohesion: 0.11
Nodes (18): ButterflyGuy Fable 5 Refactor Plan, Closed Design Decisions, code:text (Use FABLE_REFACTOR_PLAN.md as the project entry point. Start), code:text (Phase 1 is complete. Now read DOMAIN_MODEL.md and the candid), code:text (Phase 2 is complete. Now read BEHAVIORAL_SPEC.md in full. Im), code:text (Phase 3 is complete. Implement the live broker boundary only), Completion Definition, Document Map (+10 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "._parse_chain_to_quotes"
Cohesion: 0.06
Nodes (35): Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Parse Schwab chain response into OptionQuote objects., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Fetch today's 1-min bars from Schwab and run BiasScoreFilter. (+27 more)

### Community 96 - "test_position_service_settlement.py"
Cohesion: 0.21
Nodes (17): _candle(), asyncio, datetime, parametrize, RuntimeError, Tests for cash-settlement spot selection., test_broker_cash_settlement_uses_actual_cash_and_fees(), test_cash_settlement_db_failure_stops_after_one_close_attempt() (+9 more)

### Community 97 - "TradePoint"
Cohesion: 0.18
Nodes (23): compute_stats(), drawdown_series(), ReportStats, TradePoint, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl() (+15 more)

### Community 98 - "ButterflyOrderBuilder"
Cohesion: 0.13
Nodes (22): ButterflyOrderBuilder, Any, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure.  These tests check th (+14 more)

### Community 100 - "._exit_mark_parity_report"
Cohesion: 0.20
Nodes (9): Record trade exit metrics and update risk engine., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot., Compare live Schwab exit marks with the nearest DB collector snapshot. (+1 more)

### Community 102 - "._extract_quotes"
Cohesion: 0.17
Nodes (11): Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation., Extract the three butterfly leg quotes from the chain for position valuation. (+3 more)

### Community 105 - "FakeProvider"
Cohesion: 0.42
Nodes (6): candidate(), FakeProvider, market(), asyncio, test_candidate_entry_is_blocked_when_pin_fails(), test_candidate_entry_pins_before_mark_fill()

### Community 106 - "._record_monitoring_leg_quotes"
Cohesion: 0.20
Nodes (9): Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing., Compare live Schwab exit marks with the nearest DB collector snapshot., Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing., Persist the three live-polled legs so DB replay can match monitor timing. (+1 more)

### Community 107 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 108 - ".send_pending_eod_charts"
Cohesion: 0.25
Nodes (7): Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close., Send full-session EOD charts for closed trades after market close., Record trade exit metrics and update risk engine., Send full-session EOD charts for closed trades after market close.

### Community 111 - "health_monitor.py"
Cohesion: 0.18
Nodes (15): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), Derive a human-readable service name from a health URL.      Prefers the ``servi, Post a message to Discord webhook., Run one full check cycle across all URLs. Returns list of results. (+7 more)

### Community 112 - "AGENTS.md"
Cohesion: 0.13
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 113 - "ButterflyGuy Code Review State"
Cohesion: 0.12
Nodes (16): Architecture map, ButterflyGuy Code Review State, Changes implemented, Commands executed, Confirmed findings, Current phase, Decisions already made, Exact next actions (+8 more)

### Community 114 - "2. Other external and public sources"
Cohesion: 0.11
Nodes (19): 2.1 Yahoo Finance (`yfinance`), 2.2 S&P 500 constituent dataset on GitHub, 2.3 Wikipedia Nasdaq-100 page, 2.4 Nasdaq Trader symbol directories, 2.5 SEC company ticker map and submissions, 2.6 Alpha Vantage earnings calendar and news sentiment, 2.7 Forex Factory economic calendar, 2.8 Local market calendar and clock (+11 more)

### Community 115 - "5. Local files and backtest inputs"
Cohesion: 0.13
Nodes (15): 5.1 Application YAML configuration, 5.2 Environment variables and `.env`, 5.3 `tokens.json`, 5.4 Universe and metadata files, 5.5 Historical minute CSVs, 5.6 Local daily bar cache, 5.7 Local option-chain cache, 5. Local files and backtest inputs (+7 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 127 - "_print_pnl_histogram"
Cohesion: 0.06
Nodes (36): _fitted_density_counts(), _print_pnl_histogram(), print_thinkback_checklist(), Use the first regular-session snapshot for gap direction., Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., ASCII histogram with a fitted density curve overlaid on the trade buckets., Print a per-trade ToS ThinkBack validation checklist. (+28 more)

### Community 128 - "_patch_chain_cache"
Cohesion: 0.10
Nodes (22): _force_synthetic_for_date(), merge_chains(), _patch_chain_cache(), Patch load_chain_day to return None for `date`, forcing BS synthetic fallback., ASCII histogram with a fitted density curve overlaid on the trade buckets., Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains., Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains., Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains. (+14 more)

### Community 129 - "OptionQuote"
Cohesion: 0.05
Nodes (63): BoundLogger, DB-backed data loader for historical SPX + VIX data.  Reads from the live Timesc, get_logger(), Structured logging setup with structlog., Get a structlog logger with optional name., now_eastern(), session_date(), iter_chain_options() (+55 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 140 - "XSP Partial-Fill Evidence Plan"
Cohesion: 0.16
Nodes (13): code:bash (uv run python src/butterfly_guy/scripts/report_broker_order_), Completion, Controlled test, Current evidence, Decision, Done criteria, If one occurs naturally, Preconditions (+5 more)

### Community 141 - "run_live.py"
Cohesion: 0.06
Nodes (54): get_0dte_expiration(), now_utc(), Fetch current chain and store snapshot. Returns row count., AmbiguousOrderError, _broker_time(), BrokerFill, BrokerFillError, _fill_result() (+46 more)

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

### Community 166 - "services/daily_report_card.py"
Cohesion: 0.26
Nodes (12): archive_report(), date, Path, chartable_equity_trades(), format_equity_trade_chart_caption(), date, datetime, Path (+4 more)

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
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log.  Usage:     uv, run()

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
- **317 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `External sources`, `Local durable data` (+312 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `OptionQuote` connect `OptionQuote` to `ButterflyCandidate`, `run_backtest_db.py`, `test_order_manager.py`, `AppConfig`, `MarketSnapshot`, `SnapshotIdentity`, `feed.py`, `SnapshotArchive`, `TradeService`, `run_entry_analysis.py`, `.get`, `ProfitStateMachine`, `SyntheticChainGenerator`, `test_candidate_snapshot.py`, `AtomicSnapshotStore`, `StrategySettings`, `LeaseRegistry`, `DbDataLoader`, `ChainDay`, `load_date_data`, `report_exit_mark_parity.py`, `._parse_chain_to_quotes`, `._exit_mark_parity_report`, `._extract_quotes`, `FakeProvider`, `._record_monitoring_leg_quotes`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `OptionQuote`, `run_backtest_db.py`, `test_order_manager.py`, `AppConfig`, `MarketSnapshot`, `DatabasePool`, `run_live.py`, `core/config.py`, `test_run_backtest_db_defaults.py`, `TradeService`, `ProfitStateMachine`, `select_cross_width_candidate`, `StrategySettings`, `entry_loop`, `.monitor_loop`, `test_candidate_settlement.py`, `ButterflyOrderBuilder`, `._exit_mark_parity_report`, `._extract_quotes`, `FakeProvider`, `._record_monitoring_leg_quotes`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `AppConfig` connect `AppConfig` to `ProfitStateMachine`, `run_backtest_db.py`, `OptionQuote`, `test_collector.py`, `MarketSnapshot`, `test_run_live.py`, `FakeProvider`, `DatabasePool`, `test_candidate_evaluator_accounting.py`, `run_live.py`, `CandidateRegistry`, `load_config`, `core/config.py`, `TradeService`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 120 inferred relationships involving `str` (e.g. with `.__init__()` and `._get_prev_close()`) actually correct?**
  _`str` has 120 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 30 INFERRED edges - model-reasoned connections that need verification._