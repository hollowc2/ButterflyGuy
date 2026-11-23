# SPX readiness fixes: deployment, migration and rollback plan

Prepared November 23, 2026. **No production changes are authorized by this plan.**
No live orders, deployments, restarts, production migrations, or dated live sessions
were executed during the investigation. The assessment is **NO-GO for a live canary**
until the gates below are satisfied. A mechanics rehearsal establishes no profitability.

## Reviewed candidate and rollback baseline

The candidate is the clean `b3150ad75fdc01a7080e6bad42b9445bbc4c3a89` tree plus only
the files enumerated in
[`candidate-release.json`](../../data/rehearsals/SPX/2026-11-23/readiness-fixes-20261123/candidate-release.json).
Use its individual source/config hashes, the final evidence manifest and the local
image receipt as identity; the dirty workspace HEAD alone does not identify this code.
The final local image is
`sha256:568eb8a15a58b6587f6e5e8312ea7aed68421887db0794adbc501825683448b1`;
[`image-receipt.json`](../../data/rehearsals/SPX/2026-11-23/readiness-fixes-20261123/image-receipt.json)
records a credential-free, network-disabled Python 3.12.15 import and source-hash
check. The isolated build context is `/tmp/spx-readiness-candidate-20261123`. Do not build a
release from the whole dirty workspace or include the unrelated research/graph edits.
Before promotion, commit the reviewed patch separately, require the exact commit's
CI and Database Smoke checks, and match the built image's sources to these hashes.

Helios baseline:

- Host `billy@helios`; session `/opt/butterflyguy-releases/spx-live-20261123-fe051d6`.
- Runtime release `4a3c3515637a0d5346c49d640d386da3e678c27d`.
- Rollback image `sha256:6da41417101b27cd429dffb55b1768da0fbf2259c656d2cc2acf0594721c6739`.
- Only intended future session service: project `butterfly-spx-live`, service
  `app_spx_live`, container `butterfly_spx_live_app`, loopback port 8002.
- Current session is **paper**, role `live_rehearsal`, separate DB
  `butterfly_guy_spx_live_rehearsal`. It must finish its existing close-out normally.
- Regular paper SPX is `butterfly_spx_app` in the independent paper project. Its
  fingerprint was unchanged. Do not run `down`, `--remove-orphans`, or restart it.
- Shared TimescaleDB is `butterfly_timescaledb`, PG16 / TimescaleDB **2.25.2**.
  Do not restart it, upgrade its extension/image, or touch other databases.

## Schema finding and exact migration

The read-only migration ledger and public columns/index definitions match the
reviewed files through **012** in `butterfly_guy_spx_live`. Its size was 80,441,827
bytes. All 12 checksums match both the checkout and installed image. Only
[`013_account_monitor.sql`](../../src/butterfly_guy/db/migrations/013_account_monitor.sql)
is absent. SHA-256:
`5ee965d218225380ca9a92254318e4e5712e7e8e9802a1b82a2201c6d8176277`.
The rehearsal DB already has matching 001–013 and columns/indexes. The shared
paper DB also has 001–013 plus unrelated data tables and extra indexes; none of
those should be copied into the dedicated live database or removed.

The exact application SQL is:

```sql
-- Each database belongs to one account. account_key is the fixed literal
-- 'brokerage_account', with no derivation from an account number or broker hash.
CREATE TABLE IF NOT EXISTS account_monitor_state (
    account_key TEXT PRIMARY KEY,
    state JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Use the existing `run_migrations()` runner, which locks with advisory key 810770001,
checks prior checksums, and applies that SQL and its `schema_migrations` receipt in
one transaction. Do not hand-edit the receipt or relax `spx_live_db check`.
No additional migration is needed for exit receipts: they live in trade metadata.
The additive table does not rewrite trade/hypertable rows. It briefly takes catalog
locks and uses one connection. No service restart is needed for migration itself.
The rollback image already contains 013 and remains schema compatible.

## Backup and restore, before an approved migration

These commands are a **future approved procedure**, not actions taken today.
Run on Helios, with a new access-restricted backup directory, outside a session.
Record disk space, server/extension versions, exact image digests, schema ledger,
open trades/intents, broker reconciliation and container fingerprints first.

```bash
umask 077
BACKUP_DIR=/opt/butterflyguy-releases/spx-readiness-migration-backup-APPROVED_TIMESTAMP
mkdir -p "$BACKUP_DIR"
docker exec butterfly_timescaledb pg_dump -U butterfly \
  -d butterfly_guy_spx_live --format=custom > "$BACKUP_DIR/spx-live-before-013.dump"
