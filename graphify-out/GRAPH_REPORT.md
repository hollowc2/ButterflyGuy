# Graph Report - Butterflyguy  (2026-09-12)

## Corpus Check
- 257 files · ~312,263 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 7, .cron 4, .mdc 2)

## Summary
- 3605 nodes · 8382 edges · 214 communities (174 shown, 26 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 846 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2bc7739c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- chain_cache.py
- run_live.py
- test_order_manager.py
- ShadowComparingMarketDataProvider
- data_loader.py
- trade_chart.py
- butterfly_gateway_acceptance.py
- test_run_live.py
- discover_options_strategy.py
- main
- test_gateway_shadow_reads.py
- StrategySettings
- OrderIntentQueries
- gateway_client/__init__.py
- forex_calendar.py
- Schwab Gateway Credential Proof
- simulation_engine.py
- inspect_entry.py
- schwab_gateway_session_soak.py
- test_time_utils.py
- test_equity_scan.py
- Enum
- ButterflyCandidate
- reports/daily_report_card.py
- report.py
- core/config.py
- RiskQueries
- DirectProvider
- iter_chain_options
- schwab_gateway_v046_readiness_soak.py
- report_exit_mark_parity.py
- ProfitStateMachine
- test_risk_engine.py
- SchwabDataLoader
- news.py
- test_trade_service.py
- Regime
- run_morning_scan.py
- Codex Project State
- _assert_broker_state_matches_db
- report_broker_order_statuses.py
- Schwab Gateway Migration Plan
- refresh_equity_universes.py
- test_gateway_order_book.py
- run_entry_analysis.py
- PositionService
- equity_trade_chart.py
- Path
- DiscordNotifier
- order_manager.py
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- Window A — Token re-authorization (mandatory)
- load_config
- run_single
- load_date_data
- test_comparison_stats.py
- Current Schwab Integration
- _build_collector_market_data
- Standalone SchwabGateway Extraction Plan
- run_classifier_sweep.py
- parse_args
- SchwabClientWrapper
- ButterflyOrderBuilder
- universes.py
- NamedTuple
- DbDataLoader
- state_machine.py
- trade_service.py
- scanner.py
- test_run_backtest_db.py
- filter_symbols_by_price
- launch_schwab_gateway_session_soak_20260904.sh
- ShadowDiscrepancyRecorder
- Branch Review and Integration Plan
- test_gateway_ownership_boundaries.py
- AppConfig
- 1. Charles Schwab API
- test_schwab_token_keepalive.py
- test_daily_report_card.py
- weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- ChainDay
- 9) Capture equity candles and Level II for trade review
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- test_live_performance_report.py
- providers.py
- 2026-07-14 — data audit and research design
- Re-authorization checklist — Saturday 2026-08-15
- refresh_builtin_universes
- Capability recorder design
- SyntheticChainGenerator
- Option A deployment runbook — Helios, containerized
- run_backtest_db.py
- test_equity_universes.py
- Any
- Reducing the weekly re-authorization cost — a scoping question
- performance_chart.py
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- test_weekend_review.py
- TradePoint
- test_position_monitoring.py
- Window D — the gateway made reachable, started, and watched (2026-08-08)
- Re-authorization checklist — Saturday 2026-08-22
- health_monitor.py
- AGENTS.md
- BaseModel
- 2. Other external and public sources
- 5. Local files and backtest inputs
- services/daily_report_card.py
- Protocol
- RuntimeError
- Butterfly Guy
- launch_schwab_gateway_readiness_soak_20260909.sh
- report_trade_ladders.py
- BrokerStateGate
- C3 — wiring shadow reads into `run_live.py`
- Schwab gateway deployment options
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- SchwabGateway option-chain latency investigation (2026-09-04)
- main
- SchwabGateway order-book release full-session acceptance — 2026-09-01
- test_get_option_chain_returns_before_a_slow_gateway_responds
- Schwab gateway current status
- test_gateway_compose.py
- Schwab Gateway Foundation Smoke Test
- Schwab Single-Token Manager
- Window C — the two token writers resolved (2026-08-08)
- Strategy Settings
- setup_logging
- GatewayAuthoritativeMarketDataProvider
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- test_get_spot_price_returns_before_a_slow_gateway_responds
- date
- _redacted_order_audit
- test_order_preview.py
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Width Selection
- RegimeFilter
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- Schwab Gateway Multi-Consumer Foundation
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- test_no_unbounded_detail_reaches_the_logs
- Helios PAPER gateway cutover — 2026-08-25
- test_discrepancy_metric_labels_cover_every_declared_code
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- ._ema
- Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)
- launch_schwab_gateway_session_soak_20260901.sh
- Bounded proof failure codes and a settled restoration error window — 2026-08-06
- Credential proof passed — 2026-08-06
- Schwab Gateway Foundation: Local Run
- report_selection_parity.py
- SchwabGateway order books
- ButterflyGuy data sources and data types
- Equity candles and order-book recording
- Window A Executed — token re-authorized (2026-08-08)
- The token reload is DEPLOYED (2026-08-09T21:59:16Z)
- butterfly mark
- Preflight stops on the host-executed release — 2026-08-06
- test_gateway_token_manager.py
- test_auth_init_honours_schwab_token_path
- Host-executed proof step
- First token read, and a read-only container filesystem — 2026-08-06
- Operator-named absolute token path
- Live Runbook
- schwab-gateway-phase-7-execution-prompt.md
- _HtmlTableParser
- gateway-paper-cutover-handoff-prompt.md
- run_equity_universe_refresh_cron.sh
- Layered Risk Management
- Geometric butterfly icon
- 7. Operational and observability data
- ButterflyGuy data sources — representative samples
- 3) Start the SPX stack in Docker
- _MetricsHandler
- MinuteBar
- Offline safety-drill record — 2026-07-13
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- Critical External-Alert Delivery Proof - 2026-07-15
- XSP Flat-Runtime Restart Proof - 2026-07-14
- test_performance_dashboard.py
- auth_init.py
- test_run_scan_skips_market_holiday_before_schwab
- butterfly_guy/__init__.py
- equity_scan/__init__.py
- reports/__init__.py
- run_live_performance_cron.sh
- run_morning_scan_cron.sh
- Compare Real vs Synthetic Chains
- test_butterfly_selector.py
- butterfly-guy

