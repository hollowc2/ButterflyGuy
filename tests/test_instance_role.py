from __future__ import annotations

import json
import sys
from unittest.mock import Mock

import pytest

from butterfly_guy.core import instance_role as role_guard
from butterfly_guy.core.config import AppConfig, DatabaseSettings, ExecutionSettings
from butterfly_guy.core.instance_role import (
    InstanceRoleError,
    check_config,
    check_database,
    instance_role,
)
from butterfly_guy.notify import send_alertmanager
from butterfly_guy.scripts import run_live
from butterfly_guy.services.notifier import AlertmanagerNotifier, TelegramNotifier


def _config(*, paper: bool, db: str = "butterfly_guy") -> AppConfig:
    return AppConfig(
        execution=ExecutionSettings(paper_trading=paper, allow_live_trading=not paper),
        database=DatabaseSettings(name=db),
    )


class FakePool:
    def __init__(self, *results):
        self.results = list(results)
        self.queries: list[str] = []

    async def fetchval(self, query, *args):
        self.queries.append(query)
        return self.results.pop(0)


@pytest.mark.parametrize("value", [None, "", "  "])
def test_unset_or_empty_role_is_none(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(role_guard.ROLE_ENV, raising=False)
    else:
        monkeypatch.setenv(role_guard.ROLE_ENV, value)
    assert instance_role() is None


@pytest.mark.parametrize("value", ["paper", "live", "live_rehearsal"])
def test_known_roles_are_returned(monkeypatch, value):
    monkeypatch.setenv(role_guard.ROLE_ENV, value)
    assert instance_role() == value


def test_surrounding_whitespace_is_tolerated(monkeypatch):
    monkeypatch.setenv(role_guard.ROLE_ENV, " paper ")
    assert instance_role() == "paper"


@pytest.mark.parametrize("value", ["LIVE", "prod", "paper,live"])
def test_unknown_role_refuses(monkeypatch, value):
    monkeypatch.setenv(role_guard.ROLE_ENV, value)
    with pytest.raises(InstanceRoleError, match="is not one of"):
        instance_role()


@pytest.mark.parametrize(
    ("role", "paper", "db"),
    [
        (None, True, "butterfly_guy"),
        (None, False, "butterfly_guy"),  # unset: today's behavior, no check
        ("paper", True, "butterfly_guy"),
        ("live", False, "butterfly_guy_spx_live"),
        ("live_rehearsal", True, "butterfly_guy_spx_live_rehearsal"),
    ],
)
def test_config_accepts_matching_roles(role, paper, db):
    check_config(_config(paper=paper, db=db), role)


@pytest.mark.parametrize(
    ("role", "paper", "db", "match"),
    [
        ("paper", False, "butterfly_guy", "role=paper but execution.paper_trading is false"),
        ("live", True, "butterfly_guy_spx_live", "role=live but execution.paper_trading is true"),
        ("live", False, "butterfly_guy", "must not use the paper database"),
        (
            "live_rehearsal",
            False,
            "butterfly_guy_spx_live_rehearsal",
            "role=live_rehearsal but execution.paper_trading is false",
        ),
        ("live_rehearsal", True, "butterfly_guy", "must not use the paper database"),
    ],
)
def test_config_refuses_mismatched_roles(role, paper, db, match):
    with pytest.raises(InstanceRoleError, match=match):
        check_config(_config(paper=paper, db=db), role)


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [None, "paper", "live_rehearsal"])
async def test_database_check_makes_no_query_unless_live(role):
    pool = FakePool()
    await check_database(pool, role)
    assert pool.queries == []


@pytest.mark.asyncio
async def test_live_database_check_allows_brand_new_database():
    pool = FakePool(False)
    await check_database(pool, "live")
    assert len(pool.queries) == 1  # only the table-exists probe


@pytest.mark.asyncio
async def test_live_database_check_allows_live_only_history():
    pool = FakePool(True, 0)
    await check_database(pool, "live")
    assert "paper_fill_model" in pool.queries[1]


@pytest.mark.asyncio
async def test_live_database_check_refuses_any_paper_trade():
    pool = FakePool(True, 3)
    with pytest.raises(InstanceRoleError, match="holds 3 paper trade"):
        await check_database(pool, "live")


