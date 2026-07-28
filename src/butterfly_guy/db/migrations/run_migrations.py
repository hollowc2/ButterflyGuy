"""Execute SQL migration files in order."""

from __future__ import annotations

import hashlib
from pathlib import Path

from butterfly_guy.core.logging import get_logger
from butterfly_guy.db.connection import DatabasePool

log = get_logger(__name__)
MIGRATIONS_DIR = Path(__file__).parent
MIGRATION_LOCK_ID = 810_770_001
CREATE_LEDGER_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


async def run_migrations(db: DatabasePool) -> None:
    """Run all SQL migration files in order."""
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    async with db.pool.acquire() as conn:
        await conn.execute("SELECT pg_advisory_lock($1)", MIGRATION_LOCK_ID)
        try:
            await conn.execute(CREATE_LEDGER_SQL)
            applied = {
                row["version"]: row["checksum"]
                for row in await conn.fetch("SELECT version, checksum FROM schema_migrations")
            }
            for sql_file in sql_files:
                sql = sql_file.read_text()
                checksum = hashlib.sha256(sql.encode()).hexdigest()
                if applied.get(sql_file.name) == checksum:
                    continue
                if sql_file.name in applied:
                    raise RuntimeError(f"Migration checksum mismatch: {sql_file.name}")
                log.info("running_migration", file=sql_file.name)
                try:
                    async with conn.transaction():
                        await conn.execute(sql)
                        await conn.execute(
                            "INSERT INTO schema_migrations (version, checksum) VALUES ($1, $2)",
                            sql_file.name,
                            checksum,
                        )
                    log.info("migration_complete", file=sql_file.name)
                except Exception as e:
                    log.error("migration_failed", file=sql_file.name, error=str(e))
                    raise
        finally:
            await conn.execute("SELECT pg_advisory_unlock($1)", MIGRATION_LOCK_ID)
