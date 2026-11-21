from __future__ import annotations

import asyncio
import datetime as dt
import json
from contextlib import asynccontextmanager
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from butterfly_guy.core.config import AccountMonitorSettings
from butterfly_guy.core.metrics import (
    account_monitor_last_success,
    account_monitor_last_tick,
    account_monitor_required_check,
)
from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.services.account_monitor import (
    AccountMonitor,
    next_session,
    parse_margin_equity,
    required_check_at,
)


@pytest.mark.parametrize("value", ["1999.99", 2000, "2000.01", -100])
def test_margin_equity_uses_current_equity_not_buying_power_or_liquidation(value):
    assert parse_margin_equity({
        "securitiesAccount": {
            "type": "MARGIN",
            "currentBalances": {
                "equity": value,
                "liquidationValue": 9000,
                "buyingPower": 18000,
            },
        },
    }) == Decimal(str(value))


@pytest.mark.parametrize("value", [None, True, "NaN", "Infinity", "bad", [], {}])
def test_invalid_equity_is_unknown_not_zero(value):
    with pytest.raises(ValueError):
        parse_margin_equity({
            "securitiesAccount": {"type": "MARGIN", "currentBalances": {"equity": value}},
        })


@pytest.mark.parametrize("snapshot", [
    {},
    {"securitiesAccount": {"type": "MARGIN", "currentBalances": {"liquidationValue": 9000}}},
    {"securitiesAccount": {"type": "CASH", "currentBalances": {"equity": 9000}}},
])
def test_missing_equity_or_nonmargin_account_is_unknown(snapshot):
    with pytest.raises(ValueError):
        parse_margin_equity(snapshot)


def at(day="2026-11-20", clock="16:15"):
    return dt.datetime.fromisoformat(f"{day}T{clock}").replace(tzinfo=EASTERN)


def snapshot(equity):
    return {"securitiesAccount": {"type": "MARGIN", "currentBalances": {"equity": equity}}}


class MemoryDatabase:
    """Model persisted JSON and nonblocking locks across monitor instances."""

    def __init__(self):
        self.states = {}
        self.locks = set()
        self.rows = []
        self.pool = self

    @asynccontextmanager
    async def acquire(self):
        yield self

    async def fetchval(self, sql, key):
        if "pg_try_advisory_lock" in sql:
            if key in self.locks:
                return False
            self.locks.add(key)
            return True
        return self.states.get(key)

    async def execute(self, sql, *args):
        if "pg_advisory_unlock" in sql:
            self.locks.remove(args[0])
        else:
            self.states[args[0]] = args[1]

    async def fetch(self, _sql, _since):
        return self.rows

    def state(self, monitor):
        return json.loads(self.states[monitor.account_key])


@pytest.fixture
def harness(monkeypatch):
    db = MemoryDatabase()
    schwab = SimpleNamespace(
        settings=SimpleNamespace(account_id="test-private-account"),
        get_account_snapshot=AsyncMock(return_value=snapshot(2500)),
    )
    discord = SimpleNamespace(send_checked=AsyncMock(return_value=True))
    telegram = AsyncMock(return_value=True)
    monkeypatch.setattr("butterfly_guy.services.account_monitor.send_checked_async", telegram)
    monitor = AccountMonitor(db, schwab, AccountMonitorSettings(), discord)
    return SimpleNamespace(
        monitor=monitor, db=db, schwab=schwab, discord=discord, telegram=telegram,
    )


@pytest.mark.parametrize("equity,status", [
    ("1999.99", "low"), ("2000.00", "low"), ("2000.01", "healthy"),
])
async def test_equity_floor_boundary(harness, equity, status):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(equity)
    await h.monitor.tick(at())
    assert h.db.state(h.monitor)["snapshot"]["status"] == status
    assert h.telegram.await_count == h.discord.send_checked.await_count == (status == "low")
    if status == "low":
        msg = h.telegram.await_args.args[0]
        assert "2026-11-23" in msg  # Friday -> Monday
        assert "does not block trading" in msg
        assert "test-private-account" not in msg


async def test_no_trade_day_gets_morning_and_eod_checks(harness):
    h = harness
    await h.monitor.tick(at(clock="08:59"))
    h.schwab.get_account_snapshot.assert_not_awaited()
    await h.monitor.tick(at(clock="09:00"))
    await h.monitor.tick(at(clock="09:01"))
    await h.monitor.tick(at(clock="16:14"))
    assert h.schwab.get_account_snapshot.await_count == 1
    await h.monitor.tick(at())
    assert h.schwab.get_account_snapshot.await_count == 2
    assert h.db.state(h.monitor)["snapshot"]["trigger"] == "end_of_day"
    h.telegram.assert_not_awaited()


