# Next-stage prompt: exact TimescaleDB validation and default-off NDX observer

This is a saved implementation instruction, not evidence of completed work or an
operational approval. The current decision in `docs/research/ndx-strategy-development.md`
takes precedence over historical prompts if newer decisions change the scope.
Preserve the previous prompts and all frozen evidence.

Copy the instruction below into the next implementation session.

---

Continue the NDX research implementation from the completed native gateway-body
preservation and PostgreSQL adapter. **First validate the existing adapter on an
isolated instance of the exact observed TimescaleDB image. Then prepare the
smallest default-off research observer integration with tested lifecycle,
permissions, bounded resources, drop/recovery accounting and a concrete activation
review package.** Finish code, executable checks, immutable run evidence and the
living handoff. Do not stop at a plan or build another substitute storage prototype.

Proceed autonomously with reversible local implementation, synthetic fixtures and
isolated test infrastructure. A new, task-owned local test database/container is
allowed; using the live database as a test fixture is not. Complete all independent
work before requesting any necessary operational approval. **This instruction does
not activate capture, install live DDL, change a running service, place orders or
authorize strategy experiments.**

## 1. Establish the starting state

Read, in this order:

1. `AGENTS.md` and `README.md`.
2. `docs/research/ndx-strategy-development.md`, especially the current decision and
   the native/PostgreSQL section plus post-registration target supplement.
3. `docs/research/ndx-strategy/NDX-02-native-postgres-integration.md`.
4. `docs/research/ndx-strategy/NDX-02-prospective-provenance.md`,
   `NDX-02-provenance-reproduction.md`, `NDX-02-causal-minute-specification.md`,
   `NDX-02-recording-implementation.md` and `NDX-02-recording-upstream-review.md`.
5. `docs/research/ndx-strategy/NDX-remaining-roadmap.md` and the NDX evidence README.
6. The versioned `ndx02-native-postgres-{run,summary,verification,target-readonly}.json`
   records under `docs/research/ndx-strategy/evidence/2026-10-15/`, the PostgreSQL
   contract/source lock, and the upstream source trace referenced below.
7. The `trading-strategy-research` skill, including execution-validation guidance,
   and `market-data-operations`. Read `vps-server-management` before any necessary
   read-only remote inspection, and `helios-live-deploy` before preparing a live
   activation package. Apply their actual scope/approval rules without asking
   again for already authorized reversible local work.

Inspect Git status, branch, upstream and SHA before editing. The preceding work
was committed and pushed as:

- `49da0284d24814ed2bc0838bbd543444b48019b9`: baseline/accounting/continuation audits.
- `47e7d331255f412c0fa90a8c8708dd5dea7c524c`: fidelity, provenance, recording and
  native/PostgreSQL packages, on `fix/xsp-floor-wing-alert-spam`.

A later checkout SHA does not invalidate matching source hashes or prove a
historical deployment identity. Preserve existing changes; never reset/clean
work to make a source lock pass. Read graphify's report before architecture work,
prefer its wiki if present, and refresh its AST graph after code changes.

The main implementation to extend is:

- `src/butterfly_guy/research/ndx_native_response.py`.
- `src/butterfly_guy/research/ndx_postgres_recording.py`.
- `tools/check_ndx_postgres_recording.py`.
- `tests/test_ndx_native_response.py` and `tests/test_ndx_postgres_recording.py`.
- `docs/research/ndx-strategy/postgres-v1/`, including explicit SQL outside runtime
  migrations, synthetic native input/universe, body schema, contract/source lock.

Inspect the actual SDK construction/configuration paths before choosing the
observer entry point. Prefer existing patterns and surgical additions. Do not
refactor strategy, execution, risk, token or unrelated collector behavior.

## 2. Preserve the established result and its limitations

Completed work includes the historical baseline, accounting attribution,
continuation/cadence audit, constituent fidelity, prospective provenance
specification, offline checker, SQLite mechanics preparation and native gateway
SDK-to-PostgreSQL recording. The latest combined suite passed **164 tests with
zero skips**, including the private snapshots and real PostgreSQL checks. Lint,
source/output hashes and whitespace checks passed. Graph refresh completed with
optional SQL-parser and stale-community-label limitations.

The existing native client:

- Uses the pinned SDK's supported `client=` injection without modifying another
  repository or adding a second request/retry.
- Preserves exact already-buffered **gateway-normalized, HTTP-decoded option-chain
  body bytes**. It does not capture original provider wire bytes.
- Copies selected decimal fields without mark/midpoint substitution, flooring,
  multiplier defaults or leg labels inferred from chain flags.
