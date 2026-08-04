# After-Hours Schwab Gateway Credential-Proof Runbook

## Purpose and prohibition

This package prepares a supervised after-hours proof; it does not authorize one. During the
market-hours development task, do not run Docker or Compose, access Helios, quiesce a process,
read credentials or a token, contact Schwab, or deploy anything.

The previously observed `butterfly_spx_app` root filesystem is read-only. Its writable `/tmp` and
`/dev/shm` filesystems are noexec, while executable root-filesystem locations are not writable.
The prior staging attempt therefore stopped safely before credential settings, token access, or a
Schwab request.

Do not use any token, credential, application-data, database, or persistent mount for staging. Do
not loosen an existing mount or copy source into one. The proposed fix is the opt-in override
`infra/docker-compose.credential-proof-staging.yml`, which adds only a 256 MiB, ephemeral,
writable-and-executable tmpfs at `/app/.schwab-credential-proof-runtime` to Compose service
`app_spx`. The file is not a default Compose override and must always be named explicitly.

Adding that mount requires recreating exactly `butterfly_spx_app`. Recreation is a live deployment
and requires explicit Approval Boundary 1. The base Compose file remains authoritative for the
current image selection, environment wiring, ports, networks, health configuration, secret
mounts, restart policy, and persistent mounts; the staging override must not restate or alter any
of them.

## Roles and immutable preflight record

Before Approval Boundary 1, designate operator, approver, rollback owner, and watchdog owner.
Record the exact `origin/main` SHA, Compose-source SHA, UTC window, baseline container ID and image
ID, and a redacted configuration fingerprint. Record only booleans or hashes for environment,
secret, and mount preservation—never their values or paths. Confirm the rollback image is locally
available and cannot be garbage-collected during the window.

The approved interruption is two `butterfly_spx_app` recreation/startup periods plus a bounded
single-writer proof interval. The approval record must state an expected duration and a hard
deadline. The single-writer/quiescent interval is limited to five minutes; a host-side watchdog
must begin restoration at that deadline without waiting for further approval.

## Approval Boundary 1 — staging, smoke, and service quiescence

Approval 1 must name `butterfly_spx_app`, the exact SHA, window, operator, rollback owner, expected
interruption, hard deadline, and the opt-in override. It authorizes only:

1. prepare a temporary image-pin rollback override containing the recorded baseline image ID and
   no other service field;
2. recreate only `app_spx` using the base Compose file plus the staging override, with `--no-deps`
   and no build or pull;
3. verify the resulting container uses the recorded image, unchanged redacted configuration
   fingerprint, unchanged networks/health/restart/persistent mounts, and exactly one added tmpfs;
4. stage the reviewed source at the exact approved SHA and record its SHA-256;
5. run a bounded dependency/import smoke check using synthetic inputs only;
6. arm the external restoration watchdog;
7. stop NDX and XSP direct writers, confirm the token keepalive is absent/quiesced, confirm no CI
   worker or host client can write, and suspend the SPX application process while leaving a
   separate proof process possible;
8. verify process uniqueness and the candidate token mount's read-only status without printing a
   mount path or any credential metadata.

The intended recreation command shape is:

```bash
docker compose -f infra/docker-compose.yml \
  -f infra/docker-compose.credential-proof-staging.yml \
  up -d --no-deps --no-build --pull never --force-recreate app_spx
```

This command is documentation, not authorization to execute it. Stop immediately and roll back if
Compose proposes any other service, image change, build, pull, port/network/environment/secret
change, persistent-mount change, or trading-mode change.

The smoke check may prove only that reviewed code and native dependencies execute from the new
tmpfs. It must not instantiate credential settings, inspect the environment, access a token, import
the real credential probe past its bounded refusal gate, or make a network request.

## Approval Boundary 2 — fresh credential/token read and one AAPL quote

Approval 2 is requested only after the smoke check passes and the fresh single-writer record is
complete. It must explicitly authorize one real credential/token read and one fixed AAPL quote.
It does not authorize a retry, gateway server, account lookup, order/position/transaction access,
stream, consumer cutover, deployment, or configuration/default change.

If Approval 2 is not granted within two minutes of quiescence, restore immediately. If granted,
run the already-reviewed bounded proof command once under the remaining watchdog window. Capture
only the fields in the redacted evidence template. Any nonzero exit, non-ready state, timeout,
auth/rate-limit response, malformed result, unexpected output, information exposure, or process-
uniqueness doubt triggers immediate restoration with no generic retry.

## Exact restoration and rollback

Restoration begins on success, failure, approval timeout, watchdog expiry, or operator request:

1. ensure the proof process is absent; do not kill or inspect unrelated processes;
2. resume the recorded SPX process if the staged container remains healthy, restart NDX/XSP on
   their recorded images/configuration, and restore the keepalive's prior schedule/ownership;
3. verify one writer and one expected application process per service, plus bounded health and
   filtered startup-error counts;
4. recreate only `app_spx` from the base Compose file plus the temporary image-pin rollback
   override, omitting the staging override, using `--no-deps --no-build --pull never
   --force-recreate`;
5. require the recreated container's image ID and redacted configuration fingerprint to equal the
   preflight record, proving removal of the executable tmpfs and restoration of the previously
   recorded image/configuration;
6. verify SPX, NDX, XSP, candidate-feed read-only ownership, and keepalive single-writer state;
7. retain only bounded mode-`0600` evidence and remove staged source and temporary non-secret
   overrides after review.

If the baseline image or exact configuration cannot be restored, keep trading processes stopped,
declare rollback failure, and escalate to the rollback owner. Do not improvise a new image,
credential source, mount, or trading configuration.

## Review gates

- The staging override is additive, isolated, ephemeral, and never used by default commands.
- The default Compose file is not changed by this package.
- NDX/XSP and token keepalive are explicit parts of the single-writer and restoration plan.
- No token or credential path/value, account identifier, payload, header, cookie, or raw exception
  belongs in commands, logs, evidence, tickets, or chat.
- A successful proof still authorizes neither gateway deployment nor shadow reads.
