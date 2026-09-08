# Graph Report - Butterflyguy  (2026-09-08)

## Corpus Check
- 277 files · ~326,926 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3884 nodes · 9381 edges · 219 communities (185 shown, 19 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 889 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `92942997`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- run_backtest_db.py
- trade_service.py
- test_order_manager.py
- RecordingGateway
- SnapshotIdentity
- trade_chart.py
- ShadowComparingMarketDataProvider
- ButterflyCandidate
- discover_options_strategy.py
- run_single
- test_run_live.py
- PositionService
- run_live.py
- CandidateRegistry
- forex_calendar.py
- test_candidate_evaluator_accounting.py
- BiasScoreFilter
- inspect_entry.py
- ShadowDiscrepancyRecorder
- DirectProvider
- test_equity_scan.py
- Enum
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- MarketSnapshot
- ReadOnlySchwabMarketDataClient
- schwab_gateway_session_soak.py
- test_chain_parser_parity.py
- schwab_gateway_v046_readiness_soak.py
- report_exit_mark_parity.py
- ProfitStateMachine
- test_risk_engine.py
- SyntheticChainGenerator
- news.py
- test_gateway_shadow_reads.py
- session_date
- run_morning_scan.py
- Current Schwab Integration
- SchwabClientWrapper
- report_broker_order_statuses.py
- Re-authorization checklist — Saturday 2026-08-22
- test_candidate_feed.py
- gateway_order_book.py
- test_schwab_gateway_session_soak.py
- SchwabDataLoader
- equity_trade_chart.py
- OptionQuote
- evaluator.py
- position_service.py
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- set_readiness
- load_config
- StrategySettings
- run_entry_analysis.py
- test_comparison_stats.py
- Schwab Gateway Migration Plan
- gateway_cutover_flatness_audit.py
- main
- RiskQueries
- Helios PAPER gateway cutover — 2026-08-25
- ._parse_chain_response
- ButterflyOrderBuilder
- universes.py
- NamedTuple
- DbDataLoader
- core/config.py
- Regime
- scanner.py
- is_market_open
- test_value_differences_are_classified_by_provable_freshness
- launch_schwab_gateway_session_soak_20260904.sh
- chain_cache.py
- Branch Review and Integration Plan
- notify.py
- Window A — Token re-authorization (mandatory)
- 1. Charles Schwab API
- DiscordNotifier
- test_daily_report_card.py
- weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- .monitor_loop
- 9) Capture equity candles and Level II for trade review
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- daily_report_card_config.py
- gateway-paper-cutover-handoff-prompt.md
- 2026-07-14 — data audit and research design
- Codex Project State
- Re-authorization checklist — Saturday 2026-08-15
- Capability recorder design
- run_classifier_sweep.py
- Schwab Single-Token Manager
- load_date_data
- Standalone SchwabGateway Extraction Plan
- JsonlStreamRecorder
- AtomicSnapshotStore
- performance_chart.py
- Option A deployment runbook — Helios, containerized
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- generate_live_performance.py
- Schwab Gateway Foundation: Local Run
- _assert_broker_state_matches_db
- MinuteBar
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
- send_test_chart.py
- test_candidate_settlement.py
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
- test_candidate_executor.py
- feed.py
- position_manager.py
- backfill_equity_candles.py
- test_candidate_snapshot.py
- report_selection_parity.py
- test_run_backtest_db.py
- Width Selection
- SchwabGateway option-chain latency investigation (2026-09-04)
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Schwab Gateway Multi-Consumer Foundation
- _compute_spread
- Window C — the two token writers resolved (2026-08-08)
- _reconstruct_surface_request
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- CandidateFeed
- launch_schwab_gateway_session_soak_20260901.sh
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- test_position_manager.py
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)
- SchwabGateway order books
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
- _HtmlTableParser
- SessionClose
- ChainDay
- run_equity_universe_refresh_cron.sh
- Layered Risk Management
- Geometric butterfly icon
- 7. Operational and observability data
- test_candidate_provider.py
- ButterflyGuy data sources — representative samples
- launch_schwab_gateway_readiness_soak_20260909.sh
- 3) Start the SPX stack in Docker
- .handler
- _MetricsHandler
- Offline safety-drill record — 2026-07-13
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- Critical External-Alert Delivery Proof - 2026-07-15
- XSP Flat-Runtime Restart Proof - 2026-07-14
- test_performance_dashboard.py
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
4. `AppConfig` - 64 edges
5. `MarketSnapshot` - 58 edges
6. `MinuteBar` - 55 edges
7. `DatabasePool` - 53 edges
8. `main()` - 50 edges
9. `load_config()` - 49 edges
10. `PositionService` - 49 edges

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

