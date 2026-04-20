"""Execute SQL migration files in order."""

from __future__ import annotations

from pathlib import Path

from butterfly_guy.core.logging import get_logger
from butterfly_guy.db.connection import DatabasePool

log = get_logger(__name__)
MIGRATIONS_DIR = Path(__file__).parent


async def run_migrations(db: DatabasePool) -> None:
    """Run all SQL migration files in order."""
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for sql_file in sql_files:
        log.info("running_migration", file=sql_file.name)
        sql = sql_file.read_text()
        try:
            await db.pool.execute(sql)
            log.info("migration_complete", file=sql_file.name)
        except Exception as e:
            log.error("migration_failed", file=sql_file.name, error=str(e))
            raise
