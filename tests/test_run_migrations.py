from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from butterfly_guy.db.migrations import run_migrations as module


class FakeConnection:
    def __init__(self, applied=None):
        self.execute = AsyncMock()
        self.fetch = AsyncMock(return_value=applied or [])

    @asynccontextmanager
    async def transaction(self):
        yield


def fake_db(conn):
    @asynccontextmanager
    async def acquire():
        yield conn

    return SimpleNamespace(pool=SimpleNamespace(acquire=acquire))


@pytest.mark.asyncio
async def test_migration_is_recorded_and_then_skipped(tmp_path, monkeypatch):
    migration = tmp_path / "001_test.sql"
    migration.write_text("SELECT 1")
    monkeypatch.setattr(module, "MIGRATIONS_DIR", tmp_path)
    conn = FakeConnection()

    await module.run_migrations(fake_db(conn))

    assert any(call.args[0] == "SELECT 1" for call in conn.execute.await_args_list)
    checksum = next(
        call.args[2]
        for call in conn.execute.await_args_list
        if call.args[0].startswith("INSERT INTO schema_migrations")
    )

    skipped = FakeConnection([{"version": migration.name, "checksum": checksum}])
    await module.run_migrations(fake_db(skipped))
    assert not any(call.args[0] == "SELECT 1" for call in skipped.execute.await_args_list)


@pytest.mark.asyncio
async def test_changed_migration_fails_closed(tmp_path, monkeypatch):
    (tmp_path / "001_test.sql").write_text("SELECT 2")
    monkeypatch.setattr(module, "MIGRATIONS_DIR", tmp_path)
    conn = FakeConnection([{"version": "001_test.sql", "checksum": "old"}])

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        await module.run_migrations(fake_db(conn))

    assert not any(call.args[0] == "SELECT 2" for call in conn.execute.await_args_list)
