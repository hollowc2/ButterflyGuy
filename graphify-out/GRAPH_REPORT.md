# Graph Report - butterfly-gateway-readiness  (2026-08-03)

## Corpus Check
- 261 files · ~251,411 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3423 nodes · 8928 edges · 177 communities (160 shown, 17 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 718 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cc25b3df`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- .refresh
- EntrySelectionResult
- test_order_manager.py
- test_position_service_settlement.py
- SchwabClientWrapper
- ButterflyChartSpec
- FakeAccessFunctionFactory
- test_run_live.py
- discover_options_strategy.py
- TradeService
- test_candidate_evaluator_accounting.py
- 4. Detailed findings
- CsvDataLoader
- CandidateRegistry
- forex_calendar.py
- MarketSnapshot
- MinuteBar
- download_schwab_cache.py
- test_comparison_stats.py
- ChainDay
- test_equity_scan.py
- TokenManagerState
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- test_collector.py
- send_daily_report_card
- upstream.py
- token_manager.py
- GatewaySettings
- Domain Model and Ingestion Boundaries
- ProfitStateMachine
- test_risk_engine.py
- SyntheticChainGenerator
- news.py
- setup_logging
- date
- run_single
- Current Schwab Integration
- SchwabSettings
- SessionClose
- api.py
- feed.py
- ButterflyCandidate
- send_alertmanager
- SchwabDataLoader
- equity_trade_chart.py
- equity_scan/config.py
- _assert_broker_state_matches_db
- report_exit_mark_parity.py
- performance_chart.py
- Target Trading Platform
- ButterflyGuy AI Review State
- run_morning_scan.py
- load_config
- Database Compatibility
- weekend_review.py
- StrategySettings
- Schwab Gateway Migration Plan
- select_entry_candidate
- create_app
- run_entry_analysis.py
- report_trade_ladders.py
- ButterflyGuy Code Review State
- is_market_open
- universes.py
- NamedTuple
- DbDataLoader
- core/config.py
- GapRegimeFilter
- test_candidate_provider.py
- Behavioral Specification
- .should_trade
- DiscordNotifier
- chain_cache.py
- scanner.py
- live_performance.py
- find_entry_in_window
- 1. Charles Schwab API
- test_run_backtest_db_defaults.py
- test_daily_report_card.py
- run_live.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- ConsecutiveLossNotifier
- report_broker_order_statuses.py
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- test_close_trade_only_closes_an_open_trade_once
- OptionQuote
- ButterflyGuy Fable 5 Refactor Plan
- 2026-07-14 — data audit and research design
- Codex Project State
- client.py
- Capability recorder design
- test_order_preview.py
- Schwab Single-Token Manager
- XSP Opportunistic Partial-Fill Evidence Plan
- CandidatePaperExecutor
- resolve_db_dsn
- redact
- run_classifier_sweep.py
- report_selection_parity.py
- TokenTransaction
- ButterflyGuy data sources — representative samples
- Schwab Gateway Foundation: Local Run
- run_backtest_db.py
- Butterfly Guy Live-Readiness TODO
- health_monitor.py
- AGENTS.md
- BaseModel
- 2. Other external and public sources
- 5. Local files and backtest inputs
- Enum
- Protocol
- RuntimeError
- Butterfly Guy
- AppConfig
- RiskQueries
- TestEma
- test_run_migrations.py
- Schwab Gateway Foundation Smoke Test
- TokenManagerHealth
- DatabasePool
- 9) Capture equity candles and Level II for trade review
- test_position_manager.py
- _MetricsHandler
- Strategy Settings
- AtomicTokenManager
- select_cross_width_candidate
- order_manager.py
- Width Selection
- Acceptance Tests
- ButterflyGuy data sources and data types
- Equity candles and order-book recording
- butterfly mark
- test_gateway_token_manager.py
- Configuration Matrix
- Live Runbook
- Layered Risk Management
- Geometric butterfly icon
- 7. Operational and observability data
- 3) Start the SPX stack in Docker
- Fixture Manifest
- Offline safety-drill record — 2026-07-13
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
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
2. `OptionQuote` - 100 edges
3. `SchwabClientWrapper` - 84 edges
4. `AppConfig` - 75 edges
5. `MinuteBar` - 67 edges
6. `MarketSnapshot` - 63 edges
7. `DatabasePool` - 59 edges
8. `SnapshotIdentity` - 52 edges
9. `StrategySettings` - 50 edges
10. `load_config()` - 48 edges

## Surprising Connections (you probably didn't know these)
- `TestEma` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
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

## Communities (177 total, 17 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.10
Nodes (41): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close() (+33 more)

### Community 1 - ".refresh"
Cohesion: 0.15
Nodes (13): RLock, Validate only the stable schwab-py token envelope and required OAuth fields., Run one fake/replaceable refresh callback under the exclusive token lock., Run an SDK-shaped token read/client operation/write lifecycle under one lock., Keep SDK token callbacks live only for one manager-owned transaction., _ScopedTokenCallbacks, TokenCallbackScopeError, TokenRefreshError (+5 more)

### Community 2 - "EntrySelectionResult"
Cohesion: 0.27
Nodes (13): EntrySelectionResult, build_entry_selection_parity(), _candidate_payload(), _per_width_payload(), Compare live Schwab entry selection against nearest DB chain snapshot., Return a JSON-serializable Schwab vs DB selection comparison., Result of a single entry selection pass., _candidate() (+5 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.16
Nodes (58): LiveSpread, NamedTuple, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+50 more)

### Community 4 - "test_position_service_settlement.py"
Cohesion: 0.20
Nodes (19): final_regular_session_close_from_candles(), Return the latest Schwab 1-minute close in the regular session., _candle(), asyncio, datetime, parametrize, RuntimeError, Tests for cash-settlement spot selection. (+11 more)

### Community 5 - "SchwabClientWrapper"
Cohesion: 0.04
Nodes (45): Start HTTP server serving /metrics (Prometheus) and /health on *port*. Runs in…, start_metrics_server(), CollectorMarketDataProvider, DirectSchwabMarketDataProvider, MarketMoversProvider, OptionChainProvider, PriceHistoryProvider, Any (+37 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.11
Nodes (40): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+32 more)

### Community 7 - "FakeAccessFunctionFactory"
Cohesion: 0.37
Nodes (16): adapter(), FakeAccessFunctionFactory, manager(), MonkeyPatch, Path, Mimic schwab-py 1.5.1 TokenMetadata wrapping without importing schwab., test_concurrent_client_operations_cover_construction_and_cannot_lose_rotation(), test_each_metadata_wrapped_rotation_is_persisted_before_callback_returns() (+8 more)

### Community 8 - "test_run_live.py"
Cohesion: 0.17
Nodes (26): Add a not-ready reason; ``None`` explicitly resets all reasons., readiness_snapshot(), set_readiness(), test_health_stays_live_while_ready_reports_degraded(), test_readiness_recovery_clears_only_its_own_reason(), test_readiness_tracks_degraded_reason(), _never_awaited(), asyncio (+18 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "TradeService"
Cohesion: 0.12
Nodes (22): _age_seconds(), Any, date, datetime, Orchestrates the full entry/exit trading flow., Full entry flow from eligibility checks through entry fill., Return the first regular-session open for the requested Eastern date., Fetch today's 1-min bars from Schwab and run BiasScoreFilter. (+14 more)

### Community 11 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.20
Nodes (10): candidate_performance_stats(), Summarize one chronological, closed mark_v1 PnL cohort., _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_performance_stats_reports_outlier_dependence(), test_min_gap_filter_logs_no_trade_before_candidate_selection() (+2 more)

### Community 12 - "4. Detailed findings"
Cohesion: 0.04
Nodes (45): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix, 6. Duplication map (+37 more)

### Community 13 - "CsvDataLoader"
Cohesion: 0.25
Nodes (8): DataFrame, CsvDataLoader, date, Path, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files…

### Community 14 - "CandidateRegistry"
Cohesion: 0.12
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "MarketSnapshot"
Cohesion: 0.06
Nodes (29): Lease, SessionContext, Paper-only SPX candidate fleet fed by a shared market-data service., _aware_utc(), MarketSnapshot, datetime, RuntimeError, Immutable normalized market snapshots shared by candidate evaluators. (+21 more)

### Community 17 - "MinuteBar"
Cohesion: 0.09
Nodes (23): CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, MinuteBar, Shared backtest market-data models., DB-backed data loader for historical SPX + VIX data. Reads from the live…, Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).…, BiasScoreFilter, Multi-signal directional bias filter for 0-DTE butterfly entries., High and low of the opening range (bars with ET time < 09:45). Edge case: no OR… (+15 more)

### Community 18 - "download_schwab_cache.py"
Cohesion: 0.27
Nodes (10): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), date_range(), main() (+2 more)

### Community 19 - "test_comparison_stats.py"
Cohesion: 0.46
Nodes (7): _print_comparison_table(), _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 20 - "ChainDay"
Cohesion: 0.33
Nodes (9): dict, ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log…, day_with_monitoring_bars(), Add live monitor timestamps to bar iteration while carrying nearest spot…, _bar(), datetime, test_day_with_monitoring_bars_adds_live_poll_timestamps() (+1 more)

### Community 21 - "test_equity_scan.py"
Cohesion: 0.17
Nodes (35): EquityScanSettings, build_snapshots(), parse_equity_quote(), passes_filters(), datetime, _quote_age_seconds(), rank_catalyst_watch(), rank_scan_results() (+27 more)

### Community 22 - "TokenManagerState"
Cohesion: 0.11
Nodes (25): Deterministic fake-only readiness provider for the demo runner., StaticTokenReadinessProvider, authentication_middleware(), hash_api_key(), InternalKeyAuthenticator, InternalPrincipal, middleware, Path (+17 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.08
Nodes (47): ProfitManagementStrategy, nearest_snapshot(), Return quotes from the most recent snapshot at or before bar_ts., DayData, DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains. (+39 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.13
Nodes (38): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, BaseModel, ReportCardThresholds, count_rejected_orders() (+30 more)

### Community 25 - "report.py"
Cohesion: 0.18
Nodes (29): build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes() (+21 more)

### Community 26 - "test_collector.py"
Cohesion: 0.24
Nodes (10): asyncio, Integration tests for the option chain collector (requires live Schwab token)., A local JSON cache failure should not fail a DB-backed snapshot., A corrupt optional chain cache should not fail a DB-backed snapshot., Collector should parse chain response into rows., Parsed rows should have the expected fields., test_collect_snapshot_parses_chain(), test_collect_snapshot_row_fields() (+2 more)

### Community 27 - "send_daily_report_card"
Cohesion: 0.24
Nodes (10): archive_report(), date, Path, chartable_equity_trades(), date, datetime, Path, send_daily_report_card() (+2 more)

### Community 28 - "upstream.py"
Cohesion: 0.13
Nodes (21): EquityQuoteProvider, datetime, field_validator, QuoteV1, DirectSchwabQuoteUpstream, _event_time(), _integer(), normalize_schwab_quote() (+13 more)

### Community 29 - "token_manager.py"
Cohesion: 0.11
Nodes (21): AtomicFileTokenStore, _AtomicFileTokenTransaction, _fsync_directory(), Any, Path, RuntimeError, Locked, atomic token persistence without a Schwab runtime dependency., A refresh callback uses this to classify an upstream revocation. (+13 more)

### Community 30 - "GatewaySettings"
Cohesion: 0.13
Nodes (13): GatewayClientSettings, BaseSettings, model_validator, Opt-in client configuration; direct access remains the safe default., GatewaySettings, BaseSettings, field_validator, Validated configuration for the isolated gateway process. (+5 more)

### Community 31 - "Domain Model and Ingestion Boundaries"
Cohesion: 0.07
Nodes (28): Actual Schwab Symbol Formats, Backtest Database Chain Rows to Strategy, Broker Mark Versus Computed Mid, ButterflyCandidate, Candidate, Spot, and Daily Bars, Collector Schwab Chain to Database, Configuration Schemas, Core Domain Types (+20 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.08
Nodes (52): ProfitManagementSettings, QuoteQualitySettings, PositionState, Current state of an open position., ExitSignal, ProfitState, ProfitStateMachine, Enum (+44 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SyntheticChainGenerator"
Cohesion: 0.05
Nodes (60): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+52 more)

### Community 35 - "news.py"
Cohesion: 0.20
Nodes (27): EquityNewsSettings, _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts(), _fetch_alpha_news_for_symbol(), _fetch_json(), fetch_news_impacts(), _fetch_sec_impacts() (+19 more)

### Community 36 - "setup_logging"
Cohesion: 0.07
Nodes (44): Configure structlog with JSON output and correlation IDs., setup_logging(), JsonlStreamRecorder, Any, date, datetime, Event, Path (+36 more)

### Community 37 - "date"
Cohesion: 0.22
Nodes (5): date, Record that a trade was executed., Record realized dollar PnL., Overwrite dollar realized_pnl in risk state (SET, not ADD). Used at startup to…, Manually sync the trade count in the risk state table. Used at startup to…

### Community 38 - "run_single"
Cohesion: 0.13
Nodes (25): backtest_entry_price(), _dd_schedule_label(), _force_synthetic_for_date(), _live_width_label(), load_asset_config(), load_monitoring_chains(), main(), merge_chains() (+17 more)

### Community 39 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 40 - "SchwabSettings"
Cohesion: 0.17
Nodes (17): RiskSettings, SchwabSettings, _assert_live_config_supported(), asyncio, MonkeyPatch, test_token_refresh_is_retained_in_memory_without_writing_file(), test_live_config_allows_confirmed_xsp_canary(), test_live_config_allows_spx_live_when_explicitly_confirmed() (+9 more)

### Community 41 - "SessionClose"
Cohesion: 0.17
Nodes (11): Any, Auditable final regular-session SPX close supplied by the shared feed., SessionClose, date, _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence() (+3 more)

### Community 42 - "api.py"
Cohesion: 0.15
Nodes (24): Transport-neutral client contracts for the internal Schwab gateway., GatewayErrorDetailV1, GatewayErrorV1, GatewayHealthV1, GatewayModel, GatewayReadinessV1, BaseModel, QuoteResponseV1 (+16 more)

### Community 43 - "feed.py"
Cohesion: 0.05
Nodes (63): _after_identity(), AtomicSnapshotStore, CandidateFeed, create_app(), _delete_lease(), _final_regular_session_close(), _float_query(), _health() (+55 more)

### Community 44 - "ButterflyCandidate"
Cohesion: 0.09
Nodes (25): candidate_fill_parity_failures(), _candidate_mark(), CandidateEvaluator, Any, Count mark_v1 rows whose fills disagree with their recorded evidence., _restore_trade(), ButterflyCandidate, A butterfly spread candidate identified by the scanner. (+17 more)

### Community 45 - "send_alertmanager"
Cohesion: 0.12
Nodes (16): asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_alertmanager_payload_has_stable_redacted_fingerprint(), test_notify_entry_includes_trade_stats(), test_notify_exit_formats_contract_pnl_as_dollars() (+8 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.14
Nodes (11): date, Path, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day., Loads SPY 1-minute bars from Schwab, scaled to SPX price levels. Reuses the…, Fetch SPX daily open from yfinance for SPY→SPX calibration., Fetch VIX daily close from yfinance. (+3 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (31): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+23 more)

### Community 48 - "equity_scan/config.py"
Cohesion: 0.29
Nodes (7): EquityScanFilters, EquityScanLimits, load_equity_scan_config(), BaseModel, Path, Configuration for the equity morning scan., Load equity scan settings from YAML.

### Community 49 - "_assert_broker_state_matches_db"
Cohesion: 0.15
Nodes (29): _assert_broker_state_matches_db(), _broker_option_positions(), _explicit_fill_details(), _intent_order_ids(), _json_dict(), _matches_underlying(), _open_trade_positions(), _order_symbols() (+21 more)

### Community 50 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 51 - "performance_chart.py"
Cohesion: 0.19
Nodes (19): compute_stats(), ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels() (+11 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "run_morning_scan.py"
Cohesion: 0.10
Nodes (31): is_premarket_window(), True during weekday premarket (default 4:00–9:30 AM ET)., archive_report(), archive_report_json(), Path, Write the scan report to a dated markdown file under report_dir., Write machine-readable scan internals next to the markdown report., attach_news_impacts() (+23 more)

### Community 55 - "load_config"
Cohesion: 0.13
Nodes (21): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+13 more)

### Community 56 - "Database Compatibility"
Cohesion: 0.13
Nodes (14): `001_initial.sql`: `option_chain_snapshots`, `001_initial.sql`: `spot_prices`, `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, `005_add_daily_bars.sql`, Anonymized Synchronized Data Slice, Daily Bar Shape Example, `daily_bars` (+6 more)

### Community 57 - "weekend_review.py"
Cohesion: 0.13
Nodes (40): TradePoint, build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_performance_caption(), format_review_header() (+32 more)

### Community 58 - "StrategySettings"
Cohesion: 0.08
Nodes (44): StrategySettings, fly_mark_value(), Pydantic models for option data and trade records., Butterfly value at mark: lower.mark - 2*center.mark + upper.mark., main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date. Replicates the… (+36 more)

### Community 59 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (21): Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison, Phase 4 — read-only cutover (+13 more)

### Community 60 - "select_entry_candidate"
Cohesion: 0.22
Nodes (14): CollectorSettings, ConfigModel, EntrySettings, MonitoringSettings, BaseModel, VixWidthBucket, Select the live/backtest entry candidate with shared pure logic., select_entry_candidate() (+6 more)

### Community 61 - "create_app"
Cohesion: 0.22
Nodes (17): GatewayMarketDataClient, AsyncClient, Typed client for gateway market-data endpoints only., create_app(), Application, authenticator(), FakeQuoteUpstream, asyncio (+9 more)

### Community 62 - "run_entry_analysis.py"
Cohesion: 0.13
Nodes (29): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+21 more)

