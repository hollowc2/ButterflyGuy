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

## Live Finding — SPX is on a divergent orphaned token document (2026-08-06, RETIRED 2026-08-08)

Retired by the Window A re-authorization on `2026-08-08`. All three containers now resolve
`/app/tokens.json` to host inode `1067463`. See "Window A Executed" below. The analysis that follows
is retained as the record of the finding.


Found by bounded read-only inspection while planning the Option A token-directory move. No
mutation was made and no token value was read; the comparison is by inode, mtime, SHA-256 prefix,
and the integer `creation_timestamp` only.

`butterfly_spx_app` binds `/opt/butterflyguy/tokens.json` to `/app/tokens.json`, but inside the
container that path resolves to **inode 1112240**, while the host path is now **inode 1067464**.
NDX and XSP both resolve to 1067464 and match the host document byte-for-byte by digest. SPX does
not: its digest differs and its mtime is `2026-08-06 21:00:03Z` against the host's
`2026-08-07 04:00:09Z`. `find -inum 1112240` under the repository root returns nothing, so SPX's
document is reachable from no host path at all — only the container's bind mount keeps it alive.

Cause: `AtomicTokenManager` and the keepalive replace the document with `os.replace`, which creates
a new inode. A container restart re-resolves its bind mount; a running container does not. NDX and
XSP were restarted during the 2026-08-06 credential-proof restoration and picked up the new inode.
SPX was deliberately never recreated — it was suspended with `docker kill --signal STOP/CONT` and
has `RestartCount=0` with `StartedAt=2026-08-04T21:14:26Z` — so it is still pinned to the inode that
existed before the proof's atomic rewrite.

Severity. All four documents report the same `creation_timestamp` age, 4.32 days, because
`schwab-py` preserves that field across refreshes. SPX is therefore on the same token lineage, not a
separate authorization, and shares the same seven-day refresh deadline — roughly 2.7 days from the
finding. Whether SPX can still refresh at all depends on whether Schwab invalidates a refresh token
when a newer one is issued; if it does, the keepalive's host-path refreshes have already retired
SPX's generation. The next occasion SPX will attempt a Schwab call is the following regular session.

Resolution — the divergence is benign and no action is required. A bounded field-level digest
comparison (SHA-256 prefixes only; no value printed, copied, or stored) shows the **refresh token is
identical across the host document and all three containers** at `c5f05cc3fe64`. Only SPX's
short-lived access token differs. SPX therefore holds the same, still-valid refresh credential as
everyone else and will refresh normally on its next Schwab call; the earlier concern that its
generation might already have been retired is disproved.

That the refresh token is unchanged after 4.32 days of hourly keepalive refreshes also establishes
that Schwab does not rotate the refresh token when it issues a new access token, which is consistent
with `schwab-py` preserving `creation_timestamp`. The practical consequence is that the divergence
costs nothing: each side refreshes its own access token from a shared refresh credential.

**No restart of `butterfly_spx_app` is warranted.** The remedy is free during the next
re-authorization window, which is already required.

This is a pre-existing production condition, not a gateway defect, and it is independent of every
gateway change. Nothing was mutated; the standing authorization for this session is read-only.

It also blocks the Option A token-directory move. Renaming the host document while SPX is pinned to
an orphaned inode would deepen the divergence, and the move additionally requires updating the bind
source for all three services in `infra/docker-compose.yml` and recreating them, because a bind
mount whose source path no longer exists does not fail loudly on the next `up`. Resolve the SPX
divergence first, then treat the token move as a planned live-service maintenance operation rather
than a file rename.

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
Compose service, a keys template, a runbook, and `scripts/issue_gateway_keys.py`, which generates
consumer keys, prints each plaintext exactly once, writes only SHA-256 digests at mode `0600`,
refuses to overwrite an existing path, and round-trips the result through the real
`InternalKeyAuthenticator` so a file the gateway would reject is never left behind.

Under an operator authorization limited to non-mutating commands, a bounded read-only preflight then
ran on Helios on 2026-08-06. Nothing was created, started, written, or changed, and no credential or
token value was read. Full results are tabulated in the Option A runbook. Everything Option A
depends on checks out: the token document is a regular non-symlink file at mode `0600` owned by uid
`1001`, its directory is mode `755` owned by uid `1001` and writable by the operator account, and
that account is itself uid `1001` — the same uid the containers run as — so the writable
token-directory design is sound on this host. SPX/NDX/XSP are all running on recorded images, `.env`
defines all three credential variable names, the keepalive cron has its two entries, and 45 GB is
free.

Three findings change the plan:

