# Graph Report - Butterflyguy  (2026-08-15)

## Corpus Check
- 257 files · ~292,136 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3508 nodes · 8467 edges · 201 communities (182 shown, 19 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 964 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d643b08`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- core/config.py
- time_utils.py
- test_order_manager.py
- ShadowComparingMarketDataProvider
- test_candidate_provider.py
- trade_chart.py
- run_live.py
- schemas.py
- discover_options_strategy.py
- EntrySelectionResult
- SchwabSettings
- position_service.py
- logging.py
- CandidateRegistry
- forex_calendar.py
- run_backtest_db.py
- make_bar
- CsvDataLoader
- shadow.py
- _assert_broker_state_matches_db
- test_equity_scan.py
- Enum
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- MarketSnapshot
- ReadOnlySchwabMarketDataClient
- Any
- test_chain_parser_parity.py
- _build_collector_market_data
- load_date_data
- ProfitStateMachine
- test_risk_engine.py
- SyntheticChainGenerator
- news.py
- test_live_performance_report.py
- MinuteBar
- performance_chart.py
- Current Schwab Integration
- SchwabClientWrapper
- test_candidate_settlement.py
- get_logger
- test_candidate_feed.py
- AlertmanagerNotifier
- test_schwab_token_keepalive.py
- SchwabDataLoader
- equity_trade_chart.py
- session_date
- report_exit_mark_parity.py
- DiscordNotifier
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- download_schwab_cache.py
- load_config
- StrategySettings
- OptionQuote
- test_comparison_stats.py
- Schwab Gateway Migration Plan
- Any
- test_candidate_variants.py
- TradeQueries
- test_gateway_phase7_boundaries.py
- ._ema
- ButterflyOrderBuilder
- universes.py
- NamedTuple
- DbDataLoader
- CandidateFeed
- Regime
- scanner.py
- data_loader.py
- TradePoint
- notify.py
- ChainDay
- Branch Review and Integration Plan
- run_morning_scan.py
- Window A — Token re-authorization (mandatory)
- 1. Charles Schwab API
- BrokerStateGate
- test_daily_report_card.py
- weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- install_shutdown_handler
- run_entry_analysis.py
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- evaluator.py
- 2026-07-14 — data audit and research design
- Codex Project State
- Re-authorization checklist — Saturday 2026-08-15
- Capability recorder design
- Schwab Single-Token Manager
- run_classifier_sweep.py
- Standalone SchwabGateway Extraction Plan
- record_equity_market_data.py
- Option A deployment runbook — Helios, containerized
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- Schwab Gateway Foundation: Local Run
- test_run_live.py
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
- report_trade_ladders.py
- report_broker_order_statuses.py
- Window D — the gateway made reachable, started, and watched (2026-08-08)
- test_run_migrations.py
- Schwab Gateway Foundation Smoke Test
- HttpMarketDataProvider
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- Reducing the weekly re-authorization cost — a scoping question
- Schwab Gateway Credential Proof
- test_gateway_compose.py
- trade_service.py
- C3 — wiring shadow reads into `run_live.py`
- Schwab gateway deployment options
- Strategy Settings
- generate_live_performance.py
- DirectSchwabMarketDataProvider
- ButterflyCandidate
- test_candidate_snapshot.py
- resolve_db_dsn
- Width Selection
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Schwab Gateway Multi-Consumer Foundation
- CandidatePaperExecutor
- Window C — the two token writers resolved (2026-08-08)
- 9) Capture equity candles and Level II for trade review
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- feed.py
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- test_candidate_evaluator_accounting.py
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)
- ButterflyGuy data sources and data types
- Equity candles and order-book recording
- Bounded proof failure codes and a settled restoration error window — 2026-08-06
- Credential proof passed — 2026-08-06
- test_run_backtest_db_defaults.py
- Window A Executed — token re-authorized (2026-08-08)
- butterfly mark
- The token reload is DEPLOYED (2026-08-09T21:59:16Z)
- test_gateway_token_manager.py
- test_auth_init_honours_schwab_token_path
- Preflight stops on the host-executed release — 2026-08-06
- Host-executed proof step
- First token read, and a read-only container filesystem — 2026-08-06
- Live Runbook
- Operator-named absolute token path
- SessionClose
- DatabasePool
- Layered Risk Management
- Geometric butterfly icon
- 7. Operational and observability data
- ButterflyGuy data sources — representative samples
- test_collector.py
- RegimeFilter
- 3) Start the SPX stack in Docker
- Offline safety-drill record — 2026-07-13
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- Critical External-Alert Delivery Proof - 2026-07-15
- XSP Flat-Runtime Restart Proof - 2026-07-14
- test_performance_dashboard.py
- collector.py
- auth_init.py
- schwab-gateway-phase-7-execution-prompt.md
- butterfly_guy/__init__.py
- equity_scan/__init__.py
- reports/__init__.py
- run_live_performance_cron.sh
- run_morning_scan_cron.sh
- Compare Real vs Synthetic Chains
- butterfly-guy

## God Nodes (most connected - your core abstractions)
1. `ButterflyCandidate` - 89 edges
2. `SchwabClientWrapper` - 85 edges
3. `OptionQuote` - 80 edges
4. `AppConfig` - 63 edges
5. `MarketSnapshot` - 58 edges
6. `MinuteBar` - 55 edges
7. `DatabasePool` - 52 edges
8. `main()` - 49 edges
9. `load_config()` - 48 edges
10. `PositionService` - 43 edges

## Surprising Connections (you probably didn't know these)
- `test_session_close_rejects_unauditable_timestamps()` --uses--> `SessionClose`  [INFERRED]
  tests/test_candidate_snapshot.py → src/butterfly_guy/candidate_fleet/models.py
- `test_config_rejects_unknown_keys()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_database_dsn()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_profit_management_strategy_defaults_to_peak_value_trailer()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot()` --uses--> `ChainDay`  [INFERRED]
  tests/test_run_backtest_db.py → src/butterfly_guy/backtest/chain_cache.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]

## Communities (201 total, 19 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.09
Nodes (39): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close() (+31 more)

### Community 1 - "core/config.py"
Cohesion: 0.10
Nodes (40): BaseSettings, AppConfig, CollectorSettings, ConfigModel, DatabaseSettings, EntrySettings, ExecutionSettings, MonitoringSettings (+32 more)

### Community 2 - "time_utils.py"
Cohesion: 0.08
Nodes (50): _easter_sunday(), get_0dte_expiration(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_trading_day(), _last_weekday(), market_close_time() (+42 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.15
Nodes (58): LiveSpread, NamedTuple, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+50 more)

### Community 4 - "ShadowComparingMarketDataProvider"
Cohesion: 0.06
Nodes (61): ChainMetadataResponseV1, SpotResponseV1, Butterfly Guy's consumer-specific shadow-read integration., _error_code(), _mismatch_code(), _numbers_agree(), Any, date (+53 more)

### Community 5 - "test_candidate_provider.py"
Cohesion: 0.26
Nodes (12): Any, Build a synchronous schwab-py handler that never blocks the stream., make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close() (+4 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.08
Nodes (47): _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles(), build_entry_chart_png() (+39 more)

### Community 7 - "run_live.py"
Cohesion: 0.12
Nodes (28): clear_readiness(), Prometheus metrics for monitoring., Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., Start HTTP server serving /metrics (Prometheus) and /health on *port*. Runs in…, set_readiness(), start_metrics_server(), trade_pnl_dollars() (+20 more)

### Community 8 - "schemas.py"
Cohesion: 0.13
Nodes (18): Pydantic models for option data and trade records., _bucket_sigmas(), O(N*W) butterfly construction and scoring engine., Return sigma anchors spanning narrow to wide for the bucket size., Return (widths, sigma_fractions) for the active VIX bucket. Buckets are…, resolve_wing_widths_for_vix(), Butterfly selector — picks the best candidate from a list., _active_widths_and_sigmas() (+10 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "EntrySelectionResult"
Cohesion: 0.27
Nodes (13): EntrySelectionResult, build_entry_selection_parity(), _candidate_payload(), _per_width_payload(), Compare live Schwab entry selection against nearest DB chain snapshot., Return a JSON-serializable Schwab vs DB selection comparison., Result of a single entry selection pass., _candidate() (+5 more)

### Community 11 - "SchwabSettings"
Cohesion: 0.18
Nodes (25): SchwabSettings, _accessors(), _account_client(), asyncio, Initialize a wrapper against a real token file, returning its read/write funcs., Wire a wrapper whose _build_client hands out `clients` in order., An ordinary hourly refresh rewrites the document but must not rebuild the…, A bad document must leave the process on the credential that still works. (+17 more)

### Community 12 - "position_service.py"
Cohesion: 0.08
Nodes (44): A trade record for tracking entry/exit., TradeRecord, broker_cash_settlement_from_transactions(), BrokerCashSettlement, _chain_spot_price(), final_regular_session_close_from_candles(), PositionService, Any (+36 more)

### Community 13 - "logging.py"
Cohesion: 0.12
Nodes (18): Schwab market-data client deliberately lacking every account/order operation., Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs., setup_logging(), Async Schwab API client wrapper with retry logic., main(), Refresh equity universe files (sp500, nq100, liquid)., run_refresh() (+10 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.12
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "run_backtest_db.py"
Cohesion: 0.08
Nodes (56): _asset_drawdowns(), backtest_entry_price(), day_with_monitoring_bars(), _dd_schedule_label(), _duration_min(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window() (+48 more)

### Community 17 - "make_bar"
Cohesion: 0.17
Nodes (9): High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Compute bias score from 4 signals: gap : +1 if entry_close > prev_close, -1 if…, Volume-weighted average price using close as typical price. Edge case: all…, make_bar(), make_pre_entry_bars(), Unit tests for BiasScoreFilter., Build n bars starting at 09:30 ET, incrementing by 1 minute each., TestComputeOr (+1 more)

### Community 18 - "CsvDataLoader"
Cohesion: 0.25
Nodes (8): DataFrame, CsvDataLoader, date, Path, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files…

### Community 19 - "shadow.py"
Cohesion: 0.20
Nodes (6): GatewayMarketDataClient, Phase 3 shadow comparison for the collector's spot and chain reads. This…, A bounded, fixed-shape observation. Carries no payload, path, or exception text., Tally discrepancies over a fixed key space; retains no observed values., ShadowDiscrepancy, ShadowDiscrepancyRecorder

### Community 20 - "_assert_broker_state_matches_db"
Cohesion: 0.31
Nodes (16): _assert_broker_state_matches_db(), broker_fill_payload(), asyncio, parametrize, test_filled_entry_intent_rejects_wrong_broker_ratio(), test_filled_entry_intent_rejects_zero_quantity(), test_filled_entry_intent_repairs_open_trade_only_with_matching_legs_and_fill(), test_filled_exit_intent_repairs_open_trade_only_when_broker_flat() (+8 more)

### Community 21 - "test_equity_scan.py"
Cohesion: 0.18
Nodes (33): EquityScanSettings, build_snapshots(), parse_equity_quote(), datetime, _quote_age_seconds(), rank_scan_results(), Normalize a Schwab quote payload into an EquitySnapshot., build_symbol_map() (+25 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.08
Nodes (38): ProfitManagementStrategy, DayData, DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains., Runs full strategy on a single day using synthetic options., Simulate one trading day. (+30 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.14
Nodes (33): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, count_rejected_orders(), detect_problems(), _extract_order_id(), _extract_trade_leg() (+25 more)

### Community 25 - "report.py"
Cohesion: 0.14
Nodes (33): archive_report(), archive_report_json(), build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality() (+25 more)

### Community 26 - "MarketSnapshot"
Cohesion: 0.09
Nodes (13): AtomicSnapshotStore, Condition-guarded pointer swap; readers never observe partial snapshots., Paper-only SPX candidate fleet fed by a shared market-data service., _aware_utc(), MarketSnapshot, datetime, Immutable normalized market snapshots shared by candidate evaluators., One atomically published, replayable view of candidate market data. (+5 more)

### Community 27 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.14
Nodes (20): Any, date, Prove the replacement credential with one bounded read-only Schwab call., Authenticate a Schwab client without resolving or retaining an account., Build one client with an isolated in-memory refresh-token callback., Validate and install a client built from a newly authorized token document., ReadOnlySchwabMarketDataClient, asyncio (+12 more)

### Community 28 - "Any"
Cohesion: 0.11
Nodes (11): _creation_timestamp(), Any, date, Read the document's re-authorization marker. `creation_timestamp` changes only…, Authenticate and resolve account hash., Rebuild the client if the token document has been re-authorized. schwab-py…, Fetch option chain for a specific symbol and expiration., Place an order once and return the order ID. Order placement is not retried… (+3 more)

### Community 29 - "test_chain_parser_parity.py"
Cohesion: 0.13
Nodes (25): _contract(), _parse_rows(), Any, date, parametrize, Differential tests pinning the three Schwab option-chain parsers against each…, Run the live collector row parser without touching the database or Schwab., call + put contract counts equal the row count the collector writes. (+17 more)

### Community 30 - "_build_collector_market_data"
Cohesion: 0.16
Nodes (16): GatewayClientSettings, _build_collector_market_data(), _close_runtime_resources(), GatewayMarketDataClient, Build the collector provider while keeping direct reads authoritative. Gateway…, Drain shadow work and close every owned resource, even if one close fails., test_gateway_client_mode_is_opt_in_and_secret_is_hidden(), test_gateway_client_mode_rejects_shadow_reads() (+8 more)

### Community 31 - "load_date_data"
Cohesion: 0.16
Nodes (21): discover_dates(), _force_synthetic_for_date(), get_prev_close(), get_recent_closes(), get_vix_prev_close(), load_bars_from_db(), load_chains_from_db(), load_date_data() (+13 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.05
Nodes (68): ProfitManagementSettings, QuoteQualitySettings, get_time_regime(), Classify minutes since open into a named time regime., compute_tent_boundaries(), fly_bid_value(), fly_settlement_value(), _max_leg_spread_to_mark_ratio() (+60 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SyntheticChainGenerator"
Cohesion: 0.05
Nodes (58): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+50 more)

### Community 35 - "news.py"
Cohesion: 0.16
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 36 - "test_live_performance_report.py"
Cohesion: 0.16
Nodes (16): NoTradeDay, render_trade_table_rows(), date, Tests for live performance report generation., Per-run data must stay in the non-executable JSON block. The published page's…, test_chart_payload_includes_drawdown_fields(), test_compute_stats(), test_is_drawdown_exit() (+8 more)

### Community 37 - "MinuteBar"
Cohesion: 0.17
Nodes (11): MinuteBar, Fetch today's 1-min bars from Schwab and run BiasScoreFilter., BiasScoreFilter, Multi-signal directional bias filter for 0-DTE butterfly entries., Scores market direction using 4 signals; returns CALL, PUT, or None., Bars that produce strong bullish score: rising price, above OR high., Bars that produce strong bearish score: falling price, below OR low., OR signal is ±2 — alone it meets the ±2 threshold. (+3 more)

### Community 38 - "performance_chart.py"
Cohesion: 0.17
Nodes (20): compute_stats(), is_drawdown_exit(), ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle() (+12 more)

### Community 39 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 40 - "SchwabClientWrapper"
Cohesion: 0.10
Nodes (14): Execute with exponential backoff retry., Get current spot price for SPX., Get the status of an order., Cancel an existing order., Fetch 1-minute bars for today (and optionally prior days) from Schwab., Fetch daily OHLCV bars for the given symbol., Fetch regular + extended quote fields for equities in batches., Return Schwab's top movers list for an index/exchange bucket. (+6 more)

### Community 41 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 42 - "get_logger"
Cohesion: 0.19
Nodes (12): BoundLogger, get_logger(), Get a structlog logger with optional name., Async database connection pool using asyncpg., Execute SQL migration files in order., Run all SQL migration files in order., run_migrations(), main() (+4 more)

### Community 43 - "test_candidate_feed.py"
Cohesion: 0.14
Nodes (13): FakeArchive, FakeDb, FakeMarket, FakePool, asyncio, date, MonkeyPatch, test_active_feed_fetches_chain_each_cycle_and_context_once_per_minute() (+5 more)

### Community 44 - "AlertmanagerNotifier"
Cohesion: 0.18
Nodes (12): Post one stable, identifier-free alert fingerprint to Alertmanager., send_alertmanager(), AlertmanagerNotifier, Sends centrally deduplicated critical alerts through Alertmanager., asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted() (+4 more)

### Community 45 - "test_schwab_token_keepalive.py"
Cohesion: 0.16
Nodes (13): fixture, lock_events(), parametrize, SCHWAB_TOKEN_PATH overrides the default, process env winning over .env., Record lock acquire/release without touching a real lock file., Wire up the module-level environment the keepalive script reads on import., The refresh and the quote both happen while the gateway's lock is held. Schwab…, A busy lock fails loudly rather than writing alongside the other writer. (+5 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.14
Nodes (11): date, Path, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day., Loads SPY 1-minute bars from Schwab, scaled to SPX price levels. Reuses the…, Fetch SPX daily open from yfinance for SPY→SPX calibration., Fetch VIX daily close from yfinance. (+3 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.17
Nodes (30): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+22 more)

### Community 48 - "session_date"
Cohesion: 0.19
Nodes (9): Calendar date for the US/Eastern trading session., session_date(), date, Record that a trade was executed., Record realized dollar PnL., Overwrite dollar realized_pnl in risk state (SET, not ADD). Used at startup to…, Manually sync the trade count in the risk state table. Used at startup to…, Check risk conditions before entry. Returns (allowed, reason). buying_power is… (+1 more)

### Community 49 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 50 - "DiscordNotifier"
Cohesion: 0.23
Nodes (4): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook.

### Community 51 - "live_performance.py"
Cohesion: 0.15
Nodes (28): chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes(), equity_chart_description() (+20 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "download_schwab_cache.py"
Cohesion: 0.27
Nodes (10): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), date_range(), main() (+2 more)

### Community 55 - "load_config"
Cohesion: 0.09
Nodes (28): load_config(), Path, Load configuration from YAML file and environment variables., main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run… (+20 more)

### Community 56 - "StrategySettings"
Cohesion: 0.12
Nodes (29): StrategySettings, main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date. Replicates the…, ButterflyBuilder, Builds and scores butterfly spreads from an option chain snapshot., ButterflySelector (+21 more)

### Community 57 - "OptionQuote"
Cohesion: 0.14
Nodes (23): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes(), fly_mark_value() (+15 more)

### Community 58 - "test_comparison_stats.py"
Cohesion: 0.46
Nodes (7): _print_comparison_table(), _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 59 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 60 - "Any"
Cohesion: 0.29
Nodes (10): _broker_option_positions(), _explicit_fill_details(), _intent_order_ids(), _json_dict(), _matches_underlying(), _open_trade_positions(), Any, _repair_filled_entry_intent() (+2 more)

### Community 61 - "test_candidate_variants.py"
Cohesion: 0.42
Nodes (9): _candidate(), _config(), MonkeyPatch, _state(), test_absolute_stop_truncates_never_profitable_loss(), test_gap_conviction_threshold_is_wired_into_candidate_evaluator(), test_peak_trailer_retains_winner_that_profitprotector_floors(), test_target_cost_prefers_debit_target_instead_of_best_rr() (+1 more)

### Community 62 - "TradeQueries"
Cohesion: 0.06
Nodes (15): ChainQueries, OrderIntentQueries, Any, date, datetime, Queries for option_chain_snapshots table., Bulk insert option chain snapshot rows using COPY., Queries for trades table. (+7 more)

### Community 63 - "test_gateway_phase7_boundaries.py"
Cohesion: 0.24
Nodes (6): asyncio, Phase 7 boundaries after extracting the Schwab gateway from ButterflyGuy., _source(), test_compose_keeps_xsp_default_off_on_the_standalone_alias_and_others_direct(), test_shadow_failure_is_observed_without_changing_the_direct_result(), test_standalone_packages_remain_pinned_and_consumers_import_them_directly()

### Community 65 - "ButterflyOrderBuilder"
Cohesion: 0.13
Nodes (22): ButterflyOrderBuilder, Any, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check… (+14 more)

### Community 66 - "universes.py"
Cohesion: 0.06
Nodes (56): _as_float(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols(), fetch_sp500_rows() (+48 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.15
Nodes (13): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+5 more)

### Community 69 - "CandidateFeed"
Cohesion: 0.12
Nodes (14): CandidateFeed, _final_regular_session_close(), Lease, LeaseRegistry, _previous_close(), Any, date, datetime (+6 more)

### Community 70 - "Regime"
Cohesion: 0.16
Nodes (11): GapRegimeFilter, Enum, Market regime classifier for 0-DTE butterfly parameter dispatch. Classifies…, Regime, str, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias (+3 more)

### Community 71 - "scanner.py"
Cohesion: 0.17
Nodes (22): _as_float(), _as_int(), EquitySnapshot, filter_movers(), _focus_reasons(), _mid_bid_ask(), _mover_change_pct(), _mover_symbol() (+14 more)

### Community 72 - "data_loader.py"
Cohesion: 0.25
Nodes (4): CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, Shared backtest market-data models., DB-backed data loader for historical SPX + VIX data. Reads from the live…, Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).…

### Community 73 - "TradePoint"
Cohesion: 0.15
Nodes (18): TradePoint, latest_fill_model_cohort(), previous_mon_fri(), Keep performance math within the most recent paper fill model., Return Mon–Fri for the week ending on the Friday before reference., asyncio, date, Tests for weekend review date windows and orchestration. (+10 more)

### Community 74 - "notify.py"
Cohesion: 0.33
Nodes (4): Lightweight Telegram and ButterflyGuy Alertmanager helpers. Usage: from…, Send a Telegram message. Returns True on success, False on failure., send(), Keep the Schwab OAuth token alive and alert before refresh token expiry. Schwab…

### Community 75 - "ChainDay"
Cohesion: 0.14
Nodes (22): dict, chain_cache_path(), ChainDay, load_chain_day(), nearest_snapshot(), date, datetime, Path (+14 more)

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.09
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 77 - "run_morning_scan.py"
Cohesion: 0.09
Nodes (31): is_premarket_window(), True during weekday premarket (default 4:00–9:30 AM ET)., load_equity_scan_config(), Path, Load equity scan settings from YAML., attach_news_impacts(), Attach catalyst metadata without changing quote normalization., load_liquid_meta() (+23 more)

### Community 78 - "Window A — Token re-authorization (mandatory)"
Cohesion: 0.10
Nodes (20): A0 — Snapshot (read-only), A1 — Disable the keepalive, A2 — Stop the three trading services, A3 — Re-authorize, A4 — Verify the new document, A5 — Start the three services, A6 — Restore the keepalive, A7 — Verify (+12 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.17
Nodes (16): parse_trade_transactions(), Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options)., test_build_equity_trade_chart_png_returns_png_bytes(), test_chartable_equity_trades_skips_options() (+8 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.21
Nodes (22): build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_performance_caption(), format_review_header(), format_trade_recap() (+14 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "install_shutdown_handler"
Cohesion: 0.40
Nodes (5): install_shutdown_handler(), Task, Cancel the supervised loops on SIGTERM so main()'s cleanup block runs. The app…, SIGTERM must unwind the TaskGroup without reporting a shutdown as an error. The…, test_sigterm_cancels_supervised_loops_and_task_group_exits_cleanly()

### Community 87 - "run_entry_analysis.py"
Cohesion: 0.14
Nodes (28): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+20 more)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.21
Nodes (21): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+13 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 92 - "evaluator.py"
Cohesion: 0.08
Nodes (36): assert_candidate_safety(), candidate_performance_stats(), CandidateAuditContext, CandidateDecisionQueries, CandidateEvaluator, CandidatePerformanceStats, config_sha256(), Path (+28 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "Codex Project State"
Cohesion: 0.08
Nodes (24): C3 default-off deployment and gateway hardening (2026-08-10), Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z), Codex Project State, Current Phase, Current Slice, Current status — 2026-08-10 (+16 more)

### Community 96 - "Re-authorization checklist — Saturday 2026-08-15"
Cohesion: 0.13
Nodes (14): Automated warnings before the cadence reset, Before you start, Expected result: no containers restarted, First, watch the reload do its job, Re-authorization checklist — Saturday 2026-08-15, Step 0 — already done, nothing to do, Step 1 — mint the token on zeus, in a real terminal, Step 2 — stage on Helios and verify byte-identical (+6 more)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "run_classifier_sweep.py"
Cohesion: 0.16
Nodes (20): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday… (+12 more)

### Community 101 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.12
Nodes (15): Fixed defaults, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate, Phase 6 — Standalone production cutover (+7 more)

### Community 102 - "record_equity_market_data.py"
Cohesion: 0.08
Nodes (38): JsonlStreamRecorder, date, datetime, Event, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session. (+30 more)

### Community 105 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.14
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 106 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.17
Nodes (12): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding (+4 more)

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 109 - "test_run_live.py"
Cohesion: 0.16
Nodes (28): readiness_snapshot(), _never_awaited(), asyncio, parametrize, A reload failure must not take the trading loop down with it. The old client…, _synthetic_butterfly_snapshot(), _synthetic_position(), test_entry_loop_alerts_after_monitor_safety_error() (+20 more)

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
Cohesion: 0.16
Nodes (18): DailyReportCardSettings, load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds, archive_report(), date (+10 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 121 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 122 - "report_broker_order_statuses.py"
Cohesion: 0.30
Nodes (12): _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses() (+4 more)

### Community 123 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 124 - "test_run_migrations.py"
Cohesion: 0.36
Nodes (5): fake_db(), FakeConnection, asyncio, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 125 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 126 - "HttpMarketDataProvider"
Cohesion: 0.18
Nodes (6): HttpMarketDataProvider, AsyncClient, LeaseKind, Response, Fail-closed client for the internal candidate feed., _response_error()

### Community 128 - "Window H — verification held; the deadline reminder is mistimed (2026-08-08)"
Cohesion: 0.20
Nodes (10): Corrections to the Window H brief, Deliverables, Finding — the weekly reminder fires after the deadline it protects, Still open after Window H, Task 2 — the Monday check is deferred a fourth time, Tasks 3–6 — all green, verified host-against-container, The deadline in local time — stated because the brief did not, The deadline, re-derived from the document (+2 more)

### Community 129 - "Reducing the weekly re-authorization cost — a scoping question"
Cohesion: 0.15
Nodes (12): Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Production marker-change proof (2026-08-10), Recommendation, Reducing the weekly re-authorization cost — a scoping question, Stale-writer follow-up (2026-08-10), Status, The alternative worth costing first (+4 more)

### Community 130 - "Schwab Gateway Credential Proof"
Cohesion: 0.06
Nodes (34): Accepted runtime-baseline proof adapter, Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05 (+26 more)

### Community 131 - "test_gateway_compose.py"
Cohesion: 0.20
Nodes (7): Deployment boundaries retained after the standalone gateway extraction., All four trading services bind the token document from one required variable., Directory binds follow atomic token replacement to its new inode., A YAML token_path would override the deployment's shared token path., test_default_compose_binds_the_token_directory_never_the_document(), test_default_compose_token_binds_require_the_shared_token_directory(), test_live_configs_leave_token_path_to_the_environment()

### Community 132 - "trade_service.py"
Cohesion: 0.09
Nodes (23): capped_entry_limit(), Return a cent-valid debit limit that never exceeds the configured maximum., iter_chain_options(), date, Shared utilities for parsing Schwab option chain responses., Yield (strike, option_type, opt_dict) for each option matching the expiration.…, _age_seconds(), Any (+15 more)

### Community 133 - "C3 — wiring shadow reads into `run_live.py`"
Cohesion: 0.20
Nodes (9): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, The wiring point, Two corrections to the received design points (+1 more)

### Community 134 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "generate_live_performance.py"
Cohesion: 0.23
Nodes (14): render_placeholder_html(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate(), main(), parse_args(), Connection (+6 more)

### Community 137 - "DirectSchwabMarketDataProvider"
Cohesion: 0.10
Nodes (13): DirectSchwabMarketDataProvider, EquityQuoteProvider, MarketMoversProvider, OptionChainProvider, PriceHistoryProvider, Any, date, Protocol (+5 more)

### Community 141 - "ButterflyCandidate"
Cohesion: 0.08
Nodes (40): _candidate_mark(), entry_fill_within_limit(), Shared entry-price limit policy for production and candidate runtimes., Return whether an entry fill respects its hard debit ceiling., now_utc(), ButterflyCandidate, A butterfly spread candidate identified by the scanner., AmbiguousOrderError (+32 more)

### Community 142 - "test_candidate_snapshot.py"
Cohesion: 0.33
Nodes (11): asyncio, datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry(), test_long_poll_never_replays_same_sequence(), test_new_lease_wakes_idle_feed() (+3 more)

### Community 144 - "resolve_db_dsn"
Cohesion: 0.18
Nodes (13): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., Resolve the DB connection string for local backtests. Backtests follow the…, resolve_db_dsn(), asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot() (+5 more)

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
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 150 - "CandidatePaperExecutor"
Cohesion: 0.19
Nodes (11): CandidatePaperExecutor, Any, Mark-price fills only; this object intentionally has no broker methods., candidate(), FakeProvider, market(), asyncio, test_candidate_entry_blocks_fill_above_configured_width_maximum() (+3 more)

### Community 151 - "Window C — the two token writers resolved (2026-08-08)"
Cohesion: 0.25
Nodes (8): C1 — the operator chose the shared lock, C3 plan produced, and a stale design point corrected, Durability decided, monitoring still open, Housekeeping, Multi-consumer shape — confirmed sound, with two wrinkles, Proven on the host by the production path, at zero extra token writes, Still open, Window C — the two token writers resolved (2026-08-08)

### Community 152 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 153 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.25
Nodes (8): Corrections to the Window G brief, End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, The fix, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)

### Community 154 - "feed.py"
Cohesion: 0.30
Nodes (18): Application, Request, _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs() (+10 more)

### Community 156 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 157 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 158 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.20
Nodes (10): candidate_fill_parity_failures(), Count mark_v1 rows whose fills disagree with their recorded evidence., _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_fill_parity_counts_entry_exit_mismatch_or_missing_evidence(), test_min_gap_filter_logs_no_trade_before_candidate_selection() (+2 more)

### Community 159 - "Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)"
Cohesion: 0.33
Nodes (6): Correction to Window H part 1, Item 1 — the warnings now fire before the deadline (deployed), Item 3 built — the token reload (2026-08-09, NOT deployed), Item 3 — the deciding question is answered: the swap is safe, Window H correction — the restart arithmetic was wrong, and the gateway never needed restarting, Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)

### Community 160 - "Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)"
Cohesion: 0.33
Nodes (6): Fixed by binding the directory, and by a second defect that fix exposed, Still open, The finding — the always-on gateway had orphaned all three trading containers, Verified, by inode and digest and by an actual atomic replace, Window E addendum — the candidate fleet's orphaned token, fixed (2026-08-08), Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)

### Community 162 - "ButterflyGuy data sources and data types"
Cohesion: 0.22
Nodes (8): 10. Repository evidence map, 4. Shared database tables visible to the same DB account, 6. Canonical and derived analytical data types, 8. Reports, archives, charts, and outbound destinations, 9. Practical limitations and safety notes, At a glance, ButterflyGuy data sources and data types, Synthetic option-chain data

### Community 163 - "Equity candles and order-book recording"
Cohesion: 0.33
Nodes (5): Backfill candles, Equity candles and order-book recording, Historical limitation, Operational caution, Record a future BMNR session

### Community 164 - "Bounded proof failure codes and a settled restoration error window — 2026-08-06"
Cohesion: 0.40
Nodes (5): Bounded proof failure codes and a settled restoration error window — 2026-08-06, Release, The proof now names its own failure stage, The restoration error gate now counts a settled window, Two smaller decisions

### Community 165 - "Credential proof passed — 2026-08-06"
Cohesion: 0.40
Nodes (5): Credential proof passed — 2026-08-06, Disposition, Restoration, The production token was rotated, as designed, What this does and does not authorize

### Community 166 - "test_run_backtest_db_defaults.py"
Cohesion: 0.20
Nodes (11): candidate_from_trade_row(), Use the first regular-session snapshot for gap direction., select_direction_bar(), _parse_for_asset(), test_backtest_auto_direction_uses_first_regular_session_snapshot(), test_backtest_parses_exit_arm_sweep_overrides(), test_backtest_tracks_explicit_selection_overrides(), test_candidate_from_trade_row_pins_live_trade_fields() (+3 more)

### Community 167 - "Window A Executed — token re-authorized (2026-08-08)"
Cohesion: 0.50
Nodes (4): Correction 1 — A3 as written cannot work on Helios, Correction 2 — `easy_client` silently no-ops the re-authorization, Deviations from expectation, otherwise none, Window A Executed — token re-authorized (2026-08-08)

### Community 168 - "butterfly mark"
Cohesion: 0.20
Nodes (10): BUTTERFLYGUY, connectivity visual association, precision visual association, technology visual association, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background (+2 more)

### Community 169 - "The token reload is DEPLOYED (2026-08-09T21:59:16Z)"
Cohesion: 0.50
Nodes (4): The C1 write proved itself in production, on the new code, The token reload is DEPLOYED (2026-08-09T21:59:16Z), Unchanged by any of this, What this changes about 2026-08-15

### Community 170 - "test_gateway_token_manager.py"
Cohesion: 0.26
Nodes (26): AtomicTokenManager, increment_callback(), manager(), _process_refresh(), Exception, MonkeyPatch, parametrize, Path (+18 more)

### Community 171 - "test_auth_init_honours_schwab_token_path"
Cohesion: 0.50
Nodes (3): parametrize, SCHWAB_TOKEN_PATH picks the write target, process env winning over .env., test_auth_init_honours_schwab_token_path()

### Community 172 - "Preflight stops on the host-executed release — 2026-08-06"
Cohesion: 0.67
Nodes (3): Credential exposure during the window, Preflight stops on the host-executed release — 2026-08-06, Release

### Community 173 - "Host-executed proof step"
Cohesion: 0.67
Nodes (3): Host-executed proof step, Release, Workflow consequence the next window must plan for

### Community 175 - "Live Runbook"
Cohesion: 0.25
Nodes (7): During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery, XSP Canary

### Community 179 - "SessionClose"
Cohesion: 0.10
Nodes (12): Persist once and return the canonical evidence for this session., SnapshotArchive, Any, RuntimeError, Auditable final regular-session SPX close supplied by the shared feed., No verified final regular-session close is available from the shared feed., SessionClose, SessionCloseUnavailableError (+4 more)

### Community 181 - "DatabasePool"
Cohesion: 0.12
Nodes (4): Pool, DatabasePool, Manages an asyncpg connection pool for TimescaleDB., Create the connection pool.

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (9): High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy (+1 more)

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 185 - "7. Operational and observability data"
Cohesion: 0.50
Nodes (4): 7.1 Prometheus metrics, 7.2 Health and readiness endpoints, 7.3 Structured application logs, 7. Operational and observability data

### Community 187 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 188 - "test_collector.py"
Cohesion: 0.24
Nodes (10): asyncio, Integration tests for the option chain collector (requires live Schwab token)., A local JSON cache failure should not fail a DB-backed snapshot., A corrupt optional chain cache should not fail a DB-backed snapshot., Collector should parse chain response into rows., Parsed rows should have the expected fields., test_collect_snapshot_parses_chain(), test_collect_snapshot_row_fields() (+2 more)

### Community 190 - "RegimeFilter"
Cohesion: 0.27
Nodes (6): datetime, Intraday VIX regime filter — skips entry when volatility is too elevated., Filter entries based on intraday VIX level at the time of entry., Most recent VIX bar close at or before entry_ts. None if no bars., True = safe to trade. False = skip (VIX too high). Returns True if no VIX bars…, RegimeFilter

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 199 - "Offline safety-drill record — 2026-07-13"
Cohesion: 0.29
Nodes (6): Drill findings fixed, Follow-up — 2026-07-14, Offline safety-drill record — 2026-07-13, Remaining do-now work, Result, Verification

### Community 200 - "Exact-SHA Deployment Proof - 2026-07-15"
Cohesion: 0.33
Nodes (5): Deployment and verification, Exact-SHA Deployment Proof - 2026-07-15, Follow-up rollback and restore drill, Preconditions and validation, Scope

### Community 201 - "XSP Manual-Flatten Evidence - 2026-07-16"
Cohesion: 0.33
Nodes (5): Fail-closed proof, Post-action reconciliation and paper restore, Redacted evidence, Result, XSP Manual-Flatten Evidence - 2026-07-16

### Community 202 - "Critical External-Alert Delivery Proof - 2026-07-15"
Cohesion: 0.40
Nodes (4): Critical External-Alert Delivery Proof - 2026-07-15, Implementation reviewed, Scope, Supervised delivery and deduplication result

### Community 203 - "XSP Flat-Runtime Restart Proof - 2026-07-14"
Cohesion: 0.40
Nodes (4): Preconditions, Restart and verification, Scope, XSP Flat-Runtime Restart Proof - 2026-07-14

### Community 205 - "collector.py"
Cohesion: 0.12
Nodes (15): OptionChainCollector, Any, date, datetime, Option chain collector — fetches and stores SPX chain snapshots., Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Collects option chain snapshots at regular intervals., Parse Schwab callExpDateMap/putExpDateMap into flat rows. (+7 more)

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **486 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `Objective`, `Current status — 2026-08-10` (+481 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `core/config.py`, `test_order_manager.py`, `trade_service.py`, `test_candidate_provider.py`, `schemas.py`, `position_service.py`, `test_candidate_snapshot.py`, `run_backtest_db.py`, `CandidatePaperExecutor`, `feed.py`, `MarketSnapshot`, `load_date_data`, `ProfitStateMachine`, `SyntheticChainGenerator`, `report_exit_mark_parity.py`, `SessionClose`, `StrategySettings`, `DbDataLoader`, `CandidateFeed`, `data_loader.py`, `ChainDay`, `run_entry_analysis.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `time_utils.py`, `universes.py`, `trade_service.py`, `record_equity_market_data.py`, `run_live.py`, `DirectSchwabMarketDataProvider`, `get_logger`, `SchwabSettings`, `position_service.py`, `logging.py`, `run_morning_scan.py`, `ButterflyCandidate`, `evaluator.py`, `_assert_broker_state_matches_db`, `services/daily_report_card.py`, `report_broker_order_statuses.py`, `Any`, `_build_collector_market_data`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `run_paper_replay.py`, `core/config.py`, `test_order_manager.py`, `trade_service.py`, `run_live.py`, `schemas.py`, `EntrySelectionResult`, `position_service.py`, `run_backtest_db.py`, `CandidatePaperExecutor`, `simulation_engine.py`, `ProfitStateMachine`, `test_run_backtest_db_defaults.py`, `test_candidate_settlement.py`, `StrategySettings`, `OptionQuote`, `test_candidate_variants.py`, `ButterflyOrderBuilder`, `evaluator.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 45 inferred relationships involving `ButterflyCandidate` (e.g. with `SimulationEngine` and `_candidate_mark()`) actually correct?**
  _`ButterflyCandidate` has 45 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `SchwabClientWrapper` (e.g. with `DirectSchwabMarketDataProvider` and `SchwabSettings`) actually correct?**
  _`SchwabClientWrapper` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 45 inferred relationships involving `OptionQuote` (e.g. with `load_chain_day()` and `nearest_snapshot()`) actually correct?**
  _`OptionQuote` has 45 INFERRED edges - model-reasoned connections that need verification._
