"""Backtest data loader using yfinance (free, no API key required).

Uses hourly bars for SPX (^GSPC) and daily bars for VIX (^VIX).
Hourly resolution is sufficient for 10:00-10:30 ET entry and
regime-based drawdown exits throughout the day.

Switch back to BacktestDataLoader (Polygon) by setting USE_YFINANCE=False
in run_backtest.py if you have a paid Polygon account.
"""

from __future__ import annotations

import asyncio
import datetime as dt

import yfinance as yf

from butterfly_guy.backtest.data_loader import DayData, MinuteBar

SPX_TICKER = "^GSPC"
VIX_TICKER = "^VIX"


class YFinanceDataLoader:
    """Loads historical SPX + VIX data via yfinance. No API key required."""

    async def close(self) -> None:
        pass  # No persistent connection

    # --- sync internals (run via asyncio.to_thread) ---

    def _fetch_hourly_bars(self, date: dt.date) -> list[MinuteBar]:
        start = date
        end = date + dt.timedelta(days=1)
        hist = yf.Ticker(SPX_TICKER).history(start=start, end=end, interval="1h")
        bars: list[MinuteBar] = []
        for ts, row in hist.iterrows():
            ts_dt = ts.to_pydatetime()
            if ts_dt.tzinfo is None:
                ts_dt = ts_dt.replace(tzinfo=dt.timezone.utc)
            else:
                ts_dt = ts_dt.astimezone(dt.timezone.utc)
            bars.append(
                MinuteBar(
                    ts=ts_dt,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row.get("Volume", 0)),
                )
            )
        return bars

    def _fetch_vix(self, date: dt.date) -> float:
        start = date
        end = date + dt.timedelta(days=1)
        hist = yf.Ticker(VIX_TICKER).history(start=start, end=end, interval="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[0])
        return 18.0  # fallback

    def _fetch_prev_close(self, date: dt.date) -> float:
        start = date - dt.timedelta(days=7)
        end = date
        hist = yf.Ticker(SPX_TICKER).history(start=start, end=end, interval="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return 5500.0  # fallback

    # --- async public interface (matches BacktestDataLoader) ---

    async def get_spx_minute_bars(self, date: dt.date) -> list[MinuteBar]:
        return await asyncio.to_thread(self._fetch_hourly_bars, date)

    async def get_vix_daily(self, date: dt.date) -> float:
        return await asyncio.to_thread(self._fetch_vix, date)

    async def get_prev_close(self, date: dt.date) -> float:
        return await asyncio.to_thread(self._fetch_prev_close, date)

    async def load_day(self, date: dt.date) -> DayData | None:
        bars = await self.get_spx_minute_bars(date)
        if not bars:
            return None
        vix = await self.get_vix_daily(date)
        prev_close = await self.get_prev_close(date)
        return DayData(date=date, bars=bars, vix=vix, prev_close=prev_close)
