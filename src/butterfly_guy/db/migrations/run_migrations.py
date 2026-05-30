"""Execute SQL migration files in order."""

from __future__ import annotations

from pathlib import Path

from butterfly_guy.core.logging import get_logger
from butterfly_guy.db.connection import DatabasePool

log = get_logger(__name__)
MIGRATIONS_DIR = Path(__file__).parent
MIGRATION_LOCK_ID = 810_770_001


async def run_migrations(db: DatabasePool) -> None:
    """Run all SQL migration files in order."""
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    async with db.pool.acquire() as conn:
        await conn.execute("SELECT pg_advisory_lock($1)", MIGRATION_LOCK_ID)
        try:
            for sql_file in sql_files:
                log.info("running_migration", file=sql_file.name)
                sql = sql_file.read_text()
                try:
                    await conn.execute(sql)
                    log.info("migration_complete", file=sql_file.name)
                except Exception as e:
                    log.error("migration_failed", file=sql_file.name, error=str(e))
                    raise
        finally:
            await conn.execute("SELECT pg_advisory_unlock($1)", MIGRATION_LOCK_ID)
