# Schwab Gateway Credential Proof

## Status and scope

**Incomplete; three supervised launches stopped before credential access.** This is a standalone,
no-deploy proof for one public `AAPL` quote. It exists to verify the real schwab-py
access-function lifecycle through
`AtomicTokenManager` and `LockedSchwabClientAdapter` before any gateway server, consumer,
shadow read, or service configuration uses real credentials.

The proof:

- reads credentials only from the already-exported process environment;
- requires an absolute token path and uses the locked atomic store;
- constructs a synchronous schwab-py client through `client_from_access_functions`;
- requests only QUOTE and EXTENDED fields for one fixed public symbol;
- does not resolve an account or expose account/order/stream operations;
- prints only `status`, bounded token state, and quote count;
- closes the SDK session and exits without starting a server or service.

The SDK may refresh and atomically replace the token document during the request. Therefore,
the command must not run while any direct process can write the same token.

## Required operator authorization

Before execution, record all of the following without recording secret values or token paths:

- the approved host, operator, UTC window, repository SHA, and rollback owner;
- confirmation that exactly one process owns token writes and every direct writer using that
  token is quiesced for the proof window;
- explicit authorization to read the real credential environment and token document;
- confirmation that no deployment, container action, service restart, consumer cutover, or
  configuration/default change is part of the proof;
- a redacted evidence destination with mode `0600` if output is captured.

Do not source or inspect `.env`, print environment values, copy the token, or put credentials
on the command line. The caller must provide `SCHWAB_API_KEY`, `SCHWAB_SECRET_KEY`, and an
absolute `SCHWAB_TOKEN_PATH` in its existing process environment.

## Command

Run only after the authorization above is complete:

```bash
UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run python \
  src/butterfly_guy/scripts/probe_schwab_gateway_credentials.py \
  --authorize-real-credential-read \
  --confirm-single-token-writer \
  --confirm-no-deployment
```

Success output is exactly the bounded shape below; no quote payload is emitted:

```json
{"quote_count":1,"status":"ok","token_state":"ready"}
```

Any token, factory, HTTP, malformed-response, or close failure returns a bounded command
failure and must not be supplemented with raw exception or credential output.

## Evidence and stop conditions

Capture only command SHA, start/end timestamps, exit status, bounded output, token-manager
state/reason codes, and reviewer disposition. Do not capture the token path, token contents,
API credentials, response body, request headers, cookies, or exception text.

Stop immediately on a non-ready token state, refresh anomaly, lock timeout, malformed quote,
rate limit, authentication failure, unexpected account data, information exposure, evidence
permission failure, or evidence that another token writer is active. Do not retry generically.
The direct runtime remains unchanged; rollback is to leave the proof process stopped, retain
redacted evidence, and restore the previously recorded single-writer operating arrangement.

Passing this proof authorizes neither a gateway deployment nor Phase 3 shadow reads. Those
remain separate reviewed changes.

## Supervised pre-credential stop — 2026-08-04

The first corrected supervised launch used repository SHA
`aba24f52667dda3f348da2079535e345605cd389` on Helios from
`2026-08-04T04:34:17Z` through `2026-08-04T04:34:57Z`. Observed evidence showed the SPX
process suspended, NDX and XSP stopped, the candidate feed token mount read-only, no active
keepalive/direct host client/CI worker, and `single_writer=yes`. The command exited `1` with
empty stdout while importing a native dependency from the temporary execution filesystem.
It emitted raw exception text before reaching the command's existing exception boundary, so
the information-exposure stop condition fired. The retained mode-`0600` evidence replaces
that text with the bounded code `dependency_import_failure_before_credential_settings`.

Code-path inference, not broker evidence: the failure occurred during the command module's
top-level project import, before `GatewayCredentialProbeSettings()` construction, the lazy
`schwab.auth` import, `AtomicTokenManager` construction, or the quote operation was reachable.
Therefore no credential/token read or Schwab request occurred. No proof retry was attempted.
SPX resumed, NDX/XSP restarted on their recorded images, all three health endpoints returned
`ok`, filtered post-restoration error counts were zero, and the temporary source was removed.

The remediation moves all project/third-party imports inside the bounded CLI failure path and
adds a regression test that injects a sensitive import error and requires only the generic
failure line. The real credential proof remains incomplete and requires a merged remediation,
an executable staging filesystem, a fresh single-writer window, and fresh explicit approval.

The local multi-consumer foundation prepares, but does not execute, an isolated executable tmpfs
override and a two-approval restoration plan for that staging blocker. Operational review must use
`../runbooks/schwab-gateway-after-hours-credential-proof.md` and its redacted evidence template.
Nothing in that package changes this document's status: the real proof is still unproven.

## Supervised staging stop — 2026-08-04

A second supervised window used reviewed feature SHA
`3a321bd765ef01356af9d53ef1bd1a17e8c31c08`. Local focused and full validation passed,
and the Helios preflight recorded the existing SPX/NDX/XSP and candidate images, one
application process per trading container, zero active keepalive/direct-host/credential-proof/CI
worker processes, two idle CI listeners, and read-only candidate token ownership. The default
Compose and all three trading configuration hashes matched the recorded local baseline.

The opt-in Compose dry run proved that one executable tmpfs on `app_spx` was the only proposed
configuration delta and that no other service, image, build, or pull was proposed. The supervised
recreation retained the recorded SPX image, started one application process, and added the exact
tmpfs. Post-recreation validation then rejected an order-sensitive runtime configuration
fingerprint. Per the runbook, execution stopped before source staging, synthetic smoke,
single-writer quiescence, Approval 2, credential settings, token access, or a Schwab request.
Retry count remained zero.

