"""Real TimescaleDB smoke test for migrations and critical risk reads."""

import datetime as dt
import os

import pytest

from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import MIGRATIONS_DIR, run_migrations
from butterfly_guy.db.queries import RiskQueries


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
