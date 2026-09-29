"""Rules that learn from data, and the guards that keep them leakage-safe.

Two kinds:

- **Fitted rules** (`FittedFilter`, idea sweep K1/R2) fit one threshold on a fixed window
  of sessions before the run. `fit` sees the data only through a `WindowedLoader`, which
  refuses any session outside `[fit_start, fit_end]`. The fit window, the fitted value and
  the sample size are part of the variant's recorded definition; the definition hash
  covers the procedure (feature, statistic, window, base rule) but not the fitted value,
  so re-fitting the same registered procedure is not a new variant. Sessions inside the
  fit window are in-sample for such a rule; reports mark them.
- **Learning rules** (`EVSelector`, `EVRankEntry`, idea sweep G1/G2/R3/R4) learn from
  prior sessions. The runner keeps one `History` per rule, passes `decide` only the
  records dated before the session, and appends the session's own observation (which may
  use its settlement) only after every variant has decided on it. A rule therefore never
  sees a session at or after the one it is deciding. Observation starts at the rule's
  `history_start`, independent of where evaluation starts, so a short evaluation window
  (the cohort shadow) still sees the full prior history.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field, replace
from typing import ClassVar, Literal, Protocol

import numpy as np

from butterfly_guy.research.accounting import Costs
from butterfly_guy.research.entry import (
    BaselineEntry,
    Entry,
    RunContext,
    Session,
    SessionLoader,
    baseline_window,
    cached_entries,
    selection_span,
)
from butterfly_guy.research.market import Fly, et_us
from butterfly_guy.strategy.butterfly_builder import (
    ButterflyBuilder,
    resolve_wing_widths_for_vix,
)

HISTORY_START = dt.date(2026, 3, 13)  # first SPX session with a recorded 0-DTE chain


class LeakageError(RuntimeError):
    """A rule was about to see data from a session at or after the one it decides, or
    a fit was about to read outside its window."""


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


@dataclass
class History:
    """One learning rule's per-session observations, in strictly increasing date order."""

    records: list[tuple[dt.date, object]] = field(default_factory=list)

    def append(self, date: dt.date, value: object) -> None:
        if self.records and date <= self.records[-1][0]:
            raise LeakageError(f"observation for {date} after {self.records[-1][0]}")
        self.records.append((date, value))

    def before(self, date: dt.date) -> tuple[tuple[dt.date, object], ...]:
        """Records strictly before `date` (an immutable snapshot)."""
        return tuple(r for r in self.records if r[0] < date)


class WindowedLoader:
    """A session loader limited to a fixed fit window; loading outside it raises."""

    def __init__(self, loader: SessionLoader, start: dt.date, end: dt.date) -> None:
        self.loader, self.start, self.end = loader, start, end

    def dates(self) -> list[dt.date]:
        return self.loader.dates(self.start, self.end)

    def load(self, date: dt.date) -> Session | None:
        if not self.start <= date <= self.end:
            raise LeakageError(f"{date} is outside the fit window {self.start}..{self.end}")
        return self.loader.load(date)


class LearningRule(Protocol):
    history_start: dt.date

    def observe(self, s: Session, ctx: RunContext) -> object | None: ...

    def decide(self, s: Session, ctx: RunContext,
               history: tuple[tuple[dt.date, object], ...]) -> list[Entry]: ...


def is_learning(rule: object) -> bool:
    return hasattr(rule, "observe") and hasattr(rule, "decide")


def is_fitted(rule: object) -> bool:
    return hasattr(rule, "fit") and hasattr(rule, "fit_end")


# ---------------------------------------------------------------------------
# Fitted threshold filters (K1, R2)
# ---------------------------------------------------------------------------


def entry_spread_ratio(s: Session, e: Entry) -> float | None:
    """(stressless marketable entry - midpoint entry) / mark: the fly's entry spread as a
    share of its mark (K1). None when the entry market is not executable."""
    path = s.market.fly_path(e.fly)
    if path is None or not path.executable[e.index]:
        return None
    comm = Costs().commission
    entry_mkt = float(path.debit[e.index]) + comm
    entry_mid = e.cost + comm
    return (entry_mkt - entry_mid) / (entry_mid - comm)


def vix_straddle_ratio(s: Session, e: Entry) -> float | None:
    """VIX daily move / (1.25 x ATM straddle) at the entry snapshot (R2)."""
    st = s.market.atm_straddle(e.index)
    if not st or e.vix is None:
        return None
    spot = float(s.market.spot[e.index])
    return (spot * e.vix / 100 / math.sqrt(252)) / (1.25 * st)


