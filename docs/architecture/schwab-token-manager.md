# Schwab Single-Token Manager

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
concurrency gate is now fake-proven. The next integration gate is gateway readiness mapping
for every bounded manager state plus an operator-reviewed migration/rollback checklist.
Only after that separate review may a narrowly scoped credential proof be considered; it
must not deploy, cut over consumers, or change the demo-only gateway runner by implication.
