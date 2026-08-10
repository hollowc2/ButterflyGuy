# Codex Project State

## Objective

Safely migrate Schwab ownership toward one shared, permissioned gateway without changing
live ButterflyGuy behavior or production defaults.

## Current status — 2026-08-10

This section supersedes the many time-stamped intermediate status statements below; those entries
remain as an execution history, not as current instructions.

- The read-only Schwab gateway is deployed on Helios, running and monitored. Readiness, an
  authenticated Schwab quote, Prometheus scraping, alerting, and crash-restart recovery have been
  proven. It still exposes no account or order surface.
- Direct Schwab access remains authoritative for the trading applications. C3 shadow wiring is now
  implemented locally as a default-off XSP-only canary, but it is not deployed or enabled. The
  scoped consumer-key rotation and live canary remain separate operator-approved actions.
- The early full re-authorization on `2026-08-10` proved zero-restart token reload for SPX, NDX,
  XSP, and the candidate feed. The installed token was created at `2026-08-10T20:23:30Z` and
  expires at `2026-08-17T20:23:30Z` (Monday `13:23:30 PDT`).
- The planned Saturday `2026-08-15` morning re-authorization is a cadence reset, not the first
  production reload test and not the current token's hard deadline.

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
it. Two design points to settle at wiring time — **both as originally written here were wrong, and
are corrected in `docs/architecture/schwab-gateway-c3-shadow-wiring-plan.md`**: the comparator does
*not* add gateway latency, because it spawns the comparison off the critical path
(`shadow.py:142`) and returns the direct read; and the missing shadow surface is larger than
`get_daily_bars` — `get_intraday_bars`, `get_intraday_bars_for_day` and `get_daily_bars` are all
pass-throughs, so shadow covers two of the collector's four call sites.

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

## Window D — the gateway made reachable, started, and watched (2026-08-08)

D1 and D2 are both closed. The gateway is **up, always-on, scraped by Prometheus, and covered by a
firing-proven alert**. `GET /v1/history`, shadow reads, and every account and order operation remain
untouched; C3 is still unwired and still its own decision.

### Preconditions re-verified, and one record corrected

Nothing had moved: three services `running` on `faa85d748358` / `ca2ca79ca2c6` / `cc58c70ea998`,
`RestartCount=0`, all resolving `/app/tokens.json` to inode `1067463`, all four digests
`94dae53a535a`, crontab 31 lines / 2 entries, zero gateway containers, 8011 unbound (8010 still
`halt_scanner`).

**The C1 soak passed.** The window spanned 04:00–17:00 UTC, so the locked keepalive ran thirteen
consecutive hourly firings, every one `OK: token refreshed, SPX quote fetched (status 200)`, with
the "expires in" figure stepping down exactly one hour per line (161.8h → 149.8h) and the token
mtime advancing hourly on preserved inode `1067463`. This is the multi-hour evidence Window C could
not have.

**The recorded test baseline was wrong.** `c2ebad1` was **960 passed, 1 failed, 1 skipped**, not the
961/0 recorded at the end of Window C. `f5d88e5` changed the live service to `restart:
unless-stopped` and left `tests/test_gateway_compose.py:39` asserting `"no"`. Window C reported a
green suite it did not have. Fixed in `0d2bed3`; the suite is now **962 passed, 1 skipped**, ruff
clean.

### D1 — the operator chose monitoring_net, and the alternative turned out not to work

`0d2bed3` joins `schwab_gateway_live` (only) to the external `monitoring_net`. Prometheus scrapes
`butterfly_schwab_gateway_live:8011`, and the C3 consumers get the same route — one change for both,
which is why the two were decided together. The `127.0.0.1:8011` publish stays for host debugging
and is not the path any consumer uses. The demo service is untouched on the project default network.

**The host-boundary route could not have worked as briefed.** `host.docker.internal:host-gateway`
resolves to the docker0 bridge IP `172.17.0.1`, while the gateway publishes to `127.0.0.1:8011` —
loopback-only, unreachable from any container netns. Making it work would have required unbinding
loopback first (`0.0.0.0:8011`, or a cross-bridge `172.17.0.1:8011`), trading container-network
exposure for host-network exposure: **wider than what it was meant to preserve**. Window C
recommended it on a premise that does not hold.

Two further corrections to the received picture:

- **The blast radius is smaller than recorded.** `monitoring_net` carries 16 containers: the
  butterfly stack itself (3 apps, 6 candidate evaluators, feed, timescaledb, grafana, prometheus,
  alertmanager) plus `turtlequant-grafana-exporter` and `helios_node_exporter`. `pdfbillr` and
  `halt_scanner` are on their own project networks and are **not** on it.
- **`infra/prometheus.yml` and `infra/candidate-alerts.yml` are not the live config.** The running
  container binds `/opt/monitoring/prometheus.yml` — a plain file, not a symlink to this repo — and
  loads rules from `/opt/monitoring/prometheus-alerts/*.yml`. A rule placed beside
  `infra/candidate-alerts.yml` would never be read. Pre-existing drift, left alone.
  (Corrected 2026-08-08: this entry previously called the repo file's `app_spx:8000` targets
  "stale". They are not — Compose registers the service name as a network alias, and `app_spx`
  resolves on `monitoring_net` to the same address as `butterfly_spx_app`. The live config simply
  uses container names. The repo file's real hazard is that it looks deployable and is not, which
  is now stated in a header comment inside it.)

The rule therefore lives at `infra/schwab-gateway-alerts.yml` and deploys to
`/opt/monitoring/prometheus-alerts/schwab-gateway.yml`.

### Applied to /opt/monitoring with approval, by reload not recreation

Backup `prometheus.yml.bak-20260808T162316Z` taken first. The rule went in as a **new file**,
touching nothing shared; the scrape job was appended to the shared `prometheus.yml`. `promtool check
config` passed on all six rule files, then `POST /-/reload` — `--web.enable-lifecycle` is set, so
**the shared Prometheus container was never recreated**. Rollback is restoring the backup and
reloading again.

### The alert path was proven end to end, for free

Because the gateway was still down when the scrape job landed, the alert could be tested **without
ever disturbing a running gateway**. Observed in sequence: target registered `down` →
`SchwabGatewayDown` `pending` → `firing` → present in Alertmanager as `active` at `severity=critical`
→ back to `inactive` once the gateway came up and `up{job="schwab_gateway"}` went to 1. The whole
lifecycle, on the real Alertmanager, not asserted from the rule file.

### D2 — the gateway is up, and durability was proven by an actual crash

Image rebuilt (the checkout had moved), started under `--profile gateway-live`. `status=running`,
`health=healthy`, attached to `monitoring_net`, and resolving the token document to host inode
`1067463` from inside the container.

| Check | Result |
|---|---|
| `/ready`, `/health`, `/metrics` on host loopback | `200`, `200`, `200` |
| `/v1/quote?symbol=$SPX` with no key / a bogus key | `401`, `401` — auth middleware live |
| `GET /metrics` from inside `butterfly_prometheus` by DNS name | `HTTP/1.1 200 OK` — D1's actual goal |
| Prometheus target | `butterfly_schwab_gateway_live:8011` `up`, `up = 1` |

**A method correction on restart-survival.** `docker kill` did **not** restart the container
(`status=exited`, `RestartCount=0`) — Docker records `docker kill` as a *manual* stop exactly like
`docker stop`, so `unless-stopped` correctly declines. That is a bad test, not a broken policy. The
real test is killing the container's main process from the host, outside Docker's API: after
`kill -9` on the container PID, it came back on its own to `status=running`, `health=healthy`,
`RestartCount=1`, `/ready` 200, **with no manual start issued**. Crash survival is proven. *Reboot*
survival follows from the same policy but was **not** tested — rebooting Helios would have disturbed
the trading services for no proportionate gain.

**One thing Window B did that this window could not repeat: the authenticated `$SPX` quote.** The
operator confirmed the consumer key had been distributed and approved deleting
`/opt/butterflyguy-tokens/gateway-keys-plaintext.out`, which I did *before* running the quote — a
sequencing mistake on my part. The key is recoverable only from the operator's own copy;
`secrets/schwab-gateway-keys.json` holds SHA-256 digests by design, and re-issuing would rotate
`butterfly-guy`'s key and force redistribution, which is not worth it for a re-verification. What
was verified instead is that the auth surface is live (401 on missing and on bogus key) and that the
gateway reaches the token document on the right inode. Window B already proved the authenticated
quote against this same image and token document. **Run one authenticated quote at the start of the
next window**, using the operator's copy of the key.

### C1 proven under genuine contention — the thing Window C could not test

The 17:00 UTC firing was the first keepalive run **with an always-on gateway holding the same token
document**, which is what C1 exists for. Window C could only prove the lock in isolation. Proven on
the production path, at zero extra token writes, per the standing preference:

- `OK: token refreshed, SPX quote fetched (status 200), refresh token expires in 148.8h`
- Token written `17:00:04`, inode `1067463` preserved, mode `600`, digest still `94dae53a535a`
- Gateway `running` / `healthy` / `RestartCount=1` throughout, still resolving inode `1067463`
- **Zero** `lock_timeout`, error, or exception lines in the gateway log across the firing

