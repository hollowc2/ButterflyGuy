"""Real PostgreSQL engine tests on a new Unix-socket-only cluster, never a supplied DSN."""

import asyncio
import copy
import json
import os
import shlex
import subprocess
import tempfile
import uuid
from pathlib import Path

import asyncpg
import httpx
import pytest

from butterfly_guy.research.ndx_evidence import read_json
from butterfly_guy.research.ndx_native_response import NativeCapture, preserve_buffered_response
from butterfly_guy.research.ndx_postgres_recording import (
    PostgresRecorder,
    ResearchGatewayHTTPClient,
    install_empty_schema,
)
from butterfly_guy.research.ndx_provenance import ROOT
from butterfly_guy.research.ndx_recording import encode

PACKAGE = ROOT / "docs/research/ndx-strategy/postgres-v1"
BODY = (PACKAGE / "native-synthetic.json").read_bytes()
UNIVERSE = read_json(PACKAGE / "universe.json")


def capture():
    response = httpx.Response(200, content=BODY,
        request=httpx.Request("GET", "https://synthetic.invalid/v1/option-chain"))
    return preserve_buffered_response(response, snapshot_id="synthetic-snapshot",
        record_id="synthetic-record", request_id="synthetic-request", pass_id="synthetic-pass",
        acquisition_id="synthetic", expected_symbols=UNIVERSE["symbols"],
        session=UNIVERSE["session"], evidence_kind="synthetic")


@pytest.fixture(scope="session")
def postgres_cluster():
    binary = os.environ.get("NDX_POSTGRES_BIN")
    if not binary:
        pytest.skip("NDX_POSTGRES_BIN required for isolated PostgreSQL tests")
    binaries = Path(binary)
    root = Path(tempfile.mkdtemp(prefix="ndx-pg-"))
    data, sockets = root / "data", root / "socket"
    sockets.mkdir(mode=0o700)
    subprocess.run([str(binaries / "initdb"), "-D", str(data), "-A", "trust",
                    "-U", "ndx_research_test", "--no-locale", "-E", "UTF8"],
                   check=True, capture_output=True, text=True)
    options = shlex.join(["-c", "listen_addresses=", "-k", str(sockets), "-p", "55483"])
    subprocess.run([str(binaries / "pg_ctl"), "-D", str(data), "-l", str(root / "postgres.log"),
                    "-o", options, "-w", "start"], check=True, capture_output=True, text=True)
    try:
        yield {"host": str(sockets), "port": 55483, "user": "ndx_research_test",
               "database": "postgres"}
    finally:
        # Stop only this newly created test process; preserve its cluster/logs for review.
        subprocess.run([str(binaries / "pg_ctl"), "-D", str(data), "-m", "fast", "-w", "stop"],
                       check=True, capture_output=True, text=True)


@pytest.fixture
async def pg(postgres_cluster):
    params = dict(postgres_cluster)
    admin = await asyncpg.connect(**params)
    name = "ndx_test_" + uuid.uuid4().hex
    await admin.execute(f'CREATE DATABASE "{name}"')
    await admin.close()
    params["database"] = name
    pool = await asyncpg.create_pool(**params, min_size=1, max_size=5, command_timeout=5)
    async with pool.acquire() as conn:
        await install_empty_schema(conn)
    try:
        yield PostgresRecorder(pool), params
    finally:
        await pool.close()


async def read(recorder):
    return await recorder.read("synthetic-snapshot", 1, consumer="synthetic-test",
                               build_sha256="1"*64)


@pytest.mark.asyncio
async def test_real_atomic_publication_and_native_body_roundtrip(pg):
    recorder, _ = pg
    saved = capture()
    result = await recorder.publish(saved)
    assert result.published and result.acknowledgement_recorded
    receipt = await read(recorder)
    assert receipt["response"] == BODY
    assert receipt["document"]["selected"] == saved.document["selected"]
    assert receipt["document"]["transaction_id"].isdigit()
    assert receipt["commit_ack"] is not None
    assert receipt["receipt_journaled"]
    assert receipt["assessment"]["status"] == "insufficient"
    assert not receipt["assessment"]["replay_eligible"]
    assert receipt["assessment"]["decision"] is None


@pytest.mark.asyncio
async def test_metadata_failure_rolls_back_quote_copy_and_keeps_legacy_outcome(pg):
    recorder, _ = pg
    await recorder.pool.execute("""
        CREATE FUNCTION fail_metadata() RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'injected metadata failure'; END; $$;
        CREATE TRIGGER fail_metadata BEFORE INSERT ON ndx_provenance_v1.provenance
        FOR EACH ROW EXECUTE FUNCTION fail_metadata();
    """)
    result = await recorder.publish(capture(), legacy_quote_write="success")
    assert result.published is False and result.failure == "recording_failed:metadata_copy"
    for table in ("quotes", "provenance", "publications"):
        assert await recorder.pool.fetchval(f"SELECT count(*) FROM ndx_provenance_v1.{table}") == 0
    failure = json.loads(await recorder.pool.fetchval(
        "SELECT document FROM ndx_provenance_v1.journal "
                                                     "WHERE kind='publication_failed'"))
    assert failure["legacy_quote_write"] == "success"
    assert await read(recorder) is None


