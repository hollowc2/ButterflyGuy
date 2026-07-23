"""Demand-aware shared SPX snapshot feed and audit archive."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import uuid
from dataclasses import dataclass
from typing import Any

from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

from butterfly_guy.candidate_fleet.models import (
    LeaseKind,
    MarketSnapshot,
    SnapshotIdentity,
    SnapshotUnavailableError,
)
from butterfly_guy.candidate_fleet.schwab_market_data import ReadOnlySchwabMarketDataClient
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.time_utils import EASTERN, MARKET_OPEN, get_0dte_expiration
from butterfly_guy.data.chain_utils import iter_chain_options
from butterfly_guy.data.schemas import OptionQuote
from butterfly_guy.db.connection import DatabasePool

log = get_logger(__name__)

feed_sequence = Gauge("candidate_feed_sequence", "Latest atomically published sequence")
feed_snapshot_age = Gauge("candidate_feed_snapshot_age_seconds", "Age of latest snapshot")
feed_active_leases = Gauge(
    "candidate_feed_active_leases",
    "Unexpired demand leases",
    ["kind"],
)
feed_lease_active = Gauge(
    "candidate_feed_lease_active",
    "Whether an individual candidate lease is unexpired",
    ["candidate_id", "kind"],
)
feed_failures = Counter(
    "candidate_feed_failures_total",
    "Candidate feed collection failures",
    ["operation"],
)
feed_archive_failures = Counter(
    "candidate_feed_archive_failures_total",
    "Candidate snapshot archive failures",
    ["kind"],
)

ARCHIVE_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE TABLE IF NOT EXISTS candidate_market_snapshots (
    captured_at TIMESTAMPTZ NOT NULL,
    feed_instance UUID NOT NULL,
    sequence BIGINT NOT NULL,
    expiration DATE NOT NULL,
    snapshot JSONB NOT NULL,
    baseline BOOLEAN NOT NULL DEFAULT FALSE,
    pinned BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (feed_instance, sequence, captured_at)
);
SELECT create_hypertable(
    'candidate_market_snapshots',
    'captured_at',
    if_not_exists => TRUE,
    migrate_data => TRUE
);
CREATE UNIQUE INDEX IF NOT EXISTS candidate_market_snapshot_identity
    ON candidate_market_snapshots (feed_instance, sequence, captured_at);
ALTER TABLE candidate_market_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'feed_instance',
    timescaledb.compress_orderby = 'captured_at DESC, sequence DESC'
);
SELECT add_compression_policy(
    'candidate_market_snapshots',
    INTERVAL '7 days',
    if_not_exists => TRUE
);
SELECT add_retention_policy(
    'candidate_market_snapshots',
    INTERVAL '90 days',
    if_not_exists => TRUE
);
"""


@dataclass(frozen=True)
class Lease:
    candidate_id: str
    kind: LeaseKind
    expires_at: dt.datetime


class LeaseRegistry:
    def __init__(self, ttl_seconds: float = 30) -> None:
        self.ttl_seconds = ttl_seconds
        self._leases: dict[str, Lease] = {}
        self._lock = asyncio.Lock()
        self._demand_changed = asyncio.Event()

    async def refresh(
        self,
        candidate_id: str,
        kind: LeaseKind,
        *,
        now: dt.datetime | None = None,
    ) -> Lease:
        if not candidate_id:
            raise ValueError("candidate_id is required")
        current = now or dt.datetime.now(dt.timezone.utc)
        lease = Lease(
            candidate_id,
            kind,
            current + dt.timedelta(seconds=self.ttl_seconds),
        )
        async with self._lock:
            self._leases[candidate_id] = lease
            self._demand_changed.set()
        return lease

    async def release(self, candidate_id: str) -> bool:
        async with self._lock:
            return self._leases.pop(candidate_id, None) is not None

    async def active(self, now: dt.datetime | None = None) -> tuple[Lease, ...]:
        current = now or dt.datetime.now(dt.timezone.utc)
        async with self._lock:
            expired = [
                candidate_id
                for candidate_id, lease in self._leases.items()
                if lease.expires_at <= current
            ]
            for candidate_id in expired:
                del self._leases[candidate_id]
            return tuple(self._leases.values())

    async def polling_interval(self, now: dt.datetime | None = None) -> float:
        return 2.0 if await self.active(now) else 60.0

    async def wait_for_demand(self, timeout: float) -> bool:
        self._demand_changed.clear()
        if await self.active():
            return True
        try:
            await asyncio.wait_for(self._demand_changed.wait(), timeout=timeout)
            return True
        except TimeoutError:
            return False


