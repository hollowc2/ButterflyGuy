"""Exploratory (post hoc): would a narrower NDX fly keep the edge at a smaller size?

Paper NDX trades the 100-wide fly (~$770 debit). This replays the live NDX entry (gap
direction, first qualifying minute in the 07:00-07:45 PT window, VIX-anchored center,
the reward/risk floor) with one fixed wing width per arm, on ThetaData NDXP 0-DTE
1-minute quotes. Each fixed-width arm keeps the center at 0.5 x the VIX expected move
(the live 100-wide anchor) and caps cost at 8% of width (the live 100-wide cap), so only
the width changes. A `live` arm runs configs/config_ndx.yaml unchanged (80/100/150
cross-width pick) as a sanity check against paper.

There is no NDX index minute data locally, so the intraday spot comes from put-call
parity on the same 0-DTE chain (median forward of the three strikes with the smallest
|call mid - put mid|); `--validate` compares it with the NDX spot Helios recorded from
Schwab. The official open, prior close and settlement come from a daily ^NDX file
(`--daily`, date,open,high,low,close; Yahoo, checked against the bot's recorded
settlement spots).

Reads only offline data; never touches a registry, config or service.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import structlog

from butterfly_guy.core.config import AppConfig, VixWidthBucket, load_config
from butterfly_guy.research.accounting import Costs
from butterfly_guy.research.dataset import SessionChain
from butterfly_guy.research.entry import (
    PROFILES,
    Entry,
    RunContext,
    Series,
    Session,
    gap_direction,
    select_at,
)
from butterfly_guy.research.evaluate import block_bootstrap_indices
from butterfly_guy.research.market import DayMarket, Fly, et_us
from butterfly_guy.research.simulate import Variant, run_variants

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data/thetadata/ndxp_0dte/quote_1m"
CACHE = ROOT / "data/research_cache"
VIX_DATASETS = ("spx_0dte_local_durable_development_20261001",
                "spx_0dte_local_durable_spent_holdout_20261003",
                "spx_0dte_local_durable_validation_20261001")
NDX_CONFIG = ROOT / "configs/config_ndx.yaml"
DEFAULT_OUT = ROOT / "reports/research/ndx-width-20261116"
START = dt.date(2022, 9, 1)  # NDXP expirations became daily in 2022-09
WIDTHS = (30, 40, 50, 60, 80, 100)
ARMS = ("live", *(f"w{w}" for w in WIDTHS))
EXITS = {"E0": "config", "X1": ()}
MODELS = ("midpoint", "marketable", "stressed")
COST_CAP = 0.08  # max debit as a fraction of width, as live 100-wide (8.00)
COMMISSION = 1.15  # per contract, the real SPX fee observed live (2026-10-19)
REGIMES = [(0, 17, "<17"), (17, 24.5, "17-24.5"), (24.5, 999, ">=24.5")]
REPS, BLOCK = 5_000, 5

_VIX: Series | None = None
_CONFIGS: dict[str, AppConfig] = {}


def base_config() -> AppConfig:
    if "live" not in _CONFIGS:
        cfg = load_config(NDX_CONFIG)
        # `entry.selection_span` iterates the buckets; [] is selection-equivalent to None.
        strategy = cfg.strategy.model_copy(update={"vix_width_buckets": []})
        _CONFIGS["live"] = cfg.model_copy(update={"strategy": strategy})
    return _CONFIGS["live"]


def arm_config(arm: str) -> AppConfig:
    if arm not in _CONFIGS:
        w = int(arm[1:])
        base = base_config()
        strategy = base.strategy.model_copy(update={
            "wing_widths": [w],
            # One single-width bucket resolves to sigma 0.5, the live 100-wide anchor.
            "vix_width_buckets": [VixWidthBucket(vix_max=9999.0, widths=[w])],
            "max_cost_per_width": {w: round(COST_CAP * w, 2)},
        })
        _CONFIGS[arm] = base.model_copy(update={"strategy": strategy})
    return _CONFIGS[arm]


def load_vix() -> Series:
    from butterfly_guy.research.dataset import Dataset

    ts, px = [], []
    for name in VIX_DATASETS:
        t, p = Dataset.open(name, CACHE).spot_ticks("$VIX")
        ts.append(t)
        px.append(p)
    df = pd.DataFrame({"ts": np.concatenate(ts), "px": np.concatenate(px)})
    df = df.drop_duplicates("ts").sort_values("ts")
    return Series(df.ts.to_numpy(np.int64), df.px.to_numpy(float))


def parity_spot(cmid: np.ndarray, pmid: np.ndarray, strikes: np.ndarray) -> np.ndarray:
    """Per-snapshot forward: median K + C - P over the 3 strikes nearest C == P."""
    diff = np.abs(cmid - pmid)
    diff = np.where(np.isfinite(diff), diff, np.inf)
    idx = np.argsort(diff, axis=1)[:, :3]
    fwd = strikes[idx] + np.take_along_axis(cmid - pmid, idx, axis=1)
    ok = np.isfinite(np.take_along_axis(diff, idx, axis=1))
    fwd = np.where(ok, fwd, np.nan)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        out = np.nanmedian(fwd, axis=1)
    out[ok.sum(axis=1) < 2] = np.nan
    return out


def file_for(d: dt.date) -> Path:
    return ARCHIVE / str(d.year) / f"{d.isoformat()}.parquet"


def build_chain(d: dt.date) -> SessionChain | None:
    path = file_for(d)
    if not path.is_file():
        return None
    q = pd.read_parquet(path, columns=["expiration", "strike", "right", "timestamp",
                                       "bid", "ask"])
    if q.empty or set(pd.to_datetime(q.expiration).dt.date) != {d}:
        return None
    ts = pd.to_datetime(q.timestamp).dt.tz_convert("UTC")
    q = q.assign(ts_us=ts.astype("datetime64[us, UTC]").astype("int64"),
                 t=q.right.str.upper().str[0])
    q = q[(q.ts_us >= et_us(d, 9, 30)) & (q.ts_us <= et_us(d, 16, 0))]
    absent = (q.bid <= 0) & (q.ask <= 0)
    q.loc[absent, ["bid", "ask"]] = np.nan
    q.loc[q.ask <= 0, "ask"] = np.nan
    times = np.sort(q.ts_us.unique())
    strikes = np.sort(q.strike.unique().astype(float))
    ti = np.searchsorted(times, q.ts_us.to_numpy())
    ki = np.searchsorted(strikes, q.strike.to_numpy(float))
    fields: dict[str, np.ndarray] = {}
    for t in ("C", "P"):
        m = (q.t == t).to_numpy()
        for f in ("bid", "ask"):
            a = np.full((len(times), len(strikes)), np.nan)
            a[ti[m], ki[m]] = q[f].to_numpy(float)[m]
            fields[f"{t}_{f}"] = a
        fields[f"{t}_mark"] = (fields[f"{t}_bid"] + fields[f"{t}_ask"]) / 2
        fields[f"{t}_iv"] = np.full_like(fields[f"{t}_mark"], np.nan)
        fields[f"{t}_delta"] = np.full_like(fields[f"{t}_mark"], np.nan)
    # Parity uses only two-sided quotes.
    two = {t: np.where(fields[f"{t}_bid"] > 0, fields[f"{t}_mark"], np.nan) for t in "CP"}
    spot = parity_spot(two["C"], two["P"], strikes)
    return SessionChain(date=d, ts=times.astype(np.int64), strikes=strikes, spot=spot,
                        fields=fields, underlying="NDX", expiration=d, option_root="NDXP")


def last_at_or_before(chain: SessionChain, ts_us: int) -> float | None:
    ok = (chain.ts <= ts_us) & np.isfinite(chain.spot)
    return float(chain.spot[ok][-1]) if ok.any() else None


class NDXLoader:
    """Duck-typed `SessionLoader` over raw NDXP files with parity spot."""

    def __init__(self, days: list[dt.date], vix: Series, daily: pd.DataFrame) -> None:
        self.days, self.vix = days, vix
        self.daily = {dt.date.fromisoformat(r.date): r for r in daily.itertuples()}
        self.profile = PROFILES["vendor_1m"]
        self.skipped: dict[dt.date, str] = {}
        self._prev: tuple[dt.date, float] | None = None

    def dates(self, start: dt.date | None = None, end: dt.date | None = None):
        return [d for d in self.days if (not start or d >= start) and (not end or d <= end)]

    def load(self, d: dt.date) -> Session | None:
        chain = build_chain(d)
        if chain is None:
            self.skipped[d] = "no_chain"
            return None
        prior = [x for x in self.daily if x < d]
        if d not in self.daily or not prior:
            self.skipped[d] = "no_official_close"
            return None
        today, prev = self.daily[d], float(self.daily[max(prior)].close)
        clock = (chain.ts >= et_us(d, 9, 31)) & np.isfinite(chain.spot)
        if clock.sum() < 300:
            self.skipped[d] = "no_parity_spot"
            return None
        clock_ts, clock_spot = chain.ts[clock], chain.spot[clock]
        if et_us(d, 16, 0) - int(clock_ts[-1]) > 5 * 60_000_000:
            self.skipped[d] = "early_close_or_gap"
            return None
        return Session(date=d, market=DayMarket(chain), clock_ts=clock_ts,
                       clock_spot=clock_spot, open=float(today.open), prev_close=prev,
                       close=float(today.close), vix=self.vix, profile=self.profile)


@dataclass(frozen=True)
class WidthEntry:
    """Live NDX entry (gap direction, first qualifying minute) under one arm's config."""

    arm: str

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        cfg = base_config() if self.arm == "live" else arm_config(self.arm)
        lo, hi = ctx.window(s.date)
        direction = gap_direction(s)
        for ts in s.clock_ts[(s.clock_ts >= lo) & (s.clock_ts <= hi)]:
            ts = int(ts)
            vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
            if vix is None:
                continue
            cand, i, spot = select_at(s, ctx, ts, direction, vix[0], config=cfg)
            if cand is not None:
                return [Entry(Fly.from_candidate(cand), ts, i, cand.cost, direction,
                              vix=vix[0], spot=spot, candidate=cand)]
        return []


