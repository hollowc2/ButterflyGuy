# Graph Report - weekend-cleanup-2026-10-02  (2026-10-02)

## Corpus Check
- 417 files · ~878,349 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 47 file(s) not represented in the graph (top: .parquet 15, (none) 10, .jsonl 8)

## Summary
- 6562 nodes · 16483 edges · 400 communities (278 shown, 122 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 1915 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `132a2d66`
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
- simulation_engine.py
- discover_options_strategy.py
- test_research_local.py
- test_gateway_shadow_reads.py
- 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)
- spx-idea-sweep-2026-09-25/variants.py
- StrategySettings
- forex_calendar.py
- Schwab Gateway Credential Proof
- test_research_session_ledger.py
- test_research_protocol.py
- schwab_gateway_session_soak.py
- Manifest
- test_research_hypotheses.py
- export.py
- reports/daily_report_card.py
- main
- SessionChain
- SyntheticChainGenerator
- Registry
- iter_chain_options
- test_risk_engine.py
- run_entry_analysis.py
- ProfitStateMachine
- run_backtest_db.py
- MinuteBar
- run_prospective_execution.py
- research/shadow.py
- validate.py
- Codex Project State
- _assert_broker_state_matches_db
- pathlib
- Schwab Gateway Migration Plan
- test_research_learning.py
- test_gateway_order_book.py
- send_realized_vs_implied.py
- PositionService
- equity_trade_chart.py
- test_prospective_execution.py
- source_hashes
- OrderManager
- live_performance.py
- Target Trading Platform
- ButterflyGuy AI Review State
- Window A — Token re-authorization (mandatory)
- load_config
- strategy_parameters
- chain_cache.py
- report.py
- test_position_monitoring.py
- run_classifier_sweep.py
- Standalone SchwabGateway Extraction Plan
- Regime
- test_run_backtest_db_defaults.py
- SchwabClientWrapper
- config.py
- DbDataLoader
- datetime
- exit_trials/manifest.json
- trades_path
- test_strategy_page.py
- build_market_events.py
- launch_schwab_gateway_session_soak_20260904.sh
- load_spx_config
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
- run_trials.py
- mechanism.py
- 2026-07-14 — data audit and research design
- Re-authorization checklist — Saturday 2026-08-15
- session_date
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
- health_monitor.py
- AGENTS.md
- test_research_quality.py
- history.py
- test_exit_trials.py
- Butterfly Guy
- launch_schwab_gateway_readiness_soak_20260909.sh
- report_trade_ladders.py
- test_research_thetadata.py
- test_weekend_review.py
- Schwab gateway deployment options
- Window H — verification held; the deadline reminder is mistimed (2026-08-08)
- _run_with_stub_token
- thetadata_download.py
- fly_settlement_value
- strategy_page.py
- Schwab gateway current status
- test_gateway_compose.py
- Schwab Gateway Foundation Smoke Test
- Schwab Single-Token Manager
- ShadowComparingMarketDataProvider
- Strategy Settings
- ThetaDataSource
- run_all_history.py
- ShadowDiscrepancyRecorder
- Registration decision package: ThetaData development window (2026-09-29)
- test_daily_report_card.py
- After-Hours Schwab Gateway Credential-Proof Runbook
- Schwab Gateway Credential-Proof Evidence Template
- Width Selection
- ThetaData durable backtesting execution — 2026-10-01
- Stage-named proof failure and an unpaused restoration — 2026-08-06
- Schwab Gateway Multi-Consumer Foundation
- test_backtest_research_integrity.py
- DayMarket
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
- SchwabGateway order books
- test_run_backtest_db.py
- LocalThetaDataSource
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
- Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)
- gateway-paper-cutover-handoff-prompt.md
- 2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)
- Prospective execution validation — spx-prospective-2026-09-22
- evaluate.py
- Repository Agent Instructions
- Geometric butterfly icon
- RegimeFilter
- Current Schwab Integration
- Options strategy discovery journal
- 2026-09-21 — prospective execution-validation cohort (pre-registration)
- mini_spx/manifest.json
- decision_rules
- test_gateway_ownership_boundaries.py
- 3) Start the SPX stack in Docker
- load_report_gateway_settings
- write_history
- Implementation prompt: finish local ThetaData backtesting support
- SchwabGateway option-chain latency investigation (2026-09-04)
- 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)
- Prospective execution validation — spx-prospective-v2-2026-10-02
- BiasScoreFilter
- FailingDirectProvider
- Exact-SHA Deployment Proof - 2026-07-15
- XSP Manual-Flatten Evidence - 2026-07-16
- Critical External-Alert Delivery Proof - 2026-07-15
- XSP Flat-Runtime Restart Proof - 2026-07-14
- parse_quotes
- ButterflyCandidate
- 2026-09-21 — SPX executable-side accounting on the settlement-correct replay
- test_research_tieset.py
- Market
- resolve_wing_widths_for_vix
- quote_rules
- pandas
- files
- prospective_execution.py
- dev_studies.py
- Historical data management
- FakeConnection
- Offline ThetaData research
- run_live_performance_cron.sh
- decision_rules
- Compare Real vs Synthetic Chains
- ThetaData option history (raw)
- Cohort automation
- assumptions
- test_run_live.py
- test_collector.py
- endpoint
- SchwabGateway order-book release full-session acceptance — 2026-09-01
- export
- Phases
- Dataset
- test_alertmanager_new_firing_cancels_stale_pending_resolution
- test_live_performance_report.py
- SPX idea sweep — registry (written 2026-09-25 before any variant was run)
- record_equity_market_data.py
- TradeService
- test_gateway_minute_backfill.py
- entry_pricing.py
- fill_models
- Equity candles and order-book recording
- Ernie comparison reconciliation — 2026-10-02
- JsonlStreamRecorder
- run_live.py
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
- spot_ticks.parquet
- .append
- report_broker_order_statuses.py
- docs/README.md
- SPX paper-trade review — September 12, 2026
- ChainDay
- RunContext
- Registration decision package — 2026-09 (for the owner; nothing is registered)
- cohort_daily_update.sh
- test_research_accounting.py
- exit_trials/PLAN.md
- CsvDataLoader
- GatewayAuthoritativeMarketDataProvider
- All 108 historical entries: executed exit experiments
- spx-exits-2026-09-12/manifest.json
- Reproduce the SPX exit-policy experiment
- butterfly-guy
- Ernie (@0DTE) comparison — variant plan (not run)
- SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan
- Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)
- ._spawn_background
- 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)
- test_equity_market_data.py
- test_discrepancy_metric_labels_cover_every_declared_code
- 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)
- Documentation map
- quote_rules
- ButterflyOrderBuilder
- 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)
- assumptions
- Prospective cohort validation, version 2
- endpoint
- fill_models
- .history
- run_gateway_minute_backfill.sh
- round2.py
- research/__init__.py
- H-TR1 registration — trail armed at +75% with a breakeven floor
- _redacted_order_audit
- os
- 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)
- test_collector_daily_bars.py
- 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)
- 2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)
- Implementation prompt: SPX session quality and exclusion ledger
- select_pm_settled_rows
- 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0
- AlertmanagerNotifier
- simulate.py
- backfill_equity_candles.py
- DockerExecSource
- report_selection_parity.py
- Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)
- equity_market_data.py
- PostgresSource
- 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)
- load_minute_file
- files
- SPXW session quality evidence ledger — 2026-10-02
- 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data)
- 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered)
- Recorded
- lock_events

## God Nodes (most connected - your core abstractions)
1. `Dataset` - 110 edges
2. `ButterflyCandidate` - 102 edges
3. `RunContext` - 96 edges
4. `OptionQuote` - 94 edges
5. `SchwabClientWrapper` - 93 edges
6. `AppConfig` - 83 edges
7. `Session` - 64 edges
8. `MinuteBar` - 60 edges
9. `et_us()` - 60 edges
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

## Communities (400 total, 122 thin omitted)

### Community 0 - "run_paper_replay.py"
Cohesion: 0.09
Nodes (28): _butterfly_value(), _compute_spread(), detect_complete_days(), _elapsed(), EntryDecision, _et(), find_entry_candidate(), get_prev_close() (+20 more)

### Community 1 - "session_ledger.py"
Cohesion: 0.14
Nodes (11): session_close(), build(), canonical(), cmd_ledger(), Evidence, gate_status(), indexed(), publish() (+3 more)

### Community 2 - "time_utils.py"
Cohesion: 0.07
Nodes (39): M8 — Early closes are hard-coded for 2026 only, _easter_sunday(), get_us_market_early_closes(), get_us_market_holidays(), is_market_open(), is_premarket_window(), is_trading_day(), _last_weekday() (+31 more)

### Community 3 - "test_order_manager.py"
Cohesion: 0.12
Nodes (62): LiveSpread, broker_fill(), _exit_limits_for_bids(), filled_order(), make_candidate(), make_chain_data(), make_chain_data_with_oi(), make_chain_data_with_spread() (+54 more)

### Community 4 - "schwab_gateway_v046_readiness_soak.py"
Cohesion: 0.12
Nodes (30): append_jsonl(), bounded_request(), candidate_observation(), diagnostic_probe(), docker_inspect(), endpoint_snapshot(), finalize(), flatness() (+22 more)

