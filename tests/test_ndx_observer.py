"""Observer admission/lifecycle and restricted-role checks; synthetic transport only."""

import asyncio
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import asyncpg
import httpx
import pytest

from butterfly_guy.research.ndx_observer import (
    Acquisition,
    ObserverLimits,
    create_observer,
)
from butterfly_guy.research.ndx_postgres_recording import PostgresRecorder
from tests.test_ndx_postgres_recording import (
    BODY,
    PACKAGE,
    UNIVERSE,
    capture,
    postgres_cluster,  # noqa: F401
)
from tests.test_ndx_postgres_recording import pg as postgres_fixture

pg = postgres_fixture


def acquisition(**overrides):
    fields = dict(snapshot_id="synthetic-snapshot", record_id="synthetic-record",
        request_id="synthetic-request", pass_id="synthetic-pass", acquisition_id="synthetic",
        session=UNIVERSE["session"], expected_symbols=tuple(UNIVERSE["symbols"]),
        calendar="synthetic-calendar", close_utc="2030-01-02T21:00:00+00:00",
        build_sha256="1" * 64, config_sha256="2" * 64, consumer="synthetic-reader",
        evidence_kind="synthetic")
    return Acquisition(**(fields | overrides))


def observer(params, *, handler=None, **kwargs):
    return create_observer(enabled=True, connection_factory=lambda: dict(params),
        gateway_url="https://synthetic.invalid", gateway_api_key="synthetic-test-key",
        transport=httpx.MockTransport(handler or (lambda r: httpx.Response(200, content=BODY))),
        **kwargs)


def test_disabled_factory_does_not_construct_or_inspect_dependencies(monkeypatch):
    forbidden = Mock(side_effect=AssertionError("disabled observer touched dependency"))
    monkeypatch.setattr(asyncpg, "create_pool", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "__init__", forbidden)
    monkeypatch.setattr(asyncio, "create_task", forbidden)
    assert create_observer(connection_factory=forbidden, limits=object()) is None
    forbidden.assert_not_called()


@pytest.mark.asyncio
async def test_disabled_executable_ignores_context_and_secrets(monkeypatch):
    from butterfly_guy.research import ndx_observer_cli
    forbidden = Mock(side_effect=AssertionError("disabled entry point inspected dependencies"))
    monkeypatch.delenv("NDX_OBSERVER_ENABLED", raising=False)
    monkeypatch.setattr(ndx_observer_cli, "create_observer", forbidden)
    monkeypatch.setattr(ndx_observer_cli.Path, "read_text", forbidden)
    assert await ndx_observer_cli.main() == {"status": "disabled"}
    forbidden.assert_not_called()


@pytest.mark.parametrize("change", [dict(snapshot_id="secret value with spaces"),
    dict(build_sha256="unknown"), dict(expected_symbols=("NDX",)),
    dict(close_utc="2030-01-02T21:00:00"), dict(version=2)])
def test_acquisition_requires_explicit_identity(change):
    with pytest.raises(ValueError):
        acquisition(**change)


@pytest.mark.asyncio
async def test_clean_success_and_restart_inventory(pg):
    recorder, params = pg
    requests = []
    def handle(request):
        requests.append(request.url.path)
        return httpx.Response(200, content=BODY)
    item = observer(params, handler=handle)
    await item.start()
    result = await item.acquire(acquisition())
    assert result.quote_status == "success" and result.publication.published
    assert result.receipt["response"] == BODY and result.receipt["receipt_journaled"]
    assert not result.receipt["assessment"]["replay_eligible"]
    duplicate = await item.acquire(acquisition())
    assert duplicate.quote_status == "success" and not duplicate.publication.published
    assert item.counts["published"] == 1  # Duplicate is not additional coverage.
    assert requests == ["/v1/option-chain"] * 2
    assert item.retained_bytes == 0 and item.peak_retained_bytes == len(BODY)
    await item.close()
    restarted = observer(params)
    await restarted.start()
    try:
        inventory = await restarted.recorder.recovery_inventory()
        assert len(inventory) == 2 and all(r["published"] for r in inventory)
        assert restarted.instance_id != item.instance_id
        assert restarted.clock.domain != item.clock.domain
    finally:
        await restarted.close()
    assert len(await recorder.pool.fetch("SELECT * FROM ndx_provenance_v1.publications")) == 1


