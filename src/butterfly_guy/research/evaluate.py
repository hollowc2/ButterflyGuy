"""Session-level, paired and noise-aware evaluation.

Every arm is scored on the same evaluated sessions, with zero P&L on sessions it did not
trade (a session with several trades counts their sum). Comparisons against the baseline
use paired per-session differences and a moving day-block bootstrap in which one draw of
session indices is applied to both arms; below `min_bootstrap_sessions` the interval is
not reported. A fitted rule's sessions inside its fit window are in-sample; its figures
after the window are reported separately.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter
from dataclasses import dataclass

import numpy as np

from butterfly_guy.research.accounting import MODELS, Model
from butterfly_guy.research.simulate import RunResult, Trade

PRIMARY: Model = "stressed"


@dataclass(frozen=True)
class EvalParams:
    split: dt.date = dt.date(2026, 6, 18)  # H1 = sessions on or before this date
    bootstrap_reps: int = 5000
    bootstrap_block: int = 5
    bootstrap_seed: int = 1
    rolling_block: int = 20
    min_bootstrap_sessions: int = 20

    def as_dict(self) -> dict:
        return {"split": self.split.isoformat(), "bootstrap_reps": self.bootstrap_reps,
                "bootstrap_block": self.bootstrap_block, "bootstrap_seed": self.bootstrap_seed,
                "rolling_block": self.rolling_block,
                "min_bootstrap_sessions": self.min_bootstrap_sessions}


def block_bootstrap_indices(n: int, reps: int, block: int, seed: int) -> np.ndarray:
    """(reps, n) session indices from a moving-block bootstrap of consecutive sessions."""
    if n == 0:
        return np.zeros((reps, 0), dtype=int)
    block = max(1, min(block, n))
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(reps, n_blocks))
    return (starts[:, :, None] + np.arange(block)).reshape(reps, -1)[:, :n]


def paired_bootstrap(
    arm: np.ndarray, base: np.ndarray, params: EvalParams
) -> dict[str, object]:
    """Bootstrap the total of (arm - base) with one index draw applied to both arms."""
    if arm.shape != base.shape:
        raise ValueError("paired arms must cover the same sessions")
    if len(arm) < params.min_bootstrap_sessions:
        return {"ci90": None, "p_better": None}
    idx = block_bootstrap_indices(len(arm), params.bootstrap_reps, params.bootstrap_block,
                                  params.bootstrap_seed)
    totals = arm[idx].sum(axis=1) - base[idx].sum(axis=1)
    lo, med, hi = np.percentile(totals, [5, 50, 95]) if len(arm) else (0.0, 0.0, 0.0)
    return {"ci90": [round(float(lo), 2), round(float(med), 2), round(float(hi), 2)],
            "p_better": round(float((totals > 0).mean()), 4)}


def session_vector(trades: list[Trade], dates: list[dt.date], model: Model) -> np.ndarray:
    """Per-session P&L in dollars; zero where the arm did not trade or was unpriced."""
    pos = {d: i for i, d in enumerate(dates)}
    out = np.zeros(len(dates))
    for t in trades:
        p = t.pnl(model)
        if p is not None and t.date in pos:
            out[pos[t.date]] += p
    return out


def trade_metrics(pnls: np.ndarray) -> dict[str, object]:
    if len(pnls) == 0:
        return {"n": 0}
    eq = np.concatenate([[0.0], np.cumsum(pnls)])
    wins, losses = pnls[pnls > 0], pnls[pnls < 0]
    gross_w, gross_l = float(wins.sum()), float(-losses.sum())
    top3 = np.sort(pnls)[-3:]
    return {
        "n": int(len(pnls)),
        "net": round(float(pnls.sum()), 2),
        "expectancy": round(float(pnls.mean()), 2),
        "profit_factor": round(gross_w / gross_l, 3) if gross_l > 0 else None,
        "win_rate": round(100 * len(wins) / len(pnls), 1),
        "median": round(float(np.median(pnls)), 2),
        "max_drawdown": round(float(np.max(np.maximum.accumulate(eq) - eq)), 2),
        "top3_share": round(100 * float(np.sort(wins)[-3:].sum()) / gross_w, 1)
        if gross_w > 0 else None,
        "net_without_top3": round(float(pnls.sum() - top3[top3 > 0].sum()), 2),
    }


def common_dates(result: RunResult, names: list[str]) -> tuple[list[dt.date], dict]:
    """Evaluated sessions minus any session a compared arm had to exclude for data."""
    dropped = {}
    for name in names:
        for d, why in result.runs[name].excluded.items():
            dropped.setdefault(d, f"{name}:{why}")
    return [d for d in result.dates if d not in dropped], dropped


def evaluate_arm(
    trades: list[Trade], dates: list[dt.date], params: EvalParams,
    base_vectors: dict[str, np.ndarray] | None,
    fit_window: tuple[dt.date, dt.date] | None = None,
) -> dict[str, object]:
    in_dates = set(dates)
    trades = [t for t in trades if t.date in in_dates]
    out: dict[str, object] = {}
    h1 = np.array([d <= params.split for d in dates], dtype=bool)
    after_fit = None if fit_window is None else np.array([d > fit_window[1] for d in dates],
                                                         dtype=bool)
    for model in MODELS:
        priced = [t for t in trades if t.pnl(model) is not None]
        pnls = np.array([t.pnl(model) for t in priced])
        vec = session_vector(trades, dates, model)
        m = trade_metrics(pnls)
        m["per_session"] = round(float(vec.mean()), 2) if len(vec) else None
        m["unpriced"] = len(trades) - len(priced)
        m["h1_net"] = round(float(vec[h1].sum()), 2)
        m["h2_net"] = round(float(vec[~h1].sum()), 2)
        m["h1_n"] = sum(1 for t in priced if t.date <= params.split)
        m["h2_n"] = sum(1 for t in priced if t.date > params.split)
        b = params.rolling_block
        m["rolling_net"] = [round(float(vec[i:i + b].sum()), 2) for i in range(0, len(vec), b)]
        if after_fit is not None:
            m["after_fit_net"] = round(float(vec[after_fit].sum()), 2)
        if model == PRIMARY:
            debit = sum(t.stressed_debit() or 0.0 for t in priced)
            m["return_on_stressed_debit_pct"] = round(100 * float(pnls.sum()) / debit, 1) \
                if debit else None
        if base_vectors is not None:
            base = base_vectors[model]
            diff = vec - base
            m["vs_baseline"] = {
                "net_diff": round(float(diff.sum()), 2),
                "h1_diff": round(float(diff[h1].sum()), 2),
                "h2_diff": round(float(diff[~h1].sum()), 2),
                "rolling_diff": [round(float(diff[i:i + b].sum()), 2)
                                 for i in range(0, len(diff), b)],
                **paired_bootstrap(vec, base, params),
            }
            if after_fit is not None:
                m["vs_baseline"]["after_fit_diff"] = round(float(diff[after_fit].sum()), 2)
        out[model] = m
    out["exits"] = dict(sorted(Counter(t.exit_reason for t in trades).items()))
    out["exit_rolls"] = sum(t.fills.fills["stressed"].exit_roll > 0 for t in trades)
    out["settlement_fallbacks"] = sum(
        t.fills.fills["stressed"].settlement_fallback for t in trades)
    out["directions"] = dict(sorted(Counter(t.fly.direction for t in trades).items()))
    if fit_window is not None:
        out["fit_window"] = [fit_window[0].isoformat(), fit_window[1].isoformat()]
        out["sessions_in_fit_window"] = int(len(dates) - after_fit.sum())
    return out


def evaluate(result: RunResult, baseline: str, params: EvalParams,
             only: list[dt.date] | None = None) -> dict[str, object]:
    """Score every arm; `only` limits scoring to those sessions (the cohort shadow)."""
    names = list(result.runs)
    dates, dropped = common_dates(result, names)
    skipped = result.skipped
    if only is not None:
        keep = set(only)
        dates = [d for d in dates if d in keep]
        dropped = {d: why for d, why in dropped.items() if d in keep}
        skipped = {d: why for d, why in skipped.items() if d in keep}
    base_trades = result.runs[baseline].trades
    base_vectors = {m: session_vector(
        [t for t in base_trades if t.date in set(dates)], dates, m) for m in MODELS}
    arms = {}
    for name, run in result.runs.items():
        arms[name] = evaluate_arm(run.trades, dates, params,
                                  None if name == baseline else base_vectors,
                                  run.variant.fit_window)
    return {
        "sessions": len(dates),
        "first": dates[0].isoformat() if dates else None,
        "last": dates[-1].isoformat() if dates else None,
        "h1_sessions": sum(d <= params.split for d in dates),
        "h2_sessions": sum(d > params.split for d in dates),
        "dropped_sessions": {d.isoformat(): why for d, why in sorted(dropped.items())},
        "skipped_sessions": {d.isoformat(): why for d, why in sorted(skipped.items())},
        "arms": arms,
    }