### Community 5 - "cli.py"
Cohesion: 0.08
Nodes (45): build_parser(), evaluation_args(), cmd_calibrate(), cmd_catalog(), cmd_coverage(), cmd_diagnose(), cmd_exclude_sessions(), cmd_export() (+37 more)

### Community 6 - "trade_chart.py"
Cohesion: 0.09
Nodes (26): build_entry_chart_png(), build_exit_chart_png(), ButterflyChartSpec, candles_to_series(), _draw_strike_overlays(), entry_chart_window(), _exit_chart_series(), _exit_marker_point() (+18 more)

### Community 7 - "butterfly_gateway_acceptance.py"
Cohesion: 0.13
Nodes (14): _endpoints(), test_identity_checks_paper_gateway_and_no_shadow_invariants(), test_preopen_accepts_retried_market_data_unavailable(), test_preopen_allows_documented_after_hours_strategy_readiness(), test_preopen_never_suppresses_other_endpoint_failures(), test_preopen_rejects_every_other_readiness_failure(), endpoint_violations(), http_json() (+6 more)

### Community 8 - "simulation_engine.py"
Cohesion: 0.05
Nodes (29): 6.4 Early closes: decided, now fixed (D5), M7 — Regime names are unvalidated and regime time bounds are ignored, ProfitProtectorSettings, TimeRegime, get_time_regime(), PositionState, effective_drawdown_threshold(), ProfitPolicyDecision (+21 more)

### Community 9 - "discover_options_strategy.py"
Cohesion: 0.14
Nodes (33): atm_pair(), bootstrap_report(), butterfly(), candidate_charts(), closest_delta(), credit_spread(), drawdown(), entry_cost() (+25 more)

### Community 10 - "test_research_local.py"
Cohesion: 0.14
Nodes (23): Record a future BMNR session, daily_range(), audit(), normalize(), OneFly, raw(), source(), test_alternate_instrument_identity_and_fractional_grid() (+15 more)

### Community 11 - "test_gateway_shadow_reads.py"
Cohesion: 0.09
Nodes (30): chain_response(), _comparisons(), DirectProvider, _discrepancies(), RecordingGateway, spot_response(), test_a_direct_payload_that_cannot_be_summarized_is_a_parsing_discrepancy(), test_a_disabled_shadow_records_no_metrics_at_all() (+22 more)

### Community 12 - "2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)"
Cohesion: 0.29
Nodes (7): 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data), Built (provider-independent, tested on synthetic data), Development coverage and in-sample E0, Housekeeping, Hypothesis rules (implemented, not registered), Validation results (readiness doc steps 1–4), What this means for the evidence plan

### Community 13 - "spx-idea-sweep-2026-09-25/variants.py"
Cohesion: 0.10
Nodes (23): open_spot(), directions(), ema(), hourly_closes_before(), fn(), et_ts(), exit_trade(), Fly (+15 more)

### Community 14 - "StrategySettings"
Cohesion: 0.12
Nodes (27): StrategySettings, main(), parse_args(), print_help(), ButterflyBuilder, determine_direction(), DirectionFilter, make_chain() (+19 more)

### Community 15 - "forex_calendar.py"
Cohesion: 0.14
Nodes (16): _cell_text(), _fetch_calendar_html(), fetch_usd_events(), ForexEvent, _format_event_line(), format_usd_calendar_text(), _impact_from_row(), _parse_day_label() (+8 more)

### Community 16 - "Schwab Gateway Credential Proof"
Cohesion: 0.06
Nodes (33): Accepted runtime-baseline proof adapter, Candidate capture safety stop — 2026-08-05, Candidate failure diagnosis and scope correction, Candidate new-baseline capture remediation, Command, Compose-hash ambiguity remediation, Content-verified mount result — 2026-08-05, Corrected candidate capture safety stop — 2026-08-05 (+25 more)

### Community 17 - "test_research_session_ledger.py"
Cohesion: 0.12
Nodes (13): evidence(), reconcile(), save(), test_audit_import_supporting_conflict_is_visible(), test_calendar_early_close_and_accepted_no_trade(), test_conflicts_are_visible(), test_missing_input_multiple_reasons_and_approved_exclusion(), test_non_expiration_is_independently_documented_and_eom_is_preserved() (+5 more)

### Community 18 - "test_research_protocol.py"
Cohesion: 0.07
Nodes (40): Baseline, Data and split (fixed now, before any vendor data is seen), Hypotheses, Next SPX sweep on vendor history — pre-registration DRAFT (not registered), Out of scope for this sweep, Primary metric and gate, _blocks(), calibrate_gate1() (+32 more)

### Community 19 - "schwab_gateway_session_soak.py"
Cohesion: 0.13
Nodes (30): adjudicate_transient_non_200(), assert_production_identity(), background_context(), _confirm_surfaces(), _filtered_gateway_logs(), _finite(), _gateway_error_code(), _health() (+22 more)

### Community 20 - "Manifest"
Cohesion: 0.06
Nodes (41): Volatility term structure, 2026-09-28 — stage 5: corrected data decision, housekeeping, ThetaData readiness (stubbed), H-TS1 mechanism check (development window, descriptive), Data decision (corrected), H-TS1 mechanism check (DESCRIPTIVE — development window — not a rule evaluation), Housekeeping, ThetaData readiness (stubbed, nothing bought, nothing downloaded), default_cache_root(), Manifest (+33 more)

### Community 21 - "test_research_hypotheses.py"
Cohesion: 0.12
Nodes (20): _calendar(), _features(), _fly(), _quiet(), _session(), _straddle(), StubBase, StubLoader (+12 more)

### Community 23 - "export.py"
Cohesion: 0.07
Nodes (31): bars_changes(), _bars_key(), chain_sql(), clock_sql(), daily_bars_sql(), DataSource, export_session(), ExportPlan (+23 more)

### Community 24 - "reports/daily_report_card.py"
Cohesion: 0.14
Nodes (27): 6. Canonical and derived analytical data types, Synthetic option-chain data, AccountBalances, ActivitySummary, build_daily_report_card(), CashMovement, count_rejected_orders(), detect_problems() (+19 more)

### Community 25 - "main"
Cohesion: 0.03
Nodes (30): XSP held-leg omission follow-up (2026-09-10), H1 — Public repository with a self-hosted runner that reaches production, H2 — Previous close silently falls back to the current spot price, H3 — The exit decision is gated on non-critical DB writes, with no query timeout, High, M2 — Ambiguity handlers can mask `AmbiguousOrderError` with a DB error, setup_logging(), DatabasePool (+22 more)

### Community 26 - "SessionChain"
Cohesion: 0.11
Nodes (19): SessionChain, arbitrage(), _bad_cells(), _cells(), _dst_week(), index_file_crosscheck(), _lag(), markdown() (+11 more)

### Community 27 - "SyntheticChainGenerator"
Cohesion: 0.05
Nodes (29): bs_call_price(), bs_delta(), bs_gamma(), bs_put_price(), bs_theta(), bs_vega(), _d1(), _d2() (+21 more)

### Community 28 - "Registry"
Cohesion: 0.30
Nodes (10): Registry, RegistryError, _add(), _placeholder(), test_a_port_inherits_the_placeholder_stage_and_counts_once(), test_a_port_needs_a_matching_unported_placeholder(), test_appends_never_rewrite_existing_bytes(), test_stage_is_pre_only_when_registered_before_evaluation() (+2 more)

### Community 29 - "iter_chain_options"
Cohesion: 0.08
Nodes (27): iter_chain_options(), _contract(), _parse_rows(), test_a_map_present_but_empty_produces_zero_everywhere(), test_a_non_numeric_strike_key_diverges_and_the_divergence_is_recorded(), test_a_strike_with_an_empty_option_list_is_excluded_by_all_three(), test_all_three_agree_on_which_expiration_matches(), test_calls_present_with_puts_absent_is_handled_identically_by_all_three() (+19 more)

### Community 30 - "test_risk_engine.py"
Cohesion: 0.25
Nodes (15): make_risk_engine(), test_can_trade_blocks_low_buying_power(), test_can_trade_blocks_quantity_above_max_position_size(), test_can_trade_halted(), test_can_trade_market_closed(), test_can_trade_max_loss(), test_can_trade_max_trades(), test_can_trade_ok() (+7 more)

### Community 31 - "run_entry_analysis.py"
Cohesion: 0.12
Nodes (22): straddle_selection(), fmt_candidate(), get_prev_close(), get_vix(), load_bars_from_db(), load_chains_from_db(), main(), nearest_snapshot() (+14 more)

### Community 32 - "ProfitStateMachine"
Cohesion: 0.14
Nodes (25): QuoteQualitySettings, ProfitState, ProfitStateMachine, make_pos(), make_settings(), test_absolute_loss_stop_fires_without_profit_tent(), test_default_drawdown_confirmation_is_immediate(), test_drawdown_requires_configured_confirmation_polls() (+17 more)

### Community 33 - "run_backtest_db.py"
Cohesion: 0.05
Nodes (61): ExecutableTrade, DrawdownWindow, _accounting_comparison_rows(), _asset_drawdowns(), backtest_entry_price(), candidate_from_trade_row(), _dd_schedule_label(), discover_dates() (+53 more)

