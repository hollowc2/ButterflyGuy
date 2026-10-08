# Graph Report - Butterflyguy  (2026-10-07)

## Corpus Check
- 440 files · ~903,622 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 45 file(s) not represented in the graph (top: .parquet 15, (none) 9, .jsonl 8)

## Summary
- 6843 nodes · 18895 edges · 335 communities (285 shown, 50 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 2574 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `71a6d9f8`
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
- subprocess
- lifecycle.py
- OptionQuote
- test_research_local.py
- test_gateway_shadow_reads.py
- compute_tent_boundaries
- simulate.py
- pathlib
- forex_calendar.py
- Schwab Gateway Credential Proof
- test_research_session_ledger.py
- protocol.py
- schwab_gateway_session_soak.py
- pandas
- .generate_chain
- export.py
- reports/daily_report_card.py
- main
- quality.py
- history.py
- Registry
- iter_chain_options
- test_risk_engine.py
- datetime
- ProfitStateMachine
- run_backtest_db.py
- SchwabDataLoader
- run_prospective_execution.py
- research/shadow.py
- exits.py
- validate.py
- Codex Project State
- _assert_broker_state_matches_db
- date
- Schwab Gateway Migration Plan
- test_research_decisions.py
- test_gateway_order_book.py
- compare_session
- TradeRecord
- equity_trade_chart.py
- RunContext
- source_hashes
- test_position_data_diagnostics.py
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- Window A — Token re-authorization (mandatory)
- load_config
- strategy_parameters
- weekend_review.py
- test_research_learning.py
- health_monitor.py
- run_classifier_sweep.py
- Standalone SchwabGateway Extraction Plan
- SchwabClientWrapper
- test_position_monitoring.py
- parse_args
- config.py
- realized_vs_implied.py
- DbDataLoader
- numpy
- exit_trials/manifest.json
- test_prospective_execution.py
- test_f2_shadow_report.py
- build_market_events.py
- launch_schwab_gateway_session_soak_20260904.sh
- et_us
- Branch Review and Integration Plan
- thetadata_prep.py
- all_history_trials/manifest.json
- test_schwab_client.py
- strategy_parameters
- ._retry
- asyncio
- Architecture
- ButterflyGuy data sources and data types
- Options strategy discovery report
- state_machine.py
- 9) Capture equity candles and Level II for trade review
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- test_bias_filter.py
- replay.py
- mechanism.py
- 2026-07-14 — data audit and research design
- Re-authorization checklist — Saturday 2026-08-15
- gateway_cutover_flatness_audit.py
- Capability recorder design
- block_bootstrap_indices
- test_chain_utils.py
- EntrySelectionResult
- position_service.py
- ButterflyCandidate
- fidelity.py
- performance_chart.py
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- .history
- EventCalendar
- 2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)
- Window D — the gateway made reachable, started, and watched (2026-08-08)
- Re-authorization checklist — Saturday 2026-08-22
- thetadata_download.py
- AGENTS.md
- test_research_quality.py
- 3. ButterflyGuy-owned TimescaleDB data
- test_exit_trials.py
- Butterfly Guy
- launch_schwab_gateway_readiness_soak_20260909.sh
- report_trade_ladders.py
- ChainObservation
- test_daily_report_card.py
- Schwab gateway deployment options
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- GatewayAuthoritativeMarketDataProvider
- test_research_thetadata.py
- DayMarket
- parse_quotes
- Schwab gateway current status
- 1. Charles Schwab API
- Schwab Gateway Foundation Smoke Test
- Schwab Single-Token Manager
- ShadowComparingMarketDataProvider
- Strategy Settings
- DiscordNotifier
- run_trials.py
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- Registration decision package: ThetaData development window (2026-09-29)
- test_research_sweep_ports.py
- build_daily_report_card
- 2. Other external and public sources
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Width Selection
- ThetaData durable backtesting execution — 2026-10-01
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- Schwab Gateway Multi-Consumer Foundation
- select_pm_settled_rows
- entry.py
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
- f2_shadow_report.py
- test_run_backtest_db.py
- Butterfly Guy Research and Backtest Pipeline Review — 2026-09-27
- ._ema
- spx-prospective-v2-2026-10-02/manifest.json
- Part C: daily Schwab-vs-ThetaData fidelity check (PR 1)
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
- PositionManager
- gateway-paper-cutover-handoff-prompt.md
- _build_collector_market_data
- Prospective execution validation — spx-prospective-2026-09-22
- H-TR1 registration — trail armed at +75% with a breakeven floor
- Layered Risk Management
- Geometric butterfly icon
- Research core
- test_research_protocol.py
- Options strategy discovery journal
- 2026-09-21 — prospective execution-validation cohort (pre-registration)
- mini_spx/manifest.json
- decision_rules
- test_gateway_ownership_boundaries.py
- 3) Start the SPX stack in Docker
- Hist
- pytest
- 2026-09-21 — SPX executable-side accounting on the settlement-correct replay
- Market
- 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)
- Prospective execution validation — spx-prospective-v2-2026-10-02
- BiasScoreFilter
- FailingDirectProvider
- load_report_gateway_settings
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- test_research_fidelity.py
- discover_options_strategy.py
- ThetaDataSource
- 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)
- Option A deployment runbook — Helios, containerized
- files
- dev_studies.py
- quote_rules
- chain_cache.py
- files
- prospective_execution.py
- Implementation prompt: finish local ThetaData backtesting support
- docs/README.md
- Phases
- Offline ThetaData research
- run_live_performance_cron.sh
- decision_rules
- Compare Real vs Synthetic Chains
- math
- Cohort automation
- assumptions
- test_run_live.py
- _run_with_stub_token
- endpoint
- SchwabGateway order-book release full-session acceptance — 2026-09-01
- export
- Current Schwab Integration
- 2026-10-02 — edge search: hold to settlement with a VIX floor (development + validation; nothing registered)
- equity_market_data.py
- Held-position market-data diagnostics
- SPX idea sweep — registry (written 2026-09-25 before any variant was run)
- PositionState
- ButterflyOrderBuilder
- Historical data management
- entry_pricing.py
- fill_models
- 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0
- test_research_mechanism.py
- spx-idea-sweep-2026-09-25/variants.py
- 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data)
- sessions/2026-03-19/chain.parquet
- sessions/2026-03-19/clock.parquet
- sessions/2026-03-26/chain.parquet
- sessions/2026-03-26/clock.parquet
- sessions/2026-04-07/chain.parquet
- sessions/2026-04-07/clock.parquet
- sessions/2026-04-16/chain.parquet
- sessions/2026-04-16/clock.parquet
- sessions/2026-06-12/chain.parquet
- ChainDay
- sessions/2026-06-12/clock.parquet
- sessions/2026-07-13/clock.parquet
- SPX prospective execution validation v2 registration
- sessions.parquet
- 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered)
- providers.py
- ._spawn_background
- report_broker_order_statuses.py
- Recorded
- SPX paper-trade review — September 12, 2026
- round2.py
- execution_accounting.py
- cohort_daily_update.sh
- test_research_accounting.py
- Registration decision package — 2026-09 (for the owner; nothing is registered)
- exit_trials/PLAN.md
- Implementation prompt: SPX session quality and exclusion ledger
- test_market_data_providers.py
- All 108 historical entries: executed exit experiments
- manifest.json
- butterfly-guy
- Ernie (@0DTE) comparison — variant plan (not run)
- test_collector_cadence.py
- _StatefulRiskQueries
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- DirectSchwabMarketDataProvider
- 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)
- 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)
- Documentation map
- quote_rules
- 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)
- assumptions
- Prospective cohort validation, version 2
- endpoint
- Next SPX sweep on vendor history — pre-registration DRAFT (not registered)
- Offline safety-drill record — 2026-07-13
- run_gateway_minute_backfill.sh
- generate_live_performance.py
- test_research_tieset.py
- run_live.py
- Dataset
- 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)
- install_shutdown_handler
- 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)
- 2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)
- ThetaData data-quality plan and validation amendment (2026-09-28)
- learning.py
- gateway_minute_backfill.py
- DockerExecSource
- Equity candles and order-book recording
- test_discrepancy_metric_labels_cover_every_declared_code
- 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan
- XSP improvements — sequential work record, October 6, 2026
- Critical External-Alert Delivery Proof - 2026-07-15
- json
- XSP Flat-Runtime Restart Proof - 2026-07-14
- fill_models
- run_schwab_fidelity_daily.sh
- ProfitManagementSettings
- spot_ticks.parquet
- fly_settlement_value
- _reset_readiness_after_provider_test
- grafana-sql-cpu-2026-10-06.md

