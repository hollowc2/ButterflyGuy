"""How closely the live bot's recorded SPX chains agree with ThetaData, minute by minute.

Report only. No metric here has a pass/fail threshold: thresholds need a written plan the
owner approves before any metric is computed, like
`docs/research/vendor-data-quality-plan-2026-09-28.md`. Until then `thresholds` is null.

Inputs are two research datasets: a recorded Helios export (`research export`) and a
ThetaData import (`research import-local`). Rules fixed here:

- **Matching.** Each Helios snapshot is paired with the vendor row of the minute that
  contains its quote time: the recorded quote event time (`quote_event_us` in the
  session's `clock.parquet`, written by exports of sessions recorded with timing metadata)
  when present, else `snapshot_time`. The basis is reported as `timing_basis`. The export
  sets a snapshot's event time to its latest contract quote event, the moment the recorded
  state was current as of. With
  `snapshot_time` the pairing is approximate: the stamp is taken before spot, VIX and the
  chain are fetched, and a snapshot `x` seconds past the minute is compared with the
  vendor's state at the minute mark, `x` seconds earlier. Lateness is that `x`.
- **Quotes.** A cell is quoted when bid and ask are finite and not both zero. Prices are
  compared on integer strikes within `BAND` of the Helios spot of the snapshot.
- **Buckets.** Moneyness |K - S| in (0-25], (25-50], (50-100], (100-200]; time of day by
  the matched minute: `open` before 10:30 ET, `last_hour` within 60 minutes of the
  session close, `midday` between.
- **Spot.** Helios spot against put-call parity on the vendor's mids at the matched
  minute: `K + C - P` at the strike where |C - P| is smallest.
- **Flies.** Every 1/-2/1 call and put fly the live config could select at a matched
  minute: every width in `strategy.wing_widths` and `strategy.vix_width_buckets`, centers
  within `strategy.spot_range` of the Helios spot, all three legs quoted on both sides.
- **Statistics.** Differences are counted exactly in half-cent units, so pooled medians
  and percentiles over a whole range are exact and reruns are byte-identical. A
  percentile is the nearest-rank value (the smallest value with at least that share of
  observations at or below it).

Differences are Helios minus ThetaData throughout.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shlex
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from butterfly_guy.research.dataset import OPTION_TYPES, Dataset, SessionChain, session_dir
from butterfly_guy.research.event_calendar import EventCalendar
from butterfly_guy.research.history import minute_grid, session_close
from butterfly_guy.research.holdout import guard
from butterfly_guy.research.market import et_us
from butterfly_guy.research.quality import BAND, EPS, MIN_US, TOL, _bad_cells, _cells, arbitrage

SCHEMA = "schwab-fidelity-1"
PLAN_TODO = ("TODO: thresholds need an owner-approved written plan before any metric is "
             "computed, like docs/research/vendor-data-quality-plan-2026-09-28.md")
UNIT = 200  # half cents per dollar
LATENESS = ((0, 5), (5, 15), (15, 30), (30, 60))
MONEYNESS = ((0, 25), (25, 50), (50, 100), (100, 200))
TIMES = ("open", "midday", "last_hour")
FLY_LIMITS = (0.05, 0.10)
EVENT_COLUMN = "quote_event_us"  # optional clock.parquet column (recorded quote time)


def _label(lo: float, hi: float) -> str:
    return f"{lo:g}-{hi:g}"


class Hist:
    """Exact counts of values in half-cent units."""

    def __init__(self) -> None:
        self.counts: Counter[int] = Counter()

    def add(self, dollars: np.ndarray) -> None:
        v = np.asarray(dollars, dtype=np.float64)
        v = v[np.isfinite(v)]
        if v.size:
            keys, n = np.unique(np.rint(v * UNIT).astype(np.int64), return_counts=True)
            self.counts.update(dict(zip(keys.tolist(), n.tolist(), strict=True)))

    def merge(self, other: Hist) -> None:
        self.counts.update(other.counts)

    @property
    def n(self) -> int:
        return sum(self.counts.values())

    def quantile(self, q: float) -> float | None:
        n = self.n
        if not n:
            return None
        need, seen = max(1, int(np.ceil(q * n - 1e-9))), 0
        for k in sorted(self.counts):
            seen += self.counts[k]
            if seen >= need:
                return k / UNIT
        raise AssertionError("unreachable")

    def share_above(self, dollars: float) -> float | None:
        n = self.n
        if not n:
            return None
        limit = int(round(dollars * UNIT))
        return sum(c for k, c in self.counts.items() if k > limit) / n

    def stats(self) -> dict:
        return {"n": self.n, "median": self.quantile(0.5), "p95": self.quantile(0.95)}


class Agreement:
    """Price agreement on matched cells for one bucket."""

    def __init__(self) -> None:
        self.abs_mid, self.mid, self.spread = Hist(), Hist(), Hist()
        self.cells = self.agree = 0

    def add(self, d_mid, d_spread, agree) -> None:
        self.abs_mid.add(np.abs(d_mid))
        self.mid.add(d_mid)
        self.spread.add(d_spread)
        self.cells += int(d_mid.size)
        self.agree += int(agree.sum())

    def merge(self, other: Agreement) -> None:
        for name in ("abs_mid", "mid", "spread"):
            getattr(self, name).merge(getattr(other, name))
        self.cells += other.cells
        self.agree += other.agree

    def stats(self) -> dict:
        return {"cells": self.cells, "abs_mid": self.abs_mid.stats(),
                "signed_mid": self.mid.stats(), "spread": self.spread.stats(),
                "agree_within_tol": (self.agree / self.cells) if self.cells else None}


class FlyStats:
    def __init__(self) -> None:
        self.abs_mid, self.mid = Hist(), Hist()

    def add(self, d: np.ndarray) -> None:
        self.abs_mid.add(np.abs(d))
        self.mid.add(d)

    def merge(self, other: FlyStats) -> None:
        self.abs_mid.merge(other.abs_mid)
        self.mid.merge(other.mid)

    def stats(self) -> dict:
        out = {"flies": self.abs_mid.n, "abs_mid": self.abs_mid.stats(),
               "signed_mid": self.mid.stats()}
        for x in FLY_LIMITS:
            out[f"share_abs_over_{x:.2f}"] = self.abs_mid.share_above(x)
        return out


def fly_widths(config) -> list[int]:
    s = config.strategy
    widths = set(s.wing_widths)
    for bucket in s.vix_width_buckets or []:
        widths.update(bucket.widths)
    return sorted(int(w) for w in widths)


def _quoted(bid: np.ndarray, ask: np.ndarray) -> np.ndarray:
    return np.isfinite(bid) & np.isfinite(ask) & ~((bid == 0) & (ask == 0))


def _times(minute: np.ndarray, d: dt.date, close: dt.time) -> np.ndarray:
    """Index into TIMES for each matched minute (epoch us)."""
    close_us = et_us(d, close.hour, close.minute)
    out = np.ones(len(minute), dtype=np.int64)
    out[minute < et_us(d, 10, 30)] = 0
    out[minute > close_us - 60 * MIN_US] = 2
    return out


def _bucket(x: np.ndarray, edges) -> np.ndarray:
    """Index of the (lo, hi] bucket for each value (lo inclusive for the first), -1 outside."""
    out = np.full(x.shape, -1, dtype=np.int64)
    for i, (lo, hi) in enumerate(edges):
        inside = (x <= hi) & ((x > lo) if i else (x >= lo))
        out[inside] = i
    return out


def quote_times(ds: Dataset, d: dt.date, ts: np.ndarray) -> tuple[np.ndarray, str]:
    """Each snapshot's quote time and the timing basis (`quote_event_ts`, `snapshot_time`,
    or `mixed` when only some snapshots carry an event time)."""
    table = pq.read_table(ds._path(f"{session_dir(d)}/clock.parquet"))
    if EVENT_COLUMN in table.column_names:
        clock_ts = table.column("ts_us").to_numpy()
        event = table.column(EVENT_COLUMN).to_numpy(zero_copy_only=False).astype(np.float64)
        i = np.searchsorted(clock_ts, ts)
        ok = (i < len(clock_ts)) & (clock_ts[np.minimum(i, len(clock_ts) - 1)] == ts)
        got = np.where(ok, event[np.minimum(i, len(clock_ts) - 1)], np.nan)
        have = np.isfinite(got)
        if have.any():
            # A session partly recorded with timing falls back per snapshot.
            out = np.where(have, got, ts).astype(np.int64)
            return out, "quote_event_ts" if have.all() else "mixed"
    return ts, "snapshot_time"


def _parity_spot(v: SessionChain, rows: np.ndarray) -> np.ndarray:
    ks = v.strikes
    integer = ks == np.round(ks)
    c = (v.fields["C_bid"][rows] + v.fields["C_ask"][rows]) / 2
    p = (v.fields["P_bid"][rows] + v.fields["P_ask"][rows]) / 2
    ok = (_quoted(v.fields["C_bid"][rows], v.fields["C_ask"][rows])
          & _quoted(v.fields["P_bid"][rows], v.fields["P_ask"][rows]) & integer[None, :])
    gap = np.where(ok, np.abs(c - p), np.inf)
    j = np.argmin(gap, axis=1)
    i = np.arange(len(rows))
    out = ks[j] + c[i, j] - p[i, j]
    return np.where(np.isfinite(gap[i, j]), out, np.nan)


def _quality(chain: SessionChain, rows: np.ndarray) -> dict:
    mask = np.zeros(len(chain.ts), dtype=bool)
    mask[rows] = True
    _, quoted = _cells(chain, mask)
    crossed = checks = violations = 0
    for t in OPTION_TYPES:
        bid, ask = chain.fields[f"{t}_bid"][mask], chain.fields[f"{t}_ask"][mask]
        x = quoted[t] & (bid > ask)
        crossed += int(x.sum())
        c, v, _ = arbitrage(bid, ask, chain.strikes, quoted[t] & ~x, t)
        checks, violations = checks + c, violations + v
    bad = _bad_cells(chain, mask)
    return {"quoted": int(sum(q.sum() for q in quoted.values())), "crossed": crossed,
            "arb_checks": checks, "arb_violations": violations,
            "bad_cells": int(sum(b.sum() for b in bad.values()))}


def _vix(helios: Dataset, d: dt.date, close: dt.time) -> dict:
    ts, _ = helios.spot_ticks("$VIX")
    lo, hi = et_us(d, 9, 30), et_us(d, close.hour, close.minute)
    day = ts[(ts >= lo) & (ts <= hi)]
    if not len(day):
        return {"observations": 0, "max_gap_s": None}
    edges = np.concatenate([[lo], day, [hi]])
    return {"observations": int(len(day)), "max_gap_s": round(float(np.diff(edges).max()) / 1e6, 1)}


class Accumulator:
    """Everything pooled over sessions."""

    def __init__(self, widths: list[int]) -> None:
        self.overall = Agreement()
        self.by_moneyness = {_label(*m): Agreement() for m in MONEYNESS}
        self.by_time = {t: Agreement() for t in TIMES}
        self.by_cell = {f"{_label(*m)}|{t}": Agreement() for m in MONEYNESS for t in TIMES}
        self.by_lateness = {_label(*b): Agreement() for b in LATENESS}
        self.spot, self.spot_abs = Hist(), Hist()
        self.fly = FlyStats()
        self.fly_by_width = {w: FlyStats() for w in widths}
        self.fly_by_lateness = {_label(*b): FlyStats() for b in LATENESS}

    def merge(self, o: Accumulator) -> None:
        self.overall.merge(o.overall)
        for name in ("by_moneyness", "by_time", "by_cell", "by_lateness", "fly_by_width",
                     "fly_by_lateness"):
            mine = getattr(self, name)
            for k, v in getattr(o, name).items():
                mine[k].merge(v)
        self.spot.merge(o.spot)
        self.spot_abs.merge(o.spot_abs)
        self.fly.merge(o.fly)

    def stats(self) -> dict:
        return {
            "prices": {"overall": self.overall.stats(),
                       "by_moneyness": {k: v.stats() for k, v in self.by_moneyness.items()},
                       "by_time_of_day": {k: v.stats() for k, v in self.by_time.items()},
                       "by_moneyness_and_time": {k: v.stats() for k, v in self.by_cell.items()},
                       "by_lateness": {k: v.stats() for k, v in self.by_lateness.items()}},
            "spot": {"signed": self.spot.stats(), "abs": self.spot_abs.stats()},
            "flies": {"overall": self.fly.stats(),
                      "by_width": {str(k): v.stats() for k, v in self.fly_by_width.items()},
                      "by_lateness": {k: v.stats() for k, v in self.fly_by_lateness.items()}},
        }


def compare_session(helios: Dataset, vendor: Dataset, d: dt.date, widths: list[int],
                    spot_range: float, close: dt.time) -> tuple[dict, Accumulator]:
    h, v = helios.chain(d), vendor.chain(d)
    acc = Accumulator(widths)
    t_quote, basis = quote_times(helios, d, h.ts)
    grid = minute_grid(d, close)
    minute = t_quote - (t_quote % MIN_US)
    late = (t_quote - minute) / 1e6
    in_window = (minute >= grid[0]) & (minute <= grid[-1])
    vi = np.searchsorted(v.ts, minute)
    vi_c = np.minimum(vi, len(v.ts) - 1)
    hit = in_window & (vi < len(v.ts)) & (v.ts[vi_c] == minute)
    lb = np.searchsorted([b[1] for b in LATENESS[:-1]], late, side="right")
    out: dict = {"date": d.isoformat(), "timing_basis": basis,
                 "close_et": close.strftime("%H:%M"),
                 "snapshots": int(len(h.ts)), "snapshots_in_window": int(in_window.sum()),
                 "matched": int(hit.sum()),
                 "matched_by_lateness_s": {_label(*b): int((hit & (lb == i)).sum())
                                           for i, b in enumerate(LATENESS)}}
    n_win = out["snapshots_in_window"]
    out["matched_share_by_lateness_s"] = {k: (n / n_win if n_win else None)
                                          for k, n in out["matched_by_lateness_s"].items()}
    have = set(minute[hit].tolist())
    missing = [m for m in grid.tolist() if m not in have]
    longest = run = 0
    prev = None
    for m in missing:
        run = run + 1 if prev is not None and m - prev == MIN_US else 1
        longest, prev = max(longest, run), m
    out["coverage"] = {"scheduled_minutes": int(len(grid)),
                       "minutes_without_snapshot": len(missing),
                       "longest_gap_minutes": longest}
    out["vix"] = _vix(helios, d, close)
    if not hit.any():
        out["coverage"].update(vendor_quoted_cells=0, missing_in_helios=0)
        return out, acc

    hr, vr = np.flatnonzero(hit), vi[hit]
    spot = h.spot[hr]
    tod = _times(minute[hr], d, close)
    lat = lb[hr]
    ks = np.intersect1d(h.strikes, v.strikes)
    ks = ks[ks == np.round(ks)]
    hk, vk = np.searchsorted(h.strikes, ks), np.searchsorted(v.strikes, ks)
    dist = np.abs(ks[None, :] - spot[:, None])
    mon = _bucket(dist, MONEYNESS)

    # Coverage: vendor-quoted strikes within spot_range missing or unquoted on Helios.
    vendor_cells = helios_missing = 0
    near_all = np.abs(v.strikes[None, :] - spot[:, None]) <= spot_range
    in_h = np.isin(v.strikes, h.strikes)
    hpos = np.searchsorted(h.strikes, v.strikes)
    hpos_c = np.minimum(hpos, len(h.strikes) - 1)
    mid = {}
    for t in OPTION_TYPES:
        vb, va = v.fields[f"{t}_bid"][vr], v.fields[f"{t}_ask"][vr]
        vq = _quoted(vb, va) & near_all
        hb_all = np.where(in_h[None, :], h.fields[f"{t}_bid"][hr][:, hpos_c], np.nan)
        ha_all = np.where(in_h[None, :], h.fields[f"{t}_ask"][hr][:, hpos_c], np.nan)
        vendor_cells += int(vq.sum())
        helios_missing += int((vq & ~_quoted(hb_all, ha_all)).sum())

        hb, ha = h.fields[f"{t}_bid"][hr][:, hk], h.fields[f"{t}_ask"][hr][:, hk]
        vb, va = v.fields[f"{t}_bid"][vr][:, vk], v.fields[f"{t}_ask"][vr][:, vk]
        both = _quoted(hb, ha) & _quoted(vb, va) & (mon >= 0)
        hm, vm = (hb + ha) / 2, (vb + va) / 2
        mid[t] = (np.where(_quoted(hb, ha), hm, np.nan), np.where(_quoted(vb, va), vm, np.nan))
        d_mid = hm - vm
        d_spread = (ha - hb) - (va - vb)
        agree = (np.abs(hb - vb) <= TOL + EPS) & (np.abs(ha - va) <= TOL + EPS)
        tod_c = np.broadcast_to(tod[:, None], both.shape)
        lat_c = np.broadcast_to(lat[:, None], both.shape)
        sel = both
        acc.overall.add(d_mid[sel], d_spread[sel], agree[sel])
        for i, m in enumerate(MONEYNESS):
            mm = sel & (mon == i)
            acc.by_moneyness[_label(*m)].add(d_mid[mm], d_spread[mm], agree[mm])
            for j, name in enumerate(TIMES):
                c = mm & (tod_c == j)
                acc.by_cell[f"{_label(*m)}|{name}"].add(d_mid[c], d_spread[c], agree[c])
        for j, name in enumerate(TIMES):
            c = sel & (tod_c == j)
            acc.by_time[name].add(d_mid[c], d_spread[c], agree[c])
        for j, b in enumerate(LATENESS):
            c = sel & (lat_c == j)
            acc.by_lateness[_label(*b)].add(d_mid[c], d_spread[c], agree[c])
    out["coverage"].update(vendor_quoted_cells=vendor_cells, missing_in_helios=helios_missing,
                           missing_share=(helios_missing / vendor_cells) if vendor_cells else None)

    out["quality"] = {"helios": _quality(h, hr), "vendor": _quality(v, np.unique(vr))}

    parity = _parity_spot(v, vr)
    d_spot = spot - parity
    acc.spot.add(d_spot)
    acc.spot_abs.add(np.abs(d_spot))

    pos = {float(k): i for i, k in enumerate(ks)}
    for t in OPTION_TYPES:
        hm, vm = mid[t]
        for w in widths:
            centers = [k for k in ks if float(k) - w in pos and float(k) + w in pos]
            if not centers:
                continue
            c = np.array([pos[float(k)] for k in centers])
            lo = np.array([pos[float(k) - w] for k in centers])
            hi = np.array([pos[float(k) + w] for k in centers])
            near = np.abs(ks[c][None, :] - spot[:, None]) <= spot_range
            fh = hm[:, lo] + hm[:, hi] - 2 * hm[:, c]
            fv = vm[:, lo] + vm[:, hi] - 2 * vm[:, c]
            ok = near & np.isfinite(fh) & np.isfinite(fv)
            dfly = fh - fv
            acc.fly.add(dfly[ok])
            acc.fly_by_width[w].add(dfly[ok])
            lat_c = np.broadcast_to(lat[:, None], ok.shape)
            for j, b in enumerate(LATENESS):
                acc.fly_by_lateness[_label(*b)].add(dfly[ok & (lat_c == j)])
    stats = acc.stats()
    out["prices"] = stats["prices"]["overall"]
    out["prices_by_moneyness"] = stats["prices"]["by_moneyness"]
    out["prices_by_time_of_day"] = stats["prices"]["by_time_of_day"]
    out["spot"] = stats["spot"]
    out["flies"] = stats["flies"]["overall"]
    return out, acc


def run(helios: Dataset, vendor: Dataset, start: dt.date, end: dt.date,
        config) -> tuple[dict, list[dict]]:
    guard(start, end, what="schwab fidelity", dataset=vendor.name)
    cal = EventCalendar()
    widths = fly_widths(config)
    spot_range = float(config.strategy.spot_range)
    h_dates = {d for d in helios.sessions()["date"] if start <= d <= end}
    v_dates = {d for d in vendor.sessions()["date"] if start <= d <= end}
    both = sorted(h_dates & v_dates)
    total = Accumulator(widths)
    rows = []
    for d in both:
        row, acc = compare_session(helios, vendor, d, widths, spot_range, session_close(d, cal))
        rows.append(row)
        total.merge(acc)
    bases = sorted({r["timing_basis"] for r in rows})
    n_win = sum(r["snapshots_in_window"] for r in rows)
    late = {k: sum(r["matched_by_lateness_s"][k] for r in rows) for k in
            (_label(*b) for b in LATENESS)}
    cov = {k: sum(r["coverage"].get(k, 0) for r in rows)
           for k in ("scheduled_minutes", "minutes_without_snapshot", "vendor_quoted_cells",
                     "missing_in_helios")}
    cov["missing_share"] = (cov["missing_in_helios"] / cov["vendor_quoted_cells"]
                            if cov["vendor_quoted_cells"] else None)
    quality = {side: {k: sum(r.get("quality", {}).get(side, {}).get(k, 0) for r in rows)
                      for k in ("quoted", "crossed", "arb_checks", "arb_violations",
                                "bad_cells")} for side in ("helios", "vendor")}
    vix_gaps = [r["vix"]["max_gap_s"] for r in rows if r["vix"]["max_gap_s"] is not None]
    return {
        "schema_version": SCHEMA,
        "thresholds": None, "thresholds_todo": PLAN_TODO,
        "range": [start.isoformat(), end.isoformat()],
        "meta": {"helios": {"dataset": helios.name, "dataset_hash": helios.hash},
                 "vendor": {"dataset": vendor.name, "dataset_hash": vendor.hash},
                 "fly_widths": widths, "spot_range": spot_range, "band": BAND, "tol": TOL},
        "sessions": {"compared": len(both), "helios_only": sorted(str(d) for d in
                                                                  h_dates - v_dates),
                     "vendor_only": sorted(str(d) for d in v_dates - h_dates)},
        "timing_basis": bases[0] if len(bases) == 1 else bases,
        "matching": {"snapshots_in_window": n_win, "matched": sum(late.values()),
                     "matched_by_lateness_s": late,
                     "matched_share_by_lateness_s": {k: (n / n_win if n_win else None)
                                                     for k, n in late.items()}},
        "coverage": cov, "quality": quality,
        "vix": {"median_observations": (float(np.median([r["vix"]["observations"]
                                                         for r in rows])) if rows else None),
                "largest_gap_s": max(vix_gaps) if vix_gaps else None},
        **total.stats(),
    }, rows


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, indent=1, allow_nan=False) + "\n"


def _fmt(x: float | None, digits: int = 3) -> str:
    return "—" if x is None else f"{x:.{digits}f}"


def _pct(x: float | None, digits: int = 1) -> str:
    return "—" if x is None else f"{100 * x:.{digits}f}%"


def markdown(summary: dict, identity: str, command: str) -> str:
    m, p, f, s = summary["matching"], summary["prices"], summary["flies"], summary["spot"]
    o = p["overall"]
    lines = [
        f"# Schwab recording fidelity vs ThetaData ({identity[:12]})", "",
        f"- Helios `{summary['meta']['helios']['dataset']}` @ "
        f"`{summary['meta']['helios']['dataset_hash'][:12]}`; vendor "
        f"`{summary['meta']['vendor']['dataset']}` @ "
        f"`{summary['meta']['vendor']['dataset_hash'][:12]}`.",
        f"- Range {summary['range'][0]} → {summary['range'][1]}; "
        f"{summary['sessions']['compared']} sessions compared.",
        f"- Timing basis: `{summary['timing_basis']}`."
        + (" Matching is approximate: the stamp precedes the fetches, and a snapshot x s past "
           "the minute is compared with the vendor's state x s earlier."
           if summary["timing_basis"] == "snapshot_time" else ""),
        "- Report only: `thresholds` is null (no owner-approved plan yet).", "",
        "## Matching", "",
        f"{m['matched']:,} of {m['snapshots_in_window']:,} in-session snapshots matched a "
        "vendor minute. Share by lateness after the minute mark:", "",
        "| Lateness (s) | Snapshots | Share |", "|---|---:|---:|",
        *[f"| {k} | {n:,} | {_pct(m['matched_share_by_lateness_s'][k])} |"
          for k, n in m["matched_by_lateness_s"].items()], "",
        "## Prices (integer strikes within ±200 of Helios spot, Helios − ThetaData)", "",
        "| Bucket | Cells | |Δmid| median | |Δmid| p95 | Δmid median | Δmid p95 | "
        "Δspread median | Δspread p95 | Within $0.05 bid & ask |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def row(name: str, a: dict) -> str:
        return (f"| {name} | {a['cells']:,} | {_fmt(a['abs_mid']['median'])} | "
                f"{_fmt(a['abs_mid']['p95'])} | {_fmt(a['signed_mid']['median'])} | "
                f"{_fmt(a['signed_mid']['p95'])} | {_fmt(a['spread']['median'])} | "
                f"{_fmt(a['spread']['p95'])} | {_pct(a['agree_within_tol'])} |")

    lines.append(row("all", o))
    lines += [row(f"|K−S| {k}", a) for k, a in p["by_moneyness"].items()]
    lines += [row(k, a) for k, a in p["by_time_of_day"].items()]
    lines += [row(f"late {k} s", a) for k, a in p["by_lateness"].items()]
    c, q = summary["coverage"], summary["quality"]
    lines += [
        "", "## Coverage", "",
        f"- Scheduled minutes without a Helios snapshot: {c['minutes_without_snapshot']:,} of "
        f"{c['scheduled_minutes']:,}.",
        f"- Vendor-quoted cells within ±{summary['meta']['spot_range']:g} of spot at matched "
        f"minutes missing or unquoted on Helios: {c['missing_in_helios']:,} of "
        f"{c['vendor_quoted_cells']:,} ({_pct(c['missing_share'], 2)}).", "",
        "## Quality on matched rows (Q2/Q3 rules)", "",
        "| Side | Quoted cells | Crossed | Arb violations / checks | Bad cells |",
        "|---|---:|---:|---:|---:|",
        *[f"| {side} | {x['quoted']:,} | {x['crossed']:,} | {x['arb_violations']:,} / "
          f"{x['arb_checks']:,} | {x['bad_cells']:,} |" for side, x in q.items()], "",
        "## Spot", "",
        f"Helios SPX spot − ThetaData parity spot: |Δ| median {_fmt(s['abs']['median'], 2)}, "
        f"p95 {_fmt(s['abs']['p95'], 2)}; signed median {_fmt(s['signed']['median'], 2)} "
        f"({s['abs']['n']:,} minutes). VIX: median {summary['vix']['median_observations']} "
        f"observations per session, largest gap {summary['vix']['largest_gap_s']} s.", "",
        "## Butterflies the live config could select", "",
        f"Widths {summary['meta']['fly_widths']}, calls and puts, centers within "
        f"±{summary['meta']['spot_range']:g} of spot.", "",
        "| Set | Flies | |Δ| median | |Δ| p95 | Δ median | Share |Δ| > $0.05 | "
        "Share |Δ| > $0.10 |", "|---|---:|---:|---:|---:|---:|---:|",
    ]

    def fly(name: str, a: dict) -> str:
        return (f"| {name} | {a['flies']:,} | {_fmt(a['abs_mid']['median'])} | "
                f"{_fmt(a['abs_mid']['p95'])} | {_fmt(a['signed_mid']['median'])} | "
                f"{_pct(a['share_abs_over_0.05'])} | {_pct(a['share_abs_over_0.10'])} |")

    lines.append(fly("all", f["overall"]))
    lines += [fly(f"width {k}", a) for k, a in f["by_width"].items()]
    lines += [fly(f"late {k} s", a) for k, a in f["by_lateness"].items()]
    lines += ["", "Reproduce:", "", "```bash", command, "```", ""]
    return "\n".join(lines)


def publish(out: Path, summary: dict, rows: list[dict], inputs: dict,
            run_date: dt.date) -> Path:
    """Content-addressed artifact; an existing identical one is verified, never rewritten."""
    payloads = {"summary.json": _canonical(summary),
                "sessions.jsonl": "".join(json.dumps(r, sort_keys=True, allow_nan=False) + "\n"
                                          for r in rows)}
    hashes = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in payloads.items()}
    identity = hashlib.sha256(_canonical({"outputs": hashes, "inputs": inputs})
                              .encode()).hexdigest()
    folder = out / run_date.isoformat() / summary["meta"]["vendor"]["dataset"] / identity[:12]
    if folder.exists():
        verify_artifact(folder)
        return folder
    repo = Path(__file__).resolve().parents[3]
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo,
                                          text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "src",
                                              "configs"], cwd=repo, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        git_sha, dirty = "", True
    command = shlex.join(["uv", "run", "python", "-m", "butterfly_guy.research",
                          *sys.argv[1:]])
    payloads["report.md"] = markdown(summary, identity, command)
    hashes["report.md"] = hashlib.sha256(payloads["report.md"].encode()).hexdigest()
    provenance = {"schema_version": SCHEMA, "result_sha256": identity,
                  "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                  "git_sha": git_sha, "git_dirty": dirty, "command": command,
                  "input_sha256": inputs, "output_sha256": hashes}
    folder.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".fidelity-", dir=folder.parent))
    for name, payload in payloads.items():
        (stage / name).write_text(payload)
    (stage / "provenance.json").write_text(_canonical(provenance))
    stage.rename(folder)
    verify_artifact(folder)
    return folder


def verify_artifact(folder: Path) -> None:
    prov = json.loads((folder / "provenance.json").read_text())
    for name, expected in prov["output_sha256"].items():
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"artifact sha256 mismatch: {folder / name}")
    outputs = {k: prov["output_sha256"][k] for k in ("summary.json", "sessions.jsonl")}
    identity = hashlib.sha256(_canonical({"outputs": outputs, "inputs": prov["input_sha256"]})
                              .encode()).hexdigest()
    if identity != prov["result_sha256"]:
        raise ValueError("artifact result identity mismatch")


def one_line(summary: dict) -> str:
    m, f, o = summary["matching"], summary["flies"]["overall"], summary["prices"]["overall"]
    n = m["snapshots_in_window"]
    return (f"Schwab fidelity {summary['range'][0]}→{summary['range'][1]} "
            f"({summary['timing_basis']}): matched {m['matched']}/{n}; "
            f"|Δmid| med {_fmt(o['abs_mid']['median'])} p95 {_fmt(o['abs_mid']['p95'])}; "
            f"fly |Δ| med {_fmt(f['abs_mid']['median'])} p95 {_fmt(f['abs_mid']['p95'])}, "
            f">$0.10 {_pct(f['share_abs_over_0.10'])}; missing minutes "
            f"{summary['coverage']['minutes_without_snapshot']}")