### Community 34 - "MinuteBar"
Cohesion: 0.07
Nodes (12): Direct SDK construction and imports, day_cache_path(), load_day(), _parse_bar(), save_day(), DayData, MinuteBar, SchwabDataLoader (+4 more)

### Community 35 - "run_prospective_execution.py"
Cohesion: 0.11
Nodes (22): Start-date correction before the first cohort, CohortError, CohortSpec, deferred_runs_path(), load_manifest(), verify_cohort(), cohort_dir_for(), command_init() (+14 more)

### Community 36 - "research/shadow.py"
Cohesion: 0.10
Nodes (23): Shadow on the open cohort, canonical_hash(), sha256_text(), trade_key(), check_records(), CohortLedger, default_ref(), _git() (+15 more)

### Community 38 - "validate.py"
Cohesion: 0.13
Nodes (23): build_helios_clock_dataset(), _compare(), compare_replays(), _dates(), _distribution(), explain(), _first_difference(), _iso() (+15 more)

### Community 39 - "Codex Project State"
Cohesion: 0.05
Nodes (34): C3 default-off deployment and gateway hardening (2026-08-10), Candidate-feed authentication proven (2026-08-10), Candidate-feed hot reload built locally (2026-08-10, NOT deployed), Candidate-feed hot reload deployed (2026-08-10T16:54:27Z), Codex Project State, Correction 1 — A3 as written cannot work on Helios, Correction 2 — `easy_client` silently no-ops the re-authorization, Correction to Window H part 1 (+26 more)

### Community 40 - "_assert_broker_state_matches_db"
Cohesion: 0.09
Nodes (38): ActiveMonitor, _assert_broker_state_matches_db(), _expired_trade_has_broker_settlement(), _explicit_fill_details(), install_shutdown_handler(), _intent_order_ids(), _json_dict(), _open_trade_positions() (+30 more)

### Community 41 - "pathlib"
Cohesion: 0.06
Nodes (27): `DataSource` adapter spec, add_commands(), _artifact(), _clean(), cmd_audit(), cmd_cache_daily(), cmd_cache_inputs(), cmd_import() (+19 more)

### Community 42 - "Schwab Gateway Migration Plan"
Cohesion: 0.10
Nodes (20): Credential-proof gate, Current migration status, Fake-only readiness and operator checklist, Phase 0 — audit and documentation, Phase 1 — provider boundary, Phase 2 — minimal read-only gateway, Phase 3 — shadow comparison, Phase 4 — read-only cutover (+12 more)

### Community 43 - "test_research_learning.py"
Cohesion: 0.13
Nodes (18): _describe(), Variant, _ctx(), _decisions(), _history(), _loader(), Probe, _quiet() (+10 more)

### Community 44 - "test_gateway_order_book.py"
Cohesion: 0.18
Nodes (10): _recent_payload(), _snapshot(), test_recent_authenticates_and_validates_fresh_contract(), recent(), test_recent_fails_closed_when_gateway_reports_stale_feed(), test_recent_rejects_mismatched_snapshot(), test_stream_authenticates_and_yields_only_requested_contracts(), stream() (+2 more)

### Community 45 - "send_realized_vs_implied.py"
Cohesion: 0.12
Nodes (20): atm_straddle(), _fmt(), format_message(), MoveSummary, SessionMove, summarize(), _summary_line(), verdict() (+12 more)

### Community 46 - "PositionService"
Cohesion: 0.06
Nodes (44): Primary options runtime, M10 — Live settlement wait has no bound, and post-close failures surface late, readiness_snapshot(), set_readiness(), TradeRecord, broker_cash_settlement_from_transactions(), BrokerCashSettlement, _chain_spot_price() (+36 more)

### Community 47 - "equity_trade_chart.py"
Cohesion: 0.15
Nodes (25): TradeResult, build_equity_trade_chart_png(), _compact_volume(), _draw_candles(), _draw_depth_overlay(), _draw_viewfinder(), _draw_volume(), _draw_volume_overlay() (+17 more)

### Community 48 - "test_prospective_execution.py"
Cohesion: 0.16
Nodes (27): executable_side(), leg_provenance(), _baseline(), _candidate(), _cohort(), _quotes(), _record(), _repo() (+19 more)

### Community 49 - "source_hashes"
Cohesion: 0.05
Nodes (40): source_hashes, pyproject.toml, src/butterfly_guy/backtest/chain_cache.py, src/butterfly_guy/backtest/data_loader.py, src/butterfly_guy/backtest/db_loader.py, src/butterfly_guy/backtest/execution_accounting.py, src/butterfly_guy/backtest/__init__.py, src/butterfly_guy/backtest/metrics.py (+32 more)

### Community 50 - "OrderManager"
Cohesion: 0.05
Nodes (33): Historical Cycle Checkpoints, Baseline, Butterfly Guy Code Review — 2026-09-25, Executive summary, Findings index, Low / Info, Method, Operational note found during review (+25 more)

### Community 51 - "live_performance.py"
Cohesion: 0.14
Nodes (23): chart_payload(), cumulative_equity(), drawdown_chart_description(), drawdown_episodes(), drawdown_series(), DrawdownPoint, duration_minutes(), equity_chart_description() (+15 more)

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
Nodes (25): main(), main(), load_config(), ProfitManagementSettings, _regimes(), test_allow_live_trading_requires_explicit_env(), test_checked_in_configs_keep_default_regime_bounds(), test_config_rejects_unknown_keys() (+17 more)

### Community 56 - "strategy_parameters"
Cohesion: 0.07
Nodes (30): strategy_parameters, afternoon_dd, allow_late_entry_fallback, asset, bull_call_bias, csv, dd_schedule, direction (+22 more)

### Community 57 - "chain_cache.py"
Cohesion: 0.20
Nodes (13): chain_cache_path(), chain_journal_path(), load_chain_day(), _read_snapshots(), save_snapshot(), test_chain_cache_path_is_partitioned_by_underlying(), test_load_chain_day_falls_back_to_partitioned_spx_cache(), test_load_chain_day_merges_legacy_json_with_jsonl() (+5 more)

### Community 58 - "report.py"
Cohesion: 0.08
Nodes (20): render(), us_to_datetime(), _ci(), _iso(), markdown(), _money(), _r(), trade_record() (+12 more)

### Community 59 - "test_position_monitoring.py"
Cohesion: 0.21
Nodes (8): _candidate(), _gateway_contract(), _quotes(), _service(), test_intermittent_missing_held_leg_degrades_then_recovers_without_broker_write(), get_option_chain(), test_trade_282_uses_gateway_held_leg_when_contract_is_not_stale(), _trade_282_candidate()

### Community 60 - "run_classifier_sweep.py"
Cohesion: 0.16
Nodes (14): Phase 1: one command surface, max_consecutive_losses(), max_drawdown(), profit_factor(), sharpe(), win_pct(), _accounting_metrics(), _summarize_combo() (+6 more)

### Community 61 - "Standalone SchwabGateway Extraction Plan"
Cohesion: 0.10
Nodes (19): Fixed defaults, Legacy-retirement approval packet — drafted, not executable, Phase 0 — Baseline and safety record, Phase 1 — Create the standalone repository, Phase 2 — Remove program-specific coupling, Phase 3 — Package and contract parity, Phase 4 — Prepare ButterflyGuy to consume shared packages, Phase 5 — Parallel Helios candidate (+11 more)

### Community 62 - "Regime"
Cohesion: 0.13
Nodes (7): RegimeDispatch, GapRegimeFilter, Regime, TestBullCallBias, TestDefaultsAreNoop, TestMinGapPct, TestSkipBeforeOverride

### Community 63 - "test_run_backtest_db_defaults.py"
Cohesion: 0.13
Nodes (15): select_direction_bar(), _parse_for_asset(), test_backtest_auto_direction_uses_first_regular_session_snapshot(), test_backtest_parses_exit_arm_sweep_overrides(), test_backtest_rejects_invalid_research_inputs(), test_backtest_tracks_explicit_selection_overrides(), test_candidate_from_trade_row_pins_live_trade_fields(), test_db_quote_loader_does_not_impute_missing_market_fields() (+7 more)

### Community 64 - "SchwabClientWrapper"
Cohesion: 0.04
Nodes (29): Authentication and token lifecycle, Order and account flow, Shared-token risk, Candidate-feed reload follow-up (2026-08-10), Deployment addendum (2026-08-10), Production marker-change proof (2026-08-10), Recommendation, Reducing the weekly re-authorization cost — a scoping question (+21 more)

### Community 65 - "config.py"
Cohesion: 0.07
Nodes (46): Decision profiles, AppConfig, CollectorSettings, ConfigModel, DatabaseSettings, EntrySettings, ExecutionSettings, MonitoringSettings (+38 more)

### Community 69 - "datetime"
Cohesion: 0.11
Nodes (24): baseline_entry(), bucket(), main(), hma_series(), hull_rising(), main(), wma(), bs_gamma() (+16 more)

### Community 70 - "exit_trials/manifest.json"
Cohesion: 0.07
Nodes (27): account_sharpe, baseline_parity, command, created_utc, display_timezone, environment_variables, exit_commission_points, git_sha (+19 more)

