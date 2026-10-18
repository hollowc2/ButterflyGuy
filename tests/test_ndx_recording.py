"""Real isolated SQLite transaction/failure/restart checks. No broker or live DB."""

import copy
import json
import sqlite3

import pytest

from butterfly_guy.research.ndx_evidence import read_json
from butterfly_guy.research.ndx_provenance import ROOT, assess
from butterfly_guy.research.ndx_recording import Recorder, check_body, export_receipt

PACKAGE = ROOT / "docs/research/ndx-strategy/provenance-v1"
RECORD = json.loads((PACKAGE / "fixtures.jsonl").read_text().splitlines()[1])
BODY = (PACKAGE / RECORD["payload"]["path"]).read_bytes()
BUILD = "1" * 64


@pytest.fixture
def recorder(tmp_path):
    instance = Recorder(tmp_path / "research.sqlite", create=True)
    yield instance
    instance.close()


def read(recorder):
    return recorder.read(RECORD["snapshot_id"], 1, consumer="isolated-test", build_sha256=BUILD)


def test_atomic_publish_read_and_exact_bytes(recorder, tmp_path):
    result = recorder.publish(RECORD, BODY)
    assert result.published and result.acknowledgement_recorded
    receipt = read(recorder)
    assert receipt["response"] == BODY
    assert receipt["receipt_journaled"]
    assert receipt["record"]["legs"] == RECORD["legs"]
    assert receipt["record"]["stamps"]["commit_ack"] is not None
    files = export_receipt(receipt, tmp_path / "export")
    assert "response.json" in files
    exported = read_json(tmp_path / "export" / "assessment.json")
    assert exported["raw_composites"]["provider_mark"] == "-4.02"
    assert exported["raw_composites"]["bid"] == "-4.40"
    assert exported["status"] == "insufficient"  # Actual clocks are explicitly unattested.
    assert not exported["rejected"]
    assert not exported["freshness_verified"] and not exported["replay_eligible"]
    assert exported["decision"] is exported["fill"] is None
    with pytest.raises(FileExistsError):
        export_receipt(receipt, tmp_path / "export")


def test_metadata_failure_rolls_back_quote_copy_and_preserves_external_success(recorder):
    recorder.connection.executescript("""
        CREATE TRIGGER fail_metadata BEFORE INSERT ON provenance BEGIN
            SELECT RAISE(ABORT, 'injected metadata failure'); END;
    """)
    result = recorder.publish(RECORD, BODY, legacy_quote_write="success")
    assert not result.published
    for table in ("quotes", "provenance", "publications"):
        assert recorder.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    events = recorder.connection.execute("SELECT kind, document FROM journal").fetchall()
    assert [e[0] for e in events] == ["attempt", "publication_failed"]
    assert json.loads(events[-1][1])["legacy_quote_write"] == "success"
    assert read(recorder) is None


def test_commit_failure_rolls_back_and_records_no_ack(recorder):
    # A deferred foreign key fails at COMMIT after all three inserts succeed.
    recorder.connection.executescript("""
        CREATE TABLE commit_guard (id INTEGER PRIMARY KEY);
        CREATE TABLE deferred_failure (
            id INTEGER REFERENCES commit_guard(id) DEFERRABLE INITIALLY DEFERRED);
        CREATE TRIGGER inject_commit_failure AFTER INSERT ON publications BEGIN
            INSERT INTO deferred_failure VALUES (1); END;
    """)
    result = recorder.publish(RECORD, BODY)
    assert not result.published
    assert recorder.connection.execute("SELECT COUNT(*) FROM quotes").fetchone()[0] == 0
    assert recorder.connection.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 0
    assert all(not row[3] and not row[4] for row in recorder.recovery_inventory())