SPX was immediately recreated from the recorded image ID without the staging override. Its image,
bounded startup-error count, one-process state, and absence of the executable mount were verified;
NDX/XSP container IDs and images were unchanged. Exact SPX configuration equality could not be
proven because the preflight fingerprint had included nondeterministically ordered Docker mount
lists and Docker no longer retained the destroyed baseline container's Compose hash. The result is
therefore inconclusive, not a successful restoration claim. In accordance with the fail-closed
rule, SPX, NDX, and XSP were paused on their recorded image IDs pending an operator decision. The
temporary overrides were removed, candidate ownership and keepalive absence were preserved, and
the final redacted evidence is mode `0600`.

The operator subsequently approved treating the current direct-access, paper-mode configuration
as a new accepted baseline. A read-only safety gate verified the recorded images; unchanged default
Compose and trading-config hashes; paper mode; disabled live gates; direct Schwab access; recorded
risk limits, token lifetime, and XSP account guard; read-only candidate ownership; staging-mount
absence; and absence of keepalive, credential-proof, direct-host, and active CI-worker processes.
SPX/NDX/XSP were unpaused at `2026-08-04T23:36:21Z`. All three health endpoints, image checks,
container/process uniqueness checks, and staging-absence checks passed. Six filtered error markers
per service appeared immediately after the long pause; all services were healthy, and a fresh
30-second observation window from `2026-08-04T23:37:46Z` recorded zero new filtered errors for each
service. The accepted canonical configuration fingerprints are retained only in mode-`0600`
bounded evidence. This restores service under the operator-defined new baseline; it does not prove
byte-for-byte equality with the destroyed SPX container. The real credential proof remains
incomplete and requires fresh Approval 1 and Approval 2 before any later attempt.

## Supervised pre-recreation stop — 2026-08-05

A third supervised window used remediation SHA
`7435ce0d5934155ff3db9c9f0566d56b7685f601`. Before the window, the focused gateway suite
passed 100 tests, the full suite passed 598 tests with one expected database-dependent skip,
lint and diff checks passed, and the isolated worktree was clean. On Helios, the relevant source,
runtime-config, base-Compose, documentation, and state paths were unchanged even though an
unrelated tracked path made the checkout globally dirty. The default Compose and three trading
configuration hashes matched the accepted sources, and SPX, NDX, XSP, and candidate-feed
containers were running and unpaused.

The exact minimal source archive embedded the approved Git SHA, matched its reviewed SHA-256,
contained no environment, token, credential, data, or evidence files, and yielded the reviewed
fingerprint-helper hash. The committed helper then wrote four mode-`0600` baseline snapshots with
canonical configuration fingerprints, 17 field-level hashes, the Compose configuration hash, and
staging-mount absence.

The attempt stopped before recreation because an ad-hoc operator comparison wrapper violated the
bounded-output rule and emitted a raw programming traceback. No sensitive value was observed, but
the information-exposure check failed by policy. A later optional post-stop wrapper also failed;
its partial process-count lines are explicitly marked invalid and are not evidence. No Compose dry
run, rollback override, SPX recreation, executable mount, container source staging, smoke check,
watchdog, quiescence, Approval 2 request, credential/token access, or Schwab request occurred, and
retry count remained zero.

Before exit, the committed helper proved that all four containers still exactly matched their
just-captured hash-only baselines; each was running and unpaused. This proves no configuration
change during the window, but it does not substitute for the accepted-fingerprint comparison or
the invalid process-count extension. Temporary host-side source artifacts were removed, and the
bounded evidence plus four snapshots remain mode `0600`. The real credential proof remains
incomplete. Any further attempt needs a committed, fake-tested replacement for the failed operator
wrappers and fresh Approval 1.

## Supervised legacy-evidence stop — 2026-08-05

After fresh Approval 1, the exact reviewed archive and committed locator were used only for the
approved read-only search of the reviewed legacy evidence roots. The locator returned the bounded
`no_acceptance` disposition rather than `legacy_evidence_ready`; it did not uniquely link an
explicit non-rejected operator decision to one complete SPX/NDX/XSP fingerprint set.

The run therefore stopped before Compose, container, process, cron, credential, token, or Schwab
mutation. No Approval 2 was requested, retry count remained zero, and the temporary archive and
staging directory were removed. A later attempt requires an explicit operator new-baseline decision
or newly supplied qualifying legacy evidence; neither the current state nor a prior snapshot may be
adopted automatically.

## Legacy-evidence retention remediation

The bounded locator result above was not persisted to the approved evidence destination before the
temporary source artifacts were removed. The documentation summary and execution transcript do not
replace that required mode-`0600` artifact.

The local remediation adds `legacy-evidence-capture`, which validates the exact archive provenance
and approval window, performs the same reviewed legacy-evidence discovery, and exclusively writes
one redacted record before emitting either the ready or failure result. The record contains only
the approved SHA and archive hash, a hash of the approval reference, bounded timestamps and counts,
fixed result codes, retry count zero, and explicit false values for service mutation, credential
read, token read, and Schwab request. It contains no evidence roots, paths, credential values, token
metadata, payloads, URLs, or raw exceptions and will not overwrite an existing destination.

The remediation was subsequently run on Helios under fresh approval using exact commit
`57d4e3792204847a99a6246611877a29cb94e208` and its reviewed mode-`0600` archive. The locator again
returned the bounded `no_acceptance` disposition. This time it durably wrote the approved evidence
artifact before returning; a read-only check verified that the artifact is a Billy-owned regular
file with mode `0600`. The temporary archive and source directory were removed and verified absent.

