# Graph Report - butterfly-gateway-multi-consumer-foundation  (2026-08-05)

## Corpus Check
- 274 files · ~278,368 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3811 nodes · 10280 edges · 178 communities (164 shown, 14 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 776 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6c8e3d6d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- token_manager.py
- TokenTransaction
- test_order_manager.py
- AppConfig
- DatabasePool
- ButterflyChartSpec
- FakeAccessFunctionFactory
- SchwabClientWrapper
- discover_options_strategy.py
- exit_mark_parity.py
- credential_proof_fingerprint.py
- 4. Detailed findings
- DirectSchwabMarketDataProvider
- CandidateRegistry
- forex_calendar.py
- TradeRecord
- MinuteBar
- CsvDataLoader
- run_backtest_db.py
- run_live.py
- test_equity_scan.py
- InternalKeyAuthenticator
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- HttpMarketDataProvider
- StrategySettings
- upstream.py
- run_entry_analysis.py
- test_gateway_config.py
- Domain Model and Ingestion Boundaries
- ProfitStateMachine
- test_risk_engine.py
- SyntheticChainGenerator
- news.py
- record_equity_market_data.py
- test_gateway_credential_probe.py
- test_comparison_stats.py
- Current Schwab Integration
- CandidateEvaluator
- test_candidate_settlement.py
- api.py
- AtomicSnapshotStore
- test_weekend_review.py
- send_alertmanager
- SchwabDataLoader
- equity_trade_chart.py
- core/config.py
- universes.py
- OptionQuote
- performance_chart.py
- Target Trading Platform
- ButterflyGuy AI Review State
- test_gateway_credential_proof_operator.py
- load_config
- Database Compatibility
- time_utils.py
- refresh_builtin_universes
- Schwab Gateway Migration Plan
- .collect_once
- create_app
- gateway_client/models.py
- report_trade_ladders.py
- ButterflyGuy Code Review State
- MarketSnapshot
- refresh_equity_universes.py
- NamedTuple
- DbDataLoader
- feed.py
- GapRegimeFilter
- scanner.py
- Behavioral Specification
- SessionCloseUnavailableError
- DiscordNotifier
- ChainDay
- live_performance.py
- run_morning_scan.py
- ButterflySelector
- 1. Charles Schwab API
- ButterflyOrderBuilder
- test_daily_report_card.py
- weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- AtomicTokenManager
- report_broker_order_statuses.py
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- ReadOnlySchwabMarketDataClient
- ButterflyCandidate
- ButterflyGuy Fable 5 Refactor Plan
- 2026-07-14 — data audit and research design
- Codex Project State
- 9) Capture equity candles and Level II for trade review
- Capability recorder design
- test_candidate_evaluator_accounting.py
- Schwab Single-Token Manager
- XSP Opportunistic Partial-Fill Evidence Plan
- test_order_preview.py
- test_run_backtest_db.py
- redact
- test_run_backtest_db_defaults.py
- _MetricsHandler
- BrokerStateGate
- ButterflyGuy data sources — representative samples
- Schwab Gateway Foundation: Local Run
- client.py
- Butterfly Guy Live-Readiness TODO
- health_monitor.py
- AGENTS.md
- BaseModel
- 2. Other external and public sources
- 5. Local files and backtest inputs
- services/daily_report_card.py
- Protocol
- RuntimeError
- Butterfly Guy
- FakeProvider
- OrderIntentQueries
- test_candidate_snapshot.py
- GatewaySettings
- test_run_migrations.py
- Schwab Gateway Foundation Smoke Test
- StaticTokenReadinessProvider
- send_test_chart.py
- Schwab Gateway Credential Proof
- test_gateway_admission.py
- Strategy Settings
- OrderManager
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
6. `OperatorFailure` - 67 edges
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

## Communities (178 total, 14 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.11
Nodes (38): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close() (+30 more)

### Community 1 - "token_manager.py"
Cohesion: 0.10
Nodes (26): _AtomicFileTokenTransaction, _fsync_directory(), Enum, Path, str, Locked, atomic token persistence without a Schwab runtime dependency., Validate only the stable schwab-py token envelope and required OAuth fields., Run one fake/replaceable refresh callback under the exclusive token lock. (+18 more)

