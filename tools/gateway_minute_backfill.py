#!/usr/bin/env python3
"""Archive regular-session 1-minute index candles from the Schwab gateway as JSONL.

Schwab keeps only about 30 sessions of minute history, so a day our recorder missed is
lost for good once it rolls off. `tools/run_gateway_minute_backfill.sh` runs this once a
month on Helios (`infra/cron/gateway_minute_backfill.cron`), inside the SPX app container
so the gateway key is never copied or printed:

    docker exec -i butterfly_spx_app python - START END SYMBOL... \\
        < tools/gateway_minute_backfill.py > dump.jsonl

Read-only market-data GETs (`/v1/session-history`), one per symbol and weekday. Output is
one JSON object per symbol and date, the record format of the research branch's
`tools/research_gateway_vol_dump.py`, so a VIX-family file can be ingested with
`research export-vol --gateway-dump`. A date with no bars or an error is written as such
and never filled. Timestamps are the bar start (a 09:30 bar covers 09:30-09:31 ET).
`$VIX1D` is left out: the gateway returns no bars for it.

Dates before the retention edge come back with no bars and are not an error. Exits 1 when
a request failed, a symbol returned no bars at all, or a weekday after a symbol's first
retained day has no bars and no `market_holiday` flag (a hole). The records written are
kept either way.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import sys

from schwab_gateway_sdk.client import GatewayMarketDataClient


async def dump(client, start: dt.date, end: dt.date, symbols: list[str], out) -> list[dict]:
    """Write one record per symbol and weekday to `out`; return them without candles."""
    written = []
    day = start
    while day <= end:
        if day.weekday() < 5:
            for symbol in symbols:
                rec = {"symbol": symbol, "date": day.isoformat(), "bar_seconds": 60}
                try:
                    h = (await client.get_session_history(symbol, day)).session_history
                    rec["flags"] = list(h.data_quality_flags)
                    rec["candles"] = [{"ts": c.timestamp.isoformat(), "open": c.open,
                                       "high": c.high, "low": c.low, "close": c.close}
                                      for c in h.candles]
                except Exception as exc:  # recorded as a coverage gap, never filled
                    rec["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
                out.write(json.dumps(rec) + "\n")
                out.flush()
                written.append({"symbol": symbol, "date": rec["date"],
                                "bars": len(rec.get("candles", [])),
                                "flags": rec.get("flags", []), "error": rec.get("error")})
                await asyncio.sleep(0.2)
        day += dt.timedelta(days=1)
    return written


def check(records: list[dict]) -> tuple[list[str], list[str]]:
    """Per-symbol summary lines and the problems that make the run a failure."""
    summary, problems = [], []
    for symbol in dict.fromkeys(r["symbol"] for r in records):
        recs = [r for r in records if r["symbol"] == symbol]
        problems += [f"{symbol} {r['date']}: {r['error']}" for r in recs if r["error"]]
        with_bars = [r["date"] for r in recs if r["bars"]]
        if not with_bars:
            problems.append(f"{symbol}: no bars on any date")
            continue
        holes = [r["date"] for r in recs
                 if r["date"] > with_bars[0] and not r["bars"] and not r["error"]
                 and "market_holiday" not in r["flags"]]
        problems += [f"{symbol} {d}: no bars inside the retained range" for d in holes]
        summary.append(f"{symbol}: {len(with_bars)} sessions with bars, "
                       f"{with_bars[0]} -> {with_bars[-1]}")
    return summary, problems


async def main(argv: list[str]) -> int:
    start, end, symbols = dt.date.fromisoformat(argv[0]), dt.date.fromisoformat(argv[1]), argv[2:]
    client = GatewayMarketDataClient(os.environ["SCHWAB_GATEWAY_URL"],
                                     os.environ["SCHWAB_GATEWAY_API_KEY"], timeout_seconds=30)
    try:
        records = await dump(client, start, end, symbols, sys.stdout)
    finally:
        await client.close()
    summary, problems = check(records)
    for line in summary + [f"PROBLEM {p}" for p in problems]:
        print(line, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