No Compose, container, process, cron, credential, token, Schwab, staging, quiescence, or Approval 2
operation occurred. The retained evidence does not establish a baseline: an explicit operator
new-baseline decision or newly supplied qualifying legacy evidence remains required.

## Candidate new-baseline capture remediation

The operator-authorized next step is a read-only capture of the current paper/direct SPX, NDX, and
XSP configurations for a separate acceptance decision. The existing committed commands did not own
one combined operation that could prove every required safety condition and durably bind the
resulting records together, so no further Helios action was taken under that authorization.

The local remediation adds `baseline-candidate-capture`. Before producing a candidate it validates
the exact archive and approval window; reviewed Compose and SPX/NDX/XSP config sources; paper mode
and direct-access runtime settings; all four containers running and unpaused; staging-mount absence;
SPX/NDX/XSP health; application-process uniqueness; candidate read-only ownership; absence of
keepalive, host, CI, gateway, or unowned runtime writers; and exact Compose-hash and image equality.

On success it exclusively writes a mode-`0600` evidence artifact containing the three canonical
records, three image IDs, individual check results, and one digest over the exact candidate set. It
emits only that digest and a bounded service count. On a failed safety check it persists only the
bounded failure and no partial candidate. The artifact contains no raw Docker inspection,
environment values, evidence roots, credential/token data, payloads, URLs, or exceptions. A fresh
authorization tied to the new exact SHA/archive is required before this command may contact Helios,
and its output still requires separate explicit operator acceptance before becoming a baseline.

## Candidate capture safety stop — 2026-08-05

Under fresh authorization, exact release `d4ba8fa5b6dd4833c5a310595f160e9275089743`
ran the committed read-only candidate capture on Helios. The command failed closed with the bounded
`compose_semantics_invalid` result before creating a candidate set. It durably retained the failure
artifact as a Billy-owned regular file with mode `0600`; the temporary archive and source directory
were removed and verified absent. No Compose or service mutation, process/cron action,
credential/token read, Schwab request, staging, quiescence, or baseline acceptance occurred.

The broad result does not identify which fixed Compose-related check failed without reading the
artifact. The local remediation adds `baseline-candidate-status`, a strict reader that validates the
entire bounded artifact schema and emits only the single failed-check name. For a successful
artifact it re-derives and emits only the exact candidate-set digest and service count. It rejects
extra fields, partial records, inconsistent check states, invalid images, and altered candidate
hashes without printing stored content. A new exact SHA/archive and fresh authorization are required
before this reader may access the retained Helios artifact.

## Candidate failure diagnosis and scope correction

Under fresh authorization, exact release `ad450dab2f8f15237b7dd78436a312371e16273f`
strictly read the retained artifact and emitted only `failed_check=compose_hashes`. The evidence
validated successfully, remained mode `0600`, and the temporary reader archive/source was removed.
No Docker inspection, service/config mutation, credential/token read, Schwab request, or baseline
acceptance occurred.

Code review then identified that the first candidate capture compared Compose hashes and images for
all four inspected services, including candidate feed. That exceeded the authorized baseline set:
SPX, NDX, and XSP require exact Compose/image equality, while candidate feed was authorized only for
running/unpaused state, staging absence, process uniqueness, read-only ownership, and writer
exclusion. The local correction limits Compose/image equality to the three trading services and
retains every candidate-feed safety check. A trading-service Compose mismatch is persisted and
emitted only as a fixed service name; no hashes or partial candidate are exposed. The correction is
fake-tested only and requires a new exact SHA/archive plus fresh authorization before another
read-only Helios capture.

## Corrected candidate capture safety stop — 2026-08-05

Under fresh authorization, exact release `e4838664f84fda9be032e21fe2c6f9fa273fc2ae`
and archive SHA-256 `6c611947c9becc55a5441e0c6f2117e18fb56070a2a6f055736308ba876c4bf7`
ran the corrected committed read-only candidate capture on Helios. It failed closed with the bounded
`compose_semantics_invalid` result before producing any candidate set. The failure artifact was
durably retained at `/opt/butterflyguy/.baseline-candidate-evidence-20260805-e483866.json` and
verified as a Billy-owned regular file with mode `0600` and size 850 bytes. The exact temporary
archive and source directory were removed and verified absent.

No Compose or service mutation, restart, process/cron action, credential/token read, Schwab request,
staging, quiescence, trading action, or baseline acceptance occurred. Under separate authorization,
the strict artifact reader subsequently emitted only `failed_check=compose_hashes`; it did not emit
`mismatched_services`. This proves that the capture stopped at Compose-hash verification, but does
not distinguish an actual trading-service hash mismatch from invalid bounded output while deriving
a Compose hash. The evidence remained a Billy-owned regular file with mode `0600` and size 850
bytes, and the exact temporary reader archive/source were removed and verified absent. There is no
exact SPX/NDX/XSP candidate set to present for final acceptance.

## Compose-hash ambiguity remediation

The candidate capture previously stopped on the first `OperatorFailure` raised while deriving a
Compose service hash. Its bounded evidence could therefore identify only the `compose_hashes` check,
not whether a reviewed hash was unavailable or a successfully derived hash differed from the live
container label.

The local correction evaluates SPX, NDX, and XSP independently. It emits and persists only fixed
service names in separate `invalid_services` and `mismatched_services` lists, may report both classes
in one bounded result, and still persists no candidate whenever either list is non-empty. The strict
artifact reader accepts those fields only for a `compose_hashes` failure, rejects unknown, duplicate,
or overlapping service names, and remains compatible with the earlier evidence that has neither
field. No raw hashes, Compose output, stderr, configuration, environment, or exceptions are emitted
or persisted. This correction is fake-tested only; another exact release/archive and fresh read-only
authorization are required before it may contact Helios.