docker exec -i butterfly_timescaledb pg_restore --list \
  < "$BACKUP_DIR/spx-live-before-013.dump" > "$BACKUP_DIR/restore-list.txt"
sha256sum "$BACKUP_DIR/spx-live-before-013.dump" > "$BACKUP_DIR/SHA256SUMS"
```

A full database custom dump includes Timescale catalogs, hypertables and chunks;
do not use a table-only dump or copy individual volume files. A logical dump is
transactionally consistent but can add read I/O; confirm available disk first.
Keep credentials out of command output and keep the dump private. Database roles
are not in this dump; retain the existing `butterfly` role and grants on the same
cluster. A new cluster also needs the separately secured roles/ownership setup.

Test recovery into a **new, uniquely named restore database**, on PG16 with the
same TimescaleDB 2.25.2 extension. Never restore over an active database:

```bash
RESTORE_DB=butterfly_guy_spx_live_restore_APPROVED_TIMESTAMP
docker exec butterfly_timescaledb createdb -U butterfly "$RESTORE_DB"
docker exec butterfly_timescaledb psql -U butterfly -d "$RESTORE_DB" \
  -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS timescaledb VERSION '2.25.2'"
docker exec butterfly_timescaledb psql -U butterfly -d "$RESTORE_DB" \
  -v ON_ERROR_STOP=1 -c 'SELECT timescaledb_pre_restore()'
docker exec -i butterfly_timescaledb pg_restore -U butterfly \
  -d "$RESTORE_DB" --no-owner --exit-on-error < "$BACKUP_DIR/spx-live-before-013.dump"
docker exec butterfly_timescaledb psql -U butterfly -d "$RESTORE_DB" \
  -v ON_ERROR_STOP=1 -c 'SELECT timescaledb_post_restore()'
```

Run restore serially, check all errors, compare schema checksums, table/chunk row
counts, trade/intent/risk totals and grants. Restored background compression or
retention policies must not run against a test restore unexpectedly: inspect
Timescale jobs and isolate/suspend those jobs in the restore copy only. Do not
change jobs in the source DB. The local scratch migration and full logical restore
passed on PG16.11 / TimescaleDB 2.25.2; the scratch dump did not contain production's
populated/compressed chunks. A successful restore of the actual backup is still a
release gate. Dump/restore is disaster recovery, not the normal application rollback.

## Approval 1: migrate only butterfly_guy_spx_live from 012 to 013

Require explicit approval naming that database and migration. Verify zero open
bot trades, unresolved/unlinked intents, unexplained broker differences, or unknown
working orders. Verify backup/restore above and the exact migration file hash.
No new trading process is needed. The following one-off container has no mounted
tokens and runs only the migration runner. `MIGRATION_IMAGE` must be the reviewed
immutable image whose migration hashes match the evidence (the baseline image
above already has the exact 013).

```bash
MIGRATION_IMAGE=sha256:6da41417101b27cd429dffb55b1768da0fbf2259c656d2cc2acf0594721c6739
docker run --rm -i --network monitoring_net --read-only --tmpfs /tmp \
  --env-file /opt/butterflyguy/.env \
  -e DATABASE__HOST=butterfly_timescaledb -e DATABASE__PORT=5432 \
  -e DATABASE__USER=butterfly -e DATABASE__NAME=butterfly_guy_spx_live \
  --entrypoint python "$MIGRATION_IMAGE" - <<'PY'
import asyncio
import hashlib
from butterfly_guy.core.config import load_config
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import MIGRATIONS_DIR, run_migrations
from butterfly_guy.scripts.spx_live_db import check
async def main():
    config = load_config('configs/config.yaml')
    assert config.database.name == 'butterfly_guy_spx_live'
    assert hashlib.sha256((MIGRATIONS_DIR / '013_account_monitor.sql').read_bytes()).hexdigest() == (
        '5ee965d218225380ca9a92254318e4e5712e7e8e9802a1b82a2201c6d8176277'
    )
    db = DatabasePool(config.database.dsn, min_size=1, max_size=1)
    await db.initialize()
    try:
        await run_migrations(db)
        async with db.pool.acquire() as conn:
            result = await check(conn)
        print(result)
        assert result['schema_at_head'] and result['ok']
    finally:
        await db.close()