## God Nodes (most connected - your core abstractions)
1. `Dataset` - 120 edges
2. `ButterflyCandidate` - 110 edges
3. `OptionQuote` - 99 edges
4. `RunContext` - 96 edges
5. `SchwabClientWrapper` - 93 edges
6. `AppConfig` - 88 edges
7. `load_config()` - 66 edges
8. `Session` - 64 edges
9. `MinuteBar` - 63 edges
10. `et_us()` - 63 edges

## Surprising Connections (you probably didn't know these)
- `Conventions` --references--> `timestamp()`  [INFERRED]
  data/thetadata/README.md → docs/research/spx-exits-2026-09-12/replay.py
- `5.5 Historical minute CSVs` --references--> `CsvDataLoader`  [INFERRED]
  docs/data-sources-inventory.md → src/butterfly_guy/backtest/csv_loader.py
- `3.2 Sweeps rank on the wrong accounting and the wrong metric` --references--> `sharpe()`  [INFERRED]
  docs/reviews/2026-09-27-research-pipeline-review.md → src/butterfly_guy/backtest/metrics.py
- `1. Data and integrity` --references--> `SimulationEngine`  [INFERRED]
  docs/research/registration-decision-2026-09-29.md → src/butterfly_guy/backtest/simulation_engine.py
- `Decision and change` --references--> `SimulationEngine`  [INFERRED]
  docs/research/strategy-discovery-journal.md → src/butterfly_guy/backtest/simulation_engine.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]

## Communities (335 total, 50 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.08
Nodes (31): detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close(), get_vix(), LiveSpread (+23 more)

### Community 1 - "session_ledger.py"
Cohesion: 0.19
Nodes (10): add_command(), build(), canonical(), cmd_ledger(), Evidence, gate_status(), indexed(), publish() (+2 more)

### Community 2 - "time_utils.py"
Cohesion: 0.06
Nodes (39): M8 — Early closes are hard-coded for 2026 only, _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_premarket_window(), is_trading_day(), _last_weekday() (+31 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.11
Nodes (63): OrderRejectedError, LiveSpread, broker_fill(), _exit_limits_for_bids(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi() (+55 more)

### Community 4 - "schwab_gateway_v046_readiness_soak.py"
Cohesion: 0.11
Nodes (30): append_jsonl(), bounded_request(), candidate_observation(), diagnostic_probe(), docker_inspect(), endpoint_snapshot(), finalize(), flatness() (+22 more)

### Community 5 - "cli.py"
Cohesion: 0.06
Nodes (59): build_parser(), evaluation_args(), _calibrate_for_registration(), cmd_calibrate(), cmd_catalog(), cmd_coverage(), cmd_diagnose(), cmd_exclude_sessions() (+51 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.10
Nodes (26): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+18 more)

### Community 7 - "subprocess"
Cohesion: 0.13
Nodes (14): _endpoints(), test_identity_checks_paper_gateway_and_no_shadow_invariants(), test_preopen_accepts_retried_market_data_unavailable(), test_preopen_allows_documented_after_hours_strategy_readiness(), test_preopen_never_suppresses_other_endpoint_failures(), test_preopen_rejects_every_other_readiness_failure(), endpoint_violations(), http_json() (+6 more)

### Community 8 - "lifecycle.py"
Cohesion: 0.10
Nodes (13): 6.4 Early closes: decided, now fixed (D5), config_exit_rules(), ExitDecision, ExitRule, monitor(), MonitorState, PreCloseExit, capability_check() (+5 more)

### Community 9 - "OptionQuote"
Cohesion: 0.04
Nodes (66): Decision profiles, StrategySettings, _as_float(), _as_int(), rows_to_option_quotes(), fly_mark_value(), OptionQuote, fly_bid_value() (+58 more)

### Community 10 - "test_research_local.py"
Cohesion: 0.19
Nodes (20): Record a future BMNR session, normalize(), OneFly, raw(), source(), test_a_spent_holdout_session_imports_and_is_counted(), test_alternate_instrument_identity_and_fractional_grid(), test_alternate_instrument_replay_with_attributable_inputs() (+12 more)

### Community 11 - "test_gateway_shadow_reads.py"
Cohesion: 0.10
Nodes (29): test_shadow_failure_is_observed_without_changing_the_direct_result(), chain_response(), _comparisons(), DirectProvider, _discrepancies(), RecordingGateway, spot_response(), test_a_direct_payload_that_cannot_be_summarized_is_a_parsing_discrepancy() (+21 more)

### Community 12 - "compute_tent_boundaries"
Cohesion: 0.40
Nodes (3): compute_tent_boundaries(), _resolve_iv(), implied_vol()

### Community 13 - "simulate.py"
Cohesion: 0.07
Nodes (19): Status and scope, Fill, TradeFills, is_learning(), restrict_view(), us_to_datetime(), _iso(), _r() (+11 more)

### Community 14 - "pathlib"
Cohesion: 0.13
Nodes (4): load_day(), _parse_bar(), save_day(), MinuteBar

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (16): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+8 more)

### Community 16 - "Schwab Gateway Credential Proof"
Cohesion: 0.06
Nodes (33): Accepted runtime-baseline proof adapter, Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05 (+25 more)

### Community 17 - "test_research_session_ledger.py"
Cohesion: 0.12
Nodes (13): evidence(), reconcile(), save(), test_audit_import_supporting_conflict_is_visible(), test_calendar_early_close_and_accepted_no_trade(), test_conflicts_are_visible(), test_missing_input_multiple_reasons_and_approved_exclusion(), test_non_expiration_is_independently_documented_and_eom_is_preserved() (+5 more)

### Community 18 - "protocol.py"
Cohesion: 0.15
Nodes (12): check_fitted(), check_registered(), check_rerun(), describe(), prior_holdout_runs(), ProtocolError, registrations(), _reg() (+4 more)

### Community 19 - "schwab_gateway_session_soak.py"
Cohesion: 0.13
Nodes (30): adjudicate_transient_non_200(), assert_production_identity(), background_context(), _confirm_surfaces(), _filtered_gateway_logs(), _finite(), _gateway_error_code(), _health() (+22 more)

### Community 20 - "pandas"
Cohesion: 0.07
Nodes (33): Volatility term structure, DailyVol, IntradayVol, _merge(), daily_table(), export_daily(), ingest_intraday(), intraday_table() (+25 more)

### Community 21 - ".generate_chain"
Cohesion: 0.05
Nodes (29): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+21 more)