The shared lock does what it was designed to do. Refresh token life at window close: **148.8h**
against the `2026-08-14T21:49:55Z` expiry.

### Final state

- Gateway **UP** and left up, on operator approval: `restart: unless-stopped`, `monitoring_net`,
  scraped, alerted, crash-survival proven.
- All three trading services `running`, `RestartCount=0`, inode `1067463`, digest `94dae53a535a` —
  untouched throughout. Crontab still 31 lines / 2 entries; the keepalive was never modified or
  sequenced around.
- All Prometheus targets healthy except one pre-existing `nodes` target, which was already firing
  `HostDown` in Alertmanager before this window's changes.
- `/opt/butterflyguy-tokens/gateway-keys-plaintext.out` **deleted** on operator confirmation that
  the key had been distributed (was inode `12602`, mode `600`, 146 bytes). `gateway-keys-issue.err`
  remains at **0 bytes** — empty, nothing to leak, left in place.

### Still open

- **C3 wiring** — plan exists (`docs/architecture/schwab-gateway-c3-shadow-wiring-plan.md`), code
  does not. The reachability blocker it shared with monitoring is now gone: the trading containers
  can reach `butterfly_schwab_gateway_live:8011`. Still its own decision and its own window.
- One authenticated `$SPX` quote, deferred to the next window for the reason above.
- **No Prometheus metrics anywhere in `gateway_client/`** — a shadow run's results are still
  readable only from logs. Worth closing before or with C3, now that a scrape path exists.
- `issue_gateway_keys.py` still has no append mode: adding a second consumer rotates
  `butterfly-guy`'s key. Fix when the second consumer is actually wired.
- Reboot survival is unproven by test, only by policy.

### Window D addendum — the authenticated quote, and two corrections it forced

The deferred authenticated read was completed in-window after all, by re-issuing the key. Both
live surfaces returned **200**:

- `GET /v1/quotes?symbols=$SPX` → `200`, `quotes: list[1]`
- `GET /v1/spot?symbol=$SPX` → `200`, `price` present and positive, `symbol` `$SPX`,
  `source` populated, `stale=true` with two `data_quality_flags` and null `event_timestamp` /
  `age_seconds`. **2026-08-08 is a Saturday**, so a stale flag on a closed market is correct
  behaviour, not a defect — the gateway declines to claim freshness it cannot evidence.

**Correction 1 — the auth header is `X-Internal-API-Key` (`auth.py:134`), not `X-Api-Key`.** The
Window D table above records "401 on missing key / 401 on a bogus key" as evidence the auth
middleware was live. Both probes used the wrong header name, so both were really the same *missing
header* test. Unauthenticated `/v1/` requests are genuinely refused, but the bad-key path was never
exercised as claimed. What does now stand as proof is the `401 → 404 → 400 → 200` progression on the
re-issued key: 401 (no valid header) → 404 (auth passed, wrong path) → 400 (right path, wrong query
param) → 200. Authentication is proven by the transition off 401, not by an assertion.

**Correction 2 — the route and parameter names.** The surfaces are `/v1/quotes`, `/v1/spot` and
`/v1/chain` (`api.py:415-417`), not `/v1/quote`; `/v1/quotes` takes `symbols` (plural,
`api.py:155`) while `/v1/spot` takes `symbol` (`api.py:169`).

**The key was rotated.** The original was unrecoverable — `issue_gateway_keys.py` prints it exactly
once and stores only its SHA-256 — because it was deleted earlier in this window before this check
had been run. Re-issued for `butterfly-guy` with stdout redirected to a mode-`600` file so the value
never entered the assistant's context. The new document is byte-identical to the old except the
digest (same single client, `market_data:read`, `protected`); old document backed up at
`secrets/schwab-gateway-keys.json.bak-20260808T172233Z`. The gateway required an explicit
`docker restart` to pick it up: `docker compose up -d` reported `Running` and did **not** recreate,
because the compose config was unchanged and only the bind-mounted file's contents differed. New
in-container digest prefix `efa156ac5c16`.

All plaintext key material was then destroyed on operator instruction and verified absent:
`.issue.out`, `.issue.err`, `.gwkey`, `gwkeys.json`, plus the quote response bodies. **No plaintext
gateway key exists on either host.** `gateway-keys-issue.err` remains at 0 bytes.

**Consequence for C3:** wiring a real consumer will require issuing a key again, which rotates
`butterfly-guy`'s. That is free while nothing consumes the gateway, and the procedure is now
recorded above. Do the issuance and the first authenticated call in the same step, and do not delete
the plaintext until the call has returned 200.

### Gateway client metrics — closed (2026-08-08)

The "shadow results are readable only from logs" gap is closed. `core/metrics.py` gains two
counters, and `shadow.py` reports through them:

- `butterfly_gateway_shadow_comparisons_total{operation,result}` — `result` is
  `agree | discrepancy | direct_unavailable`.
- `butterfly_gateway_shadow_discrepancies_total{operation,code,classification}` — the existing
  fixed diagnostic code space, now exported rather than only logged.

The important half is `agree`. Both comparison paths previously returned early on agreement without
recording anything, so the only observable signal was failure — a mismatch *rate* had no
denominator, and a comparator silently doing nothing looked identical to one finding no problems.

`direct_unavailable` is deliberately a separate result rather than a discrepancy: when the direct
read raises there is nothing to compare, and counting that against the gateway would be wrong.

The discrepancy `fields` tuple is **not** a label — it is unbounded in shape and stays in the logs.
Label cardinality is bounded at 2 operations × 11 codes × 4 classifications.

Six tests added (**968 passed, 1 skipped**, ruff clean), covering: agreements counted, a discrepancy
counting once as a comparison and once by code, a gateway error under its own code, a failing direct
read counted separately, a disabled shadow touching no counter at all, and every declared code being
a legal label set.

Still inert with respect to trading — nothing constructs `ShadowComparingMarketDataProvider` from
`run_live.py`. These counters only produce data once C3 wires it and
`SCHWAB_GATEWAY_SHADOW_READS` is on. No alert rule was added for mismatch rates: with shadow off
there is no baseline to threshold against, and that is better chosen from real data during C3.

## Window E — C3 declined, and a live token-mount defect found and fixed (2026-08-08)

C3 was **not** wired. The operator declined shadow reads for now, so `run_live.py:743` is unchanged,
`SCHWAB_GATEWAY_SHADOW_READS` is unset in all three trading containers, and no gateway key was
re-issued — the plaintext key still does not exist on either host, and nothing consumes one.

Two of the brief's C3 claims were re-derived and both **hold**: the comparator adds no gateway
latency (`shadow.py:200` and the chain path both spawn the comparison and `return await
direct_task`), and the client timeout is 5.0s (`client.py:54`) against a 60s collector cycle.

### The finding — the always-on gateway had orphaned all three trading containers

Window D recorded all three trading services resolving `/app/tokens.json` to host inode `1067463`.
That was **true of the containers and false of the host** by the time it was written; the check
compared the containers to each other, not to the host document.

- Trading services bound the token **document**, so Docker pinned the inode resolved at container
  start.
- The gateway binds the **directory** and persists with `os.replace` (`token_manager.py:233`), which
  swaps in a new inode.
- The gateway's first refresh after going always-on logged `refresh_succeeded` at `17:26:10.940`;
  the host document's mtime is `17:26:10.940081866`. Exact match, single cause.

Result: host at inode `20422`, all three containers stranded on `1067463` holding the 17:00
keepalive result. Nothing broke that day — the refresh token was byte-identical on both sides
(`94dae53a535a`) and valid to 2026-08-14T21:49:55Z — but the containers had permanently stopped
seeing keepalive writes and would never have received the re-authorized refresh token.

Related, and still open: the trading containers bound only the document, so they could not see
`.tokens.json.lock` at all. **The three trading apps have never participated in the C1 shared
lock** — C1 covers the gateway and the keepalive only.

### Fixed by binding the directory, and by a second defect that fix exposed

`089cdc8` moves all four services in `infra/docker-compose.yml` to a directory bind, mirroring
`docker-compose.gateway.yml`, which had already documented this exact hazard.

Recreating the three containers then crash-looped them on `FileNotFoundError: 'tokens.json'` — a
**relative** path. Root cause, and a correction to a standing "established fact": `config.py:236`
applies `SCHWAB_TOKEN_PATH` with `setdefault`, and all three live configs pinned
`schwab.token_path: "tokens.json"`, so **the compose environment pin had never had any effect**. It
worked only because the relative path resolved against working directory `/app`, where the old
document bind sat. `99049fa` drops `token_path` from the three live configs; the `"tokens.json"`
default still applies when nothing sets the variable, so local runs are unchanged.

### Verified, by inode and digest and by an actual atomic replace

- Host and all three containers agree: inode `20422`, digest `c9845b385e8b`.
- The digest moved twice during the window (`7df738c08e66` → `c9845b385e8b`) and **all three
  containers followed it**, which the orphaned mount could not have done.
- Direct proof of the mount semantics: a scratch file in the token directory was atomically
  replaced; the container followed inode `12602` → `20114` and read the new content. Under a
  document bind it would have stayed on `12602`. Scratch file removed.
