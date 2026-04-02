"""DB-backed data loader for historical SPX + VIX data.

Reads from the live TimescaleDB database:
  - spot_prices  → 1-minute (or collector-interval) bars for SPX and VIX
  - daily_bars   → daily closes for prev_close and VIX daily

This is a synchronous wrapper around asyncpg so inspect_entry.py can call
it without an async event loop, matching the same interface as CsvDataLoader.
"""

from __future__ import annotations

import asyncio
import datetime as dt
from zoneinfo import ZoneInfo

import asyncpg

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

EASTERN = ZoneInfo("America/New_York")


class DbDataLoader:
    """Loads SPX + VIX data from TimescaleDB and serves DayData objects.

    Connects synchronously on construction and caches nothing — each
    load_day() call issues two small DB queries (≈ milliseconds).

    Parameters
    ----------
    dsn:
        asyncpg-compatible DSN, e.g.
        ``postgresql://user:pass@host:5432/butterfly_guy``
    underlying:
        The underlying asset symbol (e.g. "SPX", "NDX", "XSP").
    """

    def __init__(self, dsn: str, underlying: str = "SPX") -> None:
        self.dsn = dsn
        self.underlying = underlying
        # Test connectivity eagerly so failures are obvious
        self._run(self._ping())
        log.info("db_loader_ready", dsn=dsn.split("@")[-1], underlying=underlying)

    # ------------------------------------------------------------------
    # Public API  (mirrors CsvDataLoader)
    # ------------------------------------------------------------------

    def load_day(self, date: dt.date) -> DayData | None:
        """Return DayData for *date*, or None if no bars found."""
        return self._run(self._load_day_async(date))

    def available_dates(self) -> list[dt.date]:
        """Return all dates that have spot_price rows for this underlying."""
        return self._run(self._available_dates_async())

    # ------------------------------------------------------------------
    # Async internals
    # ------------------------------------------------------------------

    async def _ping(self) -> None:
        conn = await asyncpg.connect(self.dsn)
        await conn.close()

    async def _load_day_async(self, date: dt.date) -> DayData | None:
        conn = await asyncpg.connect(self.dsn)
        try:
            # 1. Spot bars for the day (stored in UTC, filter by ET date)
            day_start_et = dt.datetime(date.year, date.month, date.day,
                                       0, 0, 0, tzinfo=EASTERN)
            day_end_et = day_start_et + dt.timedelta(days=1)
            day_start_utc = day_start_et.astimezone(dt.timezone.utc)
            day_end_utc = day_end_et.astimezone(dt.timezone.utc)

            spot_rows = await conn.fetch(
                """
                SELECT ts, price
                FROM   spot_prices
                WHERE  underlying = $1
                  AND  ts >= $2
                  AND  ts <  $3
                ORDER  BY ts
                """,
                self.underlying, day_start_utc, day_end_utc,
            )

            if not spot_rows:
                log.warning("db_loader_no_bars", date=str(date), underlying=self.underlying)
                return None

            bars = [
                MinuteBar(
                    ts=row["ts"],           # already UTC-aware from asyncpg
                    open=float(row["price"]),
                    high=float(row["price"]),
                    low=float(row["price"]),
                    close=float(row["price"]),
                    volume=0,
                )
                for row in spot_rows
            ]

            # 2. VIX for the day — prefer daily_bars, fall back to spot_prices
            vix = await self._get_vix(conn, date)

            # 3. Previous trading day's close from daily_bars
            prev_close = await self._get_prev_close(conn, date)

            # 4. Recent 30 closes for bias / trend filters
            recent_closes = await self._get_recent_closes(conn, date, n=30)

            # 5. VIX minute bars (from spot_prices for $VIX)
            vix_rows = await conn.fetch(
                """
                SELECT ts, price
                FROM   spot_prices
                WHERE  underlying = '$VIX'
                  AND  ts >= $1
                  AND  ts <  $2
                ORDER  BY ts
                """,
                day_start_utc, day_end_utc,
            )
            vix_bars = [
                MinuteBar(
                    ts=row["ts"],
                    open=float(row["price"]),
                    high=float(row["price"]),
                    low=float(row["price"]),
                    close=float(row["price"]),
                    volume=0,
                )
                for row in vix_rows
            ]

            return DayData(
                date=date,
                bars=bars,
                vix=vix,
                prev_close=prev_close,
                vix_bars=vix_bars,
                recent_closes=recent_closes,
            )
        finally:
            await conn.close()

    async def _get_vix(self, conn: asyncpg.Connection, date: dt.date) -> float:
        """VIX close for *date*: daily_bars first, then last spot_prices tick."""
        val = await conn.fetchval(
            "SELECT close FROM daily_bars WHERE underlying = '$VIX' AND date = $1",
            date,
        )
        if val is not None:
            return float(val)

        # Fall back to last $VIX spot tick of that ET day
        day_start_et = dt.datetime(date.year, date.month, date.day, tzinfo=EASTERN)
        day_end_et = day_start_et + dt.timedelta(days=1)
        val = await conn.fetchval(
            """
            SELECT price FROM spot_prices
            WHERE  underlying = '$VIX'
              AND  ts >= $1 AND ts < $2
            ORDER  BY ts DESC LIMIT 1
            """,
            day_start_et.astimezone(dt.timezone.utc),
            day_end_et.astimezone(dt.timezone.utc),
        )
        if val is not None:
            return float(val)

        log.warning("db_loader_no_vix", date=str(date))
        return 18.0  # sensible default

    async def _get_prev_close(self, conn: asyncpg.Connection, date: dt.date) -> float:
        """Last close from daily_bars strictly before *date*."""
        val = await conn.fetchval(
            """
            SELECT close FROM daily_bars
            WHERE  underlying = $1 AND date < $2
            ORDER  BY date DESC LIMIT 1
            """,
            self.underlying, date,
        )
        if val is not None:
            return float(val)

        # Fallback: last tick of the prior ET day from spot_prices
        day_start_et = dt.datetime(date.year, date.month, date.day, tzinfo=EASTERN)
        prior_end_utc = day_start_et.astimezone(dt.timezone.utc)
        prior_start_utc = prior_end_utc - dt.timedelta(days=7)
        val = await conn.fetchval(
            """
            SELECT price FROM spot_prices
            WHERE  underlying = $1
              AND  ts >= $2 AND ts < $3
            ORDER  BY ts DESC LIMIT 1
            """,
            self.underlying, prior_start_utc, prior_end_utc,
        )
        if val is not None:
            return float(val)

        log.warning("db_loader_no_prev_close", date=str(date))
        return 5500.0

    async def _get_recent_closes(
        self, conn: asyncpg.Connection, date: dt.date, n: int = 30
    ) -> list[float]:
        """Up to *n* daily closes before *date*, chronological order."""
        rows = await conn.fetch(
            """
            SELECT close FROM daily_bars
            WHERE  underlying = $1 AND date < $2
            ORDER  BY date DESC LIMIT $3
            """,
            self.underlying, date, n,
        )
        return [float(r["close"]) for r in reversed(rows)]

    async def _available_dates_async(self) -> list[dt.date]:
        conn = await asyncpg.connect(self.dsn)
        try:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ts::date AT TIME ZONE 'America/New_York' AS et_date
                FROM   spot_prices
                WHERE  underlying = $1
                ORDER  BY et_date
                """,
                self.underlying,
            )
            return [r["et_date"] for r in rows]
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # Sync helper
    # ------------------------------------------------------------------

    @staticmethod
    def _run(coro):
        """Run a coroutine synchronously (works even inside an existing loop)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, coro)
                    return future.result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)
