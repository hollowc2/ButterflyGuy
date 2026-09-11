# Graph Report - Butterflyguy  (2026-09-11)

## Corpus Check
- 280 files · ~328,131 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4042 nodes · 9687 edges · 223 communities (180 shown, 28 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 1028 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `78fd49c1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- chain_cache.py
- is_market_open
- test_order_manager.py
- test_gateway_shadow_reads.py
- logging.py
- trade_chart.py
- ShadowComparingMarketDataProvider
- .monitor_loop
- discover_options_strategy.py
- DatabasePool
- main
- ReadOnlySchwabMarketDataClient
- CandidateEvaluator
- CandidateRegistry
- forex_calendar.py
- Schwab Gateway Credential Proof
- SimulationEngine
- CsvDataLoader
- ShadowDiscrepancyRecorder
- DirectProvider
- test_equity_scan.py
- Enum
- MarketSnapshot
- reports/daily_report_card.py
- report.py
- time_utils.py
- test_schwab_client.py
- schwab_gateway_session_soak.py
- test_chain_parser_parity.py
- schwab_gateway_v046_readiness_soak.py
- report_exit_mark_parity.py
- ProfitStateMachine
- test_risk_engine.py
- SchwabDataLoader
- news.py
- gateway_client/__init__.py
- simulation_engine.py
- run_morning_scan.py
- Codex Project State
- run_live.py
- report_broker_order_statuses.py
- Schwab Gateway Migration Plan
- LeaseRegistry
- ValueError
- test_schwab_gateway_session_soak.py
- position_service.py
- equity_trade_chart.py
- ButterflyCandidate
- test_notifier.py
- order_manager.py
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- Window A — Token re-authorization (mandatory)
- load_config
- state_machine.py
- run_entry_analysis.py
- test_comparison_stats.py
- Current Schwab Integration
- build_daily_report_card
- Standalone SchwabGateway Extraction Plan
- test_candidate_provider.py
- session_date
- SchwabClientWrapper
- ButterflyOrderBuilder
- universes.py
- NamedTuple
- DbDataLoader
- DiscordNotifier
- trade_service.py
- scanner.py
- ._retry
- AppConfig
- launch_schwab_gateway_session_soak_20260904.sh
- core/config.py
- Branch Review and Integration Plan
- test_candidate_settlement.py
- test_collector.py
- 1. Charles Schwab API
- test_schwab_token_keepalive.py
- test_daily_report_card.py
- weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- main
- 9) Capture equity candles and Level II for trade review
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- send_test_chart.py
- test_position_manager.py
- 2026-07-14 — data audit and research design
- Re-authorization checklist — Saturday 2026-08-15
- .collect_snapshot
- Capability recorder design
- synthetic_chain.py
- Option A deployment runbook — Helios, containerized
- run_backtest_db.py
- test_candidate_variants.py
- rows_to_option_quotes
- Reducing the weekly re-authorization cost — a scoping question
- performance_chart.py
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- backfill_equity_candles.py
- generate_live_performance.py
- CandidatePaperExecutor
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
- test_gateway_option_chain_ttl_recommendation.py
- C3 — wiring shadow reads into `run_live.py`
- Schwab gateway deployment options
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- SchwabGateway option-chain latency investigation (2026-09-04)
- TradeQueries
- SchwabGateway order-book release full-session acceptance — 2026-09-01
- report_selection_parity.py
- Schwab gateway current status
- test_gateway_compose.py
- Schwab Gateway Foundation Smoke Test
- Schwab Single-Token Manager
- Window C — the two token writers resolved (2026-08-08)
- Strategy Settings
- record_equity_market_data.py
- GatewayAuthoritativeMarketDataProvider
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- .handler
- providers.py
- gateway_cutover_flatness_audit.py
- SessionClose
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Width Selection
- notifier.py
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- Schwab Gateway Multi-Consumer Foundation
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- test_gateway_phase7_boundaries.py
- Helios PAPER gateway cutover — 2026-08-25
- .write_until_stopped
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- feed.py
- Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)
- launch_schwab_gateway_session_soak_20260901.sh
- Bounded proof failure codes and a settled restoration error window — 2026-08-06
- Credential proof passed — 2026-08-06
- Schwab Gateway Foundation: Local Run
- test_no_unbounded_detail_reaches_the_logs
- SchwabGateway order books
- ButterflyGuy data sources and data types
- Equity candles and order-book recording
- resolve_wing_widths_for_vix
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
- test_get_spot_price_returns_before_a_slow_gateway_responds
- run_equity_universe_refresh_cron.sh
- Layered Risk Management
- Geometric butterfly icon
- test_discrepancy_metric_labels_cover_every_declared_code
- 7. Operational and observability data
- validate_chain
- ButterflyGuy data sources — representative samples
- preopen_endpoint_violations
- 3) Start the SPX stack in Docker
- test_request_classifies_gateway_040_error_codes
- _MetricsHandler
- test_get_option_chain_returns_before_a_slow_gateway_responds
- MinuteBar
- Offline safety-drill record — 2026-07-13
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- Critical External-Alert Delivery Proof - 2026-07-15
- XSP Flat-Runtime Restart Proof - 2026-07-14
- test_performance_dashboard.py
- auth_init.py
- ignored_freshness_difference_paths
- test_run_scan_skips_market_holiday_before_schwab
- butterfly_guy/__init__.py
- equity_scan/__init__.py
- reports/__init__.py
- run_live_performance_cron.sh
- run_morning_scan_cron.sh
- Compare Real vs Synthetic Chains
- StrategySettings
- butterfly-guy

## God Nodes (most connected - your core abstractions)
1. `ButterflyCandidate` - 91 edges
2. `OptionQuote` - 83 edges
3. `SchwabClientWrapper` - 83 edges
4. `AppConfig` - 66 edges
5. `MarketSnapshot` - 58 edges
6. `MinuteBar` - 56 edges
7. `main()` - 52 edges
8. `PositionService` - 52 edges
9. `DatabasePool` - 51 edges
10. `GatewayAuthoritativeMarketDataProvider` - 48 edges

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

## Communities (223 total, 28 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.10
Nodes (36): _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), get_prev_close(), get_vix(), LiveSpread (+28 more)

### Community 1 - "chain_cache.py"
Cohesion: 0.09
Nodes (26): chain_cache_path(), load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->… (+18 more)

### Community 2 - "is_market_open"
Cohesion: 0.14
Nodes (25): is_market_open(), is_trading_day(), minutes_to_close(), Check if the market is currently open., Check if a given date is a trading day (weekday, not a holiday)., Check if current time is within the given window (HH:MM strings)., Minutes remaining until market close., time_in_window() (+17 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.14
Nodes (60): LiveSpread, parse_broker_fill(), Return a validated net butterfly fill derived only from broker executions., broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi() (+52 more)

### Community 4 - "test_gateway_shadow_reads.py"
Cohesion: 0.13
Nodes (35): ChainMetadataResponseV1, SpotResponseV1, chain_response(), _comparisons(), _discrepancies(), asyncio, Exception, parametrize (+27 more)

### Community 5 - "logging.py"
Cohesion: 0.07
Nodes (35): BoundLogger, day_cache_path(), load_day(), _parse_bar(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day() (+27 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.09
Nodes (41): Send full-session EOD charts for closed trades after market close., build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series() (+33 more)

### Community 7 - "ShadowComparingMarketDataProvider"
Cohesion: 0.13
Nodes (13): _error_code(), _mismatch_code(), _numbers_agree(), Any, date, Exception, Task, Classify a value difference by what the gateway could prove about its freshness. (+5 more)

### Community 8 - ".monitor_loop"
Cohesion: 0.20
Nodes (8): _chain_spot_price(), date, datetime, RuntimeError, Monitor position every 2s, evaluate state machine, trigger exit if needed., Use Schwab's final regular-session 1-minute close for cash settlement., Record trade exit metrics and update risk engine., Persist the three live-polled legs so DB replay can match monitor timing.

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "DatabasePool"
Cohesion: 0.05
Nodes (40): Pool, assert_candidate_safety(), config_sha256(), Path, Prometheus metrics for monitoring., Start HTTP server serving /metrics (Prometheus) and /health on *port*. Runs in…, start_metrics_server(), DatabasePool (+32 more)

### Community 11 - "main"
Cohesion: 0.05
Nodes (56): broker_reconciler_loop(), BrokerStateGate, _build_collector_market_data(), _close_runtime_resources(), gateway_market_data_readiness_loop(), gateway_runtime_phase_delay(), install_shutdown_handler(), main() (+48 more)

### Community 12 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.11
Nodes (21): Any, date, Prove the replacement credential with one bounded read-only Schwab call., Authenticate a Schwab client without resolving or retaining an account., Build one client with an isolated in-memory refresh-token callback., Validate and install a client built from a newly authorized token document., ReadOnlySchwabMarketDataClient, asyncio (+13 more)

### Community 13 - "CandidateEvaluator"
Cohesion: 0.13
Nodes (15): candidate_fill_parity_failures(), candidate_performance_stats(), CandidateEvaluator, CandidatePerformanceStats, Summarize one chronological, closed mark_v1 PnL cohort., Count mark_v1 rows whose fills disagree with their recorded evidence., _gauge_value(), MetricsPool (+7 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.11
Nodes (39): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime(), RenderedRuntime (+31 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "Schwab Gateway Credential Proof"
Cohesion: 0.06
Nodes (34): Accepted runtime-baseline proof adapter, Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05 (+26 more)

### Community 17 - "SimulationEngine"
Cohesion: 0.11
Nodes (23): DayResult, datetime, Runs full strategy on a single day using synthetic options., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. Skips…, Classify regime then delegate to simulate_day() with matching params. Returns…, Paper trading commission: 4 legs × quantity × rate., Paper close fill at mark minus slippage and four-leg commission. (+15 more)

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
Cohesion: 0.18
Nodes (33): EquityScanSettings, build_snapshots(), parse_equity_quote(), passes_filters(), datetime, _quote_age_seconds(), rank_catalyst_watch(), rank_scan_results() (+25 more)

### Community 23 - "MarketSnapshot"
Cohesion: 0.06
Nodes (30): AtomicSnapshotStore, Condition-guarded pointer swap; readers never observe partial snapshots., Persist once and return the canonical evidence for this session., SnapshotArchive, Paper-only SPX candidate fleet fed by a shared market-data service., MarketSnapshot, datetime, RuntimeError (+22 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.19
Nodes (25): CashMovement, count_rejected_orders(), _extract_order_id(), _extract_trade_leg(), _float(), _instrument_label(), _is_currency_instrument(), _is_zero_dte_option() (+17 more)

### Community 25 - "report.py"
Cohesion: 0.13
Nodes (37): archive_report(), archive_report_json(), build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality() (+29 more)

### Community 26 - "time_utils.py"
Cohesion: 0.14
Nodes (25): Return one cached, verified final regular-session SPX close per date., _easter_sunday(), get_0dte_expiration(), get_us_market_early_closes(), get_us_market_holidays(), is_premarket_window(), _last_weekday(), market_close_time() (+17 more)

### Community 27 - "test_schwab_client.py"
Cohesion: 0.16
Nodes (25): _accessors(), factory(), _account_client(), asyncio, Initialize a wrapper against a real token file, returning its read/write funcs., Wire a wrapper whose _build_client hands out `clients` in order., An ordinary hourly refresh rewrites the document but must not rebuild the…, A bad document must leave the process on the credential that still works. (+17 more)

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
Cohesion: 0.17
Nodes (32): ProfitStateMachine, Evaluates position state and determines exit signals. States: - LOSS: position…, make_pos(), make_settings(), Tests for the profit management state machine., Pre-close exit remains available when explicitly configured., In profit tent with no drawdown → no exit., Should exit when in profit tent + 50% drawdown in morning. (+24 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SchwabDataLoader"
Cohesion: 0.14
Nodes (11): date, Path, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day., Loads SPY 1-minute bars from Schwab, scaled to SPX price levels. Reuses the…, Fetch SPX daily open from yfinance for SPY→SPX calibration., Fetch VIX daily close from yfinance. (+3 more)

### Community 35 - "news.py"
Cohesion: 0.16
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 37 - "simulation_engine.py"
Cohesion: 0.08
Nodes (32): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., sharpe(), win_pct(), Single-day simulation engine using synthetic option chains., Maps Regime → SimulationParams for use with simulate_day_adaptive(). Per-regime… (+24 more)

### Community 38 - "run_morning_scan.py"
Cohesion: 0.08
Nodes (35): Configure structlog with JSON output and correlation IDs., setup_logging(), load_equity_scan_config(), Path, Load equity scan settings from YAML., attach_news_impacts(), Attach catalyst metadata without changing quote normalization., load_sector_map() (+27 more)

### Community 39 - "Codex Project State"
Cohesion: 0.08
Nodes (24): C3 default-off deployment and gateway hardening (2026-08-10), Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z), Codex Project State, Current Phase, Current Slice, Current status — 2026-08-10 (+16 more)

### Community 40 - "run_live.py"
Cohesion: 0.15
Nodes (33): order_ids(), walk_orders(), _assert_broker_state_matches_db(), _broker_option_positions(), _expired_trade_has_broker_settlement(), _explicit_fill_details(), _intent_order_ids(), _json_dict() (+25 more)

### Community 41 - "report_broker_order_statuses.py"
Cohesion: 0.28
Nodes (14): _allowed_roots(), _build_payload(), main(), _order_symbols(), Any, Write a redacted read-only report of Schwab order statuses for one day., _status_category(), _summarize() (+6 more)

### Community 42 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 43 - "LeaseRegistry"
Cohesion: 0.09
Nodes (17): Lease, LeaseRegistry, datetime, LeaseKind, FakeArchive, FakeDb, FakeMarket, FakePool (+9 more)

### Community 44 - "ValueError"
Cohesion: 0.06
Nodes (43): ClientSession, field_validator, _aware_utc(), model_validator, model_validator, _Contract, GatewayOrderBookClient, _normalize_symbols() (+35 more)

### Community 45 - "test_schwab_gateway_session_soak.py"
Cohesion: 0.11
Nodes (32): _log_entry(), _session_names(), test_adjudication_final_checkpoint_needs_post_close_probe(), test_adjudication_flaky_gateway_promotes_all_transients_to_gating(), test_adjudication_recovered_next_checkpoint_is_observation_not_gating(), test_adjudication_recovered_queue_wait_timeout_is_observation(), test_adjudication_two_consecutive_checkpoints_is_gating(), test_adjudication_unrecovered_midsession_transient_stays_gating() (+24 more)

### Community 46 - "position_service.py"
Cohesion: 0.08
Nodes (52): clear_readiness(), Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., readiness_snapshot(), set_readiness(), A trade record for tracking entry/exit., TradeRecord, PositionQuotesUnavailableError (+44 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (31): rank_trades(), TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume() (+23 more)

### Community 48 - "ButterflyCandidate"
Cohesion: 0.05
Nodes (72): _candidate_mark(), Paper-only candidate evaluator built without broker execution dependencies., _restore_trade(), get_time_regime(), Classify minutes since open into a named time regime., ButterflyCandidate, fly_mark_value(), OptionQuote (+64 more)

### Community 49 - "test_notifier.py"
Cohesion: 0.16
Nodes (11): asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted(), send_alertmanager(), to_thread(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_alertmanager_payload_has_stable_redacted_fingerprint() (+3 more)

### Community 50 - "order_manager.py"
Cohesion: 0.09
Nodes (33): entry_fill_within_limit(), Shared entry-price limit policy for production and candidate runtimes., Return whether an entry fill respects its hard debit ceiling., now_utc(), AmbiguousOrderError, _assert_entry_fill_within_limit(), _broker_time(), BrokerFill (+25 more)

### Community 51 - "live_performance.py"
Cohesion: 0.09
Nodes (46): chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes(), equity_chart_description() (+38 more)

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
Nodes (22): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+14 more)

### Community 56 - "state_machine.py"
Cohesion: 0.12
Nodes (17): ProfitManagementStrategy, ProfitProtectorSettings, PositionState, Current state of an open position., effective_drawdown_threshold(), ProfitPolicyDecision, profitprotector_floor_decision(), Shared profit-management policy helpers for live trading and backtests. (+9 more)

### Community 57 - "run_entry_analysis.py"
Cohesion: 0.14
Nodes (27): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+19 more)

### Community 58 - "test_comparison_stats.py"
Cohesion: 0.57
Nodes (6): _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 59 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 60 - "build_daily_report_card"
Cohesion: 0.17
Nodes (14): AccountBalances, ActivitySummary, build_daily_report_card(), DailyReportCardSettings, load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card. (+6 more)

### Community 61 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.10
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 62 - "test_candidate_provider.py"
Cohesion: 0.25
Nodes (12): make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close(), test_http_and_schwab_provider_contracts_normalize_equally(), handler() (+4 more)

### Community 63 - "session_date"
Cohesion: 0.18
Nodes (10): Calendar date for the US/Eastern trading session., session_date(), date, Record that a trade was executed., Record realized dollar PnL., Overwrite dollar realized_pnl in risk state (SET, not ADD). Used at startup to…, Manually sync the trade count in the risk state table. Used at startup to…, daily_reset_loop() (+2 more)

### Community 64 - "SchwabClientWrapper"
Cohesion: 0.10
Nodes (15): _creation_timestamp(), Any, Read the document's re-authorization marker. `creation_timestamp` changes only…, Authenticate and resolve account hash., Rebuild the client if the token document has been re-authorized. schwab-py…, Place an order once and return the order ID. Order placement is not retried…, Get the status of an order., Fetch regular + extended quote fields for equities in batches. (+7 more)

### Community 65 - "ButterflyOrderBuilder"
Cohesion: 0.13
Nodes (22): ButterflyOrderBuilder, Any, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check… (+14 more)

### Community 66 - "universes.py"
Cohesion: 0.06
Nodes (65): _as_float(), _atomic_write_text(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols() (+57 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.14
Nodes (13): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+5 more)

### Community 69 - "DiscordNotifier"
Cohesion: 0.23
Nodes (4): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook.

### Community 70 - "trade_service.py"
Cohesion: 0.12
Nodes (18): capped_entry_limit(), Return a cent-valid debit limit that never exceeds the configured maximum., iter_chain_options(), date, Shared utilities for parsing Schwab option chain responses., Yield (strike, option_type, opt_dict) for each option matching the expiration.…, _age_seconds(), Any (+10 more)

### Community 71 - "scanner.py"
Cohesion: 0.23
Nodes (17): _as_float(), _as_int(), filter_movers(), _filter(), MarketContext, _mid_bid_ask(), _mover_change_pct(), _mover_symbol() (+9 more)

### Community 72 - "._retry"
Cohesion: 0.10
Nodes (11): date, Execute with exponential backoff retry., Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Cancel an existing order., Fetch 1-minute bars for today (and optionally prior days) from Schwab., Fetch 1-minute bars for one session., Fetch daily OHLCV bars for the given symbol. (+3 more)

### Community 73 - "AppConfig"
Cohesion: 0.15
Nodes (27): BaseSettings, AppConfig, ExecutionSettings, RiskSettings, SchwabSettings, _assert_live_config_supported(), Return the first regular-session open for the requested Eastern date., _session_open_from_intraday_candles() (+19 more)

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 75 - "core/config.py"
Cohesion: 0.18
Nodes (16): CollectorSettings, ConfigModel, EntrySettings, MonitoringSettings, PeakTrackingSettings, ProfitManagementSettings, BaseModel, QuoteQualitySettings (+8 more)

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.09
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 77 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 78 - "test_collector.py"
Cohesion: 0.21
Nodes (10): asyncio, Integration tests for the option chain collector (requires live Schwab token)., A local JSON cache failure should not fail a DB-backed snapshot., A corrupt optional chain cache should not fail a DB-backed snapshot., Collector should parse chain response into rows., Parsed rows should have the expected fields., test_collect_snapshot_parses_chain(), test_collect_snapshot_row_fields() (+2 more)

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
Nodes (39): build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_performance_caption(), format_review_header(), format_trade_recap() (+31 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "main"
Cohesion: 0.23
Nodes (10): test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings(), main(), parse_report_date(), date, GatewayClientSettings, Path (+2 more)

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
Cohesion: 0.27
Nodes (9): trade_pnl_dollars(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles() (+1 more)

### Community 93 - "test_position_manager.py"
Cohesion: 0.23
Nodes (13): fly_settlement_value(), Butterfly cash-settlement value from the underlying index close., make_candidate(), make_quote(), make_xsp_candidate(), parametrize, quote_map(), Tests for butterfly position valuation helpers. (+5 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "Re-authorization checklist — Saturday 2026-08-15"
Cohesion: 0.13
Nodes (14): Automated warnings before the cadence reset, Before you start, Expected result: no containers restarted, First, watch the reload do its job, Re-authorization checklist — Saturday 2026-08-15, Step 0 — already done, nothing to do, Step 1 — mint the token on zeus, in a real terminal, Step 2 — stage on Helios and verify byte-identical (+6 more)

### Community 96 - ".collect_snapshot"
Cohesion: 0.18
Nodes (7): Any, date, datetime, Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Fetch current chain and store snapshot. Returns row count., Main collector loop — runs while market is open., Parse Schwab callExpDateMap/putExpDateMap into flat rows.

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "synthetic_chain.py"
Cohesion: 0.05
Nodes (56): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+48 more)

### Community 99 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.14
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 100 - "run_backtest_db.py"
Cohesion: 0.05
Nodes (99): dict, ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log…, DrawdownWindow, _asset_drawdowns(), backtest_entry_price(), candidate_from_trade_row(), day_with_monitoring_bars() (+91 more)

### Community 101 - "test_candidate_variants.py"
Cohesion: 0.42
Nodes (9): _candidate(), _config(), MonkeyPatch, _state(), test_absolute_stop_truncates_never_profitable_loss(), test_gap_conviction_threshold_is_wired_into_candidate_evaluator(), test_peak_trailer_retains_winner_that_profitprotector_floors(), test_target_cost_prefers_debit_target_instead_of_best_rr() (+1 more)

### Community 102 - "rows_to_option_quotes"
Cohesion: 0.39
Nodes (7): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes()

### Community 103 - "Reducing the weekly re-authorization cost — a scoping question"
Cohesion: 0.15
Nodes (12): Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Production marker-change proof (2026-08-10), Recommendation, Reducing the weekly re-authorization cost — a scoping question, Stale-writer follow-up (2026-08-10), Status, The alternative worth costing first (+4 more)

### Community 104 - "performance_chart.py"
Cohesion: 0.16
Nodes (20): compute_stats(), ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels() (+12 more)

### Community 105 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.17
Nodes (12): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding (+4 more)

### Community 106 - "backfill_equity_candles.py"
Cohesion: 0.43
Nodes (7): async_main(), main(), parse_args(), Namespace, Path, Backfill one session of one-minute equity candles from Schwab., run()

### Community 107 - "generate_live_performance.py"
Cohesion: 0.23
Nodes (14): no_trade_reason(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate(), main(), parse_args(), Connection (+6 more)

### Community 108 - "CandidatePaperExecutor"
Cohesion: 0.17
Nodes (14): CandidateAuditContext, CandidateDecisionQueries, CandidatePaperExecutor, Any, Mark-price fills only; this object intentionally has no broker methods., candidate(), FakeProvider, market() (+6 more)

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
Cohesion: 0.19
Nodes (13): PriceHistoryProvider, archive_report(), date, Path, chartable_equity_trades(), format_equity_trade_chart_caption(), date, datetime (+5 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "launch_schwab_gateway_readiness_soak_20260909.sh"
Cohesion: 0.20
Nodes (10): die(), EVIDENCE_DIR, LAUNCHER, LOG, MONITOR, SESSION_DATE, launch_schwab_gateway_readiness_soak_20260909.sh script, TARGET_EPOCH (+2 more)

### Community 121 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (16): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+8 more)

### Community 122 - "test_gateway_option_chain_ttl_recommendation.py"
Cohesion: 0.29
Nodes (8): test_histogram_percentile_none_when_empty(), test_histogram_percentile_picks_first_bucket_meeting_target(), test_parse_histograms_empty_when_operation_missing(), test_parse_histograms_filters_by_operation(), Histogram, main(), parse_histograms(), Recommend a real SCHWAB_GATEWAY_OPTION_CHAIN_CACHE_TTL_SECONDS from live…

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

### Community 127 - "TradeQueries"
Cohesion: 0.06
Nodes (14): ChainQueries, OrderIntentQueries, Any, date, datetime, Queries for option_chain_snapshots table., Bulk insert option chain snapshot rows using COPY., Queries for trades table. (+6 more)

### Community 128 - "SchwabGateway order-book release full-session acceptance — 2026-09-01"
Cohesion: 0.20
Nodes (9): Credential lineage, EquityScanner coexistence boundary, Post-close decision, Prepared read-only tools, SchwabGateway order-book release full-session acceptance — 2026-09-01, Scope and freeze boundary, Start the full-session harness (unattended), Tuesday preflight — final gate at 06:20-06:29 PDT (+1 more)

### Community 129 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run…, run()

### Community 130 - "Schwab gateway current status"
Cohesion: 0.25
Nodes (6): Current state, Deferred Helios cleanup, Historical record, Runtime boundaries, Schwab gateway current status, Archived Schwab gateway transition records

### Community 131 - "test_gateway_compose.py"
Cohesion: 0.20
Nodes (7): Deployment boundaries retained after the standalone gateway extraction., All four trading services bind the token document from one required variable., Directory binds follow atomic token replacement to its new inode., A YAML token_path would override the deployment's shared token path., test_default_compose_binds_the_token_directory_never_the_document(), test_default_compose_token_binds_require_the_shared_token_directory(), test_live_configs_leave_token_path_to_the_environment()

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

### Community 136 - "record_equity_market_data.py"
Cohesion: 0.11
Nodes (29): JsonlStreamRecorder, date, datetime, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers., Return the stable output directory for one symbol and session., Write a deterministic JSON candle snapshot. (+21 more)

### Community 137 - "GatewayAuthoritativeMarketDataProvider"
Cohesion: 0.05
Nodes (67): SimpleNamespace, DirectSchwabMarketDataProvider, _finite_number(), GatewayAuthoritativeMarketDataProvider, GatewayMarketDataError, _nonnegative_integer(), _now_eastern(), _optional_number() (+59 more)

### Community 138 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.25
Nodes (8): Corrections to the Window G brief, End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, The fix, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)

### Community 140 - "providers.py"
Cohesion: 0.11
Nodes (19): OptionChainCollector, Option chain collector — fetches and stores SPX chain snapshots., Collects option chain snapshots at regular intervals., canonicalize_schwab_chain_symbol(), CollectorMarketDataProvider, EquityQuoteProvider, MarketMoversProvider, OptionChainProvider (+11 more)

### Community 141 - "gateway_cutover_flatness_audit.py"
Cohesion: 0.38
Nodes (8): _order(), test_redacted_audit_excludes_other_underlyings(), test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes(), test_redacted_audit_treats_replaced_as_historical_terminal(), main(), Any, Run a redacted, read-only ButterflyGuy cutover flatness audit., _redacted_order_audit()

### Community 142 - "SessionClose"
Cohesion: 0.15
Nodes (16): Any, Auditable final regular-session SPX close supplied by the shared feed., SessionClose, date, asyncio, datetime, quote(), snapshot() (+8 more)

### Community 143 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 144 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 146 - "notifier.py"
Cohesion: 0.12
Nodes (13): Lightweight Telegram and ButterflyGuy Alertmanager helpers. Usage: from…, Send a Telegram message. Returns True on success, False on failure., Post one stable, identifier-free alert fingerprint to Alertmanager., send(), send_alertmanager(), AlertmanagerNotifier, Trading and risk notifications., Sends centrally deduplicated critical alerts through Alertmanager. (+5 more)

### Community 147 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 148 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 149 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 150 - "test_gateway_phase7_boundaries.py"
Cohesion: 0.20
Nodes (8): asyncio, MonkeyPatch, Phase 7 boundaries after extracting the Schwab gateway from ButterflyGuy., _source(), test_compose_keeps_each_strategy_default_direct_with_staged_gateway_opt_in(), test_default_settings_construct_no_gateway_client(), test_shadow_failure_is_observed_without_changing_the_direct_result(), test_standalone_packages_remain_pinned_and_consumers_import_them_directly()

### Community 151 - "Helios PAPER gateway cutover — 2026-08-25"
Cohesion: 0.29
Nodes (6): After-hours readiness condition, Helios PAPER gateway cutover — 2026-08-25, Immutable releases, Retained rollback images, Scope, Validation evidence

### Community 153 - "Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)"
Cohesion: 0.33
Nodes (6): Correction to Window H part 1, Item 1 — the warnings now fire before the deadline (deployed), Item 3 built — the token reload (2026-08-09, NOT deployed), Item 3 — the deciding question is answered: the swap is safe, Window H correction — the restart arithmetic was wrong, and the gateway never needed restarting, Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)

### Community 154 - "feed.py"
Cohesion: 0.12
Nodes (30): Application, Request, _after_identity(), CandidateFeed, create_app(), _delete_lease(), _final_regular_session_close(), _float_query() (+22 more)

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

### Community 161 - "SchwabGateway order books"
Cohesion: 0.50
Nodes (3): Live WebSocket, Recent snapshots, SchwabGateway order books

### Community 162 - "ButterflyGuy data sources and data types"
Cohesion: 0.22
Nodes (8): 10. Repository evidence map, 4. Shared database tables visible to the same DB account, 6. Canonical and derived analytical data types, 8. Reports, archives, charts, and outbound destinations, 9. Practical limitations and safety notes, At a glance, ButterflyGuy data sources and data types, Synthetic option-chain data

### Community 163 - "Equity candles and order-book recording"
Cohesion: 0.33
Nodes (5): Backfill candles, Equity candles and order-book recording, Historical limitation, Operational caution, Record a future BMNR session

### Community 164 - "resolve_wing_widths_for_vix"
Cohesion: 0.40
Nodes (5): _bucket_sigmas(), Return sigma anchors spanning narrow to wide for the bucket size., Return (widths, sigma_fractions) for the active VIX bucket. Buckets are…, resolve_wing_widths_for_vix(), test_two_width_vix_bucket_spans_narrow_and_wide_sigmas()

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
Cohesion: 0.33
Nodes (3): HTMLParser, _HtmlTableParser, Collect text cells from HTML tables without depending on tag attributes.

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

### Community 190 - "preopen_endpoint_violations"
Cohesion: 0.31
Nodes (9): _endpoints(), MonkeyPatch, parametrize, test_preopen_accepts_retried_market_data_unavailable(), test_preopen_allows_documented_after_hours_strategy_readiness(), test_preopen_never_suppresses_other_endpoint_failures(), test_preopen_rejects_every_other_readiness_failure(), preopen_endpoint_violations() (+1 more)

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - "test_request_classifies_gateway_040_error_codes"
Cohesion: 0.16
Nodes (13): _gateway_error(), asyncio, parametrize, test_gateway_error_code_reads_only_the_discriminator(), test_request_classifies_bare_504_without_error_body(), test_request_classifies_gateway_040_error_codes(), handler(), test_request_retry_does_not_retry_authorization_failure() (+5 more)

### Community 194 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 198 - "MinuteBar"
Cohesion: 0.07
Nodes (27): MinuteBar, BiasScoreFilter, Multi-signal directional bias filter for 0-DTE butterfly entries., High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Exponential moving average seeded with SMA of first `period` bars. Returns None…, Scores market direction using 4 signals; returns CALL, PUT, or None., Compute bias score from 4 signals: gap : +1 if entry_close > prev_close, -1 if…, Volume-weighted average price using close as typical price. Edge case: all… (+19 more)

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

### Community 227 - "StrategySettings"
Cohesion: 0.15
Nodes (26): StrategySettings, find_entry_candidate(), Find best candidate in the 10:00–10:30 ET window, returning full decision…, ButterflyBuilder, O(N*W) butterfly construction and scoring engine., Builds and scores butterfly spreads from an option chain snapshot., ButterflySelector, Selects the best butterfly candidate. (+18 more)

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **554 isolated node(s):** `butterfly-guy`, `SESSION_DATE`, `TARGET_EPOCH`, `TOOL_DIR`, `MONITOR` (+549 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1492 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `record_equity_market_data.py`, `GatewayAuthoritativeMarketDataProvider`, `DatabasePool`, `main`, `providers.py`, `gateway_cutover_flatness_audit.py`, `test_schwab_client.py`, `run_morning_scan.py`, `run_live.py`, `report_broker_order_statuses.py`, `position_service.py`, `order_manager.py`, `universes.py`, `trade_service.py`, `._retry`, `AppConfig`, `main`, `backfill_equity_candles.py`, `services/daily_report_card.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `AppConfig` connect `AppConfig` to `run_backtest_db.py`, `test_candidate_variants.py`, `trade_service.py`, `run_live.py`, `DatabasePool`, `core/config.py`, `ValueError`, `CandidateEvaluator`, `CandidateRegistry`, `providers.py`, `ButterflyCandidate`, `position_service.py`, `test_collector.py`, `CandidatePaperExecutor`, `load_config`, `test_chain_parser_parity.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `get_logger()` connect `logging.py` to `run_paper_replay.py`, `DatabasePool`, `providers.py`, `notifier.py`, `feed.py`, `news.py`, `simulation_engine.py`, `run_morning_scan.py`, `run_live.py`, `position_service.py`, `ButterflyCandidate`, `order_manager.py`, `state_machine.py`, `run_entry_analysis.py`, `ButterflyOrderBuilder`, `universes.py`, `trade_service.py`, `MinuteBar`, `weekend_review.py`, `send_test_chart.py`, `StrategySettings`, `run_backtest_db.py`, `services/daily_report_card.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `ButterflyCandidate` (e.g. with `SimulationEngine` and `_candidate_mark()`) actually correct?**
  _`ButterflyCandidate` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `OptionQuote` (e.g. with `nearest_snapshot()` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `SchwabClientWrapper` (e.g. with `DirectSchwabMarketDataProvider` and `SchwabSettings`) actually correct?**
  _`SchwabClientWrapper` has 30 INFERRED edges - model-reasoned connections that need verification._