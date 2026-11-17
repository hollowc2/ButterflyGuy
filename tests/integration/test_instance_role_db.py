"""Real TimescaleDB test of the live instance-role database check."""

import datetime as dt
import json
import os
import uuid

import asyncpg
import pytest

from butterfly_guy.core.instance_role import InstanceRoleError, check_database
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations

INSERT_TRADE = """
INSERT INTO butterfly_trades (
    trade_date, direction, wing_width, center_strike, lower_strike, upper_strike,
    entry_price, entry_time, quantity, status, underlying, metadata
) VALUES ($1, 'PUT', 20, 6000, 5980, 6020, 2, NOW(), 1, $2, 'SPX', $3::jsonb)
"""


@pytest.mark.asyncio
async def test_live_check_on_a_real_scratch_database():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    name = f"role_guard_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{name}"')
    db = DatabasePool(dsn.rsplit("/", 1)[0] + f"/{name}", min_size=1, max_size=2)
    try:
        await db.initialize()
        # Brand-new database: no trades table yet, so nothing to refuse.
        await check_database(db.pool, "live")

        await run_migrations(db)
        today = dt.date(2026, 11, 18)
        await db.pool.execute(INSERT_TRADE, today, "CLOSED", json.dumps({}))
        await check_database(db.pool, "live")  # live-only history is fine

        await db.pool.execute(
            INSERT_TRADE, today, "CLOSED", json.dumps({"paper_fill_model": "mark_v1"})
        )
        with pytest.raises(InstanceRoleError, match="holds 1 paper trade"):
            await check_database(db.pool, "live")
        await check_database(db.pool, "live_rehearsal")  # rehearsal DBs hold paper rows
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
        await admin.close()
