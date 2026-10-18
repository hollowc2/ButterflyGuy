# Observer target validation and operational review — 2026-10-15

**Isolated implementation, target resources, restore and image checks pass.
Live activation remains incomplete and disabled.** This supplements all earlier
frozen reviews, including the first passing but bootstrap-only target run-04.
Nothing below authorizes live DDL/grants, broker/token operations or capture.

## Corrected exact-image verification

The harness originally allowed testing the temporary bootstrap postmaster after
the image's initialization psql failed to find its socket. Its 50 tests really
ran on PG 16.11/TimescaleDB 2.25.2, but did not prove completed image initialization.
That weakness was found and corrected during this stage, not hidden by editing
old evidence. Failed resource run-01 and compatibility runs-05/06 remain archived.

Read-only inspection of the exact image's entrypoint shows it clears PGHOST for
initialization psql. Keep the default container-only Unix socket alongside the
private host-visible socket; TCP remains disabled. Require the final postmaster
PID after bootstrap shutdown, then verify actual server/extension identity.
The fully initialized image also installs TimescaleDB into template1. The test
fixture now uses IF NOT EXISTS, followed by the unchanged exact-version assertions;
an unexpected version still fails. No evidence constraint or runtime strategy
behavior was relaxed. See the preregistered
[revision-4 correction](observer-target-v1/INITIALIZATION-CORRECTION-4.md) and its
preserved parents/source trace.

**Compatibility run-07: 50 passed, zero failures/errors/skips, 6.36 s**, on the
fully initialized pinned digest/amd64 image, PG 16.11 and TimescaleDB 2.25.2.
The source/config/parent/output hashes and copied archive verified. Final startup
completed without the bootstrap psql socket error. Restricted roles, immutable
publication, native precision, MVCC, injected commit ambiguity, failure/receipt
separation, actual crash/restart/reconnect and default-off lifecycle checks pass.
The earlier private-enabled 186-test result remains separate; these 50 are a
subset rerun, not 236 unique tests.

## Target resources and restore

The new [target package](observer-target-v1/README.md) and
`contract-v4.json`/`source-lock-v4.json` were registered before evaluation. Optional
resource-helper hooks install/check the extension in the new fixture DB and read
backend CPU/RSS in the container PID namespace. Ordinary-PG defaults remain intact;
earlier helper source/locks are preserved for reproduction.

Target resource/restore run-02 passed in a new bounded local container:

- Twelve synthetic observer acquisitions and twelve separately timed SDK-only
  baseline calls; nine publications, acknowledgements and consumer receipts;
  three recording oversize rejections with successful SDK quotes retained.
- Varied 5,000-contract body 1,800,259 bytes, full cycle maximum 0.375659 s.
  Exact 2,097,152-byte recording accepted; one byte over refused. Zero queued
  items, two sampled research connections (pool cap three), retained body at most
  2 MiB. Clean shutdown maximum 0.004995 s.
- DB growth 1,818,624 bytes and Python process peak RSS 112,556 KiB. Backend
  CPU/RSS are correctly namespaced endpoint samples, not peak profiling.
- Custom schema-only dump 1,165,646 bytes, export 1.098118 s and restore 0.228080 s.
  Hash-verified before restore into a second newly created exact-engine DB.
- Every original research table row fingerprint, body/manifest hash, installation
  UUID, transaction identity, journal sequence and acknowledgement/receipt stamp
  matched before new reads. Nine restricted-reader reads returned exact original
  bodies and signed -4.02 arithmetic, then appended nine **new** receipts.
  All nine original commit acknowledgements stayed unchanged. One deliberately
  synthetic unpublished attempt remained unpublished and unacknowledged.

This is local tmpfs/same-container restore mechanics, not independent backup or
production disk/WAL capacity. Repeated/padded/seeded synthetic bodies do not prove
real compression or retention. HTTP buffering precedes the recording byte guard;
synchronous parsing cannot be preempted by asyncio timeouts. No production budget,
freshness, economic result or safe trading-loop delay is claimed.

## Concrete default-off runtime artifact

The active trading Dockerfile omits research SQL and installs code in a path that
does not match the research ROOT assumption. A separate
[observer review Dockerfile](observer-runtime-v1/Dockerfile) copies only locks,
source and the frozen SQL, imports `/app/src`, runs as UID 1001 and defaults to
`research.ndx_observer_cli`. No active Dockerfile, configuration or Compose changed.
No credential, token, real market evidence or active runtime config is copied.

The preregistered build used an explicitly staged 164-file, 2,387,398-byte source
context. The installed legacy builder rejected --progress in attempt 1; attempt 2
was interrupted while preparing the broad repository context; both are preserved.
Successful attempt 3 used only the verified staged source. Base tags were resolved
and retained in build logs; the local intended release artifact is the immutable
image ID:

`sha256:e55ee57b97aa8a1a624677876853574831fb83f8b6ea77bf1ca8228978669a99`

Python environment metadata reports CPython 3.12.15; actual image checks report
SDK 0.8.0, asyncpg 0.31.0 and httpx 0.28.1. The schema asset hash matches frozen
postgres-v1 SQL. Two bounded network-disabled, read-only-root containers verified
the default command exits disabled and forbidden DB/socket/context/task spies
remain untouched. Both exited zero and remain stopped.

