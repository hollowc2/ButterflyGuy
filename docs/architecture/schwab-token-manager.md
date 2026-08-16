# Schwab Single-Token Manager

> **Historical embedded-component design:** The production implementation moved to the
> `schwab-token-store` package in
> [`hollowc2/SchwabGateway`](https://github.com/hollowc2/SchwabGateway) and Butterfly Guy imports
> the pinned package directly. Local module paths below describe the pre-extraction implementation.

## Scope

`schwab_gateway/token_manager.py` and `schwab_gateway/token_adapter.py` are standalone,
fake-tested components. Neither imports `schwab`, reads `.env`, knows a production token
path, or runs from the gateway entry point. The adapter can construct only an injected
client factory; all verification uses fake clients. Existing ButterflyGuy and candidate
processes continue using their current direct token behavior until a separately reviewed
cutover.

The manager owns exactly one versioned schwab-py token document through a replaceable
`TokenStore`. `AtomicFileTokenStore` is the initial Linux implementation.

## Transaction

```text
thread RLock -> process flock -> read 0600 JSON -> validate envelope and lifetime
    -> invoke the injected client factory's zero-argument reader
    -> construct and operate the client under the same lock
    -> for every metadata-wrapped writer callback: validate -> write same-directory 0600
       temp -> fsync temp -> atomic replace -> fsync directory -> return from callback
    -> release process lock -> release thread lock
```

The standalone refresh callback and the access-function reader receive defensive copies.
An invalid callback value, lock timeout, or pre-replace persistence failure leaves the last
valid token document unchanged. A valid rotation is durable before its writer returns and
therefore remains durable if a later fake client operation fails. Scoped reader and writer
callbacks reject every call after the operation exits. The manager and adapter normalize
errors and never log callback exception text, credentials, or token values.

## Proven schwab-py callback contract

The adapter protocol matches the installed schwab-py 1.5.1
`client_from_access_functions` signature: positional API key, app secret, zero-argument
token reader, and token writer, followed by `asyncio=False` and `enforce_enums=True`.
Construction calls the reader once. schwab-py extracts `creation_timestamp` and `token`,
then its `TokenMetadata.wrapped_token_write_func` wraps each raw OAuth rotation as
`{"creation_timestamp": <original>, "token": <rotated>}` before invoking the supplied
writer. The fake factory reproduces that wrapping and pass-through `*args`/`**kwargs`.

## Validation and states

The stable schwab-py envelope requires a positive finite `creation_timestamp`, an object in
`token`, and non-empty string `access_token` and `refresh_token` fields. JSON must contain no
non-finite values and the file must be a regular, non-symlinked, size-bounded mode-`0600`
file.

Bounded health states are:

- `uninitialized`, `ready`, and `refreshing`;
- `missing`, `corrupt`, and `expired`;
- `revoked` and `reauthorization_required`, explicitly signaled by the callback;
- `lock_timeout`, `refresh_failed`, and `persistence_failed`.

Prometheus exposes a one-hot state gauge and refresh counts by a bounded result label.
Structured transitions contain only previous state, state, and reason code.

## Fake-only verification

Tests use synthetic token strings, fake factories, and fake clients. In addition to the
standalone manager cases, they directly observe the lock across store read, factory
construction, client operation, and every callback write; cover no-refresh and multi-refresh
paths; verify persistence before callback return and after a later operation failure; reject
invalid and escaped callbacks; normalize sensitive fake failures; and prove concurrent
operations retain both rotated refresh-token generations. Existing malformed, expiry,
permission, atomicity, thread, and process-lock tests remain unchanged.

No test or implementation path reads `tokens.json` or any real Schwab credential.

## Integration gate

Do not connect these components to Schwab credentials yet. The callback lifecycle and
concurrency gate is now fake-proven. Gateway `/ready` now receives an injected
token-readiness provider and returns HTTP 200 only for `ready`. Every other bounded manager
state returns HTTP 503 with the fixed `token_state` and reason code below. `/health` remains
process liveness and keeps its existing v1 fields. The gateway never returns the provider's
own reason, token data, exception text, or paths.

| Manager state | `/ready` reason | HTTP status |
|---|---|---|
| `uninitialized` | `token_not_checked` | 503 |
| `ready` | `token_ready` | 200 |
| `refreshing` | `token_refreshing` | 503 |
| `missing` | `token_missing` | 503 |
| `corrupt` | `token_corrupt` | 503 |
| `expired` | `refresh_token_expired` | 503 |
| `revoked` | `token_revoked` | 503 |
| `reauthorization_required` | `token_reauthorization_required` | 503 |
| `lock_timeout` | `token_lock_timeout` | 503 |
| `refresh_failed` | `token_refresh_failed` | 503 |
| `persistence_failed` | `token_persistence_failed` | 503 |

If the injected provider itself fails or supplies an unrecognized state, `/ready` fails closed
as `uninitialized` with `token_readiness_unavailable` and HTTP 503.

The demo runner injects only a deterministic static `ready` provider; it does not construct a
real manager, client factory, or Schwab client. Focused fake tests parameterize every state
and prove the ready -> refreshing -> refresh_failed -> ready recovery sequence.

The standalone credential-proof command is now prepared and fake-tested. It performs one
fixed public quote through the manager and adapter, emits no quote payload, and is not wired
to the demo runner. It has not read real credentials or contacted Schwab. Execution still
requires the separate operator authorization and single-writer proof in
`schwab-gateway-credential-proof.md`; it must not deploy or cut over consumers.