- **The gateway code is not on Helios at all.** Its checkout is branch `main` at `de84d91`, 64
  commits behind local `main`, so neither `infra/docker-compose.gateway.yml` nor any
  `schwab_gateway` source exists there, and the branch has never been pushed anywhere. Bringing
  Option A up is therefore not "start a container": it requires moving 64 commits onto the checkout
  of the machine running live trading, including `5055991`, which edits the live
  `infra/docker-compose.yml`. That needs its own plan and its own approval and is materially larger
  than the runbook originally assumed.
- **The Helios working tree is not clean, but nothing there is at risk.** Enumerated read-only,
  names only: two tracked modifications, `configs/universes/liquid.txt` and
  `configs/universes/liquid_meta.json`, which are weekly `refresh_equity_universes.py` output rather
  than human edits; 35 untracked entries, 33 of them retained credential-proof and runtime-baseline
  evidence artifacts, plus `.tokens.json.lock` and an `evidence/` directory; no stashes. None of the
  64 incoming commits touches either modified file, so a checkout update has no conflict to resolve.
  The evidence artifacts are **not gitignored**, so a careless `git add -A` there would commit
  private artifacts and the lock file; and any checkout update must not remove untracked files.
- **The token document lives at the repository root, which blocks the Compose design as written.**
  `/opt/butterflyguy` is simultaneously the checkout root, the evidence directory, and the directory
  holding `tokens.json`, so `SCHWAB_GATEWAY_TOKEN_DIR=/opt/butterflyguy` would bind-mount the entire
  source checkout read-write into the gateway container and largely defeat `read_only: true`.
  `AtomicTokenManager` needs write access to the document's directory for its lock and atomic
  replacement, and the trading containers avoid that only by binding the file itself — which is
  precisely why they cannot refresh and why the proof moved to the host. The recommended resolution
  is to move the token document to a dedicated directory, which costs a host-side change to the
  keepalive cron and the host proof path but does not affect the running containers. Accepting the
  repo-root mount is not recommended, and a separate gateway token document is rejected because it
  splits refresh against a seven-day refresh token. The live service must not start until this is
  decided; the Compose file has no default for the variable and will refuse rather than guess.
- **Helios is also 15 commits behind `origin/main`** and has nothing `origin/main` lacks, so the
  delivery chain is Helios `de84d91` → 15 → `origin/main` `6179f2e` → 49 → local `main` `ba2e6bc` →
  the branch commits.
- **Port 8010 is bound** by the unrelated `halt_scanner` container, so the demo service as
  configured cannot bind. The live service's 8011 is free, so Option A itself is unaffected.

The sequence is now written up in `docs/runbooks/token-reauthorization-and-gateway-enablement.md`
as two deliberately separate windows. This revises the earlier advice to bundle everything into one.
Bundling looked attractive because both need the containers recreated, but the token relocation
requires source changes to `tools/schwab_token_keepalive.py` (`TOKEN_PATH = ROOT / "tokens.json"`)
and `tools/auth_init.py` (writes `tokens.json` relative to the working directory), which in turn
requires the 64-commit checkout update. Putting a code delivery inside a deadline window means
debugging new code and a fresh credential simultaneously.

Window A is mandatory and deadline-driven: the refresh token expires around
`2026-08-09T21:00Z`. It is stop three services, re-authorize in place with `tools/auth_init.py`,
start three services — no code change, no Compose change, no rebuild, no checkout update. It fixes
the SPX inode divergence for free, because a restart re-resolves the bind. Its only irreversible
step is the authorization itself, which has no rollback because the standing rule forbids copying
the token; the remedy for a bad document is to re-run the flow. Two details that have bitten before
are called out: `docker stop --timeout`, never `--time`, whose deprecation warning breaks output
gates; and `easy_client` does not guarantee mode `0600`, so the document must be checked and
`chmod`ed before any service starts.

Window B is optional and unhurried: decide the code-delivery mechanism (push versus reviewed
archive), update the checkout without ever running `git clean` or `git add -A` since 33 untracked
evidence artifacts are not gitignored, relocate the token document and update the three trading
binds, issue the consumer keys, re-run the preflight, then one bring-up and teardown. The readiness
latch is fixed and no longer gates any of this. Wiring any consumer, `GET /v1/history`, and any
account or order operation all remain out of scope.

## Multi-Agent Review Remediation (offline, still unwired)

A `/code-review` pass against the full branch (main..HEAD) surfaced eight findings, five of them
genuinely new correctness/efficiency defects and three real-but-already-documented tradeoffs. All
eight were independently verified against the actual code before being addressed, then dispatched
to five agents working disjoint files in parallel, then re-reviewed by direct diff inspection
before this commit — not on the agents' self-reports alone.

