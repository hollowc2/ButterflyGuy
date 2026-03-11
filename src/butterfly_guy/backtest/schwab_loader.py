"""Backtest data loader using Schwab price history API.

Provides real 1-minute SPX bars — same auth as the live trading system.

Limitations:
- Schwab returns up to ~48 days of 1-minute history.
- For dates older than ~48 days use YFinanceDataLoader (hourly) or
  BacktestDataLoader (Polygon, paid plan).

Tickers:
  $SPX.X  — S&P 500 index (1-min bars)
  $VIX.X  — CBOE VIX (daily only; minute bars not available)
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

EASTERN = ZoneInfo("America/New_York")
SPX_SYMBOL = "$SPX.X"
VIX_SYMBOL = "$VIX.X"


class SchwabDataLoader:
    """Loads 1-minute SPX bars from Schwab price history API.

    Reuses the project's existing token file — no extra credentials needed.
    Supports up to ~48 days of 1-minute history.
    """

    def __init__(self, token_path: str | Path, api_key: str, secret_key: str) -> None:
        self.token_path = str(token_path)
        self.api_key = api_key
        self.secret_key = secret_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from schwab.auth import client_from_token_file
            self._client = client_from_token_file(
                token_path=self.token_path,
                api_key=self.api_key,
                app_secret=self.secret_key,
                asyncio=True,
                enforce_enums=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close_async_session()
            self._client = None

    async def get_spx_minute_bars(self, date: dt.date) -> list[MinuteBar]:
        """Fetch 1-minute SPX bars for a single trading day."""
        client = self._get_client()

        # Request the full day: 09:30–16:00 ET
        start = dt.datetime(date.year, date.month, date.day, 9, 30, tzinfo=EASTERN)
        end = dt.datetime(date.year, date.month, date.day, 16, 1, tzinfo=EASTERN)

        resp = await client.get_price_history_every_minute(
            SPX_SYMBOL,
            start_datetime=start,
            end_datetime=end,
            need_extended_hours_data=False,
            need_previous_close=False,
        )

        if resp.status_code != 200:
            log.warning("schwab_price_history_failed", symbol=SPX_SYMBOL,
                        date=str(date), status=resp.status_code)
            return []

        data = resp.json()
        candles = data.get("candles", [])

        bars: list[MinuteBar] = []
        for c in candles:
            ts = dt.datetime.fromtimestamp(c["datetime"] / 1000, tz=dt.timezone.utc)
            bars.append(MinuteBar(
                ts=ts,
                open=float(c["open"]),
                high=float(c["high"]),
                low=float(c["low"]),
                close=float(c["close"]),
                volume=int(c.get("volume", 0)),
            ))

        log.info("schwab_bars_loaded", date=str(date), count=len(bars))
        return bars

    async def get_vix_daily(self, date: dt.date) -> float:
        """Fetch VIX close for a given date (daily bar)."""
        client = self._get_client()

        start = dt.datetime(date.year, date.month, date.day, 0, 0, tzinfo=EASTERN)
        end = dt.datetime(date.year, date.month, date.day, 23, 59, tzinfo=EASTERN)

        resp = await client.get_price_history_every_day(
            VIX_SYMBOL,
            start_datetime=start,
            end_datetime=end,
            need_extended_hours_data=False,
            need_previous_close=False,
        )

        if resp.status_code != 200:
            log.warning("schwab_vix_failed", date=str(date), status=resp.status_code)
            return 18.0

        data = resp.json()
        candles = data.get("candles", [])
        if candles:
            return float(candles[-1]["close"])
        return 18.0

    async def get_prev_close(self, date: dt.date) -> float:
        """Fetch the previous trading day's SPX close."""
        client = self._get_client()

        # Fetch 7 calendar days ending the day before `date`
        end = dt.datetime(date.year, date.month, date.day, 0, 0, tzinfo=EASTERN)
        start = end - dt.timedelta(days=7)

        resp = await client.get_price_history_every_day(
            SPX_SYMBOL,
            start_datetime=start,
            end_datetime=end,
            need_extended_hours_data=False,
            need_previous_close=False,
        )

        if resp.status_code != 200:
            log.warning("schwab_prev_close_failed", date=str(date), status=resp.status_code)
            return 5500.0

        data = resp.json()
        candles = data.get("candles", [])
        if candles:
            return float(candles[-1]["close"])
        return 5500.0

    async def load_day(self, date: dt.date) -> DayData | None:
        """Load all data needed for a single backtest day."""
        bars = await self.get_spx_minute_bars(date)
        if not bars:
            return None
        vix = await self.get_vix_daily(date)
        prev_close = await self.get_prev_close(date)
        return DayData(date=date, bars=bars, vix=vix, prev_close=prev_close)