### Community 71 - "trades_path"
Cohesion: 0.19
Nodes (25): daily_runs_path(), manifest_path(), read_jsonl(), summarize_cohort(), trades_path(), write_manifest(), current_summary(), _mock_cohort_update() (+17 more)

### Community 72 - "test_strategy_page.py"
Cohesion: 0.16
Nodes (10): _params(), test_generate_refuses_missing_strategy_config(), test_generate_writes_strategy_page_beside_report(), fake_build_report(), fake_connect(), test_page_has_no_inline_executable_script(), test_page_renders_config_values_and_no_leftover_tokens(), test_params_follow_the_spx_config() (+2 more)

### Community 73 - "build_market_events.py"
Cohesion: 0.12
Nodes (23): main(), result_table(), main(), money(), table(), bea_releases(), bls_releases(), capture_date() (+15 more)

### Community 74 - "launch_schwab_gateway_session_soak_20260904.sh"
Cohesion: 0.12
Nodes (15): CONSUMERS, die(), EVIDENCE_DIR, FLATNESS, GW_CONTAINER, GW_ID, GW_IMAGE, GW_REVISION (+7 more)

### Community 75 - "load_spx_config"
Cohesion: 0.19
Nodes (10): load_spx_config(), _cboe(), _dates(), mini(), _perturbed(), _quiet(), test_a_close_that_differs_from_cboe_fails_step_4(), test_a_dataset_validated_against_itself_passes_steps_1_2_and_4() (+2 more)

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
Cohesion: 0.14
Nodes (10): PriceHistoryProvider, DailyReportCardSettings, load_daily_report_card_config(), ReportCardThresholds, archive_report(), chartable_equity_trades(), format_equity_trade_chart_caption(), ReportCardResult (+2 more)

### Community 82 - "weekend_review.py"
Cohesion: 0.15
Nodes (24): TradePoint, build_combined_performance_chart_png(), build_eod_chart_for_row(), calendar_month_to_date(), closed_trades_to_points(), fetch_closed_trades(), format_combined_performance_caption(), format_executable_pnl() (+16 more)

### Community 83 - "Architecture"
Cohesion: 0.10
Nodes (19): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, Architecture, Behavioral Guidelines, code:bash (# Start SPX live trader), code:bash (# Install dependencies) (+11 more)

### Community 84 - "ButterflyGuy data sources and data types"
Cohesion: 0.04
Nodes (48): 10. Repository evidence map, 1.1 Account-number resolution, 1.2 Option chains, 1.3 Single-symbol spot/index quotes, 1.4 Batched equity quotes, 1.5 Price-history candles, 1.6 Market movers, 1.7 Account snapshot, balances, and positions (+40 more)

### Community 85 - "Options strategy discovery report"
Cohesion: 0.18
Nodes (10): Best observed candidate (rejected), Bootstrap, Monte Carlo, and risk, Executive summary, Failed hypotheses and weaknesses, Future research roadmap, Options strategy discovery report, Out-of-sample and walk-forward evidence, Parameter sensitivity and rolling selection (+2 more)

### Community 86 - "test_research_mechanism.py"
Cohesion: 0.19
Nodes (10): _inputs(), _sessions(), _synthetic(), test_decision_rule_on_planted_and_null_effects(), test_first_session_uses_the_prior_development_session(), test_prior_values_come_from_the_previous_spx_session(), test_rows_outside_the_window_are_dropped_before_computing(), test_session_without_a_prior_vix1d_is_excluded() (+2 more)

### Community 87 - "9) Capture equity candles and Level II for trade review"
Cohesion: 0.67
Nodes (3): 9) Capture equity candles and Level II for trade review, code:bash (uv run python -m butterfly_guy.scripts.backfill_equity_candl), code:bash (uv run python -m butterfly_guy.scripts.record_equity_market_)

### Community 88 - "Shared SPX candidate fleet"
Cohesion: 0.15
Nodes (22): 4) Run the live orchestrator directly, 5) Smoke-test the backtest from Docker, 6) Inspect a historical entry decision, 7) Run the morning equity scan, 8) Generate or compare reports, Backtesting, code:bash (uv run python src/butterfly_guy/scripts/run_live.py --config), code:bash (docker exec butterfly_spx_app python -m butterfly_guy.script) (+14 more)

### Community 89 - "daily_report_card_format.py"
Cohesion: 0.21
Nodes (17): DailyReportCard, effective_pnl(), effective_pnl_pct(), effective_start_balance(), build_report_messages(), _direction_emoji(), _fmt_money(), _fmt_pct() (+9 more)

### Community 90 - "test_candidate_dashboards.py"
Cohesion: 0.32
Nodes (11): _dashboard(), _expressions(), _panels(), visit(), test_performance_trade_links_pin_the_main_strategy_datasource(), test_retired_experimental_runtime_is_absent_from_dashboards(), test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource(), test_trade_detail_uses_selected_trade_monitoring_as_candidate_spot_fallback() (+3 more)

### Community 92 - "run_trials.py"
Cohesion: 0.14
Nodes (22): main(), bootstrap_mean_delta(), main(), sha(), stats(), write_csv(), main(), metrics() (+14 more)

### Community 93 - "mechanism.py"
Cohesion: 0.15
Nodes (13): bootstrap(), confine(), _f(), fetch_spx(), frame_sha256(), _group(), markdown(), parse_spx_csv() (+5 more)

### Community 94 - "2026-07-14 — data audit and research design"
Cohesion: 0.29
Nodes (7): 2026-07-14 — data audit and research design, Data limitations and leakage controls, Final data-driven pass, First-pass result, Predeclared hypotheses (no tuning yet), Second structural pass, Verified data

### Community 95 - "Re-authorization checklist — Saturday 2026-08-15"
Cohesion: 0.13
Nodes (14): Automated warnings before the cadence reset, Before you start, Expected result: no containers restarted, First, watch the reload do its job, Re-authorization checklist — Saturday 2026-08-15, Step 0 — already done, nothing to do, Step 1 — mint the token on zeus, in a real terminal, Step 2 — stage on Helios and verify byte-identical (+6 more)

### Community 96 - "session_date"
Cohesion: 0.08
Nodes (10): M11 — A restart with an open trade double-counts the entry cost in daily P&L, RiskSettings, session_date(), ConsecutiveLossNotifier, RiskEngine, _sync_startup_risk_pnl(), _StatefulRiskQueries, test_restart_open_trade_exposure_blocks_entry_until_closed() (+2 more)

### Community 97 - "Capability recorder design"
Cohesion: 0.25
Nodes (7): Capability recorder design, Evidence per observation, Output, Probes, Schedule, Schwab Capability Matrix, Stop conditions

### Community 98 - "report_exit_mark_parity.py"
Cohesion: 0.26
Nodes (11): analyze_manual(), analyze_trade(), _compare_snapshots(), _fly_from_rows(), _leg_rows_at_snapshot(), main(), _nearest_snapshot_time(), parse_args() (+3 more)

### Community 99 - "pytest"
Cohesion: 0.12
Nodes (7): test_auth_init_honours_schwab_token_path(), test_notify_entry_includes_trade_stats(), capture(), test_notify_exit_formats_contract_pnl_as_dollars(), test_notify_text_posts_plain_message(), test_telegram_send_async_runs_blocking_send_off_loop(), test_close_trade_only_closes_an_open_trade_once()

### Community 101 - "2026-09-20 — SPX cash-settlement parity correction"
Cohesion: 0.50
Nodes (4): 2026-09-20 — SPX cash-settlement parity correction, Evidence, assumptions, and exclusions, Exact commands and implementation fingerprints, Frozen result

### Community 102 - "SimulationEngine"
Cohesion: 0.05
Nodes (39): P — strike placement, Accounting and evaluation, Diagnostics (descriptive only), Known differences, Mechanism check for H-TS1 (descriptive only), Parity with the frozen replay, Registry, Reproducing the idea sweep (+31 more)

### Community 103 - "generate_live_performance.py"
Cohesion: 0.19
Nodes (11): no_trade_reason(), best_trade(), reference_spot(), build_report(), fetch_closed_trades(), fetch_no_trade_days(), generate(), main() (+3 more)

### Community 104 - "performance_chart.py"
Cohesion: 0.15
Nodes (13): compute_stats(), ReportStats, build_performance_chart_png(), _fig_to_png(), _format_pnl(), _period_subtitle(), _plot_period_panels(), _setup_axes() (+5 more)

### Community 105 - "Window F — the refresh token re-authorized, six days early (2026-08-08)"
Cohesion: 0.15
Nodes (12): Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08), Execution, Incidental, Result, Still unproven, The correction that forced the restarts, The exit-137 finding, correctly diagnosed (2026-08-08), The scheduling finding (+4 more)

### Community 107 - "EventCalendar"
Cohesion: 0.09
Nodes (16): _date(), EventCalendar, MarketEvent, parse_row(), _row(), test_committed_calendar_has_a_scheduled_event_of_each_type_every_year(), test_committed_calendar_loads_and_covers_the_range(), test_event_published_on_or_after_the_session_is_invisible_to_it() (+8 more)

