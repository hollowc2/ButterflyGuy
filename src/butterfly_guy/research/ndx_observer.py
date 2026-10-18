"""Default-off, caller-driven research consumer. No scheduler, orders or bot wiring.

There is one in-flight request and no queue. Admission rejects concurrent calls
before requesting data. HTTP buffering precedes the recording byte guard; this
guard is not a bound on httpx's original allocation or synchronous SDK parsing.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import re
import uuid
from collections import Counter
from dataclasses import dataclass

import asyncpg
import httpx
from schwab_gateway_sdk.client import GatewayMarketDataClient

from butterfly_guy.research.ndx_native_response import preserve_buffered_response
from butterfly_guy.research.ndx_postgres_recording import PostgresRecorder
from butterfly_guy.research.ndx_recording import LocalClock

LEASE_KEY = 78020301  # One observer per research database, across process restarts.


@dataclass(frozen=True)
class ObserverLimits:
    body_bytes: int = 2 * 1024 * 1024
    storage_bytes: int = 512 * 1024 * 1024
    operation_seconds: float = 10
    startup_seconds: float = 5
    shutdown_seconds: float = 3
    journal_seconds: float = 1

    def __post_init__(self):
        if not 1 <= self.body_bytes <= 16 * 1024 * 1024:
            raise ValueError("recording byte budget outside native guard")
        if type(self.storage_bytes) is not int or self.storage_bytes < 1:
            raise ValueError("positive research storage pause budget required")
        if any(not 0 < n <= 60 for n in (self.operation_seconds, self.startup_seconds,
                self.shutdown_seconds, self.journal_seconds)):
            raise ValueError("observer time budgets must be positive and at most 60 seconds")


@dataclass(frozen=True)
class Acquisition:
    snapshot_id: str
    record_id: str
    request_id: str
    pass_id: str
    acquisition_id: str
    session: str
    expected_symbols: tuple[str, str, str]
    calendar: str
    close_utc: str
    build_sha256: str
    config_sha256: str
    consumer: str
    evidence_kind: str = "prospective"
    version: int = 1
    parent_document_sha256: str | None = None

    def __post_init__(self):
        for value in (self.snapshot_id, self.record_id, self.request_id, self.pass_id,
                      self.acquisition_id, self.consumer, self.calendar):
            if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value):
                raise ValueError("non-secret opaque research identity required")
        for value in (self.build_sha256, self.config_sha256):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError("explicit build/config hash required")
        session = dt.date.fromisoformat(self.session)
        close = dt.datetime.fromisoformat(self.close_utc)
        if close.utcoffset() != dt.timedelta(0) or close.date() != session:
            raise ValueError("explicit same-session UTC calendar close required")
        if len(set(self.expected_symbols)) != 3 or len(self.expected_symbols) != 3:
            raise ValueError("three preselected instruments required")
        for symbol in self.expected_symbols:
            match = re.fullmatch(r"NDXP\s+(\d{6})[CP]\d{8}", symbol)
            if not match or match[1] != session.strftime("%y%m%d"):
                raise ValueError("selected NDXP session identity mismatch")
        if self.evidence_kind not in ("synthetic", "prospective"):
            raise ValueError("observer does not reconstruct historical acquisitions")
        if type(self.version) is not int or self.version < 1:
            raise ValueError("positive version required")
        if (self.version == 1 and self.parent_document_sha256 is not None) or (
                self.version > 1 and not re.fullmatch(
                    r"[0-9a-f]{64}", self.parent_document_sha256 or "")):
            raise ValueError("correction parent required only for corrected versions")

    def native_context(self):
        return {k: getattr(self, k) for k in ("snapshot_id", "record_id", "request_id",
            "pass_id", "acquisition_id", "session", "expected_symbols", "evidence_kind",
            "version", "parent_document_sha256")}


@dataclass(frozen=True)
class Observation:
    quote: object | None
    quote_status: str
    publication: object | None = None
    receipt: dict | None = None
    recording_status: str = "not_attempted"


class _NativeClient(httpx.AsyncClient):
    def __init__(self, observer, **kwargs):
        super().__init__(**kwargs)
        self.observer = observer

    async def get(self, *args, **kwargs):
        owner = self.observer
        started = owner.clock.stamp()
        response = await super().get(*args, **kwargs)
        owner.counts["responses_received"] += 1
        owner.saw_response = True
        if len(response.content) > owner.limits.body_bytes:
            owner.recording_status = "oversized"
            owner.counts["recording_rejected"] += 1
            await owner.event("recording_rejected", "oversized")
            return response
        owner.retained_bytes = len(response.content)
        owner.peak_retained_bytes = max(owner.peak_retained_bytes, owner.retained_bytes)
        try:
            capture = preserve_buffered_response(response, clock=owner.clock,
                request_start=started, **owner.context.native_context())
        except ValueError:
            owner.recording_status = "body_rejected"
            owner.counts["recording_rejected"] += 1
            await owner.event("recording_rejected", "body_rejected")
            return response  # SDK still validates the original response normally.
        owner.counts["recording_accepted"] += 1
        owner.counts["publication_calls"] += 1
        try:
            owner.publication = await owner.recorder.publish(capture)
            result = owner.publication
            owner.recording_status = "published" if result.published else (
                "unresolved" if result.published is None else "publication_failed")
            owner.counts[owner.recording_status] += 1
            owner.counts["acknowledgements"] += int(result.acknowledgement_recorded)
        except asyncio.CancelledError:
            raise
        except Exception:
            owner.recording_status = "unresolved"
            owner.counts["unresolved"] += 1
            await owner.event("recording_failed", "storage_unavailable")
        return response


def create_observer(*, enabled=False, **kwargs):
    """Disabled returns before inspecting secrets, creating clients/pools or tasks."""
    return ResearchObserver(**kwargs) if enabled else None


class ResearchObserver:
    def __init__(self, *, connection_factory, gateway_url, gateway_api_key,
                 limits=None, transport=None):
        self.connection_factory = connection_factory
        self.gateway_url = gateway_url
        self.gateway_api_key = gateway_api_key
        self.limits = limits or ObserverLimits()
        self.transport = transport
        self.instance_id = "observer-" + uuid.uuid4().hex
        self.clock = LocalClock()
        self.counts = Counter()
        self.pool = self.lease = self.client = self.sdk = self.recorder = None
        self.context = self.active = None
        self.state = "new"
        self.retained_bytes = self.peak_retained_bytes = 0

    async def event(self, kind, reason):
        """Categorical fields only; never persist exception/HTTP/authentication context."""
        key = (self.context.snapshot_id, self.context.version) if self.context else (
            self.instance_id, 1)
        try:
            async with asyncio.timeout(self.limits.journal_seconds):
                await self.recorder.journal(key, kind, {"instance_id": self.instance_id,
                    "reason": reason, "observed": self.clock.stamp(),
                    "acquisition_id": self.context.acquisition_id if self.context else None,
                    "request_id": self.context.request_id if self.context else None,
                    "pass_id": self.context.pass_id if self.context else None,
                    "record_id": self.context.record_id if self.context else None,
                    "consumer": self.context.consumer if self.context else None,
                    "build_sha256": self.context.build_sha256 if self.context else None,
                    "config_sha256": self.context.config_sha256 if self.context else None,
                    "calendar": self.context.calendar if self.context else None,
                    "close_utc": self.context.close_utc if self.context else None})
            self.counts["lifecycle_events_journaled"] += 1
            return True
        except asyncio.CancelledError:
            raise
        except Exception:
            self.counts["lifecycle_events_unjournaled"] += 1
            return False

    async def start(self):
        if self.state != "new":
            raise RuntimeError("observer start requires a new instance")
        self.state = "starting"
        try:
            async with asyncio.timeout(self.limits.startup_seconds):
                self.pool = await asyncpg.create_pool(**self.connection_factory(),
                    min_size=1, max_size=3, command_timeout=2, timeout=2,
                    server_settings={"lock_timeout": "1000ms", "statement_timeout": "2000ms",
                                     "application_name": "ndx-research-observer"})
                self.recorder = PostgresRecorder(self.pool)
                await self.recorder.check_schema()  # No automatic DDL.
                self.lease = await self.pool.acquire(timeout=1)
                if not await self.lease.fetchval("SELECT pg_try_advisory_lock($1)", LEASE_KEY):
                    raise RuntimeError("research observer already active")
                self.client = _NativeClient(self, base_url=self.gateway_url,
                    transport=self.transport, timeout=2, limits=httpx.Limits(max_connections=1))
                self.sdk = GatewayMarketDataClient(self.gateway_url, self.gateway_api_key,
                                                  client=self.client)
                if not await self.event("observer_started", "unobserved_interval_before_start"):
                    raise RuntimeError("startup ledger unavailable")
                self.state = "running"
        except BaseException:
            await self.close()
            raise

    async def acquire(self, context):
        if self.state != "running":
            raise RuntimeError("observer is not running")
        if self.active is not None:
            self.counts["admission_rejected_busy"] += 1
            # Do not wait, spawn a journal task, or replace the active acquisition ID.
            return Observation(None, "not_requested", recording_status="busy")
        if not isinstance(context, Acquisition):
            self.counts["identity_unavailable"] += 1
            await self.event("admission_rejected", "acquisition_identity_unavailable")
            return Observation(None, "not_requested", recording_status="identity_unavailable")
        self.active = asyncio.current_task()
        self.context = context
        self.publication = None
        self.recording_status = "not_attempted"
        self.saw_response = False
        try:
            async with asyncio.timeout(self.limits.operation_seconds):
                # Fail before traffic if the session holding the uniqueness lock died.
                await self.lease.fetchval("SELECT pg_backend_pid()")
                storage = await self.lease.fetchval("""
                    SELECT sum(pg_total_relation_size(oid)) FROM pg_class
                    WHERE relnamespace='ndx_provenance_v1'::regnamespace AND relkind='r'
                """)
                if storage >= self.limits.storage_bytes:
                    self.counts["admission_rejected_storage"] += 1
                    await self.event("admission_rejected", "storage_pause_budget")
                    return Observation(None, "not_requested", recording_status="storage_budget")
                if not await self.event("acquisition_started", "caller_requested"):
                    return Observation(None, "not_requested", recording_status="ledger_unavailable")
                self.counts["requests_started"] += 1
                try:
                    quote = await self.sdk.get_option_chain(
                        "$NDX", dt.date.fromisoformat(context.session))
                except asyncio.CancelledError:
                    raise
                except Exception:
                    status = "sdk_rejected" if self.saw_response else "gateway_failed"
                    self.counts[status] += 1
                    await self.event("quote_failed", status)
                    return Observation(None, status, self.publication,
                                       recording_status=self.recording_status)
                self.counts["quotes_succeeded"] += 1
                receipt = None
                if self.publication is not None and self.publication.published is True:
                    try:
                        receipt = await self.recorder.read(context.snapshot_id, context.version,
                            consumer=context.consumer, build_sha256=context.build_sha256)
                        self.counts["consumer_reads"] += int(receipt is not None)
                        self.counts["receipt_records"] += int(
                            receipt is not None and receipt["receipt_journaled"])
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        self.counts["consumer_read_failed"] += 1
                        await self.event("consumer_failed", "read_unavailable")
                return Observation(quote, "success", self.publication, receipt,
                                   self.recording_status)
        except asyncio.CancelledError:
            self.counts["unresolved"] += 1
            await self.event("acquisition_interrupted", "cancelled_outcome_requires_recovery")
            raise
        except Exception:
            self.counts["unresolved"] += 1
            await self.event("acquisition_interrupted", "timeout_or_lease_lost")
            return Observation(None, "interrupted", self.publication,
                               recording_status="unresolved")
        finally:
            self.retained_bytes = 0
            self.context = self.active = None

    async def close(self):
        if self.state == "closed":
            return
        self.state = "closing"
        try:
            async with asyncio.timeout(self.limits.shutdown_seconds):
                if self.active is not None and self.active is not asyncio.current_task():
                    self.active.cancel()
                    await asyncio.gather(self.active, return_exceptions=True)
                if self.recorder is not None:
                    await self.event("observer_stopped", "memory_counts_not_durable_completeness")
                if self.client is not None:
                    await self.client.aclose()
                if self.lease is not None:
                    await self.lease.execute("SELECT pg_advisory_unlock($1)", LEASE_KEY)
                    await self.pool.release(self.lease, timeout=1)
                    self.lease = None
                if self.pool is not None:
                    await self.pool.close()
        except Exception:
            self.counts["shutdown_incomplete"] += 1
        finally:
            if self.pool is not None:
                self.pool.terminate()  # Only this dedicated task-owned pool.
            self.state = "closed"