class AtomicSnapshotStore:
    """Condition-guarded pointer swap; readers never observe partial snapshots."""

    def __init__(self, instance: str | None = None) -> None:
        self.instance = instance or str(uuid.uuid4())
        self._snapshot: MarketSnapshot | None = None
        self._recent: dict[int, MarketSnapshot] = {}
        self._sequence = 0
        self._condition = asyncio.Condition()

    async def publish(
        self,
        *,
        captured_at: dt.datetime,
        expiration: dt.date,
        spot: float,
        vix: float,
        session_open: float,
        previous_close: float,
        quotes: tuple[OptionQuote, ...],
    ) -> MarketSnapshot:
        async with self._condition:
            self._sequence += 1
            snapshot = MarketSnapshot(
                identity=SnapshotIdentity(self.instance, self._sequence),
                captured_at=captured_at,
                expiration=expiration,
                spot=spot,
                vix=vix,
                session_open=session_open,
                previous_close=previous_close,
                quotes=quotes,
            )
            self._snapshot = snapshot
            self._recent[snapshot.sequence] = snapshot
            while len(self._recent) > 120:
                del self._recent[min(self._recent)]
            self._condition.notify_all()
            return snapshot

    async def get(
        self,
        *,
        after: SnapshotIdentity | None = None,
        wait_seconds: float = 0,
    ) -> MarketSnapshot:
        async with self._condition:
            if self._is_newer(after):
                assert self._snapshot is not None
                return self._snapshot
            if wait_seconds > 0:
                try:
                    await asyncio.wait_for(
                        self._condition.wait_for(lambda: self._is_newer(after)),
                        timeout=min(wait_seconds, 30),
                    )
                except TimeoutError:
                    pass
            if self._snapshot is None:
                raise SnapshotUnavailableError("feed has not published a snapshot")
            if not self._is_newer(after):
                raise SnapshotUnavailableError("no newer snapshot is available")
            return self._snapshot

    def peek(self) -> MarketSnapshot | None:
        return self._snapshot

    def find(self, identity: SnapshotIdentity) -> MarketSnapshot | None:
        if identity.instance != self.instance:
            return None
        return self._recent.get(identity.sequence)

    def _is_newer(self, after: SnapshotIdentity | None) -> bool:
        if self._snapshot is None:
            return False
        if after is None or after.instance != self._snapshot.instance:
            return True
        return self._snapshot.sequence > after.sequence


class SnapshotArchive:
    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def initialize(self) -> None:
        await self.db.pool.execute(ARCHIVE_SCHEMA_SQL)

    async def archive(self, snapshot: MarketSnapshot, *, baseline: bool = False) -> None:
        await self.db.pool.execute(
            """
            INSERT INTO candidate_market_snapshots (
                captured_at, feed_instance, sequence, expiration, snapshot, baseline, pinned
            ) VALUES ($1, $2::uuid, $3, $4, $5::jsonb, $6, FALSE)
            ON CONFLICT (feed_instance, sequence, captured_at) DO UPDATE
            SET baseline = candidate_market_snapshots.baseline OR EXCLUDED.baseline
            """,
            snapshot.captured_at,
            snapshot.instance,
            snapshot.sequence,
            snapshot.expiration,
            json.dumps(snapshot.to_dict()),
            baseline,
        )

    async def pin(self, identity: SnapshotIdentity, current: MarketSnapshot | None) -> None:
        if current is not None and current.identity == identity:
            await self.archive(current)
        result = await self.db.pool.execute(
            """
            UPDATE candidate_market_snapshots
            SET pinned = TRUE
            WHERE feed_instance = $1::uuid AND sequence = $2
            """,
            identity.instance,
            identity.sequence,
        )
        if result == "UPDATE 0":
            raise SnapshotUnavailableError("snapshot is no longer available to pin")


