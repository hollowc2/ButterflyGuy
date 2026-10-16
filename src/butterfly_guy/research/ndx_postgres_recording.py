"""Dormant asyncpg research publication/receipt adapter for PostgreSQL/TimescaleDB.

No schema installation, pool creation, configuration or active bot wiring occurs
on import. Tables are ordinary PostgreSQL tables, separate from trading tables.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

import asyncpg
import httpx

from butterfly_guy.research.ndx_evidence import digest
from butterfly_guy.research.ndx_native_response import (
    NativeCapture,
    assess_native,
    preserve_buffered_response,
    validate_capture,
)
from butterfly_guy.research.ndx_provenance import ROOT
from butterfly_guy.research.ndx_recording import LocalClock, encode, sha

SCHEMA = ROOT / "docs/research/ndx-strategy/postgres-v1/schema.sql"
VERSION = "NDX-postgres-native-v1"


async def install_empty_schema(connection):
    """Explicit DDL. Caller must supply an isolated or separately approved connection."""
    async with connection.transaction():
        await connection.execute(SCHEMA.read_text())
        await connection.execute("INSERT INTO ndx_provenance_v1.schema_identity VALUES ($1,$2,$3)",
                                 VERSION, digest(SCHEMA), uuid.uuid4())


@dataclass(frozen=True)
class PublishResult:
    published: bool | None  # None: COMMIT outcome unknown after connection/transport failure.
    acknowledgement_recorded: bool
    manifest_sha256: str | None
    failure: str | None


class PostgresRecorder:
    def __init__(self, pool):
        self.pool = pool
        self.clock = LocalClock()

    async def check_schema(self):
        rows = await self.pool.fetch(
            "SELECT version,sql_sha256,installation_id FROM ndx_provenance_v1.schema_identity")
        if len(rows) != 1 or tuple(rows[0].values())[:2] != (VERSION, digest(SCHEMA)):
            raise ValueError("PostgreSQL research schema identity mismatch")
        return str(rows[0]["installation_id"])

    async def journal(self, key, kind, detail):
        await self.pool.execute("INSERT INTO ndx_provenance_v1.journal "
            "(event_id,snapshot_id,version,kind,document) VALUES ($1,$2,$3,$4,$5)",
            uuid.uuid4(), *key, kind, encode(detail))

    async def publish(self, capture, *, legacy_quote_write="unknown"):
        doc = validate_capture(capture)
        if legacy_quote_write not in ("success", "failed", "unknown"):
            raise ValueError("invalid legacy quote outcome")
        key = doc["snapshot_id"], doc["version"]
        installation_id = await self.check_schema()
        await self.journal(key, "attempt", {"record_id": doc["record_id"],
            "observed": self.clock.stamp(), "legacy_quote_write": legacy_quote_write})
        stage = "transaction_start"
        manifest_hash = None
        committed = False
        try:
            async with self.pool.acquire() as conn:
                # No caller-owned outer transaction: acknowledgement must follow the real COMMIT.
                if conn.is_in_transaction():
                    raise ValueError("recorder requires an independently owned connection")
                async with conn.transaction():
                    await conn.execute("SET LOCAL lock_timeout = '1000ms'")
                    transaction_id = await conn.fetchval("SELECT pg_current_xact_id()::text")
                    if doc["version"] > 1:
                        parent = await conn.fetchval(
                            "SELECT sha256 FROM ndx_provenance_v1.provenance "
                            "WHERE snapshot_id=$1 AND version=$2", key[0], key[1] - 1)
                        if parent is None or doc["parent_document_sha256"] != parent:
                            raise ValueError("missing or mismatched correction parent")
                    elif doc["parent_document_sha256"] is not None:
                        raise ValueError("initial version cannot claim a correction parent")
                    document = dict(doc, publication_clock={"domain": self.clock.domain,
                        "description": self.clock.description},
                        transaction_start_observed_at=self.clock.stamp(),
                        transaction_id=transaction_id, storage_installation_id=installation_id,
                        publisher_source_sha256=digest(Path(__file__)),
                        research_schema_sha256=digest(SCHEMA))
                    quotes, metadata = encode(doc["selected"]), encode(document)
                    manifest = {"snapshot_id": key[0], "version": key[1],
                        "symbols": doc["expected_symbols"], "transaction_id": transaction_id,
                        "storage_installation_id": installation_id,
                        "body_scope": doc["body_scope"], "response_sha256": sha(capture.body),
                        "quotes_sha256": sha(quotes), "metadata_sha256": sha(metadata),
                        "quote_write": "success", "metadata_write": "success"}
                    manifest_text = encode(manifest)
                    manifest_hash = sha(manifest_text)
                    stage = "quote_copy"
                    await conn.execute(
                        "INSERT INTO ndx_provenance_v1.quotes VALUES ($1,$2,$3,$4,$5)",
                                       *key, doc["record_id"], quotes, sha(quotes))
                    stage = "metadata_copy"
                    await conn.execute("INSERT INTO ndx_provenance_v1.provenance "
                        "VALUES ($1,$2,$3,$4,$5,$6,$7)", *key, metadata, sha(metadata),
                        capture.body, sha(capture.body), transaction_id)
                    stage = "manifest"
                    await conn.execute("INSERT INTO ndx_provenance_v1.publications "
                        "VALUES ($1,$2,$3,$4)", *key, manifest_text, manifest_hash)
                    stage = "commit"
                # Transaction context exits successfully only after COMMIT acknowledgement.
                committed = True
                commit_ack = self.clock.stamp()
            publication_ack = self.clock.stamp()
        except asyncio.CancelledError:
            # Cancellation may race COMMIT. Durable attempt + later inventory resolve presence.
            raise
        except (ValueError, asyncpg.PostgresError, asyncpg.InterfaceError,
                OSError, TimeoutError) as exc:
            known_failure = isinstance(exc, (
                ValueError, asyncpg.IntegrityConstraintViolationError,
                asyncpg.SerializationError, asyncpg.DeadlockDetectedError))
            published = True if committed else False if known_failure or stage != "commit" else None
            code = "duplicate_identity" if isinstance(exc, asyncpg.UniqueViolationError) \
                else "post_commit_release_failed" if committed \
                else f"recording_failed:{stage}" if published is False else "commit_outcome_unknown"
            try:
                await self.journal(key, "publication_failed", {"reason": code,
                    "legacy_quote_write": legacy_quote_write,
                    "publication_presence": "not_established_by_this_error"})
            except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError):
                code += ":failure_journal_unavailable"
            return PublishResult(published, False, None, code)
        try:
            await self.journal(key, "commit_ack", {"commit_ack": commit_ack,
                "publication_ack": publication_ack, "clock": self.clock.description,
                "manifest_sha256": manifest_hash})
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError):
            return PublishResult(True, False, manifest_hash, "commit_ack_journal_unavailable")
        return PublishResult(True, True, manifest_hash, None)

    async def read(self, snapshot_id, version, *, consumer, build_sha256):
        start = self.clock.stamp()
        installation_id = await self.check_schema()
        # Single SQL statement: manifest, selected rows, raw body and ack share one MVCC snapshot.
        row = await self.pool.fetchrow("""
            SELECT p.manifest,p.sha256 AS manifest_hash,q.document AS quotes,q.sha256 AS quote_hash,
                   m.document AS metadata,m.sha256 AS metadata_hash,m.response,m.response_sha256,
                   m.transaction_id,
                   (SELECT json_agg(j.document::json) FROM ndx_provenance_v1.journal j
                    WHERE j.snapshot_id=p.snapshot_id AND j.version=p.version
                    AND j.kind='commit_ack')::text AS acknowledgements
            FROM ndx_provenance_v1.publications p
            JOIN ndx_provenance_v1.quotes q USING (snapshot_id,version)
            JOIN ndx_provenance_v1.provenance m USING (snapshot_id,version)
            WHERE p.snapshot_id=$1 AND p.version=$2
        """, snapshot_id, version)
        key = snapshot_id, version
        if row is None:
            await self.journal(key, "read_failed", {"reason": "no_complete_publication",
                "consumer": consumer, "read_start": start, "read_end": self.clock.stamp()})
            return None
        for content, hashed in (("manifest", "manifest_hash"), ("quotes", "quote_hash"),
                                ("metadata", "metadata_hash"), ("response", "response_sha256")):
            if sha(row[content]) != row[hashed]:
                raise ValueError("stored content hash mismatch")
        manifest, document = json.loads(row["manifest"]), json.loads(row["metadata"])
        if (manifest["snapshot_id"] != snapshot_id or manifest["version"] != version
                or document["snapshot_id"] != snapshot_id or document["version"] != version
                or manifest["storage_installation_id"] != installation_id
                or document["storage_installation_id"] != installation_id
                or manifest["transaction_id"] != row["transaction_id"]
                or manifest["quotes_sha256"] != row["quote_hash"]
                or manifest["metadata_sha256"] != row["metadata_hash"]
                or manifest["response_sha256"] != row["response_sha256"]
                or document["selected"] != json.loads(row["quotes"])
                or manifest["symbols"] != document["expected_symbols"]):
            raise ValueError("complete snapshot identity mismatch")
        # validate_capture ignores only the additive publication fields, never body/leg identity.
        validate_capture(NativeCapture(row["response"], encode(document)))
        ack = json.loads(row["acknowledgements"] or "[]")
        if len(ack) > 1 or (ack and ack[0]["manifest_sha256"] != row["manifest_hash"]):
            raise ValueError("ambiguous or mismatched publication acknowledgement")
        end = self.clock.stamp()
        receipt = {"consumer": consumer, "build_sha256": build_sha256,
            "snapshot_id": snapshot_id, "version": version,
            "manifest_sha256": row["manifest_hash"], "read_start": start, "read_end": end,
            "consumer_receipt": self.clock.stamp(), "clock": self.clock.description}
        recorded = False
        try:
            await self.journal(key, "consumer_receipt", receipt)
            recorded = True
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError):
            pass
        return {"document": document, "response": row["response"], "manifest": row["manifest"],
            "receipt": receipt, "receipt_journaled": recorded,
            "commit_ack": ack[0] if ack else None,
            "assessment": assess_native(document, receipt_recorded=recorded,
                                         commit_ack_recorded=bool(ack))}

    async def recovery_inventory(self):
        return await self.pool.fetch("""
            SELECT j.snapshot_id,j.version,j.kind,
                EXISTS(SELECT 1 FROM ndx_provenance_v1.publications p
                       WHERE p.snapshot_id=j.snapshot_id AND p.version=j.version) AS published,
                EXISTS(SELECT 1 FROM ndx_provenance_v1.journal a
                       WHERE a.snapshot_id=j.snapshot_id AND a.version=j.version
                       AND a.kind='commit_ack') AS acknowledgement_recorded
            FROM ndx_provenance_v1.journal j WHERE j.kind='attempt' ORDER BY j.sequence
        """)


class ResearchGatewayHTTPClient(httpx.AsyncClient):
    """Explicit SDK client= injection for research only; disabled unless configured.

    Recording is awaited on this separate research path. It is not a hook on the
    active trading loop. Return the original HTTP response even when recording
    fails, exposing failure/drop counters to the research caller. No retries.
    """

    def __init__(self, *args, recorder=None, context_factory=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.recorder = recorder
        self.context_factory = context_factory
        self.recording_clock = LocalClock()
        self.last_recording_result = None
        self.recording_failures = 0

    async def get(self, *args, **kwargs):
        request_start = self.recording_clock.stamp() if self.recorder is not None else None
        response = await super().get(*args, **kwargs)
        if self.recorder is not None and response.request.url.path == "/v1/option-chain":
            context = None
            try:
                if self.context_factory is None:
                    raise ValueError("explicit acquisition context required")
                context = self.context_factory()
                capture = preserve_buffered_response(response, clock=self.recording_clock,
                    request_start=request_start, **context)
                self.last_recording_result = await self.recorder.publish(capture)
                if self.last_recording_result.published is not True \
                        or not self.last_recording_result.acknowledgement_recorded:
                    self.recording_failures += 1
            except asyncio.CancelledError:
                raise
            except Exception:
                # No exception/HTTP text retained; original SDK validation still runs.
                self.recording_failures += 1
                code = "observer_recording_failed"
                key = (context.get("snapshot_id"), context.get("version", 1)) if context else None
                if key and key[0]:
                    try:
                        await self.recorder.journal(key, "observer_failed", {
                            "reason": code, "http_success": response.status_code == 200,
                            "observed": self.recording_clock.stamp()})
                    except Exception:
                        code += ":failure_journal_unavailable"
                else:
                    code += ":acquisition_identity_unavailable"
                self.last_recording_result = PublishResult(None, False, None, code)
        return response
