"""Real PostgreSQL outbox ownership, retry and crash boundaries on disposable DBs."""

import asyncio
import datetime as dt
import json
import os
import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import asyncpg
import pytest
import pytest_asyncio

from butterfly_guy.core.config import RiskSettings
from butterfly_guy.data.schemas import TradeRecord
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations
from butterfly_guy.db.queries import RiskQueries, TradeQueries
from butterfly_guy.risk.risk_engine import RiskEngine
from butterfly_guy.scripts.spx_live_db import dsn_for
from butterfly_guy.services.exit_notifications import ExitNotifications
from tests.integration.test_spx_live_db import _settings
from tests.test_position_service_settlement import _monitor_patches, _pos_state, _telemetry_service

NOW = dt.datetime(2026, 11, 23, 16, 7, tzinfo=dt.timezone.utc)
DAY = NOW.date()


@pytest_asyncio.fixture
async def notification_db():
    dsn = os.getenv("CI_DATABASE_URL")
    if not dsn:
        pytest.skip("requires CI_DATABASE_URL pointing to disposable test infrastructure")
    name = f"exit_notifications_{uuid.uuid4().hex}"
    admin = await asyncpg.connect(dsn)
    db = DatabasePool(dsn_for(_settings(dsn), name), min_size=1, max_size=4)
    try:
        await admin.execute(f'CREATE DATABASE "{name}"')
        await db.initialize()
        await run_migrations(db)
        yield db
    finally:
        await db.close()
        await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await admin.close()


async def insert_trade(db, *, role="paper", close=True, reason="end_of_day", quantity=1):
    queries = TradeQueries(db, instance_role=role)
    trade_id = await queries.insert_trade({
        "underlying": "SPX", "trade_date": DAY, "direction": "CALL", "wing_width": 40,
        "center_strike": 7360, "lower_strike": 7320, "upper_strike": 7400,
        "entry_price": 3.75, "entry_time": NOW - dt.timedelta(minutes=7),
        "quantity": quantity,
    })
    if close:
        assert await queries.close_trade(
            trade_id, 3.38, NOW, reason, -0.37, 3.83,
            metadata={"suppressed_exit_signal": {"reason": "trailing_drawdown",
                                                "mark_at_signal": 3.43}},
        )
    return queries, trade_id


async def state(db, trade_id):
    return json.loads(await db.pool.fetchval(
        "SELECT metadata FROM butterfly_trades WHERE id=$1", trade_id,
    ))


def worker(db, notifier, **kwargs):
    return ExitNotifications(db, "SPX", kwargs.pop("role", "paper"), notifier,
                             enabled=kwargs.pop("enabled", True), **kwargs)


@pytest.mark.parametrize("failure", [False, TimeoutError("lost acknowledgment")])
async def test_failure_restart_then_acceptance_is_not_retried(notification_db, failure):
    db = notification_db
    _, trade_id = await insert_trade(db)
    notifier = SimpleNamespace(notify_exit=AsyncMock(side_effect=[failure, True]))
    await worker(db, notifier).tick(NOW)
    assert (await state(db, trade_id))["exit_notification_status"] == "pending"
    # A new service, before the persisted retry deadline, must not spin.
    restarted = worker(db, notifier)
    await restarted.tick(NOW + dt.timedelta(seconds=59))
    assert notifier.notify_exit.await_count == 1
    await restarted.tick(NOW + dt.timedelta(seconds=60))
    assert (await state(db, trade_id))["exit_notification_status"] == "sent"
    for days in (1, 2, 10):
        await worker(db, notifier).tick(NOW + dt.timedelta(days=days))
    assert notifier.notify_exit.await_count == 2
    row = await db.pool.fetchrow("SELECT status,pnl FROM butterfly_trades WHERE id=$1", trade_id)
    assert row["status"] == "CLOSED" and float(row["pnl"]) == -0.37