## Communities (219 total, 19 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.10
Nodes (35): _butterfly_value(), detect_complete_days(), _elapsed(), EntryDecision, _et(), get_prev_close(), get_vix(), load_bars_from_db() (+27 more)

### Community 1 - "run_backtest_db.py"
Cohesion: 0.11
Nodes (33): _asset_drawdowns(), _duration_min(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window(), _floatlist(), _format_et(), _intlist() (+25 more)

### Community 2 - "trade_service.py"
Cohesion: 0.06
Nodes (47): capped_entry_limit(), Return a cent-valid debit limit that never exceeds the configured maximum., _easter_sunday(), get_0dte_expiration(), get_us_market_early_closes(), get_us_market_holidays(), _last_weekday(), market_close_time() (+39 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.15
Nodes (58): LiveSpread, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread(), make_order_manager() (+50 more)

### Community 4 - "RecordingGateway"
Cohesion: 0.15
Nodes (19): ChainMetadataResponseV1, SpotResponseV1, chain_response(), ``extract_chain_metadata`` now tolerates a payload with no expiration maps (it…, Assert on what is handed to the logger, independent of any configured sink., An agreement must be observable; otherwise the ratio has no denominator., Stands in for GatewayMarketDataClient with a scripted spot/chain reply., RecordingGateway (+11 more)

### Community 5 - "SnapshotIdentity"
Cohesion: 0.10
Nodes (15): Paper-only SPX candidate fleet fed by a shared market-data service., Immutable normalized market snapshots shared by candidate evaluators., A long poll completed normally before a newer snapshot was published., SnapshotIdentity, SnapshotWaitTimeoutError, HttpMarketDataProvider, MarketDataProvider, AsyncClient (+7 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.10
Nodes (40): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+32 more)

### Community 7 - "ShadowComparingMarketDataProvider"
Cohesion: 0.14
Nodes (13): _error_code(), _mismatch_code(), _numbers_agree(), Any, date, Exception, Task, Classify a value difference by what the gateway could prove about its freshness. (+5 more)

### Community 8 - "ButterflyCandidate"
Cohesion: 0.12
Nodes (26): ButterflyCandidate, A butterfly spread candidate identified by the scanner., Butterfly selector — picks the best candidate from a list., Select the best butterfly candidate. When `target_center` is provided (derived…, Select the candidate whose cost is closest to its max_cost_per_width., EntrySelectionResult, build_entry_selection_parity(), _candidate_payload() (+18 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "run_single"
Cohesion: 0.12
Nodes (29): backtest_entry_price(), _dd_schedule_label(), _live_width_label(), load_asset_config(), load_monitoring_chains(), main(), merge_chains(), _patch_chain_cache() (+21 more)

### Community 11 - "test_run_live.py"
Cohesion: 0.13
Nodes (28): _close_runtime_resources(), install_shutdown_handler(), GatewayMarketDataClient, Task, Drain shadow work and close every owned resource, even if one close fails., Cancel the supervised loops on SIGTERM so main()'s cleanup block runs. The app…, asyncio, SIGTERM must unwind the TaskGroup without reporting a shutdown as an error. The… (+20 more)

### Community 12 - "PositionService"
Cohesion: 0.13
Nodes (35): A trade record for tracking entry/exit., TradeRecord, broker_cash_settlement_from_transactions(), BrokerCashSettlement, final_regular_session_close_from_candles(), PositionService, Any, NamedTuple (+27 more)

### Community 13 - "run_live.py"
Cohesion: 0.06
Nodes (54): BoundLogger, Pool, Schwab market-data client deliberately lacking every account/order operation., get_logger(), Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs., Get a structlog logger with optional name., setup_logging() (+46 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.11
Nodes (40): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+32 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.20
Nodes (10): candidate_fill_parity_failures(), Count mark_v1 rows whose fills disagree with their recorded evidence., _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_fill_parity_counts_entry_exit_mismatch_or_missing_evidence(), test_min_gap_filter_logs_no_trade_before_candidate_selection() (+2 more)

### Community 17 - "BiasScoreFilter"
Cohesion: 0.08
Nodes (19): BiasScoreFilter, High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Exponential moving average seeded with SMA of first `period` bars. Returns None…, Scores market direction using 4 signals; returns CALL, PUT, or None., Compute bias score from 4 signals: gap : +1 if entry_close > prev_close, -1 if…, Volume-weighted average price using close as typical price. Edge case: all…, make_bar(), make_pre_entry_bars() (+11 more)

### Community 18 - "inspect_entry.py"
Cohesion: 0.09
Nodes (25): DataFrame, CsvDataLoader, date, Path, CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day. (+17 more)

### Community 19 - "ShadowDiscrepancyRecorder"
Cohesion: 0.22
Nodes (5): GatewayMarketDataClient, A bounded, fixed-shape observation. Carries no payload, path, or exception text., Tally discrepancies over a fixed key space; retains no observed values., ShadowDiscrepancy, ShadowDiscrepancyRecorder

### Community 20 - "DirectProvider"
Cohesion: 0.15
Nodes (6): DirectProvider, FailingDirectProvider, date, The only source of returned values. Records every delegated call., A direct provider whose reads raise, to exercise the direct_unavailable path., test_get_option_chain_returns_before_a_slow_gateway_responds()

### Community 21 - "test_equity_scan.py"
Cohesion: 0.18
Nodes (30): EquityScanSettings, build_snapshots(), parse_equity_quote(), Normalize a Schwab quote payload into an EquitySnapshot., build_symbol_map(), Map each symbol to the universes it belongs to., _premarket_et(), asyncio (+22 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.09
Nodes (34): ProfitManagementStrategy, DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains., Runs full strategy on a single day using synthetic options., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. Skips… (+26 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.14
Nodes (34): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders(), detect_problems(), _extract_order_id() (+26 more)

### Community 25 - "report.py"
Cohesion: 0.14
Nodes (32): archive_report(), archive_report_json(), build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality() (+24 more)

### Community 26 - "MarketSnapshot"
Cohesion: 0.15
Nodes (9): _candidate_mark(), CandidatePaperExecutor, Any, Mark-price fills only; this object intentionally has no broker methods., _restore_trade(), _aware_utc(), MarketSnapshot, datetime (+1 more)

### Community 27 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.14
Nodes (20): Any, date, Prove the replacement credential with one bounded read-only Schwab call., Authenticate a Schwab client without resolving or retaining an account., Build one client with an isolated in-memory refresh-token callback., Validate and install a client built from a newly authorized token document., ReadOnlySchwabMarketDataClient, asyncio (+12 more)

### Community 28 - "schwab_gateway_session_soak.py"
Cohesion: 0.16
Nodes (38): background_context(), _confirm_surfaces(), _filtered_gateway_logs(), _finite(), _gateway_error_code(), _health(), health_violations(), ignored_freshness_difference_paths() (+30 more)

### Community 29 - "test_chain_parser_parity.py"
Cohesion: 0.13
Nodes (25): _contract(), _parse_rows(), Any, date, parametrize, Differential tests pinning the three Schwab option-chain parsers against each…, Run the live collector row parser without touching the database or Schwab., call + put contract counts equal the row count the collector writes. (+17 more)

### Community 30 - "schwab_gateway_v046_readiness_soak.py"
Cohesion: 0.15
Nodes (37): Client, Pattern, append_jsonl(), bounded_request(), candidate_observation(), diagnostic_probe(), docker_inspect(), endpoint_snapshot() (+29 more)

### Community 31 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

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
Cohesion: 0.16
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 36 - "test_gateway_shadow_reads.py"
Cohesion: 0.16
Nodes (18): Butterfly Guy's consumer-specific shadow-read integration., _comparisons(), _discrepancies(), asyncio, The shadow comparator must never change what the collector sees, on any path., Current value of one comparison counter; the child is created at zero if absent., A comparison that could not run is not evidence against the gateway., The default flag must leave the counters untouched, not merely unlogged. (+10 more)

### Community 37 - "session_date"
Cohesion: 0.16
Nodes (11): Calendar date for the US/Eastern trading session., session_date(), date, Record that a trade was executed., Record realized dollar PnL., Overwrite dollar realized_pnl in risk state (SET, not ADD). Used at startup to…, Manually sync the trade count in the risk state table. Used at startup to…, Check risk conditions before entry. Returns (allowed, reason). buying_power is… (+3 more)

### Community 38 - "run_morning_scan.py"
Cohesion: 0.09
Nodes (31): load_equity_scan_config(), Path, Load equity scan settings from YAML., attach_news_impacts(), parse_market_context(), Attach catalyst metadata without changing quote normalization., load_liquid_meta(), load_sector_map() (+23 more)

### Community 39 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 40 - "SchwabClientWrapper"
Cohesion: 0.05
Nodes (50): SchwabSettings, _creation_timestamp(), Any, date, Read the document's re-authorization marker. `creation_timestamp` changes only…, Authenticate and resolve account hash., Rebuild the client if the token document has been re-authorized. schwab-py…, Execute with exponential backoff retry. (+42 more)

### Community 41 - "report_broker_order_statuses.py"
Cohesion: 0.27
Nodes (14): _allowed_roots(), _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize() (+6 more)

### Community 42 - "Re-authorization checklist — Saturday 2026-08-22"
Cohesion: 0.18
Nodes (10): Preconditions — verified 2026-08-22T15:45:36Z, Re-authorization checklist — Saturday 2026-08-22, Step 1 — mint on zeus, in a real terminal, Step 2 — stage on Helios, verify byte-identical, Step 3 — move into place under the C1 lock, Step 4 — watch the reloads; restart only on a *confirmed* failure, Step 5 — verify, host against containers, Step 6 — record (+2 more)

### Community 43 - "test_candidate_feed.py"
Cohesion: 0.14
Nodes (13): FakeArchive, FakeDb, FakeMarket, FakePool, asyncio, date, MonkeyPatch, test_active_feed_fetches_chain_each_cycle_and_context_once_per_minute() (+5 more)

### Community 44 - "gateway_order_book.py"
Cohesion: 0.08
Nodes (35): ClientSession, field_validator, _Contract, GatewayOrderBookClient, _normalize_symbols(), _normalize_venue(), OrderBookAuthenticationError, OrderBookAuthorizationError (+27 more)

### Community 45 - "test_schwab_gateway_session_soak.py"
Cohesion: 0.10
Nodes (39): _chain(), _contract(), _gateway_error(), _log_entry(), _session_names(), test_adjudication_final_checkpoint_needs_post_close_probe(), test_adjudication_flaky_gateway_promotes_all_transients_to_gating(), test_adjudication_recovered_next_checkpoint_is_observation_not_gating() (+31 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.14
Nodes (11): date, Path, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day., Loads SPY 1-minute bars from Schwab, scaled to SPX price levels. Reuses the…, Fetch SPX daily open from yfinance for SPY→SPX calibration., Fetch VIX daily close from yfinance. (+3 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (31): rank_trades(), TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume() (+23 more)

### Community 48 - "OptionQuote"
Cohesion: 0.09
Nodes (31): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes(), fly_mark_value() (+23 more)

### Community 49 - "evaluator.py"
Cohesion: 0.07
Nodes (30): assert_candidate_safety(), candidate_performance_stats(), CandidateAuditContext, CandidateDecisionQueries, CandidateEvaluator, CandidatePerformanceStats, config_sha256(), Path (+22 more)

### Community 50 - "position_service.py"
Cohesion: 0.07
Nodes (43): entry_fill_within_limit(), Shared entry-price limit policy for production and candidate runtimes., Return whether an entry fill respects its hard debit ceiling., now_utc(), iter_chain_options(), date, Shared utilities for parsing Schwab option chain responses., Yield (strike, option_type, opt_dict) for each option matching the expiration.… (+35 more)

### Community 51 - "live_performance.py"
Cohesion: 0.15
Nodes (28): chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes(), equity_chart_description() (+20 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "set_readiness"
Cohesion: 0.15
Nodes (20): Add a not-ready reason; ``None`` explicitly resets all reasons., readiness_snapshot(), set_readiness(), broker_reconciler_loop(), BrokerStateGate, entry_loop(), Periodically attempt entries during the entry window., Pick up a re-authorized Schwab token without restarting the container. schwab-… (+12 more)

### Community 55 - "load_config"
Cohesion: 0.12
Nodes (22): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+14 more)

### Community 56 - "StrategySettings"
Cohesion: 0.16
Nodes (25): StrategySettings, find_entry_candidate(), Find best candidate in the 10:00–10:30 ET window, returning full decision…, ButterflyBuilder, Builds and scores butterfly spreads from an option chain snapshot., ButterflySelector, Selects the best butterfly candidate., make_chain() (+17 more)

### Community 57 - "run_entry_analysis.py"
Cohesion: 0.17
Nodes (24): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+16 more)

### Community 58 - "test_comparison_stats.py"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 59 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 60 - "gateway_cutover_flatness_audit.py"
Cohesion: 0.38
Nodes (8): _order(), test_redacted_audit_excludes_other_underlyings(), test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes(), test_redacted_audit_treats_replaced_as_historical_terminal(), main(), Any, Run a redacted, read-only ButterflyGuy cutover flatness audit., _redacted_order_audit()

### Community 61 - "main"
Cohesion: 0.26
Nodes (10): test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings(), main(), parse_report_date(), date, GatewayClientSettings, Path (+2 more)

### Community 62 - "RiskQueries"
Cohesion: 0.06
Nodes (15): OrderIntentQueries, Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Queries for durable broker order intents., Queries for daily_risk_state table., Dollar PnL for the rolling 7-day window (closed trades only). (+7 more)

### Community 63 - "Helios PAPER gateway cutover — 2026-08-25"
Cohesion: 0.29
Nodes (6): After-hours readiness condition, Helios PAPER gateway cutover — 2026-08-25, Immutable releases, Retained rollback images, Scope, Validation evidence

### Community 64 - "._parse_chain_response"
Cohesion: 0.40
Nodes (4): Any, date, datetime, Parse Schwab callExpDateMap/putExpDateMap into flat rows.

### Community 65 - "ButterflyOrderBuilder"
Cohesion: 0.14
Nodes (21): ButterflyOrderBuilder, Any, Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate. (+13 more)

### Community 66 - "universes.py"
Cohesion: 0.06
Nodes (66): _as_float(), _atomic_write_text(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols() (+58 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.15
Nodes (13): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+5 more)

### Community 69 - "core/config.py"
Cohesion: 0.08
Nodes (49): BaseSettings, AppConfig, CollectorSettings, ConfigModel, DatabaseSettings, EntrySettings, ExecutionSettings, MonitoringSettings (+41 more)

### Community 70 - "Regime"
Cohesion: 0.14
Nodes (13): Maps Regime → SimulationParams for use with simulate_day_adaptive(). Per-regime…, RegimeDispatch, GapRegimeFilter, Enum, Market regime classifier for 0-DTE butterfly parameter dispatch. Classifies…, Regime, str, Unit tests for GapRegimeFilter.apply(). (+5 more)

### Community 71 - "scanner.py"
Cohesion: 0.15
Nodes (27): is_premarket_window(), True during weekday premarket (default 4:00–9:30 AM ET)., _as_float(), _as_int(), EquitySnapshot, filter_movers(), _focus_reasons(), MarketContext (+19 more)

### Community 72 - "is_market_open"
Cohesion: 0.15
Nodes (22): is_market_open(), is_trading_day(), Check if the market is currently open., Check if a given date is a trading day (weekday, not a holiday)., Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Main collector loop — runs while market is open., et(), datetime (+14 more)

### Community 73 - "test_value_differences_are_classified_by_provable_freshness"
Cohesion: 0.40
Nodes (6): Exception, parametrize, test_direct_result_is_unchanged_when_the_gateway_errors(), test_gateway_errors_are_classified_by_fixed_code(), test_shadow_provider_canonicalizes_chain_metadata_symbol_at_client_boundary(), test_value_differences_are_classified_by_provable_freshness()

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 75 - "chain_cache.py"
Cohesion: 0.23
Nodes (15): chain_cache_path(), load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->… (+7 more)

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.09
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 77 - "notify.py"
Cohesion: 0.33
Nodes (4): Lightweight Telegram and ButterflyGuy Alertmanager helpers. Usage: from…, Send a Telegram message. Returns True on success, False on failure., send(), Keep the Schwab OAuth token alive and alert before refresh token expiry. Schwab…

### Community 78 - "Window A — Token re-authorization (mandatory)"
Cohesion: 0.10
Nodes (20): A0 — Snapshot (read-only), A1 — Disable the keepalive, A2 — Stop the three trading services, A3 — Re-authorize, A4 — Verify the new document, A5 — Start the three services, A6 — Restore the keepalive, A7 — Verify (+12 more)

### Community 79 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 80 - "DiscordNotifier"
Cohesion: 0.06
Nodes (29): Post one stable, identifier-free alert fingerprint to Alertmanager., send_alertmanager(), AlertmanagerNotifier, DiscordNotifier, date, Sends centrally deduplicated critical alerts through Alertmanager., Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook. (+21 more)

### Community 81 - "test_daily_report_card.py"
Cohesion: 0.16
Nodes (17): parse_trade_transactions(), Parse TRADE transactions into round-trip realized P&L., candles_to_series(), date, Tests for daily report card parsing and formatting., Without positionEffect, falls back to per-transaction P&L (e.g. options)., test_build_equity_trade_chart_png_returns_png_bytes(), test_chartable_equity_trades_skips_options() (+9 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.11
Nodes (43): trade_point_from_row(), TradePoint, build_combined_performance_chart_png(), Build one image with weekly, monthly, and all-time equity + drawdown panels., build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades() (+35 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - ".monitor_loop"
Cohesion: 0.15
Nodes (12): _chain_spot_price(), date, datetime, RuntimeError, Monitor position every 2s, evaluate state machine, trigger exit if needed., Raised when an open trade cannot be valued safely after market close., Use Schwab's final regular-session 1-minute close for cash settlement., Send full-session EOD charts for closed trades after market close. (+4 more)

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
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 91 - "daily_report_card_config.py"
Cohesion: 0.33
Nodes (5): load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds

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

### Community 98 - "run_classifier_sweep.py"
Cohesion: 0.15
Nodes (21): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), _print_comparison_table(), _print_same_entry_comparison_table() (+13 more)

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "load_date_data"
Cohesion: 0.16
Nodes (22): discover_dates(), _force_synthetic_for_date(), get_prev_close(), get_recent_closes(), get_vix_at(), get_vix_prev_close(), get_vix_snapshot_at(), load_bars_from_db() (+14 more)

### Community 101 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.10
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 102 - "JsonlStreamRecorder"
Cohesion: 0.12
Nodes (22): JsonlStreamRecorder, date, datetime, Event, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session. (+14 more)

### Community 103 - "AtomicSnapshotStore"
Cohesion: 0.16
Nodes (9): AtomicSnapshotStore, Condition-guarded pointer swap; readers never observe partial snapshots., SnapshotArchive, No complete snapshot is currently available., SnapshotUnavailableError, main(), Run the demand-aware shared SPX candidate market-data feed., Pick up a re-authorized token while retaining a working client on failure. (+1 more)

### Community 104 - "performance_chart.py"
Cohesion: 0.19
Nodes (17): compute_stats(), ReportStats, build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels(), Axes (+9 more)

### Community 105 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.14
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 106 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.17
Nodes (12): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding (+4 more)

### Community 107 - "generate_live_performance.py"
Cohesion: 0.23
Nodes (15): no_trade_reason(), NoTradeDay, render_placeholder_html(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate(), main() (+7 more)

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 109 - "_assert_broker_state_matches_db"
Cohesion: 0.15
Nodes (30): _assert_broker_state_matches_db(), _broker_option_positions(), _expired_trade_has_broker_settlement(), _explicit_fill_details(), _intent_order_ids(), _json_dict(), _matches_underlying(), _open_trade_positions() (+22 more)

### Community 110 - "MinuteBar"
Cohesion: 0.11
Nodes (23): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), DayData, MinuteBar (+15 more)

### Community 111 - "health_monitor.py"
Cohesion: 0.17
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
Cohesion: 0.19
Nodes (13): PriceHistoryProvider, archive_report(), date, Path, chartable_equity_trades(), format_equity_trade_chart_caption(), date, datetime (+5 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "test_live_performance_report.py"
Cohesion: 0.17
Nodes (14): date, Tests for live performance report generation., Per-run data must stay in the non-executable JSON block. The published page's…, test_chart_payload_includes_drawdown_fields(), test_compute_stats(), test_is_drawdown_exit(), test_no_trade_reason_mapping(), test_performance_report_shows_entire_history_and_fill_model_cohorts() (+6 more)

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
Cohesion: 0.36
Nodes (5): fake_db(), FakeConnection, asyncio, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 125 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 126 - "send_test_chart.py"
Cohesion: 0.27
Nodes (9): trade_pnl_dollars(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles() (+1 more)

### Community 127 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

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
Cohesion: 0.33
Nodes (9): async_main(), _install_signal_handlers(), main(), parse_args(), Event, Namespace, Path, Record raw Schwab equity chart, Level I, and Level II stream messages. (+1 more)

### Community 137 - "GatewayAuthoritativeMarketDataProvider"
Cohesion: 0.05
Nodes (60): DirectSchwabMarketDataProvider, _finite_number(), GatewayAuthoritativeMarketDataProvider, GatewayMarketDataError, _nonnegative_integer(), _now_eastern(), _optional_number(), Any (+52 more)

### Community 138 - "test_candidate_executor.py"
Cohesion: 0.44
Nodes (7): candidate(), FakeProvider, market(), asyncio, test_candidate_entry_blocks_fill_above_configured_width_maximum(), test_candidate_entry_is_blocked_when_pin_fails(), test_candidate_entry_pins_before_mark_fill()

### Community 139 - "feed.py"
Cohesion: 0.35
Nodes (16): Application, Request, _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs() (+8 more)

### Community 140 - "position_manager.py"
Cohesion: 0.28
Nodes (5): PositionManager, _quote_quality_ok(), Position value tracking and management., Tracks position value from chain data and manages peak tracking., Reset for a new position. Optionally restore a persisted peak (e.g. after…

### Community 141 - "backfill_equity_candles.py"
Cohesion: 0.43
Nodes (7): async_main(), main(), parse_args(), Namespace, Path, Backfill one session of one-minute equity candles from Schwab., run()

### Community 142 - "test_candidate_snapshot.py"
Cohesion: 0.26
Nodes (12): StaleSnapshotError, asyncio, datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry(), test_long_poll_never_replays_same_sequence() (+4 more)

### Community 143 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run…, run()

### Community 144 - "test_run_backtest_db.py"
Cohesion: 0.24
Nodes (9): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), test_fitted_density_counts_returns_bucket_heights(), test_hypothetical_monitoring_load_uses_collector_only() (+1 more)

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 146 - "SchwabGateway option-chain latency investigation (2026-09-04)"
Cohesion: 0.29
Nodes (6): Cache TTL is hard-capped at 4s in code, not just config, Chain size correlation, Recommendation, Request path (cache miss), SchwabGateway option-chain latency investigation (2026-09-04), Where the time actually goes: scheduler queueing, not the Schwab call itself

### Community 147 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 148 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 149 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 150 - "_compute_spread"
Cohesion: 0.67
Nodes (3): _compute_spread(), LiveSpread, NamedTuple

### Community 151 - "Window C — the two token writers resolved (2026-08-08)"
Cohesion: 0.25
Nodes (8): C1 — the operator chose the shared lock, C3 plan produced, and a stale design point corrected, Durability decided, monitoring still open, Housekeeping, Multi-consumer shape — confirmed sound, with two wrinkles, Proven on the host by the production path, at zero extra token writes, Still open, Window C — the two token writers resolved (2026-08-08)

### Community 152 - "_reconstruct_surface_request"
Cohesion: 0.67
Nodes (3): test_reconstruct_surface_request_round_trips_every_surface(), Rebuild the request tuple for a checkpoint surface name (post-close probe)., _reconstruct_surface_request()

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

### Community 158 - "test_position_manager.py"
Cohesion: 0.26
Nodes (13): PeakTrackingSettings, fly_settlement_value(), Butterfly cash-settlement value from the underlying index close., make_candidate(), make_quote(), make_xsp_candidate(), quote_map(), Tests for butterfly position valuation helpers. (+5 more)

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

### Community 166 - "test_run_backtest_db_defaults.py"
Cohesion: 0.21
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

### Community 177 - "_HtmlTableParser"
Cohesion: 0.29
Nodes (3): HTMLParser, _HtmlTableParser, Collect text cells from HTML tables without depending on tag attributes.

### Community 179 - "SessionClose"
Cohesion: 0.12
Nodes (11): Persist once and return the canonical evidence for this session., Any, RuntimeError, Auditable final regular-session SPX close supplied by the shared feed., No verified final regular-session close is available from the shared feed., SessionClose, SessionCloseUnavailableError, date (+3 more)

### Community 180 - "ChainDay"
Cohesion: 0.29
Nodes (9): dict, ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log…, day_with_monitoring_bars(), Add live monitor timestamps to bar iteration while carrying nearest spot…, _bar(), datetime, test_day_with_monitoring_bars_adds_live_poll_timestamps() (+1 more)

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (9): High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy (+1 more)

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 185 - "7. Operational and observability data"
Cohesion: 0.50
Nodes (4): 7.1 Prometheus metrics, 7.2 Health and readiness endpoints, 7.3 Structured application logs, 7. Operational and observability data

### Community 186 - "test_candidate_provider.py"
Cohesion: 0.33
Nodes (10): make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close(), test_http_and_schwab_provider_contracts_normalize_equally(), test_http_provider_fails_closed_on_mismatched_session_close() (+2 more)

### Community 187 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 188 - "launch_schwab_gateway_readiness_soak_20260909.sh"
Cohesion: 0.20
Nodes (10): die(), EVIDENCE_DIR, LAUNCHER, LOG, MONITOR, SESSION_DATE, launch_schwab_gateway_readiness_soak_20260909.sh script, TARGET_EPOCH (+2 more)

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - ".handler"
Cohesion: 0.29
Nodes (9): Any, Build a synchronous schwab-py handler that never blocks the stream., asyncio, parametrize, test_request_classifies_bare_504_without_error_body(), test_request_classifies_gateway_040_error_codes(), test_request_retry_does_not_retry_authorization_failure(), test_request_retry_keeps_persistent_server_error_gating() (+1 more)

### Community 194 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

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

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **546 isolated node(s):** `butterfly-guy`, `SESSION_DATE`, `TARGET_EPOCH`, `TOOL_DIR`, `MONITOR` (+541 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1406 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `trade_service.py`, `universes.py`, `run_morning_scan.py`, `record_equity_market_data.py`, `GatewayAuthoritativeMarketDataProvider`, `report_broker_order_statuses.py`, `test_run_live.py`, `PositionService`, `run_live.py`, `backfill_equity_candles.py`, `_assert_broker_state_matches_db`, `evaluator.py`, `position_service.py`, `services/daily_report_card.py`, `set_readiness`, `gateway_cutover_flatness_audit.py`, `main`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `run_backtest_db.py`, `trade_service.py`, `test_order_manager.py`, `SnapshotIdentity`, `ButterflyCandidate`, `run_single`, `feed.py`, `position_manager.py`, `PositionService`, `test_candidate_executor.py`, `test_candidate_snapshot.py`, `inspect_entry.py`, `_compute_spread`, `MarketSnapshot`, `CandidateFeed`, `test_position_manager.py`, `report_exit_mark_parity.py`, `SyntheticChainGenerator`, `position_service.py`, `SessionClose`, `ChainDay`, `StrategySettings`, `run_entry_analysis.py`, `test_candidate_provider.py`, `DbDataLoader`, `core/config.py`, `chain_cache.py`, `.monitor_loop`, `load_date_data`, `AtomicSnapshotStore`, `MinuteBar`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `run_paper_replay.py`, `run_backtest_db.py`, `trade_service.py`, `test_order_manager.py`, `test_candidate_executor.py`, `position_manager.py`, `run_live.py`, `PositionService`, `inspect_entry.py`, `_compute_spread`, `simulation_engine.py`, `MarketSnapshot`, `test_position_manager.py`, `ProfitStateMachine`, `test_run_backtest_db_defaults.py`, `OptionQuote`, `evaluator.py`, `position_service.py`, `set_readiness`, `StrategySettings`, `ButterflyOrderBuilder`, `.monitor_loop`, `test_candidate_settlement.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `ButterflyCandidate` (e.g. with `SimulationEngine` and `_candidate_mark()`) actually correct?**
  _`ButterflyCandidate` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `SchwabClientWrapper` (e.g. with `DirectSchwabMarketDataProvider` and `SchwabSettings`) actually correct?**
  _`SchwabClientWrapper` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `OptionQuote` (e.g. with `nearest_snapshot()` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 31 INFERRED edges - model-reasoned connections that need verification._