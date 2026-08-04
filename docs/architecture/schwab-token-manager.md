# Schwab Single-Token Manager

## Scope

`schwab_gateway/token_manager.py` is a standalone, fake-tested persistence component. It
does not import `schwab`, construct a Schwab client, read `.env`, know a production token
path, or run from the gateway entry point. Existing ButterflyGuy and candidate processes
continue using their current direct token behavior until a separately reviewed cutover.

The manager owns exactly one versioned schwab-py token document through a replaceable
`TokenStore`. `AtomicFileTokenStore` is the initial Linux implementation.

## Transaction

```text
thread RLock -> process flock -> read 0600 JSON -> validate envelope and lifetime
    -> invoke one supplied refresh callback -> validate returned document
    -> write same-directory 0600 temp -> fsync temp -> atomic replace -> fsync directory
    -> release process lock -> release thread lock
```

The refresh callback receives a defensive copy. A callback exception, invalid return value,
lock timeout, or pre-replace persistence failure leaves the prior token document unchanged.
The manager never logs callback exception text or token values.

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

Tests use synthetic token strings and callbacks. They cover successful refresh, defensive
copies, malformed/missing/expired/insecure files, invalid callback output, callback errors
containing fake secrets, revoked/manual-reauthorization classification, thread and process
contention, lock timeout, mode preservation, temporary-file cleanup, symlink rejection,
non-finite JSON, and a simulated `os.replace` failure.

No test or implementation path reads `tokens.json` or any real Schwab credential.

## Integration gate

Do not connect this component to Schwab credentials yet. The next integration must first
wrap a fake client factory that exercises the exact schwab-py read/write callback lifecycle
under the manager transaction. It must prove that callbacks cannot escape the lock scope,
that one concurrent refresh wins without losing a rotated refresh token, and that gateway
readiness reports every bounded manager state. Real credentials remain prohibited until
that fake adapter and an operator-reviewed migration/rollback checklist pass.
