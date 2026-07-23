"""Async database connection pool using asyncpg."""

from __future__ import annotations

import asyncpg
from prometheus_client import Gauge

from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

database_pool_size = Gauge(
    "butterfly_database_pool_size",
    "Current PostgreSQL pool connection count",
    ["database"],
)
database_pool_idle = Gauge(
    "butterfly_database_pool_idle",
    "Current idle PostgreSQL pool connection count",
    ["database"],
)
database_pool_max = Gauge(
    "butterfly_database_pool_max",
    "Configured maximum PostgreSQL pool size",
    ["database"],
)


class DatabasePool:
    """Manages an asyncpg connection pool for TimescaleDB."""

    def __init__(self, dsn: str, min_size: int = 2, max_size: int = 10) -> None:
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self._pool: asyncpg.Pool | None = None
        self._database_label = dsn.rsplit("/", 1)[-1].split("?", 1)[0]

    async def initialize(self) -> None:
        """Create the connection pool."""
        self._pool = await asyncpg.create_pool(
            self.dsn, min_size=self.min_size, max_size=self.max_size
        )
        database_pool_max.labels(database=self._database_label).set(self.max_size)
        database_pool_size.labels(database=self._database_label).set_function(
            self.pool.get_size
        )
        database_pool_idle.labels(database=self._database_label).set_function(
            self.pool.get_idle_size
        )
        log.info("database_pool_initialized", dsn=self.dsn.split("@")[-1])

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            log.info("database_pool_closed")
