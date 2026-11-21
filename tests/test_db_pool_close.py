import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from butterfly_guy.db.connection import DatabasePool


def _db(close) -> tuple[DatabasePool, MagicMock]:
    pool = MagicMock(close=close)
    db = DatabasePool("postgresql://u:p@localhost:5432/test")
    db._pool = pool
    return db, pool


@pytest.mark.asyncio
async def test_close_terminates_a_pool_that_waits_on_a_leaked_lease():
    """Codex review of 2a0f9b0: shutdown must reach the nonzero exit a restart needs."""

    async def never_released():
        await asyncio.Event().wait()

    db, pool = _db(never_released)

    await asyncio.wait_for(db.close(timeout=0.01), 1.0)

    pool.terminate.assert_called_once_with()
    assert db._pool is None


@pytest.mark.asyncio
async def test_close_does_not_terminate_a_pool_that_closes():
    db, pool = _db(AsyncMock())

    await db.close()

    pool.close.assert_awaited_once()
    pool.terminate.assert_not_called()
    assert db._pool is None