@dataclass(frozen=True)
class SessionContext:
    refreshed_at: dt.datetime
    spot: float
    vix: float
    session_open: float
    previous_close: float


class CandidateFeed:
    def __init__(
        self,
        market: ReadOnlySchwabMarketDataClient,
        store: AtomicSnapshotStore,
        leases: LeaseRegistry,
        archive: SnapshotArchive,
        *,
        stale_after_seconds: float = 65,
    ) -> None:
        self.market = market
        self.store = store
        self.leases = leases
        self.archive = archive
        self.stale_after_seconds = stale_after_seconds
        self._context: SessionContext | None = None
        self._last_baseline_minute: dt.datetime | None = None
        self._observed_lease_labels: set[tuple[str, LeaseKind]] = set()

    async def collect_once(self) -> MarketSnapshot:
        now = dt.datetime.now(dt.timezone.utc)
        expiration = get_0dte_expiration()
        if self._context is None or (
            now - self._context.refreshed_at
        ).total_seconds() >= 60:
            self._context = await self._refresh_context(now)
        chain = await self.market.option_chain(expiration)
        quotes = self._normalize_chain(chain, expiration)
        snapshot = await self.store.publish(
            captured_at=now,
            expiration=expiration,
            spot=self._context.spot,
            vix=self._context.vix,
            session_open=self._context.session_open,
            previous_close=self._context.previous_close,
            quotes=quotes,
        )
        feed_sequence.set(snapshot.sequence)
        feed_snapshot_age.set(0)
        minute = now.replace(second=0, microsecond=0)
        if minute != self._last_baseline_minute:
            try:
                await self.archive.archive(snapshot, baseline=True)
                self._last_baseline_minute = minute
            except Exception:
                feed_archive_failures.labels(kind="baseline").inc()
                log.exception("candidate_baseline_archive_failed")
        return snapshot

    async def run(self) -> None:
        while True:
            started = asyncio.get_running_loop().time()
            try:
                await self.collect_once()
            except Exception:
                feed_failures.labels(operation="collect").inc()
                log.exception("candidate_feed_collection_failed")
            active = await self.leases.active()
            for kind in ("entry", "position"):
                feed_active_leases.labels(kind=kind).set(
                    sum(lease.kind == kind for lease in active)
                )
            current_labels = {(lease.candidate_id, lease.kind) for lease in active}
            for candidate_id, kind in self._observed_lease_labels | current_labels:
                feed_lease_active.labels(candidate_id=candidate_id, kind=kind).set(
                    (candidate_id, kind) in current_labels
                )
            self._observed_lease_labels |= current_labels
            snapshot = self.store.peek()
            if snapshot is not None:
                feed_snapshot_age.set(snapshot.age_seconds())
            elapsed = asyncio.get_running_loop().time() - started
            if active:
                await asyncio.sleep(max(0.05, 2.0 - elapsed))
            else:
                await self.leases.wait_for_demand(max(0.05, 60.0 - elapsed))

    async def _refresh_context(self, now: dt.datetime) -> SessionContext:
        session_day = now.astimezone(EASTERN).date()
        spot, vix, intraday, daily = await asyncio.gather(
            self.market.quote("$SPX"),
            self.market.quote("$VIX"),
            self.market.intraday_bars(session_day),
            self.market.daily_bars(),
        )
        session_open = _session_open(intraday, session_day)
        previous_close = _previous_close(daily, session_day)
        if session_open is None or previous_close is None:
            raise SnapshotUnavailableError("complete SPX session context is unavailable")
        return SessionContext(now, spot, vix, session_open, previous_close)

    @staticmethod
    def _normalize_chain(
        chain: dict[str, Any],
        expiration: dt.date,
    ) -> tuple[OptionQuote, ...]:
        quotes = [
            OptionQuote(
                symbol=str(option.get("symbol", "")),
                underlying="SPX",
                expiration=expiration,
                strike=float(strike),
                option_type=option_type,
                bid=float(option.get("bid") or 0),
                ask=float(option.get("ask") or 0),
                mark=float(option.get("mark") or 0),
                last=float(option.get("last") or 0),
                volume=int(option.get("totalVolume") or 0),
                open_interest=int(option.get("openInterest") or 0),
                iv=float(option.get("volatility") or 0),
                delta=float(option.get("delta") or 0),
                gamma=float(option.get("gamma") or 0),
                theta=float(option.get("theta") or 0),
                vega=float(option.get("vega") or 0),
                bid_size=int(option.get("bidSize") or 0),
                ask_size=int(option.get("askSize") or 0),
                rho=float(option.get("rho") or 0),
                intrinsic_value=float(option.get("intrinsicValue") or 0),
                time_value=float(option.get("timeValue") or 0),
                in_the_money=bool(option.get("inTheMoney", False)),
                days_to_expiration=int(option.get("daysToExpiration") or 0),
                multiplier=float(option.get("multiplier") or 100),
                theoretical_value=float(option.get("theoreticalOptionValue") or 0),
            )
            for strike, option_type, option in iter_chain_options(chain, expiration)
            if option.get("symbol")
        ]
        if not quotes:
            raise SnapshotUnavailableError("Schwab returned an empty SPX option chain")
        return tuple(quotes)

    def ready(self) -> tuple[bool, str | None]:
        snapshot = self.store.peek()
        if snapshot is None:
            return False, "snapshot_unavailable"
        if snapshot.age_seconds() > self.stale_after_seconds:
            return False, "snapshot_stale"
        return True, None