def test_post_commit_ack_failure_and_restart_leave_ack_unknown(recorder, monkeypatch):
    original = recorder.journal
    def fail_ack(snapshot, version, kind, detail):
        if kind == "commit_ack":
            raise sqlite3.OperationalError("injected lost ack")
        original(snapshot, version, kind, detail)
    monkeypatch.setattr(recorder, "journal", fail_ack)
    result = recorder.publish(RECORD, BODY)
    assert result.published and not result.acknowledgement_recorded
    assert result.failure == "commit_ack_journal_unavailable"
    other = Recorder(recorder.path)
    try:
        assert other.clock.domain != recorder.clock.domain
        inventory = other.recovery_inventory()
        assert inventory[0][3:] == (1, 0)
        receipt = read(other)
        assert receipt["record"]["stamps"]["commit_ack"] is None
        assert receipt["record"]["stamps"]["publication_ack"] is None
        assert other.publish(RECORD, BODY).failure == "duplicate_or_constraint"
    finally:
        other.close()


def test_lost_receipt_journal_does_not_turn_read_into_missing_quote(recorder, monkeypatch):
    assert recorder.publish(RECORD, BODY).published
    original = recorder.journal
    def fail_receipt(snapshot, version, kind, detail):
        if kind == "consumer_receipt":
            raise sqlite3.OperationalError("injected receipt journal failure")
        original(snapshot, version, kind, detail)
    monkeypatch.setattr(recorder, "journal", fail_receipt)
    receipt = read(recorder)
    assert receipt is not None and not receipt["receipt_journaled"]
    assert receipt["record"]["consumer"]["read_status"] == "success"


def test_restart_after_ack_and_complete_snapshot_visibility(recorder, tmp_path):
    other = Recorder(recorder.path)
    try:
        assert read(other) is None
        assert recorder.publish(RECORD, BODY).published
        receipt = read(other)
        assert receipt["record"]["stamps"]["commit_ack"] is not None
        assert recorder.clock.domain in receipt["record"]["clocks"]
        assert other.clock.domain in receipt["record"]["clocks"]
        export_receipt(receipt, tmp_path / "restart-export")
        result = read_json(tmp_path / "restart-export/assessment.json")
        assert any("cross_domain_order_unproven" in s for s in result["unknown"])
    finally:
        other.close()


def test_uncommitted_quotes_are_not_visible_to_consumer(recorder):
    other = Recorder(recorder.path)
    try:
        recorder.connection.execute("BEGIN IMMEDIATE")
        recorder.connection.execute("INSERT INTO quotes VALUES ('partial',1,'partial','[]','hash')")
        # Direct read-only observation, without journaling a failed read on a busy writer.
        assert other.connection.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 0
        assert other.connection.execute("SELECT COUNT(*) FROM quotes").fetchone()[0] == 0
        recorder.connection.execute("ROLLBACK")
        assert other.read("partial", 1, consumer="test", build_sha256=BUILD) is None
    finally:
        other.close()


def test_duplicate_and_correction_parent(recorder):
    assert recorder.publish(RECORD, BODY).published
    assert not recorder.publish(RECORD, BODY).published
    changed = copy.deepcopy(RECORD)
    changed.update(record_id="correction", version=2, parent_record_sha256="0" * 64)
    assert not recorder.publish(changed, BODY).published
    changed["parent_record_sha256"] = recorder.connection.execute(
        "SELECT sha256 FROM provenance").fetchone()[0]
    assert recorder.publish(changed, BODY).published
    assert recorder.connection.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 2


@pytest.mark.parametrize("table", ["quotes", "provenance", "publications", "journal"])
def test_append_only_tables(recorder, table):
    recorder.publish(RECORD, BODY)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        recorder.connection.execute(f"DELETE FROM {table}")
    column = "kind" if table == "journal" else "snapshot_id"
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        recorder.connection.execute(f"UPDATE {table} SET {column}={column}")


