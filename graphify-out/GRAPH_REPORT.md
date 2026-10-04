# Graph Report - Butterflyguy  (2026-10-04)

## Corpus Check
- 429 files · ~890,346 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 46 file(s) not represented in the graph (top: .parquet 15, (none) 9, .jsonl 8)

## Summary
- 6745 nodes · 16921 edges · 412 communities (292 shown, 120 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 1962 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d279aaf4`
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
- simulate.py
- discover_options_strategy.py
- test_research_local.py
- test_gateway_shadow_reads.py
- 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)
- evaluate.py
- StrategySettings
- forex_calendar.py
- Schwab Gateway Credential Proof
- test_research_session_ledger.py
- protocol.py
- schwab_gateway_session_soak.py
- Manifest
- SyntheticChainGenerator
- export.py
- reports/daily_report_card.py
- TradeQueries
- SessionChain
- position_manager.py
- Registry
- test_chain_parser_parity.py
- test_risk_engine.py
- run_entry_analysis.py
- ProfitStateMachine
- run_backtest_db.py
- SchwabDataLoader
- run_prospective_execution.py
- research/shadow.py
- validate.py
- Codex Project State
- _assert_broker_state_matches_db
- pathlib
- Schwab Gateway Migration Plan
- test_research_learning.py
- test_gateway_order_book.py
- realized_vs_implied.py
- PositionService
- equity_trade_chart.py
- DayData
- source_hashes
- fidelity.py
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- Window A — Token re-authorization (mandatory)
- load_config
- strategy_parameters
- chain_cache.py
- test_research_parity.py
- test_position_monitoring.py
- run_classifier_sweep.py
- Standalone SchwabGateway Extraction Plan
- Regime
- Fly
- SchwabClientWrapper
- AppConfig
- DbDataLoader
- datetime
- exit_trials/manifest.json
- test_prospective_execution.py
- test_f2_shadow_report.py
- build_market_events.py
- launch_schwab_gateway_session_soak_20260904.sh
- SessionLoader
- Branch Review and Integration Plan
- test_order_preview.py
- all_history_trials/manifest.json
- test_schwab_client.py
- strategy_parameters
- services/daily_report_card.py
- weekend_review.py
- Architecture
- ButterflyGuy data sources and data types
- Options strategy discovery report
- test_research_mechanism.py
- 9) Capture equity candles and Level II for trade review
- Shared SPX candidate fleet
- daily_report_card_format.py
- test_candidate_dashboards.py
- replay.py
- mechanism.py
- 2026-07-14 — data audit and research design
- Re-authorization checklist — Saturday 2026-08-15
- DiscordNotifier
- Capability recorder design
- report_exit_mark_parity.py
- pytest
- 2026-09-20 — SPX cash-settlement parity correction
- SimulationEngine
- generate_live_performance.py
- performance_chart.py
- Window F — the refresh token re-authorized, six days early (2026-08-08)
- EventCalendar
- Window D — the gateway made reachable, started, and watched (2026-08-08)
- Re-authorization checklist — Saturday 2026-08-22
- thetadata_download.py
- AGENTS.md
- test_research_quality.py
- date
- run_trials.py
- Butterfly Guy
- launch_schwab_gateway_readiness_soak_20260909.sh
- report_trade_ladders.py
- ThetaDataSource
- parse_args
- Schwab gateway deployment options
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- GatewayAuthoritativeMarketDataProvider
- test_research_thetadata.py
- fly_settlement_value
- strategy_page.py
- Schwab gateway current status
- test_gateway_compose.py
- Schwab Gateway Foundation Smoke Test
- Schwab Single-Token Manager
- ShadowComparingMarketDataProvider
- Strategy Settings
- LocalThetaDataSource
- run_all_history.py
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- Registration decision package: ThetaData development window (2026-09-29)
- test_daily_report_card.py
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Width Selection
- ThetaData durable backtesting execution — 2026-10-01
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- Schwab Gateway Multi-Consumer Foundation
- CsvDataLoader
- RunContext
- Helios PAPER gateway cutover — 2026-08-25
- source_hashes
- spx-prospective-2026-09-22/manifest.json
- Ranked hypotheses
- diagnose.py
- launch_schwab_gateway_session_soak_20260901.sh
- Bounded proof failure codes and a settled restoration error window — 2026-08-06
- Credential proof passed — 2026-08-06
- Schwab Gateway Foundation: Local Run
- strategy.js
- f2_shadow_report.py
- test_run_backtest_db.py
- get_time_regime
- spx-prospective-v2-2026-10-02/manifest.json
- ThetaData data-quality plan and validation amendment (2026-09-28)
- _MetricsHandler
- butterfly mark
- Preflight stops on the host-executed release — 2026-08-06
- test_gateway_token_manager.py
- Option A deployment runbook — Helios, containerized
- Host-executed proof step
- First token read, and a read-only container filesystem — 2026-08-06
- Operator-named absolute token path
- Live Runbook
- schwab-gateway-phase-7-execution-prompt.md
- config.py
- gateway-paper-cutover-handoff-prompt.md
- 2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)
- Prospective execution validation — spx-prospective-2026-09-22
- .status
- Layered Risk Management
- Geometric butterfly icon
- Reducing the weekly re-authorization cost — a scoping question
- Current Schwab Integration
- Options strategy discovery journal
- 2026-09-21 — prospective execution-validation cohort (pre-registration)
- mini_spx/manifest.json
- decision_rules
- test_gateway_ownership_boundaries.py
- 3) Start the SPX stack in Docker
- run_live.py
- write_history
- Implementation prompt: finish local ThetaData backtesting support
- SchwabGateway option-chain latency investigation (2026-09-04)
- 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)
- Prospective execution validation — spx-prospective-v2-2026-10-02
- MinuteBar
- FailingDirectProvider
- session_date
- record_equity_market_data.py
- test_research_fidelity.py
- test_research_protocol.py
- select_pm_settled_rows
- OptionQuote
- 2026-09-21 — SPX executable-side accounting on the settlement-correct replay
- ButterflyCandidate
- numpy
- profit_policy.py
- quote_rules
- test_comparison_stats.py
- files
- prospective_execution.py
- dev_studies.py
- Historical data management
- test_run_migrations.py
- Offline ThetaData research
- run_live_performance_cron.sh
- decision_rules
- Compare Real vs Synthetic Chains
- 1. Charles Schwab API
- Cohort automation
- assumptions
- test_run_live.py
- _run_with_stub_token
- endpoint
- SchwabGateway order-book release full-session acceptance — 2026-09-01
- export
- Trade
- Dataset
- parse_quotes
- download_schwab_cache.py
- SPX idea sweep — registry (written 2026-09-25 before any variant was run)
- equity_market_data.py
- main
- test_gateway_minute_backfill.py
- entry_pricing.py
- fill_models
- Equity candles and order-book recording
- test_collector.py
- 2. Other external and public sources
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
- ThetaData backtesting readiness and completion plan
- sessions/2026-06-12/clock.parquet
- sessions/2026-07-13/clock.parquet
- SPX prospective execution validation v2 registration
- sessions.parquet
- GatewayMarketDataError
- Window C — the two token writers resolved (2026-08-08)
- report_broker_order_statuses.py
- docs/README.md
- SPX paper-trade review — September 12, 2026
- JsonlStreamRecorder
- test_research_hypotheses.py
- Registration decision package — 2026-09 (for the owner; nothing is registered)
- cohort_daily_update.sh
- test_research_accounting.py
- test_equity_market_data.py
- exit_trials/PLAN.md
- test_realized_vs_implied.py
- test_market_data_providers.py
- All 108 historical entries: executed exit experiments
- manifest.json
- Reproduce the SPX exit-policy experiment
- butterfly-guy
- Ernie (@0DTE) comparison — variant plan (not run)
- 5. Local files and backtest inputs
- SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- DirectSchwabMarketDataProvider
- 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)
- Modules
- block_bootstrap_indices
- 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)
- Documentation map
- quote_rules
- ButterflyOrderBuilder
- 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)
- assumptions
- Prospective cohort validation, version 2
- endpoint
- Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)
- Research core
- run_gateway_minute_backfill.sh
- math
- test_research_tieset.py
- H-TR1 registration — trail armed at +75% with a breakeven floor
- OrderManager
- send_realized_vs_implied.py
- 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)
- AlertmanagerNotifier
- 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)
- 2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)
- Implementation prompt: SPX session quality and exclusion ledger
- backfill_equity_candles.py
- 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0
- HistorySource
- run
- gateway_minute_backfill.py
- ThetaData option history (raw)
- DockerExecSource
- test_collector_daily_bars.py
- database
- Market
- 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- select_strike_contract
- 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data)
- 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered)
- test_discover_options_strategy.py
- 2026-10-02 — edge search: hold to settlement with a VIX floor (development + validation; nothing registered)
- Critical External-Alert Delivery Proof - 2026-07-15
- csv
- XSP Flat-Runtime Restart Proof - 2026-07-14
- fill_models
- lock_events
- research_gateway_vol_dump.py
- run_schwab_fidelity_daily.sh
- spot_ticks.parquet
- test_direct_result_is_unchanged_when_the_gateway_times_out_in_real_time
- test_get_option_chain_returns_before_a_slow_gateway_responds
- describe
- test_discrepancy_metric_labels_cover_every_declared_code
- _reset_readiness_after_provider_test

## God Nodes (most connected - your core abstractions)
1. `Dataset` - 119 edges
2. `ButterflyCandidate` - 104 edges
3. `RunContext` - 96 edges
4. `OptionQuote` - 94 edges
5. `SchwabClientWrapper` - 93 edges
6. `AppConfig` - 83 edges
7. `Session` - 64 edges
8. `MinuteBar` - 63 edges
9. `et_us()` - 63 edges
10. `PositionService` - 60 edges

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

## Communities (412 total, 120 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.10
Nodes (28): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close() (+20 more)

### Community 1 - "session_ledger.py"
Cohesion: 0.16
Nodes (9): build(), canonical(), cmd_ledger(), Evidence, gate_status(), indexed(), publish(), reconcile() (+1 more)

### Community 2 - "time_utils.py"
Cohesion: 0.07
Nodes (39): _easter_sunday(), get_0dte_expiration(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_premarket_window(), is_trading_day(), _last_weekday() (+31 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.12
Nodes (62): LiveSpread, broker_fill(), _exit_limits_for_bids(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+54 more)

### Community 4 - "schwab_gateway_v046_readiness_soak.py"
Cohesion: 0.12
Nodes (30): append_jsonl(), bounded_request(), candidate_observation(), diagnostic_probe(), docker_inspect(), endpoint_snapshot(), finalize(), flatness() (+22 more)

### Community 5 - "cli.py"
Cohesion: 0.07
Nodes (51): build_parser(), evaluation_args(), _calibrate_for_registration(), cmd_calibrate(), cmd_catalog(), cmd_coverage(), cmd_diagnose(), cmd_exclude_sessions() (+43 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.10
Nodes (26): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+18 more)

### Community 7 - "butterfly_gateway_acceptance.py"
Cohesion: 0.13
Nodes (14): _endpoints(), test_identity_checks_paper_gateway_and_no_shadow_invariants(), test_preopen_accepts_retried_market_data_unavailable(), test_preopen_allows_documented_after_hours_strategy_readiness(), test_preopen_never_suppresses_other_endpoint_failures(), test_preopen_rejects_every_other_readiness_failure(), endpoint_violations(), http_json() (+6 more)

### Community 8 - "simulate.py"
Cohesion: 0.06
Nodes (21): Costs, AbsoluteLossStop, config_exit_rules(), ExitDecision, ExitRule, monitor(), MonitorState, PreCloseExit (+13 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.37
Nodes (17): atm_pair(), butterfly(), closest_delta(), credit_spread(), entry_cost(), exit_value(), iron_condor(), iron_fly() (+9 more)

### Community 10 - "test_research_local.py"
Cohesion: 0.16
Nodes (22): Record a future BMNR session, normalize(), OneFly, raw(), source(), test_a_spent_holdout_session_imports_and_is_counted(), test_alternate_instrument_identity_and_fractional_grid(), test_alternate_instrument_replay_with_attributable_inputs() (+14 more)

### Community 11 - "test_gateway_shadow_reads.py"
Cohesion: 0.10
Nodes (28): chain_response(), _comparisons(), DirectProvider, _discrepancies(), RecordingGateway, spot_response(), test_a_direct_payload_that_cannot_be_summarized_is_a_parsing_discrepancy(), test_a_disabled_shadow_records_no_metrics_at_all() (+20 more)

### Community 12 - "2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)"
Cohesion: 0.29
Nodes (7): 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data), Built (provider-independent, tested on synthetic data), Development coverage and in-sample E0, Housekeeping, Hypothesis rules (implemented, not registered), Validation results (readiness doc steps 1–4), What this means for the evidence plan

### Community 13 - "evaluate.py"
Cohesion: 0.07
Nodes (30): Fill, TradeFills, render(), common_dates(), EvalParams, evaluate(), evaluate_arm(), paired_bootstrap() (+22 more)

### Community 14 - "StrategySettings"
Cohesion: 0.11
Nodes (26): StrategySettings, selector_pool(), main(), parse_args(), print_help(), ButterflyBuilder, vix_target_center(), determine_direction() (+18 more)

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
Cohesion: 0.13
Nodes (14): _blocks(), calibrate_gate1(), check_fitted(), check_registered(), check_rerun(), prior_holdout_runs(), ProtocolError, registrations() (+6 more)

### Community 19 - "schwab_gateway_session_soak.py"
Cohesion: 0.13
Nodes (30): adjudicate_transient_non_200(), assert_production_identity(), background_context(), _confirm_surfaces(), _filtered_gateway_logs(), _finite(), _gateway_error_code(), _health() (+22 more)

### Community 20 - "Manifest"
Cohesion: 0.06
Nodes (36): Volatility term structure, default_cache_root(), Manifest, DailyVol, IntradayVol, exclude_sessions(), daily_table(), export_daily() (+28 more)

### Community 21 - "SyntheticChainGenerator"
Cohesion: 0.12
Nodes (9): IVModel, SyntheticChainGenerator, make_snapshot_time(), test_atm_call_price_reasonable(), test_generate_chain_has_both_types(), test_generate_chain_strike_count(), test_otm_put_iv_higher_than_otm_call(), test_price_decreases_as_dte_shrinks() (+1 more)

### Community 23 - "export.py"
Cohesion: 0.08
Nodes (29): `DataSource` adapter spec, What is wrong today (verified 2026-10-04 by reading the code), dense_chain_from_rows(), bars_changes(), _bars_key(), chain_sql(), clock_sql(), daily_bars_sql() (+21 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.16
Nodes (24): AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, count_rejected_orders(), detect_problems(), _extract_order_id(), _extract_trade_leg() (+16 more)

### Community 25 - "TradeQueries"
Cohesion: 0.05
Nodes (8): Collector, H3 — The exit decision is gated on non-critical DB writes, with no query timeout, M2 — Ambiguity handlers can mask `AmbiguousOrderError` with a DB error, MonitoringLegQueries, OrderIntentQueries, RiskQueries, TradeQueries, ConsecutiveLossNotifier

### Community 26 - "SessionChain"
Cohesion: 0.09
Nodes (25): Baseline (required in PR 1), Build on what exists, Deliver, Part C: daily Schwab-vs-ThetaData fidelity check (PR 1), Tests, SessionChain, _quality(), arbitrage() (+17 more)

### Community 27 - "position_manager.py"
Cohesion: 0.07
Nodes (23): compute_tent_boundaries(), _resolve_iv(), bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega() (+15 more)

### Community 28 - "Registry"
Cohesion: 0.12
Nodes (17): _canonical(), record_hash(), Registry, RegistryError, _append(), test_catalog_fails_on_a_broken_chain(), test_catalog_lists_hashes_registries_and_counts(), test_history_counts_events_for_the_exact_definition() (+9 more)

### Community 29 - "test_chain_parser_parity.py"
Cohesion: 0.12
Nodes (12): _contract(), _parse_rows(), test_a_map_present_but_empty_produces_zero_everywhere(), test_a_non_numeric_strike_key_diverges_and_the_divergence_is_recorded(), test_a_strike_with_an_empty_option_list_is_excluded_by_all_three(), test_all_three_agree_on_which_expiration_matches(), test_calls_present_with_puts_absent_is_handled_identically_by_all_three(), test_contract_counts_equal_the_rows_the_collector_would_write() (+4 more)

### Community 30 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (15): make_risk_engine(), test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed(), test_can_trade_max_loss(), test_can_trade_max_trades(), test_can_trade_ok() (+7 more)

### Community 31 - "run_entry_analysis.py"
Cohesion: 0.15
Nodes (18): fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot(), parse_args() (+10 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.10
Nodes (26): PositionState, ExitSignal, ProfitState, ProfitStateMachine, make_pos(), make_settings(), test_absolute_loss_stop_fires_without_profit_tent(), test_default_drawdown_confirmation_is_immediate() (+18 more)

### Community 33 - "run_backtest_db.py"
Cohesion: 0.06
Nodes (54): Phase 1: one command surface, ChainDay, max_consecutive_losses(), max_drawdown(), profit_factor(), sharpe(), DrawdownWindow, _accounting_comparison_rows() (+46 more)

### Community 35 - "run_prospective_execution.py"
Cohesion: 0.08
Nodes (28): Start-date correction before the first cohort, CohortError, CohortSpec, deferred_runs_path(), load_manifest(), verify_cohort(), backtest_entry_price(), day_with_monitoring_bars() (+20 more)

### Community 36 - "research/shadow.py"
Cohesion: 0.12
Nodes (20): check_records(), CohortLedger, compare_with_cohort(), default_ref(), _git(), _jsonl(), LedgerError, _m() (+12 more)

### Community 38 - "validate.py"
Cohesion: 0.12
Nodes (24): selection_span(), build_helios_clock_dataset(), _compare(), compare_replays(), _dates(), _distribution(), explain(), _first_difference() (+16 more)

### Community 39 - "Codex Project State"
Cohesion: 0.06
Nodes (33): C3 default-off deployment and gateway hardening (2026-08-10), Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z), Codex Project State, Correction 1 — A3 as written cannot work on Helios, Correction 2 — `easy_client` silently no-ops the re-authorization, Current Phase (+25 more)

### Community 40 - "_assert_broker_state_matches_db"
Cohesion: 0.09
Nodes (38): The fix, ActiveMonitor, _assert_broker_state_matches_db(), _explicit_fill_details(), install_shutdown_handler(), _intent_order_ids(), _json_dict(), _open_trade_positions() (+30 more)

### Community 41 - "pathlib"
Cohesion: 0.05
Nodes (33): add_commands(), _artifact(), _clean(), cmd_audit(), cmd_cache_daily(), cmd_cache_inputs(), cmd_import(), cmd_inventory() (+25 more)

### Community 42 - "Schwab Gateway Migration Plan"
Cohesion: 0.10
Nodes (20): Credential-proof gate, Current migration status, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison, Phase 4 — read-only cutover (+12 more)

### Community 43 - "test_research_learning.py"
Cohesion: 0.09
Nodes (24): fit_variant_entry(), is_fitted(), _describe(), fit_variants(), run_variants(), Variant, VariantRun, _ctx() (+16 more)

### Community 44 - "test_gateway_order_book.py"
Cohesion: 0.18
Nodes (10): _recent_payload(), _snapshot(), test_recent_authenticates_and_validates_fresh_contract(), recent(), test_recent_fails_closed_when_gateway_reports_stale_feed(), test_recent_rejects_mismatched_snapshot(), test_stream_authenticates_and_yields_only_requested_contracts(), stream() (+2 more)

### Community 45 - "realized_vs_implied.py"
Cohesion: 0.25
Nodes (8): _fmt(), format_message(), MoveSummary, SessionMove, summarize(), _summary_line(), verdict(), main()

### Community 46 - "PositionService"
Cohesion: 0.06
Nodes (44): M10 — Live settlement wait has no bound, and post-close failures surface late, readiness_snapshot(), set_readiness(), TradeRecord, _expired_trade_has_broker_settlement(), broker_cash_settlement_from_transactions(), BrokerCashSettlement, _chain_spot_price() (+36 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.15
Nodes (25): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+17 more)

### Community 48 - "DayData"
Cohesion: 0.08
Nodes (29): 6. Canonical and derived analytical data types, Synthetic option-chain data, DayData, _entry_debit(), _exit_credit(), _finite_quote_side(), inspect_quote_market(), price_frozen_trade() (+21 more)

### Community 49 - "source_hashes"
Cohesion: 0.05
Nodes (40): source_hashes, pyproject.toml, src/butterfly_guy/backtest/chain_cache.py, src/butterfly_guy/backtest/data_loader.py, src/butterfly_guy/backtest/db_loader.py, src/butterfly_guy/backtest/execution_accounting.py, src/butterfly_guy/backtest/__init__.py, src/butterfly_guy/backtest/metrics.py (+32 more)

### Community 50 - "fidelity.py"
Cohesion: 0.07
Nodes (23): Accumulator, Agreement, _bucket(), _canonical(), compare_session(), fly_widths(), FlyStats, _fmt() (+15 more)

### Community 51 - "live_performance.py"
Cohesion: 0.09
Nodes (36): chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes(), equity_chart_description() (+28 more)

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
Cohesion: 0.08
Nodes (26): main(), load_config(), main(), parse_args(), run(), _regimes(), test_allow_live_trading_requires_explicit_env(), test_checked_in_configs_keep_default_regime_bounds() (+18 more)

### Community 56 - "strategy_parameters"
Cohesion: 0.07
Nodes (30): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+22 more)

### Community 57 - "chain_cache.py"
Cohesion: 0.19
Nodes (14): chain_cache_path(), chain_journal_path(), load_chain_day(), nearest_snapshot(), _read_snapshots(), save_snapshot(), test_chain_cache_path_is_partitioned_by_underlying(), test_load_chain_day_falls_back_to_partitioned_spx_cache() (+6 more)

### Community 58 - "test_research_parity.py"
Cohesion: 0.12
Nodes (11): _cache(), _quiet(), _run(), test_full_frozen_replay_parity(), test_mini_fixture_matches_the_frozen_replay_trade_by_trade(), test_mini_fixture_reproduces_the_idea_sweep_harness(), _published(), _row() (+3 more)

### Community 59 - "test_position_monitoring.py"
Cohesion: 0.21
Nodes (8): _candidate(), _gateway_contract(), _quotes(), _service(), test_intermittent_missing_held_leg_degrades_then_recovers_without_broker_write(), get_option_chain(), test_trade_282_uses_gateway_held_leg_when_contract_is_not_stale(), _trade_282_candidate()

### Community 60 - "run_classifier_sweep.py"
Cohesion: 0.21
Nodes (7): win_pct(), main(), parse_args(), print_table(), summarize_adaptive(), summarize_baseline(), RegimeClassifier

### Community 61 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.10
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 62 - "Regime"
Cohesion: 0.11
Nodes (12): classify_market_regime(), daily_reset_loop(), GapRegimeFilter, Regime, TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct, TestSkipBeforeOverride (+4 more)

### Community 63 - "Fly"
Cohesion: 0.22
Nodes (3): Fly, ev_entry_factory(), fn()

### Community 64 - "SchwabClientWrapper"
Cohesion: 0.08
Nodes (4): The alternative worth costing first, The brief's proposed remedy, and why it is weaker than it looks, Option A Live Serving (built offline, never deployed), SchwabClientWrapper

### Community 65 - "AppConfig"
Cohesion: 0.10
Nodes (38): AppConfig, EntrySettings, ExecutionSettings, RiskSettings, _assert_live_config_supported(), _session_open_from_intraday_candles(), entry_strategy_snapshot(), _quote() (+30 more)

### Community 69 - "datetime"
Cohesion: 0.12
Nodes (23): baseline_entry(), bucket(), main(), main(), bs_gamma(), gex_levels(), main(), round_levels() (+15 more)

### Community 70 - "exit_trials/manifest.json"
Cohesion: 0.07
Nodes (27): account_sharpe, baseline_parity, command, created_utc, display_timezone, environment_variables, exit_commission_points, git_sha (+19 more)

### Community 71 - "test_prospective_execution.py"
Cohesion: 0.13
Nodes (47): daily_runs_path(), read_jsonl(), summarize_cohort(), trades_path(), current_summary(), _baseline(), _candidate(), _cohort() (+39 more)

### Community 72 - "test_f2_shadow_report.py"
Cohesion: 0.19
Nodes (18): row(), summary(), test_all_winning_sample_passes_profit_factor_gate(), test_cash_settlement_equals_cohort_under_every_model(), test_chronological_order_controls_drawdown_and_stop(), test_drawdown_exactly_at_limit_does_not_stop(), test_drawdown_stop_does_not_include_subsequent_recovery(), test_endpoint_uses_first_complete_sample_only() (+10 more)

### Community 73 - "build_market_events.py"
Cohesion: 0.17
Nodes (18): bea_releases(), bls_releases(), capture_date(), Fetcher, fomc_rows(), hhmm(), main(), market_rows() (+10 more)

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 75 - "SessionLoader"
Cohesion: 0.07
Nodes (7): DecisionProfile, round_to_seconds(), Series, SessionLoader, DayMarket, restrict_view(), _et_to_utc_us()

### Community 76 - "Branch Review and Integration Plan"
Cohesion: 0.09
Nodes (21): Branch Review and Integration Plan, Consolidated Validated Findings, Decision and Findings Log, Delegated Workstreams, Final Integration Gates, Frozen Starting Snapshot, High — open blockers, Initial Verification Baseline (+13 more)

### Community 77 - "test_order_preview.py"
Cohesion: 0.27
Nodes (6): make_spx_candidate(), test_close_order_credit(), test_order_has_required_schwab_fields(), test_order_leg_has_required_fields(), test_order_session_and_duration(), test_price_format_is_string()

### Community 78 - "all_history_trials/manifest.json"
Cohesion: 0.05
Nodes (39): account_return_sharpe_marked_drawdown, baseline_scenario_regressions, command, created_utc, dependency_lock_sha256, environment_variables, git_sha, input_hashes (+31 more)

### Community 79 - "test_schwab_client.py"
Cohesion: 0.11
Nodes (31): SchwabSettings, _accessors(), factory(), _account_client(), _http_response(), no_sleep(), _reload_harness(), _schwab_returning() (+23 more)

### Community 80 - "strategy_parameters"
Cohesion: 0.06
Nodes (31): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+23 more)

### Community 81 - "services/daily_report_card.py"
Cohesion: 0.12
Nodes (14): PriceHistoryProvider, DailyReportCardSettings, load_daily_report_card_config(), ReportCardThresholds, archive_report(), build_report_messages(), _format_problems(), chartable_equity_trades() (+6 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.08
Nodes (43): trade_point_from_row(), build_combined_performance_chart_png(), build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_executable_pnl() (+35 more)

### Community 83 - "Architecture"
Cohesion: 0.10
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "ButterflyGuy data sources and data types"
Cohesion: 0.10
Nodes (21): 10. Repository evidence map, 3.10 `broker_order_intents`, 3.1 `option_chain_snapshots`, 3.2 `spot_prices`, 3.3 `butterfly_candidates`, 3.4 `butterfly_trades`, 3.5 `decision_log`, 3.6 `daily_risk_state` (+13 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "test_research_mechanism.py"
Cohesion: 0.18
Nodes (10): _inputs(), _sessions(), _synthetic(), test_decision_rule_on_planted_and_null_effects(), test_first_session_uses_the_prior_development_session(), test_prior_values_come_from_the_previous_spx_session(), test_rows_outside_the_window_are_dropped_before_computing(), test_session_without_a_prior_vix1d_is_excluded() (+2 more)

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
Cohesion: 0.32
Nodes (11): _dashboard(), _expressions(), _panels(), visit(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_retired_experimental_runtime_is_absent_from_dashboards(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_uses_selected_trade_monitoring_as_candidate_spot_fallback() (+3 more)

### Community 92 - "replay.py"
Cohesion: 0.23
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

### Community 96 - "DiscordNotifier"
Cohesion: 0.10
Nodes (12): Baseline, Butterfly Guy Code Review — 2026-09-25, Executive summary, Findings index, H1 — Public repository with a self-hosted runner that reaches production, H2 — Previous close silently falls back to the current spot price, High, Low / Info (+4 more)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (11): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+3 more)

### Community 99 - "pytest"
Cohesion: 0.09
Nodes (12): test_auth_init_honours_schwab_token_path(), test_alertmanager_failed_resolution_retries_until_accepted(), send_alertmanager(), to_thread(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_alertmanager_payload_has_stable_redacted_fingerprint(), test_notify_entry_includes_trade_stats(), capture() (+4 more)

### Community 101 - "2026-09-20 — SPX cash-settlement parity correction"
Cohesion: 0.50
Nodes (4): 2026-09-20 — SPX cash-settlement parity correction, Evidence, assumptions, and exclusions, Exact commands and implementation fingerprints, Frozen result

### Community 102 - "SimulationEngine"
Cohesion: 0.07
Nodes (25): Accounting and evaluation, Entry-point inventory and fate, Open owner decisions, Phase 0: land what exists, Phase 2: one exit kernel, Phase 3: commit the analysis that decisions rest on, Phase 5: data upkeep, Phases (+17 more)

### Community 103 - "generate_live_performance.py"
Cohesion: 0.18
Nodes (12): no_trade_reason(), best_trade(), reference_spot(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate(), main() (+4 more)

### Community 104 - "performance_chart.py"
Cohesion: 0.15
Nodes (13): compute_stats(), ReportStats, build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels(), _setup_axes() (+5 more)

### Community 105 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.12
Nodes (14): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Stale-lineage persistence guard deployed (2026-08-10T20:00:48Z), Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08) (+6 more)

### Community 107 - "EventCalendar"
Cohesion: 0.10
Nodes (16): _date(), EventCalendar, MarketEvent, parse_row(), _row(), test_committed_calendar_has_a_scheduled_event_of_each_type_every_year(), test_committed_calendar_loads_and_covers_the_range(), test_event_published_on_or_after_the_session_is_invisible_to_it() (+8 more)

### Community 109 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 110 - "Re-authorization checklist — Saturday 2026-08-22"
Cohesion: 0.18
Nodes (10): Preconditions — verified 2026-08-22T15:45:36Z, Re-authorization checklist — Saturday 2026-08-22, Step 1 — mint on zeus, in a real terminal, Step 2 — stage on Helios, verify byte-identical, Step 3 — move into place under the C1 lock, Step 4 — watch the reloads; restart only on a *confirmed* failure, Step 5 — verify, host against containers, Step 6 — record (+2 more)

### Community 111 - "thetadata_download.py"
Cohesion: 0.08
Nodes (19): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), run_check_cycle(), send_discord_alert(), signal_handler() (+11 more)

### Community 112 - "AGENTS.md"
Cohesion: 0.12
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 114 - "test_research_quality.py"
Cohesion: 0.16
Nodes (10): quality_passed(), _cboe(), _day(), test_a_clean_day_passes_every_gate(), test_a_quality_run_never_reads_the_holdout(), test_coverage_crossed_stale_and_timestamp_failures_are_caught(), test_only_a_full_window_pass_opens_earlier_pulls(), test_q5_is_not_evaluable_without_exact_minute_spx_prints() (+2 more)

### Community 115 - "date"
Cohesion: 0.06
Nodes (21): _age_fields(), build_session(), BuiltSession, carry_quotes(), GuardedSource, has_print(), index_on_grid(), _merge() (+13 more)

### Community 116 - "run_trials.py"
Cohesion: 0.14
Nodes (25): bootstrap_mean_delta(), compare(), ConfirmedMachine, main(), replay(), sha(), stats(), variants() (+17 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "launch_schwab_gateway_readiness_soak_20260909.sh"
Cohesion: 0.20
Nodes (10): die(), EVIDENCE_DIR, LAUNCHER, LOG, MONITOR, SESSION_DATE, launch_schwab_gateway_readiness_soak_20260909.sh script, TARGET_EPOCH (+2 more)

### Community 121 - "report_trade_ladders.py"
Cohesion: 0.18
Nodes (10): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+2 more)

### Community 122 - "ThetaDataSource"
Cohesion: 0.14
Nodes (7): load_minute_file(), parse_cboe(), ThetaDataSource, _ymd(), test_minute_file_is_central_time_bar_end_and_stale_days_are_dropped(), test_source_satisfies_the_history_source_interface(), test_thetadata_is_registered_and_needs_the_minute_files()

### Community 123 - "parse_args"
Cohesion: 0.09
Nodes (24): _asset_drawdowns(), candidate_from_trade_row(), _floatlist(), _intlist(), parse_args(), _parse_config_time(), select_direction_bar(), _sim_parity_fields() (+16 more)

### Community 124 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 125 - "Window H — verification held; the deadline reminder is mistimed (2026-08-08)"
Cohesion: 0.22
Nodes (9): Deliverables, Finding — the weekly reminder fires after the deadline it protects, Still open after Window H, Task 2 — the Monday check is deferred a fourth time, Tasks 3–6 — all green, verified host-against-container, The deadline in local time — stated because the brief did not, The deadline, re-derived from the document, Window H addendum — a keepalive write observed live (2026-08-09 01:00 UTC) (+1 more)

### Community 127 - "test_research_thetadata.py"
Cohesion: 0.17
Nodes (16): _cboe(), _day_quotes(), Recorded, _source(), Terminal, test_a_holdout_pull_stops_before_any_terminal_request(), test_after_the_files_end_spx_and_vix_come_from_the_recorded_dataset(), test_daily_bars_take_the_official_close_from_cboe_and_the_open_from_the_file() (+8 more)

### Community 128 - "fly_settlement_value"
Cohesion: 0.10
Nodes (15): Assumptions, Corrected implementation fingerprints, Reproduction commands, Result, Settlement evidence and reconciliation, SPX frozen baseline: cash-settlement correction, fly_settlement_value(), PositionQuotesUnavailableError (+7 more)

### Community 129 - "strategy_page.py"
Cohesion: 0.11
Nodes (22): _json_data_block(), _case_study(), _clock(), _entry_window_et(), _et_after_open(), _minutes_between(), _pct(), _regime_bar() (+14 more)

### Community 130 - "Schwab gateway current status"
Cohesion: 0.25
Nodes (6): Current state, Deferred Helios cleanup, Historical record, Runtime boundaries, Schwab gateway current status, Archived Schwab gateway transition records

### Community 131 - "test_gateway_compose.py"
Cohesion: 0.18
Nodes (3): test_default_compose_binds_the_token_directory_never_the_document(), test_default_compose_token_binds_require_the_shared_token_directory(), test_live_configs_leave_token_path_to_the_environment()

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

### Community 137 - "run_all_history.py"
Cohesion: 0.21
Nodes (13): all_stresses(), assert_prior_result(), ledger_parity(), main(), paired_comparison(), select_sources(), points(), test_all_scenarios_equal_original_replays() (+5 more)

### Community 138 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.12
Nodes (9): Corrections to the Window G brief, End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08), ShadowDiscrepancy (+1 more)

### Community 139 - "Registration decision package: ThetaData development window (2026-09-29)"
Cohesion: 0.11
Nodes (18): 1. Data and integrity, 2. Baseline E0 (descriptive; do not tune on it), 3. The hypotheses on the development window (in-sample), 4. Holdout size and power, 5. VIX-smoothing sensitivity, 6.1 Stressed exits below zero: decided, now floored (D3, draft Revision 1), 6.2 Gate 1 passed skip filters too often under the null: decided, now calibrated (D4, draft Revision 4), 6.3 A paired pass against a losing baseline: decided, gate 6 added (D2, draft Revision 5) (+10 more)

### Community 141 - "test_daily_report_card.py"
Cohesion: 0.13
Nodes (15): _match_round_trips_fifo(), parse_trade_transactions(), rank_trades(), candles_to_series(), test_build_equity_trade_chart_png_returns_png_bytes(), test_chartable_equity_trades_skips_options(), test_equity_chart_aggregates_to_two_minute_candles(), test_equity_chart_stats_text_includes_key_fields() (+7 more)

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

### Community 149 - "CsvDataLoader"
Cohesion: 0.14
Nodes (10): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs, CsvDataLoader, test_csv_loader_reads_chicago_bar_end_timestamps(), test_csv_loader_rejects_a_day_without_prior_inputs() (+2 more)

### Community 150 - "RunContext"
Cohesion: 0.05
Nodes (45): What the definition hash covers, Hypothesis rules (implemented, not registered), Rules that learn, ATMEntry, baseline_window(), BaselineEntry, BothSides, cached_entries() (+37 more)

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

### Community 155 - "diagnose.py"
Cohesion: 0.24
Nodes (12): breakdowns(), cell(), coverage(), _half(), markdown(), _money(), _r(), session_rows() (+4 more)

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
Cohesion: 0.23
Nodes (9): _candidate(), check_previous(), completed_sample(), input_hashes(), load_cohort(), main(), score(), _stats() (+1 more)

### Community 162 - "test_run_backtest_db.py"
Cohesion: 0.08
Nodes (19): fetch_prev_close(), _fitted_density_counts(), _print_pnl_histogram(), resolve_db_dsn(), _DailyBarConnection, test_entry_window_direction_ma_uses_sma_of_prior_closes(), test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), fake_vix() (+11 more)

### Community 163 - "get_time_regime"
Cohesion: 0.11
Nodes (15): M7 — Regime names are unvalidated and regime time bounds are ignored, 1. The prospective cohort's daily update was failing (P0), 2. Statistical power (P0 for research planning), 3.1 Consolidate the simulators, 3.2 Sweeps rank on the wrong accounting and the wrong metric, 3. Research infrastructure (P1), 4. Data and features known before entry (P1), 5. Live/backtest parity (P2) (+7 more)

### Community 165 - "spx-prospective-v2-2026-10-02/manifest.json"
Cohesion: 0.12
Nodes (15): asset, cohort_id, config, path, sha256, created_at, database_tables, git (+7 more)

### Community 166 - "ThetaData data-quality plan and validation amendment (2026-09-28)"
Cohesion: 0.06
Nodes (33): After Parts A and B, Headline numbers, How approximate this is, Run, Schwab recording fidelity baseline (2026-10-04), Behavior, Check the impact on live reads, Goal (+25 more)

### Community 168 - "butterfly mark"
Cohesion: 0.20
Nodes (7): BUTTERFLYGUY, butterfly mark, central cyan glow, cyan-to-purple neon palette, dark navy background, node-and-line network geometry, uppercase geometric wordmark style

### Community 169 - "Preflight stops on the host-executed release — 2026-08-06"
Cohesion: 0.67
Nodes (3): Credential exposure during the window, Preflight stops on the host-executed release — 2026-08-06, Release

### Community 170 - "test_gateway_token_manager.py"
Cohesion: 0.14
Nodes (26): increment_callback(), manager(), _process_refresh(), delayed_increment(), test_callback_failure_preserves_original_and_redacts_error_and_logs(), test_concurrent_managers_serialize_the_entire_refresh_callback(), first_refresh(), second_refresh() (+18 more)

### Community 171 - "Option A deployment runbook — Helios, containerized"
Cohesion: 0.13
Nodes (13): 1. The internal keys file — Phase 3 dependency 4, 2. The token directory, 3. Credentials, Known limitations — accept or fix before a real shadow period, Option A deployment runbook — Helios, containerized, Preflight — read-only, no mutation, Prerequisites, Recorded preflight — 2026-08-06, read-only (+5 more)

### Community 172 - "Host-executed proof step"
Cohesion: 0.67
Nodes (3): Host-executed proof step, Release, Workflow consequence the next window must plan for

### Community 175 - "Live Runbook"
Cohesion: 0.25
Nodes (7): During Session, Live Runbook, Manual Flatten, Rollback, Startup, Token Recovery, XSP Canary

### Community 177 - "config.py"
Cohesion: 0.13
Nodes (13): main(), CollectorSettings, ConfigModel, DatabaseSettings, MonitoringSettings, PeakTrackingSettings, ProfitManagementSettings, QuoteQualitySettings (+5 more)

### Community 179 - "2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)"
Cohesion: 0.20
Nodes (9): What the research core needs, 2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only), Descriptive E0 breakdowns (not evidence), Feature sources and coverage, Housekeeping, Pre-registration draft (not registered), Vendor readiness, markdown_section() (+1 more)

### Community 180 - "Prospective execution validation — spx-prospective-2026-09-22"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-2026-09-22, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 182 - "Layered Risk Management"
Cohesion: 0.22
Nodes (8): Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy, XSP Account and Loss Guards

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (6): BUTTERFLYGUY, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 184 - "Reducing the weekly re-authorization cost — a scoping question"
Cohesion: 0.18
Nodes (10): Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Production marker-change proof (2026-08-10), Recommendation, Reducing the weekly re-authorization cost — a scoping question, Stale-writer follow-up (2026-08-10), Status, The cost being attacked (+2 more)

### Community 185 - "Current Schwab Integration"
Cohesion: 0.15
Nodes (12): Assumptions requiring verification, Authentication and token lifecycle, Configuration, secrets, and deployment assumptions, Current Schwab Integration, Database and messaging dependencies, Discord and operational dependencies, Equity and research paths, Extraction boundaries (+4 more)

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
Nodes (4): _source(), test_compose_keeps_each_strategy_default_direct_with_staged_gateway_opt_in(), test_shadow_failure_is_observed_without_changing_the_direct_result(), test_standalone_packages_remain_pinned_and_consumers_import_them_directly()

### Community 191 - "3) Start the SPX stack in Docker"
Cohesion: 0.29
Nodes (7): 3) Start the SPX stack in Docker, code:bash (docker compose -f infra/docker-compose.yml up -d), code:bash (docker compose -f infra/docker-compose.yml --profile ndx --p), code:bash (docker logs --tail 100 butterfly_spx_app), Inspecting Historical Entries, 📊 Research and Inspection, Running a DB Backtest

### Community 192 - "run_live.py"
Cohesion: 0.06
Nodes (14): Interfaces and contracts, get_logger(), clear_readiness(), CollectorMarketDataProvider, EquityQuoteProvider, MarketMoversProvider, OptionChainProvider, SpotPriceProvider (+6 more)

### Community 193 - "write_history"
Cohesion: 0.07
Nodes (39): Fidelity validation (`validate.py`), The adapter (`history.py`), The holdout evaluation (`protocol.py`, `holdout`; D9, built 2026-09-29), The holdout (`holdout.py`), Vendor history (ThetaData, subscribed 2026-09-28), CostNotApprovedError, excluded_sessions(), HistoryPlan (+31 more)

### Community 194 - "Implementation prompt: finish local ThetaData backtesting support"
Cohesion: 0.17
Nodes (11): Completion checklist, Facts and constraints to carry forward, Implementation prompt: finish local ThetaData backtesting support, Objective, Phase 1 — establish the actual remaining work, Phase 3 — supporting observations and coverage policy, Phase 4 — SPXW 0-DTE integration and execution verification, Phase 5 — SPXW 1-DTE (+3 more)

### Community 195 - "SchwabGateway option-chain latency investigation (2026-09-04)"
Cohesion: 0.20
Nodes (9): 2026-09-09 runtime follow-up, Cache TTL is hard-capped at 4s in code, not just config, Chain size correlation, Recommendation, Request path (cache miss), SchwabGateway option-chain latency investigation (2026-09-04), Where the time actually goes: scheduler queueing, not the Schwab call itself, XSP held-leg event-age correction (2026-09-11) (+1 more)

### Community 196 - "2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)"
Cohesion: 0.25
Nodes (8): 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered), Changes, E0 loses on the development window, Findings about the test itself, Hypotheses, paired with E0 (draft bootstrap: 10-session blocks, 10,000 reps), Integrity, Power (from development vectors; assumes 2022–24 is representative), Recommendation for the owner

### Community 197 - "Prospective execution validation — spx-prospective-v2-2026-10-02"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-v2-2026-10-02, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 198 - "MinuteBar"
Cohesion: 0.06
Nodes (9): MinuteBar, BiasScoreFilter, RegimeFilter, make_bar(), make_pre_entry_bars(), TestBiasScore, TestComputeOr, TestComputeVwap (+1 more)

### Community 200 - "session_date"
Cohesion: 0.08
Nodes (15): M11 — A restart with an open trade double-counts the entry cost in daily P&L, M1 — The daily-bar refresh marks itself done after a failure, M3 — Runtime reconciler repair leaves an unmonitored, uncounted trade, M6 — A restart forgets `_ever_in_profit`, suppressing drawdown exits, M8 — Early closes are hard-coded for 2026 only, M9 — The chain cache rewrites the whole day's JSON on the event loop, Medium, session_date() (+7 more)

### Community 201 - "record_equity_market_data.py"
Cohesion: 0.11
Nodes (11): setup_logging(), async_main(), main(), parse_args(), test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings(), main() (+3 more)

### Community 202 - "test_research_fidelity.py"
Cohesion: 0.16
Nodes (12): sealed_holdout(), _chain(), _pair(), _spot(), test_exact_quotes_agree_everywhere(), test_missing_snapshots_and_lateness(), test_missing_strikes_are_counted(), test_one_minute_shift_is_detected() (+4 more)

### Community 203 - "test_research_protocol.py"
Cohesion: 0.23
Nodes (17): _cli(), _gates(), _holdout(), _no_replay(), _pull_holdout(), _records(), test_a_fitted_rule_is_registered_with_its_value_and_checked_at_the_holdout(), test_a_steady_gain_passes_every_gate() (+9 more)

### Community 204 - "select_pm_settled_rows"
Cohesion: 0.22
Nodes (15): select_pm_settled_rows(), _chain(), _row(), _symbols(), test_ambiguous_snapshot_rows_are_dropped(), test_custom_key_fields_group_rows(), test_duplicates_with_no_pm_settled_contract_are_skipped(), test_duplicates_with_two_pm_settled_contracts_are_skipped() (+7 more)

### Community 205 - "OptionQuote"
Cohesion: 0.08
Nodes (17): Models and SDK coupling, _as_float(), _as_int(), rows_to_option_quotes(), fly_mark_value(), OptionQuote, fly_bid_value(), _max_leg_spread_to_mark_ratio() (+9 more)

### Community 206 - "2026-09-21 — SPX executable-side accounting on the settlement-correct replay"
Cohesion: 0.29
Nodes (7): 2026-09-21 — SPX executable-side accounting on the settlement-correct replay, Accounting models and deterministic data rules, Data provenance and coverage, Exact commands and implementation fingerprints, Frozen result, Pre-registered drawdown limit, Reproduction under the roll-forward exit rule

### Community 207 - "ButterflyCandidate"
Cohesion: 0.07
Nodes (25): P — strike placement, 3.3 Make fly-choice robustness a standard output, ButterflyCandidate, ButterflySelector, _active_widths_and_sigmas(), EntrySelectionResult, build_entry_selection_parity(), _candidate_payload() (+17 more)

### Community 208 - "numpy"
Cohesion: 0.09
Nodes (23): open_spot(), directions(), ema(), hma_series(), hourly_closes_before(), hull_rising(), wma(), fn() (+15 more)

### Community 209 - "profit_policy.py"
Cohesion: 0.13
Nodes (8): ProfitProtectorSettings, effective_drawdown_threshold(), ProfitPolicyDecision, profitprotector_floor_decision(), Observation, _protector_settings(), _regime_bounds(), _threshold_regime()

### Community 210 - "quote_rules"
Cohesion: 0.29
Nodes (7): quote_rules, crossed_market, entry_gap, exit_gap, missing_market, selection, substitution

### Community 211 - "test_comparison_stats.py"
Cohesion: 0.57
Nodes (5): _capture(), _make_result(), test_no_trade_days_handled(), test_perfect_correlation(), test_stats_block_present()

### Community 212 - "files"
Cohesion: 0.29
Nodes (7): rows, sha256, files, daily_bars.parquet, sessions/2026-07-13/chain.parquet, rows, sha256

### Community 213 - "prospective_execution.py"
Cohesion: 0.06
Nodes (40): Shadow on the open cohort, Phase 4: link the stages, ExecutableTrade, append_jsonl(), append_unique(), _breakdown(), build_daily_run_record(), build_manifest() (+32 more)

### Community 214 - "dev_studies.py"
Cohesion: 0.26
Nodes (6): cmd_calibrate(), cmd_check(), cmd_power(), cmd_random_skip(), load(), main()

### Community 215 - "Historical data management"
Cohesion: 0.22
Nodes (9): Canonical normalized datasets, Current inventory, Historical data management, Next milestones, Refresh and verify, Session quality and exclusion ledger, Sources and ownership, Storage and cleaning conventions (+1 more)

### Community 216 - "test_run_migrations.py"
Cohesion: 0.27
Nodes (4): fake_db(), FakeConnection, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 217 - "Offline ThetaData research"
Cohesion: 0.20
Nodes (8): Baseline and exposure, Commands, Lifecycles, accounting and limits, Mapping and access, Offline ThetaData research, Verification artifacts, Real private artifacts, ThetaData local implementation verification

### Community 220 - "decision_rules"
Cohesion: 0.22
Nodes (9): decision_rules, checkpoint_trades, early_failure_trades, max_drawdown, max_top3_gross_profit_share, min_executable_entry_coverage, min_profit_factor, primary_hypothesis (+1 more)

### Community 222 - "1. Charles Schwab API"
Cohesion: 0.20
Nodes (10): 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions, 1.8 Orders and order status (+2 more)

### Community 223 - "Cohort automation"
Cohesion: 0.29
Nodes (6): Check on it, Cohort automation, Install, Known limitation: the SSH key, Retired v1, When the cohort closes

### Community 224 - "assumptions"
Cohesion: 0.33
Nodes (6): assumptions, commission_per_contract, contract_multiplier, contracts_per_butterfly, quantity, stressed_leg_slippage

### Community 225 - "test_run_live.py"
Cohesion: 0.05
Nodes (43): broker_reconciler_loop(), BrokerStateGate, _close_runtime_resources(), entry_loop(), _reconcile_broker_state(), _sync_startup_risk_pnl(), token_reload_loop(), _never_awaited() (+35 more)

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

### Community 230 - "Trade"
Cohesion: 0.19
Nodes (12): bootstrap_report(), candidate_charts(), drawdown(), load_asset(), main(), parse_args(), period_returns(), split_metrics() (+4 more)

### Community 231 - "Dataset"
Cohesion: 0.07
Nodes (13): Dataset, dataset_hash(), session_dir(), SessionClock, _cboe(), _dates(), mini(), _perturbed() (+5 more)

### Community 232 - "parse_quotes"
Cohesion: 0.14
Nodes (7): parse_quotes(), ThetaDataError, files(), _minute_rows(), _quote_csv(), test_millisecond_timestamps_with_trimmed_zeros_parse(), test_quotes_map_to_utc_and_types_and_a_0_0_row_is_no_quote()

### Community 233 - "download_schwab_cache.py"
Cohesion: 0.22
Nodes (6): day_cache_path(), load_day(), _parse_bar(), save_day(), date_range(), main()

### Community 234 - "SPX idea sweep — registry (written 2026-09-25 before any variant was run)"
Cohesion: 0.50
Nodes (3): Round 2 — POST-HOC (written after seeing round-1 results; exploratory only), SPX idea sweep — registry (written 2026-09-25 before any variant was run), Variants

### Community 236 - "main"
Cohesion: 0.04
Nodes (29): Architecture Map, Current architecture, Primary options runtime, Reusable components, Dependency map, Phase 3 Shadow Surfaces (unwired, default off), M5 — Chain parser takes `options[0]` per strike with no root filter (Needs verification), iter_chain_options() (+21 more)

### Community 237 - "test_gateway_minute_backfill.py"
Cohesion: 0.19
Nodes (6): FakeClient, no_sleep(), rec(), test_days_before_retention_and_holidays_are_not_problems(), test_dump_writes_one_research_format_record_per_symbol_and_weekday(), test_holes_errors_and_empty_symbols_are_problems()

### Community 238 - "entry_pricing.py"
Cohesion: 0.17
Nodes (12): capped_entry_limit(), net_price_increment(), round_credit_limit(), round_debit_limit(), _to_increment(), test_capped_entry_limit_never_rounds_above_configured_maximum(), test_debits_round_down_and_credits_round_up(), test_entry_fill_limit_comparison_is_decimal_safe() (+4 more)

### Community 239 - "fill_models"
Cohesion: 0.50
Nodes (4): fill_models, corrected_midpoint, marketable, stressed_marketable

### Community 240 - "Equity candles and order-book recording"
Cohesion: 0.40
Nodes (4): Backfill candles, Equity candles and order-book recording, Historical limitation, Operational caution

### Community 241 - "test_collector.py"
Cohesion: 0.18
Nodes (4): test_collect_snapshot_parses_chain(), test_collect_snapshot_row_fields(), test_collect_snapshot_succeeds_when_chain_cache_write_fails(), test_collect_snapshot_writes_chain_cache_off_event_loop()

### Community 242 - "2. Other external and public sources"
Cohesion: 0.22
Nodes (9): 2.1 Yahoo Finance (`yfinance`), 2.2 S&P 500 constituent dataset on GitHub, 2.3 Wikipedia Nasdaq-100 page, 2.4 Nasdaq Trader symbol directories, 2.5 SEC company ticker map and submissions, 2.6 Alpha Vantage earnings calendar and news sentiment, 2.7 Forex Factory economic calendar, 2.8 Local market calendar and clock (+1 more)

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

### Community 253 - "ThetaData backtesting readiness and completion plan"
Cohesion: 0.29
Nodes (7): Data inventory and remaining limits, Defined steps to complete broad SPXW backtesting, Execution follow-through, Separate extensions, ThetaData backtesting readiness and completion plan, What is ready, Working smoke command and evidence

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
Cohesion: 0.29
Nodes (7): canonicalize_schwab_chain_symbol(), _finite_number(), GatewayMarketDataError, _nonnegative_integer(), _optional_number(), _require_usable_observation(), _same_symbol()

### Community 260 - "Window C — the two token writers resolved (2026-08-08)"
Cohesion: 0.25
Nodes (8): C1 — the operator chose the shared lock, C3 plan produced, and a stale design point corrected, Durability decided, monitoring still open, Housekeeping, Multi-consumer shape — confirmed sound, with two wrinkles, Proven on the host by the production path, at zero extra token writes, Still open, Window C — the two token writers resolved (2026-08-08)

### Community 261 - "report_broker_order_statuses.py"
Cohesion: 0.27
Nodes (12): _allowed_roots(), _build_payload(), main(), _order_symbols(), _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses(), test_payload_excludes_non_spx_orders() (+4 more)

### Community 262 - "docs/README.md"
Cohesion: 0.10
Nodes (14): Canonical research datasets, Live WebSocket, Recent snapshots, SchwabGateway order books, Completed decision, Distinct datasets and source versions, Ernie comparison reconciliation — 2026-10-02, Provenance and access limits (+6 more)

### Community 263 - "SPX paper-trade review — September 12, 2026"
Cohesion: 0.33
Nodes (5): Evidence and scope, Findings, Mechanism worth testing, Research pipeline and proposed experiment, SPX paper-trade review — September 12, 2026

### Community 264 - "JsonlStreamRecorder"
Cohesion: 0.18
Nodes (3): Streaming, Streaming flow, JsonlStreamRecorder

### Community 265 - "test_research_hypotheses.py"
Cohesion: 0.12
Nodes (20): _calendar(), _features(), _fly(), _quiet(), _session(), _straddle(), StubBase, StubLoader (+12 more)

### Community 266 - "Registration decision package — 2026-09 (for the owner; nothing is registered)"
Cohesion: 0.25
Nodes (7): Decisions only the owner can make, H-EV1 — skip pre-entry releases (`HEV1`), H-LV1 — skip low-VIX calls (`HLV1`), H-SN1 — σ-normalised selector (`HSN1`), H-TS1 — rich one-day implied (`HTS1`), Optional H-EV2 — skip FOMC statement days (not implemented), Registration decision package — 2026-09 (for the owner; nothing is registered)

### Community 268 - "test_research_accounting.py"
Cohesion: 0.08
Nodes (50): price_trade(), PeakTrailer, fly_quotes(), make_chain(), minute(), _blown_out(), _clock_session(), _delayed() (+42 more)

### Community 294 - "test_equity_market_data.py"
Cohesion: 0.27
Nodes (6): symbol_directory(), test_jsonl_recorder_persists_raw_message(), test_subscribe_registers_handlers_before_nyse_services(), test_symbol_directory_is_stable_and_sanitizes_path_characters(), test_symbol_directory_rejects_parent_directory_symbol(), test_write_candle_snapshot_sorts_candles()

### Community 297 - "exit_trials/PLAN.md"
Cohesion: 0.40
Nodes (3): Exit trials fixed before execution — September 13, 2026, Executed SPX exit trials, Reproduce

### Community 298 - "test_realized_vs_implied.py"
Cohesion: 0.29
Nodes (8): atm_straddle(), move(), test_atm_straddle_needs_both_sides_at_nearest_strike(), test_format_message_fits_discord_and_marks_pending(), test_review_week_is_last_completed_week(), test_summarize_known_answer_and_skips_pending_closes(), test_z_uses_125x_straddle_and_landing_is_gap_directional(), _tool()

### Community 299 - "test_market_data_providers.py"
Cohesion: 0.20
Nodes (25): _bar(), _contract(), _observation(), test_direct_provider_delegates_without_transforming_results(), test_empty_extended_session_is_allowed_but_other_flags_remain_fatal(), test_gateway_provider_adapts_history_and_combines_sessions(), test_gateway_provider_adapts_typed_spot_and_full_chain(), test_gateway_provider_canonicalizes_chain_symbol_at_client_boundary() (+17 more)

### Community 301 - "All 108 historical entries: executed exit experiments"
Cohesion: 0.33
Nodes (4): All-history extension fixed before execution, All 108 historical entries: executed exit experiments, Outputs, Run locally

### Community 304 - "manifest.json"
Cohesion: 0.15
Nodes (12): created_utc, entry_prices, exit_commission_points, files, raw/checkout-source-hashes.json, raw/deployment.txt, raw/export.jsonl, raw/monitor.jsonl (+4 more)

### Community 307 - "Reproduce the SPX exit-policy experiment"
Cohesion: 0.22
Nodes (7): Acquisition actually performed, Conditional end-to-end confirmation, Offline reproduction, Output map, Replay rules and costs, Reproduce the SPX exit-policy experiment, SPX exit-policy research — September 12, 2026

### Community 314 - "Ernie (@0DTE) comparison — variant plan (not run)"
Cohesion: 0.13
Nodes (13): Constraints, D — direction, Data route (pending owner decision), E — entry trigger (structural levels), Ernie (@0DTE) comparison — variant plan (not run), Ernie's rules, as stated, Order, Source (+5 more)

### Community 349 - "5. Local files and backtest inputs"
Cohesion: 0.25
Nodes (8): 5.1 Application YAML configuration, 5.2 Environment variables and `.env`, 5.3 `tokens.json`, 5.4 Universe and metadata files, 5.5 Historical minute CSVs, 5.6 Local daily bar cache, 5.7 Local option-chain cache, 5. Local files and backtest inputs

### Community 350 - "SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan"
Cohesion: 0.18
Nodes (10): Access, credential and timestamps, Assessment, Endpoints and request plan, Licence (individual plans), Plans and prices (as read), Purchase checklist, SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan, ThetaData: public-docs findings and purchase checklist (2026-09-28) (+2 more)

### Community 351 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 352 - "DirectSchwabMarketDataProvider"
Cohesion: 0.11
Nodes (12): C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, The wiring point, What C3 does not do, Proposed provider interfaces, DirectSchwabMarketDataProvider (+4 more)

### Community 353 - "2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only), Call-only entry filters, Moving-average direction versus the gap rule, Reproduction, Robustness to fly choice (near-tied flies), Setup and accounting, Why the backtest and live paper disagree

### Community 355 - "block_bootstrap_indices"
Cohesion: 0.13
Nodes (10): Baseline, Data and split (fixed now, before any vendor data is seen), Hypotheses, Next SPX sweep on vendor history — pre-registration DRAFT (not registered), Out of scope for this sweep, Primary metric and gate, block_bootstrap_indices(), gates() (+2 more)

### Community 356 - "2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)"
Cohesion: 0.33
Nodes (6): 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only), Data and harness, Hypothesis registered for a future forward cohort (not applied), Low-VIX diagnosis, Sweep results (stressed net P&L), Why the baseline fails in H2

### Community 358 - "Documentation map"
Cohesion: 0.22
Nodes (9): Architecture, Archive, Artifact retention, Command ownership, Documentation map, Operations and data, Research, Reviews and agent handoffs (+1 more)

### Community 359 - "quote_rules"
Cohesion: 0.29
Nodes (7): quote_rules, crossed_market, entry_gap, exit_gap, missing_market, selection, substitution

### Community 360 - "ButterflyOrderBuilder"
Cohesion: 0.42
Nodes (6): ButterflyOrderBuilder, make_candidate(), test_build_close_order_structure(), test_build_open_order_legs(), test_build_open_order_structure(), test_build_order_with_quantity()

### Community 361 - "2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)"
Cohesion: 0.33
Nodes (6): 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run), Also changed, Readings the draft left open, now fixed in code, for the owner to review before registering, Refusals, all before any holdout session is replayed, Tests, The command

### Community 362 - "assumptions"
Cohesion: 0.33
Nodes (6): assumptions, commission_per_contract, contract_multiplier, contracts_per_butterfly, quantity, stressed_leg_slippage

### Community 363 - "Prospective cohort validation, version 2"
Cohesion: 0.40
Nodes (4): Corrections for newly registered cohorts, Keep the original experiment separate, Prospective cohort validation, version 2, Verification

### Community 364 - "endpoint"
Cohesion: 0.40
Nodes (5): endpoint, min_cash_settlements, min_stressed_winners, rule, target_trades

### Community 365 - "Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)"
Cohesion: 0.33
Nodes (6): Correction to Window H part 1, Item 1 — the warnings now fire before the deadline (deployed), Item 3 built — the token reload (2026-08-09, NOT deployed), Item 3 — the deciding question is answered: the swap is safe, Window H correction — the restart arithmetic was wrong, and the gateway never needed restarting, Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)

### Community 366 - "Research core"
Cohesion: 0.20
Nodes (8): Decision profiles, Diagnostics (descriptive only), Known differences, Mechanism check for H-TS1 (descriptive only), Parity with the frozen replay, Registry, Reproducing the idea sweep, Research core

### Community 368 - "math"
Cohesion: 0.29
Nodes (8): ev_rank_factory(), r1(), r2(), r5(), ratio_at(), ror(), e0(), k1()

### Community 369 - "test_research_tieset.py"
Cohesion: 0.21
Nodes (6): draw_keys(), _cand(), test_draws_are_keyed_by_session_and_direction(), test_promotion_shift_is_rr_gap_over_combined_cost_sensitivity(), test_run_scores_tie_sets_unless_told_not_to(), test_selector_pool_applies_center_tolerance_and_rr_max_per_width()

### Community 370 - "H-TR1 registration — trail armed at +75% with a breakeven floor"
Cohesion: 0.13
Nodes (11): Data, Entries (frozen, unchanged from the 09-25 harness replica), H-TR1 registration — trail armed at +75% with a breakeven floor, Hypothesis, Pass criteria (all must hold; stressed accounting; per one-lot), Reported but not gating, Result (run once, 2026-10-01, at b0b7215), Run (+3 more)

### Community 371 - "OrderManager"
Cohesion: 0.05
Nodes (27): Historical Cycle Checkpoints, Order and account flow, Corrections to the Window H brief, M4 — Price-increment rounding is $0.01; SPX complex orders likely require $0.05 (Needs verification), Strengths worth keeping, Drill findings fixed, Follow-up — 2026-07-14, Offline safety-drill record — 2026-07-13 (+19 more)

### Community 372 - "send_realized_vs_implied.py"
Cohesion: 0.39
Nodes (4): _et(), fetch_session(), fetch_sessions(), review_week()

### Community 373 - "2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only), Cohort runner move (2026-09-27) and a labeling note, Cohort shadow (exploratory, three sessions), Exit-latency stress, Parity, Research core and data, Variant registry

### Community 375 - "2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)"
Cohesion: 0.33
Nodes (6): 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered), Consequences, Decision and change, Still open, The calibration study (scratch, development data), What it gives on the real dataset (in-process, nothing registered)

### Community 376 - "2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)"
Cohesion: 0.33
Nodes (6): 2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only), Data and harness, Hypothesis for a future test (not applied), Post-hoc middle ground (defined after the table above), Pre-declared variants (written before running), Reproduction

### Community 377 - "Implementation prompt: SPX session quality and exclusion ledger"
Cohesion: 0.13
Nodes (12): Auxiliary inputs (manifest schema 2), Data, Event calendar, Overnight futures (ES): audit only, Boundaries, Deliverable and scope, Existing inputs, Implementation prompt: SPX session quality and exclusion ledger (+4 more)

### Community 378 - "backfill_equity_candles.py"
Cohesion: 0.39
Nodes (4): async_main(), main(), parse_args(), run()

### Community 379 - "2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0"
Cohesion: 0.40
Nodes (5): 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0, Decisions, How the floor is implemented (`7b1f229`), Re-run under the floor, Still open

### Community 380 - "HistorySource"
Cohesion: 0.12
Nodes (8): 2026-09-28 — stage 5: corrected data decision, housekeeping, ThetaData readiness (stubbed), H-TS1 mechanism check (development window, descriptive), Data decision (corrected), H-TS1 mechanism check (DESCRIPTIVE — development window — not a rule evaluation), Housekeeping, ThetaData readiness (stubbed, nothing bought, nothing downloaded), Phase 2 — local raw-Parquet source and normalization, HistorySource, _thetadata()

### Community 381 - "run"
Cohesion: 0.25
Nodes (3): _install_signal_handlers(), run(), _subscribe()

### Community 382 - "gateway_minute_backfill.py"
Cohesion: 0.32
Nodes (3): check(), dump(), main()

### Community 383 - "ThetaData option history (raw)"
Cohesion: 0.29
Nodes (6): Conventions, Layout, Reading, Sets, The spent holdout (2024-07-01 to 2026-03-12), ThetaData option history (raw)

### Community 385 - "test_collector_daily_bars.py"
Cohesion: 0.52
Nodes (5): _collector(), _daily_candle(), test_daily_bars_failure_leaves_refresh_pending_and_retries(), test_daily_bars_skip_todays_in_progress_candle(), test_daily_bars_use_eastern_session_date_not_host_date()

### Community 386 - "database"
Cohesion: 0.19
Nodes (4): database(), vix(), test_dry_run_start_is_rejected_before_input_reads(), test_invalid_cohort_is_rejected_before_database_access()

### Community 388 - "2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)"
Cohesion: 0.40
Nodes (5): 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered), Consequences for H-TS1 alone (k = 1), Decision and change, Still open, Study before the decision

### Community 389 - "Exact-SHA Deployment Proof - 2026-07-15"
Cohesion: 0.33
Nodes (5): Deployment and verification, Exact-SHA Deployment Proof - 2026-07-15, Follow-up rollback and restore drill, Preconditions and validation, Scope

### Community 390 - "XSP Manual-Flatten Evidence - 2026-07-16"
Cohesion: 0.33
Nodes (5): Fail-closed proof, Post-action reconciliation and paper restore, Redacted evidence, Result, XSP Manual-Flatten Evidence - 2026-07-16

### Community 392 - "2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data)"
Cohesion: 0.50
Nodes (4): 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data), Housekeeping, Registration decision package (nothing registered), Tooling hygiene

### Community 393 - "2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered)"
Cohesion: 0.50
Nodes (4): 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered), Decision and change, Results, Still open

### Community 394 - "test_discover_options_strategy.py"
Cohesion: 0.47
Nodes (4): quote(), test_credit_risk_uses_wing_width_less_credit(), test_debit_trade_crosses_spread_and_pays_commission(), test_percentile_requires_prior_history_and_drawdown_compounds()

### Community 395 - "2026-10-02 — edge search: hold to settlement with a VIX floor (development + validation; nothing registered)"
Cohesion: 0.40
Nodes (5): 2026-10-02 — edge search: hold to settlement with a VIX floor (development + validation; nothing registered), Caveats, Discipline, Findings, What followed

### Community 396 - "Critical External-Alert Delivery Proof - 2026-07-15"
Cohesion: 0.40
Nodes (4): Critical External-Alert Delivery Proof - 2026-07-15, Implementation reviewed, Scope, Supervised delivery and deduplication result

### Community 397 - "csv"
Cohesion: 0.33
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

### Community 404 - "spot_ticks.parquet"
Cohesion: 0.67
Nodes (3): spot_ticks.parquet, rows, sha256

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **1108 isolated node(s):** `created_utc`, `range`, `trades`, `provider`, `original_acquisition_utc` (+1103 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2664 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **120 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `time_utils.py`, `report_broker_order_statuses.py`, `butterfly_gateway_acceptance.py`, `JsonlStreamRecorder`, `Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)`, `TradeQueries`, `SchwabDataLoader`, `Codex Project State`, `_assert_broker_state_matches_db`, `Schwab Gateway Migration Plan`, `PositionService`, `run_live.py`, `session_date`, `record_equity_market_data.py`, `Branch Review and Integration Plan`, `OptionQuote`, `test_schwab_client.py`, `services/daily_report_card.py`, `DirectSchwabMarketDataProvider`, `Capability recorder design`, `test_run_live.py`, `Window F — the refresh token re-authorized, six days early (2026-08-08)`, `main`, `OrderManager`, `backfill_equity_candles.py`, `run`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `OptionQuote` connect `OptionQuote` to `run_paper_replay.py`, `fly_settlement_value`, `test_order_manager.py`, `simulate.py`, `test_research_accounting.py`, `StrategySettings`, `SyntheticChainGenerator`, `position_manager.py`, `run_entry_analysis.py`, `run_backtest_db.py`, `PositionService`, `DayData`, `chain_cache.py`, `test_position_monitoring.py`, `run_live.py`, `AppConfig`, `DbDataLoader`, `test_prospective_execution.py`, `SessionLoader`, `ButterflyCandidate`, `prospective_execution.py`, `report_exit_mark_parity.py`, `main`, `HistorySource`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `fly_settlement_value`, `run_paper_replay.py`, `test_order_manager.py`, `trade_chart.py`, `simulate.py`, `test_research_accounting.py`, `StrategySettings`, `RunContext`, `position_manager.py`, `run_backtest_db.py`, `f2_shadow_report.py`, `PositionService`, `DayData`, `config.py`, `test_position_monitoring.py`, `run_live.py`, `MinuteBar`, `test_prospective_execution.py`, `OptionQuote`, `test_order_preview.py`, `prospective_execution.py`, `test_run_live.py`, `SimulationEngine`, `ButterflyOrderBuilder`, `main`, `test_research_tieset.py`, `OrderManager`, `parse_args`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `Dataset` (e.g. with `cmd_cache_inputs()` and `cmd_import()`) actually correct?**
  _`Dataset` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Are the 58 inferred relationships involving `ButterflyCandidate` (e.g. with `Models and SDK coupling` and `6. Canonical and derived analytical data types`) actually correct?**
  _`ButterflyCandidate` has 58 INFERRED edges - model-reasoned connections that need verification._
- **Are the 46 inferred relationships involving `RunContext` (e.g. with `AppConfig` and `EventDaySkipEntry`) actually correct?**
  _`RunContext` has 46 INFERRED edges - model-reasoned connections that need verification._