A separately preregistered **enabled synthetic image smoke** also passed. The
built image used a mock gateway and a fresh private exact-image DB under the
restricted recording role: exactly one GET, atomic publication, acknowledged
commit, exact body/negative composite and recorded consumer receipt, with replay
eligibility false. App memory cap 256 MiB/0.5 CPU/64 PIDs and DB 1 GiB/one CPU/128
PIDs stayed bounded; all network modes were none and both containers stopped.
This small synthetic image check is not a production-capacity acceptance test.

The image has not been transferred to Helios, pushed, deployed or enabled. The
original [disabled review overlay](observer-v1/compose.review.yaml) remains off,
with no credentials, context mounts or connectivity. A real capture needs a
separately reviewed replacement overlay and the specific context below.

## Dated read-only Helios review

Observations on 2026-10-16 UTC (local research date October 15): `billy@helios`,
repository `/opt/butterflyguy`, branch main, Git HEAD
`288d6cb321e611a94acc819fa96fc5e429ff836e`. Existing tracked source/config/dashboard
edits are preserved. Git HEAD is **not** attestation of the running app image.
Current NDX app image has no verified OCI source-revision label.

Observed `butterfly_timescaledb`: project monitoring, service timescaledb, healthy,
PG 16.11/TimescaleDB 2.25.2, matching pinned image and amd64 architecture, bound to
127.0.0.1:5432. Its database was about 8.36 GB; filesystem about 22.10 GB available
(79% used). This is available-space observation, not an enforced reserve/quota.
Research schema absent and all three proposed research roles absent.

Observed NDX: project infra, service app_ndx, container `butterfly_ndx_app`, running,
loopback port 8001, immutable current image ID
`sha256:1fbc1ab3aed0aec85bcccab9e5009679789baab10fc333cfd0e4636ef1e7cc61`.
SPX/NDX/XSP health and readiness endpoints returned HTTP 200. One named NDX
container and zero matching observer CLI processes were observed. A bounded
NDX-only five-minute/20-line log query returned 11 lines with zero errors/warnings;
no raw messages retained. An earlier SPX log query timed out and is not presented
as successful broader log review. Container identity/log diagnostics were narrowed
to handle absent healthcheck fields; all diagnostic failures remain recorded.

Read-only DB counts: zero OPEN trades, zero nonterminal broker intents and no
same-day intent rows at observation time. **Broker positions/orders remain
unverified.** Existing flatness code initializes a token-refreshing client; it
was not executed under the no-token-change constraint. DB counts and `/ready`
cannot replace broker evidence. No token file/environment values, accounts,
provider requests or broad historical market windows were inspected.

## Remaining activation decisions and rollback

The local mechanics gates above are complete. Activation review is **incomplete**:

1. Establish current broker positions/orders through an approved mechanism; repeat
   the current target preflight before any actual approval request. The dated
   observations here are not a continuing flatness or health guarantee.
2. Name the intended one-shot real NDXP session, exact three symbols, calendar/
   close artifact, acquisition IDs and build/config hashes. No real capture
   context or new polling schedule is selected by these synthetic checks.
3. Review the separate image's transfer/release identity and connectivity overlay;
   provision a dedicated non-owner research login/secret reference and gateway
   read-only consumer key reference. No reuse of trading pool credentials, token
   mount, second bot or order-capable entry point is proposed. Preserve remote dirt;
   never reset/checkout it to install this observer.
4. Approve additive research-only schema/grants and a storage reserve/WAL policy.
   The 512 MiB relation-size pause is sampled and can overshoot; it is not an
   enforced filesystem quota. One approved invocation adds one gateway request
   and retains at most one accepted 2 MiB body plus metadata/journal/DB overhead.
   Real daily size and long-term production capacity remain unknown.
5. Confirm evidence owner/export destination and independent-backup expectations.
   Eros retention and verified archive hashes are established; same-filesystem
   copies and this local restore do not establish independent backup. No backup
   job, retention deletion or cleanup is created.

Proposed target change is **only** a separately approved one-shot research
invocation plus additive research tables/grants, with a dedicated maximum-three
connection pool. Existing trading services/images/configuration stay unchanged.
Use the observed NDX image/container and DB image as the dated rollback baseline;
their source release is not inferred from the dirty checkout's HEAD.

Startup procedure after approval: verify transferred immutable image/source/schema
identity, install only reviewed explicit research DDL/grants, confirm the dedicated
login's restricted functions/pool and uniqueness lease, validate the predeclared
context, then run exactly one approved research invocation. Validate actual native
body/publication/read/receipt and failure/recovery inventory, export/hash evidence
and stop that observer. Any unknown commit stays unknown pending inventory; no
automatic gateway re-request or fabricated receipt/ack is permitted.

Rollback procedure for that future change: disable the new invocation/profile,
stop only its named observer process/container, release its research pool and retain
all evidence/tables/journals. Do not restart/rebuild trading apps, roll back their
dirty checkout, delete research data or change routing/limits as observer rollback.
Exact future process/transfer/secret commands need their reviewed target choices;
none are invented or executed here. No operational approval is requested now.

All 17 historical paths stay ineligible. Gateway/provider age-reference, cache/build,
physical-clock and original-provider-body evidence, actual complex-order states/
fills, official XQC, full NDX-02 and NDX-03–06 retain their separate gates. No new
P&L, exit/threshold experiment, live DDL/grant, token change or capture occurred.