## Corrected Compose-hash result — 2026-08-05

Under fresh authorization, exact release `e32b74775e4dd4a5273de12f01a821e5056e01b4`
and archive SHA-256 `3c31a800d26fbbced84f33d320d9abc7a116a735b336a86f14aece09527dc228`
ran the corrected committed read-only candidate capture on Helios. It failed closed with the bounded
result `compose_semantics_invalid`, `mismatched_services=[spx]`, and
`invalid_services=[ndx,xsp]`. SPX therefore differs from its successfully derived reviewed Compose
hash. NDX and XSP did not yield valid bounded Compose-hash results and cannot be classified as
matching or mismatching. No candidate set was produced.

The failure artifact remains at
`/opt/butterflyguy/.baseline-candidate-evidence-20260805-e32b747.json` and was verified as a
Billy-owned regular file with mode `0600` and size 913 bytes. The exact temporary archive and source
directory were removed and verified absent. No Compose or service mutation, restart, process/cron
action, credential/token read, Schwab request, staging, quiescence, trading action, or baseline
acceptance occurred.

The current SPX/NDX/XSP runtime cannot satisfy the reviewed Compose-equality gate and must not be
accepted as the replacement baseline. Further work requires an explicit operator decision between
designing a separately reviewed baseline criterion for the current runtime or preparing an approved
live reconciliation to the reviewed Compose configuration.

## Runtime-baseline path

The operator selected a runtime-baseline capture to unblock the credential-proof implementation
without recreating any service. This is a separate command and does not weaken or replace the strict
Compose-equality capture.

`runtime-baseline-capture` requires the exact reviewed archive and approval window, validates all
three reviewed paper-mode config files, and requires each trading container to bind either the exact
reviewed file or a bounded regular file with identical contents read-only at the expected in-container
destination. It then requires SPX, NDX, XSP, and candidate feed to be running and unpaused with no
staging mount; validates SPX/NDX/XSP health and all process uniqueness; verifies direct access,
candidate read-only ownership, and no host, CI, keepalive, gateway, or unowned runtime writers; and
captures the actual trading-service image IDs and bounded runtime fingerprints.

The command evaluates the reviewed Compose hash for every trading service but records the exhaustive
result as `matched_services`, `mismatched_services`, and `invalid_services` rather than treating
Compose provenance as a runtime-safety gate. Those classifications, the actual image IDs, and the
three exact runtime records are all included in the candidate-set digest. A successful bounded output
therefore presents one digest together with its known Compose exceptions for a separate explicit
acceptance decision. A failure of any runtime-safety gate persists no candidate.

The companion `runtime-baseline-status` reader validates the complete private evidence schema,
re-derives the candidate digest, requires the three Compose classifications to be canonical,
disjoint, and exhaustive, and emits only the bounded digest, classifications, and service count. It
rejects altered records, images, classifications, checks, or extra fields without disclosing stored
content. Neither command reads credentials or tokens, calls Schwab, or mutates services. A fresh
authorization tied to an exact release, archive, evidence destination, and UTC window is required
before the capture may contact Helios.

## Runtime-baseline config-mount safety stop — 2026-08-05

Under fresh authorization, exact release `1e5ccfe7d72478ef73da5b54e4ede18baa697345`
and archive SHA-256 `226191b0f566a0783f1ce26feba1594276cac8c7ed802d37ff4ece8d6c9b33ae`
ran the committed read-only runtime-baseline capture on Helios. It failed closed with
`baseline_mismatch`; the companion strict reader identified
`failed_check=runtime_config_mounts`. No candidate set was produced.

The failure artifact remains at
`/opt/butterflyguy/.runtime-baseline-evidence-20260805-1e5ccfe.json` and was verified as a
Billy-owned regular file with mode `0600` and size 872 bytes. The exact temporary archive and source
directory were removed and verified absent. No Compose or service mutation, restart, process/cron
action, credential/token read, Schwab request, staging, quiescence, trading action, or baseline
acceptance occurred.

The first runtime implementation required the Docker bind source pathname to equal the reviewed
pathname. That is stronger than the selected runtime-baseline policy requires: a different regular
host file can safely represent the reviewed config when its bounded content hash is identical and it
is mounted read-only at the exact in-container destination. The local remediation classifies every
trading service as `config_exact_services`, `config_content_match_services`, or
`config_invalid_services`; requires those lists to be canonical, disjoint, and exhaustive; binds the
classification into the candidate digest; and remains fail-closed with fixed service names for
missing, duplicate, writable, non-bind, unreadable, oversized, or content-different sources. Fresh
authorization remains required before another Helios capture.

## Content-verified mount result — 2026-08-05

Under fresh authorization, exact release `8c7070debb11733092980f7854e66b7678c8dd86`
and archive SHA-256 `f546b9335d8a72260a69772f822f39db78b87b1db1fc535e67ef8a69ee7fa24a`
ran the content-verified read-only runtime-baseline capture on Helios. It failed closed with
`baseline_mismatch` and `invalid_config_services=[spx,ndx,xsp]`. The capture itself emitted the
complete fixed service list, so the companion reader was not needed. No candidate set was produced.

The failure artifact remains at
`/opt/butterflyguy/.runtime-baseline-evidence-20260805-8c7070d.json` and was verified as a
Billy-owned regular file with mode `0600` and size 918 bytes. The exact temporary archive and source
directory were removed and verified absent. No Compose or service mutation, restart, process/cron
action, credential/token read, Schwab request, staging, quiescence, trading action, or baseline
acceptance occurred.

