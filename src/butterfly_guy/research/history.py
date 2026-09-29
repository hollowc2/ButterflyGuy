"""Vendor option history written as a separate research dataset (`spx_0dte_<vendor>`).

**Provider: ThetaData (2026-09-28), Options Value** plus the owner's SPX/VIX minute files
and Cboe's daily files; see `thetadata.py`. The mapping onto the research Parquet schema,
the holdout guard on every request, the manifest history, the cost check and the coverage
report are vendor-independent and tested on a synthetic source. The adapter spec is in
`docs/research/history-vendor-readiness.md`; the data-quality gates that replace validation
steps 1-3 are in `docs/research/vendor-data-quality-plan-2026-09-28.md` (`quality.py`).

**No derived data** (owner, 2026-09-28): every value written is a real observation. A
session without a real SPX level, or without a real VIX print by 10:00 ET, is skipped with
its reason; nothing is computed to stand in for it.

Mapping rules (the readiness doc's spec):

- **Clock.** A 1-minute grid from 09:31 to 16:00 ET, or to the early close (13:00) that the
  event calendar lists for the session. Each grid timestamp is when the quote state
  applied, not a bar start. It becomes `clock.parquet`, read by the `vendor_1m` profile.
- **Quote state.** The vendor's last quote at or before each grid point, carried only
  within the session and never from before its first quote of the day. Each carried value
  records its age (`{C,P}_quote_age_s`). No quote state means NaN in every field.
- **Quotes are not repaired.** A zero bid is kept; a crossed quote stays crossed
  (`market.py` treats it as unexecutable); nothing is interpolated or modelled.
- **Mark** is `(bid + ask) / 2`; a vendor-supplied mark is ignored. IV and delta are the
  vendor's where supplied, else NaN; they are never computed here.
- **Strikes.** Integer strikes within `strike_margin` (400) of the session's spot range.
- **Spot.** The SPX index level at each grid point: its last print at or before it, and
  NaN when that print is older than `INDEX_MAX_AGE_S`. A session with no SPX level at all is
  skipped (`no_spx_index`); one without a VIX print between 09:55 and 10:00 ET is skipped
  (`no_vix`).
- **Official open and close** come from the source's `daily_bars`, as
  `SPX` and `$VIX` rows. A daily-bar lookback never reaches into the sealed holdout; it is
  clipped at the holdout's end instead, and the history entry says so.
- **Every pull** appends a manifest `history` entry with the source description, the
  request parameters of every vendor call and the cost estimate.
- **Quality before earlier data.** A pull reaching before the validation window
  (`holdout.VALIDATION`) needs a passing `vendor-quality` run on that window in the
  dataset's manifest history (`quality.py`).
"""

from __future__ import annotations

import datetime as dt
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from butterfly_guy.research.dataset import (
    AGE_FIELD,
    DEFAULT_DATASET,
    OPTION_TYPES,
    Dataset,
    Manifest,
    SessionChain,
    chain_to_table,
    default_cache_root,
    dense_chain_from_rows,
    session_dir,
    write_table,
)
from butterfly_guy.research.event_calendar import EventCalendar
from butterfly_guy.research.holdout import (
    HOLDOUT,
    VALIDATION,
    Unseal,
    guard,
    in_holdout,
    touches_holdout,
)
from butterfly_guy.research.market import et_us

PROVIDER_NOT_CHOSEN = (
    "Unknown history provider: the implemented sources are listed in history.SOURCES. The "
    "adapter spec and validation plan are in docs/research/history-vendor-readiness.md."
)
DEFAULT_STRIKE_MARGIN = 400.0
REGULAR_CLOSE = dt.time(16, 0)
GRID_START = dt.time(9, 31)
COVERAGE_BAND = 200.0  # strikes within this of spot count toward missing/crossed rates
INDEX_MAX_AGE_S = 120  # an index print older than this at a grid point is no level
VIX_BY = ((9, 55), (10, 0))  # a session needs a real VIX print in this ET window