def create_app(feed: CandidateFeed) -> web.Application:
    app = web.Application()
    app["feed"] = feed
    app.router.add_get("/health", _health)
    app.router.add_get("/ready", _ready)
    app.router.add_get("/metrics", _metrics)
    app.router.add_get("/v1/snapshot", _snapshot)
    app.router.add_get("/v1/legs", _legs)
    app.router.add_put("/v1/leases/{candidate_id}", _put_lease)
    app.router.add_delete("/v1/leases/{candidate_id}", _delete_lease)
    app.router.add_post(
        "/v1/snapshots/{instance}/{sequence}/pin",
        _pin_snapshot,
    )
    return app


async def _health(request: web.Request) -> web.Response:
    feed: CandidateFeed = request.app["feed"]
    return web.json_response(
        {
            "status": "ok",
            "instance": feed.store.instance,
            "sequence": feed.store.peek().sequence if feed.store.peek() else 0,
        }
    )


async def _ready(request: web.Request) -> web.Response:
    feed: CandidateFeed = request.app["feed"]
    ready, reason = feed.ready()
    return web.json_response(
        {"status": "ready" if ready else "not_ready", "reason": reason},
        status=200 if ready else 503,
    )


async def _metrics(request: web.Request) -> web.Response:
    feed: CandidateFeed = request.app["feed"]
    snapshot = feed.store.peek()
    if snapshot is not None:
        feed_snapshot_age.set(snapshot.age_seconds())
    return web.Response(body=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})