async def test_trade_close_is_delayed_then_rechecked_and_recovery_sent(harness):
    h = harness
    await h.monitor.tick(at(clock="09:00"))
    h.db.rows = [{"id": 7, "status": "CLOSED", "provisional": None}]
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    await h.monitor.tick(at(clock="11:00"))
    assert h.schwab.get_account_snapshot.await_count == 1
    await h.monitor.tick(at(clock="11:01"))
    assert h.db.state(h.monitor)["snapshot"]["status"] == "low"
    h.schwab.get_account_snapshot.return_value = snapshot(2500)
    await h.monitor.tick(at(clock="11:05"))
    assert h.db.state(h.monitor)["snapshot"]["status"] == "healthy"
    assert h.schwab.get_account_snapshot.await_count == 3
    assert "RECOVERED" in h.telegram.await_args.args[0]
    assert h.telegram.await_count == 2


async def test_second_postclose_snapshot_happens_even_when_first_is_healthy(harness):
    h = harness
    await h.monitor.tick(at(clock="09:00"))
    h.db.rows = [{"id": 7, "status": "CLOSED", "provisional": None}]
    await h.monitor.tick(at(clock="11:00"))
    await h.monitor.tick(at(clock="11:01"))
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    await h.monitor.tick(at(clock="11:05"))
    assert h.db.state(h.monitor)["snapshot"]["status"] == "low"
    h.telegram.assert_awaited_once()


@pytest.mark.parametrize("rows", [
    [{"id": 7, "status": "OPEN", "provisional": None}],
    [{"id": 7, "status": "SUBMITTED", "provisional": None}],
    [{"id": 7, "status": "CLOSED", "provisional": "true"}],
])
async def test_unresolved_local_trades_do_not_create_broker_equity_alerts(harness, rows):
    h = harness
    h.db.rows = rows
    await h.monitor.tick(at())
    assert h.db.state(h.monitor)["snapshot"]["status"] == "healthy"
    assert h.db.state(h.monitor)["snapshot"]["provisional"]
    h.telegram.assert_not_awaited()
    h.discord.send_checked.assert_not_awaited()


async def test_settlement_trueup_triggers_new_check(harness):
    h = harness
    h.db.rows = [{"id": 7, "status": "CLOSED", "provisional": "true"}]
    await h.monitor.tick(at())
    h.db.rows[0]["provisional"] = "false"
    await h.monitor.tick(at(clock="16:16"))
    await h.monitor.tick(at(clock="16:17"))
    assert h.db.state(h.monitor)["snapshot"]["status"] == "healthy"
    h.telegram.assert_not_awaited()


@pytest.mark.parametrize("value", [None, "NaN", True])
async def test_missing_or_invalid_balance_alerts_unknown(harness, value):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(value)
    await h.monitor.tick(at())
    assert h.db.state(h.monitor)["snapshot"]["status"] == "unknown"
    h.telegram.assert_not_awaited()
    await h.monitor.tick(at(clock="16:20"))
    assert "UNABLE TO VERIFY" in h.telegram.await_args.args[0]
    assert "$0.00" not in h.telegram.await_args.args[0]


async def test_broker_failure_is_retried_and_sensitive_error_is_not_in_alert(harness):
    h = harness
    h.schwab.get_account_snapshot.side_effect = TimeoutError("private-account-and-url")
    await h.monitor.tick(at())
    h.telegram.assert_not_awaited()
    h.schwab.get_account_snapshot.side_effect = None
    await h.monitor.tick(at(clock="16:20"))
    assert h.db.state(h.monitor)["snapshot"]["status"] == "healthy"
    h.telegram.assert_not_awaited()


@pytest.mark.parametrize("failed_channel", ["telegram", "discord"])
async def test_failed_channel_only_is_retried_after_restart(harness, failed_channel):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    failed = h.telegram if failed_channel == "telegram" else h.discord.send_checked
    failed.return_value = False
    await h.monitor.tick(at())
    failed.return_value = True
    restarted = AccountMonitor(h.db, h.schwab, AccountMonitorSettings(), h.discord)
    await restarted.tick(at(clock="16:16"))
    assert failed.await_count == 2
    successful = h.discord.send_checked if failed_channel == "telegram" else h.telegram
    assert successful.await_count == 1
    assert all(h.db.state(restarted)["alert"]["delivered"].values())


