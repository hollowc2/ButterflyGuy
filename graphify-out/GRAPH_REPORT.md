# Graph Report - Butterflyguy  (2026-08-11)

## Corpus Check
- 284 files · ~326,937 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4380 nodes · 11655 edges · 220 communities (198 shown, 22 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 903 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `122c4ba9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- AlertmanagerNotifier
- time_utils.py
- test_order_manager.py
- RecordingGateway
- test_gateway_collector_surfaces.py
- ButterflyChartSpec
- test_gateway_token_adapter.py
- test_schwab_client.py
- discover_options_strategy.py
- entry_selection.py
- credential_proof_fingerprint.py
- ButterflyCandidate
- test_gateway_live_provider.py
- CandidateRegistry
- forex_calendar.py
- run_backtest_db.py
- MinuteBar
- CsvDataLoader
- ShadowDiscrepancyRecorder
- test_broker_order_intents.py
- test_equity_scan.py
- InternalKeyAuthenticator
- core/config.py
- reports/daily_report_card.py
- report.py
- MarketSnapshot
- ReadOnlySchwabMarketDataClient
- upstream.py
- iter_chain_options
- _build_collector_market_data
- _approval_1_execute
- ProfitStateMachine
- test_risk_engine.py
- SyntheticChainGenerator
- news.py
- write_candle_snapshot
- test_gateway_credential_probe.py
- performance_chart.py
- Current Schwab Integration
- ._retry
- test_candidate_settlement.py
- AdmissionPolicy
- AtomicSnapshotStore
- DiscordNotifier
- test_schwab_token_keepalive.py
- SchwabDataLoader
- equity_trade_chart.py
- test_gateway_live_runner.py
- report_exit_mark_parity.py
- OperatorFailure
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- MonkeyPatch
- load_config
- StrategySettings
- OptionQuote
- test_comparison_stats.py
- Schwab Gateway Migration Plan
- Path
- create_app
- OrderIntentQueries
- Path
- DayData
- ButterflyOrderBuilder
- universes.py
- NamedTuple
- DbDataLoader
- Lease
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
- GatewayCredentialProbeError
- run_entry_analysis.py
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- test_gateway_shadow_reads.py
- DatabasePool
- ShadowComparingMarketDataProvider
- 2026-07-14 — data audit and research design
- Codex Project State
- Re-authorization checklist — Saturday 2026-08-15
- Capability recorder design
- run_gateway_credential_probe
- Schwab Single-Token Manager
- run_classifier_sweep.py
- Standalone SchwabGateway Extraction Plan
- record_equity_market_data.py
- redact
- test_gateway_issue_keys.py
- Option A deployment runbook — Helios, containerized
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- test_candidate_schwab_market_data.py
- Schwab Gateway Foundation: Local Run
- run_live.py
- GatewaySettings
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
- test_candidate_provider.py
- api.py
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- Reducing the weekly re-authorization cost — a scoping question
- Schwab Gateway Credential Proof
- test_gateway_compose.py
- AppConfig
- C3 — wiring shadow reads into `run_live.py`
- Schwab gateway deployment options
- Strategy Settings
- SchwabClientWrapper
- DirectSchwabMarketDataProvider
- volume.py
- DirectProvider
- prepare_args
- order_manager.py
- entry_selection_parity.py
- probe_schwab_gateway_credentials.py
- resolve_db_dsn
- Width Selection
- backfill_equity_candles.py
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Schwab Gateway Multi-Consumer Foundation
- FakeProvider
- Window C — the two token writers resolved (2026-08-08)
- 9) Capture equity candles and Level II for trade review
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- feed.py
- report_selection_parity.py
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- test_candidate_evaluator_accounting.py
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)
- _emit
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
- _approval_2_execute
- .execute
- SessionClose
- FakeResponse
- trade_service.py
- Layered Risk Management
- Geometric butterfly icon
- test_value_differences_are_classified_by_provable_freshness
- 7. Operational and observability data
- .write_until_stopped
- ButterflyGuy data sources — representative samples
- load_spot_series
- LockedSchwabClientAdapter
- daily_report_card_config.py
- 3) Start the SPX stack in Docker
- chain_metadata.py
- client.py
- gateway_client/config.py
- gateway_client/models.py
- token_manager.py
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
8. `DatabasePool` - 60 edges
9. `BrokerStateGate` - 53 edges
10. `SnapshotIdentity` - 52 edges

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

## Communities (220 total, 22 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.10
Nodes (36): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), _et(), get_prev_close(), get_vix(), LiveSpread (+28 more)

### Community 1 - "AlertmanagerNotifier"
Cohesion: 0.16
Nodes (8): Lightweight Telegram and ButterflyGuy Alertmanager helpers. Usage: from…, Send a Telegram message. Returns True on success, False on failure., Post one stable, identifier-free alert fingerprint to Alertmanager., send(), send_alertmanager(), AlertmanagerNotifier, Sends centrally deduplicated critical alerts through Alertmanager., Keep the Schwab OAuth token alive and alert before refresh token expiry. Schwab…

### Community 2 - "time_utils.py"
Cohesion: 0.04
Nodes (75): _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_premarket_window(), is_trading_day(), _last_weekday(), market_close_time() (+67 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.16
Nodes (57): LiveSpread, broker_fill(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread(), make_order_manager() (+49 more)

### Community 4 - "RecordingGateway"
Cohesion: 0.15
Nodes (19): ChainMetadataResponseV1, SpotResponseV1, chain_response(), ``extract_chain_metadata`` now tolerates a payload with no expiration maps (it…, Assert on what is handed to the logger, independent of any configured sink., An agreement must be observable; otherwise the ratio has no denominator., Stands in for GatewayMarketDataClient with a scripted spot/chain reply., RecordingGateway (+11 more)

### Community 5 - "test_gateway_collector_surfaces.py"
Cohesion: 0.09
Nodes (46): Build a synchronous schwab-py handler that never blocks the stream., DirectSchwabChainMetadataUpstream, DirectSchwabSpotUpstream, Normalize a spot read from the direct adapter inside the gateway boundary., Summarize a chain read from the direct adapter; contract rows never leave here., app(), authenticator(), FakeChainUpstream (+38 more)

### Community 6 - "ButterflyChartSpec"
Cohesion: 0.09
Nodes (41): Send full-session EOD charts for closed trades after market close., build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series() (+33 more)

### Community 7 - "test_gateway_token_adapter.py"
Cohesion: 0.22
Nodes (19): adapter(), FakeAccessFunctionFactory, FakeClient, manager(), Any, AtomicTokenManager, MonkeyPatch, Path (+11 more)

### Community 8 - "test_schwab_client.py"
Cohesion: 0.24
Nodes (19): _accessors(), _account_client(), asyncio, Initialize a wrapper against a real token file, returning its read/write funcs., Wire a wrapper whose _build_client hands out `clients` in order., An ordinary hourly refresh rewrites the document but must not rebuild the…, A bad document must leave the process on the credential that still works., initialize() tolerates an unreadable marker; the first check must not rebuild. (+11 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (39): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+31 more)

### Community 10 - "entry_selection.py"
Cohesion: 0.13
Nodes (20): EntrySettings, VixWidthBucket, _bucket_sigmas(), Return sigma anchors spanning narrow to wide for the bucket size., Return (widths, sigma_fractions) for the active VIX bucket. Buckets are…, resolve_wing_widths_for_vix(), Shared entry selection for live trading and backtests., Helpers for choosing a candidate across multiple active widths. (+12 more)

### Community 11 - "credential_proof_fingerprint.py"
Cohesion: 0.11
Nodes (40): _accepted_fingerprint_hashes(), _accepted_snapshots(), _approved_staging_tmpfs(), _approved_tmpfs_entry(), _canonical_mount(), _canonical_ports(), _canonical_sort_key(), _compose_json() (+32 more)

### Community 12 - "ButterflyCandidate"
Cohesion: 0.06
Nodes (48): candidate_fill_parity_failures(), _candidate_mark(), CandidateEvaluator, Any, Count mark_v1 rows whose fills disagree with their recorded evidence., _restore_trade(), ButterflyCandidate, A butterfly spread candidate identified by the scanner. (+40 more)

### Community 13 - "test_gateway_live_provider.py"
Cohesion: 0.08
Nodes (39): extract_spot_price(), Pull a spot price out of a Schwab quote response. This mirrors…, _FakeClient, _provider(), Any, asyncio, date, Exception (+31 more)

### Community 14 - "CandidateRegistry"
Cohesion: 0.12
Nodes (38): CandidateRegistration, CandidateRegistry, load_registry(), BaseModel, model_validator, Path, Validated source of truth and deterministic runtime rendering for candidates., render_runtime() (+30 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (23): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+15 more)

### Community 16 - "run_backtest_db.py"
Cohesion: 0.06
Nodes (80): max_consecutive_losses(), max_drawdown(), profit_factor(), Shared metrics for backtest sweep scripts., _asset_drawdowns(), backtest_entry_price(), _dd_schedule_label(), discover_dates() (+72 more)

### Community 17 - "MinuteBar"
Cohesion: 0.09
Nodes (22): MinuteBar, Fetch today's 1-min bars from Schwab and run BiasScoreFilter., BiasScoreFilter, Multi-signal directional bias filter for 0-DTE butterfly entries., High and low of the opening range (bars with ET time < 09:45). Edge case: no OR…, Exponential moving average seeded with SMA of first `period` bars. Returns None…, Scores market direction using 4 signals; returns CALL, PUT, or None., Compute bias score from 4 signals: gap : +1 if entry_close > prev_close, -1 if… (+14 more)

### Community 18 - "CsvDataLoader"
Cohesion: 0.25
Nodes (8): DataFrame, CsvDataLoader, date, Path, Map each date → list of up to n prior daily closes (chrono order, newest last).…, Last VIX bar close per day as daily VIX proxy., Map each date → last close of the previous trading day., Loads SPX + VIX 1-minute CSVs and serves DayData objects. Loads both files…

### Community 19 - "ShadowDiscrepancyRecorder"
Cohesion: 0.22
Nodes (5): GatewayMarketDataClient, A bounded, fixed-shape observation. Carries no payload, path, or exception text., Tally discrepancies over a fixed key space; retains no observed values., ShadowDiscrepancy, ShadowDiscrepancyRecorder

### Community 20 - "test_broker_order_intents.py"
Cohesion: 0.24
Nodes (16): broker_fill_payload(), asyncio, parametrize, test_broker_state_gate_records_unsafe_reason(), test_filled_entry_intent_rejects_wrong_broker_ratio(), test_filled_entry_intent_rejects_zero_quantity(), test_filled_entry_intent_repairs_open_trade_only_with_matching_legs_and_fill(), test_filled_exit_intent_repairs_open_trade_only_when_broker_flat() (+8 more)

### Community 21 - "test_equity_scan.py"
Cohesion: 0.16
Nodes (36): EquityScanSettings, build_snapshots(), parse_equity_quote(), passes_filters(), datetime, _quote_age_seconds(), rank_catalyst_watch(), rank_scan_results() (+28 more)

### Community 22 - "InternalKeyAuthenticator"
Cohesion: 0.07
Nodes (45): Enum, hash_api_key(), InternalKeyAuthenticator, InternalPrincipal, Any, Path, Internal service authentication with hashed, capability-scoped API keys., Read once and return both the authenticator and exact validated document. (+37 more)

### Community 23 - "core/config.py"
Cohesion: 0.06
Nodes (52): ProfitManagementStrategy, DayResult, DrawdownWindow, datetime, Single-day simulation engine using synthetic option chains., Runs full strategy on a single day using synthetic options., Simulate one trading day., Simulate intraday using BS pricing, pinned to a pre-selected real entry. Skips… (+44 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.13
Nodes (36): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders(), detect_problems(), _extract_order_id() (+28 more)

### Community 25 - "report.py"
Cohesion: 0.19
Nodes (25): _direction_emoji(), _fmt_news(), _fmt_pct(), _fmt_price(), _fmt_quality(), _fmt_rvol(), _fmt_universes(), _fmt_volume() (+17 more)

### Community 26 - "MarketSnapshot"
Cohesion: 0.07
Nodes (23): Paper-only SPX candidate fleet fed by a shared market-data service., _aware_utc(), MarketSnapshot, datetime, Immutable normalized market snapshots shared by candidate evaluators., No complete snapshot is currently available., A long poll completed normally before a newer snapshot was published., One atomically published, replayable view of candidate market data. (+15 more)

### Community 27 - "ReadOnlySchwabMarketDataClient"
Cohesion: 0.19
Nodes (7): Any, date, Prove the replacement credential with one bounded read-only Schwab call., Authenticate a Schwab client without resolving or retaining an account., Build one client with an isolated in-memory refresh-token callback., Validate and install a client built from a newly authorized token document., ReadOnlySchwabMarketDataClient

### Community 28 - "upstream.py"
Cohesion: 0.13
Nodes (20): _event_time(), _integer(), normalize_schwab_chain_metadata(), normalize_schwab_quote(), normalize_schwab_spot(), _number(), Any, ChainMetadataV1 (+12 more)

### Community 29 - "iter_chain_options"
Cohesion: 0.12
Nodes (29): iter_chain_options(), date, Shared utilities for parsing Schwab option chain responses., Yield (strike, option_type, opt_dict) for each option matching the expiration.…, _contract(), _parse_rows(), Any, date (+21 more)

### Community 30 - "_build_collector_market_data"
Cohesion: 0.17
Nodes (17): GatewayClientSettings, _build_collector_market_data(), Build the collector provider while keeping direct reads authoritative. Gateway…, _require_direct_gateway_mode(), parametrize, settings(), test_gateway_client_mode_is_opt_in_and_secret_is_hidden(), test_gateway_client_mode_rejects_shadow_reads() (+9 more)

### Community 31 - "_approval_1_execute"
Cohesion: 0.11
Nodes (32): _approval_1_execute(), _best_effort_runtime_restore(), _cleanup_runtime_staging(), _compose_service_hash(), _container_is_stopped(), _docker_top_rows(), _fresh_error_counts(), _health_ok() (+24 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.06
Nodes (63): PeakTrackingSettings, ProfitManagementSettings, QuoteQualitySettings, PositionState, Current state of an open position., ExitSignal, ProfitState, ProfitStateMachine (+55 more)

### Community 33 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (18): make_risk_engine(), asyncio, Tests for the risk engine., Should block trading when market is closed., test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed() (+10 more)

### Community 34 - "SyntheticChainGenerator"
Cohesion: 0.05
Nodes (58): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+50 more)

### Community 35 - "news.py"
Cohesion: 0.17
Nodes (30): EquityNewsSettings, EquityScanFilters, EquityScanLimits, BaseModel, Configuration for the equity morning scan., _alpha_key(), _fetch_alpha_earnings(), _fetch_alpha_impacts() (+22 more)

### Community 36 - "write_candle_snapshot"
Cohesion: 0.24
Nodes (8): Any, date, datetime, Path, Write a run summary without exposing credentials or account identifiers., Write a deterministic JSON candle snapshot., write_candle_snapshot(), test_write_candle_snapshot_sorts_candles()

### Community 37 - "test_gateway_credential_probe.py"
Cohesion: 0.25
Nodes (18): install_dependencies(), install_fake_sdk(), CaptureFixture, MonkeyPatch, parametrize, An import fault proves no token read occurred, and must say so on stdout only., A missing SDK is the last stage that proves no token read occurred., Each of these proves a token read was reached, so each needs its own code. (+10 more)

### Community 38 - "performance_chart.py"
Cohesion: 0.18
Nodes (19): compute_stats(), ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels() (+11 more)

### Community 39 - "Current Schwab Integration"
Cohesion: 0.10
Nodes (19): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current architecture, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies (+11 more)

### Community 40 - "._retry"
Cohesion: 0.07
Nodes (18): Any, date, Execute with exponential backoff retry., Fetch option chain for a specific symbol and expiration., Get current spot price for SPX., Place an order once and return the order ID. Order placement is not retried…, Get the status of an order., Cancel an existing order. (+10 more)

### Community 41 - "test_candidate_settlement.py"
Cohesion: 0.62
Nodes (6): _candidate(), _evaluator(), asyncio, test_candidate_cash_settlement_fails_closed_without_feed_evidence(), test_candidate_cash_settlement_uses_only_shared_feed_evidence(), _trade()

### Community 42 - "AdmissionPolicy"
Cohesion: 0.14
Nodes (20): AdmissionCapacityError, AdmissionController, AdmissionPolicy, RuntimeError, Bounded in-process admission policy for gateway market-data reads., The caller's bounded priority pool has no available permit., Keep background work out of ButterflyGuy's protected capacity., Expose bounded state for deterministic fake-only tests. (+12 more)

### Community 43 - "AtomicSnapshotStore"
Cohesion: 0.10
Nodes (26): AtomicSnapshotStore, CandidateFeed, LeaseRegistry, Condition-guarded pointer swap; readers never observe partial snapshots., Persist once and return the canonical evidence for this session., SnapshotArchive, RuntimeError, No verified final regular-session close is available from the shared feed. (+18 more)

### Community 44 - "DiscordNotifier"
Cohesion: 0.14
Nodes (12): DiscordNotifier, date, Post one or more plain-text messages (e.g. morning equity scan)., Sends trading notifications to Discord via webhook., asyncio, parametrize, Tests for Discord trade notifications., test_alertmanager_failed_resolution_retries_until_accepted() (+4 more)

### Community 45 - "test_schwab_token_keepalive.py"
Cohesion: 0.16
Nodes (13): fixture, lock_events(), parametrize, SCHWAB_TOKEN_PATH overrides the default, process env winning over .env., Record lock acquire/release without touching a real lock file., Wire up the module-level environment the keepalive script reads on import., The refresh and the quote both happen while the gateway's lock is held. Schwab…, A busy lock fails loudly rather than writing alongside the other writer. (+5 more)

### Community 46 - "SchwabDataLoader"
Cohesion: 0.14
Nodes (11): date, Path, Fetch VIX daily close from yfinance., Fetch previous trading day's SPX close from yfinance., Load all data needed for a single backtest day., Loads SPY 1-minute bars from Schwab, scaled to SPX price levels. Reuses the…, Fetch SPX daily open from yfinance for SPY→SPX calibration., Fetch VIX daily close from yfinance. (+3 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (31): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+23 more)

### Community 48 - "test_gateway_live_runner.py"
Cohesion: 0.11
Nodes (39): AtomicTokenManager, Re-prime a latched token manager from outside the request path. A token-level…, Return True when the manager is ready, recovering it first if it is not., Recover readiness forever, surviving any failure a single attempt can raise.…, TokenReadinessRecovery, _keys_file(), Any, asyncio (+31 more)

### Community 49 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (18): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+10 more)

### Community 50 - "OperatorFailure"
Cohesion: 0.12
Nodes (31): _accepted_runtime_baseline(), _arm_watchdog(), _baseline_candidate_status(), _best_effort_restore_cron(), _cancel_watchdog(), _cleanup_temporary_inputs(), _disable_keepalive_cron(), _emergency_restore_spx() (+23 more)

### Community 51 - "live_performance.py"
Cohesion: 0.09
Nodes (46): chart_payload(), cumulative_equity(), drawdown_series(), DrawdownPoint, duration_minutes(), format_et_time(), is_drawdown_exit(), _money() (+38 more)

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
Cohesion: 0.13
Nodes (21): load_config(), Path, Load configuration from YAML file and environment variables., parametrize, Tests for configuration loading., Loading config with no files should return sensible defaults., Config values from YAML should override defaults., test_allow_live_trading_requires_explicit_env() (+13 more)

### Community 56 - "StrategySettings"
Cohesion: 0.11
Nodes (33): StrategySettings, main(), parse_args(), print_help(), Inspect what the strategy saw at entry for a given date. Replicates the…, EntryDecision, find_entry_candidate(), Find best candidate in the 10:00–10:30 ET window, returning full decision… (+25 more)

### Community 57 - "OptionQuote"
Cohesion: 0.11
Nodes (25): _as_float(), _as_int(), Any, date, Convert option_chain_snapshots rows into OptionQuote objects., Build OptionQuote list from option_chain_snapshots query rows., rows_to_option_quotes(), fly_mark_value() (+17 more)

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
Cohesion: 0.14
Nodes (26): create_app(), Application, authentication_middleware(), middleware, Request, StreamResponse, __getattr__(), Any (+18 more)

### Community 62 - "OrderIntentQueries"
Cohesion: 0.08
Nodes (7): OrderIntentQueries, Any, date, Bulk insert option chain snapshot rows using COPY., Queries for durable broker order intents., Dollar PnL for the rolling 7-day window (closed trades only)., Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict.

### Community 63 - "Path"
Cohesion: 0.12
Nodes (27): legacy_capture_args(), patch_legacy_capture_provenance(), Path, The manager creates its lock and atomic replacement beside the document., `uv.lock` is larger than MAX_SOURCE_BYTES, and a real archive must still verify., Six benign markers at resume must no longer pause trading after a good…, The staged subset must import on its own; the deployed image has no…, test_archive_provenance_and_hash_are_exact() (+19 more)

### Community 64 - "DayData"
Cohesion: 0.12
Nodes (23): dict, day_cache_path(), load_day(), date, Path, JSON cache helpers for DayData — shared across Schwab and future loaders., save_day(), ChainDay (+15 more)

### Community 65 - "ButterflyOrderBuilder"
Cohesion: 0.13
Nodes (22): ButterflyOrderBuilder, Any, Builds butterfly spread orders for Schwab API., Constructs Schwab-compatible butterfly order JSON., Build a butterfly BUY_TO_OPEN order., Build a butterfly SELL_TO_CLOSE order., make_spx_candidate(), Integration test: validate butterfly order JSON structure. These tests check… (+14 more)

### Community 66 - "universes.py"
Cohesion: 0.06
Nodes (63): _as_float(), build_liquid_meta(), extract_quote_price(), fetch_exchange_seed_map(), fetch_nasdaq_listed_symbols(), fetch_nq100_tickers(), fetch_nyse_listed_symbols(), fetch_sp500_rows() (+55 more)

### Community 68 - "DbDataLoader"
Cohesion: 0.14
Nodes (14): DbDataLoader, Connection, date, datetime, DB-backed data loader for historical SPX + VIX data. Reads from the live…, VIX close for *date*: daily_bars first, then last spot_prices tick., Last close from daily_bars strictly before *date*., Up to *n* daily closes before *date*, chronological order. (+6 more)

### Community 69 - "Lease"
Cohesion: 0.14
Nodes (12): _final_regular_session_close(), Lease, _previous_close(), Any, date, datetime, LeaseKind, time (+4 more)

### Community 70 - "GapRegimeFilter"
Cohesion: 0.14
Nodes (12): GapRegimeFilter, Enum, Market regime classifier for 0-DTE butterfly parameter dispatch. Classifies…, Return Regime for today given prior daily closes and today's VIX. Args:…, Regime, str, Unit tests for GapRegimeFilter.apply()., min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped. (+4 more)

### Community 71 - "scanner.py"
Cohesion: 0.24
Nodes (16): _as_float(), _as_int(), filter_movers(), MarketContext, _mid_bid_ask(), _mover_change_pct(), _mover_symbol(), parse_market_context() (+8 more)

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
Cohesion: 0.14
Nodes (25): load_equity_scan_config(), Path, Load equity scan settings from YAML., archive_report(), archive_report_json(), build_report(), _format_bad_data(), _format_header() (+17 more)

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

### Community 86 - "GatewayCredentialProbeError"
Cohesion: 0.22
Nodes (14): GatewayCredentialProbeReason, GatewayCredentialProbeError, GatewayCredentialProbeResult, RuntimeError, One bounded quote proof through the locked token adapter., Bounded failure safe for operator output. The message is fixed. ``reason`` is a…, RuntimeError, Fake-verification adapter for schwab-py's access-function lifecycle. (+6 more)

### Community 87 - "run_entry_analysis.py"
Cohesion: 0.14
Nodes (28): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+20 more)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.25
Nodes (19): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+11 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.33
Nodes (12): _dashboard(), _expressions(), _panels(), test_candidate_review_metrics_are_folded_into_performance(), test_candidate_runtime_health_is_folded_into_trading(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_preserves_candidate_cohort_and_accounting_checks() (+4 more)

### Community 91 - "test_gateway_shadow_reads.py"
Cohesion: 0.16
Nodes (19): Transport-neutral client contracts for the internal Schwab gateway., _comparisons(), _discrepancies(), asyncio, The shadow comparator must never change what the collector sees, on any path., Current value of one comparison counter; the child is created at zero if absent., A comparison that could not run is not evidence against the gateway., The default flag must leave the counters untouched, not merely unlogged. (+11 more)

### Community 92 - "DatabasePool"
Cohesion: 0.06
Nodes (55): Pool, assert_candidate_safety(), candidate_performance_stats(), CandidateAuditContext, CandidateDecisionQueries, CandidatePaperExecutor, CandidatePerformanceStats, config_sha256() (+47 more)

### Community 93 - "ShadowComparingMarketDataProvider"
Cohesion: 0.14
Nodes (13): _error_code(), _mismatch_code(), _numbers_agree(), Any, date, Exception, Task, Classify a value difference by what the gateway could prove about its freshness. (+5 more)

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

### Community 98 - "run_gateway_credential_probe"
Cohesion: 0.21
Nodes (17): GatewayCredentialProbeSettings, Explicit real-credential inputs for the standalone quote proof only., Any, Read one public quote without resolving an account or exposing response data., run_gateway_credential_probe(), FakeClient, FakeFactory, Path (+9 more)

### Community 99 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 100 - "run_classifier_sweep.py"
Cohesion: 0.26
Nodes (12): sharpe(), win_pct(), _print_same_entry_comparison_table(), Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday…, main(), parse_args(), print_table(), Namespace (+4 more)

### Community 101 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.12
Nodes (15): Fixed defaults, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate, Phase 6 — Standalone production cutover (+7 more)

### Community 102 - "record_equity_market_data.py"
Cohesion: 0.15
Nodes (22): JsonlStreamRecorder, Persistence helpers for recorded equity candles and Schwab stream events., Return the stable output directory for one symbol and session., Non-blocking stream handlers backed by one JSONL file per Schwab service., symbol_directory(), utc_now(), async_main(), _install_signal_handlers() (+14 more)

### Community 103 - "redact"
Cohesion: 0.33
Nodes (5): Any, Small defensive redaction layer for gateway audit metadata., Return a recursively redacted copy suitable for bounded audit metadata., redact(), test_redaction_removes_nested_credentials_and_account_identifiers()

### Community 104 - "test_gateway_issue_keys.py"
Cohesion: 0.14
Nodes (31): docker_inspect(), CaptureFixture, MonkeyPatch, parametrize, Path, test_canonical_fingerprint_is_independent_of_semantically_unordered_fields(), test_cli_bounds_docker_failure_without_raw_exception(), test_cli_exact_and_staging_verification_are_bounded() (+23 more)

### Community 105 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.14
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 106 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.17
Nodes (12): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding (+4 more)

### Community 107 - "test_candidate_schwab_market_data.py"
Cohesion: 0.38
Nodes (14): Schwab market-data client deliberately lacking every account/order operation., asyncio, MonkeyPatch, _reload_client(), _reload_harness(), _settings(), test_close_releases_live_and_retired_clients(), test_failed_reload_keeps_the_working_client_and_marker() (+6 more)

### Community 108 - "Schwab Gateway Foundation: Local Run"
Cohesion: 0.40
Nodes (4): Prepare an internal key file, Run locally, Run the separate Compose proof, Schwab Gateway Foundation: Local Run

### Community 109 - "run_live.py"
Cohesion: 0.07
Nodes (68): clear_readiness(), Prometheus metrics for monitoring., Add a not-ready reason; ``None`` explicitly resets all reasons., Clear only the recovered subsystem's not-ready reason., readiness_snapshot(), set_readiness(), _assert_broker_state_matches_db(), _broker_option_positions() (+60 more)

### Community 110 - "GatewaySettings"
Cohesion: 0.23
Nodes (5): GatewaySettings, BaseSettings, field_validator, Path, Validated configuration for the isolated gateway process.

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

### Community 126 - "test_candidate_provider.py"
Cohesion: 0.33
Nodes (10): make_session_close(), make_snapshot(), asyncio, date, _return(), _return_close(), test_http_and_schwab_provider_contracts_normalize_equally(), test_http_provider_fails_closed_on_mismatched_session_close() (+2 more)

### Community 127 - "api.py"
Cohesion: 0.10
Nodes (43): EquityQuoteProvider, OptionChainProvider, Protocol, SpotPriceProvider, audit_middleware(), chain_metadata(), _error(), health() (+35 more)

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
Cohesion: 0.10
Nodes (12): A document-only bind under read_only: true cannot support atomic replacement.…, The template must parse under the real loader's schema rules., All four trading services bind the token document from one required variable. A…, The gateway replaces the token document atomically, swapping in a new inode. A…, A token_path in YAML silently beats the deployment's SCHWAB_TOKEN_PATH.…, Reachability is the live service's alone, and the network is never created…, test_default_compose_binds_the_token_directory_never_the_document(), test_default_compose_token_binds_require_the_shared_token_directory() (+4 more)

### Community 132 - "AppConfig"
Cohesion: 0.06
Nodes (53): AppConfig, ExecutionSettings, BaseSettings, model_validator, RiskSettings, _assert_live_config_supported(), _age_seconds(), Any (+45 more)

### Community 133 - "C3 — wiring shadow reads into `run_live.py`"
Cohesion: 0.20
Nodes (9): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, The wiring point, Two corrections to the received design points (+1 more)

### Community 134 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "SchwabClientWrapper"
Cohesion: 0.13
Nodes (13): SchwabSettings, _creation_timestamp(), Read the document's re-authorization marker. `creation_timestamp` changes only…, Authenticate and resolve account hash., Rebuild the client if the token document has been re-authorized. schwab-py…, Async wrapper around schwab-py with retry and metrics., Close the client session., SchwabClientWrapper (+5 more)

### Community 137 - "DirectSchwabMarketDataProvider"
Cohesion: 0.10
Nodes (8): DirectSchwabMarketDataProvider, MarketMoversProvider, PriceHistoryProvider, Any, date, Delegate to the current client without owning its lifecycle or changing data., asyncio, test_direct_provider_delegates_without_transforming_results()

### Community 138 - "volume.py"
Cohesion: 0.21
Nodes (12): _as_int(), avg_daily_volume(), compute_rvol(), prior_session_pct_change(), Relative volume helpers using Schwab daily bar history., Average daily volume from completed sessions (excludes today)., Close-to-close percent change for the last completed daily session., Symbols with premarket volume — only these need avg-volume for RVOL filter. (+4 more)

### Community 139 - "DirectProvider"
Cohesion: 0.15
Nodes (6): DirectProvider, FailingDirectProvider, date, A direct provider whose reads raise, to exercise the direct_unavailable path., The only source of returned values. Records every delegated call., test_get_option_chain_returns_before_a_slow_gateway_responds()

### Community 140 - "prepare_args"
Cohesion: 0.15
Nodes (19): patch_approval_1_success(), patch_prepare_success(), patch_proof_prerequisites(), prepare_args(), Neutralize the host proof gates that would read real credentials or real files., A stop-output defect must fail in preflight, not after NDX has already been…, A watchdog prerequisite must fail in preflight, not inside the one authorized…, The cheapest and most failure-prone gate must run first, not after fifteen… (+11 more)

### Community 141 - "order_manager.py"
Cohesion: 0.08
Nodes (41): capped_entry_limit(), entry_fill_within_limit(), Shared entry-price limit policy for production and candidate runtimes., Return a cent-valid debit limit that never exceeds the configured maximum., Return whether an entry fill respects its hard debit ceiling., get_0dte_expiration(), now_utc(), Get today's date as the 0-DTE expiration (SPX has daily expirations). (+33 more)

### Community 142 - "entry_selection_parity.py"
Cohesion: 0.29
Nodes (11): build_entry_selection_parity(), _candidate_payload(), _per_width_payload(), Compare live Schwab entry selection against nearest DB chain snapshot., Return a JSON-serializable Schwab vs DB selection comparison., _candidate(), Tests for Schwab vs DB entry selection parity reporting., _selection() (+3 more)

### Community 143 - "probe_schwab_gateway_credentials.py"
Cohesion: 0.27
Nodes (9): NoReturn, _fail(), _load_runtime_dependencies(), main(), _parser(), ArgumentParser, Run one explicitly authorized Schwab gateway credential proof without starting…, Import failure-prone runtime dependencies inside the bounded CLI path. (+1 more)

### Community 144 - "resolve_db_dsn"
Cohesion: 0.18
Nodes (13): _fitted_density_counts(), _print_pnl_histogram(), Return bucket-height estimates from a Gaussian KDE fit., ASCII histogram with a fitted density curve overlaid on the trade buckets., Resolve the DB connection string for local backtests. Backtests follow the…, resolve_db_dsn(), asyncio, test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot() (+5 more)

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 146 - "backfill_equity_candles.py"
Cohesion: 0.43
Nodes (7): async_main(), main(), parse_args(), Namespace, Path, Backfill one session of one-minute equity candles from Schwab., run()

### Community 147 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 148 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 149 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 150 - "FakeProvider"
Cohesion: 0.44
Nodes (7): candidate(), FakeProvider, market(), asyncio, test_candidate_entry_blocks_fill_above_configured_width_maximum(), test_candidate_entry_is_blocked_when_pin_fails(), test_candidate_entry_pins_before_mark_fill()

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

### Community 155 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (6): main(), parse_args(), date, Namespace, Summarize Schwab vs DB entry selection parity from decision_log. Usage: uv run…, run()

### Community 156 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 157 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 158 - "test_candidate_evaluator_accounting.py"
Cohesion: 0.24
Nodes (8): _gauge_value(), MetricsPool, asyncio, MonkeyPatch, test_candidate_performance_stats_reports_outlier_dependence(), test_min_gap_filter_logs_no_trade_before_candidate_selection(), test_min_gap_filter_preserves_direction_above_threshold(), test_review_progress_counts_only_closed_mark_v1_trades()

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

### Community 166 - "test_run_backtest_db_defaults.py"
Cohesion: 0.21
Nodes (11): candidate_from_trade_row(), Use the first regular-session snapshot for gap direction., select_direction_bar(), _parse_for_asset(), test_backtest_auto_direction_uses_first_regular_session_snapshot(), test_backtest_tracks_explicit_selection_overrides(), test_candidate_from_trade_row_pins_live_trade_fields(), test_default_entry_bar_lookup_rejects_late_fallback() (+3 more)

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
Nodes (26): increment_callback(), manager(), _process_refresh(), AtomicTokenManager, Exception, MonkeyPatch, parametrize, Path (+18 more)

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

### Community 177 - "_approval_2_execute"
Cohesion: 0.19
Nodes (14): _approval_2_execute(), CapturedProcess, _matching_host_processes(), _proof_process_environment(), Return the staged command's own bounded failure code, else the generic code., Require the two credentials in the operator's own environment, by presence…, Return the proof environment: the operator's own, with only these keys…, Prove the reviewed subset imports under the exact interpreter that will run the… (+6 more)

### Community 178 - ".execute"
Cohesion: 0.22
Nodes (6): ClientT, OperationResult, AtomicTokenManager, Run client construction and one operation without letting callbacks escape., TokenReadCallback, TokenWriteCallback

### Community 179 - "SessionClose"
Cohesion: 0.14
Nodes (16): Any, Auditable final regular-session SPX close supplied by the shared feed., SessionClose, date, asyncio, datetime, quote(), snapshot() (+8 more)

### Community 181 - "trade_service.py"
Cohesion: 0.05
Nodes (47): BoundLogger, get_logger(), Structured logging setup with structlog., Configure structlog with JSON output and correlation IDs., Get a structlog logger with optional name., setup_logging(), OptionChainCollector, Any (+39 more)

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (9): High-Impact Trading Changes, Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy (+1 more)

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (8): BUTTERFLYGUY, Butterfly options motif, Technology or trading brand signal, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 184 - "test_value_differences_are_classified_by_provable_freshness"
Cohesion: 0.50
Nodes (5): Exception, parametrize, test_direct_result_is_unchanged_when_the_gateway_errors(), test_gateway_errors_are_classified_by_fixed_code(), test_value_differences_are_classified_by_provable_freshness()

### Community 185 - "7. Operational and observability data"
Cohesion: 0.50
Nodes (4): 7.1 Prometheus metrics, 7.2 Health and readiness endpoints, 7.3 Structured application logs, 7. Operational and observability data

### Community 187 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 188 - "load_spot_series"
Cohesion: 0.50
Nodes (4): load_spot_series(), date, Load spot price series from TimescaleDB for chart generation., spot_rows_to_candles()

### Community 189 - "LockedSchwabClientAdapter"
Cohesion: 0.07
Nodes (38): TokenManagerState, Deterministic fake-only readiness provider for the demo runner., StaticTokenReadinessProvider, _closing_session(), GatewayUpstreamSettings, LockedSchwabMarketDataProvider, Any, BaseSettings (+30 more)

### Community 190 - "daily_report_card_config.py"
Cohesion: 0.33
Nodes (5): load_daily_report_card_config(), BaseModel, Path, Configuration for the daily report card., ReportCardThresholds

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **466 isolated node(s):** `butterfly-guy`, `run_live_performance_cron.sh script`, `run_morning_scan_cron.sh script`, `Objective`, `Current status — 2026-08-10` (+461 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `time_utils.py`, `test_order_manager.py`, `AppConfig`, `test_schwab_client.py`, `DirectSchwabMarketDataProvider`, `volume.py`, `ButterflyCandidate`, `order_manager.py`, `test_gateway_live_provider.py`, `backfill_equity_candles.py`, `_build_collector_market_data`, `._retry`, `trade_service.py`, `LockedSchwabClientAdapter`, `universes.py`, `run_morning_scan.py`, `DatabasePool`, `record_equity_market_data.py`, `run_live.py`, `services/daily_report_card.py`, `report_broker_order_statuses.py`, `api.py`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `get_logger()` connect `trade_service.py` to `run_paper_replay.py`, `time_utils.py`, `ButterflyCandidate`, `order_manager.py`, `run_backtest_db.py`, `MinuteBar`, `core/config.py`, `feed.py`, `news.py`, `AtomicSnapshotStore`, `StrategySettings`, `OptionQuote`, `LockedSchwabClientAdapter`, `DayData`, `ButterflyOrderBuilder`, `universes.py`, `DbDataLoader`, `run_morning_scan.py`, `weekend_review.py`, `GatewayCredentialProbeError`, `run_entry_analysis.py`, `DatabasePool`, `run_classifier_sweep.py`, `test_candidate_schwab_market_data.py`, `run_live.py`, `services/daily_report_card.py`, `api.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `time_utils.py`, `test_order_manager.py`, `AppConfig`, `entry_selection.py`, `ButterflyCandidate`, `run_backtest_db.py`, `FakeProvider`, `MarketSnapshot`, `feed.py`, `ProfitStateMachine`, `SyntheticChainGenerator`, `AtomicSnapshotStore`, `report_exit_mark_parity.py`, `SessionClose`, `trade_service.py`, `StrategySettings`, `DayData`, `DbDataLoader`, `Lease`, `chain_cache.py`, `run_entry_analysis.py`, `DatabasePool`, `test_candidate_provider.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `ButterflyCandidate` (e.g. with `DayResult` and `DrawdownWindow`) actually correct?**
  _`ButterflyCandidate` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `SchwabClientWrapper` (e.g. with `CollectorMarketDataProvider` and `DirectSchwabMarketDataProvider`) actually correct?**
  _`SchwabClientWrapper` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `OptionQuote` (e.g. with `ChainDay` and `DbDataLoader`) actually correct?**
  _`OptionQuote` has 31 INFERRED edges - model-reasoned connections that need verification._