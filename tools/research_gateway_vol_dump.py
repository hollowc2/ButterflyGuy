#!/usr/bin/env python3
"""Dump regular-session 1-minute VIX-family candles from the Schwab gateway as JSONL.

Read-only market-data GETs (`/v1/session-history`), one per symbol and weekday. Run it
where the gateway key already is, so the key is never copied or printed, e.g.:

    ssh billy@helios 'docker exec -i butterfly_spx_app python - 2026-08-01 2026-09-25' \
        < tools/research_gateway_vol_dump.py > vol_dump.jsonl

then ingest locally:

    uv run python -m butterfly_guy.research export-vol --gateway-dump vol_dump.jsonl

Schwab keeps about 30 sessions of minute history and returns no bars for `$VIX1D`.
Timestamps are the bar start (a 09:30 bar covers 09:30-09:31 ET).
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import sys

from schwab_gateway_sdk.client import GatewayMarketDataClient

SYMBOLS = ("$VIX", "$VIX9D", "$VIX3M", "$VIX1D")


async def main(start: dt.date, end: dt.date) -> None:
    client = GatewayMarketDataClient(os.environ["SCHWAB_GATEWAY_URL"],
                                     os.environ["SCHWAB_GATEWAY_API_KEY"], timeout_seconds=30)
    day = start
    while day <= end:
        if day.weekday() < 5:
            for symbol in SYMBOLS:
                rec = {"symbol": symbol, "date": day.isoformat(), "bar_seconds": 60}
                try:
                    h = (await client.get_session_history(symbol, day)).session_history
                    rec["flags"] = list(h.data_quality_flags)
                    rec["candles"] = [{"ts": c.timestamp.isoformat(), "open": c.open,
                                       "high": c.high, "low": c.low, "close": c.close}
                                      for c in h.candles]
                except Exception as exc:  # recorded as a coverage gap, never filled
                    rec["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
                print(json.dumps(rec), flush=True)
                await asyncio.sleep(0.2)
        day += dt.timedelta(days=1)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main(dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2])))
