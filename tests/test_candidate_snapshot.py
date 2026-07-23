import asyncio
import datetime as dt

import pytest

from butterfly_guy.candidate_fleet.feed import AtomicSnapshotStore, LeaseRegistry
from butterfly_guy.candidate_fleet.models import (
    MarketSnapshot,
    SnapshotIdentity,
    SnapshotUnavailableError,
    StaleSnapshotError,
)
from butterfly_guy.data.schemas import OptionQuote


def quote(symbol: str = "SPXW CALL 5000", strike: float = 5000) -> OptionQuote:
    return OptionQuote(
        symbol=symbol,
        underlying="SPX",
        expiration=dt.date(2026, 7, 23),
        strike=strike,
        option_type="CALL",
        bid=1.0,
        ask=1.2,
        mark=1.1,
    )


def snapshot(
    *,
    instance: str = "feed-a",
    sequence: int = 1,
    captured_at: dt.datetime | None = None,
) -> MarketSnapshot:
    return MarketSnapshot(
        identity=SnapshotIdentity(instance, sequence),
        captured_at=captured_at or dt.datetime.now(dt.timezone.utc),
        expiration=dt.date(2026, 7, 23),
        spot=6350,
        vix=18,
        session_open=6340,
        previous_close=6330,
        quotes=(quote(),),
    )


def test_snapshot_round_trip_and_immutable_indexes() -> None:
    original = snapshot()
    restored = MarketSnapshot.from_dict(original.to_dict())

    assert restored == original
    assert restored.by_symbol()["SPXW CALL 5000"].strike == 5000
    assert restored.by_strike_type()[(5000, "CALL")].mark == 1.1
    with pytest.raises(TypeError):
        restored.by_symbol()["new"] = quote()  # type: ignore[index]


def test_snapshot_rejects_stale_data() -> None:
    old = snapshot(
        captured_at=dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=4)
    )
    with pytest.raises(StaleSnapshotError):
        old.require_fresh(3)


@pytest.mark.asyncio
async def test_atomic_store_sequence_and_boot_instance_change() -> None:
    store = AtomicSnapshotStore("boot-one")
    first = await store.publish(
        captured_at=dt.datetime.now(dt.timezone.utc),
        expiration=dt.date(2026, 7, 23),
        spot=6350,
        vix=18,
        session_open=6340,
        previous_close=6330,
        quotes=(quote(),),
    )
    waiter = asyncio.create_task(store.get(after=first.identity, wait_seconds=1))
    second = await store.publish(
        captured_at=dt.datetime.now(dt.timezone.utc),
        expiration=dt.date(2026, 7, 23),
        spot=6351,
        vix=18,
        session_open=6340,
        previous_close=6330,
        quotes=(quote(),),
    )

    assert (await waiter).identity == second.identity
    assert second.sequence == 2
    assert AtomicSnapshotStore("boot-two").instance != store.instance


@pytest.mark.asyncio
async def test_lease_cadence_and_ttl_expiry() -> None:
    leases = LeaseRegistry(ttl_seconds=30)
    now = dt.datetime(2026, 7, 23, tzinfo=dt.timezone.utc)

    assert await leases.polling_interval(now) == 60
    lease = await leases.refresh("best-rr", "position", now=now)
    assert lease.expires_at == now + dt.timedelta(seconds=30)
    assert await leases.polling_interval(now + dt.timedelta(seconds=29)) == 2
    assert await leases.polling_interval(now + dt.timedelta(seconds=30)) == 60


@pytest.mark.asyncio
async def test_new_lease_wakes_idle_feed() -> None:
    leases = LeaseRegistry()
    waiter = asyncio.create_task(leases.wait_for_demand(1))
    await asyncio.sleep(0)

    await leases.refresh("best-rr", "entry")

    assert await waiter is True


@pytest.mark.asyncio
async def test_long_poll_never_replays_same_sequence() -> None:
    store = AtomicSnapshotStore("feed")
    current = await store.publish(
        captured_at=dt.datetime.now(dt.timezone.utc),
        expiration=dt.date(2026, 7, 23),
        spot=6350,
        vix=18,
        session_open=6340,
        previous_close=6330,
        quotes=(quote(),),
    )

    with pytest.raises(SnapshotUnavailableError, match="no newer"):
        await store.get(after=current.identity, wait_seconds=0.01)
