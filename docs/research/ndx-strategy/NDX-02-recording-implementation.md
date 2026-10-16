# Stage B recording preparation — isolated SQLite implementation

Status: **local recording mechanics implemented and reviewable; Stage B activation
and TimescaleDB/upstream integration remain pending**. This is a bounded next
step after the provenance specification, not completion of NDX-02 or permission
to collect quotes. Existing collector, providers, execution, schedules, risk,
configuration, credentials and automatic database migrations are unchanged.

## Contract review and implementation choice

The v1 contract is preserved byte-for-byte. The review supports its separation
of response, publication and consumer receipt, but identifies unresolved integration
requirements. Current `SchwabClientWrapper.get_option_chain` returns `resp.json()`.
The installed pinned gateway SDK's `_get_typed` likewise returns
`model.model_validate(response.json())`. Neither public return exposes original
body bytes. Reserializing either return cannot establish original response precision.
Provider age/reference and clock synchronization are also unavailable locally.
No new capture hook can honestly fill those fields from the current return values.

The smallest independently testable local step is an opt-in, standalone SQLite
research journal. It stores copies of selected three-leg evidence, not the bot's
TimescaleDB rows. This narrows the implementation to a DB receipt protocol that
can be tested with a real local engine without applying a live migration. It is
not a substitute for TimescaleDB integration tests. No PostgreSQL executables or
running local Docker daemon were available; no daemon was started and no dependency
was installed. SQLite and the tests use Python's standard library.

`research/ndx_recording.py` has no active caller. Its `Recorder` accepts a prebuilt
v1 DB-channel record, optional exact market-body bytes and an explicitly supplied
legacy quote-write outcome. It makes no network request and imports no broker.
`tools/check_ndx_recording.py` is a separate synthetic-only runner with explicit
input/response/config/source-lock/output paths. The SQL lives under
`docs/research/ndx-strategy/recording-v1/schema.sql`, outside automatic migrations.

The implementation has deliberately unresolved v1 requirements:

- Local clocks pair UTC with monotonic nanoseconds in a unique conservative domain.
  Their synchronization/uncertainty and actual boot identity remain unattested;
  wall reversal marks discontinuity. New Recorder instances use different domains.
- SQLite does not expose a provider/database transaction identifier for this
  protocol. The v1 transaction_id remains null; a publication content hash is
  never mislabeled a server transaction ID.
- Complete recording mechanics do not satisfy freshness, upstream normalization,
  historical fidelity or replay eligibility. Exported records remain insufficient.
- The reviewed payload allowlist is a selected-market envelope with response_id,
  exact typed legs, and optional true synthetic marker. This envelope matches the
  offline fixtures, not the current Schwab/Gateway response schema. Activation must
  review the actual source body schema and preservation boundary first. Caller-
  supplied bytes are never generated from DB rows by this implementation.

## Atomic writes, failure and consumer protocol

A publication attempts three writes under one SQLite transaction: quote-copy
JSON, provenance JSON plus optional exact response BLOB, then the complete manifest.
The manifest binds snapshot/version, expected symbols, quote/provenance/body hashes
and independent quote/metadata success states. Exact decimal strings are retained;
signed negative composite marks and leg-market bids are not floored or replaced.
The caller-supplied original body is hash checked and structurally allowlisted;
unknown keys, duplicate JSON keys, changed values/precision or missing declared
bytes refuse publication. Headers and account fields are outside that envelope.
Error journals contain categorical failure codes, never exception strings or bodies.

An append-only attempt event precedes the transaction. Commit acknowledgement is
observed only after COMMIT returns, then appended in a separate write. Losing that
write leaves a committed publication with unknown acknowledgement, including after
restart. Recovery inventories actual publication/ack presence and never creates a
replacement historical time. A metadata/commit failure rolls back all new research
quote copies; a separately reported legacy quote success remains success and does
not imply metadata success. A failed failure-journal write is returned explicitly.
Attempt-journal errors propagate; callers must count any resulting recording drops
in a later reviewed integration policy. No trading fail-open/fail-closed choice is
made by this dormant library.

Publication keys are immutable snapshot/version and unique record ID. Duplicate
delivery refuses overwrite; it does not acquire new coverage. A corrected version
must reference the previous immutable provenance-document SHA-256 and retain the
same snapshot ID. UPDATE/DELETE triggers protect quotes, provenance, publications
and journal through ordinary SQL; this is not protection against an administrator
rewriting the file or schema. Close/reopen checks the schema identity hash.

The consumer retrieves manifest, quotes, provenance and body in one exact-key
joined SELECT. It verifies all content/identity hashes before read completion and
receipt stamps. Receipt persistence is another append-only journal event. If that
write fails, the returned result says receipt_journaled=false while keeping the
successful data read separate. Exports use a new directory, preserve exact body
bytes and manifest, and include that recording status plus the unchanged v1
assessment. No decision, hypothetical fill, timing threshold or P&L is produced.

## Isolated verification and resource scope

Tests use actual SQLite transactions and separate connections, not a mock DB.
They cover successful publish/read and precision; metadata failure rollback;
deferred COMMIT failure; post-commit lost acknowledgement; failed receipt/failure
journals; duplicate keys/corrected versions; restart and incompatible clock domains;
uncommitted invisibility; append-only refusal; missing bodies; unsafe fields;
changed body precision; oversized/duplicate-key JSON; schema drift; overwrite
refusal; and a child process dying after quote insert but before COMMIT. Crash
recovery preserves its attempt and exposes no partial publication.