class HistorySource(Protocol):
    """One vendor's SPX/SPXW history. Timestamps are UTC epoch microseconds."""

    def describe(self) -> dict:
        """Vendor, product, plan and licence. Never a credential."""

    def sessions(self, start: dt.date, end: dt.date) -> list[dt.date]:
        """Sessions with SPXW expiring that day."""

    def quotes(self, d: dt.date, strikes: tuple[float, float]) -> pd.DataFrame:
        """0-DTE SPXW quote-state updates on `d` for strikes in the inclusive range: long
        rows `ts_us, strike, t ("C"/"P"), bid, ask` and optionally `iv, delta`."""

    def index_bars(self, d: dt.date, symbol: str) -> pd.DataFrame:
        """Intraday index level on `d` for `SPX` or `$VIX`: `ts_us, price`."""

    def daily_bars(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        """Official daily bars: `date, underlying ("SPX"/"$VIX"), open, high, low, close`."""

    def cost_estimate(self, start: dt.date, end: dt.date) -> float | None:
        """Estimated dollars for pulling `start..end`; None on a flat-rate plan. Must not
        return any market data."""


def _thetadata(**options: object) -> HistorySource:
    from butterfly_guy.research.thetadata import ThetaDataSource

    return ThetaDataSource(**options)


class RecordedSource:
    """Our own recorded dataset (Helios `spx_0dte`) as a `HistorySource`, so that its
    chains go through exactly the vendor mapping: the last recorded snapshot at or before
    each 1-minute grid point. Calibration for 1-minute vendor data: it measures what the
    1-minute clock alone does to the validation, and gives a same-clock reference."""

    def __init__(self, recorded: Dataset) -> None:
        self.recorded = recorded

    def describe(self) -> dict:
        return {"vendor": "recorded", "product": "recorded chains resampled onto the 1-minute grid",
                "dataset": self.recorded.name, "dataset_hash": self.recorded.hash}

    def sessions(self, start: dt.date, end: dt.date) -> list[dt.date]:
        return [d for d in self.recorded.sessions()["date"] if start <= d <= end]

    def quotes(self, d: dt.date, strikes: tuple[float, float]) -> pd.DataFrame:
        """Every recorded cell, NaN included, so a missing snapshot quote clears the state."""
        c = self.recorded.chain(d)
        k = (c.strikes >= strikes[0]) & (c.strikes <= strikes[1])
        n_ts, n_k = len(c.ts), int(k.sum())
        frames = [pd.DataFrame({
            "ts_us": np.repeat(c.ts, n_k), "strike": np.tile(c.strikes[k], n_ts), "t": t,
            "bid": c.fields[f"{t}_bid"][:, k].ravel(), "ask": c.fields[f"{t}_ask"][:, k].ravel(),
        }) for t in OPTION_TYPES]
        return pd.concat(frames, ignore_index=True)

    def index_bars(self, d: dt.date, symbol: str) -> pd.DataFrame:
        ts, px = self.recorded.spot_ticks(symbol)
        lo = np.searchsorted(ts, et_us(d, 0, 0), side="left")
        hi = np.searchsorted(ts, et_us(d, 23, 59), side="right")
        return pd.DataFrame({"ts_us": ts[lo:hi].astype("int64"),
                             "price": px[lo:hi].astype("float64")})

    def daily_bars(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        b = self.recorded.daily_bars()
        return b[(b["date"] >= start) & (b["date"] <= end)].reset_index(drop=True)

    def cost_estimate(self, start: dt.date, end: dt.date) -> float | None:
        return None


SOURCES: dict[str, Callable[..., HistorySource]] = {"thetadata": _thetadata,
                                                     "recorded": RecordedSource}


def get_source(name: str, **options: object) -> HistorySource:
    if name not in SOURCES:
        raise NotImplementedError(f"{PROVIDER_NOT_CHOSEN} (asked for {name!r})")
    return SOURCES[name](**options)


class CostNotApprovedError(RuntimeError):
    """A usage-billed pull is estimated above what the owner approved."""


class QualityNotPassedError(RuntimeError):
    """A pull before the validation window without a passing `vendor-quality` run."""


class GuardedSource:
    """Wraps a source so that every call is checked against the sealed holdout first and
    its parameters are logged for the manifest."""

    def __init__(self, source: HistorySource, dataset: str, unseal: Unseal | None) -> None:
        self.source, self.dataset, self.unseal = source, dataset, unseal
        self.requests: list[dict] = []

    def _check(self, call: str, start: dt.date, end: dt.date, **params: object) -> None:
        guard(start, end, what=f"vendor {call}", dataset=self.dataset, unseal=self.unseal)
        self.requests.append({"call": call, "start": start.isoformat(), "end": end.isoformat(),
                              **params})

    def describe(self) -> dict:
        return self.source.describe()

    def cost_estimate(self, start: dt.date, end: dt.date) -> float | None:
        self._check("cost_estimate", start, end)
        return self.source.cost_estimate(start, end)

    def sessions(self, start: dt.date, end: dt.date) -> list[dt.date]:
        self._check("sessions", start, end)
        out = self.source.sessions(start, end)
        stray = [d for d in out if not start <= d <= end]
        if stray:
            raise ValueError(f"source returned sessions outside {start}..{end}: {stray[:3]}")
        return out

    def daily_bars(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        self._check("daily_bars", start, end)
        return self.source.daily_bars(start, end)

    def index_bars(self, d: dt.date, symbol: str) -> pd.DataFrame:
        self._check("index_bars", d, d, symbol=symbol)
        return self.source.index_bars(d, symbol)

    def quotes(self, d: dt.date, strikes: tuple[float, float]) -> pd.DataFrame:
        self._check("quotes", d, d, strikes=[strikes[0], strikes[1]])
        return self.source.quotes(d, strikes)


# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------


def session_close(d: dt.date, calendar: EventCalendar) -> dt.time:
    """13:00 on a calendar early close (a withdrawn or unscheduled row does not count),
    else 16:00."""
    for e in calendar.events:
        if (e.event_date == d and e.event_type == "EARLY_CLOSE" and e.kind != "unscheduled"
                and e.withdrawn_on is None and e.release_time_et is not None):
            return e.release_time_et
    return REGULAR_CLOSE


def minute_grid(d: dt.date, close: dt.time = REGULAR_CLOSE) -> np.ndarray:
    """UTC microseconds of every minute from 09:31 to `close` ET inclusive."""
    first = et_us(d, GRID_START.hour, GRID_START.minute)
    last = et_us(d, close.hour, close.minute)
    return np.arange(first, last + 1, 60_000_000, dtype=np.int64)


def strike_range(spot_lo: float, spot_hi: float, margin: float = DEFAULT_STRIKE_MARGIN
                 ) -> tuple[float, float]:
    return float(math.floor(spot_lo - margin)), float(math.ceil(spot_hi + margin))


def _state_index(ts: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """For each grid time, the index of the last update at or before it (-1 if none)."""
    return np.searchsorted(ts, grid, side="right") - 1


def carry_quotes(updates: pd.DataFrame, grid: np.ndarray, d: dt.date,
                 strikes: tuple[float, float]) -> pd.DataFrame:
    """Long rows on `grid`: each (strike, type) carries its last vendor quote state from
    the same session, with its age. Integer strikes in `strikes` (inclusive) only.

    Columns: ts_us, strike, t, bid, ask, mark, iv, delta, quote_age_s. A grid time before
    the contract's first quote of the day has no row (NaN in the dense chain)."""
    cols = ["ts_us", "strike", "t", "bid", "ask", "mark", "iv", "delta", AGE_FIELD]
    if updates.empty:
        return pd.DataFrame(columns=cols)
    u = updates.copy()
    for c in ("iv", "delta"):
        if c not in u:
            u[c] = np.nan
    day_start = et_us(d, 0, 0)
    keep = ((u["ts_us"] >= day_start) & (u["ts_us"] <= grid[-1])
            & (u["strike"] >= strikes[0]) & (u["strike"] <= strikes[1])
            & (u["strike"] == np.round(u["strike"])) & u["t"].isin(OPTION_TYPES))
    u = u[keep].sort_values(["t", "strike", "ts_us"], kind="stable")
    u = u.drop_duplicates(["t", "strike", "ts_us"], keep="last")
    frames = []
    for (t, strike), g in u.groupby(["t", "strike"], sort=True):
        ts = g["ts_us"].to_numpy(dtype=np.int64)
        idx = _state_index(ts, grid)
        ok = idx >= 0
        if not ok.any():
            continue
        src = idx[ok]
        bid = g["bid"].to_numpy(dtype=np.float64)[src]
        ask = g["ask"].to_numpy(dtype=np.float64)[src]
        frames.append(pd.DataFrame({
            "ts_us": grid[ok], "strike": float(strike), "t": t, "bid": bid, "ask": ask,
            "mark": (bid + ask) / 2,
            "iv": g["iv"].to_numpy(dtype=np.float32)[src],
            "delta": g["delta"].to_numpy(dtype=np.float32)[src],
            AGE_FIELD: ((grid[ok] - ts[src]) / 1e6).astype(np.float32),
        }))
    if not frames:
        return pd.DataFrame(columns=cols)
    return pd.concat(frames, ignore_index=True)[cols]


def index_on_grid(bars: pd.DataFrame, grid: np.ndarray, d: dt.date,
                  max_age_s: float | None = None) -> np.ndarray:
    """The index's last print at or before each grid time on the same session; NaN
    before its first print, and where that print is older than `max_age_s`."""
    out = np.full(len(grid), np.nan)
    if bars is None or bars.empty:
        return out
    b = bars[(bars["ts_us"] >= et_us(d, 0, 0)) & (bars["ts_us"] <= grid[-1])
             & np.isfinite(bars["price"])].sort_values("ts_us", kind="stable")
    if b.empty:
        return out
    ts = b["ts_us"].to_numpy(dtype=np.int64)
    idx = _state_index(ts, grid)
    ok = idx >= 0
    if max_age_s is not None:
        ok &= (grid - ts[np.maximum(idx, 0)]) <= max_age_s * 1e6
    out[ok] = b["price"].to_numpy(dtype=np.float64)[idx[ok]]
    return out


def has_print(bars: pd.DataFrame, d: dt.date, window: tuple[tuple[int, int], tuple[int, int]]
              ) -> bool:
    """Whether the index has a finite print inside the ET `window` on `d`."""
    if bars is None or bars.empty:
        return False
    lo, hi = et_us(d, *window[0]), et_us(d, *window[1])
    ts = bars["ts_us"].to_numpy(dtype=np.int64)
    return bool(((ts >= lo) & (ts <= hi) & np.isfinite(bars["price"].to_numpy())).any())


def _age_fields(rows: pd.DataFrame, chain: SessionChain) -> dict[str, np.ndarray]:
    ti = np.searchsorted(chain.ts, rows["ts_us"].to_numpy())
    ki = np.searchsorted(chain.strikes, rows["strike"].to_numpy())
    out = {}
    for t in OPTION_TYPES:
        m = (rows["t"] == t).to_numpy()
        a = np.full((len(chain.ts), len(chain.strikes)), np.nan, dtype=np.float32)
        a[ti[m], ki[m]] = rows[AGE_FIELD].to_numpy(dtype=np.float32)[m]
        out[f"{t}_{AGE_FIELD}"] = a
    return out


@dataclass
class BuiltSession:
    chain: SessionChain
    clock: pd.DataFrame
    row: dict
    ticks: pd.DataFrame


def build_session(source: GuardedSource, d: dt.date, close: dt.time,
                  margin: float = DEFAULT_STRIKE_MARGIN) -> BuiltSession | str:
    """One session's chain, clock and index ticks, or the reason it was skipped."""
    grid = minute_grid(d, close)
    spx = source.index_bars(d, "SPX")
    spot = index_on_grid(spx, grid, d, INDEX_MAX_AGE_S)
    if not np.isfinite(spot).any():
        return "no_spx_index"
    vix = source.index_bars(d, "$VIX")
    if not has_print(vix, d, VIX_BY):
        return "no_vix"
    lo, hi = float(np.nanmin(spot)), float(np.nanmax(spot))
    strikes = strike_range(lo, hi, margin)
    rows = carry_quotes(source.quotes(d, strikes), grid, d, strikes)
    if rows.empty:
        return "no_quotes"
    rows["spot"] = spot[np.searchsorted(grid, rows["ts_us"].to_numpy())]
    chain = dense_chain_from_rows(rows, d)
    chain.fields.update(_age_fields(rows, chain))
    finite = np.isfinite(chain.spot)
    clock = pd.DataFrame({"ts_us": chain.ts[finite], "spot": chain.spot[finite],
                          "spot_min": chain.spot[finite], "spot_max": chain.spot[finite]})
    ticks = pd.concat([
        pd.DataFrame({"ts_us": b["ts_us"].astype("int64"), "underlying": u,
                      "price": b["price"].astype("float64")})
        for u, b in (("SPX", spx), ("$VIX", vix)) if b is not None and not b.empty
    ] or [pd.DataFrame({"ts_us": pd.Series(dtype="int64"),
                        "underlying": pd.Series(dtype=str),
                        "price": pd.Series(dtype="float64")})], ignore_index=True)
    row = {
        "date": d, "snapshots": len(clock), "chain_snapshots": len(chain.ts),
        "strikes": len(chain.strikes), "strike_lo": float(chain.strikes[0]),
        "strike_hi": float(chain.strikes[-1]), "clock_spot_disagreements": 0,
        "grid_points": len(grid), "session_close_et": close.strftime("%H:%M"),
        "spot_source": "index",
    }
    return BuiltSession(chain, clock, row, ticks)


# ---------------------------------------------------------------------------
# Writing a vendor dataset
# ---------------------------------------------------------------------------


@dataclass
class HistoryPlan:
    start: dt.date
    end: dt.date
    dataset: str
    strike_margin: float = DEFAULT_STRIKE_MARGIN
    daily_lookback_days: int = 10  # enough for the prior close across a long weekend
    max_cost: float | None = None  # owner-approved dollars for a usage-billed pull
    unseal: Unseal | None = None
    require_quality: bool = True  # tests of the mapping on synthetic dates switch it off
    log: object = field(default=sys.stderr)


def daily_range(plan: HistoryPlan) -> tuple[tuple[dt.date, dt.date], bool]:
    """The daily-bar request range, and whether its lookback was clipped so that it does
    not reach into the sealed holdout while the pull itself avoids it."""
    lo = plan.start - dt.timedelta(days=plan.daily_lookback_days)
    if (plan.unseal is None and touches_holdout(lo, plan.end)
            and not touches_holdout(plan.start, plan.end)):
        return (max(lo, HOLDOUT[1] + dt.timedelta(days=1)), plan.end), True
    return (lo, plan.end), False


def quality_passed(manifest: Manifest | None) -> bool:
    """Whether the dataset's history holds a passing `vendor-quality` run over the whole
    validation window."""
    if manifest is None:
        return False
    return any(h.get("mode") == "vendor_quality" and h.get("pass") is True
               and h.get("range") == [VALIDATION[0].isoformat(), VALIDATION[1].isoformat()]
               for h in manifest.history)


def _table(df: pd.DataFrame) -> pa.Table:
    """Without pandas metadata, so re-writing unchanged rows gives identical bytes."""
    return pa.Table.from_pandas(df, preserve_index=False).replace_schema_metadata(None)


def _merge(old: pd.DataFrame | None, new: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if old is None or old.empty:
        return new.sort_values(keys, ignore_index=True)
    both = pd.concat([old, new], ignore_index=True)
    return both.drop_duplicates(keys, keep="last").sort_values(keys, ignore_index=True)


def write_history(source: HistorySource, plan: HistoryPlan, cache_root: Path | None = None,
                  calendar: EventCalendar | None = None) -> Manifest:
    """Pull `plan.start..plan.end` from `source` into `plan.dataset`. Existing sessions
    are kept; every pull appends a manifest history entry."""
    if plan.dataset == DEFAULT_DATASET or not plan.dataset.startswith(f"{DEFAULT_DATASET}_"):
        raise ValueError(f"vendor data goes into its own dataset ({DEFAULT_DATASET}_<vendor>), "
                         f"not {plan.dataset!r}")
    guard(plan.start, plan.end, what="vendor history pull", dataset=plan.dataset,
          unseal=plan.unseal)
    root = (cache_root or default_cache_root()) / plan.dataset
    manifest_path = root / "manifest.json"
    if plan.require_quality and plan.start < VALIDATION[0] and not quality_passed(
            Manifest.load(manifest_path) if manifest_path.exists() else None):
        raise QualityNotPassedError(
            f"{plan.dataset}: a pull before {VALIDATION[0]} needs a passing vendor-quality run "
            f"on {VALIDATION[0]}..{VALIDATION[1]} first "
            "(docs/research/vendor-data-quality-plan-2026-09-28.md)")
    calendar = calendar or EventCalendar()
    g = GuardedSource(source, plan.dataset, plan.unseal)
    estimate = g.cost_estimate(plan.start, plan.end)
    if estimate is not None and (plan.max_cost is None or estimate > plan.max_cost):
        raise CostNotApprovedError(
            f"estimated ${estimate:,.2f} for {plan.start}..{plan.end} exceeds the approved "
            f"{'nothing' if plan.max_cost is None else f'${plan.max_cost:,.2f}'}; ask the owner")

    root.mkdir(parents=True, exist_ok=True)
    export_params = {"kind": "vendor_history", "underlying": "SPX",
                     "strike_margin": plan.strike_margin, "clock": "1m grid 09:31-close ET",
                     "mark": "mid", "spot_underlyings": ["SPX", "$VIX"],
                     "spot": "index only, no derived levels", "index_max_age_s": INDEX_MAX_AGE_S,
                     "holdout": [HOLDOUT[0].isoformat(), HOLDOUT[1].isoformat()]}
    if manifest_path.exists():
        manifest = Manifest.load(manifest_path)
        if manifest.export != export_params:
            raise ValueError(f"{plan.dataset} was written with {manifest.export}; use a new "
                             "dataset name")
    else:
        manifest = Manifest(dataset=plan.dataset, underlying="SPX", source=g.describe(),
                            export=export_params)
    prev_files = {p: dict(v) for p, v in manifest.files.items()}
    prev_hash = manifest.dataset_hash if manifest.files else None
    manifest.source = g.describe()

    def read(rel: str) -> pd.DataFrame | None:
        return pd.read_parquet(root / rel) if rel in manifest.files else None

    sessions = read("sessions.parquet")
    if sessions is not None:
        sessions["date"] = pd.to_datetime(sessions["date"]).dt.date
    known = set() if sessions is None else set(sessions["date"])
    (lo, hi), clipped = daily_range(plan)
    official = g.daily_bars(lo, hi)
    official = official.assign(date=pd.to_datetime(official["date"]).dt.date)

    rows, tick_frames, added, skipped = [], [], [], {}
    for d in g.sessions(plan.start, plan.end):
        if d in known:
            continue
        built = build_session(g, d, session_close(d, calendar), plan.strike_margin)
        if isinstance(built, str):
            skipped[d.isoformat()] = built
            print(f"  {d}: skipped ({built})", file=plan.log)
            continue
        rel = session_dir(d)
        manifest.files[f"{rel}/chain.parquet"] = write_table(
            chain_to_table(built.chain), root / rel / "chain.parquet")
        manifest.files[f"{rel}/clock.parquet"] = write_table(
            _table(built.clock), root / rel / "clock.parquet")
        rows.append(built.row)
        tick_frames.append(built.ticks)
        added.append(d)
        print(f"  {d}: {built.row['chain_snapshots']} x {built.row['strikes']} "
              f"({built.row['spot_source']} spot, close {built.row['session_close_et']})",
              file=plan.log)

    if sessions is None and not rows:
        raise RuntimeError("no sessions written")
    new_sessions = pd.DataFrame(rows)
    if not new_sessions.empty:
        sessions = _merge(sessions, new_sessions, ["date"])
        out = sessions.assign(date=pd.to_datetime(sessions["date"]))
        manifest.files["sessions.parquet"] = write_table(
            _table(out), root / "sessions.parquet")
        ticks = _merge(read("spot_ticks.parquet"), pd.concat(tick_frames, ignore_index=True),
                       ["underlying", "ts_us"])
        manifest.files["spot_ticks.parquet"] = write_table(
            _table(ticks), root / "spot_ticks.parquet")
    bars = official.assign(date=pd.to_datetime(official["date"]))[
        ["date", "underlying", "open", "high", "low", "close"]]
    bars = _table(_merge(read("daily_bars.parquet"), bars, ["underlying", "date"]))
    if ("daily_bars.parquet" not in manifest.files
            or not bars.equals(pq.read_table(root / "daily_bars.parquet"))):
        manifest.files["daily_bars.parquet"] = write_table(bars, root / "daily_bars.parquet")

    dates = [pd.Timestamp(x).date() for x in sessions["date"]]
    entry = {
        "at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "mode": "vendor_pull",
        "source": manifest.source,
        "range": [plan.start.isoformat(), plan.end.isoformat()],
        "daily_bars_range": [lo.isoformat(), hi.isoformat()],
        "daily_lookback_clipped_at_holdout": clipped,
        "strike_margin": plan.strike_margin,
        "cost_estimate": estimate,
        "requests": g.requests,
        "previous_dataset_hash": prev_hash,
        "dataset_hash": manifest.dataset_hash,
        "sessions_added": [d.isoformat() for d in added],
        "sessions_skipped": skipped,
        "files_changed": sorted(p for p in set(prev_files) | set(manifest.files)
                                if prev_files.get(p) != manifest.files.get(p)),
        "holdout_sessions": sum(in_holdout(d) for d in dates),
    }
    manifest.history.append(entry)
    manifest.updated_at = entry["at"]
    manifest.save(manifest_path)
    print(f"dataset {plan.dataset}: {len(dates)} sessions, hash {manifest.dataset_hash}; "
          f"added {len(added)}, skipped {len(skipped)}", file=plan.log)
    return manifest


# ---------------------------------------------------------------------------
# Coverage (any dataset: vendor or Helios)
# ---------------------------------------------------------------------------


def session_coverage(ds: Dataset, d: dt.date, band: float = COVERAGE_BAND) -> dict:
    """Per-session coverage: quote presence, missing and crossed rates within `band` of
    spot, spot and VIX availability and the official bars."""
    chain = ds.chain(d)
    row = ds.sessions().set_index("date").loc[d]
    f = chain.fields
    near = np.abs(chain.strikes[None, :] - chain.spot[:, None]) <= band
    out: dict = {"date": d.isoformat(), "timestamps": len(chain.ts),
                 "strikes": len(chain.strikes)}
    for t in OPTION_TYPES:
        bid, ask = f[f"{t}_bid"], f[f"{t}_ask"]
        quoted = np.isfinite(bid) & np.isfinite(ask) & np.isfinite(f[f"{t}_mark"])
        cells = int(near.sum())
        out[f"{t}_missing_rate"] = None if cells == 0 else round(
            float((near & ~quoted).sum() / cells), 6)
        q = int((near & quoted).sum())
        out[f"{t}_crossed_rate"] = None if q == 0 else round(
            float((near & quoted & (bid > ask)).sum() / q), 6)
        out[f"{t}_zero_bid_rate"] = None if q == 0 else round(
            float((near & quoted & (bid == 0)).sum() / q), 6)
    out["spot_finite_rate"] = round(float(np.isfinite(chain.spot).mean()), 6)
    out["spot_source"] = str(row["spot_source"]) if "spot_source" in row.index else "helios"
    vts, _ = ds.spot_ticks("$VIX")
    in_day = (vts >= et_us(d, 9, 30)) & (vts <= et_us(d, 16, 0))
    out["vix_ticks"] = int(in_day.sum())
    out["vix_at_10"] = bool(((vts <= et_us(d, 10, 0)) & (vts >= et_us(d, 9, 55))).any())
    bars = ds.daily_bars()
    for u in ("SPX", "$VIX"):
        b = bars[(bars["underlying"] == u) & (bars["date"] == d)]
        out[f"{u.lstrip('$').lower()}_official_open"] = bool(
            not b.empty and np.isfinite(b["open"].iloc[0]))
        out[f"{u.lstrip('$').lower()}_official_close"] = bool(
            not b.empty and np.isfinite(b["close"].iloc[0]))
    return out


def coverage(ds: Dataset, start: dt.date | None = None, end: dt.date | None = None,
             unseal: Unseal | None = None) -> dict:
    """Coverage by session and a summary. Holdout sessions need a verified unseal."""
    dates = [d for d in ds.sessions()["date"]
             if (start is None or d >= start) and (end is None or d <= end)]
    for d in dates:
        if in_holdout(d):
            guard(d, d, what=f"coverage of {d}", dataset=ds.name, unseal=unseal)
    rows = [session_coverage(ds, d) for d in dates]

    def med(key: str) -> float | None:
        vals = [r[key] for r in rows if r[key] is not None]
        return None if not vals else round(float(np.median(vals)), 6)

    summary = {
        "sessions": len(rows),
        "first": rows[0]["date"] if rows else None,
        "last": rows[-1]["date"] if rows else None,
        "median_strikes": med("strikes"),
        "median_timestamps": med("timestamps"),
        **{f"median_{t}_{k}": med(f"{t}_{k}") for t in OPTION_TYPES
           for k in ("missing_rate", "crossed_rate", "zero_bid_rate")},
        "spot_sources": {s: sum(r["spot_source"] == s for r in rows)
                         for s in sorted({r["spot_source"] for r in rows})},
        "sessions_with_vix_at_10": sum(r["vix_at_10"] for r in rows),
        "sessions_with_spx_official_close": sum(r["spx_official_close"] for r in rows),
        "sessions_with_spx_official_open": sum(r["spx_official_open"] for r in rows),
    }
    return {"dataset": ds.name, "dataset_hash": ds.hash, "band": COVERAGE_BAND,
            "summary": summary, "sessions": rows}