All three reviewed Compose short-form config mounts omit an explicit read-only suffix. The result is
therefore consistent with writable bind permissions for every trading config, not an unknown service
or lost evidence. The operator selected the runtime path and explicitly accepted writable config
mounts as a visible, digest-bound exception for this paper-mode baseline. Read-only mount hardening
remains a separate deployment concern before live trading or gateway cutover.

The local capture still requires a single bind at the exact in-container destination, the expected
config filename under a `configs` directory, and exact bounded content equality with the reviewed
file. It independently classifies the content relation as exact, content-matched, or invalid and the
permission as read-only or writable. Both exhaustive classifications are included in the candidate
digest and bounded output; only invalid content or structure blocks candidate creation. This policy
preserves current runtime behavior while making the writable-mount exception explicit and auditable.

## Writable-exception runtime candidate — 2026-08-05

Under fresh authorization, exact release `dd1d9ef76b448cd0582f9408204e9e7f1eb8d380`
and archive SHA-256 `82fedcb944783526fa1731bcae5da02d667bc68fda4d0eac0ac0dfe93ada6a49`
ran the committed read-only runtime-baseline capture on Helios. Every runtime-safety gate passed and
the command produced candidate digest
`6872c3582cf728f67acba78bf5f7e226b735c40a4be09ea27c135c7641e5320d` for three services.

The bounded candidate classifications are:

- config exact: SPX, NDX, XSP;
- config content-match-only: none;
- config invalid: none;
- config read-only: none;
- config writable: SPX, NDX, XSP;
- Compose matched: none;
- Compose mismatched: SPX;
- Compose invalid: NDX, XSP.

The strict companion reader validated the complete private artifact and independently re-derived the
same digest and classifications. The evidence remains at
`/opt/butterflyguy/.runtime-baseline-evidence-20260805-dd1d9ef.json` and was verified as a
Billy-owned regular file with mode `0600` and size 6,672 bytes. The exact temporary archive and source
directory were removed and verified absent. No Compose or service mutation, restart, process/cron
action, credential/token read, Schwab request, staging, quiescence, trading action, or baseline
acceptance occurred.

This candidate is not the baseline until the operator separately accepts the exact digest together
with the recorded writable-config and Compose-provenance exceptions.

## Runtime baseline accepted — 2026-08-05

The operator explicitly accepted candidate digest
`6872c3582cf728f67acba78bf5f7e226b735c40a4be09ea27c135c7641e5320d` as the new runtime
baseline with writable SPX/NDX/XSP config mounts and the Compose exceptions `SPX=mismatched` and
`NDX/XSP=invalid`. This acceptance covers exactly the three runtime records, actual image IDs,
config-mount classifications, and Compose classifications bound into that digest; it does not waive
any paper/direct, health, process-uniqueness, ownership, no-writer, no-staging, image, or fingerprint
gate.

The authoritative accepted evidence is
`/opt/butterflyguy/.runtime-baseline-evidence-20260805-dd1d9ef.json`. Acceptance did not contact
Helios, mutate services or configuration, read credentials or tokens, call Schwab, place a trade, or
authorize the credential-proof execution. Any subsequent use of this baseline must strictly validate
the private artifact and re-derive the accepted digest before acting.

## Accepted runtime-baseline proof adapter

The local operator now has a distinct, fail-closed path for the accepted runtime baseline. `prepare`
accepts the private artifact only together with its explicit accepted digest and rejects any mixture
with legacy per-service evidence. It strictly validates the artifact, binds the digest into operator
state, and rechecks the current trading records, actual image IDs, reviewed paper-mode config
contents, config-mount classifications, Compose exception classifications, direct-access state,
health, ownership, process uniqueness, and no-writer gates. The state validator re-derives the digest
from the stored records, images, and exceptions on every read and separately preserves the three
reviewed config-content hashes because writable bind contents are not part of Docker's fingerprint.

Because SPX's accepted Compose hash is mismatched, this path never recreates SPX from the reviewed
Compose file. After fresh Approval 1 it requires a fixed mode-`0700` directory to be absent, stages
only the reviewed Python source under `/tmp/.schwab-credential-proof-runtime` in the existing SPX
tmpfs, and verifies the accepted runtime fingerprint is unchanged. Restoration sends `SIGCONT` to
the original SPX process, restarts NDX/XSP if needed, removes only that exact staging directory, and
requires the original container/image/configuration baseline and config-content hashes. The legacy
strict-Compose recreation path remains unchanged for a future baseline that passes its original
Compose gates.

This adapter is local and fake-tested only. It has not contacted Helios, staged source, quiesced a
process, read credentials or tokens, called Schwab, or received Approval 1 or Approval 2.

## Runtime-baseline Approval 1 staging stop — 2026-08-05

The operator authorized Approval 1 for release
`5a472b3da1feefbc1e592785839704b104e94c28`, archive SHA-256
`59e4944d1781cd9954caee42d3a681c3ceba3b8238c317ad2f58113088bf6a8a`, and accepted
runtime-baseline digest `6872c3582cf728f67acba78bf5f7e226b735c40a4be09ea27c135c7641e5320d`.
The archive and Git provenance matched on Helios. The first preflight stopped before Docker
inspection because the checkout lacked the reviewed staging-override file; its bounded failure
state was retained. Repointing only that input to the archive-extracted reviewed copy allowed the
full preflight to pass.

Approval 1 execution then failed closed with `staging_invalid` before native smoke, watchdog arming,
writer quiescence, credential/token access, or a Schwab request. Automatic restoration passed: the
original SPX/NDX/XSP container, image, configuration, and config-content baselines matched; health,
process uniqueness, candidate ownership, keepalive state, and fresh error checks passed; cron was
restored; and watchdog state was cancelled. The exact container and host staging directories plus
temporary archive, rollback override, and cron snapshot were removed. Both private failure state
records remain on Helios as evidence.