- **Spot upstream misclassified malformed data as unavailable.**
  `DirectSchwabSpotUpstream.get_spot` wrapped fetch and parse in one `except Exception`, so a
  malformed price payload and a genuine network failure both reported `UpstreamUnavailableError`.
  Fixed by moving `extract_spot_price` outside the locked transaction in
  `live_provider.py`'s `get_spot_price` — `LockedSchwabMarketDataProvider.get_spot_price` now
  returns the raw JSON from inside the transaction and parses it after, so a malformed payload
  raises a bare `ValueError` instead of being folded into the adapter's generic
  `SchwabClientOperationError`. `upstream.py` gained an `except ValueError` clause ahead of the
  generic one, mapping it to `UpstreamMalformedError`, matching the pattern
  `DirectSchwabChainMetadataUpstream` already used. No protocol or return-type change, so no other
  caller is affected.
- **Shadow reads ran sequentially, adding gateway latency to every collector cycle.**
  `ShadowComparingMarketDataProvider.get_spot_price`/`get_option_chain` now start the direct and
  gateway calls as concurrent `asyncio.Task`s and return the direct result immediately; the
  comparison runs as a tracked background task (`_spawn_background`, `_background_tasks` set with
  a done-callback so nothing is garbage-collected mid-flight or leaves an unretrieved-exception
  warning) via a new `wait_for_shadow_reads()` method, used only by tests and available for future
  graceful shutdown. Proven by a real timing test: a gateway fake that sleeps 1.0s, asserting the
  call returns in under 0.2s while the gateway call is provably still in flight (`started.is_set()`
  and `finished is False`), then that the comparison completes and is observable after
  `wait_for_shadow_reads()`. The existing per-request `upstream_timeout_seconds` already bounds
  each gateway call, so no additional bound on background-task growth was added.
- **`chain_metadata` refused a payload shape the live parsers tolerate.** This divergence was
  previously discovered and deliberately pinned as accepted; the review found its unconsidered
  cost — a degenerate-but-legitimate chain response (after-hours, halted symbol) made `GET
  /v1/chain` return 502 and made the shadow comparator log a false "parsing" discrepancy for a
  shape the collector already treats as zero rows. Resolved, not worked around: the raise on
  "neither expiration map present" was removed from `extract_chain_metadata`, so it now agrees
  with both live parsers on that shape exactly (`_count_expiration` already tolerated a non-dict
  input from before this fix). The one remaining raise is a payload that is not a dict at all — the
  one shape none of the three parsers can walk. This is an intentional behavior change: `GET
  /v1/chain` now returns 200 with zero counts for that shape instead of 502. The differential test
  suite's docstring and the affected test were rewritten from asserting divergence to asserting
  agreement, following the file's existing differential-test style. One genuine divergence remains
  and is unaffected: a non-numeric strike key is skipped by the metadata but raises in both live
  parsers.
- **`TokenReadinessRecovery.run_forever` could die silently on a non-`TokenManagerError`
  exception**, defeating the entire point of the class — permanently latching the gateway
  not-ready with nothing left to retry it. `run_forever` now catches any `Exception` around each
  attempt (propagating `asyncio.CancelledError` unchanged so shutdown cancellation still works),
  logging a bounded `reason="unexpected_error"` and continuing to the next interval, matching the
  redaction pattern already used in `api.py`'s `_token_readiness`.
- **`access_mode="gateway"` plus `shadow_reads=True` was representable with undefined meaning.**
  `GatewayClientSettings` gained a third `model_validator(mode="after")`, matching the existing two
  in style, rejecting that exact combination — shadow reads compare a direct read against the
  gateway and have no meaning once the client is gateway-only. Verified no other code reads
  `.access_mode` or `.shadow_reads` before adding the validator rather than restructuring the two
  fields into one enum.
- **Two already-documented tradeoffs were hardened rather than changed**, since changing either
  would have been worse than the status quo. `GatewayUpstreamSettings` continues to deliberately
  duplicate `GatewayCredentialProbeSettings` (the latter is a member of the credential proof's
  reviewed archive and must not be edited); a new test asserts the two classes' field names,
  validation aliases, and absolute-path validation stay identical, so future drift between them
  fails a test immediately instead of going unnoticed. `extract_spot_price`'s falsy-zero gap (a
  legitimate all-zero quote is misreported as absent) remains a deliberate bug-for-bug mirror of
  `data/schwab_client.py`'s identical gap in the live production path, which stays untouched and
  out of scope; a new differential test pins that both extractors reject the same all-zero payload
  identically, and the docstring states plainly that fixing one without the other would create a
  new gateway/direct divergence.
