# Helios weekend preparation — October 17 UTC

**Disabled installation completed; gateway registration completed 2026-10-18** — see
[the registration record](../../../../reports/research/ndx-02-observer-gateway-20261018/run-01/README.md). Corey
approved proceeding after the named plan to install the tested observer disabled,
create dedicated permissions/credentials and verify non-market connectivity and
storage. No capture was authorized or performed. The expired October 16 context
was not installed. No polling, cron, automatic startup or restart loop was added.

## Installed and verified

- Release: `/opt/ndx-observer-review/v1` on `billy@helios`. Existing remote Git
  checkout/dirt and trading configuration were preserved.
- Image: `sha256:e55ee57b97aa8a1a624677876853574831fb83f8b6ea77bf1ca8228978669a99`.
  Docker save/gzip archive SHA-256
  `e71bc003c95e5d89bfbe47fcb96dadf92784940dbc6ad68e874562fa477613ab`
  matched on Helios before load. No active image was rebuilt.
- `ndx_provenance_v1` installed additively in one transaction with the reviewed
  NOLOGIN roles, explicit schema identity and dedicated SCRAM-authenticated
  `ndx_observer_capture` login. Lock timeout 1 s, statement timeout 5 s; the
  transaction rechecked no OPEN trades/nonterminal intents. Frozen SQL SHA-256
  `cd99bb8c27aedef901cbb9567cb09d3bd53e5fb22e7a9ba2e039176993bceb59`;
  installation UUID `d18ac329-cccf-4a57-93ba-ffc9759ed172`.
- The actual observer image connected with that login. Membership is only
  `ndx_evidence_recorder`, connection limit three. Verified no superuser,
  CREATEDB/CREATEROLE, research CREATE/UPDATE/DELETE/TRUNCATE, or trading-table
  SELECT/INSERT access. Research INSERT permission exists; no synthetic inserts
  or live-fixture testing were performed. Quotes/publications/journal remain zero.
- New DB password and gateway key were generated on Helios. Their dedicated file
  `/home/billy/.config/ndx-observer/observer.env` is billy-owned mode 0600, parent
  0700. This intentionally replaces the proposal's root-owned `/etc` location:
  passwordless sudo is unavailable, and no privileged workaround was used.
  No existing credentials were copied, rotated or overwritten; no secret values
  were printed or archived. Docker administrators can inspect container env.
- `compose.disabled.yaml` is the installed weekend command: exact image,
  default false flag, manual profile, no context mount, read-only root, no ports,
  256 MiB / 0.5 CPU / 64 PIDs / no restart. It omits the base review template's
  nonexistent session-context bind mount so disabled checks can run. Enabling
  without a separately approved fresh context fails before any acquisition.
- Actual Compose disabled execution returned `{"status":"disabled"}`.
  A second bounded container verified restricted DB access and gateway `/health`
  HTTP 200 over `monitoring_net`. No authenticated market-data route was called.
  Both named check containers exited zero and were retained; zero observers run.

## Preflight, storage and preservation

Read-only preflight recorded Helios main SHA
`288d6cb321e611a94acc819fa96fc5e429ff836e` with existing dirty files preserved.
Postflight verified identical images and start times for SPX, NDX, XSP and the
live gateway. All three trading apps' `/health` and `/ready` returned HTTP 200.

The fresh authorized helper audit passed for its declared tracked-root scope:
zero SPX/NDX/XSP option positions, zero returned orders for the original naive
October 16 day query, zero OPEN DB trades and nonterminal intents. No token-write
callback occurred. This is not an all-history/GTC-order inventory or ongoing
flatness guarantee. The preflight JSON's older generic broker-not-checked field
is superseded by the separately saved broker audit, not silently rewritten.
Its original app inspect template failed; corrected image/start-time inspection
and postflight supply those facts. An exploratory WAL query had a shell-quoting
error before corrected structured execution succeeded. Transient sandbox DNS
failures were retried through normal escalation; no alternate/public host used.

Preflight free space was 22,454,706,176 bytes, WAL 536,870,912 bytes, with no
replication slots. After retained transfer archive and image load, free space was
20,621,971,456 bytes, above the reviewed proposal's 10 GiB operator admission
floor. This is a point-in-time check, not continuous monitoring or capacity
proof. The sampled 512 MiB observer relation pause does not cap WAL/filesystem
usage. No long-term collection or deletion policy was activated.

The newly installed empty research schema and installation row were exported
without trading tables or roles/passwords. Export SHA-256
`70f1247b23df4cea10b6a4e836c5013e7af1c10cac6fbbe84f782264183567a1`.
It is retained on Helios and in the existing accepted Eros-backed archive at
`reports/research/ndx-02-observer-weekend-20261017/run-01/`, with redacted records,
execution source and manifest. This is not an independent full production DB
backup. Existing Eros retention remains accepted; independent backup is still
unestablished. No pre-existing trading data was altered or destructive rollback
performed. Repeated isolated engine/image tests were unnecessary because pinned
runtime/source did not change; package/identity, real restricted-connectivity,
disabled execution, container exit, health and whitespace checks passed.

## Remaining work and rollback

The new gateway consumer is staged as a hashed entry with `market_data:read` and
background priority. The deployed authenticator validates a merge with its three
existing consumers. **Its live registry is unchanged and the new key is not yet
accepted by the running gateway.** Deployed auth reads keys once at startup.
Registering the key and restarting `schwab_gateway_live` is a distinct live-service
change requiring named approval; see the concrete
[gateway restart review](GATEWAY-RESTART-REVIEW.md). No capture is included in that
future change.

Keep the observer disabled. If rollback is necessary, stop only a named observer
check/invocation; retain the research schema, immutable evidence and new secrets.
Do not drop tables, remove files, reset the remote checkout, restart trading apps
or rotate shared tokens. After gateway registration, market-hours work still
requires a fresh real NDXP selection/calendar/context and scoped capture approval.
All historical replay and later NDX research gates remain unchanged.