- The 21:00 keepalive fired `status 200` against the recreated containers, 144.8h remaining.
- All three on the original Window A images (`faa85d748358` / `ca2ca79ca2c6` / `cc58c70ea998`),
  `RestartCount=0`, zero error lines since restart, collectors at `market_closed_waiting`.
- Gateway `running`/`healthy`, `up{job="schwab_gateway"} == 1`, `SchwabGatewayDown` inactive.

Suite **970 passed, 1 skipped**, ruff clean. Two regression tests added: one asserting the compose
never binds the token document, one asserting the live configs leave `token_path` to the environment.

### Still open

- **C3 itself.** Declined this window, not rejected. When it happens the key goes in `infra/.env`
  on Helios — that was decided here even though it was not needed.
- **The trading apps do not take the C1 lock.** They now share the directory, so the lock file is
  finally reachable; nothing yet acquires it. They write in place, unlocked, while the gateway
  replaces atomically.
- **The candidate fleet has the same defect, pre-existing and untouched.**
  `butterfly_spx_candidate_feed` binds `/opt/butterflyguy/tokens.json`, a path that **no longer
  exists on the host**; the container holds an orphaned inode `1112240` from 2026-08-07 19:52. It
  is generated from `candidate_fleet/registry.py:172`, a separate stack on a separate token
  document, and was deliberately left alone.
- The trades table is `butterfly_trades`, not `trades` — CLAUDE.md and several briefs say
  otherwise. `public.trades` in the same database is an unrelated crypto table.
- `infra/docker-compose.yml` is pinned by SHA in `test_gateway_compose.py`; it was re-pinned to
  `5e7804fe…`. Any edit to that file must update it.

### Window E addendum — the candidate fleet's orphaned token, fixed (2026-08-08)

The defect recorded above as "pre-existing and untouched" was addressed on operator instruction.

Only `butterfly_spx_candidate_feed` touched Schwab; the six evaluators have no token mount and
consume the feed. The feed bound `../../tokens.json`, which resolves to
`/opt/butterflyguy/tokens.json` — the **pre-B3 location**. B3 moved the document to
`/opt/butterflyguy-tokens` and never updated `candidate_fleet/registry.py`, so the host path
stopped existing and the container kept the inode it had resolved at start.

The orphan was worse than the trading one. It carried a **separate credential lineage**: refresh
token `c5f05cc3fe64`, created 2026-08-02T20:39:34Z, against the maintained `94dae53a535a` created
2026-08-07T21:49:55Z. On a 7-day life that token expired **2026-08-09T20:39Z — roughly 23 hours
after it was found**. The feed was still serving 200s from Schwab on Friday, so this would have
failed silently, in a research stack nobody watches, a day later.

It survived because of a deliberate design: `schwab_market_data.py` reads the token file **once**
and keeps every refresh in memory (`_retain_token`), never writing. That is why the mount is `:ro`
and why an orphaned document worked for nine days.

`e48c2df` binds the token directory read-only from `SCHWAB_GATEWAY_TOKEN_DIR` and names the
document absolutely. `:ro` is retained deliberately — the feed must never write the shared document,
so it needs neither the lock nor a writable mount. `candidatectl` now also loads `infra/.env`,
where that variable lives; compose interpolates from the process environment, and the `:?` guard
fails loudly instead of letting Docker invent an empty directory.

`infra/generated/` is **gitignored**, so the compose artifact does not travel by `git pull` — it
must be re-rendered on the host. Re-rendering also bumps `DEPLOYED_GIT_SHA` on all six evaluators,
so a full `candidatectl apply` would recreate the whole fleet; only `spx_candidate_feed` was
recreated here, by naming the single service.

Verified: feed on inode `20422`, digest `c9845b385e8b`, identical to host and to the three trading
containers; refresh token now `94dae53a535a`, the maintained lineage; `RestartCount=0`, zero errors,
`candidate_market_data_client_initialized`. All six evaluators still running at `RestartCount=0`
with zero errors. No butterfly or gateway alert is firing.

**Not proven, and deliberately so:** the feed makes no Schwab call while the market is closed, so an
authenticated call from the new document was not observed. `/ready` returns
`503 snapshot_unavailable` because the restart reset its sequence, which is expected of any restart
on a Saturday and is not a regression. The credential itself is proven — the 21:00 keepalive fetched
a quote with `94dae53a535a` at status 200. **Confirm the feed publishes a snapshot at Monday's open.**

Residual: the feed reads the document only at first use, so it will still not see a re-authorized
refresh token until it is restarted. Restarting it after the 2026-08-14 re-authorization is now
sufficient, where before no restart would have helped.

## Window F — the refresh token re-authorized, six days early (2026-08-08)

Executed 2026-08-08 21:56–22:15 UTC. The deadline item was closed on the first day of the window
rather than the last, because the calendar left no better moment.

### The scheduling finding

The refresh token `94dae53a535a` expired **2026-08-14T21:49:55Z** (a Friday), with 144.8h remaining
at 21:00 UTC — exactly as the keepalive reported and the brief claimed. Re-authorization requires
restarting live trading containers, which is only safe with no open position. The last weekend
before expiry was **2026-08-08/09 itself**; the next one begins after the token is already dead.
The operator chose to execute immediately and approved the container restarts.

### The correction that forced the restarts

The Window F brief claimed that after the directory-bind fix "nothing else should need" a restart
because all four trading services and the feed now bind the directory. **That is wrong**, and it
would have left three trading apps on a dead credential.

`SchwabClientWrapper.initialize()` (`schwab_client.py:37-43`) calls `client_from_token_file` exactly
once, and `run_live.py:742` calls `initialize()` once at startup. schwab-py then holds the token in
memory and writes back on refresh; it never re-reads the document. The directory bind lets a
container *see* a new inode — it does not make it *re-read* one. That distinction is the same one
that made the feed's orphan survive nine days, and it applies to the trading apps too. All five
token consumers needed restarting, not just the feed.

### Execution

Preconditions verified before touching anything: baseline re-derived at **970 passed, 1 skipped**,
`ruff` clean; zero open trades (`butterfly_trades` has 224 rows, all `CLOSED`, none with a null
`exit_time`); market closed (Saturday); all five containers `RestartCount=0`; gateway
`running`/`healthy` on `monitoring_net`; `up{job="schwab_gateway"} == 1`; `SchwabGatewayDown`
inactive; cron 31 lines / 2 keepalive entries; keepalive succeeding hourly.

zeus and Helios were confirmed to carry **identical** app credentials before the flow was run —
API key sha `6888173cf7e1`, secret sha `872ed858a44d` on both — so a token minted on zeus is valid
on Helios. That had been assumed in every prior window and never checked.

The browser flow ran on zeus via `tools/auth_init.py` with `SCHWAB_TOKEN_PATH` pointed at a scratch
file, so the operator's stale `./tokens.json` was left untouched. Drop-in was staged by `scp` to
`.tokens.json.incoming` in the token directory, verified byte-identical by digest on both hosts
(`046a27e34047`), `chmod 600`, then moved into place under `flock -w 30` on `.tokens.json.lock` —
the same `fcntl.flock` primitive `token_manager.py:295` and the keepalive use, so the C1 lock was
honoured rather than bypassed.

Gateway restarted **first**, deliberately: it holds the old refresh token in memory and would have
written it back over the new document on its next refresh.

### Result

New lineage: refresh token sha `94dae53a535a` → **`a44cc5263be9`**, `creation_timestamp`
2026-08-08T22:05:28Z, expiry **2026-08-15T22:05:28Z**. Schema and size (787 bytes) identical.

Host and all five consumers agree on inode **`20446`**, digest **`046a27e34047`**, mode 600, uid
1001 — compared against the host, not only across containers. All five `running`, `RestartCount=0`,
gateway `healthy`, `/ready` 200, `up == 1`, no Schwab alert. Feed
`candidate_market_data_client_initialized`, zero errors; all six evaluators still running.

**Proven on the production path:** all three trading apps resolved account hashes on startup with
zero errors, which is a real authenticated Schwab call against the new document. The credential is
therefore proven for the trading path — not merely mounted.

### Still unproven

The candidate feed makes no Schwab call while the market is closed, so its authentication against
the new document is *not* observed. `/ready` returns `503 snapshot_unavailable`, which is expected
of any restart on a Saturday. **The Monday check carried over from Window E is still owed, and now
covers the new credential rather than the old one.**

Reboot survival for the gateway remains proven by policy, not by test.

### Incidental

Running the auth flow through the session's `!` prefix failed on `EOFError` — that path has no
stdin and schwab-py prompts for ENTER — and the library printed the **`client_id` (Schwab app key)**
into the transcript before failing. Nothing was written and no credential was consumed. This is the
same exposure class as the Window E `docker compose config` incident; the app key should be treated
as disclosed. The secret key was not printed.

The restarts took the full 30s SIGTERM timeout each before SIGKILL, confirming the open exit-137
finding: the trading services still have no prompt SIGTERM handler. Harmless with the market closed
and no position open; it is the reason a weekday-evening re-auth would have been worse.

### Window F addendum — the trading apps now take the C1 lock (2026-08-08)

The gap recorded in the Window F brief as "a real gap and a reasonable next piece of work" was
closed on operator instruction, after the re-authorization.

