# Schwab Gateway Credential Proof

## Status and scope

**Incomplete; two supervised launches stopped before credential access.** This is a standalone,
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
rule, SPX, NDX, and XSP are paused on their recorded image IDs pending an operator decision. The
temporary overrides were removed, candidate ownership and keepalive absence were preserved, and
the final redacted evidence is mode `0600`. The real credential proof remains incomplete.