FEATURES = {"entry_spread_ratio": entry_spread_ratio, "vix_straddle_ratio": vix_straddle_ratio}


@dataclass(frozen=True)
class FittedFilter:
    """Keep the base rule's entry when `feature <= threshold`, the threshold being
    `statistic` of the feature over the base rule's entries in the fit window.
    `if_undefined` says what happens to an entry whose feature is undefined."""

    FITTED: ClassVar[tuple[str, ...]] = ("threshold", "fit_n")

    base: BaselineEntry
    feature: str  # key into FEATURES
    fit_start: dt.date
    fit_end: dt.date
    statistic: Literal["median"] = "median"
    if_undefined: Literal["keep", "skip"] = "skip"
    threshold: float | None = None
    fit_n: int | None = None

    def fit(self, loader: WindowedLoader, ctx: RunContext) -> FittedFilter:
        fn = FEATURES[self.feature]
        values = []
        for d in loader.dates():
            s = loader.load(d)
            if s is None:
                continue
            for e in cached_entries(s, ctx, self.base):
                v = fn(s, e)
                if v is not None:
                    values.append(v)
        if not values:
            raise ValueError(f"no {self.feature} observations in the fit window")
        return replace(self, threshold=float(np.median(values)), fit_n=len(values))

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        if self.threshold is None:
            raise ValueError("FittedFilter used before it was fitted")
        fn = FEATURES[self.feature]
        out = []
        for e in cached_entries(s, ctx, self.base):
            v = fn(s, e)
            if (v is None and self.if_undefined == "keep") or (v is not None
                                                                and v <= self.threshold):
                out.append(e)
        return out


def fit_variant_entry(rule: object, loader: SessionLoader, ctx: RunContext) -> object:
    """Fit an unfitted rule on its own window through a fresh, windowed loader."""
    if not is_fitted(rule) or rule.threshold is not None:
        return rule
    window = WindowedLoader(SessionLoader(loader.dataset, loader.profile, loader.unseal),
                            rule.fit_start, rule.fit_end)
    return rule.fit(window, ctx)


# ---------------------------------------------------------------------------
# Prior-session expected-value learners (G1/G2, R3/R4)
# ---------------------------------------------------------------------------

# Gaussian kernel nodes: the idea sweep's fixed 25 quantiles of 200,000 standard normals.
KERNEL_NODES = np.quantile(np.random.default_rng(0).standard_normal(200_000),
                           np.linspace(0.02, 0.98, 25))


def settle_z(s: Session, hour: int, minute: int) -> float | None:
    """(official close - spot) / ATM straddle at the first snapshot at or after hh:mm ET."""
    i = s.market.first_at_or_after(et_us(s.date, hour, minute))
    if i is None or s.close is None:
        return None
    st = s.market.atm_straddle(i)
    if not st:
        return None
    return (s.close - float(s.market.spot[i])) / st


def settlement_scenarios(history: tuple[tuple[dt.date, object], ...], spot: float,
                         straddle: float, bandwidth: float) -> np.ndarray:
    """Kernel-smoothed settlement scenarios from prior sessions' z values."""
    z = (np.array([v for _, v in history])[:, None]
         + bandwidth * KERNEL_NODES[None, :]).ravel()
    return spot + z * straddle


def fly_ev(settles: np.ndarray, center: float, width: float) -> float:
    return float(np.maximum(0.0, width - np.abs(settles - center)).mean())


def _audit(history: tuple[tuple[dt.date, object], ...]) -> dict:
    return {"history_n": len(history), "history_last": history[-1][0] if history else None}


