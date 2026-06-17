
  # ButterflyGuy Fable 5 Rebuild Plan

  ## Summary

  Use a long-lived rebuild branch in a separate Git worktree, created from updated origin/main, while keeping the current
  repo as the behavioral and data reference. Do not fork as the main strategy unless remote-level isolation becomes
  necessary.

  The rebuild should be a new product-shape trading platform core: live-capable, but gated; open to a new tech stack;
  clean-room implementation; and read-compatible with the existing TimescaleDB data so current historical option-chain
  data remains usable for backtesting.

  ## Git Process

  - Preserve current local state before doing anything:
      - Local main is currently behind origin/main by 15 commits.
      - Local uncommitted files exist: .github/workflows/deploy.yml and .claude/settings.local.json.
  - Create the rebuild from origin/main, not stale local main.
  - Recommended shape:
      - Branch: fable5/rebuild-core
      - Worktree: sibling directory such as ../ButterflyGuy-fable5
      - Current repo remains the reference implementation and database schema source.
  - Merge finished slices back through PRs only after tests/backtests pass.

  ## Fable Context Package

  Create docs/fable5/ as the handoff package:

  - REBUILD_BRIEF.md
      - Product intent: automated 0-DTE SPX/NDX/XSP butterfly trading platform.
      - Core modes: paper trading, gated live trading, backtesting, research inspection, reporting.
  - DOMAIN_MODEL.md
      - Underlyings, option chains, spots, daily bars, butterfly candidates, trades, fills, marks, risk state, decision
        logs, regimes.
  - DATABASE_COMPATIBILITY.md
      - Existing TimescaleDB schema treated as an external data contract for historical reads.
      - Required first-milestone read tables: option_chain_snapshots, spot_prices, daily_bars.
      - Runtime writes should go to rebuilt/namespaced tables first, not the current production tables.
  - BEHAVIORAL_SPEC.md
      - Entry window, direction logic, VIX anchoring, width selection, candidate filtering, paper fill convention, exit
        state machine, risk gates.
  - ACCEPTANCE_TESTS.md
      - Behavior-level tests derived from current repo tests and configs, without copying implementation.

  ## Implementation Guidance For Fable

  - Treat the current Python repo as reference behavior only, not source to copy.
  - Fable may choose a new stack, but it must preserve these external capabilities:
      - Read historical data from existing TimescaleDB tables for backtests.
      - Replay option chains from option_chain_snapshots by underlying, expiration, and timestamp.
      - Use spot_prices and daily_bars for spot/VIX/regime/backtest context.
      - Keep Schwab market data and order integration behind explicit boundaries.
      - Use mark price (bid + ask) / 2 for paper fills.
      - Log decisions and risk blocks in the rebuilt system’s own persistence layer.
  - Live trading must be gated:
      - Default mode is non-live.
      - Live order placement requires explicit config.
      - Account, buying-power, and risk guards must pass.
      - No token values or secrets appear in generated docs, logs, or commits.

  ## Database Interoperability

  - First milestone is read compatibility, not full schema replacement.
  - The rebuild must include a DB adapter that can query:
      - option_chain_snapshots: historical option chains, quotes, greeks, symbols, spot-at-snapshot.
      - spot_prices: underlying/VIX spot history.
      - daily_bars: daily OHLCV for regime and prior-close context.
  - Current historical data must be backtestable without migration.
  - New runtime state should initially write to new or namespaced tables to avoid corrupting existing butterfly_trades,
    daily_risk_state, decision_log, or candidate records.
  - Full same-schema write compatibility can be considered later after the rebuilt system proves parity.

  ## Test Plan

  - First milestone:
      - Connect to existing TimescaleDB.
      - Load one historical SPX day from option_chain_snapshots.
      - Load matching spot and daily bar context.
      - Run a deterministic backtest/replay without modifying current tables.
  - Acceptance coverage should include:
      - Candidate construction and selection.
      - VIX width/center behavior.
      - Gap/regime direction behavior.
      - Paper fill pricing.
      - Profit state machine exits.
      - Daily trade count and loss-limit blocking.
      - Backtest/live parity for shared strategy decisions.
  - Before any live-capable branch merges:
      - Unit tests pass.
      - DB-backed backtest smoke test passes on existing data.
      - Paper/replay mode proves end-to-end flow.
      - Live mode remains disabled by default.

  ## Assumptions

  - The rebuild should be clean-room: no implementation copying from the current repo.
  - Branch + worktree is the default Git strategy.
  - Existing historical DB data is valuable and must remain directly usable.
  - The first DB compatibility target is read-only access to chains, spot prices, and daily bars.
  - New runtime writes should avoid the current production tables until compatibility is deliberately promoted.
  -
  -
  
  
  
  
  
  
  
  Execution notes
  
  5. Execution Strategy for Fable 5

When you feed this package to the agent, don't ask it to build the entire app in a single prompt. Take advantage of its structured tool usage by directing it to build system slices in a strict topological order:

    Phase 1: Database Adapter & Historical Ingestion Layer (Must pass basic read validation).

    Phase 2: Mathematical Context & Candidate Selection Engine (Wing width logic and VIX anchoring).

    Phase 3: Paper Execution Engine & State Machine (Property-based validation using simulated data streams).

    Phase 4: Gated Live Integration Broker Framework.

Instruct the model to write its own comprehensive property-based test suite for Phase 2 and 3 before it moves on to integration. Fable 5 has a native capacity for proactive self-verification and will happily run its own testing loop to verify that candidate filters behave flawlessly against edge-case inputs.  

Are you leaning toward keeping the core in Python to ensure frictionless database adapter reuse, or are you considering a system-level language shift (like Rust) to squeeze the absolute minimum latency out of your 0-DTE execution loop?