def chunk(job: tuple[list[str], str]) -> list[dict]:
    global _VIX
    days, daily_path = job
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    if _VIX is None:
        _VIX = load_vix()
    dates = [dt.date.fromisoformat(d) for d in days]
    loader = NDXLoader(dates, _VIX, pd.read_csv(daily_path))
    ctx = RunContext(base_config(), asset="NDX")
    variants = [Variant(f"{a}:{x}", WidthEntry(a), ex) for a in ARMS for x, ex in EXITS.items()]
    res = run_variants(loader, variants, ctx, start=dates[0], end=dates[-1],
                       costs=Costs(COMMISSION))
    rows = [{"date": d.isoformat(), "skipped": why} for d, why in res.skipped.items()]
    for d in res.dates:
        rows.append({"date": d.isoformat(), "evaluated": True})
    for vname, run in res.runs.items():
        arm, exits = vname.split(":")
        for d, why in run.excluded.items():
            rows.append({"date": d.isoformat(), "arm": arm, "exits": exits, "excluded": why})
        for t in run.trades:
            rows.append({
                "date": t.date.isoformat(), "arm": arm, "exits": exits, "excluded": None,
                "width": t.fly.width, "fly": str(t.fly), "vix": t.vix, "spot": t.spot,
                "cost": t.entry_cost, "exit_reason": t.exit_reason,
                "settlement": t.settlement, "peak": t.peak,
                **{f"pnl_{m}": t.pnl(m) for m in MODELS},
                **{f"status_{m}": t.status(m) for m in MODELS},
            })
    return rows


