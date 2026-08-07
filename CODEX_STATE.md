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
`uv run ruff check .` is clean. Exact release `22643615f2125107dba8a54fd4cf1a0e5b8f939e` has archive
`/tmp/butterfly-gateway-multi-consumer-foundation-2264361.tar` at mode `0600` with SHA-256
`cf11fdfcdfc23585acf166293d3ce8e137eb2bc4b07302a1824d6d227c404467`, reproducible bit-for-bit from
the commit. That release reached Helios preflight in an approved window and stopped twice without
mutating anything, both times with `proof.attempted=false` and `attempt_count=0`: first at
`proof_environment_invalid`, because the credentials were not exported in the operator's shell,
which is what the gate exists to catch; then at `archive_invalid`, a defect in the release, because
`_require_host_reviewed_source` hashed every reviewed member with `MAX_SOURCE_BYTES` while `uv.lock`
is 481750 bytes, and the archive-member hash sat outside the gate's failure boundary so a generic
code escaped where `proof_source_invalid` was intended. Both hashes are now bounded by
`MAX_ARCHIVE_BYTES` and taken inside the boundary, with a regression test that builds a real tar
whose oversize member is verified and then tampered with. Exact release
`ad8394277f9ee224b4d8e19f77f7599dc5b0f4fc` has archive
`/tmp/butterfly-gateway-multi-consumer-foundation-ad83942.tar` at mode `0600` with SHA-256
`679800b5cdf98b0f523023aed56681b095c0b47b0171dd85baabb06588c09d87`; `_validate_archive` accepts it,
the archived operator member matches the checkout, and the gate that failed on Helios passes against
it locally. `uv run pytest` is 762 passed, 1 skipped, and `uv run ruff check .` is clean. This
release then ran on Helios under fresh Approval 1 and Approval 2 during
`2026-08-06T21:10:00Z`-`2026-08-06T23:10:00Z`, with Approval 2 naming the host token document
`/opt/butterflyguy/tokens.json` and the operator accepting the rotation risk. `prepare` returned
`approval_1_ready`, `approval1-execute` returned `approval_2_required` in 55 seconds, and
`approval2-execute` returned **`credential_proof_passed`** with `quote_count=1`,
`token_state=ready`, `attempt_count=1`, `retry_count=0`, and `information_exposure=pass`. All 27
checks passed, the first window with no failed check. One real AAPL quote was retrieved from Schwab
through `AtomicTokenManager` and `LockedSchwabClientAdapter` using the real credential environment
and the real token document, which is the objective this standalone proof was built for. The
manager also performed the first gateway write of the production token: the document was atomically
rewritten at `21:25:29.524Z`, three seconds into the probe, with the keepalive disabled and its
hourly schedule not falling there. Afterwards it is a regular non-symlink file at mode `0600` with a
valid envelope and an unchanged `creation_timestamp` of 4.03 days, since `schwab-py` preserves that
field across refreshes, so the seven-day refresh life is unaffected. The advisory lock file
`/opt/butterflyguy/.tokens.json.lock` now exists, owned by `billy` at mode `0600`, zero bytes, held
by no process; it is expected to persist, so its presence alone is no longer a stale-lock signal.
Restoration passed with per-service error counts `spx=0, ndx=0, xsp=0` for the third consecutive
window, both watchdogs cancelled, cron restored at two keepalive entries, SPX still on its original
container and recorded image and never recreated, NDX/XSP restarted healthy, no staging directory,
and no residual watchdog unit. Temporary inputs and the extracted host source were removed and the
mode-`0600` state was retained. Separately, a credential value was echoed to a visible shell prompt
during this window. Rotation was then evaluated and deliberately declined. The Schwab developer
portal offers no in-place secret regeneration, so replacing the credential requires provisioning a
new app and waiting out its approval. Bounded read-only checks established the exposure surface: the
app key and secret are the application's identity, not the account's, and Schwab issues tokens only
through the user-authorized code flow, so account access additionally requires either an interactive
login with MFA or the refresh token in `tokens.json` — neither of which was exposed, the document
having stayed mode `0600` and never printed or copied. Helios `~/.bash_history` had mtime
`2026-08-04T04:30:38Z`, predating the window, and matched no named-variable or bare-token shape, so
the value was never flushed to disk there; two interactive login shells from `21:07` and `21:13`
still held it in memory and would have appended it on clean exit. The surviving copies are the
operator's terminal scrollback and the 2026-08-06 session transcript. The operator accepted the
residual risk and retained the credentials. The remaining exposure is a loss of defence in depth:
the secret is now the only factor standing between a future token exposure and account access.

