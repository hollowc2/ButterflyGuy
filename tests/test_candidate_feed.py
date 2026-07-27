import asyncio
import datetime as dt
import json
from types import SimpleNamespace

import pytest

import butterfly_guy.candidate_fleet.feed as feed_module
from butterfly_guy.candidate_fleet.feed import (
    AtomicSnapshotStore,
    CandidateFeed,
    LeaseRegistry,
    SnapshotArchive,
    _session_close,
    create_app,
)
from butterfly_guy.candidate_fleet.models import (
    SessionCloseUnavailableError,
    SnapshotIdentity,
)
from butterfly_guy.core.time_utils import EASTERN


class FakeMarket:
    def __init__(self) -> None:
        self.context_calls = 0
        self.chain_calls = 0
        self.intraday_calls = 0

    async def quote(self, symbol: str) -> float:
        self.context_calls += 1
        return 6300 if symbol == "$SPX" else 18

    async def intraday_bars(self, day: dt.date) -> list[dict]:
        self.context_calls += 1
        self.intraday_calls += 1
        await asyncio.sleep(0)
        session_open = dt.datetime.combine(day, dt.time(9, 30), tzinfo=EASTERN)
        final_bar = dt.datetime.combine(day, dt.time(15, 59), tzinfo=EASTERN)
        return [
            {
                "datetime": session_open.timestamp() * 1000,
                "open": 6290,
                "close": 6291,
            },
            {"datetime": final_bar.timestamp() * 1000, "close": 6305.25},
        ]

    async def daily_bars(self) -> list[dict]:
        self.context_calls += 1
        yesterday = dt.datetime.now(EASTERN) - dt.timedelta(days=1)
        return [{"datetime": yesterday.timestamp() * 1000, "close": 6280}]

    async def option_chain(self, expiration: dt.date) -> dict:
        self.chain_calls += 1
        key = f"{expiration.isoformat()}:0"
        option = {
            "symbol": "SPXW TEST",
            "bid": 1,
            "ask": 1.2,
            "mark": 1.1,
        }
        return {"callExpDateMap": {key: {"6300.0": [option]}}}


class FakeArchive:
    def __init__(self) -> None:
        self.archived: list[tuple[int, bool]] = []

    async def archive(self, snapshot, *, baseline: bool = False) -> None:
        self.archived.append((snapshot.sequence, baseline))

    async def archive_session_close(self, evidence):
        return evidence


@pytest.mark.asyncio
async def test_active_feed_fetches_chain_each_cycle_and_context_once_per_minute() -> None:
    market = FakeMarket()
    archive = FakeArchive()
    feed = CandidateFeed(
        market,  # type: ignore[arg-type]
        AtomicSnapshotStore("feed"),
        LeaseRegistry(),
        archive,  # type: ignore[arg-type]
    )

    first = await feed.collect_once()
    second = await feed.collect_once()

    assert first.sequence == 1
    assert second.sequence == 2
    assert market.chain_calls == 2
    assert market.context_calls == 4
    assert archive.archived == [(1, True)]


@pytest.mark.asyncio
async def test_feed_makes_no_market_data_calls_while_market_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market = FakeMarket()
    feed = CandidateFeed(
        market,  # type: ignore[arg-type]
        AtomicSnapshotStore("feed-closed"),
        LeaseRegistry(),
        FakeArchive(),  # type: ignore[arg-type]
    )
    monkeypatch.setattr(feed_module, "is_market_open", lambda: False)

    task = asyncio.create_task(feed.run())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert market.context_calls == 0
    assert market.chain_calls == 0


class FakePool:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []
        self.session_close_row = None

    async def execute(self, sql: str, *args):
        self.calls.append((sql, args))
        if "INSERT INTO candidate_session_closes" in sql:
            self.session_close_row = {
                "session_date": args[0],
                "close": args[1],
                "bar_timestamp": args[2],
                "observed_at": args[3],
                "source": args[4],
                "feed_instance": args[5],
            }
        if sql.lstrip().startswith("UPDATE"):
            return "UPDATE 1"
        return "INSERT 0 1"

    async def fetchrow(self, sql: str, *_args):
        self.calls.append((sql, _args))
        return self.session_close_row


class FakeDb:
    def __init__(self) -> None:
        self.pool = FakePool()


