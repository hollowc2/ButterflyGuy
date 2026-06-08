"""Tests for equity scan volume helpers."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.equity_scan.volume import avg_daily_volume


def test_avg_daily_volume_excludes_today_candle():
    today_start_ms = int(
        dt.datetime.combine(dt.date.today(), dt.time.min).timestamp() * 1000
    )
    candles = [
        {"volume": 1_000_000, "datetime": today_start_ms - 86_400_000},
        {"volume": 2_000_000, "datetime": today_start_ms - 43_200_000},
        {"volume": 5_000_000, "datetime": today_start_ms},
    ]
    avg = avg_daily_volume(candles, lookback=2)
    assert avg == 1_500_000.0