- Records the observer's view of the buffered response separately from request
  start, gateway/event timestamps and actual consumer receipt.
- Publishes quote copies, metadata/body and complete manifest atomically through
  asyncpg; observes commit acknowledgement afterward and journals it separately.
- Treats lost COMMIT reply as unknown outcome until recovery queries publication
  presence. A later query cannot recreate an unrecorded historical acknowledgement.
- Keeps read success separate from receipt-journal failure, refuses duplicate
  overwrite and requires correction-parent hashes.
- Is dormant. No active bot factory currently wires it in. Awaiting publication
  adds latency on its research path and is not approved inside trading delivery.

The recorded resource run used five synthetic 4-contract bodies and three
synthetic 5,000-contract bodies. The latter were 1,295,450 bytes; the largest complete
mock-SDK/real-DB cycle was about 0.318 s. That is a small synthetic mechanics result,
not a production budget, representative compression ratio or safe trading delay.
The existing 16 MiB recording guard applies after the response has already been
buffered; it does not cap the HTTP client's original buffering allocation.

Retain all distinctions and unknowns. In particular:

- All **17 historical paths remain ineligible** for R0 continuation and minute replay.
- Actual age-reference/evaluation instant, gateway build attestation, physical
  clock synchronization/uncertainty and original provider body remain missing.
- Pinned gateway source recomputes ages at cache evaluation while retaining the
  original gateway receipt timestamp. Do not subtract age from receipt/completion
  to reconstruct a clock. Zero age may reflect clamping of a future event.
- Provider event selection can combine quote/trade timestamp fields; do not
  silently rename it a pure exchange quote update.
- Actual complex-order fills/order states and official XQC remain separate gaps.
- No new P&L, liquidity threshold, exit trial, economic replay or promotion follows
  from successful recording mechanics.

## 3. Verify the parent packages and retain reproducibility

Start with:

- `docs/research/ndx-strategy/postgres-v1/contract.json` and `source-lock.json`.
- `reports/research/ndx-02-native-postgres-20261015/run-01/`.
- `reports/research/ndx-02-recording-20261015/run-02/`.
- `reports/research/ndx-02-provenance-20261015/run-01/`.
- The earlier fidelity/accounting/continuation/baseline parents these reference.
- `docs/research/ndx-strategy/evidence/2026-10-15/ndx02-recording-upstream-source-trace.json`.

Use existing digest/manifest/parent verification helpers. Verify required file
membership, applicable source pins and parent output hashes before relying on
prior results. Raw private snapshots and bulk outputs are not recovered by cloning
Git; report missing dependencies explicitly. Fixture-only success must not be
called private-snapshot verification. Existing Eros retention is accepted;
independent backup remains unestablished.

Register a new named contract and source lock before target/resource evaluation.
Keep `postgres-v1`, earlier contracts, source copies and run outputs immutable.
A correction requires a new contract/lock/run and an explicit correction parent.
If code changes a previously pinned file, disclose the drift and preserve the
old runner/source reproduction route; never rewrite an older lock to hide it.

## 4. Exact target-image validation — immediate prerequisite

The prior read-only observation identified:

- Host/repository: `billy@helios`, `/opt/butterflyguy`.
- Container: `butterfly_timescaledb`.
- PostgreSQL **16.11**, TimescaleDB extension **2.25.2**.
- Recorded repository digest:
  `timescale/timescaledb@sha256:0af03ecf697825f6ddae76fd275d16bf46007bed6d00eb3d754779cb7db96fa6`.
- The tag `timescale/timescaledb:latest-pg16` was observed, but is mutable.

These are dated observations, not current health or approval. The earlier real
engine tests used PostgreSQL **16.2 without the TimescaleDB extension**.

Build an isolated, reproducible harness for the observed image/digest, architecture
and extension version. Record resolved manifest/image identities and verify actual
server/extension versions in each new test DB. Installing/activating the extension
in a newly created isolated fixture DB is permitted. A metadata lookup on Helios
alone does not establish compatibility. Do not silently substitute latest-pg16,
plain PostgreSQL or another extension version and call it exact-target validation.
If the recorded image cannot be resolved/pulled, record the precise discrepancy;
only a material identity question justifies narrowly scoped read-only refresh.

Use an available local container runtime or another genuinely isolated supported
runtime. New test resources must have unique ownership/names, private disposable
storage, bounded resources and no public exposure or host networking. Record exact
resource IDs, versions, commands, logs, shutdown and preserved output paths. Stop
only the new task-owned test process/container. Do not start/stop a shared daemon,
use the live container, attach production volumes, run broad Compose commands,
prune resources or delete prior evidence to make the harness work.