@pytest.mark.asyncio
async def test_deferred_server_commit_failure_is_known_rollback(pg):
    recorder, _ = pg
    await recorder.pool.execute("""
        CREATE FUNCTION fail_commit() RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'deferred commit failure' USING ERRCODE='23514'; END; $$;
        CREATE CONSTRAINT TRIGGER fail_commit AFTER INSERT ON ndx_provenance_v1.publications
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fail_commit();
    """)
    result = await recorder.publish(capture())
    assert result.published is False and result.failure == "recording_failed:commit"
    assert await recorder.pool.fetchval(
                "SELECT count(*) FROM ndx_provenance_v1.quotes") == 0
    assert not (await recorder.recovery_inventory())[0]["published"]


@pytest.mark.asyncio
async def test_commit_reply_loss_stays_unknown_until_inventory(pg, monkeypatch):
    recorder, _ = pg
    pool = recorder.pool
    original_acquire = pool.acquire
    class Transaction:
        def __init__(self, transaction):
            self.transaction = transaction
        async def __aenter__(self):
            return await self.transaction.__aenter__()
        async def __aexit__(self, *args):
            await self.transaction.__aexit__(*args)
            # Server COMMIT actually completed; inject loss of that acknowledgement.
            if args[0] is None:
                raise asyncpg.ConnectionDoesNotExistError("synthetic lost COMMIT reply")
    class Connection:
        def __init__(self, conn):
            self.conn = conn
        def __getattr__(self, name):
            return getattr(self.conn, name)
        def transaction(self):
            return Transaction(self.conn.transaction())
    class Acquire:
        async def __aenter__(self):
            self.ctx = original_acquire()
            return Connection(await self.ctx.__aenter__())
        async def __aexit__(self, *args):
            return await self.ctx.__aexit__(*args)
    class Pool:
        def __getattr__(self, name):
            return getattr(pool, name)
        def acquire(self):
            return Acquire()
    monkeypatch.setattr(recorder, "pool", Pool())
    result = await recorder.publish(capture())
    assert result.published is None and result.failure == "commit_outcome_unknown"
    monkeypatch.setattr(recorder, "pool", pool)
    inventory = await recorder.recovery_inventory()
    assert inventory[0]["published"] and not inventory[0]["acknowledgement_recorded"]
    assert (await read(recorder))["commit_ack"] is None


@pytest.mark.asyncio
async def test_lost_ack_receipt_and_recreated_reader_are_separate(pg, monkeypatch):
    recorder, _ = pg
    original = recorder.journal
    async def fail_ack(key, kind, detail):
        if kind in ("commit_ack", "consumer_receipt"):
            raise asyncpg.PostgresError("synthetic journal failure")
        return await original(key, kind, detail)
    monkeypatch.setattr(recorder, "journal", fail_ack)
    result = await recorder.publish(capture())
    assert result.published and not result.acknowledgement_recorded
    receipt = await read(recorder)
    assert receipt is not None and not receipt["receipt_journaled"]
    other = PostgresRecorder(recorder.pool)
    assert other.clock.domain != recorder.clock.domain
    recovered = await read(other)
    assert recovered["commit_ack"] is None
    assert recovered["receipt_journaled"]


@pytest.mark.asyncio
async def test_duplicate_and_parent_link_refuse_overwrite(pg):
    recorder, _ = pg
    saved = capture()
    assert (await recorder.publish(saved)).published
    assert (await recorder.publish(saved)).failure == "duplicate_identity"
    document = copy.deepcopy(saved.document)
    document.update(version=2, record_id="synthetic-correction", parent_document_sha256="0" * 64)
    assert (await recorder.publish(NativeCapture(BODY, encode(document)))).published is False
    document["parent_document_sha256"] = await recorder.pool.fetchval(
        "SELECT sha256 FROM ndx_provenance_v1.provenance")
    assert (await recorder.publish(NativeCapture(BODY, encode(document)))).published
    assert await recorder.pool.fetchval("SELECT count(*) FROM ndx_provenance_v1.publications") == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("table", ["quotes", "provenance", "publications", "journal"])
async def test_real_append_only_and_truncate_refusal(pg, table):
    recorder, _ = pg
    assert (await recorder.publish(capture())).published
    for sql in (f"DELETE FROM ndx_provenance_v1.{table}",
                f"UPDATE ndx_provenance_v1.{table} SET version=version",
                f"TRUNCATE ndx_provenance_v1.{table} CASCADE"):
        with pytest.raises(asyncpg.PostgresError):
            await recorder.pool.execute(sql)


@pytest.mark.asyncio
async def test_schema_reinstall_and_drift_refuse(pg):
    recorder, _ = pg
    async with recorder.pool.acquire() as conn:
        with pytest.raises(asyncpg.DuplicateSchemaError):
            await install_empty_schema(conn)
    await recorder.pool.execute("UPDATE ndx_provenance_v1.schema_identity SET sql_sha256='wrong'")
    with pytest.raises(ValueError, match="schema identity mismatch"):
        await recorder.publish(capture())