@pytest.mark.asyncio
async def test_singleton_and_dead_lease_fail_before_gateway(pg):
    recorder, params = pg
    item, other = observer(params), observer(params)
    await item.start()
    try:
        with pytest.raises(RuntimeError, match="already active"):
            await other.start()
        pid = await item.lease.fetchval("SELECT pg_backend_pid()")
        await recorder.pool.execute("SELECT pg_terminate_backend($1)", pid)
        result = await item.acquire(acquisition())
        assert result.quote is None and not item.counts["requests_started"]
    finally:
        # Terminated lease can fail unlock; close still terminates its own pool.
        try:
            await item.close()
        except asyncpg.InterfaceError:
            pass


@pytest.mark.asyncio
async def test_pending_shutdown_cancel_and_busy_admission(pg):
    _, params = pg
    entered = asyncio.Event()
    async def handle(request):
        entered.set()
        await asyncio.Event().wait()
    item = observer(params, handler=handle, limits=ObserverLimits(shutdown_seconds=.5))
    await item.start()
    task = asyncio.create_task(item.acquire(acquisition()))
    await entered.wait()
    assert (await item.acquire(acquisition())).recording_status == "busy"
    await item.close()
    assert task.cancelled() and item.state == "closed" and item.retained_bytes == 0
    assert item.counts["requests_started"] == 1 and item.counts["unresolved"] == 1


@pytest.mark.asyncio
async def test_recording_oversize_does_not_change_sdk_result(pg):
    _, params = pg
    item = observer(params, limits=ObserverLimits(body_bytes=len(BODY) - 1))
    await item.start()
    try:
        result = await item.acquire(acquisition())
        assert result.quote_status == "success" and result.recording_status == "oversized"
        assert result.publication is None and item.peak_retained_bytes == 0
    finally:
        await item.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [b'{"accountNumber":"never-store"}', b'{}'])
async def test_rejection_preserves_sdk_validation_and_safe_failure_ledger(pg, body):
    recorder, params = pg
    item = observer(params, handler=lambda r: httpx.Response(200, content=body))
    await item.start()
    try:
        result = await item.acquire(acquisition())
        assert result.quote_status == "sdk_rejected" and result.recording_status == "body_rejected"
        assert not item.counts["publication_calls"]
        rows = await recorder.pool.fetch("SELECT document FROM ndx_provenance_v1.journal")
        assert "never-store" not in str(rows)
    finally:
        await item.close()


@pytest.mark.asyncio
async def test_storage_outage_identity_and_failure_journal(pg, monkeypatch):
    _, params = pg
    item = observer(params)
    await item.start()
    async def unavailable(*args, **kwargs):
        raise OSError("must-not-appear-in-ledger")
    try:
        assert (await item.acquire(None)).recording_status == "identity_unavailable"
        monkeypatch.setattr(item.recorder, "publish", unavailable)
        result = await item.acquire(acquisition())
        assert result.quote_status == "success" and result.recording_status == "unresolved"
        monkeypatch.setattr(item.recorder, "journal", unavailable)
        result = await item.acquire(acquisition())
        assert result.quote_status == "not_requested"
        assert result.recording_status == "ledger_unavailable"
        assert item.counts["lifecycle_events_unjournaled"] == 1
    finally:
        await item.close()


@pytest.mark.asyncio
async def test_gateway_failure_and_operation_timeout(pg):
    _, params = pg
    def failure(request):
        raise httpx.ConnectError("synthetic unavailable")
    item = observer(params, handler=failure)
    await item.start()
    try:
        assert (await item.acquire(acquisition())).quote_status == "gateway_failed"
        async def blocked(request):
            await asyncio.Event().wait()
        item.client._transport = httpx.MockTransport(blocked)
        item.limits = replace(item.limits, operation_seconds=.05)
        assert (await item.acquire(acquisition())).quote_status == "interrupted"
        assert item.retained_bytes == 0
    finally:
        await item.close()


