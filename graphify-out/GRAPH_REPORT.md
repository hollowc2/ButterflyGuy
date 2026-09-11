# Graph Report - Butterflyguy  (2026-09-11)

## Corpus Check
- 279 files · ~327,736 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4035 nodes · 9703 edges · 242 communities (192 shown, 35 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 1023 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a7057a1c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- replay_day
- chain_cache.py
- is_market_open
- test_order_manager.py
- test_gateway_shadow_reads.py
- run_morning_scan.py
- trade_chart.py
- ShadowComparingMarketDataProvider
- .monitor_loop
- discover_options_strategy.py
- run_live.py
- test_run_live.py
- ReadOnlySchwabMarketDataClient
- CandidateEvaluator
- CandidateRegistry
- forex_calendar.py
- test_candidate_evaluator_accounting.py
- MinuteBar
- CsvDataLoader
- ShadowDiscrepancyRecorder
- DirectProvider
- test_equity_scan.py
- Enum
- SnapshotIdentity
- reports/daily_report_card.py
- report.py
- date
- SchwabSettings
- schwab_gateway_session_soak.py
- test_chain_parser_parity.py
- schwab_gateway_v046_readiness_soak.py
- report_exit_mark_parity.py
- ProfitStateMachine
- test_risk_engine.py
- SchwabDataLoader
- news.py
- gateway_client/__init__.py
- run_classifier_sweep.py
- volume.py
- Current Schwab Integration
- _assert_broker_state_matches_db
- report_broker_order_statuses.py
- Re-authorization checklist — Saturday 2026-08-22
- test_candidate_feed.py
- gateway_order_book.py
- test_schwab_gateway_session_soak.py
- PositionService
- equity_trade_chart.py
- ButterflyCandidate
- DiscordNotifier
- OrderManager
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- DirectSchwabMarketDataProvider
- load_config
- time_utils.py
- run_entry_analysis.py
- test_comparison_stats.py
- Schwab Gateway Migration Plan
- daily_report_card_config.py
- run_candidate_feed.py
- test_candidate_provider.py
- Helios PAPER gateway cutover — 2026-08-25
- .reload_if_reauthorized
- test_order_preview.py
- universes.py
- NamedTuple
- DbDataLoader
- SyntheticChainGenerator
- TradeService
- scanner.py
- SchwabClientWrapper
- core/config.py
- launch_schwab_gateway_session_soak_20260904.sh
- .paper_entry_commission
- Branch Review and Integration Plan
- test_candidate_settlement.py
- Window A — Token re-authorization (mandatory)
- 1. Charles Schwab API
- test_schwab_token_keepalive.py
- test_daily_report_card.py
- weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- load_report_gateway_settings
- 9) Capture equity candles and Level II for trade review
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- send_test_chart.py
- gateway-paper-cutover-handoff-prompt.md
- 2026-07-14 — data audit and research design
- Codex Project State
- Re-authorization checklist — Saturday 2026-08-15
- Capability recorder design
- test_black_scholes.py
- Schwab Single-Token Manager
- run_backtest_db.py
- Standalone SchwabGateway Extraction Plan
- test_position_monitoring.py
- test_candidate_schwab_market_data.py
- TradePoint
- Option A deployment runbook — Helios, containerized
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- generate_live_performance.py
- Schwab Gateway Foundation: Local Run
- black_scholes.py
- refresh_equity_universes.py
- health_monitor.py
- AGENTS.md
- BaseModel
- 2. Other external and public sources
- 5. Local files and backtest inputs
- services/daily_report_card.py
- Protocol
- RuntimeError
- Butterfly Guy
- test_live_performance_report.py
- report_trade_ladders.py
- test_gateway_option_chain_ttl_recommendation.py
- Window D — the gateway made reachable, started, and watched (2026-08-08)
- test_run_migrations.py
- Schwab Gateway Foundation Smoke Test
- Path
- OrderIntentQueries
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- Reducing the weekly re-authorization cost — a scoping question
- Schwab Gateway Credential Proof
- test_gateway_compose.py
- SchwabGateway order-book release full-session acceptance — 2026-09-01
- C3 — wiring shadow reads into `run_live.py`
- Schwab gateway deployment options
- Strategy Settings
- record_equity_market_data.py
- GatewayAuthoritativeMarketDataProvider
- synthetic_chain.py
- feed.py
- providers.py
- _redacted_order_audit
- AtomicSnapshotStore
- refresh_builtin_universes
- ButterflyOrderBuilder
- Width Selection
- SchwabGateway option-chain latency investigation (2026-09-04)
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Schwab Gateway Multi-Consumer Foundation
- test_gateway_phase7_boundaries.py
- Window C — the two token writers resolved (2026-08-08)
- backfill_equity_candles.py
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- CandidateFeed
- launch_schwab_gateway_session_soak_20260901.sh
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- ValueError
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)
- SchwabGateway order books
- ButterflyGuy data sources and data types
- Equity candles and order-book recording
- Bounded proof failure codes and a settled restoration error window — 2026-08-06
- Credential proof passed — 2026-08-06
- TradeQueries
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
- _HtmlTableParser
- .collect_snapshot
- MarketSnapshot
- test_get_spot_price_returns_before_a_slow_gateway_responds
- run_equity_universe_refresh_cron.sh
- Layered Risk Management
- Geometric butterfly icon
- test_discrepancy_metric_labels_cover_every_declared_code
- 7. Operational and observability data
- validate_chain
- ButterflyGuy data sources — representative samples
- launch_schwab_gateway_readiness_soak_20260909.sh
- test_equity_universes.py
- preopen_endpoint_violations
- 3) Start the SPX stack in Docker
- test_request_classifies_gateway_040_error_codes
- .generate_chain
- _MetricsHandler
- install_shutdown_handler
- report_selection_parity.py
- test_get_option_chain_returns_before_a_slow_gateway_responds
- ._ema
- Offline safety-drill record — 2026-07-13
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- Critical External-Alert Delivery Proof - 2026-07-15
- XSP Flat-Runtime Restart Proof - 2026-07-14
- test_performance_dashboard.py
- .handler
- auth_init.py
- ignored_freshness_difference_paths
- set_readiness
- schwab-gateway-phase-7-execution-prompt.md
- test_run_scan_skips_market_holiday_before_schwab
- test_close_trade_only_closes_an_open_trade_once
- .write_until_stopped
- butterfly_guy/__init__.py
- equity_scan/__init__.py
- reports/__init__.py
- run_live_performance_cron.sh
- run_morning_scan_cron.sh
- Compare Real vs Synthetic Chains
- _reset_readiness_after_provider_test
- filter_symbols_by_price
- test_order_builder.py
- compute_tent_boundaries
- bs_vega
- determine_direction
- .__init__
- gateway_market_data_readiness_loop
- butterfly-guy

