"""Load spot price series from TimescaleDB for chart generation."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.db.connection import DatabasePool


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
