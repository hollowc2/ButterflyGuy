import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "gateway_minute_backfill",
    Path(__file__).parent.parent / "tools" / "gateway_minute_backfill.py",
)
backfill = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backfill)

UTC = dt.timezone.utc


class FakeClient:
    """Answers from a {(symbol, date): flags | Exception} table; flags without
    `no_bars_returned` come back with two candles."""

    def __init__(self, table):
        self.table, self.calls = table, []

    async def get_session_history(self, symbol, day):
        self.calls.append((symbol, day))
        answer = self.table.get((symbol, day), ["no_bars_returned"])
        if isinstance(answer, Exception):
            raise answer
        candles = [] if "no_bars_returned" in answer else [
            SimpleNamespace(timestamp=dt.datetime.combine(day, dt.time(13, 30 + i), UTC),
                            open=1.0, high=2.0, low=0.5, close=1.5)
            for i in range(2)
        ]
        return SimpleNamespace(session_history=SimpleNamespace(
            data_quality_flags=answer, candles=candles))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    async def instant(_):
        return None

    monkeypatch.setattr(backfill.asyncio, "sleep", instant)


async def test_dump_writes_one_research_format_record_per_symbol_and_weekday():
    fri, mon = dt.date(2026, 9, 25), dt.date(2026, 9, 28)
    client = FakeClient({("$SPX", fri): ["stale"], ("$VIX", fri): ["stale"],
                         ("$SPX", mon): ["stale"], ("$VIX", mon): RuntimeError("boom")})
    out = io.StringIO()

    await backfill.dump(client, fri, mon, ["$SPX", "$VIX"], out)

    lines = [json.loads(line) for line in out.getvalue().splitlines()]
    assert [(r["symbol"], r["date"]) for r in lines] == [
        ("$SPX", "2026-09-25"), ("$VIX", "2026-09-25"),
        ("$SPX", "2026-09-28"), ("$VIX", "2026-09-28"),
    ]  # the weekend is never requested
    assert lines[0] == {
        "symbol": "$SPX", "date": "2026-09-25", "bar_seconds": 60, "flags": ["stale"],
        "candles": [
            {"ts": "2026-09-25T13:30:00+00:00", "open": 1.0, "high": 2.0, "low": 0.5,
             "close": 1.5},
            {"ts": "2026-09-25T13:31:00+00:00", "open": 1.0, "high": 2.0, "low": 0.5,
             "close": 1.5},
        ],
    }
    assert lines[3]["error"] == "RuntimeError: boom" and "candles" not in lines[3]


def rec(symbol, date, bars=390, flags=(), error=None):
    return {"symbol": symbol, "date": date, "bars": bars, "flags": list(flags), "error": error}


def test_days_before_retention_and_holidays_are_not_problems():
    records = [
        rec("$SPX", "2026-08-03", 0, ["no_bars_returned", "stale"]),
        rec("$SPX", "2026-08-04", 390),
        rec("$SPX", "2026-09-07", 0, ["market_holiday", "no_bars_returned"]),
        rec("$SPX", "2026-09-08", 390),
    ]

    summary, problems = backfill.check(records)

    assert problems == []
    assert summary == ["$SPX: 2 sessions with bars, 2026-08-04 -> 2026-09-08"]


def test_holes_errors_and_empty_symbols_are_problems():
    records = [
        rec("$SPX", "2026-08-04", 390),
        rec("$SPX", "2026-08-05", 0, ["no_bars_returned"]),
        rec("$SPX", "2026-08-06", 0, error="HTTPError: 503"),
        rec("$SPX", "2026-08-07", 390),
        rec("$VIX", "2026-08-04", 0, ["no_bars_returned"]),
    ]

    _, problems = backfill.check(records)

    assert problems == [
        "$SPX 2026-08-06: HTTPError: 503",
        "$SPX 2026-08-05: no bars inside the retained range",
        "$VIX: no bars on any date",
    ]
