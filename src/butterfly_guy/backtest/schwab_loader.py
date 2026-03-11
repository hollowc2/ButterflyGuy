"""Backtest data loader using Schwab price history API.

Uses SPY 1-minute bars (ETF, fully supported by Schwab) scaled to SPX price
levels using the SPX daily open as a calibration anchor. This gives true
minute-level resolution with accurate SPX absolute pricing.

Calibration:
  ratio = SPX_daily_open / SPY_first_bar_open
  scaled_price = spy_price * ratio

Limitations:
- Schwab returns up to ~48 days of 1-minute history.
- For dates older than ~48 days use YFinanceDataLoader (hourly) or
  BacktestDataLoader (Polygon, paid plan).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

EASTERN = ZoneInfo("America/New_York")
SPY_SYMBOL = "SPY"       # ETF — full 1-min support from Schwab
SPX_SYMBOL = "$SPX.X"   # Index — daily bars only (used for price calibration)
VIX_SYMBOL = "$VIX.X"   # VIX index — daily bars


class SchwabDataLoader:
    """Loads SPY 1-minute bars from Schwab, scaled to SPX price levels.

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

    async def _fetch_spx_daily_open(self, date: dt.date) -> float | None:
        """Fetch the SPX daily open for calibrating SPY → SPX scaling."""
        client = self._get_client()
        start = dt.datetime(date.year, date.month, date.day, 0, 0, tzinfo=EASTERN)
        end = dt.datetime(date.year, date.month, date.day, 23, 59, tzinfo=EASTERN)
        resp = await client.get_price_history_every_day(
            SPX_SYMBOL,
            start_datetime=start,
            end_datetime=end,
            need_extended_hours_data=False,
            need_previous_close=False,
        )
        if resp.status_code != 200:
            log.warning("schwab_spx_daily_failed", date=str(date), status=resp.status_code)
            return None
        candles = resp.json().get("candles", [])
        if candles:
            return float(candles[0]["open"])
        return None

    async def get_spx_minute_bars(self, date: dt.date) -> list[MinuteBar]:
        """Fetch SPY 1-minute bars, scaled to SPX price levels."""
        client = self._get_client()

        start = dt.datetime(date.year, date.month, date.day, 9, 30, tzinfo=EASTERN)
        end = dt.datetime(date.year, date.month, date.day, 16, 1, tzinfo=EASTERN)

        resp = await client.get_price_history_every_minute(
            SPY_SYMBOL,
            start_datetime=start,
            end_datetime=end,
            need_extended_hours_data=False,
            need_previous_close=False,
        )

        if resp.status_code != 200:
            log.warning("schwab_spy_failed", date=str(date), status=resp.status_code)
            return []

        candles = resp.json().get("candles", [])
        if not candles:
            return []

        # Calibrate: scale SPY prices to SPX levels
        spy_open = float(candles[0]["open"])
        spx_open = await self._fetch_spx_daily_open(date)

        if spx_open and spy_open > 0:
            ratio = spx_open / spy_open
            log.info("spy_spx_calibration", date=str(date),
                     spy_open=spy_open, spx_open=spx_open, ratio=round(ratio, 4))
        else:
            # Fallback: use approximate 10:1 ratio
            ratio = 10.0
            log.warning("spy_spx_calibration_fallback", date=str(date), ratio=ratio)

        bars: list[MinuteBar] = []
        for c in candles:
            ts = dt.datetime.fromtimestamp(c["datetime"] / 1000, tz=dt.timezone.utc)
            bars.append(MinuteBar(
                ts=ts,
                open=float(c["open"]) * ratio,
                high=float(c["high"]) * ratio,
                low=float(c["low"]) * ratio,
                close=float(c["close"]) * ratio,
                volume=int(c.get("volume", 0)),
            ))

        log.info("schwab_bars_loaded", date=str(date), count=len(bars),
                 source="SPY*ratio", ratio=round(ratio, 4))
        return bars

    async def get_vix_daily(self, date: dt.date) -> float:
        """Fetch VIX close for a given date."""
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
        candles = resp.json().get("candles", [])
        if candles:
            return float(candles[-1]["close"])
        return 18.0

    async def get_prev_close(self, date: dt.date) -> float:
        """Fetch previous trading day's SPX close."""
        client = self._get_client()
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
        candles = resp.json().get("candles", [])
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
