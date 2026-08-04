# Codex Project State

## Objective

Safely migrate Schwab ownership toward one shared, permissioned gateway without changing
live ButterflyGuy behavior or production defaults.

## Current Phase

The gateway foundation merged in PR #7 at merge commit `b8248a5`. The next isolated slice
on `codex/atomic-token-manager` implements a locked atomic single-token manager using only
synthetic token documents and fake refresh callbacks. It is not wired to schwab-py, the
gateway runner, a real token path, or any deployed service. No production cutover has begun.

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
- Defer Redis, shared streaming, account APIs, order APIs, and token-manager cutover.
- Do not start the inactive local Docker daemon because unrelated `unless-stopped`
  containers could restart; use the equivalent localhost demo runner for this proof.

## Current Slice

- `schwab_gateway/token_manager.py`: replaceable token-store protocol, thread/process lock,
  schema/lifetime validation, atomic mode-0600 persistence, health states, redacted
  transitions, and bounded Prometheus metrics.
- `tests/test_gateway_token_manager.py`: synthetic/fake callback failure, concurrency,
  process locking, state, redaction, and atomicity coverage.
- `infra/docker-compose.gateway.yml` and its runbook/test: run the unprivileged container as
  the mode-0600 key-file owner and add a readiness health check.
- `docs/architecture/schwab-token-manager.md`: contract and next integration gate.

## Token-Manager Tests Added

- Successful fake refresh and defensive-copy behavior.
- Missing, malformed, insecure, expired, symlinked, and non-finite token rejection.
- Revoked, manual-reauthorization, callback-failure, persistence-failure, and lock-timeout
  states without logging fake token contents.
- Thread and separate-process serialization with no lost refresh update.
- Same-directory temporary write, mode `0600`, fsync/replace flow, and cleanup after a
  simulated atomic-replace failure.

## Tests Passing

- Focused token-manager/Compose tests: 17 passed.
- Full suite: 533 passed, 1 skipped because `CI_DATABASE_URL` is provided only by the
  real-database workflow, and 2 pre-existing warnings.
- `uv run ruff check .`, `git diff --check`, Compose overlay rendering with an explicit
  UID/GID, wheel/sdist build, and `graphify update .` pass.

## Known Failures

None in focused tests. Docker runtime execution remains deliberately deferred because
starting the local daemon could restart unrelated containers. This slice performs no
deployment and reads no real token or credential.

## Open Questions

- Real Schwab extended-hours/streaming/EXTO capability results.
- Final production gateway host, private-network route, and OAuth callback domain.
- Future authorization to migrate account/order operations (not granted for this phase).

## Risks

- Existing production token refresh/write races remain because the new manager is not yet
  wired; this is deliberate until fake SDK callback integration is proven.
- Raw exception logging has no central redaction.
- The foundation runner intentionally serves fake data only; a production Schwab upstream
  and the standalone token manager are not wired.
- Only the collector uses the new direct market-data adapter; trade/position/order separation
  remains later work.
- New gateway code must remain disabled and isolated until shadow/session proof.
- Container runtime packaging still needs proof on a host where starting Docker cannot affect
  live or unrelated services.

## Next Exact Action

Review and merge the fake-only atomic token-manager slice without deploying. After merge,
build a fake schwab-py client adapter that proves the exact read/write callback lifecycle
under the manager lock before considering any real credential connection.
