# Target Trading Platform

## Recommendation

Create one independently deployed `schwab-gateway` as the sole Schwab trust boundary.
During migration its code lives under `src/butterfly_guy/schwab_gateway/`, with transport-
neutral client code under `src/butterfly_guy/gateway_client/`. This keeps the existing wheel
layout intact and permits later extraction to `TradingCore` without making strategy code
import server internals.

```text
                                  Schwab Trader API
                                           |
                             one OAuth identity/token owner
                                           |
                    +----------------------v----------------------+
                    |                schwab-gateway               |
                    | auth/token store | REST | stream | policies |
                    | cache/recording  | RBAC | audit  | health   |
                    +----------+-----------+------------+----------+
                               |           |            |
                    read/order | read-only | derived events
                               |           |            |
                 +-------------v--+   +----v---------+  +---------v------+
                 | ButterflyGuy   |   |AfterHoursLab |  |market recorder |
                 |strategy/risk   |   |scanner       |  |and Discord bot |
                 +--------+-------+   +------+-------+  +---------+------+
                          |                  |                    |
                          +------------------v--------------------+
                                     TimescaleDB
                               Redis Streams only when needed
```

## Boundaries

The gateway eventually owns all Schwab credentials, token reads/writes/refresh, account
number/hash mapping, REST/stream clients, rate limits, normalized upstream errors, caches,
raw evidence, caller authorization, and order audit. Callers receive only the capabilities
and normalized data they need.

ButterflyGuy retains strategy, schedule, candidate selection, risk policy, paper-fill
semantics, order intent lifecycle, position state machine, and trade database. During the
strangler period it may retain direct brokerage access for rollback, but gateway-mode
processes must not receive Schwab secrets.

## Interfaces and contracts

Use narrow Python protocols at the strategy boundary:

- `SpotPriceProvider`
- `OptionChainProvider`
- `PriceHistoryProvider`
- `EquityQuoteProvider`
- later: `AccountProvider`, `OrderExecutionProvider`, `OrderStatusProvider`

The initial gateway API implements only `GET /health`, `GET /ready`, and authenticated
`GET /v1/quotes`. Later endpoints are added only when a migrated caller needs them. API v1
models use Pydantic and nullable fields for missing market data. Missing bid/ask must never
become zero.

Every quote contract includes `symbol`, event timestamp when known, gateway receive
timestamp, source, session when known, bid/ask/sizes, last/size, mark, volume, explicit
staleness, age, and data-quality flags. Raw upstream fields may be stored as redacted
evidence but are not part of strategy logic.

## Internal authorization

Initial authentication uses an internal API key in `X-Internal-API-Key`. The server reads a
root-owned, read-only JSON file containing caller IDs, SHA-256 key digests, and capabilities;
raw keys are never stored in configuration or logged. Comparison is constant-time.

Capabilities:

| Consumer | Capabilities |
|---|---|
| ButterflyGuy foundation client | `market_data:read` |
| ButterflyGuy later | market/history/options plus only the account/order permissions proven necessary |
| AfterHours collector/scanner | `market_data:read`, `history:read`; no account/order |
| Research notebook | `history:read` only |
| Discord bot | none; derived scanner events only |

Future order writes require a distinct service identity, `orders:write`, an independent
kill switch, correlation ID, reconciliation policy, and `SCHWAB_GATEWAY_ORDER_WRITES_ENABLED=true`.
There will be no order route in the foundation.

## OAuth and token storage

Target design uses one logical `TokenManager` with:

1. an exclusive process/file lock covering read-refresh-write;
2. schema validation and explicit corruption/revocation states;
3. atomic write to a same-directory temporary file, `fsync`, restrictive `0600` mode,
   atomic replace, and directory `fsync` where supported;
4. redacted structured transition logs and refresh metrics;
5. one manual-reauthorization state exposed through limited auth health;
6. a `TokenStore` interface so a host secret store can replace the file later.

The locked atomic manager is implemented as a standalone component and tested only with
synthetic token documents and fake refresh callbacks. It is intentionally not placed in the
gateway or any existing production path. Changing SDK token callbacks before a fake client
adapter and reviewed cutover would create more operational risk than it removes.

## REST policy

- Explicit connect/read/write/pool timeouts.
- Retry only classified, idempotent reads; bounded exponential backoff with jitter and
  `Retry-After` support.
- Never automatically retry order submission.
- Normalize timeout, auth, rate limit, unavailable, malformed, and partial-data errors.
- Short-lived quote deduplication/cache and history cache only after correctness tests.
- Caller, operation, status, latency, cache result, retry count, and normalized error are
  audited; symbols and account identifiers are excluded from unbounded metric labels.

## Streaming

Do not build shared streaming until Schwab limits are measured. The target has one upstream
connection where practical, a reference-counted subscription union, per-consumer requested
sets, reconnect/resubscribe, stale detection, normalized events, optional redacted raw
recording, and health/metrics. A symbol is removed upstream only when its consumer reference
count reaches zero.

The existing `JsonlStreamRecorder` supplies the local archive envelope and queue/drop
patterns but needs schema-aware redaction, reconnect, wrapper cleanup, and capability tests.

## Events and Discord

Use synchronous REST for the foundation. There is no current event bus, and adding Redis
does not help the one-quote proof.

When AfterHoursLab needs fan-out, replay, and consumer groups, prefer Redis Streams because
it is operationally smaller than NATS in this environment and more durable/replayable than
in-process WebSockets or ZeroMQ. PostgreSQL `LISTEN/NOTIFY` does not provide durable replay.
This is a deferred decision: confirm expected volume and Redis operational acceptance first.

Future flow:

```text
gateway -> recorder/scanner -> TimescaleDB + event stream -> Discord bot
```

