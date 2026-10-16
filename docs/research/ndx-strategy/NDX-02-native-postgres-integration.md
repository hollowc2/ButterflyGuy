# Native gateway response and PostgreSQL research integration — 2026-10-15

Status: **opt-in research integration implemented; capture remains disabled**.
This advances the prior SQLite preparation to the actual asyncpg/PostgreSQL
publication protocol and the pinned gateway SDK's native HTTP response schema.
It does not change the active collector, providers, trading database tables,
configuration, dependency pins, schedules, execution or risk behavior. Full NDX-02
and operational Stage B activation remain incomplete.

## Concrete integration boundary

`src/butterfly_guy/research/ndx_native_response.py` preserves the exact buffered
HTTP response body from a successful GET `/v1/option-chain`, after validating the
pinned SDK's extra-field-forbidding native schema. It does not fetch or consume a
stream. Bodies from other endpoints, non-200 responses, duplicate JSON keys,
extra fields such as account/authorization fields, mismatched selected identity,
unbuffered responses and bodies above the explicit 16 MiB recording guard refuse
preservation. No headers, URLs/query secrets, account endpoints, credentials or
error bodies are stored. A native contract body can contain both calls and puts;
its selected derivative is the predeclared exact three NDXP symbols and session.

Scope is **gateway-http-decoded-option-chain-v1**: the buffered, possibly HTTP-
decoded gateway-normalized response body. It is not original provider wire bytes,
not a reconstructed selected-leg envelope, and not a raw pre-normalization
provider market. Exact JSON number tokens survive in the preserved body. Selected
bid/ask/mark/strike/age derivatives use decimal fixed-point strings, preserve
signed composites, missing multiplier and sizes, and retain per-leg flags separately
from chain flags. Original timestamp/age fields are copied, never synthesized by
age subtraction. Exponents in the derivative are formatted in fixed-point form;
original exponent/trailing-zero precision remains in the body bytes.

The observer records when it **saw the already-buffered response**, not an invented
network-arrival instant. Request start is separately nullable, or observed immediately
before GET by the research HTTP client. The local UTC/monotonic clock domain is
unique and unattested; synchronization/actual boot evidence remains unknown.
Observer source SHA-256, installed HTTP/SDK versions and non-secret effective
recording settings accompany each native capture. Gateway build and actual
age-reference/evaluation instant remain null: the current SDK does not deliver
them. Provider-original-body, synchronization and gateway normalization/deployment
attribution remain separate gaps. The pinned-source cache findings still apply.

`src/butterfly_guy/research/ndx_postgres_recording.py` provides
`ResearchGatewayHTTPClient`, an optional `httpx.AsyncClient` subclass supplied via
the existing SDK constructor's **client=** argument. This requires no SDK or other-
repository change. After the normal GET buffers its response, the explicit research
observer preserves it and awaits publication. The SDK then validates the same
original response normally. It makes no second request, retry, order or provider
call. With recorder=None, recording is disabled. No bot wiring or factory currently
instantiates this client. It is intentionally a separate research path: awaiting
publication on an active trading path would alter delivery latency and is not
approved here. No new queue/worker or change to trading failure policy is introduced.

The research client returns the original response if recording fails, exposes a
recording_failures counter and categorical last_recording_result, and attempts a
safe observer-failure journal event when acquisition identity is known. Quote
success is distinct from recording failure. Cancellation propagates. If the DB or
identity is unavailable, that recording failure cannot magically become durable;
caller-side drop accounting and restart reconciliation remain activation gates.
No exception strings or HTTP error context are persisted in failure records.

## PostgreSQL/TimescaleDB adapter and append-only storage

The SQL is `docs/research/ndx-strategy/postgres-v1/schema.sql`, outside automatic
runtime migrations. `install_empty_schema(connection)` is explicit and refuses an
existing namespace. It creates only `ndx_provenance_v1` research tables; importing
or constructing the adapter executes no DDL or creates a pool. A separately supplied
pool must have bounded command timeouts. The isolated run uses command_timeout=5 s,
max_size=5 and a 1 s transaction-local lock timeout. These are recording/test
resource guards, not market-age, liquidity, fill or trading thresholds.

Schema identity includes a version, SQL hash and installation UUID. Publications
bind that installation, exact snapshot/version/record IDs, selected symbols,
original gateway-body hash, metadata/quote hashes and the real PostgreSQL
pg_current_xact_id() transaction identifier. The transaction identifier is scoped
to this database installation; it is not a commit timestamp or receipt proof.
Publisher source and SQL identity accompany the producer metadata.

Quote copies, provenance/BYTEA body and complete manifest are inserted in one
transaction using a recorder-owned pool connection; no caller outer transaction
is accepted. Commit acknowledgement is stamped only after the transaction context
returns successfully, then journaled separately. A COMMIT reply lost on the wire
returns published=null, not false. A later recovery query resolves actual manifest
presence without inventing a past acknowledgement. Definitive server constraint
failure is a rollback. If COMMIT succeeded but acknowledgement journaling fails,
publication success remains true while that timestamp evidence remains unavailable.
A durable attempt precedes writing; cancellation/connection loss can leave it
unresolved for later inventory. A separately reported legacy quote-write outcome
is not changed by a failed research publication.

The consumer reads the exact manifest, selected quotes, metadata, raw body and
acknowledgement under one SQL statement's MVCC snapshot. It verifies bytes/hashes,
snapshot/version, installation, transaction and exact symbol membership before
recording read completion and actual consumer receipt. Receipt journaling is a
later operation. Failure there says receipt_journaled=false while retaining the
successful data read separately. Earliest possible availability stays unknown.
No decision/fill is created; native assessments remain **insufficient** and
replay_eligible=false because upstream timing/build/provider evidence is missing.