- The double full-chain-fetch cost of a chain shadow comparison (one direct, one via the gateway's
  own independent Schwab call) was reviewed and left unchanged: it is inherent to what a shadow
  comparison is for — proving the gateway's own path to Schwab works, not recomputing off the
  collector's bytes — and reducing it (e.g. shadow reads at less than full cadence) is a design
  decision for wiring time, not a bug to silently code around now.

Baseline after remediation: `uv run python -m pytest` is **952 passed, 1 skipped, 0 failed**, and
`uv run ruff check .` is clean. `git diff --check` is clean. No file under `data/`, `services/`,
`strategy/`, `execution/`, `position/`, `risk/`, `configs/`, `infra/`, `uv.lock`, or `Dockerfile` is
touched, and `schwab_gateway/config.py` (the credential-proof archive member) is unmodified. Nothing
new is wired; `SCHWAB_GATEWAY_SHADOW_READS` still defaults to false and no service constructs any of
this.

One residual note, not fixed and not blocking: wrapping the direct read in `asyncio.create_task` for
the shadow-concurrency fix means that if the *caller* of `get_spot_price`/`get_option_chain` is
itself cancelled while the direct call is in flight, the direct call's task is not automatically
cancelled with it — a well-known asyncio structured-concurrency gap, not specific to this fix. With
shadow reads enabled the background comparison task still holds and eventually awaits the direct
task, so nothing is orphaned; with shadow reads disabled and no other awaiter, an abandoned direct
task could in principle log an unretrieved-exception warning if it later fails. This has zero
current impact, since nothing wires this class to a live cancellable call path yet. Worth a look at
wiring time, not before.

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

## Window A Executed — token re-authorized (2026-08-08)

Window A of `docs/runbooks/token-reauthorization-and-gateway-enablement.md` ran to completion on
Helios with the market closed (2026-08-07 16:15 EDT, past the cash close). Window B was not touched:
no checkout update, no token relocation, no consumer keys, no gateway preflight, no gateway bring-up.

**Result.** The refresh token was replaced. `refresh_token_sha12` moved from `c5f05cc3fe64` to
`94dae53a535a`. The new document's `creation_timestamp` is `2026-08-07T21:49:55Z`, so the seven-day
deadline is now **`2026-08-14T21:49:55Z`**, and the keepalive's `WARN_BEFORE` will begin alerting
eight hours ahead of that. Host and Helios clocks were confirmed within 2 seconds of each other, so
the age figure is not skew.

**A7 verification, by inode and digest.** All three services came back on the exact image IDs
recorded in A0 — spx `faa85d748358`, ndx `ca2ca79ca2c6`, xsp `cc58c70ea998` — each `running` with
`RestartCount=0`. No container was recreated; `docker start` was used throughout and no Compose
command was issued. The host document is inode `1067463`, mode `600`, uid/gid `1001`, a regular
non-symlink file, and **all three containers resolve `/app/tokens.json` to that same inode**. All
four documents agree on `refresh_token_sha12=94dae53a535a` and `access_token_sha12=f0baf4fe1531`
with `age_days=0.1020`. The 30-second settle window returned `errors_30s=0` for each service. The
crontab was restored from its snapshot to 31 lines with exactly 2 keepalive entries.

**SPX divergence retired.** The orphaned inode `1112240` is gone; the stop/start re-resolved the bind
as predicted, at no extra cost. This closes the 2026-08-06 live finding above.

### Correction 1 — A3 as written cannot work on Helios

The runbook instructs running `tools/auth_init.py` on Helios. **Helios is headless**, and the flow is
browser-based, so it cannot complete there. The established operator procedure is to mint the token
on `zeus`, which has a browser, and `scp` it to `helios:/opt/butterflyguy/tokens.json`.

This was verified safe rather than assumed: `tools/auth_init.py` is byte-identical on both hosts
(`sha256` prefix `7ad6ce468168`), and all six long string literals — where the API key and app secret
are hardcoded — match by digest, so both hosts drive the same OAuth app and a zeus-minted token is
valid on Helios. No credential value was read, printed, or compared other than by digest.

Two consequences for the procedure. The runbook's warning that `auth_init.py` writes `tokens.json`
relative to the working directory still applies, but to the **zeus** checkout. And `scp` lands the
file at mode `644`, not `600`, so the A4 `chmod 600` is not merely a contingency for `easy_client` —
it is required on every run of this path. It was applied this window.

### Correction 2 — `easy_client` silently no-ops the re-authorization

`easy_client` takes `max_token_age=561600.0` seconds — **6.5 days**. If a `tokens.json` younger than
that is present in the working directory, it loads that document and skips the login flow entirely,
while `auth_init.py` still prints `tokens.json created successfully`.

