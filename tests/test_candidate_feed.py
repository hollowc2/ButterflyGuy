import datetime as dt

import pytest

from butterfly_guy.candidate_fleet.feed import (
    AtomicSnapshotStore,
    CandidateFeed,
    LeaseRegistry,
    SnapshotArchive,
)
from butterfly_guy.candidate_fleet.models import SnapshotIdentity
from butterfly_guy.core.time_utils import EASTERN


class FakeMarket:
    def __init__(self) -> None:
        self.context_calls = 0
        self.chain_calls = 0

    async def quote(self, symbol: str) -> float:
        self.context_calls += 1
        return 6300 if symbol == "$SPX" else 18

    async def intraday_bars(self, day: dt.date) -> list[dict]:
        self.context_calls += 1
        timestamp = dt.datetime.combine(
            day,
            dt.time(9, 30),
            tzinfo=EASTERN,
        )
        return [{"datetime": timestamp.timestamp() * 1000, "open": 6290}]

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


class FakePool:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    async def execute(self, sql: str, *args):
        self.calls.append((sql, args))
        if sql.lstrip().startswith("UPDATE"):
            return "UPDATE 1"
        return "INSERT 0 1"


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
