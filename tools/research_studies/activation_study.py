"""Retrospective activation-filter study over frozen canonical E0/X1 replays.

Run after the three research-core commands in the dated study plan. Reads only
offline normalized inputs; never changes a dataset, registry, or runtime config.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.entry import PROFILES, SessionLoader
from butterfly_guy.research.evaluate import EvalParams, paired_bootstrap, trade_metrics
from butterfly_guy.research.exits import HELD
from butterfly_guy.research.features import SessionFeatures
from butterfly_guy.research.market import Fly, et_us
from butterfly_guy.strategy.butterfly_builder import vix_expected_move

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "reports/thetadata_completion/2026-10-01/thetadata-cache"
DEFAULT_OUT = ROOT / "reports/research/spx-activation-20261018"
NAMES = (
    "spx_0dte_local_durable_development_20261001",
    "spx_0dte_local_durable_spent_holdout_20261003",
    "spx_0dte_local_durable_validation_20261001",
)
MODELS = ("midpoint", "marketable", "stressed", "stressed_delayed", "stressed_floor")
# Each tuple is (identifier, feature, comparator, threshold). True means skip.
RULES = (
    ("low_vix", "vix", "lt", 17),
    ("high_vix", "vix", "ge", 24.5),
    ("chaos_vix", "vix", "ge", 32),
    ("backwardation", "vix_vix3m_prior", "ge", 1),
    ("one_day_premium", "vix1d_vix_prior", "ge", 1),
    ("small_gap", "abs_gap", "lt", .0025),
    ("large_gap", "abs_gap", "ge", .01),
    ("opening_reversal", "opening_reversal", "ge", 1),
    ("quiet_open", "opening_range_sigma", "lt", .25),
    ("fast_open", "opening_range_sigma", "ge", .75),
    ("vix_chain_mismatch", "vix_chain_ratio", "ge", 1.25),
    ("wide_spread", "spread_ratio", "ge", .20),
    ("early_release", "early_release", "ge", 1),
    ("fomc", "fomc", "ge", 1),
    ("losing_20", "prior20_pnl", "lt", 0),
    ("underwater_5000", "prior_dd", "ge", 5000),
)
NEIGHBORS = (
    ("low_vix_16", "vix", "lt", 16), ("low_vix_18", "vix", "lt", 18),
    ("large_gap_075", "abs_gap", "ge", .0075),
    ("large_gap_125", "abs_gap", "ge", .0125),
    ("spread_015", "spread_ratio", "ge", .15),
    ("spread_025", "spread_ratio", "ge", .25),
    ("mismatch_110", "vix_chain_ratio", "ge", 1.1),
    ("mismatch_140", "vix_chain_ratio", "ge", 1.4),
    ("underwater_2500", "prior_dd", "ge", 2500),
    ("underwater_7500", "prior_dd", "ge", 7500),
)


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False) + "\n")


def skip_mask(frame: pd.DataFrame, rule: tuple) -> np.ndarray:
    _, feature, op, level = rule
    x = frame[feature]
    return ((x < level) if op == "lt" else (x >= level)).fillna(False).to_numpy(bool)


def add_history(frame: pd.DataFrame) -> pd.DataFrame:
    """Shadow E0 history, strictly before each date, reset across input gaps >7 days.

    A filter keeps observing the virtual baseline while paused. This avoids the
    absorbing state of a cooldown that can never recover while it is switched off.
    """
    frame = frame.copy()
    groups = pd.to_datetime(frame.date).diff().dt.days.gt(7).cumsum()
    for _, ix in frame.groupby(groups).groups.items():
        pnl = frame.loc[ix, "stressed"].fillna(0)
        prior_eq = pnl.cumsum().shift(1, fill_value=0)
        frame.loc[ix, "prior_dd"] = prior_eq.cummax().clip(lower=0) - prior_eq
        frame.loc[ix, "prior20_pnl"] = pnl.shift(1).rolling(20, min_periods=20).sum()
    return frame


def load_rows(out: Path) -> tuple[pd.DataFrame, list[dict]]:
    aux = Dataset.open("spx_0dte", CACHE)
    features = SessionFeatures.load(aux)
    rows, provenance = [], []
    for name in NAMES:
        ds = Dataset.open(name, CACHE)
        errors = ds.verify()
        if errors:
            raise ValueError(errors)
        runs = list((out / "replays" / name).glob("*/trades.jsonl"))
        if len(runs) != 1:
            raise ValueError(f"Expected one frozen replay for {name}: {runs}")
        trades_path = runs[0]
        records = [json.loads(line) for line in trades_path.read_text().splitlines()]
        by_variant = {v: {t["date"]: t for t in records if t["variant"] == v}
                      for v in ("E0", "X1")}
        result = json.loads((trades_path.parent / "results.json").read_text())
        if result["evaluation"]["dropped_sessions"] or result["evaluation"]["skipped_sessions"]:
            raise ValueError("Replay exclusions require explicit reconciliation")
        loader = SessionLoader(ds, PROFILES["vendor_1m"])
        daily = ds.daily_bars()
        local_features = replace(features, spx_sessions=np.array(sorted(
            daily.loc[daily.underlying == "SPX", "date"])))
        provenance.append({"dataset": name, "dataset_hash": ds.hash,
                           "verified_errors": errors, "sessions": len(loader.dates()),
                           "replay": str(trades_path.parent),
                           "trades_sha256": hashlib.sha256(trades_path.read_bytes()).hexdigest(),
                           "config_sha256": result["meta"]["config_sha256"]})
        for d in loader.dates():
            s = loader.load(d)
            if s is None:
                raise ValueError(f"Previously scored session unavailable: {d}")
            day = d.isoformat()
            t, held = by_variant["E0"].get(day), by_variant["X1"].get(day)
            row = {"date": day, "dataset": name, "traded": t is not None,
                   "gap": s.open / s.prev_close - 1,
                   "abs_gap": abs(s.open / s.prev_close - 1),
                   **local_features.term_structure(d)}
            events = features.calendar.events_for(d)
            row.update(events=list(features.events(d)), fomc="FOMC" in features.events(d),
                       early_release=any(e.event_type in ("CPI", "NFP", "PCE")
                                         and e.before(dt.time(10)) for e in events))
            ts10 = et_us(d, 10, 0)
            i = s.market.at_or_before(ts10)
            k = s.clock_index(ts10)
            if i < 0 or k < 0 or ts10 - int(s.market.ts[i]) > 120_000_000:
                raise ValueError(f"Missing fresh opening anchor: {day}")
            spot10 = float(s.clock_spot[k])
            straddle = s.market.atm_straddle(i)
            sigma = 1.25 * straddle if straddle and straddle > 0 else None
            opening = s.clock_spot[(s.clock_ts >= et_us(d, 9, 30)) &
                                   (s.clock_ts <= ts10)]
            row["opening_reversal"] = int((spot10 - s.open) * (s.open - s.prev_close) < 0)
            row["opening_range_sigma"] = (float(np.ptp(np.r_[s.open, opening])) / sigma
                                          if sigma is not None else None)
            # Future close is DESCRIPTIVE ONLY and never used by any mask.
            row["realized_move_sigma"] = ((s.close - spot10) / sigma
                                           if sigma and s.close is not None else None)
            row["vix_chain_ratio"] = None
            row["vix"] = None
            row["spread_ratio"] = None
            for m in MODELS:
                row[m] = 0.0
            row.update(x1_stressed=0.0, x1_midpoint=0.0, fly_minutes=0.0,
                       debit_dollars=0.0, max_loss_r=None, direction=None)
            if t is not None:
                for m in MODELS[:-1]:
                    if t[m]["pnl"] is None:
                        raise ValueError(f"Unpriced {m} trade {day}")
                    row[m] = t[m]["pnl"]
                row["stressed_floor"] = row["stressed"]
                if t["exit_reason"] != HELD and not t["stressed"]["settlement_fallback"]:
                    row["stressed_floor"] += max(0, -t["stressed"]["exit"]) * 100
                entry_us = int(dt.datetime.fromisoformat(t["entry_time"]).timestamp() * 1e6)
                if entry_us < ts10:
                    raise ValueError("Opening features were unavailable at entry")
                j = s.market.at_or_before(entry_us)
                fly = Fly(t["direction"], t["lower"], t["center"], t["upper"])
                path = s.market.fly_path(fly)
                row.update(vix=t["vix"], direction=t["direction"],
                           entry_time=t["entry_time"], exit_time=t["exit_time"],
                           exit_reason=t["exit_reason"], entry_cost=t["entry_cost"],
                           center=t["center"], width=t["width"])
                row["spread_ratio"] = float((path.debit[j] - t["entry_cost"]) / t["entry_cost"])
                entry_straddle = s.market.atm_straddle(j)
                if entry_straddle and entry_straddle > 0:
                    row["vix_chain_ratio"] = vix_expected_move(t["vix"], t["spot"]) / (1.25 * entry_straddle)
                # Exit timestamp is the simulator decision or scheduled settlement cutoff.
                exit_us = (int(dt.datetime.fromisoformat(t["exit_time"]).timestamp() * 1e6)
                           if t["exit_time"] else et_us(d, s.scheduled_close.hour,
                                                       s.scheduled_close.minute))
                row["fly_minutes"] = (exit_us - entry_us) / 60e6
                row["debit_dollars"] = 100 * t["stressed"]["entry"]
                row["max_loss_r"] = row["stressed"] / row["debit_dollars"]
                for model in ("stressed", "midpoint"):
                    row[f"x1_{model}"] = held[model]["pnl"]
            rows.append(row)
        print(f"features complete: {name}", flush=True)
    frame = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    if frame.date.duplicated().any():
        raise ValueError("Overlapping datasets")
    dump(out / "feature-inputs.json", features.inputs)
    return add_history(frame), provenance


def summary(frame: pd.DataFrame, keep: np.ndarray, model: str = "stressed") -> dict:
    actual = keep & frame.traded.to_numpy(bool)
    pnl = frame[model].to_numpy(float)[actual]
    m = trade_metrics(pnl)
    base = frame[model].to_numpy(float)
    skipped = ~keep & frame.traded.to_numpy(bool)
    winning = np.maximum(base, 0)
    losing = np.maximum(-base, 0)
    winners = np.flatnonzero(base > 0)
    top = winners[np.argsort(base[winners])[-10:]]
    m.update(sessions=len(frame), kept_trades=int(actual.sum()), skipped_trades=int(skipped.sum()),
             net=round(float(pnl.sum()), 2),
             gross_wins_retained_pct=round(100 * winning[keep].sum() / winning.sum(), 1)
             if winning.sum() else None,
             losses_avoided=round(float(losing[skipped].sum()), 2),
             winning_dollars_missed=round(float(winning[skipped].sum()), 2),
             top10_retained=int(keep[top].sum()), top10_available=len(top),
             avg_win=round(float(pnl[pnl > 0].mean()), 2) if (pnl > 0).any() else None,
             avg_loss=round(float(pnl[pnl < 0].mean()), 2) if (pnl < 0).any() else None,
             net_diff=round(float(pnl.sum() - base.sum()), 2),
             exposure_minutes=round(float(frame.loc[actual, "fly_minutes"].sum()), 1),
             expectancy_r=round(float(frame.loc[actual, "max_loss_r"].mean()), 4)
             if actual.any() else None,
             cost_drag_vs_midpoint=round(float(frame.loc[actual, "midpoint"].sum() - pnl.sum()), 2))
    return m


def eligible(frame: pd.DataFrame, rule: tuple, split: str | None = None) -> bool:
    keep = ~skip_mask(frame, rule)
    base = summary(frame, np.ones(len(frame), dtype=bool))
    m = summary(frame, keep)
    if not m.get("max_drawdown") or not base.get("max_drawdown"):
        return False
    halves = ([np.flatnonzero((frame.date <= split).to_numpy()),
               np.flatnonzero((frame.date > split).to_numpy())] if split else
              [np.arange(len(frame))[:len(frame)//2],
               np.arange(len(frame))[len(frame)//2:]])
    return (m["net"] > 0 and m["max_drawdown"] <= .8 * base["max_drawdown"]
            and (m["gross_wins_retained_pct"] or 0) >= 80 and m["top10_retained"] >= 8
            and all(summary(frame.loc[ix], keep[ix])["net_diff"] > 0
                    for ix in halves if len(ix)))


def analyze(frame: pd.DataFrame, out: Path) -> dict:
    all_keep = np.ones(len(frame), dtype=bool)
    periods = {"all": all_keep,
               "development": (frame.date <= "2024-06-28").to_numpy(),
               "later": (frame.date >= "2024-07-01").to_numpy()}
    for year in (2022, 2023, 2024, 2025, 2026):
        periods[str(year)] = frame.date.str.startswith(str(year)).to_numpy()
    for start, end, label in (("2024-07-01", "2024-12-31", "2024H2"),
                              ("2025-01-01", "2025-06-30", "2025H1"),
                              ("2025-07-01", "2025-12-31", "2025H2")):
        periods[label] = ((frame.date >= start) & (frame.date <= end)).to_numpy()
    rules = []
    base = frame.stressed.to_numpy(float)
    params = EvalParams(bootstrap_block=10, bootstrap_reps=5000)
    rng = np.random.default_rng(20261018)
    trade_pnl = base[frame.traded.to_numpy(bool)]
    for rule in (*RULES, *NEIGHBORS):
        name, feature, op, threshold = rule
        keep = ~skip_mask(frame, rule)
        vec = np.where(keep, base, 0)
        m = {"name": name, "feature": feature, "op": op, "threshold": threshold,
             "primary": rule in RULES,
             "missing_trade_features": int((frame[feature].isna() & frame.traded).sum()),
             "periods": {p: summary(frame.loc[ix], keep[ix]) for p, ix in periods.items()},
             "models": {model: summary(frame, keep, model) for model in MODELS}}
        m["bootstrap"] = paired_bootstrap(vec, base, params)
        n = m["periods"]["all"]["skipped_trades"]
        random_delta = np.array([-rng.choice(trade_pnl, n, replace=False).sum()
                                 for _ in range(5000)])
        m["random_skip"] = {"mean_delta": round(float(random_delta.mean()), 2),
                            "share_at_least_observed": round(float(
                                (random_delta >= m["periods"]["all"]["net_diff"]).mean()), 4),
                            "ci90_delta": np.percentile(random_delta, [5, 50, 95]).round(2).tolist()}
        dev = frame.loc[periods["development"]].reset_index(drop=True)
        m["development_eligible"] = eligible(dev, rule, "2023-03-31")
        rules.append(m)
    candidates = [r for r in rules if r["primary"] and r["development_eligible"]]
    selected = max(candidates, key=lambda r: r["periods"]["development"]["net"])["name"] if candidates else "E0"
    walk = []
    for start, end in (("2023-01-01", "2023-06-30"), ("2023-07-01", "2023-12-31"),
                       ("2024-01-01", "2024-06-30"), ("2024-07-01", "2024-12-31"),
                       ("2025-01-01", "2025-06-30"), ("2025-07-01", "2025-12-31"),
                       ("2026-01-01", "2026-09-25")):
        train = frame.loc[frame.date < start].reset_index(drop=True)
        test = frame.loc[(frame.date >= start) & (frame.date <= end)].reset_index(drop=True)
        if len(train) < 200 or test.empty:
            continue
        qualified = [r for r in RULES if eligible(train, r)]
        chosen = max(qualified, key=lambda r: summary(train, ~skip_mask(train, r))["net"]) if qualified else None
        keep = ~skip_mask(test, chosen) if chosen else np.ones(len(test), bool)
        walk.append({"start": start, "end": end, "training_sessions": len(train),
                     "selected": chosen[0] if chosen else "E0", "result": summary(test, keep)})
    # Descriptive strata are deliberately separate from causal activation rules.
    groups = {}
    for column, bins in (("vix", [-np.inf, 17, 24.5, 32, np.inf]),
                         ("realized_move_sigma", [-np.inf, -2, -1, 0, 1, 2, np.inf])):
        groups[column] = {}
        for category, g in frame.groupby(pd.cut(frame[column], bins, right=False), observed=True):
            groups[column][str(category)] = summary(g, np.ones(len(g), bool))
    for label, ids in (("weekday", pd.to_datetime(frame.date).dt.day_name()),
                       ("month", frame.date.str[:7]), ("direction", frame.direction)):
        groups[label] = {str(k): summary(g, np.ones(len(g), bool))
                         for k, g in frame.groupby(ids, observed=True)}
    curve = np.cumsum(base)
    peaks = np.maximum.accumulate(np.r_[0, curve])[1:]
    end_ix = int(np.argmax(peaks - curve))
    prior = np.r_[0, curve[:end_ix + 1]]
    peak_ix = int(np.argmax(prior)) - 1
    drawdown = {"peak_date": frame.iloc[peak_ix].date if peak_ix >= 0 else "initial zero",
                "trough_date": frame.iloc[end_ix].date,
                "depth": round(float(peaks[end_ix] - curve[end_ix]), 2),
                "sessions_peak_to_trough": end_ix - peak_ix}
    top = frame.loc[frame.traded].nlargest(10, "stressed")
    top_rows = top[["date", "direction", "vix", "stressed", "realized_move_sigma"]].to_dict("records")
    for r in top_rows:
        one = frame.loc[frame.date == r["date"]]
        r["skipped_by"] = [rule[0] for rule in RULES if skip_mask(one, rule)[0]]
    metrics = {"baseline": {p: summary(frame.loc[ix], all_keep[ix]) for p, ix in periods.items()},
               "baseline_models": {m: summary(frame, all_keep, m) for m in MODELS},
               "rules": rules, "selected_on_development": selected, "walk_forward": walk,
               "groups": groups, "max_drawdown_episode": drawdown, "top_winners": top_rows,
               "x1": {p: trade_metrics(frame.loc[ix & frame.traded, "x1_stressed"].to_numpy())
                       for p, ix in periods.items()},
               "coverage": {"eligible_sessions": len(frame), "trades": int(frame.traded.sum()),
                            "first": frame.date.min(), "last": frame.date.max()},
               "note": "All history retrospective. Bootstrap and random-skip summaries unadjusted exploratory comparisons."
               }
    dump(out / "summary.json", metrics)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--reuse-features", action="store_true")
    args = parser.parse_args()
    out = args.out
    if not (out / "plan.json").exists():
        raise ValueError("Freeze plan.json before analysis")
    if args.reuse_features:
        frame = pd.read_json(out / "sessions.jsonl", lines=True, convert_dates=False)
    else:
        frame, provenance = load_rows(out)
        frame.to_json(out / "sessions.jsonl", orient="records", lines=True, double_precision=12)
        dump(out / "dataset-verification.json", provenance)
    m = analyze(frame, out)
    print(json.dumps({"coverage": m["coverage"], "baseline": m["baseline"]["all"],
                      "development_selected": m["selected_on_development"],
                      "drawdown": m["max_drawdown_episode"]}, indent=2))


if __name__ == "__main__":
    main()