Duplicate keys refuse overwrite. A correction needs the previous immutable
provenance-document hash. UPDATE, DELETE and TRUNCATE triggers protect evidence
through ordinary SQL; administrators can still alter/drop schemas. Permissions,
retention and storage administration require the target integration review. No
cleanup/deletion or live migration is executed by this task.

These are ordinary PostgreSQL tables usable alongside TimescaleDB, with no
hypertable, compression, scheduler or extension API. Real engine checks use
**PostgreSQL 16.2**. A deployed TimescaleDB extension/container has not been tested;
this does not claim parity with the Helios engine, pool, permissions or load.

## Real engine tests and synthetic resource run

`tests/test_ndx_native_response.py` checks native schema/extra fields, exact number
precision, null versus zero/chain flags, size/stream refusal, tampering, default-off
client behavior, one-request SDK injection and recording failure separated from
normal SDK validation. `tests/test_ndx_postgres_recording.py` creates a new local
cluster and fresh databases, exercising actual transactions, deferred COMMIT
failure, rollback, uncommitted invisibility across connections, backend termination,
append-only/TRUNCATE guards, correction parents, schema drift, acknowledgement and
receipt failure, recreated readers, and native SDK-to-DB byte roundtrip. COMMIT-reply
loss is injected after a real server commit; its transport loss is synthetic,
while publication presence and recovery are checked on the actual engine.

A temporary pgserver==0.1.4 package supplies the PostgreSQL 16.2 test executables.
It was acquired with uv in a separate Python 3.12 environment because the package
has no compatible wheel for the project's Python 3.13. No project dependencies,
pyproject.toml or uv.lock were changed. Test acquisition initially found no offline
cache, then rejected Python 3.13 before succeeding in the separate environment.
No Docker daemon, system service, remote host or live DB was started/changed.
Each new test cluster uses a private /tmp directory, trust authentication only on
its private Unix socket, listen_addresses empty, no TCP listener, and explicit
shutdown of that test process only. Cluster/log files are retained for review.

Register `postgres-v1/contract.json` and `source-lock.json` before the measured run.
The runner accepts no DSN, broker URL or real market input; it creates a new local
cluster itself. It uses synthetic native bodies and httpx.MockTransport with the
real pinned SDK, PostgreSQL driver and server. It runs five small 4-contract bodies
and three 5,000-contract bodies at the SDK's declared maximum. The scale recipe
clones synthetic calls and recomputes counts; it is not a reconstruction or new
market coverage. All three selected legs are kept unchanged numerically. The
native input file retains its original lexical tokens; the generated full-size
body has its own newly generated, explicitly synthetic bytes/hash.

Measured wall/CPU time covers native SDK request/validation, recording and actual
DB receipt, excluding filesystem export writes. DB-size growth and process peak
RSS are reported. Repeated synthetic bodies compress differently from real chains;
these checks do not approve production throughput, clock bounds, latency, resource
budgets, retention or trading-loop impact. No thresholds are chosen from P&L.
A custom-format pg_dump plus exact body/receipt/manifest samples, source copies,
source/input/config/parent/output hashes and environment identity are retained.

Exact execution (use a **new output** to repeat):

```bash
uv run --offline --frozen python tools/check_ndx_postgres_recording.py \
  --input docs/research/ndx-strategy/postgres-v1/native-synthetic.json \
  --universe docs/research/ndx-strategy/postgres-v1/universe.json \
  --postgres-bin /home/corey/.cache/uv/archive-v0/ZWZ0Mqbj4Iv7hOst/pgserver/pginstall/bin \
  --config docs/research/ndx-strategy/postgres-v1/contract.json \
  --source-lock docs/research/ndx-strategy/postgres-v1/source-lock.json \
  --output /tmp/ndx-native-postgres-20261015/run-01
```

The binary path is this environment's cache location; elsewhere obtain the same
package in an isolated Python 3.12 uv environment and pass its pginstall/bin path.
The run records hashes of postgres/initdb/pg_ctl/pg_dump and the actual server version.
After stopping the cluster, archive the output unchanged to
`reports/research/ndx-02-native-postgres-20261015/run-01/` and verify all hashes.
NFS remains an archive, not a live local-test cluster. Independent backup remains
unestablished. Failed/corrected runs need new identities, never edited source locks.

For checks, set NDX_POSTGRES_BIN to the same binary directory and run both new
test files alongside the prior 136-test private-enabled suite. Without that variable,
the isolated PG tests explicitly skip; this is not real-engine validation. Exact
commands/results and resource summary are saved in the versioned
`evidence/2026-10-15/ndx02-native-postgres-*` records. Repository lint, diff checks
and graphify AST refresh remain required after code changes.

## Remaining integration/activation gates

The code now provides the previously missing client= injection and actual asyncpg
adapter. The original provider body, gateway cache/reference instant/build evidence
and clock attestation still require upstream changes or external evidence; no
other repository was modified. A real research capture plan may preserve those
unknowns, but cannot claim freshness or eligible replay from this package.

Before capture activation: validate the schema/roles/pool on an isolated copy of
the deployed TimescaleDB version, choose bounded observation scope and actual
non-secret settings, validate runtime drop/restart/retention behavior and real-size
resource budgets, and prepare a default-off observer integration plus named-target
preflight/release/validation/rollback record under the VPS/Helios deployment skills.
Schema installation, capture activation and service changes each still require
separately scoped authorization. The approval target must be concrete and reviewable;
this document does not invent current live service/release identity.

All 17 historical paths remain ineligible. NDX-03 through NDX-06, economic
experiments, actual execution/XQC attribution and strategy promotion retain their
gates. No new P&L, broker operation, credential change or live-service action occurs.
