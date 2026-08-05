# Codex Project State

## Objective

Safely migrate Schwab ownership toward one shared, permissioned gateway without changing
live ButterflyGuy behavior or production defaults.

## Current Phase

The fake gateway foundation, atomic token manager/adapter, readiness boundary, and standalone
credential-proof command are merged. Four supervised launches stopped before credential settings,
token access, or Schwab access was reachable. The first stopped during a native dependency import
and was restored. The second proved the isolated Compose delta but stopped on an unreliable
runtime fingerprint before source staging or quiescence. Its recorded images and executable-mount
absence were restored, but exact SPX configuration equality could not be proven. The operator then
accepted the current verified paper/direct configuration as a new baseline; SPX/NDX/XSP were
resumed healthy with recorded images, unique processes, no staging mount, and zero new filtered
errors during a fresh observation window. The third stopped during baseline preflight when ad-hoc
operator wrappers violated the bounded-output rule; no service mutation occurred. The fourth used
the committed, read-only legacy-evidence locator after fresh Approval 1; it returned the bounded
`no_acceptance` disposition, so no service mutation occurred. The operator-accepted SPX/NDX/XSP
baseline is not uniquely proven by the reviewed legacy evidence. Its bounded result was not
persisted to the approved evidence destination before temporary staging cleanup. The committed
evidence-capturing locator was subsequently run on Helios under fresh approval; it returned the
same bounded `no_acceptance` disposition and durably retained a mode-`0600` evidence artifact
before temporary source cleanup. No service mutation occurred. No production cutover has begun.
An authorized read-only new-baseline candidate capture then failed closed with the bounded
`compose_semantics_invalid` result before producing any candidate set; its mode-`0600` failure
evidence was retained and temporary source removed. The authorized bounded reader identified the
failed check as `compose_hashes`. Local review found that the capture had incorrectly required
Compose/image equality for the candidate-feed container even though the authorized baseline set is
SPX/NDX/XSP and candidate feed requires ownership/uniqueness checks only. The current isolated slice
adds a fake-tested three-consumer trust/admission boundary.

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
- `scripts/credential_proof_fingerprint.py`: `legacy-evidence-capture` validates the exact archive
  and approval window, performs the bounded locator, and exclusively persists one mode-`0600`
  redacted result before returning success or failure. It records no evidence roots or secret
  values and refuses to overwrite an existing artifact.
- `scripts/credential_proof_fingerprint.py`: `baseline-candidate-capture` is the local-only,
  fake-tested read-only path for a possible new baseline. It requires exact reviewed paper configs
  and Compose source, direct-access runtime settings, running/unpaused services, staging absence,
  health, uniqueness, read-only candidate ownership, writer absence, Compose-hash equality, and
  image equality before persisting the exact three-service hash/image set.
- `scripts/credential_proof_fingerprint.py`: `baseline-candidate-status` strictly validates a
  retained candidate artifact and emits only the fixed failed-check name or the successful
  candidate-set digest. It rejects extra fields, partial records, inconsistent checks, and altered
  candidate hashes without disclosing stored content.

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

- Required focused gateway/remediation suite: 167 passed.
- Full suite: 666 passed, 1 skipped because `CI_DATABASE_URL` is only supplied by the
  real-database workflow, and 2 pre-existing warnings.
- `uv run ruff check .`, `git diff --check`, wheel/sdist builds and content checks, and
  `graphify update .` pass.
- The current adversarial review removed unimplemented future capabilities and verified bounded
  errors/labels, identity derivation, permit cleanup, route/import boundaries, unchanged defaults,
  and package exclusions. The real credential proof remains unproven and requires fresh approval.

## Known Failures

The first supervised command launch on 2026-08-04 exited before credential access because a native
dependency could not load from the temporary execution filesystem. The pre-remediation CLI
emitted raw exception text because project imports occurred outside its failure boundary.
Retained evidence is bounded and mode `0600`; no credential/token read or Schwab request was
reachable, no retry occurred, and all direct services were restored healthy. The real proof
remains incomplete pending remediation merge and fresh authorization.

A second supervised window on 2026-08-04 used feature SHA
`3a321bd765ef01356af9d53ef1bd1a17e8c31c08`. The opt-in Compose dry run proved a target-only
executable-tmpfs delta, and staged SPX recreation retained the recorded image with one process.
Validation then rejected an order-sensitive runtime fingerprint, so the run stopped before source
staging, smoke, quiescence, Approval 2, credential/token access, or Schwab access. SPX was recreated
without the staging override from its recorded image ID; its image, startup-error count, one-process
state, and staging-mount absence passed, while NDX/XSP remained on their original container/image
IDs. Because the destroyed baseline's authoritative Compose hash was unavailable, exact SPX
configuration equality is unproven. SPX/NDX/XSP were paused fail-closed, temporary overrides were
removed, and bounded mode-`0600` evidence recorded the inconclusive result. No retry occurred.

The operator then approved the current paper-mode/direct-access configuration as a new baseline.
The safety gate passed recorded-image, Compose/config hash, live-gate, risk-limit, account-guard,
token-lifetime, staging-absence, candidate-ownership, and process/writer checks. SPX/NDX/XSP were
unpaused at `2026-08-04T23:36:21Z`; all health and uniqueness checks passed. Six filtered error
markers per service occurred immediately after the long pause, followed by zero new filtered
errors for every service in a fresh 30-second window. A separate mode-`0600` evidence supplement
records the accepted canonical fingerprints and resume result. This is an operator-defined new
baseline, not proof of byte-for-byte equality with the destroyed SPX configuration.

A third supervised window on 2026-08-05 used remediation SHA
`7435ce0d5934155ff3db9c9f0566d56b7685f601`. Relevant remote source, runtime-config, base-Compose,
documentation, and state paths were clean, and the default Compose and three trading-config hashes
matched the accepted sources. SPX/NDX/XSP and candidate feed were running and unpaused. The exact
minimal archive passed SHA-256 and embedded-commit verification and contained no forbidden
environment, token, credential, data, or evidence entries. The committed helper captured four
mode-`0600` baseline snapshots containing canonical, field-level, and Compose hashes.

An ad-hoc accepted-fingerprint comparison wrapper then emitted a raw programming traceback, so the
information-exposure stop condition fired before any recreation. A later optional post-stop
wrapper also failed, and its partial process-count lines are marked invalid and must not be used.
No Compose dry run, rollback override, executable mount, source staging inside a container, smoke,
watchdog, quiescence, Approval 2 request, credential/token access, or Schwab request occurred; retry
count remained zero. The committed helper verified that all four containers still exactly matched
their just-captured baselines and were running and unpaused. Temporary host-side source artifacts
were removed. This proves no configuration change during the window, not accepted-fingerprint or
process-uniqueness completion.

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

Commit and archive the corrected candidate capture, which limits Compose-hash and image equality to
the authorized SPX/NDX/XSP baseline set while preserving candidate-feed running, staging-absence,
ownership, uniqueness, and no-writer checks. Obtain fresh authorization tied to that exact release
before rerunning the read-only capture. Do not adopt a candidate automatically. Until an exact
candidate passes and is explicitly accepted, leave the direct-access paper services unchanged. No
gateway deployment, staging, credential/token read, Schwab request, or cutover is currently
authorized.
