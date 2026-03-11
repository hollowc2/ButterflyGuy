"""Backtest data loader using Schwab (1-min SPY bars) + yfinance (daily data).

Schwab provides real 1-minute SPY bars (up to ~48 days history).
yfinance provides SPX daily open (for calibration), VIX, and prev close.

Calibration:
  ratio = SPX_daily_open / SPY_first_bar_open   (from yfinance + Schwab)
  scaled_price = spy_price * ratio

This hybrid approach gives true minute-level resolution with accurate
SPX absolute pricing, correct VIX, and correct direction signal.
"""

from __future__ import annotations

import asyncio
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

EASTERN = ZoneInfo("America/New_York")
SPY_SYMBOL = "SPY"    # ETF — full 1-min support from Schwab
SPX_YF = "^GSPC"     # SPX on yfinance — for daily open calibration + prev close
VIX_YF = "^VIX"      # VIX on yfinance — daily close


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

    def _yf_spx_daily_open(self, date: dt.date) -> float | None:
        """Fetch SPX daily open from yfinance for SPY→SPX calibration."""
        end = date + dt.timedelta(days=1)
        hist = yf.Ticker(SPX_YF).history(start=date, end=end, interval="1d")
        if not hist.empty:
            return float(hist["Open"].iloc[0])
        return None

    def _yf_vix(self, date: dt.date) -> float:
        """Fetch VIX daily close from yfinance."""
        end = date + dt.timedelta(days=1)
        hist = yf.Ticker(VIX_YF).history(start=date, end=end, interval="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[0])
        return 18.0

    def _yf_prev_close(self, date: dt.date) -> float:
        """Fetch previous trading day's SPX close from yfinance."""
        start = date - dt.timedelta(days=7)
        hist = yf.Ticker(SPX_YF).history(start=start, end=date, interval="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return 5500.0

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
        spx_open = await asyncio.to_thread(self._yf_spx_daily_open, date)

        if spx_open and spy_open > 0:
            ratio = spx_open / spy_open
            log.info("spy_spx_calibration", date=str(date),
                     spy_open=round(spy_open, 2), spx_open=round(spx_open, 2),
                     ratio=round(ratio, 4))
        else:
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
        """Fetch VIX daily close from yfinance."""
        return await asyncio.to_thread(self._yf_vix, date)

    async def get_prev_close(self, date: dt.date) -> float:
        """Fetch previous trading day's SPX close from yfinance."""
        return await asyncio.to_thread(self._yf_prev_close, date)

    async def load_day(self, date: dt.date) -> DayData | None:
        """Load all data needed for a single backtest day."""
        bars = await self.get_spx_minute_bars(date)
        if not bars:
            return None
        vix = await self.get_vix_daily(date)
        prev_close = await self.get_prev_close(date)
        return DayData(date=date, bars=bars, vix=vix, prev_close=prev_close)