async def _snapshot(request: web.Request) -> web.Response:
    feed: CandidateFeed = request.app["feed"]
    try:
        snapshot = await feed.store.get(
            after=_after_identity(request),
            wait_seconds=_float_query(request, "wait_seconds", 0),
        )
        snapshot.require_fresh(feed.stale_after_seconds)
        return web.json_response(snapshot.to_dict())
    except SnapshotUnavailableError as exc:
        return web.json_response({"error": str(exc)}, status=503)


async def _legs(request: web.Request) -> web.Response:
    feed: CandidateFeed = request.app["feed"]
    symbols = tuple(
        symbol
        for value in request.query.getall("symbol", [])
        for symbol in value.split(",")
        if symbol
    )
    if not symbols:
        return web.json_response({"error": "symbol is required"}, status=400)
    try:
        snapshot = await feed.store.get(
            after=_after_identity(request),
            wait_seconds=_float_query(request, "wait_seconds", 0),
        )
        snapshot.require_fresh(3)
        return web.json_response(snapshot.leg_quotes(symbols).to_dict())
    except (SnapshotUnavailableError, KeyError) as exc:
        return web.json_response({"error": str(exc)}, status=503)


async def _put_lease(request: web.Request) -> web.Response:
    feed: CandidateFeed = request.app["feed"]
    payload = await request.json()
    kind = payload.get("kind")
    if kind not in {"entry", "position"}:
        return web.json_response({"error": "kind must be entry or position"}, status=400)
    lease = await feed.leases.refresh(request.match_info["candidate_id"], kind)
    return web.json_response(
        {
            "candidate_id": lease.candidate_id,
            "kind": lease.kind,
            "expires_at": lease.expires_at.isoformat(),
        }
    )


async def _delete_lease(request: web.Request) -> web.Response:
    feed: CandidateFeed = request.app["feed"]
    removed = await feed.leases.release(request.match_info["candidate_id"])
    return web.Response(status=204 if removed else 404)


async def _pin_snapshot(request: web.Request) -> web.Response:
    feed: CandidateFeed = request.app["feed"]
    try:
        identity = SnapshotIdentity(
            request.match_info["instance"],
            int(request.match_info["sequence"]),
        )
        await feed.archive.pin(identity, feed.store.find(identity))
        return web.json_response({"status": "pinned"}, status=200)
    except (ValueError, SnapshotUnavailableError) as exc:
        feed_archive_failures.labels(kind="pin").inc()
        return web.json_response({"error": str(exc)}, status=503)


def _after_identity(request: web.Request) -> SnapshotIdentity | None:
    instance = request.query.get("after_instance")
    sequence = request.query.get("after_sequence")
    if not instance or not sequence:
        return None
    return SnapshotIdentity(instance, int(sequence))


def _float_query(request: web.Request, name: str, default: float) -> float:
    try:
        return min(max(float(request.query.get(name, default)), 0), 30)
    except ValueError:
        return default


def _session_open(candles: list[dict[str, Any]], day: dt.date) -> float | None:
    values: list[tuple[dt.datetime, float]] = []
    for candle in candles:
        if candle.get("datetime") is None or candle.get("open") is None:
            continue
        timestamp = dt.datetime.fromtimestamp(
            float(candle["datetime"]) / 1000,
            tz=dt.timezone.utc,
        ).astimezone(EASTERN)
        if timestamp.date() == day and timestamp.time() >= MARKET_OPEN:
            values.append((timestamp, float(candle["open"])))
    return min(values)[1] if values else None


def _previous_close(candles: list[dict[str, Any]], day: dt.date) -> float | None:
    values: list[tuple[dt.date, float]] = []
    for candle in candles:
        if candle.get("datetime") is None or candle.get("close") is None:
            continue
        candle_day = dt.datetime.fromtimestamp(
            float(candle["datetime"]) / 1000,
            tz=dt.timezone.utc,
        ).astimezone(EASTERN).date()
        if candle_day < day:
            values.append((candle_day, float(candle["close"])))
    return max(values)[1] if values else None
