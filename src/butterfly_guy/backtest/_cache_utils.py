"""JSON cache helpers for DayData — shared across Schwab and future loaders."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from butterfly_guy.backtest.data_loader import DayData, MinuteBar


def day_cache_path(date: dt.date, cache_dir: Path) -> Path:
    return cache_dir / f"{date.isoformat()}.json"


def save_day(day: DayData, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "date": day.date.isoformat(),
        "vix": day.vix,
        "prev_close": day.prev_close,
        "bars": [
            {
                "ts": bar.ts.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in day.bars
        ],
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def load_day(path: Path) -> DayData:
    data = json.loads(path.read_text(encoding="utf-8"))
    bars = [
        MinuteBar(
            ts=dt.datetime.fromisoformat(b["ts"]),
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
            volume=b["volume"],
        )
        for b in data["bars"]
    ]
    return DayData(
        date=dt.date.fromisoformat(data["date"]),
        vix=data["vix"],
        prev_close=data["prev_close"],
        bars=bars,
    )