Phase 3's offline prerequisites are now built on branch
`codex/schwab-gateway-phase3-shadow-surfaces`, entirely fake-backed. Before this slice the gateway
served the equity scanner's quote surface only: `DirectSchwabQuoteUpstream` wraps
`EquityQuoteProvider.get_equity_quotes`, which in production is called only by
`refresh_equity_universes.py` and `run_morning_scan.py`. The butterfly collector reads
`get_spot_price` and `get_option_chain`, neither of which the gateway could serve, so no shadow
comparison of the collector was possible. The gateway now also serves `GET /v1/spot` and
`GET /v1/chain`, the client exposes `get_spot` and `get_chain_metadata`, and
`SCHWAB_GATEWAY_SHADOW_READS` — the flag Phase 3's own rollback names — exists for the first time,
defaulting to false. `/v1/chain` returns fixed-shape metadata only and never contract rows; full
chain transport remains Phase 4. Nothing is wired: no service constructs the shadow decorator, and
`run_live.py`, `run_collector.py`, and `data/collector.py` are untouched. Phase 3's four
dependencies — a production-capable single token manager, a safe gateway deployment host, capability
probe approval, and a read-only consumer key — remain unmet, and none is solvable offline.

A following offline slice on the same branch corrected a defect introduced by `c8c673e` and made the
suite a trustworthy gate again. `extract_chain_metadata` counted a strike whose option list was empty
into `strike_count` while contributing no contracts to `call_contract_count`/`put_contract_count`, so
the two count fields disagreed about whether that strike existed. `strike_count` is now defined as
"distinct strikes carrying at least one contract", which is what both live parsers can actually act
on, and the relationship between all three parsers is pinned by differential tests over shared
synthetic fixtures. Golden recorded inputs remain unavailable: `data/chains/` holds already-parsed
rows, no raw `callExpDateMap` payload exists outside test files, and none can be captured offline, so
migration-doc line 199 is still unsatisfied and the three parsers are documented rather than unified.
The stale `infra/docker-compose.yml` hash pin was re-recorded at `5055991` after proving that
commit's diff is gateway-unrelated. `docs/architecture/schwab-gateway-deployment-options.md` now
enumerates the four candidate gateway hosts for the operator. Nothing was wired, deployed, or run
against Schwab.

The operator then chose **Option A — Helios, containerized** — and authorized its offline package.
The gateway can now serve real Schwab market data: `run_schwab_gateway.py` gained `--serve-live`,
gated behind `--authorize-real-credential-read` and `--confirm-single-token-writer`, which builds the
three read surfaces over `AtomicTokenManager` and `LockedSchwabClientAdapter`. `--demo` remains
available and unchanged, and exactly one mode must be chosen. A separate `schwab_gateway_live`
Compose service under the non-default `gateway-live` profile carries the same hardening as the demo
service on a distinct port, container name, and token mount. This is built and tested offline only:
no Docker command was run, Helios was never contacted, no credential or token was read, and no
Schwab request was made. Nothing is wired to any consumer and `SCHWAB_GATEWAY_SHADOW_READS` still
defaults to false.

