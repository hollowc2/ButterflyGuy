# ButterflyGuy Fable 5 Refactor Plan

This file is the entry point for the Fable 5 refactor package. Feed it first, then feed
the companion documents in the order below. The goal is not to copy the current Python
implementation. The goal is to build a clean, live-capable trading platform core that
preserves the current system's market-data contracts and verified trading behavior.

## Document Map

Read these files as one continuous package:

1. `FABLE_REFACTOR_PLAN.md`
   - Defines the rebuild objective, sequencing, safety constraints, and acceptance
     milestones.
2. `DATABASE_COMPATIBILITY.md`
   - Defines the existing TimescaleDB read contract for historical replay and
     backtesting. This is the first implementation dependency.
3. `DOMAIN_MODEL.md`
   - Defines the canonical domain objects, broker symbol details, ingestion boundaries,
     and strict typing target for Fable.
4. `BEHAVIORAL_SPEC.md`
   - Defines strategy selection, paper-fill conventions, exit behavior, lifecycle
     states, quote-quality gates, and live-trading safety requirements.
5. `CONFIG_MATRIX.md`
   - Defines the current SPX, NDX, and XSP profile differences that Fable must preserve
     or intentionally change with tests.
6. `ACCEPTANCE_TESTS.md`
   - Defines the phase gates, fixture package, golden replay requirements, and behavior
     map for the rebuilt system.
7. `FIXTURE_MANIFEST.md`
   - Defines the deterministic fixture identifiers, config hashes, selected candidates,
     and golden replay cases that prevent abstract parity tests from drifting away from
     observed SPX, NDX, and XSP behavior.

Use `DATABASE_COMPATIBILITY.md` before `DOMAIN_MODEL.md` because the first Fable
milestone must prove it can read existing historical data without mutating production
tables. Use `BEHAVIORAL_SPEC.md` after the model is in place because behavior should be
implemented against typed domain objects and explicit data adapters. Use
`CONFIG_MATRIX.md` when implementing profile loading and per-asset behavior. Use
`FIXTURE_MANIFEST.md` when building deterministic tests. Use `ACCEPTANCE_TESTS.md` as
the definition of done for each phase.

## Refactor Objective

Build a new ButterflyGuy platform core for automated 0-DTE SPX, NDX, and XSP butterfly
trading with these modes:

- Historical database replay and backtesting.
- Paper trading with realistic mark, bid/ask, spread, and fill rules.
- Research inspection and reporting.
- Gated live trading, disabled by default.

The rebuilt system must be read-compatible with the existing TimescaleDB market-data
tables so current option-chain, spot, and daily-bar history remains usable immediately.
New runtime writes should initially use new or namespaced tables until write
compatibility is deliberately designed and tested.

## Non-Negotiable Constraints

- Treat the current repo as a behavioral reference, not source code to copy.
- Do not place broker orders during the refactor.
- Default execution mode must be non-live.
- Live routing must require explicit config approval plus an explicit environment
  confirmation, checked immediately before every broker order submission.
- Do not print, commit, or summarize Schwab tokens, account ids, or secret values.
- Paper fills use the project convention of mark price `(bid + ask) / 2`, with the
  spread-quality refinements defined in `BEHAVIORAL_SPEC.md`.
- Historical backtests must be deterministic for a fixed DB snapshot and config.
- Existing production tables must not be mutated by early Fable milestones.

## Recommended Git Process

Use a long-lived rebuild branch in a separate Git worktree:

- Branch: `fable5/rebuild-core`
- Worktree: sibling directory such as `../ButterflyGuy-fable5`
- Base: updated `origin/main`
- Current repo: reference implementation and schema source

Merge finished slices back through pull requests only after tests and DB-backed smoke
checks pass. Keep each slice small enough to review independently.

## Implementation Phases

### Phase 1: Database Adapter And Historical Ingestion

Primary reference: `DATABASE_COMPATIBILITY.md`