The first A3 attempt hit this. The token was 5.04 days old, under the threshold, so nothing happened:
same inode `1067464`, same `refresh_token_sha12=c5f05cc3fe64`, same access token, and an `age_days`
that had only grown with elapsed time. The runbook's stated remedy — "re-run A3" — cannot break the
loop, because every re-run fails identically until the document crosses 6.5 days, which for this
credential would have been roughly twelve hours before hard expiry.

The fix, chosen by the operator, is to **park the existing document before running the flow** so
`easy_client` finds nothing and is forced to authorize:

```
mv tokens.json tokens.json.pre-reauth   # on the minting host, and on Helios
```

Both hosts needed this, not just Helios; zeus carried its own 5.05-day document of the same lineage.
Parking also supplies the rollback the runbook says Window A lacks: the old credential stays valid
until its own expiry, so an aborted flow costs nothing. Both parked documents were deleted once A7
verified, since a completed authorization retires the old refresh token and leaves it worthless.

Two standing rules follow. **Never treat "the script said success" as evidence** — verify that
`refresh_token_sha12` actually changed and that `age_days` is near zero. And on zeus the parked file
is **not** covered by `.gitignore` (only `tokens.json` is), so it must be kept outside the working
tree; it was moved out rather than left in the repo root. The same gap exists on Helios, where the
repo root is also the token directory — one more argument for the Window B relocation.

### Deviations from expectation, otherwise none

`docker stop --timeout 30` returned exit code `137` for all three services, meaning none completed
SIGTERM handling inside the 30-second grace and all were killed. Harmless here — a stop is not a
recreation, and images and restart counts were untouched — but the trading services appear to lack a
prompt shutdown handler. Not investigated; out of scope for this window.

## Window B Executed — gateway enabled, exercised, and rolled back (2026-08-08)

Window B of `docs/runbooks/token-reauthorization-and-gateway-enablement.md` ran to completion on
Helios with the market closed (2026-08-07 21:51 EDT). B7 was not touched: no consumer is wired to
the gateway, `SCHWAB_GATEWAY_SHADOW_READS` was not enabled, `GET /v1/history` was not exercised, and
no account or order operation was issued. The gateway is **down** at the end of the session.

**Precondition re-verified** before anything else. All three services `running` on the Window A
image IDs with `RestartCount=0`, all resolving `/app/tokens.json` to host inode `1067463`, all four
documents agreeing on `refresh_token_sha12=94dae53a535a`, crontab at 31 lines / 2 keepalive entries.
Nothing had moved.

### B3 was not ready — the runbook asserted code that did not exist

B3 claims the token-path changes "arrive with B2". They did not. On the branch at `fd9bc97`,
`tools/schwab_token_keepalive.py` still hardcoded `ROOT / "tokens.json"` and `tools/auth_init.py`
still hardcoded the cwd-relative literal; neither referenced `SCHWAB_TOKEN_PATH`, which only `src/`
honoured. The code was written this session, offline and reviewed, before anything reached the host:

- `3f0e9c0` — `.gitignore` now covers `tokens.json.pre-reauth`, closing the Window A footgun.
- `3c36c03` — both tools honour `SCHWAB_TOKEN_PATH`, process environment over `.env`, defaulting to
  today's location. A relative value stays relative to the same base each script used before.
- `f4585fd` — all **four** trading binds, not three, resolve through `SCHWAB_GATEWAY_TOKEN_DIR`,
  the variable `docker-compose.gateway.yml` already required, so the two files cannot disagree.
  `app_spx_candidate` is not running but its bind moved with the others. The variable carries **no
  default**: a bind whose source does not exist creates an empty directory rather than failing, so
  refusing to render is the only loud failure available.
- `e49a17f` — see the third finding below.

Baseline was 952 passed / 1 skipped, **not** the 941 recorded earlier; that figure was stale. After
the change: 959 passed, 1 skipped, ruff clean.

### Finding — the containers were reading the host's token path

Not in the runbook, and it would have broken all three trading services on recreation. The four
services inherit `SCHWAB_TOKEN_PATH` from `../.env`, where it is the relative `tokens.json`; it
resolves correctly inside the container only because the workdir happens to be `/app`. B3 has to
repoint that same `.env` value at the moved host document so the host keepalive and `auth_init` can
find it — which would have handed the containers a host path they do not have, and
`core/config.py:235` would have taken it. Each service now pins `SCHWAB_TOKEN_PATH: /app/tokens.json`
in its own `environment:` block, which wins over `env_file`. Host and container paths are now
independent.

### B1 — operator chose push-and-pull, with the framing corrected