The prior environment lacked a running local Docker daemon; its temporary pgserver
package supplied only PostgreSQL 16.2. Reassess available local infrastructure.
Ordinary dependency downloads/test-environment setup can proceed through normal
sandbox approvals. If exact-target execution remains unavailable, finish all
independent code/tests/docs, report the missing prerequisite, and leave this gate
incomplete. Another SQLite/plain-PG demonstration is not a substitute.

Exercise the actual adapter under the target engine, including:

1. Schema installation/identity, extension identity, installation UUID, repeat-
   installation refusal and correction-parent enforcement.
2. Original native body/decimal precision, complete snapshot membership and signed
   arithmetic through the pinned SDK, asyncpg and actual target engine.
3. Transaction rollback on metadata failure; definitive deferred COMMIT failure;
   ambiguous transport loss at COMMIT; missing post-commit acknowledgement;
   actual backend termination/cancellation and recovery after restart.
4. Consumer MVCC visibility, exact-key reads under concurrent publication, read
   failure, failed receipt journaling and separation of receipt from earliest
   possible availability. Never invent timestamps, decisions or fills.
5. Duplicate/concurrent delivery, out-of-order receipt and corrected versions,
   with existing publications preserved rather than overwritten.
6. Lock contention, pool exhaustion, bounded timeouts and unavailability, with
   publication outcome unknown wherever it really cannot be determined.
7. Ordinary-SQL immutability including UPDATE/DELETE/TRUNCATE; no weakening of
   constraints just to make tests pass.

## 5. Least-privilege roles and pool ownership

Prepare additive, reviewable role/grant SQL and verify it only in isolated DBs.
Separate schema/migration ownership from runtime recording and receipt access.
Use synthetic test roles; do not create, rotate, print or install live credentials.

Specify the minimum privileges required for schema identity reads, quote/provenance/
manifest inserts, correction-parent reads, journal/identity-sequence use, exact
consumer reads and receipt insertion. Verify actual restricted-role operations;
superuser/owner-only tests do not establish application-role compatibility.
Runtime roles must not require broad trading-table access, UPDATE/DELETE/TRUNCATE,
DDL ownership, trigger disabling or a public schema's general privileges. Account
for generated journal sequences and the actual transaction-ID function used.

Specify a dedicated bounded research pool and its ownership, command/acquisition/
lock timeouts, maximum connections, shutdown and recovery. Do not reuse, resize or
hold connections from the order/position/risk pool. A runtime role must be able
to perform required functions without becoming schema owner. Record any target
permission/version dependency rather than granting broad access to hide it.

No live migration/grant runs are authorized. Keep proposed DDL outside automatic
runtime migration discovery until separately reviewed and authorized.

## 6. Smallest default-off observer integration

Choose and justify one concrete research consumer/entry point from local source.
Extend the native client/adapter instead of replacing their protocols. A separate
research entry point/factory is acceptable; a hook that delays trading delivery is
not implicitly approved. Define how it would obtain exact selected instrument
identity, session/calendar, request/pass/acquisition IDs, build/config identity and
consumer identity without consulting hindsight or assuming every session traded.
The full entry-opportunity/skip set needed by NDX-03 remains a later requirement.

Deliver a callable integration and tests, not merely pseudocode. Requirements:

- **Disabled by default**, with an explicit enable decision on the research path.
  Disabled construction/import/startup performs no DB connection/query, DDL,
  gateway request, body copy/parse, worker startup or observer scheduling.
  Preserve the existing SDK validation and routing behavior.
- Keep checked-in active runtime settings unchanged. Put proposed observer config,
  environment-variable names/secret references and deployment overlay in the review
  package, with activation disabled. Never include secret values.
- Recording cannot add retries, duplicate broker/gateway requests or silently
  introduce a new polling schedule. Any proposed independent research traffic
  needs its own declared scope, frequency, capacity and later activation approval.
- Do not await publication inline on an active trading response path. Choose a
  separate research lifecycle or an independently justified bounded handoff. Add
  only the minimal queue/worker mechanism if the selected design actually needs it.
- Bound retained response bytes as well as item count/concurrency; expose the
  limitation that native HTTP buffering already occurred before preservation.
  Cover async backpressure and serialization/parse overhead without an unbounded
  executor/task backlog or indefinite shutdown waits.