def all_days(end: dt.date) -> list[dt.date]:
    out = []
    for p in sorted(ARCHIVE.glob("*/*.parquet")):
        d = dt.date.fromisoformat(p.stem)
        if START <= d <= end:
            out.append(d)
    return out


def summarize(df: pd.DataFrame) -> dict:
    for col in ("skipped", "evaluated", "arm", "excluded"):
        if col not in df:
            df[col] = None
    t = df[df.arm.notna()]
    excl = set(t.loc[t.excluded.notna(), "date"])
    t = t[t.excluded.isna() & ~t.date.isin(excl)].copy()
    out: dict = {"evaluated_sessions": int(df.evaluated.fillna(False).sum()),
                 "skipped": df.skipped.value_counts().to_dict(),
                 "excluded_sessions": len(excl)}
    t["regime"] = pd.cut(t.vix, [r[0] for r in REGIMES] + [999], right=False,
                         labels=[r[2] for r in REGIMES])
    t["year"] = t.date.str[:4]
    for ex in EXITS:
        for m in MODELS:
            col = f"pnl_{m}"
            sub = t[(t.exits == ex) & t[col].notna()]
            # Calendar of every evaluated, non-excluded session; no trade = $0.
            days = sorted(set(df.loc[df.evaluated.fillna(False), "date"]) - excl)
            piv = sub.pivot_table(index="date", columns="arm", values=col, aggfunc="sum")
            piv = piv.reindex(index=days, columns=list(ARMS)).fillna(0.0)
            idx = block_bootstrap_indices(len(piv), REPS, BLOCK, seed=20261116)
            key = f"{ex}/{m}"
            out[key] = {}
            for a in ARMS:
                v = piv[a].to_numpy()
                tr = sub[sub.arm == a]
                eq = np.cumsum(v)
                dd = float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min())
                boot = v[idx].mean(axis=1)
                losing = tr[col].to_numpy() <= 0
                streak = run = 0
                for x in losing:
                    run = run + 1 if x else 0
                    streak = max(streak, run)
                out[key][a] = {
                    "trades": int(len(tr)), "total": round(float(v.sum())),
                    "per_session": round(float(v.mean()), 2),
                    "per_session_ci95": [round(float(np.percentile(boot, q)), 2)
                                         for q in (2.5, 97.5)],
                    "p_positive": round(float((boot > 0).mean()), 3),
                    "win_rate": round(float((tr[col] > 0).mean()), 3) if len(tr) else None,
                    "avg_debit": round(float(tr.cost.mean() * 100), 0) if len(tr) else None,
                    "roi_on_debit": round(float(tr[col].sum() / (tr.cost.sum() * 100)), 3)
                    if len(tr) else None,
                    "max_drawdown": round(dd), "longest_losing_streak": int(streak),
                    "by_year": {k: round(float(g[col].sum())) for k, g in tr.groupby("year")},
                    "by_regime": {str(k): [int(len(g)), round(float(g[col].sum()))]
                                  for k, g in tr.groupby("regime", observed=True)},
                }
    live = t[(t.arm == "live") & (t.exits == "E0")]
    out["live_width_choice"] = live.width.value_counts().sort_index().to_dict()
    return out