@pytest.mark.asyncio
async def test_roles_publish_receipt_and_forbidden_operations(pg):
    recorder, params = pg
    roles = (PACKAGE.parent / "observer-v1/roles.sql").read_text()
    await recorder.pool.execute(roles)
    async def role_setup(conn):
        await conn.execute("SET ROLE ndx_evidence_recorder; SET search_path=pg_catalog")
    pool = await asyncpg.create_pool(**params, min_size=1, max_size=2,
                                    command_timeout=2, setup=role_setup)
    limited = PostgresRecorder(pool)
    try:
        assert (await limited.publish(capture())).published
        assert await pool.fetchval("SELECT has_function_privilege("
            "current_user, 'pg_catalog.pg_current_xact_id()', 'EXECUTE')")
        for table in ("schema_identity", "quotes", "provenance", "publications", "journal"):
            for command in (f"UPDATE ndx_provenance_v1.{table} SET version=version",
                            f"DELETE FROM ndx_provenance_v1.{table}",
                            f"TRUNCATE ndx_provenance_v1.{table}"):
                with pytest.raises(asyncpg.PostgresError):
                    await pool.execute(command)
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await pool.execute("CREATE TABLE ndx_provenance_v1.unwanted (id int)")
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await pool.execute("ALTER TABLE ndx_provenance_v1.journal DISABLE TRIGGER ALL")
        async def reader_setup(conn):
            await conn.execute("SET ROLE ndx_evidence_reader; SET search_path=pg_catalog")
        readers = await asyncpg.create_pool(**params, min_size=1, max_size=1,
                                            command_timeout=2, setup=reader_setup)
        try:
            receipt = await PostgresRecorder(readers).read("synthetic-snapshot", 1,
                consumer="restricted-reader", build_sha256="1" * 64)
            assert receipt["receipt_journaled"]
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await readers.execute("INSERT INTO ndx_provenance_v1.quotes "
                                      "SELECT * FROM ndx_provenance_v1.quotes")
        finally:
            await readers.close()
        # Startup/lease/publication/receipt also work under the restricted role.
        restricted = observer(params)
        # Use a synthetic LOGIN with role membership; no password/production credential.
        await recorder.pool.execute("CREATE ROLE ndx_observer_fixture LOGIN "
                                    "IN ROLE ndx_evidence_recorder")
        restricted.connection_factory = lambda: dict(params, user="ndx_observer_fixture")
        await restricted.start()
        try:
            result = await restricted.acquire(acquisition(snapshot_id="role-snapshot",
                                                           record_id="role-record"))
            assert result.quote_status == "success" and result.receipt["receipt_journaled"]
        finally:
            await restricted.close()
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_cancelled_publication_recovers_without_invented_ack(pg):
    recorder, params = pg
    item = observer(params)
    await item.start()
    entered = asyncio.Event()
    async def interrupt(capture):
        await item.recorder.journal(("synthetic-snapshot", 1), "attempt", {"synthetic": True})
        entered.set()
        await asyncio.Event().wait()
    item.recorder.publish = interrupt
    task = asyncio.create_task(item.acquire(acquisition()))
    await entered.wait()
    await item.close()
    assert task.cancelled()
    inventory = await recorder.recovery_inventory()
    assert len(inventory) == 1 and not inventory[0]["published"]
    assert not inventory[0]["acknowledgement_recorded"]
    rows = await recorder.pool.fetch("SELECT document FROM ndx_provenance_v1.journal "
                                    "WHERE kind='acquisition_interrupted'")
    assert json.loads(rows[0]["document"])["reason"] == "cancelled_outcome_requires_recovery"


@pytest.mark.asyncio
async def test_pool_pressure_and_storage_budget_do_not_request_market(pg):
    _, params = pg
    item = observer(params, limits=ObserverLimits(operation_seconds=.05, journal_seconds=.02))
    await item.start()
    try:
        async with item.pool.acquire() as first, item.pool.acquire() as second:
            assert first is not second
            result = await item.acquire(acquisition())
            assert result.quote_status in ("interrupted", "not_requested")
            assert not item.counts["requests_started"]
        item.limits = replace(item.limits, storage_bytes=1)
        result = await item.acquire(acquisition())
        assert result.recording_status == "storage_budget"
        assert not item.counts["requests_started"]
    finally:
        await item.close()


@pytest.mark.asyncio
async def test_startup_failure_and_shutdown_timeout_are_bounded(pg, monkeypatch):
    _, params = pg
    item = observer(params, limits=ObserverLimits(shutdown_seconds=.05))
    await item.start()
    async def hang(*args, **kwargs):
        await asyncio.Event().wait()
    monkeypatch.setattr(item.recorder, "journal", hang)
    started = asyncio.get_running_loop().time()
    await item.close()
    assert asyncio.get_running_loop().time() - started < .5
    assert item.counts["shutdown_incomplete"] == 1 and item.state == "closed"
    # New instance can acquire the released backend lock after forced pool termination.
    other = observer(params)
    await other.start()
    await other.close()
    broken = observer(params)
    broken.gateway_api_key = ""  # Preserve the SDK's normal constructor validation.
    with pytest.raises(ValueError, match="API key"):
        await broken.start()
    assert broken.state == "closed"


