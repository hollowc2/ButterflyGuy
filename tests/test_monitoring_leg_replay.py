from __future__ import annotations

import datetime as dt

from butterfly_guy.backtest.chain_cache import ChainDay
from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.data.schemas import OptionQuote
from butterfly_guy.scripts.run_backtest_db import day_with_monitoring_bars


def _bar(ts: dt.datetime, close: float) -> MinuteBar:
    return MinuteBar(ts=ts, open=close, high=close, low=close, close=close, volume=0)


def test_day_with_monitoring_bars_adds_live_poll_timestamps():
    base_ts = dt.datetime(2026, 5, 20, 14, 0, tzinfo=dt.timezone.utc)
    poll_ts = base_ts + dt.timedelta(seconds=2)
    next_ts = base_ts + dt.timedelta(minutes=1)
    day = DayData(
        date=base_ts.date(),
        bars=[_bar(base_ts, 7400.0), _bar(next_ts, 7401.0)],
        vix=18.0,
        prev_close=7390.0,
        recent_closes=[7380.0, 7390.0],
    )
    monitoring = ChainDay(
        {
            poll_ts: [
                OptionQuote(
                    symbol="SPXW260520C7400",
                    underlying="SPX",
                    expiration=base_ts.date(),
                    strike=7400.0,
                    option_type="CALL",
                    bid=1.0,
                    ask=1.1,
                    mark=1.05,
                )
            ]
        }
    )

    augmented = day_with_monitoring_bars(day, monitoring)

    assert [bar.ts for bar in augmented.bars] == [base_ts, poll_ts, next_ts]
    assert augmented.bars[1].close == 7400.0
    assert augmented.vix == day.vix
    assert augmented.recent_closes == day.recent_closes


def test_day_with_monitoring_bars_keeps_existing_bar_for_same_timestamp():
    base_ts = dt.datetime(2026, 5, 20, 14, 0, tzinfo=dt.timezone.utc)
    day = DayData(
        date=base_ts.date(),
        bars=[_bar(base_ts, 7400.0)],
        vix=18.0,
        prev_close=7390.0,
    )
    monitoring = ChainDay({base_ts: []})

    augmented = day_with_monitoring_bars(day, monitoring)

    assert augmented.bars == day.bars
