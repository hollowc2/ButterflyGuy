"""Real TimescaleDB smoke test for migrations and critical risk and intent reads."""

import datetime as dt
import json
import os
import runpy
import uuid

import asyncpg
import pytest

from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import MIGRATIONS_DIR, run_migrations
from butterfly_guy.db.queries import OrderIntentQueries, RiskQueries, TradeQueries
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


@pytest.mark.asyncio
async def test_intent_insert_carries_its_before_submit_evidence_atomically():
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
        queries = OrderIntentQueries(db)
        today = dt.date(2026, 11, 19)
        intent = dict(
            underlying="SPX", trade_date=today, side="ENTRY", limit_price=3.75, quantity=1,
            order_spec={}, candidate_snapshot={
                "center_strike": 7475, "execution_observations": [{"phase": "before_submit"}],
            },
        )
        intent_id = await queries.create_intent(**intent)
        await queries.append_execution_observation(intent_id, {"phase": "broker_acknowledged"})
        phases = await db.pool.fetchval(
            "SELECT jsonb_path_query_array(candidate_snapshot, '$.execution_observations[*].phase')"
            " FROM broker_order_intents WHERE id = $1",
            intent_id,
        )
        assert json.loads(phases) == ["before_submit", "broker_acknowledged"]

        # A failed INSERT commits nothing: no second active intent and no evidence row.
        with pytest.raises(asyncpg.exceptions.UniqueViolationError):
            await queries.create_intent(**intent)
        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await queries.create_intent(**{**intent, "side": "EXIT", "trade_id": 999_999})
        assert await db.pool.fetchval("SELECT count(*) FROM broker_order_intents") == 1
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()


PROVISIONAL_TRADE = """
INSERT INTO butterfly_trades (
    trade_date, direction, wing_width, center_strike, lower_strike, upper_strike,
    entry_price, entry_time, exit_price, exit_time, pnl, quantity, status, underlying, metadata
) VALUES ($1, 'CALL', 40, 7475, 7435, 7515, 3.75, NOW(), 0, NOW(), $2, 1, 'CLOSED', 'SPX',
          $3::jsonb) RETURNING id
"""


@pytest.mark.asyncio
async def test_provisional_true_up_corrects_the_trade_and_its_risk_day_atomically():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    name = f"trueup_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{name}"')
    db = DatabasePool(spx_live_db.dsn_for(_settings(dsn), name), min_size=1, max_size=2)
    try:
        await db.initialize()
        await run_migrations(db)
        pool, trades = db.pool, TradeQueries(db)

        async def provisional(day, net):
            meta = json.dumps({"settlement_provisional": True, "net_pnl_dollars": net})
            return await pool.fetchval(PROVISIONAL_TRADE, day, net / 100, meta)

        async def risk(day):
            return await pool.fetchrow(
                "SELECT realized_pnl, halted, max_loss_hit FROM daily_risk_state"
                " WHERE trade_date = $1 AND underlying = 'SPX'", day,
            )

        async def finalize(trade_id, posted, provisional_net):
            return await trades.finalize_provisional_settlement(
                trade_id, 0.0, posted / 100,
                {"settlement_provisional": False, "net_pnl_dollars": posted,
                 "provisional_net_pnl_dollars": provisional_net},
                max_daily_loss=500.0,
            )

        # The day already holds the provisional P&L; Schwab posts 21 cents worse.
        day = dt.date(2026, 11, 19)
        trade = await provisional(day, -379.79)
        await pool.execute(
            "INSERT INTO daily_risk_state (trade_date, underlying, realized_pnl)"
            " VALUES ($1, 'SPX', -379.79)", day,
        )
        assert await finalize(trade, -380.0, -379.79) is True
        assert (float((await risk(day))["realized_pnl"]), (await risk(day))["halted"]) == (
            -380.0, False,
        )
        pnl = await pool.fetchval("SELECT pnl FROM butterfly_trades WHERE id = $1", trade)
        assert float(pnl) == pytest.approx(-3.80)
        # A second true-up corrects nothing twice.
        assert await finalize(trade, -380.0, -379.79) is False
        assert float((await risk(day))["realized_pnl"]) == -380.0

        # Crossing the daily loss limit halts that day, as record_pnl did.
        day2 = dt.date(2026, 11, 18)
        trade2 = await provisional(day2, -300.0)
        await pool.execute(
            "INSERT INTO daily_risk_state (trade_date, underlying, realized_pnl)"
            " VALUES ($1, 'SPX', -300.0)", day2,
        )
        assert await finalize(trade2, -550.0, -300.0) is True
        row = await risk(day2)
        assert (float(row["realized_pnl"]), row["halted"], row["max_loss_hit"]) == (
            -550.0, True, True,
        )

        # No risk row for the day yet: the delta creates it.
        day3 = dt.date(2026, 11, 17)
        trade3 = await provisional(day3, 100.0)
        assert await finalize(trade3, 150.0, 100.0) is True
        row = await risk(day3)
        assert (float(row["realized_pnl"]), row["halted"]) == (50.0, False)

        # If the risk write fails, the trade correction rolls back with it.
        day4 = dt.date(2026, 11, 16)
        trade4 = await provisional(day4, 0.0)
        with pytest.raises(asyncpg.exceptions.NumericValueOutOfRangeError):
            await finalize(trade4, 10_000_000.0, 0.0)  # past NUMERIC(10,4)
        assert await pool.fetchval(
            "SELECT metadata->>'settlement_provisional' FROM butterfly_trades WHERE id = $1",
            trade4,
        ) == "true"
        assert await risk(day4) is None
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()


@pytest.mark.asyncio
async def test_settle_tool_closes_the_row_and_books_risk_in_one_transaction():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    tool = runpy.run_path("tools/spx_live_settle_expired.py", run_name="spx_live_settle_expired")
    name = f"settle_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{name}"')
    db = DatabasePool(spx_live_db.dsn_for(_settings(dsn), name), min_size=1, max_size=2)
    try:
        await db.initialize()
        await run_migrations(db)
        pool = db.pool

        async def open_trade(day):
            return await pool.fetchval(TRADE, day, "OPEN", "SPX")

        async def apply(trade_id, day, net):
            close_at = dt.datetime(day.year, day.month, day.day, 21, 0, tzinfo=dt.timezone.utc)
            await tool["apply_settlement"](
                db, (trade_id, 0.0, close_at, "cash_settled", net / 100, 4.93),
                {"net_pnl_dollars": net, "settlement_provisional": True}, day, "SPX",
            )

        async def state(trade_id, day):
            status = await pool.fetchval(
                "SELECT status FROM butterfly_trades WHERE id = $1", trade_id
            )
            pnl = await pool.fetchval(
                "SELECT realized_pnl FROM daily_risk_state"
                " WHERE trade_date = $1 AND underlying = 'SPX'", day,
            )
            return status, None if pnl is None else float(pnl)

        day = dt.date(2026, 11, 19)
        trade = await open_trade(day)
        await apply(trade, day, -379.79)
        assert await state(trade, day) == ("CLOSED", -379.79)
        with pytest.raises(tool["SettleRefusedError"], match="no longer OPEN"):
            await apply(trade, day, -379.79)
        assert await state(trade, day) == ("CLOSED", -379.79)

        # The risk write fails, so the close rolls back with it: the row stays OPEN.
        day2 = dt.date(2026, 11, 18)
        trade2 = await open_trade(day2)
        with pytest.raises(asyncpg.exceptions.NumericValueOutOfRangeError):
            await apply(trade2, day2, 10_000_000.0)  # past NUMERIC(10,4)
        assert await state(trade2, day2) == ("OPEN", None)
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()