The gap was worse than "unlocked". schwab-py's default persister, `__make_update_token_func`
(`schwab/auth.py:30-36`), is `open(token_path, 'w')` followed by `json.dump` — a **truncating
in-place write**, with no lock, no atomicity, no fsync, and no mode enforcement. All three trading
apps used it, via `client_from_token_file`. The benign failure is two writers clobbering each
other's access token. The malign one is a reader — the gateway, the keepalive, or a restarting
container — seeing a **truncated document**, because the file spends a real interval empty.

`schwab_client.py` now builds its client with `client_from_access_functions` and persists through
`AtomicFileTokenStore`, the same primitive and the same `.tokens.json.lock` the gateway
(`token_manager.py:295`) and the keepalive already use. Reads take the lock too. The pattern
matches the candidate feed's, which already used the accessor API for its own reasons.

A failed persist is logged as `schwab_token_persist_failed` and swallowed rather than raised: the
refreshed access token is already live in memory and the keepalive rewrites the document hourly, so
a lost write is recoverable, while killing the live trading loop over a transient lock conflict is
not. The lock timeout is 10s, deliberately short — it is held on the event loop.

**What this does not fix.** The app's read-refresh-write is still not one critical section, the way
the keepalive's is (`schwab_token_keepalive.py:116`). authlib performs the refresh internally and
only hands back the result, so only the write is guarded. Two writers can therefore still overwrite
each other's *access* token. That is benign — both are valid until their own expiry, each holder
keeps its own copy in memory, and Schwab does not rotate the refresh token on an ordinary refresh.
Torn writes were the real defect and they are gone.

Three tests added, against a real token file and a real `flock` rather than mocks: the read goes
through the store; the write lands on a **new inode** at mode 600, which is the direct proof it is
`os.replace` and not truncation; and a write blocked by a competing lock holder logs and returns
instead of raising.

**One boundary was deliberately narrowed.** `test_no_service_or_entry_point_imports_the_shadow_
harness_or_gateway_client` forbade any import from `butterfly_guy.schwab_gateway` outside three
standalone entry points. `token_manager` is not a Phase 3 surface — it is the shared persistence
primitive, it reaches no market-data path, and the keepalive already depends on it — so it is now
excluded from that rule by name, with the reasoning in the test. The alternative was moving the
module to a neutral package, which is 20 references across 17 files and is not a surgical change.
Everything else in both gateway packages stays restricted, and the shadow-harness assertion is
untouched.

Suite after: **973 passed, 1 skipped** (was 970), `ruff` clean.

**Not deployed.** This is a code change, so it needs an image rebuild and container recreation, not
a restart — that is outside the standing authorization and was not done. The three trading apps on
Helios are still running the pre-change images listed above.

### Window F addendum 2 — the C1 lock change deployed (2026-08-08)

Deployed on operator instruction, in the same closed-market window as the re-authorization.

Preconditions re-checked immediately before: zero open trades, Saturday 22:39 UTC. Images rebuilt
with `docker compose --profile ndx --profile xsp build app_spx app_ndx app_xsp`, and the change was
confirmed *inside each built image* before anything was recreated — `client_from_access_functions`
present in all three. Recreation named the three services explicitly, so `app_spx_candidate`, the
legacy rollback service, was untouched and is still `exited` from 2026-07-23.

New images `ed73ab7b7c20` / `d5b60ca954a3` / `17935e7c09aa` (were `faa85d748358` / `ca2ca79ca2c6` /
`cc58c70ea998`). All five token consumers and the host agree on inode `20446`, digest `046a27e34047`,
mode 600. All `running`, `RestartCount=0`.

Proven on the production path: all three logged `schwab_client_initialized`, which only emits after
`get_account_numbers()` returns 200 and the configured account matches, so the **locked read path
authenticated against Schwab for real**. The SPX log shows the underlying `POST /v1/oauth/token 200`
and `GET /accountNumbers 200`. Zero errors and zero `schwab_token_persist_failed` across all three.

Note for future verification: a `docker logs --since` grep run immediately after `up -d` returns
zero, because initialization takes ~4s. That is a race in the check, not a failure in the service.

**A write through the new path has not yet been observed.** `schwab_client_initialized` proves the
locked *read*; the locked *write* fires only on an access-token refresh, roughly every 30 minutes of
running, and was not waited for. The unit tests cover it against a real `flock`; production has not
exercised it yet.

### The exit-137 finding, correctly diagnosed (2026-08-08)

Recorded across earlier windows as the trading services lacking "a prompt SIGTERM handler". That is
directionally right and mechanically wrong, and the difference determines the fix.

Measured inside `butterfly_spx_app`: `/proc/1/comm` is `python` — the app is **PID 1** — and
`SigCgt: 0000000100000002` catches only SIGINT (2) and CPython's internal signal 33. SIGTERM is bit
15, mask `0x4000`, and appears in neither `SigCgt` nor `SigIgn`. The kernel does not deliver a
default-action signal to PID 1, so **SIGTERM is silently discarded**, Docker waits out the full
timeout, and SIGKILL produces exit 137. Nothing is slow; the signal never arrives.

`HostConfig.Init` is unset and no service in `infra/docker-compose.yml` sets `init:`.

Two fixes, and they are not equivalent:

- `init: true` per service puts tini at PID 1, so Python is no longer PID 1 and SIGTERM's *default*
  action applies. One line per service, no application code. Death is prompt but abrupt: the
  existing `finally` in `run_live.py` never runs, so the DB pool is not closed and readiness is not
  set. Note this edits `infra/docker-compose.yml`, whose SHA-256 is pinned in
  `test_gateway_compose.py` — the pin and its comment must be updated in the same change.
- An explicit handler in `main()` that requests cancellation of the TaskGroup, letting the existing
  `finally` (`set_readiness("shutting_down")`, `schwab.close()`, `db.close()`) run. This is the real
  fix. It is fiddlier than it looks: the loops are infinite tasks inside an `asyncio.TaskGroup`, and
  a cancellation path has to unwind them without the `except* Exception` handler reporting the
  shutdown as `task_group_error`.

### Correction — the deadline recurs weekly; it was moved, not removed (2026-08-08)

The Window F record above frames the re-authorization as closing the deadline "six days early".
That is misleading and is corrected here.

The Schwab refresh token has a hard **7-day life** from `creation_timestamp`, and an ordinary
access-token refresh does not extend it (verified 2026-08-08: the value survives gateway and
keepalive refreshes). So re-authorizing early does not buy a week of runway — it buys only the
difference between the old expiry and seven days from the moment of re-authorization.

Old expiry 2026-08-14T21:49:55Z, new expiry **2026-08-15T22:05:28Z**: roughly **24 hours gained**,
not six days. **This deadline recurs every week and always will.** Manual re-authorization is a
permanent weekly operating cost, not a one-off.

What genuinely improved is the *weekday*. The old expiry fell on a **Friday**, when re-authorizing
means restarting live trading containers on a trading day. The new one falls on a **Saturday**, and
the cadence is self-perpetuating: re-authorize on a Saturday and the next expiry is the following
Saturday. That is the durable win from this window, and it was a side effect of the timing rather
than a designed outcome. **Keep it there** — re-authorizing mid-week would drag the deadline back
onto a trading day and it would stay there.

The real fix for the recurring cost is out of scope here and unexamined: whether the gateway can
hold the sole credential and serve the trading apps, so that one re-authorization does not require
restarting five containers. That is the question C3 and the eventual cutover exist to answer.

### Window F addendum 3 — the locked write is proven in production (2026-08-08)

Addendum 2 recorded the locked *write* as unobserved. It was observed shortly afterward, at
23:21 UTC, and the evidence is conclusive by elimination.

The host document moved from inode `20446` to **`12602`**, digest `80a525dfea9a`. An inode change is
an `os.replace`. The keepalive cannot produce one — it persists through
`client_from_token_file`, whose writer truncates in place and keeps the inode. The gateway logged
**zero** `refresh_succeeded` in the surrounding 45 minutes. Each of the three trading apps logged
exactly one `POST /v1/oauth/token`, at construction, and every one of those fires authlib's
`update_token` into the new `_write_token`. The replace therefore came from the trading apps' new
path — the first atomic, locked token write they have ever performed.

It happened under genuine contention: three apps constructing within the same second, plus the 23:00
keepalive taking the same lock. `schwab_token_persist_failed` is **zero** across all three, so no
writer timed out at the 10s bound. All five consumers and the host still agree on one inode and one
digest.

The 23:00 keepalive also succeeded, reporting **167.1h** remaining — the first hourly run against the
new credential, on the production path.

This closes the C1 gap end to end: decided in Window C, found unimplemented for the trading apps in
Window F, fixed, deployed, and now exercised under real contention rather than only in tests.

## Window G — SIGTERM handled, exit 137 eliminated (2026-08-08)

Executed 2026-08-08, one commit `e5860fd`, pushed and pulled to Helios. Window G reviewed the Window
G brief against the code, implemented and deployed the SIGTERM fix, and proved it in production on
all three trading apps. The re-authorization was **not** performed — it is not due until
2026-08-15.

### The fix

