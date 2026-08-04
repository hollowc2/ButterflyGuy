# Schwab Gateway Credential Proof

## Status and scope

**Prepared but not executed.** This is a standalone, no-deploy proof for one public `AAPL`
quote. It exists to verify the real schwab-py access-function lifecycle through
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
