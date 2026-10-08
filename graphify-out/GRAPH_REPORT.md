# Graph Report - Butterflyguy  (2026-10-08)

## Corpus Check
- 443 files · ~905,885 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 45 file(s) not represented in the graph (top: .parquet 15, (none) 9, .jsonl 8)

## Summary
- 6870 nodes · 19002 edges · 322 communities (283 shown, 39 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 2584 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4ed09872`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_paper_replay.py
- EventCalendar
- market_close_time
- test_order_manager.py
- schwab_gateway_v046_readiness_soak.py
- json
- trade_chart.py
- butterfly_gateway_acceptance.py
- market.py
- run_entry_analysis.py
- math
- test_gateway_shadow_reads.py
- compute_tent_boundaries
- numpy
- report_exit_mark_parity.py
- RunContext
- Schwab Gateway Credential Proof
- test_research_session_ledger.py
- protocol.py
- schwab_gateway_session_soak.py
- test_research_features.py
- .generate_chain
- export.py
- reports/daily_report_card.py
- PositionService
- quality.py
- archive_cli.py
- Registry
- test_chain_parser_parity.py
- test_risk_engine.py
- datetime
- ProfitStateMachine
- run_backtest_db.py
- SchwabDataLoader
- run_prospective_execution.py
- research/shadow.py
- .wait_for_shadow_reads
- Dataset
- Codex Project State
- _assert_broker_state_matches_db
- date
- Schwab Gateway Migration Plan
- test_collector_timing.py
- test_gateway_order_book.py
- fidelity.py
- set_readiness
- equity_trade_chart.py
- backfill_equity_candles.py
- source_hashes
- test_position_data_diagnostics.py
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- Window A — Token re-authorization (mandatory)
- load_config
- strategy_parameters
- weekend_review.py
- simulate.py
- thetadata_download.py
- GapRegimeFilter
- Standalone SchwabGateway Extraction Plan
- .place_order
- test_position_monitoring.py
- parse_args
- config.py
- realized_vs_implied.py
- DbDataLoader
- sys
- exit_trials/manifest.json
- test_prospective_execution.py
- test_f2_shadow_report.py
- build_market_events.py
- launch_schwab_gateway_session_soak_20260904.sh
- et_us
- Branch Review and Integration Plan
- thetadata_prep.py
- all_history_trials/manifest.json
- SchwabClientWrapper
- strategy_parameters
- Any
- position_service.py
- Architecture
- ButterflyGuy data sources and data types
- Options strategy discovery report
- ThetaDataSource
- 9) Capture equity candles and Level II for trade review
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- MinuteBar
- test_weekend_review.py
- mechanism.py
- 2026-07-14 — data audit and research design
- Re-authorization checklist — Saturday 2026-08-15
- main
- Capability recorder design
- argparse
- read_jsonl
- generate_live_performance.py
- ButterflyCandidate
- SimulationEngine
- yaml
- run_all_history.py
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- test_research_catalog.py
- test_research_calendar.py
- services/daily_report_card.py
- Window D — the gateway made reachable, started, and watched (2026-08-08)
- Re-authorization checklist — Saturday 2026-08-22
- DayMarket
- AGENTS.md
- pandas
- 3. ButterflyGuy-owned TimescaleDB data
- test_exit_trials.py
- Butterfly Guy
- launch_schwab_gateway_readiness_soak_20260909.sh
- report_trade_ladders.py
- Path
- test_daily_report_card.py
- Schwab gateway deployment options
- run_trials.py
- GatewayAuthoritativeMarketDataProvider
- test_run_migrations.py
- diagnose.py
- Phases
- Schwab gateway current status
- 1. Charles Schwab API
- Schwab Gateway Foundation Smoke Test
- Schwab Single-Token Manager
- ShadowComparingMarketDataProvider
- Strategy Settings
- DiscordNotifier
- replay.py
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- Registration decision package: ThetaData development window (2026-09-29)
- test_position_quote_recovery.py
- F2 prospective shadow registration — 2026-10-02
- 2. Other external and public sources
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Width Selection
- ThetaData durable backtesting execution — 2026-10-01
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- Schwab Gateway Multi-Consumer Foundation
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
- broker_cash_settlement_from_transactions
- spx-prospective-v2-2026-10-02/manifest.json
- ThetaData data-quality plan and validation amendment (2026-09-28)
- _MetricsHandler
- butterfly mark
- Preflight stops on the host-executed release — 2026-08-06
- test_gateway_token_manager.py
- ButterflyGuy data sources — representative samples
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
- OptionChainProvider
- pytest
- 2026-09-21 — SPX executable-side accounting on the settlement-correct replay
- et_ts
- 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)
- Prospective execution validation — spx-prospective-v2-2026-10-02
- Next SPX sweep on vendor history — pre-registration DRAFT (not registered)
- DirectProvider
- load_report_gateway_settings
- Offline safety-drill record — 2026-07-13
- report_selection_parity.py
- ThetaData option history (raw)
- discover_options_strategy.py
- test_research_thetadata.py
- 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)
- Option A deployment runbook — Helios, containerized
- ThetaData backtesting readiness and completion plan
- dev_studies.py
- quote_rules
- chain_cache.py
- files
- prospective_execution.py
- HistorySource
- docs/README.md
- run_classifier_sweep.py
- Offline ThetaData research
- run_live_performance_cron.sh
- decision_rules
- Compare Real vs Synthetic Chains
- day_with_monitoring_bars
- Cohort automation
- assumptions
- test_run_live.py
- unittest_mock
- endpoint
- SchwabGateway order-book release full-session acceptance — 2026-09-01
- export
- Current Schwab Integration
- test_a_discrepancy_counts_once_as_a_comparison_and_once_by_code
- XSP protection and fresh-quote recovery candidate — October 8, 2026
- Held-position market-data diagnostics
- SPX idea sweep — registry (written 2026-09-25 before any variant was run)
- SchwabGateway option-chain latency investigation (2026-09-04)
- ButterflyOrderBuilder
- Historical data management
- entry_pricing.py
- fill_models
- state_machine.py
- test_research_mechanism.py
- PositionQuotesUnavailableError
- round_to_seconds
- sessions/2026-03-19/chain.parquet
- sessions/2026-03-19/clock.parquet
- sessions/2026-03-26/chain.parquet
- sessions/2026-03-26/clock.parquet
- sessions/2026-04-07/chain.parquet
- sessions/2026-04-07/clock.parquet
- sessions/2026-04-16/chain.parquet
- sessions/2026-04-16/clock.parquet
- sessions/2026-06-12/chain.parquet
- Recorded
- sessions/2026-06-12/clock.parquet
- sessions/2026-07-13/clock.parquet
- SPX prospective execution validation v2 registration
- sessions.parquet
- GatewayMarketDataError
- Window C — the two token writers resolved (2026-08-08)
- report_broker_order_statuses.py
- SPX paper-trade review — September 12, 2026
- spx-idea-sweep-2026-09-25/variants.py
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
- DirectSchwabMarketDataProvider
- 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)
- 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)
- Documentation map
- quote_rules
- 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)
- assumptions
- Prospective cohort validation, version 2
- endpoint
- gates
- TradeRecord
- run_gateway_minute_backfill.sh
- strategy_page.py
- validate.py
- run_live.py
- 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)
- install_shutdown_handler
- 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)
- gateway_minute_backfill.py
- test_research_local.py
- 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan
- XSP improvements — sequential work record, October 6, 2026
- Critical External-Alert Delivery Proof - 2026-07-15
- csv
- XSP Flat-Runtime Restart Proof - 2026-07-14
- fill_models
- run_schwab_fidelity_daily.sh
- Reproduce the SPX exit-policy experiment
- spot_ticks.parquet
- fly_settlement_value
- _reset_readiness_after_provider_test
- grafana-sql-cpu-2026-10-06.md

## God Nodes (most connected - your core abstractions)
1. `Dataset` - 120 edges
2. `ButterflyCandidate` - 113 edges
3. `OptionQuote` - 102 edges
4. `RunContext` - 96 edges
5. `SchwabClientWrapper` - 93 edges
6. `AppConfig` - 88 edges
7. `load_config()` - 70 edges
8. `GatewayAuthoritativeMarketDataProvider` - 66 edges
9. `PositionService` - 65 edges
10. `Session` - 64 edges

## Surprising Connections (you probably didn't know these)
- `Conventions` --references--> `timestamp()`  [INFERRED]
  data/thetadata/README.md → docs/research/spx-exits-2026-09-12/replay.py
- `Repository and runtime inputs` --references--> `CsvDataLoader`  [INFERRED]
  data/data_sample.md → src/butterfly_guy/backtest/csv_loader.py
- `5.5 Historical minute CSVs` --references--> `CsvDataLoader`  [INFERRED]
  docs/data-sources-inventory.md → src/butterfly_guy/backtest/csv_loader.py
- `3.2 Sweeps rank on the wrong accounting and the wrong metric` --references--> `sharpe()`  [INFERRED]
  docs/reviews/2026-09-27-research-pipeline-review.md → src/butterfly_guy/backtest/metrics.py
- `Start-date correction before the first cohort` --references--> `CohortSpec`  [INFERRED]
  docs/research/strategy-discovery-journal.md → src/butterfly_guy/backtest/prospective_execution.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **hyperedge:logo_composition** — visual:geometric_butterfly_icon, brand:ButterflyGuy, visual:neon_green_accent, visual:dark_navy_background [EXTRACTED 1.00]
- **Multi-Asset Runtime Configurations** — configs_config_spx_runtime, configs_config_ndx_runtime, configs_config_xsp_runtime, butterflyguy_readme_butterfly_guy [EXTRACTED 1.00]
- **hyperedge:brand_visual_identity_inference** — brand:ButterflyGuy, visual:geometric_butterfly_icon, visual:polygon_linework, visual:futuristic_uppercase_wordmark, concept:technology_or_trading_brand_signal [INFERRED 0.62]
- **hyperedge:logo_brand_system** — brand:butterflyguy, visual:butterfly_mark, visual:network_geometry, visual:cyan_purple_gradient, visual:dark_background [INFERRED 0.80]
- **Monitoring Stack** — infra_prometheus_butterfly_scrapes, infra_grafana_provisioning_datasources_datasources_prometheus, infra_grafana_provisioning_datasources_datasources_timescaledb, infra_grafana_provisioning_dashboards_dashboards_butterfly_provider [INFERRED 0.86]

## Communities (322 total, 39 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.06
Nodes (44): _is_pm_settled(), select_pm_settled_rows(), select_strike_contract(), _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision (+36 more)

### Community 1 - "EventCalendar"
Cohesion: 0.13
Nodes (13): EventCalendar, session_close(), add_command(), build(), canonical(), cmd_ledger(), Evidence, gate_status() (+5 more)

### Community 2 - "market_close_time"
Cohesion: 0.08
Nodes (36): M8 — Early closes are hard-coded for 2026 only, _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_trading_day(), _last_weekday(), market_close_time() (+28 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.11
Nodes (63): OrderRejectedError, LiveSpread, broker_fill(), _exit_limits_for_bids(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi() (+55 more)

### Community 4 - "schwab_gateway_v046_readiness_soak.py"
Cohesion: 0.12
Nodes (30): append_jsonl(), bounded_request(), candidate_observation(), diagnostic_probe(), docker_inspect(), endpoint_snapshot(), finalize(), flatness() (+22 more)

### Community 5 - "json"
Cohesion: 0.06
Nodes (52): main(), build_parser(), evaluation_args(), _calibrate_for_registration(), cmd_calibrate(), cmd_catalog(), cmd_coverage(), cmd_diagnose() (+44 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.13
Nodes (16): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+8 more)

### Community 7 - "butterfly_gateway_acceptance.py"
Cohesion: 0.14
Nodes (14): _endpoints(), test_identity_checks_paper_gateway_and_no_shadow_invariants(), test_preopen_accepts_retried_market_data_unavailable(), test_preopen_allows_documented_after_hours_strategy_readiness(), test_preopen_never_suppresses_other_endpoint_failures(), test_preopen_rejects_every_other_readiness_failure(), endpoint_violations(), http_json() (+6 more)

### Community 8 - "market.py"
Cohesion: 0.07
Nodes (19): render(), restrict_view(), us_to_datetime(), _ci(), _iso(), markdown(), _money(), _r() (+11 more)

### Community 9 - "run_entry_analysis.py"
Cohesion: 0.07
Nodes (45): StrategySettings, straddle_selection(), main(), parse_args(), print_help(), fmt_candidate(), get_prev_close(), get_vix() (+37 more)

### Community 10 - "math"
Cohesion: 0.10
Nodes (20): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+12 more)

### Community 11 - "test_gateway_shadow_reads.py"
Cohesion: 0.15
Nodes (18): chain_response(), _discrepancies(), RecordingGateway, spot_response(), test_a_direct_payload_that_cannot_be_summarized_is_a_parsing_discrepancy(), test_a_gateway_error_is_counted_under_its_own_code(), test_a_null_gateway_price_is_reported_as_a_field_level_difference(), test_agreements_are_counted_and_not_only_failures() (+10 more)

### Community 12 - "compute_tent_boundaries"
Cohesion: 0.40
Nodes (3): compute_tent_boundaries(), _resolve_iv(), implied_vol()

### Community 13 - "numpy"
Cohesion: 0.07
Nodes (34): Status and scope, Fill, TradeFills, block_bootstrap_indices(), common_dates(), EvalParams, evaluate(), evaluate_arm() (+26 more)

### Community 14 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (11): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+3 more)

### Community 15 - "RunContext"
Cohesion: 0.09
Nodes (25): cached_entries(), EntryRule, RunContext, EventDaySkipEntry, PriorRatioFilter, ReleaseSkipEntry, session_features(), _calendar() (+17 more)

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

### Community 20 - "test_research_features.py"
Cohesion: 0.07
Nodes (31): Modules, Volatility term structure, DailyVol, IntradayVol, daily_table(), export_daily(), ingest_intraday(), intraday_table() (+23 more)

### Community 21 - ".generate_chain"
Cohesion: 0.11
Nodes (9): IVModel, SyntheticChainGenerator, make_snapshot_time(), test_atm_call_price_reasonable(), test_generate_chain_has_both_types(), test_generate_chain_strike_count(), test_otm_put_iv_higher_than_otm_call(), test_price_decreases_as_dte_shrinks() (+1 more)

### Community 23 - "export.py"
Cohesion: 0.08
Nodes (31): What is wrong today (verified 2026-10-04 by reading the code), bars_changes(), _bars_key(), chain_sql(), clock_sql(), daily_bars_sql(), DataSource, export_session() (+23 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.13
Nodes (30): 6. Canonical and derived analytical data types, Synthetic option-chain data, AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, DailyReportCardSettings, count_rejected_orders() (+22 more)

### Community 25 - "PositionService"
Cohesion: 0.03
Nodes (42): Architecture Map, Current architecture, Primary options runtime, Reusable components, Dependency map, Phase 3 Shadow Surfaces (unwired, default off), Collector, 1. Risk accounting — existing fix verified (+34 more)

### Community 26 - "quality.py"
Cohesion: 0.11
Nodes (19): Build on what exists, _quality(), arbitrage(), _bad_cells(), _cells(), _dst_week(), history_entry(), index_file_crosscheck() (+11 more)

### Community 27 - "archive_cli.py"
Cohesion: 0.08
Nodes (23): Fidelity validation (`validate.py`), The adapter (`history.py`), The holdout evaluation (`protocol.py`, `holdout`; D9, built 2026-09-29), Vendor history (ThetaData, subscribed 2026-09-28), add_commands(), _artifact(), _clean(), cmd_audit() (+15 more)

### Community 28 - "Registry"
Cohesion: 0.17
Nodes (12): _canonical(), record_hash(), Registry, RegistryError, _add(), _placeholder(), test_a_port_inherits_the_placeholder_stage_and_counts_once(), test_a_port_needs_a_matching_unported_placeholder() (+4 more)

### Community 29 - "test_chain_parser_parity.py"
Cohesion: 0.12
Nodes (12): _contract(), _parse_rows(), test_a_map_present_but_empty_produces_zero_everywhere(), test_a_non_numeric_strike_key_diverges_and_the_divergence_is_recorded(), test_a_strike_with_an_empty_option_list_is_excluded_by_all_three(), test_all_three_agree_on_which_expiration_matches(), test_calls_present_with_puts_absent_is_handled_identically_by_all_three(), test_contract_counts_equal_the_rows_the_collector_would_write() (+4 more)

### Community 30 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (15): make_risk_engine(), test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed(), test_can_trade_max_loss(), test_can_trade_max_trades(), test_can_trade_ok() (+7 more)

### Community 31 - "datetime"
Cohesion: 0.09
Nodes (29): main(), _collector(), _daily_candle(), test_daily_bars_failure_leaves_refresh_pending_and_retries(), test_daily_bars_skip_todays_in_progress_candle(), test_daily_bars_use_eastern_session_date_not_host_date(), _capture(), _make_result() (+21 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.13
Nodes (26): QuoteQualitySettings, PositionState, ProfitStateMachine, test_xsp_candidate_protects_october_8_giveback_after_confirmation(), make_pos(), make_settings(), test_absolute_loss_stop_fires_without_profit_tent(), test_default_drawdown_confirmation_is_immediate() (+18 more)

### Community 33 - "run_backtest_db.py"
Cohesion: 0.05
Nodes (55): ChainDay, DrawdownWindow, _accounting_comparison_rows(), backtest_entry_price(), candidate_from_trade_row(), _dd_schedule_label(), discover_dates(), _duration_min() (+47 more)

### Community 34 - "SchwabDataLoader"
Cohesion: 0.09
Nodes (7): day_cache_path(), load_day(), _parse_bar(), save_day(), SchwabDataLoader, date_range(), main()

### Community 35 - "run_prospective_execution.py"
Cohesion: 0.12
Nodes (21): CohortError, CohortSpec, deferred_runs_path(), load_manifest(), write_reports(), cohort_dir_for(), command_init(), command_report() (+13 more)

### Community 36 - "research/shadow.py"
Cohesion: 0.12
Nodes (20): check_records(), CohortLedger, compare_with_cohort(), default_ref(), _git(), _jsonl(), LedgerError, _m() (+12 more)

### Community 37 - ".wait_for_shadow_reads"
Cohesion: 0.13
Nodes (11): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", Two corrections to the received design points, Multi-Agent Review Remediation (offline, still unwired), test_shadow_failure_is_observed_without_changing_the_direct_result(), test_direct_result_is_unchanged_when_the_gateway_errors(), test_direct_result_is_unchanged_when_the_gateway_times_out_in_real_time(), test_gateway_errors_are_classified_by_fixed_code() (+3 more)

### Community 38 - "Dataset"
Cohesion: 0.07
Nodes (25): Dataset, dataset_hash(), SessionClock, SessionFeatures, coverage(), session_coverage(), summarize(), build_helios_clock_dataset() (+17 more)

### Community 39 - "Codex Project State"
Cohesion: 0.05
Nodes (42): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, C3 default-off deployment and gateway hardening (2026-08-10), Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z) (+34 more)

### Community 40 - "_assert_broker_state_matches_db"
Cohesion: 0.14
Nodes (27): ActiveMonitor, _assert_broker_state_matches_db(), broker_fill_payload(), _filled_entry_without_trade(), _filled_exit_with_open_trade(), _run_reconciler_once(), test_active_monitor_reports_trade_only_while_task_runs(), test_filled_entry_intent_rejects_wrong_broker_ratio() (+19 more)

### Community 41 - "date"
Cohesion: 0.08
Nodes (15): _age_fields(), build_session(), carry_quotes(), GuardedSource, has_print(), index_on_grid(), minute_grid(), RecordedSource (+7 more)

### Community 42 - "Schwab Gateway Migration Plan"
Cohesion: 0.09
Nodes (21): Credential-proof gate, Current migration status, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison, Phase 4 — read-only cutover (+13 more)

### Community 43 - "test_collector_timing.py"
Cohesion: 0.24
Nodes (9): _collector(), _no_side_effects(), _provider(), test_aligned_pass_fetches_the_chain_first_and_records_the_tick(), test_all_paper_strategy_configs_record_timing(), test_default_config_keeps_the_untimed_path(), test_meta_write_failure_does_not_block_the_chain_insert(), test_provider_without_observations_records_unobserved_meta() (+1 more)

### Community 44 - "test_gateway_order_book.py"
Cohesion: 0.18
Nodes (11): _recent_payload(), _snapshot(), test_client_rejects_unsafe_or_ambiguous_inputs(), test_recent_authenticates_and_validates_fresh_contract(), recent(), test_recent_fails_closed_when_gateway_reports_stale_feed(), test_recent_rejects_mismatched_snapshot(), test_stream_authenticates_and_yields_only_requested_contracts() (+3 more)

### Community 45 - "fidelity.py"
Cohesion: 0.08
Nodes (21): Accumulator, Agreement, _bucket(), compare_session(), fly_widths(), FlyStats, _fmt(), Hist (+13 more)

### Community 46 - "set_readiness"
Cohesion: 0.09
Nodes (35): readiness_snapshot(), set_readiness(), BrokerCashSettlement, test_health_stays_live_while_ready_reports_degraded(), test_readiness_recovery_clears_only_its_own_reason(), test_readiness_tracks_degraded_reason(), _candle(), _monitor_patches() (+27 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.15
Nodes (25): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+17 more)

### Community 48 - "backfill_equity_candles.py"
Cohesion: 0.09
Nodes (15): Streaming, Streaming flow, JsonlStreamRecorder, symbol_directory(), utc_now(), write_candle_snapshot(), async_main(), main() (+7 more)

### Community 49 - "source_hashes"
Cohesion: 0.05
Nodes (40): source_hashes, pyproject.toml, src/butterfly_guy/backtest/chain_cache.py, src/butterfly_guy/backtest/data_loader.py, src/butterfly_guy/backtest/db_loader.py, src/butterfly_guy/backtest/execution_accounting.py, src/butterfly_guy/backtest/__init__.py, src/butterfly_guy/backtest/metrics.py (+32 more)

### Community 50 - "test_position_data_diagnostics.py"
Cohesion: 0.26
Nodes (15): held_leg_evidence(), candidate(), chain_quotes(), shadow(), test_completed_shadow_samples_are_rate_limited(), test_held_leg_records_the_filtered_quote_instead_of_losing_its_evidence(), test_missing_contract_and_chain_failure_are_distinct(), test_position_monitor_never_values_or_exits_using_shadow_prices() (+7 more)

### Community 51 - "live_performance.py"
Cohesion: 0.08
Nodes (37): chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes(), equity_chart_description() (+29 more)

### Community 52 - "Target Trading Platform"
Cohesion: 0.12
Nodes (15): AfterHoursLab compatibility, Architecture decisions, Boundaries, Configuration model, Deployment topology, Events and Discord, Failure policy, Foundation proof (+7 more)

### Community 53 - "ButterflyGuy AI Review State"
Cohesion: 0.20
Nodes (9): Active Work Item, ButterflyGuy AI Review State, Current Objective, Important Files Reviewed, Next Session Launch Prompt, Non-Negotiable Rules, Ranked Issues, Remaining Risks (+1 more)

### Community 54 - "Window A — Token re-authorization (mandatory)"
Cohesion: 0.10
Nodes (20): A0 — Snapshot (read-only), A1 — Disable the keepalive, A2 — Stop the three trading services, A3 — Re-authorize, A4 — Verify the new document, A5 — Start the three services, A6 — Restore the keepalive, A7 — Verify (+12 more)

### Community 55 - "load_config"
Cohesion: 0.10
Nodes (23): load_config(), _regimes(), test_allow_live_trading_requires_explicit_env(), test_checked_in_configs_keep_default_regime_bounds(), test_config_rejects_unknown_keys(), test_config_rejects_unsafe_trading_values(), test_database_dsn(), test_database_dsn_encodes_password() (+15 more)

### Community 56 - "strategy_parameters"
Cohesion: 0.07
Nodes (30): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+22 more)

### Community 57 - "weekend_review.py"
Cohesion: 0.09
Nodes (36): compute_stats(), ReportStats, TradePoint, build_combined_performance_chart_png(), build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle() (+28 more)

### Community 58 - "simulate.py"
Cohesion: 0.07
Nodes (30): What the definition hash covers, Hypothesis rules (implemented, not registered), Rules that learn, fit_variant_entry(), History, is_fitted(), is_learning(), LeakageError (+22 more)

### Community 59 - "thetadata_download.py"
Cohesion: 0.08
Nodes (19): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), run_check_cycle(), send_discord_alert(), signal_handler() (+11 more)

### Community 60 - "GapRegimeFilter"
Cohesion: 0.25
Nodes (5): GapRegimeFilter, TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct, TestSkipBeforeOverride

### Community 61 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.10
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 62 - ".place_order"
Cohesion: 0.07
Nodes (19): Order and account flow, Recommendation, Reducing the weekly re-authorization cost — a scoping question, Status, The alternative worth costing first, The brief's proposed remedy, and why it is weaker than it looks, The cost being attacked, The questions to answer before building either (+11 more)

### Community 63 - "test_position_monitoring.py"
Cohesion: 0.21
Nodes (8): _candidate(), _gateway_contract(), _quotes(), _service(), test_intermittent_missing_held_leg_degrades_then_recovers_without_broker_write(), get_option_chain(), test_trade_282_uses_gateway_held_leg_when_contract_is_not_stale(), _trade_282_candidate()

### Community 64 - "parse_args"
Cohesion: 0.10
Nodes (23): 5. Live/backtest parity (P2), _asset_drawdowns(), _floatlist(), _intlist(), parse_args(), select_direction_bar(), _sim_parity_fields(), _strlist() (+15 more)

### Community 65 - "config.py"
Cohesion: 0.05
Nodes (55): Decision profiles, M7 — Regime names are unvalidated and regime time bounds are ignored, AppConfig, CollectorSettings, ConfigModel, DatabaseSettings, EntrySettings, ExecutionSettings (+47 more)

### Community 66 - "realized_vs_implied.py"
Cohesion: 0.15
Nodes (15): atm_straddle(), _fmt(), format_message(), MoveSummary, SessionMove, summarize(), _summary_line(), verdict() (+7 more)

### Community 69 - "sys"
Cohesion: 0.12
Nodes (21): baseline_entry(), bucket(), main(), main(), bs_gamma(), gex_levels(), main(), round_levels() (+13 more)

### Community 70 - "exit_trials/manifest.json"
Cohesion: 0.07
Nodes (27): account_sharpe, baseline_parity, command, created_utc, display_timezone, environment_variables, exit_commission_points, git_sha (+19 more)

### Community 71 - "test_prospective_execution.py"
Cohesion: 0.14
Nodes (33): manifest_path(), write_manifest(), _baseline(), _candidate(), _cohort(), _mock_cohort_update(), _quotes(), _record() (+25 more)

### Community 72 - "test_f2_shadow_report.py"
Cohesion: 0.08
Nodes (28): database(), vix(), row(), summary(), test_all_winning_sample_passes_profit_factor_gate(), test_cash_settlement_equals_cohort_under_every_model(), test_chronological_order_controls_drawdown_and_stop(), test_drawdown_exactly_at_limit_does_not_stop() (+20 more)

### Community 73 - "build_market_events.py"
Cohesion: 0.08
Nodes (35): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+27 more)

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 75 - "et_us"
Cohesion: 0.06
Nodes (28): session_rows(), _session_z(), SessionLoader, AbsoluteLossStop, config_exit_rules(), ExitDecision, ExitRule, monitor() (+20 more)

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.09
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 78 - "all_history_trials/manifest.json"
Cohesion: 0.05
Nodes (39): account_return_sharpe_marked_drawdown, baseline_scenario_regressions, command, created_utc, dependency_lock_sha256, environment_variables, git_sha, input_hashes (+31 more)

### Community 79 - "SchwabClientWrapper"
Cohesion: 0.09
Nodes (35): Authentication and token lifecycle, Shared-token risk, Option A Live Serving (built offline, never deployed), SchwabSettings, SchwabClientWrapper, _accessors(), factory(), _account_client() (+27 more)

### Community 80 - "strategy_parameters"
Cohesion: 0.06
Nodes (31): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+23 more)

### Community 81 - "Any"
Cohesion: 0.08
Nodes (14): Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Production marker-change proof (2026-08-10), Stale-writer follow-up (2026-08-10), Item 3 built — the token reload (2026-08-09, NOT deployed), Stale-lineage persistence guard deployed (2026-08-10T20:00:48Z), The C1 write proved itself in production, on the new code, The correction that forced the restarts (+6 more)

### Community 82 - "position_service.py"
Cohesion: 0.05
Nodes (22): Provider, get_logger(), is_premarket_window(), minutes_since_open(), now_eastern(), session_date(), canonicalize_schwab_chain_symbol(), ChainObservation (+14 more)

### Community 83 - "Architecture"
Cohesion: 0.10
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "ButterflyGuy data sources and data types"
Cohesion: 0.11
Nodes (18): 10. Repository evidence map, 4. Shared database tables visible to the same DB account, 5.1 Application YAML configuration, 5.2 Environment variables and `.env`, 5.3 `tokens.json`, 5.4 Universe and metadata files, 5.5 Historical minute CSVs, 5.6 Local daily bar cache (+10 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "ThetaDataSource"
Cohesion: 0.17
Nodes (6): parse_quotes(), ThetaDataError, ThetaDataSource, _ymd(), test_after_the_files_end_spx_and_vix_come_from_the_recorded_dataset(), test_millisecond_timestamps_with_trimmed_zeros_parse()

### Community 87 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.25
Nodes (15): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+7 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.30
Nodes (13): _dashboard(), _expressions(), _panels(), visit(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_position_value_checks_eligible_trades_before_monitoring_history(), test_retired_experimental_runtime_is_absent_from_dashboards(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource() (+5 more)

### Community 91 - "MinuteBar"
Cohesion: 0.08
Nodes (9): MinuteBar, BiasScoreFilter, RegimeFilter, make_bar(), make_pre_entry_bars(), TestBiasScore, TestComputeOr, TestComputeVwap (+1 more)

### Community 92 - "test_weekend_review.py"
Cohesion: 0.14
Nodes (18): trade_point_from_row(), previous_mon_fri(), _row(), test_calendar_month_to_date(), test_caption_and_recap_show_paper_and_executable_side_by_side(), test_cash_settled_exit_uses_settlement_value(), test_executable_pnl_is_none_without_recorded_prices(), test_executable_pnl_uses_marketable_entry_and_exit() (+10 more)

### Community 93 - "mechanism.py"
Cohesion: 0.15
Nodes (13): bootstrap(), confine(), _f(), fetch_spx(), frame_sha256(), _group(), markdown(), parse_spx_csv() (+5 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.29
Nodes (7): 2026-07-14 — data audit and research design, Data limitations and leakage controls, Final data-driven pass, First-pass result, Predeclared hypotheses (no tuning yet), Second structural pass, Verified data

### Community 95 - "Re-authorization checklist — Saturday 2026-08-15"
Cohesion: 0.13
Nodes (14): Automated warnings before the cadence reset, Before you start, Expected result: no containers restarted, First, watch the reload do its job, Re-authorization checklist — Saturday 2026-08-15, Step 0 — already done, nothing to do, Step 1 — mint the token on zeus, in a real terminal, Step 2 — stage on Helios and verify byte-identical (+6 more)

### Community 96 - "main"
Cohesion: 0.23
Nodes (6): _order(), test_redacted_audit_excludes_other_underlyings(), test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes(), test_redacted_audit_treats_replaced_as_historical_terminal(), main(), _redacted_order_audit()

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "argparse"
Cohesion: 0.06
Nodes (15): setup_logging(), DatabasePool, run_migrations(), trade_pnl_dollars(), main(), _load_trade(), main(), test_migrations_and_weekly_pnl_query() (+7 more)

### Community 99 - "read_jsonl"
Cohesion: 0.27
Nodes (19): daily_runs_path(), read_jsonl(), record_session(), summarize_cohort(), trades_path(), verify_cohort(), current_summary(), _recorded_cohort() (+11 more)

### Community 100 - "generate_live_performance.py"
Cohesion: 0.18
Nodes (12): now_pacific(), no_trade_reason(), NoTradeDay, best_trade(), reference_spot(), build_report(), fetch_closed_trades(), fetch_no_trade_days() (+4 more)

### Community 101 - "ButterflyCandidate"
Cohesion: 0.05
Nodes (36): _as_float(), _as_int(), rows_to_option_quotes(), ButterflyCandidate, fly_mark_value(), OptionQuote, _max_leg_spread_to_mark_ratio(), HeldQuoteRecovery (+28 more)

### Community 102 - "SimulationEngine"
Cohesion: 0.10
Nodes (21): Phase 2: one exit kernel, Why a plan is still needed, 6. Cleanup (P3), DayData, DayResult, RegimeDispatch, SimulationEngine, SimulationParams (+13 more)

### Community 103 - "yaml"
Cohesion: 0.14
Nodes (6): load_daily_report_card_config(), ReportCardThresholds, test_default_compose_binds_the_token_directory_never_the_document(), test_default_compose_token_binds_require_the_shared_token_directory(), test_each_strategy_has_an_independent_default_direct_gateway_toggle(), test_live_configs_leave_token_path_to_the_environment()

### Community 104 - "run_all_history.py"
Cohesion: 0.21
Nodes (13): all_stresses(), assert_prior_result(), ledger_parity(), main(), paired_comparison(), select_sources(), points(), test_all_scenarios_equal_original_replays() (+5 more)

### Community 105 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.20
Nodes (10): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding, Window F addendum 2 — the C1 lock change deployed (2026-08-08) (+2 more)

### Community 106 - "test_research_catalog.py"
Cohesion: 0.48
Nodes (5): _append(), test_catalog_fails_on_a_broken_chain(), test_catalog_lists_hashes_registries_and_counts(), test_history_counts_events_for_the_exact_definition(), test_history_of_a_port_includes_its_placeholder()

### Community 107 - "test_research_calendar.py"
Cohesion: 0.10
Nodes (14): _date(), MarketEvent, parse_row(), _row(), test_committed_calendar_has_a_scheduled_event_of_each_type_every_year(), test_event_published_on_or_after_the_session_is_invisible_to_it(), test_file_level_checks(), test_hash_follows_content_and_version_follows_file_name() (+6 more)

### Community 108 - "services/daily_report_card.py"
Cohesion: 0.18
Nodes (8): PriceHistoryProvider, archive_report(), chartable_equity_trades(), format_equity_trade_chart_caption(), ReportCardResult, send_daily_report_card(), _send_equity_trade_charts(), test_chartable_equity_trades_skips_options()

### Community 109 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 110 - "Re-authorization checklist — Saturday 2026-08-22"
Cohesion: 0.18
Nodes (10): Preconditions — verified 2026-08-22T15:45:36Z, Re-authorization checklist — Saturday 2026-08-22, Step 1 — mint on zeus, in a real terminal, Step 2 — stage on Helios, verify byte-identical, Step 3 — move into place under the C1 lock, Step 4 — watch the reloads; restart only on a *confirmed* failure, Step 5 — verify, host against containers, Step 6 — record (+2 more)

### Community 112 - "AGENTS.md"
Cohesion: 0.12
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 114 - "pandas"
Cohesion: 0.05
Nodes (41): `DataSource` adapter spec, chain_to_table(), default_cache_root(), dense_chain_from_rows(), Manifest, session_dir(), SessionChain, table_to_chain() (+33 more)

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
Cohesion: 0.18
Nodes (10): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+2 more)

### Community 122 - "Path"
Cohesion: 0.20
Nodes (7): build_manifest(), git_state(), manifest_drift(), ManifestDriftError, require_frozen_manifest(), sha256_path(), source_hashes()

### Community 123 - "test_daily_report_card.py"
Cohesion: 0.15
Nodes (13): parse_trade_transactions(), rank_trades(), candles_to_series(), test_build_equity_trade_chart_png_returns_png_bytes(), test_equity_chart_aggregates_to_two_minute_candles(), test_equity_chart_stats_text_includes_key_fields(), test_equity_chart_window_keeps_6am_premarket_and_regular_session(), test_equity_chart_window_rejects_prior_day_same_times() (+5 more)

### Community 124 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 125 - "run_trials.py"
Cohesion: 0.22
Nodes (9): bootstrap_mean_delta(), compare(), main(), sha(), stats(), write_csv(), config(), test_pairing_never_presents_missing_winner_as_zero() (+1 more)

### Community 127 - "test_run_migrations.py"
Cohesion: 0.27
Nodes (4): fake_db(), FakeConnection, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 128 - "diagnose.py"
Cohesion: 0.29
Nodes (10): breakdowns(), cell(), coverage(), _half(), markdown(), _money(), _r(), session_table() (+2 more)

### Community 129 - "Phases"
Cohesion: 0.17
Nodes (11): Entry-point inventory and fate, Open owner decisions, Phase 0: land what exists, Phase 1: one command surface, Phase 3: commit the analysis that decisions rest on, Phase 4: link the stages, Phase 5: data upkeep, Phases (+3 more)

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
Cohesion: 0.17
Nodes (5): _error_code(), _mismatch_code(), _numbers_agree(), ShadowComparingMarketDataProvider, test_non_shadowed_reads_are_pure_delegation()

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "DiscordNotifier"
Cohesion: 0.08
Nodes (15): send_alertmanager(), broker_reconciler_loop(), _reconcile_broker_state(), AlertmanagerNotifier, DiscordNotifier, test_alertmanager_failed_resolution_retries_until_accepted(), send_alertmanager(), to_thread() (+7 more)

### Community 137 - "replay.py"
Cohesion: 0.23
Nodes (16): main(), main(), metrics(), path_for(), replay(), timestamp(), write_csv(), points() (+8 more)

### Community 138 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.12
Nodes (10): Corrections to the Window G brief, End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, The fix, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08) (+2 more)

### Community 139 - "Registration decision package: ThetaData development window (2026-09-29)"
Cohesion: 0.11
Nodes (18): 1. Data and integrity, 2. Baseline E0 (descriptive; do not tune on it), 3. The hypotheses on the development window (in-sample), 4. Holdout size and power, 5. VIX-smoothing sensitivity, 6.1 Stressed exits below zero: decided, now floored (D3, draft Revision 1), 6.2 Gate 1 passed skip filters too often under the null: decided, now calibrated (D4, draft Revision 4), 6.3 A paired pass against a losing baseline: decided, gate 6 added (D2, draft Revision 5) (+10 more)

### Community 140 - "test_position_quote_recovery.py"
Cohesion: 0.38
Nodes (7): observation(), response(), recovery(), test_complete_fresh_response_recovers_all_legs_and_rate_limits(), test_monitor_only_evaluates_complete_fresh_recovery(), test_rejects_unusable_response_without_partial_or_stale_valuation(), test_request_failure_is_bounded_and_cancellation_propagates()

### Community 141 - "F2 prospective shadow registration — 2026-10-02"
Cohesion: 0.22
Nodes (7): Definition, Endpoint and gates (fixed now, judged only at the endpoint), Evidence that motivated it (all in-sample or partly used), F2 prospective shadow registration — 2026-10-02, How it is scored, Operation, F2 draft scorer review — 2026-10-03

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
Cohesion: 0.29
Nodes (7): Code and experiment freeze, Full development eligibility audit, Normalization and frozen baseline — completed, Persistent inputs and provenance, Preserved research boundaries, Reproduce from durable inputs, ThetaData durable backtesting execution — 2026-10-01

### Community 147 - "Stage-named proof failure and an unpaused restoration — 2026-08-06"
Cohesion: 0.29
Nodes (7): Disposition, Result, Stage-named proof failure and an unpaused restoration — 2026-08-06, The failure stage was identified read-only before the attempt was spent, The remaining defect, The restoration no longer pauses trading, What this does and does not say about the previous window

### Community 148 - "Schwab Gateway Multi-Consumer Foundation"
Cohesion: 0.29
Nodes (6): ButterflyGuy-first admission policy, Historical evidence classification, Ownership and contracts, Schwab Gateway Multi-Consumer Foundation, Status and safety boundary, Trust model

### Community 150 - "entry.py"
Cohesion: 0.05
Nodes (34): ATMEntry, baseline_window(), BaselineEntry, BothSides, _call_only(), DecisionProfile, Entry, FilteredEntry (+26 more)

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
Nodes (6): BrokerStateGate, test_broker_state_gate_records_unsafe_reason(), test_failed_token_reload_blocks_new_entries(), test_runtime_reconciliation_resolution_rearms_alert(), test_token_reload_loop_survives_a_failed_reload(), reload_if_reauthorized()

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

### Community 164 - "broker_cash_settlement_from_transactions"
Cohesion: 0.25
Nodes (4): broker_cash_settlement_from_transactions(), SettlementEvidenceError, _transaction_time(), test_broker_cash_settlement_uses_actual_cash_and_fees()

### Community 165 - "spx-prospective-v2-2026-10-02/manifest.json"
Cohesion: 0.12
Nodes (15): asset, cohort_id, config, path, sha256, created_at, database_tables, git (+7 more)

### Community 166 - "ThetaData data-quality plan and validation amendment (2026-09-28)"
Cohesion: 0.05
Nodes (36): After Parts A and B, Headline numbers, How approximate this is, Run, Schwab recording fidelity baseline (2026-10-04), Baseline (required in PR 1), Behavior, Check the impact on live reads (+28 more)

### Community 168 - "butterfly mark"
Cohesion: 0.20
Nodes (7): BUTTERFLYGUY, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background, node-and-line network geometry, uppercase geometric wordmark style

### Community 169 - "Preflight stops on the host-executed release — 2026-08-06"
Cohesion: 0.67
Nodes (3): Credential exposure during the window, Preflight stops on the host-executed release — 2026-08-06, Release

### Community 170 - "test_gateway_token_manager.py"
Cohesion: 0.14
Nodes (26): increment_callback(), manager(), _process_refresh(), delayed_increment(), test_callback_failure_preserves_original_and_redacts_error_and_logs(), test_concurrent_managers_serialize_the_entire_refresh_callback(), first_refresh(), second_refresh() (+18 more)

### Community 171 - "ButterflyGuy data sources — representative samples"
Cohesion: 0.33
Nodes (5): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs

### Community 172 - "Host-executed proof step"
Cohesion: 0.67
Nodes (3): Host-executed proof step, Release, Workflow consequence the next window must plan for

### Community 175 - "Live Runbook"
Cohesion: 0.25
Nodes (7): During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery, XSP Canary

### Community 177 - "PositionManager"
Cohesion: 0.17
Nodes (16): PeakTrackingSettings, PositionManager, _quote_quality_ok(), replay_trade(), make_quote(), make_xsp_candidate(), quote_map(), test_missing_held_quote_preserves_last_mark_without_returning_stale_state() (+8 more)

### Community 179 - "_build_collector_market_data"
Cohesion: 0.14
Nodes (10): C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, The wiring point, What C3 does not do, _build_collector_market_data(), test_default_settings_construct_no_gateway_client() (+2 more)

### Community 180 - "Prospective execution validation — spx-prospective-2026-09-22"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-2026-09-22, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 181 - "H-TR1 registration — trail armed at +75% with a breakeven floor"
Cohesion: 0.13
Nodes (11): Data, Entries (frozen, unchanged from the 09-25 harness replica), H-TR1 registration — trail armed at +75% with a breakeven floor, Hypothesis, Pass criteria (all must hold; stressed accounting; per one-lot), Reported but not gating, Result (run once, 2026-10-01, at b0b7215), Run (+3 more)

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (8): Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy, XSP Account and Loss Guards

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (6): BUTTERFLYGUY, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 184 - "Research core"
Cohesion: 0.14
Nodes (13): Accounting and evaluation, Auxiliary inputs (manifest schema 2), Data, Diagnostics (descriptive only), Event calendar, Known differences, Mechanism check for H-TS1 (descriptive only), Overnight futures (ES): audit only (+5 more)

### Community 185 - "test_research_protocol.py"
Cohesion: 0.35
Nodes (11): _cli(), _holdout(), _no_replay(), _pull_holdout(), _records(), test_a_fitted_rule_is_registered_with_its_value_and_checked_at_the_holdout(), test_evaluates_the_registered_set_once_and_records_every_look(), test_h_sn1_is_refused_until_gate_5_has_a_statistic() (+3 more)

### Community 186 - "Options strategy discovery journal"
Cohesion: 0.05
Nodes (38): 2026-07-14 — diminishing returns checkpoint, 2026-09-20 — SPX cash-settlement parity correction, 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data), 2026-09-29/30 — Package review, provenance, D7, D10, 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered), 2026-09-29 (later) — D6: no Indices month, 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0, 2026-09-30 — H-TS1 registered and evaluated on the holdout: FAIL (+30 more)

### Community 187 - "2026-09-21 — prospective execution-validation cohort (pre-registration)"
Cohesion: 0.18
Nodes (11): 2026-09-21 — prospective execution-validation cohort (pre-registration), Checkpoint results, Dry-run rehearsal, Exact commands, Implementation fingerprints at pre-registration, Ledgers and integrity, Pre-registered hypothesis, Quote-handling rules (+3 more)

### Community 188 - "mini_spx/manifest.json"
Cohesion: 0.20
Nodes (9): dataset, dataset_hash, exporter_git_sha, schema_version, source, from_dataset_hash, kind, underlying (+1 more)

### Community 189 - "decision_rules"
Cohesion: 0.22
Nodes (9): decision_rules, checkpoint_trades, early_failure_trades, max_drawdown, max_top3_gross_profit_share, min_executable_entry_coverage, min_profit_factor, primary_hypothesis (+1 more)

### Community 190 - "test_gateway_ownership_boundaries.py"
Cohesion: 0.24
Nodes (3): _source(), test_compose_keeps_each_strategy_default_direct_with_staged_gateway_opt_in(), test_standalone_packages_remain_pinned_and_consumers_import_them_directly()

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - "OptionChainProvider"
Cohesion: 0.32
Nodes (5): Interfaces and contracts, EquityQuoteProvider, MarketMoversProvider, OptionChainProvider, SpotPriceProvider

### Community 193 - "pytest"
Cohesion: 0.06
Nodes (46): The holdout (`holdout.py`), cmd_export_history(), excluded_sessions(), get_source(), HistoryPlan, write_history(), HoldoutSealedError, Unseal (+38 more)

### Community 194 - "2026-09-21 — SPX executable-side accounting on the settlement-correct replay"
Cohesion: 0.29
Nodes (7): 2026-09-21 — SPX executable-side accounting on the settlement-correct replay, Accounting models and deterministic data rules, Data provenance and coverage, Exact commands and implementation fingerprints, Frozen result, Pre-registered drawdown limit, Reproduction under the roll-forward exit rule

### Community 195 - "et_ts"
Cohesion: 0.18
Nodes (8): directions(), ema(), hma_series(), hourly_closes_before(), hull_rising(), wma(), et_ts(), Market

### Community 196 - "2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)"
Cohesion: 0.25
Nodes (8): 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered), Changes, E0 loses on the development window, Findings about the test itself, Hypotheses, paired with E0 (draft bootstrap: 10-session blocks, 10,000 reps), Integrity, Power (from development vectors; assumes 2022–24 is representative), Recommendation for the owner

### Community 197 - "Prospective execution validation — spx-prospective-v2-2026-10-02"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-v2-2026-10-02, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 198 - "Next SPX sweep on vendor history — pre-registration DRAFT (not registered)"
Cohesion: 0.29
Nodes (6): Baseline, Data and split (fixed now, before any vendor data is seen), Hypotheses, Next SPX sweep on vendor history — pre-registration DRAFT (not registered), Out of scope for this sweep, Primary metric and gate

### Community 199 - "DirectProvider"
Cohesion: 0.13
Nodes (4): DirectProvider, FailingDirectProvider, test_get_option_chain_returns_before_a_slow_gateway_responds(), get_chain_metadata()

### Community 200 - "load_report_gateway_settings"
Cohesion: 0.32
Nodes (3): test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings()

### Community 201 - "Offline safety-drill record — 2026-07-13"
Cohesion: 0.29
Nodes (6): Drill findings fixed, Follow-up — 2026-07-14, Offline safety-drill record — 2026-07-13, Remaining do-now work, Result, Verification

### Community 202 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (3): main(), parse_args(), run()

### Community 203 - "ThetaData option history (raw)"
Cohesion: 0.29
Nodes (6): Conventions, Layout, Reading, Sets, The spent holdout (2024-07-01 to 2026-03-12), ThetaData option history (raw)

### Community 204 - "discover_options_strategy.py"
Cohesion: 0.15
Nodes (33): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+25 more)

### Community 205 - "test_research_thetadata.py"
Cohesion: 0.12
Nodes (21): _cboe(), _day_quotes(), files(), _minute_rows(), _quote_csv(), _source(), Terminal, test_a_holdout_pull_stops_before_any_terminal_request() (+13 more)

### Community 206 - "2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)"
Cohesion: 0.33
Nodes (6): 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run), Also changed, Readings the draft left open, now fixed in code, for the owner to review before registering, Refusals, all before any holdout session is replayed, Tests, The command

### Community 207 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.13
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 208 - "ThetaData backtesting readiness and completion plan"
Cohesion: 0.29
Nodes (7): Data inventory and remaining limits, Defined steps to complete broad SPXW backtesting, Execution follow-through, Separate extensions, ThetaData backtesting readiness and completion plan, What is ready, Working smoke command and evidence

### Community 209 - "dev_studies.py"
Cohesion: 0.26
Nodes (6): cmd_calibrate(), cmd_check(), cmd_power(), cmd_random_skip(), load(), main()

### Community 210 - "quote_rules"
Cohesion: 0.29
Nodes (7): quote_rules, crossed_market, entry_gap, exit_gap, missing_market, selection, substitution

### Community 211 - "chain_cache.py"
Cohesion: 0.19
Nodes (14): chain_cache_path(), chain_journal_path(), load_chain_day(), nearest_snapshot(), _read_snapshots(), save_snapshot(), test_chain_cache_path_is_partitioned_by_underlying(), test_load_chain_day_falls_back_to_partitioned_spx_cache() (+6 more)

### Community 212 - "files"
Cohesion: 0.29
Nodes (7): rows, sha256, files, daily_bars.parquet, sessions/2026-07-13/chain.parquet, rows, sha256

### Community 213 - "prospective_execution.py"
Cohesion: 0.07
Nodes (28): Shadow on the open cohort, ExecutableTrade, append_jsonl(), append_unique(), _breakdown(), build_daily_run_record(), build_trade_record(), canonical_hash() (+20 more)

### Community 214 - "HistorySource"
Cohesion: 0.07
Nodes (19): 2026-09-28 — stage 5: corrected data decision, housekeeping, ThetaData readiness (stubbed), H-TS1 mechanism check (development window, descriptive), Data decision (corrected), H-TS1 mechanism check (DESCRIPTIVE — development window — not a rule evaluation), Housekeeping, ThetaData readiness (stubbed, nothing bought, nothing downloaded), Completion checklist, Facts and constraints to carry forward, Implementation prompt: finish local ThetaData backtesting support (+11 more)

### Community 215 - "docs/README.md"
Cohesion: 0.08
Nodes (18): Canonical research datasets, Backfill candles, Equity candles and order-book recording, Historical limitation, Operational caution, Live WebSocket, Recent snapshots, SchwabGateway order books (+10 more)

### Community 216 - "run_classifier_sweep.py"
Cohesion: 0.10
Nodes (14): CsvDataLoader, max_consecutive_losses(), max_drawdown(), profit_factor(), sharpe(), win_pct(), _accounting_metrics(), _summarize_combo() (+6 more)

### Community 217 - "Offline ThetaData research"
Cohesion: 0.20
Nodes (8): Baseline and exposure, Commands, Lifecycles, accounting and limits, Mapping and access, Offline ThetaData research, Verification artifacts, Real private artifacts, ThetaData local implementation verification

### Community 220 - "decision_rules"
Cohesion: 0.22
Nodes (9): decision_rules, checkpoint_trades, early_failure_trades, max_drawdown, max_top3_gross_profit_share, min_executable_entry_coverage, min_profit_factor, primary_hypothesis (+1 more)

### Community 222 - "day_with_monitoring_bars"
Cohesion: 0.48
Nodes (4): day_with_monitoring_bars(), _bar(), test_day_with_monitoring_bars_adds_live_poll_timestamps(), test_day_with_monitoring_bars_keeps_existing_bar_for_same_timestamp()

### Community 223 - "Cohort automation"
Cohesion: 0.29
Nodes (6): Check on it, Cohort automation, Install, Known limitation: the SSH key, Retired v1, When the cohort closes

### Community 224 - "assumptions"
Cohesion: 0.33
Nodes (6): assumptions, commission_per_contract, contract_multiplier, contracts_per_butterfly, quantity, stressed_leg_slippage

### Community 225 - "test_run_live.py"
Cohesion: 0.09
Nodes (32): _close_runtime_resources(), gateway_runtime_phase_delay(), _never_awaited(), _run_daily_reset_once(), _synthetic_butterfly_snapshot(), _synthetic_position(), test_collector_market_data_shadow_is_opt_in_and_direct_authoritative(), test_daily_reset_keeps_regime_when_reclassification_fails() (+24 more)

### Community 226 - "unittest_mock"
Cohesion: 0.07
Nodes (11): test_auth_init_honours_schwab_token_path(), lock_events(), _run_with_stub_token(), test_token_keepalive_exits_when_the_token_lock_is_held(), test_token_keepalive_honours_schwab_token_path(), test_token_keepalive_refreshes_inside_the_token_lock(), refresh(), test_token_keepalive_reports_alertmanager_failure() (+3 more)

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
Cohesion: 0.17
Nodes (11): Assumptions requiring verification, Configuration, secrets, and deployment assumptions, Current Schwab Integration, Database and messaging dependencies, Direct SDK construction and imports, Discord and operational dependencies, Equity and research paths, Extraction boundaries (+3 more)

### Community 231 - "test_a_discrepancy_counts_once_as_a_comparison_and_once_by_code"
Cohesion: 0.29
Nodes (4): _comparisons(), test_a_disabled_shadow_records_no_metrics_at_all(), test_a_discrepancy_counts_once_as_a_comparison_and_once_by_code(), test_a_failing_direct_read_is_counted_separately_from_a_discrepancy()

### Community 232 - "XSP protection and fresh-quote recovery candidate — October 8, 2026"
Cohesion: 0.33
Nodes (5): Candidate contract, Frozen development evidence and mechanics replay, Observed causes and boundaries, Reproduce, XSP protection and fresh-quote recovery candidate — October 8, 2026

### Community 233 - "Held-position market-data diagnostics"
Cohesion: 0.50
Nodes (3): Behavior, Deployment and verification, Held-position market-data diagnostics

### Community 234 - "SPX idea sweep — registry (written 2026-09-25 before any variant was run)"
Cohesion: 0.50
Nodes (3): Round 2 — POST-HOC (written after seeing round-1 results; exploratory only), SPX idea sweep — registry (written 2026-09-25 before any variant was run), Variants

### Community 235 - "SchwabGateway option-chain latency investigation (2026-09-04)"
Cohesion: 0.20
Nodes (9): 2026-09-09 runtime follow-up, Cache TTL is hard-capped at 4s in code, not just config, Chain size correlation, Recommendation, Request path (cache miss), SchwabGateway option-chain latency investigation (2026-09-04), Where the time actually goes: scheduler queueing, not the Schwab call itself, XSP held-leg event-age correction (2026-09-11) (+1 more)

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

### Community 241 - "test_research_mechanism.py"
Cohesion: 0.18
Nodes (13): _inputs(), _sessions(), _synthetic(), test_bootstrap_is_deterministic(), test_cboe_spx_parser(), test_decision_rule_on_planted_and_null_effects(), test_first_session_uses_the_prior_development_session(), test_prior_values_come_from_the_previous_spx_session() (+5 more)

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
Cohesion: 0.16
Nodes (9): ContractTiming, _finite_number(), GatewayMarketDataError, _nonnegative_integer(), OmittedContract, _optional_number(), _require_usable_observation(), _same_symbol() (+1 more)

### Community 260 - "Window C — the two token writers resolved (2026-08-08)"
Cohesion: 0.25
Nodes (8): C1 — the operator chose the shared lock, C3 plan produced, and a stale design point corrected, Durability decided, monitoring still open, Housekeeping, Multi-consumer shape — confirmed sound, with two wrinkles, Proven on the host by the production path, at zero extra token writes, Still open, Window C — the two token writers resolved (2026-08-08)

### Community 261 - "report_broker_order_statuses.py"
Cohesion: 0.27
Nodes (12): _allowed_roots(), _build_payload(), main(), _order_symbols(), _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses(), test_payload_excludes_non_spx_orders() (+4 more)

### Community 263 - "SPX paper-trade review — September 12, 2026"
Cohesion: 0.33
Nodes (5): Evidence and scope, Findings, Mechanism worth testing, Research pipeline and proposed experiment, SPX paper-trade review — September 12, 2026

### Community 264 - "spx-idea-sweep-2026-09-25/variants.py"
Cohesion: 0.07
Nodes (27): open_spot(), ev_rank_factory(), fn(), r1(), r2(), r5(), ratio_at(), ror() (+19 more)

### Community 266 - "execution_accounting.py"
Cohesion: 0.12
Nodes (21): _entry_debit(), _exit_credit(), _finite_quote_side(), inspect_quote_market(), price_frozen_trade(), QuoteMarket, snapshot_at_or_before(), snapshot_keys() (+13 more)

### Community 268 - "test_research_accounting.py"
Cohesion: 0.08
Nodes (49): Costs, price_trade(), Series, PeakTrailer, delayed_exit_index(), simulate_entry(), fly_quotes(), make_chain() (+41 more)

### Community 294 - "Registration decision package — 2026-09 (for the owner; nothing is registered)"
Cohesion: 0.25
Nodes (7): Decisions only the owner can make, H-EV1 — skip pre-entry releases (`HEV1`), H-LV1 — skip low-VIX calls (`HLV1`), H-SN1 — σ-normalised selector (`HSN1`), H-TS1 — rich one-day implied (`HTS1`), Optional H-EV2 — skip FOMC statement days (not implemented), Registration decision package — 2026-09 (for the owner; nothing is registered)

### Community 297 - "exit_trials/PLAN.md"
Cohesion: 0.40
Nodes (3): Exit trials fixed before execution — September 13, 2026, Executed SPX exit trials, Reproduce

### Community 298 - "Implementation prompt: SPX session quality and exclusion ledger"
Cohesion: 0.25
Nodes (7): Boundaries, Deliverable and scope, Implementation prompt: SPX session quality and exclusion ledger, Ledger behavior, Read first and establish the checkout, Reconciliation targets, Verification and completion criteria

### Community 299 - "test_market_data_providers.py"
Cohesion: 0.20
Nodes (26): _bar(), _contract(), _observation(), test_empty_extended_session_is_allowed_but_other_flags_remain_fatal(), test_gateway_provider_adapts_history_and_combines_sessions(), test_gateway_provider_adapts_typed_spot_and_full_chain(), test_gateway_provider_canonicalizes_chain_symbol_at_client_boundary(), test_gateway_provider_defaults_normalized_null_time_value_to_zero() (+18 more)

### Community 301 - "All 108 historical entries: executed exit experiments"
Cohesion: 0.33
Nodes (4): All-history extension fixed before execution, All 108 historical entries: executed exit experiments, Outputs, Run locally

### Community 304 - "manifest.json"
Cohesion: 0.15
Nodes (12): created_utc, entry_prices, exit_commission_points, files, raw/checkout-source-hashes.json, raw/deployment.txt, raw/export.jsonl, raw/monitor.jsonl (+4 more)

### Community 314 - "Ernie (@0DTE) comparison — variant plan (not run)"
Cohesion: 0.12
Nodes (14): Constraints, D — direction, Data route (pending owner decision), E — entry trigger (structural levels), Ernie (@0DTE) comparison — variant plan (not run), Ernie's rules, as stated, Order, P — strike placement (+6 more)

### Community 315 - "test_collector_cadence.py"
Cohesion: 0.14
Nodes (11): et(), FakeClock, _run(), StopLoopError, test_a_stall_alerts_once_and_never_catches_up(), test_first_tick_is_the_open_and_last_is_before_the_early_close(), test_next_tick(), test_offset_shifts_the_grid() (+3 more)

### Community 352 - "DirectSchwabMarketDataProvider"
Cohesion: 0.19
Nodes (3): DirectSchwabMarketDataProvider, test_direct_provider_delegates_without_transforming_results(), test_direct_provider_observations_are_empty()

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

### Community 365 - "gates"
Cohesion: 0.15
Nodes (11): _blocks(), calibrate_gate1(), gates(), _gates(), test_a_steady_gain_passes_every_gate(), test_calibration_picks_the_loosest_level_within_the_target_and_tightens_skewed_rules(), test_each_gate_can_fail_on_its_own(), test_gate_1_is_the_drafted_bootstrap_at_one_minus_alpha_over_k() (+3 more)

### Community 366 - "TradeRecord"
Cohesion: 0.05
Nodes (20): Models and SDK coupling, M10 — Live settlement wait has no bound, and post-close failures surface late, M11 — A restart with an open trade double-counts the entry cost in daily P&L, M1 — The daily-bar refresh marks itself done after a failure, M3 — Runtime reconciler repair leaves an unmonitored, uncounted trade, M4 — Price-increment rounding is $0.01; SPX complex orders likely require $0.05 (Needs verification), M6 — A restart forgets `_ever_in_profit`, suppressing drawdown exits, M9 — The chain cache rewrites the whole day's JSON on the event loop (+12 more)

### Community 368 - "strategy_page.py"
Cohesion: 0.10
Nodes (23): _json_data_block(), _case_study(), _clock(), _entry_window_et(), _et_after_open(), _minutes_between(), _pct(), _regime_bar() (+15 more)

### Community 369 - "validate.py"
Cohesion: 0.07
Nodes (25): draw_keys(), promotion_shift(), selector_pool(), TiesetScorer, _compare(), _distribution(), _first_difference(), _iso() (+17 more)

### Community 371 - "run_live.py"
Cohesion: 0.05
Nodes (40): Historical Cycle Checkpoints, Baseline, Butterfly Guy Code Review — 2026-09-25, Executive summary, Findings index, Low / Info, Method, Operational note found during review (+32 more)

### Community 373 - "2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only), Cohort runner move (2026-09-27) and a labeling note, Cohort shadow (exploratory, three sessions), Exit-latency stress, Parity, Research core and data, Variant registry

### Community 374 - "install_shutdown_handler"
Cohesion: 0.22
Nodes (3): install_shutdown_handler(), test_shutdown_handler_tolerates_already_finished_tasks(), test_sigterm_cancels_supervised_loops_and_task_group_exits_cleanly()

### Community 375 - "2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)"
Cohesion: 0.33
Nodes (6): 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered), Consequences, Decision and change, Still open, The calibration study (scratch, development data), What it gives on the real dataset (in-process, nothing registered)

### Community 382 - "gateway_minute_backfill.py"
Cohesion: 0.32
Nodes (3): check(), dump(), main()

### Community 385 - "test_research_local.py"
Cohesion: 0.18
Nodes (21): Record a future BMNR session, normalize(), OneFly, raw(), source(), test_a_spent_holdout_session_imports_and_is_counted(), test_alternate_instrument_identity_and_fractional_grid(), test_alternate_instrument_replay_with_attributable_inputs() (+13 more)

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
Cohesion: 0.10
Nodes (19): Access, credential and timestamps, Assessment, Endpoints and request plan, Licence (individual plans), Plans and prices (as read), Purchase checklist, SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan, ThetaData: public-docs findings and purchase checklist (2026-09-28) (+11 more)

### Community 394 - "XSP improvements — sequential work record, October 6, 2026"
Cohesion: 0.11
Nodes (17): 2. XSP exit replay — baseline established before tuning, 3. Earlier trailer — experiment fixed before execution, 4. Independent width policy — no recent behavioral difference, 5. Execution and settlement evidence — proxy discrepancy measured, Reproduce, Result: refine; do not activate this candidate, XSP improvements — sequential work record, October 6, 2026, 2. High — the trailer and exit-quality floor conflict for modest peaks (+9 more)

### Community 396 - "Critical External-Alert Delivery Proof - 2026-07-15"
Cohesion: 0.40
Nodes (4): Critical External-Alert Delivery Proof - 2026-07-15, Implementation reviewed, Scope, Supervised delivery and deduplication result

### Community 397 - "csv"
Cohesion: 0.50
Nodes (5): main(), result_table(), main(), money(), table()

### Community 398 - "XSP Flat-Runtime Restart Proof - 2026-07-14"
Cohesion: 0.40
Nodes (4): Preconditions, Restart and verification, Scope, XSP Flat-Runtime Restart Proof - 2026-07-14

### Community 399 - "fill_models"
Cohesion: 0.50
Nodes (4): fill_models, corrected_midpoint, marketable, stressed_marketable

### Community 402 - "run_schwab_fidelity_daily.sh"
Cohesion: 0.67
Nodes (3): BUTTERFLY_RESEARCH_CACHE, research(), run_schwab_fidelity_daily.sh script

### Community 403 - "Reproduce the SPX exit-policy experiment"
Cohesion: 0.22
Nodes (7): Acquisition actually performed, Conditional end-to-end confirmation, Offline reproduction, Output map, Replay rules and costs, Reproduce the SPX exit-policy experiment, SPX exit-policy research — September 12, 2026

### Community 404 - "spot_ticks.parquet"
Cohesion: 0.67
Nodes (3): spot_ticks.parquet, rows, sha256

### Community 408 - "fly_settlement_value"
Cohesion: 0.15
Nodes (11): Assumptions, Corrected implementation fingerprints, Reproduction commands, Result, Settlement evidence and reconciliation, SPX frozen baseline: cash-settlement correction, fly_settlement_value(), make_candidate() (+3 more)

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **1124 isolated node(s):** `created_utc`, `range`, `trades`, `provider`, `original_acquisition_utc` (+1119 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2610 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `report_broker_order_statuses.py`, `butterfly_gateway_acceptance.py`, `DiscordNotifier`, `Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)`, `.get_orders_for_day`, `PositionService`, `Codex Project State`, `_assert_broker_state_matches_db`, `Schwab Gateway Migration Plan`, `backfill_equity_candles.py`, `_build_collector_market_data`, `.place_order`, `OptionChainProvider`, `Branch Review and Integration Plan`, `Any`, `position_service.py`, `DirectSchwabMarketDataProvider`, `Capability recorder design`, `main`, `test_run_live.py`, `ButterflyCandidate`, `Current Schwab Integration`, `services/daily_report_card.py`, `TradeRecord`, `run_live.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `Dataset` (e.g. with `cmd_cache_inputs()` and `cmd_import()`) actually correct?**
  _`Dataset` has 80 INFERRED edges - model-reasoned connections that need verification._
- **What connects `created_utc`, `range`, `trades` to the rest of the system?**
  _1124 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `run_paper_replay.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06202435312024353 - nodes in this community are weakly interconnected._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `run_paper_replay.py`, `test_order_manager.py`, `market.py`, `run_entry_analysis.py`, `execution_accounting.py`, `compute_tent_boundaries`, `test_research_accounting.py`, `entry.py`, `fly_settlement_value`, `reports/daily_report_card.py`, `PositionService`, `datetime`, `run_backtest_db.py`, `f2_shadow_report.py`, `PositionManager`, `test_position_data_diagnostics.py`, `test_position_monitoring.py`, `config.py`, `test_prospective_execution.py`, `position_service.py`, `prospective_execution.py`, `argparse`, `SimulationEngine`, `ButterflyOrderBuilder`, `TradeRecord`, `validate.py`, `run_live.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Should `EventCalendar` be split into smaller, more focused modules?**
  _Cohesion score 0.12643678160919541 - nodes in this community are weakly interconnected._