The bot consumes normalized events such as `SESSION_STARTED`, `SYMBOL_DISCOVERED`,
`SETUP_TRIGGERED`, and `DATA_HEALTH_WARNING`; it never imports Schwab code or credentials.
Discord message IDs may be written back to scanner tables for update/thread support.

## Deployment topology

### Foundation proof

- Separate Git worktree and branch.
- Local process or separate Compose overlay/project only.
- Bind gateway to `127.0.0.1` by default.
- Fake upstream for CI and local contract proof.
- No modification to `infra/docker-compose.yml`, existing services, profiles, ports, token
  mounts, deployment workflow, or production default.
- Order writes disabled by model invariant.

### Later production

An always-on private host may run gateway, recorder, scanner, bot, and Redis. TimescaleDB may
remain on its current host. Development/research may run elsewhere over Tailscale. These host
names are proposals, not repository-verified facts.

Internal endpoints bind only to a private Docker network, loopback, or Tailscale interface.
The OAuth callback is a separate narrowly routed listener; account/order APIs are never
public. Only the gateway receives Schwab secret mounts. Client services receive one scoped
internal key through a file mount or secret mechanism.

## Configuration model

Foundation variables:

```text
SCHWAB_GATEWAY_BIND_HOST=127.0.0.1
SCHWAB_GATEWAY_PORT=8010
SCHWAB_GATEWAY_INTERNAL_KEYS_PATH=/run/secrets/schwab-gateway-keys.json
SCHWAB_GATEWAY_LOG_LEVEL=INFO
SCHWAB_GATEWAY_ORDER_WRITES_ENABLED=false
SCHWAB_GATEWAY_URL=http://127.0.0.1:8010
SCHWAB_GATEWAY_API_KEY=<client secret>
SCHWAB_ACCESS_MODE=direct
```

Gateway upstream variables remain the existing `SCHWAB_API_KEY`, `SCHWAB_SECRET_KEY`,
`SCHWAB_TOKEN_PATH`, and later `SCHWAB_CALLBACK_URL`. `SCHWAB_ACCOUNT_ID` is not required by
the read-only quote proof. `DATABASE_URL`, `REDIS_URL`, and raw recording are deferred until
needed.

Configuration rejects unknown fields, public bind hosts unless explicitly allowed, missing
key files for a real server, invalid key digests/capabilities, and any attempt to enable
order writes in this foundation.

## Health and observability

- `/health`: process liveness only; never includes secrets, callers, symbols, or accounts.
- `/ready`: initially upstream object initialized and internal auth configuration loaded.
- `/metrics`: reuse Prometheus; add bounded labels for operation/status/caller class.

Target metrics include request/error/latency/rate-limit, token refresh/failure/expiry,
stream reconnect/age, cache hit/miss, client requests, and order requests. Auth, stream,
DB, and Redis components appear in readiness only when they are actual dependencies.

Audit records include caller, operation, timestamp, status, latency, cache result, retry
count, normalized upstream category, and redacted order correlation. No tokens, keys,
account numbers/hashes, webhook URLs, or raw OAuth payloads are logged.

## Failure policy

| Failure | Behavior |
|---|---|
| timeout/network loss | Explicit unavailable/timeout error; idempotent reads may retry within budget. |
| 401/invalid refresh | Stop generic retries, mark auth not ready, require reauthorization when classified. |
| 429 | Honor `Retry-After`, update metrics, return rate-limit error after bounded wait. |
| corrupt token | Refuse startup/refresh, preserve evidence metadata without contents. |
| malformed/partial quote | Return explicit error or nullable fields plus quality flags; never zero-fill. |
| stale quote | Return timestamp, age, and `stale=true`; ButterflyGuy fails closed. |
| gateway restart/loss | Clients time out explicitly; direct fallback requires an operator-selected mode, never automatic dual order paths. |
| DB/Redis outage | Market REST remains available if independent; recording/events report degraded readiness and buffer only within declared bounds. |
| stream disconnect | Mark stale, reconnect with backoff, restore subscriptions, never imply fresh data. |
| order timeout/unknown | Do not resubmit; reconcile correlation ID and broker state, retain audit trail. |

## AfterHoursLab compatibility

AfterHoursLab can use quotes/history without account access. Broad snapshots should be
batched and cached centrally, then active symbols promoted to higher-frequency polling or
streaming. Contracts reserve session, bid/ask sizes, trade/quote timestamps, volume, data
quality, and instrument metadata. EXTO/24x5 and extended-hours volume remain optional and
`UNVERIFIED` until captured.

## Architecture decisions

1. **One gateway:** one app identity requires one token/stream/rate-policy owner.
2. **No shared token file:** a file cannot enforce refresh serialization or caller
   capabilities and distributes secrets to every consumer.
3. **REST over direct imports:** it enforces a process/security boundary and allows
   ButterflyGuy and AfterHoursLab to deploy independently. Python protocols preserve local
   testability.
4. **Event bus deferred:** current proof is request/response and the repo has no bus.
5. **Token store:** locked atomic file first, replaceable store later; no production token
   callback change in the foundation.
6. **Internal auth:** hashed API keys and explicit capabilities from the first endpoint.
7. **Read/write separation:** read-only consumers never inherit account/order access;
   order routes and permissions arrive last.
8. **Repository extraction:** keep code inside the existing package until contracts and a
   complete session are stable, then move gateway/client packages to `TradingCore`.
9. **Messaging:** Redis Streams is the leading later option, contingent on need and ops
   approval.
10. **Retirement:** direct mode remains a feature-flagged rollback through read cutover and
    order stabilization, then credentials/token/SDK ownership are removed from ButterflyGuy.