## God Nodes (most connected - your core abstractions)
1. `ButterflyCandidate` - 91 edges
2. `SchwabClientWrapper` - 85 edges
3. `OptionQuote` - 83 edges
4. `AppConfig` - 64 edges
5. `MarketSnapshot` - 58 edges
6. `MinuteBar` - 56 edges
7. `DatabasePool` - 53 edges
8. `main()` - 52 edges
9. `PositionService` - 52 edges
10. `load_config()` - 49 edges

## Surprising Connections (you probably didn't know these)
- `test_session_close_rejects_unauditable_timestamps()` --uses--> `SessionClose`  [INFERRED]
  tests/test_candidate_snapshot.py → src/butterfly_guy/candidate_fleet/models.py
- `test_config_rejects_unknown_keys()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_database_dsn()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_profit_management_strategy_defaults_to_peak_value_trailer()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_equity_scan_settings_accepts_news_config()` --uses--> `EquityScanSettings`  [INFERRED]
  tests/test_equity_scan_news.py → src/butterfly_guy/equity_scan/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]

## Communities (242 total, 35 thin omitted)

### Community 0 - "replay_day"
Cohesion: 0.10
Nodes (30): detect_complete_days(), _elapsed(), _et(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main() (+22 more)

### Community 1 - "chain_cache.py"
Cohesion: 0.23
Nodes (15): chain_cache_path(), load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->… (+7 more)

### Community 2 - "is_market_open"
Cohesion: 0.17
Nodes (21): is_market_open(), minutes_to_close(), Check if the market is currently open., Minutes remaining until market close., et(), datetime, Tests for market time utilities., test_get_0dte_expiration() (+13 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.14
Nodes (60): LiveSpread, parse_broker_fill(), Return a validated net butterfly fill derived only from broker executions., broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi() (+52 more)

### Community 4 - "test_gateway_shadow_reads.py"
Cohesion: 0.12
Nodes (37): ChainMetadataResponseV1, SpotResponseV1, chain_response(), _comparisons(), _discrepancies(), asyncio, Exception, parametrize (+29 more)

### Community 5 - "run_morning_scan.py"
Cohesion: 0.12
Nodes (26): is_premarket_window(), is_trading_day(), now_eastern(), Current time in US/Eastern., True during weekday premarket (default 4:00–9:30 AM ET)., Check if a given date is a trading day (weekday, not a holiday)., load_equity_scan_config(), Path (+18 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.10
Nodes (40): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+32 more)

### Community 7 - "ShadowComparingMarketDataProvider"
Cohesion: 0.13
Nodes (14): _error_code(), _mismatch_code(), _numbers_agree(), Any, date, Exception, Task, Phase 3 shadow comparison for the collector's spot and chain reads. This… (+6 more)

### Community 8 - ".monitor_loop"
Cohesion: 0.11
Nodes (16): broker_cash_settlement_from_transactions(), _chain_spot_price(), Any, date, datetime, RuntimeError, Extract the three butterfly leg quotes from the chain for position valuation., Monitor position every 2s, evaluate state machine, trigger exit if needed. (+8 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.08
Nodes (52): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+44 more)

### Community 10 - "run_live.py"
Cohesion: 0.03
Nodes (105): BoundLogger, Pool, CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, assert_candidate_safety(), config_sha256(), Path, Paper-only candidate evaluator built without broker execution dependencies., entry_fill_within_limit() (+97 more)

### Community 11 - "test_run_live.py"
Cohesion: 0.09
Nodes (40): broker_reconciler_loop(), _build_collector_market_data(), _close_runtime_resources(), gateway_runtime_phase_delay(), GatewayClientSettings, GatewayMarketDataClient, Return a bounded startup delay that spreads gateway PAPER runtimes evenly.…, Select one authoritative read path without changing broker boundaries. (+32 more)

### Community 12 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.17
Nodes (7): Any, date, Prove the replacement credential with one bounded read-only Schwab call., Authenticate a Schwab client without resolving or retaining an account., Build one client with an isolated in-memory refresh-token callback., Validate and install a client built from a newly authorized token document., ReadOnlySchwabMarketDataClient

### Community 13 - "CandidateEvaluator"
Cohesion: 0.21
Nodes (8): candidate_performance_stats(), CandidateEvaluator, CandidatePerformanceStats, Summarize one chronological, closed mark_v1 PnL cohort., _restore_trade(), Check if current time is within the given window (HH:MM strings)., time_in_window(), test_candidate_performance_stats_reports_outlier_dependence()

### Community 14 - "CandidateRegistry"
Cohesion: 0.11
Nodes (40): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+32 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.20
Nodes (10): candidate_fill_parity_failures(), Count mark_v1 rows whose fills disagree with their recorded evidence., _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_fill_parity_counts_entry_exit_mismatch_or_missing_evidence(), test_min_gap_filter_logs_no_trade_before_candidate_selection() (+2 more)

### Community 17 - "MinuteBar"
Cohesion: 0.05
Nodes (55): DayData, MinuteBar, Shared backtest market-data models., Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).…, DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains. (+47 more)

### Community 18 - "CsvDataLoader"
Cohesion: 0.25
Nodes (8): DataFrame, CsvDataLoader, date, Path, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files…

### Community 19 - "ShadowDiscrepancyRecorder"
Cohesion: 0.22
Nodes (5): GatewayMarketDataClient, A bounded, fixed-shape observation. Carries no payload, path, or exception text., Tally discrepancies over a fixed key space; retains no observed values., ShadowDiscrepancy, ShadowDiscrepancyRecorder

### Community 20 - "DirectProvider"
Cohesion: 0.12
Nodes (7): DirectProvider, FailingDirectProvider, date, The only source of returned values. Records every delegated call., A direct provider whose reads raise, to exercise the direct_unavailable path., test_direct_result_is_unchanged_when_the_gateway_times_out_in_real_time(), test_shadow_stays_disabled_when_no_gateway_client_is_supplied()

### Community 21 - "test_equity_scan.py"
Cohesion: 0.20
Nodes (31): EquityScanSettings, build_snapshots(), parse_equity_quote(), datetime, _quote_age_seconds(), rank_scan_results(), Normalize a Schwab quote payload into an EquitySnapshot., build_symbol_map() (+23 more)

### Community 23 - "SnapshotIdentity"
Cohesion: 0.06
Nodes (26): Persist once and return the canonical evidence for this session., Paper-only SPX candidate fleet fed by a shared market-data service., Any, RuntimeError, Immutable normalized market snapshots shared by candidate evaluators., A long poll completed normally before a newer snapshot was published., Auditable final regular-session SPX close supplied by the shared feed., No verified final regular-session close is available from the shared feed. (+18 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.14
Nodes (35): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders(), detect_problems(), _extract_order_id() (+27 more)

### Community 25 - "report.py"
Cohesion: 0.17
Nodes (28): build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes() (+20 more)

### Community 26 - "date"
Cohesion: 0.14
Nodes (4): date, datetime, Dollar PnL for the rolling 7-day window (closed trades only)., Return the nearest full chain snapshot at or before *at* within…

### Community 27 - "SchwabSettings"
Cohesion: 0.15
Nodes (26): SchwabSettings, _accessors(), factory(), _account_client(), asyncio, Initialize a wrapper against a real token file, returning its read/write funcs., Wire a wrapper whose _build_client hands out `clients` in order., An ordinary hourly refresh rewrites the document but must not rebuild the… (+18 more)

### Community 28 - "schwab_gateway_session_soak.py"
Cohesion: 0.19
Nodes (33): background_context(), _confirm_surfaces(), _filtered_gateway_logs(), _finite(), _health(), main(), _metrics(), parse_args() (+25 more)

### Community 29 - "test_chain_parser_parity.py"
Cohesion: 0.13
Nodes (25): _contract(), _parse_rows(), Any, date, parametrize, Differential tests pinning the three Schwab option-chain parsers against each…, Run the live collector row parser without touching the database or Schwab., call + put contract counts equal the row count the collector writes. (+17 more)

### Community 30 - "schwab_gateway_v046_readiness_soak.py"
Cohesion: 0.14
Nodes (37): Client, Pattern, append_jsonl(), bounded_request(), candidate_observation(), diagnostic_probe(), docker_inspect(), endpoint_snapshot() (+29 more)

### Community 31 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.05
Nodes (75): ProfitManagementStrategy, PeakTrackingSettings, ProfitManagementSettings, ProfitProtectorSettings, QuoteQualitySettings, fly_settlement_value(), PositionState, Butterfly cash-settlement value from the underlying index close. (+67 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SchwabDataLoader"
Cohesion: 0.09
Nodes (22): day_cache_path(), load_day(), _parse_bar(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), date (+14 more)

### Community 35 - "news.py"
Cohesion: 0.16
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 37 - "run_classifier_sweep.py"
Cohesion: 0.09
Nodes (28): max_consecutive_losses(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _summarize_combo(), main(), parse_args() (+20 more)

### Community 38 - "volume.py"
Cohesion: 0.16
Nodes (16): _as_int(), avg_daily_volume(), compute_rvol(), _fetch_one(), fetch_prior_day_changes(), _fetch_one(), prior_session_pct_change(), Relative volume helpers using Schwab daily bar history. (+8 more)

### Community 39 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 40 - "_assert_broker_state_matches_db"
Cohesion: 0.16
Nodes (29): order_ids(), walk_orders(), _assert_broker_state_matches_db(), _expired_trade_has_broker_settlement(), _explicit_fill_details(), _intent_order_ids(), _json_dict(), _open_trade_positions() (+21 more)

### Community 41 - "report_broker_order_statuses.py"
Cohesion: 0.28
Nodes (14): _allowed_roots(), _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize() (+6 more)

### Community 42 - "Re-authorization checklist — Saturday 2026-08-22"
Cohesion: 0.18
Nodes (10): Preconditions — verified 2026-08-22T15:45:36Z, Re-authorization checklist — Saturday 2026-08-22, Step 1 — mint on zeus, in a real terminal, Step 2 — stage on Helios, verify byte-identical, Step 3 — move into place under the C1 lock, Step 4 — watch the reloads; restart only on a *confirmed* failure, Step 5 — verify, host against containers, Step 6 — record (+2 more)

### Community 43 - "test_candidate_feed.py"
Cohesion: 0.13
Nodes (13): FakeArchive, FakeDb, FakeMarket, FakePool, asyncio, date, MonkeyPatch, test_active_feed_fetches_chain_each_cycle_and_context_once_per_minute() (+5 more)

### Community 44 - "gateway_order_book.py"
Cohesion: 0.07
Nodes (38): ClientSession, field_validator, _Contract, GatewayOrderBookClient, _normalize_symbols(), _normalize_venue(), OrderBookAuthenticationError, OrderBookAuthorizationError (+30 more)

### Community 45 - "test_schwab_gateway_session_soak.py"
Cohesion: 0.11
Nodes (32): _log_entry(), _session_names(), test_adjudication_final_checkpoint_needs_post_close_probe(), test_adjudication_flaky_gateway_promotes_all_transients_to_gating(), test_adjudication_recovered_next_checkpoint_is_observation_not_gating(), test_adjudication_recovered_queue_wait_timeout_is_observation(), test_adjudication_two_consecutive_checkpoints_is_gating(), test_adjudication_unrecovered_midsession_transient_stays_gating() (+24 more)

### Community 46 - "PositionService"
Cohesion: 0.14
Nodes (33): readiness_snapshot(), A trade record for tracking entry/exit., TradeRecord, BrokerCashSettlement, final_regular_session_close_from_candles(), PositionService, NamedTuple, Return the latest Schwab 1-minute close in the regular session. (+25 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.17
Nodes (30): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+22 more)

### Community 48 - "ButterflyCandidate"
Cohesion: 0.04
Nodes (90): DB-backed data loader for historical SPX + VIX data. Reads from the live…, _candidate_mark(), _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows. (+82 more)

### Community 49 - "DiscordNotifier"
Cohesion: 0.06
Nodes (23): Lightweight Telegram and ButterflyGuy Alertmanager helpers. Usage: from…, Send a Telegram message. Returns True on success, False on failure., Post one stable, identifier-free alert fingerprint to Alertmanager., send(), send_alertmanager(), AlertmanagerNotifier, DiscordNotifier, date (+15 more)

### Community 50 - "OrderManager"
Cohesion: 0.15
Nodes (18): get_0dte_expiration(), now_utc(), Get today's date as the 0-DTE expiration (SPX has daily expirations)., _assert_entry_fill_within_limit(), BrokerFill, _fill_result(), order_statuses(), OrderManager (+10 more)

### Community 51 - "live_performance.py"
Cohesion: 0.13
Nodes (33): max_drawdown(), chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes() (+25 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "DirectSchwabMarketDataProvider"
Cohesion: 0.19
Nodes (4): DirectSchwabMarketDataProvider, date, Exercise each required read surface that has not succeeded yet., Delegate to the current client without owning its lifecycle or changing data.

### Community 55 - "load_config"
Cohesion: 0.12
Nodes (22): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+14 more)

### Community 56 - "time_utils.py"
Cohesion: 0.21
Nodes (16): _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), _last_weekday(), market_close_time(), minutes_since_open(), now_pacific(), _nth_weekday() (+8 more)

### Community 57 - "run_entry_analysis.py"
Cohesion: 0.16
Nodes (23): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+15 more)

### Community 58 - "test_comparison_stats.py"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 59 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 60 - "daily_report_card_config.py"
Cohesion: 0.33
Nodes (5): load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds

### Community 61 - "run_candidate_feed.py"
Cohesion: 0.19
Nodes (7): SnapshotArchive, Schwab market-data client deliberately lacking every account/order operation., DatabaseSettings, main(), Run the demand-aware shared SPX candidate market-data feed., Pick up a re-authorized token while retaining a working client on failure., token_reload_loop()

### Community 62 - "test_candidate_provider.py"
Cohesion: 0.25
Nodes (12): make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close(), test_http_and_schwab_provider_contracts_normalize_equally(), handler() (+4 more)

### Community 63 - "Helios PAPER gateway cutover — 2026-08-25"
Cohesion: 0.29
Nodes (6): After-hours readiness condition, Helios PAPER gateway cutover — 2026-08-25, Immutable releases, Retained rollback images, Scope, Validation evidence

### Community 64 - ".reload_if_reauthorized"
Cohesion: 0.25
Nodes (3): Authenticate and resolve account hash., Rebuild the client if the token document has been re-authorized. schwab-py…, Close the client session.

### Community 65 - "test_order_preview.py"
Cohesion: 0.27
Nodes (10): make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate., Order spec must have all fields Schwab requires., Schwab expects price as a string., test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields() (+2 more)

### Community 66 - "universes.py"
Cohesion: 0.17
Nodes (18): fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nyse_listed_symbols(), _fetch_url_text(), _is_common_equity_symbol(), _is_symbol_directory_footer(), parse_nasdaq_listed_text(), parse_nyse_listed_text() (+10 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.14
Nodes (13): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+5 more)

### Community 69 - "SyntheticChainGenerator"
Cohesion: 0.23
Nodes (14): Generates a synthetic SPX option chain from spot + VIX., SyntheticChainGenerator, make_snapshot_time(), datetime, Tests for the synthetic chain generator., Create a snapshot time N minutes before 4pm ET., Volatility skew: OTM puts should have higher IV than equidistant OTM calls., Option price should decrease as expiration approaches. (+6 more)

### Community 70 - "TradeService"
Cohesion: 0.10
Nodes (20): capped_entry_limit(), Return a cent-valid debit limit that never exceeds the configured maximum., AmbiguousOrderError, _broker_time(), BrokerFillError, datetime, RuntimeError, Broker reported FILLED without complete, consistent execution evidence. (+12 more)

### Community 71 - "scanner.py"
Cohesion: 0.15
Nodes (25): _as_float(), _as_int(), attach_news_impacts(), EquitySnapshot, filter_movers(), _filter(), _focus_reasons(), _mid_bid_ask() (+17 more)

### Community 72 - "SchwabClientWrapper"
Cohesion: 0.07
Nodes (23): _creation_timestamp(), Any, date, Read the document's re-authorization marker. `creation_timestamp` changes only…, Execute with exponential backoff retry., Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order once and return the order ID. Order placement is not retried… (+15 more)

### Community 73 - "core/config.py"
Cohesion: 0.06
Nodes (69): BaseSettings, AppConfig, CollectorSettings, ConfigModel, EntrySettings, ExecutionSettings, MonitoringSettings, BaseModel (+61 more)

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.09
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 77 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 78 - "Window A — Token re-authorization (mandatory)"
Cohesion: 0.10
Nodes (20): A0 — Snapshot (read-only), A1 — Disable the keepalive, A2 — Stop the three trading services, A3 — Re-authorize, A4 — Verify the new document, A5 — Start the three services, A6 — Restore the keepalive, A7 — Verify (+12 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 80 - "test_schwab_token_keepalive.py"
Cohesion: 0.11
Nodes (15): lock_events(), fixture, parametrize, SCHWAB_TOKEN_PATH overrides the default, process env winning over .env., Record lock acquire/release without touching a real lock file., Wire up the module-level environment the keepalive script reads on import., The refresh and the quote both happen while the gateway's lock is held. Schwab…, A busy lock fails loudly rather than writing alongside the other writer. (+7 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.16
Nodes (17): parse_trade_transactions(), Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options)., test_build_equity_trade_chart_png_returns_png_bytes(), test_chartable_equity_trades_skips_options() (+9 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.11
Nodes (38): build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_review_header(), format_trade_recap(), latest_fill_model_cohort() (+30 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "load_report_gateway_settings"
Cohesion: 0.32
Nodes (6): test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings(), GatewayClientSettings, Path, Load the host cron's market-data settings without exposing key material.

### Community 87 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.25
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (11): _dashboard(), _expressions(), _panels(), visit(), test_experimental_candidate_fleet_is_absent_from_dashboards(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_uses_selected_trade_monitoring_as_candidate_spot_fallback() (+3 more)

### Community 91 - "send_test_chart.py"
Cohesion: 0.31
Nodes (8): trade_pnl_dollars(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles()

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

### Community 98 - "test_black_scholes.py"
Cohesion: 0.13
Nodes (16): bs_delta(), Delta — rate of change of price wrt spot., Tests for Black-Scholes pricing and Greeks., ATM call price should be approximately S * sigma * sqrt(T/2pi)., Deep ITM call should be approximately S - K * exp(-rT)., Deep ITM put should be approximately K - S., Expired call should equal intrinsic value., Put-call delta parity: call_delta - put_delta = 1. (+8 more)

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "run_backtest_db.py"
Cohesion: 0.05
Nodes (100): dict, ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log…, _asset_drawdowns(), backtest_entry_price(), candidate_from_trade_row(), day_with_monitoring_bars(), _dd_schedule_label() (+92 more)

### Community 101 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.10
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 102 - "test_position_monitoring.py"
Cohesion: 0.23
Nodes (13): _candidate(), _gateway_contract(), asyncio, parametrize, _quotes(), Regression coverage for incomplete held-position market data., A quiet 778 quote is usable when the gateway explicitly says it is fresh., Replay valid -> incomplete threshold -> valid for every held leg. (+5 more)

### Community 103 - "test_candidate_schwab_market_data.py"
Cohesion: 0.35
Nodes (14): asyncio, MonkeyPatch, _reload_client(), _reload_harness(), _settings(), test_close_releases_live_and_retired_clients(), test_failed_reload_keeps_the_working_client_and_marker(), test_missing_startup_marker_is_adopted_without_rebuilding() (+6 more)

### Community 104 - "TradePoint"
Cohesion: 0.17
Nodes (21): compute_stats(), ReportStats, TradePoint, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle() (+13 more)

### Community 105 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.14
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 106 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.17
Nodes (12): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding (+4 more)

### Community 107 - "generate_live_performance.py"
Cohesion: 0.20
Nodes (16): no_trade_reason(), render_placeholder_html(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate(), main(), parse_args() (+8 more)

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 109 - "black_scholes.py"
Cohesion: 0.26
Nodes (12): bs_call_price(), bs_put_price(), bs_theta(), _d1(), _d2(), Black-Scholes option pricing and Greeks., Black-Scholes European call price. Args: S: Spot price K: Strike price T: Time…, Black-Scholes European put price. (+4 more)

### Community 110 - "refresh_equity_universes.py"
Cohesion: 0.23
Nodes (11): build_liquid_meta(), filter_symbols_by_avg_volume(), Keep symbols whose 20-day average daily volume meets the minimum., main(), Path, Refresh equity universe files (sp500, nq100, liquid)., Build liquid.txt from exchange seeds validated via Schwab quotes and volume., refresh_liquid_universe() (+3 more)

### Community 111 - "health_monitor.py"
Cohesion: 0.16
Nodes (16): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), Derive a human-readable service name from a health URL. Prefers the ``service``…, Post a message to Discord webhook., Run one full check cycle across all URLs. Returns list of results. (+8 more)

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
Cohesion: 0.21
Nodes (13): PriceHistoryProvider, archive_report(), date, Path, chartable_equity_trades(), format_equity_trade_chart_caption(), date, datetime (+5 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "test_live_performance_report.py"
Cohesion: 0.18
Nodes (13): date, Tests for live performance report generation., Per-run data must stay in the non-executable JSON block. The published page's…, test_chart_payload_includes_drawdown_fields(), test_compute_stats(), test_is_drawdown_exit(), test_performance_report_shows_entire_history_and_fill_model_cohorts(), test_regenerated_data_stays_out_of_executable_script() (+5 more)

### Community 121 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 122 - "test_gateway_option_chain_ttl_recommendation.py"
Cohesion: 0.29
Nodes (8): test_histogram_percentile_none_when_empty(), test_histogram_percentile_picks_first_bucket_meeting_target(), test_parse_histograms_empty_when_operation_missing(), test_parse_histograms_filters_by_operation(), Histogram, main(), parse_histograms(), Recommend a real SCHWAB_GATEWAY_OPTION_CHAIN_CACHE_TTL_SECONDS from live…

### Community 123 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 124 - "test_run_migrations.py"
Cohesion: 0.31
Nodes (5): fake_db(), FakeConnection, asyncio, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 125 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 126 - "Path"
Cohesion: 0.27
Nodes (11): _atomic_write_text(), load_universe(), load_universes(), Path, Durably replace a text file only after its complete contents are written., Load tickers for a named universe., Load all requested universes., _read_ticker_file() (+3 more)

### Community 127 - "OrderIntentQueries"
Cohesion: 0.13
Nodes (5): OrderIntentQueries, Any, Bulk insert option chain snapshot rows using COPY., Queries for durable broker order intents., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict.

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

### Community 132 - "SchwabGateway order-book release full-session acceptance — 2026-09-01"
Cohesion: 0.20
Nodes (9): Credential lineage, EquityScanner coexistence boundary, Post-close decision, Prepared read-only tools, SchwabGateway order-book release full-session acceptance — 2026-09-01, Scope and freeze boundary, Start the full-session harness (unattended), Tuesday preflight — final gate at 06:20-06:29 PDT (+1 more)

### Community 133 - "C3 — wiring shadow reads into `run_live.py`"
Cohesion: 0.20
Nodes (9): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, The wiring point, Two corrections to the received design points (+1 more)

### Community 134 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "record_equity_market_data.py"
Cohesion: 0.11
Nodes (29): JsonlStreamRecorder, date, datetime, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session., Write a deterministic JSON candle snapshot. (+21 more)

### Community 137 - "GatewayAuthoritativeMarketDataProvider"
Cohesion: 0.24
Nodes (32): SimpleNamespace, GatewayAuthoritativeMarketDataProvider, Adapt the standalone gateway's typed contracts to existing strategy inputs. The…, _bar(), _contract(), _observation(), asyncio, datetime (+24 more)

### Community 138 - "synthetic_chain.py"
Cohesion: 0.20
Nodes (6): IVModel, Implied volatility model with VIX scaling and skew adjustment., Models implied volatility with VIX scaling and volatility skew., Convert VIX index value to 0-DTE ATM IV estimate. VIX is the 30-day implied vol…, Compute skew-adjusted IV for a given strike. OTM puts have elevated IV…, Synthetic option chain generator using Black-Scholes + VIX IV model.

### Community 139 - "feed.py"
Cohesion: 0.30
Nodes (18): Application, Request, _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs() (+10 more)

### Community 140 - "providers.py"
Cohesion: 0.11
Nodes (19): canonicalize_schwab_chain_symbol(), EquityQuoteProvider, _finite_number(), GatewayMarketDataError, MarketMoversProvider, _nonnegative_integer(), _now_eastern(), _optional_number() (+11 more)

### Community 141 - "_redacted_order_audit"
Cohesion: 0.31
Nodes (10): _broker_option_positions(), _matches_underlying(), _order(), test_redacted_audit_excludes_other_underlyings(), test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes(), test_redacted_audit_treats_replaced_as_historical_terminal(), test_broker_option_positions_keep_signed_quantity_for_matching_options(), main() (+2 more)

### Community 142 - "AtomicSnapshotStore"
Cohesion: 0.18
Nodes (13): AtomicSnapshotStore, Condition-guarded pointer swap; readers never observe partial snapshots., asyncio, datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry() (+5 more)

### Community 143 - "refresh_builtin_universes"
Cohesion: 0.22
Nodes (10): fetch_sp500_rows(), fetch_sp500_sectors(), fetch_sp500_tickers(), Refresh sp500.txt, nq100.txt, and sectors.json from public sources., Download S&P 500 constituents with GICS sector metadata., Download the current S&P 500 constituents list., Map S&P 500 tickers to GICS sector names., refresh_builtin_universes() (+2 more)

### Community 144 - "ButterflyOrderBuilder"
Cohesion: 0.29
Nodes (5): ButterflyOrderBuilder, Any, Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order.

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 146 - "SchwabGateway option-chain latency investigation (2026-09-04)"
Cohesion: 0.20
Nodes (9): 2026-09-09 runtime follow-up, Cache TTL is hard-capped at 4s in code, not just config, Chain size correlation, Recommendation, Request path (cache miss), SchwabGateway option-chain latency investigation (2026-09-04), Where the time actually goes: scheduler queueing, not the Schwab call itself, XSP held-leg event-age correction (2026-09-11) (+1 more)

### Community 147 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 148 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 149 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 150 - "test_gateway_phase7_boundaries.py"
Cohesion: 0.20
Nodes (8): asyncio, MonkeyPatch, Phase 7 boundaries after extracting the Schwab gateway from ButterflyGuy., _source(), test_compose_keeps_each_strategy_default_direct_with_staged_gateway_opt_in(), test_default_settings_construct_no_gateway_client(), test_shadow_failure_is_observed_without_changing_the_direct_result(), test_standalone_packages_remain_pinned_and_consumers_import_them_directly()

### Community 151 - "Window C — the two token writers resolved (2026-08-08)"
Cohesion: 0.25
Nodes (8): C1 — the operator chose the shared lock, C3 plan produced, and a stale design point corrected, Durability decided, monitoring still open, Housekeeping, Multi-consumer shape — confirmed sound, with two wrinkles, Proven on the host by the production path, at zero extra token writes, Still open, Window C — the two token writers resolved (2026-08-08)

### Community 152 - "backfill_equity_candles.py"
Cohesion: 0.43
Nodes (7): async_main(), main(), parse_args(), Namespace, Path, Backfill one session of one-minute equity candles from Schwab., run()

### Community 153 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.25
Nodes (8): Corrections to the Window G brief, End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, The fix, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)

### Community 154 - "CandidateFeed"
Cohesion: 0.13
Nodes (14): CandidateFeed, _final_regular_session_close(), Lease, LeaseRegistry, _previous_close(), Any, date, datetime (+6 more)

### Community 155 - "launch_schwab_gateway_session_soak_20260901.sh"
Cohesion: 0.33
Nodes (5): LAUNCH_LOG, NOW_EPOCH, launch_schwab_gateway_session_soak_20260901.sh script, TARGET_EPOCH, TOKEN_PATH

### Community 156 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 157 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 158 - "ValueError"
Cohesion: 0.22
Nodes (5): _aware_utc(), datetime, StaleSnapshotError, model_validator, ValueError

### Community 159 - "Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)"
Cohesion: 0.33
Nodes (6): Correction to Window H part 1, Item 1 — the warnings now fire before the deadline (deployed), Item 3 built — the token reload (2026-08-09, NOT deployed), Item 3 — the deciding question is answered: the swap is safe, Window H correction — the restart arithmetic was wrong, and the gateway never needed restarting, Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)

### Community 160 - "Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)"
Cohesion: 0.33
Nodes (6): Fixed by binding the directory, and by a second defect that fix exposed, Still open, The finding — the always-on gateway had orphaned all three trading containers, Verified, by inode and digest and by an actual atomic replace, Window E addendum — the candidate fleet's orphaned token, fixed (2026-08-08), Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)

### Community 161 - "SchwabGateway order books"
Cohesion: 0.50
Nodes (3): Live WebSocket, Recent snapshots, SchwabGateway order books

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
Cohesion: 0.15
Nodes (33): AtomicTokenManager, increment_callback(), manager(), _process_refresh(), delayed_increment(), Exception, MonkeyPatch, parametrize (+25 more)

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

### Community 177 - "_HtmlTableParser"
Cohesion: 0.18
Nodes (8): HTMLParser, fetch_nq100_tickers(), _HtmlTableParser, parse_nq100_html(), Extract constituents from the table identified by Ticker and Company headers., Download the current Nasdaq-100 constituents from Wikipedia., Collect text cells from HTML tables without depending on tag attributes., test_parse_nq100_html_handles_current_parsoid_cell_attributes_and_nested_tags()

### Community 178 - ".collect_snapshot"
Cohesion: 0.18
Nodes (7): Any, date, datetime, Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Fetch current chain and store snapshot. Returns row count., Main collector loop — runs while market is open., Parse Schwab callExpDateMap/putExpDateMap into flat rows.

### Community 179 - "MarketSnapshot"
Cohesion: 0.15
Nodes (15): CandidateAuditContext, CandidateDecisionQueries, CandidatePaperExecutor, Any, Mark-price fills only; this object intentionally has no broker methods., MarketSnapshot, One atomically published, replayable view of candidate market data., candidate() (+7 more)

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (9): High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy (+1 more)

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 185 - "7. Operational and observability data"
Cohesion: 0.50
Nodes (4): 7.1 Prometheus metrics, 7.2 Health and readiness endpoints, 7.3 Structured application logs, 7. Operational and observability data

### Community 186 - "validate_chain"
Cohesion: 0.50
Nodes (9): _chain(), _contract(), test_cache_canonicalization_does_not_weaken_independent_freshness_gate(), test_chain_records_but_does_not_reject_null_time_value(), test_chain_records_formula_consistency_by_option_type(), test_chain_rejects_invalid_intrinsic_and_time_values(), test_validate_chain_accepts_audible_crossed_market_normalization(), test_validate_chain_rejects_silent_or_invalid_normalization() (+1 more)

### Community 187 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 188 - "launch_schwab_gateway_readiness_soak_20260909.sh"
Cohesion: 0.20
Nodes (10): die(), EVIDENCE_DIR, LAUNCHER, LOG, MONITOR, SESSION_DATE, launch_schwab_gateway_readiness_soak_20260909.sh script, TARGET_EPOCH (+2 more)

### Community 189 - "test_equity_universes.py"
Cohesion: 0.22
Nodes (7): load_sector_map(), Load symbol -> sector mapping (GICS for index names, exchange fallback for…, Tests for equity universe seed parsing and liquidity gates., test_equity_scan_settings_accepts_liquid_universe(), test_extract_quote_price_prefers_extended_price(), test_load_sector_map_uses_liquid_meta_exchange_fallback(), test_write_universe_file_preserves_existing_file_if_replace_fails()

### Community 190 - "preopen_endpoint_violations"
Cohesion: 0.31
Nodes (9): _endpoints(), MonkeyPatch, parametrize, test_preopen_accepts_retried_market_data_unavailable(), test_preopen_allows_documented_after_hours_strategy_readiness(), test_preopen_never_suppresses_other_endpoint_failures(), test_preopen_rejects_every_other_readiness_failure(), preopen_endpoint_violations() (+1 more)

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - "test_request_classifies_gateway_040_error_codes"
Cohesion: 0.16
Nodes (13): _gateway_error(), asyncio, parametrize, test_gateway_error_code_reads_only_the_discriminator(), test_request_classifies_bare_504_without_error_body(), test_request_classifies_gateway_040_error_codes(), handler(), test_request_retry_does_not_retry_authorization_failure() (+5 more)

### Community 193 - ".generate_chain"
Cohesion: 0.28
Nodes (7): bs_gamma(), Gamma — rate of change of delta wrt spot., date, datetime, Minutes until market close on expiration day., Generate full synthetic option chain for one expiration. Args: spot: Underlying…, test_gamma_positive()

### Community 194 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 195 - "install_shutdown_handler"
Cohesion: 0.29
Nodes (5): install_shutdown_handler(), Task, Cancel the supervised loops on SIGTERM so main()'s cleanup block runs. The app…, SIGTERM must unwind the TaskGroup without reporting a shutdown as an error. The…, test_sigterm_cancels_supervised_loops_and_task_group_exits_cleanly()

### Community 196 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run…, run()

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

### Community 211 - "set_readiness"
Cohesion: 0.11
Nodes (17): clear_readiness(), Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., set_readiness(), BrokerStateGate, entry_loop(), Periodically attempt entries during the entry window., Pick up a re-authorized Schwab token without restarting the container. schwab-… (+9 more)

### Community 223 - "filter_symbols_by_price"
Cohesion: 0.32
Nodes (8): _as_float(), extract_quote_price(), filter_symbols_by_price(), load_liquid_meta(), Any, Best-effort price from a Schwab quote payload for liquidity screening., Keep symbols whose Schwab quote price meets the minimum., test_filter_symbols_by_price()

### Community 224 - "test_order_builder.py"
Cohesion: 0.48
Nodes (6): make_candidate(), Tests for butterfly order builder., test_build_close_order_structure(), test_build_open_order_legs(), test_build_open_order_structure(), test_build_order_with_quantity()

### Community 225 - "compute_tent_boundaries"
Cohesion: 0.40
Nodes (5): compute_tent_boundaries(), _resolve_iv(), Find the two spot prices where the fly's BS mark equals entry cost. These are…, implied_vol(), Back-solve for implied volatility given an option market price. Returns None if…

### Community 226 - "bs_vega"
Cohesion: 0.67
Nodes (3): bs_vega(), Vega — sensitivity to 1% change in IV., test_vega_positive()

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **549 isolated node(s):** `butterfly-guy`, `SESSION_DATE`, `TARGET_EPOCH`, `TOOL_DIR`, `MONITOR` (+544 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1488 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `run_morning_scan.py`, `record_equity_market_data.py`, `run_live.py`, `test_run_live.py`, `providers.py`, `_redacted_order_audit`, `ButterflyOrderBuilder`, `backfill_equity_candles.py`, `SchwabSettings`, `volume.py`, `_assert_broker_state_matches_db`, `report_broker_order_statuses.py`, `PositionService`, `ButterflyCandidate`, `OrderManager`, `DirectSchwabMarketDataProvider`, `.reload_if_reauthorized`, `TradeService`, `set_readiness`, `refresh_equity_universes.py`, `services/daily_report_card.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `AppConfig` connect `core/config.py` to `ProfitStateMachine`, `run_backtest_db.py`, `TradeService`, `run_live.py`, `CandidateEvaluator`, `CandidateRegistry`, `PositionService`, `ButterflyCandidate`, `test_candidate_evaluator_accounting.py`, `load_config`, `test_chain_parser_parity.py`, `ValueError`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `DiscordNotifier` connect `DiscordNotifier` to `run_morning_scan.py`, `TradeService`, `run_live.py`, `PositionService`, `forex_calendar.py`, `ButterflyCandidate`, `weekend_review.py`, `services/daily_report_card.py`, `send_test_chart.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `ButterflyCandidate` (e.g. with `SimulationEngine` and `_candidate_mark()`) actually correct?**
  _`ButterflyCandidate` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `SchwabClientWrapper` (e.g. with `DirectSchwabMarketDataProvider` and `SchwabSettings`) actually correct?**
  _`SchwabClientWrapper` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `OptionQuote` (e.g. with `nearest_snapshot()` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 32 INFERRED edges - model-reasoned connections that need verification._