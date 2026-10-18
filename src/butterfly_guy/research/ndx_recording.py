"""Explicit local research recording; no imports or hooks into the running bot.

SQLite is an isolated evidence journal, not the trading TimescaleDB. Three writes
publish atomically. Acknowledgements and receipts are subsequent observations.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from butterfly_guy.research.ndx_evidence import digest, new_directory, write_json
from butterfly_guy.research.ndx_provenance import ROOT, Leg, Record, assess

SCHEMA = ROOT / "docs/research/ndx-strategy/recording-v1/schema.sql"
VERSION = "NDX-recording-sqlite-v1"


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def check_body(body, record):
    """Accept only the reviewed selected-market envelope, not arbitrary HTTP data.

    This envelope is not available from today's Schwab client. No raw-body claim
    can be made by reconstructing it from normalized rows. Only caller-supplied
    original boundary bytes are accepted; upstream integration remains pending.
    """
    if len(body) > 1024 * 1024:
        raise ValueError("market response exceeds prototype 1 MiB recording budget")
    value = json.loads(body, object_pairs_hook=unique_pairs)
    if not isinstance(value, dict) or set(value) not in (
        {"response_id", "legs"}, {"response_id", "legs", "synthetic"}
    ):
        raise ValueError("unapproved market response envelope")
    if value["response_id"] != record.payload.response_id:
        raise ValueError("response identity mismatch")
    if "synthetic" in value and (value["synthetic"] is not True
                                 or record.evidence_kind != "synthetic"):
        raise ValueError("synthetic response identity mismatch")
    legs = [Leg.model_validate(leg).model_dump() for leg in value["legs"]]
    if legs != [leg.model_dump() for leg in record.legs]:
        raise ValueError("response leg values or precision mismatch")
    if record.payload.sha256 != sha(body):
        raise ValueError("response hash mismatch")


class LocalClock:
    """New instance = new process/domain scope; no invented synchronization bound."""

    def __init__(self):
        self.domain = "local-" + uuid.uuid4().hex
        self.previous_wall = None
        self.description = {
            "owner": "local-research-host", "process": f"pid-{os.getpid()}",
            "boot": "unattested-boot-" + uuid.uuid4().hex,
            "source": "datetime UTC paired with time.monotonic_ns",
            "sync_evidence": None, "uncertainty_seconds": None, "discontinuity": False,
        }

    def stamp(self):
        wall = dt.datetime.now(dt.timezone.utc)
        if self.previous_wall is not None and wall < self.previous_wall:
            self.description["discontinuity"] = True
        self.previous_wall = wall
        return {"wall_utc": wall.isoformat(),
                "monotonic_ns": time.monotonic_ns(), "clock": self.domain}


@dataclass(frozen=True)
class PublicationResult:
    published: bool
    acknowledgement_recorded: bool
    failure: str | None
    manifest_sha256: str | None


class Recorder:
    def __init__(self, path, *, create=False):
        self.path = Path(path)
        self.clock = LocalClock()
        if create:
            # Exclusive creation is intentional: never initialize over an existing DB.
            with self.path.open("xb"):
                pass
        elif not self.path.is_file():
            raise FileNotFoundError(self.path)
        self.connection = sqlite3.connect(self.path, isolation_level=None, timeout=1)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA synchronous = FULL")
        if create:
            self.connection.executescript(SCHEMA.read_text())
            self.connection.execute("INSERT INTO recording_schema VALUES (?, ?)",
                                    (VERSION, digest(SCHEMA)))
        elif self.connection.execute(
            "SELECT version, sql_sha256 FROM recording_schema").fetchall() \
                != [(VERSION, digest(SCHEMA))]:
            self.connection.close()
            raise ValueError("recording schema identity mismatch")

    def close(self):
        self.connection.close()

    def journal(self, snapshot_id, version, kind, detail):
        # No exception strings or raw HTTP context are logged: safe categorical codes only.
        self.connection.execute("INSERT INTO journal VALUES (?, ?, ?, ?, ?)",
                                (uuid.uuid4().hex, snapshot_id, version, kind, encode(detail)))

    def publish(self, raw, response=None, *, legacy_quote_write="unknown"):
        """Publish a copy of research evidence. Never writes the trading quote table."""
        record = Record.model_validate(raw)
        if record.channel != "db-research":
            raise ValueError("DB research channel required")
        if legacy_quote_write not in ("unknown", "success", "failed"):
            raise ValueError("invalid legacy quote status")
        key = record.snapshot_id, record.version
        self.journal(*key, "attempt", {"record_id": record.record_id,
                                      "legacy_quote_write": legacy_quote_write,
                                      "observed": self.clock.stamp()})
        stage = "validation"
        try:
            if response is not None:
                check_body(response, record)
            elif record.payload.sha256 is not None:
                raise ValueError("declared original response bytes missing")
            if len(record.legs) != 3 or sorted(leg.symbol for leg in record.legs) \
                    != sorted(record.expected_symbols) or len(set(record.expected_symbols)) != 3:
                raise ValueError("incomplete or duplicate research universe")
            # v1's structural checks are reused without interpreting its missing evidence
            # as failure. Files are bound directly below, not looked up via caller paths.
            document = record.model_dump()
            document["payload"].update(path=None, sha256=None)
            document["publication"].update(complete_manifest_path=None,
                                            complete_manifest_sha256=None)
            if document["consumer"]["returned_snapshot_id"] is None:
                # Only an internal structural probe: no receipt is persisted or inferred.
                document["consumer"]["returned_snapshot_id"] = record.snapshot_id
            structural = assess(document, self.path.parent)
            structural_errors = [s for s in structural["rejected"]
                                 if not s.startswith(
                                     ("publication_manifest_", "unsafe_publication_"))]
            if structural_errors:
                raise ValueError("structural provenance contradiction")
            document = record.model_dump()
            for stage in ("read_start", "read_end", "consumer_receipt", "commit_ack",
                          "publication_ack"):
                document["stamps"][stage] = None
            document["consumer"].update(returned_snapshot_id=None, returned_symbols=[],
                                        read_status="unknown")
            document["publication"] = {"publication_id": None, "transaction_id": None,
                "snapshot_id": None, "quote_write": "unknown", "metadata_write": "unknown",
                "complete_manifest_sha256": None, "complete_manifest_path": None,
                "visibility_evidence": None, "failure": None}
            document["clocks"][self.clock.domain] = self.clock.description
            document["stamps"]["transaction_start"] = self.clock.stamp()
            self.connection.execute("BEGIN IMMEDIATE")
            if record.version > 1:
                previous = self.connection.execute(
                    "SELECT sha256 FROM provenance WHERE snapshot_id=? AND version=?",
                    (record.snapshot_id, record.version - 1)).fetchone()
                if previous is None or record.parent_record_sha256 != previous[0]:
                    raise ValueError("missing or mismatched correction parent")
            elif record.parent_record_sha256 is not None:
                raise ValueError("initial publication cannot claim correction parent")
            document["stamps"]["insert_start"] = self.clock.stamp()
            quotes = encode(document["legs"])
            metadata = encode(document)
            body_hash = sha(response) if response is not None else None
            manifest = {"snapshot_id": key[0], "version": key[1],
                        "symbols": record.expected_symbols, "response_sha256": body_hash,
                        "quote_write": "success", "metadata_write": "success",
                        "quotes_sha256": sha(quotes), "metadata_sha256": sha(metadata)}
            manifest_text = encode(manifest)
            stage = "quote_copy"
            self.connection.execute("INSERT INTO quotes VALUES (?, ?, ?, ?, ?)",
                                    (*key, record.record_id, quotes, sha(quotes)))
            stage = "metadata_copy"
            self.connection.execute("INSERT INTO provenance VALUES (?, ?, ?, ?, ?, ?)",
                                    (*key, metadata, sha(metadata), response, body_hash))
            stage = "manifest"
            self.connection.execute("INSERT INTO publications VALUES (?, ?, ?, ?)",
                                    (*key, manifest_text, sha(manifest_text)))
            stage = "commit"
            self.connection.execute("COMMIT")
        except (ValueError, sqlite3.Error) as exc:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
            code = "duplicate_or_constraint" if getattr(exc, "sqlite_errorname", "") in (
                "SQLITE_CONSTRAINT_UNIQUE", "SQLITE_CONSTRAINT_PRIMARYKEY") \
                else f"recording_failed:{stage}"
            # A failed failure-journal write must be visible to the caller as well.
            try:
                self.journal(*key, "publication_failed", {"reason": code,
                    "legacy_quote_write": legacy_quote_write,
                    "research_publication": "absent_or_preexisting_not_overwritten"})
            except sqlite3.Error:
                code += ":failure_journal_unavailable"
            return PublicationResult(False, False, code, None)
        # These observations occur AFTER COMMIT returns, never inside the transaction.
        acknowledgement = {"commit_ack": self.clock.stamp(),
                           "publication_ack": self.clock.stamp(),
                           "clock": self.clock.description,
                           "manifest_sha256": sha(manifest_text)}
        try:
            self.journal(*key, "commit_ack", acknowledgement)
        except sqlite3.Error:
            return PublicationResult(True, False, "commit_ack_journal_unavailable",
                                     sha(manifest_text))
        return PublicationResult(True, True, None, sha(manifest_text))

    def read(self, snapshot_id, version, *, consumer, build_sha256):
        """Return one committed complete snapshot and separate receipt-journal status."""
        start = self.clock.stamp()
        # One statement reads the exact manifest and its rows under one DB snapshot.
        row = self.connection.execute("""
            SELECT p.manifest, p.sha256, q.document, q.sha256, m.document,
                   m.sha256, m.response, m.response_sha256
            FROM publications p JOIN quotes q USING (snapshot_id, version)
            JOIN provenance m USING (snapshot_id, version)
            WHERE p.snapshot_id = ? AND p.version = ?
        """, (snapshot_id, version)).fetchone()
        if row is None:
            self.journal(snapshot_id, version, "read_failed", {"reason": "no_complete_publication",
                         "read_start": start, "read_end": self.clock.stamp()})
            return None
        (manifest_text, manifest_hash, quotes, quotes_hash, metadata, metadata_hash,
         body, body_hash) = row
        if (sha(manifest_text) != manifest_hash or sha(quotes) != quotes_hash
                or sha(metadata) != metadata_hash or (sha(body) if body is not None else None)
                != body_hash):
            raise ValueError("stored content hash mismatch")
        manifest, raw = json.loads(manifest_text), json.loads(metadata)
        if (manifest["quotes_sha256"] != quotes_hash
                or manifest["metadata_sha256"] != metadata_hash
                or manifest["response_sha256"] != body_hash
                or raw["legs"] != json.loads(quotes)
                or raw["snapshot_id"] != snapshot_id or raw["version"] != version
                or sorted(manifest["symbols"]) != sorted(raw["expected_symbols"])):
            raise ValueError("complete snapshot identity mismatch")
        raw["clocks"][self.clock.domain] = self.clock.description
        acknowledgements = self.connection.execute("""
            SELECT document FROM journal WHERE snapshot_id = ? AND version = ?
            AND kind = 'commit_ack'
        """, (snapshot_id, version)).fetchall()
        if len(acknowledgements) == 1:
            ack = json.loads(acknowledgements[0][0])
            if ack["manifest_sha256"] != manifest_hash:
                raise ValueError("acknowledgement identity mismatch")
            for stage in ("commit_ack", "publication_ack"):
                raw["stamps"][stage] = ack[stage]
                raw["clocks"][ack[stage]["clock"]] = ack["clock"]
        raw["publication"].update(publication_id=manifest_hash, snapshot_id=snapshot_id,
            transaction_id=None, quote_write="success",
            metadata_write="success", complete_manifest_path="publication.json",
            complete_manifest_sha256=sha(manifest_text), visibility_evidence=
            "SQLite committed manifest/quotes/metadata read in one exact-key SELECT")
        raw["payload"].update(path="response.json" if body is not None else None,
                               sha256=body_hash)
        raw["consumer"].update(identity=consumer, build_sha256=build_sha256,
                               returned_snapshot_id=snapshot_id,
                               returned_symbols=manifest["symbols"], read_status="success")
        raw["stamps"]["read_start"] = start
        raw["stamps"]["read_end"] = self.clock.stamp()
        Record.model_validate(raw)  # Decode and validate before receipt, never after a decision.
        raw["stamps"]["consumer_receipt"] = self.clock.stamp()
        receipt = {"record": raw, "manifest": manifest_text, "response": body,
                   "receipt_journaled": False}
        try:
            self.journal(snapshot_id, version, "consumer_receipt", {
                "consumer": consumer, "build_sha256": build_sha256,
                "read_start": start, "read_end": raw["stamps"]["read_end"],
                "consumer_receipt": raw["stamps"]["consumer_receipt"],
                "clock": self.clock.description, "manifest_sha256": manifest_hash})
            receipt["receipt_journaled"] = True
        except sqlite3.Error:
            # Read succeeded; recording failed. Do not mislabel a missing quote.
            pass
        return receipt

    def recovery_inventory(self):
        """Report actual publication/ack presence; never synthesize a lost ack."""
        return self.connection.execute("""
            SELECT j.snapshot_id, j.version, j.kind,
                   EXISTS(SELECT 1 FROM publications p WHERE p.snapshot_id=j.snapshot_id
                          AND p.version=j.version) AS published,
                   EXISTS(SELECT 1 FROM journal a WHERE a.snapshot_id=j.snapshot_id
                          AND a.version=j.version AND a.kind='commit_ack') AS ack_recorded
            FROM journal j WHERE j.kind='attempt' ORDER BY j.rowid
        """).fetchall()


def export_receipt(receipt, output):
    """Export a new evidence bundle accepted by the existing v1 offline assessor."""
    output = Path(output)
    new_directory(output)
    if receipt["response"] is not None:
        (output / "response.json").write_bytes(receipt["response"])
    (output / "publication.json").write_text(receipt["manifest"])
    write_json(output / "record.json", receipt["record"])
    write_json(output / "receipt-recording.json",
               {"receipt_journaled": receipt["receipt_journaled"]})
    write_json(output / "assessment.json", assess(receipt["record"], output))
    return {p.name: digest(p) for p in output.iterdir() if p.is_file()}
