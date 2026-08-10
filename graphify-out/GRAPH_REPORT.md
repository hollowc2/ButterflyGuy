# Graph Report - Butterflyguy  (2026-08-10)

## Corpus Check
- 286 files · ~333,111 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4521 nodes · 12198 edges · 221 communities (202 shown, 19 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1056 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8d714710`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- token_manager.py
- .monitor_loop
- test_order_manager.py
- ShadowComparingMarketDataProvider
- GatewayMarketDataClient
- ButterflyChartSpec
- FakeAccessFunctionFactory
- ReadOnlySchwabMarketDataClient
- discover_options_strategy.py
- OptionQuote
- credential_proof_fingerprint.py
- 4. Detailed findings
- _Response
- CandidateRegistry
- forex_calendar.py
- run_single
- BiasScoreFilter
- CsvDataLoader
- run_schwab_gateway.py
- test_broker_order_intents.py
- test_equity_scan.py
- InternalKeyAuthenticator
- simulation_engine.py
- reports/daily_report_card.py
- report.py
- SnapshotIdentity
- StrategySettings
- upstream.py
- extract_chain_metadata
- GatewayClientSettings
- _approval_1_execute
- ProfitStateMachine
- test_risk_engine.py
- synthetic_chain.py
- news.py
- record_equity_market_data.py
- test_gateway_credential_probe.py
- performance_chart.py
- Current Schwab Integration
- run_classifier_sweep.py
- test_candidate_settlement.py
- api.py
- AtomicSnapshotStore
- DiscordNotifier
- test_schwab_token_keepalive.py
- MinuteBar
- equity_trade_chart.py
- AtomicFileTokenStore
- report_exit_mark_parity.py
- OperatorFailure
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- MonkeyPatch
- load_config
- test_candidate_evaluator_accounting.py
- time_utils.py
- test_comparison_stats.py
- Schwab Gateway Migration Plan
- Path
- create_app
- OrderIntentQueries
- Path
- ButterflyGuy Code Review State
- test_candidate_snapshot.py
- universes.py
- NamedTuple
- DbDataLoader
- SnapshotUnavailableError
- GapRegimeFilter
- scanner.py
- Any
- test_gateway_credential_proof_operator.py
- populated_state
- chain_cache.py
- Branch Review and Integration Plan
- run_morning_scan.py
- Window A — Token re-authorization (mandatory)
- 1. Charles Schwab API
- CaptureFixture
- test_daily_report_card.py
- weekend_review.py
- Architecture
- 3. ButterflyGuy-owned TimescaleDB data
- Options strategy discovery report
- LockedSchwabClientAdapter
- run_entry_analysis.py
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- schemas.py
- DatabasePool
- ._shadow_chain
- 2026-07-14 — data audit and research design
- Codex Project State
- Re-authorization checklist — Saturday 2026-08-15
- Capability recorder design
- SchwabClientWrapper
- Schwab Single-Token Manager
- XSP Opportunistic Partial-Fill Evidence Plan
- trade_service.py
- resolve_db_dsn
- redact
- test_gateway_issue_keys.py
- Option A deployment runbook — Helios, containerized
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- ButterflyGuy data sources — representative samples
- Schwab Gateway Foundation: Local Run
- run_live.py
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
- load_date_data
- Window D — the gateway made reachable, started, and watched (2026-08-08)
- test_run_migrations.py
- Schwab Gateway Foundation Smoke Test
- HttpMarketDataProvider
- TokenManagerState
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- Reducing the weekly re-authorization cost — a scoping question
- Schwab Gateway Credential Proof
- test_gateway_compose.py
- AppConfig
- C3 — wiring shadow reads into `run_live.py`
- Schwab gateway deployment options
- Strategy Settings
- generate_live_performance.py
- OptionChainProvider
- run_backtest_db.py
- daily_report_card_config.py
- prepare_args
- position_service.py
- ButterflyCandidate
- probe_schwab_gateway_credentials.py
- test_order_preview.py
- Width Selection
- Any
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Schwab Gateway Multi-Consumer Foundation
- MarketSnapshot
- Window C — the two token writers resolved (2026-08-08)
- 9) Capture equity candles and Level II for trade review
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- feed.py
- parse_args
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- SyntheticChainGenerator
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)
- _emit
- ButterflyGuy data sources and data types
- Equity candles and order-book recording
- Bounded proof failure codes and a settled restoration error window — 2026-08-06
- Credential proof passed — 2026-08-06
- _signal_spx
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
- _require_proof_credential_environment
- EntrySelectionResult
- SessionClose
- test_position_manager.py
- AlertmanagerNotifier
- Layered Risk Management
- Geometric butterfly icon
- select_entry_candidate
- 7. Operational and observability data
- ChainDay
- .collect_snapshot
- send_test_chart.py
- GatewayUpstreamSettings
- GatewaySettings
- 3) Start the SPX stack in Docker
- LockedSchwabMarketDataProvider
- Any
- _aware_utc
- test_order_builder.py
- _Session
- test_provider_exposes_only_the_three_read_surfaces
- test_performance_dashboard.py
- auth_init.py
- butterfly_guy/__init__.py
- equity_scan/__init__.py
- reports/__init__.py
- run_live_performance_cron.sh
- run_morning_scan_cron.sh
- Compare Real vs Synthetic Chains
- butterfly-guy

## God Nodes (most connected - your core abstractions)
1. `ButterflyCandidate` - 110 edges
2. `SchwabClientWrapper` - 102 edges
3. `OptionQuote` - 100 edges
4. `OperatorFailure` - 83 edges
5. `AppConfig` - 76 edges
6. `MinuteBar` - 67 edges
7. `MarketSnapshot` - 63 edges
8. `DatabasePool` - 59 edges
9. `SnapshotIdentity` - 52 edges
10. `BrokerStateGate` - 51 edges

## Surprising Connections (you probably didn't know these)
- `TestBiasScore` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestComputeOr` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestComputeVwap` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
- `TestEma` --uses--> `MinuteBar`  [INFERRED]
  tests/test_bias_filter.py → src/butterfly_guy/backtest/data_loader.py
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

## Communities (221 total, 19 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.11
Nodes (33): _butterfly_value(), detect_complete_days(), _elapsed(), _et(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db() (+25 more)

### Community 1 - "token_manager.py"
Cohesion: 0.05
Nodes (43): AbstractContextManager, RLock, _AtomicFileTokenTransaction, AtomicTokenManager, _fsync_directory(), Any, datetime, Enum (+35 more)

### Community 2 - ".monitor_loop"
Cohesion: 0.15
Nodes (10): _chain_spot_price(), date, datetime, RuntimeError, Monitor position every 2s, evaluate state machine, trigger exit if needed., Use Schwab's final regular-session 1-minute close for cash settlement., Record trade exit metrics and update risk engine., Send full-session EOD charts for closed trades after market close. (+2 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.14
Nodes (60): LiveSpread, parse_broker_fill(), NamedTuple, Return a validated net butterfly fill derived only from broker executions., broker_fill(), filled_order(), make_candidate(), make_chain_data() (+52 more)

### Community 4 - "ShadowComparingMarketDataProvider"
Cohesion: 0.09
Nodes (47): Return the direct read always; compare a gateway read alongside it when…, Wait for any in-flight shadow comparisons to finish. Not used on the…, ShadowComparingMarketDataProvider, chain_response(), _comparisons(), DirectProvider, _discrepancies(), asyncio (+39 more)

### Community 5 - "GatewayMarketDataClient"
Cohesion: 0.07
Nodes (62): Build a synchronous schwab-py handler that never blocks the stream., GatewayAuthenticationError, GatewayAuthorizationError, GatewayCapacityError, GatewayClientError, GatewayMarketDataClient, GatewayResponseError, GatewayTimeoutError (+54 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.10
Nodes (40): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+32 more)

### Community 7 - "FakeAccessFunctionFactory"
Cohesion: 0.24
Nodes (18): adapter(), FakeAccessFunctionFactory, FakeClient, manager(), Any, MonkeyPatch, Path, Mimic schwab-py 1.5.1 TokenMetadata wrapping without importing schwab. (+10 more)

### Community 8 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.08
Nodes (45): Any, date, Prove the replacement credential with one bounded read-only Schwab call., Authenticate a Schwab client without resolving or retaining an account., Build one client with an isolated in-memory refresh-token callback., Validate and install a client built from a newly authorized token document., ReadOnlySchwabMarketDataClient, SchwabSettings (+37 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "OptionQuote"
Cohesion: 0.08
Nodes (34): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes(), fly_mark_value() (+26 more)

### Community 11 - "credential_proof_fingerprint.py"
Cohesion: 0.11
Nodes (40): _accepted_fingerprint_hashes(), _accepted_snapshots(), _approved_staging_tmpfs(), _approved_tmpfs_entry(), _canonical_mount(), _canonical_ports(), _canonical_sort_key(), _compose_json() (+32 more)

### Community 12 - "4. Detailed findings"
Cohesion: 0.04
Nodes (45): 10. Refactoring roadmap, 11. Verification log, 1. Executive summary, 2. Architecture map, 3. Original audit findings summary, 4. Detailed findings, 5. Single-source-of-truth matrix, 6. Duplication map (+37 more)

### Community 13 - "_Response"
Cohesion: 0.26
Nodes (19): _FakeClient, _provider(), asyncio, Tests for the real Schwab provider bound to the locked token manager. No test…, Parsing runs outside the locked transaction, so a malformed payload must raise…, The direct path retries three times; inside a held token lock this one must not., Differential test pinning the known zero-price gap bug-for-bug. A legitimate…, Minimal stand-in for a schwab-py client. Exposes only read methods. (+11 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.12
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "run_single"
Cohesion: 0.14
Nodes (24): backtest_entry_price(), _dd_schedule_label(), _live_width_label(), load_asset_config(), load_live_trades(), main(), merge_chains(), _patch_chain_cache() (+16 more)

### Community 17 - "BiasScoreFilter"
Cohesion: 0.08
Nodes (19): BiasScoreFilter, High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Exponential moving average seeded with SMA of first `period` bars. Returns None…, Scores market direction using 4 signals; returns CALL, PUT, or None., Compute bias score from 4 signals: gap : +1 if entry_close > prev_close, -1 if…, Volume-weighted average price using close as typical price. Edge case: all…, make_bar(), make_pre_entry_bars() (+11 more)

### Community 18 - "CsvDataLoader"
Cohesion: 0.25
Nodes (8): DataFrame, CsvDataLoader, date, Path, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files…

### Community 19 - "run_schwab_gateway.py"
Cohesion: 0.18
Nodes (14): build_demo_app(), build_live_app(), build_parser(), DemoQuoteUpstream, main(), Any, Application, ArgumentParser (+6 more)

### Community 20 - "test_broker_order_intents.py"
Cohesion: 0.24
Nodes (16): broker_fill_payload(), asyncio, parametrize, test_broker_state_gate_records_unsafe_reason(), test_filled_entry_intent_rejects_wrong_broker_ratio(), test_filled_entry_intent_rejects_zero_quantity(), test_filled_entry_intent_repairs_open_trade_only_with_matching_legs_and_fill(), test_filled_exit_intent_repairs_open_trade_only_when_broker_flat() (+8 more)

### Community 21 - "test_equity_scan.py"
Cohesion: 0.17
Nodes (35): EquityScanSettings, build_snapshots(), parse_equity_quote(), passes_filters(), datetime, _quote_age_seconds(), rank_catalyst_watch(), rank_scan_results() (+27 more)

### Community 22 - "InternalKeyAuthenticator"
Cohesion: 0.08
Nodes (39): Enum, hash_api_key(), InternalKeyAuthenticator, InternalPrincipal, Path, Internal service authentication with hashed, capability-scoped API keys., build_keys_document(), generate_key() (+31 more)

### Community 23 - "simulation_engine.py"
Cohesion: 0.08
Nodes (39): ProfitManagementStrategy, DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains., Runs full strategy on a single day using synthetic options., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. Skips… (+31 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.13
Nodes (36): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders(), detect_problems(), _extract_order_id() (+28 more)

### Community 25 - "report.py"
Cohesion: 0.16
Nodes (31): archive_report_json(), build_report(), _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol() (+23 more)

### Community 26 - "SnapshotIdentity"
Cohesion: 0.12
Nodes (11): Paper-only SPX candidate fleet fed by a shared market-data service., Immutable normalized market snapshots shared by candidate evaluators., A long poll completed normally before a newer snapshot was published., SnapshotIdentity, SnapshotWaitTimeoutError, MarketDataProvider, Protocol, Market-data provider contract and shared-feed HTTP implementation. (+3 more)

### Community 27 - "StrategySettings"
Cohesion: 0.11
Nodes (37): StrategySettings, main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date. Replicates the…, EntryDecision, find_entry_candidate(), MonitorResult (+29 more)

### Community 28 - "upstream.py"
Cohesion: 0.07
Nodes (37): Transport-neutral client contracts for the internal Schwab gateway., ChainMetadataResponseV1, ChainMetadataV1, GatewayErrorDetailV1, GatewayErrorV1, GatewayHealthV1, GatewayModel, GatewayReadinessV1 (+29 more)

### Community 29 - "extract_chain_metadata"
Cohesion: 0.09
Nodes (41): iter_chain_options(), date, Shared utilities for parsing Schwab option chain responses., Yield (strike, option_type, opt_dict) for each option matching the expiration.…, ChainMetadataFields, _count_expiration(), _epoch_millis(), extract_chain_metadata() (+33 more)

### Community 30 - "GatewayClientSettings"
Cohesion: 0.16
Nodes (14): GatewayClientSettings, BaseSettings, model_validator, Opt-in client configuration; direct access remains the safe default., parametrize, settings(), test_gateway_client_mode_is_opt_in_and_secret_is_hidden(), test_gateway_client_mode_rejects_shadow_reads() (+6 more)

### Community 31 - "_approval_1_execute"
Cohesion: 0.12
Nodes (37): _approval_1_execute(), _approval_2_execute(), _best_effort_runtime_restore(), CapturedProcess, _cleanup_runtime_staging(), _compose_service_hash(), _container_is_stopped(), _docker_top_rows() (+29 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.10
Nodes (42): ProfitManagementSettings, QuoteQualitySettings, PositionState, Current state of an open position., ExitSignal, ProfitState, ProfitStateMachine, Enum (+34 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "synthetic_chain.py"
Cohesion: 0.07
Nodes (44): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+36 more)

### Community 35 - "news.py"
Cohesion: 0.16
Nodes (31): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+23 more)

### Community 36 - "record_equity_market_data.py"
Cohesion: 0.08
Nodes (39): JsonlStreamRecorder, Any, date, datetime, Event, Path, Persistence helpers for recorded equity candles and Schwab stream events., Write a run summary without exposing credentials or account identifiers. (+31 more)

### Community 37 - "test_gateway_credential_probe.py"
Cohesion: 0.10
Nodes (37): GatewayCredentialProbeSettings, Validated configuration for the isolated gateway process., Explicit real-credential inputs for the standalone quote proof only., Any, Read one public quote without resolving an account or exposing response data., run_gateway_credential_probe(), FakeClient, FakeFactory (+29 more)

### Community 38 - "performance_chart.py"
Cohesion: 0.19
Nodes (17): compute_stats(), ReportStats, build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels(), Axes (+9 more)

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
Nodes (25): audit_middleware(), chain_metadata(), _error(), health(), _json(), metrics(), _parse_expiration(), _parse_symbol() (+17 more)

### Community 43 - "AtomicSnapshotStore"
Cohesion: 0.11
Nodes (23): AtomicSnapshotStore, CandidateFeed, LeaseRegistry, Condition-guarded pointer swap; readers never observe partial snapshots., Persist once and return the canonical evidence for this session., SnapshotArchive, RuntimeError, No verified final regular-session close is available from the shared feed. (+15 more)

### Community 44 - "DiscordNotifier"
Cohesion: 0.14
Nodes (12): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook., asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted() (+4 more)

### Community 45 - "test_schwab_token_keepalive.py"
Cohesion: 0.16
Nodes (13): fixture, lock_events(), parametrize, SCHWAB_TOKEN_PATH overrides the default, process env winning over .env., Record lock acquire/release without touching a real lock file., Wire up the module-level environment the keepalive script reads on import., The refresh and the quote both happen while the gateway's lock is held. Schwab…, A busy lock fails loudly rather than writing alongside the other writer. (+5 more)

### Community 46 - "MinuteBar"
Cohesion: 0.07
Nodes (32): day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), CSV-based data loader for historical SPX + VIX 1-minute data. Reads two CSV…, DayData (+24 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (31): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+23 more)

### Community 48 - "AtomicFileTokenStore"
Cohesion: 0.11
Nodes (40): Re-prime a latched token manager from outside the request path. A token-level…, Return True when the manager is ready, recovering it first if it is not., Recover readiness forever, surviving any failure a single attempt can raise.…, TokenReadinessRecovery, AtomicFileTokenStore, One JSON token file protected by thread and process locks., _keys_file(), Any (+32 more)

### Community 49 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 50 - "OperatorFailure"
Cohesion: 0.11
Nodes (33): _accepted_runtime_baseline(), _arm_watchdog(), _baseline_candidate_status(), _best_effort_restore_cron(), _cancel_watchdog(), _cleanup_temporary_inputs(), _disable_keepalive_cron(), _emergency_restore_spx() (+25 more)

### Community 51 - "live_performance.py"
Cohesion: 0.17
Nodes (25): chart_payload(), cumulative_equity(), drawdown_series(), DrawdownPoint, duration_minutes(), format_et_time(), is_drawdown_exit(), _money() (+17 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.11
Nodes (17): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+9 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.17
Nodes (11): Active Work Item, Architecture Map, ButterflyGuy AI Review State, Current Objective, Historical Cycle Checkpoints, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules (+3 more)

### Community 54 - "MonkeyPatch"
Cohesion: 0.07
Nodes (39): MonkeyPatch, parametrize, The counted window must begin after resume, so the known burst is never counted., The operator account has no passwordless sudo on the non-interactive proof path., The container init is the app; a namespace-internal SIGSTOP to PID 1 is ignored., The probe must never suspend SPX during preflight., result(), test_approval_2_and_prepare_require_the_explicit_host_proof_inputs() (+31 more)

### Community 55 - "load_config"
Cohesion: 0.05
Nodes (57): load_config(), Path, Load configuration from YAML file and environment variables., walk_orders(), _build_payload(), main(), _order_symbols(), Any (+49 more)

### Community 56 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.20
Nodes (10): candidate_fill_parity_failures(), Count mark_v1 rows whose fills disagree with their recorded evidence., _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_fill_parity_counts_entry_exit_mismatch_or_missing_evidence(), test_min_gap_filter_logs_no_trade_before_candidate_selection() (+2 more)

### Community 57 - "time_utils.py"
Cohesion: 0.06
Nodes (63): _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_trading_day(), _last_weekday(), market_close_time(), minutes_since_open() (+55 more)

### Community 58 - "test_comparison_stats.py"
Cohesion: 0.46
Nodes (7): _print_comparison_table(), _capture(), _make_result(), Tests for _print_comparison_table aggregate stats., test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 59 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (22): Credential-proof gate, Current migration status, Dependency map, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison (+14 more)

### Community 60 - "Path"
Cohesion: 0.16
Nodes (29): _archive_member_sha256(), _capture_crontab(), _create_archive(), _host_reviewed_source_root(), _legacy_evidence_capture(), _prepare(), Path, Return an operator-named absolute host path, or fail with the caller's fixed… (+21 more)

### Community 61 - "create_app"
Cohesion: 0.28
Nodes (18): create_app(), Application, __getattr__(), Any, Import ``api`` lazily so the reviewed credential-proof subset loads standalone., authenticator(), FakeQuoteUpstream, FakeTokenReadinessProvider (+10 more)

### Community 62 - "OrderIntentQueries"
Cohesion: 0.06
Nodes (9): OrderIntentQueries, Any, date, datetime, Bulk insert option chain snapshot rows using COPY., Queries for durable broker order intents., Dollar PnL for the rolling 7-day window (closed trades only)., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict. (+1 more)

### Community 63 - "Path"
Cohesion: 0.12
Nodes (27): legacy_capture_args(), patch_legacy_capture_provenance(), Path, The manager creates its lock and atomic replacement beside the document., `uv.lock` is larger than MAX_SOURCE_BYTES, and a real archive must still verify., Six benign markers at resume must no longer pause trading after a good…, The staged subset must import on its own; the deployed image has no…, test_archive_provenance_and_hash_are_exact() (+19 more)

### Community 64 - "ButterflyGuy Code Review State"
Cohesion: 0.12
Nodes (15): Architecture map, ButterflyGuy Code Review State, Changes implemented, Commands executed, Current phase, Decisions already made, Exact next actions, Files and directories reviewed (+7 more)

### Community 65 - "test_candidate_snapshot.py"
Cohesion: 0.38
Nodes (10): asyncio, datetime, quote(), snapshot(), test_atomic_store_sequence_and_boot_instance_change(), test_lease_cadence_and_ttl_expiry(), test_long_poll_never_replays_same_sequence(), test_new_lease_wakes_idle_feed() (+2 more)

### Community 66 - "universes.py"
Cohesion: 0.06
Nodes (57): _as_float(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols(), fetch_sp500_rows() (+49 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.15
Nodes (13): DbDataLoader, Connection, date, datetime, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order., Query option_chain_snapshots for the nearest snapshot_time <= *at*. (+5 more)

### Community 69 - "SnapshotUnavailableError"
Cohesion: 0.13
Nodes (14): _final_regular_session_close(), Lease, _previous_close(), Any, date, datetime, LeaseKind, time (+6 more)

### Community 70 - "GapRegimeFilter"
Cohesion: 0.13
Nodes (14): GapRegimeFilter, Enum, str, Market regime classifier for 0-DTE butterfly parameter dispatch. Classifies…, Classifies market regime from SPX recent closes and daily VIX level., Return Regime for today given prior daily closes and today's VIX. Args:…, Regime, RegimeClassifier (+6 more)

### Community 71 - "scanner.py"
Cohesion: 0.19
Nodes (19): _as_float(), _as_int(), filter_movers(), _focus_reasons(), MarketContext, _mid_bid_ask(), _mover_change_pct(), _mover_symbol() (+11 more)

### Community 72 - "Any"
Cohesion: 0.18
Nodes (25): _approved_window(), _baseline_candidate_capture(), build_record(), _candidate_read_only(), _compose_config_hash(), _compose_observation(), _config_mount_observation(), _container_identity() (+17 more)

### Community 73 - "test_gateway_credential_proof_operator.py"
Cohesion: 0.11
Nodes (25): compose_pair(), Refusal must stay an argparse stderr exit-2, not one of the new bounded codes., A live service emitting errors is not an output-parsing fault., An early command must be self-explanatory; the window rule itself is unchanged., Docker writes the --time deprecation notice to stdout, breaking the exact-…, Never stop a container that actually exists., runtime_inspect(), test_accepted_snapshot_discovery_extracts_bounded_composite_supplement() (+17 more)

### Community 74 - "populated_state"
Cohesion: 0.12
Nodes (39): approval_args(), armed_approval_state(), patch_approval_checks(), patch_restoration_success(), populated_state(), Namespace, A mistyped path must not surface as probe_token_invalid, which asserts a token…, A failed proof must name its own stage, and with it whether a token read… (+31 more)

### Community 75 - "chain_cache.py"
Cohesion: 0.23
Nodes (15): chain_cache_path(), load_chain_day(), nearest_snapshot(), date, datetime, Path, Real option chain cache — per-day JSON snapshots from the live collector.…, Load all chain snapshots for a day. Returns dict of UTC datetime ->… (+7 more)

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.09
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 77 - "run_morning_scan.py"
Cohesion: 0.09
Nodes (33): is_premarket_window(), True during weekday premarket (default 4:00–9:30 AM ET)., load_equity_scan_config(), Path, Load equity scan settings from YAML., archive_report(), Path, Write the scan report to a dated markdown file under report_dir. (+25 more)

### Community 78 - "Window A — Token re-authorization (mandatory)"
Cohesion: 0.10
Nodes (20): A0 — Snapshot (read-only), A1 — Disable the keepalive, A2 — Stop the three trading services, A3 — Re-authorize, A4 — Verify the new document, A5 — Start the three services, A6 — Restore the keepalive, A7 — Verify (+12 more)

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
Cohesion: 0.11
Nodes (42): TradePoint, build_combined_performance_chart_png(), Build one image with weekly, monthly, and all-time equity + drawdown panels., build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption() (+34 more)

### Community 83 - "Architecture"
Cohesion: 0.11
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "LockedSchwabClientAdapter"
Cohesion: 0.11
Nodes (28): ClientT, GatewayCredentialProbeReason, OperationResult, GatewayCredentialProbeError, GatewayCredentialProbeResult, RuntimeError, One bounded quote proof through the locked token adapter., Bounded failure safe for operator output. The message is fixed. ``reason`` is a… (+20 more)

### Community 87 - "run_entry_analysis.py"
Cohesion: 0.17
Nodes (24): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+16 more)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.16
Nodes (21): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+13 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.25
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 91 - "schemas.py"
Cohesion: 0.14
Nodes (17): Pydantic models for option data and trade records., _bucket_sigmas(), O(N*W) butterfly construction and scoring engine., Return sigma anchors spanning narrow to wide for the bucket size., Return (widths, sigma_fractions) for the active VIX bucket. Buckets are…, resolve_wing_widths_for_vix(), Butterfly selector — picks the best candidate from a list., _active_widths_and_sigmas() (+9 more)

### Community 92 - "DatabasePool"
Cohesion: 0.04
Nodes (76): BoundLogger, Pool, assert_candidate_safety(), CandidateAuditContext, CandidateDecisionQueries, CandidatePerformanceStats, config_sha256(), Path (+68 more)

### Community 93 - "._shadow_chain"
Cohesion: 0.18
Nodes (10): _error_code(), _mismatch_code(), _numbers_agree(), Any, date, Exception, Task, Classify a value difference by what the gateway could prove about its freshness. (+2 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.20
Nodes (9): 2026-07-14 — data audit and research design, 2026-07-14 — diminishing returns checkpoint, Data limitations and leakage controls, Final data-driven pass, First-pass result, Options strategy discovery journal, Predeclared hypotheses (no tuning yet), Second structural pass (+1 more)

### Community 95 - "Codex Project State"
Cohesion: 0.10
Nodes (20): Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z), Codex Project State, Current Phase, Current Slice, Decisions Made, Known Failures (+12 more)

### Community 96 - "Re-authorization checklist — Saturday 2026-08-15"
Cohesion: 0.13
Nodes (14): Before you start, Expected result: no containers restarted, First, watch the reload do its job, Re-authorization checklist — Saturday 2026-08-15, Step 0 — already done, nothing to do, Step 1 — mint the token on zeus, in a real terminal, Step 2 — stage on Helios and verify byte-identical, Step 3 — move into place under the C1 lock (+6 more)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "SchwabClientWrapper"
Cohesion: 0.05
Nodes (35): DirectSchwabMarketDataProvider, MarketMoversProvider, Narrow read-only provider boundaries for Schwab market data., Delegate to the current client without owning its lifecycle or changing data., _creation_timestamp(), Any, date, Read the document's re-authorization marker. `creation_timestamp` changes only… (+27 more)

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "XSP Opportunistic Partial-Fill Evidence Plan"
Cohesion: 0.29
Nodes (6): Completion, Current evidence, Decision, If one occurs naturally, Required artifacts, XSP Opportunistic Partial-Fill Evidence Plan

### Community 101 - "trade_service.py"
Cohesion: 0.10
Nodes (21): capped_entry_limit(), entry_fill_within_limit(), Shared entry-price limit policy for production and candidate runtimes., Return a cent-valid debit limit that never exceeds the configured maximum., Return whether an entry fill respects its hard debit ceiling., _age_seconds(), Any, date (+13 more)

### Community 102 - "resolve_db_dsn"
Cohesion: 0.18
Nodes (13): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., Resolve the DB connection string for local backtests. Backtests follow the…, resolve_db_dsn(), asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot() (+5 more)

### Community 103 - "redact"
Cohesion: 0.33
Nodes (5): Any, Small defensive redaction layer for gateway audit metadata., Return a recursively redacted copy suitable for bounded audit metadata., redact(), test_redaction_removes_nested_credentials_and_account_identifiers()

### Community 104 - "test_gateway_issue_keys.py"
Cohesion: 0.15
Nodes (27): docker_inspect(), CaptureFixture, MonkeyPatch, parametrize, Path, test_canonical_fingerprint_is_independent_of_semantically_unordered_fields(), test_cli_bounds_docker_failure_without_raw_exception(), test_cli_exact_and_staging_verification_are_bounded() (+19 more)

### Community 105 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.14
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 106 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.17
Nodes (12): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding (+4 more)

### Community 107 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 109 - "run_live.py"
Cohesion: 0.07
Nodes (65): clear_readiness(), Prometheus metrics for monitoring., Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., readiness_snapshot(), set_readiness(), ButterflyOrderBuilder, Builds butterfly spread orders for Schwab API. (+57 more)

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
Cohesion: 0.12
Nodes (16): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+8 more)

### Community 120 - "_MetricsHandler"
Cohesion: 0.32
Nodes (4): BaseHTTPRequestHandler, _MetricsHandler, HTTP request handler serving both Prometheus metrics and health checks., Suppress default request logging to stderr.

### Community 121 - "CandidateEvaluator"
Cohesion: 0.27
Nodes (5): candidate_performance_stats(), CandidateEvaluator, Summarize one chronological, closed mark_v1 PnL cohort., _restore_trade(), test_candidate_performance_stats_reports_outlier_dependence()

### Community 122 - "load_date_data"
Cohesion: 0.15
Nodes (23): discover_dates(), _force_synthetic_for_date(), get_prev_close(), get_recent_closes(), get_vix_at(), get_vix_prev_close(), get_vix_snapshot_at(), load_bars_from_db() (+15 more)

### Community 123 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 124 - "test_run_migrations.py"
Cohesion: 0.43
Nodes (5): fake_db(), FakeConnection, asyncio, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 125 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 126 - "HttpMarketDataProvider"
Cohesion: 0.12
Nodes (15): HttpMarketDataProvider, AsyncClient, LeaseKind, Fail-closed client for the internal candidate feed., _response_error(), make_session_close(), make_snapshot(), asyncio (+7 more)

### Community 127 - "TokenManagerState"
Cohesion: 0.07
Nodes (41): AdmissionCapacityError, AdmissionController, AdmissionPolicy, RuntimeError, Bounded in-process admission policy for gateway market-data reads., The caller's bounded priority pool has no available permit., Keep background work out of ButterflyGuy's protected capacity., Expose bounded state for deterministic fake-only tests. (+33 more)

### Community 128 - "Window H — verification held; the deadline reminder is mistimed (2026-08-08)"
Cohesion: 0.20
Nodes (10): Corrections to the Window H brief, Deliverables, Finding — the weekly reminder fires after the deadline it protects, Still open after Window H, Task 2 — the Monday check is deferred a fourth time, Tasks 3–6 — all green, verified host-against-container, The deadline in local time — stated because the brief did not, The deadline, re-derived from the document (+2 more)

### Community 129 - "Reducing the weekly re-authorization cost — a scoping question"
Cohesion: 0.18
Nodes (10): Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Recommendation, Reducing the weekly re-authorization cost — a scoping question, Status, The alternative worth costing first, The brief's proposed remedy, and why it is weaker than it looks, The cost being attacked (+2 more)

### Community 130 - "Schwab Gateway Credential Proof"
Cohesion: 0.06
Nodes (34): Accepted runtime-baseline proof adapter, Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05 (+26 more)

### Community 131 - "test_gateway_compose.py"
Cohesion: 0.12
Nodes (12): All four trading services bind the token document from one required variable. A…, The gateway replaces the token document atomically, swapping in a new inode. A…, A token_path in YAML silently beats the deployment's SCHWAB_TOKEN_PATH.…, Reachability is the live service's alone, and the network is never created…, A document-only bind under read_only: true cannot support atomic replacement.…, The template must parse under the real loader's schema rules., test_default_compose_binds_the_token_directory_never_the_document(), test_default_compose_token_binds_require_the_shared_token_directory() (+4 more)

### Community 132 - "AppConfig"
Cohesion: 0.07
Nodes (53): Schwab market-data client deliberately lacking every account/order operation., AppConfig, CollectorSettings, ConfigModel, DatabaseSettings, EntrySettings, ExecutionSettings, MonitoringSettings (+45 more)

### Community 133 - "C3 — wiring shadow reads into `run_live.py`"
Cohesion: 0.20
Nodes (9): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", C3 — wiring shadow reads into `run_live.py`, Prerequisites, in order, Proposed steps, The blocker C3 shares with monitoring: the gateway is unreachable, The wiring point, Two corrections to the received design points (+1 more)

### Community 134 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "generate_live_performance.py"
Cohesion: 0.16
Nodes (20): no_trade_reason(), _parse_metadata(), Any, render_placeholder_html(), trade_point_from_row(), build_report(), fetch_closed_trades(), fetch_no_trade_days() (+12 more)

### Community 137 - "OptionChainProvider"
Cohesion: 0.15
Nodes (11): EquityQuoteProvider, OptionChainProvider, PriceHistoryProvider, Protocol, SpotPriceProvider, DirectSchwabQuoteUpstream, Normalize quotes from the direct adapter inside the gateway boundary., _FakeQuote (+3 more)

### Community 138 - "run_backtest_db.py"
Cohesion: 0.19
Nodes (19): _duration_min(), _find_bar_at(), _find_entry_bar_at(), find_entry_in_window(), _format_et(), nearest_snapshot(), _parse_config_time(), _pst_to_et() (+11 more)

### Community 139 - "daily_report_card_config.py"
Cohesion: 0.33
Nodes (5): load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds

### Community 140 - "prepare_args"
Cohesion: 0.15
Nodes (19): patch_approval_1_success(), patch_prepare_success(), patch_proof_prerequisites(), prepare_args(), Neutralize the host proof gates that would read real credentials or real files., A stop-output defect must fail in preflight, not after NDX has already been…, A watchdog prerequisite must fail in preflight, not inside the one authorized…, The cheapest and most failure-prone gate must run first, not after fifteen… (+11 more)

### Community 141 - "position_service.py"
Cohesion: 0.06
Nodes (61): get_0dte_expiration(), now_utc(), Get today's date as the 0-DTE expiration (SPX has daily expirations)., A trade record for tracking entry/exit., TradeRecord, AmbiguousOrderError, _assert_entry_fill_within_limit(), _broker_time() (+53 more)

### Community 142 - "ButterflyCandidate"
Cohesion: 0.17
Nodes (11): _candidate_mark(), ButterflyCandidate, A butterfly spread candidate identified by the scanner., Any, Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., _compute_spread(), LiveSpread (+3 more)

### Community 143 - "probe_schwab_gateway_credentials.py"
Cohesion: 0.27
Nodes (9): NoReturn, _fail(), _load_runtime_dependencies(), main(), _parser(), ArgumentParser, Run one explicitly authorized Schwab gateway credential proof without starting…, Import failure-prone runtime dependencies inside the bounded CLI path. (+1 more)

### Community 144 - "test_order_preview.py"
Cohesion: 0.27
Nodes (10): make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check…, Realistic SPX butterfly candidate., Order spec must have all fields Schwab requires., Schwab expects price as a string., test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields() (+2 more)

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 146 - "Any"
Cohesion: 0.15
Nodes (12): extract_spot_price(), Pull a spot price out of a Schwab quote response. This mirrors…, Any, date, Exception, parametrize, The protocols are not runtime-checkable, so match signatures explicitly., Differential test against SchwabClientWrapper.get_spot_price.… (+4 more)

### Community 147 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 148 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 149 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 150 - "MarketSnapshot"
Cohesion: 0.16
Nodes (12): CandidatePaperExecutor, Any, Mark-price fills only; this object intentionally has no broker methods., MarketSnapshot, One atomically published, replayable view of candidate market data., candidate(), FakeProvider, market() (+4 more)

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
Cohesion: 0.32
Nodes (15): _after_identity(), create_app(), _delete_lease(), _float_query(), _health(), _legs(), _metrics(), _pin_snapshot() (+7 more)

### Community 155 - "parse_args"
Cohesion: 0.12
Nodes (20): _asset_drawdowns(), candidate_from_trade_row(), _floatlist(), _intlist(), parse_args(), _parse_dd_schedule(), Use the first regular-session snapshot for gap direction., Shared live/backtest parity fields from runtime config. (+12 more)

### Community 156 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 157 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 158 - "SyntheticChainGenerator"
Cohesion: 0.25
Nodes (14): Generates a synthetic SPX option chain from spot + VIX., SyntheticChainGenerator, make_snapshot_time(), datetime, Tests for the synthetic chain generator., Create a snapshot time N minutes before 4pm ET., Volatility skew: OTM puts should have higher IV than equidistant OTM calls., Option price should decrease as expiration approaches. (+6 more)

### Community 159 - "Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)"
Cohesion: 0.33
Nodes (6): Correction to Window H part 1, Item 1 — the warnings now fire before the deadline (deployed), Item 3 built — the token reload (2026-08-09, NOT deployed), Item 3 — the deciding question is answered: the swap is safe, Window H correction — the restart arithmetic was wrong, and the gateway never needed restarting, Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)

### Community 160 - "Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)"
Cohesion: 0.33
Nodes (6): Fixed by binding the directory, and by a second defect that fix exposed, Still open, The finding — the always-on gateway had orphaned all three trading containers, Verified, by inode and digest and by an actual atomic replace, Window E addendum — the candidate fleet's orphaned token, fixed (2026-08-08), Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)

### Community 161 - "_emit"
Cohesion: 0.33
Nodes (5): _emit(), _parser(), ArgumentParser, Argparse variant that never echoes arguments, paths, or parser internals., SafeArgumentParser

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

### Community 166 - "_signal_spx"
Cohesion: 0.40
Nodes (5): Prove the host-side SPX signal command works, using a signal that cannot change…, Signal SPX from the host. The container's init is the application itself, and…, _require_spx_signal_capability(), _signal_spx(), _suspend_spx()

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
Cohesion: 0.30
Nodes (24): increment_callback(), manager(), _process_refresh(), Exception, MonkeyPatch, parametrize, Path, test_callback_failure_preserves_original_and_redacts_error_and_logs() (+16 more)

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

### Community 178 - "EntrySelectionResult"
Cohesion: 0.27
Nodes (13): EntrySelectionResult, build_entry_selection_parity(), _candidate_payload(), _per_width_payload(), Compare live Schwab entry selection against nearest DB chain snapshot., Return a JSON-serializable Schwab vs DB selection comparison., Result of a single entry selection pass., _candidate() (+5 more)

### Community 179 - "SessionClose"
Cohesion: 0.21
Nodes (6): Any, Auditable final regular-session SPX close supplied by the shared feed., SessionClose, date, test_session_close_rejects_unauditable_timestamps(), test_session_close_round_trip_preserves_timezone_aware_evidence()

### Community 180 - "test_position_manager.py"
Cohesion: 0.26
Nodes (13): PeakTrackingSettings, fly_settlement_value(), Butterfly cash-settlement value from the underlying index close., make_candidate(), make_quote(), make_xsp_candidate(), quote_map(), Tests for butterfly position valuation helpers. (+5 more)

### Community 181 - "AlertmanagerNotifier"
Cohesion: 0.20
Nodes (7): Lightweight Telegram and ButterflyGuy Alertmanager helpers. Usage: from…, Send a Telegram message. Returns True on success, False on failure., Post one stable, identifier-free alert fingerprint to Alertmanager., send(), send_alertmanager(), AlertmanagerNotifier, Sends centrally deduplicated critical alerts through Alertmanager.

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (9): High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy (+1 more)

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 184 - "select_entry_candidate"
Cohesion: 0.33
Nodes (11): Select the live/backtest entry candidate with shared pure logic., select_entry_candidate(), _candidate(), _config(), MonkeyPatch, _state(), test_absolute_stop_truncates_never_profitable_loss(), test_gap_conviction_threshold_is_wired_into_candidate_evaluator() (+3 more)

### Community 185 - "7. Operational and observability data"
Cohesion: 0.50
Nodes (4): 7.1 Prometheus metrics, 7.2 Health and readiness endpoints, 7.3 Structured application logs, 7. Operational and observability data

### Community 186 - "ChainDay"
Cohesion: 0.29
Nodes (9): dict, ChainDay, dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log…, day_with_monitoring_bars(), Add live monitor timestamps to bar iteration while carrying nearest spot…, _bar(), datetime, test_day_with_monitoring_bars_adds_live_poll_timestamps() (+1 more)

### Community 187 - ".collect_snapshot"
Cohesion: 0.18
Nodes (7): Any, date, datetime, Fetch and store daily OHLCV bars for SPX and VIX. Runs once per calendar day., Fetch current chain and store snapshot. Returns row count., Main collector loop — runs while market is open., Parse Schwab callExpDateMap/putExpDateMap into flat rows.

### Community 188 - "send_test_chart.py"
Cohesion: 0.27
Nodes (9): trade_pnl_dollars(), _load_trade(), main(), Generate entry + EOD charts from a historic trade and post to Discord., load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles() (+1 more)

### Community 189 - "GatewayUpstreamSettings"
Cohesion: 0.22
Nodes (10): GatewayUpstreamSettings, BaseSettings, field_validator, Path, Real credential inputs for a live-serving gateway process. Deliberately a…, MonkeyPatch, Regression guard for the deliberate duplication of these two settings classes.…, test_upstream_settings_do_not_expose_secrets_in_their_repr() (+2 more)

### Community 190 - "GatewaySettings"
Cohesion: 0.29
Nodes (4): GatewaySettings, BaseSettings, field_validator, Path

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - "LockedSchwabMarketDataProvider"
Cohesion: 0.31
Nodes (5): LockedSchwabMarketDataProvider, Any, date, Read-only Schwab market data through one locked token transaction per call., Run one synchronous locked transaction without blocking the event loop.

### Community 194 - "_aware_utc"
Cohesion: 0.32
Nodes (3): _aware_utc(), datetime, StaleSnapshotError

### Community 195 - "test_order_builder.py"
Cohesion: 0.48
Nodes (6): make_candidate(), Tests for butterfly order builder., test_build_close_order_structure(), test_build_open_order_legs(), test_build_open_order_structure(), test_build_order_with_quantity()

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **507 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `Objective`, `Current Phase` (+502 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `get_logger()` connect `DatabasePool` to `run_paper_replay.py`, `token_manager.py`, `AppConfig`, `GatewayMarketDataClient`, `OptionQuote`, `run_backtest_db.py`, `position_service.py`, `run_schwab_gateway.py`, `feed.py`, `news.py`, `run_classifier_sweep.py`, `api.py`, `MinuteBar`, `time_utils.py`, `send_test_chart.py`, `run_morning_scan.py`, `weekend_review.py`, `LockedSchwabClientAdapter`, `run_entry_analysis.py`, `schemas.py`, `SchwabClientWrapper`, `trade_service.py`, `run_live.py`, `services/daily_report_card.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `universes.py`, `test_order_manager.py`, `record_equity_market_data.py`, `trade_service.py`, `_Session`, `ReadOnlySchwabMarketDataClient`, `OptionChainProvider`, `run_morning_scan.py`, `position_service.py`, `run_live.py`, `AtomicFileTokenStore`, `_Response`, `services/daily_report_card.py`, `LockedSchwabClientAdapter`, `load_config`, `time_utils.py`, `DatabasePool`, `OrderIntentQueries`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `.monitor_loop`, `test_order_manager.py`, `AppConfig`, `run_backtest_db.py`, `position_service.py`, `ButterflyCandidate`, `MarketSnapshot`, `SnapshotIdentity`, `feed.py`, `StrategySettings`, `SyntheticChainGenerator`, `ProfitStateMachine`, `synthetic_chain.py`, `AtomicSnapshotStore`, `MinuteBar`, `report_exit_mark_parity.py`, `EntrySelectionResult`, `SessionClose`, `test_position_manager.py`, `select_entry_candidate`, `ChainDay`, `test_candidate_snapshot.py`, `_aware_utc`, `DbDataLoader`, `SnapshotUnavailableError`, `chain_cache.py`, `run_entry_analysis.py`, `schemas.py`, `DatabasePool`, `trade_service.py`, `load_date_data`, `HttpMarketDataProvider`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `SchwabClientWrapper` (e.g. with `CollectorMarketDataProvider` and `DirectSchwabMarketDataProvider`) actually correct?**
  _`SchwabClientWrapper` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 31 INFERRED edges - model-reasoned connections that need verification._