### Community 23 - "export.py"
Cohesion: 0.07
Nodes (34): `DataSource` adapter spec, What is wrong today (verified 2026-10-04 by reading the code), dense_chain_from_rows(), bars_changes(), _bars_key(), chain_sql(), clock_sql(), daily_bars_sql() (+26 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.15
Nodes (22): 6. Canonical and derived analytical data types, Synthetic option-chain data, AccountBalances, CashMovement, count_rejected_orders(), _extract_order_id(), _extract_trade_leg(), _float() (+14 more)

### Community 25 - "main"
Cohesion: 0.02
Nodes (40): Architecture Map, Current architecture, Primary options runtime, Dependency map, Phase 3 Shadow Surfaces (unwired, default off), Collector, 1. Risk accounting — existing fix verified, H1 — Public repository with a self-hosted runner that reaches production (+32 more)

### Community 26 - "quality.py"
Cohesion: 0.11
Nodes (19): Build on what exists, _quality(), arbitrage(), _bad_cells(), _cells(), _dst_week(), history_entry(), index_file_crosscheck() (+11 more)

### Community 27 - "history.py"
Cohesion: 0.05
Nodes (38): Fidelity validation (`validate.py`), The adapter (`history.py`), The holdout evaluation (`protocol.py`, `holdout`; D9, built 2026-09-29), Vendor history (ThetaData, subscribed 2026-09-28), add_commands(), _artifact(), _clean(), cmd_audit() (+30 more)

### Community 28 - "Registry"
Cohesion: 0.17
Nodes (12): _canonical(), record_hash(), Registry, RegistryError, _add(), _placeholder(), test_a_port_inherits_the_placeholder_stage_and_counts_once(), test_a_port_needs_a_matching_unported_placeholder() (+4 more)

### Community 29 - "iter_chain_options"
Cohesion: 0.12
Nodes (13): iter_chain_options(), _contract(), _parse_rows(), test_a_map_present_but_empty_produces_zero_everywhere(), test_a_non_numeric_strike_key_diverges_and_the_divergence_is_recorded(), test_a_strike_with_an_empty_option_list_is_excluded_by_all_three(), test_all_three_agree_on_which_expiration_matches(), test_calls_present_with_puts_absent_is_handled_identically_by_all_three() (+5 more)

### Community 30 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (15): make_risk_engine(), test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed(), test_can_trade_max_loss(), test_can_trade_max_trades(), test_can_trade_ok() (+7 more)

### Community 31 - "datetime"
Cohesion: 0.10
Nodes (23): main(), main(), _print_comparison_table(), previous_mon_fri(), _collector(), _daily_candle(), test_daily_bars_failure_leaves_refresh_pending_and_retries(), test_daily_bars_skip_todays_in_progress_candle() (+15 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.15
Nodes (24): QuoteQualitySettings, ProfitStateMachine, make_pos(), make_settings(), test_absolute_loss_stop_fires_without_profit_tent(), test_default_drawdown_confirmation_is_immediate(), test_drawdown_requires_configured_confirmation_polls(), test_drawdown_requires_min_peak_profit_ratio() (+16 more)

### Community 33 - "run_backtest_db.py"
Cohesion: 0.06
Nodes (55): max_consecutive_losses(), max_drawdown(), profit_factor(), sharpe(), DrawdownWindow, _accounting_comparison_rows(), _accounting_metrics(), candidate_from_trade_row() (+47 more)

### Community 34 - "SchwabDataLoader"
Cohesion: 0.10
Nodes (6): Equity and research paths, Market-data flow, day_cache_path(), SchwabDataLoader, date_range(), main()

### Community 35 - "run_prospective_execution.py"
Cohesion: 0.09
Nodes (25): Start-date correction before the first cohort, CohortError, CohortSpec, deferred_runs_path(), load_manifest(), verify_cohort(), backtest_entry_price(), merge_chains() (+17 more)

### Community 36 - "research/shadow.py"
Cohesion: 0.12
Nodes (20): check_records(), CohortLedger, compare_with_cohort(), default_ref(), _git(), _jsonl(), LedgerError, _m() (+12 more)

### Community 37 - "exits.py"
Cohesion: 0.09
Nodes (16): ProfitProtectorSettings, TimeRegime, get_time_regime(), effective_drawdown_threshold(), ProfitPolicyDecision, profitprotector_floor_decision(), AbsoluteLossStop, Observation (+8 more)

### Community 38 - "validate.py"
Cohesion: 0.08
Nodes (35): chain_to_table(), Manifest, session_dir(), SessionChain, SessionClock, table_to_chain(), build_helios_clock_dataset(), _compare() (+27 more)

### Community 39 - "Codex Project State"
Cohesion: 0.06
Nodes (34): C3 default-off deployment and gateway hardening (2026-08-10), Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z), Codex Project State, Correction 1 — A3 as written cannot work on Helios, Correction 2 — `easy_client` silently no-ops the re-authorization, Current Phase (+26 more)

### Community 40 - "_assert_broker_state_matches_db"
Cohesion: 0.14
Nodes (27): ActiveMonitor, _assert_broker_state_matches_db(), broker_fill_payload(), _filled_entry_without_trade(), _filled_exit_with_open_trade(), _run_reconciler_once(), test_active_monitor_reports_trade_only_while_task_runs(), test_filled_entry_intent_rejects_wrong_broker_ratio() (+19 more)

### Community 41 - "date"
Cohesion: 0.05
Nodes (24): 2026-09-28 — stage 5: corrected data decision, housekeeping, ThetaData readiness (stubbed), H-TS1 mechanism check (development window, descriptive), Data decision (corrected), H-TS1 mechanism check (DESCRIPTIVE — development window — not a rule evaluation), Housekeeping, ThetaData readiness (stubbed, nothing bought, nothing downloaded), _age_fields(), build_session(), BuiltSession (+16 more)

### Community 42 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (21): Credential-proof gate, Current migration status, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison, Phase 4 — read-only cutover (+13 more)

### Community 43 - "test_research_decisions.py"
Cohesion: 0.16
Nodes (22): Series, PeakTrailer, make_chain(), minute(), _clock_session(), test_delayed_index_uses_the_next_clock_time_and_at_least_one_snapshot(), _config(), _monitor() (+14 more)

### Community 44 - "test_gateway_order_book.py"
Cohesion: 0.18
Nodes (11): _recent_payload(), _snapshot(), test_client_rejects_unsafe_or_ambiguous_inputs(), test_recent_authenticates_and_validates_fresh_contract(), recent(), test_recent_fails_closed_when_gateway_reports_stale_feed(), test_recent_rejects_mismatched_snapshot(), test_stream_authenticates_and_yields_only_requested_contracts() (+3 more)

### Community 45 - "compare_session"
Cohesion: 0.12
Nodes (11): Accumulator, Agreement, _bucket(), compare_session(), FlyStats, _label(), _parity_spot(), _quoted() (+3 more)

### Community 46 - "TradeRecord"
Cohesion: 0.09
Nodes (38): readiness_snapshot(), set_readiness(), TradeRecord, BrokerCashSettlement, final_regular_session_close_from_candles(), test_health_stays_live_while_ready_reports_degraded(), test_readiness_recovery_clears_only_its_own_reason(), test_readiness_tracks_degraded_reason() (+30 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.14
Nodes (27): TradeResult, build_equity_trade_chart_png(), chartable_equity_trades(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume() (+19 more)

### Community 48 - "RunContext"
Cohesion: 0.09
Nodes (25): cached_entries(), EntryRule, RunContext, EventDaySkipEntry, PriorRatioFilter, ReleaseSkipEntry, session_features(), _calendar() (+17 more)

### Community 49 - "source_hashes"
Cohesion: 0.05
Nodes (40): source_hashes, pyproject.toml, src/butterfly_guy/backtest/chain_cache.py, src/butterfly_guy/backtest/data_loader.py, src/butterfly_guy/backtest/db_loader.py, src/butterfly_guy/backtest/execution_accounting.py, src/butterfly_guy/backtest/__init__.py, src/butterfly_guy/backtest/metrics.py (+32 more)

### Community 50 - "test_position_data_diagnostics.py"
Cohesion: 0.28
Nodes (16): held_leg_evidence(), candidate(), chain_quotes(), response(), shadow(), test_completed_shadow_samples_are_rate_limited(), test_held_leg_records_the_filtered_quote_instead_of_losing_its_evidence(), test_missing_contract_and_chain_failure_are_distinct() (+8 more)

### Community 51 - "live_performance.py"
Cohesion: 0.08
Nodes (39): chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes(), equity_chart_description() (+31 more)

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
Cohesion: 0.05
Nodes (41): load_config(), analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time() (+33 more)

### Community 56 - "strategy_parameters"
Cohesion: 0.07
Nodes (30): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+22 more)

### Community 57 - "weekend_review.py"
Cohesion: 0.10
Nodes (39): trade_point_from_row(), TradePoint, build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_executable_pnl() (+31 more)

### Community 58 - "test_research_learning.py"
Cohesion: 0.10
Nodes (21): BaselineEntry, BothSides, StraddleAnchoredEntry, FittedFilter, Variant, _late(), _ctx(), _decisions() (+13 more)

### Community 59 - "health_monitor.py"
Cohesion: 0.15
Nodes (8): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), run_check_cycle(), send_discord_alert(), signal_handler()

### Community 60 - "run_classifier_sweep.py"
Cohesion: 0.10
Nodes (14): win_pct(), main(), parse_args(), print_table(), summarize_adaptive(), summarize_baseline(), classify_market_regime(), GapRegimeFilter (+6 more)

### Community 61 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.09
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 62 - "SchwabClientWrapper"
Cohesion: 0.08
Nodes (9): Order and account flow, The alternative worth costing first, The brief's proposed remedy, and why it is weaker than it looks, The questions to answer before building either, Corrections to the Window H brief, The correction that forced the restarts, _creation_timestamp(), SchwabClientWrapper (+1 more)

### Community 63 - "test_position_monitoring.py"
Cohesion: 0.21
Nodes (8): _candidate(), _gateway_contract(), _quotes(), _service(), test_intermittent_missing_held_leg_degrades_then_recovers_without_broker_write(), get_option_chain(), test_trade_282_uses_gateway_held_leg_when_contract_is_not_stale(), _trade_282_candidate()

### Community 64 - "parse_args"
Cohesion: 0.10
Nodes (24): 5. Live/backtest parity (P2), _asset_drawdowns(), _floatlist(), _intlist(), parse_args(), select_direction_bar(), _sim_parity_fields(), spx_sweep_retired_message() (+16 more)

### Community 65 - "config.py"
Cohesion: 0.05
Nodes (48): AppConfig, CollectorSettings, ConfigModel, DatabaseSettings, EntrySettings, ExecutionSettings, MonitoringSettings, PeakTrackingSettings (+40 more)

### Community 66 - "realized_vs_implied.py"
Cohesion: 0.15
Nodes (15): atm_straddle(), _fmt(), format_message(), MoveSummary, SessionMove, summarize(), _summary_line(), verdict() (+7 more)

### Community 69 - "numpy"
Cohesion: 0.13
Nodes (21): bucket(), main(), directions(), ema(), hma_series(), hourly_closes_before(), hull_rising(), main() (+13 more)

### Community 70 - "exit_trials/manifest.json"
Cohesion: 0.07
Nodes (27): account_sharpe, baseline_parity, command, created_utc, display_timezone, environment_variables, exit_commission_points, git_sha (+19 more)

### Community 71 - "test_prospective_execution.py"
Cohesion: 0.12
Nodes (50): daily_runs_path(), manifest_path(), read_jsonl(), summarize_cohort(), trades_path(), write_manifest(), current_summary(), _baseline() (+42 more)

### Community 72 - "test_f2_shadow_report.py"
Cohesion: 0.08
Nodes (28): database(), vix(), row(), summary(), test_all_winning_sample_passes_profit_factor_gate(), test_cash_settlement_equals_cohort_under_every_model(), test_chronological_order_controls_drawdown_and_stop(), test_drawdown_exactly_at_limit_does_not_stop() (+20 more)

### Community 73 - "build_market_events.py"
Cohesion: 0.17
Nodes (19): test_migrations_add_decision_log_underlying_column(), bea_releases(), bls_releases(), capture_date(), Fetcher, fomc_rows(), hhmm(), main() (+11 more)

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 75 - "et_us"
Cohesion: 0.09
Nodes (23): compare_to_ledger(), breakdowns(), cell(), coverage(), _half(), markdown(), _money(), _r() (+15 more)

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.10
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 78 - "all_history_trials/manifest.json"
Cohesion: 0.05
Nodes (39): account_return_sharpe_marked_drawdown, baseline_scenario_regressions, command, created_utc, dependency_lock_sha256, environment_variables, git_sha, input_hashes (+31 more)

### Community 79 - "test_schwab_client.py"
Cohesion: 0.13
Nodes (26): SchwabSettings, _accessors(), factory(), _account_client(), no_sleep(), _reload_harness(), _schwab_returning(), test_close_releases_both_the_live_and_retired_sessions() (+18 more)

### Community 80 - "strategy_parameters"
Cohesion: 0.06
Nodes (31): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+23 more)