The live-serving slice left the credential proof's reviewed archive untouched: `live_provider.py` is
a new non-member and `run_schwab_gateway.py` was never a member. A following slice deliberately
edited one member, `scripts/credential_proof_fingerprint.py`, to stop the native smoke check
inheriting `SCHWAB_TOKEN_PATH`; see Next Exact Action for the archive-hash consequence.

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

## Phase 3 Shadow Surfaces (unwired, default off)

- `schwab_gateway/api.py`: `GET /v1/spot` and `GET /v1/chain` follow the quote handler's exact
  order — capability, parameter validation, readiness, admission, then the upstream call inside
  `asyncio.timeout`. `_serve_upstream` holds steps 3–5 once for both new routes; the quote handler
  is unchanged.
- Upstream injection decision: `create_app` keeps its single positional `upstream: QuoteUpstream`
  and gains keyword-only `spot_upstream` and `chain_upstream`, each defaulting to a fail-closed
  stub that raises `UpstreamUnavailableError` (503). A widened composite protocol was rejected
  because Python protocols are not enforced at runtime, so every existing fake, test, and the demo
  runner would have satisfied it structurally while returning `AttributeError` on a real spot or
  chain request. Separate optional upstreams make each surface's availability an explicit
  deployment declaration and keep every current caller and default unchanged.
- `gateway_client/models.py`: `SpotV1`/`SpotResponseV1` and `ChainMetadataV1`/
  `ChainMetadataResponseV1` — `extra="forbid"`, frozen, `schema_version: Literal["1.0"]`,
  timezone-aware timestamp validators, nonnegative age and count validators, nullable data, and a
  `data_quality_flags` tuple.
- `gateway_client/chain_metadata.py`: one pure `extract_chain_metadata` shared by the gateway's
  chain upstream and the consumer-side comparator, so both derive identical counts from the same
  raw payload. It mirrors the collector's expiration-key filter and never returns contract rows.
  `strike_count` counts distinct strikes carrying at least one contract; a strike with an empty
  option list is excluded, matching `iter_chain_options`' `if options:` guard and the empty row set
  `_parse_chain_response` produces for it. The original `c8c673e` implementation added the strike
  before the length check, so `strike_count` and the contract counts disagreed about that strike.
  This never produced a false shadow discrepancy — `shadow.py:_shadow_chain` runs the same function
  on both sides — but it changed what the metadata meant.
- `tests/test_chain_parser_parity.py`: differential tests over shared synthetic fixtures pinning the
  three parsers against each other. Asserted: `call_contract_count + put_contract_count` equals the
  row count `_parse_chain_response` writes for the same payload and expiration, with the per-side
  split also matching; `strike_count` equals both the distinct strikes `iter_chain_options` yields
  across both directions and the distinct strikes the collector's rows cover; all three select the
  same expiration when one map holds several. Fixtures cover multiple contracts at one strike, a
  strike with an empty option list, several expirations, a non-numeric strike key, both maps present
  but empty, and `callExpDateMap` present with `putExpDateMap` absent. Two divergences are recorded
  as assertions rather than reconciled: a non-numeric strike key is skipped by the metadata and
  raises `ValueError` in both live parsers, and a payload carrying neither map is tolerated by both
  live parsers but refused by the metadata. These are synthetic fixtures, not golden recorded
  inputs; migration-doc line 199 remains unsatisfied and no consolidation is licensed.
- `schwab_gateway/upstream.py`: `SpotUpstream`/`ChainMetadataUpstream` protocols,
  `DirectSchwabSpotUpstream`, and `DirectSchwabChainMetadataUpstream`, reusing the existing
  `UpstreamUnavailableError`/`UpstreamMalformedError` classification. `get_spot_price` returns a
  bare float, so a direct spot read carries no upstream event time and is reported `stale` with
  `missing_event_timestamp` rather than claiming a freshness it cannot prove.
- `gateway_client/client.py`: `get_spot` and `get_chain_metadata` reuse every existing error class
  and the explicit timeout, with no retries. `get_quotes` is untouched.
