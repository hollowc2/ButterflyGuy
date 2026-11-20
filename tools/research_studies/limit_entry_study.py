"""Exploratory limit-order entry study (post hoc, not registered).

E0 picks the fly at its usual decision time; instead of paying the market, a buy limit
rests at the decision-time mark + `offset` for `wait` minutes. Every trade is held to
cash settlement (the X1 exit), so only the entry price differs from X1.

Fill rules, bracketing a real combo fill (1-minute quotes cannot see inside a minute):
- `touch`: the fly's natural debit (outer asks - 2 x center bid) reaches the limit.
  Conservative: nobody fills a combo inside the spread.
- `through`: the fly mark trades 0.05 or more through the limit. Optimistic proxy for a
  market maker filling a combo inside the spread.
An order marketable at the decision snapshot fills at the natural debit. Unfilled orders
either miss the day (`miss`) or pay the stressed natural debit at the window end
(`chase`).

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

from butterfly_guy.research.accounting import Costs
from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.entry import (
    PROFILES,
    BaselineEntry,
    RunContext,
    SessionLoader,
    cached_entries,
    load_spx_config,
)
from butterfly_guy.research.evaluate import EvalParams, paired_bootstrap

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/research_cache"
DEFAULT_OUT = ROOT / "reports/research/spx-limit-entry-20261028"
NAMES = (
    "spx_0dte_local_durable_development_20261001",
    "spx_0dte_local_durable_spent_holdout_20261003",
    "spx_0dte_local_durable_validation_20261001",
)
OFFSETS = (-0.10, -0.05, 0.0, 0.05, 0.10, 0.20)
WAITS = (1, 5, 15, 30)
RULES = ("touch", "through")


def session_rows(args: tuple[str, list[str]]) -> list[dict]:
    """One row per E0 entry: settlement value and every limit variant's fill price."""
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    name, days = args
    loader = SessionLoader(Dataset.open(name, CACHE), PROFILES["vendor_1m"])
    ctx = RunContext(load_spx_config())
    costs = Costs(ctx.config.execution.paper_commission_per_contract)
    rows = []
    for day in days:
        s = loader.load(dt.date.fromisoformat(day))
        if s is None:
            continue
        rows.append({"dataset": name, "date": day, "traded": False})
        entries = cached_entries(s, ctx, BaselineEntry())
        if not entries or s.close is None:
            continue
        e = entries[0]
        path = s.market.fly_path(e.fly)
        if path is None:
            continue
        i = e.index
        executable = path.executable
        row = rows[-1]
        row.update(traded=True, direction=e.direction, vix=e.vix, mark=e.cost,
                   settle=e.fly.settlement_value(s.close), commission=costs.commission,
                   stress=costs.stress,
                   natural=float(path.debit[i]) if executable[i] else None)
        for wait in WAITS:
            hi = s.market.at_or_before(e.ts_us + wait * 60_000_000)
            js = np.arange(i, max(i, hi) + 1)
            ok = executable[js]
            last = js[ok][-1] if ok.any() else None
            row[f"chase_{wait}"] = None if last is None else float(path.debit[last])
            for off in OFFSETS:
                limit = e.cost + off
                if executable[i] and path.debit[i] <= limit + 1e-9:
                    fill = float(path.debit[i])  # marketable on arrival
                    row[f"touch_{off:+.2f}_{wait}"] = row[f"through_{off:+.2f}_{wait}"] = fill
                    continue
                later = js[1:]
                touch = later[executable[later] & (path.debit[later] <= limit + 1e-9)]
                through = later[np.isfinite(path.mark[later])
                                & (path.mark[later] <= limit - 0.05 + 1e-9)]
                row[f"touch_{off:+.2f}_{wait}"] = limit if len(touch) else None
                row[f"through_{off:+.2f}_{wait}"] = limit if len(through) else None
    return rows


def replay(out: Path, workers: int) -> pd.DataFrame:
    jobs = []
    for name in NAMES:
        days = [d.isoformat() for d in
                SessionLoader(Dataset.open(name, CACHE), PROFILES["vendor_1m"]).dates()]
        jobs += [(name, days[i:i + 30]) for i in range(0, len(days), 30)]
    with ProcessPoolExecutor(workers) as pool:
        rows = [r for chunk in pool.map(session_rows, jobs) for r in chunk]
    frame = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    frame.to_parquet(out / "sessions.parquet")
    return frame


def pnl(frame: pd.DataFrame, price: pd.Series) -> pd.Series:
    """Session P&L in dollars for entry prices (NaN = no trade -> 0)."""
    return (100 * (frame.settle - price - frame.commission)).where(price.notna(), 0.0) \
        .fillna(0.0)


def analyze(frame: pd.DataFrame, out: Path) -> dict:
    params = EvalParams()
    periods = {"all": frame.date.notna()} | {n.split("_")[4]: frame.dataset == n for n in NAMES}
    x1_mid = pnl(frame, frame.mark)
    x1_str = pnl(frame, frame.natural + frame.stress)
    result = {"sessions": len(frame), "e0_entries": int(frame.traded.sum()),
              "X1_midpoint": {p: round(float(x1_mid[m].sum())) for p, m in periods.items()},
              "X1_stressed": {p: round(float(x1_str[m].sum())) for p, m in periods.items()},
              "variants": {}}
    for rule in RULES:
        for off in OFFSETS:
            for wait in WAITS:
                price = frame[f"{rule}_{off:+.2f}_{wait}"]
                filled = price.notna()
                chase = price.fillna(frame[f"chase_{wait}"] + frame.stress)
                for fallback, entry in (("miss", price), ("chase", chase)):
                    v = pnl(frame, entry)
                    rec = {
                        "fill_rate": round(float(filled.sum() / frame.traded.sum()), 3),
                        "trades": int(entry.notna().sum()),
                        "total": {p: round(float(v[m].sum())) for p, m in periods.items()},
                        "vs_x1_stressed": paired_bootstrap(v.to_numpy(), x1_str.to_numpy(),
                                                           params),
                        # Adverse selection: X1's midpoint P&L on filled vs unfilled days.
                        "x1_mid_filled_days": round(float(x1_mid[filled].sum())),
                        "x1_mid_unfilled_days": round(float(x1_mid[frame.traded
                                                                    & ~filled].sum())),
                    }
                    result["variants"][f"{rule}_{off:+.2f}_{wait}m_{fallback}"] = rec
    (out / "summary.json").write_text(json.dumps(result, indent=1) + "\n")
    return result


def table(result: dict) -> str:
    lines = [f"sessions={result['sessions']} E0 entries={result['e0_entries']}",
             f"X1 midpoint {result['X1_midpoint']}", f"X1 stressed {result['X1_stressed']}",
             f"{'variant':28} {'fill':>5} {'n':>4} {'total':>8} {'dev':>8} {'spent':>8} "
             f"{'val':>8} {'vsX1str':>8} {'p>':>5} {'x1mid_fill':>10} {'x1mid_unf':>9}"]
    for name, r in result["variants"].items():
        t, b = r["total"], r["vs_x1_stressed"]
        lines.append(
            f"{name:28} {r['fill_rate']:>5.2f} {r['trades']:>4} {t['all']:>8} "
            f"{t['development']:>8} {t['spent']:>8} {t['validation']:>8} "
            f"{t['all'] - result['X1_stressed']['all']:>8} {b['p_better'] or 0:>5.2f} "
            f"{r['x1_mid_filled_days']:>10} {r['x1_mid_unfilled_days']:>9}")
    return "\n".join(lines)


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
    text = table(analyze(frame, out))
    (out / "table.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