async def test_concurrent_workers_skip_owned_closed_row(notification_db):
    db = notification_db
    _, trade_id = await insert_trade(db)
    entered, release = asyncio.Event(), asyncio.Event()

    async def deliver(**kwargs):
        entered.set()
        await release.wait()
        return True

    first = SimpleNamespace(notify_exit=AsyncMock(side_effect=deliver))
    other = SimpleNamespace(notify_exit=AsyncMock(return_value=True))
    task = asyncio.create_task(worker(db, first).tick(NOW))
    try:
        await asyncio.wait_for(entered.wait(), 2)
        await asyncio.wait_for(worker(db, other).tick(NOW), 2)
        other.notify_exit.assert_not_awaited()
    finally:
        release.set()
        await task
    await worker(db, other).tick(NOW + dt.timedelta(minutes=1))
    other.notify_exit.assert_not_awaited()
    assert (await state(db, trade_id))["exit_notification_status"] == "sent"


@pytest.mark.parametrize("enabled,notifier,status,error", [
    (True, None, "pending", "unconfigured"),
    (False, None, "disabled", "intentionally_disabled"),
])
async def test_missing_config_and_intentional_disable_are_distinct(
    notification_db, enabled, notifier, status, error,
):
    db = notification_db
    _, trade_id = await insert_trade(db)
    await worker(db, notifier, enabled=enabled).tick(NOW)
    metadata = await state(db, trade_id)
    assert metadata["exit_notification_status"] == status
    assert metadata["exit_notification_error"] == error
    assert "exit_notification_accepted_at" not in metadata
    restored = SimpleNamespace(notify_exit=AsyncMock(return_value=True))
    await worker(db, restored).tick(NOW + dt.timedelta(minutes=1))
    assert restored.notify_exit.await_count == int(enabled)


async def test_request_deadline_and_cancel_release_ownership(notification_db, monkeypatch):
    db = notification_db
    _, trade_id = await insert_trade(db)
    cancelled = asyncio.Event()

    async def hang(**kwargs):
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    monkeypatch.setattr("butterfly_guy.services.exit_notifications.DELIVERY_TIMEOUT_SECONDS", 0.01)
    await worker(db, SimpleNamespace(notify_exit=hang)).tick(NOW)
    assert cancelled.is_set()
    assert (await state(db, trade_id))["exit_notification_error"] == "TimeoutError"
    accepted = SimpleNamespace(notify_exit=AsyncMock(return_value=True))
    await worker(db, accepted).tick(NOW + dt.timedelta(minutes=1))
    accepted.notify_exit.assert_awaited_once()


@pytest.mark.parametrize("reason", ["manual_close", "cash_settled", "end_of_day"])
async def test_restart_reconstructs_persisted_message_and_respects_role(notification_db, reason):
    db = notification_db
    _, trade_id = await insert_trade(db, role="live_rehearsal", reason=reason, quantity=3)
    notifier = SimpleNamespace(notify_exit=AsyncMock(return_value=True))
    await worker(db, notifier, role="paper").tick(NOW)
    notifier.notify_exit.assert_not_awaited()
    await worker(db, notifier, role="live_rehearsal").tick(NOW)
    call = notifier.notify_exit.await_args.kwargs
    assert call["trade_id"] == trade_id and call["quantity"] == 3
    assert call["pnl"] == -0.37 and call["exit_price"] == 3.38
    assert call["exit_time"] == NOW and call["instance_role"] == "live_rehearsal"
    if reason == "manual_close":
        assert "Closed by you in Schwab (filled 11:07:00 ET)" in call["manual_detail"]
        assert "`trailing_drawdown`" in call["manual_detail"]
    else:
        assert call["manual_detail"] is None