### Community 81 - "._retry"
Cohesion: 0.13
Nodes (7): Authentication and token lifecycle, Shared-token risk, _http_response(), test_retry_does_not_retry_non_retryable_4xx(), test_retry_exhausted_on_429_reports_rate_limit(), test_retry_retries_5xx_and_429_then_succeeds(), test_retry_retries_transport_errors()

### Community 82 - "asyncio"
Cohesion: 0.04
Nodes (31): get_logger(), setup_logging(), DatabasePool, run_migrations(), trade_pnl_dollars(), async_main(), main(), parse_args() (+23 more)

### Community 83 - "Architecture"
Cohesion: 0.10
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "ButterflyGuy data sources and data types"
Cohesion: 0.11
Nodes (18): 10. Repository evidence map, 4. Shared database tables visible to the same DB account, 5.1 Application YAML configuration, 5.2 Environment variables and `.env`, 5.3 `tokens.json`, 5.4 Universe and metadata files, 5.5 Historical minute CSVs, 5.6 Local daily bar cache (+10 more)

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
Cohesion: 0.20
Nodes (16): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), archive_report(), build_report_messages(), _direction_emoji(), _fmt_money() (+8 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.30
Nodes (13): _dashboard(), _expressions(), _panels(), visit(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_position_value_checks_eligible_trades_before_monitoring_history(), test_retired_experimental_runtime_is_absent_from_dashboards(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource() (+5 more)

### Community 91 - "test_bias_filter.py"
Cohesion: 0.19
Nodes (4): make_bar(), make_pre_entry_bars(), TestComputeOr, TestComputeVwap

### Community 92 - "replay.py"
Cohesion: 0.25
Nodes (16): main(), main(), metrics(), path_for(), replay(), timestamp(), write_csv(), points() (+8 more)

### Community 93 - "mechanism.py"
Cohesion: 0.15
Nodes (13): bootstrap(), confine(), _f(), fetch_spx(), frame_sha256(), _group(), markdown(), parse_spx_csv() (+5 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.29
Nodes (7): 2026-07-14 — data audit and research design, Data limitations and leakage controls, Final data-driven pass, First-pass result, Predeclared hypotheses (no tuning yet), Second structural pass, Verified data

### Community 95 - "Re-authorization checklist — Saturday 2026-08-15"
Cohesion: 0.13
Nodes (14): Automated warnings before the cadence reset, Before you start, Expected result: no containers restarted, First, watch the reload do its job, Re-authorization checklist — Saturday 2026-08-15, Step 0 — already done, nothing to do, Step 1 — mint the token on zeus, in a real terminal, Step 2 — stage on Helios and verify byte-identical (+6 more)

### Community 96 - "gateway_cutover_flatness_audit.py"
Cohesion: 0.42
Nodes (5): _order(), test_redacted_audit_excludes_other_underlyings(), test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes(), test_redacted_audit_treats_replaced_as_historical_terminal(), _redacted_order_audit()

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "block_bootstrap_indices"
Cohesion: 0.16
Nodes (7): block_bootstrap_indices(), _blocks(), calibrate_gate1(), gates(), test_indices_are_consecutive_blocks(), test_calibration_picks_the_loosest_level_within_the_target_and_tightens_skewed_rules(), Development-window studies

### Community 99 - "test_chain_utils.py"
Cohesion: 0.25
Nodes (13): _chain(), _row(), _symbols(), test_ambiguous_snapshot_rows_are_dropped(), test_custom_key_fields_group_rows(), test_duplicates_with_no_pm_settled_contract_are_skipped(), test_duplicates_with_two_pm_settled_contracts_are_skipped(), test_ndx_and_ndxp_at_one_strike_yields_ndxp() (+5 more)

### Community 100 - "EntrySelectionResult"
Cohesion: 0.27
Nodes (9): EntrySelectionResult, build_entry_selection_parity(), _candidate_payload(), _per_width_payload(), _candidate(), _selection(), test_build_entry_selection_parity_detects_ranking_flip(), test_build_entry_selection_parity_marks_match_when_widths_agree() (+1 more)

### Community 101 - "position_service.py"
Cohesion: 0.05
Nodes (19): M10 — Live settlement wait has no bound, and post-close failures surface late, M11 — A restart with an open trade double-counts the entry cost in daily P&L, M1 — The daily-bar refresh marks itself done after a failure, M3 — Runtime reconciler repair leaves an unmonitored, uncounted trade, M4 — Price-increment rounding is $0.01; SPX complex orders likely require $0.05 (Needs verification), M6 — A restart forgets `_ever_in_profit`, suppressing drawdown exits, M7 — Regime names are unvalidated and regime time bounds are ignored, M9 — The chain cache rewrites the whole day's JSON on the event loop (+11 more)

### Community 102 - "ButterflyCandidate"
Cohesion: 0.07
Nodes (26): Models and SDK coupling, Phase 2: one exit kernel, Why a plan is still needed, 6. Cleanup (P3), nearest_snapshot(), DayData, DayResult, RegimeDispatch (+18 more)

### Community 103 - "fidelity.py"
Cohesion: 0.29
Nodes (10): _canonical(), fly_widths(), _fmt(), markdown(), fly(), row(), one_line(), _pct() (+2 more)

### Community 104 - "performance_chart.py"
Cohesion: 0.17
Nodes (13): compute_stats(), ReportStats, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels() (+5 more)

### Community 105 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.09
Nodes (21): Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Production marker-change proof (2026-08-10), Recommendation, Reducing the weekly re-authorization cost — a scoping question, Stale-writer follow-up (2026-08-10), Status, The cost being attacked (+13 more)

### Community 106 - ".history"
Cohesion: 0.23
Nodes (9): Auxiliary inputs (manifest schema 2), Data, Event calendar, Overnight futures (ES): audit only, _append(), test_catalog_fails_on_a_broken_chain(), test_catalog_lists_hashes_registries_and_counts(), test_history_counts_events_for_the_exact_definition() (+1 more)

### Community 107 - "EventCalendar"
Cohesion: 0.13
Nodes (16): _date(), EventCalendar, MarketEvent, parse_row(), _row(), test_committed_calendar_has_a_scheduled_event_of_each_type_every_year(), test_committed_calendar_loads_and_covers_the_range(), test_event_published_on_or_after_the_session_is_invisible_to_it() (+8 more)

### Community 108 - "2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)"
Cohesion: 0.18
Nodes (10): Option A Live Serving (built offline, never deployed), What the research core needs, 2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only), Descriptive E0 breakdowns (not evidence), Feature sources and coverage, Housekeeping, Pre-registration draft (not registered), Vendor readiness (+2 more)

### Community 109 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 110 - "Re-authorization checklist — Saturday 2026-08-22"
Cohesion: 0.18
Nodes (10): Preconditions — verified 2026-08-22T15:45:36Z, Re-authorization checklist — Saturday 2026-08-22, Step 1 — mint on zeus, in a real terminal, Step 2 — stage on Helios, verify byte-identical, Step 3 — move into place under the C1 lock, Step 4 — watch the reloads; restart only on a *confirmed* failure, Step 5 — verify, host against containers, Step 6 — record (+2 more)

### Community 111 - "thetadata_download.py"
Cohesion: 0.18
Nodes (11): cboe_sessions(), expirations(), fetch(), file_path(), _get(), LargeRequestError, load_no_data(), main() (+3 more)

### Community 112 - "AGENTS.md"
Cohesion: 0.12
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 114 - "test_research_quality.py"
Cohesion: 0.21
Nodes (11): quality_passed(), _cboe(), _day(), test_a_clean_day_passes_every_gate(), test_a_quality_run_never_reads_the_holdout(), test_coverage_crossed_stale_and_timestamp_failures_are_caught(), test_only_a_full_window_pass_opens_earlier_pulls(), test_q5_is_not_evaluable_without_exact_minute_spx_prints() (+3 more)

### Community 115 - "3. ButterflyGuy-owned TimescaleDB data"
Cohesion: 0.18
Nodes (11): 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state`, 3.7 `daily_bars` (+3 more)

### Community 116 - "test_exit_trials.py"
Cohesion: 0.27
Nodes (16): ConfirmedMachine, replay(), variants(), points(), test_confirmation_does_not_delay_hard_end_of_day(), test_confirmation_missing_followup_is_censored(), test_confirmation_uses_elapsed_time_and_observed_fill(), test_frozen_baseline_matches_original_replay() (+8 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "launch_schwab_gateway_readiness_soak_20260909.sh"
Cohesion: 0.20
Nodes (10): die(), EVIDENCE_DIR, LAUNCHER, LOG, MONITOR, SESSION_DATE, launch_schwab_gateway_readiness_soak_20260909.sh script, TARGET_EPOCH (+2 more)

### Community 121 - "report_trade_ladders.py"
Cohesion: 0.20
Nodes (10): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+2 more)

### Community 122 - "ChainObservation"
Cohesion: 0.27
Nodes (4): Provider, ChainObservation, _fly_mark(), PositionQuoteShadow

### Community 123 - "test_daily_report_card.py"
Cohesion: 0.16
Nodes (13): parse_trade_transactions(), candles_to_series(), test_build_equity_trade_chart_png_returns_png_bytes(), test_chartable_equity_trades_skips_options(), test_equity_chart_aggregates_to_two_minute_candles(), test_equity_chart_stats_text_includes_key_fields(), test_equity_chart_window_keeps_6am_premarket_and_regular_session(), test_equity_chart_window_rejects_prior_day_same_times() (+5 more)

### Community 124 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 125 - "Window H — verification held; the deadline reminder is mistimed (2026-08-08)"
Cohesion: 0.22
Nodes (9): Deliverables, Finding — the weekly reminder fires after the deadline it protects, Still open after Window H, Task 2 — the Monday check is deferred a fourth time, Tasks 3–6 — all green, verified host-against-container, The deadline in local time — stated because the brief did not, The deadline, re-derived from the document, Window H addendum — a keepalive write observed live (2026-08-09 01:00 UTC) (+1 more)

### Community 127 - "test_research_thetadata.py"
Cohesion: 0.23
Nodes (14): _cboe(), _day_quotes(), _source(), Terminal, test_a_holdout_pull_stops_before_any_terminal_request(), test_daily_bars_take_the_official_close_from_cboe_and_the_open_from_the_file(), test_describe_pins_the_inputs_and_carries_no_credential(), test_index_bars_serve_the_day_and_nothing_for_a_stale_day() (+6 more)

### Community 129 - "parse_quotes"
Cohesion: 0.20
Nodes (6): _et_to_utc_us(), parse_quotes(), ThetaDataError, _quote_csv(), test_millisecond_timestamps_with_trimmed_zeros_parse(), test_quotes_map_to_utc_and_types_and_a_0_0_row_is_no_quote()

### Community 130 - "Schwab gateway current status"
Cohesion: 0.25
Nodes (6): Current state, Deferred Helios cleanup, Historical record, Runtime boundaries, Schwab gateway current status, Archived Schwab gateway transition records

### Community 131 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 132 - "Schwab Gateway Foundation Smoke Test"
Cohesion: 0.25
Nodes (7): Defect Found During Proof, Observed Contract, Result, Safety Boundary, Schwab Gateway Foundation Smoke Test, Shutdown and Residual State, Temporary Authentication

### Community 133 - "Schwab Single-Token Manager"
Cohesion: 0.25
Nodes (7): Fake-only verification, Integration gate, Proven schwab-py callback contract, Schwab Single-Token Manager, Scope, Transaction, Validation and states

### Community 134 - "ShadowComparingMarketDataProvider"
Cohesion: 0.15
Nodes (7): _error_code(), _mismatch_code(), _numbers_agree(), ShadowComparingMarketDataProvider, test_get_option_chain_returns_before_a_slow_gateway_responds(), get_chain_metadata(), test_non_shadowed_reads_are_pure_delegation()

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "DiscordNotifier"
Cohesion: 0.05
Nodes (23): Interfaces and contracts, EquityQuoteProvider, OptionChainProvider, PriceHistoryProvider, SpotPriceProvider, send_alertmanager(), broker_reconciler_loop(), _reconcile_broker_state() (+15 more)

### Community 137 - "run_trials.py"
Cohesion: 0.15
Nodes (20): all_stresses(), assert_prior_result(), ledger_parity(), main(), paired_comparison(), select_sources(), points(), test_all_scenarios_equal_original_replays() (+12 more)

### Community 138 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.12
Nodes (10): Corrections to the Window G brief, End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, The fix, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08) (+2 more)

### Community 139 - "Registration decision package: ThetaData development window (2026-09-29)"
Cohesion: 0.11
Nodes (17): 1. Data and integrity, 2. Baseline E0 (descriptive; do not tune on it), 3. The hypotheses on the development window (in-sample), 4. Holdout size and power, 5. VIX-smoothing sensitivity, 6.1 Stressed exits below zero: decided, now floored (D3, draft Revision 1), 6.2 Gate 1 passed skip filters too often under the null: decided, now calibrated (D4, draft Revision 4), 6.3 A paired pass against a losing baseline: decided, gate 6 added (D2, draft Revision 5) (+9 more)

### Community 140 - "test_research_sweep_ports.py"
Cohesion: 0.29
Nodes (5): _published(), _row(), test_fitted_thresholds_match_the_published_ones(), test_learners_decide_only_from_earlier_sessions(), test_variant_reproduces_the_idea_sweep()

### Community 141 - "build_daily_report_card"
Cohesion: 0.18
Nodes (11): ActivitySummary, build_daily_report_card(), DailyReportCardSettings, load_daily_report_card_config(), ReportCardThresholds, detect_problems(), rank_trades(), summarize_activity() (+3 more)

### Community 142 - "2. Other external and public sources"
Cohesion: 0.22
Nodes (9): 2.1 Yahoo Finance (`yfinance`), 2.2 S&P 500 constituent dataset on GitHub, 2.3 Wikipedia Nasdaq-100 page, 2.4 Nasdaq Trader symbol directories, 2.5 SEC company ticker map and submissions, 2.6 Alpha Vantage earnings calendar and news sentiment, 2.7 Forex Factory economic calendar, 2.8 Local market calendar and clock (+1 more)

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
Cohesion: 0.09
Nodes (20): Completed decision, Distinct datasets and source versions, Ernie comparison reconciliation — 2026-10-02, Provenance and access limits, Reproduce, SPX idea sweep — 2026-09-25, Code and experiment freeze, Full development eligibility audit (+12 more)

### Community 147 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 148 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 149 - "select_pm_settled_rows"
Cohesion: 0.25
Nodes (4): _is_pm_settled(), select_pm_settled_rows(), select_strike_contract(), test_snapshot_rows_are_grouped_per_snapshot_time()

### Community 150 - "entry.py"
Cohesion: 0.06
Nodes (26): What the definition hash covers, ATMEntry, baseline_window(), _call_only(), Entry, FilteredEntry, gap_direction(), select_at() (+18 more)

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
Cohesion: 0.22
Nodes (6): BrokerStateGate, token_reload_loop(), test_broker_state_gate_records_unsafe_reason(), test_failed_token_reload_blocks_new_entries(), test_token_reload_loop_survives_a_failed_reload(), reload_if_reauthorized()

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

### Community 161 - "f2_shadow_report.py"
Cohesion: 0.25
Nodes (9): _candidate(), check_previous(), completed_sample(), input_hashes(), load_cohort(), main(), score(), _stats() (+1 more)

### Community 162 - "test_run_backtest_db.py"
Cohesion: 0.09
Nodes (18): fetch_prev_close(), _fitted_density_counts(), _print_pnl_histogram(), _DailyBarConnection, test_entry_window_direction_ma_uses_sma_of_prior_closes(), test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), fake_vix(), test_fitted_density_counts_returns_bucket_heights() (+10 more)

### Community 163 - "Butterfly Guy Research and Backtest Pipeline Review — 2026-09-27"
Cohesion: 0.17
Nodes (11): 1. The prospective cohort's daily update was failing (P0), 2. Statistical power (P0 for research planning), 3.1 Consolidate the simulators, 3.2 Sweeps rank on the wrong accounting and the wrong metric, 3.3 Make fly-choice robustness a standard output, 3. Research infrastructure (P1), 4. Data and features known before entry (P1), Butterfly Guy Research and Backtest Pipeline Review — 2026-09-27 (+3 more)

### Community 165 - "spx-prospective-v2-2026-10-02/manifest.json"
Cohesion: 0.12
Nodes (15): asset, cohort_id, config, path, sha256, created_at, database_tables, git (+7 more)

### Community 166 - "Part C: daily Schwab-vs-ThetaData fidelity check (PR 1)"
Cohesion: 0.50
Nodes (4): Baseline (required in PR 1), Deliver, Part C: daily Schwab-vs-ThetaData fidelity check (PR 1), Tests

### Community 168 - "butterfly mark"
Cohesion: 0.20
Nodes (7): BUTTERFLYGUY, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background, node-and-line network geometry, uppercase geometric wordmark style

### Community 169 - "Preflight stops on the host-executed release — 2026-08-06"
Cohesion: 0.67
Nodes (3): Credential exposure during the window, Preflight stops on the host-executed release — 2026-08-06, Release

### Community 170 - "test_gateway_token_manager.py"
Cohesion: 0.14
Nodes (26): increment_callback(), manager(), _process_refresh(), delayed_increment(), test_callback_failure_preserves_original_and_redacts_error_and_logs(), test_concurrent_managers_serialize_the_entire_refresh_callback(), first_refresh(), second_refresh() (+18 more)

### Community 171 - "CsvDataLoader"
Cohesion: 0.17
Nodes (6): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs, CsvDataLoader

### Community 172 - "Host-executed proof step"
Cohesion: 0.67
Nodes (3): Host-executed proof step, Release, Workflow consequence the next window must plan for

### Community 175 - "Live Runbook"
Cohesion: 0.25
Nodes (7): During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery, XSP Canary

### Community 177 - "PositionManager"
Cohesion: 0.14
Nodes (15): PositionManager, PositionQuotesUnavailableError, _quote_quality_ok(), replay_trade(), make_quote(), make_xsp_candidate(), quote_map(), test_missing_held_quote_preserves_last_mark_without_returning_stale_state() (+7 more)

### Community 179 - "_build_collector_market_data"
Cohesion: 0.15
Nodes (9): C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, The wiring point, What C3 does not do, _build_collector_market_data(), test_collector_market_data_defaults_to_direct_without_a_gateway_client() (+1 more)

### Community 180 - "Prospective execution validation — spx-prospective-2026-09-22"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-2026-09-22, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 181 - "H-TR1 registration — trail armed at +75% with a breakeven floor"
Cohesion: 0.11
Nodes (12): Data, Entries (frozen, unchanged from the 09-25 harness replica), H-TR1 registration — trail armed at +75% with a breakeven floor, Hypothesis, Pass criteria (all must hold; stressed accounting; per one-lot), Reported but not gating, Result (run once, 2026-10-01, at b0b7215), Run (+4 more)

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (8): Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy, XSP Account and Loss Guards

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (6): BUTTERFLYGUY, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 184 - "Research core"
Cohesion: 0.25
Nodes (8): Accounting and evaluation, Diagnostics (descriptive only), Known differences, Mechanism check for H-TS1 (descriptive only), Parity with the frozen replay, Registry, Reproducing the idea sweep, Research core

### Community 185 - "test_research_protocol.py"
Cohesion: 0.23
Nodes (17): _cli(), _gates(), _holdout(), _no_replay(), _pull_holdout(), _records(), test_a_fitted_rule_is_registered_with_its_value_and_checked_at_the_holdout(), test_a_steady_gain_passes_every_gate() (+9 more)

### Community 186 - "Options strategy discovery journal"
Cohesion: 0.20
Nodes (10): 2026-07-14 — diminishing returns checkpoint, 2026-09-29/30 — Package review, provenance, D7, D10, 2026-09-29 (later) — D6: no Indices month, 2026-09-30 — H-TS1 registered and evaluated on the holdout: FAIL, 2026-10-01 — direction: gap rule vs Ernie's trend indicators (development data only), 2026-10-01 — entry trigger: GEX-wall bounce vs our 10:00 entry (development data only), 2026-10-01 — H-TR1 registered test: FAIL, 2026-10-01 — strike placement: VIX-sigma anchor vs Ernie's price rule (development data only) (+2 more)

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
Nodes (4): _source(), test_compose_keeps_each_strategy_default_direct_with_staged_gateway_opt_in(), test_default_settings_construct_no_gateway_client(), test_standalone_packages_remain_pinned_and_consumers_import_them_directly()

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 193 - "pytest"
Cohesion: 0.05
Nodes (45): The holdout (`holdout.py`), cmd_export_history(), excluded_sessions(), get_source(), HistoryPlan, write_history(), HoldoutSealedError, verify_unseal() (+37 more)

### Community 194 - "2026-09-21 — SPX executable-side accounting on the settlement-correct replay"
Cohesion: 0.29
Nodes (7): 2026-09-21 — SPX executable-side accounting on the settlement-correct replay, Accounting models and deterministic data rules, Data provenance and coverage, Exact commands and implementation fingerprints, Frozen result, Pre-registered drawdown limit, Reproduction under the roll-forward exit rule

### Community 196 - "2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)"
Cohesion: 0.25
Nodes (8): 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered), Changes, E0 loses on the development window, Findings about the test itself, Hypotheses, paired with E0 (draft bootstrap: 10-session blocks, 10,000 reps), Integrity, Power (from development vectors; assumes 2022–24 is representative), Recommendation for the owner

### Community 197 - "Prospective execution validation — spx-prospective-v2-2026-10-02"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-v2-2026-10-02, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 200 - "load_report_gateway_settings"
Cohesion: 0.32
Nodes (3): test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings()

### Community 201 - "Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)"
Cohesion: 0.33
Nodes (6): Correction to Window H part 1, Item 1 — the warnings now fire before the deadline (deployed), Item 3 built — the token reload (2026-08-09, NOT deployed), Item 3 — the deciding question is answered: the swap is safe, Window H correction — the restart arithmetic was wrong, and the gateway never needed restarting, Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)

### Community 202 - "test_research_fidelity.py"
Cohesion: 0.25
Nodes (11): _chain(), _pair(), _spot(), test_exact_quotes_agree_everywhere(), test_histogram_quantiles_are_nearest_rank(), test_missing_snapshots_and_lateness(), test_missing_strikes_are_counted(), test_one_minute_shift_is_detected() (+3 more)

### Community 204 - "discover_options_strategy.py"
Cohesion: 0.13
Nodes (34): bootstrap_mean_delta(), atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown() (+26 more)

### Community 205 - "ThetaDataSource"
Cohesion: 0.18
Nodes (6): parse_cboe(), ThetaDataSource, _ymd(), test_after_the_files_end_spx_and_vix_come_from_the_recorded_dataset(), test_source_satisfies_the_history_source_interface(), test_thetadata_is_registered_and_needs_the_minute_files()

### Community 206 - "2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)"
Cohesion: 0.33
Nodes (6): 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run), Also changed, Readings the draft left open, now fixed in code, for the owner to review before registering, Refusals, all before any holdout session is replayed, Tests, The command

### Community 207 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.13
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 209 - "dev_studies.py"
Cohesion: 0.26
Nodes (6): cmd_calibrate(), cmd_check(), cmd_power(), cmd_random_skip(), load(), main()

### Community 210 - "quote_rules"
Cohesion: 0.29
Nodes (7): quote_rules, crossed_market, entry_gap, exit_gap, missing_market, selection, substitution

### Community 211 - "chain_cache.py"
Cohesion: 0.21
Nodes (13): chain_cache_path(), chain_journal_path(), load_chain_day(), _read_snapshots(), save_snapshot(), test_chain_cache_path_is_partitioned_by_underlying(), test_load_chain_day_falls_back_to_partitioned_spx_cache(), test_load_chain_day_merges_legacy_json_with_jsonl() (+5 more)

### Community 212 - "files"
Cohesion: 0.29
Nodes (7): rows, sha256, files, daily_bars.parquet, sessions/2026-07-13/chain.parquet, rows, sha256

### Community 213 - "prospective_execution.py"
Cohesion: 0.06
Nodes (37): Shadow on the open cohort, ExecutableTrade, append_jsonl(), append_unique(), _breakdown(), build_daily_run_record(), build_manifest(), build_trade_record() (+29 more)

### Community 214 - "Implementation prompt: finish local ThetaData backtesting support"
Cohesion: 0.15
Nodes (12): Completion checklist, Facts and constraints to carry forward, Implementation prompt: finish local ThetaData backtesting support, Objective, Phase 1 — establish the actual remaining work, Phase 2 — local raw-Parquet source and normalization, Phase 3 — supporting observations and coverage policy, Phase 4 — SPXW 0-DTE integration and execution verification (+4 more)

### Community 215 - "docs/README.md"
Cohesion: 0.09
Nodes (14): Canonical research datasets, Conventions, Layout, Reading, Sets, The spent holdout (2024-07-01 to 2026-03-12), ThetaData option history (raw), Live WebSocket (+6 more)

### Community 216 - "Phases"
Cohesion: 0.18
Nodes (10): Open owner decisions, Phase 0: land what exists, Phase 1: one command surface, Phase 3: commit the analysis that decisions rest on, Phase 4: link the stages, Phase 5: data upkeep, Phases, Research workflow unification plan — 2026-09-29 (+2 more)

### Community 217 - "Offline ThetaData research"
Cohesion: 0.20
Nodes (8): Baseline and exposure, Commands, Lifecycles, accounting and limits, Mapping and access, Offline ThetaData research, Verification artifacts, Real private artifacts, ThetaData local implementation verification

### Community 220 - "decision_rules"
Cohesion: 0.22
Nodes (9): decision_rules, checkpoint_trades, early_failure_trades, max_drawdown, max_top3_gross_profit_share, min_executable_entry_coverage, min_profit_factor, primary_hypothesis (+1 more)

### Community 222 - "math"
Cohesion: 0.24
Nodes (7): bs_gamma(), gex_levels(), main(), round_levels(), triggered_entry(), rr_pick(), select_anchor()

### Community 223 - "Cohort automation"
Cohesion: 0.29
Nodes (6): Check on it, Cohort automation, Install, Known limitation: the SSH key, Retired v1, When the cohort closes

### Community 224 - "assumptions"
Cohesion: 0.33
Nodes (6): assumptions, commission_per_contract, contract_multiplier, contracts_per_butterfly, quantity, stressed_leg_slippage

### Community 225 - "test_run_live.py"
Cohesion: 0.08
Nodes (35): _never_awaited(), _run_daily_reset_once(), _synthetic_butterfly_snapshot(), _synthetic_position(), test_collector_market_data_shadow_is_opt_in_and_direct_authoritative(), test_daily_reset_keeps_regime_when_reclassification_fails(), test_daily_reset_reclassifies_regime_before_entry(), test_daily_reset_skips_regime_on_non_trading_day() (+27 more)

### Community 226 - "_run_with_stub_token"
Cohesion: 0.12
Nodes (8): _run_with_stub_token(), test_token_keepalive_exits_when_the_token_lock_is_held(), test_token_keepalive_honours_schwab_token_path(), test_token_keepalive_refreshes_inside_the_token_lock(), refresh(), test_token_keepalive_reports_alertmanager_failure(), test_token_keepalive_reports_alertmanager_state(), fake_open()

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
Cohesion: 0.20
Nodes (9): Assumptions requiring verification, Configuration, secrets, and deployment assumptions, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies, Extraction boundaries, Retry and failure behavior (+1 more)

### Community 231 - "2026-10-02 — edge search: hold to settlement with a VIX floor (development + validation; nothing registered)"
Cohesion: 0.40
Nodes (5): 2026-10-02 — edge search: hold to settlement with a VIX floor (development + validation; nothing registered), Caveats, Discipline, Findings, What followed

### Community 232 - "equity_market_data.py"
Cohesion: 0.09
Nodes (13): Streaming, Reusable components, Streaming flow, JsonlStreamRecorder, symbol_directory(), utc_now(), write_candle_snapshot(), run() (+5 more)

### Community 233 - "Held-position market-data diagnostics"
Cohesion: 0.50
Nodes (3): Behavior, Deployment and verification, Held-position market-data diagnostics

### Community 234 - "SPX idea sweep — registry (written 2026-09-25 before any variant was run)"
Cohesion: 0.50
Nodes (3): Round 2 — POST-HOC (written after seeing round-1 results; exploratory only), SPX idea sweep — registry (written 2026-09-25 before any variant was run), Variants

### Community 235 - "PositionState"
Cohesion: 0.13
Nodes (10): 2026-09-09 runtime follow-up, Cache TTL is hard-capped at 4s in code, not just config, Chain size correlation, Recommendation, Request path (cache miss), SchwabGateway option-chain latency investigation (2026-09-04), Where the time actually goes: scheduler queueing, not the Schwab call itself, XSP held-leg event-age correction (2026-09-11) (+2 more)

### Community 236 - "ButterflyOrderBuilder"
Cohesion: 0.17
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
Cohesion: 0.20
Nodes (12): _inputs(), _sessions(), _synthetic(), test_bootstrap_is_deterministic(), test_cboe_spx_parser(), test_decision_rule_on_planted_and_null_effects(), test_first_session_uses_the_prior_development_session(), test_prior_values_come_from_the_previous_spx_session() (+4 more)

### Community 242 - "spx-idea-sweep-2026-09-25/variants.py"
Cohesion: 0.12
Nodes (21): baseline_entry(), open_spot(), fn(), et_ts(), exit_trade(), Fly, open_trade(), Trade (+13 more)

### Community 243 - "2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data)"
Cohesion: 0.50
Nodes (4): 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data), Housekeeping, Registration decision package (nothing registered), Tooling hygiene

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

### Community 253 - "ChainDay"
Cohesion: 0.29
Nodes (5): ChainDay, day_with_monitoring_bars(), _bar(), test_day_with_monitoring_bars_adds_live_poll_timestamps(), test_day_with_monitoring_bars_keeps_existing_bar_for_same_timestamp()

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

### Community 258 - "2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered)"
Cohesion: 0.50
Nodes (4): 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered), Decision and change, Results, Still open

### Community 259 - "providers.py"
Cohesion: 0.15
Nodes (11): canonicalize_schwab_chain_symbol(), ContractTiming, _finite_number(), GatewayMarketDataError, _nonnegative_integer(), OmittedContract, _optional_number(), _require_usable_observation() (+3 more)

### Community 260 - "._spawn_background"
Cohesion: 0.13
Nodes (12): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", Two corrections to the received design points, C1 — the operator chose the shared lock, C3 plan produced, and a stale design point corrected, Durability decided, monitoring still open, Housekeeping, Multi-Agent Review Remediation (offline, still unwired) (+4 more)

### Community 261 - "report_broker_order_statuses.py"
Cohesion: 0.27
Nodes (12): _allowed_roots(), _build_payload(), main(), _order_symbols(), _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses(), test_payload_excludes_non_spx_orders() (+4 more)

### Community 263 - "SPX paper-trade review — September 12, 2026"
Cohesion: 0.33
Nodes (5): Evidence and scope, Findings, Mechanism worth testing, Research pipeline and proposed experiment, SPX paper-trade review — September 12, 2026

### Community 264 - "round2.py"
Cohesion: 0.33
Nodes (8): ev_rank_factory(), r1(), r2(), r5(), ratio_at(), ror(), e0(), k1()

### Community 266 - "execution_accounting.py"
Cohesion: 0.12
Nodes (22): _entry_debit(), _exit_credit(), _finite_quote_side(), inspect_quote_market(), price_frozen_trade(), QuoteMarket, snapshot_at_or_before(), snapshot_keys() (+14 more)

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
Cohesion: 0.21
Nodes (26): _bar(), _contract(), _observation(), test_empty_extended_session_is_allowed_but_other_flags_remain_fatal(), test_gateway_provider_adapts_history_and_combines_sessions(), test_gateway_provider_adapts_typed_spot_and_full_chain(), test_gateway_provider_canonicalizes_chain_symbol_at_client_boundary(), test_gateway_provider_defaults_normalized_null_time_value_to_zero() (+18 more)

### Community 301 - "All 108 historical entries: executed exit experiments"
Cohesion: 0.33
Nodes (4): All-history extension fixed before execution, All 108 historical entries: executed exit experiments, Outputs, Run locally

### Community 304 - "manifest.json"
Cohesion: 0.15
Nodes (12): created_utc, entry_prices, exit_commission_points, files, raw/checkout-source-hashes.json, raw/deployment.txt, raw/export.jsonl, raw/monitor.jsonl (+4 more)

### Community 314 - "Ernie (@0DTE) comparison — variant plan (not run)"
Cohesion: 0.13
Nodes (14): Constraints, D — direction, Data route (pending owner decision), E — entry trigger (structural levels), Ernie (@0DTE) comparison — variant plan (not run), Ernie's rules, as stated, Order, P — strike placement (+6 more)

### Community 315 - "test_collector_cadence.py"
Cohesion: 0.09
Nodes (20): et(), FakeClock, _run(), StopLoopError, test_a_stall_alerts_once_and_never_catches_up(), test_first_tick_is_the_open_and_last_is_before_the_early_close(), test_next_tick(), test_offset_shifts_the_grid() (+12 more)

### Community 351 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 352 - "DirectSchwabMarketDataProvider"
Cohesion: 0.18
Nodes (4): DirectSchwabMarketDataProvider, MarketMoversProvider, test_direct_provider_delegates_without_transforming_results(), test_direct_provider_observations_are_empty()

### Community 353 - "2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only), Call-only entry filters, Moving-average direction versus the gap rule, Reproduction, Robustness to fly choice (near-tied flies), Setup and accounting, Why the backtest and live paper disagree

### Community 356 - "2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)"
Cohesion: 0.33
Nodes (6): 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only), Data and harness, Hypothesis registered for a future forward cohort (not applied), Low-VIX diagnosis, Sweep results (stressed net P&L), Why the baseline fails in H2

### Community 358 - "Documentation map"
Cohesion: 0.22
Nodes (9): Architecture, Archive, Artifact retention, Command ownership, Documentation map, Operations and data, Research, Reviews and agent handoffs (+1 more)

### Community 359 - "quote_rules"
Cohesion: 0.29
Nodes (7): quote_rules, crossed_market, entry_gap, exit_gap, missing_market, selection, substitution

### Community 360 - "2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)"
Cohesion: 0.29
Nodes (7): 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data), Built (provider-independent, tested on synthetic data), Development coverage and in-sample E0, Housekeeping, Hypothesis rules (implemented, not registered), Validation results (readiness doc steps 1–4), What this means for the evidence plan

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

### Community 368 - "generate_live_performance.py"
Cohesion: 0.07
Nodes (33): now_pacific(), _json_data_block(), best_trade(), _case_study(), _clock(), _entry_window_et(), _et_after_open(), _minutes_between() (+25 more)

### Community 369 - "test_research_tieset.py"
Cohesion: 0.19
Nodes (6): draw_keys(), _cand(), test_draws_are_keyed_by_session_and_direction(), test_promotion_shift_is_rr_gap_over_combined_cost_sensitivity(), test_run_scores_tie_sets_unless_told_not_to(), test_selector_pool_applies_center_tolerance_and_rr_max_per_width()

### Community 371 - "run_live.py"
Cohesion: 0.05
Nodes (40): Historical Cycle Checkpoints, Entry-point inventory and fate, Baseline, Butterfly Guy Code Review — 2026-09-25, Executive summary, Findings index, Low / Info, Method (+32 more)

### Community 372 - "Dataset"
Cohesion: 0.05
Nodes (25): Modules, Dataset, dataset_hash(), DecisionProfile, round_to_seconds(), SessionFeatures, quote_times(), coverage() (+17 more)

### Community 373 - "2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only), Cohort runner move (2026-09-27) and a labeling note, Cohort shadow (exploratory, three sessions), Exit-latency stress, Parity, Research core and data, Variant registry

### Community 375 - "2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)"
Cohesion: 0.33
Nodes (6): 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered), Consequences, Decision and change, Still open, The calibration study (scratch, development data), What it gives on the real dataset (in-process, nothing registered)

### Community 376 - "2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)"
Cohesion: 0.33
Nodes (6): 2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only), Data and harness, Hypothesis for a future test (not applied), Post-hoc middle ground (defined after the table above), Pre-declared variants (written before running), Reproduction

### Community 379 - "ThetaData data-quality plan and validation amendment (2026-09-28)"
Cohesion: 0.06
Nodes (32): After Parts A and B, Headline numbers, How approximate this is, Run, Schwab recording fidelity baseline (2026-10-04), Behavior, Check the impact on live reads, Goal (+24 more)

### Community 380 - "learning.py"
Cohesion: 0.08
Nodes (18): Hypothesis rules (implemented, not registered), Rules that learn, Costs, _audit(), entry_spread_ratio(), EVRankEntry, EVSelector, fit_variant_entry() (+10 more)

### Community 382 - "gateway_minute_backfill.py"
Cohesion: 0.32
Nodes (3): check(), dump(), main()

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

### Community 393 - "SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan"
Cohesion: 0.18
Nodes (10): Access, credential and timestamps, Assessment, Endpoints and request plan, Licence (individual plans), Plans and prices (as read), Purchase checklist, SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan, ThetaData: public-docs findings and purchase checklist (2026-09-28) (+2 more)

### Community 394 - "XSP improvements — sequential work record, October 6, 2026"
Cohesion: 0.10
Nodes (18): 2. XSP exit replay — baseline established before tuning, 3. Earlier trailer — experiment fixed before execution, 4. Independent width policy — no recent behavioral difference, 5. Execution and settlement evidence — proxy discrepancy measured, Reproduce, Result: refine; do not activate this candidate, XSP improvements — sequential work record, October 6, 2026, 1. High — reconcile risk accounting before trusting risk dashboards (+10 more)

### Community 396 - "Critical External-Alert Delivery Proof - 2026-07-15"
Cohesion: 0.40
Nodes (4): Critical External-Alert Delivery Proof - 2026-07-15, Implementation reviewed, Scope, Supervised delivery and deduplication result

### Community 397 - "json"
Cohesion: 0.13
Nodes (7): main(), result_table(), main(), money(), table(), config(), test_closed_trade_queries_filter_paper_fill_model()

### Community 398 - "XSP Flat-Runtime Restart Proof - 2026-07-14"
Cohesion: 0.40
Nodes (4): Preconditions, Restart and verification, Scope, XSP Flat-Runtime Restart Proof - 2026-07-14

### Community 399 - "fill_models"
Cohesion: 0.50
Nodes (4): fill_models, corrected_midpoint, marketable, stressed_marketable

### Community 402 - "run_schwab_fidelity_daily.sh"
Cohesion: 0.67
Nodes (3): BUTTERFLY_RESEARCH_CACHE, research(), run_schwab_fidelity_daily.sh script

### Community 403 - "ProfitManagementSettings"
Cohesion: 0.17
Nodes (8): Acquisition actually performed, Conditional end-to-end confirmation, Offline reproduction, Output map, Replay rules and costs, Reproduce the SPX exit-policy experiment, SPX exit-policy research — September 12, 2026, ProfitManagementSettings

### Community 404 - "spot_ticks.parquet"
Cohesion: 0.67
Nodes (3): spot_ticks.parquet, rows, sha256

### Community 408 - "fly_settlement_value"
Cohesion: 0.09
Nodes (21): Definition, Endpoint and gates (fixed now, judged only at the endpoint), Evidence that motivated it (all in-sample or partly used), F2 prospective shadow registration — 2026-10-02, How it is scored, Operation, Assumptions, Corrected implementation fingerprints (+13 more)

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **1120 isolated node(s):** `created_utc`, `range`, `trades`, `provider`, `original_acquisition_utc` (+1115 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2600 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **50 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `providers.py`, `report_broker_order_statuses.py`, `subprocess`, `DiscordNotifier`, `OptionQuote`, `Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)`, `main`, `BrokerStateGate`, `Codex Project State`, `_assert_broker_state_matches_db`, `Schwab Gateway Migration Plan`, `_build_collector_market_data`, `Standalone SchwabGateway Extraction Plan`, `config.py`, `Branch Review and Integration Plan`, `test_schwab_client.py`, `._retry`, `asyncio`, `DirectSchwabMarketDataProvider`, `Capability recorder design`, `position_service.py`, `ButterflyCandidate`, `Current Schwab Integration`, `equity_market_data.py`, `Window F — the refresh token re-authorized, six days early (2026-08-08)`, `run_live.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `Dataset` (e.g. with `cmd_cache_inputs()` and `cmd_import()`) actually correct?**
  _`Dataset` has 80 INFERRED edges - model-reasoned connections that need verification._
- **What connects `created_utc`, `range`, `trades` to the rest of the system?**
  _1120 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `run_paper_replay.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07683000604960677 - nodes in this community are weakly interconnected._
- **Why does `Schwab Gateway Credential Proof` connect `Schwab Gateway Credential Proof` to `Preflight stops on the host-executed release — 2026-08-06`, `Host-executed proof step`, `First token read, and a read-only container filesystem — 2026-08-06`, `Operator-named absolute token path`, `simulate.py`, `Stage-named proof failure and an unpaused restoration — 2026-08-06`, `Bounded proof failure codes and a settled restoration error window — 2026-08-06`, `Credential proof passed — 2026-08-06`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Should `time_utils.py` be split into smaller, more focused modules?**
  _Cohesion score 0.060455486542443065 - nodes in this community are weakly interconnected._