Build a read-only adapter for:

- `option_chain_snapshots`
- `spot_prices`
- `daily_bars`

Required outcomes:

- Connect to existing TimescaleDB.
- Load one historical SPX 0-DTE chain by underlying, expiration, and snapshot time.
- Load nearest-at-or-before spot and daily-bar context.
- Convert row-oriented option-chain data into typed in-memory quote objects.
- Prove the adapter does not write to current production tables.

Acceptance checks:

- A deterministic replay fixture can load the same chain twice with identical typed
  output.
- Nullable quote fields, Decimal precision, timestamp zones, and row-oriented chain
  shape are handled explicitly.
- Fable does not assume the database has JSON chain blobs, `id`, or `chain_data`
  columns.

### Phase 2: Domain Model And Candidate Selection

Primary references: `DOMAIN_MODEL.md`, `CONFIG_MATRIX.md`, then the strategy sections
in `BEHAVIORAL_SPEC.md`

Build the typed domain layer and deterministic butterfly selection engine:

- `OptionContract`
- `ButterflySpread`
- `ButterflyCandidateModel`
- trade and lifecycle records
- chain snapshot and replay context objects
- VIX width bucket and target-center behavior
- optional dynamic-width policy only if it is explicit and test-covered

Required outcomes:

- Preserve SPX, NDX, and XSP strike-grid and symbol-root behavior.
- Keep broker mark, computed mid, and model valuation fields separate.
- Reject malformed quotes and missing legs before ranking candidates.
- Keep research/audit modes separate from normal backtest and paper execution modes.

Acceptance checks:

- Candidate construction is symmetric unless an explicit asymmetric mode exists.
- CALL centers are above spot and PUT centers are below spot.
- Reward/risk, debit floor, width cost ceiling, and complete-leg constraints are tested.
- Property-based tests cover bad quotes, missing strikes, zero/negative costs, invalid
  VIX values, and DTE edge cases.

### Phase 3: Paper Execution And Position State Machine

Primary reference: `BEHAVIORAL_SPEC.md`

Build the paper execution engine and lifecycle model:

- Mark-based paper entry and exit fills.
- Bid/ask spread penalty and hard-block policy.
- Profit regime classification.
- Peak tracking and drawdown exit confirmation.
- Explicit trade lifecycle states.
- Cash-settlement path for cash-settled index positions.
- SPX, NDX, and XSP profile-specific quote-quality and timing behavior.

Required outcomes:

- Profit regime and order lifecycle are modeled as separate concerns.
- Exit attempts are idempotent and retryable.
- `CLOSED` is terminal.
- Paper execution cannot call broker order-placement code.

Acceptance checks:

- State-machine tests cover `LOSS`, `NEAR_LONG`, and `PROFIT_TENT`.
- Lifecycle tests cover `OPEN_MONITORING`, `EXIT_SIGNALLED`, `EXITING`,
  `EXIT_FAILED_RETRYABLE`, `CASH_SETTLING`, and `CLOSED`.
- Spread-quality tests prove warning penalties, hard blocks, forced exits, and audit
  fields.
- Backtest, replay, and live-paper paths use the same fill-quality policy.

### Phase 4: Gated Broker Integration

Primary reference: the double-factor live gating section in `BEHAVIORAL_SPEC.md`

Build the live broker boundary after the paper/replay system is stable:

- Separate paper and live execution modules behind a narrow execution interface.
- No shared code path that lets paper mode place Schwab orders.
- Config gate plus exact environment confirmation.
- Gate checked at construction time and immediately before each `place_order` call.
- Typed failure for missing or malformed approvals.

Acceptance checks:

- Config-only approval fails.
- Environment-only approval fails.
- Typo approval fails.
- Paper mode cannot import or call live order placement.
- Live mode can submit only when both independent approvals are present.

## System Acceptance Path

The rebuild is usable only after these checks pass in order:

1. Read-only DB adapter smoke test passes on existing SPX data.
2. Typed domain conversion passes for SPX, NDX, and XSP sample chains.
3. Candidate selection produces deterministic results for fixed chain, spot, VIX, and
   config inputs.
4. Paper execution records realistic fills or explicit fill blocks.
5. Open-position monitoring can replay mark updates and exit signals without broker
   writes.
6. Runtime writes go only to rebuilt or namespaced tables.
7. Live mode remains disabled by default.

`ACCEPTANCE_TESTS.md` is the authoritative checklist for the full acceptance suite and
golden replay package.

## Fable Prompting Guidance

Do not ask Fable to build the entire application in one pass. Give it this package and
instruct it to implement one phase at a time, writing tests before moving to the next
phase.

Suggested first prompt:

```text
Use FABLE_REFACTOR_PLAN.md as the project entry point. Start Phase 1 only.
Read DATABASE_COMPATIBILITY.md, ACCEPTANCE_TESTS.md, CONFIG_MATRIX.md, and
FIXTURE_MANIFEST.md. Implement a read-only historical data adapter for
option_chain_snapshots, spot_prices, and daily_bars. Do not implement strategy,
execution, live broker routing, runtime writes, or Schwab order code yet. Add
deterministic tests for exact snapshot loading, nearest-at-or-before spot lookup,
timestamp/timezone handling, row-oriented option-chain loading, Decimal conversion,
nullable columns, and read-only enforcement for SPX, NDX, and XSP fixtures. Use
ACCEPTANCE_TESTS.md Phase 1 as the gate.
```

Suggested second prompt after Phase 1 passes:

```text
Phase 1 is complete. Now read DOMAIN_MODEL.md and the candidate-selection sections
of BEHAVIORAL_SPEC.md, plus CONFIG_MATRIX.md for asset profiles. Implement typed
immutable domain objects and deterministic candidate construction against the Phase 1
adapter output. Add property-based tests for invalid quotes, missing legs, bad VIX
inputs, DTE floors, reward/risk bounds, and asset-specific strike grids. Use
ACCEPTANCE_TESTS.md Phase 2 as the gate.
```

Suggested third prompt after Phase 2 passes:

```text
Phase 2 is complete. Now read BEHAVIORAL_SPEC.md in full. Implement paper execution,
profit-regime classification, peak tracking, drawdown exits, lifecycle states, and
cash settlement. Do not implement live broker routing yet. Add tests for state
transitions, spread-quality penalties, hard fill blocks, idempotent exits, and
CLOSED as a terminal state. Use CONFIG_MATRIX.md for SPX, NDX, and XSP profile
differences, and use ACCEPTANCE_TESTS.md Phase 3 and Phase 4 as the gate.
```

Suggested fourth prompt after Phase 3 passes:

```text
Phase 3 is complete. Implement the live broker boundary only. Keep paper and live
execution separated behind a narrow interface. Require config approval plus the
exact environment confirmation before any broker order submission, and verify both
immediately before every place_order call. Add tests proving all partial approval
cases fail closed. Use ACCEPTANCE_TESTS.md Phase 5 as the gate.
```

## Closed Design Decisions

These decisions are fixed for the first Fable implementation pass:

- Phase 1-3 target language and runtime: Python, to minimize friction with the current
  DB adapter, Decimal, Pydantic-style config, and pytest ecosystem.
- Property-based testing framework: Hypothesis.
- Dynamic wing-width selection: deferred until the current configured VIX bucket
  behavior is reproduced by deterministic SPX, NDX, and XSP fixtures.
- Early runtime writes: use a new namespace/schema in the existing database, not the
  current production tables. Early milestones should remain read-only until that write
  namespace is deliberately designed and tested.

## Completion Definition

The refactor package has done its job when a new agent can start from this file, follow
the linked documents in order, build the platform in phases, and prove each phase with
tests before any live-capable broker code exists.