### Community 63 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 64 - "ButterflyGuy Code Review State"
Cohesion: 0.12
Nodes (15): Architecture map, ButterflyGuy Code Review State, Changes implemented, Commands executed, Current phase, Decisions already made, Exact next actions, Files and directories reviewed (+7 more)

### Community 65 - "is_market_open"
Cohesion: 0.10
Nodes (29): is_market_open(), time, Check if the market is currently open., Check if current time is within the given window (HH:MM strings)., time_in_window(), Any, date, datetime (+21 more)

### Community 66 - "universes.py"
Cohesion: 0.06
Nodes (58): _as_float(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols(), fetch_sp500_rows() (+50 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.16
Nodes (13): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+5 more)

### Community 69 - "core/config.py"
Cohesion: 0.05
Nodes (62): BoundLogger, Schwab market-data client deliberately lacking every account/order operation., Configuration management using Pydantic settings., get_logger(), Structured logging setup with structlog., Get a structlog logger with optional name., Prometheus metrics for monitoring., _easter_sunday() (+54 more)

### Community 70 - "GapRegimeFilter"
Cohesion: 0.20
Nodes (6): GapRegimeFilter, min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct, TestSkipBeforeOverride

### Community 71 - "test_candidate_provider.py"
Cohesion: 0.31
Nodes (11): Build a synchronous schwab-py handler that never blocks the stream., make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close(), test_http_and_schwab_provider_contracts_normalize_equally() (+3 more)

### Community 72 - "Behavioral Specification"
Cohesion: 0.09
Nodes (22): Algorithmic Refinements For 0-DTE Robustness, Behavioral Specification, Bid-Ask Spread Penalization, Candidate Construction Invariants, Current Config Defaults, Current Width And Center Selection Data, Double-Factor Live Gating, Dynamic Wing Width Formula (+14 more)

### Community 73 - ".should_trade"
Cohesion: 0.50
Nodes (3): datetime, Most recent VIX bar close at or before entry_ts. None if no bars., True = safe to trade. False = skip (VIX too high). Returns True if no VIX bars…

### Community 74 - "DiscordNotifier"
Cohesion: 0.23
Nodes (4): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook.

### Community 75 - "chain_cache.py"
Cohesion: 0.27
Nodes (13): chain_cache_path(), load_chain_day(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->…, Append one chain snapshot to the day's cache file. Called by the collector… (+5 more)

### Community 76 - "scanner.py"
Cohesion: 0.19
Nodes (19): _as_float(), _as_int(), filter_movers(), _focus_reasons(), MarketContext, _mid_bid_ask(), _mover_change_pct(), _mover_symbol() (+11 more)

### Community 77 - "live_performance.py"
Cohesion: 0.10
Nodes (46): max_drawdown(), chart_payload(), cumulative_equity(), drawdown_series(), DrawdownPoint, duration_minutes(), format_et_time(), is_drawdown_exit() (+38 more)

### Community 78 - "find_entry_in_window"
Cohesion: 0.15
Nodes (27): discover_dates(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window(), get_prev_close(), get_recent_closes(), get_vix_at(), get_vix_prev_close() (+19 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 80 - "test_run_backtest_db_defaults.py"
Cohesion: 0.19
Nodes (12): candidate_from_trade_row(), Use the first regular-session snapshot for gap direction., select_direction_bar(), _parse_for_asset(), test_backtest_auto_direction_uses_first_regular_session_snapshot(), test_backtest_parses_exit_arm_sweep_overrides(), test_backtest_tracks_explicit_selection_overrides(), test_candidate_from_trade_row_pins_live_trade_fields() (+4 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.16
Nodes (13): candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options)., test_build_equity_trade_chart_png_returns_png_bytes(), test_equity_chart_aggregates_to_two_minute_candles(), test_equity_chart_stats_text_includes_key_fields(), test_equity_chart_window_keeps_6am_premarket_and_regular_session() (+5 more)

### Community 82 - "run_live.py"
Cohesion: 0.07
Nodes (33): clear_readiness(), Clear only the recovered subsystem's not-ready reason., OptionChainCollector, Collects option chain snapshots at regular intervals., Async database connection pool using asyncpg., ChainQueries, DailyBarQueries, OrderIntentQueries (+25 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "ConsecutiveLossNotifier"
Cohesion: 0.50
Nodes (3): ConsecutiveLossNotifier, Protocol, Notification hook for risk warnings that do not block trading.

### Community 87 - "report_broker_order_statuses.py"
Cohesion: 0.30
Nodes (12): _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses() (+4 more)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.21
Nodes (21): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+13 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 92 - "OptionQuote"
Cohesion: 0.10
Nodes (28): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes(), OptionQuote (+20 more)

### Community 93 - "ButterflyGuy Fable 5 Refactor Plan"
Cohesion: 0.13
Nodes (14): ButterflyGuy Fable 5 Refactor Plan, Closed Design Decisions, Completion Definition, Document Map, Fable Prompting Guidance, Implementation Phases, Non-Negotiable Constraints, Phase 1: Database Adapter And Historical Ingestion (+6 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "Codex Project State"
Cohesion: 0.14
Nodes (13): Codex Project State, Current Phase, Current Slice, Decisions Made, Known Failures, Next Exact Action, Objective, Open Questions (+5 more)

### Community 96 - "client.py"
Cohesion: 0.35
Nodes (9): GatewayAuthenticationError, GatewayAuthorizationError, GatewayClientError, GatewayResponseError, GatewayTimeoutError, GatewayUnavailableError, RuntimeError, Fail-closed HTTP client for the read-only gateway contract. (+1 more)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "test_order_preview.py"
Cohesion: 0.27
Nodes (10): make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate., Order spec must have all fields Schwab requires., Schwab expects price as a string., test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields() (+2 more)

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "XSP Opportunistic Partial-Fill Evidence Plan"
Cohesion: 0.29
Nodes (6): Completion, Current evidence, Decision, If one occurs naturally, Required artifacts, XSP Opportunistic Partial-Fill Evidence Plan

### Community 101 - "CandidatePaperExecutor"
Cohesion: 0.33
Nodes (9): CandidatePaperExecutor, Mark-price fills only; this object intentionally has no broker methods., candidate(), FakeProvider, market(), asyncio, test_candidate_entry_blocks_fill_above_configured_width_maximum(), test_candidate_entry_is_blocked_when_pin_fails() (+1 more)

### Community 102 - "resolve_db_dsn"
Cohesion: 0.18
Nodes (13): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., Resolve the DB connection string for local backtests. Backtests follow the…, resolve_db_dsn(), asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot() (+5 more)

### Community 103 - "redact"
Cohesion: 0.33
Nodes (5): Any, Small defensive redaction layer for gateway audit metadata., Return a recursively redacted copy suitable for bounded audit metadata., redact(), test_redaction_removes_nested_credentials_and_account_identifiers()

### Community 104 - "run_classifier_sweep.py"
Cohesion: 0.21
Nodes (16): max_consecutive_losses(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday…, _summarize_combo() (+8 more)

### Community 105 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run…, run()

### Community 106 - "TokenTransaction"
Cohesion: 0.20
Nodes (7): AbstractContextManager, datetime, Protocol, Operations available only while a token-store lock is held., Replaceable persistence boundary for one logical token document., TokenStore, TokenTransaction

### Community 107 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 109 - "run_backtest_db.py"
Cohesion: 0.15
Nodes (22): _asset_drawdowns(), _duration_min(), _floatlist(), _format_et(), _intlist(), parse_args(), _parse_config_time(), _parse_dd_schedule() (+14 more)

### Community 110 - "Butterfly Guy Live-Readiness TODO"
Cohesion: 0.40
Nodes (4): Butterfly Guy Live-Readiness TODO, Current gate, Remaining tasks, Safety boundaries

### Community 111 - "health_monitor.py"
Cohesion: 0.18
Nodes (15): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), Derive a human-readable service name from a health URL. Prefers the ``service``…, Post a message to Discord webhook., Run one full check cycle across all URLs. Returns list of results. (+7 more)

### Community 112 - "AGENTS.md"
Cohesion: 0.13
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 114 - "2. Other external and public sources"
Cohesion: 0.22
Nodes (9): 2.1 Yahoo Finance (`yfinance`), 2.2 S&P 500 constituent dataset on GitHub, 2.3 Wikipedia Nasdaq-100 page, 2.4 Nasdaq Trader symbol directories, 2.5 SEC company ticker map and submissions, 2.6 Alpha Vantage earnings calendar and news sentiment, 2.7 Forex Factory economic calendar, 2.8 Local market calendar and clock (+1 more)

### Community 115 - "5. Local files and backtest inputs"
Cohesion: 0.25
Nodes (8): 5.1 Application YAML configuration, 5.2 Environment variables and `.env`, 5.3 `tokens.json`, 5.4 Universe and metadata files, 5.5 Historical minute CSVs, 5.6 Local daily bar cache, 5.7 Local option-chain cache, 5. Local files and backtest inputs

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "AppConfig"
Cohesion: 0.10
Nodes (41): assert_candidate_safety(), CandidateAuditContext, CandidateDecisionQueries, CandidatePerformanceStats, config_sha256(), Path, Paper-only candidate evaluator built without broker execution dependencies., AppConfig (+33 more)

### Community 121 - "RiskQueries"
Cohesion: 0.07
Nodes (10): Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Queries for daily_risk_state table., Dollar PnL for the rolling 7-day window (closed trades only)., Dollar PnL of the last N closed trades, most recent first., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict. (+2 more)

### Community 124 - "test_run_migrations.py"
Cohesion: 0.43
Nodes (5): fake_db(), FakeConnection, asyncio, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 125 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 127 - "TokenManagerHealth"
Cohesion: 0.19
Nodes (7): Protocol, Injected boundary for the token manager's bounded readiness state., Fail closed when an app has no injected readiness dependency., TokenReadinessProvider, _UnavailableTokenReadinessProvider, TokenManagerHealth, FakeTokenReadinessProvider

### Community 128 - "DatabasePool"
Cohesion: 0.09
Nodes (13): Pool, DatabasePool, Manages an asyncpg connection pool for TimescaleDB., Create the connection pool., trade_pnl_dollars(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord. (+5 more)

### Community 129 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 130 - "test_position_manager.py"
Cohesion: 0.26
Nodes (13): PeakTrackingSettings, fly_settlement_value(), Butterfly cash-settlement value from the underlying index close., make_candidate(), make_quote(), make_xsp_candidate(), quote_map(), Tests for butterfly position valuation helpers. (+5 more)

### Community 133 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "AtomicTokenManager"
Cohesion: 0.12
Nodes (20): ClientT, OperationResult, LockedSchwabClientAdapter, RuntimeError, Fake-verification adapter for schwab-py's access-function lifecycle., Signature of schwab.auth.client_from_access_functions in schwab-py 1.5.1., Base error with a bounded message safe for gateway logs and responses., Construct and use one injected client inside a token-manager transaction. (+12 more)

### Community 137 - "select_cross_width_candidate"
Cohesion: 0.48
Nodes (6): Choose the final candidate from one best candidate per width. When…, select_cross_width_candidate(), _candidate(), test_cross_width_selection_can_prefer_first_bucket_width(), test_cross_width_selection_prefers_wider_wing_on_rr_tie(), test_cross_width_selection_returns_none_for_empty_pool()

### Community 141 - "order_manager.py"
Cohesion: 0.07
Nodes (51): ExecutionSettings, capped_entry_limit(), entry_fill_within_limit(), Shared entry-price limit policy for production and candidate runtimes., Return a cent-valid debit limit that never exceeds the configured maximum., Return whether an entry fill respects its hard debit ceiling., get_0dte_expiration(), now_utc() (+43 more)

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 156 - "Acceptance Tests"
Cohesion: 0.17
Nodes (11): Acceptance Tests, Completion Gate, Current Reference Test Map, Golden Replay Requirements, Observability Acceptance, Phase 1: Database Adapter Acceptance, Phase 2: Domain And Selection Acceptance, Phase 3: Paper Execution And Lifecycle Acceptance (+3 more)

### Community 162 - "ButterflyGuy data sources and data types"
Cohesion: 0.22
Nodes (8): 10. Repository evidence map, 4. Shared database tables visible to the same DB account, 6. Canonical and derived analytical data types, 8. Reports, archives, charts, and outbound destinations, 9. Practical limitations and safety notes, At a glance, ButterflyGuy data sources and data types, Synthetic option-chain data

### Community 163 - "Equity candles and order-book recording"
Cohesion: 0.33
Nodes (5): Backfill candles, Equity candles and order-book recording, Historical limitation, Operational caution, Record a future BMNR session

### Community 168 - "butterfly mark"
Cohesion: 0.20
Nodes (10): BUTTERFLYGUY, connectivity visual association, precision visual association, technology visual association, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background (+2 more)

### Community 170 - "test_gateway_token_manager.py"
Cohesion: 0.33
Nodes (21): Exception, increment_callback(), manager(), _process_refresh(), MonkeyPatch, parametrize, Path, test_callback_failure_preserves_original_and_redacts_error_and_logs() (+13 more)

### Community 174 - "Configuration Matrix"
Cohesion: 0.20
Nodes (9): Configuration Matrix, Execution And Risk Differences, Max Cost Per Width, Profit Management Regimes, Quote Quality And Peak Tracking, Refactor Requirements, Shared Defaults, Strategy Profile (+1 more)

### Community 175 - "Live Runbook"
Cohesion: 0.25
Nodes (7): During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery, XSP Canary

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (9): High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy (+1 more)

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 185 - "7. Operational and observability data"
Cohesion: 0.50
Nodes (4): 7.1 Prometheus metrics, 7.2 Health and readiness endpoints, 7.3 Structured application logs, 7. Operational and observability data

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - "Fixture Manifest"
Cohesion: 0.29
Nodes (6): Config Hashes, Export Rules, Fixture Manifest, Golden Replay Cases, Phase 1 Market-Data Fixtures, Selection Fixtures

### Community 193 - "Offline safety-drill record — 2026-07-13"
Cohesion: 0.29
Nodes (6): Drill findings fixed, Follow-up — 2026-07-14, Offline safety-drill record — 2026-07-13, Remaining do-now work, Result, Verification

### Community 197 - "Exact-SHA Deployment Proof - 2026-07-15"
Cohesion: 0.33
Nodes (5): Deployment and verification, Exact-SHA Deployment Proof - 2026-07-15, Follow-up rollback and restore drill, Preconditions and validation, Scope

### Community 198 - "XSP Manual-Flatten Evidence - 2026-07-16"
Cohesion: 0.33
Nodes (5): Fail-closed proof, Post-action reconciliation and paper restore, Redacted evidence, Result, XSP Manual-Flatten Evidence - 2026-07-16

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
- **390 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `Objective`, `Current Phase` (+385 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `get_logger()` connect `core/config.py` to `run_paper_replay.py`, `DatabasePool`, `SchwabClientWrapper`, `AtomicTokenManager`, `order_manager.py`, `MinuteBar`, `TokenManagerState`, `token_manager.py`, `news.py`, `setup_logging`, `api.py`, `feed.py`, `run_morning_scan.py`, `weekend_review.py`, `StrategySettings`, `run_entry_analysis.py`, `run_live.py`, `run_classifier_sweep.py`, `run_backtest_db.py`, `AppConfig`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `EntrySelectionResult`, `test_order_manager.py`, `test_position_manager.py`, `TradeService`, `MarketSnapshot`, `MinuteBar`, `ChainDay`, `simulation_engine.py`, `ProfitStateMachine`, `SyntheticChainGenerator`, `run_single`, `SessionClose`, `feed.py`, `ButterflyCandidate`, `report_exit_mark_parity.py`, `StrategySettings`, `select_entry_candidate`, `run_entry_analysis.py`, `DbDataLoader`, `core/config.py`, `test_candidate_provider.py`, `chain_cache.py`, `find_entry_in_window`, `CandidatePaperExecutor`, `run_backtest_db.py`, `AppConfig`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `AppConfig` connect `AppConfig` to `ProfitStateMachine`, `EntrySelectionResult`, `test_collector.py`, `core/config.py`, `CandidatePaperExecutor`, `run_single`, `SchwabSettings`, `TradeService`, `test_candidate_evaluator_accounting.py`, `ButterflyCandidate`, `run_backtest_db.py`, `CandidateRegistry`, `find_entry_in_window`, `order_manager.py`, `run_live.py`, `load_config`, `StrategySettings`, `select_entry_candidate`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `SchwabClientWrapper` (e.g. with `CollectorMarketDataProvider` and `DirectSchwabMarketDataProvider`) actually correct?**
  _`SchwabClientWrapper` has 21 INFERRED edges - model-reasoned connections that need verification._