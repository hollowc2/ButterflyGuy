# Graph Report - butterfly-gateway-multi-consumer-foundation  (2026-08-05)

## Corpus Check
- 274 files · ~285,705 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3890 nodes · 10524 edges · 194 communities (178 shown, 16 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 777 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b825f5f2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- token_manager.py
- TradeRecord
- test_order_manager.py
- OrderIntentQueries
- schemas.py
- ButterflyChartSpec
- FakeAccessFunctionFactory
- SchwabClientWrapper
- discover_options_strategy.py
- OptionQuote
- credential_proof_fingerprint.py
- 4. Detailed findings
- .refresh
- CandidateRegistry
- forex_calendar.py
- run_backtest_db.py
- MinuteBar
- CsvDataLoader
- run_live.py
- _assert_broker_state_matches_db
- test_equity_scan.py
- InternalKeyAuthenticator
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- MarketSnapshot
- StrategySettings
- upstream.py
- run_entry_analysis.py
- test_gateway_config.py
- Domain Model and Ingestion Boundaries
- ProfitStateMachine
- test_risk_engine.py
- test_black_scholes.py
- news.py
- backfill_equity_candles.py
- test_gateway_credential_probe.py
- performance_chart.py
- Current Schwab Integration
- run_classifier_sweep.py
- test_candidate_settlement.py
- api.py
- AtomicSnapshotStore
- DiscordNotifier
- AlertmanagerNotifier
- DayData
- equity_trade_chart.py
- EntrySelectionResult
- report_exit_mark_parity.py
- SyntheticChainGenerator
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- test_gateway_credential_proof_operator.py
- load_config
- Database Compatibility
- time_utils.py
- test_comparison_stats.py
- Schwab Gateway Migration Plan
- black_scholes.py
- create_app
- gateway_client/models.py
- report_trade_ladders.py
- ButterflyGuy Code Review State
- test_candidate_snapshot.py
- universes.py
- NamedTuple
- DbDataLoader
- feed.py
- GapRegimeFilter
- scanner.py
- Behavioral Specification
- Path
- populated_state
- ChainDay
- .generate_chain
- run_morning_scan.py
- core/config.py
- 1. Charles Schwab API
- CaptureFixture
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
- AppConfig
- ButterflyGuy Fable 5 Refactor Plan
- 2026-07-14 — data audit and research design
- Codex Project State
- .session_close
- Capability recorder design
- DirectSchwabMarketDataProvider
- Schwab Single-Token Manager
- XSP Opportunistic Partial-Fill Evidence Plan
- TradeService
- test_run_backtest_db.py
- redact
- synthetic_chain.py
- ButterflyOrderBuilder
- position_manager.py
- ButterflyGuy data sources — representative samples
- Schwab Gateway Foundation: Local Run
- test_run_live.py
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
- _MetricsHandler
- CandidateEvaluator
- TestEma
- GatewaySettings
- test_run_migrations.py
- Schwab Gateway Foundation Smoke Test
- test_candidate_provider.py
- StaticTokenReadinessProvider
- load_spot_series
- schwab_gateway/__init__.py
- Schwab Gateway Credential Proof
- select_entry_candidate
- test_gateway_admission.py
- set_readiness
- Strategy Settings
- record_equity_market_data.py
- TokenManagerHealth
- test_credential_proof_fingerprint.py
- daily_report_card_config.py
- prepare_args
- ButterflyCandidate
- .can_trade
- GatewayCredentialProbeSettings
- test_order_preview.py
- Width Selection
- _repair_filled_entry_intent
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Schwab Gateway Multi-Consumer Foundation
- test_equity_market_data.py
- test_token_keepalive_reports_alertmanager_state
- 9) Capture equity candles and Level II for trade review
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
4. `OperatorFailure` - 78 edges
5. `AppConfig` - 75 edges
6. `MinuteBar` - 67 edges
7. `MarketSnapshot` - 63 edges
8. `DatabasePool` - 59 edges
9. `SnapshotIdentity` - 52 edges
10. `StrategySettings` - 50 edges

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

## Communities (194 total, 16 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.11
Nodes (38): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close() (+30 more)