## God Nodes (most connected - your core abstractions)
1. `SchwabClientWrapper` - 83 edges
2. `ButterflyCandidate` - 79 edges
3. `OptionQuote` - 70 edges
4. `MinuteBar` - 58 edges
5. `AppConfig` - 54 edges
6. `main()` - 52 edges
7. `PositionService` - 52 edges
8. `GatewayAuthoritativeMarketDataProvider` - 48 edges
9. `load_config()` - 46 edges
10. `make_order_manager()` - 45 edges

## Surprising Connections (you probably didn't know these)
- `test_config_rejects_unknown_keys()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_database_dsn()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_profit_management_strategy_defaults_to_peak_value_trailer()` --uses--> `AppConfig`  [INFERRED]
  tests/test_config.py → src/butterfly_guy/core/config.py
- `test_equity_scan_settings_accepts_news_config()` --uses--> `EquityScanSettings`  [INFERRED]
  tests/test_equity_scan_news.py → src/butterfly_guy/equity_scan/config.py
- `test_equity_scan_settings_accepts_liquid_universe()` --uses--> `EquityScanSettings`  [INFERRED]
  tests/test_equity_universes.py → src/butterfly_guy/equity_scan/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]

## Communities (214 total, 26 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.09
Nodes (40): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close() (+32 more)

### Community 1 - "chain_cache.py"
Cohesion: 0.22
Nodes (16): chain_cache_path(), load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->… (+8 more)

### Community 2 - "run_live.py"
Cohesion: 0.05
Nodes (70): BoundLogger, get_logger(), Structured logging setup with structlog., Get a structlog logger with optional name., _easter_sunday(), get_0dte_expiration(), get_us_market_early_closes(), get_us_market_holidays() (+62 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.15
Nodes (59): LiveSpread, NamedTuple, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+51 more)

### Community 4 - "ShadowComparingMarketDataProvider"
Cohesion: 0.13
Nodes (13): _error_code(), _mismatch_code(), _numbers_agree(), Any, date, Exception, Task, Classify a value difference by what the gateway could prove about its freshness. (+5 more)