The corrected local operator uses Docker's supported `cp --quiet` mode and emits distinct bounded
codes for target creation, archive copy, extraction, and digest verification. No further live
staging attempt is authorized until that correction is committed, archived, fully tested, and tied
to fresh Approval 1.

## Runtime-baseline Approval 1 copy stop — 2026-08-05

Fresh Approval 1 authorized one attempt for release
`62d32ad73243a4bf36819f8e3c838e477c57611a` and archive SHA-256
`765b2179be64695814348d8330adab1149500401ca5843ede95e1ea5ee2ac4f6`. Archive and Git
provenance matched, and the complete accepted-runtime preflight passed. The attempt then returned
the new exact result `staging_copy_invalid`: fixed target creation passed, but Docker's
host-to-container `cp` mechanism did not copy the archive into the existing SPX tmpfs. Native smoke,
watchdog arming, cron disablement, writer quiescence, credential/token access, and Schwab access did
not occur.

Automatic restoration again passed every exact fingerprint, image, config-content, health,
uniqueness, ownership, keepalive/cron, and fresh-error check. The container staging target, private
archive, rollback override, cron snapshot, and exact host source directory were removed; the private
mode-`0600` failure state remains as evidence. A read-only capability check confirmed that the
running SPX image provides GNU `dd` 9.7.

The next local correction removes `docker cp` entirely. It reads only the already validated bounded
archive, streams those exact bytes through `docker exec -i ... dd` into the fixed tmpfs target,
requires silent success, re-verifies the in-container SHA-256, and only then extracts. This remains
local and requires a new committed release, full verification, and fresh Approval 1 before any live
attempt.

## Runtime-baseline staging digest-path defect — 2026-08-06

Local review of release `768dc6d21c6121210e7ed597026ecf49bbb1b99f` found that the streaming
correction verified the staged archive at the fixed legacy `/app` target instead of the caller's
own root target. The runtime-baseline path stages under `/tmp`, and the legacy `/app` tmpfs exists
only under the prohibited staging override, so that path is affirmatively absent whenever the
accepted runtime baseline is in force. The release would therefore have created the target,
streamed the bytes, and extracted them successfully, then failed closed at `staging_digest_invalid`
before native smoke, watchdog arming, quiescence, credential access, or Schwab access.

The existing staging tests only exercised the default legacy root target and monkeypatched both
runtime-mode call sites, so no test covered the runtime root. A reproduction test drives the
runtime root target and asserts that target creation, the `dd` stream, extraction, and the
in-container digest all resolve under `/tmp/.schwab-credential-proof-runtime` and that no command
references the legacy root. It fails against the defective release with the exact `/app` versus
`/tmp` mismatch. A second test requires a digest reply naming the legacy path to be rejected in
runtime mode. The digest gate now verifies the caller's own archive target. No live attempt was
made under the defective release, and a new committed release, full verification, and fresh
Approval 1 are required before any live attempt.

## Runtime-baseline Approval 1 native-smoke stop — 2026-08-06

Fresh Approval 1 authorized one attempt for release
`a54c2343c2ac8cb2e20d6c60329f1a1b1edd720e` and archive SHA-256
`5f3b5c056988a25bb33069c7b1f41c0bcc721767817d5440ba4bc81eb0bb1697` during
`2026-08-06T02:45:00Z`–`2026-08-06T04:35:00Z`.

The first `prepare` failed closed at `baseline_mismatch`. The accepted artifact revalidated to its
exact digest, and live records, images, direct access, and the Compose observation all matched. The
sole difference was the config-mount observation: the accepted digest records
`config_exact_services=[spx,ndx,xsp]`, but passing archive-extracted config paths classifies the
same byte-identical files as `config_content_match_services`. The reviewed config arguments must
therefore be the live config paths whose provenance is separately verified against the archive; only
the staging override, which is absent from the live checkout, comes from the extracted source. The
corrected `prepare` returned `approval_1_ready`.

The single authorized attempt then created the `/tmp` staging target, streamed the archive through
`docker exec -i ... dd`, extracted it, and passed the in-container SHA-256 check at the corrected
target — clearing both the earlier `staging_copy_invalid` stop and the digest-path defect. It failed
at the bounded native smoke check. `_run_exact_json` collapses the staged command's own exit into
the generic `subprocess_failed` code, so the specific inner reason was not recorded.

A bounded read-only check confirmed the running SPX image imports `scipy.special` and `schwab.auth`
cleanly with no stderr. The deployed venv contains a regular, non-editable `butterfly_guy`
distribution with no `schwab_gateway` subpackage, so under the staged `PYTHONPATH` the whole
`butterfly_guy` namespace resolves to the archive's partial tree. `schwab_gateway/__init__.py`
eagerly executes `from butterfly_guy.schwab_gateway.api import create_app`, and the minimal reviewed
archive deliberately omits `api.py` together with its admission/auth dependencies. Importing
`credential_probe` therefore raises `ModuleNotFoundError` inside the package `__init__`.

Automatic exact restoration passed every fingerprint, image, config-content, health, uniqueness,
ownership, keepalive/cron, and fresh-error check with zero filtered errors per service. Quiescence
never started, SPX was never suspended, NDX/XSP were never stopped, and service uptimes were
unchanged. No credential or token was read and no Schwab request occurred. The exact temporary
archive, source directory, rollback override, and cron snapshot were removed; the two mode-`0600`
operator states are retained as evidence. No retry was attempted.

The next correction must remove the import-time dependency from `schwab_gateway/__init__.py` so the
reviewed subset imports standalone, and should also propagate the staged command's own bounded
failure code instead of collapsing it into `subprocess_failed`.