The runbook frames B1 as if the gateway code were on `main`. It was not: 25 commits past local
`main`, which was itself 49 past `origin/main`, and nothing had ever been pushed. Helios's
`de84d91` was confirmed a clean ancestor of the branch tip — 89 commits behind, zero divergence.
The operator chose to push the branch and check it out on the live host. `origin/main` was not
moved. The archive alternative was presented but is weaker than the runbook implies: the gateway
builds from `context: ..`, and it imports `butterfly_guy.data.providers` (changed) and
`butterfly_guy.gateway_client.*` (new) while `pyproject.toml` also changed, so a partial extraction
onto an 89-commit-old tree would build a hybrid image. The honest archive was all 78 changed files.

**B2 preserved the evidence.** A collision pre-check confirmed zero overlap between the 78 incoming
paths and the 35 untracked artifacts before the checkout. Afterwards `git status` reports
**untracked=0** — not deletion: the branch's `.gitignore` now covers the evidence globs, so the 282
ignored entries include all of them plus `.tokens.json.lock`. The hazard is now structural rather
than procedural. The two tracked modifications survived unstaged. No destructive git command was
used on either host.

### B3 executed and verified by inode and digest

Token directory `/opt/butterflyguy-tokens`, mode `0700`, uid/gid `1001`, created without sudo —
`/opt` is operator-writable. The document moved by rename on the same filesystem, so **inode
`1067463` and mode `600` were preserved**. `.env` now names the absolute new path;
`infra/.env` (gitignored, and the directory Compose reads for interpolation) carries
`SCHWAB_GATEWAY_TOKEN_DIR=/opt/butterflyguy-tokens`.

Recreation was safe to do with `up -d`: the tags `infra-app_spx` / `infra-app_ndx` / `infra-app_xsp`
were confirmed to resolve to exactly `faa85d748358` / `ca2ca79ca2c6` / `cc58c70ea998`, so no rebuild
occurred and the recorded images were retained. The `com.docker.compose.project.config_files` label
on `app_spx` still referenced `/var/tmp/butterfly-schwab-credential-proof-rollback.yml`; that file
no longer exists and its extra tmpfs was not applied, so the label was stale history only.

After recreation: all three `running` on the same image IDs, `RestartCount=0`, all three resolving
`/app/tokens.json` to host inode `1067463`, all four documents agreeing on
`refresh_token_sha12=94dae53a535a`, `errors_30s=0` each. The keepalive was then run manually against
the new location and returned `OK: token refreshed, SPX quote fetched (status 200)` — the code
change proven end to end on the host, not merely in tests. Cron was never touched: 31 lines, 2
entries throughout.

### B4/B5/B6

**B4.** `butterfly-guy` only; the operator declined `equity-scanner` and `afterhours-lab` since
neither will be wired. `secrets/` created mode `0700` (and only then matched by the `secrets/`
gitignore rule, which is directory-only and cannot match a path that does not yet exist), keys file
mode `0600`, validated by the gateway's own loader. The plaintext was redirected under `umask 077`
to `/opt/butterflyguy-tokens/gateway-keys-plaintext.out` so it never entered an agent context; it
was read into a shell variable for B6 and never echoed. **This file still exists and holds a
recoverable plaintext key — distribute it and delete it.** That is a deliberate, flagged departure
from the command's print-once design.

**B5.** `gateway-live` renders clean. The token mount now renders as `/opt/butterflyguy-tokens` on
both sides, **not** the checkout root — this is exactly what B3 existed to achieve. 8011 free,
8010 still held by `halt_scanner` and unused by the live profile.

**B6.** Image built from the updated checkout. Sequenced deliberately around the hourly keepalive
rather than pausing cron — the build touches no token, and the up/quote/down cycle ran inside the
02:12–03:00 UTC gap, honouring `--confirm-single-token-writer` with no crontab mutation to restore.
`/ready` returned **200** with `status=ready`, `token_state=ready`. One authenticated
`GET /v1/quotes?symbols=$SPX` returned **200** with a single quote carrying a last price; bid and
ask were null, expected for an index with the market closed. The same request without the header
returned **401**. Torn down in the same session: container removed, project network removed, 8011
unbound, zero gateway containers remaining.

**Post-teardown state.** Three trading services `running` on `faa85d748358` / `ca2ca79ca2c6` /
`cc58c70ea998`, `RestartCount=0`, all on inode `1067463`; host document mode `600` uid/gid `1001`;
`refresh_token_sha12=94dae53a535a` unchanged with expiry still `2026-08-14T21:49:55Z`; cron 31 lines
/ 2 entries; Helios on `e49a17f` with only the two universe files modified; `errors_60s=0` each.

### Follow-ups, none blocking