### Community 109 - "Window D — the gateway made reachable, started, and watched (2026-08-08)"
Cohesion: 0.18
Nodes (11): Applied to /opt/monitoring with approval, by reload not recreation, C1 proven under genuine contention — the thing Window C could not test, D1 — the operator chose monitoring_net, and the alternative turned out not to work, D2 — the gateway is up, and durability was proven by an actual crash, Final state, Gateway client metrics — closed (2026-08-08), Preconditions re-verified, and one record corrected, Still open (+3 more)

### Community 110 - "Re-authorization checklist — Saturday 2026-08-22"
Cohesion: 0.18
Nodes (10): Preconditions — verified 2026-08-22T15:45:36Z, Re-authorization checklist — Saturday 2026-08-22, Step 1 — mint on zeus, in a real terminal, Step 2 — stage on Helios, verify byte-identical, Step 3 — move into place under the C1 lock, Step 4 — watch the reloads; restart only on a *confirmed* failure, Step 5 — verify, host against containers, Step 6 — record (+2 more)

### Community 111 - "health_monitor.py"
Cohesion: 0.14
Nodes (8): check_endpoint(), extract_service_name(), load_config(), main(), _now_et(), run_check_cycle(), send_discord_alert(), signal_handler()

### Community 112 - "AGENTS.md"
Cohesion: 0.12
Nodes (15): Architecture Map, code:bash (uv sync), code:bash (uv run pytest), code:bash (uv run ruff check .), code:bash (uv run python src/butterfly_guy/scripts/run_backtest_db.py 2), code:bash (uv run python src/butterfly_guy/scripts/inspect_entry.py 202), code:bash (uv run python src/butterfly_guy/scripts/refresh_equity_unive), code:bash (docker compose -f infra/docker-compose.yml --profile spx up ) (+7 more)

### Community 114 - "test_research_quality.py"
Cohesion: 0.19
Nodes (11): quality_passed(), _cboe(), _day(), test_a_clean_day_passes_every_gate(), test_a_quality_run_never_reads_the_holdout(), test_coverage_crossed_stale_and_timestamp_failures_are_caught(), test_only_a_full_window_pass_opens_earlier_pulls(), test_q5_is_not_evaluable_without_exact_minute_spx_prints() (+3 more)

### Community 115 - "history.py"
Cohesion: 0.05
Nodes (25): _age_fields(), build_session(), BuiltSession, carry_quotes(), GuardedSource, has_print(), HistorySource, index_on_grid() (+17 more)

### Community 116 - "test_exit_trials.py"
Cohesion: 0.20
Nodes (19): compare(), ConfirmedMachine, replay(), variants(), config(), points(), test_confirmation_does_not_delay_hard_end_of_day(), test_confirmation_missing_followup_is_censored() (+11 more)

### Community 119 - "Butterfly Guy"
Cohesion: 0.13
Nodes (15): Gap Regime Filter, Charles Schwab API, Architecture at a glance, Butterfly Guy, code:text (Schwab API), Configuration files, Core repo layout, 🚀 Features (+7 more)

### Community 120 - "launch_schwab_gateway_readiness_soak_20260909.sh"
Cohesion: 0.20
Nodes (10): die(), EVIDENCE_DIR, LAUNCHER, LOG, MONITOR, SESSION_DATE, launch_schwab_gateway_readiness_soak_20260909.sh script, TARGET_EPOCH (+2 more)

### Community 121 - "report_trade_ladders.py"
Cohesion: 0.18
Nodes (10): _coerce_json(), _docker_postgres_password(), _load_trace_event(), _load_trade_rows(), main(), parse_args(), _pretty(), _print_trace_block() (+2 more)

### Community 122 - "test_research_thetadata.py"
Cohesion: 0.22
Nodes (15): _cboe(), _source(), Terminal, test_a_holdout_pull_stops_before_any_terminal_request(), test_after_the_files_end_spx_and_vix_come_from_the_recorded_dataset(), test_daily_bars_take_the_official_close_from_cboe_and_the_open_from_the_file(), test_describe_pins_the_inputs_and_carries_no_credential(), test_index_bars_serve_the_day_and_nothing_for_a_stale_day() (+7 more)

### Community 123 - "test_weekend_review.py"
Cohesion: 0.14
Nodes (18): previous_mon_fri(), _row(), test_calendar_month_to_date(), test_caption_and_recap_show_paper_and_executable_side_by_side(), test_cash_settled_exit_uses_settlement_value(), test_executable_pnl_is_none_without_recorded_prices(), test_executable_pnl_uses_marketable_entry_and_exit(), test_format_executable_pnl_counts_unpriced_trades() (+10 more)

### Community 124 - "Schwab gateway deployment options"
Cohesion: 0.20
Nodes (9): Explicitly not established here, Option A — Helios, containerized, Option B — zeus, containerized, Option C — a separate/new host, Option D — Helios, as a `systemd --user` service, not containerized, Reading, Schwab gateway deployment options, The one bounded read-only check to ask for next (+1 more)

### Community 125 - "Window H — verification held; the deadline reminder is mistimed (2026-08-08)"
Cohesion: 0.22
Nodes (9): Deliverables, Finding — the weekly reminder fires after the deadline it protects, Still open after Window H, Task 2 — the Monday check is deferred a fourth time, Tasks 3–6 — all green, verified host-against-container, The deadline in local time — stated because the brief did not, The deadline, re-derived from the document, Window H addendum — a keepalive write observed live (2026-08-09 01:00 UTC) (+1 more)

### Community 126 - "_run_with_stub_token"
Cohesion: 0.12
Nodes (7): _run_with_stub_token(), test_token_keepalive_exits_when_the_token_lock_is_held(), test_token_keepalive_honours_schwab_token_path(), test_token_keepalive_refreshes_inside_the_token_lock(), test_token_keepalive_reports_alertmanager_failure(), test_token_keepalive_reports_alertmanager_state(), fake_open()

### Community 127 - "thetadata_download.py"
Cohesion: 0.20
Nodes (12): base_dir(), cboe_sessions(), expirations(), fetch(), file_path(), _get(), LargeRequestError, load_no_data() (+4 more)

### Community 128 - "fly_settlement_value"
Cohesion: 0.10
Nodes (18): Assumptions, Corrected implementation fingerprints, Reproduction commands, Result, Settlement evidence and reconciliation, SPX frozen baseline: cash-settlement correction, fly_settlement_value(), PositionQuotesUnavailableError (+10 more)

### Community 129 - "strategy_page.py"
Cohesion: 0.24
Nodes (13): _json_data_block(), _case_study(), _clock(), _entry_window_et(), _et_after_open(), _minutes_between(), _pct(), _regime_bar() (+5 more)

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
Cohesion: 0.13
Nodes (6): Next Exact Action, _error_code(), _mismatch_code(), _numbers_agree(), ShadowComparingMarketDataProvider, test_direct_result_is_unchanged_when_the_gateway_times_out_in_real_time()

### Community 135 - "Strategy Settings"
Cohesion: 0.25
Nodes (8): 1) Install dependencies, 2) Run the test and lint pass, code:bash (uv sync), code:bash (uv run pytest), 🛠 Configuration, Key Entry Settings, SPX vs NDX vs XSP, Strategy Settings

### Community 136 - "ThetaDataSource"
Cohesion: 0.21
Nodes (3): parse_cboe(), ThetaDataSource, _ymd()

### Community 137 - "run_all_history.py"
Cohesion: 0.21
Nodes (13): all_stresses(), assert_prior_result(), ledger_parity(), main(), paired_comparison(), select_sources(), points(), test_all_scenarios_equal_original_replays() (+5 more)

### Community 139 - "Registration decision package: ThetaData development window (2026-09-29)"
Cohesion: 0.11
Nodes (17): 1. Data and integrity, 2. Baseline E0 (descriptive; do not tune on it), 3. The hypotheses on the development window (in-sample), 4. Holdout size and power, 5. VIX-smoothing sensitivity, 6.1 Stressed exits below zero: decided, now floored (D3, draft Revision 1), 6.2 Gate 1 passed skip filters too often under the null: decided, now calibrated (D4, draft Revision 4), 6.3 A paired pass against a losing baseline: decided, gate 6 added (D2, draft Revision 5) (+9 more)

### Community 141 - "test_daily_report_card.py"
Cohesion: 0.15
Nodes (14): parse_trade_transactions(), candles_to_series(), test_build_daily_report_card_detects_problems(), test_build_equity_trade_chart_png_returns_png_bytes(), test_chartable_equity_trades_skips_options(), test_equity_chart_aggregates_to_two_minute_candles(), test_equity_chart_stats_text_includes_key_fields(), test_equity_chart_window_keeps_6am_premarket_and_regular_session() (+6 more)

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

### Community 149 - "test_backtest_research_integrity.py"
Cohesion: 0.23
Nodes (14): _baseline(), _candidate(), _quotes(), test_cash_settlement_has_entry_commission_but_no_exit_fill_cost(), test_csv_loader_reads_chicago_bar_end_timestamps(), test_csv_loader_rejects_a_day_without_prior_inputs(), test_csv_loader_uses_prior_vix_close_and_preserves_underlying(), test_marketable_accounting_never_uses_a_future_quote() (+6 more)

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

### Community 161 - "SchwabGateway order books"
Cohesion: 0.50
Nodes (3): Live WebSocket, Recent snapshots, SchwabGateway order books

