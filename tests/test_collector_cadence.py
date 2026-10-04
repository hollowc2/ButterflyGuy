"""The aligned collector loop on a fake clock: grid alignment, overrun skips, early close."""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from butterfly_guy.core.config import AppConfig
from butterfly_guy.data import collector as collector_module
from butterfly_guy.data.collector import OptionChainCollector, next_tick

ET = ZoneInfo("America/New_York")


class StopLoopError(Exception):
    pass


class FakeClock:
    """Wall and monotonic time that move only when the loop sleeps or a pass runs."""

    def __init__(self, start: dt.datetime, end: dt.datetime) -> None:
        self.wall, self.mono, self.end = start, 1000.0, end

    def now(self) -> dt.datetime:
        return self.wall

    def monotonic(self) -> float:
        return self.mono

    def advance(self, seconds: float) -> None:
        self.wall += dt.timedelta(seconds=seconds)
        self.mono += seconds

    async def sleep(self, seconds: float) -> None:
        self.advance(seconds)
        if self.wall >= self.end:
            raise StopLoopError


def _run(start: dt.datetime, end: dt.datetime, durations: dict[int, float] | None = None,
         *, offset: float = 0.0, record_timing: bool = True):
    """Run the aligned loop from `start` to `end`; pass i takes durations.get(i, 4) s.
    Returns (scheduled ticks, pass start times, notify mock, missed-tick increments)."""
    config = AppConfig()
    config.collector.align_to_minute = True
    config.collector.align_offset_seconds = offset
    config.collector.record_timing = record_timing
    clock = FakeClock(start, end)
    c = OptionChainCollector(config, MagicMock(), MagicMock(), MagicMock())
    c._now, c._monotonic, c._sleep = clock.now, clock.monotonic, clock.sleep
    scheduled, started = [], []

    async def timed(scheduled_at, *, chain_first):
        assert chain_first
        scheduled.append(scheduled_at)
        started.append(clock.now())
        clock.advance((durations or {}).get(len(started) - 1, 4.0))
        return 1

    async def plain():
        scheduled.append(None)
        started.append(clock.now())
        clock.advance((durations or {}).get(len(started) - 1, 4.0))
        return 1

    c._collect_timed_snapshot = timed
    c.collect_snapshot = plain
    c.collect_daily_bars = AsyncMock()
    missed = MagicMock()
    with patch.object(collector_module, "notify", AsyncMock()) as notify, \
            patch.object(collector_module.collector_missed_ticks, "labels",
                         return_value=missed):
        import asyncio
        with pytest.raises(StopLoopError):
            asyncio.run(c.run_loop())
    return scheduled, started, notify, [x.args[0] for x in missed.inc.call_args_list]


def et(h: int, m: int, s: float = 0.0, day: dt.date = dt.date(2026, 10, 5)) -> dt.datetime:
    whole = int(s)
    return dt.datetime(day.year, day.month, day.day, h, m, whole,
                       int(round((s - whole) * 1e6)), tzinfo=ET).astimezone(dt.UTC)


def test_next_tick():
    assert next_tick(et(10, 0, 17.3), 0) == et(10, 1)
    assert next_tick(et(10, 1), 0) == et(10, 1)
    assert next_tick(et(10, 0, 17.3), 2.5) == et(10, 0, 2.5) + dt.timedelta(minutes=1)
    assert next_tick(et(10, 0, 1.0), 2.5) == et(10, 0, 2.5)
    assert next_tick(et(10, 0, 59.0), -1.5) == et(10, 0, 58.5) + dt.timedelta(minutes=1)


def test_passes_start_on_the_minute_grid():
    scheduled, started, _, missed = _run(et(10, 0, 17.3), et(10, 5, 30))
    assert scheduled == [et(10, m) for m in range(1, 6)]
    assert started == scheduled  # each sleep ends at its absolute deadline
    assert missed == []


def test_offset_shifts_the_grid():
    scheduled, _, _, _ = _run(et(10, 0, 17.3), et(10, 3, 30), offset=2.5)
    assert scheduled == [et(10, m, 2.5) for m in range(1, 4)]


def test_overrun_skips_the_missed_tick_without_a_burst():
    scheduled, started, notify, missed = _run(et(10, 0, 30), et(10, 6, 30), {1: 75.0})
    # Pass 2 (10:02) ran until 10:03:15, so 10:03 is skipped and the next runs at 10:04.
    assert scheduled == [et(10, 1), et(10, 2), et(10, 4), et(10, 5), et(10, 6)]
    assert started == scheduled
    assert missed == [1]
    notify.assert_not_awaited()


def test_a_stall_alerts_once_and_never_catches_up():
    scheduled, started, notify, missed = _run(et(10, 0, 30), et(10, 9, 30), {1: 200.0})
    # 10:02 ran until 10:05:20: 10:03, 10:04 and 10:05 are skipped, then the grid resumes.
    assert scheduled == [et(10, 1), et(10, 2), et(10, 6), et(10, 7), et(10, 8), et(10, 9)]
    assert all(b - a >= dt.timedelta(minutes=1) for a, b in zip(started, started[1:],
                                                                    strict=False))
    assert missed == [3]
    messages = [c.args[0] for c in notify.await_args_list]
    assert len(messages) == 2 and "missed 3" in messages[0] and "back on" in messages[1]


def test_first_tick_is_the_open_and_last_is_before_the_early_close():
    day = dt.date(2026, 11, 27)  # day after Thanksgiving: 13:00 close
    scheduled, _, _, _ = _run(et(9, 28, 40, day), et(9, 32, 30, day))
    assert scheduled[0] == et(9, 30, 0, day)
    scheduled, _, _, _ = _run(et(12, 57, 40, day), et(13, 3, 30, day))
    assert scheduled == [et(12, 58, 0, day), et(12, 59, 0, day)]


def test_untimed_config_uses_the_plain_pass():
    scheduled, started, _, _ = _run(et(10, 0, 17.3), et(10, 2, 30), record_timing=False)
    assert scheduled == [None, None] and started == [et(10, 1), et(10, 2)]


def test_default_config_keeps_the_old_loop():
    config = AppConfig()
    assert config.collector.align_to_minute is False
    c = OptionChainCollector(config, MagicMock(), MagicMock(), MagicMock())
    c.run_aligned_loop = AsyncMock()
    c.collect_daily_bars = AsyncMock()
    c.collect_snapshot = AsyncMock(return_value=1)
    sleeps = []

    async def sleep(seconds):
        sleeps.append(seconds)
        raise StopLoopError

    import asyncio
    with patch.object(collector_module, "is_market_open", return_value=True), \
            patch.object(collector_module.asyncio, "sleep", sleep), pytest.raises(StopLoopError):
        asyncio.run(c.run_loop())
    c.run_aligned_loop.assert_not_awaited()
    assert sleeps == [60]  # a fixed interval after the work, as before