- Distribute and delete `/opt/butterflyguy-tokens/gateway-keys-plaintext.out`.
- `/opt/butterflyguy-tokens/.env.b3-backup` (mode `600`) is the pre-B3 `.env`; delete once settled.
  It was moved out of the checkout because `.env.b3-backup` is not gitignored — the same class of
  footgun as `tokens.json.pre-reauth`.
- Running any trading Compose command now requires `SCHWAB_GATEWAY_TOKEN_DIR`. It is in
  `infra/.env` on Helios, so day-to-day commands are unaffected, but an operator running Compose
  from a different project directory will get a loud refusal rather than an empty-directory mount.

## Window C — the two token writers resolved (2026-08-08)

C1 was the gate and it is closed. The gateway is still **down**; no consumer points at it and
`GET /v1/history`, shadow reads, and every account or order operation remain untouched.

**Precondition re-verified** read-only before anything else, and nothing had moved: all three
trading services `running` on the Window A images `faa85d748358` / `ca2ca79ca2c6` / `cc58c70ea998`
with `RestartCount=0`, all resolving `/app/tokens.json` to host inode `1067463`, all four documents
agreeing on `refresh_token_sha12=94dae53a535a`, crontab at 31 lines / 2 entries, zero gateway
containers, 8011 unbound. One naming correction: the containers are `butterfly_spx_app` /
`butterfly_ndx_app` / `butterfly_xsp_app`; `app_spx` and friends are the Compose *service* names.

Refresh token life at decision time was **163.1h** against the `2026-08-14T21:49:55Z` expiry — far
outside the last-48-hour window, so there was no reason to defer implementation.

### C1 — the operator chose the shared lock

The defect was sharper than "a lost write". Both writers do read → refresh → write, and Schwab
rotates the refresh token on every refresh, so an interleave means one writer spends a credential
the other has already consumed. `docker-compose.gateway.yml` binds the token *directory* rw at the
same absolute path on both sides, so `/opt/butterflyguy-tokens/.tokens.json.lock` is genuinely the
same inode for the host keepalive and the containerized gateway; `flock` works across that boundary.

`b135313` — the keepalive now holds `AtomicFileTokenStore(TOKEN_PATH).locked(30.0)` across both
`client_from_token_file` and the SPX quote, so read-refresh-write is one critical section. schwab-py
remains the refresh implementation: what changed is *when* it may run, not *how* it refreshes. A busy
lock exits non-zero with a bounded message rather than writing anyway. Contention makes the
**gateway** back off into its already-handled `lock_timeout` state while the keepalive wins, which is
the correct priority — the keepalive is what prevents silent expiry. The two writers stay
independent: gateway down still leaves the token refreshed, and vice versa.

Rejected with reasons recorded: replacing the keepalive's refresh with `AtomicTokenManager` (rewrites
the highest-consequence script and drags an event loop into cron for a benefit the lock already
buys); having the keepalive call the gateway (truly single-writer, but gateway-down becomes silent
expiry — the exact failure Window A exists because of, and a Schwab fallback reinstates two writers);
and leaving the gateway non-durable (correct and free, but it declines durability rather than
resolving C1, and the operator wants an always-on multi-consumer service).

Baseline moved 959 → **961 passed, 1 skipped**, ruff clean. `uv run pytest` still cannot spawn; use
`uv run python -m pytest`.

### Proven on the host by the production path, at zero extra token writes

Delivered as B1 settled: pushed, then `git pull --ff-only` on Helios to `f5d88e5`, leaving only the
two universe files modified. The pull landed at 03:51 UTC, *after* the 03:00 cron firing, so the
**04:00 firing was the first production run of the locked keepalive** — no manual invocation was
needed and none was made. It returned `OK: token refreshed, SPX quote fetched (status 200)`, wrote
the document at `04:00:05` preserving inode `1067463` at mode `600`, and left
`refresh_token_sha12=94dae53a535a` and the `2026-08-14T21:49:55Z` expiry unchanged. All three
containers still resolve inode `1067463` on the same digest, `RestartCount=0`. The lock file is mode
`600` uid `1001`.

### Durability decided, monitoring still open

`f5d88e5` sets `restart: unless-stopped` on `schwab_gateway_live` only; the demo profile keeps
`restart: "no"`. This is safe **only** in combination with `b135313`: an always-on gateway overlaps
the hourly keepalive by construction, which is exactly what Window B avoided by sequencing its whole
up/quote/down cycle into the 02:12–03:00 UTC gap.

