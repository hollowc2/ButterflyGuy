# Codex Project State

## Objective

Safely migrate Schwab ownership toward one shared, permissioned gateway without changing
live ButterflyGuy behavior or production defaults.

## Current Phase

The fake gateway foundation, atomic token manager/adapter, readiness boundary, and standalone
credential-proof command are merged. A supervised launch proved the single-writer quiescence
procedure but stopped during a native dependency import before credential settings, token
access, or Schwab access was reachable. The direct services were restored and no production
cutover has begun. The bounded import remediation is merged. The current isolated slice adds a
fake-tested three-consumer trust/admission boundary and prepares an unexecuted after-hours staging
and evidence package.

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
- Keep `/health` as v1 process liveness. `/ready` is HTTP 200 only for injected `ready`; every
  other bounded manager state is HTTP 503 with a fixed non-sensitive state/reason code.
- Use a deterministic static fake readiness provider in the demo runner rather than wiring a
  real manager or schwab-py factory.
- Defer Redis, shared streaming, account APIs, order APIs, and token-manager cutover.
- Do not start the inactive local Docker daemon because unrelated `unless-stopped`
  containers could restart; use the equivalent localhost demo runner for this proof.

## Current Slice

- `schwab_gateway/auth.py`: exact `butterfly-guy`, `equity-scanner`, and `afterhours-lab`
  identities with distinct digests, read-only capabilities, and fixed protected/background policy.
- `schwab_gateway/admission.py` and `api.py`: separate finite pools, readiness-gated quote
  admission, fixed overload response, bounded metrics, and unconditional permit release.
- Gateway client/config/examples/tests: explicit capacity failure, three synthetic callers,
  constant-time full digest scan, route/import boundaries, and concurrent failure-path coverage.
- Architecture/runbook/template/isolated Compose override: prepared after-hours executable staging,
  two approvals, watchdog restoration, exact-image rollback, and redacted evidence fields; not run.

- `schwab_gateway/token_adapter.py`: exact injected client-factory protocol, bounded adapter
  errors, and manager-owned construction/operation scope.
- `schwab_gateway/token_manager.py`: scoped read/write callbacks that validate and durably
  persist every rotation before returning, then become unusable before lock release.
- `tests/test_gateway_token_adapter.py`: fake SDK metadata wrapping, directly observed lock
  coverage, no-refresh/multi-refresh behavior, invalid/escaped callbacks, later failures,
  redaction, and concurrent rotation coverage.
- `schwab_gateway/api.py`: injected readiness protocol, exhaustive state-to-code mapping, and
  fail-closed default when no provider is injected.
- `scripts/run_schwab_gateway.py`: deterministic fake `ready` provider for `--demo` only.
- Architecture/state docs: readiness semantics and the explicit operator checklist.
- `schwab_gateway/credential_probe.py`: bounded one-quote proof with no response payload,
  account lookup, order/stream surface, retry, or server startup.
- `scripts/probe_schwab_gateway_credentials.py`: explicit three-confirmation entry point;
  lazy real-factory import only after the confirmations and environment validation; all
  project/third-party imports and result serialization occur inside the generic CLI failure
  boundary so runtime failures cannot emit raw exception text.
- `tests/test_gateway_credential_probe.py`: synthetic token, fake factory/client/response,
  exact quote-only call, close, redaction, malformed response, CLI refusal, and bounded
  runtime-import failure coverage.

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
- Every bounded manager state returns the expected fake-proven `/ready` status and bounded
  code; refresh, failure, and recovery return 200, 503, 503, and 200 respectively.

## Tests Passing

- Required gateway auth/config/API/model/redaction/token/credential suite: 76 passed.
- New admission/client/import/Compose/provider suite: 13 passed.
- Full suite: 587 passed, 1 skipped because `CI_DATABASE_URL` is only supplied by the
  real-database workflow, and 2 pre-existing warnings.
- `uv run ruff check .`, `git diff --check`, wheel/sdist builds and content checks, and
  `graphify update .` pass.
- The current adversarial review removed unimplemented future capabilities and verified bounded
  errors/labels, identity derivation, permit cleanup, route/import boundaries, unchanged defaults,
  and package exclusions. The real credential proof remains unproven and requires fresh approval.

## Known Failures

The supervised command launch on 2026-08-04 exited before credential access because a native
dependency could not load from the temporary execution filesystem. The pre-remediation CLI
emitted raw exception text because project imports occurred outside its failure boundary.
Retained evidence is bounded and mode `0600`; no credential/token read or Schwab request was
reachable, no retry occurred, and all direct services were restored healthy. The real proof
remains incomplete pending remediation merge and fresh authorization.

## Open Questions

- Real Schwab extended-hours/streaming/EXTO capability results.
- Final production gateway host, private-network route, and OAuth callback domain.
- Future authorization to migrate account/order operations (not granted for this phase).

## Risks

- Existing production token refresh/write races remain because the fake-proven manager and
  adapter are deliberately not wired to any current direct path.
- Raw exception logging has no central redaction. This slice bounds the standalone proof
  command's project/third-party imports but does not change unrelated commands.
- The foundation runner intentionally serves fake data only. The real manager/adapter are
  reachable only through the standalone, explicitly confirmed credential-proof command; no
  gateway server or consumer uses them.
- Only the collector uses the new direct market-data adapter; trade/position/order separation
  remains later work.
- New gateway code must remain disabled and isolated until shadow/session proof.
- Container runtime packaging still needs proof on a host where starting Docker cannot affect
  live or unrelated services.

## Next Exact Action

Review and merge the multi-consumer foundation without deploying. After market hours, obtain
Approval 1 before the isolated staging recreation/smoke/quiescence procedure, then obtain fresh
Approval 2 before one real credential/token read and one AAPL quote. No live action is authorized
by the prepared package.
