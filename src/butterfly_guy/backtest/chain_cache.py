"""Real option chain cache — per-day JSON snapshots from the live collector.

Format: data/chains/YYYY-MM-DD.json
  {
    "date": "2026-03-10",
    "snapshots": {
      "2026-03-10T14:30:00+00:00": {
        "spot": 6803.88,
        "quotes": [
          {"strike": 6800, "type": "CALL", "bid": 5.2, "ask": 5.4, "mark": 5.3,
           "iv": 0.15, "delta": 0.85, "gamma": 0.02, "symbol": "SPXW..."},
          ...
        ]
      },
      ...
    }
  }

As the collector runs each day it appends snapshots to today's file.
Simulation uses real quotes when available, falls back to synthetic otherwise.
"""

from __future__ import annotations

import bisect
import datetime as dt
import json
from pathlib import Path

from butterfly_guy.data.schemas import OptionQuote

CHAIN_CACHE_DIR = Path("data/chains")


class ChainDay(dict):
    """dict of {UTC datetime: OptionQuote list} with a pre-sorted key index for O(log n) lookups."""

    _sorted_keys: list

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sorted_keys = sorted(self.keys())


def chain_cache_path(date: dt.date, cache_dir: Path = CHAIN_CACHE_DIR) -> Path:
    return cache_dir / f"{date.isoformat()}.json"


def save_snapshot(
    date: dt.date,
    snapshot_time: dt.datetime,
    spot: float,
    rows: list[dict],
    cache_dir: Path = CHAIN_CACHE_DIR,
) -> None:
    """Append one chain snapshot to the day's cache file.

    Called by the collector after each successful chain fetch.
    rows is the list of parsed option rows (same format as bulk_insert_snapshot).
    """
    path = chain_cache_path(date, cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"date": date.isoformat(), "snapshots": {}}

    quotes = [
        {
            "strike": r["strike"],
            "type": r["option_type"],
            "bid": r.get("bid") or 0.0,
            "ask": r.get("ask") or 0.0,
            "mark": r.get("mark") or 0.0,
            "iv": r.get("iv") or 0.0,
            "delta": r.get("delta") or 0.0,
            "gamma": r.get("gamma") or 0.0,
            "symbol": r.get("symbol") or "",
            "bid_size": r.get("bid_size") or 0,
            "ask_size": r.get("ask_size") or 0,
        }
        for r in rows
    ]
    data["snapshots"][snapshot_time.isoformat()] = {"spot": spot, "quotes": quotes}
    path.write_text(json.dumps(data), encoding="utf-8")


def load_chain_day(
    date: dt.date,
    cache_dir: Path = CHAIN_CACHE_DIR,
) -> dict[dt.datetime, list[OptionQuote]] | None:
    """Load all chain snapshots for a day.

    Returns dict of UTC datetime -> list[OptionQuote], or None if no cache file.
    The simulation engine calls this once per day and uses nearest-prior snapshot
    at each bar instead of generating a synthetic chain.
    """
    path = chain_cache_path(date, cache_dir)
    if not path.exists():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    result: dict[dt.datetime, list[OptionQuote]] = {}

    for ts_str, snap in data["snapshots"].items():
        ts = dt.datetime.fromisoformat(ts_str)
        quotes = [
            OptionQuote(
                symbol=q.get("symbol") or f"REAL_{q['type'][0]}{int(q['strike'])}",
                underlying="SPX",
                expiration=date,
                strike=q["strike"],
                option_type=q["type"],
                bid=float(q["bid"]),
                ask=float(q["ask"]),
                mark=float(q["mark"]),
                iv=float(q.get("iv") or 0.0),
                delta=float(q.get("delta") or 0.0),
                gamma=float(q.get("gamma") or 0.0),
                bid_size=int(q.get("bid_size") or 0),
                ask_size=int(q.get("ask_size") or 0),
            )
            for q in snap["quotes"]
            if q.get("mark") is not None
        ]
        result[ts] = quotes

    return ChainDay(result) if result else None


def nearest_snapshot(
    chains: dict[dt.datetime, list[OptionQuote]],
    bar_ts: dt.datetime,
) -> list[OptionQuote] | None:
    """Return quotes from the most recent snapshot at or before bar_ts."""
    if isinstance(chains, ChainDay):
        keys = chains._sorted_keys
        i = bisect.bisect_right(keys, bar_ts) - 1
        return chains[keys[i]] if i >= 0 else None
    candidates = [ts for ts in chains if ts <= bar_ts]
    return chains[max(candidates)] if candidates else None
