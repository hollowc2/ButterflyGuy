# Codex Project State

## Objective

Safely migrate Schwab ownership toward one shared, permissioned gateway without changing
live ButterflyGuy behavior or production defaults.

## Current Phase

The gateway foundation and atomic token manager merged through PR #8. The current isolated
slice on `codex/fake-schwab-token-adapter` adds an injected client-factory adapter and proves
the exact schwab-py 1.5.1 access-function lifecycle using only synthetic token documents,
fake clients, and fake callbacks. It is not wired to schwab-py, the gateway runner, a real
token path, or any deployed service. No production cutover has begun.

## Repository Findings

- SPX/NDX/XSP and host utilities independently construct `schwab-py` clients.
- Primary containers share one writable `tokens.json`; no token lock/atomic owner exists.
- `SchwabClientWrapper` combines market, account, transaction, and order capabilities.
- Candidate feed is a useful aiohttp/provider precedent but is SPX-specific and unauthenticated.
- No Redis/NATS/ZMQ/event bus exists; REST-first is the safe initial choice.

## Decisions Made

- Work only in the isolated worktree; do not touch live Compose/services.
- Keep direct access as the production default and do not migrate order submission.
- Add narrow market-data protocols/direct delegation first.
- Build an aiohttp/httpx/Pydantic read-only quote proof with hashed internal API keys.
- Build the token manager as a standalone `TokenStore` boundary before any SDK integration.
- Hold one thread/process lock across read, fake refresh callback, and atomic persistence.
- Match the installed schwab-py 1.5.1 factory signature and `TokenMetadata` wrapping through
  an injected protocol; do not import or wire the real factory in this slice.
- Keep fake client construction, operation, and every callback write inside one manager
  transaction; invalidate callbacks before releasing the lock.
- Defer Redis, shared streaming, account APIs, order APIs, and token-manager cutover.
- Do not start the inactive local Docker daemon because unrelated `unless-stopped`
  containers could restart; use the equivalent localhost demo runner for this proof.

## Current Slice

- `schwab_gateway/token_adapter.py`: exact injected client-factory protocol, bounded adapter
  errors, and manager-owned construction/operation scope.
- `schwab_gateway/token_manager.py`: scoped read/write callbacks that validate and durably
  persist every rotation before returning, then become unusable before lock release.
- `tests/test_gateway_token_adapter.py`: fake SDK metadata wrapping, directly observed lock
  coverage, no-refresh/multi-refresh behavior, invalid/escaped callbacks, later failures,
  redaction, and concurrent rotation coverage.
- Architecture/state docs: proven callback contract and the next readiness/checklist gate.

## Token-Manager Tests Added

- Successful fake refresh and defensive-copy behavior.
- Missing, malformed, insecure, expired, symlinked, and non-finite token rejection.
- Revoked, manual-reauthorization, callback-failure, persistence-failure, and lock-timeout
  states without logging fake token contents.
- Thread and separate-process serialization with no lost refresh update.
- Same-directory temporary write, mode `0600`, fsync/replace flow, and cleanup after a
  simulated atomic-replace failure.

## Token-Adapter Tests Added

- Direct lock observation across token-store read, fake factory construction, operation, and
  metadata-wrapped writes.
- Exact fake reproduction of schwab-py 1.5.1 reader/writer arguments and metadata envelope.
- No-refresh and multiple-refresh paths, with every valid rotation persisted before return.
- Persistence of a valid rotation when the later fake operation fails.
- Invalid data rejection, callback expiry, and bounded error/log redaction.
- Concurrent operations serialize construction and retain both refresh-token generations.

## Tests Passing

- Focused token-manager/adapter tests: 24 passed.
- Full suite: 541 passed, 1 skipped because `CI_DATABASE_URL` is provided only by the
  real-database workflow, and 2 pre-existing warnings.
- `uv run ruff check .`, `git diff --check`, wheel/sdist build and content inspection, and
  `graphify update .` pass. Pull-request CI is pending.

## Known Failures

None in focused tests. Docker runtime execution remains deliberately deferred because
starting the local daemon could restart unrelated containers. This slice performs no
deployment and reads no real token or credential.

## Open Questions

- Real Schwab extended-hours/streaming/EXTO capability results.
- Final production gateway host, private-network route, and OAuth callback domain.
- Future authorization to migrate account/order operations (not granted for this phase).

## Risks

- Existing production token refresh/write races remain because the fake-proven manager and
  adapter are deliberately not wired to any current direct path.
- Raw exception logging has no central redaction.
- The foundation runner intentionally serves fake data only; a production Schwab upstream,
  the standalone token manager, and the adapter are not wired.
- Only the collector uses the new direct market-data adapter; trade/position/order separation
  remains later work.
- New gateway code must remain disabled and isolated until shadow/session proof.
- Container runtime packaging still needs proof on a host where starting Docker cannot affect
  live or unrelated services.

## Next Exact Action

Review and merge the fake-only adapter slice without deploying. After merge, add gateway
readiness mapping for every bounded token-manager state and complete an operator-reviewed
migration/rollback checklist before considering any real credential proof.