async def test_delivery_exception_does_not_prevent_other_channel(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    h.telegram.side_effect = RuntimeError("unavailable")
    await h.monitor.tick(at())
    assert not h.db.state(h.monitor)["alert"]["delivered"]["telegram"]
    h.discord.send_checked.assert_awaited_once()
    assert not h.db.locks


async def test_missing_discord_configuration_remains_pending(harness):
    h = harness
    h.monitor.discord = None
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    await h.monitor.tick(at())
    assert h.db.state(h.monitor)["alert"]["delivered"] == {
        "telegram": True, "discord": False,
    }


async def test_same_account_same_database_has_one_daily_warning_across_runtimes(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    other = AccountMonitor(h.db, h.schwab, AccountMonitorSettings(), h.discord)
    await h.monitor.tick(at())
    await other.tick(at())
    await h.monitor.tick(at(clock="16:16"))
    assert h.schwab.get_account_snapshot.await_count == 1
    h.telegram.assert_awaited_once()
    h.discord.send_checked.assert_awaited_once()


async def test_busy_account_lock_skips_without_touching_broker(harness):
    h = harness
    h.db.locks.add(h.monitor.lock_id)
    await h.monitor.tick(at())
    h.schwab.get_account_snapshot.assert_not_awaited()


async def test_warning_reminds_on_next_trading_day_and_recovers(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    await h.monitor.tick(at())
    await h.monitor.tick(at(day="2026-11-21"))  # Saturday
    assert h.telegram.await_count == 1
    await h.monitor.tick(at(day="2026-11-23", clock="09:00"))
    assert h.telegram.await_count == 2
    assert "Next trading session: 2026-11-23" in h.telegram.await_args.args[0]
    h.schwab.get_account_snapshot.return_value = snapshot(2100)
    await h.monitor.tick(at(day="2026-11-23", clock="09:05"))
    assert h.telegram.await_count == 3
    assert "RECOVERED" in h.telegram.await_args.args[0]


async def test_delivery_retries_continue_on_weekend(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    h.telegram.return_value = False
    await h.monitor.tick(at())
    h.telegram.return_value = True
    await h.monitor.tick(at(day="2026-11-21"))
    assert h.telegram.await_count == 2
    assert h.schwab.get_account_snapshot.await_count == 1


async def test_holiday_skipped_and_early_close_respected(harness):
    h = harness
    await h.monitor.tick(at(day="2026-11-26"))  # Thanksgiving
    h.schwab.get_account_snapshot.assert_not_awaited()
    await h.monitor.tick(at(day="2026-11-27", clock="13:14"))
    h.schwab.get_account_snapshot.assert_not_awaited()
    await h.monitor.tick(at(day="2026-11-27", clock="13:15"))
    h.schwab.get_account_snapshot.assert_awaited_once()
    assert h.db.state(h.monitor)["eod_day"] == "2026-11-27"


async def test_disabled_monitor_does_nothing(harness):
    h = harness
    h.monitor.settings.enabled = False
    await h.monitor.tick(at())
    assert not h.db.states
    h.schwab.get_account_snapshot.assert_not_awaited()


def test_next_session_skips_holiday_and_weekend():
    assert next_session(at(day="2026-11-25")) == dt.date(2026, 11, 27)
    assert next_session(at()) == dt.date(2026, 11, 23)


async def test_account_lock_prevents_concurrent_balance_requests(harness):
    h = harness
    entered = asyncio.Event()
    release = asyncio.Event()

    async def pending_snapshot():
        entered.set()
        await release.wait()
        return snapshot(1900)

    h.schwab.get_account_snapshot.side_effect = pending_snapshot
    first = asyncio.create_task(h.monitor.tick(at()))
    await asyncio.wait_for(entered.wait(), timeout=1)
    other = AccountMonitor(h.db, h.schwab, AccountMonitorSettings(), h.discord)
    try:
        await other.tick(at())
        assert h.schwab.get_account_snapshot.await_count == 1
    finally:
        release.set()
        await first
    h.telegram.assert_awaited_once()


async def test_broker_timeout_alerts_unknown(harness, monkeypatch):
    h = harness
    monkeypatch.setattr("butterfly_guy.services.account_monitor.BALANCE_TIMEOUT_SECONDS", 0.001)

    async def hung_snapshot():
        await asyncio.Event().wait()

    h.schwab.get_account_snapshot.side_effect = hung_snapshot
    await h.monitor.tick(at())
    assert h.db.state(h.monitor)["snapshot"]["status"] == "unknown"
    h.telegram.assert_not_awaited()
    await h.monitor.tick(at(clock="16:20"))
    h.telegram.assert_awaited_once()


async def test_rolling_window_pruning_never_triggers_midnight_check_or_eats_reminder(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    h.db.rows = [{"id": 1, "status": "CLOSED", "provisional": None}]
    await h.monitor.tick(at(day="2026-11-18"))
    # Complete the legitimate close follow-ups before the window rolls forward.
    await h.monitor.tick(at(day="2026-11-18", clock="16:16"))
    await h.monitor.tick(at(day="2026-11-18", clock="16:20"))
    h.db.rows = []
    calls = h.schwab.get_account_snapshot.await_count
    await h.monitor.tick(at(day="2026-11-19", clock="00:00"))
    await h.monitor.tick(at(day="2026-11-19", clock="00:01"))
    assert h.schwab.get_account_snapshot.await_count == calls
    assert h.telegram.await_count == 1
    await h.monitor.tick(at(day="2026-11-19", clock="09:00"))
    assert h.telegram.await_count == 2
    assert "pre_session" in h.telegram.await_args.args[0]


async def test_single_failed_read_between_low_results_does_not_realert(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    await h.monitor.tick(at())
    h.schwab.get_account_snapshot.side_effect = TimeoutError()
    await h.monitor.tick(at(clock="16:20"))
    h.schwab.get_account_snapshot.side_effect = None
    await h.monitor.tick(at(clock="16:25"))
    h.telegram.assert_awaited_once()
    h.discord.send_checked.assert_awaited_once()


async def test_unknown_confirmation_survives_restart_and_recovers_once(harness):
    h = harness
    h.schwab.get_account_snapshot.side_effect = TimeoutError()
    await h.monitor.tick(at())
    other = AccountMonitor(h.db, h.schwab, AccountMonitorSettings(), h.discord)
    await other.tick(at(clock="16:20"))
    assert "UNABLE TO VERIFY" in h.telegram.await_args.args[0]
    assert "retry" in h.telegram.await_args.args[0]
    await other.tick(at(clock="16:25"))
    h.telegram.assert_awaited_once()
    h.schwab.get_account_snapshot.side_effect = None
    await other.tick(at(clock="16:30"))
    assert "RECOVERED" in h.telegram.await_args.args[0]
    assert h.telegram.await_count == 2


async def test_high_equity_paper_close_with_another_open_trade_is_silent(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(50000)
    await h.monitor.tick(at(clock="09:00"))
    h.db.rows = [
        {"id": 1, "status": "CLOSED", "provisional": None},
        {"id": 2, "status": "OPEN", "provisional": None},
    ]
    await h.monitor.tick(at(clock="11:00"))
    await h.monitor.tick(at(clock="11:01"))
    h.db.rows[1]["status"] = "CLOSED"
    await h.monitor.tick(at(clock="11:02"))
    await h.monitor.tick(at(clock="11:03"))
    h.telegram.assert_not_awaited()
    h.discord.send_checked.assert_not_awaited()


async def test_low_equity_message_keeps_ledger_note_without_changing_condition(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    h.db.rows = [{"id": 2, "status": "SUBMITTED", "provisional": None}]
    await h.monitor.tick(at())
    message = h.telegram.await_args.args[0]
    assert "MARGIN EQUITY WARNING" in message
    assert "Local ledger note" in message
    assert h.db.state(h.monitor)["condition"] == "low"
    h.db.rows = []
    await h.monitor.tick(at(clock="16:20"))
    h.telegram.assert_awaited_once()


async def test_new_close_at_night_waits_for_morning_check(harness):
    h = harness
    await h.monitor.tick(at(day="2026-11-18"))
    h.db.rows = [{"id": 1, "status": "CLOSED", "provisional": None}]
    await h.monitor.tick(at(day="2026-11-19", clock="00:00"))
    await h.monitor.tick(at(day="2026-11-19", clock="00:01"))
    assert h.schwab.get_account_snapshot.await_count == 1
    await h.monitor.tick(at(day="2026-11-19", clock="09:00"))
    assert h.schwab.get_account_snapshot.await_count == 2
    assert h.db.state(h.monitor)["snapshot"]["trigger"] == "pre_session"


def test_state_and_lock_keys_have_no_account_number_derivation(harness):
    h = harness
    other_broker = SimpleNamespace(settings=SimpleNamespace(account_id="different-account"))
    other = AccountMonitor(h.db, other_broker, AccountMonitorSettings(), h.discord)
    assert other.account_key == h.monitor.account_key == "brokerage_account"
    assert other.lock_id == h.monitor.lock_id == 810_770_013


async def test_metrics_distinguish_valid_balance_from_a_completed_failed_read(harness):
    h = harness
    await h.monitor.tick(at(clock="09:00"))
    valid_at = at(clock="09:00").timestamp()
    assert account_monitor_last_success._value.get() == valid_at
    assert account_monitor_last_tick._value.get() == valid_at
    assert account_monitor_required_check._value.get() == valid_at
    h.schwab.get_account_snapshot.side_effect = TimeoutError()
    # EOD is a required new read even though the morning result was healthy.
    await h.monitor.tick(at())
    assert account_monitor_last_success._value.get() == valid_at
    assert account_monitor_last_tick._value.get() == at().timestamp()
    assert account_monitor_required_check._value.get() == at().timestamp()


async def test_database_failure_and_stuck_lock_do_not_refresh_heartbeat(harness):
    h = harness
    await h.monitor.tick(at(clock="09:00"))
    valid_at = at(clock="09:00").timestamp()
    h.db.locks.add(h.monitor.lock_id)
    await h.monitor.tick(at(clock="09:03"))
    assert account_monitor_last_tick._value.get() == valid_at
    h.db.locks.clear()
    h.db.fetch = AsyncMock(side_effect=RuntimeError("missing table"))
    with pytest.raises(RuntimeError):
        await h.monitor.tick(at(clock="09:04"))
    assert account_monitor_last_tick._value.get() == valid_at
    assert not h.db.locks


async def test_last_success_metric_restored_from_state_after_restart(harness):
    h = harness
    await h.monitor.tick(at())
    account_monitor_last_success.set(0)  # New process has an empty registry.
    restarted = AccountMonitor(h.db, h.schwab, AccountMonitorSettings(), h.discord)
    await restarted.tick(at(day="2026-11-21"))
    assert account_monitor_last_success._value.get() == at().timestamp()
    h.schwab.get_account_snapshot.assert_awaited_once()


@pytest.mark.parametrize("now,expected", [
    (at(clock="08:59"), at(day="2026-11-19")),
    (at(clock="09:00"), at(clock="09:00")),
    (at(clock="16:14"), at(clock="09:00")),
    (at(), at()),
    (at(day="2026-11-21"), at()),
    (at(day="2026-11-26"), at(day="2026-11-25")),
    (at(day="2026-11-27", clock="13:15"), at(day="2026-11-27", clock="13:15")),
])
def test_required_check_metric_tracks_sessions_including_early_closes(now, expected):
    assert required_check_at(now) == expected


async def test_cancelled_check_releases_account_lock(harness):
    h = harness
    h.schwab.get_account_snapshot.side_effect = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await h.monitor.tick(at())
    assert not h.db.locks
    h.telegram.assert_not_awaited()


async def test_recovery_supersedes_undelivered_low_warning(harness):
    h = harness
    h.schwab.get_account_snapshot.return_value = snapshot(1900)
    h.telegram.return_value = False
    await h.monitor.tick(at())
    h.schwab.get_account_snapshot.return_value = snapshot(2500)
    h.telegram.return_value = True
    await h.monitor.tick(at(clock="16:20"))
    assert "RECOVERED" in h.telegram.await_args.args[0]
    assert "WARNING" not in h.db.state(h.monitor)["alert"]["message"]


async def test_monitor_loop_survives_failure_and_propagates_cancellation(harness, monkeypatch):
    h = harness
    h.monitor.tick = AsyncMock(side_effect=RuntimeError("database unavailable"))
    monkeypatch.setattr(
        "butterfly_guy.services.account_monitor.asyncio.sleep",
        AsyncMock(side_effect=asyncio.CancelledError()),
    )
    with pytest.raises(asyncio.CancelledError):
        await h.monitor.run()
    h.monitor.tick.assert_awaited_once()
