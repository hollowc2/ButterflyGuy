"""Real TimescaleDB: the live bot's queries never see the paper bot's rows, and vice versa.

The hard blocks of a shared database (docs/operations/concurrent-paper-live-spx-phase0.md §2)
are the runtime queries below. With one database per bot they cannot cross.
"""

import datetime as dt
import json
import os
import uuid

import asyncpg
import pytest

from butterfly_guy.core.instance_role import InstanceRoleError, check_database
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations
from butterfly_guy.db.queries import OrderIntentQueries, RiskQueries, TradeQueries
from butterfly_guy.scripts import spx_live_db
from tests.integration.test_spx_live_db import _settings

DAY = dt.date(2026, 11, 18)
OPEN_PAPER_TRADE = """
INSERT INTO butterfly_trades (
    trade_date, direction, wing_width, center_strike, lower_strike, upper_strike,
    entry_price, entry_time, quantity, status, underlying, metadata
) VALUES ($1, 'CALL', 20, 7450, 7430, 7470, 3.0, NOW(), 1, $2, 'SPX', $3::jsonb)
"""


@pytest.mark.asyncio
async def test_live_runtime_queries_never_see_paper_rows():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    base = _settings(dsn)
    suffix = uuid.uuid4().hex[:8]
    paper_name = f"paper_{suffix}"
    live_name = f"butterfly_guy_spx_live_iso_{suffix}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{paper_name}"')
    paper = DatabasePool(spx_live_db.dsn_for(base, paper_name), min_size=1, max_size=2)
    live = DatabasePool(spx_live_db.dsn_for(base, live_name), min_size=1, max_size=2)
    try:
        await paper.initialize()
        await run_migrations(paper)
        paper_meta = json.dumps({"paper_fill_model": "mark_v1"})
        await paper.pool.execute(OPEN_PAPER_TRADE, DAY, "OPEN", paper_meta)
        await paper.pool.execute(
            OPEN_PAPER_TRADE.replace("NOW()", "NOW() - INTERVAL '1 day'"),
            DAY - dt.timedelta(days=1), "CLOSED", paper_meta,
        )
        await paper.pool.execute(
            "UPDATE butterfly_trades SET pnl = -15 WHERE status = 'CLOSED'"
        )  # -$1,500: would trip live's weekly halt if shared
        paper_risk = RiskQueries(paper)
        await paper_risk.get_or_create(DAY, "SPX")
        await paper_risk.increment_trade_count(DAY, "SPX")
        await paper_risk.set_halted(DAY, "SPX")

        report = await spx_live_db.bootstrap(base, live_name, paper_name, [])
        assert report["check"]["ok"] is True
        await live.initialize()
        await check_database(live.pool, "live")  # startup guard passes

        # Startup recovery and the reconciler's input: no paper trade to adopt or mismatch.
        assert await TradeQueries(live).get_open_trades("SPX") == []
        assert await TradeQueries(live).get_trades_for_date(DAY, "SPX") == []
        assert await OrderIntentQueries(live).active_intents("SPX", DAY) == []
        # Risk: paper's count, halt and -$1,500 week do not exist for live.
        live_risk = RiskQueries(live)
        state = await live_risk.get_or_create(DAY, "SPX")
        assert (state["trade_count"], state["halted"]) == (0, False)
        assert await live_risk.get_weekly_pnl("SPX", DAY) == 0.0
        assert await live_risk.get_recent_closed_pnls("SPX", 10) == []
        # One OPEN trade per day each: the live entry is not blocked by paper's open row.
        await live.pool.execute(OPEN_PAPER_TRADE, DAY, "OPEN", json.dumps({}))
        live_open = await TradeQueries(live).get_open_trades("SPX")
        assert [row["id"] for row in live_open] == [100_000]

        # And paper never sees live: still exactly its own open trade.
        assert len(await TradeQueries(paper).get_open_trades("SPX")) == 1
        assert (await paper_risk.get_or_create(DAY, "SPX"))["halted"] is True

        # A paper row reaching the live DB makes the next live start refuse.
        await live.pool.execute(OPEN_PAPER_TRADE, DAY - dt.timedelta(days=2), "CLOSED",
                                paper_meta)
        with pytest.raises(InstanceRoleError):
            await check_database(live.pool, "live")
    finally:
        await paper.close()
        await live.close()
        for name in (live_name, paper_name):
            await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()
