"""Real asyncpg pool: a failed entry-lock release must never hang shutdown.

pool.close() waits for every checked-out connection. If pool.release() fails before it
hands the lease back, the safety exception reaches main() but shutdown waits forever, so
the process never exits nonzero and the restart that reconciles the fill never comes.
A failed connection reset is the ordinary case and asyncpg already frees that lease.
Runs where CI_DATABASE_URL points at a scratch server.
"""

import asyncio
import contextlib
import datetime as dt
import os
import time
import uuid

import asyncpg
import pytest

from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.queries import entry_lock_key
from butterfly_guy.execution.order_manager import AmbiguousOrderError
from butterfly_guy.scripts import spx_live_db
from tests.integration.test_spx_live_db import _settings
from tests.test_trade_service import _filled_live_entry, _patch_filled_entry

DAY = dt.date(2026, 11, 20)
# Prompt, and well inside DatabasePool's own close bound: these tests prove the lease is
# returned, not that the bound rescued it.
PROMPT_CLOSE_S = 5.0


@contextlib.asynccontextmanager
async def scratch_pool():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")
    name = f"lockrel_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{name}"')
    scratch = spx_live_db.dsn_for(_settings(dsn), name)
    db = DatabasePool(scratch, min_size=1, max_size=2)
    await db.initialize()
    try:
        yield name, admin, db, scratch
    finally:
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(db.close(), PROMPT_CLOSE_S)  # no-op once a test closed it
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()


async def lock_is_free(scratch: str, key: str) -> bool:
    """The server drops a terminated session's advisory lock once it sees the EOF."""
    probe = await asyncpg.connect(scratch)
    try:
        for _ in range(100):
            if await probe.fetchval("SELECT pg_try_advisory_lock(hashtext($1)::bigint)", key):
                await probe.execute("SELECT pg_advisory_unlock(hashtext($1)::bigint)", key)
                return True
            await asyncio.sleep(0.02)
        return False
    finally:
        await probe.close()


async def close_promptly(db: DatabasePool) -> float:
    started = time.monotonic()
    await asyncio.wait_for(db.close(), PROMPT_CLOSE_S)
    return time.monotonic() - started


def fail_release_before_the_lease_returns(monkeypatch):
    async def release(self, connection, *, timeout=None):
        raise asyncpg.InterfaceError("release failed before returning the lease")

    monkeypatch.setattr(asyncpg.Pool, "release", release)


def live_service(db: DatabasePool):
    """The filled-entry service with the real advisory-lock helpers on the real pool."""
    f = _filled_live_entry()
    del f.service._acquire_entry_lock
    del f.service._release_entry_lock
    f.trade_queries.db = db
    f.keys = []
    acquire = f.service._acquire_entry_lock

    async def recording_acquire(underlying, trade_date):
        lock = await acquire(underlying, trade_date)
        if lock is not None:
            f.keys.append(lock[1])
        return lock

    f.service._acquire_entry_lock = recording_acquire
    return f


@pytest.mark.asyncio
async def test_a_lease_release_never_returned_keeps_the_halt_and_cannot_hang_shutdown(
    monkeypatch,
):
    async with scratch_pool() as (_, _, db, scratch):
        f = live_service(db)
        f.trade_queries.insert_trade.side_effect = RuntimeError("db unavailable")
        fail_release_before_the_lease_returns(monkeypatch)

        with _patch_filled_entry(f.selection), pytest.raises(
            AmbiguousOrderError, match="broker fill was not fully persisted"
        ):
            await f.service.attempt_entry()

        monkeypatch.undo()
        assert len(f.keys) == 1
        assert await lock_is_free(scratch, f.keys[0])
        assert await close_promptly(db) < PROMPT_CLOSE_S


@pytest.mark.asyncio
async def test_a_saved_fill_survives_a_lease_release_never_returned(monkeypatch):
    async with scratch_pool() as (_, _, db, scratch):
        f = live_service(db)
        fail_release_before_the_lease_returns(monkeypatch)

        with _patch_filled_entry(f.selection):
            result = await f.service.attempt_entry()

        monkeypatch.undo()
        assert result is not None and result[0].trade_id == 99
        assert len(f.keys) == 1
        assert await lock_is_free(scratch, f.keys[0])
        assert await close_promptly(db) < PROMPT_CLOSE_S


@pytest.mark.asyncio
async def test_an_ordinary_reset_failure_is_freed_by_asyncpg_alone(monkeypatch):
    """Control: asyncpg terminates and frees a connection whose reset failed."""
    async with scratch_pool() as (_, _, db, scratch):
        f = live_service(db)
        terminations = []
        terminate = asyncpg.connection.Connection.terminate

        def counting_terminate(self):
            terminations.append(self)
            terminate(self)

        async def failing_reset(self, *, timeout=None):
            raise ConnectionResetError("reset failed")

        monkeypatch.setattr(asyncpg.connection.Connection, "terminate", counting_terminate)
        monkeypatch.setattr(asyncpg.connection.Connection, "reset", failing_reset)
        lock = await f.service._acquire_entry_lock("SPX", DAY)
        assert lock is not None

        await f.service._release_entry_lock_quietly(lock, trade_id=99)

        monkeypatch.undo()
        assert len(terminations) == 1  # asyncpg's own; the proxy was already detached
        assert await lock_is_free(scratch, entry_lock_key("SPX", DAY))
        assert await close_promptly(db) < PROMPT_CLOSE_S


@pytest.mark.asyncio
async def test_pool_close_is_bounded_and_terminates_a_leaked_lease():
    async with scratch_pool() as (name, admin, db, _):
        leaked = await db.pool.acquire()
        await leaked.execute("SELECT 1")

        started = time.monotonic()
        await db.close(timeout=0.5)

        assert time.monotonic() - started < PROMPT_CLOSE_S
        for _ in range(100):
            backends = await admin.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = $1", name
            )
            if backends == 0:
                break
            await asyncio.sleep(0.02)
        assert backends == 0
