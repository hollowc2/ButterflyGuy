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