def validate(helios_csv: Path) -> dict:
    """Parity spot vs Helios-recorded Schwab NDX spot on overlapping minutes."""
    h = pd.read_csv(helios_csv, names=["epoch", "price"])
    h["ts_us"] = h.epoch * 1_000_000
    h["date"] = pd.to_datetime(h.epoch, unit="s", utc=True).dt.tz_convert(
        "America/New_York").dt.date
    errs, closes = [], []
    for d, g in h.groupby("date"):
        chain = build_chain(d)
        if chain is None:
            continue
        g = g.sort_values("ts_us")
        k = np.searchsorted(g.ts_us.to_numpy(), chain.ts, side="right") - 1
        ok = (k >= 0) & np.isfinite(chain.spot)
        ok &= chain.ts - g.ts_us.to_numpy()[np.clip(k, 0, None)] <= 90_000_000
        errs.append(chain.spot[ok] - g.price.to_numpy()[k[ok]])
        hc = g[g.ts_us <= et_us(d, 16, 0)].price
        pc = last_at_or_before(chain, et_us(d, 16, 0))
        if len(hc) and pc is not None:
            closes.append(pc - float(hc.iloc[-1]))
    e, c = np.concatenate(errs), np.array(closes)

    def q(a):
        return {p: round(float(np.percentile(np.abs(a), p)), 2) for p in (50, 90, 99)}

    return {"minutes": len(e), "mean": round(float(e.mean()), 2), "abs_pct": q(e),
            "closes": len(c), "close_mean": round(float(c.mean()), 2), "close_abs_pct": q(c)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--end", type=dt.date.fromisoformat, default=dt.date(2026, 9, 25))
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--daily", type=Path, required=True, help="^NDX daily OHLC CSV")
    ap.add_argument("--validate", type=Path, help="Helios NDX spot CSV (epoch,price)")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.validate:
        v = validate(a.validate)
        (a.out / "parity_validation.json").write_text(json.dumps(v, indent=2))
        print(json.dumps(v, indent=2))
        return
    days = [d.isoformat() for d in all_days(a.end)]
    jobs = [(days[i:i + a.chunk], str(a.daily)) for i in range(0, len(days), a.chunk)]
    rows: list[dict] = []
    with ProcessPoolExecutor(a.workers) as pool:
        for r in pool.map(chunk, jobs):
            rows += r
    df = pd.DataFrame(rows)
    df.to_csv(a.out / "trades.csv", index=False)
    summary = summarize(df)
    (a.out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    sys.exit(main())
