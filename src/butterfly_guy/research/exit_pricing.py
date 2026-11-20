"""Exit order pricing study: ladder rules, fill models and the pre-registered decision.

Pre-registered in docs/research/exit-ladder-pricing-plan.md (owner-approved 2026-11-16).
Each candidate rule is replayed over the fly quote path after an exit signal. Step `i` is
submitted at `i x interval` seconds, priced by `core.exit_pricing.exit_limit` (the function
live execution uses) from the medians of the last three quotes seen at submission, and rests
until the next step. A fill is always at the limit:

- `touch`: fills only when an observed fly bid reaches the limit;
- `mid50` / `mid100`: fills for certain when a bid reaches it, otherwise with probability p
  (once per step) when an observed mid, rounded to a valid credit, reaches it.

Expected credit is exact over step outcomes; whatever is still unfilled at the horizon is
valued at the fly bid there (no fill at all, then cross).
"""

from __future__ import annotations

import dataclasses
import statistics
from collections import deque
from collections.abc import Sequence

import numpy as np
import pandas as pd

from butterfly_guy.core.entry_pricing import round_credit_limit
from butterfly_guy.core.exit_pricing import exit_limit
from butterfly_guy.research.evaluate import block_bootstrap_indices

LADDER_STEP, LADDER_STEPS, ANCHOR_WINDOW = 0.10, 4, 3  # configs/config.yaml, order_manager
EPS = 1e-9


@dataclasses.dataclass(frozen=True)
class Candidate:
    rule: str
    interval: float  # seconds between submissions


CANDIDATES: dict[str, Candidate] = {
    "R0": Candidate("bid_ladder", 20.0),
    "R2": Candidate("mid_capped_ladder", 20.0),
    "R3": Candidate("mid_walk", 20.0),
    "R1": Candidate("mid_walk", 10.0),
}
PREFERENCE = ("R2", "R3", "R1")  # smaller change first, for ties within $1
FILL_MODELS: dict[str, float] = {"touch": 0.0, "mid50": 0.5, "mid100": 1.0}  # p at mid
PRIMARY_MODEL = "mid50"


@dataclasses.dataclass(frozen=True)
class Path:
    """Fly quotes after the signal: seconds since the signal (t[0] == 0), bid and mid."""

    t: np.ndarray
    bid: np.ndarray
    mid: np.ndarray

    def asof(self, t: float) -> int:
        return max(0, int(np.searchsorted(self.t, t + EPS, side="right")) - 1)


@dataclasses.dataclass(frozen=True)
class Outcome:
    expected_credit: float  # fly points
    p_filled: float  # probability of a fill before the horizon
    expected_fill_seconds: float | None  # conditional on a fill
    limits: tuple[float, ...]


def simulate(
    path: Path, candidate: Candidate, p_mid: float, *, horizon: float, underlying: str = "SPX"
) -> Outcome:
    bids: deque[float] = deque(maxlen=ANCHOR_WINDOW)
    mids: deque[float] = deque(maxlen=ANCHOR_WINDOW)
    surv, credit, fill_time = 1.0, 0.0, 0.0
    limits: list[float] = []
    step, t_i = 0, 0.0
    while t_i < horizon - EPS:
        j = path.asof(t_i)
        bids.append(float(path.bid[j]))
        mids.append(float(path.mid[j]))
        limit = exit_limit(
            candidate.rule, step, statistics.median(bids), statistics.median(mids),
            ladder_step=LADDER_STEP, ladder_steps=LADDER_STEPS, underlying=underlying,
        )
        limits.append(limit)
        t_next = min(t_i + candidate.interval, horizon)
        window = [j, *np.nonzero((path.t > t_i + EPS) & (path.t < t_next - EPS))[0]]
        q, t_fill = 0.0, None
        for k in window:
            at = max(t_i, float(path.t[k]))
            if path.bid[k] >= limit - EPS:
                if q == 0.0:
                    t_fill = at
                q = 1.0
                break
            if q == 0.0 and p_mid > 0 and round_credit_limit(
                float(path.mid[k]), underlying
            ) >= limit - EPS:
                q, t_fill = p_mid, at
        if q > 0:
            credit += surv * q * limit
            fill_time += surv * q * (t_fill or t_i)
            surv *= 1.0 - q
        step, t_i = step + 1, t_next
    filled = 1.0 - surv
    credit += surv * float(path.bid[path.asof(horizon)])
    return Outcome(
        expected_credit=credit,
        p_filled=filled,
        expected_fill_seconds=fill_time / filled if filled > 0 else None,
        limits=tuple(limits),
    )


# --------------------------------------------------------------------------- data shaping