async def test_legacy_pending_closed_trade_is_consumed_but_open_trade_is_not(notification_db):
    db = notification_db
    _, trade_id = await insert_trade(db)
    await db.pool.execute("UPDATE butterfly_trades SET metadata = "
                          "'{\"exit_secondary_work_pending\":true}' WHERE id=$1", trade_id)
    notifier = SimpleNamespace(notify_exit=AsyncMock(return_value=True))
    await worker(db, notifier).tick(NOW)
    assert (await state(db, trade_id))["exit_notification_status"] == "sent"
    await db.pool.execute("UPDATE butterfly_trades SET status='OPEN', metadata = "
                          "'{\"exit_notification_status\":\"pending\"}' WHERE id=$1", trade_id)
    await worker(db, notifier).tick(NOW)
    notifier.notify_exit.assert_awaited_once()


async def test_acceptance_before_failed_receipt_commit_can_duplicate(notification_db):
    db = notification_db
    _, trade_id = await insert_trade(db)
    accepted = SimpleNamespace(notify_exit=AsyncMock(return_value=True))

    @asynccontextmanager
    async def failing_receipt_connection():
        async with db.pool.acquire() as conn:
            yield SimpleNamespace(
                transaction=conn.transaction, fetchrow=conn.fetchrow,
                execute=AsyncMock(side_effect=ConnectionError("lost receipt commit")),
            )

    fault_db = SimpleNamespace(pool=SimpleNamespace(acquire=failing_receipt_connection))
    with pytest.raises(ConnectionError):
        await worker(fault_db, accepted).tick(NOW)
    assert (await state(db, trade_id))["exit_notification_status"] == "pending"
    # Same persisted trade, another process: acceptance may occur twice. No order or
    # accounting method exists on this worker; only the delivery receipt is updated.
    await worker(db, accepted).tick(NOW + dt.timedelta(minutes=1))
    assert accepted.notify_exit.await_count == 2


@pytest.mark.parametrize("quantity,pnl_dollars", [(1, -37), (2, -74), (3, -111)])
async def test_monitor_one_exit_one_accounting_update_despite_delivery_failure(
    notification_db, quantity, pnl_dollars,
):
    db = notification_db
    queries, trade_id = await insert_trade(db, close=False, quantity=quantity)
    service = _telemetry_service(None)
    service.config.execution.paper_trading = True
    service.position_manager.update_position_value.return_value = _pos_state(3.43, 3.83, entry=3.75)
    service.state_machine = MagicMock()
    service.state_machine.state.name = "LOSS"
    service.state_machine.evaluate.return_value = MagicMock(
        reason="end_of_day", urgency="immediate",
    )
    service.trade_queries = queries
    risk_queries = RiskQueries(db)
    await risk_queries.get_or_create(DAY, "SPX")
    service.risk_engine = RiskEngine(RiskSettings(), risk_queries)
    service.risk_engine.record_pnl = AsyncMock(wraps=service.risk_engine.record_pnl)
    service._exit_mark_parity_report = AsyncMock(return_value={})
    service._start_post_exit_recording = MagicMock()
    service.order_manager.execute_exit.return_value = {"fill_price": 3.38, "fill_time": NOW}
    trade = TradeRecord(trade_id=trade_id, trade_date=DAY, direction="CALL",
                        entry_price=3.75, quantity=quantity)
    patches = _monitor_patches(trade, AsyncMock())
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        await service.monitor_loop(trade, MagicMock())
    notifier = SimpleNamespace(notify_exit=AsyncMock(side_effect=[False, True]))
    await worker(db, notifier).tick(NOW)
    await worker(db, notifier).tick(NOW + dt.timedelta(minutes=1))
    await worker(db, notifier).tick(NOW + dt.timedelta(minutes=2))
    service.order_manager.execute_exit.assert_awaited_once()
    service.risk_engine.record_pnl.assert_awaited_once()
    risk = await risk_queries.get_or_create(DAY, "SPX")
    assert float(risk["realized_pnl"]) == pnl_dollars
    assert (await state(db, trade_id))["exit_notification_status"] == "sent"
