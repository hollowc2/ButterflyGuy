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
SPX/NDX/XSP and candidate feed requires ownership/uniqueness checks only. The corrected capture was
then run under fresh authorization from exact release
`e4838664f84fda9be032e21fe2c6f9fa273fc2ae`; it also failed closed with
`compose_semantics_invalid` before producing any candidate set. Its mode-`0600` failure evidence is
retained on Helios, the exact temporary source/archive were removed, and no live state was mutated.
The separately authorized bounded reader then identified `failed_check=compose_hashes` but emitted
no `mismatched_services`. The result therefore does not distinguish a trading-service hash mismatch
from invalid bounded output while deriving a Compose hash. Local remediation now collects all three
trading-service results and emits separate fixed `invalid_services` and `mismatched_services` lists
without hashes or subprocess output. Under fresh authorization, exact release
`e32b74775e4dd4a5273de12f01a821e5056e01b4` classified SPX as mismatched and NDX/XSP as invalid
while deriving reviewed Compose hashes. It retained protected evidence, removed exact temporary
paths, and made no live mutation. No candidate set exists, and the current SPX/NDX/XSP set remains
unaccepted as a replacement baseline. The operator chose the runtime-baseline path. The local
`runtime-baseline-capture` keeps every paper/direct health, process-uniqueness, ownership,
no-writer, and no-staging gate; requires each live trading container to use its exact reviewed config
file through a read-only bind; and binds the three runtime records, actual image IDs, and exhaustive
Compose observation into one candidate digest. Compose invalid/mismatch classifications remain
explicit but are not acceptance gates. The strict Compose-equality capture remains unchanged. This
runtime path is local and fake-tested only until a new exact release receives fresh read-only Helios
authorization. Under that authorization, exact release
`1e5ccfe7d72478ef73da5b54e4ede18baa697345` failed closed at
`runtime_config_mounts` before producing a candidate. Its protected failure evidence was retained,
the temporary paths were removed, and no live mutation occurred. The exact-host-path requirement is
overstrict for a runtime baseline because a different bind source may contain the identical reviewed
file. Local remediation now requires the expected read-only destination and either exact source
identity or bounded regular-file content equality, emits exhaustive fixed per-service classifications,
and binds them into the candidate digest. Under fresh authorization, exact release
`8c7070debb11733092980f7854e66b7678c8dd86` failed closed and named SPX, NDX, and XSP as invalid
config-mount services. The reviewed Compose short-form mounts omit read-only flags, so accepting the
current runtime required an explicit policy decision. The operator accepted writable config mounts
as a recorded runtime-baseline exception. Local capture now requires exact bounded config contents,
classifies every service independently by content relation and read-only/writable permission, and
binds both classifications into the candidate digest. Under fresh authorization, exact release
`dd1d9ef76b448cd0582f9408204e9e7f1eb8d380` produced candidate digest
`6872c3582cf728f67acba78bf5f7e226b735c40a4be09ea27c135c7641e5320d`. SPX/NDX/XSP use the
exact reviewed config sources with writable permissions; Compose remains SPX mismatched and NDX/XSP
invalid. Every runtime-safety gate passed, the strict reader re-derived the same digest, protected
evidence was retained, exact temporary paths were removed, and no live mutation occurred. The
operator then explicitly accepted that exact digest as the new runtime baseline together with
writable SPX/NDX/XSP config mounts and the Compose exceptions `SPX=mismatched` and
`NDX/XSP=invalid`. The protected artifact at
`/opt/butterflyguy/.runtime-baseline-evidence-20260805-dd1d9ef.json` is the authoritative accepted
baseline evidence. No live mutation occurred. The current isolated slice adds a fake-tested
runtime-baseline credential-proof adapter that consumes only that exact digest and stages reviewed
Python source in the existing SPX `/tmp` tmpfs without recreating the accepted container. Approval 1
for release `5a472b3da1feefbc1e592785839704b104e94c28` passed corrected preflight but failed closed
inside the generic staging-copy gate before native smoke or quiescence. Automatic exact restoration
passed, all temporary staging material was removed, two private failure states were retained, and no
credential/token read or Schwab request occurred. The local correction now uses `docker cp --quiet`
and distinct bounded target/copy/extract/digest failure codes. Fresh Approval 1 for release
`62d32ad73243a4bf36819f8e3c838e477c57611a` passed full preflight and then identified the exact
failure as `staging_copy_invalid`; target creation passed, but `docker cp` did not copy into the SPX
tmpfs. Automatic exact restoration passed again, all exact temporary material was removed, a third
private failure state was retained, and no smoke/quiescence/credential/Schwab action occurred. GNU
`dd` 9.7 is present in the running image. The local correction now replaces `docker cp` with a
bounded `docker exec -i ... dd` byte stream followed by the existing in-container SHA-256 check.
Local review of release `768dc6d21c6121210e7ed597026ecf49bbb1b99f` then found that its digest gate
verified the fixed legacy `/app` target rather than the caller's own root target, so the
runtime-baseline path would have staged correctly under `/tmp` and failed closed at
`staging_digest_invalid`. No live attempt was made under that release. The digest gate now uses the
caller's archive target, and new tests cover the runtime root target and reject a legacy-path digest
reply in runtime mode. Fresh Approval 1 for release `a54c2343c2ac8cb2e20d6c60329f1a1b1edd720e`
first failed `prepare` at `baseline_mismatch` because archive-extracted config paths classify the
runtime config mounts as `content_match` while the accepted digest records `exact`; the corrected
`prepare` passed with the live config paths. The single authorized attempt then streamed, extracted,
and digest-verified the archive under `/tmp` — clearing both prior staging stops — and failed at the
native smoke check, reported as generic `subprocess_failed`. Automatic exact restoration passed,
services were never quiesced, and no credential/token read or Schwab request occurred. The cause is
that `schwab_gateway/__init__.py` eagerly imports `api`, which the minimal reviewed archive
deliberately omits, so importing `credential_probe` raises `ModuleNotFoundError`. The local
correction makes `create_app` resolve through a module-level `__getattr__`, propagates the staged
command's own bounded failure code from `_run_exact_json` when the payload is exactly one of the
fixed staged codes, and adds an isolation test that imports the reviewed subset in a separate
interpreter with only the `_ARCHIVE_PATHS` member set on `sys.path`. Fresh Approval 1 for release
`ca0d3481dbb53edfde5b1ba9ee03d61935ca4bad` reached `approval_1_ready` on the first `prepare` and then
passed staging, the bounded native smoke check, and the refusal gate for the first time, confirming
that correction. It failed closed at `watchdog_invalid` while arming the hard watchdog because
`sudo -n` requires a password for the operator account on the non-interactive proof path. Automatic
exact restoration passed, no transient unit remained, quiescence never started, and no
credential/token read or Schwab request occurred. The account has `Linger=yes` and a running user
manager, so the watchdog can move to `systemd-run --user`/`systemctl --user` without privilege
escalation; preflight must also gate watchdog-arming capability before quiescence. An authorized
bounded capability probe confirmed a `--user` transient timer arms, reports active, cancels, and
leaves no residual unit, and that such a run accepts `--uid`/`--gid` and emits byte-identical output.
The local correction moves every watchdog command to `systemd-run --user`/`systemctl --user`, removes
all `sudo` use, and adds `_require_watchdog_capability` to `prepare` so a watchdog prerequisite fails
in preflight rather than inside the one authorized attempt. Fresh Approval 1 for release
`cc614567b035f8a62cd9355ed3302eb11db44012` passed that new capability gate on the host and then
passed staging, native smoke, the refusal gate, and `watchdog` for the first time. It armed the hard
watchdog, disabled the keepalive, stopped NDX, and failed closed at `single_writer_invalid` before
XSP was stopped or SPX suspended, because Docker CLI 29.6.2 writes `Flag --time has been deprecated,
use --timeout instead` to stdout and the gate requires exactly the container name. Automatic exact
restoration passed, NDX restarted clean, and no credential/token read or Schwab request occurred. The
local correction switches quiescence to `docker stop --timeout` and adds
`_require_docker_stop_output_shape` to `prepare`, which proves the stop command writes nothing to
stdout using a container name that must not exist. Fresh Approval 1 for release
`b825f5f2a022d0c2d2d463295dd63e2dc522fee7` then passed both new gates, staging, native smoke, the
refusal gate, watchdog arming, and keepalive disablement, and stopped both NDX and XSP before failing
closed at `signal_invalid`. The SPX container's init is the application itself, and the kernel
ignores a default-action signal sent to a PID-namespace init from inside that namespace, so the
staged `os.kill(1, SIGSTOP)` did nothing. Automatic exact restoration passed and no credential/token
read or Schwab request occurred. Suspension is now symmetric with the already host-delivered resume:
`_signal_spx` issues `docker kill --signal STOP|CONT`, and `prepare` gains
`_require_spx_signal_capability`, which proves the command with a no-op `CONT`. Fresh Approval 1
for release `a1ce6eb6543c7654132347679cb608e6145767ff` then passed every gate and suspended SPX for
the first time, returning `approval_2_required`. Approval 2 was granted inside the 120-second window
for exactly one credential/token read and one AAPL quote; the staged probe exited nonzero and was
recorded as `credential_proof_failed` with `attempt_count=1`, `retry_count=0`, and
`information_exposure=pass`. Because only the return code is inspected, the state does not record
whether the probe reached the token read and Schwab request, so this must be treated as a possible
real credential/token read and the prior no-read claim no longer holds. Automatic restoration passed
24 of 26 checks — all fingerprint, image, config-content, health, uniqueness, ownership, and
keepalive/cron checks — and failed only `restoration_errors` with `spx=6, ndx=0, xsp=0`, returning
`restoration_failed_paused` and pausing all three services fail-closed. Those six markers match the
benign post-pause burst recorded on 2026-08-04. The rollback owner authorized the resume; all three
services unpaused with zero fresh filtered errors over 30 seconds, one process each, staging absent,
keepalive intact, and no residual watchdog unit. Exact temporary paths were removed and the
mode-`0600` state and all baseline evidence were retained. Both defects from that window are now
corrected locally. The credential proof no longer collapses every failure into one stderr message:
it emits exactly one of seven fixed codes on stdout, nothing on stderr, and a nonzero exit, split so
that `probe_import_failed`, `probe_settings_invalid`, and `probe_sdk_import_failed` prove no token
read occurred while `probe_token_invalid`, `probe_client_construction_failed`, `probe_quote_failed`,
and `probe_state_invalid` prove one was reached. The adapter taxonomy that already distinguished
construction from operation is surfaced through a fixed `reason` literal on
`GatewayCredentialProbeError`; `TokenManagerState` was explicitly rejected as a ride-along field
because carrying it would widen the shared staged-payload schema for every staged command.
`_approval_2_execute` now propagates the probe's own code through `_staged_failure_code`, with
stderr, malformed payloads, extra fields, unlisted codes, and codes belonging to other staged
commands all collapsing to `credential_proof_failed`. The success line and the argparse refusal
behaviour are byte-identical to before. The restoration error gate now counts a window that begins
`RESUME_SETTLE_SECONDS` after all three services were running again, so the recorded post-resume
marker burst is excluded by time rather than by an allowance, and fresh errors raise the distinct
`restoration_errors_detected` instead of `subprocess_output_invalid`. Failed restoration now removes
the release archive but deliberately keeps the rollback override and cron snapshot for manual
recovery, and an early `prepare` reports `approval_window_pending` instead of the generic
`invalid_arguments`. Exact release `58a5b0d64a1cbf1665d09e664d12d1415fa3b10d` has archive SHA-256
`5c115f494c6224a0f8b463a9ba1d7f1ffcdd32b039fe2e4f01ef29aca2d44723`. Fresh Approval 1 and
Approval 2 then authorized one attempt for that exact release on Helios during
`2026-08-06T17:15:00Z`–`2026-08-06T18:15:00Z`, and both corrections are now host-proven. Under
Approval 1's authorization to read the real credential environment, a bounded presence-only check
emitted booleans showing the API key and secret key set and the SPX container's
`SCHWAB_TOKEN_PATH` set but **not absolute**, so `GatewayCredentialProbeSettings()` was certain to
raise; the staged probe inherits that container environment and nothing on its import path calls
`load_dotenv`. The operator was told the attempt would fail at that stage and chose to spend it to
prove the machinery. The first `prepare` was issued nine seconds early and returned the new
distinct `approval_window_pending` without creating a state file; a fresh state path returned
`approval_1_ready`. `approval1-execute` returned `approval_2_required` in 52 seconds, and
`approval2-execute` returned `probe_settings_invalid` in 65 seconds including restoration. That is
the first proof failure to name its own stage: it is raised before the `schwab.auth` import and
before any manager transaction opens the token store, so no token read and no Schwab request
occurred on this attempt. Because `schwab_gateway/config.py` is byte-identical between `a1ce6eb`
and `58a5b0d` and the earlier probe built settings at the same point, the 2026-08-06 failure would
have failed at the same gate — strong circumstantial evidence of a settings failure with no token
read, but not retroactive proof, so the withdrawn no-read claim stays withdrawn. The lock
hypothesis is ruled out by code: no live service path acquires `.tokens.json.lock`, so a suspended
SPX cannot hold it, and the token document is a regular non-symlink file at mode `0600`.
Restoration returned `restoration_passed` with per-service filtered error counts `spx=0`, `ndx=0`,
`xsp=0`; the resume burst fell inside `RESUME_SETTLE_SECONDS` and **all three services stayed
running**, so no mid-session pause occurred. Twenty-five of twenty-six checks passed with only
`proof` failing; both watchdogs cancelled and cron was restored at two keepalive entries. The
archive, rollback override, cron snapshot, extracted host source, and in-container staging are all
gone; the mode-`0600` state
`/opt/butterflyguy/.credential-proof-state-20260806-58a5b0d-r2.json` and every
`.runtime-baseline-evidence-*.json` are retained. The remaining defect — that the probe cannot
reach a token read in the SPX container as invoked — is now fixed in local source. `approval2-execute`
requires an explicit `--proof-token-path`, validated absolute, normalized, at most 255 printable
non-space ASCII characters, and passed only as a second `docker exec -e SCHWAB_TOKEN_PATH=...`
argument; the probe's absolute-path guard, the inherited-only handling of the two secrets, and every
live service configuration are unchanged. Validation runs before the attempt is claimed, so a
malformed path leaves `attempted=false` and `attempt_count=0` while the quiesced services are still
restored. A bounded `docker exec ... test -f` gate then proves the document exists, because
otherwise a mistyped path would return `probe_token_invalid` and falsely assert that a token read
occurred. The new `proof_token_path_invalid` is registered in `_RESULT_CODES`, mapped to the `proof`
check, and adoptable by `_approval_2_execute`, but is deliberately excluded from
`_STAGED_FAILURE_CODES` because no container payload may claim an operator-side gate. Exact release
`76317442402095df03009dabb3d4453bc73064d3` has archive SHA-256
`a499c3eca7c51e7d1381cfff29e3f2a1f5d83842afa8eb31348953be81954fbf`, reproducible bit-for-bit from
the commit. Under fresh Approval 1 and Approval 2 naming `/app/tokens.json`, with the rotation risk
acknowledged, that release ran on Helios during `2026-08-06T18:00:00Z`–`2026-08-06T19:00:00Z`.
`prepare` returned `approval_1_ready` first time, `approval1-execute` returned
`approval_2_required` in 51 seconds, and `approval2-execute` returned **`probe_token_invalid`** —
the first time a token read has ever been reached, since that code is raised from inside the probe
after the manager transaction opens the token store. Restoration passed again with per-service
error counts `spx=0, ndx=0, xsp=0`, 25 of 26 checks passed with only `proof` failing, and the token
document was **not** modified, so the rotation risk did not materialize. The document itself is
valid: positive `creation_timestamp` only 3.89 days old against the 7-day TTL, non-empty
`access_token`/`refresh_token`, regular non-symlink file at mode `0600`. The real cause is
`TokenPersistenceError` on the lock open: the containers set `read_only: true`, so `/app` is
read-only while `/app/tokens.json` is writable only as its own bind mount point, and
`AtomicTokenManager` creates both its lock and its atomic replacement as siblings of the document.
Relocating the temporary file cannot fix it because `os.replace` cannot cross filesystems, so the
in-container proof path cannot work for any of these services. The proof step is therefore now
executed on the host, where `/opt/butterflyguy` is writable by the same uid the containers use:
`_approval_2_execute` runs the probe under an operator-named `--proof-interpreter` with `PYTHONPATH`
and `SCHWAB_TOKEN_PATH` overridden in a copy of its own environment, with no `docker exec` and no
credential on a command line. Four gates — credential-environment presence, interpreter validity,
per-member reviewed-source equality against the archive, and a token document that is a private
regular file **in a writable directory** — run in `prepare` as well as immediately before the probe,
under the new `proof_prerequisites` check and the fixed codes `proof_environment_invalid`,
`proof_interpreter_invalid`, `proof_source_invalid`, and `proof_token_path_invalid`; a host native
smoke runs the existing bounded command under the same interpreter. Verified read-only on Helios:
the venv interpreter passes its gate and is a symlink, `scipy.special` and `schwab.auth` import
under it, and the token directory is writable. `uv run pytest` is 761 passed, 1 skipped, and
`uv run ruff check .` is clean. This host-execution change has no release archive and has never run
against Helios.

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
- A successful credential proof will very likely trigger an SDK refresh, and the manager durably
  rewrites the live token document. The standing rules forbid copying the token, so there is no
  rollback for a damaged document; recovery would be a manual Schwab re-authorization. The write
  path validates, `fsync`s, and atomically replaces at mode `0600` and is extensively fake-tested,
  so the risk is low, but it is unmitigated and must be acknowledged before the next approval.

