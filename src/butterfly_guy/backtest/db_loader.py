"""DB-backed data loader for historical SPX + VIX data.

Reads from the live TimescaleDB database:
  - spot_prices          → 1-minute (or collector-interval) bars for SPX and VIX
  - daily_bars           → daily closes for prev_close and VIX daily
  - option_chain_snapshots → real option chain data for butterfly construction

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
from butterfly_guy.data.schemas import OptionQuote

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

    def load_chain_at_time(
        self,
        underlying: str,
        expiration: dt.date,
        at: dt.datetime,
        window_minutes: int = 15,
    ) -> list[OptionQuote]:
        """Return real OptionQuotes from the nearest snapshot to *at*.

        Searches the *window_minutes* window before *at* for the latest
        snapshot timestamp, then returns all rows at that timestamp.
        Returns an empty list if no snapshot exists in the window.

        Args:
            underlying: e.g. "SPX"
            expiration: Option expiration date (0DTE = same as trade date)
            at: Reference datetime (entry bar timestamp, UTC-aware)
            window_minutes: How far back to search for a snapshot.
        """
        return self._run(self._load_chain_async(underlying, expiration, at, window_minutes))

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

    async def _load_chain_async(
        self,
        underlying: str,
        expiration: dt.date,
        at: dt.datetime,
        window_minutes: int,
    ) -> list[OptionQuote]:
        """Query option_chain_snapshots for the nearest snapshot_time <= *at*."""
        conn = await asyncpg.connect(self.dsn)
        try:
            window_start = at - dt.timedelta(minutes=window_minutes)

            # Find the closest snapshot timestamp in the window
            snap_ts = await conn.fetchval(
                """
                SELECT MAX(snapshot_time)
                FROM   option_chain_snapshots
                WHERE  underlying  = $1
                  AND  expiration  = $2
                  AND  snapshot_time >= $3
                  AND  snapshot_time <= $4
                """,
                underlying, expiration, window_start, at,
            )

            if snap_ts is None:
                log.warning(
                    "db_loader_no_chain_snapshot",
                    underlying=underlying,
                    expiration=str(expiration),
                    at=str(at),
                    window_minutes=window_minutes,
                )
                return []

            rows = await conn.fetch(
                """
                SELECT strike, option_type, bid, ask, mark, last, volume,
                       open_interest, iv, delta, gamma, theta, vega,
                       symbol, spot_price, bid_size, ask_size, rho,
                       intrinsic_value, time_value, in_the_money,
                       days_to_expiration, multiplier, theoretical_value
                FROM   option_chain_snapshots
                WHERE  underlying    = $1
                  AND  expiration    = $2
                  AND  snapshot_time = $3
                ORDER  BY strike, option_type
                """,
                underlying, expiration, snap_ts,
            )

            def _f(v, default=0.0):
                return float(v) if v is not None else default

            def _i(v, default=0):
                return int(v) if v is not None else default

            quotes: list[OptionQuote] = []
            for r in rows:
                quotes.append(OptionQuote(
                    symbol=r["symbol"] or "",
                    underlying=underlying,
                    expiration=expiration,
                    strike=float(r["strike"]),
                    option_type=r["option_type"],
                    bid=_f(r["bid"]),
                    ask=_f(r["ask"]),
                    mark=_f(r["mark"]),
                    last=_f(r["last"]),
                    volume=_i(r["volume"]),
                    open_interest=_i(r["open_interest"]),
                    iv=_f(r["iv"]),
                    delta=_f(r["delta"]),
                    gamma=_f(r["gamma"]),
                    theta=_f(r["theta"]),
                    vega=_f(r["vega"]),
                    bid_size=_i(r["bid_size"]),
                    ask_size=_i(r["ask_size"]),
                    rho=_f(r["rho"]),
                    intrinsic_value=_f(r["intrinsic_value"]),
                    time_value=_f(r["time_value"]),
                    in_the_money=bool(r["in_the_money"]),
                    days_to_expiration=_i(r["days_to_expiration"]),
                    multiplier=_f(r["multiplier"], default=100.0),
                    theoretical_value=_f(r["theoretical_value"]),
                ))

            log.info(
                "db_loader_chain_loaded",
                underlying=underlying,
                expiration=str(expiration),
                snapshot_time=str(snap_ts),
                quotes=len(quotes),
            )
            return quotes
        finally:
            await conn.close()

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
