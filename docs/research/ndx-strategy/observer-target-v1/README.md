# Exact-target resources and restore — registered mechanisms

This package extends the passing observer-v1 exact-image compatibility checks
without activating capture. Its named contract/source lock is registered before
resource or restore evaluation. Earlier contracts, source copies and outputs
remain immutable. No strategy, execution, risk, token or active config changes.

`check_ndx_target_restore.py` creates a fresh UUID-named local container of the
same frozen digest/amd64 image, private Unix socket, network=none, one CPU,
1 GiB memory, 128 PIDs and 512 MiB disposable data tmpfs. It accepts no DSN,
existing container/volume or image override. Actual PG 16.11/TimescaleDB 2.25.2
are checked in each database, including the resource and restored databases.
Only the task-owned container is stopped; its identity and logs are preserved.

The previously registered four resource cases and three samples per case are
reused unchanged: small, varied 5,000 contracts, exactly 2 MiB, one byte over.
SDK-only and full publication/read measurements remain separate. The resource
helper adds optional explicit database initialization and process sampling hooks;
its ordinary-PG default behavior is unchanged. This is disclosed source drift
from observer-v1's helper pin, whose original remains archived in resources-run-02
and target-run-04. Never rewrite those locks to hide drift.

The initializer activates the registered extension only inside the fresh fixture
DB. Process sampling reads `/proc/PID/stat` inside the owned container, because
backend PIDs belong to that namespace. Reading host `/proc/PID` would attribute
unrelated processes. Page size/clock ticks come from the shared local kernel.
RSS/CPU remain endpoint samples, not peaks. The reused helper's original
`exact_target_gate=not_tested_by_this_runner` label stays intact; the enclosing
runner independently attests the actual target identity. All limits, compression,
body buffering, synchronous parse and local/tmpfs capacity caveats still apply.

After resource observers close, add one explicitly synthetic durable attempt
without a publication. Fingerprint every original research table row, including
raw-body hashes, installation UUID, journal sequences, transaction IDs and actual
acknowledgement/receipt stamps. Export only the research schema to a custom-format
pg_dump without ownership/ACLs; hash it and verify the dump manifest before restore.

Create a second fresh DB on the same isolated target engine. Install/verify the
extension, restore in a single transaction and apply explicit research ownership/
grants using existing synthetic NOLOGIN group roles. This is the exact scope of
`restore-grants.sql`; no live role/credential is created or changed. Compare all
restored row fingerprints and recovery inventory before new reads. Then read each
of the nine publications as a restricted research reader, compare exact body
bytes with the frozen synthetic input, check signed -4.02 arithmetic and false
replay eligibility, and append nine newly observed consumer receipts. Verify no
new commit acknowledgements and that the unpublished attempt remains unpublished
and unacknowledged. A restore cannot recreate a lost historical acknowledgement.

Register measurements for dump/restore elapsed time and bytes, DB growth, Python
peak RSS, namespaced backend endpoint CPU/RSS, retained bytes/connections/counters,
shutdown and one post-run container resource sample. Limits are resource proposals,
not market thresholds. A same-container/local-tmpfs restore validates mechanics,
not independent backup, durable/network storage, WAL reserve or production capacity.
Closed hashed evidence is archived on the accepted Eros filesystem; no deletion,
retention automation or backup job is created.

Run with explicit new output:

```bash
uv run --offline --frozen python tools/check_ndx_target_restore.py \
  --config docs/research/ndx-strategy/observer-target-v1/contract.json \
  --source-lock docs/research/ndx-strategy/observer-target-v1/source-lock.json \
  --output /tmp/ndx-target-resources-restore/run-01
```

Read-only Helios review is separate from synthetic evaluation. Collect filtered
current release/image/service identities, health, disk, unique container names,
aggregate current DB open/nonterminal intent counts and research-schema/role
presence. Do not print environments, account IDs, tokens or raw logs. Broker
flatness is a distinct check: the existing audit initializes a token-refreshing
client and is not run under a no-token-change scope. Health/DB counts cannot
replace broker evidence. Current remote source/config dirt must be preserved.
No release, DDL/grant, restart, capture or operational approval follows from
these read-only observations; the final review must name remaining blockers.