@pytest.mark.asyncio
async def test_reader_cannot_see_uncommitted_quote_and_metadata(pg):
    recorder, _ = pg
    await recorder.pool.execute("""
        CREATE FUNCTION pause_metadata() RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN PERFORM pg_advisory_xact_lock(918273); RETURN NEW; END; $$;
        CREATE TRIGGER pause_metadata BEFORE INSERT ON ndx_provenance_v1.provenance
        FOR EACH ROW EXECUTE FUNCTION pause_metadata();
    """)
    async with recorder.pool.acquire() as blocker:
        await blocker.execute("SELECT pg_advisory_lock(918273)")
        task = asyncio.create_task(recorder.publish(capture()))
        try:
            for _ in range(50):
                if await recorder.pool.fetchval("SELECT count(*) FROM pg_stat_activity "
                    "WHERE wait_event='advisory' AND datname=current_database()"):
                    break
                await asyncio.sleep(.005)
            else:
                pytest.fail("writer did not reach metadata barrier")
            assert await read(recorder) is None
            assert await recorder.pool.fetchval(
                "SELECT count(*) FROM ndx_provenance_v1.quotes") == 0
        finally:
            await blocker.execute("SELECT pg_advisory_unlock(918273)")
            result = await task
        assert result.published
    assert (await read(recorder))["receipt_journaled"]


@pytest.mark.asyncio
async def test_sdk_native_to_postgres_end_to_end_has_no_extra_request(pg):
    import datetime as dt

    from schwab_gateway_sdk.client import GatewayMarketDataClient
    recorder, _ = pg
    calls = []
    def handle(request):
        calls.append(request.url.path)
        return httpx.Response(200, content=BODY)
    def context():
        return {k: v for k, v in capture().document.items() if k in (
            "snapshot_id", "record_id", "request_id", "pass_id", "acquisition_id",
            "expected_symbols", "session", "evidence_kind")}
    async with ResearchGatewayHTTPClient(base_url="https://synthetic.invalid",
            transport=httpx.MockTransport(handle), recorder=recorder,
            context_factory=context) as client:
        sdk = GatewayMarketDataClient(
            "https://synthetic.invalid", "synthetic-test-key", client=client)
        await sdk.get_option_chain("$NDX", dt.date(2030, 1, 2))
        assert client.recording_failures == 0
    assert calls == ["/v1/option-chain"]
    assert (await read(recorder))["response"] == BODY


@pytest.mark.asyncio
async def test_backend_termination_before_commit_rolls_back(pg):
    recorder, _ = pg
    await recorder.pool.execute("""
        CREATE FUNCTION pause_metadata() RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN PERFORM pg_advisory_xact_lock(918274); RETURN NEW; END; $$;
        CREATE TRIGGER pause_metadata BEFORE INSERT ON ndx_provenance_v1.provenance
        FOR EACH ROW EXECUTE FUNCTION pause_metadata();
    """)
    async with recorder.pool.acquire() as blocker:
        await blocker.execute("SELECT pg_advisory_lock(918274)")
        task = asyncio.create_task(recorder.publish(capture()))
        try:
            pid = None
            for _ in range(50):
                pid = await recorder.pool.fetchval("SELECT pid FROM pg_stat_activity "
                    "WHERE wait_event='advisory' AND datname=current_database()")
                if pid:
                    break
                await asyncio.sleep(.005)
            assert pid
            await blocker.execute("SELECT pg_terminate_backend($1)", pid)
            result = await task
            assert result.published is False
        finally:
            await blocker.execute("SELECT pg_advisory_unlock(918274)")
    assert await recorder.pool.fetchval("SELECT count(*) FROM ndx_provenance_v1.quotes") == 0
    inventory = await recorder.recovery_inventory()
    assert not inventory[0]["published"] and not inventory[0]["acknowledgement_recorded"]


@pytest.mark.asyncio
async def test_rejected_native_body_is_a_failure_event_not_a_quote(pg):
    recorder, _ = pg
    def context():
        return {k: v for k, v in capture().document.items() if k in (
            "snapshot_id", "record_id", "request_id", "pass_id", "acquisition_id",
            "expected_symbols", "session", "evidence_kind")}
    async with ResearchGatewayHTTPClient(base_url="https://synthetic.invalid",
            transport=httpx.MockTransport(lambda r: httpx.Response(200,
                json={"accountNumber": "must-never-be-persisted"})), recorder=recorder,
            context_factory=context) as client:
        await client.get("/v1/option-chain")
        assert client.recording_failures == 1
    events = await recorder.pool.fetch("SELECT document FROM ndx_provenance_v1.journal")
    assert len(events) == 1 and "must-never-be-persisted" not in str(events)
    assert await recorder.pool.fetchval("SELECT count(*) FROM ndx_provenance_v1.quotes") == 0
