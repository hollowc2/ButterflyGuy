# Schwab Gateway Migration Plan

## Safety envelope

All foundation work occurs on branch `codex/schwab-gateway-foundation` in the isolated
worktree `/tmp/butterfly-schwab-gateway`. The original checkout contains uncommitted
deployment/monitoring changes and is not modified. No Schwab request, Docker service action,
database write, callback, token read, or order command is part of this work.

Production defaults remain direct. A gateway is never selected implicitly, and direct and
gateway paths must never both submit an order.

## Dependency map

```text
SchwabClientWrapper
├── OptionChainCollector -> Chain/Spot/DailyBar queries -> TimescaleDB
├── TradeService -> selection + RiskEngine -> OrderManager
├── PositionService -> PositionManager/ProfitStateMachine -> OrderManager
├── OrderManager -> order builder + broker_order_intents
├── broker reconciliation -> positions/orders/transactions
├── morning/universe/report scripts
└── StreamClient (raw client escape)

Candidate ReadOnlySchwabMarketDataClient
└── CandidateFeed aiohttp -> HttpMarketDataProvider -> evaluators

SchwabDataLoader / keepalive / auth_init
└── independent token-file ownership
```

The first production consumer boundary is `OptionChainCollector`: it is market-data-only
and has focused fake-backed tests. `TradeService`, `PositionService`, and `OrderManager`
mix market/account/order behavior and are deferred until narrow providers can be injected
without changing safety behavior.

## Proposed provider interfaces

- `SpotPriceProvider.get_spot_price(symbol) -> float`
- `OptionChainProvider.get_option_chain(symbol, expiration) -> dict`
- `PriceHistoryProvider.get_intraday_bars(...)` and `get_daily_bars(...)`
- composite `CollectorMarketDataProvider` for the collector only
- `DirectSchwabMarketDataProvider`, a pure delegation adapter around the existing wrapper
- `GatewayMarketDataClient.get_quotes(symbols) -> QuoteResponseV1` for the initial proof

Account and order protocols are intentionally absent from the foundation. The existing
wrapper and order manager remain unchanged.

## Phase 0 — audit and documentation

Dependencies: repository/graph/source access only.

Deliverables:

- current integration map;
- target architecture and decisions;
- capability matrix/recorder design;
- risk register and migration/rollback plan;
- resumable `CODEX_STATE.md`.

Acceptance:

- every SDK construction, token reader/writer, account/order path, streaming path, retry
  policy, deployment secret mount, and existing provider precedent is mapped to source;
- verified facts and assumptions are distinguished;
- no runtime behavior changes.

Rollback: documentation deletion only; no runtime state exists.

## Phase 1 — provider boundary

Dependencies: Phase 0 and focused baseline tests.

Deliverables:

- narrow read-only protocols;
- exact delegation direct adapter;
- collector constructor depends on the composite protocol;
- runtime passes a direct adapter while all account/order consumers retain the wrapper;
- tests prove delegated arguments/results and unchanged collector outputs.

Acceptance:

- direct remains the only production mode/default;
- no strategy, risk, execution, schedule, or order payload change;
- existing collector, trade, position, order, and reconciliation tests pass;
- no SDK object reaches newly normalized gateway models.

Rollback: pass `SchwabClientWrapper` directly again (it structurally satisfies the
transitional protocol) and remove adapter construction. No data migration is involved.

## Phase 2 — minimal read-only gateway

Dependencies: Phase 1 interfaces and internal-key file provisioned for local proof.

Deliverables:

- `butterfly_guy.schwab_gateway` aiohttp app;
- liveness/readiness and one authenticated `GET /v1/quotes` endpoint;
- normalized Pydantic v1 quote contract with nullable missing data;
- SHA-256 API-key verifier and `market_data:read` capability;
- httpx gateway client with explicit timeout and error classes;
- replaceable quote upstream plus fake-backed end-to-end HTTP test;
- isolated local/Compose instructions and placeholder env/key examples.

Acceptance:

- client -> actual in-process HTTP server -> gateway -> fake upstream returns a typed quote;
- missing/invalid key is 401 and wrong capability is 403;
- missing bid/ask stays null with quality flags;
- upstream timeout/unavailable/malformed data is explicit;
- route table contains no account/order route; order writes cannot be enabled;
- current live Compose/defaults are unchanged;
- no client in the integration test reads Schwab credentials.

Rollback: stop the isolated gateway process/project. ButterflyGuy remains direct and no
configuration/default points to the gateway.

## Phase 3 — shadow comparison

Dependencies: production-capable single token manager, safe gateway deployment, capability
probe approval, read-only consumer key.

Compare direct and gateway reads for quotes, history, and option-chain metadata. Record
timestamps, latency, normalized errors, and field-level discrepancies with secrets removed.
Never shadow order submissions or account calls.

Acceptance:

- differences are classified (timing, cache, parsing, upstream);
- representative identical normalized inputs produce identical selection/position/risk
  decisions and semantically identical order intents;
- token refresh and gateway outage drills are documented.

Rollback: disable `SCHWAB_GATEWAY_SHADOW_READS`; direct path is untouched.

