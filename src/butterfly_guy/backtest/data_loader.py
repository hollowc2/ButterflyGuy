"""Backtest data loader — fetches SPX 1-min bars and VIX from Polygon.io."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import httpx

POLYGON_BASE = "https://api.polygon.io"


@dataclass
class MinuteBar:
    ts: dt.datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class DayData:
    date: dt.date
    bars: list[MinuteBar]
    vix: float
    prev_close: float


class BacktestDataLoader:
    """Loads historical data from Polygon.io for backtesting."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=30)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_spx_minute_bars(
        self, date: dt.date
    ) -> list[MinuteBar]:
        """Fetch SPX 1-minute bars for a given date from Polygon."""
        url = (
            f"{POLYGON_BASE}/v2/aggs/ticker/I:SPX/range/1/minute"
            f"/{date}/{date}"
            f"?adjusted=true&sort=asc&limit=1000&apiKey={self.api_key}"
        )
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()

        bars: list[MinuteBar] = []
        for result in data.get("results", []):
            ts = dt.datetime.fromtimestamp(result["t"] / 1000, tz=dt.timezone.utc)
            bars.append(
                MinuteBar(
                    ts=ts,
                    open=result["o"],
                    high=result["h"],
                    low=result["l"],
                    close=result["c"],
                    volume=result.get("v", 0),
                )
            )
        return bars

    async def get_vix_daily(self, date: dt.date) -> float:
        """Fetch VIX close for a given date from Polygon."""
        url = (
            f"{POLYGON_BASE}/v2/aggs/ticker/I:VIX/range/1/day"
            f"/{date}/{date}"
            f"?adjusted=true&sort=asc&limit=1&apiKey={self.api_key}"
        )
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            return float(results[0]["c"])
        return 18.0  # default fallback

    async def get_prev_close(self, date: dt.date) -> float:
        """Fetch the actual previous trading day's SPX close for a given date."""
        # Look back up to 7 calendar days to find the last trading day
        look_back_start = date - dt.timedelta(days=7)
        look_back_end = date - dt.timedelta(days=1)
        url = (
            f"{POLYGON_BASE}/v2/aggs/ticker/I:SPX/range/1/day"
            f"/{look_back_start}/{look_back_end}"
            f"?adjusted=true&sort=asc&limit=10&apiKey={self.api_key}"
        )
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            return float(results[-1]["c"])  # most recent day before `date`
        return 5500.0  # fallback

    async def load_day(self, date: dt.date) -> DayData | None:
        """Load all data needed for a single backtest day."""
        bars = await self.get_spx_minute_bars(date)
        if not bars:
            return None
        vix = await self.get_vix_daily(date)
        prev_close = await self.get_prev_close(date)
        return DayData(date=date, bars=bars, vix=vix, prev_close=prev_close)