### Community 162 - "test_run_backtest_db.py"
Cohesion: 0.08
Nodes (19): fetch_prev_close(), _fitted_density_counts(), _print_pnl_histogram(), resolve_db_dsn(), _DailyBarConnection, test_entry_window_direction_ma_uses_sma_of_prior_closes(), test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(), fake_vix() (+11 more)

### Community 165 - "spx-prospective-v2-2026-10-02/manifest.json"
Cohesion: 0.12
Nodes (15): asset, cohort_id, config, path, sha256, created_at, database_tables, git (+7 more)

### Community 166 - "ThetaData data-quality plan and validation amendment (2026-09-28)"
Cohesion: 0.13
Nodes (14): Artifacts referenced, Decisions for the owner, P&L replay (report only, 2026-09-29), Phase 1: code (no data pulled), Phase 1 implementation notes (2026-09-28), Phase 2: re-pull the validation window, then check quality, Phase 2 re-run and Phase 3 result (2026-09-28), Phase 2 result (2026-09-28): FAIL on Q4 (+6 more)

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

### Community 177 - "Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)"
Cohesion: 0.29
Nodes (7): End state — verified host-versus-container, 2026-08-09 00:15 UTC, Proven in production, not only in tests, Still open after Window G, The deadline, The fix, What today did *not* prove, Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)

### Community 179 - "2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)"
Cohesion: 0.15
Nodes (10): Option A Live Serving (built offline, never deployed), What the research core needs, 2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only), Descriptive E0 breakdowns (not evidence), Feature sources and coverage, Housekeeping, Pre-registration draft (not registered), Vendor readiness (+2 more)

### Community 180 - "Prospective execution validation — spx-prospective-2026-09-22"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-2026-09-22, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 181 - "evaluate.py"
Cohesion: 0.10
Nodes (22): Fill, TradeFills, block_bootstrap_indices(), common_dates(), EvalParams, evaluate(), evaluate_arm(), paired_bootstrap() (+14 more)

### Community 182 - "Repository Agent Instructions"
Cohesion: 0.22
Nodes (8): Repository Agent Instructions, Profit State Machine, run_live.py Entry Point, Strategy Entry Pipeline, TimescaleDB Trading Tables, Layered Risk Management, VIX-Aware Strategy, XSP Account and Loss Guards

### Community 183 - "Geometric butterfly icon"
Cohesion: 0.25
Nodes (6): BUTTERFLYGUY, Dark navy background, Futuristic uppercase wordmark, Geometric butterfly icon, Neon green accent color, Polygonal connected linework

### Community 185 - "Current Schwab Integration"
Cohesion: 0.18
Nodes (10): Assumptions requiring verification, Configuration, secrets, and deployment assumptions, Current Schwab Integration, Database and messaging dependencies, Discord and operational dependencies, Equity and research paths, Extraction boundaries, Market-data flow (+2 more)

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

### Community 192 - "load_report_gateway_settings"
Cohesion: 0.32
Nodes (3): test_report_gateway_process_values_override_infra_env(), test_report_gateway_settings_load_host_values_from_infra_env(), load_report_gateway_settings()

### Community 193 - "write_history"
Cohesion: 0.08
Nodes (37): Fidelity validation (`validate.py`), The adapter (`history.py`), The holdout evaluation (`protocol.py`, `holdout`; D9, built 2026-09-29), The sealed holdout (`holdout.py`), Vendor history (ThetaData, subscribed 2026-09-28), CostNotApprovedError, excluded_sessions(), HistoryPlan (+29 more)

### Community 194 - "Implementation prompt: finish local ThetaData backtesting support"
Cohesion: 0.15
Nodes (12): Completion checklist, Facts and constraints to carry forward, Implementation prompt: finish local ThetaData backtesting support, Objective, Phase 1 — establish the actual remaining work, Phase 2 — local raw-Parquet source and normalization, Phase 3 — supporting observations and coverage policy, Phase 4 — SPXW 0-DTE integration and execution verification (+4 more)

### Community 195 - "SchwabGateway option-chain latency investigation (2026-09-04)"
Cohesion: 0.22
Nodes (8): 2026-09-09 runtime follow-up, Cache TTL is hard-capped at 4s in code, not just config, Chain size correlation, Recommendation, Request path (cache miss), SchwabGateway option-chain latency investigation (2026-09-04), Where the time actually goes: scheduler queueing, not the Schwab call itself, XSP held-leg event-age correction (2026-09-11)

### Community 196 - "2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)"
Cohesion: 0.25
Nodes (8): 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered), Changes, E0 loses on the development window, Findings about the test itself, Hypotheses, paired with E0 (draft bootstrap: 10-session blocks, 10,000 reps), Integrity, Power (from development vectors; assumes 2022–24 is representative), Recommendation for the owner

### Community 197 - "Prospective execution validation — spx-prospective-v2-2026-10-02"
Cohesion: 0.17
Nodes (11): Accounting models, Coverage, Decision gates, Prospective execution validation — spx-prospective-v2-2026-10-02, Registered endpoint, Sessions, stressed_marketable by direction, stressed_marketable by exit_reason (+3 more)

### Community 198 - "BiasScoreFilter"
Cohesion: 0.08
Nodes (7): BiasScoreFilter, make_bar(), make_pre_entry_bars(), TestBiasScore, TestComputeOr, TestComputeVwap, TestEma

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

### Community 204 - "parse_quotes"
Cohesion: 0.17
Nodes (8): _et_to_utc_us(), parse_quotes(), ThetaDataError, _day_quotes(), _quote_csv(), test_millisecond_timestamps_with_trimmed_zeros_parse(), test_no_data_is_empty_transient_errors_retry_and_large_requests_split(), test_quotes_map_to_utc_and_types_and_a_0_0_row_is_no_quote()

### Community 205 - "ButterflyCandidate"
Cohesion: 0.04
Nodes (42): Models and SDK coupling, _entry_debit(), _exit_credit(), _finite_quote_side(), inspect_quote_market(), price_frozen_trade(), QuoteMarket, snapshot_at_or_before() (+34 more)

### Community 206 - "2026-09-21 — SPX executable-side accounting on the settlement-correct replay"
Cohesion: 0.29
Nodes (7): 2026-09-21 — SPX executable-side accounting on the settlement-correct replay, Accounting models and deterministic data rules, Data provenance and coverage, Exact commands and implementation fingerprints, Frozen result, Pre-registered drawdown limit, Reproduction under the roll-forward exit rule

### Community 207 - "test_research_tieset.py"
Cohesion: 0.15
Nodes (8): draw_keys(), promotion_shift(), selector_pool(), _cand(), test_draws_are_keyed_by_session_and_direction(), test_promotion_shift_is_rr_gap_over_combined_cost_sensitivity(), test_run_scores_tie_sets_unless_told_not_to(), test_selector_pool_applies_center_tolerance_and_rr_max_per_width()

### Community 209 - "resolve_wing_widths_for_vix"
Cohesion: 0.33
Nodes (4): W — widths (decided: apply live after the cohort endpoint), _bucket_sigmas(), resolve_wing_widths_for_vix(), test_two_width_vix_bucket_spans_narrow_and_wide_sigmas()

### Community 210 - "quote_rules"
Cohesion: 0.29
Nodes (7): quote_rules, crossed_market, entry_gap, exit_gap, missing_market, selection, substitution

### Community 212 - "files"
Cohesion: 0.29
Nodes (7): rows, sha256, files, daily_bars.parquet, sessions/2026-07-13/chain.parquet, rows, sha256

### Community 213 - "prospective_execution.py"
Cohesion: 0.08
Nodes (29): append_jsonl(), append_unique(), _breakdown(), build_daily_run_record(), build_manifest(), build_trade_record(), _comparable(), evaluate_endpoint() (+21 more)

### Community 214 - "dev_studies.py"
Cohesion: 0.26
Nodes (6): cmd_calibrate(), cmd_check(), cmd_power(), cmd_random_skip(), load(), main()

### Community 215 - "Historical data management"
Cohesion: 0.25
Nodes (8): Canonical normalized datasets, Current inventory, Historical data management, Next milestones, Refresh and verify, Session quality and exclusion ledger, Sources and ownership, Storage and cleaning conventions

### Community 216 - "FakeConnection"
Cohesion: 0.32
Nodes (4): fake_db(), FakeConnection, test_changed_migration_fails_closed(), test_migration_is_recorded_and_then_skipped()

### Community 217 - "Offline ThetaData research"
Cohesion: 0.20
Nodes (8): Baseline and exposure, Commands, Lifecycles, accounting and limits, Mapping and access, Offline ThetaData research, Verification artifacts, Real private artifacts, ThetaData local implementation verification

### Community 220 - "decision_rules"
Cohesion: 0.22
Nodes (9): decision_rules, checkpoint_trades, early_failure_trades, max_drawdown, max_top3_gross_profit_share, min_executable_entry_coverage, min_profit_factor, primary_hypothesis (+1 more)

### Community 222 - "ThetaData option history (raw)"
Cohesion: 0.29
Nodes (6): Conventions, Layout, Reading, Sealed dates, Sets, ThetaData option history (raw)

### Community 223 - "Cohort automation"
Cohesion: 0.29
Nodes (6): Check on it, Cohort automation, Install, Known limitation: the SSH key, Retired v1, When the cohort closes

