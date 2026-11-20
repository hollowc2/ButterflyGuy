"""Exploratory (post hoc): why did VIX agreement reverse on real 2020-21 options?

The 2020-21 window is spent (pre-registered test, research/direction-vix-oos ae123c3).
This splits gap - fade into payout (settlement value) and cost (entry mark), on agree vs
disagree days, for 2020-21 and the 2022-26 in-sample data. It also reruns the synthetic
settlement test on the 2020-21 calendar, to separate "the market behaved differently"
from "real fly selection or prices differed".

Reads only offline data; never touches a registry, config or service.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import structlog

from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.entry import (
    PROFILES,
    BaselineEntry,
    RunContext,
    SessionLoader,
    gap_direction,
    load_spx_config,
)
from butterfly_guy.research.features import DailyVol
from butterfly_guy.research.simulate import Variant, run_variants

sys.path.insert(0, str(Path(__file__).resolve().parent))
import direction_oos_test as oos  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATASETS = {
    "2020-21": (oos.DURABLE, oos.DATASET),
    "dev": (ROOT / "data/research_cache", "spx_0dte_local_durable_development_20261001"),
    "spent": (ROOT / "data/research_cache", "spx_0dte_local_durable_spent_holdout_20261003"),
    "val": (ROOT / "data/research_cache", "spx_0dte_local_durable_validation_20261001"),
}
DEFAULT_OUT = ROOT / "reports/research/spx-reversal-2020-20261029"


def chunk(args: tuple[str, list[str]]) -> list[dict]:
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    period, days = args
    cache, name = DATASETS[period]
    loader = SessionLoader(Dataset.open(name, cache), PROFILES["vendor_1m"])
    ctx = RunContext(load_spx_config())
    vol = DailyVol(pd.read_parquet(oos.VOL_DAILY))
    dates = [dt.date.fromisoformat(d) for d in days]
    variants = [Variant(d, BaselineEntry(direction=d), ()) for d in ("CALL", "PUT")]
    res = run_variants(loader, variants, ctx, start=dates[0], end=dates[-1])
    rows = {}
    for d in res.dates:
        s = loader.load(d)
        lo, _ = ctx.window(d)
        vix = s.vix.at_or_before(lo, max_age_s=ctx.max_vix_age_s)
        k = min(int(np.searchsorted(s.clock_ts, lo, side="left")), len(s.clock_ts) - 1)
        prev = max(x for x in loader.closes if x < d)
        rows[d] = {"period": period, "date": d.isoformat(), "gap_dir": gap_direction(s),
                   "gap": s.open / s.prev_close - 1, "spot10": float(s.clock_spot[k]),
                   "close": s.close, "vix10": None if vix is None else vix[0],
                   "vix_prior_close": vol.features(d, prev)["vix_prior_close"]}
    for v, run in res.runs.items():
        for d in run.excluded:
            rows[d]["excluded"] = run.excluded[d]
        for t in run.trades:
            st = t.fills.fills["stressed"].entry
            rows[t.date].update({
                f"{v}_mark": t.entry_cost, f"{v}_stressed_entry": st,
                f"{v}_settle": t.settlement, f"{v}_center": t.fly.center,
                f"{v}_width": t.fly.width, f"{v}_mid": t.pnl("midpoint"),
                f"{v}_stressed": t.pnl("stressed")})
    return list(rows.values())


def replay(out: Path, workers: int) -> pd.DataFrame:
    jobs = []
    for period, (cache, name) in DATASETS.items():
        days = [d.isoformat() for d in
                SessionLoader(Dataset.open(name, cache), PROFILES["vendor_1m"]).dates()]
        jobs += [(period, days[i:i + 30]) for i in range(0, len(days), 30)]
    with ProcessPoolExecutor(workers) as pool:
        rows = [r for c in pool.map(chunk, jobs) for r in c]
    frame = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    frame.to_parquet(out / "sessions.parquet")
    return frame


def side(f: pd.DataFrame, which: str) -> pd.DataFrame:
    """Columns of the gap fly (which='gap') or the fade fly, per session."""
    call = f.gap_dir == "CALL"
    pick = call if which == "gap" else ~call
    out = {}
    for c in ("mark", "stressed_entry", "settle", "center", "width", "mid", "stressed"):
        out[c] = np.where(pick, f[f"CALL_{c}"], f[f"PUT_{c}"]).astype(float)
    return pd.DataFrame(out, index=f.index)


def decompose(f: pd.DataFrame) -> dict:
    """Paired days (both flies traded): gap - fade split into payout and cost, $/fly."""
    g, x = side(f, "gap"), side(f, "fade")
    both = g.mark.notna() & x.mark.notna() & g.settle.notna() & x.settle.notna()
    g, x, ff = g[both], x[both], f[both]
    em = ff.spot10 * ff.vix10 / 100 / np.sqrt(252)
    rec = {"paired_days": int(both.sum())}
    pay = 100 * (g.settle - x.settle)
    cost = 100 * (g.mark - x.mark)
    cost_st = 100 * (g.stressed_entry - x.stressed_entry)
    rec |= {
        "edge_mid_per_day": round(float((pay - cost).mean()), 1),
        "payout_diff_per_day": round(float(pay.mean()), 1),
        "cost_diff_per_day": round(float(cost.mean()), 1),
        "stressed_cost_diff_per_day": round(float(cost_st.mean()), 1),
        "gap_cost": round(float(100 * g.mark.mean()), 1),
        "fade_cost": round(float(100 * x.mark.mean()), 1),
        "gap_payout": round(float(100 * g.settle.mean()), 1),
        "fade_payout": round(float(100 * x.settle.mean()), 1),
        "gap_cost_per_width": round(float((g.mark / g.width).mean()), 4),
        "fade_cost_per_width": round(float((x.mark / x.width).mean()), 4),
        "gap_hit_share": round(float((g.settle > 0).mean()), 3),
        "fade_hit_share": round(float((x.settle > 0).mean()), 3),
        "gap_center_em": round(float(((g.center - ff.spot10).abs() / em).median()), 2),
        "fade_center_em": round(float(((x.center - ff.spot10).abs() / em).median()), 2),
        "move_with_gap_em": round(float((np.where(ff.gap_dir == "CALL", 1, -1)
                                         * (ff.close - ff.spot10) / em).mean()), 3),
        "abs_move_em": round(float(((ff.close - ff.spot10).abs() / em).mean()), 3),
        "gap_right_share": round(float((np.sign(ff.close - ff.spot10)
                                        == np.where(ff.gap_dir == "CALL", 1, -1)).mean()), 3),
    }
    return rec


def synthetic(start: dt.date, end: dt.date, dates: set[str] | None) -> dict:
    oos.B_START, oos.B_END = start, end
    d, _ = oos.build_b()
    if dates is not None:
        d = d[d.date.astype(str).isin(dates)].reset_index(drop=True)
    r = oos.subset_diff(d, "agree")
    e = oos.excess(d, []).to_numpy()
    return {"days": len(d), "mean_excess_all": round(float(e.mean()), 5),
            **{k: r[k] for k in ("n_true", "n_false", "mean_true", "mean_false", "diff",
                                 "ci90", "p_positive", "per_year")}}


def analyze(frame: pd.DataFrame) -> dict:
    f = frame[frame.excluded.isna()] if "excluded" in frame else frame
    f = f.assign(
        agree=oos.agree_flags((f.gap_dir == "CALL").to_numpy(),
                              (f.vix10 / f.vix_prior_close - 1).to_numpy()),
        year=pd.to_datetime(f.date).dt.year,
        insample=f.period != "2020-21")
    out: dict = {"decomposition": {}}
    groups = {"2020-21": f.period == "2020-21", "2020": f.year == 2020,
              "2021": f.year == 2021, "2022-26": f.insample}
    for gname, gmask in groups.items():
        for a in (True, False):
            key = f"{gname}/{'agree' if a else 'disagree'}"
            out["decomposition"][key] = decompose(f[gmask & (f.agree == a)])
        # By direction on agree days: gap up + VIX down vs gap down + VIX up.
        for gd in ("CALL", "PUT"):
            m = gmask & f.agree & (f.gap_dir == gd)
            out["decomposition"][f"{gname}/agree/{gd}"] = decompose(f[m])
    # Synthetic close-only test on the 2020-21 calendar: all weekdays, and the M/W/F
    # sessions Test A scored.
    sessions = set(f.loc[f.period == "2020-21", "date"])
    out["synthetic_2020_21_all_weekdays"] = synthetic(dt.date(2020, 1, 2),
                                                      dt.date(2021, 12, 31), None)
    out["synthetic_2020_21_test_a_days"] = synthetic(dt.date(2020, 1, 2),
                                                     dt.date(2021, 12, 31), sessions)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--analyze-only", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frame = (pd.read_parquet(out / "sessions.parquet") if args.analyze_only
             else replay(out, args.workers))
    result = analyze(frame)
    (out / "summary.json").write_text(json.dumps(result, indent=1, default=str) + "\n")
    print(json.dumps(result, indent=1, default=str))


if __name__ == "__main__":
    main()
