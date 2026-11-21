"""Real TimescaleDB test of the live SPX database bootstrap, seed and gate."""

import asyncio
import datetime as dt
import json
import os
import uuid

import asyncpg
import pytest

from butterfly_guy.core.config import DatabaseSettings
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations
from butterfly_guy.reports import spx_paired
from butterfly_guy.scripts import spx_live_db

DAY = dt.date(2026, 11, 16)
ENTRY = dt.datetime(2026, 11, 16, 15, 0, tzinfo=dt.timezone.utc)
EXIT = dt.datetime(2026, 11, 16, 20, 23, tzinfo=dt.timezone.utc)

TRADE = """
INSERT INTO butterfly_trades (
    id, trade_date, direction, wing_width, center_strike, lower_strike, upper_strike,
    entry_price, entry_time, exit_price, exit_time, pnl, quantity, status, underlying, metadata
) VALUES ($1, $2, 'PUT', 20, 7440, 7420, 7460, 2.0, $3, 1.3, $4, -0.7, 1, $5, 'SPX', $6::jsonb)
"""
INTENT = """
INSERT INTO broker_order_intents (underlying, trade_date, trade_id, side, status, broker_order_id)
VALUES ('SPX', $1, $2, $3, 'FILLED', $4)
"""
LEG = """
INSERT INTO monitoring_leg_quotes (ts, trade_id, underlying, expiration, strike, option_type, mark)
VALUES ($1, $2, 'SPX', $3, 7440, 'PUT', 1.0)
"""


def _settings(dsn: str) -> DatabaseSettings:
    rest = dsn.split("://", 1)[1]
    creds, hostpart = rest.rsplit("@", 1)
    user, password = creds.split(":", 1)
    host, port = hostpart.split("/", 1)[0].split(":")
    return DatabaseSettings(host=host, port=int(port), user=user, password=password)


