"""Offline launch safety regressions; no broker writes or service changes."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import yaml
from pydantic import ValidationError
from schwab_gateway_sdk.config import GatewayClientSettings

from butterfly_guy.core.config import AppConfig, load_config
from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.db.queries import RiskQueries
from butterfly_guy.execution.order_manager import AmbiguousOrderError, PartialFillError
from butterfly_guy.risk.live_safety import LiveSafetyError, require_spx_supervision
from butterfly_guy.scripts.halt_live_entries import halt
from butterfly_guy.scripts.run_live import (
    BrokerStateGate,
    _assert_live_config_supported,
    broker_reconciler_loop,
    entry_loop,
)


@pytest.fixture
def supervised(monkeypatch):
    now = dt.datetime(2026, 10, 20, 10, tzinfo=EASTERN)
    monkeypatch.setenv("LIVE_SUPERVISOR", "Corey")
    monkeypatch.setenv("LIVE_SUPERVISION_UNTIL", "2026-10-20T16:30:00-04:00")
    monkeypatch.setattr("butterfly_guy.risk.live_safety.now_eastern", lambda: now)
    return now


@pytest.mark.parametrize("paper", [True, False])
def test_compose_execution_controls_override_yaml_in_both_directions(tmp_path, monkeypatch, paper):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump({"execution": {
        "paper_trading": not paper, "allow_live_trading": paper,
    }}))
    monkeypatch.setenv("EXECUTION__PAPER_TRADING", str(paper).lower())
    monkeypatch.setenv("EXECUTION__ALLOW_LIVE_TRADING", str(not paper).lower())
    monkeypatch.setenv("ALLOW_LIVE_TRADING", "true")
    config = load_config(path, env_file=str(tmp_path / "absent.env"))
    assert config.execution.paper_trading is paper
    assert config.execution.allow_live_trading is (not paper)


def test_invalid_compose_mode_does_not_silently_fall_back_to_yaml(monkeypatch):
    monkeypatch.setenv("EXECUTION__PAPER_TRADING", "typo")
    with pytest.raises(ValidationError):
        load_config("configs/config.yaml")


def test_live_overlay_loads_real_mode_and_keeps_frozen_strategy(monkeypatch, supervised):
    # SafeLoader deliberately doesn't execute Compose-specific tags.
    class Loader(yaml.SafeLoader):
        pass

    Loader.add_constructor("!reset", lambda loader, node: None)
    overlay = yaml.load(Path("infra/docker-compose.spx-live.yml").read_text(), Loader=Loader)
    assert set(overlay["services"]) == {"app_spx"}
    service = overlay["services"]["app_spx"]
    assert service["restart"] == "no"
    baseline = load_config("configs/config.yaml")
    for key, value in service["environment"].items():
        if not value.startswith("${"):
            monkeypatch.setenv(key, value)
    monkeypatch.setenv("SCHWAB_ACCOUNT_ID", "reviewed-account")
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "reviewed-account")
    live = load_config("configs/config.yaml")
    assert live.execution.paper_trading is False
    assert live.execution.allow_live_trading is True
    assert live.strategy == baseline.strategy
    assert live.entry == baseline.entry
    assert live.profit_management == baseline.profit_management
    assert live.risk == baseline.risk
    _assert_live_config_supported(live, GatewayClientSettings())

    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "wrong-account")
    with pytest.raises(RuntimeError, match="LIVE_EXPECTED"):
        _assert_live_config_supported(live, GatewayClientSettings())
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "reviewed-account")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "501")
    with pytest.raises(RuntimeError, match="LIVE_MAX_ACCOUNT_DAILY_LOSS"):
        _assert_live_config_supported(live, GatewayClientSettings())


@pytest.mark.parametrize("risk", [{"max_position_size": 2}, {"max_trades_per_day": 2}])
def test_launch_guard_rejects_increased_size_or_trade_count(monkeypatch, supervised, risk):
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "reviewed-account")
    monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20000")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "500")
    config = AppConfig(
        schwab={"account_id": "reviewed-account"}, risk=risk,
        execution={"paper_trading": False, "allow_live_trading": True},
    )
    with pytest.raises(RuntimeError, match="one contract and one trade"):
        _assert_live_config_supported(config, GatewayClientSettings())


@pytest.mark.parametrize("failure", ["allocation", "loss_cap", "supervisor"])
def test_startup_rejects_unconfirmed_spx_risk_or_supervision(monkeypatch, supervised, failure):
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "reviewed-account")
    monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20000")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "500")
    config = AppConfig(
        schwab={"account_id": "reviewed-account"},
        execution={"paper_trading": False, "allow_live_trading": True},
    )
    if failure == "allocation":
        monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20001")
    elif failure == "loss_cap":
        config.risk.max_daily_loss = 501
    else:
        monkeypatch.delenv("LIVE_SUPERVISOR")
    with pytest.raises(RuntimeError):
        _assert_live_config_supported(config, GatewayClientSettings())


def test_combined_compose_keeps_ndx_xsp_paper_and_requires_an_account_pin(tmp_path):
    if shutil.which("docker") is None:
        pytest.skip("Docker Compose is not installed")
    # Some Compose versions still stat required env_file paths with
    # --no-env-resolution. Preserve the three real overlay bodies and tags,
    # substituting only env_file paths with an existing empty synthetic file.
    # Never create /opt paths or read a developer's deployment credentials.
    empty_env = tmp_path / "synthetic.env"
    empty_env.write_text("")
    overlay_args = []
    for name in (
        "docker-compose.yml", "docker-compose.gateway-paper-cutover.yml",
        "docker-compose.spx-live.yml",
    ):
        source = (Path("infra") / name).read_text()
        for env_path in (
            "../.env", "/opt/butterflyguy/.env", "/opt/butterflyguy-gateway-consumer.env",
        ):
            source = source.replace(f"      - {env_path}\n", f"      - {empty_env}\n")
        target = tmp_path / name
        target.write_text(source)
        overlay_args.extend(["-f", str(target)])
    argv = [
        "docker", "compose", "--env-file", "/dev/null",
        *overlay_args,
        "--profile", "ndx", "--profile", "xsp",
        "config", "--no-env-resolution", "--format", "json",
    ]
    # No daemon or real credentials: this verifies actual Compose merge semantics.
    env = {
        "PATH": os.environ["PATH"],
        "SCHWAB_GATEWAY_TOKEN_DIR": "/tmp/test-tokens",
        "BUTTERFLY_GATEWAY_PAPER_IMAGE": "sha256:" + "1" * 64,
        "BUTTERFLY_SPX_LIVE_IMAGE": "sha256:" + "2" * 64,
        "SCHWAB_GATEWAY_API_KEY": "test-only",
        "LIVE_EXPECTED_SCHWAB_ACCOUNT_ID": "test-account",
        "LIVE_SUPERVISOR": "Corey",
        "LIVE_SUPERVISION_UNTIL": "2026-10-20T16:30:00-04:00",
    }
    result = subprocess.run(argv, env=env, capture_output=True, text=True, check=True)
    services = json.loads(result.stdout)["services"]
    spx = services["app_spx"]
    assert spx["environment"]["EXECUTION__PAPER_TRADING"] == "false"
    assert spx["environment"]["SCHWAB_ACCESS_MODE"] == "direct"
    assert spx["restart"] == "no"
    assert spx["image"] == env["BUTTERFLY_SPX_LIVE_IMAGE"]
    for name in ("app_ndx", "app_xsp"):
        service = services[name]
        assert service["environment"]["EXECUTION__PAPER_TRADING"] == "true"
        assert service["environment"]["EXECUTION__ALLOW_LIVE_TRADING"] == "false"
        assert service["environment"]["SCHWAB_ACCESS_MODE"] == "gateway"
        assert service["image"] == env["BUTTERFLY_GATEWAY_PAPER_IMAGE"]
    del env["LIVE_EXPECTED_SCHWAB_ACCOUNT_ID"]
    rejected = subprocess.run(argv, env=env, capture_output=True, text=True)
    assert rejected.returncode != 0
    assert "LIVE_EXPECTED_SCHWAB_ACCOUNT_ID" in rejected.stderr


@pytest.mark.parametrize("until", [
    "", "tomorrow", "2026-10-20T16:30:00", "2026-10-20T15:59:00-04:00",
    "2026-10-21T16:30:00-04:00", "2026-10-19T16:30:00-04:00",
])
def test_supervision_requires_this_session_and_the_whole_window(monkeypatch, supervised, until):
    monkeypatch.setenv("LIVE_SUPERVISION_UNTIL", until)
    with pytest.raises(LiveSafetyError):
        require_spx_supervision()


def test_supervision_handles_early_close_and_expires(monkeypatch, supervised):
    early = dt.datetime(2026, 11, 27, 10, tzinfo=EASTERN)
    monkeypatch.setenv("LIVE_SUPERVISION_UNTIL", "2026-11-27T13:00:00-05:00")
    require_spx_supervision(early)
    with pytest.raises(LiveSafetyError):
        require_spx_supervision(early.replace(hour=13, minute=1))
    monkeypatch.setenv("LIVE_SUPERVISOR", " ")
    with pytest.raises(LiveSafetyError):
        require_spx_supervision(early)


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [
    PartialFillError("PARTIALLY_FILLED"), PartialFillError("CANCEL_PENDING"),
    AmbiguousOrderError("UNKNOWN"), LiveSafetyError("stale_chain"),
])
async def test_live_entry_safety_stop_halts_audits_and_never_retries(
    monkeypatch, supervised, error
):
    config = AppConfig(execution={"paper_trading": False, "allow_live_trading": True})
    risk = Mock(halt_entries=AsyncMock())
    service = Mock(
        config=config, attempt_entry=AsyncMock(side_effect=error),
        risk_engine=Mock(risk_queries=risk),
    )
    notifier = Mock(notify_critical=AsyncMock())
    position = Mock(monitor_loop=AsyncMock())
    monkeypatch.setattr("butterfly_guy.scripts.run_live.is_market_open", lambda: True)
    set_readiness(None)
    try:
        await entry_loop(service, position, critical_notifier=notifier)
        service.attempt_entry.assert_awaited_once()
        risk.halt_entries.assert_awaited_once()
        assert risk.halt_entries.await_args.args[1:] == ("SPX", type(error).__name__)
        position.monitor_loop.assert_not_awaited()
        notifier.notify_critical.assert_awaited_once()
        assert readiness_snapshot()[0] is False
    finally:
        set_readiness(None)


@pytest.mark.asyncio
async def test_live_broker_gate_never_auto_recovers(monkeypatch):
    gate = BrokerStateGate(latched=True)
    risk = Mock(halt_entries=AsyncMock())
    reconcile = AsyncMock(side_effect=[RuntimeError("mismatch"), None])
    monkeypatch.setattr("butterfly_guy.scripts.run_live._reconcile_broker_state", reconcile)
    calls = 0

    async def sleep(_):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise asyncio.CancelledError

    monkeypatch.setattr("butterfly_guy.scripts.run_live.asyncio.sleep", sleep)
    try:
        with pytest.raises(asyncio.CancelledError):
            await broker_reconciler_loop(
                Mock(), "SPX", Mock(), Mock(), gate, risk_queries=risk
            )
        assert gate.unsafe
        risk.halt_entries.assert_awaited_once()
    finally:
        set_readiness(None)


@pytest.mark.asyncio
async def test_latched_broker_halt_retries_persistence_after_reconciliation_recovers(monkeypatch):
    gate = BrokerStateGate(latched=True)
    risk = Mock(halt_entries=AsyncMock(side_effect=[RuntimeError("DB down"), None]))
    reconcile = AsyncMock(side_effect=[RuntimeError("mismatch"), None])
    monkeypatch.setattr("butterfly_guy.scripts.run_live._reconcile_broker_state", reconcile)
    calls = 0

    async def sleep(_):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise asyncio.CancelledError

    monkeypatch.setattr("butterfly_guy.scripts.run_live.asyncio.sleep", sleep)
    try:
        with pytest.raises(asyncio.CancelledError):
            await broker_reconciler_loop(
                Mock(), "SPX", Mock(), Mock(), gate, risk_queries=risk
            )
        assert gate.unsafe
        assert risk.halt_entries.await_count == 2
    finally:
        set_readiness(None)


@pytest.mark.asyncio
@pytest.mark.parametrize("trigger", ["expiry", "broker", "manual"])
async def test_entry_halt_preserves_active_monitor(monkeypatch, supervised, trigger):
    config = AppConfig(execution={"paper_trading": False, "allow_live_trading": True})
    risk = Mock(halt_entries=AsyncMock())
    service = Mock(config=config, attempt_entry=AsyncMock(), risk_engine=Mock(risk_queries=risk))
    notifier = Mock(notify_critical=AsyncMock())
    gate = BrokerStateGate(latched=True)
    if trigger == "broker":
        gate.set_unsafe("mismatch")
    if trigger == "manual":
        # A persisted entry halt is read by can_trade, never by position monitoring.
        risk.get_or_create = AsyncMock(return_value={"halted": True})

    finished = asyncio.Event()
    started = asyncio.Event()
    real_sleep = asyncio.sleep
    task = None
    calls = 0

    async def monitor(*args, **kwargs):
        nonlocal task
        task = asyncio.current_task()
        started.set()
        await finished.wait()

    async def sleep(_):
        nonlocal calls
        calls += 1
        await real_sleep(0)
        assert started.is_set()
        assert not task.cancelled()
        if calls == 1 and trigger == "expiry":
            monkeypatch.setenv("LIVE_SUPERVISION_UNTIL", "2026-10-19T16:30:00-04:00")
        if calls == 2:
            if trigger == "expiry":
                risk.halt_entries.assert_awaited_once()
                notifier.notify_critical.assert_awaited_once()
            finished.set()
            await real_sleep(0)
            raise asyncio.CancelledError

    monkeypatch.setattr("butterfly_guy.scripts.run_live.is_market_open", lambda: True)
    monkeypatch.setattr("butterfly_guy.scripts.run_live.asyncio.sleep", sleep)
    set_readiness(None)
    try:
        with pytest.raises(asyncio.CancelledError):
            await entry_loop(
                service, Mock(monitor_loop=monitor), recovered_trade=Mock(trade_id=7),
                recovered_candidate=Mock(), broker_gate=gate, critical_notifier=notifier,
            )
        service.attempt_entry.assert_not_awaited()
        assert task.done() and task.exception() is None
    finally:
        finished.set()
        if task is not None:
            await task
        set_readiness(None)


@pytest.mark.asyncio
async def test_supervision_halt_retries_database_without_entry(monkeypatch, supervised):
    config = AppConfig(execution={"paper_trading": False, "allow_live_trading": True})
    risk = Mock(halt_entries=AsyncMock(side_effect=[RuntimeError("DB down"), None]))
    service = Mock(config=config, attempt_entry=AsyncMock(), risk_engine=Mock(risk_queries=risk))
    notifier = Mock(notify_critical=AsyncMock())
    monkeypatch.setenv("LIVE_SUPERVISOR", "")
    monkeypatch.setattr("butterfly_guy.scripts.run_live.is_market_open", lambda: True)
    sleeps = 0

    async def sleep(_):
        nonlocal sleeps
        sleeps += 1
        assert sleeps < 3

    monkeypatch.setattr("butterfly_guy.scripts.run_live.asyncio.sleep", sleep)
    set_readiness(None)
    try:
        await entry_loop(service, Mock(), critical_notifier=notifier)
        assert risk.halt_entries.await_count == 2
        service.attempt_entry.assert_not_awaited()
        notifier.notify_critical.assert_awaited_once()
    finally:
        set_readiness(None)


@pytest.mark.asyncio
async def test_operational_halt_is_atomic_and_does_not_fabricate_a_loss():
    conn = MagicMock(execute=AsyncMock())
    transaction = conn.transaction.return_value
    db = Mock()
    db.pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    # __aexit__ must be awaitable for both the pool lease and transaction.
    transaction.__aenter__ = AsyncMock()
    transaction.__aexit__ = AsyncMock(return_value=False)
    db.pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    queries = RiskQueries(db)
    date = dt.date(2026, 10, 20)
    await queries.halt_entries(date, "SPX", "incident-1")
    assert conn.execute.await_count == 2
    assert "max_loss_hit" not in conn.execute.await_args_list[0].args[0]
    assert json.loads(conn.execute.await_args_list[1].args[1])["reason"] == "incident-1"
    transaction.__aexit__.assert_awaited_once_with(None, None, None)

    conn.execute.side_effect = [None, RuntimeError("audit insert failed")]
    with pytest.raises(RuntimeError, match="audit insert failed"):
        await queries.halt_entries(date, "SPX", "incident-2")
    assert transaction.__aexit__.await_args.args[0] is RuntimeError


@pytest.mark.asyncio
async def test_halt_command_closes_database_on_failure(monkeypatch):
    db = Mock(initialize=AsyncMock(), close=AsyncMock())
    monkeypatch.setattr("butterfly_guy.scripts.halt_live_entries.DatabasePool", lambda _: db)
    query = Mock(halt_entries=AsyncMock(side_effect=RuntimeError("DB down")))
    monkeypatch.setattr("butterfly_guy.scripts.halt_live_entries.RiskQueries", lambda _: query)
    with pytest.raises(RuntimeError, match="DB down"):
        await halt("configs/config.yaml", "incident")
    db.close.assert_awaited_once()