@pytest.mark.asyncio
async def test_snapshot_pinning_is_idempotent_and_persists_recent_snapshot() -> None:
    store = AtomicSnapshotStore("feed-pin")
    market = FakeMarket()
    snapshot = await CandidateFeed(
        market,  # type: ignore[arg-type]
        store,
        LeaseRegistry(),
        FakeArchive(),  # type: ignore[arg-type]
    ).collect_once()
    archive = SnapshotArchive(FakeDb())  # type: ignore[arg-type]

    await archive.pin(snapshot.identity, store.find(snapshot.identity))
    await archive.pin(snapshot.identity, store.find(snapshot.identity))

    updates = [
        call for call in archive.db.pool.calls if call[0].lstrip().startswith("UPDATE")
    ]
    assert len(updates) == 2
    assert store.find(SnapshotIdentity("another-boot", snapshot.sequence)) is None


@pytest.mark.asyncio
async def test_session_close_archive_persists_canonical_evidence() -> None:
    archive = SnapshotArchive(FakeDb())  # type: ignore[arg-type]
    evidence = feed_module.SessionClose(
        session_date=dt.date(2026, 7, 23),
        close=6305.25,
        bar_timestamp=dt.datetime(2026, 7, 23, 15, 59, tzinfo=EASTERN),
        observed_at=dt.datetime(2026, 7, 23, 16, 1, tzinfo=EASTERN),
        source=feed_module.SESSION_CLOSE_SOURCE,
        feed_instance="feed-close",
    )

    persisted = await archive.archive_session_close(evidence)

    assert persisted == evidence
    assert any(
        "INSERT INTO candidate_session_closes" in sql
        for sql, _args in archive.db.pool.calls
    )


@pytest.mark.asyncio
async def test_session_close_endpoint_returns_one_cached_auditable_result() -> None:
    market = FakeMarket()
    feed = CandidateFeed(
        market,  # type: ignore[arg-type]
        AtomicSnapshotStore("feed-close"),
        LeaseRegistry(),
        FakeArchive(),  # type: ignore[arg-type]
    )
    app = create_app(feed)
    request = SimpleNamespace(
        app={"feed": feed},
        match_info={"session_date": "2026-07-23"},
    )
    first_response, second_response = await asyncio.gather(
        _session_close(request),  # type: ignore[arg-type]
        _session_close(request),  # type: ignore[arg-type]
    )
    first = json.loads(first_response.text)
    second = json.loads(second_response.text)

    assert any(
        route.resource.canonical == "/v1/sessions/{session_date}/close"
        for route in app.router.routes()
    )
    assert first_response.status == 200
    assert second_response.status == 200
    assert first == second
    assert first == {
        "session_date": "2026-07-23",
        "close": 6305.25,
        "bar_timestamp": "2026-07-23T19:59:00+00:00",
        "observed_at": first["observed_at"],
        "source": "schwab_spx_intraday_1m_regular_session_close",
        "feed_instance": "feed-close",
    }
    assert dt.datetime.fromisoformat(first["observed_at"]).tzinfo is not None
    assert market.intraday_calls == 1


@pytest.mark.asyncio
async def test_session_close_fails_closed_for_incomplete_or_premature_data() -> None:
    market = FakeMarket()
    feed = CandidateFeed(
        market,  # type: ignore[arg-type]
        AtomicSnapshotStore("feed-close-failure"),
        LeaseRegistry(),
        FakeArchive(),  # type: ignore[arg-type]
    )
    session_day = dt.date(2026, 7, 23)

    with pytest.raises(SessionCloseUnavailableError, match="not final yet"):
        await feed.session_close(
            session_day,
            now=dt.datetime(2026, 7, 23, 15, 59, tzinfo=EASTERN),
        )
    assert market.intraday_calls == 0

    async def incomplete_bars(day: dt.date) -> list[dict]:
        market.intraday_calls += 1
        timestamp = dt.datetime.combine(day, dt.time(15, 58), tzinfo=EASTERN)
        return [{"datetime": timestamp.timestamp() * 1000, "close": 6301}]

    market.intraday_bars = incomplete_bars  # type: ignore[method-assign]
    with pytest.raises(SessionCloseUnavailableError, match="final regular-session"):
        await feed.session_close(
            session_day,
            now=dt.datetime(2026, 7, 23, 16, 1, tzinfo=EASTERN),
        )
    assert market.intraday_calls == 1