### Community 5 - "data_loader.py"
Cohesion: 0.16
Nodes (13): day_cache_path(), load_day(), _parse_bar(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), Shared backtest market-data models. (+5 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.08
Nodes (47): _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles(), build_entry_chart_png() (+39 more)

### Community 7 - "butterfly_gateway_acceptance.py"
Cohesion: 0.14
Nodes (23): _endpoints(), MonkeyPatch, parametrize, test_identity_checks_paper_gateway_and_no_shadow_invariants(), test_preopen_accepts_retried_market_data_unavailable(), test_preopen_allows_documented_after_hours_strategy_readiness(), test_preopen_never_suppresses_other_endpoint_failures(), test_preopen_rejects_every_other_readiness_failure() (+15 more)

### Community 8 - "test_run_live.py"
Cohesion: 0.14
Nodes (26): _never_awaited(), asyncio, parametrize, _synthetic_butterfly_snapshot(), _synthetic_position(), test_collector_market_data_shadow_is_opt_in_and_direct_authoritative(), test_entry_loop_alerts_after_monitor_safety_error(), test_entry_loop_stops_after_unsafe_order_error() (+18 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "main"
Cohesion: 0.31
Nodes (7): test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings(), main(), GatewayClientSettings, Path, Load the host cron's market-data settings without exposing key material.

### Community 11 - "test_gateway_shadow_reads.py"
Cohesion: 0.13
Nodes (35): ChainMetadataResponseV1, SpotResponseV1, chain_response(), _comparisons(), _discrepancies(), asyncio, Exception, parametrize (+27 more)

### Community 12 - "StrategySettings"
Cohesion: 0.22
Nodes (17): StrategySettings, ButterflyBuilder, Builds and scores butterfly spreads from an option chain snapshot., make_chain(), make_quote(), Tests for the butterfly builder scanner., Generate a synthetic chain of call quotes around spot., test_builder_breakevens_valid() (+9 more)

### Community 13 - "OrderIntentQueries"
Cohesion: 0.12
Nodes (5): OrderIntentQueries, Any, Bulk insert option chain snapshot rows using COPY., Queries for durable broker order intents., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict.

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "Schwab Gateway Credential Proof"
Cohesion: 0.06
Nodes (34): Accepted runtime-baseline proof adapter, Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05 (+26 more)

### Community 17 - "simulation_engine.py"
Cohesion: 0.08
Nodes (38): ProfitManagementStrategy, DayData, DayResult, datetime, Single-day simulation engine using synthetic option chains., Runs full strategy on a single day using synthetic options., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. Skips… (+30 more)

### Community 18 - "inspect_entry.py"
Cohesion: 0.13
Nodes (17): DataFrame, CsvDataLoader, date, Path, CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files… (+9 more)

### Community 19 - "schwab_gateway_session_soak.py"
Cohesion: 0.10
Nodes (52): model_validator, GatewayMarketDataClient, adjudicate_transient_non_200(), assert_production_identity(), background_context(), cache_consistency_result(), canonical_market_data(), _confirm_surfaces() (+44 more)

### Community 20 - "test_time_utils.py"
Cohesion: 0.18
Nodes (18): Check if current time is within the given window (HH:MM strings)., time_in_window(), et(), datetime, Tests for market time utilities., test_get_0dte_expiration(), test_is_trading_day_monday(), test_is_trading_day_weekend() (+10 more)

### Community 21 - "test_equity_scan.py"
Cohesion: 0.19
Nodes (32): EquityScanSettings, build_snapshots(), parse_equity_quote(), passes_filters(), datetime, _quote_age_seconds(), rank_scan_results(), Normalize a Schwab quote payload into an EquitySnapshot. (+24 more)

### Community 23 - "ButterflyCandidate"
Cohesion: 0.06
Nodes (48): get_time_regime(), Classify minutes since open into a named time regime., _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows. (+40 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.16
Nodes (30): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, count_rejected_orders(), detect_problems(), _extract_order_id(), _extract_trade_leg() (+22 more)

### Community 25 - "report.py"
Cohesion: 0.14
Nodes (34): archive_report(), archive_report_json(), build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality() (+26 more)

### Community 26 - "core/config.py"
Cohesion: 0.14
Nodes (22): CollectorSettings, ConfigModel, DatabaseSettings, MonitoringSettings, PeakTrackingSettings, ProfitManagementSettings, BaseModel, QuoteQualitySettings (+14 more)

### Community 27 - "RiskQueries"
Cohesion: 0.12
Nodes (7): Queries for daily_risk_state table., Dollar PnL for the rolling 7-day window (closed trades only)., Dollar PnL of the last N closed trades, most recent first., RiskQueries, ConsecutiveLossNotifier, Protocol, Notification hook for risk warnings that do not block trading.

### Community 28 - "DirectProvider"
Cohesion: 0.12
Nodes (7): DirectProvider, FailingDirectProvider, date, The only source of returned values. Records every delegated call., A direct provider whose reads raise, to exercise the direct_unavailable path., test_direct_result_is_unchanged_when_the_gateway_times_out_in_real_time(), test_shadow_stays_disabled_when_no_gateway_client_is_supplied()

### Community 29 - "iter_chain_options"
Cohesion: 0.13
Nodes (28): iter_chain_options(), date, Yield (strike, option_type, opt_dict) for each option matching the expiration.…, _contract(), _parse_rows(), Any, date, parametrize (+20 more)

### Community 30 - "schwab_gateway_v046_readiness_soak.py"
Cohesion: 0.13
Nodes (39): Pattern, append_jsonl(), bounded_request(), candidate_observation(), diagnostic_probe(), docker_inspect(), endpoint_snapshot(), finalize() (+31 more)

### Community 31 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.17
Nodes (32): ProfitStateMachine, Evaluates position state and determines exit signals. States: - LOSS: position…, make_pos(), make_settings(), Tests for the profit management state machine., Pre-close exit remains available when explicitly configured., In profit tent with no drawdown → no exit., Should exit when in profit tent + 50% drawdown in morning. (+24 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SchwabDataLoader"
Cohesion: 0.14
Nodes (11): date, Path, Fetch the last VIX close known before the session., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day., Loads SPY 1-minute bars from Schwab, scaled to SPX price levels. Reuses the…, Fetch SPX daily open from yfinance for SPY→SPX calibration., Fetch the last VIX close before *date* to avoid lookahead. (+3 more)

### Community 35 - "news.py"
Cohesion: 0.15
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 36 - "test_trade_service.py"
Cohesion: 0.17
Nodes (20): EntrySettings, Return the first regular-session open for the requested Eastern date., _session_open_from_intraday_candles(), _quote(), test_entry_selection_config_applies_only_explicit_overrides(), test_entry_strategy_snapshot_records_live_selection_profile(), test_vix_entry_selection_does_not_fallback_outside_center_tolerance(), test_vix_entry_selection_prefers_first_width_for_xsp() (+12 more)

### Community 37 - "Regime"
Cohesion: 0.16
Nodes (11): GapRegimeFilter, Enum, Market regime classifier for 0-DTE butterfly parameter dispatch. Classifies…, Regime, str, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped., TestBullCallBias (+3 more)

### Community 38 - "run_morning_scan.py"
Cohesion: 0.11
Nodes (28): load_equity_scan_config(), Path, Load equity scan settings from YAML., attach_news_impacts(), Attach catalyst metadata without changing quote normalization., _as_int(), avg_daily_volume(), compute_rvol() (+20 more)

### Community 39 - "Codex Project State"
Cohesion: 0.08
Nodes (24): C3 default-off deployment and gateway hardening (2026-08-10), Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z), Codex Project State, Current Phase, Current Slice, Current status — 2026-08-10 (+16 more)

### Community 40 - "_assert_broker_state_matches_db"
Cohesion: 0.25
Nodes (19): _assert_broker_state_matches_db(), _open_trade_positions(), _repair_filled_entry_intent(), broker_fill_payload(), asyncio, parametrize, test_broker_state_gate_records_unsafe_reason(), test_filled_entry_intent_rejects_wrong_broker_ratio() (+11 more)

### Community 41 - "report_broker_order_statuses.py"
Cohesion: 0.28
Nodes (14): _allowed_roots(), _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize() (+6 more)

### Community 42 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 43 - "refresh_equity_universes.py"
Cohesion: 0.23
Nodes (11): build_liquid_meta(), filter_symbols_by_avg_volume(), Keep symbols whose 20-day average daily volume meets the minimum., main(), Path, Refresh equity universe files (sp500, nq100, liquid)., Build liquid.txt from exchange seeds validated via Schwab quotes and volume., refresh_liquid_universe() (+3 more)

### Community 44 - "test_gateway_order_book.py"
Cohesion: 0.23
Nodes (12): asyncio, ButterflyGuy's fail-closed SchwabGateway order-book consumer contract., _recent_payload(), _snapshot(), test_recent_authenticates_and_validates_fresh_contract(), recent(), test_recent_fails_closed_when_gateway_reports_stale_feed(), test_recent_rejects_mismatched_snapshot() (+4 more)

### Community 45 - "run_entry_analysis.py"
Cohesion: 0.16
Nodes (24): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+16 more)

### Community 46 - "PositionService"
Cohesion: 0.08
Nodes (49): A trade record for tracking entry/exit., TradeRecord, _expired_trade_has_broker_settlement(), date, broker_cash_settlement_from_transactions(), BrokerCashSettlement, _chain_spot_price(), final_regular_session_close_from_candles() (+41 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.17
Nodes (30): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+22 more)

### Community 48 - "Path"
Cohesion: 0.27
Nodes (11): _atomic_write_text(), load_universe(), load_universes(), Path, Durably replace a text file only after its complete contents are written., Load tickers for a named universe., Load all requested universes., _read_ticker_file() (+3 more)

### Community 49 - "DiscordNotifier"
Cohesion: 0.07
Nodes (21): Lightweight Telegram and ButterflyGuy Alertmanager helpers. Usage: from…, Post one stable, identifier-free alert fingerprint to Alertmanager., send_alertmanager(), AlertmanagerNotifier, DiscordNotifier, date, Sends centrally deduplicated critical alerts through Alertmanager., Post one or more plain-text messages (e.g. morning equity scan). (+13 more)

### Community 50 - "order_manager.py"
Cohesion: 0.10
Nodes (32): now_utc(), Shared utilities for parsing Schwab option chain responses., AmbiguousOrderError, _assert_entry_fill_within_limit(), _broker_time(), BrokerFill, BrokerFillError, _fill_result() (+24 more)

### Community 51 - "live_performance.py"
Cohesion: 0.12
Nodes (31): max_drawdown(), chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes() (+23 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "Window A — Token re-authorization (mandatory)"
Cohesion: 0.10
Nodes (20): A0 — Snapshot (read-only), A1 — Disable the keepalive, A2 — Stop the three trading services, A3 — Re-authorize, A4 — Verify the new document, A5 — Start the three services, A6 — Restore the keepalive, A7 — Verify (+12 more)

### Community 55 - "load_config"
Cohesion: 0.12
Nodes (21): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+13 more)

### Community 56 - "run_single"
Cohesion: 0.12
Nodes (28): backtest_entry_price(), _dd_schedule_label(), _force_synthetic_for_date(), _live_width_label(), load_asset_config(), main(), merge_chains(), _patch_chain_cache() (+20 more)

### Community 57 - "load_date_data"
Cohesion: 0.19
Nodes (19): discover_dates(), get_prev_close(), get_recent_closes(), get_vix_prev_close(), load_bars_from_db(), load_chains_from_db(), load_date_data(), load_entry_chains() (+11 more)

### Community 58 - "test_comparison_stats.py"
Cohesion: 0.46
Nodes (7): _print_comparison_table(), _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 59 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 60 - "_build_collector_market_data"
Cohesion: 0.20
Nodes (10): _build_collector_market_data(), _close_runtime_resources(), GatewayClientSettings, GatewayMarketDataClient, Select one authoritative read path without changing broker boundaries., Drain shadow work and close every owned resource, even if one close fails., MonkeyPatch, test_default_settings_construct_no_gateway_client() (+2 more)

### Community 61 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.10
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 62 - "run_classifier_sweep.py"
Cohesion: 0.15
Nodes (20): max_consecutive_losses(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday…, _summarize_combo() (+12 more)

### Community 63 - "parse_args"
Cohesion: 0.12
Nodes (21): _asset_drawdowns(), candidate_from_trade_row(), _floatlist(), _intlist(), parse_args(), Use the first regular-session snapshot for gap direction., Shared live/backtest parity fields from runtime config., Return live morning/late/afternoon drawdown thresholds. (+13 more)

### Community 64 - "SchwabClientWrapper"
Cohesion: 0.05
Nodes (52): SchwabSettings, _creation_timestamp(), Any, date, Read the document's re-authorization marker. `creation_timestamp` changes only…, Authenticate and resolve account hash., Rebuild the client if the token document has been re-authorized. schwab-py…, Execute with exponential backoff retry. (+44 more)

### Community 65 - "ButterflyOrderBuilder"
Cohesion: 0.21
Nodes (12): ButterflyOrderBuilder, Any, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_candidate(), Tests for butterfly order builder. (+4 more)

### Community 66 - "universes.py"
Cohesion: 0.17
Nodes (18): fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nyse_listed_symbols(), _fetch_url_text(), _is_common_equity_symbol(), _is_symbol_directory_footer(), parse_nasdaq_listed_text(), parse_nyse_listed_text() (+10 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.13
Nodes (14): DbDataLoader, Connection, date, datetime, DB-backed data loader for historical SPX + VIX data. Reads from the live…, Last VIX close strictly before *date*, avoiding morning lookahead., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order. (+6 more)

### Community 69 - "state_machine.py"
Cohesion: 0.16
Nodes (9): PositionState, Current state of an open position., ExitSignal, ProfitState, Enum, Profit management state machine for butterfly positions., Transition between profit states., Reset state machine for a new position. (+1 more)

### Community 70 - "trade_service.py"
Cohesion: 0.05
Nodes (58): capped_entry_limit(), entry_fill_within_limit(), Shared entry-price limit policy for production and candidate runtimes., Return a cent-valid debit limit that never exceeds the configured maximum., Return whether an entry fill respects its hard debit ceiling., _age_seconds(), Any, date (+50 more)

### Community 71 - "scanner.py"
Cohesion: 0.17
Nodes (21): _as_float(), _as_int(), filter_movers(), _filter(), _focus_reasons(), MarketContext, _mid_bid_ask(), _mover_change_pct() (+13 more)

### Community 72 - "test_run_backtest_db.py"
Cohesion: 0.14
Nodes (11): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), test_fitted_density_counts_returns_bucket_heights(), test_hypothetical_monitoring_load_uses_collector_only() (+3 more)

### Community 73 - "filter_symbols_by_price"
Cohesion: 0.32
Nodes (8): _as_float(), extract_quote_price(), filter_symbols_by_price(), load_liquid_meta(), Any, Best-effort price from a Schwab quote payload for liquidity screening., Keep symbols whose Schwab quote price meets the minimum., test_filter_symbols_by_price()

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 75 - "ShadowDiscrepancyRecorder"
Cohesion: 0.22
Nodes (5): GatewayMarketDataClient, A bounded, fixed-shape observation. Carries no payload, path, or exception text., Tally discrepancies over a fixed key space; retains no observed values., ShadowDiscrepancy, ShadowDiscrepancyRecorder

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.09
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 77 - "test_gateway_ownership_boundaries.py"
Cohesion: 0.24
Nodes (6): asyncio, Ownership boundaries after extracting the Schwab gateway from ButterflyGuy., _source(), test_compose_keeps_each_strategy_default_direct_with_staged_gateway_opt_in(), test_shadow_failure_is_observed_without_changing_the_direct_result(), test_standalone_packages_remain_pinned_and_consumers_import_them_directly()

### Community 78 - "AppConfig"
Cohesion: 0.15
Nodes (22): BaseSettings, AppConfig, ExecutionSettings, RiskSettings, _assert_live_config_supported(), asyncio, Integration tests for the option chain collector (requires live Schwab token)., A local JSON cache failure should not fail a DB-backed snapshot. (+14 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 80 - "test_schwab_token_keepalive.py"
Cohesion: 0.11
Nodes (15): lock_events(), fixture, parametrize, SCHWAB_TOKEN_PATH overrides the default, process env winning over .env., Record lock acquire/release without touching a real lock file., Wire up the module-level environment the keepalive script reads on import., The refresh and the quote both happen while the gateway's lock is held. Schwab…, A busy lock fails loudly rather than writing alongside the other writer. (+7 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.13
Nodes (20): parse_trade_transactions(), rank_trades(), Parse TRADE transactions into round-trip realized P&L., candles_to_series(), chartable_equity_trades(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options). (+12 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.18
Nodes (25): trade_pnl_dollars(), build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_performance_caption(), format_review_header() (+17 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "ChainDay"
Cohesion: 0.31
Nodes (9): dict, ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log…, day_with_monitoring_bars(), Add live monitor timestamps to bar iteration while carrying nearest spot…, _bar(), datetime, test_day_with_monitoring_bars_adds_live_poll_timestamps() (+1 more)

### Community 87 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.21
Nodes (21): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+13 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (11): _dashboard(), _expressions(), _panels(), visit(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_retired_experimental_runtime_is_absent_from_dashboards(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_uses_selected_trade_monitoring_as_candidate_spot_fallback() (+3 more)

### Community 91 - "test_live_performance_report.py"
Cohesion: 0.15
Nodes (15): date, Tests for live performance report generation., Per-run data must stay in the non-executable JSON block. The published page's…, test_chart_payload_includes_drawdown_fields(), test_compute_stats(), test_is_drawdown_exit(), test_no_trade_reason_mapping(), test_performance_report_shows_entire_history_and_fill_model_cohorts() (+7 more)

### Community 93 - "providers.py"
Cohesion: 0.10
Nodes (28): clear_readiness(), Prometheus metrics for monitoring., Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., Start HTTP server serving /metrics (Prometheus) and /health on *port*. Runs in…, readiness_snapshot(), set_readiness(), start_metrics_server() (+20 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "Re-authorization checklist — Saturday 2026-08-15"
Cohesion: 0.13
Nodes (14): Automated warnings before the cadence reset, Before you start, Expected result: no containers restarted, First, watch the reload do its job, Re-authorization checklist — Saturday 2026-08-15, Step 0 — already done, nothing to do, Step 1 — mint the token on zeus, in a real terminal, Step 2 — stage on Helios and verify byte-identical (+6 more)

### Community 96 - "refresh_builtin_universes"
Cohesion: 0.22
Nodes (10): fetch_sp500_rows(), fetch_sp500_sectors(), fetch_sp500_tickers(), Refresh sp500.txt, nq100.txt, and sectors.json from public sources., Download S&P 500 constituents with GICS sector metadata., Download the current S&P 500 constituents list., Map S&P 500 tickers to GICS sector names., refresh_builtin_universes() (+2 more)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "SyntheticChainGenerator"
Cohesion: 0.05
Nodes (58): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+50 more)

### Community 99 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.14
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 100 - "run_backtest_db.py"
Cohesion: 0.14
Nodes (25): DrawdownWindow, _duration_min(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window(), _format_et(), get_vix_at(), get_vix_snapshot_at() (+17 more)

### Community 101 - "test_equity_universes.py"
Cohesion: 0.22
Nodes (7): load_sector_map(), Load symbol -> sector mapping (GICS for index names, exchange fallback for…, Tests for equity universe seed parsing and liquidity gates., test_equity_scan_settings_accepts_liquid_universe(), test_extract_quote_price_prefers_extended_price(), test_load_sector_map_uses_liquid_meta_exchange_fallback(), test_write_universe_file_preserves_existing_file_if_replace_fails()

### Community 102 - "Any"
Cohesion: 0.16
Nodes (12): _explicit_fill_details(), install_shutdown_handler(), _intent_order_ids(), _json_dict(), _order_symbols(), Any, Task, Cancel the supervised loops on SIGTERM so main()'s cleanup block runs. The app… (+4 more)

### Community 103 - "Reducing the weekly re-authorization cost — a scoping question"
Cohesion: 0.15
Nodes (12): Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Production marker-change proof (2026-08-10), Recommendation, Reducing the weekly re-authorization cost — a scoping question, Stale-writer follow-up (2026-08-10), Status, The alternative worth costing first (+4 more)

### Community 104 - "performance_chart.py"
Cohesion: 0.18
Nodes (19): compute_stats(), ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels() (+11 more)

### Community 105 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.17
Nodes (12): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding (+4 more)

### Community 106 - "test_weekend_review.py"
Cohesion: 0.17
Nodes (15): previous_mon_fri(), Return Mon–Fri for the week ending on the Friday before reference., asyncio, date, Tests for weekend review date windows and orchestration., test_calendar_month_to_date(), test_format_performance_caption_includes_stats(), test_latest_fill_model_cohort_does_not_mix_legacy_and_mark_v1() (+7 more)

### Community 107 - "TradePoint"
Cohesion: 0.24
Nodes (17): no_trade_reason(), NoTradeDay, render_report_html(), render_trade_table_rows(), TradePoint, build_report(), fetch_closed_trades(), fetch_no_trade_days() (+9 more)

### Community 108 - "test_position_monitoring.py"
Cohesion: 0.23
Nodes (13): _candidate(), _gateway_contract(), asyncio, parametrize, _quotes(), Regression coverage for incomplete held-position market data., A quiet 778 quote is usable when the gateway explicitly says it is fresh., Replay valid -> incomplete threshold -> valid for every held leg. (+5 more)

### Community 109 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 110 - "Re-authorization checklist — Saturday 2026-08-22"
Cohesion: 0.18
Nodes (10): Preconditions — verified 2026-08-22T15:45:36Z, Re-authorization checklist — Saturday 2026-08-22, Step 1 — mint on zeus, in a real terminal, Step 2 — stage on Helios, verify byte-identical, Step 3 — move into place under the C1 lock, Step 4 — watch the reloads; restart only on a *confirmed* failure, Step 5 — verify, host against containers, Step 6 — record (+2 more)

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
Cohesion: 0.14
Nodes (18): PriceHistoryProvider, DailyReportCardSettings, load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds, archive_report() (+10 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "launch_schwab_gateway_readiness_soak_20260909.sh"
Cohesion: 0.20
Nodes (10): die(), EVIDENCE_DIR, LAUNCHER, LOG, MONITOR, SESSION_DATE, launch_schwab_gateway_readiness_soak_20260909.sh script, TARGET_EPOCH (+2 more)

### Community 121 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 122 - "BrokerStateGate"
Cohesion: 0.20
Nodes (5): BrokerStateGate, A reload failure must not take the trading loop down with it. The old client…, test_failed_token_reload_blocks_new_entries(), test_token_reload_loop_survives_a_failed_reload(), reload_if_reauthorized()

### Community 123 - "C3 — wiring shadow reads into `run_live.py`"
Cohesion: 0.20
Nodes (9): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, The wiring point, Two corrections to the received design points (+1 more)

### Community 124 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 125 - "Window H — verification held; the deadline reminder is mistimed (2026-08-08)"
Cohesion: 0.20
Nodes (10): Corrections to the Window H brief, Deliverables, Finding — the weekly reminder fires after the deadline it protects, Still open after Window H, Task 2 — the Monday check is deferred a fourth time, Tasks 3–6 — all green, verified host-against-container, The deadline in local time — stated because the brief did not, The deadline, re-derived from the document (+2 more)

### Community 126 - "SchwabGateway option-chain latency investigation (2026-09-04)"
Cohesion: 0.20
Nodes (9): 2026-09-09 runtime follow-up, Cache TTL is hard-capped at 4s in code, not just config, Chain size correlation, Recommendation, Request path (cache miss), SchwabGateway option-chain latency investigation (2026-09-04), Where the time actually goes: scheduler queueing, not the Schwab call itself, XSP held-leg event-age correction (2026-09-11) (+1 more)

### Community 127 - "main"
Cohesion: 0.05
Nodes (41): Pool, OptionChainCollector, Any, date, datetime, Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Fetch current chain and store snapshot. Returns row count., Main collector loop — runs while market is open. (+33 more)

### Community 128 - "SchwabGateway order-book release full-session acceptance — 2026-09-01"
Cohesion: 0.20
Nodes (9): Credential lineage, EquityScanner coexistence boundary, Post-close decision, Prepared read-only tools, SchwabGateway order-book release full-session acceptance — 2026-09-01, Scope and freeze boundary, Start the full-session harness (unattended), Tuesday preflight — final gate at 06:20-06:29 PDT (+1 more)

### Community 130 - "Schwab gateway current status"
Cohesion: 0.25
Nodes (6): Current state, Deferred Helios cleanup, Historical record, Runtime boundaries, Schwab gateway current status, Archived Schwab gateway transition records

### Community 131 - "test_gateway_compose.py"
Cohesion: 0.20
Nodes (7): Deployment boundaries retained after the standalone gateway extraction., All three trading services bind the token document from one required variable., Directory binds follow atomic token replacement to its new inode., A YAML token_path would override the deployment's shared token path., test_default_compose_binds_the_token_directory_never_the_document(), test_default_compose_token_binds_require_the_shared_token_directory(), test_live_configs_leave_token_path_to_the_environment()

### Community 132 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 133 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 134 - "Window C — the two token writers resolved (2026-08-08)"
Cohesion: 0.25
Nodes (8): C1 — the operator chose the shared lock, C3 plan produced, and a stale design point corrected, Durability decided, monitoring still open, Housekeeping, Multi-consumer shape — confirmed sound, with two wrinkles, Proven on the host by the production path, at zero extra token writes, Still open, Window C — the two token writers resolved (2026-08-08)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "setup_logging"
Cohesion: 0.07
Nodes (42): Configure structlog with JSON output and correlation IDs., setup_logging(), JsonlStreamRecorder, Any, date, datetime, Event, Path (+34 more)

### Community 137 - "GatewayAuthoritativeMarketDataProvider"
Cohesion: 0.06
Nodes (56): SimpleNamespace, DirectSchwabMarketDataProvider, _finite_number(), GatewayAuthoritativeMarketDataProvider, GatewayMarketDataError, _nonnegative_integer(), _now_eastern(), _optional_number() (+48 more)

### Community 138 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.25
Nodes (8): Corrections to the Window G brief, End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, The fix, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)

### Community 140 - "date"
Cohesion: 0.21
Nodes (3): date, datetime, Return the nearest full chain snapshot at or before *at* within…

### Community 141 - "_redacted_order_audit"
Cohesion: 0.31
Nodes (10): _broker_option_positions(), _matches_underlying(), _order(), test_redacted_audit_excludes_other_underlyings(), test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes(), test_redacted_audit_treats_replaced_as_historical_terminal(), test_broker_option_positions_keep_signed_quantity_for_matching_options(), main() (+2 more)

### Community 142 - "test_order_preview.py"
Cohesion: 0.27
Nodes (10): make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate., Order spec must have all fields Schwab requires., Schwab expects price as a string., test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields() (+2 more)

### Community 143 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 144 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 146 - "RegimeFilter"
Cohesion: 0.27
Nodes (6): datetime, Intraday VIX regime filter — skips entry when volatility is too elevated., Filter entries based on intraday VIX level at the time of entry., Most recent VIX bar close at or before entry_ts. None if no bars., True = safe to trade. False = skip (VIX too high). Returns True if no VIX bars…, RegimeFilter

### Community 147 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 148 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 149 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 151 - "Helios PAPER gateway cutover — 2026-08-25"
Cohesion: 0.29
Nodes (6): After-hours readiness condition, Helios PAPER gateway cutover — 2026-08-25, Immutable releases, Retained rollback images, Scope, Validation evidence

### Community 153 - "Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)"
Cohesion: 0.33
Nodes (6): Correction to Window H part 1, Item 1 — the warnings now fire before the deadline (deployed), Item 3 built — the token reload (2026-08-09, NOT deployed), Item 3 — the deciding question is answered: the swap is safe, Window H correction — the restart arithmetic was wrong, and the gateway never needed restarting, Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)

### Community 155 - "Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)"
Cohesion: 0.33
Nodes (6): Fixed by binding the directory, and by a second defect that fix exposed, Still open, The finding — the always-on gateway had orphaned all three trading containers, Verified, by inode and digest and by an actual atomic replace, Window E addendum — the candidate fleet's orphaned token, fixed (2026-08-08), Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)

### Community 156 - "launch_schwab_gateway_session_soak_20260901.sh"
Cohesion: 0.33
Nodes (5): LAUNCH_LOG, NOW_EPOCH, launch_schwab_gateway_session_soak_20260901.sh script, TARGET_EPOCH, TOKEN_PATH

### Community 157 - "Bounded proof failure codes and a settled restoration error window — 2026-08-06"
Cohesion: 0.40
Nodes (5): Bounded proof failure codes and a settled restoration error window — 2026-08-06, Release, The proof now names its own failure stage, The restoration error gate now counts a settled window, Two smaller decisions

### Community 158 - "Credential proof passed — 2026-08-06"
Cohesion: 0.40
Nodes (5): Credential proof passed — 2026-08-06, Disposition, Restoration, The production token was rotated, as designed, What this does and does not authorize

### Community 159 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 160 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run…, run()

### Community 161 - "SchwabGateway order books"
Cohesion: 0.50
Nodes (3): Live WebSocket, Recent snapshots, SchwabGateway order books

### Community 162 - "ButterflyGuy data sources and data types"
Cohesion: 0.22
Nodes (8): 10. Repository evidence map, 4. Shared database tables visible to the same DB account, 6. Canonical and derived analytical data types, 8. Reports, archives, charts, and outbound destinations, 9. Practical limitations and safety notes, At a glance, ButterflyGuy data sources and data types, Synthetic option-chain data

### Community 163 - "Equity candles and order-book recording"
Cohesion: 0.33
Nodes (5): Backfill candles, Equity candles and order-book recording, Historical limitation, Operational caution, Record a future BMNR session

### Community 165 - "Window A Executed — token re-authorized (2026-08-08)"
Cohesion: 0.50
Nodes (4): Correction 1 — A3 as written cannot work on Helios, Correction 2 — `easy_client` silently no-ops the re-authorization, Deviations from expectation, otherwise none, Window A Executed — token re-authorized (2026-08-08)

### Community 167 - "The token reload is DEPLOYED (2026-08-09T21:59:16Z)"
Cohesion: 0.50
Nodes (4): The C1 write proved itself in production, on the new code, The token reload is DEPLOYED (2026-08-09T21:59:16Z), Unchanged by any of this, What this changes about 2026-08-15

### Community 168 - "butterfly mark"
Cohesion: 0.20
Nodes (10): BUTTERFLYGUY, connectivity visual association, precision visual association, technology visual association, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background (+2 more)

### Community 169 - "Preflight stops on the host-executed release — 2026-08-06"
Cohesion: 0.67
Nodes (3): Credential exposure during the window, Preflight stops on the host-executed release — 2026-08-06, Release

### Community 170 - "test_gateway_token_manager.py"
Cohesion: 0.15
Nodes (33): AtomicTokenManager, increment_callback(), manager(), _process_refresh(), delayed_increment(), Exception, MonkeyPatch, parametrize (+25 more)

### Community 171 - "test_auth_init_honours_schwab_token_path"
Cohesion: 0.50
Nodes (3): parametrize, SCHWAB_TOKEN_PATH picks the write target, process env winning over .env., test_auth_init_honours_schwab_token_path()

### Community 172 - "Host-executed proof step"
Cohesion: 0.67
Nodes (3): Host-executed proof step, Release, Workflow consequence the next window must plan for

### Community 175 - "Live Runbook"
Cohesion: 0.25
Nodes (7): During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery, XSP Canary

### Community 177 - "_HtmlTableParser"
Cohesion: 0.18
Nodes (8): HTMLParser, fetch_nq100_tickers(), _HtmlTableParser, parse_nq100_html(), Extract constituents from the table identified by Ticker and Company headers., Download the current Nasdaq-100 constituents from Wikipedia., Collect text cells from HTML tables without depending on tag attributes., test_parse_nq100_html_handles_current_parsoid_cell_attributes_and_nested_tags()

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

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 194 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 198 - "MinuteBar"
Cohesion: 0.11
Nodes (19): MinuteBar, BiasScoreFilter, Multi-signal directional bias filter for 0-DTE butterfly entries., High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Scores market direction using 4 signals; returns CALL, PUT, or None., Compute bias score from 4 signals: gap : +1 if entry_close > prev_close, -1 if…, Volume-weighted average price using close as typical price. Edge case: all…, make_bar() (+11 more)

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

### Community 227 - "test_butterfly_selector.py"
Cohesion: 0.48
Nodes (6): make_candidate(), Tests for butterfly candidate selection., test_regular_best_rr_selection_still_uses_rr_target(), test_vix_centered_selection_blocks_when_no_candidate_near_target(), test_vix_centered_selection_uses_rr_target_after_center_filter(), test_vix_selection_rejects_cheap_extreme_rr_tail_candidate()

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **554 isolated node(s):** `butterfly-guy`, `SESSION_DATE`, `TARGET_EPOCH`, `TOOL_DIR`, `MONITOR` (+549 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1407 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `run_live.py`, `news.py`, `run_morning_scan.py`, `trade_service.py`, `setup_logging`, `GatewayAuthoritativeMarketDataProvider`, `report_broker_order_statuses.py`, `refresh_equity_universes.py`, `_assert_broker_state_matches_db`, `_redacted_order_audit`, `PositionService`, `main`, `order_manager.py`, `services/daily_report_card.py`, `_build_collector_market_data`, `providers.py`, `main`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `MinuteBar` connect `MinuteBar` to `run_paper_replay.py`, `SchwabDataLoader`, `DbDataLoader`, `data_loader.py`, `run_backtest_db.py`, `trade_service.py`, `test_run_backtest_db.py`, `run_entry_analysis.py`, `simulation_engine.py`, `inspect_entry.py`, `RegimeFilter`, `ChainDay`, `load_date_data`, `parse_args`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `TradeService` connect `trade_service.py` to `SchwabClientWrapper`, `run_live.py`, `test_trade_service.py`, `Regime`, `MinuteBar`, `trade_chart.py`, `StrategySettings`, `AppConfig`, `PositionService`, `DiscordNotifier`, `order_manager.py`, `ButterflyCandidate`, `providers.py`, `main`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `SchwabClientWrapper` (e.g. with `DirectSchwabMarketDataProvider` and `SchwabSettings`) actually correct?**
  _`SchwabClientWrapper` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `ButterflyCandidate` (e.g. with `SimulationEngine` and `ButterflyOrderBuilder`) actually correct?**
  _`ButterflyCandidate` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `OptionQuote` (e.g. with `nearest_snapshot()` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 28 INFERRED edges - model-reasoned connections that need verification._