async def _seed_source(base: DatabaseSettings, name: str) -> None:
    db = DatabasePool(spx_live_db.dsn_for(base, name), min_size=1, max_size=2)
    await db.initialize()
    try:
        await run_migrations(db)
        pool = db.pool
        # 415-like live trade with broker orders, leg quotes and decisions.
        await pool.execute(TRADE, 415, DAY, ENTRY, EXIT, "CLOSED", json.dumps({}))
        await pool.execute(INTENT, DAY, 415, "ENTRY", "b-1")
        await pool.execute(INTENT, DAY, 415, "EXIT", "b-2")
        for minute in range(3):
            await pool.execute(LEG, ENTRY + dt.timedelta(minutes=minute), 415, DAY)
        await pool.execute(
            "INSERT INTO decision_log (ts, event_type, data, underlying) "
            "VALUES ($1, 'entry_filled', '{}', 'SPX'), ($2, 'unrelated_day', '{}', 'SPX')",
            ENTRY,
            ENTRY - dt.timedelta(days=2),
        )
        # A paper trade and an unrelated legacy trade that must never be copied.
        paper = json.dumps({"paper_fill_model": "mark_v1"})
        await pool.execute(TRADE, 417, DAY + dt.timedelta(days=1), ENTRY, EXIT, "CLOSED", paper)
        await pool.execute(TRADE, 300, DAY, ENTRY, EXIT, "CLOSED", json.dumps({}))
        for offset in range(10):
            date = DAY - dt.timedelta(days=offset)
            for symbol, close in (("SPX", 7400 + offset), ("$VIX", 17 + offset / 10)):
                await pool.execute(
                    "INSERT INTO daily_bars (date, underlying, close) VALUES ($1, $2, $3)",
                    date,
                    symbol,
                    close,
                )
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_bootstrap_seed_and_check_on_real_scratch_databases():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    base = _settings(dsn)
    suffix = uuid.uuid4().hex[:8]
    source = f"paper_src_{suffix}"
    target = f"butterfly_guy_spx_live_test_{suffix}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{source}"')
    try:
        await _seed_source(base, source)

        with pytest.raises(spx_live_db.LiveDbError, match="paper trade"):
            await spx_live_db.bootstrap(base, target, source, [417])
        with pytest.raises(spx_live_db.LiveDbError, match="no broker order"):
            await spx_live_db.bootstrap(base, target, source, [300])
        assert not await admin.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target)

        report = await spx_live_db.bootstrap(base, target, source, [415])
        assert report["created"] is True  # the refused attempts wrote nothing
        assert report["copied_trades"][415] == {
            "butterfly_trades": 1,
            "broker_order_intents": 2,
            "monitoring_leg_quotes": 3,
            "post_exit_leg_quotes": 0,
            "decision_log": 1,
        }
        assert report["daily_bars_copied"] == 20
        assert report["check"] == {
            "schema_at_head": True,
            "open_spx_trades": 0,
            "nonterminal_spx_intents": 0,
            "unlinked_filled_spx_entries": 0,
            "paper_trades": 0,
            "ok": True,
        }

        # Idempotent: nothing is copied twice.
        again = await spx_live_db.bootstrap(base, target, source, [415])
        assert again["copied_trades"][415] == {}
        assert again["daily_bars_copied"] == 0

        conn = await asyncpg.connect(spx_live_db.dsn_for(base, target))
        try:
            assert await conn.fetchval("SELECT count(*) FROM butterfly_trades") == 1
            assert await conn.fetchval("SELECT nextval('butterfly_trades_id_seq')") == 100_000
            assert (
                await conn.fetchval("SELECT nextval('broker_order_intents_id_seq')") == 100_000
            )
            policies = {
                r["hypertable_name"]
                for r in await conn.fetch(
                    "SELECT hypertable_name FROM timescaledb_information.jobs "
                    "WHERE proc_name = 'policy_compression'"
                )
            }
            assert policies == set(spx_live_db.COMPRESSION)
            # 415's weekly-loss contribution is visible to the live risk engine.
            weekly = await conn.fetchval(
                "SELECT SUM(pnl * 100 * quantity) FROM butterfly_trades WHERE status = 'CLOSED'"
            )
            assert weekly == -70

            # The paired report counts the trade's distinct monitor polls and their spacing.
            trades, _ = await spx_paired.fetch_side(conn, DAY)
            assert [(t["id"], t["monitor_polls"], float(t["monitor_median_gap_s"]))
                    for t in trades] == [(415, 3, 60.0)]

            # seed-daily-bars is incremental.
            source_conn = await spx_live_db.connect_read_only(base, source)
            try:
                writer = await asyncpg.connect(spx_live_db.dsn_for(base, source))
                await writer.execute(
                    "INSERT INTO daily_bars (date, underlying, close) VALUES ($1, 'SPX', 7500)",
                    DAY + dt.timedelta(days=1),
                )
                await writer.close()
                assert await spx_live_db.seed_daily_bars(source_conn, conn) == 1
                with pytest.raises(asyncpg.ReadOnlySQLTransactionError):
                    await source_conn.execute("DELETE FROM daily_bars")
            finally:
                await source_conn.close()

            # The gate fails closed on an open trade and on a paper row.
            await conn.execute(
                TRADE, 100_001, DAY, ENTRY, None, "OPEN", json.dumps({"paper_fill_model": "x"})
            )
            result = await spx_live_db.check(conn)
            assert result["ok"] is False
            assert result["open_spx_trades"] == 1
            assert result["paper_trades"] == 1
        finally:
            await conn.close()
    finally:
        await admin.execute(f'DROP DATABASE IF EXISTS "{target}" WITH (FORCE)')
        await admin.execute(f'DROP DATABASE IF EXISTS "{source}" WITH (FORCE)')
        await admin.close()


def test_target_name_never_allows_the_paper_database():
    for name in ("butterfly_guy", "butterfly_guy_spx_candidate", "postgres", "spx_live"):
        with pytest.raises(spx_live_db.LiveDbError, match="refusing to write"):
            spx_live_db.target_name(name)
    assert spx_live_db.target_name("butterfly_guy_spx_live") == "butterfly_guy_spx_live"
    assert (
        spx_live_db.target_name("butterfly_guy_spx_live_rehearsal")
        == "butterfly_guy_spx_live_rehearsal"
    )