def _patch_main(monkeypatch, config, pool):
    """Stub main()'s collaborators; record what ran before the guard stopped it."""
    calls: list[str] = []

    class FakeDatabasePool:
        def __init__(self, dsn):
            calls.append("DatabasePool")
            self.pool = pool

        async def initialize(self):
            calls.append("db.initialize")

        async def close(self):
            calls.append("db.close")

    async def run_migrations(db):
        calls.append("run_migrations")

    def schwab(*args, **kwargs):
        calls.append("SchwabClientWrapper")
        return Mock()

    monkeypatch.setattr(sys, "argv", ["run_live"])
    monkeypatch.setattr(run_live, "load_config", lambda path: config)
    monkeypatch.setattr(run_live, "setup_logging", lambda *a, **k: None)
    monkeypatch.setattr(run_live, "_assert_live_config_supported", lambda *a: None)
    monkeypatch.setattr(
        run_live, "start_metrics_server", lambda *a, **k: calls.append("metrics")
    )
    monkeypatch.setattr(run_live, "DatabasePool", FakeDatabasePool)
    monkeypatch.setattr(run_live, "run_migrations", run_migrations)
    monkeypatch.setattr(run_live, "SchwabClientWrapper", schwab)
    return calls


@pytest.mark.asyncio
async def test_main_config_refusal_happens_before_db_and_schwab(monkeypatch):
    monkeypatch.setenv(role_guard.ROLE_ENV, "live")
    calls = _patch_main(monkeypatch, _config(paper=True, db="butterfly_guy_spx_live"), None)

    with pytest.raises(SystemExit) as exc:
        await run_live.main()

    assert exc.value.code == 2
    assert calls == []


@pytest.mark.asyncio
async def test_main_database_refusal_happens_before_migrations_and_schwab(monkeypatch):
    monkeypatch.setenv(role_guard.ROLE_ENV, "live")
    pool = FakePool(True, 1)
    calls = _patch_main(monkeypatch, _config(paper=False, db="butterfly_guy_spx_live"), pool)

    with pytest.raises(SystemExit) as exc:
        await run_live.main()

    assert exc.value.code == 2
    assert calls == ["metrics", "DatabasePool", "db.initialize", "db.close"]


@pytest.mark.asyncio
async def test_main_unset_role_reads_nothing_extra_before_migrations(monkeypatch):
    monkeypatch.delenv(role_guard.ROLE_ENV, raising=False)
    pool = FakePool()  # any guard query would pop from an empty list and fail
    calls = _patch_main(monkeypatch, _config(paper=True), pool)
    monkeypatch.setattr(
        run_live, "SchwabClientWrapper", Mock(side_effect=RuntimeError("stop here"))
    )

    with pytest.raises(RuntimeError, match="stop here"):
        await run_live.main()

    assert pool.queries == []
    assert calls == ["metrics", "DatabasePool", "db.initialize", "run_migrations", "db.close"]


def _capture_alert(monkeypatch):
    requests = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def urlopen(request, timeout):
        requests.append(json.loads(request.data)[0])
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    return requests


def test_alert_role_label_separates_paper_and_live(monkeypatch):
    requests = _capture_alert(monkeypatch)

    send_alertmanager("http://am:9093", "reconciliation_failure", "spx")
    send_alertmanager("http://am:9093", "reconciliation_failure", "spx", instance_role="live")
    send_alertmanager("http://am:9093", "reconciliation_failure", "spx", instance_role="paper")

    unset, live, paper = requests
    assert "instance_role" not in unset["labels"]
    assert unset["annotations"]["summary"] == "ButterflyGuy SPX reconciliation failure"
    assert live["labels"]["instance_role"] == "live"
    assert live["annotations"]["summary"] == "ButterflyGuy SPX live reconciliation failure"
    assert {k: v for k, v in live["labels"].items() if k != "instance_role"} == unset["labels"]
    assert live["labels"] != paper["labels"]


@pytest.mark.asyncio
async def test_alertmanager_notifier_passes_role_only_when_set(monkeypatch):
    calls = []

    def fake_send(*args, **kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr("butterfly_guy.notify.send_alertmanager", fake_send)

    async def to_thread(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr("butterfly_guy.services.notifier.asyncio.to_thread", to_thread)

    await AlertmanagerNotifier("http://am:9093", "spx").notify_critical("broker_ambiguity")
    await AlertmanagerNotifier("http://am:9093", "spx", instance_role="live").resolve_critical(
        "broker_ambiguity"
    )

    assert calls == [{}, {"resolved": True, "instance_role": "live"}]


@pytest.mark.asyncio
@pytest.mark.parametrize(("role", "header"), [(None, "⚠️ SPX RISK"), ("live", "⚠️ [LIVE] SPX RISK")])
async def test_telegram_risk_warning_carries_role_prefix(monkeypatch, role, header):
    sent = Mock(return_value=True)
    monkeypatch.setattr("butterfly_guy.notify.send", sent)

    await TelegramNotifier(instance_role=role).notify_consecutive_loss_warning(
        "SPX", 10, [-1.0] * 10
    )

    assert sent.call_args.args[0].startswith(header)

