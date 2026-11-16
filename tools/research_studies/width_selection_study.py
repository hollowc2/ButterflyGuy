"""Exploratory (post hoc): does the cross-width pick matter, or does it only add variance?

Live SPX selection builds one VIX-anchored best fly per width in the active VIX bucket,
then keeps the width whose reward/risk is closest to the target (`select_cross_width_candidate`).
On 2026-11-16 that rule picked the 20-wide by an RR margin of 0.10, and the 30/40-wide
flies settled far in the money. This replays the same decision time and the same per-width
candidates under four cross-width policies:

- live:   RR closest to target (the current rule)
- narrow: the bucket's first (narrowest) width
- middle: the bucket's middle width
- wide:   the bucket's last (widest) width

A fixed-width policy falls back to the live pick when its width has no qualifying fly; the
fallback count is reported. Each policy runs with the configured exits (E0) and held to cash
settlement (X1). Sessions excluded for any policy are dropped from every policy.

Reads only offline data; never touches a registry, config or service.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import structlog

from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.entry import (
    PROFILES,
    Entry,
    RunContext,
    SessionLoader,
    gap_direction,
    load_spx_config,
    selection_span,
)
from butterfly_guy.research.evaluate import block_bootstrap_indices
from butterfly_guy.research.market import Fly
from butterfly_guy.research.simulate import Variant, run_variants
from butterfly_guy.strategy.entry_selection import select_entry_candidate

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reversal_2020_study as rev  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "reports/research/spx-width-selection-20261116"
POLICIES = ("live", "narrow", "middle", "wide")
EXITS = {"E0": "config", "X1": ()}
MODELS = ("midpoint", "stressed")
REGIMES = [(0, 17, "<17"), (17, 24.5, "17-24.5"), (24.5, 32, "24.5-32"), (32, 999, ">=32")]
REPS, BLOCK = 5_000, 5


@dataclass(frozen=True)
class WidthPolicyEntry:
    """Baseline entry timing and direction; the cross-width pick follows `policy`."""

    policy: str

    def entries(self, s, ctx: RunContext) -> list[Entry]:
        lo, hi = ctx.window(s.date)
        direction = gap_direction(s)
        for ts in s.clock_ts[(s.clock_ts >= lo) & (s.clock_ts <= hi)]:
            ts = int(ts)
            vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
            if vix is None:
                continue
            i = s.market.at_or_before(ts)
            if i < 0:
                continue
            spot = float(s.clock_spot[s.clock_index(ts)])
            quotes = s.market.quotes_at(i, direction, near=spot,
                                        span=selection_span(ctx.config))
            r = select_entry_candidate(quotes=quotes, spot=spot, direction=direction,
                                       vix=vix[0], config=ctx.config, asset=ctx.asset)
            if r.candidate is None:
                continue
            cand, how = r.candidate, "live"
            if self.policy != "live":
                widths = list(r.active_widths)
                want = {"narrow": widths[0], "middle": widths[len(widths) // 2],
                        "wide": widths[-1]}[self.policy]
                hit = [c for c in r.per_width_bests if c.wing_width == want]
                cand, how = (hit[0], "fixed") if hit else (r.candidate, "fallback")
            tag = f"{how}|live_w={r.candidate.wing_width}|bucket={list(r.active_widths)}"
            return [Entry(Fly.from_candidate(cand), ts, i, cand.cost, direction,
                          vix=vix[0], spot=spot, candidate=cand, tag=tag)]
        return []


def chunk(args: tuple[str, list[str]]) -> list[dict]:
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    period, days = args
    cache, name = rev.DATASETS[period]
    loader = SessionLoader(Dataset.open(name, cache), PROFILES["vendor_1m"])
    ctx = RunContext(load_spx_config())
    variants = [Variant(f"{p}:{x}", WidthPolicyEntry(p), ex)
                for p in POLICIES for x, ex in EXITS.items()]
    dates = [dt.date.fromisoformat(d) for d in days]
    res = run_variants(loader, variants, ctx, start=dates[0], end=dates[-1])
    rows = []
    for vname, run in res.runs.items():
        policy, exits = vname.split(":")
        for d, why in run.excluded.items():
            rows.append({"period": period, "date": d.isoformat(), "policy": policy,
                         "exits": exits, "excluded": why})
        for t in run.trades:
            how, live_w, bucket = t.tag.split("|")
            rows.append({
                "period": period, "date": t.date.isoformat(), "policy": policy,
                "exits": exits, "excluded": None, "how": how,
                "live_width": int(live_w.split("=")[1]), "bucket": bucket.split("=")[1],
                "width": t.fly.width,
                "fly": str(t.fly), "vix": t.vix, "cost": t.entry_cost,
                "exit_reason": t.exit_reason, "settlement": t.settlement, "peak": t.peak,
                **{f"pnl_{m}": t.pnl(m) for m in MODELS},
            })
    return rows


def session_days(period: str) -> list[str]:
    cache, name = rev.DATASETS[period]
    loader = SessionLoader(Dataset.open(name, cache), PROFILES["vendor_1m"])
    return [d.isoformat() for d in loader.dates()]


def summarize(df: pd.DataFrame) -> dict:
    out: dict = {}
    excl = set(df.loc[df.excluded.notna(), ["period", "date"]].itertuples(index=False))
    t = df[df.excluded.isna()].copy()
    t = t[[(p, d) not in excl for p, d in zip(t.period, t.date)]]
    # Keep sessions every policy traded under both exit modes, so arms are paired.
    full = t.groupby(["period", "date"]).size()
    keep = set(full[full == len(POLICIES) * len(EXITS)].index)
    t = t[[(p, d) in keep for p, d in zip(t.period, t.date)]]
    t["regime"] = pd.cut(t.vix, [r[0] for r in REGIMES] + [999], right=False,
                         labels=[r[2] for r in REGIMES])
    out["sessions"] = len(keep)
    out["excluded_sessions"] = len(excl)
    for ex in EXITS:
        for m in MODELS:
            col = f"pnl_{m}"
            piv = t[t.exits == ex].pivot_table(index=["period", "date"], columns="policy",
                                               values=col, aggfunc="sum").sort_index()
            n = len(piv)
            idx = block_bootstrap_indices(n, REPS, BLOCK, seed=20261116)
            key = f"{ex}/{m}"
            out[key] = {}
            for p in POLICIES:
                v = piv[p].to_numpy()
                diff = v - piv["live"].to_numpy()
                boot = diff[idx].mean(axis=1) if n else np.array([0.0])
                sub = t[(t.exits == ex) & (t.policy == p)]
                out[key][p] = {
                    "total": round(float(v.sum()), 0), "mean": round(float(v.mean()), 2),
                    "win_rate": round(float((v > 0).mean()), 3),
                    "sd": round(float(v.std(ddof=1)), 1),
                    "diff_vs_live_mean": round(float(diff.mean()), 2),
                    "diff_ci95": [round(float(np.percentile(boot, q)), 2) for q in (2.5, 97.5)],
                    "p_better": round(float((boot > 0).mean()), 3),
                    "fallbacks": int((sub.how == "fallback").sum()),
                    "by_period": {k: round(float(g[col].sum()), 0)
                                  for k, g in sub.groupby("period")},
                    "by_regime": {str(k): [int(len(g)), round(float(g[col].sum()), 0)]
                                  for k, g in sub.groupby("regime", observed=True)},
                }
    live = t[(t.policy == "live") & (t.exits == "E0")]
    out["live_width_choice"] = {
        b: live[live.bucket == b].live_width.value_counts().sort_index().to_dict()
        for b in sorted(live.bucket.unique())}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--periods", nargs="+", default=["2020-21", "spent", "dev", "val"])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--chunk", type=int, default=20)
    a = ap.parse_args()
    jobs = []
    for p in a.periods:
        days = session_days(p)
        jobs += [(p, days[i:i + a.chunk]) for i in range(0, len(days), a.chunk)]
    rows: list[dict] = []
    with ProcessPoolExecutor(a.workers) as pool:
        for r in pool.map(chunk, jobs):
            rows += r
    df = pd.DataFrame(rows)
    a.out.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out / "trades.csv", index=False)
    summary = summarize(df)
    (a.out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
