# Schwab Gateway Multi-Consumer Foundation

> **Status update — 2026-08-10:** The read-only foundation is now deployed on Helios, running and
> monitored. Readiness, one authenticated Schwab quote, Prometheus scraping, alerting, and
> crash-restart recovery have been proven. Direct trading access remains authoritative, and XSP has
> installed default-off C3 shadow wiring that always returns the direct result. Account and order
> authority remain absent. The live read-only routes now include `/v1/quotes`, `/v1/spot`, and
> `/v1/chain`; `/v1/history` remains absent. The implementation inventory below is retained for
> design history; deployment and proof classifications written before the live window are
> superseded by this note.

## Status and safety boundary

The historical foundation section below predates deployment. The read-only gateway and its
admission policy are now active in the Helios gateway runtime, while direct access remains the
production default for trading. XSP may use the gateway only for an explicitly enabled shadow
comparison, never as the source of a returned trading value. Equity Scanner and AfterHours Lab are
not gateway consumers.

## Trust model

Each consumer has one distinct internal identity and key digest. A raw internal key is supplied
only by its client and is never committed or logged. The versioned server configuration accepts
only a caller ID, lowercase SHA-256 digest, capabilities, and priority class.

| Caller ID | Current capabilities | Priority class | Explicitly absent |
|---|---|---|---|
| `butterfly-guy` | `market_data:read` | `protected` | account, order, position, transaction, stream |
| `equity-scanner` | `market_data:read` | `background` | account, order, position, transaction, stream |
| `afterhours-lab` | `market_data:read` | `background` | account, order, position, transaction, stream |

`history:read` may be added to the two background identities only when a history endpoint is
implemented and reviewed. ButterflyGuy may later receive history/options capabilities only with
the corresponding implemented contracts. Account and order authority is outside this slice.

Authentication hashes the presented key, compares it against every configured digest with
`hmac.compare_digest`, and derives identity and priority exclusively from the matching server
record. A caller-supplied identity header has no authority. Unknown keys return the same bounded
401 response. A valid identity lacking `market_data:read` receives the same bounded 403 response.
The three known IDs have fixed priority classes, so configuration cannot label a background app
as protected.

## ButterflyGuy-first admission policy

The quote handler enforces this sequence:

```text
internal-key authentication
  -> capability check
  -> bounded symbol validation
  -> token readiness check
  -> class-specific admission
  -> bounded upstream timeout
  -> v1 normalization
  -> unconditional permit release
```

Two finite in-process pools are configured independently:

- protected capacity is usable only by `butterfly-guy`;
- background capacity is shared by `equity-scanner` and `afterhours-lab`.

Background work therefore cannot consume ButterflyGuy's reserved permits. A full background pool
returns HTTP 429 with the fixed `gateway_capacity_exceeded` contract; requests are not queued or
retried generically. Cancellation, timeout, normalized upstream failure, and successful return all
release the permit in `finally`. Values must be integers from 1 through 256. They are internal
concurrency controls, not claims about an unmeasured Schwab quota.

Admission metrics label only `protected`/`background` and `admitted`/`rejected`. Request metrics
label only bounded route operation and HTTP status. Audit caller IDs come only from the configured
three-identity set. Symbols, URLs, keys, digests, account identifiers, upstream payloads, and raw
error strings are never Prometheus labels.

## Ownership and contracts

`schwab_gateway` owns internal authentication, token readiness/management, upstream interaction,
admission policy, normalization, liveness/readiness, bounded errors, metrics, and auditing.
`gateway_client` owns transport-neutral v1 models and fail-closed HTTP client behavior. Strategy,
risk, execution, position, and service code must not import gateway server internals. Future
scanner and research consumers should depend only on `gateway_client` or an equally narrow
protocol.

The implemented route table is `/health`, `/ready`, `/metrics`, and authenticated `/v1/quotes`,
`/v1/spot`, and `/v1/chain`. Existing v1 quote fields remain backward compatible. Missing bid/ask
remain null, not zero. Timeouts, unavailability, malformed responses, authentication failures,
authorization failures, readiness failures, and capacity rejection remain explicit and bounded.

Future endpoint order, without implementation in this slice:

1. batch quotes;
2. price history;
3. option chains;
4. streaming only after measured need;
5. account/order mediation only under separate authorization and security review.

No history, account, order, position, transaction, or streaming route exists here. No automatic
order retry exists; order submission remains outside the gateway foundation.

## Historical evidence classification

- **Implemented/fake-tested:** three identities, digest-only configuration, fixed priority
  mapping, fail-closed auth/capability behavior, readiness-gated quote admission, two bounded
  pools, permit cleanup, route/import boundaries, nullable quote normalization, and bounded labels.
- **Prepared but not executed:** the opt-in executable staging mount, after-hours approval
  runbook, rollback procedure, and redacted evidence template.
- **Observed on Helios previously:** SPX root filesystem read-only; writable `/tmp` and `/dev/shm`
  noexec; the earlier root-filesystem staging attempt failed safely; services were restored.
- **Proposed/inferred:** an isolated writable-and-executable tmpfs at the staging-only application
  path removes that specific filesystem blocker. This has not been exercised on Helios.
- **Unproven at that stage:** real credential/token readability, real schwab-py lifecycle, one real
  AAPL quote, broker behavior, production gateway capacity, and every deployment/cutover property.
  The status note above records the later live proof; production capacity and consumer cutover are
  still not proven.
