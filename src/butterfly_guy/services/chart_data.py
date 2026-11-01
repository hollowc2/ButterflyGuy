"""Load spot price series from TimescaleDB for chart generation."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.services.trade_chart import FlyMarkPoint


def spot_rows_to_candles(rows: list) -> list[dict]:
    return [
        {"datetime": int(row["ts"].timestamp() * 1000), "close": float(row["price"])}
        for row in rows
    ]


async def load_spot_series(
    db: DatabasePool,
    underlying: str,
    session_date: dt.date,
) -> list[dict]:
    rows = await db.pool.fetch(
        """
        SELECT ts, price
        FROM spot_prices
        WHERE underlying = $1
          AND ts >= $2::timestamptz
          AND ts < $3::timestamptz
        ORDER BY ts ASC
        """,
        underlying,
        dt.datetime.combine(session_date, dt.time.min, tzinfo=dt.timezone.utc),
        dt.datetime.combine(session_date + dt.timedelta(days=1), dt.time.min, tzinfo=dt.timezone.utc),
    )
    return spot_rows_to_candles(rows)


async def load_fly_marks(db: DatabasePool, trade_id: int) -> list[FlyMarkPoint]:
    """One point per monitor poll; every leg row of a poll carries the same fly mark."""
    rows = await db.pool.fetch(
        """
        SELECT DISTINCT ON (ts) ts, fly_mark
        FROM monitoring_leg_quotes
        WHERE trade_id = $1 AND fly_mark IS NOT NULL
        ORDER BY ts ASC
        """,
        trade_id,
    )
    return [FlyMarkPoint(ts=row["ts"], mark=float(row["fly_mark"])) for row in rows]