### Community 1 - "token_manager.py"
Cohesion: 0.11
Nodes (20): RLock, _AtomicFileTokenTransaction, _fsync_directory(), Enum, Path, str, Locked, atomic token persistence without a Schwab runtime dependency., A refresh callback uses this to classify an upstream revocation. (+12 more)

### Community 2 - "TradeRecord"
Cohesion: 0.21
Nodes (21): A trade record for tracking entry/exit., TradeRecord, final_regular_session_close_from_candles(), Return the latest Schwab 1-minute close in the regular session., _candle(), asyncio, datetime, parametrize (+13 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.16
Nodes (58): LiveSpread, NamedTuple, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+50 more)

### Community 4 - "OrderIntentQueries"
Cohesion: 0.07
Nodes (9): OrderIntentQueries, Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Queries for durable broker order intents., Dollar PnL for the rolling 7-day window (closed trades only)., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict. (+1 more)

### Community 5 - "schemas.py"
Cohesion: 0.12
Nodes (20): Pydantic models for option data and trade records., ButterflySelector, Butterfly selector — picks the best candidate from a list., Selects the best butterfly candidate., Select the best butterfly candidate. When `target_center` is provided (derived…, Select the candidate whose cost is closest to its max_cost_per_width., Shared entry selection for live trading and backtests., Helpers for choosing a candidate across multiple active widths. (+12 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.10
Nodes (44): trade_pnl_dollars(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series() (+36 more)

### Community 7 - "FakeAccessFunctionFactory"
Cohesion: 0.24
Nodes (18): adapter(), FakeAccessFunctionFactory, FakeClient, manager(), Any, MonkeyPatch, Path, Mimic schwab-py 1.5.1 TokenMetadata wrapping without importing schwab. (+10 more)

### Community 8 - "SchwabClientWrapper"
Cohesion: 0.06
Nodes (38): ExecutionSettings, RiskSettings, SchwabSettings, Any, date, Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order once and return the order ID. Order placement is not retried… (+30 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "OptionQuote"
Cohesion: 0.10
Nodes (27): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes(), fly_mark_value() (+19 more)

### Community 11 - "credential_proof_fingerprint.py"
Cohesion: 0.06
Nodes (156): _accepted_fingerprint_hashes(), _accepted_runtime_baseline(), _accepted_snapshots(), _approval_1_execute(), _approval_2_execute(), _approved_staging_tmpfs(), _approved_tmpfs_entry(), _approved_window() (+148 more)

### Community 12 - "4. Detailed findings"
Cohesion: 0.04
Nodes (45): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix, 6. Duplication map (+37 more)

### Community 13 - ".refresh"
Cohesion: 0.16
Nodes (11): Run one fake/replaceable refresh callback under the exclusive token lock., Run an SDK-shaped token read/client operation/write lifecycle under one lock., Keep SDK token callbacks live only for one manager-owned transaction., _ScopedTokenCallbacks, TokenCallbackScopeError, TokenExpiredError, TokenRefreshError, TokenAccessOperation (+3 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.12
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "run_backtest_db.py"
Cohesion: 0.06
Nodes (89): _asset_drawdowns(), backtest_entry_price(), candidate_from_trade_row(), _dd_schedule_label(), discover_dates(), _duration_min(), _find_bar_at(), _find_entry_bar_at() (+81 more)

### Community 17 - "MinuteBar"
Cohesion: 0.08
Nodes (27): CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, MinuteBar, Shared backtest market-data models., DB-backed data loader for historical SPX + VIX data. Reads from the live…, Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).…, BiasScoreFilter, Multi-signal directional bias filter for 0-DTE butterfly entries., High and low of the opening range (bars with ET time < 09:45). Edge case: no OR… (+19 more)

### Community 18 - "CsvDataLoader"
Cohesion: 0.25
Nodes (8): DataFrame, CsvDataLoader, date, Path, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files…

### Community 19 - "run_live.py"
Cohesion: 0.04
Nodes (62): BoundLogger, Schwab market-data client deliberately lacking every account/order operation., get_logger(), Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs., Get a structlog logger with optional name., setup_logging(), Prometheus metrics for monitoring. (+54 more)

### Community 20 - "_assert_broker_state_matches_db"
Cohesion: 0.19
Nodes (23): order_ids(), walk_orders(), _assert_broker_state_matches_db(), _expired_trade_has_broker_settlement(), _order_symbols(), date, broker_fill_payload(), asyncio (+15 more)

### Community 21 - "test_equity_scan.py"
Cohesion: 0.17
Nodes (35): EquityScanSettings, build_snapshots(), parse_equity_quote(), passes_filters(), datetime, _quote_age_seconds(), rank_catalyst_watch(), rank_scan_results() (+27 more)

### Community 22 - "InternalKeyAuthenticator"
Cohesion: 0.12
Nodes (25): Enum, hash_api_key(), InternalKeyAuthenticator, InternalPrincipal, Path, Internal service authentication with hashed, capability-scoped API keys., principal(), parametrize (+17 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.08
Nodes (42): ProfitManagementStrategy, DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains., Runs full strategy on a single day using synthetic options., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. Skips… (+34 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.13
Nodes (36): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders(), detect_problems(), _extract_order_id() (+28 more)

### Community 25 - "report.py"
Cohesion: 0.14
Nodes (34): archive_report(), archive_report_json(), build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality() (+26 more)

### Community 26 - "MarketSnapshot"
Cohesion: 0.05
Nodes (41): Lease, Persist once and return the canonical evidence for this session., SessionContext, Paper-only SPX candidate fleet fed by a shared market-data service., _aware_utc(), MarketSnapshot, Any, datetime (+33 more)

### Community 27 - "StrategySettings"
Cohesion: 0.17
Nodes (23): StrategySettings, main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date. Replicates the…, ButterflyBuilder, O(N*W) butterfly construction and scoring engine., Builds and scores butterfly spreads from an option chain snapshot. (+15 more)

### Community 28 - "upstream.py"
Cohesion: 0.12
Nodes (23): EquityQuoteProvider, Protocol, Injected boundary for the token manager's bounded readiness state., Fail closed when an app has no injected readiness dependency., TokenReadinessProvider, _UnavailableTokenReadinessProvider, DirectSchwabQuoteUpstream, _event_time() (+15 more)

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
Cohesion: 0.08
Nodes (51): ProfitManagementSettings, PositionState, Current state of an open position., ExitSignal, ProfitState, ProfitStateMachine, Enum, Transition between profit states. (+43 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "test_black_scholes.py"
Cohesion: 0.13
Nodes (16): bs_delta(), Delta — rate of change of price wrt spot., Tests for Black-Scholes pricing and Greeks., ATM call price should be approximately S * sigma * sqrt(T/2pi)., Deep ITM call should be approximately S - K * exp(-rT)., Deep ITM put should be approximately K - S., Expired call should equal intrinsic value., Put-call delta parity: call_delta - put_delta = 1. (+8 more)

### Community 35 - "news.py"
Cohesion: 0.16
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 36 - "backfill_equity_candles.py"
Cohesion: 0.16
Nodes (18): Any, date, datetime, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session., Write a deterministic JSON candle snapshot. (+10 more)

### Community 37 - "test_gateway_credential_probe.py"
Cohesion: 0.16
Nodes (16): FakeClient, FakeFactory, FakeResponse, CaptureFixture, MonkeyPatch, Path, settings(), test_probe_command_bounds_configuration_failure() (+8 more)

### Community 38 - "performance_chart.py"
Cohesion: 0.19
Nodes (19): compute_stats(), ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels() (+11 more)

### Community 39 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 40 - "run_classifier_sweep.py"
Cohesion: 0.20
Nodes (17): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday… (+9 more)

### Community 41 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 42 - "api.py"
Cohesion: 0.18
Nodes (21): audit_middleware(), _error(), health(), _json(), metrics(), _parse_symbols(), Application, middleware (+13 more)

### Community 43 - "AtomicSnapshotStore"
Cohesion: 0.13
Nodes (20): AtomicSnapshotStore, CandidateFeed, LeaseRegistry, Condition-guarded pointer swap; readers never observe partial snapshots., SnapshotArchive, main(), Run the demand-aware shared SPX candidate market-data feed., FakeArchive (+12 more)

### Community 44 - "DiscordNotifier"
Cohesion: 0.16
Nodes (8): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook., main(), parse_reference_date(), date, Send SPX weekend review to Discord #weekend-review. Cron: Saturday 9:00 AM PT 0…

### Community 45 - "AlertmanagerNotifier"
Cohesion: 0.13
Nodes (16): AlertmanagerNotifier, Sends centrally deduplicated critical alerts through Alertmanager., asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_alertmanager_payload_has_stable_redacted_fingerprint() (+8 more)

### Community 46 - "DayData"
Cohesion: 0.10
Nodes (22): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), DayData, date (+14 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (31): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+23 more)

### Community 48 - "EntrySelectionResult"
Cohesion: 0.27
Nodes (13): EntrySelectionResult, build_entry_selection_parity(), _candidate_payload(), _per_width_payload(), Compare live Schwab entry selection against nearest DB chain snapshot., Return a JSON-serializable Schwab vs DB selection comparison., Result of a single entry selection pass., _candidate() (+5 more)

### Community 49 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 50 - "SyntheticChainGenerator"
Cohesion: 0.25
Nodes (14): Generates a synthetic SPX option chain from spot + VIX., SyntheticChainGenerator, make_snapshot_time(), datetime, Tests for the synthetic chain generator., Create a snapshot time N minutes before 4pm ET., Volatility skew: OTM puts should have higher IV than equidistant OTM calls., Option price should decrease as expiration approaches. (+6 more)

### Community 51 - "live_performance.py"
Cohesion: 0.09
Nodes (48): now_pacific(), Current time in US/Pacific., chart_payload(), cumulative_equity(), drawdown_series(), DrawdownPoint, duration_minutes(), format_et_time() (+40 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "test_gateway_credential_proof_operator.py"
Cohesion: 0.10
Nodes (42): compose_pair(), MonkeyPatch, parametrize, The operator account has no passwordless sudo on the non-interactive proof path., The container init is the app; a namespace-internal SIGSTOP to PID 1 is ignored., The probe must never suspend SPX during preflight., Docker writes the --time deprecation notice to stdout, breaking the exact-…, Never stop a container that actually exists. (+34 more)

### Community 55 - "load_config"
Cohesion: 0.10
Nodes (27): load_config(), Path, Load configuration from YAML file and environment variables., main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run… (+19 more)

### Community 56 - "Database Compatibility"
Cohesion: 0.13
Nodes (14): `001_initial.sql`: `option_chain_snapshots`, `001_initial.sql`: `spot_prices`, `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, `005_add_daily_bars.sql`, Anonymized Synchronized Data Slice, Daily Bar Shape Example, `daily_bars` (+6 more)

### Community 57 - "time_utils.py"
Cohesion: 0.09
Nodes (50): _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_premarket_window(), is_trading_day(), _last_weekday(), market_close_time() (+42 more)

### Community 58 - "test_comparison_stats.py"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 59 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 60 - "black_scholes.py"
Cohesion: 0.26
Nodes (12): bs_call_price(), bs_put_price(), bs_theta(), _d1(), _d2(), Black-Scholes option pricing and Greeks., Black-Scholes European call price. Args: S: Spot price K: Strike price T: Time…, Black-Scholes European put price. (+4 more)

### Community 61 - "create_app"
Cohesion: 0.21
Nodes (17): GatewayMarketDataClient, AsyncClient, Typed client for gateway market-data endpoints only., create_app(), authenticator(), FakeQuoteUpstream, FakeTokenReadinessProvider, asyncio (+9 more)

### Community 62 - "gateway_client/models.py"
Cohesion: 0.13
Nodes (23): GatewayAuthenticationError, GatewayAuthorizationError, GatewayCapacityError, GatewayClientError, GatewayResponseError, GatewayTimeoutError, GatewayUnavailableError, RuntimeError (+15 more)

### Community 63 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 64 - "ButterflyGuy Code Review State"
Cohesion: 0.12
Nodes (15): Architecture map, ButterflyGuy Code Review State, Changes implemented, Commands executed, Current phase, Decisions already made, Exact next actions, Files and directories reviewed (+7 more)

### Community 65 - "test_candidate_snapshot.py"
Cohesion: 0.33
Nodes (12): asyncio, datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry(), test_long_poll_never_replays_same_sequence(), test_new_lease_wakes_idle_feed() (+4 more)

### Community 66 - "universes.py"
Cohesion: 0.06
Nodes (62): _as_float(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols(), fetch_sp500_rows() (+54 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.16
Nodes (13): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+5 more)

### Community 69 - "feed.py"
Cohesion: 0.26
Nodes (16): _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs(), _metrics(), _pin_snapshot() (+8 more)

### Community 70 - "GapRegimeFilter"
Cohesion: 0.14
Nodes (12): GapRegimeFilter, Enum, str, Market regime classifier for 0-DTE butterfly parameter dispatch. Classifies…, Return Regime for today given prior daily closes and today's VIX. Args:…, Regime, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped. (+4 more)

### Community 71 - "scanner.py"
Cohesion: 0.19
Nodes (19): _as_float(), _as_int(), filter_movers(), _focus_reasons(), MarketContext, _mid_bid_ask(), _mover_change_pct(), _mover_symbol() (+11 more)

### Community 72 - "Behavioral Specification"
Cohesion: 0.09
Nodes (22): Algorithmic Refinements For 0-DTE Robustness, Behavioral Specification, Bid-Ask Spread Penalization, Candidate Construction Invariants, Current Config Defaults, Current Width And Center Selection Data, Double-Factor Live Gating, Dynamic Wing Width Formula (+14 more)

### Community 73 - "Path"
Cohesion: 0.11
Nodes (30): legacy_capture_args(), patch_legacy_capture_provenance(), Path, The staged subset must import on its own; the deployed image has no…, runtime_inspect(), test_accepted_snapshot_discovery_extracts_bounded_composite_supplement(), test_accepted_snapshot_discovery_rejects_duplicate_composite_records(), test_accepted_snapshot_discovery_rejects_insecure_or_partial_records() (+22 more)

### Community 74 - "populated_state"
Cohesion: 0.18
Nodes (24): approval_args(), patch_approval_checks(), patch_restoration_success(), populated_state(), Namespace, runtime_baseline_state(), test_approval_2_runs_credential_command_exactly_once_without_retry(), test_approval_timer_race_restores_without_invoking_credentials() (+16 more)

### Community 75 - "ChainDay"
Cohesion: 0.14
Nodes (24): dict, chain_cache_path(), ChainDay, load_chain_day(), nearest_snapshot(), date, datetime, Path (+16 more)

### Community 76 - ".generate_chain"
Cohesion: 0.20
Nodes (10): bs_gamma(), bs_vega(), Gamma — rate of change of delta wrt spot., Vega — sensitivity to 1% change in IV., date, datetime, Minutes until market close on expiration day., Generate full synthetic option chain for one expiration. Args: spot: Underlying… (+2 more)

### Community 77 - "run_morning_scan.py"
Cohesion: 0.11
Nodes (26): load_equity_scan_config(), Path, Load equity scan settings from YAML., attach_news_impacts(), Attach catalyst metadata without changing quote normalization., _as_int(), avg_daily_volume(), compute_rvol() (+18 more)

### Community 78 - "core/config.py"
Cohesion: 0.16
Nodes (20): CollectorSettings, ConfigModel, DatabaseSettings, MonitoringSettings, PeakTrackingSettings, BaseModel, QuoteQualitySettings, Configuration management using Pydantic settings. (+12 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 80 - "CaptureFixture"
Cohesion: 0.21
Nodes (21): baseline_candidate_args(), patch_baseline_candidate_success(), patch_runtime_baseline_success(), CaptureFixture, runtime_baseline_args(), test_baseline_candidate_capture_distinguishes_invalid_compose_hash_output(), test_baseline_candidate_capture_limits_compose_and_image_equality_to_trading_set(), test_baseline_candidate_capture_persists_bounded_failed_check() (+13 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.17
Nodes (16): parse_trade_transactions(), Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options)., test_build_equity_trade_chart_png_returns_png_bytes(), test_chartable_equity_trades_skips_options() (+8 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.13
Nodes (40): TradePoint, build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_performance_caption(), format_review_header() (+32 more)

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
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.25
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 91 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.18
Nodes (7): Any, date, Authenticate a Schwab client without resolving or retaining an account., ReadOnlySchwabMarketDataClient, asyncio, MonkeyPatch, test_token_refresh_is_retained_in_memory_without_writing_file()

### Community 92 - "AppConfig"
Cohesion: 0.06
Nodes (60): Pool, assert_candidate_safety(), CandidateAuditContext, CandidateDecisionQueries, CandidatePaperExecutor, CandidatePerformanceStats, config_sha256(), Path (+52 more)

### Community 93 - "ButterflyGuy Fable 5 Refactor Plan"
Cohesion: 0.13
Nodes (14): ButterflyGuy Fable 5 Refactor Plan, Closed Design Decisions, Completion Definition, Document Map, Fable Prompting Guidance, Implementation Phases, Non-Negotiable Constraints, Phase 1: Database Adapter And Historical Ingestion (+6 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "Codex Project State"
Cohesion: 0.14
Nodes (13): Codex Project State, Current Phase, Current Slice, Decisions Made, Known Failures, Next Exact Action, Objective, Open Questions (+5 more)

### Community 96 - ".session_close"
Cohesion: 0.20
Nodes (10): _final_regular_session_close(), _previous_close(), Any, date, datetime, LeaseKind, time, Return one cached, verified final regular-session SPX close per date. (+2 more)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "DirectSchwabMarketDataProvider"
Cohesion: 0.14
Nodes (6): DirectSchwabMarketDataProvider, Any, date, Delegate to the current client without owning its lifecycle or changing data., asyncio, test_direct_provider_delegates_without_transforming_results()

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "XSP Opportunistic Partial-Fill Evidence Plan"
Cohesion: 0.29
Nodes (6): Completion, Current evidence, Decision, If one occurs naturally, Required artifacts, XSP Opportunistic Partial-Fill Evidence Plan

### Community 101 - "TradeService"
Cohesion: 0.12
Nodes (16): capped_entry_limit(), Shared entry-price limit policy for production and candidate runtimes., Return a cent-valid debit limit that never exceeds the configured maximum., _age_seconds(), Any, date, datetime, Orchestrates the full entry/exit trading flow. (+8 more)

### Community 102 - "test_run_backtest_db.py"
Cohesion: 0.20
Nodes (11): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), test_fitted_density_counts_returns_bucket_heights(), test_hypothetical_monitoring_load_uses_collector_only() (+3 more)

### Community 103 - "redact"
Cohesion: 0.33
Nodes (5): Any, Small defensive redaction layer for gateway audit metadata., Return a recursively redacted copy suitable for bounded audit metadata., redact(), test_redaction_removes_nested_credentials_and_account_identifiers()

### Community 104 - "synthetic_chain.py"
Cohesion: 0.20
Nodes (6): IVModel, Implied volatility model with VIX scaling and skew adjustment., Models implied volatility with VIX scaling and volatility skew., Convert VIX index value to 0-DTE ATM IV estimate. VIX is the 30-day implied vol…, Compute skew-adjusted IV for a given strike. OTM puts have elevated IV…, Synthetic option chain generator using Black-Scholes + VIX IV model.

### Community 105 - "ButterflyOrderBuilder"
Cohesion: 0.21
Nodes (12): ButterflyOrderBuilder, Any, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_candidate(), Tests for butterfly order builder. (+4 more)

### Community 106 - "position_manager.py"
Cohesion: 0.25
Nodes (6): compute_tent_boundaries(), _quote_quality_ok(), Position value tracking and management., Find the two spot prices where the fly's BS mark equals entry cost. These are…, implied_vol(), Back-solve for implied volatility given an option market price. Returns None if…

### Community 107 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 109 - "test_run_live.py"
Cohesion: 0.26
Nodes (17): _never_awaited(), asyncio, parametrize, _synthetic_butterfly_snapshot(), _synthetic_position(), test_entry_loop_alerts_after_monitor_safety_error(), test_runtime_reconciliation_degrades_readiness_on_dependency_failure(), test_runtime_reconciliation_sets_gate_unsafe_for_wrong_ratio() (+9 more)

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
Cohesion: 0.27
Nodes (11): archive_report(), date, Path, chartable_equity_trades(), date, datetime, Path, Daily report card orchestration — fetch Schwab data, build, post to Discord. (+3 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 121 - "CandidateEvaluator"
Cohesion: 0.18
Nodes (10): candidate_fill_parity_failures(), _candidate_mark(), candidate_performance_stats(), CandidateEvaluator, Any, Summarize one chronological, closed mark_v1 PnL cohort., Count mark_v1 rows whose fills disagree with their recorded evidence., _restore_trade() (+2 more)

### Community 123 - "GatewaySettings"
Cohesion: 0.33
Nodes (3): GatewaySettings, field_validator, Path

### Community 124 - "test_run_migrations.py"
Cohesion: 0.43
Nodes (5): fake_db(), FakeConnection, asyncio, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 125 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 126 - "test_candidate_provider.py"
Cohesion: 0.31
Nodes (11): Build a synchronous schwab-py handler that never blocks the stream., make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close(), test_http_and_schwab_provider_contracts_normalize_equally() (+3 more)

### Community 127 - "StaticTokenReadinessProvider"
Cohesion: 0.13
Nodes (16): AdmissionCapacityError, AdmissionController, AdmissionPolicy, RuntimeError, Bounded in-process admission policy for gateway market-data reads., The caller's bounded priority pool has no available permit., Keep background work out of ButterflyGuy's protected capacity., Expose bounded state for deterministic fake-only tests. (+8 more)

### Community 128 - "load_spot_series"
Cohesion: 0.50
Nodes (4): load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles()

### Community 129 - "schwab_gateway/__init__.py"
Cohesion: 0.40
Nodes (4): __getattr__(), Any, Read-only Schwab gateway foundation., Import ``api`` lazily so the reviewed credential-proof subset loads standalone.

### Community 130 - "Schwab Gateway Credential Proof"
Cohesion: 0.06
Nodes (33): Accepted runtime-baseline proof adapter, Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05 (+25 more)

### Community 132 - "select_entry_candidate"
Cohesion: 0.12
Nodes (28): EntrySettings, VixWidthBucket, Return the first regular-session open for the requested Eastern date., _session_open_from_intraday_candles(), _bucket_sigmas(), Return sigma anchors spanning narrow to wide for the bucket size., Return (widths, sigma_fractions) for the active VIX bucket. Buckets are…, resolve_wing_widths_for_vix() (+20 more)

### Community 133 - "test_gateway_admission.py"
Cohesion: 0.37
Nodes (9): authenticator(), BlockingUpstream, headers(), asyncio, ready_provider(), test_identity_claim_header_cannot_override_authenticated_caller(), test_normalized_upstream_failure_releases_permit_for_next_request(), test_permits_release_after_success_failure_timeout_and_cancellation() (+1 more)

### Community 134 - "set_readiness"
Cohesion: 0.20
Nodes (14): clear_readiness(), Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., readiness_snapshot(), set_readiness(), broker_reconciler_loop(), entry_loop(), Periodically attempt entries during the entry window. (+6 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "record_equity_market_data.py"
Cohesion: 0.20
Nodes (15): JsonlStreamRecorder, Event, Non-blocking stream handlers backed by one JSONL file per Schwab service., Drain queued events until the stop flag is set and the queue is empty., async_main(), _install_signal_handlers(), main(), parse_args() (+7 more)

### Community 137 - "TokenManagerHealth"
Cohesion: 0.13
Nodes (9): AbstractContextManager, Any, datetime, Protocol, Operations available only while a token-store lock is held., Replaceable persistence boundary for one logical token document., TokenManagerHealth, TokenStore (+1 more)

### Community 138 - "test_credential_proof_fingerprint.py"
Cohesion: 0.29
Nodes (13): docker_inspect(), CaptureFixture, MonkeyPatch, parametrize, Path, test_canonical_fingerprint_is_independent_of_semantically_unordered_fields(), test_cli_bounds_docker_failure_without_raw_exception(), test_cli_exact_and_staging_verification_are_bounded() (+5 more)

### Community 139 - "daily_report_card_config.py"
Cohesion: 0.33
Nodes (5): load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds

### Community 140 - "prepare_args"
Cohesion: 0.20
Nodes (15): patch_approval_1_success(), patch_prepare_success(), prepare_args(), A stop-output defect must fail in preflight, not after NDX has already been…, A watchdog prerequisite must fail in preflight, not inside the one authorized…, test_approval_1_success_arms_both_watchdogs_and_starts_two_minute_gate(), test_post_recreation_watchdog_failure_invokes_immediate_restoration(), test_pre_recreation_failure_does_not_mutate_or_restore() (+7 more)

### Community 141 - "ButterflyCandidate"
Cohesion: 0.06
Nodes (65): entry_fill_within_limit(), Return whether an entry fill respects its hard debit ceiling., get_0dte_expiration(), now_utc(), Calendar date for the US/Eastern trading session., Get today's date as the 0-DTE expiration (SPX has daily expirations)., session_date(), iter_chain_options() (+57 more)

### Community 142 - ".can_trade"
Cohesion: 0.17
Nodes (6): date, Record that a trade was executed., Record realized dollar PnL., Overwrite dollar realized_pnl in risk state (SET, not ADD). Used at startup to…, Manually sync the trade count in the risk state table. Used at startup to…, Check risk conditions before entry. Returns (allowed, reason). buying_power is…

### Community 143 - "GatewayCredentialProbeSettings"
Cohesion: 0.20
Nodes (10): GatewayCredentialProbeSettings, BaseSettings, Validated configuration for the isolated gateway process., Explicit real-credential inputs for the standalone quote proof only., _load_runtime_dependencies(), main(), _parser(), ArgumentParser (+2 more)

### Community 144 - "test_order_preview.py"
Cohesion: 0.27
Nodes (10): make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate., Order spec must have all fields Schwab requires., Schwab expects price as a string., test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields() (+2 more)

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 146 - "_repair_filled_entry_intent"
Cohesion: 0.29
Nodes (10): _broker_option_positions(), _explicit_fill_details(), _intent_order_ids(), _json_dict(), _matches_underlying(), _open_trade_positions(), Any, _repair_filled_entry_intent() (+2 more)

### Community 147 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 148 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 149 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 150 - "test_equity_market_data.py"
Cohesion: 0.38
Nodes (6): asyncio, test_jsonl_recorder_persists_raw_message(), test_subscribe_registers_handlers_before_nyse_services(), test_symbol_directory_is_stable_and_sanitizes_path_characters(), test_symbol_directory_rejects_parent_directory_symbol(), test_write_candle_snapshot_sorts_candles()

### Community 152 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

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
- **440 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `Objective`, `Current Phase` (+435 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `_restore_argv()` connect `credential_proof_fingerprint.py` to `MarketSnapshot`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `get_logger()` connect `run_live.py` to `run_paper_replay.py`, `token_manager.py`, `schemas.py`, `ButterflyChartSpec`, `ButterflyCandidate`, `run_backtest_db.py`, `MinuteBar`, `simulation_engine.py`, `StrategySettings`, `run_entry_analysis.py`, `news.py`, `run_classifier_sweep.py`, `api.py`, `time_utils.py`, `universes.py`, `feed.py`, `run_morning_scan.py`, `weekend_review.py`, `AtomicTokenManager`, `AppConfig`, `ButterflyOrderBuilder`, `position_manager.py`, `services/daily_report_card.py`, `StaticTokenReadinessProvider`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `test_order_manager.py`, `select_entry_candidate`, `schemas.py`, `ButterflyCandidate`, `run_backtest_db.py`, `MinuteBar`, `run_live.py`, `MarketSnapshot`, `StrategySettings`, `run_entry_analysis.py`, `ProfitStateMachine`, `AtomicSnapshotStore`, `EntrySelectionResult`, `report_exit_mark_parity.py`, `SyntheticChainGenerator`, `test_candidate_snapshot.py`, `DbDataLoader`, `feed.py`, `ChainDay`, `.generate_chain`, `core/config.py`, `AppConfig`, `.session_close`, `TradeService`, `synthetic_chain.py`, `position_manager.py`, `test_candidate_provider.py`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `SchwabClientWrapper` (e.g. with `CollectorMarketDataProvider` and `DirectSchwabMarketDataProvider`) actually correct?**
  _`SchwabClientWrapper` has 21 INFERRED edges - model-reasoned connections that need verification._