def test_missing_payload_is_preserved_as_unknown(recorder, tmp_path):
    raw = copy.deepcopy(RECORD)
    raw["payload"].update(path=None, sha256=None)
    assert recorder.publish(raw).published
    receipt = read(recorder)
    assert receipt["response"] is None
    export_receipt(receipt, tmp_path / "missing-export")
    result = assess(receipt["record"], tmp_path / "missing-export")
    assert "original_response_missing" in result["unknown"]


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(accountNumber="private"),
    lambda r: r["legs"][0].update(authorization="private"),
    lambda r: r.update(response_id="wrong"),
    lambda r: r["legs"][0].update(provider_mark="10.1000"),
])
def test_unknown_sensitive_fields_and_changed_precision_refuse(recorder, mutation):
    value = json.loads(BODY)
    mutation(value)
    result = recorder.publish(RECORD, json.dumps(value).encode())
    assert not result.published
    assert recorder.connection.execute("SELECT COUNT(*) FROM provenance").fetchone()[0] == 0
    events = recorder.connection.execute("SELECT document FROM journal").fetchall()
    assert "private" not in str(events)


def test_duplicate_json_key_and_body_budget(recorder):
    from butterfly_guy.research.ndx_provenance import Record
    raw = Record.model_validate(RECORD)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        check_body(b'{"response_id":"a","response_id":"b","legs":[]}', raw)
    with pytest.raises(ValueError, match="1 MiB"):
        check_body(b"x" * (1024 * 1024 + 1), raw)


def test_exclusive_creation_and_schema_drift_refuse(recorder):
    with pytest.raises(FileExistsError):
        Recorder(recorder.path, create=True)
    recorder.connection.execute("UPDATE recording_schema SET sql_sha256='wrong'")
    with pytest.raises(ValueError, match="schema identity mismatch"):
        Recorder(recorder.path)


def test_schema_is_not_in_automatic_migrations():
    assert not (ROOT / "src/butterfly_guy/db/migrations/012_ndx_recording.sql").exists()
    assert "ndx_recording" not in (ROOT / "src/butterfly_guy/data/collector.py").read_text()


def test_process_crash_before_commit_leaves_only_attempt(recorder):
    import subprocess
    import sys
    script = """
import os
import sys
from butterfly_guy.research.ndx_recording import Recorder
r = Recorder(sys.argv[1])
r.journal('crash', 1, 'attempt', {'reason': 'synthetic crash fixture'})
r.connection.execute('BEGIN IMMEDIATE')
r.connection.execute("INSERT INTO quotes VALUES ('crash',1,'crash','[]','hash')")
os._exit(17)
"""
    completed = subprocess.run([sys.executable, "-c", script, str(recorder.path)], check=False)
    assert completed.returncode == 17
    assert recorder.connection.execute("SELECT COUNT(*) FROM quotes").fetchone()[0] == 0
    assert recorder.recovery_inventory() == [('crash', 1, 'attempt', 0, 0)]


def test_failed_failure_journal_is_visible_to_caller(recorder):
    recorder.connection.executescript("""
        CREATE TRIGGER fail_metadata BEFORE INSERT ON provenance BEGIN
            SELECT RAISE(ABORT, 'metadata failed'); END;
        CREATE TRIGGER fail_failure_journal BEFORE INSERT ON journal
        WHEN NEW.kind='publication_failed' BEGIN
            SELECT RAISE(ABORT, 'journal failed'); END;
    """)
    result = recorder.publish(RECORD, BODY, legacy_quote_write="success")
    assert not result.published
    assert result.failure == 'recording_failed:metadata_copy:failure_journal_unavailable'
    assert recorder.recovery_inventory()[0][3:] == (0, 0)


def test_producer_does_not_need_a_future_consumer_receipt(recorder):
    raw = copy.deepcopy(RECORD)
    for stage in ("read_start", "read_end", "consumer_receipt", "commit_ack", "publication_ack"):
        raw["stamps"][stage] = None
    raw["consumer"].update(returned_snapshot_id=None, returned_symbols=[], read_status="unknown")
    raw["publication"].update(complete_manifest_path=None, complete_manifest_sha256=None)
    assert recorder.publish(raw, BODY).published
    row = recorder.connection.execute("SELECT document FROM provenance").fetchone()
    stored = json.loads(row[0])
    assert stored["consumer"]["returned_snapshot_id"] is None
    assert stored["stamps"]["consumer_receipt"] is None
    actual_receipt = read(recorder)
    assert actual_receipt["record"]["consumer"]["read_status"] == "success"
