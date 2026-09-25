"""Send the weekly SPX realized-vs-implied diagnostic to Discord #weekend-review.

Read-only: queries option_chain_snapshots, spot_prices and daily_bars; never touches
strategy, orders or the prospective cohort.

Official closes reach daily_bars only when the collector runs at the next session's open,
so the post waits for Monday 10:00 ET to include Friday. After a Monday holiday, Friday
shows as pending and is counted in the rolling windows the following week.

Cron (CRON_TZ=America/Los_Angeles): Monday 7:00 AM PT
  0 7 * * 1 cd /opt/butterflyguy && /opt/butterflyguy/.venv/bin/python tools/send_realized_vs_implied.py >> /opt/butterflyguy/realized_vs_implied.log 2>&1
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import dotenv_values

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.core.time_utils import now_pacific
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.reports.realized_vs_implied import (
    SessionMove,
    atm_straddle,
    format_message,
    summarize,
)
from butterfly_guy.services.notifier import DiscordNotifier

ET = ZoneInfo("America/New_York")
COHORT_START = dt.date(2026, 9, 22)  # spx-prospective-2026-09-22 first eligible session
TRAILING_SESSIONS = 20


def _et(day: dt.date, hh: int, mm: int) -> dt.datetime:
    return dt.datetime.combine(day, dt.time(hh, mm), tzinfo=ET)


async def fetch_session(conn, day: dt.date, underlying: str) -> SessionMove | None:
    snap = await conn.fetchval(
        """
        SELECT min(snapshot_time) FROM option_chain_snapshots
        WHERE underlying = $1 AND expiration = $2
          AND snapshot_time >= $3 AND snapshot_time < $4
        """,
        underlying, day, _et(day, 10, 0), _et(day, 10, 15),
    )
    if snap is None:
        return None
    rows = await conn.fetch(
        """
        SELECT strike, option_type, mark, spot_price FROM option_chain_snapshots
        WHERE underlying = $1 AND expiration = $2 AND snapshot_time = $3
          AND abs(strike - spot_price) <= 15
        """,
        underlying, day, snap,
    )
    if not rows or rows[0]["spot_price"] is None:
        return None
    spot = float(rows[0]["spot_price"])
    straddle = atm_straddle(
        [(float(r["strike"]), r["option_type"],
          float(r["mark"]) if r["mark"] is not None else None) for r in rows],
        spot,
    )
    open_spot = await conn.fetchval(
        """
        SELECT price FROM spot_prices WHERE underlying = $1 AND ts >= $2 AND ts < $3
        ORDER BY ts LIMIT 1
        """,
        underlying, _et(day, 9, 30), _et(day, 16, 0),
    )
    prev_close = await conn.fetchval(
        "SELECT close FROM daily_bars WHERE underlying = $1 AND date < $2 "
        "ORDER BY date DESC LIMIT 1",
        underlying, day,
    )
    if not straddle or open_spot is None or prev_close is None:
        return None
    close = await conn.fetchval(
        "SELECT close FROM daily_bars WHERE underlying = $1 AND date = $2", underlying, day
    )
    return SessionMove(
        date=day,
        spot_10=spot,
        straddle=straddle,
        close=float(close) if close is not None else None,
        gap_sign=1 if float(open_spot) >= float(prev_close) else -1,
    )


async def fetch_sessions(db: DatabasePool, start: dt.date, end: dt.date, underlying: str):
    out: list[SessionMove] = []
    async with db.pool.acquire() as conn:
        async with conn.transaction(readonly=True):
            day = start
            while day <= end:
                if day.weekday() < 5:
                    move = await fetch_session(conn, day, underlying)
                    if move is not None:
                        out.append(move)
                day += dt.timedelta(days=1)
    return out


def review_week(reference: dt.date) -> tuple[dt.date, dt.date]:
    """Monday-Friday of the most recent week that has finished by `reference`."""
    friday = reference - dt.timedelta(days=(reference.weekday() - 4) % 7)
    if friday == reference and reference.weekday() == 4:
        friday -= dt.timedelta(days=7)
    return friday - dt.timedelta(days=4), friday


async def main() -> int:
    parser = argparse.ArgumentParser(description="Weekly SPX realized-vs-implied to Discord")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--week-ending", default=None, help="Friday ending the week (YYYY-MM-DD)")
    parser.add_argument("--since", default=None,
                        help="Print a summary from this date through the week end (no post)")
    parser.add_argument("--dry-run", action="store_true", help="Print instead of posting")
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)
    underlying = config.strategy.underlying
    if args.week_ending:
        week_end = dt.date.fromisoformat(args.week_ending)
        week_start = week_end - dt.timedelta(days=4)
    else:
        week_start, week_end = review_week(now_pacific().date())

    db = DatabasePool(config.database.dsn)
    await db.initialize()
    try:
        if args.since:
            moves = await fetch_sessions(db, dt.date.fromisoformat(args.since), week_end, underlying)
            s = summarize(moves)
            print(f"{args.since}..{week_end}: {s}")
            return 0
        lookback = min(COHORT_START, week_start - dt.timedelta(days=45))
        moves = await fetch_sessions(db, lookback, week_end, underlying)
    finally:
        await db.close()

    message = format_message(
        week_start=week_start,
        week_end=week_end,
        week=[m for m in moves if week_start <= m.date <= week_end],
        cohort=[m for m in moves if m.date >= COHORT_START],
        cohort_start=COHORT_START,
        trailing=[m for m in moves if m.close is not None][-TRAILING_SESSIONS:],
    )
    if args.dry_run:
        print(message)
        return 0

    webhook = os.environ.get("DISCORD_WEEKEND_REVIEW_WEBHOOK") or dotenv_values(ROOT / ".env").get(
        "DISCORD_WEEKEND_REVIEW_WEBHOOK", ""
    )
    if not webhook:
        print("ERROR: DISCORD_WEEKEND_REVIEW_WEBHOOK not configured")
        return 1
    await DiscordNotifier(webhook)._post(message)
    print(f"OK: sent realized-vs-implied for {week_start}..{week_end}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