- Preserve native body scope, source precision, absent fields, independent clocks,
  commit ambiguity and consumer receipt. No successful observer record may silently
  claim provider-original bytes, gateway build or age-reference evidence.
- Treat quote success and recording success separately. A storage/queue failure
  must not change schedules, sizes, orders, risk decisions, account guards, token
  handling or paper/live mode. Define the research consumer's response explicitly;
  this is not permission to change the running bot's failure policy.
- Bound startup/shutdown, identify a single observer instance and test reconnect,
  cancellation, crash, queue recovery and duplicate publication. A default-off
  factory must not create a second bot or order-capable process.

Test disabled mode with forbidden-network/DB spies and no worker side effects.
Test enabled mode with synthetic market transport and the isolated target DB only.
Cover pending work at shutdown, full/oversized handoff, unavailable DB/gateway,
SDK validation failure and body rejection, as well as clean success.

## 7. Drop/failure accounting, resource budgets and retention

Specify and test an observer lifecycle ledger with clear units and identities.
Separate received market responses, accepted/rejected recording items, queued
items, attempts, committed publications, observed acknowledgements, consumer reads,
receipt records, known drops and unresolved outcomes. Do not count duplicate delivery
as new market coverage or a missing provenance record as a missing market quote.

Counters that exist only in process memory cannot prove durable completeness after
a crash. Make that limitation explicit. Reconcile durable attempts, publications,
failure events and restarts without creating lost timestamps or claiming zero
drops during an unobserved interval. Test observer failure when acquisition identity
or the failure journal itself is unavailable. Persist categorical, non-secret
reasons; do not log exception/HTTP context that could contain sensitive data.

Register mechanisms and resource-test scenarios before measuring them. Include
representative and boundary-sized native bodies, incompressible/varied synthetic
content, concurrency, pressure/outage/recovery and elapsed shutdown. Measure SDK
and observer overhead separately where feasible, Python and DB CPU/RSS, retained
bytes, connections, queue pressure, dropped/unresolved records, storage growth and
consumer lag. Distinguish local/tmpfs and network/durable storage and attribute
any transport/commit-fault injection. Repeated compressible bodies do not establish
real retention or production performance.

Propose explicit, independently justified connection/byte/concurrency/disk/time
budgets and the behavior at each bound. They are resource limits, not freshness,
liquidity, signal/fill or strategy thresholds. Do not derive them from P&L.
If production capacity remains unmeasured, label it unvalidated rather than inventing
an acceptance claim. Preserve all raw signed market values when excluding or
rejecting recording items.

Prepare a retention/restore plan: owner, location, manifest/hash verification,
expected daily bytes under the proposed capture universe/schedule, failure records,
recovery checks and evidence preservation. Do not delete/prune existing snapshots,
create real backup jobs or claim independent backup merely because two copies are
on the same Eros filesystem. Any proposed live retention automation needs its
own reviewed activation. NFS is the current archive; do not put an active local
test PostgreSQL/SQLite data directory on it as a substitute for validated storage.

## 8. Upstream evidence and scope boundary

Maintain a concise gap/ownership ledger for ButterflyGuy, the pinned gateway SDK,
SchwabGateway service and provider. Current public SDK output lacks the actual
freshness-reference instant and complete upstream build/cache/clock identity.
Record what the new local code observes versus what requires an upstream contract
change or external attestation. Original provider body and gateway-normalized body
remain distinct. Per-contract versus chain-wide metadata remain distinct.

Read-only local upstream source inspection may clarify a specific question.
Do not modify another repository, change SDK pins, acquire real market data,
scan credentials, reauthorize tokens or query broader historical trading windows
under this task. Prepare a concrete upstream request/spec if necessary, with the
missing field, owner, observation point and required evidence. Missing upstream
facts may remain unknown; do not relax v1 sufficiency/replay eligibility to make
new records appear complete.

## 9. Prepare an activation review package; do not execute it

Finish a concrete package with:

- The final implementation diff and proposed disabled configuration/entry point.
- Exact target image/version proof and isolated role/schema/adapter test evidence.
- Capture universe/window/cadence proposal, expected traffic, observer uniqueness,
  resource/drop/retention budgets and unresolved upstream/backup evidence.
- Proposed additive DDL/grants, the dedicated research pool/secret references and
  an explicit statement of affected services and trading/database impact.
- Startup, live validation, stop/rollback and evidence-preservation procedures.
  Rollback must not delete research evidence or alter trading limits/routing.
- A clear readiness result: ready for operational review, or incomplete with
  named blockers. Passing isolated mechanics alone does not make activation ready.

