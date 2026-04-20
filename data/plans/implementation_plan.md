# Butterfly Guy — Implementation Plan

## Context

Automated 0-DTE butterfly options trading system targeting SPX/XSP via Charles Schwab API.

---

## Phase 1: Infrastructure + TimescaleDB + Option Chain Collector

- [x] Step 1.1: Project Scaffolding (pyproject.toml, config.yaml, uv init)
- [x] Step 1.2: Core Module (config, logging, time_utils, metrics)
- [x] Step 1.3: Database Layer (connection, migrations, queries)
- [x] Step 1.4: Schwab Client Wrapper
- [x] Step 1.5: Option Chain Collector
- [x] Step 1.6: Docker Infrastructure
- [x] Step 1.7: Collector Entry Point
- [ ] Phase 1 Verification

## Phase 2: Butterfly Scanner

- [x] Step 2.1: Butterfly Construction Engine (O(N*W) algorithm)
- [x] Step 2.2: Direction Filter
- [x] Step 2.3: Butterfly Selector
- [ ] Phase 2 Verification

## Phase 3: Paper Trading Execution

- [x] Step 3.1: Order Builder
- [x] Step 3.2: Order Manager
- [x] Step 3.3: Risk Engine
- [x] Step 3.4: Trade Service
- [ ] Phase 3 Verification

## Phase 4: Profit Management State Machine

- [x] Step 4.1: Position Manager
- [x] Step 4.2: Profit State Machine
- [x] Step 4.3: Position Monitor Loop
- [ ] Phase 4 Verification

## Phase 5: Synthetic Engine + Backtesting

- [x] Step 5.1: Black-Scholes Engine
- [x] Step 5.2: IV Model
- [x] Step 5.3: Synthetic Chain Generator
- [x] Step 5.4: Backtest Data Loader
- [x] Step 5.5: Simulation Engine
- [x] Step 5.6: Parameter Sweeper
- [ ] Phase 5 Verification

## Phase 6: Dashboard + Monitoring + Discord

- [x] Step 6.1: Grafana Dashboards
- [x] Step 6.2: Discord Notifications
- [x] Step 6.3: Main Entry Point
- [ ] Phase 6 Verification
