# Graph Report - butterfly-gateway-multi-consumer-foundation  (2026-08-05)

## Corpus Check
- 274 files · ~274,198 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3786 nodes · 10168 edges · 179 communities (165 shown, 14 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 776 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d4ba8fa5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- StrategySettings
- token_manager.py
- client.py
- test_order_manager.py
- AppConfig
- DatabasePool
- ButterflyChartSpec
- FakeAccessFunctionFactory
- ._retry
- discover_options_strategy.py
- ButterflyCandidate
- credential_proof_fingerprint.py
- 4. Detailed findings
- generate_live_performance.py
- CandidateRegistry
- forex_calendar.py
- _assert_broker_state_matches_db
- MinuteBar
- CsvDataLoader
- test_comparison_stats.py
- run_live.py
- test_equity_scan.py
- InternalKeyAuthenticator
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- test_candidate_provider.py
- MarketSnapshot
- upstream.py
- SchwabClientWrapper
- test_gateway_config.py
- Domain Model and Ingestion Boundaries
- ProfitStateMachine
- test_risk_engine.py
- SyntheticChainGenerator
- news.py
- symbol_directory
- test_gateway_credential_probe.py
- run_classifier_sweep.py
- Current Schwab Integration
- gateway_client/models.py
- test_candidate_settlement.py
- api.py
- AtomicSnapshotStore
- run_backtest_db.py
- AlertmanagerNotifier
- SchwabDataLoader
- equity_trade_chart.py
- position_service.py
- DayData
- report_exit_mark_parity.py
- TradePoint
- Target Trading Platform
- ButterflyGuy AI Review State
- test_gateway_credential_proof_operator.py
- load_config
- Database Compatibility
- test_position_service_settlement.py
- test_run_live.py
- Schwab Gateway Migration Plan
- .session_close
- create_app
- volume.py
- report_trade_ladders.py
- ButterflyGuy Code Review State
- test_candidate_evaluator_accounting.py
- universes.py
- NamedTuple
- DbDataLoader
- feed.py
- GapRegimeFilter
- scanner.py
- Behavioral Specification
- test_weekend_review.py
- DiscordNotifier
- chain_cache.py
- live_performance.py
- run_morning_scan.py
- DirectSchwabMarketDataProvider
- 1. Charles Schwab API
- FakeProvider
- test_daily_report_card.py
- weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- TokenManagerError
- report_broker_order_statuses.py
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- ReadOnlySchwabMarketDataClient
- trade_service.py
- ButterflyGuy Fable 5 Refactor Plan
- 2026-07-14 — data audit and research design
- Codex Project State
- test_order_preview.py
- Capability recorder design
- record_equity_market_data.py
- Schwab Single-Token Manager
- XSP Opportunistic Partial-Fill Evidence Plan
- DailyReportCardSettings
- test_run_backtest_db.py
- redact
- report_selection_parity.py
- _MetricsHandler
- set_readiness
- ButterflyGuy data sources — representative samples
- Schwab Gateway Foundation: Local Run
- Butterfly Guy Live-Readiness TODO
- health_monitor.py
- AGENTS.md
- BaseModel
- 2. Other external and public sources
- 5. Local files and backtest inputs
- send_daily_report_card
- Protocol
- RuntimeError
- Butterfly Guy
- SnapshotIdentity
- date
- SessionClose
- GatewaySettings
- test_run_migrations.py
- Schwab Gateway Foundation Smoke Test
- StaticTokenReadinessProvider
- send_test_chart.py
- Schwab Gateway Credential Proof
- test_gateway_admission.py
- Strategy Settings
- backfill_equity_candles.py
- probe_schwab_gateway_credentials.py
- order_manager.py
- Width Selection
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Schwab Gateway Multi-Consumer Foundation
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
6. `OperatorFailure` - 65 edges
7. `MarketSnapshot` - 63 edges
8. `DatabasePool` - 59 edges
9. `SnapshotIdentity` - 52 edges
10. `StrategySettings` - 50 edges

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

## Communities (179 total, 14 thin omitted)

### Community 0 - "StrategySettings"
Cohesion: 0.05
Nodes (86): StrategySettings, main(), fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main() (+78 more)

### Community 1 - "token_manager.py"
Cohesion: 0.06
Nodes (41): AbstractContextManager, RLock, _AtomicFileTokenTransaction, AtomicTokenManager, _fsync_directory(), Any, datetime, Enum (+33 more)

### Community 2 - "client.py"
Cohesion: 0.33
Nodes (10): GatewayAuthenticationError, GatewayAuthorizationError, GatewayCapacityError, GatewayClientError, GatewayResponseError, GatewayTimeoutError, GatewayUnavailableError, RuntimeError (+2 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.16
Nodes (58): LiveSpread, NamedTuple, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+50 more)

### Community 4 - "AppConfig"
Cohesion: 0.07
Nodes (57): AppConfig, CollectorSettings, ConfigModel, EntrySettings, ExecutionSettings, MonitoringSettings, BaseModel, BaseSettings (+49 more)

### Community 5 - "DatabasePool"
Cohesion: 0.06
Nodes (59): Pool, assert_candidate_safety(), candidate_performance_stats(), CandidateAuditContext, CandidateDecisionQueries, CandidatePaperExecutor, CandidatePerformanceStats, config_sha256() (+51 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.11
Nodes (40): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+32 more)

### Community 7 - "FakeAccessFunctionFactory"
Cohesion: 0.24
Nodes (18): adapter(), FakeAccessFunctionFactory, FakeClient, manager(), Any, MonkeyPatch, Path, Mimic schwab-py 1.5.1 TokenMetadata wrapping without importing schwab. (+10 more)

### Community 8 - "._retry"
Cohesion: 0.08
Nodes (17): Any, date, Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order once and return the order ID. Order placement is not retried…, Get the status of an order., Cancel an existing order., Fetch 1-minute bars for today (and optionally prior days) from Schwab. (+9 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "ButterflyCandidate"
Cohesion: 0.05
Nodes (60): DB-backed data loader for historical SPX + VIX data. Reads from the live…, _candidate_mark(), get_time_regime(), Classify minutes since open into a named time regime., _as_float(), _as_int(), Any, date (+52 more)

### Community 11 - "credential_proof_fingerprint.py"
Cohesion: 0.07
Nodes (125): _accepted_fingerprint_hashes(), _accepted_snapshots(), _approval_1_execute(), _approval_2_execute(), _approved_staging_tmpfs(), _approved_tmpfs_entry(), _approved_window(), _archive_member_sha256() (+117 more)

### Community 12 - "4. Detailed findings"
Cohesion: 0.04
Nodes (45): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix, 6. Duplication map (+37 more)

### Community 13 - "generate_live_performance.py"
Cohesion: 0.20
Nodes (17): no_trade_reason(), _parse_metadata(), Any, trade_point_from_row(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate() (+9 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.12
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "_assert_broker_state_matches_db"
Cohesion: 0.21
Nodes (22): _assert_broker_state_matches_db(), _broker_option_positions(), _matches_underlying(), _open_trade_positions(), _repair_filled_entry_intent(), broker_fill_payload(), asyncio, parametrize (+14 more)

### Community 17 - "MinuteBar"
Cohesion: 0.09
Nodes (23): MinuteBar, _find_bar_at(), _find_entry_bar_at(), BiasScoreFilter, High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Exponential moving average seeded with SMA of first `period` bars. Returns None…, Scores market direction using 4 signals; returns CALL, PUT, or None., Compute bias score from 4 signals: gap : +1 if entry_close > prev_close, -1 if… (+15 more)

### Community 18 - "CsvDataLoader"
Cohesion: 0.25
Nodes (8): DataFrame, CsvDataLoader, date, Path, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files…

### Community 19 - "test_comparison_stats.py"
Cohesion: 0.46
Nodes (7): _print_comparison_table(), _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 20 - "run_live.py"
Cohesion: 0.05
Nodes (58): BoundLogger, CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, Schwab market-data client deliberately lacking every account/order operation., get_logger(), Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs., Get a structlog logger with optional name., setup_logging() (+50 more)

### Community 21 - "test_equity_scan.py"
Cohesion: 0.17
Nodes (36): EquityScanSettings, build_snapshots(), parse_equity_quote(), passes_filters(), datetime, _quote_age_seconds(), rank_catalyst_watch(), rank_scan_results() (+28 more)

### Community 22 - "InternalKeyAuthenticator"
Cohesion: 0.11
Nodes (28): Enum, authentication_middleware(), hash_api_key(), InternalKeyAuthenticator, InternalPrincipal, middleware, Path, StreamResponse (+20 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.08
Nodes (38): ProfitManagementStrategy, DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains., Runs full strategy on a single day using synthetic options., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. Skips… (+30 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.18
Nodes (29): build_daily_report_card(), count_rejected_orders(), _extract_order_id(), _extract_trade_leg(), _float(), _instrument_label(), _is_currency_instrument(), _is_zero_dte_option() (+21 more)

### Community 25 - "report.py"
Cohesion: 0.16
Nodes (32): build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes() (+24 more)

### Community 26 - "test_candidate_provider.py"
Cohesion: 0.27
Nodes (12): Any, Build a synchronous schwab-py handler that never blocks the stream., make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close() (+4 more)

### Community 27 - "MarketSnapshot"
Cohesion: 0.13
Nodes (9): candidate_fill_parity_failures(), CandidateEvaluator, Any, Count mark_v1 rows whose fills disagree with their recorded evidence., _aware_utc(), MarketSnapshot, datetime, One atomically published, replayable view of candidate market data. (+1 more)

### Community 28 - "upstream.py"
Cohesion: 0.20
Nodes (16): EquityQuoteProvider, DirectSchwabQuoteUpstream, _event_time(), _integer(), normalize_schwab_quote(), _number(), Any, datetime (+8 more)

### Community 29 - "SchwabClientWrapper"
Cohesion: 0.11
Nodes (20): SchwabSettings, CollectorMarketDataProvider, MarketMoversProvider, OptionChainProvider, PriceHistoryProvider, Protocol, Narrow read-only provider boundaries for Schwab market data., The read-only surface required by ``OptionChainCollector``. (+12 more)

### Community 30 - "test_gateway_config.py"
Cohesion: 0.20
Nodes (11): GatewayClientSettings, BaseSettings, model_validator, Opt-in client configuration; direct access remains the safe default., parametrize, settings(), test_gateway_client_mode_is_opt_in_and_secret_is_hidden(), test_gateway_client_mode_requires_url_and_key() (+3 more)

### Community 31 - "Domain Model and Ingestion Boundaries"
Cohesion: 0.07
Nodes (28): Actual Schwab Symbol Formats, Backtest Database Chain Rows to Strategy, Broker Mark Versus Computed Mid, ButterflyCandidate, Candidate, Spot, and Daily Bars, Collector Schwab Chain to Database, Configuration Schemas, Core Domain Types (+20 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.06
Nodes (65): PeakTrackingSettings, ProfitManagementSettings, QuoteQualitySettings, fly_settlement_value(), PositionState, Butterfly cash-settlement value from the underlying index close., Current state of an open position., ExitSignal (+57 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SyntheticChainGenerator"
Cohesion: 0.05
Nodes (58): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+50 more)

### Community 35 - "news.py"
Cohesion: 0.17
Nodes (30): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+22 more)

### Community 36 - "symbol_directory"
Cohesion: 0.16
Nodes (16): date, datetime, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session., Write a deterministic JSON candle snapshot., symbol_directory() (+8 more)

### Community 37 - "test_gateway_credential_probe.py"
Cohesion: 0.13
Nodes (19): GatewayCredentialProbeSettings, Validated configuration for the isolated gateway process., Explicit real-credential inputs for the standalone quote proof only., FakeClient, FakeFactory, FakeResponse, CaptureFixture, MonkeyPatch (+11 more)

### Community 38 - "run_classifier_sweep.py"
Cohesion: 0.16
Nodes (19): max_consecutive_losses(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday…, _summarize_combo() (+11 more)

### Community 39 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 40 - "gateway_client/models.py"
Cohesion: 0.19
Nodes (13): Transport-neutral client contracts for the internal Schwab gateway., GatewayErrorDetailV1, GatewayErrorV1, GatewayHealthV1, GatewayModel, GatewayReadinessV1, BaseModel, datetime (+5 more)

### Community 41 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 42 - "api.py"
Cohesion: 0.22
Nodes (18): audit_middleware(), _error(), health(), _json(), metrics(), _parse_symbols(), Application, middleware (+10 more)

### Community 43 - "AtomicSnapshotStore"
Cohesion: 0.12
Nodes (24): AtomicSnapshotStore, CandidateFeed, LeaseRegistry, Condition-guarded pointer swap; readers never observe partial snapshots., Persist once and return the canonical evidence for this session., SnapshotArchive, No verified final regular-session close is available from the shared feed., SessionCloseUnavailableError (+16 more)

### Community 44 - "run_backtest_db.py"
Cohesion: 0.06
Nodes (85): _asset_drawdowns(), backtest_entry_price(), candidate_from_trade_row(), _dd_schedule_label(), discover_dates(), _duration_min(), find_entry_in_window(), _floatlist() (+77 more)

### Community 45 - "AlertmanagerNotifier"
Cohesion: 0.11
Nodes (18): AlertmanagerNotifier, Sends centrally deduplicated critical alerts through Alertmanager., asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_alertmanager_payload_has_stable_redacted_fingerprint() (+10 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.14
Nodes (11): date, Path, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day., Loads SPY 1-minute bars from Schwab, scaled to SPX price levels. Reuses the…, Fetch SPX daily open from yfinance for SPY→SPX calibration., Fetch VIX daily close from yfinance. (+3 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (31): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+23 more)

### Community 48 - "position_service.py"
Cohesion: 0.04
Nodes (81): _easter_sunday(), get_0dte_expiration(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_premarket_window(), is_trading_day(), _last_weekday() (+73 more)

### Community 49 - "DayData"
Cohesion: 0.13
Nodes (22): dict, day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), ChainDay (+14 more)

### Community 50 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 51 - "TradePoint"
Cohesion: 0.17
Nodes (22): compute_stats(), ReportStats, TradePoint, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle() (+14 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "test_gateway_credential_proof_operator.py"
Cohesion: 0.07
Nodes (96): docker_inspect(), CaptureFixture, MonkeyPatch, parametrize, Path, test_canonical_fingerprint_is_independent_of_semantically_unordered_fields(), test_cli_bounds_docker_failure_without_raw_exception(), test_cli_exact_and_staging_verification_are_bounded() (+88 more)

### Community 55 - "load_config"
Cohesion: 0.13
Nodes (21): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+13 more)

### Community 56 - "Database Compatibility"
Cohesion: 0.13
Nodes (14): `001_initial.sql`: `option_chain_snapshots`, `001_initial.sql`: `spot_prices`, `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, `005_add_daily_bars.sql`, Anonymized Synchronized Data Slice, Daily Bar Shape Example, `daily_bars` (+6 more)

### Community 57 - "test_position_service_settlement.py"
Cohesion: 0.22
Nodes (18): final_regular_session_close_from_candles(), Return the latest Schwab 1-minute close in the regular session., _candle(), asyncio, datetime, parametrize, RuntimeError, Tests for cash-settlement spot selection. (+10 more)

### Community 58 - "test_run_live.py"
Cohesion: 0.29
Nodes (14): _never_awaited(), asyncio, _synthetic_butterfly_snapshot(), _synthetic_position(), test_order_symbols_walks_child_orders(), test_startup_reconciliation_allows_exact_signed_butterfly_ratio(), test_startup_reconciliation_allows_posted_expiration_settlement(), test_startup_reconciliation_blocks_broker_position_without_open_trade() (+6 more)

### Community 59 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 60 - ".session_close"
Cohesion: 0.17
Nodes (12): _final_regular_session_close(), Lease, _previous_close(), Any, date, datetime, LeaseKind, time (+4 more)

### Community 61 - "create_app"
Cohesion: 0.22
Nodes (17): GatewayMarketDataClient, AsyncClient, Typed client for gateway market-data endpoints only., create_app(), authenticator(), FakeQuoteUpstream, FakeTokenReadinessProvider, asyncio (+9 more)

### Community 62 - "volume.py"
Cohesion: 0.21
Nodes (12): _as_int(), avg_daily_volume(), compute_rvol(), prior_session_pct_change(), Relative volume helpers using Schwab daily bar history., Average daily volume from completed sessions (excludes today)., Close-to-close percent change for the last completed daily session., Symbols with premarket volume — only these need avg-volume for RVOL filter. (+4 more)

### Community 63 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 64 - "ButterflyGuy Code Review State"
Cohesion: 0.12
Nodes (15): Architecture map, ButterflyGuy Code Review State, Changes implemented, Commands executed, Current phase, Decisions already made, Exact next actions, Files and directories reviewed (+7 more)

### Community 65 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.24
Nodes (8): _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_performance_stats_reports_outlier_dependence(), test_min_gap_filter_logs_no_trade_before_candidate_selection(), test_min_gap_filter_preserves_direction_above_threshold(), test_review_progress_counts_only_closed_mark_v1_trades()

### Community 66 - "universes.py"
Cohesion: 0.06
Nodes (60): _as_float(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols(), fetch_sp500_rows() (+52 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.16
Nodes (13): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+5 more)

### Community 69 - "feed.py"
Cohesion: 0.26
Nodes (16): _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs(), _metrics(), _pin_snapshot() (+8 more)

### Community 70 - "GapRegimeFilter"
Cohesion: 0.13
Nodes (14): Classify regime then delegate to simulate_day() with matching params. Returns…, Maps Regime → SimulationParams for use with simulate_day_adaptive(). Per-regime…, RegimeDispatch, GapRegimeFilter, Enum, str, Market regime classifier for 0-DTE butterfly parameter dispatch. Classifies…, Regime (+6 more)

### Community 71 - "scanner.py"
Cohesion: 0.24
Nodes (16): _as_float(), _as_int(), filter_movers(), MarketContext, _mid_bid_ask(), _mover_change_pct(), _mover_symbol(), parse_market_context() (+8 more)

### Community 72 - "Behavioral Specification"
Cohesion: 0.09
Nodes (22): Algorithmic Refinements For 0-DTE Robustness, Behavioral Specification, Bid-Ask Spread Penalization, Candidate Construction Invariants, Current Config Defaults, Current Width And Center Selection Data, Double-Factor Live Gating, Dynamic Wing Width Formula (+14 more)

### Community 73 - "test_weekend_review.py"
Cohesion: 0.29
Nodes (13): asyncio, date, Tests for weekend review date windows and orchestration., test_calendar_month_to_date(), test_format_performance_caption_includes_stats(), test_latest_fill_model_cohort_does_not_mix_legacy_and_mark_v1(), test_previous_mon_fri_from_friday(), test_previous_mon_fri_from_saturday() (+5 more)

### Community 74 - "DiscordNotifier"
Cohesion: 0.23
Nodes (4): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook.

### Community 75 - "chain_cache.py"
Cohesion: 0.23
Nodes (15): chain_cache_path(), load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->… (+7 more)

### Community 76 - "live_performance.py"
Cohesion: 0.15
Nodes (29): max_drawdown(), chart_payload(), cumulative_equity(), drawdown_series(), DrawdownPoint, duration_minutes(), format_et_time(), is_drawdown_exit() (+21 more)

### Community 77 - "run_morning_scan.py"
Cohesion: 0.14
Nodes (21): load_equity_scan_config(), Path, Load equity scan settings from YAML., archive_report(), archive_report_json(), Path, Write the scan report to a dated markdown file under report_dir., Write machine-readable scan internals next to the markdown report. (+13 more)

### Community 78 - "DirectSchwabMarketDataProvider"
Cohesion: 0.14
Nodes (6): DirectSchwabMarketDataProvider, Any, date, Delegate to the current client without owning its lifecycle or changing data., asyncio, test_direct_provider_delegates_without_transforming_results()

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 80 - "FakeProvider"
Cohesion: 0.38
Nodes (8): candidate(), FakeProvider, market(), asyncio, test_candidate_entry_blocks_fill_above_configured_width_maximum(), test_candidate_entry_is_blocked_when_pin_fails(), test_candidate_entry_pins_before_mark_fill(), test_candidate_safety_rejects_live_or_credentialed_runtime()

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.15
Nodes (14): candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options)., test_build_daily_report_card_detects_problems(), test_build_equity_trade_chart_png_returns_png_bytes(), test_equity_chart_aggregates_to_two_minute_candles(), test_equity_chart_stats_text_includes_key_fields() (+6 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.19
Nodes (24): build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_review_header(), format_trade_recap(), latest_fill_model_cohort(), _parse_metadata() (+16 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "TokenManagerError"
Cohesion: 0.12
Nodes (29): ClientT, OperationResult, GatewayCredentialProbeError, GatewayCredentialProbeResult, Any, RuntimeError, One bounded quote proof through the locked token adapter., Bounded failure safe for operator output. (+21 more)

### Community 87 - "report_broker_order_statuses.py"
Cohesion: 0.30
Nodes (12): _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses() (+4 more)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.13
Nodes (25): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, 9) Capture equity candles and Level II for trade review, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config) (+17 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.21
Nodes (21): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+13 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 91 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.20
Nodes (7): Any, date, Authenticate a Schwab client without resolving or retaining an account., ReadOnlySchwabMarketDataClient, asyncio, MonkeyPatch, test_token_refresh_is_retained_in_memory_without_writing_file()

### Community 92 - "trade_service.py"
Cohesion: 0.09
Nodes (31): capped_entry_limit(), Return a cent-valid debit limit that never exceeds the configured maximum., iter_chain_options(), date, Shared utilities for parsing Schwab option chain responses., Yield (strike, option_type, opt_dict) for each option matching the expiration.…, _age_seconds(), Any (+23 more)

### Community 93 - "ButterflyGuy Fable 5 Refactor Plan"
Cohesion: 0.13
Nodes (14): ButterflyGuy Fable 5 Refactor Plan, Closed Design Decisions, Completion Definition, Document Map, Fable Prompting Guidance, Implementation Phases, Non-Negotiable Constraints, Phase 1: Database Adapter And Historical Ingestion (+6 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "Codex Project State"
Cohesion: 0.14
Nodes (13): Codex Project State, Current Phase, Current Slice, Decisions Made, Known Failures, Next Exact Action, Objective, Open Questions (+5 more)

### Community 96 - "test_order_preview.py"
Cohesion: 0.27
Nodes (10): make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate., Order spec must have all fields Schwab requires., Schwab expects price as a string., test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields() (+2 more)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "record_equity_market_data.py"
Cohesion: 0.20
Nodes (15): JsonlStreamRecorder, Event, Non-blocking stream handlers backed by one JSONL file per Schwab service., Drain queued events until the stop flag is set and the queue is empty., async_main(), _install_signal_handlers(), main(), parse_args() (+7 more)

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "XSP Opportunistic Partial-Fill Evidence Plan"
Cohesion: 0.29
Nodes (6): Completion, Current evidence, Decision, If one occurs naturally, Required artifacts, XSP Opportunistic Partial-Fill Evidence Plan

### Community 101 - "DailyReportCardSettings"
Cohesion: 0.21
Nodes (11): AccountBalances, ActivitySummary, CashMovement, DailyReportCardSettings, load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card. (+3 more)

### Community 102 - "test_run_backtest_db.py"
Cohesion: 0.20
Nodes (11): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), test_fitted_density_counts_returns_bucket_heights(), test_hypothetical_monitoring_load_uses_collector_only() (+3 more)

### Community 103 - "redact"
Cohesion: 0.33
Nodes (5): Any, Small defensive redaction layer for gateway audit metadata., Return a recursively redacted copy suitable for bounded audit metadata., redact(), test_redaction_removes_nested_credentials_and_account_identifiers()

### Community 104 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run…, run()

### Community 105 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 106 - "set_readiness"
Cohesion: 0.18
Nodes (18): clear_readiness(), Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., readiness_snapshot(), set_readiness(), broker_reconciler_loop(), entry_loop(), Periodically attempt entries during the entry window. (+10 more)

### Community 107 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

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

### Community 116 - "send_daily_report_card"
Cohesion: 0.22
Nodes (11): archive_report(), date, Path, chartable_equity_trades(), date, datetime, Path, ReportCardResult (+3 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "SnapshotIdentity"
Cohesion: 0.08
Nodes (21): Paper-only SPX candidate fleet fed by a shared market-data service., RuntimeError, Immutable normalized market snapshots shared by candidate evaluators., No complete snapshot is currently available., A long poll completed normally before a newer snapshot was published., SnapshotIdentity, SnapshotUnavailableError, SnapshotWaitTimeoutError (+13 more)

### Community 121 - "date"
Cohesion: 0.08
Nodes (7): Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Dollar PnL for the rolling 7-day window (closed trades only)., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict., Return the nearest full chain snapshot at or before *at* within…

### Community 122 - "SessionClose"
Cohesion: 0.15
Nodes (16): Any, Auditable final regular-session SPX close supplied by the shared feed., SessionClose, date, asyncio, datetime, quote(), snapshot() (+8 more)

### Community 123 - "GatewaySettings"
Cohesion: 0.29
Nodes (4): GatewaySettings, BaseSettings, field_validator, Path

### Community 124 - "test_run_migrations.py"
Cohesion: 0.43
Nodes (5): fake_db(), FakeConnection, asyncio, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 125 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 127 - "StaticTokenReadinessProvider"
Cohesion: 0.09
Nodes (24): AdmissionCapacityError, AdmissionController, AdmissionPolicy, RuntimeError, Bounded in-process admission policy for gateway market-data reads., The caller's bounded priority pool has no available permit., Keep background work out of ButterflyGuy's protected capacity., Expose bounded state for deterministic fake-only tests. (+16 more)

### Community 128 - "send_test_chart.py"
Cohesion: 0.27
Nodes (9): trade_pnl_dollars(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles() (+1 more)

### Community 130 - "Schwab Gateway Credential Proof"
Cohesion: 0.15
Nodes (12): Candidate capture safety stop — 2026-08-05, Candidate new-baseline capture remediation, Command, Evidence and stop conditions, Legacy-evidence retention remediation, Required operator authorization, Schwab Gateway Credential Proof, Status and scope (+4 more)

### Community 133 - "test_gateway_admission.py"
Cohesion: 0.30
Nodes (10): Read-only Schwab gateway foundation., authenticator(), BlockingUpstream, headers(), asyncio, ready_provider(), test_identity_claim_header_cannot_override_authenticated_caller(), test_normalized_upstream_failure_releases_permit_for_next_request() (+2 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 137 - "backfill_equity_candles.py"
Cohesion: 0.46
Nodes (7): async_main(), main(), parse_args(), Namespace, Path, Backfill one session of one-minute equity candles from Schwab., run()

### Community 140 - "probe_schwab_gateway_credentials.py"
Cohesion: 0.38
Nodes (6): _load_runtime_dependencies(), main(), _parser(), ArgumentParser, Run one explicitly authorized Schwab gateway credential proof without starting…, Import failure-prone runtime dependencies inside the bounded CLI path.

### Community 141 - "order_manager.py"
Cohesion: 0.06
Nodes (50): entry_fill_within_limit(), Shared entry-price limit policy for production and candidate runtimes., Return whether an entry fill respects its hard debit ceiling., now_utc(), OrderIntentQueries, Queries for durable broker order intents., ButterflyOrderBuilder, Any (+42 more)

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 147 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 148 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 149 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

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
- **419 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `Objective`, `Current Phase` (+414 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `get_logger()` connect `run_live.py` to `StrategySettings`, `token_manager.py`, `send_test_chart.py`, `DatabasePool`, `ButterflyCandidate`, `order_manager.py`, `news.py`, `run_classifier_sweep.py`, `api.py`, `run_backtest_db.py`, `position_service.py`, `DayData`, `universes.py`, `feed.py`, `run_morning_scan.py`, `weekend_review.py`, `TokenManagerError`, `trade_service.py`, `StaticTokenReadinessProvider`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `_restore_argv()` connect `credential_proof_fingerprint.py` to `MarketSnapshot`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `ButterflyCandidate` to `StrategySettings`, `test_order_manager.py`, `AppConfig`, `DatabasePool`, `test_candidate_provider.py`, `MarketSnapshot`, `ProfitStateMachine`, `SyntheticChainGenerator`, `AtomicSnapshotStore`, `run_backtest_db.py`, `position_service.py`, `DayData`, `report_exit_mark_parity.py`, `.session_close`, `DbDataLoader`, `feed.py`, `chain_cache.py`, `FakeProvider`, `trade_service.py`, `SnapshotIdentity`, `SessionClose`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `SchwabClientWrapper` (e.g. with `CollectorMarketDataProvider` and `DirectSchwabMarketDataProvider`) actually correct?**
  _`SchwabClientWrapper` has 21 INFERRED edges - model-reasoned connections that need verification._