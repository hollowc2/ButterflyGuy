# TimescaleDB and default-off NDX observer — implementation review

Decision: **incomplete; capture remains disabled**. The observer implementation
and isolated PostgreSQL checks are independent preparation. Exact-image execution
requires an available supported local container runtime. Docker's client exists;
the normal sandbox cannot access its socket, and the escalated read-only check
reports no running daemon/socket. No daemon was started. This is an unavailable
runtime prerequisite, not a successful pull, image resolution or TimescaleDB test.

## Concrete consumer and identities

`research/ndx_observer.py:create_observer()` returns `None` unless explicitly
enabled. `python -m butterfly_guy.research.ndx_observer_cli` also returns disabled
unless `NDX_OBSERVER_ENABLED=true`. Disabled execution does not inspect a context
file, gateway key or DSN; create a client/pool/task; parse/copy a body; query or
request anything. Existing `run_live.py:_build_collector_market_data` constructs
its own SDK client. It is unchanged and never imports this observer.

The enabled entry point is a separate read-only research consumer of one caller-
requested `$NDX` option chain. It injects an httpx client into the existing pinned
SDK using `client=` and uses the existing native preservation and PostgreSQL
adapter. It makes one SDK call without retries. There is no schedule, background
worker, queue, order client or trade decision. Awaited preservation/publication
occurs only in this separate research lifecycle.

Before acquisition the caller supplies `Acquisition`: preselected exact three
NDXP OCC symbols/session, independently sourced calendar name and UTC close,
opaque snapshot/record/request/pass/acquisition IDs, version/correction parent,
consumer and build/config artifact SHA-256 values. They are validated and bound
to the native publication and/or acquisition ledger. Build/config hashes name
caller-supplied artifacts; they are not gateway deployment attestations. The
native document additionally measures its actual local source/dependency hashes.
For prospective use, generate IDs before requesting, obtain instrument identity
from the predeclared research universe and calendar from the selected exchange
calendar artifact. Archive those artifacts and verify the supplied hashes before
activation. Synthetic tests stipulate these identities and calendar; they do not
prove any real session traded. The full entry-opportunity/skip set is still NDX-03.

The CLI reads the explicit non-secret context at `NDX_OBSERVER_CONTEXT_FILE` only
after enablement. Proposed secret references are `NDX_OBSERVER_DATABASE_DSN` (a
dedicated research login) and `NDX_OBSERVER_GATEWAY_KEY` (read-only market access).
`NDX_OBSERVER_GATEWAY_URL` is the separately reviewed endpoint. No secret value,
environment dump or HTTP exception text is printed or journaled. No environment
variable is installed by this package. The CLI emits categorical status only.

## Lifecycle, bounds and permissions

One database-session advisory lock, key 78020301, identifies the single observer
within a research database. The lease uses one connection in a dedicated asyncpg
pool with min=1/max=3, connection/command timeout 2 s, statement timeout 2 s and
lock timeout 1 s. No order/position/risk pool is borrowed, resized or held. A dead
lease stops requests. Recovery closes that instance and starts a new one; it
does not silently retry a request or reclaim an uncertain publication. Record
the deployment's research database identity: separate DBs have separate locks.

Startup is bounded at 5 s; one acquisition at 10 s; journal attempts at 1 s;
shutdown at 3 s. Shutdown cancels the owned pending acquisition, closes the HTTP
client, releases the lease and closes its pool. Timeout/failure terminates only
that pool and increments `shutdown_incomplete`. A later process reconciles durable
attempts/publications/acks. No invented acknowledgement or timestamp is appended.
CPU-bound JSON/SDK validation is synchronous: asyncio timeouts cannot interrupt
it. Measured parse cost and the proposed process CPU/RSS cap need target validation.

Admission permits one request, rejects concurrent calls immediately, and retains
at most one recording body up to 2 MiB. Queued items and queue retained bytes are
always zero. Oversized recording is refused before native preservation/parse;
the original SDK still validates the response. HTTP buffering already happened,
and the SDK can still parse a larger body: this guard is **not** a hard process-
memory/HTTP allocation bound. Derived objects and consumer return values add
memory; callers own retention of returned quotes/receipts. No executor/task backlog
or automatic replay queue exists.

The observer pauses new requests at 512 MiB total research-table size, sampled
before each request. This is a conservative local storage resource proposal,
independent of prices or returns. One publication/journal can overshoot that
sampled threshold; relation size is not a filesystem quota or WAL cap. Production
disk/WAL capacity, filesystem reserve and an independently enforced quota remain
unvalidated and block activation. Proposed process caps in the disabled overlay
are 256 MiB RSS, 0.5 CPU and 64 PIDs; they are containment proposals, not measured
production acceptance budgets.