`install_shutdown_handler` (`run_live.py:710`) is installed at the end of the TaskGroup body and
cancels the supervised child tasks on SIGTERM. Child cancellation, not parent cancellation, is the
load-bearing choice: `asyncio.TaskGroup._on_task_done` returns early for a child cancelled from
outside, so no error is recorded, the group exits normally, and the existing `finally` runs.
Cancelling the parent would also work but raises `CancelledError` out of `asyncio.run` and would
need an `uncancel()` to exit zero.

Chosen over `init: true`, which kills promptly but skips the `finally` entirely — leaving the DB pool
open and readiness unset — and which would have edited `infra/docker-compose.yml`. **The compose
SHA-256 pin in `test_gateway_compose.py` is unchanged**, still `5e7804fe…`; this fix needed no
compose edit at all.

The brief's stated hazard — `except* Exception` reporting a normal shutdown as `task_group_error` —
does not arise, and not for the reason given. `CancelledError` is a `BaseException` and would not be
caught by `except* Exception` anyway; more to the point, under child cancellation the group raises
nothing, so that handler is never reached. Confirmed by zero `task_group_error` across all three apps
through six shutdowns.

### Proven in production, not only in tests

Preconditions cleared first: ET Saturday 20:00, market closed; `butterfly_trades` held 224 rows, all
`CLOSED`, zero `OPEN`.

Rebuilt all three images, recreated the three trading services **by explicit name** so Compose would
not start the legacy `app_spx_candidate` (confirmed still `Exited (137) 11 days ago`, untouched).
Then each app was stopped and started to measure the real shutdown:

| container | stop duration | exit code |
|---|---|---|
| `butterfly_xsp_app` | 0.75 s | **0** |
| `butterfly_spx_app` | 1.36 s | **0** |
| `butterfly_ndx_app` | 1.78 s | **0** |

Previously every one of these was 10 s of grace followed by SIGKILL and exit 137. The XSP log shows
the whole chain: `shutdown_signal_received` → `schwab_client_closed` → `database_pool_closed`. Those
last two are exactly what `init: true` would have skipped.

All three then logged `schwab_client_initialized`, which only emits after a real authenticated
`get_account_numbers()` 200. `schwab_token_persist_failed` is **zero** across all three.
`RestartCount=0` on all five consumers.

### What today did *not* prove

The locked write path was **not** re-exercised. All three apps logged **zero** `oauth/token` POSTs at
construction — the access token was still valid, so authlib had nothing to refresh and nothing to
persist. The host document accordingly stayed on inode `12602`, digest `98a5d4608f22`, unchanged
across the entire deployment. The locked write remains proven by Window F addendum 3 and by the three
lock tests; it was not re-proven today.

Note this corrects a Window F expectation: the brief predicted the inode would move because "the
keepalive writes hourly and every atomic replace mints a new inode." The keepalive writes **in
place** and keeps the inode. Only a trading-app persist mints a new one, and only when a refresh
actually occurs. A stable inode across hours is normal, not evidence of a stalled keepalive.

### End state — verified host-versus-container, 2026-08-09 00:15 UTC

- All five token consumers **and the host** agree: inode `12602`, digest `98a5d4608f22`, mode `600`,
  uid `1001`, 787 bytes.
- Gateway `running` / `healthy` on `monitoring_net`; `up{job="schwab_gateway"} == 1`;
  `SchwabGatewayDown`, `ButterflyGuySchwabApiErrors`, `CandidateFeedSchwab429` all **inactive**.
- Cron 31 lines, 2 keepalive entries. Last keepalive 00:00:18Z: "OK: token refreshed, SPX quote
  fetched (status 200), refresh token expires in 166.1h."
- Baseline `uv run python -m pytest` is now **975 passed, 1 skipped, 0 failed** (973 before Window G
  added two shutdown tests). `uv run ruff check .` clean.

### The deadline

Re-derived from `creation_timestamp + 7d`: created 2026-08-08T22:05:28Z Sat, **expires
2026-08-15T22:05:28Z Sat**, 166.0 h remaining — agreeing with the keepalive's independently reported
166.1 h.

The Saturday cadence holds, but the safe window is **one day wide**, not a week. 2026-08-15 is the
only Saturday before expiry, and the re-auth must land before 22:05 UTC that day. A slip puts the
next expiry on a Sunday and it stays there. Corollary the Window F record does not state: each
Saturday's re-auth must be no *later* in the day than the current expiry's time of day, so doing it
early in the day banks permanent slack while doing it late spends it.

### Corrections to the Window G brief

- **`client_from_token_file` is not called at `run_live.py:742`.** It is not in `run_live.py` at all;
  Window F's own change removed it. `run_live.py:741` builds `SchwabClientWrapper`, and
  `schwab_client.py:65` uses `client_from_access_functions`. The *mechanism* claim survives — the
  token is still read once at startup and held in memory, so a directory bind still does not force a
  re-read — but the citation is dead. `client_from_token_file` does survive in
  `tools/schwab_token_keepalive.py:117` and `backtest/schwab_loader.py:50`.
- **"C3 — the code still does not exist" is wrong.** `gateway_client/shadow.py` is 318 lines with
  `ShadowComparingMarketDataProvider` and `ShadowDiscrepancyRecorder`, fully covered by
  `tests/test_gateway_shadow_reads.py`, and `GatewayClientSettings` (`gateway_client/config.py:11`)
  already carries the `gateway_url` / `gateway_api_key` surface. What does not exist is the **wiring**
  — nothing outside tests imports it and `run_live.py:743` still builds a bare
  `DirectSchwabMarketDataProvider`. C3 is a wiring-and-key task, not an implementation task. The plan
  doc is precise about this; the brief compressed it wrongly.
- `issue_gateway_keys.py` refuses to overwrite at **`:94`**, not `:93`, and lives at
  `src/butterfly_guy/scripts/`, not `tools/`. The `:50` citation is exact.
- **There are two keepalive logs and one is a decoy.** `/opt/butterflyguy/data/keepalive.log` is
  abandoned, mtime **2026-04-20**. The live log is `/opt/butterflyguy/keepalive.log`. Reading the
  stale one would suggest the keepalive died in April.
- The repo has a second untracked file the brief does not mention,
  `docs/ai/BRANCH_REVIEW_INTEGRATION_PLAN.md`, alongside `Fable_refactor/fly_Spec.html`. Both left
  alone.

### Still open after Window G

The Monday snapshot check is **deferred a third time** — it is gated on the 2026-08-10 open and
Window G ran on a Saturday. Nothing about the feed's Schwab authentication was learned today; it has
still never been observed on a real call. C3 wiring, the weekly re-auth cost, and the
`issue_gateway_keys.py` append mode are untouched.

## Window H — verification held; the deadline reminder is mistimed (2026-08-08)

Executed 2026-08-08 17:12 PDT / 2026-08-09 00:12 UTC, a Saturday evening. Read-only on Helios
throughout. No container was restarted, no re-authorization was performed, and no code changed.

### The deadline, re-derived from the document

`creation_timestamp` **2026-08-08T22:05:28Z** (Sat) + 7d = expiry **2026-08-15T22:05:28Z** (Sat),
**165.88 h remaining**. The keepalive independently reported 166.1 h at 00:00:17 UTC — agreement
within 0.1 h, exactly as the brief claimed.

A 2-hour-old `creation_timestamp` looked alarming and is not. Window F re-authorized at
2026-08-08T22:05:28Z, six days early, and Window G ran later the same evening; the brief for
Window H was written at 00:15 UTC. The consecutive keepalive entries decrease 167.1 h → 166.1 h,
which also confirms the keepalive does **not** reset `creation_timestamp` — so `creation_timestamp
+ 7d` remains the authority.

**The re-auth was not performed and was not due.** Per the brief, re-authorizing early buys hours,
not a week. The operator holds the 2026-08-15 execution.

### The deadline in local time — stated because the brief did not

Expiry 22:05 UTC is **15:05 PDT**. The safe window on 2026-08-15 is Saturday **morning to midday**
local, not Saturday evening. This session ran at 17:12 PDT; the equivalent moment next Saturday
would already be two hours past expiry.

### Finding — the weekly reminder fires after the deadline it protects

The `--sunday-reminder` cron is `50 1 * * 1` = **Monday 01:50 UTC**, which is **27.7 hours after**
the Saturday 22:05 UTC expiry. It can never prompt a re-authorization in time. It was presumably set
in local-time thinking — Monday 01:50 UTC is Sunday 18:50 PDT — but the deadline is Saturday
afternoon local, so Sunday evening is still too late.