**The gateway is not reachable by Prometheus today**, and this is unresolved. `docker-compose.gateway.yml`
has no `networks:` section at all — it runs on its own isolated project network and publishes only to
`127.0.0.1:8011`, while `butterfly_prometheus` is on `monitoring_net` and scrapes by container DNS
name. The gateway does serve `/metrics` (`api.py:414`) and the auth middleware guards only `/v1/`
paths (`auth.py:130`), so a scrape needs no key. Two routes were put to the operator: join the
gateway to `monitoring_net` (conventional, but widens reachability from host loopback to every
container on that network), or scrape across the host boundary via `extra_hosts:
host.docker.internal:host-gateway` (preserves the isolation, but edits `/opt/monitoring/docker-compose.yml`,
which is outside this repo and shared with unrelated stacks). Either adds an `up{job="schwab_gateway"} == 0`
rule. Both need a Prometheus reload, which was outside this window's authorization.

**The gateway was deliberately not started.** An always-on service with nothing watching it is how a
silently-dead gateway happens, so bringing it up should follow the monitoring decision, not precede it.

### Multi-consumer shape — confirmed sound, with two wrinkles

The operator's intent is an always-on gateway with `butterfly-guy` permanent and `equity-scanner` /
`afterhours-lab` periodic. The design already anticipates this: `KNOWN_CLIENT_IDS` (`auth.py:16`)
allowlists all three and `EXPECTED_PRIORITY_BY_CLIENT` (`auth.py:31`) already makes `butterfly-guy`
`protected` and the other two `background`. Declining to issue their keys in Window B remains correct.

- `issue_gateway_keys.py` has **no append mode**: it refuses to overwrite (`:93`) and regenerates keys
  for every client in the document (`:50`), so adding a second consumer later rotates
  `butterfly-guy`'s key and forces redistribution. Fixable when the second consumer is actually wired.
- A fourth consumer needs a one-line `auth.py` change; the allowlist is closed by design.
- `/v1/history` is still deliberately absent, so a consumer needing bars rather than quotes has no
  surface yet.

### Still open

- The monitoring route above, then whether to start the gateway.
- C3 wiring — untouched this window, still its own decision.
- `/opt/butterflyguy-tokens/gateway-keys-plaintext.out` (146 bytes, mode `600`) still holds a
  recoverable plaintext consumer key; the operator has not yet confirmed distribution. Delete once
  confirmed. `.env.b3-backup` likewise.

### C3 plan produced, and a stale design point corrected

`docs/architecture/schwab-gateway-c3-shadow-wiring-plan.md` — plan only, no code. Re-deriving from
`shadow.py` rather than trusting the prose caught two errors that both this file's "Next Exact
Action" (lines ~723-726) and the Window C brief carry:

- **The latency claim is wrong.** Both say the comparator awaits the gateway read after the direct
  read returns, adding gateway latency to every collector cycle. It does not: `get_spot_price`
  (`shadow.py:188`) and `get_option_chain` (`shadow.py:224`) spawn the comparison via
  `_spawn_background` (`:142`, docstring "Run a shadow comparison off the caller's critical path")
  and `return await direct_task`. True of some earlier revision; the prose was never updated. The
  real costs are a doubled outbound request count on shadowed calls and background tasks that
  outlive the call, bounded by the client's 5.0s timeout (`client.py:54`) against a 60s cycle.
- **The no-shadow-surface set is larger than stated.** Not just `get_daily_bars`: `get_intraday_bars`
  (`:281`), `get_intraday_bars_for_day` (`:286`) and `get_daily_bars` (`:299`) are all pass-throughs.
  Shadow covers two of the collector's four call sites. The chain comparison is also metadata-only,
  not strike-by-strike.

**A blocker C3 shares with the monitoring question:** `docker-compose.gateway.yml` has no `networks:`
section, so the trading containers cannot reach the gateway either. Joining `monitoring_net` solves
Prometheus *and* the future consumers in one change but widens reachability; the host-boundary
`extra_hosts` route preserves isolation but must then be applied to Prometheus and all three trading
services. This should be decided once with C3 in view, not separately. There are also **no Prometheus
metrics anywhere in `gateway_client/`**, so a shadow run's results are currently readable only from
logs.

### Housekeeping

`/opt/butterflyguy-tokens/.env.b3-backup` deleted on operator instruction, after confirming it was a
distinct inode from the live `/opt/butterflyguy/.env` (1059921 vs 1111276) and that the live file was
intact at 1547 bytes with all 21 variables including `SCHWAB_TOKEN_PATH`. The 25-byte size delta is
exactly the `/opt/butterflyguy-tokens/` prefix B3 added, corroborating the backup as the pre-B3 copy.
No file contents were read.

`/opt/butterflyguy-tokens/gateway-keys-plaintext.out` **still exists** — distribution was never
confirmed, so it was deliberately left in place.
