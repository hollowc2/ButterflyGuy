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

        # Operational kill is asset-scoped, survives a second call, and never
        # overwrites P&L, trade counts, or a real loss-limit flag.
        date = dt.date(2026, 10, 20)
        await risk_queries.get_or_create(date, "NDX")
        await risk_queries.get_or_create(date, "SPX")
        await risk_queries.increment_trade_count(date, "SPX")
        await risk_queries.update_pnl(date, -123.0, "SPX")
        for _ in range(2):
            await risk_queries.halt_entries(date, "SPX", "smoke-test")
        state = await risk_queries.get_or_create(date, "SPX")
        assert state["halted"] is True
        assert state["max_loss_hit"] is False
        assert state["trade_count"] == 1
        assert state["realized_pnl"] == -123.0
        assert (await risk_queries.get_or_create(date, "NDX"))["halted"] is False
        assert await db.pool.fetchval(
            "SELECT COUNT(*) FROM decision_log WHERE event_type = 'live_entry_halted' "
            "AND underlying = 'SPX' AND data->>'reason' = 'smoke-test'"
        ) == 2
    finally:
        await db.close()