## Standalone reviewed-subset correction — 2026-08-06

`schwab_gateway/__init__.py` now resolves `create_app` through a module-level `__getattr__` instead
of importing `api` at package-import time. Real consumers keep `from butterfly_guy.schwab_gateway
import create_app`, while the reviewed subset imports `credential_probe` without requiring the
omitted `api`, `auth`, and `admission` modules or their dependencies.

`_run_exact_json` now returns the staged command's own bounded failure code when the staged process
exits nonzero, writes nothing to stderr, and emits exactly `{"code": ..., "status": "error"}` whose
code is one of the fixed staged codes `credential_refused`, `native_smoke_failed`, or
`signal_invalid`. Any stderr output, malformed payload, extra field, unexpected status, or
unlisted code still yields the generic `subprocess_failed`, so container output can never introduce
an arbitrary operator code. `credential_refused` now maps to the `refusal_gate` check.

A regression test copies exactly the `_ARCHIVE_PATHS` member set into a temporary tree and imports
`butterfly_guy.schwab_gateway.credential_probe` in a separate interpreter with only that tree
prepended to `sys.path`, asserting both the package and the probe resolve inside it. It reproduces
the live failure with `ModuleNotFoundError: No module named 'butterfly_guy.schwab_gateway.api'`
against the previous package init. This closes the gap that let a staged-environment defect reach
Helios twice: the reviewed subset is now exercised in isolation locally.

## Runtime-baseline Approval 1 watchdog stop — 2026-08-06

Fresh Approval 1 authorized one attempt for release
`ca0d3481dbb53edfde5b1ba9ee03d61935ca4bad` and archive SHA-256
`d980b64558e0f553ff94c3430dee102957f96d071d98682838b86100bbecdf62` during
`2026-08-06T03:41:00Z`–`2026-08-06T05:31:00Z`. `prepare` returned `approval_1_ready` on the first
run once the reviewed config arguments were the live config paths.

The single authorized attempt passed staging, and for the first time passed both the bounded native
smoke check and the refusal gate, confirming the standalone-subset correction. It then failed closed
at `watchdog_invalid` while arming the hard watchdog.

The cause is an access-path prerequisite rather than a code defect in the proof itself.
`_arm_watchdog` invokes `sudo -n systemd-run`, and `_watchdog_active`,
`_watchdog_service_active`, and `_cancel_watchdog` invoke `sudo -n systemctl`. A bounded read-only
check confirmed that `sudo -n` returns `a password is required` for the operator account over the
non-interactive session used for the proof, so no system-level transient unit can be created on this
path. The same check confirmed the account has `Linger=yes` and a running user manager, so a
user-level transient timer is available without privilege escalation and survives session close.

Automatic exact restoration passed every fingerprint, image, config-content, health, uniqueness,
ownership, keepalive/cron, and fresh-error check with zero filtered errors per service. Both
watchdogs recorded `cancelled`, and no transient unit remained in either the system or user manager.
Quiescence never started, SPX was never suspended, NDX/XSP were never stopped, and service uptimes
were unchanged. No credential or token was read and no Schwab request occurred. The exact temporary
archive, source directory, rollback override, and cron snapshot were removed and the mode-`0600`
operator state was retained. No retry was attempted.

The watchdog mechanism must therefore either move to `systemd-run --user` with `systemctl --user`
management, or the operator account must be granted a narrowly scoped passwordless sudoers rule for
the fixed watchdog units. Whichever is chosen, preflight should verify watchdog-arming capability
before quiescence so this prerequisite cannot consume another attempt.

## User-level watchdog and preflight capability gate — 2026-08-06

The operator chose the user-manager path, which needs no privilege escalation and no host security
change. An authorized bounded capability probe on Helios armed one distinctively named transient
`--user` timer far in the future, observed it `active`, cancelled it, and left no residual unit in
either manager. The probe corrected two assumptions: a user-manager run **accepts** `--uid`/`--gid`,
so those arguments are unchanged, and its output is byte-identical to the system-level form:

```
Running timer as unit: <unit>.timer
Will run service as unit: <unit>.service
```

so the existing exact output validation needs no change either.

`_arm_watchdog` now invokes `systemd-run --user`, and `_watchdog_active`,
`_watchdog_service_active`, and `_cancel_watchdog` invoke `systemctl --user`. No operator command
uses `sudo`. The lingering user manager keeps an armed timer alive across session close, so
restoration still fires without the operator process.

`prepare` now calls `_require_watchdog_capability` before capturing the crontab and writing the
rollback override. It arms a transient `probe` unit one hour out, requires it to report active,
cancels it, and requires it to be gone, failing closed with `watchdog_invalid`. `_UNIT_PATTERN`
accepts the added `probe` kind. A watchdog prerequisite therefore now fails during preflight, where
a failure costs nothing, instead of inside the single authorized attempt.

The test suite must never create real transient units: `patch_prepare_success` stubs the capability
gate, and a dedicated test asserts `prepare` invokes the gate and fails closed with
`checks["watchdog"] == "fail"` when it is denied. Further tests assert no watchdog command contains
`sudo`, that `systemctl` calls are `--user`, and that the probe fails closed both when arming is
denied and when the timer never activates.

## Runtime-baseline Approval 1 single-writer stop — 2026-08-06

Fresh Approval 1 authorized one attempt for release
`cc614567b035f8a62cd9355ed3302eb11db44012` and archive SHA-256
`c40d6879e7f339d06808546d58b7be6dfb542d09eb4088f5760f093804cb9e12` during
`2026-08-06T04:42:00Z`–`2026-08-06T06:32:00Z`. `prepare` returned `approval_1_ready`, and its new
capability gate armed and cancelled a transient `--user` probe timer on the host with no residual
unit, proving the watchdog mechanism before the attempt rather than inside it.