@pytest.mark.asyncio
async def test_concurrent_publication_out_of_order_and_lock_timeout(pg):
    recorder, _ = pg
    results = await asyncio.gather(recorder.publish(capture()), recorder.publish(capture()))
    assert sum(result.published is True for result in results) == 1
    assert any(result.failure == "duplicate_identity" for result in results)
    # Corrected version cannot arrive before its parent exists.
    saved = capture()
    doc = saved.document | {"snapshot_id": "later", "record_id": "later-correction",
        "version": 2, "parent_document_sha256": "0" * 64}
    from butterfly_guy.research.ndx_native_response import NativeCapture
    from butterfly_guy.research.ndx_recording import encode
    assert not (await recorder.publish(NativeCapture(saved.body, encode(doc)))).published
    async with recorder.pool.acquire() as blocker:
        async with blocker.transaction():
            await blocker.execute("LOCK TABLE ndx_provenance_v1.quotes IN ACCESS EXCLUSIVE MODE")
            result = await recorder.publish(saved)
            assert result.published is False and result.failure == "recording_failed:quote_copy"


@pytest.mark.asyncio
async def test_observer_process_crash_releases_lease_and_keeps_durable_attempt(pg):
    recorder, params = pg
    # Kill only the newly spawned synthetic observer, after its durable attempt.
    code = '''
import asyncio, json, os, sys
from tests.test_ndx_observer import observer, acquisition
async def main():
    item = observer(json.loads(sys.argv[1]))
    await item.start()
    async def crash(capture):
        await item.recorder.journal(("synthetic-snapshot", 1), "attempt", {"synthetic": True})
        os._exit(19)
    item.recorder.publish = crash
    await item.acquire(acquisition())
asyncio.run(main())
'''
    process = await asyncio.create_subprocess_exec(sys.executable, "-c", code, json.dumps(params),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await asyncio.wait_for(process.communicate(), 10)
    assert process.returncode == 19, (stdout, stderr)
    inventory = await recorder.recovery_inventory()
    assert len(inventory) == 1 and not inventory[0]["published"]
    assert not inventory[0]["acknowledgement_recorded"]
    item = observer(params)
    await item.start()
    await item.close()


@pytest.mark.asyncio
async def test_owned_database_restart_preserves_publications_and_reconnects(pg):
    recorder, params = pg
    assert (await recorder.publish(capture())).published
    previous = observer(params)
    await previous.start()
    if os.environ.get("NDX_TIMESCALE_SOCKET"):
        name = Path(params["host"]).parent.name
        assert name.startswith("ndx-timescale-")
        # Restart PostgreSQL inside the owned container, preserving its tmpfs.
        command = ["docker", "exec", "--user", "postgres", name, "pg_ctl",
                   "-D", "/var/lib/postgresql/data", "-l", "/tmp/ndx-restart.log",
                   "-m", "fast", "-w", "restart"]
    else:
        root = Path(params["host"]).parent
        command = [str(Path(os.environ["NDX_POSTGRES_BIN"]) / "pg_ctl"),
                   "-D", str(root / "data"), "-l", str(root / "postgres.log"),
                   "-m", "fast", "-w", "restart"]
    result = await asyncio.to_thread(subprocess.run, command, capture_output=True,
                                    text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    # Old idle connections can report a single terminated-session error. Retry only
    # the recovery DB read, never a gateway request or publication.
    for attempt in range(20):
        try:
            inventory = await recorder.recovery_inventory()
            break
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError):
            await asyncio.sleep(.1)
    else:
        pytest.fail("task-owned DB did not recover")
    assert inventory[0]["published"] and inventory[0]["acknowledgement_recorded"]
    assert (await previous.acquire(acquisition())).quote_status == "interrupted"
    assert not previous.counts["requests_started"]
    await previous.close()
    replacement = observer(params)
    await replacement.start()
    try:
        result = await replacement.acquire(acquisition())
        assert result.quote_status == "success"
        assert result.publication.failure == "duplicate_identity"
    finally:
        await replacement.close()