The prototype refuses market bodies over 1 MiB before JSON parsing. This is an
explicit recording resource guard for selected three-leg evidence, not a quote
freshness/liquidity threshold or permission to alter trading. SQLite lock wait is
one second and synchronous=FULL. Calls are synchronous and unsuitable for direct
insertion into the live async loop without a separately measured integration.

The registered synthetic run uses 25 copies of one input response with distinct
snapshot/record IDs. It records publish/read wall time, process CPU time, peak RSS
and closed DB bytes; export writes are outside the timed operation. This measures
only local prototype mechanics. It cannot establish production throughput, full-
chain sizing, long-term retention, network, TimescaleDB or trading-loop impact.
Its summary is evidence, not a production budget approval. There is no automatic
retention deletion. Before activation, estimate real daily bytes from the reviewed
capture universe and schedule, set explicit disk/latency/queue budgets, validate
failure counts and choose retention/backup ownership.

The checkout is on **nfs4**. Use **local /tmp (tmpfs here)** for the active isolated
SQLite run, close it, then archive its bytes and hashes to the existing Eros-backed
reports filesystem. Do not use this prototype as a shared live SQLite-on-NFS
service. Cross-host locking/durability and independent backup are not established.
Operational capture still targets a separately reviewed integration/storage plan.

## Exact reproduction and retention

Register a named contract/source lock before the measured run. Final metadata
revision uses `recording-v1/contract-v2.json` and `source-lock-v2.json`; original
v1 files/run-01 remain unchanged. Revision 2 wraps a test line for repository lint
and records/verifies the preserved correction parent; recording behavior is unchanged.
Use a provisioned locked environment and a **new local output**:

```bash
uv run --offline --frozen python tools/check_ndx_recording.py \
  --input docs/research/ndx-strategy/recording-v1/producer.json \
  --response docs/research/ndx-strategy/recording-v1/response.json \
  --config docs/research/ndx-strategy/recording-v1/contract-v2.json \
  --source-lock docs/research/ndx-strategy/recording-v1/source-lock-v2.json \
  --output /tmp/ndx-recording-20261015/run-02
```

The closed output is retained unchanged under
`reports/research/ndx-02-recording-20261015/run-02/`. Verify every run output hash
before using an archived copy. run.json records exact execution path/invocation,
source copies, input/config/parent/output hashes, Git SHA/dirty state, UTC,
Python/platform and dependencies. Contract corrections require a new identity;
failed runs are preserved. Versioned small run/summary/verification records use
`evidence/2026-10-15/ndx02-recording-*`. The living plan owns current status.

Focused command: `uv run --offline --frozen pytest tests/test_ndx_recording.py -q`.
Run the existing 113-test private-enabled suite alongside it as specified in the
provenance reproduction guide, adding this test file. Run repository Ruff,
`git diff --check` and graphify AST update after code changes. No economic trial
or broker-connected testing is part of these checks.

## Activation, validation and rollback checklist — pending scope

This is a concrete preparation checklist, not a deployment approval request.
No target service/release or live migration is yet approved. The VPS and Helios
skills were read for preparation; no server access or live preflight was performed.

1. Resolve upstream ownership: obtain reviewed original response access, raw schema,
   build identity, age/reference implementation and clock evidence. Alternatively
   explicitly preserve their absence; do not loosen v1 sufficiency to manufacture it.
2. Choose and implement the actual deployment storage/consumer path. A TimescaleDB
   implementation needs separate additive research tables, atomic publication,
   exact-key consistent read and real isolated PostgreSQL tests. This prototype
   demonstrates SQLite only. Avoid changing existing quote/meta writes and strategy
   behavior; any integration diff must identify bounded async worker/drop policy.
3. Measure real-size bodies, latency, disk/CPU, queue/backpressure and retention;
   test restart/retry/commit ambiguity and quote-success/provenance-failure in that
   target integration. Verify allowlist/redaction against actual market responses.
4. Prepare a named-target activation diff with capture disabled by default, release
   identity, explicit schedules/universe, observer uniqueness, retention ownership
   and no new orders. Read-only Helios preflight must establish current SHA/image,
   service state, disk, positions/orders and rollback baseline before an operational
   approval request. No service restart, live migration or capture starts here.
5. After separately authorized activation, validate output identities, completeness,
   failure/drop accounting, raw precision, commit-vs-receipt ordering and resource
   budgets against a bounded observation window. Fixtures do not count as coverage.
6. Roll back the observer by disabling its opt-in integration and restoring the
   verified prior image/release if needed; preserve all research tables, bodies,
   attempts and failures. Do not delete evidence or touch trading limits, routes,
   credentials or paper/live mode. Exact commands belong to the named-target
   preflight/approval package, not an invented service name in this checklist.

Next bounded action: implement/review actual upstream preservation and target
DB/consumer integration using this tested protocol, then perform isolated target-
engine/resource validation. Activation remains gated; Stage C needs real observed
provenance, actual execution/XQC gaps remain, and all 17 historical continuation
paths stay ineligible. Later research stages retain their separate instructions.
