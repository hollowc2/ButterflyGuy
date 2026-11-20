"""Real Postgres faults at the intent INSERT, through the real OrderManager.

The unit tests decided with fakes which exceptions mean "outcome unknown". Here the real
asyncpg driver and server raise them: a backend killed mid-INSERT, asyncpg's client-side
command timeout, the server's statement_timeout, and the real unique indexes. Only Schwab
is a fake. Runs where CI_DATABASE_URL points at a scratch server.
"""

import asyncio
import contextlib
import os
import uuid

import asyncpg
import pytest
from asyncpg.exceptions import QueryCanceledError, UniqueViolationError

from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations
from butterfly_guy.db.queries import OrderIntentQueries
from butterfly_guy.execution.order_manager import AmbiguousOrderError, IntentPersistenceError
from butterfly_guy.scripts import spx_live_db
from tests.integration.test_spx_live_db import _settings
from tests.test_live_incident_replay import DAY, FLY, Broker, _live_candidate, _manager
from tests.test_order_manager import filled_order

TRADE = """
INSERT INTO butterfly_trades (
    id, trade_date, direction, wing_width, center_strike, lower_strike, upper_strike,
    entry_price, entry_time, quantity, status, underlying
) VALUES (100000, $1, 'CALL', 40, 7475, 7435, 7515, 3.75, NOW(), 1, 'OPEN', 'SPX')
"""


@contextlib.asynccontextmanager
async def scratch_db(command_timeout: float = 10.0, statement_timeout: str | None = None):
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")
    name = f"faults_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{name}"')
    scratch = spx_live_db.dsn_for(_settings(dsn), name)
    setup = DatabasePool(scratch, min_size=1, max_size=1)
    await setup.initialize()
    await run_migrations(setup)
    await setup.close()
    if statement_timeout:
        await admin.execute(
            f"ALTER DATABASE \"{name}\" SET statement_timeout = '{statement_timeout}'"
        )
    db = DatabasePool(scratch, min_size=1, max_size=2, command_timeout=command_timeout)
    await db.initialize()
    locker = await asyncpg.connect(scratch)
    try:
        yield name, admin, db, locker
    finally:
        await locker.close()
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()


@contextlib.asynccontextmanager
async def inserts_blocked(locker):
    """Hold a SHARE lock: reads proceed, every INSERT waits until it is released."""
    tx = locker.transaction()
    await tx.start()
    await locker.execute("LOCK TABLE broker_order_intents IN SHARE MODE")
    try:
        yield
    finally:
        await tx.rollback()


async def waiting_insert_pid(admin, name: str) -> int:
    for _ in range(200):
        pid = await admin.fetchval(
            "SELECT pid FROM pg_stat_activity WHERE datname = $1 AND wait_event_type = 'Lock'"
            " AND query ILIKE '%INSERT INTO broker_order_intents%'",
            name,
        )
        if pid:
            return pid
        await asyncio.sleep(0.02)
    raise AssertionError("the intent INSERT never reached the lock")


async def intent_count(db) -> int:
    return await db.pool.fetchval("SELECT count(*) FROM broker_order_intents")


def places(broker):
    return [order for event, order in broker.events if event == "place"]


@pytest.mark.asyncio
async def test_backend_killed_mid_insert_halts_before_any_order():
    async with scratch_db() as (name, admin, db, locker):
        broker = Broker({})
        om = _manager(broker, OrderIntentQueries(db))
        async with inserts_blocked(locker):
            attempt = asyncio.create_task(om.execute_single_attempt(_live_candidate(), 3.75))
            pid = await waiting_insert_pid(admin, name)
            assert await admin.fetchval("SELECT pg_terminate_backend($1)", pid)
            with pytest.raises(IntentPersistenceError, match="entry intent creation") as caught:
                await attempt

        print("connection-killed cause:", type(caught.value.__cause__).__name__)
        assert places(broker) == []
        assert await intent_count(db) == 0  # it never committed; the bot cannot know that


@pytest.mark.asyncio
async def test_asyncpg_command_timeout_on_the_insert_halts_before_any_order():
    # DatabasePool's client-side timeout (10 s in production) cancels a slow INSERT.
    async with scratch_db(command_timeout=0.5) as (_, _admin, db, locker):
        broker = Broker({})
        om = _manager(broker, OrderIntentQueries(db))
        async with inserts_blocked(locker):
            with pytest.raises(IntentPersistenceError) as caught:
                await om.execute_single_attempt(_live_candidate(), 3.75)

        print("command-timeout cause:", type(caught.value.__cause__).__name__)
        assert isinstance(caught.value.__cause__, (asyncio.TimeoutError, TimeoutError))
        assert places(broker) == []
        assert await intent_count(db) == 0


@pytest.mark.asyncio
async def test_server_statement_timeout_is_definitive_and_the_retry_trades_normally():
    async with scratch_db(statement_timeout="300ms") as (_, _admin, db, locker):
        broker = Broker({})
        broker.script("ORD1", working=[filled_order()])
        om = _manager(broker, OrderIntentQueries(db))
        async with inserts_blocked(locker):
            with pytest.raises(QueryCanceledError):
                await om.execute_single_attempt(_live_candidate(), 3.75)
        assert places(broker) == []
        assert await intent_count(db) == 0

        fill = await om.execute_single_attempt(_live_candidate(), 3.75)

        assert fill is not None and places(broker) == ["ORD1"]
        assert await intent_count(db) == 1


@pytest.mark.asyncio
async def test_real_unique_indexes_block_a_second_active_intent():
    async with scratch_db() as (_, _admin, db, _locker):
        queries = OrderIntentQueries(db)
        await db.pool.execute(TRADE, DAY)
        await queries.create_intent(
            underlying="SPX", trade_date=DAY, side="ENTRY", limit_price=3.75, quantity=1,
            order_spec={}, candidate_snapshot={},
        )
        await queries.create_intent(
            underlying="SPX", trade_date=DAY, side="EXIT", limit_price=1.85, quantity=1,
            order_spec={}, candidate_snapshot={}, trade_id=100000,
        )

        entry_broker, exit_broker = Broker({}), Broker(FLY)
        with pytest.raises(UniqueViolationError):
            await _manager(entry_broker, queries).execute_single_attempt(_live_candidate(), 3.75)
        with pytest.raises(AmbiguousOrderError, match="active exit intent already exists"):
            await _manager(exit_broker, queries).execute_exit(
                _live_candidate(), 1.97, trade_id=100000
            )

        assert places(entry_broker) == places(exit_broker) == []
        assert await intent_count(db) == 2
