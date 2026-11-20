"""Real TimescaleDB smoke test for migrations and critical risk and intent reads."""

import datetime as dt
import os
import uuid

import asyncpg
import pytest

from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import MIGRATIONS_DIR, run_migrations
from butterfly_guy.db.queries import OrderIntentQueries, RiskQueries
from butterfly_guy.scripts import spx_live_db
from tests.integration.test_spx_live_db import _settings


@pytest.mark.asyncio
async def test_migrations_and_weekly_pnl_query():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    db = DatabasePool(dsn, min_size=1, max_size=2)
    await db.initialize()
    try:
        await run_migrations(db)
        applied = await db.pool.fetchval("SELECT count(*) FROM schema_migrations")
        assert applied == len(list(MIGRATIONS_DIR.glob("*.sql")))
        # 011 is idempotent: re-applying it is a no-op.
        await db.pool.execute((MIGRATIONS_DIR / "011_snapshot_timing.sql").read_text())
        timing_columns = await db.pool.fetchval(
            "SELECT count(*) FROM information_schema.columns WHERE "
            "(table_name, column_name) IN (('option_chain_snapshots', 'quote_event_ts'), "
            "('option_chain_snapshots', 'quote_age_s'), ('spot_prices', 'event_ts'), "
            "('spot_prices', 'age_s'), ('chain_snapshot_meta', 'scheduled_at'))"
        )
        assert timing_columns == 5

        await db.pool.execute(
            """
            INSERT INTO butterfly_trades (
                trade_date, direction, wing_width, center_strike, lower_strike,
                upper_strike, entry_price, entry_time, pnl, quantity, status, underlying
            ) VALUES ($1, 'CALL', 5, 6000, 5995, 6005, 1, NOW(), -1.25, 2, 'CLOSED', 'SPX')
            """,
            dt.date(2026, 7, 14),
        )

        risk_queries = RiskQueries(db)
        assert await risk_queries.get_weekly_pnl("SPX", dt.date(2026, 7, 15)) == -250.0
        assert await risk_queries.get_recent_closed_pnls("SPX", 1) == [-250.0]
    finally:
        await db.close()


TRADE = """
INSERT INTO butterfly_trades (
    trade_date, direction, wing_width, center_strike, lower_strike, upper_strike,
    entry_price, entry_time, quantity, status, underlying
) VALUES ($1, 'CALL', 40, 7475, 7435, 7515, 3.75, NOW(), 1, $2, $3) RETURNING id
"""
INTENT = """
INSERT INTO broker_order_intents (
    underlying, trade_date, trade_id, side, status, broker_order_id
) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
"""


@pytest.mark.asyncio
async def test_startup_exit_intent_read_spans_dates_for_open_trades_only():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    name = f"intents_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{name}"')
    db = DatabasePool(spx_live_db.dsn_for(_settings(dsn), name), min_size=1, max_size=2)
    try:
        await db.initialize()
        await run_migrations(db)
        pool = db.pool
        today = dt.date(2026, 11, 19)
        day = dt.timedelta(days=1)
        prior = await pool.fetchval(TRADE, today - day, "OPEN", "SPX")
        current = await pool.fetchval(TRADE, today, "OPEN", "SPX")
        closed = await pool.fetchval(TRADE, today, "CLOSED", "SPX")
        ndx = await pool.fetchval(TRADE, today, "OPEN", "NDX")
        # Held by the active-exit index (per trade, any date): both must be read.
        before = await pool.fetchval(INTENT, "SPX", today - day, prior, "EXIT", "SUBMITTING", None)
        after = await pool.fetchval(
            INTENT, "SPX", today + day, current, "EXIT", "CANCEL_REQUESTED", "55"
        )
        # Final history, a CLOSED trade's, another underlying's, and entries: never read.
        await pool.fetchval(INTENT, "SPX", today - 2 * day, prior, "EXIT", "CANCELED", "50")
        await pool.fetchval(INTENT, "SPX", today - day, current, "EXIT", "FILLED", "51")
        same_day = await pool.fetchval(INTENT, "SPX", today, closed, "EXIT", "SUBMITTING", None)
        await pool.fetchval(INTENT, "NDX", today, ndx, "EXIT", "SUBMITTING", None)
        await pool.fetchval(INTENT, "SPX", today - day, None, "ENTRY", "UNKNOWN_ABORTED", None)
        await pool.fetchval(INTENT, "SPX", today - 2 * day, prior, "ENTRY", "REPLACED", "40")

        queries = OrderIntentQueries(db)
        rows = await queries.active_exit_intents_for_trades("SPX", [prior, current, ndx])
        assert [row["id"] for row in rows] == [before, after]
        assert await queries.active_exit_intents_for_trades("SPX", []) == []
        # The date-scoped read keeps its meaning.
        assert [row["id"] for row in await queries.intents_for_day("SPX", today)] == [same_day]
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()
