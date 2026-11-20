"""Exploratory counter-impulse entry study (post hoc, not registered).

Idea: keep the gap direction, but only enter after spot has moved against that direction
inside the entry window (a pullback on a gap-up CALL day, a bounce on a gap-down PUT
day). The pullback is measured from the running favorable extreme, in units of the
VIX-implied daily move (`vix_expected_move`) at the window start.

Entry modes:
- `reselect`: at the trigger, run the live selector on the new spot (fly re-centered).
- `same_fly`: buy the strikes E0 selected, at the trigger snapshot's mark (cheaper fly).

Anchors: `window` tracks the extreme from the window start; `open` from 09:30 ET (a
pullback that began before the window counts once the window opens). No trigger by the
window end means no trade.

Reads only the canonical offline datasets; never touches a registry, config or service.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import structlog

from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.entry import (
    PROFILES,
    BaselineEntry,
    Entry,
    RunContext,
    Session,
    SessionLoader,
    baseline_window,
    cached_entries,
    load_spx_config,
    select_at,
)
from butterfly_guy.research.evaluate import EvalParams, paired_bootstrap, trade_metrics
from butterfly_guy.research.market import Fly, et_us
from butterfly_guy.research.simulate import Variant, run_variants
from butterfly_guy.strategy.butterfly_builder import vix_expected_move

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/research_cache"
DEFAULT_OUT = ROOT / "reports/research/spx-counter-impulse-20261028"
NAMES = (
    "spx_0dte_local_durable_development_20261001",
    "spx_0dte_local_durable_spent_holdout_20261003",
    "spx_0dte_local_durable_validation_20261001",
)
MODELS = ("midpoint", "stressed", "stressed_delayed")
BASE = BaselineEntry()


def trigger_ts(s: Session, ctx: RunContext, lo: int, hi: int, frac: float,
               anchor: str) -> int | None:
    """First clock time in [lo, hi] where spot has retraced `frac` x the VIX daily move
    from its running favorable extreme (since `lo`, or since 09:30 ET)."""
    vix = s.vix.at_or_before(lo, max_age_s=ctx.max_vix_age_s)
    k = int(np.searchsorted(s.clock_ts, lo, side="left"))
    if vix is None or k >= len(s.clock_ts):
        return None
    em = vix_expected_move(vix[0], float(s.clock_spot[k]))
    start = et_us(s.date, 9, 30) if anchor == "open" else lo
    m = (s.clock_ts >= start) & (s.clock_ts <= hi)
    ts, px = s.clock_ts[m], s.clock_spot[m]
    sign = 1.0 if BASE._direction(s, lo) == "CALL" else -1.0
    retrace = np.maximum.accumulate(sign * px) - sign * px
    hit = np.flatnonzero((ts >= lo) & (retrace >= frac * em))
    return int(ts[hit[0]]) if len(hit) else None


@dataclass(frozen=True)
class CounterImpulseEntry:
    frac: float
    anchor: Literal["window", "open"] = "window"
    mode: Literal["reselect", "same_fly"] = "reselect"
    window_minutes: int | None = None  # None: the configured window
    fallback: bool = False  # no trigger: enter at the last clock time in the window
    fixed_delay: int | None = None  # control: trigger `fixed_delay` minutes after lo

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        lo, hi = baseline_window(BaselineEntry(window_minutes=self.window_minutes), s, ctx)
        trig = (trigger_ts(s, ctx, lo, hi, self.frac, self.anchor)
                if self.fixed_delay is None else lo + self.fixed_delay * 60_000_000)
        if trig is None and self.fallback:
            in_window = s.clock_ts[(s.clock_ts >= lo) & (s.clock_ts <= hi)]
            trig = int(in_window[-1]) if len(in_window) else None
        if trig is None:
            return []
        direction = BASE._direction(s, lo)
        tag = f"trigger={trig}"
        if self.mode == "reselect":
            for ts in s.clock_ts[(s.clock_ts >= trig) & (s.clock_ts <= hi)]:
                ts = int(ts)
                vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
                if vix is None:
                    continue
                cand, i, spot = select_at(s, ctx, ts, direction, vix[0])
                if cand is not None:
                    return [Entry(Fly.from_candidate(cand), ts, i, cand.cost, direction,
                                  vix=vix[0], spot=spot, candidate=cand, tag=tag)]
            return []
        base = cached_entries(s, ctx, BASE)
        if not base:
            return []
        e0 = base[0]
        path = s.market.fly_path(e0.fly)
        if path is None:
            return []
        for ts in s.clock_ts[(s.clock_ts >= max(trig, e0.ts_us)) & (s.clock_ts <= hi)]:
            ts = int(ts)
            i = s.market.at_or_before(ts)
            if i >= 0 and path.observed[i] and np.isfinite(path.mark[i]) and path.mark[i] > 0:
                k = s.clock_index(ts)
                return [Entry(e0.fly, ts, i, float(path.mark[i]), direction, vix=e0.vix,
                              spot=float(s.clock_spot[k]), tag=tag)]
        return []


FRACS = (0.10, 0.20, 0.30)


def variants() -> list[Variant]:
    out = [Variant("E0", BASE, "config", "baseline"), Variant("X1", BASE, (), "E0 held")]
    for frac in FRACS:
        for anchor in ("window", "open"):
            for mode in ("reselect", "same_fly"):
                for wm in (None, 90, 120):
                    rule = CounterImpulseEntry(frac, anchor, mode, wm)
                    name = f"CI_{int(frac * 100):02d}_{anchor}_{mode}_{wm or 45}"
                    out.append(Variant(name + "_trail", rule, "config", ""))
                    out.append(Variant(name + "_held", rule, (), ""))
                    if anchor == "window":
                        rule = CounterImpulseEntry(frac, anchor, mode, wm, fallback=True)
                        out.append(Variant(name + "_fb_trail", rule, "config", ""))
                        out.append(Variant(name + "_fb_held", rule, (), ""))
    for delay in (15, 30, 45, 60, 90, 120):
        for mode in ("reselect", "same_fly"):
            rule = CounterImpulseEntry(0.0, "window", mode, 120, fixed_delay=delay)
            out.append(Variant(f"DELAY_{delay}_{mode}_trail", rule, "config", ""))
            out.append(Variant(f"DELAY_{delay}_{mode}_held", rule, (), ""))
    return out


def run_chunk(args: tuple[str, list[str]]) -> list[dict]:
    name, days = args
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    ds = Dataset.open(name, CACHE)
    loader = SessionLoader(ds, PROFILES["vendor_1m"])
    ctx = RunContext(load_spx_config())
    dates = [dt.date.fromisoformat(d) for d in days]
    res = run_variants(loader, variants(), ctx, start=dates[0], end=dates[-1])
    rows = []
    for d in res.dates:
        rows.append({"dataset": name, "date": d.isoformat(), "variant": None})
    for vname, run in res.runs.items():
        for d, why in run.excluded.items():
            rows.append({"dataset": name, "date": d.isoformat(), "variant": vname,
                         "excluded": why})
        for t in run.trades:
            rows.append({
                "dataset": name, "date": t.date.isoformat(), "variant": vname,
                "direction": t.fly.direction, "lower": t.fly.lower, "center": t.fly.center,
                "upper": t.fly.upper, "entry_ts_us": t.entry_ts_us, "cost": t.entry_cost,
                "vix": t.vix, "spot": t.spot, "exit_reason": t.exit_reason,
                "settlement": t.settlement,
                **{f"pnl_{m}": t.pnl(m) for m in MODELS},
            })
    return rows


def replay(out: Path, workers: int) -> pd.DataFrame:
    jobs = []
    for name in NAMES:
        ds = Dataset.open(name, CACHE)
        days = [d.isoformat() for d in SessionLoader(ds, PROFILES["vendor_1m"]).dates()]
        jobs += [(name, days[i:i + 30]) for i in range(0, len(days), 30)]
    rows: list[dict] = []
    with ProcessPoolExecutor(workers) as pool:
        for i, chunk in enumerate(pool.map(run_chunk, jobs)):
            rows += chunk
            print(f"chunk {i + 1}/{len(jobs)}", flush=True)
    frame = pd.DataFrame(rows)
    frame.to_parquet(out / "trades.parquet")
    return frame


def analyze(frame: pd.DataFrame, out: Path) -> dict:
    sessions = frame[frame.variant.isna()][["dataset", "date"]].drop_duplicates()
    sessions = sessions.sort_values("date").reset_index(drop=True)
    if "excluded" not in frame:
        frame = frame.assign(excluded=None)
    excluded = set(frame.loc[frame.excluded.notna(), "date"])
    sessions = sessions[~sessions.date.isin(excluded)].reset_index(drop=True)
    trades = frame[frame.variant.notna() & frame.excluded.isna()]
    names = [v.name for v in variants()]
    params = EvalParams()
    periods = {"all": sessions.date.notna()} | {
        n.split("_")[4]: sessions.dataset == n for n in NAMES}

    def vec(v: str, model: str) -> pd.Series:
        t = trades[trades.variant == v].groupby("date")[f"pnl_{model}"].sum()
        return sessions.date.map(t).fillna(0.0)

    summary = {"sessions": len(sessions), "excluded_sessions": sorted(excluded),
               "variants": {}}
    for v in names:
        base = "X1" if v.endswith("_held") or v == "X1" else "E0"
        rec = {"baseline": base}
        tv = trades[trades.variant == v]
        traded_dates = set(tv.date)
        for model in MODELS:
            a, b = vec(v, model), vec(base, model)
            for p, mask in periods.items():
                aa, bb = a[mask].to_numpy(), b[mask].to_numpy()
                on = (sessions.date.isin(traded_dates) & mask).to_numpy()[mask.to_numpy()]
                rec[f"{model}/{p}"] = {
                    "total": round(float(aa.sum()), 0),
                    "base_total": round(float(bb.sum()), 0),
                    "diff": round(float(aa.sum() - bb.sum()), 0),
                    "trades": int(on.sum()), "sessions": int(len(aa)),
                    # Same-day comparison: only sessions the variant traded.
                    "on_days_diff": round(float(aa[on].sum() - bb[on].sum()), 0),
                    "on_days_base": round(float(bb[on].sum()), 0),
                    "metrics": trade_metrics(aa[on]) if on.any() else {"n": 0},
                    "bootstrap": paired_bootstrap(aa, bb, params) if model == "stressed"
                    else None,
                }
        e0 = trades[trades.variant == ("E0" if base == "E0" else "X1")].set_index("date")
        same = tv[tv.date.isin(e0.index)].set_index("date")
        if len(same):
            rec["vs_e0_entry"] = {
                "mean_cost": round(float(same.cost.mean()), 3),
                "mean_e0_cost": round(float(e0.loc[same.index, "cost"].mean()), 3),
                "mean_delay_min": round(float(
                    (same.entry_ts_us - e0.loc[same.index, "entry_ts_us"]).mean() / 6e7), 1),
                "mean_center_shift_signed": round(float(np.where(
                    same.direction == "CALL", 1, -1) @ (
                    same.center - e0.loc[same.index, "center"]) / len(same)), 1),
            }
        summary["variants"][v] = rec
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    return summary


def table(summary: dict, model: str = "stressed") -> str:
    lines = [f"model={model}  sessions={summary['sessions']}",
             f"{'variant':38} {'n':>5} {'total':>9} {'base':>9} {'diff':>8} "
             f"{'p>':>5} {'onday d':>8} {'dev':>8} {'hold':>8} {'val':>8} {'cost':>6} "
             f"{'e0cost':>6} {'delay':>5}"]
    for v, rec in summary["variants"].items():
        a = rec[f"{model}/all"]
        bs = a["bootstrap"] or {}
        ent = rec.get("vs_e0_entry", {})
        lines.append(
            f"{v:38} {a['trades']:>5} {a['total']:>9.0f} {a['base_total']:>9.0f} "
            f"{a['diff']:>8.0f} {bs.get('p_better') or 0:>5.2f} {a['on_days_diff']:>8.0f} "
            + " ".join(f"{rec[f'{model}/{p}']['diff']:>8.0f}"
                       for p in ("development", "spent", "validation"))
            + f" {ent.get('mean_cost', 0):>6.2f} {ent.get('mean_e0_cost', 0):>6.2f}"
            f" {ent.get('mean_delay_min', 0):>5.1f}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--analyze-only", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frame = (pd.read_parquet(out / "trades.parquet") if args.analyze_only
             else replay(out, args.workers))
    summary = analyze(frame, out)
    for model in MODELS:
        text = table(summary, model)
        (out / f"table_{model}.txt").write_text(text + "\n")
        print(text, "\n")


if __name__ == "__main__":
    main()
