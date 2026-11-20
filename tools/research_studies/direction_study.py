"""Exploratory direction study (post hoc, not registered): is the gap direction worth
anything?

Every session is replayed with the live-selected CALL fly and the live-selected PUT fly
(same window, selector and exits as E0/X1). The gap rule picks one of them per day, the
fade picks the other, a coin flip picks at random (a sign-permutation null over 20,000
draws), and `both` holds the two (reported per fly: half their sum). `gap` must equal
E0/X1 exactly; the run checks it.

Reads only the canonical offline datasets; never touches a registry, config or service.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
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
from butterfly_guy.research.evaluate import EvalParams, paired_bootstrap
from butterfly_guy.research.market import et_us
from butterfly_guy.research.simulate import Variant, run_variants

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/research_cache"
DEFAULT_OUT = ROOT / "reports/research/spx-direction-20261028"
NAMES = (
    "spx_0dte_local_durable_development_20261001",
    "spx_0dte_local_durable_spent_holdout_20261003",
    "spx_0dte_local_durable_validation_20261001",
)
MODELS = ("midpoint", "stressed")
EXITS = {"held": (), "trail": "config"}


def variants() -> list[Variant]:
    return [Variant(f"{d}_{x}", BaselineEntry(direction=d), rules)
            for d in ("gap", "CALL", "PUT") for x, rules in EXITS.items()]


def chunk(args: tuple[str, list[str]]) -> list[dict]:
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    name, days = args
    loader = SessionLoader(Dataset.open(name, CACHE), PROFILES["vendor_1m"])
    ctx = RunContext(load_spx_config())
    dates = [dt.date.fromisoformat(d) for d in days]
    res = run_variants(loader, variants(), ctx, start=dates[0], end=dates[-1])
    rows = {}
    for d in res.dates:
        s = loader.load(d)
        lo, _ = ctx.window(d)
        k = min(int(np.searchsorted(s.clock_ts, lo, side="left")), len(s.clock_ts) - 1)
        spot10 = float(s.clock_spot[k])
        vix = s.vix.at_or_before(lo, max_age_s=ctx.max_vix_age_s)
        rows[d] = {"dataset": name, "date": d.isoformat(), "gap_dir": gap_direction(s),
                   "gap": s.open / s.prev_close - 1, "spot10": spot10, "close": s.close,
                   "vix": None if vix is None else vix[0],
                   "move_open_to_10": spot10 / s.open - 1,
                   "first_30m": float(s.clock_spot[min(int(np.searchsorted(
                       s.clock_ts, et_us(d, 10, 0), side="left")), len(s.clock_ts) - 1)])
                   / s.open - 1}
    for v, run in res.runs.items():
        for d in run.excluded:
            rows[d][f"excluded_{v}"] = run.excluded[d]
        for t in run.trades:
            for m in MODELS:
                rows[t.date][f"{v}_{m}"] = t.pnl(m)
    return list(rows.values())


def replay(out: Path, workers: int) -> pd.DataFrame:
    jobs = []
    for name in NAMES:
        days = [d.isoformat() for d in
                SessionLoader(Dataset.open(name, CACHE), PROFILES["vendor_1m"]).dates()]
        jobs += [(name, days[i:i + 30]) for i in range(0, len(days), 30)]
    with ProcessPoolExecutor(workers) as pool:
        rows = [r for c in pool.map(chunk, jobs) for r in c]
    frame = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    frame.to_parquet(out / "sessions.parquet")
    return frame


def analyze(frame: pd.DataFrame, out: Path) -> dict:
    excluded = frame.filter(like="excluded_").notna().any(axis=1)
    frame = frame[~excluded].reset_index(drop=True)
    params = EvalParams()
    rng = np.random.default_rng(1)
    periods = {"all": frame.date.notna()} | {n.split("_")[4]: frame.dataset == n for n in NAMES}
    is_call = (frame.gap_dir == "CALL").to_numpy()
    known = frame.close.notna()
    up = (frame.close > frame.spot10)[known]
    result = {
        "sessions": len(frame), "excluded": int(excluded.sum()),
        # Was the gap direction right from 10:00 to the close?
        "gap_dir_right_from_10": round(float((up == is_call[known]).mean()), 4),
        "close_above_10_share": round(float(up.mean()), 4),
        "gap_call_share": round(float(is_call.mean()), 4),
        "arms": {},
    }
    for x in EXITS:
        for m in MODELS:
            call = frame[f"CALL_{x}_{m}"].fillna(0.0).to_numpy()
            put = frame[f"PUT_{x}_{m}"].fillna(0.0).to_numpy()
            gap = np.where(is_call, call, put)
            check = frame[f"gap_{x}_{m}"].fillna(0.0).to_numpy()
            assert np.allclose(gap, check), f"gap arm != replayed E0/X1 ({x}, {m})"
            fade = np.where(is_call, put, call)
            flips = rng.random((20_000, len(call))) < 0.5
            coin = np.where(flips, call, put).sum(axis=1)
            arms = {"gap": gap, "fade": fade, "CALL": call, "PUT": put,
                    "both_per_fly": (call + put) / 2}
            rec = {name: {p: round(float(v[mask].sum())) for p, mask in periods.items()}
                   for name, v in arms.items()}
            rec["coin_flip"] = {"mean": round(float(coin.mean())),
                                "p5_p95": [round(float(q)) for q in np.percentile(coin, [5, 95])],
                                "gap_percentile": round(float((coin < gap.sum()).mean()), 4)}
            rec["gap_vs_fade"] = paired_bootstrap(gap, fade, params)
            rec["gap_vs_both_per_fly"] = paired_bootstrap(gap, arms["both_per_fly"], params)
            # Gap advantage over the fade by gap size and VIX (descriptive).
            diff = pd.Series(gap - fade)
            g = frame.gap.abs()
            rec["gap_minus_fade_by_abs_gap"] = {
                str(k): round(float(v)) for k, v in diff.groupby(pd.cut(
                    g, [0, .0025, .005, .01, 1], include_lowest=True), observed=True).sum().items()}
            rec["gap_minus_fade_by_vix"] = {
                str(k): round(float(v)) for k, v in diff.groupby(pd.cut(
                    frame.vix, [0, 14, 17, 20, 25, 100]), observed=True).sum().items()}
            result["arms"][f"{x}/{m}"] = rec
    (out / "summary.json").write_text(json.dumps(result, indent=1) + "\n")
    return result


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
    print(json.dumps(analyze(frame, out), indent=1))


if __name__ == "__main__":
    main()
