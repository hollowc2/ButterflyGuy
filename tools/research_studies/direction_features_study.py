"""Exploratory follow-up to `direction_study.py` (post hoc, not registered).

Part A asks what makes the gap direction more reliable. Every feature is known by 10:00
ET. The quantity of interest per session is gap-minus-fade: the gap fly's P&L minus the
opposite fly's. Rules are chosen on the development window (2022-01 -> 2024-06) and then
checked on the spent holdout and validation windows. Those windows were already seen in
aggregate, so the check is a stability check, not a holdout.

Part B describes how the X1 trade behaves by VIX regime and simulates VIX-based sizing.

Inputs: the direction study's sessions.parquet, the activation study's sessions.jsonl
(pre-10:00 features), dataset daily bars and Cboe VIX daily closes. No replay.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from butterfly_guy.research.dataset import Dataset

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/research_cache"
DIRECTION = ROOT / "reports/research/spx-direction-20261028/sessions.parquet"
ACTIVATION = ROOT / "reports/research/spx-activation-20261018/sessions.jsonl"
DEFAULT_OUT = ROOT / "reports/research/spx-direction-features-20261028"
NAMES = (
    "spx_0dte_local_durable_development_20261001",
    "spx_0dte_local_durable_spent_holdout_20261003",
    "spx_0dte_local_durable_validation_20261001",
)
PERIODS = ("dev", "spent", "val")
SQ252 = math.sqrt(252)


def load() -> pd.DataFrame:
    d = pd.read_parquet(DIRECTION)
    a = pd.read_json(ACTIVATION, lines=True, convert_dates=False, dtype={"date": str})
    keep = ["date", "vix_prior_close", "vix9d_vix_prior", "vix_vix3m_prior",
            "opening_range_sigma", "spread_ratio", "entry_cost", "center", "width", "fomc",
            "early_release"]
    f = d.merge(a[keep], on="date", how="left", validate="one_to_one")
    f["period"] = f.dataset.map(dict(zip(NAMES, PERIODS, strict=True)))
    f["date_"] = pd.to_datetime(f.date)

    # SPX daily closes (sessions plus the prior days each dataset carries).
    closes = pd.concat([
        (b := Dataset.open(n, CACHE).daily_bars())[b.underlying == "SPX"][["date", "close"]]
        for n in NAMES]).drop_duplicates("date").sort_values("date")
    closes["date"] = pd.to_datetime(closes.date)
    c = closes.set_index("date").close
    prior = c.shift(1)
    trend = pd.DataFrame({
        "ret_1d_prior": prior / c.shift(2) - 1,
        "ret_5d_prior": prior / c.shift(6) - 1,
        "above_ma20_prior": prior / c.shift(1).rolling(20).mean() - 1,
    })
    f = f.merge(trend, left_on="date_", right_index=True, how="left")

    # VIX relative to its own recent level (Cboe daily closes, prior sessions only).
    vd = pd.read_parquet(CACHE / "spx_0dte/aux/vol_index_daily.parquet")
    vix = vd[vd["index"] == "VIX"].assign(date=lambda x: pd.to_datetime(x.date)) \
        .set_index("date").close.sort_index()
    rel = (vix.shift(1) / vix.shift(1).rolling(60).median()).rename("vix_rel60_prior")
    f = f.merge(rel, left_on="date_", right_index=True, how="left")

    sign = np.where(f.gap_dir == "CALL", 1.0, -1.0)
    sigma_prior = f.vix_prior_close / 100 / SQ252
    f["abs_gap"] = f.gap.abs()
    f["gap_sigma"] = f.abs_gap / sigma_prior
    f["open10_with_gap"] = (np.sign(f.move_open_to_10) == np.sign(f.gap)).astype(int)
    f["gap_fill_10"] = -f.move_open_to_10 / f.gap  # 1 = gap fully filled by 10:00
    f["vix_overnight"] = f.vix / f.vix_prior_close - 1
    f["vix_agrees"] = (np.sign(-f.vix_overnight) == sign).astype(int)
    f["ret1d_agrees"] = (np.sign(f.ret_1d_prior) == sign).astype(int)
    f["ret5d_agrees"] = (np.sign(f.ret_5d_prior) == sign).astype(int)
    f["ma20_agrees"] = (np.sign(f.above_ma20_prior) == sign).astype(int)
    f["weekday"] = f.date_.dt.day_name().str[:3]

    for x in ("held", "trail"):
        for m in ("midpoint", "stressed"):
            call = f[f"CALL_{x}_{m}"].fillna(0.0)
            put = f[f"PUT_{x}_{m}"].fillna(0.0)
            f[f"gap_{x}_{m}"] = f[f"gap_{x}_{m}"].fillna(0.0)
            f[f"fade_{x}_{m}"] = np.where(sign > 0, put, call)
            f[f"edge_{x}_{m}"] = f[f"gap_{x}_{m}"] - f[f"fade_{x}_{m}"]
    # Descriptive only (uses the close): directional and absolute move from 10:00 in units
    # of the VIX-implied daily move.
    em = f.spot10 * f.vix / 100 / SQ252
    f["move_with_gap_em"] = sign * (f.close - f.spot10) / em
    f["abs_move_em"] = (f.close - f.spot10).abs() / em
    f["center_dist_em"] = (f.center - f.spot10).abs() / em
    f["cost_per_width"] = f.entry_cost / f.width
    return f


def bucket_table(f: pd.DataFrame, col: str, bins: list | None, model: str) -> pd.DataFrame:
    key = pd.cut(f[col], bins) if bins is not None else f[col]
    rows = []
    for k, g in f.groupby(key, observed=True):
        row = {"bucket": str(k), "n": len(g)}
        for p in PERIODS:
            row[f"edge_{p}"] = round(g.loc[g.period == p, f"edge_held_{model}"].sum())
        row["edge_all"] = round(g[f"edge_held_{model}"].sum())
        row["edge_per_day"] = round(g[f"edge_held_{model}"].mean(), 1)
        row["gap_all"] = round(g[f"gap_held_{model}"].sum())
        row["gap_per_day"] = round(g[f"gap_held_{model}"].mean(), 1)
        rows.append(row)
    return pd.DataFrame(rows)


def max_dd(x: np.ndarray) -> float:
    eq = np.cumsum(x)
    return float(np.max(np.maximum.accumulate(np.r_[0, eq])[1:] - eq)) if len(x) else 0.0


def part_a(f: pd.DataFrame, out: list[str], summary: dict) -> None:
    out.append("=" * 100 + "\nPART A - what makes the gap direction reliable (held to settlement)\n"
               "edge = gap fly P&L - fade fly P&L; gap = the current rule's P&L\n")
    specs = [
        ("gap_sigma", [0, .1, .2, .35, .5, .75, 1, 10]),
        ("abs_gap", [0, .001, .0025, .005, .0075, .01, .1]),
        ("open10_with_gap", None),
        ("gap_fill_10", [-10, -0.5, 0, .25, .5, 1, 10]),
        ("vix_agrees", None),
        ("vix_overnight", [-1, -.08, -.04, 0, .04, .08, 1]),
        ("ret1d_agrees", None),
        ("ret5d_agrees", None),
        ("ma20_agrees", None),
        ("vix9d_vix_prior", [0, .85, .95, 1.05, 5]),
        ("vix_vix3m_prior", [0, .85, .9, .95, 1, 5]),
        ("opening_range_sigma", [0, .25, .4, .55, .75, 5]),
        ("weekday", None),
    ]
    for model in ("midpoint", "stressed"):
        for col, bins in specs:
            t = bucket_table(f, col, bins, model)
            summary.setdefault("part_a", {}).setdefault(model, {})[col] = t.to_dict("records")
            out.append(f"-- {col} [{model}]\n{t.to_string(index=False)}\n")

    # Direction rules on binary agreement features, chosen on dev, checked elsewhere.
    out.append("-- direction rules (midpoint / stressed totals by period)")
    rules = {
        "gap (baseline)": np.ones(len(f), bool),
        "gap if VIX agrees else fade": f.vix_agrees.to_numpy(bool),
        "gap if 10:00 agrees else fade": f.open10_with_gap.to_numpy(bool),
        "gap if 5d trend agrees else fade": f.ret5d_agrees.to_numpy(bool),
        "gap if MA20 agrees else fade": f.ma20_agrees.to_numpy(bool),
        "gap if 1d agrees else fade": f.ret1d_agrees.to_numpy(bool),
    }
    rows = []
    for name, keep in rules.items():
        for alt in ("fade", "skip"):
            if name.startswith("gap (") and alt == "skip":
                continue
            row = {"rule": name if alt == "fade" else name.replace("else fade", "else skip")}
            for m in ("midpoint", "stressed"):
                other = f[f"fade_held_{m}"] if alt == "fade" else 0.0
                v = np.where(keep, f[f"gap_held_{m}"], other)
                for p in PERIODS:
                    row[f"{m[:3]}_{p}"] = round(float(v[(f.period == p).to_numpy()].sum()))
                row[f"{m[:3]}_all"] = round(float(v.sum()))
            rows.append(row)
    t = pd.DataFrame(rows)
    summary["part_a_rules"] = t.to_dict("records")
    out.append(t.to_string(index=False) + "\n")


def part_b(f: pd.DataFrame, out: list[str], summary: dict) -> None:
    out.append("=" * 100 + "\nPART B - VIX regime (X1 = gap fly held to settlement)\n")
    bins = [0, 13, 15, 16, 17, 18, 20, 22, 25, 30, 100]
    traded = f.gap_held_midpoint != 0
    rows = []
    for k, g in f[traded].groupby(pd.cut(f.vix[traded], bins), observed=True):
        rows.append({
            "vix": str(k), "trades": len(g),
            "mid_total": round(g.gap_held_midpoint.sum()),
            "str_total": round(g.gap_held_stressed.sum()),
            "mid_per": round(g.gap_held_midpoint.mean(), 1),
            "str_per": round(g.gap_held_stressed.mean(), 1),
            "win%": round(100 * (g.gap_held_stressed > 0).mean(), 1),
            "edge_per": round(g.edge_held_midpoint.mean(), 1),
            "cost/width": round(g.cost_per_width.mean(), 3),
            "spread_ratio": round(g.spread_ratio.mean(), 3),
            "center_em": round(g.center_dist_em.mean(), 2),
            "absmove_em": round(g.abs_move_em.mean(), 2),
            "withgap_em": round(g.move_with_gap_em.mean(), 2),
            "hit_center%": round(100 * (np.abs(g.move_with_gap_em - g.center_dist_em)
                                        <= g.width / (g.spot10 * g.vix / 100 / SQ252)).mean(), 1),
            **{f"str_{p}": round(g.loc[g.period == p, "gap_held_stressed"].sum())
               for p in PERIODS},
        })
    t = pd.DataFrame(rows)
    summary["part_b_buckets"] = t.to_dict("records")
    out.append("center_em: fly center distance from 10:00 spot in VIX-implied daily moves;\n"
               "absmove_em: |close - 10:00 spot| in the same units (descriptive);\n"
               "withgap_em: signed move in the gap direction; hit_center%: close within one\n"
               "wing width of the center.\n")
    out.append(t.to_string(index=False) + "\n")

    rel = []
    for k, g in f[traded].groupby(pd.cut(f.vix_rel60_prior[traded], [0, .85, .95, 1.05, 1.2, 5]),
                                  observed=True):
        rel.append({"vix/60d median": str(k), "trades": len(g),
                    "mid_total": round(g.gap_held_midpoint.sum()),
                    "str_total": round(g.gap_held_stressed.sum()),
                    "edge_mid": round(g.edge_held_midpoint.sum()),
                    **{f"str_{p}": round(g.loc[g.period == p, "gap_held_stressed"].sum())
                       for p in PERIODS}})
    t = pd.DataFrame(rel)
    summary["part_b_relative"] = t.to_dict("records")
    out.append("-- VIX relative to its prior 60-session median\n" + t.to_string(index=False) + "\n")

    # Sizing: weights by entry VIX; exposure = sum of weights over traded sessions.
    out.append("-- sizing rules (X1, stressed unless noted; exposure in fly-days)")
    rng = np.random.default_rng(1)
    rows = []
    v = f.vix.to_numpy()
    base_mid = f.gap_held_midpoint.to_numpy()
    base_str = f.gap_held_stressed.to_numpy()
    tr = traded.to_numpy()
    schemes = {
        "flat 1x": np.ones_like(v),
        **{f"skip VIX<{t}": (v >= t).astype(float) for t in (15, 16, 17, 18, 19)},
        **{f"0.5x VIX<{t}": np.where(v < t, 0.5, 1.0) for t in (16, 17, 18)},
        "skip <17 and >25": ((v >= 17) & (v <= 25)).astype(float),
        "0.5x<17, 1.5x 17-25, 1x>25": np.where(v < 17, .5, np.where(v <= 25, 1.5, 1.0)),
    }
    for name, w in schemes.items():
        w = np.nan_to_num(w)
        sm, ss = w * base_mid, w * base_str
        exposure = float(w[tr].sum())
        # Matched-exposure random sizing: same multiset of weights shuffled over trades.
        shuffled = np.array([np.sum(rng.permutation(w[tr]) * base_str[tr])
                             for _ in range(2000)])
        rows.append({
            "scheme": name, "exposure": round(exposure),
            "mid_total": round(sm.sum()), "str_total": round(ss.sum()),
            "str_per_fly": round(ss.sum() / exposure, 1) if exposure else 0,
            **{f"str_{p}": round(ss[(f.period == p).to_numpy()].sum()) for p in PERIODS},
            "str_maxdd": round(max_dd(ss)),
            "random_same_weights_pctile": round(float((shuffled < ss.sum()).mean()), 3),
        })
    t = pd.DataFrame(rows)
    summary["part_b_sizing"] = t.to_dict("records")
    out.append(t.to_string(index=False) + "\n")

    # Year-by-year stability of the VIX>=17 split.
    yr = f[traded].assign(year=f.date_.dt.year, hi=f.vix >= 17)
    t = yr.pivot_table(index="year", columns="hi", values="gap_held_stressed",
                       aggfunc=["sum", "count"]).round(0)
    out.append("-- X1 stressed by year, VIX<17 (False) vs >=17 (True)\n" + t.to_string() + "\n")
    summary["part_b_by_year"] = json.loads(t.to_json())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    f = load()
    lines: list[str] = [f"sessions={len(f)} traded={int((f.gap_held_midpoint != 0).sum())}"]
    summary: dict = {}
    part_a(f, lines, summary)
    part_b(f, lines, summary)
    text = "\n".join(lines)
    (out_dir / "report.txt").write_text(text + "\n")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    f.to_parquet(out_dir / "features.parquet")
    print(text)


if __name__ == "__main__":
    main()
