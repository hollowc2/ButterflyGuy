"""CSV-based data loader for historical SPX + VIX 1-minute data.

Reads two CSV files:
  - spx_1min.csv: columns ts, close, high, low, open  (no volume)
  - vix_1min.csv: columns ts, close, high, low, open  (no volume)

Timestamps in the CSV are naive Eastern Time.  The loader converts them to
UTC so the simulation engine's astimezone(EASTERN) calls work correctly.

VIX per day: last bar close of that trading day.
prev_close: last SPX close of the prior trading day.
Volume: set to 0 (not in source data).  The bias filter's VWAP signal falls
back to entry_close when volume is zero — this is handled upstream.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

EASTERN = ZoneInfo("America/New_York")


class CsvDataLoader:
    """Loads SPX + VIX 1-minute CSVs and serves DayData objects.

    Loads both files fully into memory on construction (~2-5 seconds for 5M rows).
    After that, load_day() is O(1).
    """

    def __init__(self, spx_path: str | Path, vix_path: str | Path) -> None:
        spx_path = Path(spx_path)
        vix_path = Path(vix_path)
        log.info("csv_loader_loading", spx=str(spx_path), vix=str(vix_path))

        spx_df = self._read_csv(spx_path)
        vix_df = self._read_csv(vix_path)

        # Build date-keyed lookups
        self._bars_by_date: dict[dt.date, list[MinuteBar]] = self._build_bars(spx_df)
        self._vix_by_date: dict[dt.date, float] = self._build_vix(vix_df)
        self._vix_bars_by_date: dict[dt.date, list[MinuteBar]] = self._build_vix_bars(vix_df)
        self._prev_close: dict[dt.date, float] = self._build_prev_close(spx_df)
        self._recent_closes: dict[dt.date, list[float]] = self._build_recent_closes(spx_df)

        dates = sorted(self._bars_by_date)
        log.info(
            "csv_loader_ready",
            days=len(dates),
            first=str(dates[0]) if dates else None,
            last=str(dates[-1]) if dates else None,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def available_dates(self) -> list[dt.date]:
        return sorted(self._bars_by_date)

    def load_day(self, date: dt.date) -> DayData | None:
        bars = self._bars_by_date.get(date)
        if not bars:
            return None
        vix = self._vix_by_date.get(date, 18.0)
        prev_close = self._prev_close.get(date, 5500.0)
        vix_bars = self._vix_bars_by_date.get(date, [])
        recent_closes = self._recent_closes.get(date, [])
        return DayData(
            date=date,
            bars=bars,
            vix=vix,
            prev_close=prev_close,
            vix_bars=vix_bars,
            recent_closes=recent_closes,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_csv(path: Path) -> pd.DataFrame:
        df = pd.read_csv(path, parse_dates=["ts"])
        # Timestamps are naive ET — localize, then convert to UTC
        df["ts"] = df["ts"].dt.tz_localize(
            "America/New_York", ambiguous="NaT", nonexistent="NaT"
        )
        df = df.dropna(subset=["ts"])
        df["ts"] = df["ts"].dt.tz_convert("UTC")
        # ET date for grouping (bars just before midnight ET still belong to that day)
        df["et_date"] = df["ts"].dt.tz_convert("America/New_York").dt.date
        return df

    @staticmethod
    def _build_bars(df: pd.DataFrame) -> dict[dt.date, list[MinuteBar]]:
        bars_by_date: dict[dt.date, list[MinuteBar]] = {}
        for date, group in df.groupby("et_date"):
            group = group.sort_values("ts")
            bars = [
                MinuteBar(
                    ts=row.ts.to_pydatetime(),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=0,
                )
                for row in group.itertuples()
            ]
            bars_by_date[date] = bars
        return bars_by_date

    @staticmethod
    def _build_recent_closes(df: pd.DataFrame, n: int = 30) -> dict[dt.date, list[float]]:
        """Map each date → list of up to n prior daily closes (chrono order, newest last).

        Uses last bar close per day as the daily close proxy, same as _build_prev_close.
        """
        last = df.sort_values("ts").groupby("et_date")["close"].last()
        dates = list(last.index)
        closes = [float(last.iloc[i]) for i in range(len(dates))]
        result: dict[dt.date, list[float]] = {}
        for i, date in enumerate(dates):
            start_idx = max(0, i - n)
            result[date] = closes[start_idx:i]
        return result

    @staticmethod
    def _build_vix_bars(df: pd.DataFrame) -> dict[dt.date, list[MinuteBar]]:
        result: dict[dt.date, list[MinuteBar]] = {}
        for date, group in df.groupby("et_date"):
            group = group.sort_values("ts")
            bars = [
                MinuteBar(
                    ts=row.ts.to_pydatetime(),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=0,
                )
                for row in group.itertuples()
            ]
            result[date] = bars
        return result

    @staticmethod
    def _build_vix(df: pd.DataFrame) -> dict[dt.date, float]:
        """Last VIX bar close per day as daily VIX proxy."""
        last = df.sort_values("ts").groupby("et_date")["close"].last()
        return {date: float(close) for date, close in last.items()}

    @staticmethod
    def _build_prev_close(df: pd.DataFrame) -> dict[dt.date, float]:
        """Map each date → last close of the previous trading day."""
        last = df.sort_values("ts").groupby("et_date")["close"].last()
        dates = list(last.index)
        prev: dict[dt.date, float] = {}
        for i, date in enumerate(dates):
            if i > 0:
                prev[date] = float(last.iloc[i - 1])
        return prev