asyncio.run(main())
PY
```

Re-read all ledger checksums, account-monitor columns, trade/risk counts, broker
positions/orders and paper fingerprint afterward. If the transaction fails, keep
the service stopped and investigate; do not insert a successful receipt manually.
If it commits, retain 013 even when rolling application code back. Do not drop its
table or delete the ledger entry. Restoring an old dump after any new fills would
lose trading evidence; never use restore to erase or reconcile real transactions.
If disaster recovery is required, restore to a new DB, reconcile subsequent broker
activity, and obtain separate approval before changing a service's DB target.

## Approval 2: deploy the fixed image for a dated paper rehearsal

After the current session's real close-out/export/audit pass, prepare a new session
directory by copying the reviewed session scripts. Pin the fixed immutable image
from `image-receipt.json`, retain the original session untouched, and record both
new and rollback compose arguments. Verify dedicated chain directories and the
fresh rehearsal DB; do not rerun fault tests against either runtime DB.

Use the existing `activate.sh`/`common.sh` compose construction, with `REHEARSAL=1`
and the rehearsal overlay applied last. Review `DRY_RUN=1 ./activate.sh` first.
Approve the exact dated session and target before the real activation. Verify:
`paper_trading=true`, **both** allow-live flags false, role `live_rehearsal`, the
separate rehearsal DB, dedicated live/rehearsal webhook, normal entry/profit
settings, one-contract/one-trade limits and one intended runtime. Do not carry the
November 23 entry-window, center-tolerance or early-exit nudges forward.

Validate health/readiness, source hashes, new worker heartbeat/delivery logs,
pending receipts, an isolated rejection→recovery demonstration, accounting and
paper fingerprints. Require real Discord HTTP acceptance through the intended
channel before promotion; a unit fixture does not prove credentials or delivery.
For a failed notification, the monitor must complete while its closed trade's
`exit_notification_status` stays pending. No broker APIs may be fault-injected.

## Stop and rollback

Use the copied session's existing guarded `stop-live.sh`/`closeout.sh`. Never use
`FORCE=1` just to satisfy a gate. Halt/drain new entries with the established
procedure while preserving position management; reconcile with the broker. If an
operator takes over an open fly, retain explicit supervision until its actual fill
or settlement is recorded. Do not restart through unknown/working broker orders.

Once safe/flat and explicitly approved, stop only `app_spx_live`, pin
`SPX_LIVE_IMAGE` back to the rollback digest above, and run the existing activation
path in the **approved mode/date**, using the same dedicated DB and normal config. `$REL` below is the source
release directory containing `infra/`, not the session-scripts directory.
A concrete compose recreation, after confirming these variables/overlays and the
named approval, is:

```bash
SPX_LIVE_IMAGE=sha256:6da41417101b27cd429dffb55b1768da0fbf2259c656d2cc2acf0594721c6739 \
  SPX_LIVE_TEST_DATE="$DATE" SCHWAB_GATEWAY_TOKEN_DIR="$TOKEN_DIR" \
  docker compose --project-directory /opt/butterflyguy/infra \
  -f "$REL/infra/docker-compose.spx-live.yml" \
  -f "$REL/infra/docker-compose.spx-live-rehearsal.yml" \
  up -d --no-deps --no-build --pull never app_spx_live
```

This example is **paper rehearsal only**, with the rehearsal overlay last and the
existing approved session environment (including required token-directory/date
interpolation). For real-money rollback use that supervised session's recorded
compose argv, not this example. Revalidate role, flags, DB target, schema, broker
state, health and the unchanged regular-paper fingerprint. Preserve all trade
metadata and evidence. The old image tolerates the new receipt metadata and 013,
but has no retry worker: pending messages remain stored and need operator follow-up
until the fixed image returns; old code retains the original notification bug.

## Future one-contract canary gates

Do not request or schedule it until all these have current evidence:

1. Exact reviewed release, successful CI/Database Smoke, matching source/config and
   image hashes, migration 013 in the live DB, validated backup and recovery.
2. Actual November 23 close-out/export/post-close audit results, complete hashes,
   explicit gap analysis, closed trade and reconciled risk, deliberate stop and
   unchanged paper fingerprint. A waiting timer is not successful execution.
3. Fresh read-only broker reconciliation for all current positions and working
   orders, matching bot-owned intents. Attribute external/manual trades explicitly;
   do not adopt them. No unknown orders or unexplained differences.
4. One intended runtime, direct SPX market data, normal entry/exit settings with
   all rehearsal nudges absent, original risk/account/order guards unchanged.
5. Confirmed alert routing/acceptance and supervision, health checks, halt/drain,
   guarded close-out and recorded rollback argv/digest. Exit delivery is at least
   once: a lost acknowledgment/receipt may duplicate a message, never an exit order.
6. Separate explicit owner approval for the named **dated supervised session**.
   Keep one contract; do not raise limits or relax criteria to obtain a fill.