@pytest.mark.asyncio
async def test_halt_entries_blocks_the_risk_gate_and_keeps_the_day_counters():
    """Review 2026-11-20 finding 2: activation's rollback blocks entries, not exits."""
    from unittest.mock import patch

    from butterfly_guy.core.config import RiskSettings
    from butterfly_guy.db.queries import RiskQueries
    from butterfly_guy.risk.risk_engine import RiskEngine

    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    base = _settings(dsn)
    target = f"butterfly_guy_spx_live_test_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{target}"')
    db = DatabasePool(spx_live_db.dsn_for(base, target), min_size=1, max_size=2)
    try:
        await db.initialize()
        await run_migrations(db)
        await db.pool.execute(
            "INSERT INTO daily_risk_state (trade_date, underlying, trade_count, realized_pnl) "
            "VALUES ($1, 'SPX', 1, -12.5)",
            DAY,
        )
        conn = await asyncpg.connect(spx_live_db.dsn_for(base, target))
        try:
            assert (await spx_live_db.halt_entries(conn, DAY))["ok"] is True
            # No row yet for the next day: created halted.
            assert (await spx_live_db.halt_entries(conn, DAY + dt.timedelta(days=1)))["ok"]
            # Idempotent.
            assert (await spx_live_db.halt_entries(conn, DAY))["ok"] is True
        finally:
            await conn.close()
        row = await db.pool.fetchrow(
            "SELECT * FROM daily_risk_state WHERE trade_date = $1 AND underlying = 'SPX'", DAY
        )
        assert row["halted"] is True and row["trade_count"] == 1
        assert float(row["realized_pnl"]) == -12.5 and row["max_loss_hit"] is False

        engine = RiskEngine(RiskSettings(), RiskQueries(db), underlying="SPX")
        with patch("butterfly_guy.risk.risk_engine.is_trading_day", return_value=True), \
             patch("butterfly_guy.risk.risk_engine.is_market_open", return_value=True):
            assert await engine.can_trade(trade_date=DAY) == (False, "trading_halted")
        # A restart's syncs never clear it.
        await engine.sync_trade_count(0, DAY)
        await engine.sync_realized_pnl(0.0, DAY)
        assert await db.pool.fetchval(
            "SELECT halted FROM daily_risk_state WHERE trade_date = $1 AND underlying = 'SPX'",
            DAY,
        ) is True
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{target}" WITH (FORCE)')
        await admin.close()


@pytest.mark.asyncio
async def test_halt_entries_refuses_the_paper_database(capsys, monkeypatch):
    from butterfly_guy.core.config import AppConfig

    # Never load the real .env into the test process.
    monkeypatch.setattr(spx_live_db, "load_config", lambda _path: AppConfig())
    code = await spx_live_db._main(
        ["halt-entries", "--db", "butterfly_guy", "--date", "2026-11-20"]
    )
    assert code == 2
    assert "refusing to write" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_halt_entries_drains_an_admitted_entry_before_reporting_ok():
    """Codex review of #103: an entry admitted under its lock must finish first."""
    from butterfly_guy.db.queries import entry_lock_key

    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    base = _settings(dsn)
    target = f"butterfly_guy_spx_live_test_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{target}"')
    db = DatabasePool(spx_live_db.dsn_for(base, target), min_size=1, max_size=2)
    try:
        await db.initialize()
        await run_migrations(db)
        # The bot's admitted attempt: the same session lock TradeService takes.
        bot = await asyncpg.connect(spx_live_db.dsn_for(base, target))
        key = entry_lock_key("SPX", DAY)
        assert await bot.fetchval("SELECT pg_try_advisory_lock(hashtext($1)::bigint)", key)
        tool = await asyncpg.connect(spx_live_db.dsn_for(base, target))
        try:
            # Still in flight past the drain timeout: halted, not drained.
            stuck = await spx_live_db.halt_entries(tool, DAY, drain_timeout_s=0.3)
            assert stuck == {
                "trade_date": DAY, "halted": True, "entries_drained": False, "ok": False,
            }

            async def finish_entry() -> None:
                await asyncio.sleep(0.3)
                await bot.execute("SELECT pg_advisory_unlock(hashtext($1)::bigint)", key)

            finishing = asyncio.create_task(finish_entry())
            drained = await spx_live_db.halt_entries(tool, DAY, drain_timeout_s=5)
            await finishing
            assert drained["ok"] is True and drained["entries_drained"] is True
            # The tool released the lock again: the bot's next attempt can take it
            # (and then sees the halt in can_trade).
            assert await bot.fetchval("SELECT pg_try_advisory_lock(hashtext($1)::bigint)", key)
        finally:
            await tool.close()
            await bot.close()
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{target}" WITH (FORCE)')
        await admin.close()


@pytest.mark.asyncio
async def test_check_refuses_a_filled_entry_that_never_got_its_trade_row():
    """Codex review of #103: open at the broker, flat in the DB."""
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    base = _settings(dsn)
    target = f"butterfly_guy_spx_live_test_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    await admin.execute(f'CREATE DATABASE "{target}"')
    db = DatabasePool(spx_live_db.dsn_for(base, target), min_size=1, max_size=2)
    try:
        await db.initialize()
        await run_migrations(db)
        conn = await asyncpg.connect(spx_live_db.dsn_for(base, target))
        try:
            assert (await spx_live_db.check(conn))["ok"] is True
            await conn.execute(
                "INSERT INTO broker_order_intents "
                "(underlying, trade_date, side, status, broker_order_id) "
                "VALUES ('SPX', $1, 'ENTRY', 'FILLED', 'b-9')",
                DAY,
            )
            result = await spx_live_db.check(conn)
            assert result["ok"] is False and result["unlinked_filled_spx_entries"] == 1
        finally:
            await conn.close()
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{target}" WITH (FORCE)')
        await admin.close()
