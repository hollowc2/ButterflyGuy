# Codex Project State

## Objective

Safely migrate Schwab ownership toward one shared, permissioned gateway without changing
live ButterflyGuy behavior or production defaults.

## Current Phase

Phase 0 is complete. The safest Phase 1 collector boundary and fake-backed Phase 2 gateway
foundation, including an isolated localhost smoke proof, are complete on branch
`codex/schwab-gateway-foundation` at `/tmp/butterfly-schwab-gateway`. The foundation
has been approved for commit and push only. No production cutover has begun.

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
- Defer Redis, shared streaming, account APIs, order APIs, and token-manager cutover.
- Do not start the inactive local Docker daemon because unrelated `unless-stopped`
  containers could restart; use the equivalent localhost demo runner for this proof.

## Files Changed

- Architecture/state: `CODEX_STATE.md` and six `docs/architecture/` documents covering the
  current state, target, migration, capability matrix, local run, and redacted smoke proof.
- Boundary/client/server: `data/providers.py`, collector and two constructor call sites,
  `gateway_client/`, `schwab_gateway/`, and `scripts/run_schwab_gateway.py`.
- Safe local ops: `.dockerignore`, `.env.example`, hashed-key example, and the separate
  `infra/docker-compose.gateway.yml` project.
- Generated graph: `graphify-out/GRAPH_REPORT.md`, `graph.html`, `graph.json`, and manifest.
- Tests: six new gateway/provider test modules.

## Tests Added

- Direct adapter exact delegation.
- Quote parsing, null/missing-field preservation, timestamps, and staleness.
- Hashed API-key authentication, key-file validation, capabilities, and redaction.
- Server/client configuration safety and direct-mode default.
- Real localhost client -> aiohttp gateway -> fake upstream contract, authn/authz, request
  validation, no order routes, and timeout behavior.
- Correct 404 audit/metric classification for the intentionally absent order route.

## Tests Passing

- Baseline before edits: 35 focused tests.
- Focused final: 53 provider/gateway/current-boundary tests.
- Full final: 516 passed, 1 skipped because `CI_DATABASE_URL` is only provided by the
  real-DB workflow, and 2 pre-existing warnings.
- `uv run ruff check .`, `git diff --check`, Compose overlay rendering, graphify update, and
  wheel/sdist build all pass.
- Local smoke: health 200, ready 200, anonymous quote 401, authenticated demo quote 200,
  absent order route 404, and `operation=unknown,status=404` metric verified.

## Known Failures

None. Docker runtime execution was deliberately deferred because the local Docker daemon is
inactive and starting it could restart unrelated containers. Compose rendering and the
equivalent local-process smoke proof passed.

## Open Questions

- Real Schwab extended-hours/streaming/EXTO capability results.
- Final production gateway host, private-network route, and OAuth callback domain.
- Future authorization to migrate account/order operations (not granted for this phase).

## Risks

- Concurrent token refresh/write races remain until cutover to a single token manager.
- Raw exception logging has no central redaction.
- The foundation runner intentionally serves fake data only; a production Schwab upstream
  and token manager are not wired.
- Only the collector uses the new direct market-data adapter; trade/position/order separation
  remains later work.
- New gateway code must remain disabled and isolated until shadow/session proof.
- Container runtime packaging still needs proof on a host where starting Docker cannot affect
  live or unrelated services.

## Next Exact Action

Open a pull request for architecture/code review of `codex/schwab-gateway-foundation`; do not
deploy or change production defaults.