Before any actual approval request, use the VPS/Helios skills to establish the
named target's current release/image, state, disk, relevant positions/orders,
uniqueness and rollback baseline through appropriately scoped read-only checks.
The old DB-version observation is not a full or current operational preflight.
Use existing safe project mechanisms and avoid credential-bearing diagnostics.
Do not invent unverified service names, release IDs, approval or rollback commands.
If preflight cannot be completed, finish the independent package and say which
operational facts remain unavailable; do not call it deployment-ready.

**No live schema/grant changes, capture activation, service rebuild/restart,
deployment, order, credential change, paper observation or economic experiment is
authorized by this instruction.** Operational approval, if requested later, must
name the completed concrete target/change. Do not repeatedly ask for permission
to perform reversible local preparation already authorized here.

## 10. Verification and immutable handoff

Run focused native, observer, role and exact-target tests, then the existing
private-enabled NDX suite where affected. The prior full check was:

```bash
NDX_POSTGRES_BIN=/home/corey/.cache/uv/archive-v0/ZWZ0Mqbj4Iv7hOst/pgserver/pginstall/bin \
NDX_FIDELITY_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_CONTINUATION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-minute-continuation-20261015-v2 \
NDX_EXECUTION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014 \
NDX_SUPPLEMENT=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015 \
uv run --offline --frozen pytest \
  tests/test_ndx_native_response.py tests/test_ndx_postgres_recording.py \
  tests/test_ndx_recording.py tests/test_ndx_provenance.py \
  tests/test_ndx_quote_fidelity.py tests/test_ndx_quote_fidelity_raw.py \
  tests/test_ndx_continuation.py tests/test_ndx_execution_audit.py \
  tests/test_ndx_baseline.py tests/test_state_machine.py tests/test_position_manager.py -q
uv run --offline --frozen ruff check .
git diff --check
```

The pgserver binary path belongs to the earlier PostgreSQL 16.2 tests. It does
**not** satisfy the new exact TimescaleDB-image gate. Add a separately identifiable
exact-target command/harness and new focused observer/permission checks. Preserve
clear denominators for ordinary PG tests, exact-target tests, private-snapshot
checks and skipped fixtures; do not sum skips into a successful target claim.
Use a provisioned locked environment; separate dependency acquisition from offline
reproduction and record any required downloads/temporary environment changes.

After code changes run the installed graphify AST update without semantic/API work
or unrelated parser installation; record optional parser/label limitations. The
previous available binary was
`/home/corey/.cache/uv/archive-v0/Yo1tT0lFfjWucooJ/bin/graphify`.

Each new run needs new explicit input/config/source-lock/output paths, parent and
correction hashes, exact invocation, source copies, starting Git SHA/dirty state,
UTC, Python/dependency/platform and target image/server/extension identity,
input/config/source/output hashes and test/process/container ownership/shutdown
records. Preserve unsuccessful/superseded runs. Never overwrite an old dated
contract, source lock, record or bulk output. Archive closed evidence with verified
hashes, keeping secrets/real raw bodies and bulk outputs outside Git.

Update the living plan and index with status, exact commands/paths, source/run
identities, actual checks, skips/failures, unresolved facts and the next bounded
action. Keep earlier dated evidence intact. Full NDX-02, actual execution/XQC and
NDX-03–06 remain open; the existing roadmap retains their separate evidence and
research authorization gates. Do not rerun any of the six rejected exit settings,
calculate new strategy P&L or choose market thresholds in this task.

## Completion criteria and final response

Complete the stage only when the review package contains:

1. Real isolated exact-image/extension and restricted-role validation. If this cannot
   run, finish the independent work but mark the stage incomplete and name the
   specific unavailable prerequisite.
2. A minimal tested default-off observer factory/entry point and lifecycle, with
   bounded pool/bytes/concurrency/shutdown and explicit drop/recovery semantics.
3. A preregistered resource run and preserved evidence; no production-capacity claim
   beyond what was measured.
4. A concrete activation/retention/rollback review package with unresolved upstream
   and operational facts clearly distinguished from implemented behavior.
5. Updated immutable verification records and living handoff, while all historical
   eligibility decisions and runtime trading behavior remain unchanged.

Report overall stage readiness honestly: independent code completion does not make
a missing exact-target gate pass or activate capture. In the final response state
what was implemented/saved, exact tests and skips, remaining evidence/blockers,
that no live activation occurred, and the exact next action. Ask for operational
approval only if the full named-target package and required preflight are ready;
otherwise finish with the actual unresolved gate rather than a speculative request.