The only automated warning that lands before expiry is the hourly keepalive's `WARN_BEFORE = 8 *
3600` window (`schwab_token_keepalive.py:39`), opening at **2026-08-15T14:05Z / 07:05 PDT** — 8
hours of margin, and it fights the "re-authorize early in the day" corollary, since acting when it
fires means acting almost immediately.

Not changed: the keepalive cron requires an explicit operator decision. Recorded for that decision.
The brief's end-state check "cron 31 lines / 2 keepalive entries" passes and is not sufficient —
it counts the entries without checking their timing.

### Tasks 3–6 — all green, verified host-against-container

- **Shutdown fix held.** `task_group_error` **0** on all three trading apps; all `RestartCount=0`,
  status `running`, last exit code `0`. No container has exited 137 since Window G.
- **Locked write healthy.** `schwab_token_persist_failed` **0** on all three trading apps.
- **One inode, one digest, six ways.** Host `/opt/butterflyguy-tokens/tokens.json` at inode
  **12602**, digest **`98a5d4608f22`**, 787 bytes, mode 600, uid/gid 1001 — and all five consumers
  agree with the host. Unchanged from Window G, which is expected: only a trading-app persist
  following a real refresh calls `os.replace`, and no refresh occurred.
- **End state.** Gateway `running`/`healthy` on `monitoring_net`; `up{job="schwab_gateway"} == 1`
  with instance `butterfly_schwab_gateway_live:8011`; no Schwab or candidate alert firing; cron 31
  lines / 2 keepalive entries; keepalive succeeding hourly.
- **No open trades.** `butterfly_trades` 224 rows, all `CLOSED`. Market closed (Saturday).
- **Baseline re-derived, not trusted:** `uv run python -m pytest` → **975 passed, 1 skipped**;
  `uv run ruff check .` clean. Helios on `7401dea`, same branch, only the two
  `configs/universes/` files modified as expected.

### Task 2 — the Monday check is deferred a fourth time

This window ran on a Saturday evening with the market closed. `/ready` returned
`503 snapshot_unavailable`, which is expected of a closed market and is **not** a fault, and
`docker logs butterfly_spx_candidate_feed | grep -c api.schwabapi.com` is **0 all-time** — the feed
has never made a Schwab call in this container's life.

**Nothing was learned about the feed's authentication.** It has still never been observed on a real
call. The check is owed at or after the 2026-08-10 open (09:30 ET / 13:30 UTC).

### Deliverables

- `docs/runbooks/reauthorization-2026-08-15-checklist.md` — operator-executed checklist for the
  2026-08-15 re-auth, per operator decision that they run it. Window F's sequence with the local-time
  deadline, the gateway-first ordering, the terminal-not-`!` warning, host-vs-container verification,
  and the mistimed-reminder workaround folded in.
- `docs/architecture/reducing-the-weekly-reauth-cost.md` — the open item the operator chose. Scoping
  question only; nothing built, no decision taken.

### Corrections to the Window H brief

- **`run_live.py:743` has drifted.** The bare `DirectSchwabMarketDataProvider` is constructed at
  **`run_live.py:764`**; `:763` is `await schwab.initialize()`. Line 743 is `start_metrics_server`.
  The brief asserted this anchor "is still exact" — it is not. (The Window G record above carries the
  same stale `:743`.)
- **The brief's premise for the gateway cutover is incomplete.** "If the gateway held the sole
  credential and the trading apps read through it, one re-authorization would not require restarting
  five containers." The gateway serves three read routes, all market data. The trading apps also call
  `get_account_numbers` at startup and `place_order` / `get_order_status` / `cancel_order` during the
  session, and account and order operations are forbidden on the gateway by standing policy. So a
  full market-data cutover takes the restart count from **5 to 4**, not to 1 — only the candidate
  feed could become credential-free. Detail in the scoping doc.
- **The restarts exist for one narrow reason, and it is cheaper to attack directly.** schwab-py's
  `client_from_access_functions` calls `token_read_func()` **exactly once** at construction
  (verified in the installed `schwab/auth.py`), then holds the token in the `AsyncOAuth2Client`
  session for the process lifetime. The restart's only useful effect is re-running that one read.
  `_read_token` is already pluggable and already takes the C1 lock, so a `reload()` that re-runs
  `client_from_access_functions` and swaps `self._client` would take the weekly cost to **zero**
  restarts. Scoped, not built; the deciding question is whether a mid-session client swap has a safe
  point against the 60 s collector cycle and the 2 s position poll.

### Still open after Window H

The Monday snapshot check (2026-08-10 open), now owed a fourth time. The 2026-08-15 re-authorization,
held by the operator. The mistimed `--sunday-reminder` cron. C3 wiring and the gateway key re-issue.
`issue_gateway_keys.py` append mode. Gateway reboot survival, still proven by policy not by test.
The credential exposure from Windows E and F, still left to the operator.

### Window H addendum — a keepalive write observed live (2026-08-09 01:00 UTC)

The hourly keepalive fired during the session and was caught in the act, which converts two
previously *asserted* facts into *observed* ones.

Before (00:12 UTC): inode `12602`, digest `98a5d4608f22`.
After (01:05 UTC): inode **`12602` unchanged**, digest **`e66fb6642ef4`**, still 787 bytes.

- **The keepalive truncates in place.** The digest moved while the inode did not. This is the first
  direct observation of the Window G correction, which until now rested on reading
  `client_from_token_file` rather than on watching it. **A stable inode is not evidence of a stalled
  keepalive; a stable digest would be.** Window G could not show this because no refresh occurred
  during it.
- **`creation_timestamp` survives a keepalive refresh.** Still `2026-08-08T22:05:28Z`, expiry still
  `2026-08-15T22:05:28Z`, after a write that demonstrably changed the document. The deadline
  derivation `creation_timestamp + 7d` is therefore load-bearing-safe: an ordinary refresh does not
  push the deadline out. Previously this was inferred only from the keepalive log's remaining-hours
  decreasing 167.1 → 166.1 → 165.1 h.

Host and all five consumers re-verified in agreement on the new digest, host-against-container. All
five `running`, `RestartCount=0`. The directory bind propagates an in-place rewrite to every
consumer's view immediately — as it must, since it is the same inode.

Note the asymmetry this exposes: consumers see the new *bytes* instantly but continue to use the
token they parsed at startup, because schwab-py holds it in memory. Visibility was never the problem;
re-reading is. See `docs/architecture/reducing-the-weekly-reauth-cost.md`.

## Window H part 2 — the expiry warnings fixed, and the reload question answered (2026-08-09)

Operator instruction: address items 1–3 of the Window H summary. Item 2 was a finding already
recorded and needed no action. Items 1 and 3 follow.

### Item 1 — the warnings now fire before the deadline (deployed)

Commit `34aca5f`, pulled to Helios, crontab updated in place.

Two independent defects, both leaving the Saturday deadline effectively unwarned:

- `--sunday-reminder` at `50 1 * * 1` = Monday 01:50 UTC, **27.7 h after** the Saturday 22:05 UTC
  expiry. It could never prompt a re-auth in time.
- `WARN_BEFORE = 8 * 3600` opened the alert window at 07:05 PDT **on the morning the token died**,
  which is also the morning the re-auth has to happen — no slack at all.

Both stemmed from the pre-Window-F design, when the intent was a Sunday-evening re-auth before
Monday's open. The Saturday cadence made that obsolete and nothing was re-timed.

Now: reminder `0 14 * * 5` (Fri 07:00 PDT, **32.1 h** lead) and `WARN_BEFORE = 24 * 3600` (window
opens Fri 15:05 PDT, **24.0 h** lead).

**The reminder moved to Friday, not to Saturday morning, deliberately.** As slack is banked by
re-authorizing earlier each Saturday, the deadline drifts *earlier in the day*, so a fixed
Saturday-morning reminder would eventually become too late again — the same class of bug being
fixed. A Friday reminder keeps 24 h+ of lead regardless of where in Saturday the deadline sits.

`--sunday-reminder` is still accepted as an alias of `--weekly-reminder`, so a host whose crontab
lagged the pull would keep sending reminders rather than silently sending none.

Verified: threshold behaviour exercised at 30 h / 20 h / 6 h remaining → `healthy` / `sent` / `sent`
(under the old 8 h, 20 h would have been silent); both flag spellings drive the reminder; crontab
still **31 lines / 2 keepalive entries** with the reminder on line 3; and the hourly job re-run on
the production path exits `0` — "OK: token refreshed, SPX quote fetched (status 200), refresh token
expires in 164.1h".

**Not proven: the Telegram transport for the reminder itself.** The hourly alert path uses
`send_alertmanager`; `notify()` is used *only* by the reminder, so its delivery has never been
observed either before or after this change. Firing it would send a real message to the operator's
phone and was not done unprompted. Backup of the previous crontab at
`/opt/butterflyguy/crontab.backup-2026-08-09`.

### Item 3 — the deciding question is answered: the swap is safe

`docs/architecture/reducing-the-weekly-reauth-cost.md` updated. Still **not built**.

Every one of the 26 client call sites in `schwab_client.py` resolves the bound method **eagerly**
and passes it into `_retry` — `self._retry(self.client.get_option_chain, ...)` evaluates
`self.client.get_option_chain` before `_retry` is awaited. An in-flight call therefore holds its own
reference to the client it started on and completes against that object, whose access token is still
valid in memory. **Rebinding `self._client` cannot disturb a request in flight, and no
reference-counting is needed.**

The hazard is not the swap but `close()` (`:401`), which calls `close_async_session()` and *would*
break in-flight requests. The reload must not close the old session immediately — either leave it to
GC (one orphaned session per weekly reload) or close after a delay exceeding the worst-case
`MAX_RETRIES`/`RETRY_BACKOFF` chain.

So the cheap option is genuinely cheap, and the recommendation is now to build it. The failure mode
to get right is a *silent* reload failure: log, alert, keep the old client, retry — never leave an
app running on a credential it believes is fresh. Deployment recreates trading containers, so the
natural moment is alongside the 2026-08-15 re-authorization — the last one it would not help with.

### Item 3 built — the token reload (2026-08-09, NOT deployed)

Commit `9fbd9f6`. Baseline moves **975 → 983 passed, 1 skipped**; `ruff` clean.

`SchwabClientWrapper.reload_if_reauthorized()` rebuilds the client when the document's
`creation_timestamp` moves, and `token_reload_loop` (`run_live.py`) polls it every
`TOKEN_RELOAD_INTERVAL = 300s` as a sixth supervised task.

Design decisions worth keeping:

- **`creation_timestamp` is the change marker, not the refresh token.** It moves only on
  re-authorization — schwab-py preserves it across ordinary refreshes, which the Window H addendum
  observed directly — so the hourly keepalive rewrite does not trigger a rebuild. It is also not a
  credential, so it can be read and compared without touching a secret value.
- **Verify before installing.** The candidate client resolves the account hash against Schwab
  *before* it replaces the live one. A bad document therefore leaves the process on the credential
  that still works, which is the silent-failure mode the scoping doc flagged as the one to get right.
- **The displaced client is not closed immediately.** Closing it would abort requests in flight
  against it. It is held as `_retired_client` and released at the next reload or at `close()`.
- **The marker does not advance on a failed reload**, or the retry would be skipped forever. Tested.
- **An unreadable marker at startup does not fail startup** and is adopted on the first check rather
  than being mistaken for a re-authorization. The marker is an optimisation, not a credential
  requirement.
- **A failed reload never faults the TaskGroup** — logged as `schwab_token_reload_failed` and
  retried, because the old client is still holding a working access token.

Six new tests: reload is a no-op on an unchanged marker; swaps on a changed one without closing the
old session; keeps the working client and the old marker when the new document fails to
authenticate; `close()` releases both sessions; an unreadable marker is adopted; and the loop
survives a failed reload and retries.

**Unproven and honest about it:** this has never run against a real re-authorization. It is covered
by tests only. The first genuine exercise would be the 2026-08-15 re-auth, and it is **not deployed**
— no container was recreated, and deploying it requires recreating the three trading apps, which is
an operator decision wanting a closed market.

### Correction to Window H part 1

"No tests cover this script", written of `tools/schwab_token_keepalive.py` while fixing the reminder
timing, was **wrong** — `tests/test_schwab_token_keepalive.py` exists and covers it. The grep that
produced the claim filtered on the reminder flag and `WARN_BEFORE` and so missed the file. The
`WARN_BEFORE` 8h → 24h change duly broke a parametrized case that used 24h as its "healthy" example;
the case now uses 25h, and 20h/24h cases were added to pin the new inclusive boundary. Caught by the
full suite, not by the targeted run — the reason the standing constraint says to re-derive the whole
baseline.

### Window H correction — the restart arithmetic was wrong, and the gateway never needed restarting

Found 2026-08-09 while checking when the reload could first be exercised. Two errors, both in claims
this window itself made, and one of them inherited from Window F.

**1. The gateway holds no token between requests, so it does not need a restart at all.**
`LockedSchwabClientAdapter.execute` (`token_adapter.py:64`) constructs a client, runs **one**
operation, and discards it, entirely inside a single locked token transaction. `live_provider.py`
documents this as deliberate and load-bearing — "one transaction per call". Every gateway read
therefore re-reads the document under the C1 lock.

The Window F instruction to restart the gateway **first**, because "it holds the old refresh token in
memory and would have written it back over the new document", is **false**. It has been repeated in
every brief since and is baked into the 2026-08-15 checklist, now corrected. Restarting the gateway
is harmless and mildly reassuring, but it is not required and nothing needs sequencing around it.

**2. The reload covers three of five consumers, not five.** There are three separate token paths:

| Consumer | Token lifetime | Restart on re-auth |
|---|---|---|
| gateway | fresh client per request, under the lock | **never needed** |
| spx / ndx / xsp apps | `client_from_access_functions` once at startup | yes → **no**, once the reload deploys |
| candidate feed | read once at first use, cached in memory, never written back (`candidate_fleet/schwab_market_data.py:29`) | **yes**, not covered |

So the baseline was **4**, not 5, and the reload takes it to **1**, not 0. "5 → 0" as recorded in the
Window H part 2 section above is wrong. The feed is now the only consumer forcing a weekly restart,
which makes extending the reload to it — or cutting it over to the gateway — the deciding step for
reaching zero. The feed version is the cheaper of the two: it resolves no account hash, so there is
nothing to verify before swapping.

Neither error was caught by tests, because both are facts about *other* services' construction
patterns that no test in this repo asserts.

**3. Deploy the reload before the re-authorization, not after.** Window H's own guidance — "re-auth
first and verify fully, then rebuild" — delays the reload's first real exercise by a week for no
gain. Deploying first makes the 2026-08-15 re-auth itself the test: the rebuild restarts the apps
anyway, and if the reload does not fire the fallback is to restart them by hand, which is exactly the
existing procedure. Low risk, high information. The checklist now carries this as step 0.

## The token reload is DEPLOYED (2026-08-09T21:59:16Z)

Supersedes "Item 3 built — the token reload (2026-08-09, NOT deployed)" above. The operator asked for
a merge and a deploy; the branch was merged to `main` via PRs #13 and #14 and the three trading apps
were rebuilt and recreated. **Every earlier statement in this file that the reload is not deployed is
now false.**

Conditions were correct: Sunday, market closed, `butterfly_trades` flat at 224 rows all `CLOSED`.

- Trading apps recreated `2026-08-09T21:59:16Z` on new images **`9a7fcf6f0704`** (spx) /
  **`4d3f578c8cfd`** (ndx) / **`efc7c0e0c590`** (xsp). The Window G values `5912986ea455` /
  `a71eacd32eb2` / `a092423a6257` are stale.
- **Gateway (`22baff9404c3`) and candidate feed (`97201c17e372`) were NOT rebuilt** — still their
  2026-08-08 containers. The CD deploy step only names `app_spx app_ndx app_xsp`.
- `token_reload_loop` confirmed present in the running SPX image, so the deployed code is the merged
  code, including the operator's `56e483d` hardening.

Post-deploy state, verified: all three `/ready` 200; `up == 1` for all three plus the gateway; **zero
errors and zero warnings** in any app since the deploy; `schwab_client_initialized` once per app,
which is a real authenticated Schwab call against the live document; `schwab_token_reloaded` **0**
and `schwab_token_reload_failed` **0**, which is correct — no re-authorization has happened since the
deploy, so the marker has not moved and there is nothing to reload.

### The C1 write proved itself in production, on the new code

The token document's inode moved **`12602` → `776`** after the deploy, digest `85d607826a0d`, still
787 bytes, mode 600, uid/gid 1001, schema and `creation_timestamp` intact, and all five consumers
agreeing with the host. Only a trading-app persist calls `os.replace`; the keepalive truncates in
place. So a newly deployed app refreshed its access token and wrote it through the shared C1 lock
atomically, with **zero `schwab_token_persist_failed`**. Window F proved that path under synthetic
contention; this is the first observation of it in ordinary operation, on the post-merge code.

### What this changes about 2026-08-15

- **Checklist step 0 is done.** Do not rebuild; the reload is already live.
- **The three trading apps should need no restart.** After the locked move, watch for
  `schwab_token_reloaded` in their logs within `TOKEN_RELOAD_INTERVAL` (300 s). That is the test.
- **The candidate feed still needs its restart** — it is not covered by the reload.
- **The gateway needs none**, per the 2026-08-09 correction.
- **Expected restarts on 2026-08-15: one, the feed.** Down from the four this work started with.
- If `schwab_token_reloaded` does not appear, fall back to restarting the three apps by hand, which
  is the pre-existing procedure, and record that the reload did not fire.

### Unchanged by any of this

The candidate feed has still made **zero** Schwab calls in its container's lifetime and its
authentication has still never been observed. It was not rebuilt and not restarted. The 2026-08-10
open remains the test.

## Candidate-feed authentication proven (2026-08-10)

The repeatedly deferred market-open check is complete. At `2026-08-10T09:11 PDT`, the running
`butterfly_spx_candidate_feed` returned:

```text
200 {"status": "ready", "reason": null}
schwab_calls_30m=151
schwab_calls_alltime=1409
auth_error_scan:
```

This proves that the candidate feed authenticated against the current shared token, reached Schwab,
and built a ready snapshot. The empty bounded error scan found no `error`, `denied`, `401`, or `403`
markers in the preceding 30 minutes. No container, service, configuration, credential, or deployment
state was changed; `candidatectl apply` was not run.

This closes the 2026-08-10 check recorded above. It does not pre-prove the token that will be minted
at the 2026-08-15 re-authorization: until the candidate feed's new hot-reload path is deployed and
proven, that feed still requires its one explicit restart after the locked token move and a new
authentication check at the next market open. The three trading apps' deployed reload remains
scheduled for its first production exercise during that re-authorization.

## Candidate-feed hot reload built locally (2026-08-10, NOT deployed)

The next offline slice adds the candidate feed's separate hot-reload path. The running Helios feed
is unchanged and still requires the one restart in the 2026-08-15 checklist until a separate live
deployment is explicitly approved and verified.

- `AtomicFileTokenStore.read_locked()` opens the already-created `.tokens.json.lock` read-only and
  takes a shared flock. It coordinates with every exclusive C1 writer while preserving the feed's
  read-only directory mount; it cannot create the lock file or write the token document.
- `ReadOnlySchwabMarketDataClient` now records `creation_timestamp`, checks it every five minutes,
  builds a replacement client only when that re-authorization marker changes, and proves the new
  credential with one bounded read-only `$SPX` quote before installing it.
- A failed marker read, lock acquisition, client build, or validation leaves the working client and
  old marker intact. The loop logs a bounded `candidate_token_reload_failed` event and retries; it
  does not stop collection or make the feed a persistent token writer.
- Live and retired clients have isolated in-memory token callbacks, so a late refresh from an
  in-flight request on the displaced client cannot overwrite the replacement client's memory.
  The displaced session is retained for in-flight work and closed at the next successful reload or
  normal shutdown.
- The feed runner supervises the reload loop alongside collection and cancels both during cleanup.

Focused verification is **26 passed** across the candidate market-data and token-manager suites,
and the broader candidate/runtime selection is **40 passed**, with focused Ruff checks clean. The
full repository gate is **993 passed, 1 skipped, 2 pre-existing warnings**; full Ruff and
`git diff --check` are clean. `graphify update .` refreshed the checked-in graph to include the new
shared-lock reader, reload lifecycle, and tests. No Docker, Helios, credential, token, or Schwab
action was performed by the code work.

## Candidate-feed hot reload deployed (2026-08-10T16:54:27Z)

The local slice was committed as `789d8c3`, its exact-release graph as `e40ee7f`, pushed to `main`,
and deployed to Helios while the market was open under explicit operator approval. Deployment was
safe to attempt during the session because all six candidate databases had zero open trades, the
feed was ready, and the targeted command named only `spx_candidate_feed` with `--no-deps`.
`candidatectl apply` was never run, and none of the six evaluators was recreated.

Rollback baseline: remote release `ace76fd`, running image
`97201c17e372fd282f65f1080cfb97aa393e6ebe512e52f9a0b6c0df2890df89`, one feed process,
`/ready` 200, no recent auth/error markers, and exact rollback tag
`generated-spx_candidate_feed:rollback-20260810-97201c17`.

The first recreation used `infra/.env` only. Compose correctly found the token-directory setting but
defaulted the root `.env` database/API variables to blank; the new container failed database
authentication and entered a restart loop. Validation caught it immediately. The exact old image
was retagged and force-recreated with both existing env files, restoring `/ready` 200, restart count
0, one process, and zero recent errors before any further attempt. No evaluator was affected.

The corrected deployment used both `.env` and `infra/.env` and installed image
`f9df84dca695a2514483046c9a73fa967033aca4f3df67e13eeafaf336f97274`. Post-deploy proof:

- status `running`, exit code 0, restart count 0, exactly one process;
- token-directory mount still `rw=false`, with the existing mode-`0600` shared lock visible;
- `/ready` returned 200 with `status=ready`, and five Schwab log calls appeared after startup;
- the running image exposes `reload_if_reauthorized` with a 300-second interval;
- `candidate_feed_sequence=2`, snapshot age 37.4 seconds, and market-open gauge 1;
- no `error`, `denied`, `401`, `403`, or traceback markers after the corrected start;
- all six evaluators remained on their 11-day-old containers and all six databases remained flat;
- exact release and rollback tags resolve to the new and old image IDs respectively.

The 2026-08-15 re-authorization is now the first production marker-change test for both reload
implementations. Expected restarts are **zero**. Watch the three trading apps for
`schwab_token_reloaded` and the feed for `candidate_market_data_token_reloaded`; restart only a
consumer whose reload fails or does not appear after six minutes. The feed's validation quote means
a successful reload proves its new credential even while Saturday snapshot collection is closed.

## Stale-lineage persistence guard deployed (2026-08-10T20:00:48Z)

An early re-authorization was proposed to exercise both hot-reload paths before 2026-08-15, followed
by a second re-authorization on Saturday to restore the Saturday cadence. Review found one race that
the shared lock alone did not close: during the five-minute marker-detection window, a trading app's
old in-memory client could finish an access-token refresh and atomically persist its older
`creation_timestamp` lineage over the newly authorized document. `flock` prevented torn bytes but
did not provide semantic monotonicity.

Commit `4aefb37` adds the guard at the only persistent stale-writer boundary,
`SchwabClientWrapper._write_token`. Under the existing exclusive C1 lock it reads the current disk
marker and refuses an incoming document whose valid `creation_timestamp` is older, logging the
bounded `schwab_token_stale_persist_rejected` event. Same-lineage hourly/access refreshes retain the
existing atomic persistence path. The candidate feed remains a read-only persistent consumer and
needs no equivalent disk guard. A focused reproduction proves that a late old callback leaves the
newer document and inode unchanged.

Verification: focused token/reload suites **40 passed**; full repository **994 passed, 1 skipped, 2
pre-existing warnings**; full Ruff and `git diff --check` clean. Required graphify outputs were
refreshed in `4b70686`. That release also contains the independently committed `8d71471` notify
module relocation; it was reviewed and is covered by the same full gate.

Live deployment waited on one real `XSP|OPEN` position. No running container was touched while it
was open. The cash-settlement path closed the row at `2026-08-10T20:00:23Z`; a second pre-deploy
query returned zero open trades. Only `app_spx`, `app_ndx`, and `app_xsp` were then force-recreated
with `--no-deps` at `2026-08-10T20:00:48Z`:

- SPX image `377ae0b55f3bf7a6656103ebbb3b79175deaaa9adb2e3b0bafb5db0eebb55aa6`;
- NDX image `8f90a18e54a054f1c997e5ed75ba43e1f10cc429a7555b868bedb3379245bc77`;
- XSP image `172beb61abfc2336a3b27050d47e90ce03719614e9a6dab61b1f77bebdfdc1ff`.

Post-deploy: all three `/ready` 200, one process each, exit/restart count 0, exactly one
`schwab_client_initialized` each, zero warning/error-level events, the running source contains the
guard, and the shared token-directory mounts remain writable as required for the three persistent
writers. Open trades remained zero. Gateway start/image, candidate-feed start/image, and all seven
candidate containers were unchanged.

Exact rollback tags are `infra-app_spx:rollback-20260810-9a7fcf6f`,
`infra-app_ndx:rollback-20260810-4d3f578c`, and
`infra-app_xsp:rollback-20260810-efc7c0e0`. Exact release tags are the corresponding
`infra-app_{spx,ndx,xsp}:release-4b70686` tags.

The early marker-change test is now safe to perform. Mint into `/tmp/tokens.new.json`, stage and
move it under C1, then require all three `schwab_token_reloaded` events and the feed's
`candidate_market_data_token_reloaded` within six minutes. Re-authorize again on Saturday—not
Sunday—to restore the Saturday expiry/fallback cadence.

## Early full re-authorization proves zero-restart reload (2026-08-10)

The operator completed the browser flow in a real zeus terminal. The scratch document was a regular
787-byte file with the exact expected envelope, `creation_timestamp`
`2026-08-10T20:23:30Z`, derived expiry `2026-08-17T20:23:30Z`, and digest prefix
`b5e99b7e93cd`. Its initial mode `0644` was corrected to `0600` before transfer. The byte-identical
Helios staging file was schema-checked without printing credential values.

At `2026-08-10T20:27:22Z`, with zero open trades and every consumer running at restart count 0, the
incoming file was moved into place under `flock -w 30 .tokens.json.lock`. Installed state: inode
`776`, mode `0600`, owner `1001:1001`, digest `b5e99b7e93cd`, and the new marker above.

The first real marker-change exercise passed end to end:

- candidate feed: `candidate_market_data_token_reloaded=1`, failure count 0; its mandatory
  read-only `$SPX` validation produced the one Schwab call after the move;
- SPX/NDX/XSP: `schwab_token_reloaded=1` on each, failure count 0;
- stale-write guard: `schwab_token_stale_persist_rejected=0`; no old callback raced this exercise,
  while the deployed regression test remains the proof that such a callback is rejected;
- every app/feed warning/error count 0, every consumer restart count 0, and all three trading
  `/ready` endpoints 200;
- host, gateway, three apps, and feed all saw the same inode `776` and digest `b5e99b7e93cd`;
- open trades remained zero and no `.tokens.json.incoming` file remained on Helios.

The feed's ordinary `/ready` was 503 `snapshot_stale` after the cash close, with
`candidate_feed_market_open=0` and snapshot age about 32.6 minutes. That is a market-data freshness
state, not an auth result; the successful reload event can only occur after its explicit Schwab
validation quote returns 200.

This closes the production-proof block for both reload implementations. No restart fallback was
used. The new token's Monday expiry is deliberately temporary: perform the full flow again on
**Saturday 2026-08-15**, preferably in the morning, to restore a Saturday seven-day cadence. Do not
defer that reset to Sunday.