@dataclass(frozen=True)
class EVSelector:
    """Idea sweep G1/G2: at the first snapshot at or after hh:mm ET, score every
    buildable fly of either type (widths `widths`, centers within `center_range` of spot on
    the strike step, mark >= `min_mark`, no crossed leg) by expected settlement value under
    the prior-session z model minus its stressed marketable debit; trade the best if its
    edge is positive. Needs `min_history` prior observations."""

    hour: int
    minute: int
    bandwidth: float = 0.3
    min_history: int = 20
    widths: tuple[int, ...] = (10, 15, 20, 25, 30, 40, 50)
    center_range: float = 100.0
    strike_step: int = 5
    min_mark: float = 0.30
    history_start: dt.date = HISTORY_START

    def observe(self, s: Session, ctx: RunContext) -> float | None:
        return settle_z(s, self.hour, self.minute)

    def decide(self, s: Session, ctx: RunContext,
               history: tuple[tuple[dt.date, object], ...]) -> list[Entry]:
        i = s.market.first_at_or_after(et_us(s.date, self.hour, self.minute))
        if i is None:
            return []
        st = s.market.atm_straddle(i)
        if not st or len(history) < self.min_history:
            return []
        spot = float(s.market.spot[i])
        settles = settlement_scenarios(history, spot, st, self.bandwidth)
        costs = Costs(ctx.config.execution.paper_commission_per_contract)
        strikes = s.market.strikes
        col = {float(k): j for j, k in enumerate(strikes)}
        f = s.market.chain.fields
        best = None
        for typ, direction in (("C", "CALL"), ("P", "PUT")):
            mk, bid, ask = f[f"{typ}_mark"][i], f[f"{typ}_bid"][i], f[f"{typ}_ask"][i]
            for c in strikes:
                c = float(c)
                if abs(c - spot) > self.center_range or c % self.strike_step:
                    continue
                for w in self.widths:
                    if c - w not in col or c + w not in col:
                        continue
                    jl, jc, jh = col[c - w], col[c], col[c + w]
                    m = mk[jl] + mk[jh] - 2 * mk[jc]
                    a = ask[jl] + ask[jh] - 2 * bid[jc]
                    if not (np.isfinite(m) and np.isfinite(a)) or m < self.min_mark:
                        continue
                    if bid[jl] > ask[jl] or bid[jc] > ask[jc] or bid[jh] > ask[jh]:
                        continue
                    ev = fly_ev(settles, c, w) - (a + costs.commission + costs.stress)
                    if best is None or ev > best[0]:
                        best = (ev, Fly(direction, c - w, c, c + w), float(m))
        if best is None or best[0] <= 0:
            return []
        ev, fly, mark = best
        return [Entry(fly, int(s.market.ts[i]), i, mark, fly.direction, spot=spot,
                      tag=f"ev={ev:.2f}", **_audit(history))]


@dataclass(frozen=True)
class EVRankEntry:
    """Idea sweep R3/R4: the baseline's candidate set (gap direction, VIX-bucket widths,
    live candidate filters) at the first window time with a fresh VIX, a straddle and at
    least one candidate, ranked by expected settlement value under the prior-session z
    model minus mark cost instead of the VIX anchor and reward/risk. Needs `min_history`
    prior observations; observes the settle z at `anchor` ET."""

    base: BaselineEntry = BaselineEntry()
    bandwidth: float = 0.3
    min_history: int = 20
    anchor: tuple[int, int] = (10, 0)
    history_start: dt.date = HISTORY_START

    def observe(self, s: Session, ctx: RunContext) -> float | None:
        return settle_z(s, *self.anchor)

    def decide(self, s: Session, ctx: RunContext,
               history: tuple[tuple[dt.date, object], ...]) -> list[Entry]:
        if len(history) < self.min_history:
            return []
        lo, hi = baseline_window(self.base, s, ctx)
        direction = self.base._direction(s, lo)
        config = ctx.config
        for ts in s.clock_ts[(s.clock_ts >= lo) & (s.clock_ts <= hi)]:
            ts = int(ts)
            vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
            i = s.market.at_or_before(ts)
            st = s.market.atm_straddle(i) if i >= 0 else None
            if vix is None or not st:
                continue
            spot = float(s.clock_spot[s.clock_index(ts)])
            widths, _ = resolve_wing_widths_for_vix(vix[0], config.strategy.vix_width_buckets)
            builder = ButterflyBuilder(config.strategy.model_copy(
                update={"wing_widths": list(widths)}))
            quotes = s.market.quotes_at(i, direction, near=spot, span=selection_span(config))
            cands = builder.build_candidates(quotes, spot, direction)
            if not cands:
                continue
            settles = settlement_scenarios(history, spot, st, self.bandwidth)
            best = max(cands, key=lambda c: fly_ev(settles, c.center_strike, c.wing_width)
                       - c.cost)
            return [Entry(Fly.from_candidate(best), ts, i, best.cost, direction, vix=vix[0],
                          spot=spot, tag="evrank", **_audit(history))]
        return []