- `gateway_client/shadow.py`: `ShadowComparingMarketDataProvider` wraps a
  `CollectorMarketDataProvider`, returns the direct result unconditionally on every path, and
  swallows every gateway failure. Discrepancies map to the four migration-doc categories through a
  closed code table: timeouts and unprovable freshness are `timing`, a known-stale differing value
  is `cache`, a provably fresh differing value or an invalid contract is `parsing`, and every
  gateway-reported error is `upstream`. Diagnostics are fixed codes, classifications, operation
  names, and field names only.
- `gateway_client/config.py`: `SCHWAB_GATEWAY_SHADOW_READS` defaults to false and, like gateway
  mode, requires the URL and key when enabled. `SCHWAB_ACCESS_MODE` still defaults to `direct` and
  is still consumed by no service.
- `tests/test_gateway_collector_surfaces.py`, `tests/test_gateway_shadow_reads.py`, and additions
  to `tests/test_gateway_contract_boundaries.py` and `tests/test_gateway_models.py`: typed success
  through the real in-process aiohttp app, 401/403/400/503/429/504/503/502 coverage per route, a
  route table with no account or order surface, fail-closed undeclared surfaces, client status
  classification with no retry, and proof that the only importers of `schwab_gateway`/
  `gateway_client` anywhere in `src/` are `run_schwab_gateway.py` and
  `probe_schwab_gateway_credentials.py`.

## Option A Live Serving (built offline, never deployed)

- `schwab_gateway/live_provider.py`: `LockedSchwabMarketDataProvider` exposes exactly
  `get_spot_price`, `get_option_chain`, and `get_equity_quotes` — no account, order, transaction,
  movers, or streaming method exists to call. Each read runs one
  `LockedSchwabClientAdapter.execute` on a worker thread via `asyncio.to_thread`, so the aiohttp
  loop is never blocked by the synchronous adapter. All batches of a multi-batch quote request share
  one transaction, so the token lock is taken once. No retries: the direct path's three-attempt
  backoff would multiply the time every other caller waits inside a held lock.
- `GatewayUpstreamSettings` lives in that new module rather than in `schwab_gateway/config.py`,
  deliberately, because `config.py` is a member of the credential proof's reviewed archive and
  editing it would change a release hash for a proof that is already complete.
- `extract_spot_price` duplicates `SchwabClientWrapper.get_spot_price`'s extraction
  (`data/schwab_client.py:122-130`), including the `lastPrice`/`mark`/`closePrice` preference, the
  unprefixed-symbol fallback, and the falsy-zero fall-through. `data/schwab_client.py` is not
  modified to share it; the duplication is pinned by a differential test that runs both against the
  same six payload shapes, the same technique used for the three chain parsers.
- `scripts/run_schwab_gateway.py`: `--serve-live` requires `--authorize-real-credential-read` and
  `--confirm-single-token-writer`, and exactly one of `--demo`/`--serve-live` must be given.
  Refusal happens in argparse before any setting, key file, or token is touched. `build_live_app`
  injects the real `AtomicTokenManager` as the readiness provider and declares all three upstreams.
- The startup `manager.load()` in `build_live_app` is load-bearing, not bookkeeping. `/ready` and
  every route gate on `TokenManagerState.READY` (`api.py:244`, `:270`, `:315`), and the manager only
  reaches READY inside a transaction, so without priming, no request could be admitted to produce
  the transaction that would make it ready and the gateway would answer 503 forever while looking
  healthy at the process level. A missing or invalid token fails the build closed.
