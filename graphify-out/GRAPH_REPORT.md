# Graph Report - Butterflyguy  (2026-10-06)

## Corpus Check
- 437 files · ~901,091 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 46 file(s) not represented in the graph (top: .parquet 15, (none) 9, .jsonl 8)

## Summary
- 6869 nodes · 17248 edges · 416 communities (291 shown, 125 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 1998 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `334994a8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- session_ledger.py
- time_utils.py
- test_order_manager.py
- schwab_gateway_v046_readiness_soak.py
- cli.py
- trade_chart.py
- butterfly_gateway_acceptance.py
- dataclasses
- ButterflyCandidate
- test_research_local.py
- test_gateway_shadow_reads.py
- OptionQuote
- evaluate.py
- save_day
- forex_calendar.py
- Schwab Gateway Credential Proof
- test_research_session_ledger.py
- protocol.py
- schwab_gateway_session_soak.py
- Manifest
- SyntheticChainGenerator
- export.py
- reports/daily_report_card.py
- PositionService
- fidelity.py
- archive_cli.py
- Registry
- test_chain_parser_parity.py
- test_risk_engine.py
- test_collector_daily_bars.py
- ProfitStateMachine
- run_backtest_db.py
- SchwabDataLoader
- run_prospective_execution.py
- research/shadow.py
- validate.py
- Codex Project State
- _assert_broker_state_matches_db
- history.py
- Schwab Gateway Migration Plan
- test_research_decisions.py
- test_gateway_order_book.py
- test_direct_result_is_unchanged_when_the_gateway_times_out_in_real_time
- TradeRecord
- equity_trade_chart.py
- test_research_hypotheses.py
- source_hashes
- run_entry_analysis.py
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- Window A — Token re-authorization (mandatory)
- load_config
- strategy_parameters
- test_weekend_review.py
- simulate.py
- run_check_cycle
- simulation_engine.py
- Standalone SchwabGateway Extraction Plan
- ._retry
- test_position_monitoring.py
- parse_args
- test_trade_service.py
- DbDataLoader
- numpy
- exit_trials/manifest.json
- test_prospective_execution.py
- test_f2_shadow_report.py
- build_market_events.py
- launch_schwab_gateway_session_soak_20260904.sh
- et_us
- Branch Review and Integration Plan
- all_history_trials/manifest.json
- SchwabClientWrapper
- strategy_parameters
- run_classifier_sweep.py
- weekend_review.py
- Architecture
- ButterflyGuy data sources and data types
- Options strategy discovery report
- PositionState
- 9) Capture equity candles and Level II for trade review
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- replay
- mechanism.py
- 2026-07-14 — data audit and research design
- Re-authorization checklist — Saturday 2026-08-15
- _redacted_order_audit
- Capability recorder design
- block_bootstrap_indices
- send_daily_report_card
- datetime
- SimulationEngine
- read_jsonl
- TradePoint
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- test_research_calendar.py
- Window D — the gateway made reachable, started, and watched (2026-08-08)
- Re-authorization checklist — Saturday 2026-08-22
- date
- AGENTS.md
- test_research_quality.py
- StrategySettings
- run_trials.py
- Butterfly Guy
- launch_schwab_gateway_readiness_soak_20260909.sh
- report_trade_ladders.py
- test_gateway_compose.py
- test_daily_report_card.py
- Schwab gateway deployment options
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- GatewayAuthoritativeMarketDataProvider
- test_research_thetadata.py
- DayMarket
- strategy_page.py
- Schwab gateway current status
- test_run_migrations.py
- Schwab Gateway Foundation Smoke Test
- Schwab Single-Token Manager
- ShadowComparingMarketDataProvider
- Strategy Settings
- DiscordNotifier
- test_all_history.py
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- Registration decision package: ThetaData development window (2026-09-29)
- TradeResult
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Width Selection
- ThetaData durable backtesting execution — 2026-10-01
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- Schwab Gateway Multi-Consumer Foundation
- AppConfig
- RunContext
- Helios PAPER gateway cutover — 2026-08-25
- source_hashes
- spx-prospective-2026-09-22/manifest.json
- Ranked hypotheses
- BrokerStateGate
- launch_schwab_gateway_session_soak_20260901.sh
- Bounded proof failure codes and a settled restoration error window — 2026-08-06
- Credential proof passed — 2026-08-06
- Schwab Gateway Foundation: Local Run
- strategy.js
- load_cohort
- test_run_backtest_db.py
- Butterfly Guy Research and Backtest Pipeline Review — 2026-09-27
- spx-prospective-v2-2026-10-02/manifest.json
- Implementation prompt: SPX Schwab recording fidelity (timing, cadence, ThetaData check)
- _MetricsHandler
- butterfly mark
- Preflight stops on the host-executed release — 2026-08-06
- test_gateway_token_manager.py
- CsvDataLoader
- Host-executed proof step
- First token read, and a read-only container filesystem — 2026-08-06
- Operator-named absolute token path
- Live Runbook
- schwab-gateway-phase-7-execution-prompt.md
- test_position_manager.py
- gateway-paper-cutover-handoff-prompt.md
- _build_collector_market_data
- Prospective execution validation — spx-prospective-2026-09-22
- H-TR1 registration — trail armed at +75% with a breakeven floor
- Layered Risk Management
- Geometric butterfly icon
- Ernie (@0DTE) comparison — variant plan (not run)
- test_research_protocol.py
- Options strategy discovery journal
- 2026-09-21 — prospective execution-validation cohort (pre-registration)
- mini_spx/manifest.json
- decision_rules
- test_gateway_ownership_boundaries.py
- 3) Start the SPX stack in Docker
- ConfigModel
- write_history
- black_scholes.py
- Market
- 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)
- Prospective execution validation — spx-prospective-v2-2026-10-02
- MinuteBar
- FailingDirectProvider
- load_report_gateway_settings
- Reducing the weekly re-authorization cost — a scoping question
- test_research_fidelity.py
- test_black_scholes.py
- discover_options_strategy.py
- ThetaDataSource
- test_collector.py
- Option A deployment runbook — Helios, containerized
- direction_compare.py
- dev_studies.py
- quote_rules
- load_chain_day
- files
- prospective_execution.py
- Implementation prompt: finish local ThetaData backtesting support
- docs/README.md
- Phases
- Offline ThetaData research
- run_live_performance_cron.sh
- decision_rules
- Compare Real vs Synthetic Chains
- sim.py
- Cohort automation
- assumptions
- test_run_live.py
- _run_with_stub_token
- endpoint
- SchwabGateway order-book release full-session acceptance — 2026-09-01
- export
- Current Schwab Integration
- CohortError
- record_equity_market_data.py
- Butterfly Guy Code Review — 2026-09-25
- SPX idea sweep — registry (written 2026-09-25 before any variant was run)
- SchwabGateway option-chain latency investigation (2026-09-04)
- ButterflyOrderBuilder
- Historical data management
- entry_pricing.py
- fill_models
- 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0
- test_research_mechanism.py
- spx-idea-sweep-2026-09-25/variants.py
- F2 prospective shadow registration — 2026-10-02
- sessions/2026-03-19/chain.parquet
- sessions/2026-03-19/clock.parquet
- sessions/2026-03-26/chain.parquet
- sessions/2026-03-26/clock.parquet
- sessions/2026-04-07/chain.parquet
- sessions/2026-04-07/clock.parquet
- sessions/2026-04-16/chain.parquet
- sessions/2026-04-16/clock.parquet
- sessions/2026-06-12/chain.parquet
- test_monitoring_leg_replay.py
- sessions/2026-06-12/clock.parquet
- sessions/2026-07-13/clock.parquet
- SPX prospective execution validation v2 registration
- sessions.parquet
- GatewayMarketDataError
- Window C — the two token writers resolved (2026-08-08)
- _build_payload
- ThetaData backtesting readiness and completion plan
- SPX paper-trade review — September 12, 2026
- round2.py
- .generate_chain
- test_backtest_research_integrity.py
- cohort_daily_update.sh
- test_research_accounting.py
- Registration decision package — 2026-09 (for the owner; nothing is registered)
- exit_trials/PLAN.md
- Implementation prompt: SPX session quality and exclusion ledger
- test_market_data_providers.py
- All 108 historical entries: executed exit experiments
- manifest.json
- IVModel
- butterfly-guy
- Variants
- test_collector_cadence.py
- test_get_option_chain_returns_before_a_slow_gateway_responds
- _StatefulRiskQueries
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- DirectSchwabMarketDataProvider
- 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)
- pytest
- generate_live_performance.py
- 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)
- event_calendar.py
- Documentation map
- quote_rules
- HistorySource
- Schwab recording fidelity baseline (2026-10-04)
- assumptions
- Prospective cohort validation, version 2
- endpoint
- Next SPX sweep on vendor history — pre-registration DRAFT (not registered)
- Offline safety-drill record — 2026-07-13
- run_gateway_minute_backfill.sh
- test_strategy_page.py
- test_research_tieset.py
- bs_put_price
- OrderManager
- Dataset
- 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)
- ActiveMonitor
- 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)
- 2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)
- run_export
- test_butterfly_selector.py
- ThetaData data-quality plan and validation amendment (2026-09-28)
- gateway_minute_backfill.py
- ThetaData option history (raw)
- DockerExecSource
- Equity candles and order-book recording
- test_discrepancy_metric_labels_cover_every_declared_code
- OrderRejectedError
- 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- lock_events
- test_research_export.py
- SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan
- XSP improvements — sequential work record, October 6, 2026
- no_sleep
- Critical External-Alert Delivery Proof - 2026-07-15
- render_report.py
- XSP Flat-Runtime Restart Proof - 2026-07-14
- fill_models
- latency.py
- Modules
- run_schwab_fidelity_daily.sh
- Reproduce the SPX exit-policy experiment
- spot_ticks.parquet
- Part A: timing metadata (PR 2)
- SPX frozen baseline: cash-settlement correction
- _history_entry
- _reset_readiness_after_provider_test
- run
- test_comparison_stats.py
- LargeRequestError
- grafana-sql-cpu-2026-10-06.md

## God Nodes (most connected - your core abstractions)
1. `Dataset` - 120 edges
2. `ButterflyCandidate` - 105 edges
3. `OptionQuote` - 96 edges
4. `RunContext` - 96 edges
5. `SchwabClientWrapper` - 93 edges
6. `AppConfig` - 88 edges
7. `load_config()` - 64 edges
8. `Session` - 64 edges
9. `et_us()` - 63 edges
10. `MinuteBar` - 60 edges

## Surprising Connections (you probably didn't know these)
- `Conventions` --references--> `timestamp()`  [INFERRED]
  data/thetadata/README.md → docs/research/spx-exits-2026-09-12/replay.py
- `5.5 Historical minute CSVs` --references--> `CsvDataLoader`  [INFERRED]
  docs/data-sources-inventory.md → src/butterfly_guy/backtest/csv_loader.py
- `3.2 Sweeps rank on the wrong accounting and the wrong metric` --references--> `sharpe()`  [INFERRED]
  docs/reviews/2026-09-27-research-pipeline-review.md → src/butterfly_guy/backtest/metrics.py
- `Equity and research paths` --references--> `SchwabDataLoader`  [INFERRED]
  docs/archive/schwab-gateway/architecture/current-schwab-integration.md → src/butterfly_guy/backtest/schwab_loader.py
- `1. Data and integrity` --references--> `SimulationEngine`  [INFERRED]
  docs/research/registration-decision-2026-09-29.md → src/butterfly_guy/backtest/simulation_engine.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]

## Communities (416 total, 125 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.10
Nodes (26): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), _et(), get_prev_close(), get_vix(), LiveSpread (+18 more)

### Community 1 - "session_ledger.py"
Cohesion: 0.16
Nodes (9): build(), canonical(), cmd_ledger(), Evidence, gate_status(), indexed(), publish(), reconcile() (+1 more)

### Community 2 - "time_utils.py"
Cohesion: 0.03
Nodes (62): M10 — Live settlement wait has no bound, and post-close failures surface late, M11 — A restart with an open trade double-counts the entry cost in daily P&L, M1 — The daily-bar refresh marks itself done after a failure, M3 — Runtime reconciler repair leaves an unmonitored, uncounted trade, M4 — Price-increment rounding is $0.01; SPX complex orders likely require $0.05 (Needs verification), M6 — A restart forgets `_ever_in_profit`, suppressing drawdown exits, M8 — Early closes are hard-coded for 2026 only, M9 — The chain cache rewrites the whole day's JSON on the event loop (+54 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.12
Nodes (62): LiveSpread, broker_fill(), _exit_limits_for_bids(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+54 more)

### Community 4 - "schwab_gateway_v046_readiness_soak.py"
Cohesion: 0.12
Nodes (30): append_jsonl(), bounded_request(), candidate_observation(), diagnostic_probe(), docker_inspect(), endpoint_snapshot(), finalize(), flatness() (+22 more)

### Community 5 - "cli.py"
Cohesion: 0.05
Nodes (63): build_parser(), evaluation_args(), _calibrate_for_registration(), cmd_calibrate(), cmd_catalog(), cmd_coverage(), cmd_diagnose(), cmd_exclude_sessions() (+55 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.10
Nodes (26): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+18 more)

### Community 7 - "butterfly_gateway_acceptance.py"
Cohesion: 0.13
Nodes (14): _endpoints(), test_identity_checks_paper_gateway_and_no_shadow_invariants(), test_preopen_accepts_retried_market_data_unavailable(), test_preopen_allows_documented_after_hours_strategy_readiness(), test_preopen_never_suppresses_other_endpoint_failures(), test_preopen_rejects_every_other_readiness_failure(), endpoint_violations(), http_json() (+6 more)

### Community 8 - "dataclasses"
Cohesion: 0.08
Nodes (15): AbsoluteLossStop, config_exit_rules(), ExitDecision, ExitRule, monitor(), MonitorState, Observation, PreCloseExit (+7 more)

### Community 9 - "ButterflyCandidate"
Cohesion: 0.06
Nodes (27): ButterflyCandidate, main(), parse_args(), print_help(), EntryDecision, find_entry_candidate(), _age_seconds(), vix_expected_move() (+19 more)

### Community 10 - "test_research_local.py"
Cohesion: 0.16
Nodes (21): Record a future BMNR session, normalize(), OneFly, raw(), source(), test_a_spent_holdout_session_imports_and_is_counted(), test_alternate_instrument_identity_and_fractional_grid(), test_cached_daily_inputs_supply_development_closes_without_network() (+13 more)

### Community 11 - "test_gateway_shadow_reads.py"
Cohesion: 0.10
Nodes (28): chain_response(), _comparisons(), DirectProvider, _discrepancies(), RecordingGateway, spot_response(), test_a_direct_payload_that_cannot_be_summarized_is_a_parsing_discrepancy(), test_a_disabled_shadow_records_no_metrics_at_all() (+20 more)

### Community 12 - "OptionQuote"
Cohesion: 0.05
Nodes (36): Models and SDK coupling, XSP held-leg omission follow-up (2026-09-10), _as_float(), _as_int(), rows_to_option_quotes(), fly_mark_value(), OptionQuote, compute_tent_boundaries() (+28 more)

### Community 13 - "evaluate.py"
Cohesion: 0.10
Nodes (16): Status and scope, Fill, TradeFills, evaluate_arm(), paired_bootstrap(), session_vector(), trade_metrics(), Trade (+8 more)

### Community 14 - "save_day"
Cohesion: 0.29
Nodes (4): day_cache_path(), save_day(), date_range(), main()

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (16): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+8 more)

### Community 16 - "Schwab Gateway Credential Proof"
Cohesion: 0.06
Nodes (33): Accepted runtime-baseline proof adapter, Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05 (+25 more)

### Community 17 - "test_research_session_ledger.py"
Cohesion: 0.11
Nodes (14): evidence(), reconcile(), save(), test_audit_import_supporting_conflict_is_visible(), test_calendar_early_close_and_accepted_no_trade(), test_cli_requires_dataset_and_cache(), test_conflicts_are_visible(), test_missing_input_multiple_reasons_and_approved_exclusion() (+6 more)

### Community 18 - "protocol.py"
Cohesion: 0.17
Nodes (11): check_fitted(), check_registered(), check_rerun(), prior_holdout_runs(), ProtocolError, registrations(), _reg(), test_a_second_evaluation_is_only_an_exact_reproduction() (+3 more)

### Community 19 - "schwab_gateway_session_soak.py"
Cohesion: 0.13
Nodes (30): adjudicate_transient_non_200(), assert_production_identity(), background_context(), _confirm_surfaces(), _filtered_gateway_logs(), _finite(), _gateway_error_code(), _health() (+22 more)

### Community 20 - "Manifest"
Cohesion: 0.07
Nodes (34): Volatility term structure, default_cache_root(), Manifest, DailyVol, IntradayVol, daily_table(), export_daily(), ingest_intraday() (+26 more)

### Community 21 - "SyntheticChainGenerator"
Cohesion: 0.23
Nodes (8): SyntheticChainGenerator, make_snapshot_time(), test_atm_call_price_reasonable(), test_generate_chain_has_both_types(), test_generate_chain_strike_count(), test_otm_put_iv_higher_than_otm_call(), test_price_decreases_as_dte_shrinks(), test_spread_positive()

### Community 23 - "export.py"
Cohesion: 0.30
Nodes (9): What is wrong today (verified 2026-10-04 by reading the code), chain_sql(), clock_sql(), daily_bars_sql(), quote_event_sql(), snapshot_count_sql(), spot_ticks_sql(), _underlying() (+1 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.17
Nodes (23): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, count_rejected_orders(), detect_problems(), _extract_order_id(), _extract_trade_leg() (+15 more)

### Community 25 - "PositionService"
Cohesion: 0.02
Nodes (40): Architecture Map, Current architecture, Primary options runtime, Reusable components, Dependency map, Phase 3 Shadow Surfaces (unwired, default off), Provider, 1. Risk accounting — existing fix verified (+32 more)

### Community 26 - "fidelity.py"
Cohesion: 0.04
Nodes (45): Build on what exists, SessionChain, Accumulator, Agreement, _bucket(), _canonical(), compare_session(), fly_widths() (+37 more)

### Community 27 - "archive_cli.py"
Cohesion: 0.09
Nodes (16): add_commands(), _artifact(), _clean(), cmd_audit(), cmd_cache_daily(), cmd_cache_inputs(), cmd_import(), cmd_inventory() (+8 more)

### Community 28 - "Registry"
Cohesion: 0.08
Nodes (26): `DataSource` adapter spec, Auxiliary inputs (manifest schema 2), Data, Event calendar, Fidelity validation (`validate.py`), Overnight futures (ES): audit only, The adapter (`history.py`), The holdout evaluation (`protocol.py`, `holdout`; D9, built 2026-09-29) (+18 more)

### Community 29 - "test_chain_parser_parity.py"
Cohesion: 0.12
Nodes (12): _contract(), _parse_rows(), test_a_map_present_but_empty_produces_zero_everywhere(), test_a_non_numeric_strike_key_diverges_and_the_divergence_is_recorded(), test_a_strike_with_an_empty_option_list_is_excluded_by_all_three(), test_all_three_agree_on_which_expiration_matches(), test_calls_present_with_puts_absent_is_handled_identically_by_all_three(), test_contract_counts_equal_the_rows_the_collector_would_write() (+4 more)

### Community 30 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (15): make_risk_engine(), test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed(), test_can_trade_max_loss(), test_can_trade_max_trades(), test_can_trade_ok() (+7 more)

### Community 31 - "test_collector_daily_bars.py"
Cohesion: 0.52
Nodes (5): _collector(), _daily_candle(), test_daily_bars_failure_leaves_refresh_pending_and_retries(), test_daily_bars_skip_todays_in_progress_candle(), test_daily_bars_use_eastern_session_date_not_host_date()

### Community 32 - "ProfitStateMachine"
Cohesion: 0.14
Nodes (25): QuoteQualitySettings, ProfitState, ProfitStateMachine, make_pos(), make_settings(), test_absolute_loss_stop_fires_without_profit_tent(), test_default_drawdown_confirmation_is_immediate(), test_drawdown_requires_configured_confirmation_polls() (+17 more)

### Community 33 - "run_backtest_db.py"
Cohesion: 0.06
Nodes (53): ChainDay, DrawdownWindow, backtest_entry_price(), candidate_from_trade_row(), day_with_monitoring_bars(), _dd_schedule_label(), discover_dates(), _duration_min() (+45 more)

### Community 35 - "run_prospective_execution.py"
Cohesion: 0.11
Nodes (16): Start-date correction before the first cohort, CohortSpec, cohort_dir_for(), command_init(), command_verify(), default_prospective_start(), frozen_backtest_args(), _jsonable() (+8 more)

### Community 36 - "research/shadow.py"
Cohesion: 0.12
Nodes (20): check_records(), CohortLedger, compare_with_cohort(), default_ref(), _git(), _jsonl(), LedgerError, _m() (+12 more)

### Community 38 - "validate.py"
Cohesion: 0.13
Nodes (22): _compare(), compare_replays(), _dates(), _distribution(), explain(), _first_difference(), _iso(), markdown() (+14 more)

### Community 39 - "Codex Project State"
Cohesion: 0.06
Nodes (33): C3 default-off deployment and gateway hardening (2026-08-10), Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z), Codex Project State, Correction 1 — A3 as written cannot work on Helios, Correction 2 — `easy_client` silently no-ops the re-authorization, Current Phase (+25 more)

### Community 40 - "_assert_broker_state_matches_db"
Cohesion: 0.13
Nodes (33): _assert_broker_state_matches_db(), _expired_trade_has_broker_settlement(), _explicit_fill_details(), _intent_order_ids(), _json_dict(), _open_trade_positions(), _repair_filled_entry_intent(), _repair_filled_exit_intent() (+25 more)

### Community 41 - "history.py"
Cohesion: 0.05
Nodes (27): EventCalendar, _age_fields(), build_session(), BuiltSession, carry_quotes(), daily_range(), GuardedSource, has_print() (+19 more)

### Community 42 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (21): Credential-proof gate, Current migration status, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison, Phase 4 — read-only cutover (+13 more)

### Community 43 - "test_research_decisions.py"
Cohesion: 0.11
Nodes (28): Series, PeakTrailer, restrict_view(), make_chain(), minute(), _clock_session(), test_delayed_index_uses_the_next_clock_time_and_at_least_one_snapshot(), _config() (+20 more)

### Community 44 - "test_gateway_order_book.py"
Cohesion: 0.18
Nodes (10): _recent_payload(), _snapshot(), test_recent_authenticates_and_validates_fresh_contract(), recent(), test_recent_fails_closed_when_gateway_reports_stale_feed(), test_recent_rejects_mismatched_snapshot(), test_stream_authenticates_and_yields_only_requested_contracts(), stream() (+2 more)

### Community 46 - "TradeRecord"
Cohesion: 0.09
Nodes (38): readiness_snapshot(), set_readiness(), TradeRecord, BrokerCashSettlement, test_health_stays_live_while_ready_reports_degraded(), test_readiness_recovery_clears_only_its_own_reason(), test_readiness_tracks_degraded_reason(), get_option_chain() (+30 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.16
Nodes (21): build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay(), _duration() (+13 more)

### Community 48 - "test_research_hypotheses.py"
Cohesion: 0.08
Nodes (26): _calendar(), _features(), _fly(), _quiet(), _session(), _straddle(), StubBase, StubLoader (+18 more)

### Community 49 - "source_hashes"
Cohesion: 0.05
Nodes (40): source_hashes, pyproject.toml, src/butterfly_guy/backtest/chain_cache.py, src/butterfly_guy/backtest/data_loader.py, src/butterfly_guy/backtest/db_loader.py, src/butterfly_guy/backtest/execution_accounting.py, src/butterfly_guy/backtest/__init__.py, src/butterfly_guy/backtest/metrics.py (+32 more)

### Community 50 - "run_entry_analysis.py"
Cohesion: 0.12
Nodes (19): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+11 more)

### Community 51 - "live_performance.py"
Cohesion: 0.09
Nodes (38): chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes(), equity_chart_description() (+30 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.13
Nodes (15): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+7 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.20
Nodes (9): Active Work Item, ButterflyGuy AI Review State, Current Objective, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules, Ranked Issues, Remaining Risks (+1 more)

### Community 54 - "Window A — Token re-authorization (mandatory)"
Cohesion: 0.10
Nodes (20): A0 — Snapshot (read-only), A1 — Disable the keepalive, A2 — Stop the three trading services, A3 — Re-authorize, A4 — Verify the new document, A5 — Start the three services, A6 — Restore the keepalive, A7 — Verify (+12 more)

### Community 55 - "load_config"
Cohesion: 0.08
Nodes (26): main(), main(), config(), load_config(), ProfitManagementSettings, _regimes(), test_allow_live_trading_requires_explicit_env(), test_checked_in_configs_keep_default_regime_bounds() (+18 more)

### Community 56 - "strategy_parameters"
Cohesion: 0.07
Nodes (30): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+22 more)

### Community 57 - "test_weekend_review.py"
Cohesion: 0.08
Nodes (35): build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), format_review_header(), format_trade_recap(), latest_fill_model_cohort(), _parse_metadata(), _post_with_delay() (+27 more)

### Community 58 - "simulate.py"
Cohesion: 0.07
Nodes (29): EntryRule, fit_variant_entry(), History, is_fitted(), is_learning(), delayed_exit_index(), _describe(), entries_for() (+21 more)

### Community 59 - "run_check_cycle"
Cohesion: 0.12
Nodes (8): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), run_check_cycle(), send_discord_alert(), signal_handler()

### Community 60 - "simulation_engine.py"
Cohesion: 0.05
Nodes (21): M7 — Regime names are unvalidated and regime time bounds are ignored, nearest_snapshot(), RegimeDispatch, ProfitProtectorSettings, TimeRegime, get_time_regime(), effective_drawdown_threshold(), ProfitPolicyDecision (+13 more)

### Community 61 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.10
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 62 - "._retry"
Cohesion: 0.08
Nodes (5): Order and account flow, The brief's proposed remedy, and why it is weaker than it looks, The questions to answer before building either, Corrections to the Window H brief, Option A Live Serving (built offline, never deployed)

### Community 63 - "test_position_monitoring.py"
Cohesion: 0.23
Nodes (7): _candidate(), _gateway_contract(), _quotes(), _service(), test_intermittent_missing_held_leg_degrades_then_recovers_without_broker_write(), test_trade_282_uses_gateway_held_leg_when_contract_is_not_stale(), _trade_282_candidate()

### Community 64 - "parse_args"
Cohesion: 0.12
Nodes (21): 5. Live/backtest parity (P2), _asset_drawdowns(), _floatlist(), _intlist(), parse_args(), _sim_parity_fields(), _strlist(), _parse_for_asset() (+13 more)

### Community 65 - "test_trade_service.py"
Cohesion: 0.17
Nodes (21): EntrySettings, _session_open_from_intraday_candles(), _attempt_on(), _bid_quote(), _blocked_payloads(), _candle(), _prev_close_service(), test_attempt_entry_blocks_stale_vix_before_chain_fetch() (+13 more)

### Community 69 - "numpy"
Cohesion: 0.10
Nodes (17): bucket(), main(), bs_gamma(), gex_levels(), main(), round_levels(), triggered_entry(), f() (+9 more)

### Community 70 - "exit_trials/manifest.json"
Cohesion: 0.07
Nodes (27): account_sharpe, baseline_parity, command, created_utc, display_timezone, environment_variables, exit_commission_points, git_sha (+19 more)

### Community 71 - "test_prospective_execution.py"
Cohesion: 0.14
Nodes (33): leg_provenance(), write_manifest(), _baseline(), _candidate(), _cohort(), _mock_cohort_update(), _quotes(), _record() (+25 more)

### Community 72 - "test_f2_shadow_report.py"
Cohesion: 0.05
Nodes (43): atm_straddle(), _fmt(), format_message(), MoveSummary, SessionMove, summarize(), _summary_line(), verdict() (+35 more)

### Community 73 - "build_market_events.py"
Cohesion: 0.17
Nodes (18): bea_releases(), bls_releases(), capture_date(), Fetcher, fomc_rows(), hhmm(), main(), market_rows() (+10 more)

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 75 - "et_us"
Cohesion: 0.10
Nodes (17): breakdowns(), cell(), coverage(), _half(), markdown(), _money(), _r(), session_rows() (+9 more)

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.10
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 78 - "all_history_trials/manifest.json"
Cohesion: 0.05
Nodes (39): account_return_sharpe_marked_drawdown, baseline_scenario_regressions, command, created_utc, dependency_lock_sha256, environment_variables, git_sha, input_hashes (+31 more)

### Community 79 - "SchwabClientWrapper"
Cohesion: 0.12
Nodes (31): SchwabSettings, SchwabClientWrapper, _accessors(), factory(), _account_client(), _http_response(), _reload_harness(), _schwab_returning() (+23 more)

### Community 80 - "strategy_parameters"
Cohesion: 0.06
Nodes (31): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+23 more)

### Community 81 - "run_classifier_sweep.py"
Cohesion: 0.13
Nodes (16): max_consecutive_losses(), max_drawdown(), profit_factor(), sharpe(), win_pct(), _accounting_comparison_rows(), _accounting_metrics(), _print_comparison_table() (+8 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.08
Nodes (14): DatabasePool, run_migrations(), trade_pnl_dollars(), _load_trade(), main(), load_spot_series(), spot_rows_to_candles(), fetch_closed_trades() (+6 more)

### Community 83 - "Architecture"
Cohesion: 0.10
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "ButterflyGuy data sources and data types"
Cohesion: 0.04
Nodes (48): 10. Repository evidence map, 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions (+40 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 87 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.29
Nodes (13): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), _direction_emoji(), _fmt_money(), _fmt_pct(), _fmt_signed() (+5 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.30
Nodes (13): _dashboard(), _expressions(), _panels(), visit(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_position_value_checks_eligible_trades_before_monitoring_history(), test_retired_experimental_runtime_is_absent_from_dashboards(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource() (+5 more)

### Community 92 - "replay"
Cohesion: 0.44
Nodes (10): replay(), points(), settings(), test_all_mark_v1_baselines_reproduce_ledger(), test_commission_once_and_latency_uses_next_quote(), test_drawdown_includes_zero_start_and_positive_winners_only(), test_incomplete_or_duplicate_snapshot_not_forward_filled(), test_no_signal_is_censored_not_last_quote_close() (+2 more)

### Community 93 - "mechanism.py"
Cohesion: 0.15
Nodes (13): bootstrap(), confine(), _f(), fetch_spx(), frame_sha256(), _group(), markdown(), parse_spx_csv() (+5 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.29
Nodes (7): 2026-07-14 — data audit and research design, Data limitations and leakage controls, Final data-driven pass, First-pass result, Predeclared hypotheses (no tuning yet), Second structural pass, Verified data

### Community 95 - "Re-authorization checklist — Saturday 2026-08-15"
Cohesion: 0.13
Nodes (14): Automated warnings before the cadence reset, Before you start, Expected result: no containers restarted, First, watch the reload do its job, Re-authorization checklist — Saturday 2026-08-15, Step 0 — already done, nothing to do, Step 1 — mint the token on zeus, in a real terminal, Step 2 — stage on Helios and verify byte-identical (+6 more)

### Community 96 - "_redacted_order_audit"
Cohesion: 0.39
Nodes (7): _order_symbols(), _order(), test_redacted_audit_excludes_other_underlyings(), test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes(), test_redacted_audit_treats_replaced_as_historical_terminal(), test_order_symbols_walks_child_orders(), _redacted_order_audit()

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "block_bootstrap_indices"
Cohesion: 0.16
Nodes (7): block_bootstrap_indices(), _blocks(), calibrate_gate1(), gates(), test_indices_are_consecutive_blocks(), test_calibration_picks_the_loosest_level_within_the_target_and_tightens_skewed_rules(), Development-window studies

### Community 99 - "send_daily_report_card"
Cohesion: 0.24
Nodes (5): archive_report(), format_equity_trade_chart_caption(), ReportCardResult, send_daily_report_card(), _send_equity_trade_charts()

### Community 101 - "datetime"
Cohesion: 0.03
Nodes (27): Interfaces and contracts, main(), owner_minutes(), get_logger(), clear_readiness(), start_metrics_server(), canonicalize_schwab_chain_symbol(), CollectorMarketDataProvider (+19 more)

### Community 102 - "SimulationEngine"
Cohesion: 0.07
Nodes (29): 6. Canonical and derived analytical data types, Synthetic option-chain data, Accounting and evaluation, Diagnostics (descriptive only), Known differences, Mechanism check for H-TS1 (descriptive only), Parity with the frozen replay, Registry (+21 more)

### Community 103 - "read_jsonl"
Cohesion: 0.23
Nodes (25): daily_runs_path(), deferred_runs_path(), load_manifest(), manifest_path(), read_jsonl(), record_session(), require_frozen_manifest(), summarize_cohort() (+17 more)

### Community 104 - "TradePoint"
Cohesion: 0.12
Nodes (19): compute_stats(), ReportStats, TradePoint, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle() (+11 more)

### Community 105 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.11
Nodes (16): Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Production marker-change proof (2026-08-10), Stale-writer follow-up (2026-08-10), Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result (+8 more)

### Community 107 - "test_research_calendar.py"
Cohesion: 0.26
Nodes (12): _row(), test_committed_calendar_has_a_scheduled_event_of_each_type_every_year(), test_committed_calendar_loads_and_covers_the_range(), test_event_published_on_or_after_the_session_is_invisible_to_it(), test_file_level_checks(), test_hash_follows_content_and_version_follows_file_name(), test_held_is_descriptive_only(), test_invalid_rows_are_rejected() (+4 more)

### Community 109 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 110 - "Re-authorization checklist — Saturday 2026-08-22"
Cohesion: 0.18
Nodes (10): Preconditions — verified 2026-08-22T15:45:36Z, Re-authorization checklist — Saturday 2026-08-22, Step 1 — mint on zeus, in a real terminal, Step 2 — stage on Helios, verify byte-identical, Step 3 — move into place under the C1 lock, Step 4 — watch the reloads; restart only on a *confirmed* failure, Step 5 — verify, host against containers, Step 6 — record (+2 more)

### Community 111 - "date"
Cohesion: 0.24
Nodes (10): cboe_sessions(), expirations(), fetch(), file_path(), _get(), load_no_data(), main(), _path() (+2 more)

### Community 112 - "AGENTS.md"
Cohesion: 0.12
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 114 - "test_research_quality.py"
Cohesion: 0.20
Nodes (10): _cboe(), _day(), test_a_clean_day_passes_every_gate(), test_a_quality_run_never_reads_the_holdout(), test_coverage_crossed_stale_and_timestamp_failures_are_caught(), test_only_a_full_window_pass_opens_earlier_pulls(), test_q5_is_not_evaluable_without_exact_minute_spx_prints(), test_q6_catches_a_close_that_differs_from_cboe() (+2 more)

### Community 115 - "StrategySettings"
Cohesion: 0.20
Nodes (18): StrategySettings, ButterflyBuilder, make_chain(), make_quote(), _quote_filter_settings(), _single_fly_quotes(), test_builder_accepts_zero_bid_leg(), test_builder_breakevens_valid() (+10 more)

### Community 116 - "run_trials.py"
Cohesion: 0.16
Nodes (22): bootstrap_mean_delta(), compare(), ConfirmedMachine, main(), replay(), sha(), variants(), write_csv() (+14 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "launch_schwab_gateway_readiness_soak_20260909.sh"
Cohesion: 0.20
Nodes (10): die(), EVIDENCE_DIR, LAUNCHER, LOG, MONITOR, SESSION_DATE, launch_schwab_gateway_readiness_soak_20260909.sh script, TARGET_EPOCH (+2 more)

### Community 121 - "report_trade_ladders.py"
Cohesion: 0.18
Nodes (10): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+2 more)

### Community 122 - "test_gateway_compose.py"
Cohesion: 0.20
Nodes (3): test_default_compose_binds_the_token_directory_never_the_document(), test_default_compose_token_binds_require_the_shared_token_directory(), test_live_configs_leave_token_path_to_the_environment()

### Community 123 - "test_daily_report_card.py"
Cohesion: 0.13
Nodes (14): DailyReportCardSettings, ReportCardThresholds, build_report_messages(), _format_problems(), candles_to_series(), two_minute_candles(), test_build_daily_report_card_detects_problems(), test_build_report_messages_format() (+6 more)

### Community 124 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 125 - "Window H — verification held; the deadline reminder is mistimed (2026-08-08)"
Cohesion: 0.22
Nodes (9): Deliverables, Finding — the weekly reminder fires after the deadline it protects, Still open after Window H, Task 2 — the Monday check is deferred a fourth time, Tasks 3–6 — all green, verified host-against-container, The deadline in local time — stated because the brief did not, The deadline, re-derived from the document, Window H addendum — a keepalive write observed live (2026-08-09 01:00 UTC) (+1 more)

### Community 127 - "test_research_thetadata.py"
Cohesion: 0.12
Nodes (20): _cboe(), _day_quotes(), files(), _minute_rows(), _quote_csv(), Recorded, _source(), Terminal (+12 more)

### Community 129 - "strategy_page.py"
Cohesion: 0.26
Nodes (12): _json_data_block(), _case_study(), _clock(), _entry_window_et(), _et_after_open(), _minutes_between(), _pct(), _regime_bar() (+4 more)

### Community 130 - "Schwab gateway current status"
Cohesion: 0.25
Nodes (6): Current state, Deferred Helios cleanup, Historical record, Runtime boundaries, Schwab gateway current status, Archived Schwab gateway transition records

### Community 131 - "test_run_migrations.py"
Cohesion: 0.27
Nodes (4): fake_db(), FakeConnection, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 132 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 133 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 134 - "ShadowComparingMarketDataProvider"
Cohesion: 0.11
Nodes (9): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", Two corrections to the received design points, Multi-Agent Review Remediation (offline, still unwired), Next Exact Action, _error_code(), _mismatch_code(), _numbers_agree() (+1 more)

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "DiscordNotifier"
Cohesion: 0.08
Nodes (11): DiscordNotifier, test_alertmanager_failed_resolution_retries_until_accepted(), send_alertmanager(), to_thread(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_alertmanager_payload_has_stable_redacted_fingerprint(), test_notify_entry_includes_trade_stats(), capture() (+3 more)

### Community 137 - "test_all_history.py"
Cohesion: 0.15
Nodes (20): all_stresses(), assert_prior_result(), ledger_parity(), main(), paired_comparison(), select_sources(), points(), test_all_scenarios_equal_original_replays() (+12 more)

### Community 138 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.12
Nodes (9): Corrections to the Window G brief, End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08), ShadowDiscrepancy (+1 more)

### Community 139 - "Registration decision package: ThetaData development window (2026-09-29)"
Cohesion: 0.11
Nodes (18): 1. Data and integrity, 2. Baseline E0 (descriptive; do not tune on it), 3. The hypotheses on the development window (in-sample), 4. Holdout size and power, 5. VIX-smoothing sensitivity, 6.1 Stressed exits below zero: decided, now floored (D3, draft Revision 1), 6.2 Gate 1 passed skip filters too often under the null: decided, now calibrated (D4, draft Revision 4), 6.3 A paired pass against a losing baseline: decided, gate 6 added (D2, draft Revision 5) (+10 more)

### Community 141 - "TradeResult"
Cohesion: 0.17
Nodes (13): _match_round_trips_fifo(), parse_trade_transactions(), rank_trades(), TradeResult, chartable_equity_trades(), _format_trade_stats(), _render_trade_stats(), test_build_equity_trade_chart_png_returns_png_bytes() (+5 more)

### Community 143 - "After-Hours Schwab Gateway Credential-Proof Runbook"
Cohesion: 0.25
Nodes (7): After-Hours Schwab Gateway Credential-Proof Runbook, Approval Boundary 1 — staging, smoke, and service quiescence, Approval Boundary 2 — fresh credential/token read and one AAPL quote, Exact restoration and rollback, Purpose and prohibition, Review gates, Roles and immutable preflight record

### Community 144 - "Schwab Gateway Credential-Proof Evidence Template"
Cohesion: 0.25
Nodes (7): Baseline and staging, Bounded command result, Classification, Restoration and review, Schwab Gateway Credential-Proof Evidence Template, Single-writer and approvals, Window and provenance

### Community 145 - "Width Selection"
Cohesion: 0.26
Nodes (13): Width Selection, NDX Runtime Configuration, SPX Runtime Configuration, SPX VIX Width Buckets, XSP Runtime Configuration, NDX App Container, SPX App Container, XSP App Container (+5 more)

### Community 146 - "ThetaData durable backtesting execution — 2026-10-01"
Cohesion: 0.29
Nodes (7): Code and experiment freeze, Full development eligibility audit, Normalization and frozen baseline — completed, Persistent inputs and provenance, Preserved research boundaries, Reproduce from durable inputs, ThetaData durable backtesting execution — 2026-10-01

### Community 147 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 148 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 149 - "AppConfig"
Cohesion: 0.25
Nodes (12): Decision profiles, AppConfig, ExecutionSettings, RiskSettings, _assert_live_config_supported(), test_live_config_allows_confirmed_xsp_canary(), test_live_config_allows_spx_live_when_explicitly_confirmed(), test_live_config_rejects_gateway_market_data() (+4 more)

### Community 150 - "RunContext"
Cohesion: 0.05
Nodes (47): What the definition hash covers, Hypothesis rules (implemented, not registered), Rules that learn, Costs, ATMEntry, baseline_window(), BaselineEntry, BothSides (+39 more)

### Community 151 - "Helios PAPER gateway cutover — 2026-08-25"
Cohesion: 0.29
Nodes (6): After-hours readiness condition, Helios PAPER gateway cutover — 2026-08-25, Immutable releases, Retained rollback images, Scope, Validation evidence

### Community 152 - "source_hashes"
Cohesion: 0.12
Nodes (17): source_hashes, src/butterfly_guy/backtest/chain_cache.py, src/butterfly_guy/backtest/db_loader.py, src/butterfly_guy/backtest/execution_accounting.py, src/butterfly_guy/backtest/prospective_execution.py, src/butterfly_guy/backtest/simulation_engine.py, src/butterfly_guy/position/position_manager.py, src/butterfly_guy/position/profit_policy.py (+9 more)

### Community 153 - "spx-prospective-2026-09-22/manifest.json"
Cohesion: 0.12
Nodes (15): asset, cohort_id, config, path, sha256, created_at, database_tables, git (+7 more)

### Community 154 - "Ranked hypotheses"
Cohesion: 0.12
Nodes (14): 1. Match the center and width to remaining-session movement, 2. Rank by expected net payoff rather than target reward/risk, 3. Require persistent evidence for discretionary profit exits, 4. Exit on deteriorating butterfly geometry, not just a percentage of the peak, 5. Add an execution-cost entry gate, 6. Condition entry on scheduled events and observed directional conviction, 7. Normalize risk without increasing the position limit, 8. Diversify only after finding a second net-positive component (+6 more)

### Community 155 - "BrokerStateGate"
Cohesion: 0.18
Nodes (5): BrokerStateGate, test_broker_state_gate_records_unsafe_reason(), test_failed_token_reload_blocks_new_entries(), test_token_reload_loop_survives_a_failed_reload(), reload_if_reauthorized()

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

### Community 160 - "strategy.js"
Cohesion: 0.26
Nodes (15): bs(), bucketFor(), failReason(), fly(), ncdf(), pickBest(), quote(), render() (+7 more)

### Community 161 - "load_cohort"
Cohesion: 0.24
Nodes (8): check_previous(), completed_sample(), input_hashes(), load_cohort(), main(), score(), _stats(), summarize()

### Community 162 - "test_run_backtest_db.py"
Cohesion: 0.09
Nodes (18): fetch_prev_close(), _fitted_density_counts(), _print_pnl_histogram(), _DailyBarConnection, test_entry_window_direction_ma_uses_sma_of_prior_closes(), test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), fake_vix(), test_fitted_density_counts_returns_bucket_heights() (+10 more)

### Community 163 - "Butterfly Guy Research and Backtest Pipeline Review — 2026-09-27"
Cohesion: 0.14
Nodes (11): 1. The prospective cohort's daily update was failing (P0), 2. Statistical power (P0 for research planning), 3.1 Consolidate the simulators, 3.2 Sweeps rank on the wrong accounting and the wrong metric, 3.3 Make fly-choice robustness a standard output, 3. Research infrastructure (P1), 4. Data and features known before entry (P1), Butterfly Guy Research and Backtest Pipeline Review — 2026-09-27 (+3 more)

### Community 165 - "spx-prospective-v2-2026-10-02/manifest.json"
Cohesion: 0.12
Nodes (15): asset, cohort_id, config, path, sha256, created_at, database_tables, git (+7 more)

### Community 166 - "Implementation prompt: SPX Schwab recording fidelity (timing, cadence, ThetaData check)"
Cohesion: 0.15
Nodes (13): Baseline (required in PR 1), Behavior, Check the impact on live reads, Deliver, Goal, Hard constraints, Implementation prompt: SPX Schwab recording fidelity (timing, cadence, ThetaData check), Out of scope (+5 more)

### Community 168 - "butterfly mark"
Cohesion: 0.20
Nodes (7): BUTTERFLYGUY, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background, node-and-line network geometry, uppercase geometric wordmark style

### Community 169 - "Preflight stops on the host-executed release — 2026-08-06"
Cohesion: 0.67
Nodes (3): Credential exposure during the window, Preflight stops on the host-executed release — 2026-08-06, Release

### Community 170 - "test_gateway_token_manager.py"
Cohesion: 0.13
Nodes (26): increment_callback(), manager(), _process_refresh(), delayed_increment(), test_callback_failure_preserves_original_and_redacts_error_and_logs(), test_concurrent_managers_serialize_the_entire_refresh_callback(), first_refresh(), second_refresh() (+18 more)

### Community 171 - "CsvDataLoader"
Cohesion: 0.14
Nodes (10): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs, CsvDataLoader, test_csv_loader_reads_chicago_bar_end_timestamps(), test_csv_loader_rejects_a_day_without_prior_inputs() (+2 more)

### Community 172 - "Host-executed proof step"
Cohesion: 0.67
Nodes (3): Host-executed proof step, Release, Workflow consequence the next window must plan for

### Community 175 - "Live Runbook"
Cohesion: 0.25
Nodes (7): During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery, XSP Canary

### Community 177 - "test_position_manager.py"
Cohesion: 0.20
Nodes (15): make_candidate(), make_quote(), make_xsp_candidate(), quote_map(), test_call_butterfly_settles_to_intrinsic_with_spot_below_all_strikes(), test_missing_held_quote_preserves_last_mark_without_returning_stale_state(), test_peak_tracking_rejects_bad_quote_quality(), test_peak_tracking_requires_confirming_polls() (+7 more)

### Community 179 - "_build_collector_market_data"
Cohesion: 0.14
Nodes (10): C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, The wiring point, What C3 does not do, _build_collector_market_data(), test_default_settings_construct_no_gateway_client() (+2 more)

### Community 180 - "Prospective execution validation — spx-prospective-2026-09-22"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-2026-09-22, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 181 - "H-TR1 registration — trail armed at +75% with a breakeven floor"
Cohesion: 0.25
Nodes (8): Data, Entries (frozen, unchanged from the 09-25 harness replica), H-TR1 registration — trail armed at +75% with a breakeven floor, Hypothesis, Pass criteria (all must hold; stressed accounting; per one-lot), Reported but not gating, Result (run once, 2026-10-01, at b0b7215), Run

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (8): Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy, XSP Account and Loss Guards

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (6): BUTTERFLYGUY, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 184 - "Ernie (@0DTE) comparison — variant plan (not run)"
Cohesion: 0.14
Nodes (9): Reproduce, SPX idea sweep — 2026-09-25, Constraints, Data route (pending owner decision), Ernie (@0DTE) comparison — variant plan (not run), Ernie's rules, as stated, Order, Source (+1 more)

### Community 185 - "test_research_protocol.py"
Cohesion: 0.23
Nodes (17): _cli(), _gates(), _holdout(), _no_replay(), _pull_holdout(), _records(), test_a_fitted_rule_is_registered_with_its_value_and_checked_at_the_holdout(), test_a_steady_gain_passes_every_gate() (+9 more)

### Community 186 - "Options strategy discovery journal"
Cohesion: 0.05
Nodes (40): 2026-07-14 — diminishing returns checkpoint, 2026-09-20 — SPX cash-settlement parity correction, 2026-09-21 — SPX executable-side accounting on the settlement-correct replay, 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data), 2026-09-29/30 — Package review, provenance, D7, D10, 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered), 2026-09-29 (later) — D6: no Indices month, 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run) (+32 more)

### Community 187 - "2026-09-21 — prospective execution-validation cohort (pre-registration)"
Cohesion: 0.20
Nodes (10): 2026-09-21 — prospective execution-validation cohort (pre-registration), Checkpoint results, Dry-run rehearsal, Exact commands, Implementation fingerprints at pre-registration, Ledgers and integrity, Pre-registered hypothesis, Quote-handling rules (+2 more)

### Community 188 - "mini_spx/manifest.json"
Cohesion: 0.20
Nodes (9): dataset, dataset_hash, exporter_git_sha, schema_version, source, from_dataset_hash, kind, underlying (+1 more)

### Community 189 - "decision_rules"
Cohesion: 0.22
Nodes (9): decision_rules, checkpoint_trades, early_failure_trades, max_drawdown, max_top3_gross_profit_share, min_executable_entry_coverage, min_profit_factor, primary_hypothesis (+1 more)

### Community 190 - "test_gateway_ownership_boundaries.py"
Cohesion: 0.18
Nodes (4): _source(), test_compose_keeps_each_strategy_default_direct_with_staged_gateway_opt_in(), test_shadow_failure_is_observed_without_changing_the_direct_result(), test_standalone_packages_remain_pinned_and_consumers_import_them_directly()

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - "ConfigModel"
Cohesion: 0.19
Nodes (11): CollectorSettings, ConfigModel, MonitoringSettings, PeakTrackingSettings, VixWidthBucket, test_two_width_vix_bucket_spans_narrow_and_wide_sigmas(), _quote(), test_entry_selection_config_applies_only_explicit_overrides() (+3 more)

### Community 193 - "write_history"
Cohesion: 0.06
Nodes (44): The holdout (`holdout.py`), CostNotApprovedError, coverage(), excluded_sessions(), HistoryPlan, write_history(), guard(), HoldoutSealedError (+36 more)

### Community 194 - "black_scholes.py"
Cohesion: 0.21
Nodes (7): bs_call_price(), bs_gamma(), bs_theta(), _d1(), _d2(), test_gamma_positive(), test_theta_negative_calls()

### Community 196 - "2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)"
Cohesion: 0.25
Nodes (8): 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered), Changes, E0 loses on the development window, Findings about the test itself, Hypotheses, paired with E0 (draft bootstrap: 10-session blocks, 10,000 reps), Integrity, Power (from development vectors; assumes 2022–24 is representative), Recommendation for the owner

### Community 197 - "Prospective execution validation — spx-prospective-v2-2026-10-02"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-v2-2026-10-02, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 198 - "MinuteBar"
Cohesion: 0.06
Nodes (13): load_day(), _parse_bar(), MinuteBar, select_direction_bar(), BiasScoreFilter, RegimeFilter, make_bar(), make_pre_entry_bars() (+5 more)

### Community 200 - "load_report_gateway_settings"
Cohesion: 0.32
Nodes (3): test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings()

### Community 201 - "Reducing the weekly re-authorization cost — a scoping question"
Cohesion: 0.08
Nodes (14): Recommendation, Reducing the weekly re-authorization cost — a scoping question, Status, The alternative worth costing first, The cost being attacked, Why the restarts happen — the actual mechanism, Correction to Window H part 1, Item 1 — the warnings now fire before the deadline (deployed) (+6 more)

### Community 202 - "test_research_fidelity.py"
Cohesion: 0.25
Nodes (10): _chain(), _pair(), _spot(), test_exact_quotes_agree_everywhere(), test_missing_snapshots_and_lateness(), test_missing_strikes_are_counted(), test_one_minute_shift_is_detected(), test_quote_event_time_is_the_basis_when_recorded() (+2 more)

### Community 203 - "test_black_scholes.py"
Cohesion: 0.16
Nodes (7): bs_delta(), test_bs_call_atm(), test_bs_call_deep_itm(), test_bs_call_expired(), test_delta_call_plus_put_parity(), test_delta_call_range(), test_delta_put_range()

### Community 204 - "discover_options_strategy.py"
Cohesion: 0.07
Nodes (51): DatabaseSettings, _is_pm_settled(), select_pm_settled_rows(), select_strike_contract(), atm_pair(), bootstrap_report(), butterfly(), candidate_charts() (+43 more)

### Community 205 - "ThetaDataSource"
Cohesion: 0.12
Nodes (9): _et_to_utc_us(), parse_cboe(), parse_quotes(), ThetaDataError, ThetaDataSource, _ymd(), test_quotes_map_to_utc_and_types_and_a_0_0_row_is_no_quote(), test_source_satisfies_the_history_source_interface() (+1 more)

### Community 206 - "test_collector.py"
Cohesion: 0.18
Nodes (4): test_collect_snapshot_parses_chain(), test_collect_snapshot_row_fields(), test_collect_snapshot_succeeds_when_chain_cache_write_fails(), test_collect_snapshot_writes_chain_cache_off_event_loop()

### Community 207 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.13
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 208 - "direction_compare.py"
Cohesion: 0.33
Nodes (7): directions(), ema(), hma_series(), hourly_closes_before(), hull_rising(), main(), wma()

### Community 209 - "dev_studies.py"
Cohesion: 0.26
Nodes (6): cmd_calibrate(), cmd_check(), cmd_power(), cmd_random_skip(), load(), main()

### Community 210 - "quote_rules"
Cohesion: 0.29
Nodes (7): quote_rules, crossed_market, entry_gap, exit_gap, missing_market, selection, substitution

### Community 211 - "load_chain_day"
Cohesion: 0.23
Nodes (13): chain_cache_path(), chain_journal_path(), load_chain_day(), _read_snapshots(), save_snapshot(), test_chain_cache_path_is_partitioned_by_underlying(), test_load_chain_day_falls_back_to_partitioned_spx_cache(), test_load_chain_day_merges_legacy_json_with_jsonl() (+5 more)

### Community 212 - "files"
Cohesion: 0.29
Nodes (7): rows, sha256, files, daily_bars.parquet, sessions/2026-07-13/chain.parquet, rows, sha256

### Community 213 - "prospective_execution.py"
Cohesion: 0.07
Nodes (32): Shadow on the open cohort, Phase 4: link the stages, ExecutableTrade, append_jsonl(), append_unique(), _breakdown(), build_daily_run_record(), build_manifest() (+24 more)

### Community 214 - "Implementation prompt: finish local ThetaData backtesting support"
Cohesion: 0.17
Nodes (11): Completion checklist, Facts and constraints to carry forward, Implementation prompt: finish local ThetaData backtesting support, Objective, Phase 1 — establish the actual remaining work, Phase 3 — supporting observations and coverage policy, Phase 4 — SPXW 0-DTE integration and execution verification, Phase 5 — SPXW 1-DTE (+3 more)

### Community 215 - "docs/README.md"
Cohesion: 0.09
Nodes (14): Canonical research datasets, Live WebSocket, Recent snapshots, SchwabGateway order books, Completed decision, Distinct datasets and source versions, Ernie comparison reconciliation — 2026-10-02, Provenance and access limits (+6 more)

### Community 216 - "Phases"
Cohesion: 0.18
Nodes (10): Entry-point inventory and fate, Open owner decisions, Phase 0: land what exists, Phase 1: one command surface, Phase 3: commit the analysis that decisions rest on, Phase 5: data upkeep, Phases, Research workflow unification plan — 2026-09-29 (+2 more)

### Community 217 - "Offline ThetaData research"
Cohesion: 0.20
Nodes (8): Baseline and exposure, Commands, Lifecycles, accounting and limits, Mapping and access, Offline ThetaData research, Verification artifacts, Real private artifacts, ThetaData local implementation verification

### Community 220 - "decision_rules"
Cohesion: 0.22
Nodes (9): decision_rules, checkpoint_trades, early_failure_trades, max_drawdown, max_top3_gross_profit_share, min_executable_entry_coverage, min_profit_factor, primary_hypothesis (+1 more)

### Community 222 - "sim.py"
Cohesion: 0.24
Nodes (6): exit_trade(), _mins(), rr_pick(), select_anchor(), Trade, run()

### Community 223 - "Cohort automation"
Cohesion: 0.29
Nodes (6): Check on it, Cohort automation, Install, Known limitation: the SSH key, Retired v1, When the cohort closes

### Community 224 - "assumptions"
Cohesion: 0.33
Nodes (6): assumptions, commission_per_contract, contract_multiplier, contracts_per_butterfly, quantity, stressed_leg_slippage

### Community 225 - "test_run_live.py"
Cohesion: 0.08
Nodes (36): _close_runtime_resources(), _sync_startup_risk_pnl(), _never_awaited(), _run_daily_reset_once(), _synthetic_butterfly_snapshot(), _synthetic_position(), test_collector_market_data_shadow_is_opt_in_and_direct_authoritative(), test_daily_reset_keeps_regime_when_reclassification_fails() (+28 more)

### Community 226 - "_run_with_stub_token"
Cohesion: 0.12
Nodes (7): _run_with_stub_token(), test_token_keepalive_exits_when_the_token_lock_is_held(), test_token_keepalive_honours_schwab_token_path(), test_token_keepalive_refreshes_inside_the_token_lock(), test_token_keepalive_reports_alertmanager_failure(), test_token_keepalive_reports_alertmanager_state(), fake_open()

### Community 227 - "endpoint"
Cohesion: 0.40
Nodes (5): endpoint, min_cash_settlements, min_stressed_winners, rule, target_trades

### Community 228 - "SchwabGateway order-book release full-session acceptance — 2026-09-01"
Cohesion: 0.14
Nodes (12): Credential lineage, EquityScanner coexistence boundary, Post-close decision, Prepared read-only tools, SchwabGateway order-book release full-session acceptance — 2026-09-01, Scope and freeze boundary, Start the full-session harness (unattended), Tuesday preflight — final gate at 06:20-06:29 PDT (+4 more)

### Community 229 - "export"
Cohesion: 0.40
Nodes (5): export, min_session_snapshots, spot_underlyings, strike_margin, underlying

### Community 230 - "Current Schwab Integration"
Cohesion: 0.15
Nodes (12): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current Schwab Integration, Database and messaging dependencies, Discord and operational dependencies, Equity and research paths, Extraction boundaries (+4 more)

### Community 231 - "CohortError"
Cohesion: 0.22
Nodes (4): CohortError, LedgerConflictError, ManifestDriftError, SessionOutOfRangeError

### Community 232 - "record_equity_market_data.py"
Cohesion: 0.06
Nodes (24): Streaming, Streaming flow, setup_logging(), JsonlStreamRecorder, symbol_directory(), utc_now(), write_candle_snapshot(), async_main() (+16 more)

### Community 233 - "Butterfly Guy Code Review — 2026-09-25"
Cohesion: 0.18
Nodes (10): Baseline, Butterfly Guy Code Review — 2026-09-25, Executive summary, Findings index, H1 — Public repository with a self-hosted runner that reaches production, H2 — Previous close silently falls back to the current spot price, High, Method (+2 more)

### Community 234 - "SPX idea sweep — registry (written 2026-09-25 before any variant was run)"
Cohesion: 0.50
Nodes (3): Round 2 — POST-HOC (written after seeing round-1 results; exploratory only), SPX idea sweep — registry (written 2026-09-25 before any variant was run), Variants

### Community 235 - "SchwabGateway option-chain latency investigation (2026-09-04)"
Cohesion: 0.22
Nodes (8): 2026-09-09 runtime follow-up, Cache TTL is hard-capped at 4s in code, not just config, Chain size correlation, Recommendation, Request path (cache miss), SchwabGateway option-chain latency investigation (2026-09-04), Where the time actually goes: scheduler queueing, not the Schwab call itself, XSP held-leg event-age correction (2026-09-11)

### Community 236 - "ButterflyOrderBuilder"
Cohesion: 0.14
Nodes (12): ButterflyOrderBuilder, make_spx_candidate(), test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields(), test_order_session_and_duration(), test_price_format_is_string(), make_candidate() (+4 more)

### Community 237 - "Historical data management"
Cohesion: 0.22
Nodes (9): Canonical normalized datasets, Current inventory, Historical data management, Next milestones, Refresh and verify, Session quality and exclusion ledger, Sources and ownership, Storage and cleaning conventions (+1 more)

### Community 238 - "entry_pricing.py"
Cohesion: 0.17
Nodes (12): capped_entry_limit(), net_price_increment(), round_credit_limit(), round_debit_limit(), _to_increment(), test_capped_entry_limit_never_rounds_above_configured_maximum(), test_debits_round_down_and_credits_round_up(), test_entry_fill_limit_comparison_is_decimal_safe() (+4 more)

### Community 239 - "fill_models"
Cohesion: 0.50
Nodes (4): fill_models, corrected_midpoint, marketable, stressed_marketable

### Community 240 - "2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0"
Cohesion: 0.40
Nodes (5): 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0, Decisions, How the floor is implemented (`7b1f229`), Re-run under the floor, Still open

### Community 241 - "test_research_mechanism.py"
Cohesion: 0.18
Nodes (10): _inputs(), _sessions(), _synthetic(), test_decision_rule_on_planted_and_null_effects(), test_first_session_uses_the_prior_development_session(), test_prior_values_come_from_the_previous_spx_session(), test_rows_outside_the_window_are_dropped_before_computing(), test_session_without_a_prior_vix1d_is_excluded() (+2 more)

### Community 242 - "spx-idea-sweep-2026-09-25/variants.py"
Cohesion: 0.19
Nodes (18): baseline_entry(), open_spot(), fn(), et_ts(), Fly, open_trade(), boot_ci(), c1() (+10 more)

### Community 243 - "F2 prospective shadow registration — 2026-10-02"
Cohesion: 0.22
Nodes (7): Definition, Endpoint and gates (fixed now, judged only at the endpoint), Evidence that motivated it (all in-sample or partly used), F2 prospective shadow registration — 2026-10-02, How it is scored, Operation, F2 draft scorer review — 2026-10-03

### Community 244 - "sessions/2026-03-19/chain.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-03-19/chain.parquet, rows, sha256

### Community 245 - "sessions/2026-03-19/clock.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-03-19/clock.parquet, rows, sha256

### Community 246 - "sessions/2026-03-26/chain.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-03-26/chain.parquet, rows, sha256

### Community 247 - "sessions/2026-03-26/clock.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-03-26/clock.parquet, rows, sha256

### Community 248 - "sessions/2026-04-07/chain.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-04-07/chain.parquet, rows, sha256

### Community 249 - "sessions/2026-04-07/clock.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-04-07/clock.parquet, rows, sha256

### Community 250 - "sessions/2026-04-16/chain.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-04-16/chain.parquet, rows, sha256

### Community 251 - "sessions/2026-04-16/clock.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-04-16/clock.parquet, rows, sha256

### Community 252 - "sessions/2026-06-12/chain.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-06-12/chain.parquet, rows, sha256

### Community 253 - "test_monitoring_leg_replay.py"
Cohesion: 0.70
Nodes (3): _bar(), test_day_with_monitoring_bars_adds_live_poll_timestamps(), test_day_with_monitoring_bars_keeps_existing_bar_for_same_timestamp()

### Community 254 - "sessions/2026-06-12/clock.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-06-12/clock.parquet, rows, sha256

### Community 255 - "sessions/2026-07-13/clock.parquet"
Cohesion: 0.67
Nodes (3): sessions/2026-07-13/clock.parquet, rows, sha256

### Community 256 - "SPX prospective execution validation v2 registration"
Cohesion: 0.29
Nodes (6): Activation and paper deployment evidence, Completed development baseline, Operational checks, Registered experiment, Retiring v1, SPX prospective execution validation v2 registration

### Community 257 - "sessions.parquet"
Cohesion: 0.67
Nodes (3): sessions.parquet, rows, sha256

### Community 259 - "GatewayMarketDataError"
Cohesion: 0.17
Nodes (9): ContractTiming, _finite_number(), GatewayMarketDataError, _nonnegative_integer(), OmittedContract, _optional_number(), _require_usable_observation(), _same_symbol() (+1 more)

### Community 260 - "Window C — the two token writers resolved (2026-08-08)"
Cohesion: 0.25
Nodes (8): C1 — the operator chose the shared lock, C3 plan produced, and a stale design point corrected, Durability decided, monitoring still open, Housekeeping, Multi-consumer shape — confirmed sound, with two wrinkles, Proven on the host by the production path, at zero extra token writes, Still open, Window C — the two token writers resolved (2026-08-08)

### Community 261 - "_build_payload"
Cohesion: 0.26
Nodes (12): _allowed_roots(), _build_payload(), main(), _order_symbols(), _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses(), test_payload_excludes_non_spx_orders() (+4 more)

### Community 262 - "ThetaData backtesting readiness and completion plan"
Cohesion: 0.29
Nodes (7): Data inventory and remaining limits, Defined steps to complete broad SPXW backtesting, Execution follow-through, Separate extensions, ThetaData backtesting readiness and completion plan, What is ready, Working smoke command and evidence

### Community 263 - "SPX paper-trade review — September 12, 2026"
Cohesion: 0.33
Nodes (5): Evidence and scope, Findings, Mechanism worth testing, Research pipeline and proposed experiment, SPX paper-trade review — September 12, 2026

### Community 264 - "round2.py"
Cohesion: 0.33
Nodes (8): ev_rank_factory(), r1(), r2(), r5(), ratio_at(), ror(), e0(), k1()

### Community 266 - "test_backtest_research_integrity.py"
Cohesion: 0.14
Nodes (17): _entry_debit(), _exit_credit(), _finite_quote_side(), inspect_quote_market(), price_frozen_trade(), QuoteMarket, snapshot_at_or_before(), snapshot_keys() (+9 more)

### Community 268 - "test_research_accounting.py"
Cohesion: 0.17
Nodes (22): price_trade(), fly_quotes(), _blown_out(), _delayed(), _option_quotes(), _path(), test_cash_settlement_is_free_in_every_model(), test_delayed_exit_falls_back_to_settlement_or_stays_unpriced() (+14 more)

### Community 294 - "Registration decision package — 2026-09 (for the owner; nothing is registered)"
Cohesion: 0.25
Nodes (7): Decisions only the owner can make, H-EV1 — skip pre-entry releases (`HEV1`), H-LV1 — skip low-VIX calls (`HLV1`), H-SN1 — σ-normalised selector (`HSN1`), H-TS1 — rich one-day implied (`HTS1`), Optional H-EV2 — skip FOMC statement days (not implemented), Registration decision package — 2026-09 (for the owner; nothing is registered)

### Community 297 - "exit_trials/PLAN.md"
Cohesion: 0.40
Nodes (3): Exit trials fixed before execution — September 13, 2026, Executed SPX exit trials, Reproduce

### Community 298 - "Implementation prompt: SPX session quality and exclusion ledger"
Cohesion: 0.22
Nodes (8): Boundaries, Deliverable and scope, Existing inputs, Implementation prompt: SPX session quality and exclusion ledger, Ledger behavior, Read first and establish the checkout, Reconciliation targets, Verification and completion criteria

### Community 299 - "test_market_data_providers.py"
Cohesion: 0.18
Nodes (28): _bar(), _contract(), _observation(), test_direct_provider_delegates_without_transforming_results(), test_direct_provider_observations_are_empty(), test_empty_extended_session_is_allowed_but_other_flags_remain_fatal(), test_gateway_provider_adapts_history_and_combines_sessions(), test_gateway_provider_adapts_typed_spot_and_full_chain() (+20 more)

### Community 301 - "All 108 historical entries: executed exit experiments"
Cohesion: 0.33
Nodes (4): All-history extension fixed before execution, All 108 historical entries: executed exit experiments, Outputs, Run locally

### Community 304 - "manifest.json"
Cohesion: 0.15
Nodes (12): created_utc, entry_prices, exit_commission_points, files, raw/checkout-source-hashes.json, raw/deployment.txt, raw/export.jsonl, raw/monitor.jsonl (+4 more)

### Community 314 - "Variants"
Cohesion: 0.18
Nodes (8): D — direction, E — entry trigger (structural levels), P — strike placement, T — trail start and basis (likely the largest gap), TW — Time Warp (1DTE Batman), from the full transcript read, Variants, W — widths (decided: apply live after the cohort endpoint), _bucket_sigmas()

### Community 315 - "test_collector_cadence.py"
Cohesion: 0.08
Nodes (21): et(), FakeClock, _run(), StopLoopError, test_a_stall_alerts_once_and_never_catches_up(), test_default_config_keeps_the_old_loop(), test_first_tick_is_the_open_and_last_is_before_the_early_close(), test_next_tick() (+13 more)

### Community 351 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 353 - "2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only), Call-only entry filters, Moving-average direction versus the gap rule, Reproduction, Robustness to fly choice (near-tied flies), Setup and accounting, Why the backtest and live paper disagree

### Community 355 - "generate_live_performance.py"
Cohesion: 0.20
Nodes (11): no_trade_reason(), best_trade(), reference_spot(), strategy_script(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate() (+3 more)

### Community 356 - "2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)"
Cohesion: 0.33
Nodes (6): 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only), Data and harness, Hypothesis registered for a future forward cohort (not applied), Low-VIX diagnosis, Sweep results (stressed net P&L), Why the baseline fails in H2

### Community 357 - "event_calendar.py"
Cohesion: 0.12
Nodes (3): _date(), MarketEvent, parse_row()

### Community 358 - "Documentation map"
Cohesion: 0.22
Nodes (9): Architecture, Archive, Artifact retention, Command ownership, Documentation map, Operations and data, Research, Reviews and agent handoffs (+1 more)

### Community 359 - "quote_rules"
Cohesion: 0.29
Nodes (7): quote_rules, crossed_market, entry_gap, exit_gap, missing_market, selection, substitution

### Community 360 - "HistorySource"
Cohesion: 0.08
Nodes (15): 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data), 2026-09-28 — stage 5: corrected data decision, housekeeping, ThetaData readiness (stubbed), H-TS1 mechanism check (development window, descriptive), Built (provider-independent, tested on synthetic data), Data decision (corrected), Development coverage and in-sample E0, H-TS1 mechanism check (DESCRIPTIVE — development window — not a rule evaluation), Housekeeping, Housekeeping (+7 more)

### Community 361 - "Schwab recording fidelity baseline (2026-10-04)"
Cohesion: 0.25
Nodes (5): After Parts A and B, Headline numbers, How approximate this is, Run, Schwab recording fidelity baseline (2026-10-04)

### Community 362 - "assumptions"
Cohesion: 0.33
Nodes (6): assumptions, commission_per_contract, contract_multiplier, contracts_per_butterfly, quantity, stressed_leg_slippage

### Community 363 - "Prospective cohort validation, version 2"
Cohesion: 0.40
Nodes (4): Corrections for newly registered cohorts, Keep the original experiment separate, Prospective cohort validation, version 2, Verification

### Community 364 - "endpoint"
Cohesion: 0.40
Nodes (5): endpoint, min_cash_settlements, min_stressed_winners, rule, target_trades

### Community 365 - "Next SPX sweep on vendor history — pre-registration DRAFT (not registered)"
Cohesion: 0.29
Nodes (6): Baseline, Data and split (fixed now, before any vendor data is seen), Hypotheses, Next SPX sweep on vendor history — pre-registration DRAFT (not registered), Out of scope for this sweep, Primary metric and gate

### Community 366 - "Offline safety-drill record — 2026-07-13"
Cohesion: 0.29
Nodes (6): Drill findings fixed, Follow-up — 2026-07-14, Offline safety-drill record — 2026-07-13, Remaining do-now work, Result, Verification

### Community 368 - "test_strategy_page.py"
Cohesion: 0.16
Nodes (10): _params(), test_generate_refuses_missing_strategy_config(), test_generate_writes_strategy_page_beside_report(), fake_build_report(), fake_connect(), test_page_has_no_inline_executable_script(), test_page_renders_config_values_and_no_leftover_tokens(), test_params_follow_the_spx_config() (+2 more)

### Community 369 - "test_research_tieset.py"
Cohesion: 0.18
Nodes (7): draw_keys(), selector_pool(), _cand(), test_draws_are_keyed_by_session_and_direction(), test_promotion_shift_is_rr_gap_over_combined_cost_sensitivity(), test_run_scores_tie_sets_unless_told_not_to(), test_selector_pool_applies_center_tolerance_and_rr_max_per_width()

### Community 370 - "bs_put_price"
Cohesion: 0.29
Nodes (4): bs_put_price(), test_bs_put_call_parity(), test_bs_put_deep_itm(), test_bs_put_expired()

### Community 371 - "OrderManager"
Cohesion: 0.09
Nodes (13): Historical Cycle Checkpoints, Low / Info, Strengths worth keeping, entry_fill_within_limit(), get_0dte_expiration(), now_utc(), AmbiguousOrderError, _assert_entry_fill_within_limit() (+5 more)

### Community 372 - "Dataset"
Cohesion: 0.05
Nodes (33): chain_to_table(), Dataset, dataset_hash(), dense_chain_from_rows(), session_dir(), SessionClock, table_to_chain(), write_table() (+25 more)

### Community 373 - "2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only), Cohort runner move (2026-09-27) and a labeling note, Cohort shadow (exploratory, three sessions), Exit-latency stress, Parity, Research core and data, Variant registry

### Community 374 - "ActiveMonitor"
Cohesion: 0.15
Nodes (4): The fix, ActiveMonitor, install_shutdown_handler(), test_sigterm_cancels_supervised_loops_and_task_group_exits_cleanly()

### Community 375 - "2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)"
Cohesion: 0.33
Nodes (6): 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered), Consequences, Decision and change, Still open, The calibration study (scratch, development data), What it gives on the real dataset (in-process, nothing registered)

### Community 376 - "2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)"
Cohesion: 0.33
Nodes (6): 2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only), Data and harness, Hypothesis for a future test (not applied), Post-hoc middle ground (defined after the table above), Pre-declared variants (written before running), Reproduction

### Community 377 - "run_export"
Cohesion: 0.18
Nodes (6): DataSource, export_session(), has_timing_columns(), _read_csv(), run_export(), _ts_us()

### Community 378 - "test_butterfly_selector.py"
Cohesion: 0.48
Nodes (5): make_candidate(), test_regular_best_rr_selection_still_uses_rr_target(), test_vix_centered_selection_blocks_when_no_candidate_near_target(), test_vix_centered_selection_uses_rr_target_after_center_filter(), test_vix_selection_rejects_cheap_extreme_rr_tail_candidate()

### Community 379 - "ThetaData data-quality plan and validation amendment (2026-09-28)"
Cohesion: 0.14
Nodes (14): Artifacts referenced, Decisions for the owner, P&L replay (report only, 2026-09-29), Phase 1: code (no data pulled), Phase 1 implementation notes (2026-09-28), Phase 2: re-pull the validation window, then check quality, Phase 2 re-run and Phase 3 result (2026-09-28), Phase 2 result (2026-09-28): FAIL on Q4 (+6 more)

### Community 382 - "gateway_minute_backfill.py"
Cohesion: 0.32
Nodes (3): check(), dump(), main()

### Community 383 - "ThetaData option history (raw)"
Cohesion: 0.33
Nodes (6): Conventions, Layout, Reading, Sets, The spent holdout (2024-07-01 to 2026-03-12), ThetaData option history (raw)

### Community 385 - "Equity candles and order-book recording"
Cohesion: 0.40
Nodes (4): Backfill candles, Equity candles and order-book recording, Historical limitation, Operational caution

### Community 388 - "2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)"
Cohesion: 0.40
Nodes (5): 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered), Consequences for H-TS1 alone (k = 1), Decision and change, Still open, Study before the decision

### Community 389 - "Exact-SHA Deployment Proof - 2026-07-15"
Cohesion: 0.33
Nodes (5): Deployment and verification, Exact-SHA Deployment Proof - 2026-07-15, Follow-up rollback and restore drill, Preconditions and validation, Scope

### Community 390 - "XSP Manual-Flatten Evidence - 2026-07-16"
Cohesion: 0.33
Nodes (5): Fail-closed proof, Post-action reconciliation and paper restore, Redacted evidence, Result, XSP Manual-Flatten Evidence - 2026-07-16

### Community 392 - "test_research_export.py"
Cohesion: 0.24
Nodes (5): ExportPlan, FakeSource, test_bars_only_refresh_records_the_landed_settlement(), test_recorded_quote_ages_and_event_times_are_exported(), test_sessions_without_quote_ages_export_exactly_as_before()

### Community 393 - "SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan"
Cohesion: 0.10
Nodes (19): Access, credential and timestamps, Assessment, Endpoints and request plan, Licence (individual plans), Plans and prices (as read), Purchase checklist, SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan, ThetaData: public-docs findings and purchase checklist (2026-09-28) (+11 more)

### Community 394 - "XSP improvements — sequential work record, October 6, 2026"
Cohesion: 0.11
Nodes (17): 2. XSP exit replay — baseline established before tuning, 3. Earlier trailer — experiment fixed before execution, 4. Independent width policy — no recent behavioral difference, 5. Execution and settlement evidence — proxy discrepancy measured, Reproduce, Result: refine; do not activate this candidate, XSP improvements — sequential work record, October 6, 2026, 2. High — the trailer and exit-quality floor conflict for modest peaks (+9 more)

### Community 396 - "Critical External-Alert Delivery Proof - 2026-07-15"
Cohesion: 0.40
Nodes (4): Critical External-Alert Delivery Proof - 2026-07-15, Implementation reviewed, Scope, Supervised delivery and deduplication result

### Community 397 - "render_report.py"
Cohesion: 0.36
Nodes (5): main(), result_table(), main(), money(), table()

### Community 398 - "XSP Flat-Runtime Restart Proof - 2026-07-14"
Cohesion: 0.40
Nodes (4): Preconditions, Restart and verification, Scope, XSP Flat-Runtime Restart Proof - 2026-07-14

### Community 399 - "fill_models"
Cohesion: 0.50
Nodes (4): fill_models, corrected_midpoint, marketable, stressed_marketable

### Community 400 - "latency.py"
Cohesion: 0.31
Nodes (6): _weekdays(), collect(), _csv(), polls_sql(), trades_sql(), _us()

### Community 402 - "run_schwab_fidelity_daily.sh"
Cohesion: 0.67
Nodes (3): BUTTERFLY_RESEARCH_CACHE, research(), run_schwab_fidelity_daily.sh script

### Community 403 - "Reproduce the SPX exit-policy experiment"
Cohesion: 0.22
Nodes (7): Acquisition actually performed, Conditional end-to-end confirmation, Offline reproduction, Output map, Replay rules and costs, Reproduce the SPX exit-policy experiment, SPX exit-policy research — September 12, 2026

### Community 404 - "spot_ticks.parquet"
Cohesion: 0.67
Nodes (3): spot_ticks.parquet, rows, sha256

### Community 407 - "Part A: timing metadata (PR 2)"
Cohesion: 0.29
Nodes (5): Collector, Part A: timing metadata (PR 2), Research export, Schema (migration `011_snapshot_timing.sql`, idempotent like 004), Tests

### Community 408 - "SPX frozen baseline: cash-settlement correction"
Cohesion: 0.29
Nodes (6): Assumptions, Corrected implementation fingerprints, Reproduction commands, Result, Settlement evidence and reconciliation, SPX frozen baseline: cash-settlement correction

### Community 409 - "_history_entry"
Cohesion: 0.43
Nodes (5): bars_changes(), _bars_key(), _git_sha(), _history_entry(), _spx_closes()

### Community 412 - "run"
Cohesion: 0.40
Nodes (3): main(), parse_args(), run()

### Community 413 - "test_comparison_stats.py"
Cohesion: 0.57
Nodes (5): _capture(), _make_result(), test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **1120 isolated node(s):** `created_utc`, `range`, `trades`, `provider`, `original_acquisition_utc` (+1115 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2700 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **125 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `time_utils.py`, `_build_payload`, `butterfly_gateway_acceptance.py`, `ButterflyCandidate`, `Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)`, `OptionQuote`, `PositionService`, `SchwabDataLoader`, `Codex Project State`, `_assert_broker_state_matches_db`, `Schwab Gateway Migration Plan`, `_build_collector_market_data`, `._retry`, `Reducing the weekly re-authorization cost — a scoping question`, `Branch Review and Integration Plan`, `DirectSchwabMarketDataProvider`, `Capability recorder design`, `test_run_live.py`, `send_daily_report_card`, `datetime`, `record_equity_market_data.py`, `Window F — the refresh token re-authorized, six days early (2026-08-08)`, `OrderManager`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `run_paper_replay.py`, `time_utils.py`, `test_order_manager.py`, `dataclasses`, `test_backtest_research_integrity.py`, `OptionQuote`, `test_research_accounting.py`, `RunContext`, `PositionService`, `run_backtest_db.py`, `Butterfly Guy Research and Backtest Pipeline Review — 2026-09-27`, `test_position_manager.py`, `Variants`, `simulation_engine.py`, `test_position_monitoring.py`, `test_prospective_execution.py`, `prospective_execution.py`, `datetime`, `SimulationEngine`, `ButterflyOrderBuilder`, `test_research_tieset.py`, `OrderManager`, `StrategySettings`, `test_butterfly_selector.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `Repository Agent Instructions` connect `Layered Risk Management` to `docs/README.md`, `Butterfly Guy`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `Dataset` (e.g. with `cmd_cache_inputs()` and `cmd_import()`) actually correct?**
  _`Dataset` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 58 inferred relationships involving `ButterflyCandidate` (e.g. with `Models and SDK coupling` and `6. Canonical and derived analytical data types`) actually correct?**
  _`ButterflyCandidate` has 58 INFERRED edges - model-reasoned connections that need verification._
- **Are the 55 inferred relationships involving `OptionQuote` (e.g. with `Models and SDK coupling` and `Reusable components`) actually correct?**
  _`OptionQuote` has 55 INFERRED edges - model-reasoned connections that need verification._