### Community 2 - "TokenTransaction"
Cohesion: 0.10
Nodes (13): AbstractContextManager, RLock, Any, datetime, Protocol, A refresh callback uses this to classify an upstream revocation., A refresh callback uses this when manual OAuth authorization is required., Operations available only while a token-store lock is held. (+5 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.16
Nodes (58): LiveSpread, NamedTuple, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+50 more)

### Community 4 - "AppConfig"
Cohesion: 0.08
Nodes (48): assert_candidate_safety(), AppConfig, CollectorSettings, ConfigModel, EntrySettings, ExecutionSettings, MonitoringSettings, BaseModel (+40 more)

### Community 5 - "DatabasePool"
Cohesion: 0.06
Nodes (54): Pool, candidate_performance_stats(), CandidateAuditContext, CandidateDecisionQueries, CandidatePaperExecutor, CandidatePerformanceStats, config_sha256(), Path (+46 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.11
Nodes (40): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+32 more)

### Community 7 - "FakeAccessFunctionFactory"
Cohesion: 0.24
Nodes (18): adapter(), FakeAccessFunctionFactory, FakeClient, manager(), Any, MonkeyPatch, Path, Mimic schwab-py 1.5.1 TokenMetadata wrapping without importing schwab. (+10 more)

### Community 8 - "SchwabClientWrapper"
Cohesion: 0.06
Nodes (33): SchwabSettings, Any, date, Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order once and return the order ID. Order placement is not retried…, Get the status of an order., Cancel an existing order. (+25 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "exit_mark_parity.py"
Cohesion: 0.16
Nodes (17): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes(), build_exit_mark_parity() (+9 more)

### Community 11 - "credential_proof_fingerprint.py"
Cohesion: 0.07
Nodes (132): _accepted_fingerprint_hashes(), _accepted_snapshots(), _approval_1_execute(), _approval_2_execute(), _approved_staging_tmpfs(), _approved_tmpfs_entry(), _approved_window(), _archive_member_sha256() (+124 more)

### Community 12 - "4. Detailed findings"
Cohesion: 0.04
Nodes (45): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix, 6. Duplication map (+37 more)

### Community 13 - "DirectSchwabMarketDataProvider"
Cohesion: 0.10
Nodes (14): CollectorMarketDataProvider, DirectSchwabMarketDataProvider, MarketMoversProvider, OptionChainProvider, PriceHistoryProvider, Any, date, Protocol (+6 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.12
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "TradeRecord"
Cohesion: 0.10
Nodes (29): A trade record for tracking entry/exit., TradeRecord, PartialFillError, RuntimeError, Broker reported a partial fill; operator reconciliation is required., Broker rejected or expired an order; the ladder must stop., TerminalOrderError, broker_cash_settlement_from_transactions() (+21 more)

### Community 17 - "MinuteBar"
Cohesion: 0.07
Nodes (28): CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, MinuteBar, Shared backtest market-data models., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., BiasScoreFilter, Multi-signal directional bias filter for 0-DTE butterfly entries., High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Exponential moving average seeded with SMA of first `period` bars. Returns None… (+20 more)

### Community 18 - "CsvDataLoader"
Cohesion: 0.25
Nodes (8): DataFrame, CsvDataLoader, date, Path, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files…

### Community 19 - "run_backtest_db.py"
Cohesion: 0.05
Nodes (92): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), _asset_drawdowns(), backtest_entry_price(), candidate_from_trade_row() (+84 more)

### Community 20 - "run_live.py"
Cohesion: 0.12
Nodes (39): BrokerFill, order_ids(), parse_broker_fill(), Return a validated net butterfly fill derived only from broker executions., walk_orders(), _assert_broker_state_matches_db(), _broker_option_positions(), eod_chart_loop() (+31 more)

### Community 21 - "test_equity_scan.py"
Cohesion: 0.17
Nodes (35): EquityScanSettings, build_snapshots(), parse_equity_quote(), passes_filters(), datetime, _quote_age_seconds(), rank_catalyst_watch(), rank_scan_results() (+27 more)

### Community 22 - "InternalKeyAuthenticator"
Cohesion: 0.11
Nodes (28): Enum, authentication_middleware(), hash_api_key(), InternalKeyAuthenticator, InternalPrincipal, middleware, Path, StreamResponse (+20 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.07
Nodes (51): nearest_snapshot(), Return quotes from the most recent snapshot at or before bar_ts., DayData, win_pct(), DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains. (+43 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.13
Nodes (37): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders(), detect_problems(), _extract_order_id() (+29 more)

### Community 25 - "report.py"
Cohesion: 0.18
Nodes (29): build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes() (+21 more)

### Community 26 - "HttpMarketDataProvider"
Cohesion: 0.12
Nodes (17): HttpMarketDataProvider, AsyncClient, LeaseKind, Response, Fail-closed client for the internal candidate feed., _response_error(), Build a synchronous schwab-py handler that never blocks the stream., make_session_close() (+9 more)

### Community 27 - "StrategySettings"
Cohesion: 0.13
Nodes (28): StrategySettings, main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date. Replicates the…, _bucket_sigmas(), ButterflyBuilder, O(N*W) butterfly construction and scoring engine. (+20 more)

### Community 28 - "upstream.py"
Cohesion: 0.20
Nodes (16): EquityQuoteProvider, DirectSchwabQuoteUpstream, _event_time(), _integer(), normalize_schwab_quote(), _number(), Any, datetime (+8 more)

### Community 29 - "run_entry_analysis.py"
Cohesion: 0.15
Nodes (26): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+18 more)

### Community 30 - "test_gateway_config.py"
Cohesion: 0.20
Nodes (11): GatewayClientSettings, BaseSettings, model_validator, Opt-in client configuration; direct access remains the safe default., parametrize, settings(), test_gateway_client_mode_is_opt_in_and_secret_is_hidden(), test_gateway_client_mode_requires_url_and_key() (+3 more)

### Community 31 - "Domain Model and Ingestion Boundaries"
Cohesion: 0.07
Nodes (28): Actual Schwab Symbol Formats, Backtest Database Chain Rows to Strategy, Broker Mark Versus Computed Mid, ButterflyCandidate, Candidate, Spot, and Daily Bars, Collector Schwab Chain to Database, Configuration Schemas, Core Domain Types (+20 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.05
Nodes (73): ProfitManagementStrategy, PeakTrackingSettings, ProfitManagementSettings, QuoteQualitySettings, fly_settlement_value(), PositionState, Butterfly cash-settlement value from the underlying index close., Current state of an open position. (+65 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SyntheticChainGenerator"
Cohesion: 0.05
Nodes (60): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+52 more)

### Community 35 - "news.py"
Cohesion: 0.16
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 36 - "record_equity_market_data.py"
Cohesion: 0.09
Nodes (39): JsonlStreamRecorder, Any, date, datetime, Event, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers. (+31 more)

### Community 37 - "test_gateway_credential_probe.py"
Cohesion: 0.16
Nodes (16): FakeClient, FakeFactory, FakeResponse, CaptureFixture, MonkeyPatch, Path, settings(), test_probe_command_bounds_configuration_failure() (+8 more)

### Community 38 - "test_comparison_stats.py"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 39 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 40 - "CandidateEvaluator"
Cohesion: 0.22
Nodes (7): candidate_fill_parity_failures(), _candidate_mark(), CandidateEvaluator, Any, Count mark_v1 rows whose fills disagree with their recorded evidence., _restore_trade(), test_candidate_fill_parity_counts_entry_exit_mismatch_or_missing_evidence()

### Community 41 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 42 - "api.py"
Cohesion: 0.22
Nodes (18): audit_middleware(), _error(), health(), _json(), metrics(), _parse_symbols(), Application, middleware (+10 more)

### Community 43 - "AtomicSnapshotStore"
Cohesion: 0.12
Nodes (21): AtomicSnapshotStore, CandidateFeed, LeaseRegistry, Condition-guarded pointer swap; readers never observe partial snapshots., SnapshotArchive, DatabaseSettings, main(), Run the demand-aware shared SPX candidate market-data feed. (+13 more)

### Community 44 - "test_weekend_review.py"
Cohesion: 0.27
Nodes (14): asyncio, date, Tests for weekend review date windows and orchestration., test_calendar_month_to_date(), test_format_performance_caption_includes_stats(), test_latest_fill_model_cohort_does_not_mix_legacy_and_mark_v1(), test_previous_mon_fri_from_friday(), test_previous_mon_fri_from_saturday() (+6 more)

### Community 45 - "send_alertmanager"
Cohesion: 0.12
Nodes (16): asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_alertmanager_payload_has_stable_redacted_fingerprint(), test_notify_entry_includes_trade_stats(), test_notify_exit_formats_contract_pnl_as_dollars() (+8 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.09
Nodes (22): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), date, Path (+14 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (31): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+23 more)

### Community 48 - "core/config.py"
Cohesion: 0.04
Nodes (59): BoundLogger, Schwab market-data client deliberately lacking every account/order operation., Configuration management using Pydantic settings., capped_entry_limit(), Shared entry-price limit policy for production and candidate runtimes., Return a cent-valid debit limit that never exceeds the configured maximum., get_logger(), Structured logging setup with structlog. (+51 more)

### Community 49 - "universes.py"
Cohesion: 0.17
Nodes (18): fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nyse_listed_symbols(), _fetch_url_text(), _is_common_equity_symbol(), _is_symbol_directory_footer(), parse_nasdaq_listed_text(), parse_nyse_listed_text() (+10 more)

### Community 50 - "OptionQuote"
Cohesion: 0.11
Nodes (31): fly_mark_value(), OptionQuote, A single option quote from a chain snapshot., Butterfly value at mark: lower.mark - 2*center.mark + upper.mark., compute_tent_boundaries(), fly_bid_value(), _max_leg_spread_to_mark_ratio(), _quote_quality_ok() (+23 more)

### Community 51 - "performance_chart.py"
Cohesion: 0.18
Nodes (18): compute_stats(), ReportStats, build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels(), Axes (+10 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "test_gateway_credential_proof_operator.py"
Cohesion: 0.07
Nodes (107): docker_inspect(), CaptureFixture, MonkeyPatch, parametrize, Path, test_canonical_fingerprint_is_independent_of_semantically_unordered_fields(), test_cli_bounds_docker_failure_without_raw_exception(), test_cli_exact_and_staging_verification_are_bounded() (+99 more)

### Community 55 - "load_config"
Cohesion: 0.10
Nodes (27): load_config(), Path, Load configuration from YAML file and environment variables., main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run… (+19 more)

### Community 56 - "Database Compatibility"
Cohesion: 0.13
Nodes (14): `001_initial.sql`: `option_chain_snapshots`, `001_initial.sql`: `spot_prices`, `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, `005_add_daily_bars.sql`, Anonymized Synchronized Data Slice, Daily Bar Shape Example, `daily_bars` (+6 more)

### Community 57 - "time_utils.py"
Cohesion: 0.07
Nodes (62): _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_premarket_window(), is_trading_day(), _last_weekday(), market_close_time() (+54 more)

### Community 58 - "refresh_builtin_universes"
Cohesion: 0.13
Nodes (19): fetch_nq100_tickers(), fetch_sp500_rows(), fetch_sp500_sectors(), fetch_sp500_tickers(), load_liquid_meta(), load_universe(), load_universes(), Path (+11 more)

### Community 59 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 60 - ".collect_once"
Cohesion: 0.20
Nodes (9): _final_regular_session_close(), _previous_close(), Any, date, datetime, LeaseKind, time, Select only a final (15:59/16:00 normally) regular-session 1-minute bar. (+1 more)

### Community 61 - "create_app"
Cohesion: 0.22
Nodes (17): GatewayMarketDataClient, AsyncClient, Typed client for gateway market-data endpoints only., create_app(), authenticator(), FakeQuoteUpstream, FakeTokenReadinessProvider, asyncio (+9 more)

### Community 62 - "gateway_client/models.py"
Cohesion: 0.19
Nodes (13): Transport-neutral client contracts for the internal Schwab gateway., GatewayErrorDetailV1, GatewayErrorV1, GatewayHealthV1, GatewayModel, GatewayReadinessV1, BaseModel, datetime (+5 more)

### Community 63 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 64 - "ButterflyGuy Code Review State"
Cohesion: 0.12
Nodes (15): Architecture map, ButterflyGuy Code Review State, Changes implemented, Commands executed, Current phase, Decisions already made, Exact next actions, Files and directories reviewed (+7 more)

### Community 65 - "MarketSnapshot"
Cohesion: 0.08
Nodes (20): Paper-only SPX candidate fleet fed by a shared market-data service., _aware_utc(), MarketSnapshot, Any, datetime, RuntimeError, Immutable normalized market snapshots shared by candidate evaluators., No complete snapshot is currently available. (+12 more)

### Community 66 - "refresh_equity_universes.py"
Cohesion: 0.11
Nodes (25): _as_float(), build_liquid_meta(), extract_quote_price(), filter_symbols_by_avg_volume(), filter_symbols_by_price(), load_sector_map(), Any, Load symbol -> sector mapping (GICS for index names, exchange fallback for… (+17 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.15
Nodes (14): DbDataLoader, Connection, date, datetime, DB-backed data loader for historical SPX + VIX data. Reads from the live…, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order. (+6 more)

### Community 69 - "feed.py"
Cohesion: 0.26
Nodes (16): _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs(), _metrics(), _pin_snapshot() (+8 more)

### Community 70 - "GapRegimeFilter"
Cohesion: 0.18
Nodes (7): GapRegimeFilter, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct, TestSkipBeforeOverride

### Community 71 - "scanner.py"
Cohesion: 0.19
Nodes (19): _as_float(), _as_int(), filter_movers(), _focus_reasons(), MarketContext, _mid_bid_ask(), _mover_change_pct(), _mover_symbol() (+11 more)

### Community 72 - "Behavioral Specification"
Cohesion: 0.09
Nodes (22): Algorithmic Refinements For 0-DTE Robustness, Behavioral Specification, Bid-Ask Spread Penalization, Candidate Construction Invariants, Current Config Defaults, Current Width And Center Selection Data, Double-Factor Live Gating, Dynamic Wing Width Formula (+14 more)

### Community 73 - "SessionCloseUnavailableError"
Cohesion: 0.21
Nodes (9): Lease, Persist once and return the canonical evidence for this session., Return one cached, verified final regular-session SPX close per date., SessionContext, Auditable final regular-session SPX close supplied by the shared feed., No verified final regular-session close is available from the shared feed., SessionClose, SessionCloseUnavailableError (+1 more)

### Community 74 - "DiscordNotifier"
Cohesion: 0.16
Nodes (8): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook., main(), parse_reference_date(), date, Send SPX weekend review to Discord #weekend-review. Cron: Saturday 9:00 AM PT 0…

### Community 75 - "ChainDay"
Cohesion: 0.15
Nodes (22): dict, chain_cache_path(), ChainDay, load_chain_day(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.… (+14 more)

### Community 76 - "live_performance.py"
Cohesion: 0.10
Nodes (44): chart_payload(), cumulative_equity(), drawdown_series(), DrawdownPoint, duration_minutes(), format_et_time(), is_drawdown_exit(), _money() (+36 more)

### Community 77 - "run_morning_scan.py"
Cohesion: 0.09
Nodes (31): load_equity_scan_config(), Path, Load equity scan settings from YAML., archive_report(), archive_report_json(), Path, Write the scan report to a dated markdown file under report_dir., Write machine-readable scan internals next to the markdown report. (+23 more)

### Community 78 - "ButterflySelector"
Cohesion: 0.19
Nodes (11): ButterflySelector, Butterfly selector — picks the best candidate from a list., Selects the best butterfly candidate., Select the best butterfly candidate. When `target_center` is provided (derived…, Select the candidate whose cost is closest to its max_cost_per_width., make_candidate(), Tests for butterfly candidate selection., test_regular_best_rr_selection_still_uses_rr_target() (+3 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 80 - "ButterflyOrderBuilder"
Cohesion: 0.26
Nodes (9): ButterflyOrderBuilder, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., make_candidate(), Tests for butterfly order builder., test_build_close_order_structure(), test_build_open_order_legs(), test_build_open_order_structure() (+1 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.18
Nodes (15): parse_trade_transactions(), Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options)., test_build_equity_trade_chart_png_returns_png_bytes(), test_chartable_equity_trades_skips_options() (+7 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.17
Nodes (28): TradePoint, build_combined_performance_chart_png(), Build one image with weekly, monthly, and all-time equity + drawdown panels., build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption() (+20 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "AtomicTokenManager"
Cohesion: 0.13
Nodes (31): ClientT, OperationResult, GatewayCredentialProbeError, GatewayCredentialProbeResult, Any, RuntimeError, One bounded quote proof through the locked token adapter., Bounded failure safe for operator output. (+23 more)

### Community 87 - "report_broker_order_statuses.py"
Cohesion: 0.30
Nodes (12): _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses() (+4 more)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.16
Nodes (21): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+13 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.25
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 91 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.26
Nodes (4): Any, date, Authenticate a Schwab client without resolving or retaining an account., ReadOnlySchwabMarketDataClient

### Community 92 - "ButterflyCandidate"
Cohesion: 0.11
Nodes (28): ButterflyCandidate, Pydantic models for option data and trade records., A butterfly spread candidate identified by the scanner., Any, Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., Compare Schwab selection with the nearest DB collector snapshot., EntrySelectionResult (+20 more)

### Community 93 - "ButterflyGuy Fable 5 Refactor Plan"
Cohesion: 0.13
Nodes (14): ButterflyGuy Fable 5 Refactor Plan, Closed Design Decisions, Completion Definition, Document Map, Fable Prompting Guidance, Implementation Phases, Non-Negotiable Constraints, Phase 1: Database Adapter And Historical Ingestion (+6 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "Codex Project State"
Cohesion: 0.14
Nodes (13): Codex Project State, Current Phase, Current Slice, Decisions Made, Known Failures, Next Exact Action, Objective, Open Questions (+5 more)

### Community 96 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.24
Nodes (8): _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_performance_stats_reports_outlier_dependence(), test_min_gap_filter_logs_no_trade_before_candidate_selection(), test_min_gap_filter_preserves_direction_above_threshold(), test_review_progress_counts_only_closed_mark_v1_trades()

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "XSP Opportunistic Partial-Fill Evidence Plan"
Cohesion: 0.29
Nodes (6): Completion, Current evidence, Decision, If one occurs naturally, Required artifacts, XSP Opportunistic Partial-Fill Evidence Plan

### Community 101 - "test_order_preview.py"
Cohesion: 0.27
Nodes (10): make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate., Order spec must have all fields Schwab requires., Schwab expects price as a string., test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields() (+2 more)

### Community 102 - "test_run_backtest_db.py"
Cohesion: 0.20
Nodes (11): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), test_fitted_density_counts_returns_bucket_heights(), test_hypothetical_monitoring_load_uses_collector_only() (+3 more)

### Community 103 - "redact"
Cohesion: 0.33
Nodes (5): Any, Small defensive redaction layer for gateway audit metadata., Return a recursively redacted copy suitable for bounded audit metadata., redact(), test_redaction_removes_nested_credentials_and_account_identifiers()

### Community 104 - "test_run_backtest_db_defaults.py"
Cohesion: 0.27
Nodes (9): Use the first regular-session snapshot for gap direction., select_direction_bar(), _parse_for_asset(), test_backtest_auto_direction_uses_first_regular_session_snapshot(), test_candidate_from_trade_row_pins_live_trade_fields(), test_default_entry_bar_lookup_rejects_late_fallback(), test_ndx_backtest_drawdown_defaults_match_live_config(), test_spx_backtest_drawdown_defaults_match_live_config() (+1 more)

### Community 105 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 106 - "BrokerStateGate"
Cohesion: 0.06
Nodes (51): clear_readiness(), Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., readiness_snapshot(), set_readiness(), OptionChainCollector, Any, date (+43 more)

### Community 107 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 109 - "client.py"
Cohesion: 0.33
Nodes (10): GatewayAuthenticationError, GatewayAuthorizationError, GatewayCapacityError, GatewayClientError, GatewayResponseError, GatewayTimeoutError, GatewayUnavailableError, RuntimeError (+2 more)

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

### Community 116 - "services/daily_report_card.py"
Cohesion: 0.13
Nodes (20): load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds, archive_report(), date, Path (+12 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.12
Nodes (16): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+8 more)

### Community 120 - "FakeProvider"
Cohesion: 0.44
Nodes (7): candidate(), FakeProvider, market(), asyncio, test_candidate_entry_blocks_fill_above_configured_width_maximum(), test_candidate_entry_is_blocked_when_pin_fails(), test_candidate_entry_pins_before_mark_fill()

### Community 121 - "OrderIntentQueries"
Cohesion: 0.07
Nodes (9): OrderIntentQueries, Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Queries for durable broker order intents., Dollar PnL for the rolling 7-day window (closed trades only)., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict. (+1 more)

### Community 122 - "test_candidate_snapshot.py"
Cohesion: 0.33
Nodes (12): asyncio, datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry(), test_long_poll_never_replays_same_sequence(), test_new_lease_wakes_idle_feed() (+4 more)

### Community 123 - "GatewaySettings"
Cohesion: 0.13
Nodes (13): GatewayCredentialProbeSettings, GatewaySettings, BaseSettings, field_validator, Path, Validated configuration for the isolated gateway process., Explicit real-credential inputs for the standalone quote proof only., _load_runtime_dependencies() (+5 more)

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
Cohesion: 0.10
Nodes (19): Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05, Corrected Compose-hash result — 2026-08-05 (+11 more)

### Community 133 - "test_gateway_admission.py"
Cohesion: 0.30
Nodes (10): Read-only Schwab gateway foundation., authenticator(), BlockingUpstream, headers(), asyncio, ready_provider(), test_identity_claim_header_cannot_override_authenticated_caller(), test_normalized_upstream_failure_releases_permit_for_next_request() (+2 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 141 - "OrderManager"
Cohesion: 0.15
Nodes (18): entry_fill_within_limit(), Return whether an entry fill respects its hard debit ceiling., now_utc(), AmbiguousOrderError, _assert_entry_fill_within_limit(), _fill_result(), order_statuses(), OrderManager (+10 more)

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
- **426 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `Objective`, `Current Phase` (+421 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `_restore_argv()` connect `credential_proof_fingerprint.py` to `AtomicSnapshotStore`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `get_logger()` connect `core/config.py` to `run_paper_replay.py`, `token_manager.py`, `send_test_chart.py`, `DatabasePool`, `MinuteBar`, `run_backtest_db.py`, `run_live.py`, `simulation_engine.py`, `StrategySettings`, `run_entry_analysis.py`, `ProfitStateMachine`, `news.py`, `api.py`, `SchwabDataLoader`, `refresh_equity_universes.py`, `DbDataLoader`, `feed.py`, `run_morning_scan.py`, `ButterflySelector`, `ButterflyOrderBuilder`, `weekend_review.py`, `AtomicTokenManager`, `services/daily_report_card.py`, `StaticTokenReadinessProvider`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `test_order_manager.py`, `AppConfig`, `DatabasePool`, `exit_mark_parity.py`, `TradeRecord`, `run_backtest_db.py`, `simulation_engine.py`, `HttpMarketDataProvider`, `StrategySettings`, `run_entry_analysis.py`, `ProfitStateMachine`, `SyntheticChainGenerator`, `AtomicSnapshotStore`, `core/config.py`, `.collect_once`, `MarketSnapshot`, `DbDataLoader`, `feed.py`, `SessionCloseUnavailableError`, `ChainDay`, `ButterflyCandidate`, `FakeProvider`, `test_candidate_snapshot.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `SchwabClientWrapper` (e.g. with `CollectorMarketDataProvider` and `DirectSchwabMarketDataProvider`) actually correct?**
  _`SchwabClientWrapper` has 21 INFERRED edges - model-reasoned connections that need verification._