- `infra/docker-compose.gateway.yml`: new `schwab_gateway_live` service, profile `gateway-live`,
  container `butterfly_schwab_gateway_live`, port `127.0.0.1:8011`, with the demo service left
  byte-identical on `gateway-foundation`/8010. It carries the same `read_only`, `cap_drop: ALL`,
  `no-new-privileges`, and non-root uid. The token **directory** is bind-mounted writable at its own
  host path with no default value, because `AtomicTokenManager` creates its lock and its atomic
  replacement as siblings of the document and `os.replace` cannot cross filesystems — a
  document-only bind under `read_only: true` is exactly what stopped the in-container credential
  proof.
- `infra/schwab-gateway-keys.example.json`: placeholder template for the internal keys file, which
  is Phase 3 dependency 4. Schema-checked against the real loader's rules; the real file is never
  committed.
- `docs/architecture/schwab-gateway-option-a-deployment.md`: prerequisites, the single-writer
  problem, read-only preflight, start, verify, rollback, and five known limitations.
- `TokenReadinessRecovery` closes the readiness latch that the first Option A slice shipped with.
  It is registered as an aiohttp `cleanup_ctx` entry in live mode only — the demo app's readiness is
  a static fake with nothing to recover — and retries `load()` on a 30-second interval, but only
  while the manager is not READY, so a healthy gateway never touches the token document on this path
  and a latched one cannot spin. Its interval is a constructor argument rather than a
  `GatewaySettings` field, for the same archive-hash reason as `GatewayUpstreamSettings`.
- `tests/test_gateway_live_provider.py` and `tests/test_gateway_live_runner.py`: 52 tests covering
  the read-only surface boundary, protocol signature match, one-transaction-per-call, session
  teardown on both success and failure, absence of retries, single-transaction batching, the
  spot-extraction differential against the live client, secret-free settings reprs, argparse
  refusal, demo-mode isolation, real-manager readiness, startup priming, fail-closed build on an
  unusable token, no client construction at startup, a route table with no account or order
  surface, and a real latch-and-recover cycle that loads a manager, deletes its token to latch it,
  proves recovery fails while the cause persists, restores the document, and proves the next tick
  returns it to READY without any request.

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
- A token-level failure takes the live gateway not-ready for up to one recovery interval. When a
  transaction fails with a `TokenManagerError`, `_record_load_failure` moves the manager out of
  READY, and every later request is refused with `gateway_not_ready` — including the request that
  would have produced a recovering transaction. `TokenReadinessRecovery` now retries `load()` every
  30 seconds while not ready, so a transient lock timeout clears without a restart; a genuinely
  missing, expired, or corrupt token stays fail-closed and keeps retrying harmlessly. Schwab-side
  errors never latch it, because `SchwabClientOperationError` is not a `TokenManagerError`. The
  residual exposure is the interval itself, which is harmless for a shadow reader and should be
  re-evaluated before anything depends on the gateway for a trading decision.
- A live gateway becomes a second writer of the production token document. `AtomicTokenManager`
  takes an exclusive advisory lock, but the direct services do not acquire `.tokens.json.lock`, so
  the lock protects gateway writers from each other, not from SPX/NDX/XSP or the keepalive cron. The
  first window should be outside market hours with the keepalive disabled.
- Container runtime packaging still needs proof on a host where starting Docker cannot affect
  live or unrelated services.
- A successful credential proof will very likely trigger an SDK refresh, and the manager durably
  rewrites the live token document. The standing rules forbid copying the token, so there is no
  rollback for a damaged document; recovery would be a manual Schwab re-authorization. The write
  path validates, `fsync`s, and atomically replaces at mode `0600` and is extensively fake-tested,
  so the risk is low, but it is unmitigated and must be acknowledged before the next approval.

## Next Exact Action

The credential proof is complete. No further proof window is needed.

Credential rotation was evaluated and declined; see Current Phase. One operator decision remains and
it is not a proof step: whether the proven manager and adapter should now move toward Phase 3 shadow
reads, which is a separate reviewed change requiring its own approvals. Nothing in the completed
proof authorizes a gateway deployment, a shadow read, a consumer cutover, or any account or order
operation.