### Community 224 - "assumptions"
Cohesion: 0.33
Nodes (6): assumptions, commission_per_contract, contract_multiplier, contracts_per_butterfly, quantity, stressed_leg_slippage

### Community 225 - "test_run_live.py"
Cohesion: 0.05
Nodes (45): clear_readiness(), broker_reconciler_loop(), BrokerStateGate, _close_runtime_resources(), daily_reset_loop(), entry_loop(), _reconcile_broker_state(), token_reload_loop() (+37 more)

### Community 226 - "test_collector.py"
Cohesion: 0.18
Nodes (4): test_collect_snapshot_parses_chain(), test_collect_snapshot_row_fields(), test_collect_snapshot_succeeds_when_chain_cache_write_fails(), test_collect_snapshot_writes_chain_cache_off_event_loop()

### Community 227 - "endpoint"
Cohesion: 0.40
Nodes (5): endpoint, min_cash_settlements, min_stressed_winners, rule, target_trades

### Community 228 - "SchwabGateway order-book release full-session acceptance — 2026-09-01"
Cohesion: 0.14
Nodes (12): Credential lineage, EquityScanner coexistence boundary, Post-close decision, Prepared read-only tools, SchwabGateway order-book release full-session acceptance — 2026-09-01, Scope and freeze boundary, Start the full-session harness (unattended), Tuesday preflight — final gate at 06:20-06:29 PDT (+4 more)

### Community 229 - "export"
Cohesion: 0.40
Nodes (5): export, min_session_snapshots, spot_underlyings, strike_margin, underlying

### Community 230 - "Phases"
Cohesion: 0.15
Nodes (11): Entry-point inventory and fate, Open owner decisions, Phase 0: land what exists, Phase 3: commit the analysis that decisions rest on, Phase 4: link the stages, Phase 5: data upkeep, Phases, Research workflow unification plan — 2026-09-29 (+3 more)

### Community 231 - "Dataset"
Cohesion: 0.07
Nodes (12): Modules, _calibrate_for_registration(), Dataset, DecisionProfile, round_to_seconds(), SessionLoader, SessionFeatures, coverage() (+4 more)

### Community 232 - "test_alertmanager_new_firing_cancels_stale_pending_resolution"
Cohesion: 0.20
Nodes (5): test_alertmanager_failed_resolution_retries_until_accepted(), send_alertmanager(), to_thread(), test_alertmanager_new_firing_cancels_stale_pending_resolution(), test_alertmanager_payload_has_stable_redacted_fingerprint()

### Community 233 - "test_live_performance_report.py"
Cohesion: 0.17
Nodes (14): NoTradeDay, render_report_html(), render_trade_table_rows(), test_chart_payload_includes_drawdown_fields(), test_is_drawdown_exit(), test_performance_report_shows_entire_history_and_fill_model_cohorts(), test_regenerated_data_stays_out_of_executable_script(), render() (+6 more)

### Community 234 - "SPX idea sweep — registry (written 2026-09-25 before any variant was run)"
Cohesion: 0.50
Nodes (3): Round 2 — POST-HOC (written after seeing round-1 results; exploratory only), SPX idea sweep — registry (written 2026-09-25 before any variant was run), Variants

### Community 235 - "record_equity_market_data.py"
Cohesion: 0.21
Nodes (6): async_main(), _install_signal_handlers(), main(), parse_args(), run(), _subscribe()

### Community 236 - "TradeService"
Cohesion: 0.07
Nodes (15): Architecture Map, Current architecture, Dependency map, M1 — The daily-bar refresh marks itself done after a failure, M3 — Runtime reconciler repair leaves an unmonitored, uncounted trade, M5 — Chain parser takes `options[0]` per strike with no root filter (Needs verification), M6 — A restart forgets `_ever_in_profit`, suppressing drawdown exits, M9 — The chain cache rewrites the whole day's JSON on the event loop (+7 more)

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

### Community 241 - "Ernie comparison reconciliation — 2026-10-02"
Cohesion: 0.50
Nodes (4): Completed decision, Distinct datasets and source versions, Ernie comparison reconciliation — 2026-10-02, Provenance and access limits

### Community 242 - "JsonlStreamRecorder"
Cohesion: 0.18
Nodes (4): Streaming, Reusable components, Streaming flow, JsonlStreamRecorder

### Community 243 - "run_live.py"
Cohesion: 0.06
Nodes (15): Interfaces and contracts, get_logger(), start_metrics_server(), canonicalize_schwab_chain_symbol(), CollectorMarketDataProvider, EquityQuoteProvider, MarketMoversProvider, OptionChainProvider (+7 more)

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

### Community 259 - "spot_ticks.parquet"
Cohesion: 0.67
Nodes (3): spot_ticks.parquet, rows, sha256

### Community 261 - "report_broker_order_statuses.py"
Cohesion: 0.27
Nodes (12): _allowed_roots(), _build_payload(), main(), _order_symbols(), _status_category(), _summarize(), test_payload_counts_parent_and_descendant_statuses(), test_payload_excludes_non_spx_orders() (+4 more)

### Community 262 - "docs/README.md"
Cohesion: 0.15
Nodes (5): Reproduce, SPX idea sweep — 2026-09-25, Ernie comparison — historical research record, Reproduce, SPX idea sweep — 2026-09-25

### Community 263 - "SPX paper-trade review — September 12, 2026"
Cohesion: 0.33
Nodes (5): Evidence and scope, Findings, Mechanism worth testing, Research pipeline and proposed experiment, SPX paper-trade review — September 12, 2026

### Community 264 - "ChainDay"
Cohesion: 0.29
Nodes (5): ChainDay, day_with_monitoring_bars(), _bar(), test_day_with_monitoring_bars_adds_live_poll_timestamps(), test_day_with_monitoring_bars_keeps_existing_bar_for_same_timestamp()

### Community 265 - "RunContext"
Cohesion: 0.05
Nodes (43): What the definition hash covers, Hypothesis rules (implemented, not registered), Rules that learn, ATMEntry, baseline_window(), BaselineEntry, BothSides, cached_entries() (+35 more)

### Community 266 - "Registration decision package — 2026-09 (for the owner; nothing is registered)"
Cohesion: 0.25
Nodes (7): Decisions only the owner can make, H-EV1 — skip pre-entry releases (`HEV1`), H-LV1 — skip low-VIX calls (`HLV1`), H-SN1 — σ-normalised selector (`HSN1`), H-TS1 — rich one-day implied (`HTS1`), Optional H-EV2 — skip FOMC statement days (not implemented), Registration decision package — 2026-09 (for the owner; nothing is registered)

### Community 268 - "test_research_accounting.py"
Cohesion: 0.08
Nodes (51): price_trade(), Series, PeakTrailer, fly_quotes(), make_chain(), minute(), _blown_out(), _clock_session() (+43 more)

### Community 297 - "exit_trials/PLAN.md"
Cohesion: 0.40
Nodes (3): Exit trials fixed before execution — September 13, 2026, Executed SPX exit trials, Reproduce

### Community 298 - "CsvDataLoader"
Cohesion: 0.17
Nodes (6): ButterflyGuy data sources — representative samples, External sources, Local durable data, Not data inputs, Repository and runtime inputs, CsvDataLoader

### Community 299 - "GatewayAuthoritativeMarketDataProvider"
Cohesion: 0.08
Nodes (34): _finite_number(), GatewayAuthoritativeMarketDataProvider, GatewayMarketDataError, _nonnegative_integer(), _now_eastern(), _optional_number(), _require_usable_observation(), _same_symbol() (+26 more)

### Community 301 - "All 108 historical entries: executed exit experiments"
Cohesion: 0.33
Nodes (4): All-history extension fixed before execution, All 108 historical entries: executed exit experiments, Outputs, Run locally

### Community 304 - "spx-exits-2026-09-12/manifest.json"
Cohesion: 0.15
Nodes (12): created_utc, entry_prices, exit_commission_points, files, raw/checkout-source-hashes.json, raw/deployment.txt, raw/export.jsonl, raw/monitor.jsonl (+4 more)

### Community 307 - "Reproduce the SPX exit-policy experiment"
Cohesion: 0.22
Nodes (7): Acquisition actually performed, Conditional end-to-end confirmation, Offline reproduction, Output map, Replay rules and costs, Reproduce the SPX exit-policy experiment, SPX exit-policy research — September 12, 2026

### Community 314 - "Ernie (@0DTE) comparison — variant plan (not run)"
Cohesion: 0.17
Nodes (11): Constraints, D — direction, Data route (pending owner decision), E — entry trigger (structural levels), Ernie (@0DTE) comparison — variant plan (not run), Ernie's rules, as stated, Order, Source (+3 more)

### Community 350 - "SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan"
Cohesion: 0.18
Nodes (10): Access, credential and timestamps, Assessment, Endpoints and request plan, Licence (individual plans), Plans and prices (as read), Purchase checklist, SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan, ThetaData: public-docs findings and purchase checklist (2026-09-28) (+2 more)