def fly_quotes(legs: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    """Per poll fly bid/ask/mid from leg rows (trade_id, ts, strike, bid, ask[, drawdown_pct]).

    Polls missing a leg are dropped.
    """
    t = trades.set_index("id")[["lower_strike", "center_strike", "upper_strike"]].astype(float)
    df = legs.join(t, on="trade_id")
    df["strike"] = df.strike.astype(float)
    role = np.select(
        [df.strike == df.lower_strike, df.strike == df.center_strike,
         df.strike == df.upper_strike], ["lo", "ce", "up"], "")
    df = df[role != ""].assign(role=role[role != ""])
    wide = df.pivot_table(index=["trade_id", "ts"], columns="role", values=["bid", "ask"],
                          aggfunc="first")
    wide = wide.dropna()
    bid = wide["bid"]["lo"] + wide["bid"]["up"] - 2 * wide["ask"]["ce"]
    ask = wide["ask"]["lo"] + wide["ask"]["up"] - 2 * wide["bid"]["ce"]
    out = pd.DataFrame({"bid": bid, "ask": ask, "mid": (bid + ask) / 2}).reset_index()
    if "drawdown_pct" in legs.columns:
        dd = legs.groupby(["trade_id", "ts"]).drawdown_pct.first()
        out = out.join(dd, on=["trade_id", "ts"])
    return out.sort_values(["trade_id", "ts"], ignore_index=True)


def stand_in_signals(
    flies: pd.DataFrame, *, threshold: float = 30.0, min_after: float = 90.0,
    spacing: float = 300.0,
) -> pd.DataFrame:
    """Polls where drawdown from peak first rises through `threshold` percent.

    Needs `min_after` seconds of polls after it within the trade, and at most one per
    `spacing` seconds per trade (earliest first).
    """
    rows = []
    for trade_id, g in flies.groupby("trade_id", sort=True):
        dd = g.drawdown_pct.to_numpy(dtype=float)
        ts = g.ts.reset_index(drop=True)
        last = ts.iloc[-1]
        prev = np.r_[np.nan, dd[:-1]]
        crossing = np.nonzero((dd >= threshold) & ~(prev >= threshold))[0]
        taken = None
        for k in crossing:
            if (last - ts[k]).total_seconds() < min_after:
                continue
            if taken is not None and (ts[k] - taken).total_seconds() < spacing:
                continue
            rows.append({"trade_id": trade_id, "ts": ts[k]})
            taken = ts[k]
    return pd.DataFrame(rows, columns=["trade_id", "ts"])


def path_from(flies: pd.DataFrame, t0: pd.Timestamp) -> Path:
    """Path of one trade's fly quotes from `t0` (which must be a poll) onward."""
    g = flies[flies.ts >= t0]
    t = (g.ts - t0).dt.total_seconds().to_numpy()
    return Path(t=t, bid=g.bid.to_numpy(dtype=float), mid=g.mid.to_numpy(dtype=float))


def max_gap(path: Path, horizon: float) -> float:
    t = np.r_[path.t[path.t <= horizon], horizon]
    return float(np.diff(t).max()) if len(t) > 1 else horizon


# --------------------------------------------------------------------------- statistics


@dataclasses.dataclass(frozen=True)
class Summary:
    n_exits: int
    n_sessions: int
    mean: float  # $ per exit, mean of per-session means
    lower90: float  # one-sided 90% lower bound of that mean
    ci95: tuple[float, float]
    worst: float  # worst single-exit difference


def summarize(
    dates: Sequence, diffs: Sequence[float], *, reps: int = 5000, block: int = 5,
    seed: int = 20261117,
) -> Summary:
    """Session-level block bootstrap (sessions in date order, each session's exits averaged)."""
    df = pd.DataFrame({"d": pd.to_datetime(list(dates)), "x": np.asarray(diffs, float)})
    per = df.groupby("d").x.mean().sort_index().to_numpy()
    idx = block_bootstrap_indices(len(per), reps, block, seed)
    boot = per[idx].mean(axis=1)
    return Summary(
        n_exits=len(df), n_sessions=len(per), mean=float(per.mean()),
        lower90=float(np.percentile(boot, 10)),
        ci95=(float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))),
        worst=float(df.x.min()),
    )


def qualifies(primary: Summary, optimistic: Summary, touch: Summary) -> dict[str, bool]:
    """Plan section 4, criteria 1-4 (criterion 5 is a code property, tested separately)."""
    return {
        "1_mid50_mean_ge_0_and_lower90_gt_-5": primary.mean >= 0 and primary.lower90 > -5,
        "2_mid100_mean_ge_0": optimistic.mean >= 0,
        "3_touch_mean_ge_-10": touch.mean >= -10,
        "4_worst_ge_-50": primary.worst >= -50,
    }


def select(passing: dict[str, float]) -> str | None:
    """Highest mid50 mean among qualifying candidates; within $1, prefer the smaller change."""
    if not passing:
        return None
    best = max(passing.values())
    for name in PREFERENCE:
        if name in passing and passing[name] >= best - 1.0:
            return name
    return None