The first deferred code item is done: `_require_proof_credential_environment` is now the first
statement in `prepare`'s failure boundary, ahead of archive validation, Docker inspection, and the
docker-stop, SPX-signal, and watchdog capability probes, with a test that records call order and
fails if anything costlier runs first. One deferred item remains: the container staging step is now
vestigial for the proof itself, because nothing executes from it, though it still proves the image
can host the reviewed subset and restoration still requires its absence. Removing it is not
recommended while no further proof window is planned, since it would weaken what restoration
verifies in exchange for nothing.

The next decision is wiring. `ShadowComparingMarketDataProvider` exists and is proven against the
real in-process gateway, but nothing constructs it. Wiring it into `run_live.py` behind
`SCHWAB_GATEWAY_SHADOW_READS` would make gateway code reachable from a live trading entry point for
the first time and needs its own approval. It is also blocked in practice: with no deployed gateway
there is nothing for the flag to point at, so wiring should follow a deployment host, not precede
it. Two design points to settle at wiring time: the comparator awaits the gateway read after the
direct read returns, adding gateway latency to each collector cycle; and `GET /v1/history` is
deliberately absent, so `get_daily_bars` (`data/collector.py:117`) has no shadow surface.

The deployment host that wiring waits on is now written up for the operator in
`docs/architecture/schwab-gateway-deployment-options.md`. It evaluates four candidates — Helios
containerized, zeus containerized, a separate/new host, and Helios as a `systemd --user` service —
with requirements, risks, recorded evidence, and the smallest safe first step for each, and states
which of Phase 3's four dependencies each moves. Its central finding is that no host option is
sufficient by itself: `run_schwab_gateway.py` refuses to start without `--demo`, so no real-backed
serving mode exists on any host, and the `secrets/schwab-gateway-keys.json` that
`infra/docker-compose.gateway.yml` mounts has never been created. The `systemd --user` option is the
cheapest to prove safe, because the credential proof already host-proved on Helios that a `--user`
transient unit arms, reports active, cancels, and leaves no residual unit without privilege
escalation, and that the account has `Linger=yes`; its cost is no image pinning, no Compose-level
isolation, and a restoration story that none of this project's existing container-shaped restoration
checks cover. The one bounded read-only check the brief asks for next is whether a `--user` unit on
Helios can bind and release `127.0.0.1:8010`, emitting only two booleans — the capability probe
already run proved a timer, not a socket. The brief recommends no host and authorizes nothing.

The operator selected Option A and its offline package is complete: a live serving mode, an isolated
Compose service, a keys template, and a runbook. What remains before anything can actually run on
Helios is not code. It is, in order: issue the internal consumer keys and create
`secrets/schwab-gateway-keys.json` at mode `0600`; decide whether a second token writer is
acceptable and when; obtain an approved window; and run the read-only preflight in the runbook.
The readiness latch described in Risks should be fixed before the gateway is depended on, though it
does not block a first supervised bring-up, where a restart is an acceptable remedy. Wiring any
consumer and `GET /v1/history` both remain out of scope and unchanged by this slice.

Baselines on the current host: `uv run python -m pytest` is **930 passed, 1 skipped, 0 failed**, and
`uv run ruff check .` is clean. This is the first fully green suite recorded on any host. The prior
baseline here was 851 passed, 1 skipped, 2 failed; the parity slice added 24 tests and cleared the
Compose pin, the Option A slice added 48, and the readiness/environment slice added 7 more and
cleared the last failure. `uv run pytest` still cannot
spawn here because `.venv/bin/`'s console-script shebangs point at
`/mnt/Files/Projects/Python/Butterflyguy/.venv/bin/python`, a path that does not exist for the
current user, so `uv run python -m pytest` is used instead. The previously recorded 763 passed,
1 skipped baseline was taken on a different host and does not reproduce here.

