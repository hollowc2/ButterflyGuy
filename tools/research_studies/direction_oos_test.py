"""Pre-registered out-of-sample test of gap direction, VIX agreement and VIX regime.

Plan: docs/research/spx-direction-vix-oos-preregistration-2026-10-29.md, approved and
committed as 4c72a35 before anything here was computed. Run once; any rerun after a bug
fix must be recorded in the plan as a revision.

- Test A: real SPXW 0DTE options, 2020-01-02 -> 2021-12-31 (dataset
  spx_0dte_local_durable_pre2022_20261029), E0 entry, X1 exit.
- Test B: synthetic settlement payoff on the owner SPX/VIX minute CSVs, 2003-07-01 ->
  2019-12-31.

Reads only offline data; never touches a registry, config or service.
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
from butterfly_guy.research.evaluate import (
    EvalParams,
    block_bootstrap_indices,
    paired_bootstrap,
    trade_metrics,
)
from butterfly_guy.research.features import DailyVol
from butterfly_guy.research.simulate import Variant, run_variants

ROOT = Path(__file__).resolve().parents[2]
PLAN = "docs/research/spx-direction-vix-oos-preregistration-2026-10-29.md"
PLAN_COMMIT = "4c72a35"
DURABLE = ROOT / "reports/thetadata_completion/2026-10-01/thetadata-cache"
DATASET = "spx_0dte_local_durable_pre2022_20261029"
VOL_DAILY = ROOT / "data/research_cache/spx_0dte/aux/vol_index_daily.parquet"
CBOE_SPX = (ROOT / "reports/thetadata_completion/2026-10-01/thetadata-daily/"
            "SPX_778e5f33f32685473b8e2a1cf5c3ab18286589e310ab7140dd014d65241c3e07.csv")
SPX_MIN, VIX_MIN = ROOT / "data/spx_1min.csv", ROOT / "data/vix_1min.csv"
DEFAULT_OUT = ROOT / "reports/research/spx-direction-oos-20261029"
MODELS = ("midpoint", "stressed", "marketable")
EXITS = {"held": (), "trail": "config"}
HIGH_VIX = 17.0
CENTER_EM, WING_EM = 0.93, 0.57
B_START, B_END = dt.date(2003, 7, 1), dt.date(2019, 12, 31)
B_YEARS = range(2004, 2020)
B_REPS, B_BLOCK = 10_000, 5
SQ252 = np.sqrt(252)


# --------------------------------------------------------------------------- Test A
def variants() -> list[Variant]:
    return [Variant(f"{d}_{x}", BaselineEntry(direction=d), rules)
            for d in ("gap", "CALL", "PUT") for x, rules in EXITS.items()]


def chunk(days: list[str]) -> list[dict]:
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    loader = SessionLoader(Dataset.open(DATASET, DURABLE), PROFILES["vendor_1m"])
    ctx = RunContext(load_spx_config())
    vol = DailyVol(pd.read_parquet(VOL_DAILY))
    dates = [dt.date.fromisoformat(d) for d in days]
    res = run_variants(loader, variants(), ctx, start=dates[0], end=dates[-1])
    rows = {}
    for d in res.dates:
        s = loader.load(d)
        lo, _ = ctx.window(d)
        vix = s.vix.at_or_before(lo, max_age_s=ctx.max_vix_age_s)
        prev = max(x for x in loader.closes if x < d)
        rows[d] = {"date": d.isoformat(), "gap_dir": gap_direction(s),
                   "gap": s.open / s.prev_close - 1,
                   "vix10": None if vix is None else vix[0],
                   "vix_prior_close": vol.features(d, prev)["vix_prior_close"]}
    for v, run in res.runs.items():
        for d in run.excluded:
            rows[d][f"excluded_{v}"] = run.excluded[d]
        for t in run.trades:
            for m in MODELS:
                rows[t.date][f"{v}_{m}"] = t.pnl(m)
    return list(rows.values())


def replay_a(out: Path, workers: int) -> pd.DataFrame:
    days = [d.isoformat() for d in
            SessionLoader(Dataset.open(DATASET, DURABLE), PROFILES["vendor_1m"]).dates()]
    jobs = [days[i:i + 30] for i in range(0, len(days), 30)]
    with ProcessPoolExecutor(workers) as pool:
        rows = [r for c in pool.map(chunk, jobs) for r in c]
    frame = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    frame.to_parquet(out / "test_a_sessions.parquet")
    return frame


def agree_flags(gap_call: np.ndarray, overnight: np.ndarray, min_move: float = 0.0):
    """VIX agrees: CALL with VIX down, PUT with VIX up (zero never agrees)."""
    return np.where(gap_call, overnight < -min_move, overnight > min_move)


def money(v: np.ndarray) -> dict:
    m = trade_metrics(v[v != 0])
    return {"total": round(float(v.sum())), "trades": int((v != 0).sum()),
            "max_dd": m.get("max_drawdown")}


def analyze_a(frame: pd.DataFrame) -> dict:
    excluded = frame.filter(like="excluded_").notna().any(axis=1)
    f = frame[~excluded].reset_index(drop=True)
    params = EvalParams()
    is_call = (f.gap_dir == "CALL").to_numpy()
    overnight = (f.vix10 / f.vix_prior_close - 1).to_numpy()
    agree = agree_flags(is_call, overnight)
    high = (f.vix10 >= HIGH_VIX).to_numpy()
    monday = (pd.to_datetime(f.date).dt.weekday == 0).to_numpy()
    year = pd.to_datetime(f.date).dt.year.to_numpy()

    def col(name: str) -> np.ndarray:
        return f[name].fillna(0.0).to_numpy() if name in f else np.zeros(len(f))

    out: dict = {"sessions": len(f), "excluded_by_loader": int(excluded.sum()),
                 "missing_vix_prior": int(f.vix_prior_close.isna().sum()),
                 "agree_days": int(agree.sum()), "high_days": int(high.sum()),
                 "e0_entries": int(f["gap_held_midpoint"].notna().sum()),
                 "e0_entries_low_regime": int((f["gap_held_midpoint"].notna() & ~high).sum())}
    arms_by_exit = {}
    for x in EXITS:
        for m in MODELS:
            call, put, gap = col(f"CALL_{x}_{m}"), col(f"PUT_{x}_{m}"), col(f"gap_{x}_{m}")
            assert np.allclose(gap, np.where(is_call, call, put)), "gap arm != CALL/PUT pick"
            arms_by_exit[(x, m)] = {
                "A0": gap, "A-VA": gap * agree, "A-RG": gap * high,
                "A-CB": gap * (agree & high), "Fade": np.where(is_call, put, call)}
    arms = {m: arms_by_exit[("held", m)] for m in MODELS}
    st, mid = arms["stressed"], arms["midpoint"]
    edge = mid["A0"] - mid["Fade"]

    a1 = paired_bootstrap(st["A-VA"], st["A0"], params)
    a4 = paired_bootstrap(st["A-RG"], st["A0"], params)
    a5 = paired_bootstrap(st["A-CB"], st["A0"], params)
    a4_scored = out["e0_entries_low_regime"] >= 30
    crit = {
        "A1": {"vs_A0": a1, "pass": (a1["p_better"] or 0) >= 0.80},
        "A2": {"edge_mean_agree": round(float(edge[agree].mean()), 2),
               "edge_mean_disagree": round(float(edge[~agree].mean()), 2),
               "pass": bool(edge[agree].mean() > edge[~agree].mean())},
        "A3": {"sum_gap_minus_fade_mid": round(float(edge.sum())),
               "pass": bool(edge.sum() > 0)},
        "A4": {"vs_A0": a4, "scored": a4_scored,
               "pass": (a4["p_better"] or 0) >= 0.80 if a4_scored else None},
        "A5": {"total": round(float(st["A-CB"].sum())), "vs_A0": a5,
               "pass": bool(st["A-CB"].sum() > 0) and (a5["p_better"] or 0) >= 0.80},
    }
    out["criteria"] = crit
    out["arms"] = {f"{x}/{m}": {k: money(v) | {str(y): round(float(v[year == y].sum()))
                                              for y in sorted(set(year))}
                               for k, v in a.items()}
                   for (x, m), a in arms_by_exit.items()}
    out["edge_mid_by_subset"] = {
        "agree": round(float(edge[agree].sum())), "disagree": round(float(edge[~agree].sum())),
        "high": round(float(edge[high].sum())), "low": round(float(edge[~high].sum()))}
    out["x1_stressed_low_regime_total"] = round(float(st["A0"][~high].sum()))

    # Report-only: Mondays excluded; agreement of at least 1%.
    ro = {}
    for name, keep, ag in (
            ("no_monday", ~monday, agree),
            ("agree_ge_1pct", np.ones(len(f), bool), agree_flags(is_call, overnight, 0.01))):
        e = edge[keep]
        va = st["A0"][keep] * ag[keep]
        ro[name] = {"sessions": int(keep.sum()), "agree_days": int(ag[keep].sum()),
                    "A-VA_minus_A0_stressed": round(float(va.sum() - st["A0"][keep].sum())),
                    "A-VA_vs_A0": paired_bootstrap(va, st["A0"][keep], params),
                    "edge_mean_agree": round(float(e[ag[keep]].mean()), 2),
                    "edge_mean_disagree": round(float(e[~ag[keep]].mean()), 2)}
    out["report_only"] = ro
    return out


# --------------------------------------------------------------------------- Test B
def stale_days() -> set[dt.date]:
    src = Dataset.open(DATASET, DURABLE).manifest.source["index_files"]
    return {dt.date.fromisoformat(x) for k in ("SPX", "$VIX")
            for x in src[k]["stale_days_excluded"]}


def minute_frame(path: Path) -> pd.DataFrame:
    m = pd.read_csv(path)
    ts = pd.to_datetime(m.ts)
    m = m.assign(date=ts.dt.date, hm=ts.dt.strftime("%H:%M"))
    return m[(m.date >= B_START) & (m.date <= B_END)]


def build_b() -> tuple[pd.DataFrame, dict]:
    spx, vixm = minute_frame(SPX_MIN), minute_frame(VIX_MIN)
    g = spx[spx.hm >= "08:31"].groupby("date")
    days = pd.DataFrame({"open": g.open.first(), "last_hm": g.hm.max()})
    days["spx10"] = spx[spx.hm == "09:00"].set_index("date").close
    days["vix10"] = vixm[vixm.hm == "09:00"].set_index("date").close
    cboe = pd.read_csv(CBOE_SPX)
    cboe = pd.Series(cboe.SPX.to_numpy(float),
                     index=pd.to_datetime(cboe.DATE, format="%m/%d/%Y").dt.date).sort_index()
    prev_date = pd.Series(cboe.index[:-1], index=cboe.index[1:])
    days["close"] = cboe.reindex(days.index)
    days["prev_date"] = prev_date.reindex(days.index)
    days["prev_close"] = cboe.reindex(days.prev_date).to_numpy()
    vol = DailyVol(pd.read_parquet(VOL_DAILY))
    days["vix_prior_close"] = [
        vol.features(d, p)["vix_prior_close"] if isinstance(p, dt.date) else np.nan
        for d, p in zip(days.index, days.prev_date, strict=True)]
    stale = stale_days()
    reasons = {
        "stale_csv_day": days.index.isin(stale),
        "early_close": days.last_hm < "13:30",
        "missing_10am_bar": days.spx10.isna() | days.vix10.isna(),
        "missing_cboe_close": days.close.isna() | days.prev_close.isna(),
        "missing_vix_prior_close": days.vix_prior_close.isna(),
    }
    drop = np.zeros(len(days), bool)
    counts = {}
    for k, r in reasons.items():
        r = np.asarray(r, bool)
        counts[k] = int((r & ~drop).sum())
        drop |= r
    excl = {"counts": counts,
            "early_close_dates": [str(d) for d in days.index[np.asarray(
                reasons["early_close"], bool)]]}
    d = days[~drop].copy()
    d["is_call"] = d.open >= d.prev_close
    em = d.spx10 * d.vix10 / 100 / SQ252
    w = WING_EM * em

    def payoff(center: pd.Series) -> pd.Series:
        return np.maximum(0.0, 1 - (d.close - center).abs() / w)

    d["p_call"] = payoff(d.spx10 + CENTER_EM * em)
    d["p_put"] = payoff(d.spx10 - CENTER_EM * em)
    d["p_gap"] = np.where(d.is_call, d.p_call, d.p_put)
    d["p_fade"] = np.where(d.is_call, d.p_put, d.p_call)
    d["overnight"] = d.vix10 / d.vix_prior_close - 1
    d["agree"] = agree_flags(d.is_call.to_numpy(), d.overnight.to_numpy())
    d["agree_1pct"] = agree_flags(d.is_call.to_numpy(), d.overnight.to_numpy(), 0.01)
    d["high"] = d.vix10 >= HIGH_VIX
    d["gap"] = d.open / d.prev_close - 1
    idx = pd.to_datetime(pd.Series(d.index, index=d.index))
    d["year"] = idx.dt.year
    d["monday"] = idx.dt.weekday == 0
    return d.reset_index(names="date"), excl


def excess(d: pd.DataFrame, by: list[str]) -> pd.Series:
    """Gap payoff minus its expectation when gap directions are shuffled within
    year x `by` (the stratum's call/put mix is kept)."""
    q = d.groupby(["year", *by]).is_call.transform("mean")
    return d.p_gap - (q * d.p_call + (1 - q) * d.p_put)


def boot_means(x: np.ndarray, seed: int) -> np.ndarray:
    return x[block_bootstrap_indices(len(x), B_REPS, B_BLOCK, seed)].mean(axis=1)


def subset_diff(d: pd.DataFrame, flag: str) -> dict:
    """Mean excess where `flag` is true minus where it is false, strata year x flag."""
    e = excess(d, [flag]).to_numpy()
    on = d[flag].to_numpy(bool)
    a, b = e[on], e[~on]
    diff = boot_means(a, 1) - boot_means(b, 2)
    per_year = {int(y): round(float(e[on & (d.year == y).to_numpy()].mean()
                                    - e[~on & (d.year == y).to_numpy()].mean()), 5)
                for y in sorted(d.year.unique())}
    return {"n_true": int(on.sum()), "n_false": int((~on).sum()),
            "mean_true": round(float(a.mean()), 5), "mean_false": round(float(b.mean()), 5),
            "diff": round(float(a.mean() - b.mean()), 5),
            "ci90": [round(float(q), 5) for q in np.percentile(diff, [5, 95])],
            "p_positive": round(float((diff > 0).mean()), 4), "per_year": per_year}


def analyze_b(d: pd.DataFrame, excl: dict) -> dict:
    out: dict = {"days": len(d), "exclusions": excl, "call_share": round(float(d.is_call.mean()), 4),
                 "agree_share": round(float(d.agree.mean()), 4),
                 "high_share": round(float(d.high.mean()), 4)}
    e_all = excess(d, []).to_numpy()
    b3_boot = boot_means(e_all, 1)
    va = subset_diff(d, "agree")
    rg = subset_diff(d, "high")
    years_pos = sum(1 for y in B_YEARS if va["per_year"].get(y, -1) > 0)
    p_low, p_high = float(d.p_gap[~d.high].mean()), float(d.p_gap[d.high].mean())
    out["criteria"] = {
        "B1": {**{k: va[k] for k in ("n_true", "n_false", "mean_true", "mean_false", "diff",
                                     "ci90", "p_positive")},
               "pass": va["diff"] > 0 and va["p_positive"] >= 0.95},
        "B2": {"years_positive": years_pos, "of": len(B_YEARS),
               "per_year": {y: va["per_year"][y] for y in B_YEARS if y in va["per_year"]},
               "pass": years_pos >= 10},
        "B3": {"mean_excess": round(float(e_all.mean()), 5),
               "ci90": [round(float(q), 5) for q in np.percentile(b3_boot, [5, 95])],
               "p_positive": round(float((b3_boot > 0).mean()), 4),
               "mean_p_gap": round(float(d.p_gap.mean()), 5),
               "mean_p_fade": round(float(d.p_fade.mean()), 5),
               "pass": bool(e_all.mean() > 0 and (b3_boot > 0).mean() >= 0.95)},
        "B4": {**{k: rg[k] for k in ("n_true", "n_false", "mean_true", "mean_false", "diff",
                                     "ci90", "p_positive")},
               "pass": rg["diff"] > 0 and rg["p_positive"] >= 0.90},
        "B5": {"mean_p_gap_low": round(p_low, 5), "mean_p_gap_high": round(p_high, 5),
               "pass": p_low < p_high},
    }
    out["regime_per_year"] = rg["per_year"]
    out["excess_by_year"] = {int(y): round(float(e_all[(d.year == y).to_numpy()].mean()), 5)
                             for y in sorted(d.year.unique())}
    # Report-only cuts.
    ro = {"no_monday": subset_diff(d[~d.monday].reset_index(drop=True), "agree"),
          "agree_ge_1pct": subset_diff(d, "agree_1pct")}
    for name, r in ro.items():
        r["years_positive"] = sum(1 for y in B_YEARS if r["per_year"].get(y, -1) > 0)
    zones = pd.cut(d.vix10, [0, 17, 24.5, 32, 999]).astype(str)
    gaps = pd.cut(d.gap.abs(), [0, .001, .0025, .005, .01, 1], include_lowest=True).astype(str)
    for name, b in (("by_vix_zone", zones), ("by_abs_gap", gaps)):
        dd = d.assign(bucket=b)
        e = excess(dd, ["bucket"])
        ro[name] = {k: {"n": int(len(g)), "mean_excess": round(float(e[g.index].mean()), 5),
                        "mean_p_gap": round(float(g.p_gap.mean()), 5)}
                    for k, g in dd.groupby("bucket")}
    out["report_only"] = ro
    return out


# --------------------------------------------------------------------------- verdict
def verdict(a: dict, b: dict) -> dict:
    ca, cb = a["criteria"], b["criteria"]
    va = all([ca["A1"]["pass"], ca["A2"]["pass"], cb["B1"]["pass"], cb["B2"]["pass"]])
    gd = ca["A3"]["pass"] and cb["B3"]["pass"]
    rg_parts = [cb["B4"]["pass"], cb["B5"]["pass"]]
    if ca["A4"]["scored"]:
        rg_parts.append(ca["A4"]["pass"])
    rg = all(rg_parts)
    cb_ = ca["A5"]["pass"]
    if not va:
        decision = "H-VA1 failed: VIX agreement is dropped; no report-only cut is promoted."
    elif not gd:
        decision = "H-VA1 passed but H-GD1 failed: contradiction; no forward test until understood."
    elif rg and cb_:
        decision = "Forward test (paper shadow) of the combined rule: VIX >= 17 and VIX agrees."
    else:
        decision = "Forward test (paper shadow) of 'trade the gap only when VIX agrees'."
    return {"H-VA1": va, "H-GD1": gd, "H-RG1": rg, "H-CB1": cb_, "decision": decision}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    a = analyze_a(replay_a(out, args.workers))
    days, excl = build_b()
    days.to_parquet(out / "test_b_days.parquet")
    b = analyze_b(days, excl)
    result = {"plan": PLAN, "plan_commit": PLAN_COMMIT, "dataset": DATASET,
              "dataset_hash": Dataset.open(DATASET, DURABLE).hash,
              "run_at": dt.datetime.now(dt.UTC).isoformat(),
              "test_a": a, "test_b": b, "verdict": verdict(a, b)}
    (out / "results.json").write_text(json.dumps(result, indent=1, default=str) + "\n")
    print(json.dumps(result["verdict"], indent=1))


if __name__ == "__main__":
    main()
