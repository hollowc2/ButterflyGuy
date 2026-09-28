"""Pre-entry session features: scheduled events and the volatility term structure.

Every value here is one a decision could have known:

- `events`: the event calendar's leakage rule (`EventCalendar.events_for`).
- Daily term structure: the **prior-session close** of each index only: its close on
  the previous SPX session (from the dataset's `daily_bars`). The session's own
  open/high/low/close are never used (the daily file carries no time stamps for them).
  Cboe also prints VIX on some exchange holidays; those rows are skipped because they
  are not the previous session. An index with no row on the previous session is missing.
- Intraday term structure: the close of the last bar that was **complete at or before
  the decision** (`ts + bar_seconds <= decision`). A bar still open at the decision is
  never used.

Missing inputs stay missing (None); nothing is imputed.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import pandas as pd

from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.event_calendar import EventCalendar
from butterfly_guy.research.volindex import CBOE_INDICES, DAILY_FILE, INTRADAY_FILE

RATIOS = {"vix1d_vix": ("VIX1D", "VIX"), "vix9d_vix": ("VIX9D", "VIX"),
          "vix_vix3m": ("VIX", "VIX3M")}


class DailyVol:
    """Prior-session closes from `aux/vol_index_daily.parquet`."""

    def __init__(self, table: pd.DataFrame) -> None:
        self.series: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for index, g in table.groupby("index"):
            g = g[g["close"].notna()].sort_values("date")
            dates = pd.to_datetime(g["date"]).dt.date.to_numpy()
            self.series[str(index)] = (dates, g["close"].to_numpy(dtype=float))

    def prior(self, index: str, session: dt.date) -> tuple[float, dt.date] | None:
        """The index's latest close dated before `session`."""
        if index not in self.series:
            return None
        dates, closes = self.series[index]
        i = int(np.searchsorted(dates, session, side="left")) - 1
        return None if i < 0 else (float(closes[i]), dates[i])

    def features(self, session: dt.date, previous_session: dt.date | None = None) -> dict:
        """Closes on `previous_session` (the prior SPX session). Without one, the latest
        VIX row before `session` stands in for it."""
        if previous_session is None:
            ref = self.prior("VIX", session)
            previous_session = None if ref is None else ref[1]
        if previous_session is not None and previous_session >= session:
            raise ValueError("previous_session must be before the session")
        out: dict = {"prior_session": None if previous_session is None
                     else previous_session.isoformat()}
        values = {}
        for index in CBOE_INDICES:
            p = (None if previous_session is None
                 else self.prior(index, previous_session + dt.timedelta(days=1)))
            values[index] = None if p is None or p[1] != previous_session else p[0]
            out[f"{index.lower()}_prior_close"] = values[index]
        for name, (a, b) in RATIOS.items():
            x, y = values.get(a), values.get(b)
            out[f"{name}_prior"] = None if x is None or not y else x / y
        return out


class IntradayVol:
    """Completed minute bars from `aux/vol_index_intraday.parquet`."""

    def __init__(self, table: pd.DataFrame) -> None:
        self.series: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for index, g in table.groupby("index"):
            g = g.sort_values("ts_us")
            done = g["ts_us"].to_numpy() + g["bar_seconds"].to_numpy() * 1_000_000
            self.series[str(index)] = (done, g["close"].to_numpy(dtype=float))

    def at(self, index: str, decision_us: int, max_age_s: float = 300.0) -> float | None:
        """Close of the last bar complete at or before `decision_us`, if recent enough."""
        if index not in self.series:
            return None
        done, closes = self.series[index]
        i = int(np.searchsorted(done, decision_us, side="right")) - 1
        if i < 0 or decision_us - done[i] > max_age_s * 1e6:
            return None
        return float(closes[i])

    def features(self, decision_us: int) -> dict:
        values = {index: self.at(index, decision_us) for index in CBOE_INDICES}
        out = {f"{i.lower()}_intraday": v for i, v in values.items()}
        for name, (a, b) in RATIOS.items():
            x, y = values.get(a), values.get(b)
            out[f"{name}_intraday"] = None if x is None or not y else x / y
        return out


@dataclass
class SessionFeatures:
    """Feature inputs for a dataset, with what a run must record when it uses them."""

    calendar: EventCalendar
    daily: DailyVol | None
    intraday: IntradayVol | None
    inputs: dict
    spx_sessions: np.ndarray | None = None  # sorted dates with an SPX daily bar

    @classmethod
    def load(cls, ds: Dataset, calendar: EventCalendar | None = None) -> SessionFeatures:
        calendar = calendar or EventCalendar()
        daily = DailyVol(ds.aux_table(DAILY_FILE)) if ds.has_aux(DAILY_FILE) else None
        intraday = (IntradayVol(ds.aux_table(INTRADAY_FILE))
                    if ds.has_aux(INTRADAY_FILE) else None)
        inputs = {"event_calendar": calendar.meta(), "aux_hash": ds.aux_hash,
                  "aux_files": {rel: ds.manifest.aux[rel]["sha256"]
                                for rel in sorted(ds.manifest.aux)}}
        bars = ds.daily_bars()
        spx = np.array(sorted(bars.loc[bars["underlying"] == "SPX", "date"]))
        return cls(calendar, daily, intraday, inputs, spx if len(spx) else None)

    def previous_session(self, session: dt.date) -> dt.date | None:
        if self.spx_sessions is None:
            return None
        i = int(np.searchsorted(self.spx_sessions, session, side="left")) - 1
        return None if i < 0 else self.spx_sessions[i]

    def events(self, session: dt.date) -> tuple[str, ...]:
        return self.calendar.event_types(session)

    def term_structure(self, session: dt.date, decision_us: int | None = None) -> dict:
        out = self.daily.features(session, self.previous_session(session)) \
            if self.daily else {}
        if self.intraday is not None and decision_us is not None:
            out.update(self.intraday.features(decision_us))
        return out