`test_gateway_compose.py::test_staging_package_does_not_change_default_compose` is fixed. It pinned
the SHA-256 of `infra/docker-compose.yml` as recorded at `origin/main` `6179f2e`, and `5055991` — the
only commit to touch that file since, confirmed by `git log 6179f2e..HEAD -- infra/docker-compose.yml`
— edited it afterwards, so the pin was stale rather than violated. `git show 5055991 --
infra/docker-compose.yml` is a two-line change to `app_spx_candidate`: `restart: unless-stopped`
becomes `restart: "no"` plus an explanatory comment. It adds no gateway service, profile, mount, or
environment entry, so the assertion the test was written to make still holds. The pin is re-recorded
as `e006fa07f86e962c04231dc47a9a3830d8c28c5075c5c20536354c1dc6d14afc` with a comment naming both the
original `6179f2e` value and why it moved. `infra/docker-compose.yml` itself is unchanged.

`test_gateway_credential_proof_operator.py::test_host_native_smoke_runs_the_reviewed_operator_under_the_named_interpreter`
is now fixed, and its previously recorded cause was wrong twice over. It was never the venv
shebangs. The test passed in isolation and failed only in a full run, because `core/config.py:228`
calls `load_dotenv(env_file)`, which mutates the process `os.environ` for the remainder of the
session; `tests/test_config.py` alone is enough to trigger it, proven by running those two files
together. That looked like cross-test pollution, but the deeper reading is that the test was
catching a real product gap and passing vacuously in a clean environment:
`_proof_process_environment` copied `os.environ` wholesale, so the native smoke check inherited
whatever `SCHWAB_TOKEN_PATH` the operator's shell carried — and on a real Helios proof run the
operator does export exactly that. The fix is in the product, not the test:
`_proof_process_environment` now removes `SCHWAB_TOKEN_PATH` when the caller names no token path, so
a command with no business naming a token document cannot silently receive one. The approval-2
probe, which always names a path explicitly, is unchanged; it is the only other caller.

That edit changes one `_ARCHIVE_PATHS` member, `scripts/credential_proof_fingerprint.py`, so any
future release archive built from this branch will have a different SHA-256 than
`ad8394277f9ee224b4d8e19f77f7599dc5b0f4fc`'s
`679800b5cdf98b0f523023aed56681b095c0b47b0171dd85baabb06588c09d87`. That costs nothing today — the
credential proof is complete and no further window is planned — but a future proof window must build
and re-record its own archive rather than reuse the retained hash.
`graphify update .` remains skipped because the recorded binary does not exist for the current user.
The branch has never been pushed. On 2026-08-06 the accumulated change set landed on `main` as a
reviewed local fast-forward to `b9a6c61`: 62 commits, no merge commit, no rebase, squash, amend, or
reorder, and no remote interaction of any kind. `origin/main` is untouched at `6179f2e`.

The pre-merge review confirmed that nothing changes SPX/NDX/XSP runtime behavior. Paper/live flags,
risk limits, account guards, order routing, token handling, container entry points, resolved
dependencies, and the `infra/docker-compose.yml` profiles are all unchanged; `uv.lock` and
`Dockerfile` are not in the diff. Outside `graphify-out/` the change set is 16,560 insertions and 8
deletions, and only four files are modified rather than added. The single runtime-adjacent change is
`OptionChainCollector` receiving `DirectSchwabMarketDataProvider(schwab)`, a signature-identical
delegation shim over the same client instance that adds no retry, caching, state, or extra calls.
Gateway code remains disabled and isolated: no service imports `schwab_gateway` or `gateway_client`,
no entry point references them, and both new Compose files require an explicit `-f` plus a
non-default profile.

The four `graphify-out/` artifacts were taken from the branch. The discarded main working-tree
regeneration was a strict subset apart from nodes for `.claude/settings.local.json`,
`Fable_refactor/fly_Spec.html`, and the then-uncommitted `infra/` edits; those edits had been
uncommitted since 2026-07-28 and are now recorded separately in `5055991`.