### Community 351 - "Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)"
Cohesion: 0.29
Nodes (7): B1 — operator chose push-and-pull, with the framing corrected, B3 executed and verified by inode and digest, B3 was not ready — the runbook asserted code that did not exist, B4/B5/B6, Finding — the containers were reading the host's token path, Follow-ups, none blocking, Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

### Community 352 - "._spawn_background"
Cohesion: 0.09
Nodes (17): 1. The latency claim is stale — the comparator does *not* add gateway latency, 2. The no-shadow-surface set is larger than "just history", C3 — wiring shadow reads into `run_live.py`, Implemented steps and remaining operator gate, Prerequisites, in order, Reachability and observability are resolved, Two corrections to the received design points, What C3 does not do (+9 more)

### Community 353 - "2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only), Call-only entry filters, Moving-average direction versus the gap rule, Reproduction, Robustness to fly choice (near-tied flies), Setup and accounting, Why the backtest and live paper disagree

### Community 354 - "test_equity_market_data.py"
Cohesion: 0.27
Nodes (6): symbol_directory(), test_jsonl_recorder_persists_raw_message(), test_subscribe_registers_handlers_before_nyse_services(), test_symbol_directory_is_stable_and_sanitizes_path_characters(), test_symbol_directory_rejects_parent_directory_symbol(), test_write_candle_snapshot_sorts_candles()

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

### Community 365 - "fill_models"
Cohesion: 0.50
Nodes (4): fill_models, corrected_midpoint, marketable, stressed_marketable

### Community 366 - ".history"
Cohesion: 0.29
Nodes (5): Auxiliary inputs (manifest schema 2), Data, Event calendar, Overnight futures (ES): audit only, Existing inputs

### Community 368 - "round2.py"
Cohesion: 0.33
Nodes (8): ev_rank_factory(), r1(), r2(), r5(), ratio_at(), ror(), e0(), k1()

### Community 369 - "research/__init__.py"
Cohesion: 0.33
Nodes (5): _append(), test_catalog_fails_on_a_broken_chain(), test_catalog_lists_hashes_registries_and_counts(), test_history_counts_events_for_the_exact_definition(), test_history_of_a_port_includes_its_placeholder()

### Community 370 - "H-TR1 registration — trail armed at +75% with a breakeven floor"
Cohesion: 0.25
Nodes (8): Data, Entries (frozen, unchanged from the 09-25 harness replica), H-TR1 registration — trail armed at +75% with a breakeven floor, Hypothesis, Pass criteria (all must hold; stressed accounting; per one-lot), Reported but not gating, Result (run once, 2026-10-01, at b0b7215), Run

### Community 371 - "_redacted_order_audit"
Cohesion: 0.46
Nodes (6): _order(), test_redacted_audit_excludes_other_underlyings(), test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes(), test_redacted_audit_treats_replaced_as_historical_terminal(), main(), _redacted_order_audit()

### Community 372 - "os"
Cohesion: 0.10
Nodes (4): check(), dump(), main(), main()

### Community 373 - "2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)"
Cohesion: 0.29
Nodes (7): 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only), Cohort runner move (2026-09-27) and a labeling note, Cohort shadow (exploratory, three sessions), Exit-latency stress, Parity, Research core and data, Variant registry

### Community 374 - "test_collector_daily_bars.py"
Cohesion: 0.52
Nodes (5): _collector(), _daily_candle(), test_daily_bars_failure_leaves_refresh_pending_and_retries(), test_daily_bars_skip_todays_in_progress_candle(), test_daily_bars_use_eastern_session_date_not_host_date()

### Community 375 - "2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)"
Cohesion: 0.33
Nodes (6): 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered), Consequences, Decision and change, Still open, The calibration study (scratch, development data), What it gives on the real dataset (in-process, nothing registered)

### Community 376 - "2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)"
Cohesion: 0.33
Nodes (6): 2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only), Data and harness, Hypothesis for a future test (not applied), Post-hoc middle ground (defined after the table above), Pre-declared variants (written before running), Reproduction

### Community 377 - "Implementation prompt: SPX session quality and exclusion ledger"
Cohesion: 0.25
Nodes (7): Boundaries, Deliverable and scope, Implementation prompt: SPX session quality and exclusion ledger, Ledger behavior, Read first and establish the checkout, Reconciliation targets, Verification and completion criteria

### Community 378 - "select_pm_settled_rows"
Cohesion: 0.29
Nodes (3): _is_pm_settled(), select_pm_settled_rows(), select_strike_contract()

### Community 379 - "2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0"
Cohesion: 0.40
Nodes (5): 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0, Decisions, How the floor is implemented (`7b1f229`), Re-run under the floor, Still open

### Community 381 - "simulate.py"
Cohesion: 0.08
Nodes (15): Status and scope, Costs, ExitRule, fit_variant_entry(), History, is_fitted(), is_learning(), delayed_exit_index() (+7 more)

### Community 382 - "backfill_equity_candles.py"
Cohesion: 0.39
Nodes (4): async_main(), main(), parse_args(), run()

### Community 384 - "report_selection_parity.py"
Cohesion: 0.38
Nodes (3): main(), parse_args(), run()

### Community 385 - "Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)"
Cohesion: 0.33
Nodes (6): Fixed by binding the directory, and by a second defect that fix exposed, Still open, The finding — the always-on gateway had orphaned all three trading containers, Verified, by inode and digest and by an actual atomic replace, Window E addendum — the candidate fleet's orphaned token, fixed (2026-08-08), Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)

### Community 388 - "2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)"
Cohesion: 0.40
Nodes (5): 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered), Consequences for H-TS1 alone (k = 1), Decision and change, Still open, Study before the decision

### Community 391 - "SPXW session quality evidence ledger — 2026-10-02"
Cohesion: 0.50
Nodes (4): Interpretation, Private artifacts and reconciliation, Reproduce offline, SPXW session quality evidence ledger — 2026-10-02

### Community 392 - "2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data)"
Cohesion: 0.50
Nodes (4): 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data), Housekeeping, Registration decision package (nothing registered), Tooling hygiene

### Community 393 - "2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered)"
Cohesion: 0.50
Nodes (4): 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered), Decision and change, Results, Still open

## Ambiguous Edges - Review These
- `central cyan glow` → `technology visual association`  [AMBIGUOUS]
  data/images/butterflyguy_logo2.png · relation: suggests

## Knowledge Gaps
- **1083 isolated node(s):** `created_utc`, `range`, `trades`, `provider`, `original_acquisition_utc` (+1078 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2596 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **122 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `central cyan glow` and `technology visual association`?**
  _Edge tagged AMBIGUOUS (relation: suggests) - confidence is low._
- **Why does `SchwabClientWrapper` connect `SchwabClientWrapper` to `report_broker_order_statuses.py`, `butterfly_gateway_acceptance.py`, `main`, `MinuteBar`, `Codex Project State`, `_assert_broker_state_matches_db`, `Schwab Gateway Migration Plan`, `PositionService`, `OrderManager`, `2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)`, `Branch Review and Integration Plan`, `ButterflyCandidate`, `test_schwab_client.py`, `services/daily_report_card.py`, `Capability recorder design`, `test_run_live.py`, `record_equity_market_data.py`, `TradeService`, `JsonlStreamRecorder`, `run_live.py`, `_redacted_order_audit`, `backfill_equity_candles.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `ButterflyCandidate` connect `ButterflyCandidate` to `fly_settlement_value`, `run_paper_replay.py`, `test_order_manager.py`, `trade_chart.py`, `simulation_engine.py`, `RunContext`, `test_research_accounting.py`, `StrategySettings`, `test_backtest_research_integrity.py`, `reports/daily_report_card.py`, `main`, `run_backtest_db.py`, `MinuteBar`, `PositionService`, `test_prospective_execution.py`, `OrderManager`, `test_position_monitoring.py`, `config.py`, `test_order_preview.py`, `test_research_tieset.py`, `prospective_execution.py`, `test_run_live.py`, `SimulationEngine`, `ButterflyOrderBuilder`, `TradeService`, `run_live.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `Options strategy discovery journal` connect `Options strategy discovery journal` to `2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)`, `docs/README.md`, `2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data)`, `2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered)`, `2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)`, `Manifest`, `2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)`, `2026-09-21 — prospective execution-validation cohort (pre-registration)`, `2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)`, `2026-09-21 — SPX executable-side accounting on the settlement-correct replay`, `2026-07-14 — data audit and research design`, `2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)`, `2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)`, `2026-09-20 — SPX cash-settlement parity correction`, `2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)`, `2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)`, `2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)`, `2026-10-01 — trail start and breakeven floor (Ernie @0DTE comparison; development data only)`, `2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 71 inferred relationships involving `Dataset` (e.g. with `cmd_cache_inputs()` and `cmd_import()`) actually correct?**
  _`Dataset` has 71 INFERRED edges - model-reasoned connections that need verification._
- **Are the 57 inferred relationships involving `ButterflyCandidate` (e.g. with `Models and SDK coupling` and `6. Canonical and derived analytical data types`) actually correct?**
  _`ButterflyCandidate` has 57 INFERRED edges - model-reasoned connections that need verification._
- **Are the 46 inferred relationships involving `RunContext` (e.g. with `AppConfig` and `EventDaySkipEntry`) actually correct?**
  _`RunContext` has 46 INFERRED edges - model-reasoned connections that need verification._