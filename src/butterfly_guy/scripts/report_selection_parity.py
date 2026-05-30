"""Summarize Schwab vs DB entry selection parity from decision_log.

Usage:
    uv run python src/butterfly_guy/scripts/report_selection_parity.py
    uv run python src/butterfly_guy/scripts/report_selection_parity.py \\
        2026-05-15 2026-05-29 --asset SPX
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg

from butterfly_guy.core.config import load_config


async def run(start: dt.date | None, end: dt.date | None, asset: str) -> None:
    conn = await asyncpg.connect(load_config().database.dsn)
    try:
        rows = await conn.fetch(
            """
            SELECT ts, data
            FROM decision_log
            WHERE underlying = $1
              AND event_type = 'entry_selection_parity'
              AND ($2::date IS NULL OR ts::date >= $2)
              AND ($3::date IS NULL OR ts::date <= $3)
            ORDER BY ts
            """,
            asset,
            start,
            end,
        )
    finally:
        await conn.close()

    if not rows:
        print("No entry_selection_parity events found.")
        return

    available = 0
    flips = 0
    width_matches = 0
    print(f"{'Date':>12}  {'Lag(s)':>6}  {'Live':>12}  {'DB':>12}  Flip  Per-width cost deltas")
    print("-" * 90)
    for row in rows:
        data = row["data"]
        if isinstance(data, str):
            data = json.loads(data)
        if not data.get("available"):
            reason = data.get("reason", "unavailable")
            print(
                f"{row['ts'].date()!s:>12}  {'n/a':>6}  {'—':>12}  {'—':>12}  —     {reason}"
            )
            continue

        available += 1
        if data.get("ranking_flip"):
            flips += 1
        if data.get("width_match"):
            width_matches += 1

        live = data.get("live_selected") or {}
        db = data.get("db_selected") or {}
        live_s = f"{live.get('width', '?')}W/{live.get('center', '?')}"
        db_s = f"{db.get('width', '?')}W/{db.get('center', '?')}"
        deltas = data.get("per_width_deltas") or []
        delta_s = ", ".join(
            f"{d['width']}W:mark{d.get('mark_delta', d.get('cost_delta', 0)):+.2f}" for d in deltas
        ) or "-"
        flip_s = "YES" if data.get("ranking_flip") else "no"
        lag = data.get("snapshot_lag_seconds")
        lag_s = f"{lag:.0f}" if lag is not None else "?"
        print(
            f"{row['ts'].date()!s:>12}  {lag_s:>6}  {live_s:>12}  {db_s:>12}  "
            f"{flip_s:<4}  {delta_s}"
        )

    print("-" * 90)
    print(
        f"Events: {len(rows)}  Available: {available}  "
        f"Width match: {width_matches}/{available}  "
        f"Ranking flips: {flips}/{available} ({(flips / available * 100):.0f}%)" if available else
        f"Events: {len(rows)}  Available: 0"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report Schwab vs DB entry selection parity")
    parser.add_argument("start", nargs="?", type=dt.date.fromisoformat)
    parser.add_argument("end", nargs="?", type=dt.date.fromisoformat)
    parser.add_argument("--asset", default="SPX")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args.start, args.end, args.asset))


if __name__ == "__main__":
    main()
