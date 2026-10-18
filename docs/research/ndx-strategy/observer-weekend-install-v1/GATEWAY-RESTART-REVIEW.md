# Remaining separate gateway change

Target: `billy@helios`, existing container `schwab_gateway_live`.
Current immutable image:
`sha256:2a2236931f85c79c27171d966c5486852f9aa9a5287806565bffd674576df35e`.
Started October 11 at 21:09:30 UTC. No image change is proposed.
The existing registry has three consumers and SHA-256
`074e1a25088dec50bbbdf429c2c791f10f733e9fb5ea82826bc8643d7867a481`.
It is mounted read-only from
`/opt/schwab-gateway/secrets/schwab-gateway-keys.json` to
`/run/secrets/schwab-gateway-keys.json`.

The prepared fourth entry is `ndx-timescale-observer-v1`, capability
`market_data:read`, priority `background`. The deployed authenticator validates
this merged document. Its source documents read-once loading; runner source has
two startup `from_file` paths. The current consumer registry was not changed.
The new raw key stays only in the dedicated mode-0600 observer env file; its
hashed principal is staged separately under the same mode-0700 directory.

Requested future change: after named approval and a fresh preflight, back up the
current registry securely without exposing it, refuse a changed baseline, append
only the validated new hashed entry, preserve ownership/mode and restart only
`schwab_gateway_live`. The restart must ensure the single-file bind mount sees
the intended inode/document; verify host and container hashes afterward. Existing
consumer entries must remain identical. Do not rebuild, restart trading apps or
alter broker token files, network exposure or other secrets.

This briefly interrupts the gateway used by existing market-data consumers.
Validate gateway health/readiness and existing consumer health, the loaded new
principal through a non-upstream validation path, unchanged trading-app image and
start identities, no duplicates, and positions/intents/order activity. No capture
or option-chain/spot/history provider request is authorized by weekend prep.
If validation fails, securely restore the exact original registry, restart only
the gateway to reload it, recheck health/consumers, and retain all evidence. No
registry deletion, pruning, schema drop or credential rotation is a rollback step.

This document is review only. Gateway registry replacement and restart were not
included in the prior named disabled-observer installation and were not run.
