# Graph Report - Butterflyguy  (2026-07-28)

## Corpus Check
- 228 files · ~245,977 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3290 nodes · 8884 edges · 165 communities (154 shown, 11 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 885 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9edfa707`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- OptionQuote
- ExecutionSettings
- test_order_manager.py
- DatabasePool
- SchwabClientWrapper
- ButterflyChartSpec
- run_single
- test_run_live.py
- discover_options_strategy.py
- AppConfig
- test_candidate_evaluator_accounting.py
- test_position_manager.py
- DayData
- CandidateRegistry
- forex_calendar.py
- SnapshotIdentity
- MinuteBar
- feed.py
- test_comparison_stats.py
- notifier.py
- EquityScanSettings
- 4. Detailed findings
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- core/config.py
- services/daily_report_card.py
- trade_service.py
- run_entry_analysis.py
- .session_close
- Domain Model and Ingestion Boundaries
- ProfitStateMachine
- test_risk_engine.py
- synthetic_chain.py
- news.py
- record_equity_market_data.py
- is_market_open
- load_date_data
- SyntheticChainGenerator
- state_machine.py
- test_candidate_snapshot.py
- send_test_chart.py
- AtomicSnapshotStore
- CandidateEvaluator
- StrategySettings
- SchwabDataLoader
- equity_trade_chart.py
- run_morning_scan.py
- test_broker_order_intents.py
- DiscordNotifier
- live_performance.py
- entry_loop
- ButterflyGuy AI Review State
- ButterflyCandidate
- load_config
- Database Compatibility
- weekend_review.py
- TradeQueries
- daily_reset_loop
- TradeRecord
- .can_trade
- SessionClose
- ButterflySelector
- time_utils.py
- ReadOnlySchwabMarketDataClient
- universes.py
- order_manager.py
- DbDataLoader
- _MetricsHandler
- GapRegimeFilter
- test_candidate_provider.py
- Behavioral Specification
- logging.py
- run_backtest_db.py
- chain_cache.py
- scanner.py
- download_schwab_cache.py
- position_service.py
- 1. Charles Schwab API
- parse_args
- test_daily_report_card.py
- .collect_snapshot
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- test_trade_service.py
- str
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- ChainDay
- report_exit_mark_parity.py
- ButterflyGuy Fable 5 Refactor Plan
- 2026-07-14 — data audit and research design
- .attempt_entry
- RegimeFilter
- performance_chart.py
- ButterflyOrderBuilder
- test_candidate_variants.py
- _asset_drawdowns
- FakeProvider
- resolve_db_dsn
- select_cross_width_candidate
- _print_same_entry_comparison_table
- test_candidate_settlement.py
- 9) Capture equity candles and Level II for trade review
- .bulk_upsert
- test_schwab_token_keepalive.py
- health_monitor.py
- AGENTS.md
- ButterflyGuy Code Review State
- 2. Other external and public sources
- 5. Local files and backtest inputs
- Butterfly Guy
- _force_synthetic_for_date
- position_manager.py
- Strategy Settings
- XSP Partial-Fill Evidence Plan
- OrderManager
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
2. `OptionQuote` - 100 edges
3. `SchwabClientWrapper` - 78 edges
4. `AppConfig` - 76 edges
5. `make_settings()` - 71 edges
6. `make_candidate()` - 71 edges
7. `make_order_manager()` - 71 edges
8. `MinuteBar` - 70 edges
9. `MarketSnapshot` - 63 edges
10. `DatabasePool` - 59 edges

## Surprising Connections (you probably didn't know these)
- `test_startup_rejects_bot_owned_partial_child_order()` --calls--> `_assert_broker_state_matches_db()`  [INFERRED]
  tests/test_broker_order_intents.py → src/butterfly_guy/scripts/run_live.py
- `test_startup_rejects_bot_owned_partial_order()` --calls--> `_assert_broker_state_matches_db()`  [INFERRED]
  tests/test_broker_order_intents.py → src/butterfly_guy/scripts/run_live.py
- `test_startup_rejects_unknown_working_order()` --calls--> `_assert_broker_state_matches_db()`  [INFERRED]
  tests/test_broker_order_intents.py → src/butterfly_guy/scripts/run_live.py
- `test_broker_option_position_symbols_filters_same_underlying_options()` --calls--> `_broker_option_position_symbols()`  [INFERRED]
  tests/test_run_live.py → src/butterfly_guy/scripts/run_live.py
- `TestEngineIntegration` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]

## Communities (165 total, 11 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.10
Nodes (38): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close() (+30 more)

### Community 1 - "OptionQuote"
Cohesion: 0.11
Nodes (10): _aware_utc(), from_dict(), MarketSnapshot, Any, datetime, Immutable normalized market snapshots shared by candidate evaluators., One atomically published, replayable view of candidate market data., StaleSnapshotError (+2 more)

### Community 2 - "ExecutionSettings"
Cohesion: 0.24
Nodes (16): ExecutionSettings, RiskSettings, SchwabSettings, _assert_live_config_supported(), test_live_config_allows_confirmed_xsp_canary(), test_live_config_allows_spx_live_when_explicitly_confirmed(), test_live_config_allows_spx_live_when_explicitly_enabled(), test_live_config_rejects_non_spx_live_money() (+8 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.10
Nodes (86): LiveSpread, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread(), make_order_manager() (+78 more)

### Community 4 - "DatabasePool"
Cohesion: 0.06
Nodes (37): BoundLogger, Pool, config_sha256(), Path, get_logger(), Get a structlog logger with optional name., Prometheus metrics for monitoring., Start HTTP server serving /metrics (Prometheus) and /health on *port*. Runs in… (+29 more)

### Community 5 - "SchwabClientWrapper"
Cohesion: 0.07
Nodes (21): Any, date, Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Get the status of an order., Cancel an existing order., Fetch 1-minute bars for today (and optionally prior days) from Schwab., Fetch all orders entered today from Schwab. (+13 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.10
Nodes (40): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+32 more)

### Community 7 - "run_single"
Cohesion: 0.14
Nodes (31): _dd_schedule_label(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window(), _live_width_label(), load_asset_config(), main(), nearest_snapshot() (+23 more)

### Community 8 - "test_run_live.py"
Cohesion: 0.12
Nodes (33): clear_readiness(), Add a not-ready reason; ``None`` explicitly resets all reasons., Set readiness; ``None`` means the service is ready., readiness_snapshot(), set_readiness(), broker_reconciler_loop(), test_health_stays_live_while_ready_reports_degraded(), test_readiness_recovery_clears_only_its_own_reason() (+25 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "AppConfig"
Cohesion: 0.14
Nodes (18): BaseSettings, assert_candidate_safety(), AppConfig, model_validator, entry_strategy_snapshot(), Serializable live strategy profile used for entry selection., asyncio, Integration tests for the option chain collector (requires live Schwab token). (+10 more)

### Community 11 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.24
Nodes (8): _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_performance_stats_reports_outlier_dependence(), test_min_gap_filter_logs_no_trade_before_candidate_selection(), test_min_gap_filter_preserves_direction_above_threshold(), test_review_progress_counts_only_closed_mark_v1_trades()

### Community 12 - "test_position_manager.py"
Cohesion: 0.28
Nodes (12): fly_settlement_value(), Butterfly cash-settlement value from the underlying index close., make_candidate(), make_quote(), make_xsp_candidate(), quote_map(), Tests for butterfly position valuation helpers., test_call_butterfly_settles_to_intrinsic_with_spot_below_all_strikes() (+4 more)

### Community 13 - "DayData"
Cohesion: 0.09
Nodes (30): DataFrame, _build_bars(), _build_prev_close(), _build_recent_closes(), _build_vix(), _build_vix_bars(), CsvDataLoader, date (+22 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.11
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.11
Nodes (31): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), is_sunday_startup_window() (+23 more)

### Community 16 - "SnapshotIdentity"
Cohesion: 0.09
Nodes (18): Paper-only SPX candidate fleet fed by a shared market-data service., RuntimeError, No complete snapshot is currently available., A long poll completed normally before a newer snapshot was published., SnapshotIdentity, SnapshotUnavailableError, SnapshotWaitTimeoutError, HttpMarketDataProvider (+10 more)

### Community 17 - "MinuteBar"
Cohesion: 0.09
Nodes (24): MinuteBar, BiasScoreFilter, _compute_or(), _compute_vwap(), _ema(), Multi-signal directional bias filter for 0-DTE butterfly entries., High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Exponential moving average seeded with SMA of first `period` bars. Returns None… (+16 more)

### Community 18 - "feed.py"
Cohesion: 0.18
Nodes (21): Application, Request, _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs() (+13 more)

### Community 19 - "test_comparison_stats.py"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 20 - "notifier.py"
Cohesion: 0.12
Nodes (17): AlertmanagerNotifier, Trading and risk notifications., Sends centrally deduplicated critical alerts through Alertmanager., asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted(), test_alertmanager_new_firing_cancels_stale_pending_resolution() (+9 more)

### Community 21 - "EquityScanSettings"
Cohesion: 0.13
Nodes (46): EquityScanSettings, attach_news_impacts(), build_snapshots(), _focus_reasons(), OpeningFocusItem, parse_equity_quote(), passes_filters(), datetime (+38 more)

### Community 22 - "4. Detailed findings"
Cohesion: 0.05
Nodes (47): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Findings summary, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix (+39 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.09
Nodes (36): ProfitManagementStrategy, DayResult, _drawdown_rule(), DrawdownWindow, _profit_exit_reason(), datetime, Single-day simulation engine using synthetic option chains., Runs full strategy on a single day using synthetic options. (+28 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.13
Nodes (36): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders(), detect_problems(), _extract_order_id() (+28 more)

### Community 25 - "report.py"
Cohesion: 0.17
Nodes (31): build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes() (+23 more)

### Community 26 - "core/config.py"
Cohesion: 0.15
Nodes (15): BaseModel, Schwab market-data client deliberately lacking every account/order operation., CollectorSettings, ConfigModel, DatabaseSettings, MonitoringSettings, PeakTrackingSettings, BaseModel (+7 more)

### Community 27 - "services/daily_report_card.py"
Cohesion: 0.13
Nodes (19): load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds, archive_report(), date, Path (+11 more)

### Community 28 - "trade_service.py"
Cohesion: 0.14
Nodes (24): candidate_performance_stats(), CandidateAuditContext, CandidateDecisionQueries, CandidatePerformanceStats, Paper-only candidate evaluator built without broker execution dependencies., Summarize one chronological, closed mark_v1 PnL cohort., CandidateQueries, DecisionQueries (+16 more)

### Community 29 - "run_entry_analysis.py"
Cohesion: 0.15
Nodes (26): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+18 more)

### Community 30 - ".session_close"
Cohesion: 0.17
Nodes (12): _final_regular_session_close(), Lease, _previous_close(), Any, date, datetime, LeaseKind, time (+4 more)

### Community 31 - "Domain Model and Ingestion Boundaries"
Cohesion: 0.05
Nodes (40): Actual Schwab Symbol Formats, Backtest Database Chain Rows to Strategy, Broker Mark Versus Computed Mid, ButterflyCandidate, Candidate, Spot, and Daily Bars, code:python (fly_mark_value(lower, center, upper) = lower.mark - 2 * cent), code:text (OptionQuote[]), code:text (External API / asyncpg row / JSON cache) (+32 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.17
Nodes (33): ProfitStateMachine, Evaluates position state and determines exit signals. States: - LOSS: position…, make_pos(), make_settings(), Tests for the profit management state machine., Pre-close exit remains available when explicitly configured., In profit tent with no drawdown → no exit., Should exit when in profit tent + 50% drawdown in morning. (+25 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "synthetic_chain.py"
Cohesion: 0.08
Nodes (40): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+32 more)

### Community 35 - "news.py"
Cohesion: 0.22
Nodes (26): EquityNewsSettings, _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts(), _fetch_alpha_news_for_symbol(), _fetch_json(), fetch_news_impacts(), _fetch_sec_impacts() (+18 more)

### Community 36 - "record_equity_market_data.py"
Cohesion: 0.10
Nodes (31): JsonlStreamRecorder, date, datetime, Event, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session. (+23 more)

### Community 37 - "is_market_open"
Cohesion: 0.15
Nodes (26): is_market_open(), is_premarket_window(), is_trading_day(), time, Check if the market is currently open., True during weekday premarket (default 4:00–9:30 AM ET)., Check if a given date is a trading day (weekday, not a holiday)., Check if current time is within the given window (HH:MM strings). (+18 more)

### Community 38 - "load_date_data"
Cohesion: 0.14
Nodes (26): discover_dates(), get_prev_close(), get_recent_closes(), get_vix_prev_close(), load_bars_from_db(), load_chains_from_db(), load_date_data(), load_entry_chains() (+18 more)

### Community 39 - "SyntheticChainGenerator"
Cohesion: 0.15
Nodes (18): IVModel, Models implied volatility with VIX scaling and volatility skew., Convert VIX index value to 0-DTE ATM IV estimate. VIX is the 30-day implied vol…, Compute skew-adjusted IV for a given strike. OTM puts have elevated IV…, Generates a synthetic SPX option chain from spot + VIX., SyntheticChainGenerator, make_snapshot_time(), datetime (+10 more)

### Community 40 - "state_machine.py"
Cohesion: 0.14
Nodes (11): Enum, ProfitManagementSettings, PositionState, Current state of an open position., ExitSignal, ProfitState, Enum, Profit management state machine for butterfly positions. (+3 more)

### Community 41 - "test_candidate_snapshot.py"
Cohesion: 0.36
Nodes (11): asyncio, datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry(), test_long_poll_never_replays_same_sequence(), test_new_lease_wakes_idle_feed() (+3 more)

### Community 42 - "send_test_chart.py"
Cohesion: 0.24
Nodes (11): trade_pnl_dollars(), _load_spot_series(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., _spot_rows_to_candles(), load_spot_series(), date (+3 more)

### Community 43 - "AtomicSnapshotStore"
Cohesion: 0.13
Nodes (23): AtomicSnapshotStore, CandidateFeed, LeaseRegistry, Condition-guarded pointer swap; readers never observe partial snapshots., Persist once and return the canonical evidence for this session., SnapshotArchive, No verified final regular-session close is available from the shared feed., SessionCloseUnavailableError (+15 more)

### Community 44 - "CandidateEvaluator"
Cohesion: 0.18
Nodes (9): candidate_fill_parity_failures(), _candidate_mark(), CandidateEvaluator, CandidatePaperExecutor, Any, Count mark_v1 rows whose fills disagree with their recorded evidence., Mark-price fills only; this object intentionally has no broker methods., _restore_trade() (+1 more)

### Community 45 - "StrategySettings"
Cohesion: 0.12
Nodes (32): StrategySettings, main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date. Replicates the…, per_width_selection_winners(), Select the best butterfly candidate for a single wing width., Load collector quotes, adding 2s polls only for a pinned live trade. (+24 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.14
Nodes (11): date, Path, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day., Loads SPY 1-minute bars from Schwab, scaled to SPX price levels. Reuses the…, Fetch SPX daily open from yfinance for SPY→SPX calibration., Fetch VIX daily close from yfinance. (+3 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.15
Nodes (34): TradeResult, build_equity_trade_chart_png(), chartable_equity_trades(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume() (+26 more)

### Community 48 - "run_morning_scan.py"
Cohesion: 0.09
Nodes (31): archive_report(), archive_report_json(), Path, Write the scan report to a dated markdown file under report_dir., Write machine-readable scan internals next to the markdown report., load_liquid_meta(), load_sector_map(), Load symbol -> GICS sector mapping written by refresh_equity_universes. (+23 more)

### Community 49 - "test_broker_order_intents.py"
Cohesion: 0.19
Nodes (19): broker_fill_payload(), asyncio, parametrize, test_broker_state_gate_records_unsafe_reason(), test_filled_entry_intent_rejects_wrong_broker_ratio(), test_filled_entry_intent_rejects_zero_quantity(), test_filled_entry_intent_repairs_open_trade_only_with_matching_legs_and_fill(), test_filled_exit_intent_repairs_open_trade_only_when_broker_flat() (+11 more)

### Community 50 - "DiscordNotifier"
Cohesion: 0.22
Nodes (4): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook.

### Community 51 - "live_performance.py"
Cohesion: 0.12
Nodes (42): chart_payload(), duration_minutes(), format_et_time(), is_drawdown_exit(), _money(), no_trade_reason(), NoTradeDay, _parse_metadata() (+34 more)

### Community 52 - "entry_loop"
Cohesion: 0.14
Nodes (14): entry_loop(), Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window., Periodically attempt entries during the entry window. (+6 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.11
Nodes (18): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Changes Made This Session, Commands Run, Current Cycle Checkpoints, Current Objective, Decisions Made (+10 more)

### Community 54 - "ButterflyCandidate"
Cohesion: 0.19
Nodes (18): ButterflyCandidate, Pydantic models for option data and trade records., A butterfly spread candidate identified by the scanner., O(N*W) scan: for each center strike within spot_range, for each wing_width,…, EntrySelectionResult, build_entry_selection_parity(), _candidate_payload(), _per_width_payload() (+10 more)

### Community 55 - "load_config"
Cohesion: 0.05
Nodes (59): load_config(), Path, Load configuration from YAML file and environment variables., _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day. (+51 more)

### Community 56 - "Database Compatibility"
Cohesion: 0.09
Nodes (25): `001_initial.sql`: `option_chain_snapshots`, `001_initial.sql`: `spot_prices`, `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, `005_add_daily_bars.sql`, Anonymized Synchronized Data Slice, code:sql (CREATE TABLE IF NOT EXISTS option_chain_snapshots (), code:sql (CREATE TABLE IF NOT EXISTS spot_prices () (+17 more)

### Community 57 - "weekend_review.py"
Cohesion: 0.12
Nodes (38): build_eod_chart_for_row(), calendar_month_to_date(), fetch_closed_trades(), format_combined_performance_caption(), format_performance_caption(), format_review_header(), format_trade_recap(), latest_fill_model_cohort() (+30 more)

### Community 58 - "TradeQueries"
Cohesion: 0.06
Nodes (20): dict, Protocol, Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Sum of realized PnL for the rolling 7-day window (closed trades only)., Queries for trades table. (+12 more)

### Community 59 - "daily_reset_loop"
Cohesion: 0.08
Nodes (28): daily_reset_loop(), eod_chart_loop(), Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Send deferred full-session EOD charts after the cash close., Reset daily risk state at market open. (+20 more)

### Community 60 - "TradeRecord"
Cohesion: 0.21
Nodes (20): A trade record for tracking entry/exit., TradeRecord, final_regular_session_close_from_candles(), _candle(), asyncio, datetime, parametrize, RuntimeError (+12 more)

### Community 61 - ".can_trade"
Cohesion: 0.14
Nodes (8): date, Overwrite realized_pnl in risk state (SET, not ADD).         Used at startup to, Record that a trade was executed., Record realized dollar PnL., Overwrite dollar realized_pnl in risk state (SET, not ADD). Used at startup to…, Manually sync the trade count in the risk state table. Used at startup to…, Check all risk conditions. Returns (allowed, reason).          account_value and, Check risk conditions before entry. Returns (allowed, reason). buying_power is…

### Community 62 - "SessionClose"
Cohesion: 0.19
Nodes (6): Auditable final regular-session SPX close supplied by the shared feed., SessionClose, date, Direct-provider adapter for primary/parity paths that normalize Schwab data., SchwabMarketDataProvider, test_session_close_round_trip_preserves_timezone_aware_evidence()

### Community 63 - "ButterflySelector"
Cohesion: 0.15
Nodes (14): ButterflySelector, Butterfly selector — picks the best candidate from a list., Selects the best butterfly candidate., Select the best butterfly candidate. When `target_center` is provided (derived…, Select the farthest OTM candidate from the already-valid candidate set., Select the candidate whose cost is closest to its max_cost_per_width., Helpers for choosing a candidate across multiple active widths., make_candidate() (+6 more)

### Community 64 - "time_utils.py"
Cohesion: 0.15
Nodes (26): _easter_sunday(), get_0dte_expiration(), get_us_market_early_closes(), get_us_market_holidays(), _last_weekday(), market_close_time(), minutes_since_open(), minutes_to_close() (+18 more)

### Community 65 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.24
Nodes (4): Any, date, Authenticate a Schwab client without resolving or retaining an account., ReadOnlySchwabMarketDataClient

### Community 66 - "universes.py"
Cohesion: 0.05
Nodes (68): EquityScanFilters, EquityScanLimits, load_equity_scan_config(), BaseModel, Path, Configuration for the equity morning scan., Load equity scan settings from YAML., _as_float() (+60 more)

### Community 67 - "order_manager.py"
Cohesion: 0.10
Nodes (22): NamedTuple, RuntimeError, Place an order once and return the order ID. Order placement is not retried…, Place an order and return the order ID., Execute with exponential backoff retry., OrderIntentQueries, Queries for durable broker order intents., _broker_time() (+14 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.15
Nodes (15): DbDataLoader, Connection, date, datetime, DB-backed data loader for historical SPX + VIX data. Reads from the live…, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order. (+7 more)

### Community 69 - "_MetricsHandler"
Cohesion: 0.31
Nodes (5): BaseHTTPRequestHandler, _MetricsHandler, Clear only the recovered subsystem's not-ready reason., HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 70 - "GapRegimeFilter"
Cohesion: 0.13
Nodes (13): Classify regime then delegate to simulate_day() with matching params. Returns…, Maps Regime → SimulationParams for use with simulate_day_adaptive(). Per-regime…, RegimeDispatch, GapRegimeFilter, Enum, Return Regime for today given prior daily closes and today's VIX. Args:…, Regime, Unit tests for GapRegimeFilter.apply(). (+5 more)

### Community 71 - "test_candidate_provider.py"
Cohesion: 0.27
Nodes (12): Any, Build a synchronous schwab-py handler that never blocks the stream., make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close() (+4 more)

### Community 72 - "Behavioral Specification"
Cohesion: 0.08
Nodes (23): Algorithmic Refinements For 0-DTE Robustness, Behavioral Specification, Bid-Ask Spread Penalization, Candidate Construction Invariants, code:text (raw_expected_move = underlying_spot * (vix / 100) * sqrt(cla), Current Config Defaults, Current Width And Center Selection Data, Double-Factor Live Gating (+15 more)

### Community 73 - "logging.py"
Cohesion: 0.18
Nodes (14): Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs., setup_logging(), async_main(), main(), parse_args(), Namespace, Path (+6 more)

### Community 74 - "run_backtest_db.py"
Cohesion: 0.19
Nodes (19): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), _duration_min(), _format_et(), get_vix_at() (+11 more)

### Community 75 - "chain_cache.py"
Cohesion: 0.23
Nodes (15): chain_cache_path(), load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->… (+7 more)

### Community 76 - "scanner.py"
Cohesion: 0.21
Nodes (19): _as_float(), _as_int(), _dedupe_premarket(), filter_movers(), _is_duplicate_premarket(), _live_price(), MarketContext, _mid_bid_ask() (+11 more)

### Community 77 - "download_schwab_cache.py"
Cohesion: 0.27
Nodes (10): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), date_range(), main() (+2 more)

### Community 78 - "position_service.py"
Cohesion: 0.08
Nodes (37): Queries for tent_boundaries table., TentQueries, PositionManager, Tracks position value from chain data and manages peak tracking., Reset for a new position. Optionally restore a persisted peak (e.g. after…, broker_cash_settlement_from_transactions(), BrokerCashSettlement, _chain_spot_price() (+29 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.17
Nodes (15): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+7 more)

### Community 80 - "parse_args"
Cohesion: 0.15
Nodes (16): candidate_from_trade_row(), _floatlist(), _intlist(), parse_args(), _parse_dd_schedule(), _strlist(), _timelist_pst(), _parse_for_asset() (+8 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.15
Nodes (18): parse_trade_transactions(), Parse TRADE transactions into ranked trade results., Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options)., test_build_equity_trade_chart_png_returns_png_bytes() (+10 more)

### Community 82 - ".collect_snapshot"
Cohesion: 0.20
Nodes (7): Any, date, datetime, Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Fetch current chain and store snapshot. Returns row count., Main collector loop — runs while market is open., Parse Schwab callExpDateMap/putExpDateMap into flat rows.

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.10
Nodes (21): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+13 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "test_trade_service.py"
Cohesion: 0.22
Nodes (17): EntrySettings, _session_open_from_intraday_candles(), _quote(), test_entry_selection_config_applies_only_explicit_overrides(), test_vix_entry_selection_does_not_fallback_outside_center_tolerance(), test_vix_entry_selection_prefers_first_width_for_xsp(), _candle(), asyncio (+9 more)

### Community 87 - "str"
Cohesion: 0.20
Nodes (27): order_ids(), order_statuses(), walk_orders(), _assert_broker_state_matches_db(), _broker_option_position_symbols(), _broker_option_positions(), _expired_trade_has_broker_settlement(), _explicit_fill_details() (+19 more)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.27
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 91 - "ChainDay"
Cohesion: 0.38
Nodes (8): ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log…, day_with_monitoring_bars(), Add live monitor timestamps to bar iteration while carrying nearest spot…, _bar(), datetime, test_day_with_monitoring_bars_adds_live_poll_timestamps(), test_day_with_monitoring_bars_keeps_existing_bar_for_same_timestamp()

### Community 92 - "report_exit_mark_parity.py"
Cohesion: 0.10
Nodes (38): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes(), fly_mark_value() (+30 more)

### Community 93 - "ButterflyGuy Fable 5 Refactor Plan"
Cohesion: 0.11
Nodes (18): ButterflyGuy Fable 5 Refactor Plan, Closed Design Decisions, code:text (Use FABLE_REFACTOR_PLAN.md as the project entry point. Start), code:text (Phase 1 is complete. Now read DOMAIN_MODEL.md and the candid), code:text (Phase 2 is complete. Now read BEHAVIORAL_SPEC.md in full. Im), code:text (Phase 3 is complete. Implement the live broker boundary only), Completion Definition, Document Map (+10 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - ".attempt_entry"
Cohesion: 0.09
Nodes (23): _age_seconds(), Any, date, datetime, Full entry flow from eligibility checks through entry fill., Fetch today's 1-min bars from Schwab and run BiasScoreFilter., Parse Schwab chain response into OptionQuote objects., Fetch today's 1-min bars from Schwab and run BiasScoreFilter. (+15 more)

### Community 96 - "RegimeFilter"
Cohesion: 0.27
Nodes (6): datetime, Intraday VIX regime filter — skips entry when volatility is too elevated., Filter entries based on intraday VIX level at the time of entry., Most recent VIX bar close at or before entry_ts. None if no bars., True = safe to trade. False = skip (VIX too high). Returns True if no VIX bars…, RegimeFilter

### Community 97 - "performance_chart.py"
Cohesion: 0.15
Nodes (24): compute_stats(), cumulative_equity(), drawdown_series(), DrawdownPoint, ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png() (+16 more)

### Community 98 - "ButterflyOrderBuilder"
Cohesion: 0.13
Nodes (22): ButterflyOrderBuilder, Any, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check… (+14 more)

### Community 99 - "test_candidate_variants.py"
Cohesion: 0.42
Nodes (9): _candidate(), _config(), MonkeyPatch, _state(), test_absolute_stop_truncates_never_profitable_loss(), test_gap_conviction_threshold_is_wired_into_candidate_evaluator(), test_peak_trailer_retains_winner_that_profitprotector_floors(), test_target_cost_prefers_debit_target_instead_of_best_rr() (+1 more)

### Community 100 - "_asset_drawdowns"
Cohesion: 0.22
Nodes (9): _asset_drawdowns(), backtest_entry_price(), _parse_config_time(), Paper entry at mark plus optional stress slippage and commission., Entry fill price with slippage and paper commission (matches live OrderManager)., Shared live/backtest parity fields from runtime config., Parity fields, allowing CLI sweeps to override exit-arm knobs., Return live morning/late/afternoon drawdown thresholds. (+1 more)

### Community 101 - "FakeProvider"
Cohesion: 0.42
Nodes (6): candidate(), FakeProvider, market(), asyncio, test_candidate_entry_is_blocked_when_pin_fails(), test_candidate_entry_pins_before_mark_fill()

### Community 102 - "resolve_db_dsn"
Cohesion: 0.28
Nodes (8): Resolve the DB connection string for local backtests. Backtests follow the…, resolve_db_dsn(), asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), test_hypothetical_monitoring_load_uses_collector_only(), test_print_pnl_histogram_overlays_fitted_density(), test_resolve_db_dsn_falls_back_to_config(), test_resolve_db_dsn_uses_config_even_if_database_url_is_set()

### Community 103 - "select_cross_width_candidate"
Cohesion: 0.48
Nodes (6): Choose the final candidate from one best candidate per width. When…, select_cross_width_candidate(), _candidate(), test_cross_width_selection_can_prefer_first_bucket_width(), test_cross_width_selection_prefers_wider_wing_on_rr_tie(), test_cross_width_selection_returns_none_for_empty_pool()

### Community 104 - "_print_same_entry_comparison_table"
Cohesion: 0.33
Nodes (6): _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday, Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday…

### Community 105 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 106 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 107 - ".bulk_upsert"
Cohesion: 0.40
Nodes (3): Queries for decision_log table., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict., Return the last `days` daily closes in chronological order (oldest first).

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

### Community 127 - "_force_synthetic_for_date"
Cohesion: 0.18
Nodes (15): _fitted_density_counts(), _force_synthetic_for_date(), _print_pnl_histogram(), print_thinkback_checklist(), Patch load_chain_day to return None for `date`, forcing BS synthetic fallback.…, ASCII histogram with a fitted density curve overlaid on the trade buckets., Print a per-trade ToS ThinkBack validation checklist., Print a per-trade ToS ThinkBack validation checklist. (+7 more)

### Community 129 - "position_manager.py"
Cohesion: 0.15
Nodes (13): get_time_regime(), Current time in US/Pacific., Classify minutes since open into a named time regime., compute_tent_boundaries(), fly_bid_value(), _max_leg_spread_to_mark_ratio(), _quote_quality_ok(), Position value tracking and management. (+5 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 140 - "XSP Partial-Fill Evidence Plan"
Cohesion: 0.16
Nodes (13): code:bash (uv run python src/butterfly_guy/scripts/report_broker_order_), Completion, Controlled test, Current evidence, Decision, Done criteria, If one occurs naturally, Preconditions (+5 more)

### Community 141 - "OrderManager"
Cohesion: 0.15
Nodes (19): now_utc(), AmbiguousOrderError, _fill_result(), OrderManager, Place one butterfly order at limit_price. Wait for fill; cancel if unfilled., Ignore collapsed post-close bids that no longer reflect mark at signal., Execute entry with price ladder: reprice from live mark each step,         step, Manages order execution with price ladder and fill monitoring. (+11 more)

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
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `position_manager.py`, `test_order_manager.py`, `run_single`, `test_position_manager.py`, `SnapshotIdentity`, `feed.py`, `trade_service.py`, `run_entry_analysis.py`, `.session_close`, `synthetic_chain.py`, `load_date_data`, `SyntheticChainGenerator`, `state_machine.py`, `test_candidate_snapshot.py`, `AtomicSnapshotStore`, `StrategySettings`, `ButterflyCandidate`, `SessionClose`, `DbDataLoader`, `test_candidate_provider.py`, `run_backtest_db.py`, `chain_cache.py`, `position_service.py`, `test_trade_service.py`, `ChainDay`, `report_exit_mark_parity.py`, `.attempt_entry`, `FakeProvider`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `run_paper_replay.py`, `position_manager.py`, `test_order_manager.py`, `ButterflyChartSpec`, `run_single`, `test_position_manager.py`, `OrderManager`, `simulation_engine.py`, `trade_service.py`, `state_machine.py`, `CandidateEvaluator`, `StrategySettings`, `entry_loop`, `ButterflySelector`, `order_manager.py`, `GapRegimeFilter`, `run_backtest_db.py`, `position_service.py`, `parse_args`, `str`, `report_exit_mark_parity.py`, `.attempt_entry`, `ButterflyOrderBuilder`, `test_candidate_variants.py`, `FakeProvider`, `select_cross_width_candidate`, `test_candidate_settlement.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `time_utils.py`, `ExecutionSettings`, `order_manager.py`, `DatabasePool`, `test_order_manager.py`, `record_equity_market_data.py`, `universes.py`, `test_run_live.py`, `logging.py`, `OrderManager`, `position_service.py`, `run_morning_scan.py`, `str`, `load_config`, `services/daily_report_card.py`, `trade_service.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 120 inferred relationships involving `str` (e.g. with `.__init__()` and `._get_prev_close()`) actually correct?**
  _`str` has 120 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 31 INFERRED edges - model-reasoned connections that need verification._