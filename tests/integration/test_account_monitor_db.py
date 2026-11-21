"""Exercise account-monitor SQL and lock coordination in a disposable CI database."""

import asyncio
import datetime as dt
import json
import os
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import asyncpg
import pytest

from butterfly_guy.core.config import AccountMonitorSettings
from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import MIGRATIONS_DIR
from butterfly_guy.scripts.spx_live_db import dsn_for
from butterfly_guy.services.account_monitor import AccountMonitor
from tests.integration.test_spx_live_db import _settings


async def test_account_monitor_state_lock_and_restart_with_postgres(monkeypatch):
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("CI_DATABASE_URL is only set by the real-DB workflow")

    name = f"monitor_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(dsn)
    db = DatabasePool(dsn_for(_settings(dsn), name), min_size=1, max_size=3)
    try:
        await admin.execute(f'CREATE DATABASE "{name}"')
        await db.initialize()
        migration = (MIGRATIONS_DIR / "013_account_monitor.sql").read_text()
        await db.pool.execute(migration)
        await db.pool.execute(migration)  # idempotent
        await db.pool.execute(
            "CREATE TABLE butterfly_trades "
            "(id SERIAL PRIMARY KEY, trade_date DATE, status TEXT, metadata JSONB)"
        )
        await db.pool.execute(
            "INSERT INTO butterfly_trades (trade_date, status, metadata) "
            "VALUES ('2026-11-20', 'CLOSED', '{}')"
        )
        broker = SimpleNamespace(
            settings=SimpleNamespace(account_id="private-test-account"),
            get_account_snapshot=AsyncMock(return_value={
                "securitiesAccount": {"type": "MARGIN", "currentBalances": {"equity": 1900}},
            }),
        )
        telegram = AsyncMock(return_value=True)
        monkeypatch.setattr("butterfly_guy.services.account_monitor.send_checked_async", telegram)
        discord = SimpleNamespace(send_checked=AsyncMock(return_value=False))
        first = AccountMonitor(db, broker, AccountMonitorSettings(), discord)
        other = AccountMonitor(db, broker, AccountMonitorSettings(), discord)
        now = dt.datetime(2026, 11, 20, 16, 15, tzinfo=EASTERN)

        # Hold the lock on one connection; another runtime must skip immediately.
        async with db.pool.acquire() as conn:
            await conn.execute("SELECT pg_advisory_lock($1)", first.lock_id)
            try:
                await asyncio.wait_for(other.tick(now), timeout=2)
                broker.get_account_snapshot.assert_not_awaited()
            finally:
                await conn.execute("SELECT pg_advisory_unlock($1)", first.lock_id)

        await first.tick(now)
        discord.send_checked.return_value = True
        await other.tick(now)
        telegram.assert_awaited_once()
        assert discord.send_checked.await_count == 2
        broker.get_account_snapshot.assert_awaited_once()
        raw = await db.pool.fetchval("SELECT state FROM account_monitor_state")
        assert all(json.loads(raw)["alert"]["delivered"].values())
        assert "private-test-account" not in raw
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()