## Phase 4 — read-only cutover

Dependencies: successful shadow period and at least one complete session checklist.

Move spot/history/chain reads by narrow provider, not all at once. Default changes only in a
separately approved deployment. Retain direct rollback but prevent automatic dual-order use.

Acceptance:

- one complete session has fresh collector, entry, monitoring, and settlement evidence;
- selection/entry/exit/risk decisions match expected behavior;
- only gateway has Schwab market-data credentials in gateway-mode deployment;
- alerting and readiness cover gateway loss and auth degradation.

Rollback condition: stale/missing data, unexplained discrepancies, token/auth degradation,
latency that jeopardizes two-second monitoring, or any decision divergence. Operator selects
`SCHWAB_ACCESS_MODE=direct` and restarts only after confirming no in-flight orders.

## Phase 5 — shared streaming

Dependencies: measured Schwab capability/limits and chosen event distribution.

Deliver one upstream connection, reference-counted subscriptions, reconnect/resubscribe,
stale health, normalized events, redacted raw recording, and consumer isolation. Add Redis
Streams only if multiple durable consumers/replay are required.

Rollback: stop internal consumers and use current polling/direct recorder; no order impact.

## Phase 6 — account and order mediation

Requires explicit user authorization. Perform account reads, order reads, and writes in
separate steps. Preserve durable intents, no-submit-retry, fill validation, reconciliation,
kill switch, dry-run, and live safety gates. An order-write key is distinct from all market
keys, and gateway order writes default false.

Acceptance includes correlation IDs, unknown-state reconciliation, complete audit records,
manual rollback drill, and proof that no direct/gateway duplicate submit is possible.

Rollback condition: any unknown broker state, reconciliation mismatch, duplicate risk,
permission bypass, or audit gap. Disable writes and retain the gateway for reads only.

## Phase 7 — AfterHoursLab enablement

Dependencies: stable read contracts and recorded after-hours capability matrix.

Add scoped batch quotes/history, capability recorder, candidate promotion design,
Timescale schemas, normalized scanner events, and later Discord bot. No account/order
permissions are issued to scanner, recorder, notebook, or Discord identities.

## Regression strategy

Before changing transport, preserve these suites:

- `test_schwab_client.py`: auth failure, identifier redaction, submit exactly once;
- `test_order_manager.py`: mark/ladder behavior, intent-before-submit, ambiguity/cancel;
- `test_trade_service.py`: stale data, selection, terminal entry behavior;
- `test_position_service_settlement.py`: settlement and no resubmit;
- `test_broker_order_intents.py` and `test_run_live.py`: reconciliation;
- `test_risk_engine.py`, `test_entry_selection*.py`, `test_exit_mark_parity.py`, and
  `test_simulation_parity.py`: unchanged decisions;
- candidate provider/feed/snapshot suites: existing deployed boundary remains intact.

Golden recorded inputs are required before consolidating the duplicated option-chain
parsers. That consolidation is not part of the foundation.

## Risk register

| Risk | Severity | Foundation treatment |
|---|---|---|
| concurrent token refresh/file overwrite | critical | Document; do not add another production writer; design single manager for later cutover. |
| duplicate order submission | critical | No gateway order routes; direct default; no shadow writes. |
| missing quote interpreted as zero | high | Nullable v1 model and explicit quality flags. Preserve legacy parser behavior until golden tests. |
| credentials spread to consumers | high | Fake proof; scoped key contract; later only gateway gets Schwab mounts. |
| unauthenticated internal HTTP | high | Authentication/capability check from first generic endpoint. |
| live deployment interference | high | Separate worktree, branch, Compose overlay/project; no existing Compose edits/actions. |
| raw exception/response leakage | high | Normalized errors and redaction helper; never return upstream payloads. |
| gateway latency/outage during monitoring | high | Timeouts, fail-closed client, shadow measurement, direct operator rollback. |
| SDK token semantics uncertain | high | Capability/auth probes before token-manager cutover. |
| stream limits/reconnect uncertain | medium | Capability recorder; defer broker. |
| new Redis operational burden | medium | Defer until durable fan-out is required. |
| Docker context includes secrets | high | Add `.dockerignore`; keep secret mounts out of image layers. |

## Rollback runbook

Foundation rollback:

1. Do not merge/change any deployment default.
2. Stop only the isolated gateway process/Compose project.
3. Confirm existing containers were never recreated and remain on their prior image/SHA.
4. Keep `SCHWAB_ACCESS_MODE=direct`; unset gateway URL/key variables in the test shell.
5. Run focused direct-provider/collector tests.

Future cutover rollback:

1. Establish DB/broker flatness using the existing reconciliation gate.
2. Disable gateway order writes before any mode change.
3. Set direct mode in the specific ButterflyGuy service and restart it once.
4. Verify `/ready`, current token health, one quote/chain read, and no duplicate process with
   order capability.
5. Preserve gateway logs/audit/discrepancies for diagnosis; do not delete token evidence.

## Current migration status

Phase 0 is complete. Phase 1 and the fake-backed portion of Phase 2 are the only authorized
implementation scope. The gateway must remain disabled and outside the production stack.