`observer-v1/roles.sql` is an explicit additive proposal outside automatic
migrations. A NOLOGIN owner owns the research schema/tables/function; NOLOGIN
recorder/reader groups own nothing. Recorder gets research SELECT/INSERT;
reader gets research SELECT and journal INSERT; both get schema USAGE and journal
identity-sequence USAGE. Runtime requires standard pg_catalog execution of
`pg_current_xact_id()`, relation-size and advisory-lock functions, checked under
restricted roles. No broad trading-table access, DDL, schema ownership, trigger
disabling or UPDATE/DELETE/TRUNCATE privilege is needed. CONNECT, LOGIN membership,
TLS, secret provisioning and any nonstandard target pg_catalog restrictions
need separate named-target review. Existing database-wide PUBLIC privileges are
not changed by this proposal, and runtime does not depend on public-schema CREATE.

## Ledger units, drops and recovery

The durable append-only adapter journal retains publication attempts, failures,
commit acknowledgements and consumer receipts by exact snapshot/version. The
observer adds instance start/stop, acquisition start, categorical rejection/failure
and interruption observations. Request/pass/acquisition/consumer/build/config/
calendar identity accompany contextual lifecycle events. A failed acquisition-
start journal prevents this research consumer from requesting data; it changes
no bot failure policy. Missing acquisition identity gets an unattributed instance
event and no gateway request. Journal failure is counted locally and stays unknown
after crash unless independently observed.

Counters distinguish admitted requests, received HTTP responses, accepted/rejected
recording bodies, publication calls, published/failed/unresolved results, observed
acknowledgements, successful consumer reads, receipt records and lifecycle events
journaled/unjournaled. A duplicate causes another delivery attempt, not another
immutable publication or new coverage. Read success survives receipt-journal
failure; market response success survives storage rejection/failure. A research
operation timeout returns interrupted while retaining the received-response count;
it makes no statement about a still-unresolved commit.

Busy admissions are memory-only known rejections with no spawned journaling task.
Counts, including body rejections whose failure journal was unavailable, cannot
prove durable completeness after a process crash. Start/stop events explicitly
leave unobserved intervals unknown. There is no claim of zero drops or complete
market coverage, no durable retry queue, and nothing silently recovered from a
lost response. Recover only by enumerating durable attempts and exact immutable
publication/ack presence with `PostgresRecorder.recovery_inventory()`. For large
archives use bounded sequence/key ranges in journal queries; the existing full
inventory helper is an offline audit, not an automatic startup scan. Never recreate
the old ack/read time or count a later query as historical receipt. An interrupted
attempt with no publication is not evidence that the market had no quote.

## Registered verification and reproduction

`observer-v1/contract.json` preregisters mechanisms, resources, synthetic cases,
parent runs, input hashes and the exact target. Its new source lock preserves all
older locks. `tests/test_ndx_postgres_recording.py` changed only to support the
strict `/tmp/ndx-timescale-<UUID>/socket` fixture and verify PG 16.11/extension 2.25.2
in every newly created target DB. This is disclosed drift from postgres-v1's test
pin; its archived original source under native-postgres run-01 remains available
to reproduce the old runner in a separate copied source tree. No old lock was edited.

Exact target (use a new output every time):

```bash
uv run --offline --frozen python tools/check_ndx_timescale.py \
  --config docs/research/ndx-strategy/observer-v1/contract.json \
  --source-lock docs/research/ndx-strategy/observer-v1/source-lock.json \
  --output /tmp/ndx-timescale-observer-target/run-02
```

The harness accepts no image/DSN/broker override. It resolves/pulls the recorded
digest for linux/amd64; preserves image ID/RepoDigests/architecture; creates a
UUID-named, labeled container with network=none, no TCP/public port, private socket,
512 MiB disposable data tmpfs, 1 GiB memory, one CPU and 128 PIDs; verifies actual
PG/extension versions; runs adapter/native/observer/role tests; and stops only that
container, preserving logs and stopped container identity. It never starts a
daemon, mounts production storage, prunes or deletes evidence. Exact identity
discrepancies fail closed, never substitute a mutable tag. A current target-source
refresh is needed only if actual resolution exposes a material identity problem.

Independent observer resource run (explicitly ordinary PG 16.2, not target proof):

```bash
uv run --offline --frozen python tools/check_ndx_observer_resources.py \
  --config docs/research/ndx-strategy/observer-v1/contract.json \
  --source-lock docs/research/ndx-strategy/observer-v1/source-lock.json \
  --postgres-bin /home/corey/.cache/uv/archive-v0/ZWZ0Mqbj4Iv7hOst/pgserver/pginstall/bin \
  --output /tmp/ndx-observer-resources/run-02
```