## Next Exact Action

Cut a release archive for the host-execution commit, then obtain fresh Approval 1 and Approval 2 and
run one supervised attempt on Helios. Approval 1 must name the new host-execution commit, not the
follow-up commit that records the release identifiers. Approval 2 must name the **host** token
document `/opt/butterflyguy/tokens.json` — no longer the in-container `/app/tokens.json` — and must
re-acknowledge the unmitigated token-rotation risk, which is now live because the manager can
actually persist.

**The operator must run `prepare` and `approval2-execute` personally, with `SCHWAB_API_KEY` and
`SCHWAB_SECRET_KEY` exported.** They are absent from a non-interactive `ssh` session, and the agent
may not source or inspect `.env`, so the agent cannot supply them or run those two commands. Expect
`proof_environment_invalid` in preflight if they are missing. `approval1-execute` needs no
credentials and can be run normally, but the 120-second approval watchdog means it must be chained
to `approval2-execute` in the same invocation.

That attempt will be the first able to complete a token read, construct a client, and issue the
quote. Realistic outcomes are `credential_proof_passed`, `probe_client_construction_failed`, or
`probe_quote_failed` — the last being the only code proving a Schwab request was issued.

Already host-proven and not in need of re-proof: bounded staged-code propagation, the settled
restoration error window (zero filtered errors, no pause, twice), `approval_window_pending`, the
whole staging/smoke/refusal/watchdog/quiescence path, and the token read itself. Still unproven
against the live host: the host-executed proof step, its four new prerequisite gates, and the
failed-restoration cleanup split, since restoration has not failed under either release.

Issue `prepare` at or after the window start — not before — and always against a fresh state path.
No gateway deployment, trading action, configuration change, order/account operation, or cutover is
authorized.
