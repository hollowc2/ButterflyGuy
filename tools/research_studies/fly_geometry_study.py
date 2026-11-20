"""Exploratory (post hoc): which fly center distance and wing width pay best, by VIX regime?

Live flies sit about 0.9 of the VIX-implied daily move (EM) from spot while SPX typically
moves about 0.4 EM after 10:00 ET. This prices a grid of flies, center offset x wing width
in EM units, in both directions, at the first entry-window snapshot (10:00 ET) with a fresh
VIX, and holds each to cash settlement:

- Real: the 2020-21 (spent) and 2022-26 SPXW chains, mark and executable debit.
- Synthetic: 2003-2019 closes from the owner's minute CSVs (the close-only proxy validated
  in reversal_2020_study.py), with each cell's cost taken from the 2022-26 real marks, as
  a fraction of width, per direction and VIX regime.

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
from butterfly_guy.research.entry import PROFILES, RunContext, SessionLoader, load_spx_config
from butterfly_guy.research.evaluate import block_bootstrap_indices
from butterfly_guy.research.market import Fly

sys.path.insert(0, str(Path(__file__).resolve().parent))
import direction_oos_test as oos  # noqa: E402
import reversal_2020_study as rev  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "reports/research/spx-fly-geometry-20261029"
OFFSETS = (0.0, 0.25, 0.5, 0.75, 0.93, 1.25, 1.5)
WIDTHS = (0.25, 0.4, 0.57, 0.75, 1.0)
BASE = (0.93, 0.57)  # the live geometry's median, as in the OOS synthetic test
COMMISSION = 4 * 0.65 / 100  # per fly, points
STRESS = 4 * 0.05
REGIMES = {"<17": (0, 17), "17-25": (17, 25), ">=25": (25, 999)}
REPS, BLOCK = 5_000, 5
EM_REF = 50.0  # dollars are quoted at a 50-point EM (SPX ~5,000, VIX ~16)


def regime(vix: pd.Series) -> pd.Series:
    return pd.cut(vix, [0, 17, 25, 999], right=False, labels=list(REGIMES))


def snap(x: float, step: float = 5.0) -> float:
    return float(round(x / step) * step)


def chunk(args: tuple[str, list[str]]) -> list[dict]:
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    period, days = args
    cache, name = rev.DATASETS[period]
    loader = SessionLoader(Dataset.open(name, cache), PROFILES["vendor_1m"])
    ctx = RunContext(load_spx_config())
    rows = []
    for d in (dt.date.fromisoformat(x) for x in days):
        s = loader.load(d)
        if s is None or s.close is None:
            continue
        lo, _ = ctx.window(d)
        vix = s.vix.at_or_before(lo, max_age_s=ctx.max_vix_age_s)
        i = s.market.at_or_before(lo)
        if vix is None or i < 0:
            continue
        spot = float(s.clock_spot[s.clock_index(lo)])
        em = spot * vix[0] / 100 / np.sqrt(252)
        base = {"period": period, "date": d.isoformat(), "spot10": spot, "vix10": vix[0],
                "em": em, "close": s.close, "is_call": s.open >= s.prev_close}
        for direction, sign in (("CALL", 1), ("PUT", -1)):
            for c in OFFSETS:
                for w in WIDTHS:
                    k = snap(spot + sign * c * em)
                    width = max(5.0, snap(w * em))
                    fly = Fly(direction, k - width, k, k + width)
                    path = s.market.fly_path(fly)
                    mark = debit = np.nan
                    if path is not None:
                        mark, debit = float(path.mark[i]), float(path.debit[i])
                    rows.append(base | {
                        "dir": direction, "c": c, "w": w, "center": k, "width": width,
                        "mark": mark, "debit": debit,
                        "settle": fly.settlement_value(s.close)})
    return rows


def replay(out: Path, workers: int) -> pd.DataFrame:
    jobs = []
    for period, (cache, name) in rev.DATASETS.items():
        days = [d.isoformat() for d in
                SessionLoader(Dataset.open(name, cache), PROFILES["vendor_1m"]).dates()]
        jobs += [(period, days[i:i + 30]) for i in range(0, len(days), 30)]
    with ProcessPoolExecutor(workers) as pool:
        rows = [r for c in pool.map(chunk, jobs) for r in c]
    frame = pd.DataFrame(rows)
    frame.to_parquet(out / "real.parquet")
    return frame


def boot(x: np.ndarray, seed: int = 1) -> np.ndarray:
    return x[block_bootstrap_indices(len(x), REPS, BLOCK, seed)].mean(axis=1)


def summarize(pnl: pd.DataFrame) -> dict:
    """pnl: one row per day (sorted by date), one column per cell (c, w), in EM-points.
    Mean per cell, plus the paired difference against BASE with a block-bootstrap CI."""
    out = {}
    base = pnl[BASE].to_numpy()
    idx = block_bootstrap_indices(len(pnl), REPS, BLOCK, 1)
    for cell in pnl.columns:
        x = pnl[cell].to_numpy()
        diff = (x - base)[idx].mean(axis=1)
        out[f"{cell[0]}/{cell[1]}"] = {
            "usd_at_ref_em": round(float(x.mean()) * 100 * EM_REF, 1),
            "diff_vs_base_usd": round(float((x - base).mean()) * 100 * EM_REF, 1),
            "p_better": round(float((diff > 0).mean()), 3)}
    return out


def real_tables(f: pd.DataFrame) -> dict:
    """Per-fly P&L in EM-points on days where every cell priced, by period, side, regime."""
    f = f.assign(mid=(f.settle - f.mark - COMMISSION) / f.em,
                 stressed=(f.settle - f.debit - COMMISSION - STRESS) / f.em,
                 side=np.where((f.dir == "CALL") == f.is_call, "gap", "fade"),
                 regime=regime(f.vix10))
    out: dict = {}
    for period, pmask in {"2022-26": f.period != "2020-21",
                          "2020-21": f.period == "2020-21"}.items():
        for side in ("gap", "fade"):
            g = f[pmask & (f.side == side)]
            for model in ("mid", "stressed"):
                wide = g.pivot_table(index="date", columns=["c", "w"], values=model)
                wide = wide.dropna().sort_index()
                reg = g.groupby("date").regime.first().reindex(wide.index)
                key = f"{period}/{side}/{model}"
                out[key] = {"days": len(wide), "all": summarize(wide)}
                for r in REGIMES:
                    m = (reg == r).to_numpy()
                    if m.sum() >= 40:
                        out[key][r] = {"days": int(m.sum()), **summarize(wide[m])}
    return out


def cost_table(f: pd.DataFrame) -> pd.DataFrame:
    """Mean mark / width per direction x regime x cell, 2022-26 (the synthetic's costs);
    2020-21 alongside to show whether pricing in EM units carries across eras."""
    f = f.assign(frac=f.mark / f.width, frac_debit=(f.debit + STRESS) / f.width,
                 regime=regime(f.vix10), era=np.where(f.period == "2020-21", "2020-21",
                                                      "2022-26"))
    return (f.groupby(["era", "dir", "regime", "c", "w"], observed=True)
            [["frac", "frac_debit"]].mean().reset_index())


def synthetic(costs: pd.DataFrame) -> dict:
    oos.B_START, oos.B_END = dt.date(2003, 7, 1), dt.date(2019, 12, 31)
    d, _ = oos.build_b()
    d = d.sort_values("date").reset_index(drop=True)
    em = d.spx10 * d.vix10 / 100 / np.sqrt(252)
    d["regime"] = regime(d.vix10)
    c22 = costs[costs.era == "2022-26"].set_index(["dir", "regime", "c", "w"])
    out: dict = {"days": len(d)}
    for side in ("gap", "fade"):
        call = d.is_call if side == "gap" else ~d.is_call
        for model, col in (("mid", "frac"), ("stressed", "frac_debit")):
            cells = {}
            for c in OFFSETS:
                for w in WIDTHS:
                    center = d.spx10 + np.where(call, 1, -1) * c * em
                    pay = np.maximum(0.0, 1 - (d.close - center).abs() / (w * em))
                    keys = zip(np.where(call, "CALL", "PUT"), d.regime, strict=True)
                    cost = np.array([c22[col].get((dr, r, c, w), np.nan) for dr, r in keys])
                    cells[(c, w)] = w * (pay - cost) - COMMISSION / em  # EM-points per fly
            wide = pd.DataFrame(cells)
            key = f"{side}/{model}"
            out[key] = {"all": summarize(wide.dropna())}
            for r in REGIMES:
                m = (d.regime == r).to_numpy()
                out[key][r] = {"days": int(m.sum()), **summarize(wide[m].dropna())}
    # Where the close lands after 10:00, in EM: the realized density the cells sample.
    mv = ((d.close - d.spx10) / em)
    out["abs_move_em"] = {r: round(float(mv[d.regime == r].abs().median()), 3)
                          for r in REGIMES}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--analyze-only", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    f = (pd.read_parquet(out / "real.parquet") if args.analyze_only
         else replay(out, args.workers))
    costs = cost_table(f)
    costs.to_csv(out / "cost_table.csv", index=False)
    result = {"real": real_tables(f), "synthetic_2003_19": synthetic(costs)}
    (out / "summary.json").write_text(json.dumps(result, indent=1, default=str) + "\n")
    print("wrote", out / "summary.json")


if __name__ == "__main__":
    main()