The attempt passed staging, native smoke, the refusal gate, and — for the first time — `watchdog`,
confirming the user-manager correction. It armed the hard watchdog, disabled the token keepalive,
and stopped NDX. It then failed closed at `single_writer_invalid` before XSP was stopped, before SPX
was suspended, and before the approval watchdog was armed.

The cause is Docker CLI 29.6.2. The quiescence loop invoked `docker stop --time 20`, and the CLI now
writes `Flag --time has been deprecated, use --timeout instead` to **stdout**, so the captured output
was that notice followed by the container name while the gate required exactly the container name.
The stop itself succeeded; the exact-output rule correctly rejected the extra line. `docker stop
--help` now documents only `-t, --timeout`.

Automatic exact restoration passed every fingerprint, image, config-content, health, uniqueness,
ownership, keepalive/cron, and fresh-error check with zero filtered errors per service. NDX was
restarted on its recorded image and reported no errors afterward; XSP was never stopped; SPX was
never suspended and its uptime was unchanged. The keepalive crontab was restored to its recorded
entries, both watchdogs were cancelled with no residual unit, and staging was removed. No credential
or token was read and no Schwab request occurred. The exact temporary archive, source directory,
rollback override, and cron snapshot were removed and the mode-`0600` operator state was retained.
No retry was attempted.

## Current-flag quiescence stop and stop-output gate — 2026-08-06

Quiescence now stops NDX and XSP with `docker stop --timeout 20`, the form `docker stop --help`
documents, so no deprecation notice reaches stdout.

`prepare` now also calls `_require_docker_stop_output_shape` before the watchdog capability gate. It
requires a fixed probe container name to be absent, then runs the exact quiescence stop command
against that name and requires a nonzero exit with empty stdout. A deprecated or otherwise noisy flag
therefore fails during preflight instead of after NDX has already been stopped. The probe refuses to
run the stop at all if a container with the probe name exists.

Tests assert the stop command uses `--timeout` and never `--time`, that the probe passes on empty
stdout, that it fails closed on the exact observed deprecation notice, that it never issues a stop
when the probe container exists, and that `prepare` fails closed with
`checks["single_writer"] == "fail"` when the gate is denied. `patch_prepare_success` stubs the gate
so the suite never touches Docker.

## Runtime-baseline Approval 1 suspend stop — 2026-08-06

Fresh Approval 1 authorized one attempt for release
`b825f5f2a022d0c2d2d463295dd63e2dc522fee7` and archive SHA-256
`d0cb4566fbc0908b8854660db25f7bc0f083c0fea81bb380ffc0e875c37e1157`. `prepare` returned
`approval_1_ready` with both new capability gates passing on the host.

The attempt passed staging, native smoke, the refusal gate, watchdog arming, and keepalive
disablement, then stopped **both** NDX and XSP — confirming the `--timeout` correction, since the
previous attempt had failed after NDX alone. It failed closed at `signal_invalid` before SPX was
suspended and before the approval watchdog was armed. The staged command's own bounded code
propagated rather than collapsing to `subprocess_failed`, confirming that earlier correction too.

The cause is PID-namespace signal semantics. The SPX container's init is the application itself
(`/proc/1/status` reports `Name: python`, `SigCgt: 0000000100000002`, catching only SIGINT and one
real-time signal). The kernel ignores a default-action signal sent to a PID-namespace init from
**inside** that namespace, and SIGSTOP can never have a handler, so the staged
`internal-signal --action stop` performed `os.kill(1, SIGSTOP)` with no effect and no error. PID 1
remained `S (sleeping)`, and the following `internal-signal-status --expect stopped` correctly
reported `signal_invalid`.

Restoration passed every check with zero filtered errors per service. NDX and XSP were restarted on
their recorded images and reported no errors, SPX was never suspended and its uptime was unchanged,
the keepalive crontab was restored, both watchdogs were cancelled with no residual unit, and staging
was removed. No credential or token was read and no Schwab request occurred. Exact temporary paths
were removed and the mode-`0600` operator state was retained. No retry was attempted.

## Host-delivered SPX suspension — 2026-08-06

Restoration already resumed SPX from the host with `docker kill --signal CONT`, which the daemon
delivers from an ancestor namespace where init protection does not apply; only the suspend path went
through the container. Suspension is now symmetric: `_signal_spx` issues
`docker kill --signal <NAME>`, with `_suspend_spx` sending `STOP` and `_resume_spx` sending `CONT`,
both requiring exactly the container name on stdout. `docker exec` is served by the runtime shim
rather than by PID 1, so a suspended init still permits the separate proof process the runbook
requires. A read-only check confirmed the operator account and the SPX init share uid 1001 with no
user-namespace remapping, so no privilege escalation is involved.

`prepare` now also calls `_require_spx_signal_capability`, which issues the exact host-side signal
command with `CONT`. Sending SIGCONT to an already-running process is a no-op, so the gate proves
permission and output shape without suspending SPX. The orphaned in-container `internal-signal`
command, its `_internal_signal` implementation, and the then-unused `signal` import were removed;
`internal-signal-status` remains in use.

Tests assert that suspend and resume issue exactly `docker kill --signal STOP|CONT`, that an
unexpected output fails closed, that the capability probe uses only `CONT` and never `STOP`, and
that `prepare` fails closed when the gate is denied. The approval-1 fake now echoes the container
name for `docker kill` as well as `docker stop`, matching real CLI behaviour.