Runs use only mock transport and synthetic four-contract, varied 5,000-contract,
exact byte-budget and one-byte-over bodies. Seeded random flags/prices vary the
unselected synthetic contracts; original selected lexical tokens are preserved in
the small input, and generated bodies have separate hashes. SDK-only and full
observer/publication/read CPU/wall time are measured separately, with body/zlib
bytes, Python peak RSS, DB backend CPU/RSS samples, sampled connections, storage
growth, counters, operation lag upper bounds and shutdown elapsed time. Compression
and local /tmp storage do not establish real retention or durable/network capacity.
Pressure/outage/cancellation/crash/restart tests are registered separately from
sequential resource measurements. Peak DB memory and production throughput remain
unmeasured. No P&L, fill or liquidity threshold is calculated.

## Proposed capture, retention and restore — not activated

Initial operational review proposal: one owner-selected research session, one
predeclared NDXP three-symbol identity and one `$NDX` native full-chain acquisition
through this caller-driven executable. Traffic is **one additional gateway request
per separately approved invocation**, maximum one request per process, no polling.
Repeated/time-based capture would require a separately reviewed caller/schedule
and gateway capacity budget. A one-shot observation does not cover a session or
the full NDX-03 opportunity set.

The default retained-body ceiling is 2 MiB per approved invocation, plus metadata,
quotes, journal, indexes and WAL. Expected daily body bytes are N times the measured
body mean for N approved invocations; for this one-shot proposal N=1, at most 2 MiB
accepted body/day. Actual mean and DB/WAL overhead are unmeasured prospectively;
do not extrapolate synthetic compression. Proposed storage pause 512 MiB is a
resource stop, not a retention deletion rule. Corey's operational review must name
the storage owner, filesystem reserve/quota and export destination before activation.

Proposed owner: Corey for research evidence and operational approval; reviewer to
confirm. Closed evidence stays in new run directories on the existing Eros archive
under `reports/research/ndx-02-observer-20261015/`, with versioned small verification
records in Git. Eros is accepted retention; independent backup remains unestablished.
No backup job or delete/prune policy is created. Do not put active test DB data on NFS.

Restore drill proposal: freeze one export, take custom-format pg_dump of only the
research schema plus role definitions without credentials, record image/server/
extension/installation IDs and SHA-256 manifest, archive and verify every member;
restore to a newly owned private exact-image DB; install reviewed NOLOGIN role
ownership/grants; verify installation identity, body/manifest/quote hashes, exact
snapshot membership and journal sequences; reconcile attempts/publications/acks/
receipts. A restored query creates a new receipt, never an old ack. This restore
drill and independent destination must be verified before a durability claim.

## Activation and rollback review — pending facts

Affected proposed components: new separate research executable/pool and additive
research-only tables/grants on a separately approved DB. Trading services, runtime
configuration, limits, sizing, account guards, tokens, routing and paper/live mode
are unchanged. The [disabled overlay](observer-v1/compose.review.yaml) is outside
active Compose discovery, requires an explicit profile/image and has no network,
secrets or context mount. It is not a runnable enabled deployment proposal.

Do not request activation approval from this package yet. Missing facts are the
exact-image test result, measured target resources/restore, enforced storage reserve,
current named-target release/image/health/disk, recording login/DB/TLS identity,
gateway capacity/secret references, uniqueness, relevant positions/orders and
rollback baseline. No operational preflight was attempted because local target
validation is incomplete. The old Helios version observation is not current
health or approval. No verified release/service identity or rollback command is
invented here.

After those gates: complete read-only VPS/Helios preflight, freeze a reviewed
release/image and one-shot context, then seek separately named approval for DDL/
grants and the single capture invocation. Validate schema/role/version/lease before
traffic, confirm exactly one request and native body/publication/actual receipt,
inventory failures/unknowns, export/hash evidence and stop that observer. Rollback
is disable this separate invocation/profile, stop only its approved process and
restore the reviewed release baseline if needed; retain all research tables,
roles, bodies and journals for review. Never delete evidence or change trading
settings as rollback.

## Upstream ownership and unchanged research gates

ButterflyGuy owns native buffered-body preservation, identities, local clocks,
publication/receipt and drop observations. The SDK owns strict native validation
and supported client injection. Gateway service must expose the actual age-
evaluation/reference instant, cache-hit/coalescing identity, response identity,
deployed build/config and process/clock domain at evaluation. Request an upstream
contract with per-contract versus chain metadata, original event-selection fields,
unclamped age diagnostics and measured clock uncertainty artifacts. The provider
must attest original-body scope, quote/trade-event semantics and normalization.
No other repository is changed; these are unsent requirements, not new evidence.

Gateway-normalized HTTP-decoded bytes remain distinct from provider-original wire
bytes. Zero age can reflect future-event clamping; cached ages are not referenced
to the old gateway receipt. Never subtract ages to reconstruct clocks or relabel
selected provider events as pure quote updates. All 17 historical paths stay
ineligible for R0/minute replay. Actual complex execution/order states/fills and
official XQC remain missing; full NDX-02 and NDX-03–06 remain open. Next bounded
action: provide an available isolated container runtime, run the exact-image
harness in a new directory, resolve any image identity discrepancy, then complete
target resource/restore and named-target operational review. No activation occurs.
