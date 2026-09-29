"""Entry rules for the drafted hypotheses H-SN1, H-EV1 and H-TS1.

Implemented from `docs/research/next-sweep-preregistration-draft.md` (DRAFT, not
registered). They are catalog entries so that the owner can `register` them; nothing here
has been registered or run on vendor data. H-LV1 is the existing `HLV1`.

Each rule keeps its logic inside the class, so the variant's definition hash (which
covers the class source) changes whenever the logic does. Rules that read session
features (`USES_FEATURES`) take them from `RunContext.features`; a run records their
input hashes (event calendar, aux files) in its meta.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, replace
from typing import ClassVar

import numpy as np

from butterfly_guy.research.entry import (
    BaselineEntry,
    Entry,
    RunContext,
    Session,
    cached_entries,
    gap_direction,
)
from butterfly_guy.research.learning import LeakageError, WindowedLoader
from butterfly_guy.research.market import Fly, et_us


def uses_features(rule: object) -> bool:
    return bool(getattr(rule, "USES_FEATURES", False))


def session_features(ctx: RunContext, rule: object):
    if ctx.features is None:
        raise ValueError(f"{type(rule).__name__} needs session features (RunContext.features)")
    return ctx.features


@dataclass(frozen=True)
class SigmaPlacedEntry:
    """H-SN1: deterministic σ-normalised placement instead of the live selector.

    σ = `straddle_multiple` x the ATM straddle mark at the snapshot at or before
    `sigma_at_et` (10:00 ET), fixed for the session. At each clock time in the configured
    entry window with a fresh VIX (as E0), in the gap direction:

    - center: the listed strike nearest spot ± `center_sigma` σ (the lower one on an exact
      tie); it must be out of the money, as the live builder requires;
    - width: `width_sigma` σ rounded to the nearest `width_step` points, at least one step;
    - the fly must be listed, executable at the snapshot, and its mark debit within the
      live cost limits: at least `min_debit`, at most the configured cap for the width,
      or, for a width the config has no cap for, the per-point rate every configured cap
      shares (the config must have a single rate). There is no reward/risk filter.

    The first time that qualifies is the entry. No straddle at `sigma_at_et`, no entry.
    Flies are not chosen by the live selector, so tie-sets do not apply."""

    center_sigma: float = 1.58
    width_sigma: float = 0.88
    straddle_multiple: float = 1.25
    sigma_at_et: tuple[int, int] = (10, 0)
    width_step: int = 5

    def sigma(self, s: Session) -> float | None:
        i = s.market.at_or_before(et_us(s.date, *self.sigma_at_et))
        straddle = s.market.atm_straddle(i) if i >= 0 else None
        return None if straddle is None or straddle <= 0 else self.straddle_multiple * straddle

    def width(self, sigma: float) -> int:
        steps = int(np.floor(self.width_sigma * sigma / self.width_step + 0.5))
        return self.width_step * max(1, steps)

    @staticmethod
    def cost_cap(ctx: RunContext, width: int) -> float:
        caps = ctx.config.strategy.max_cost_per_width
        if width in caps:
            return float(caps[width])
        rates = {round(c / w, 9) for w, c in caps.items()}
        if len(rates) != 1:
            raise ValueError(f"no cost cap for width {width} and no single per-point rate")
        return rates.pop() * width

    def center(self, s: Session, spot: float, direction: str, sigma: float) -> float | None:
        sign = 1.0 if direction == "CALL" else -1.0
        target = spot + sign * self.center_sigma * sigma
        strikes = s.market.strikes
        c = float(strikes[int(np.argmin(np.abs(strikes - target)))])
        otm = c > spot if direction == "CALL" else c < spot
        return c if otm else None

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        sigma = self.sigma(s)
        if sigma is None:
            return []
        width = self.width(sigma)
        cap = self.cost_cap(ctx, width)
        min_debit = ctx.config.strategy.min_debit
        direction = gap_direction(s)
        lo, hi = ctx.window(s.date)
        for ts in s.clock_ts[(s.clock_ts >= lo) & (s.clock_ts <= hi)]:
            ts = int(ts)
            vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
            i = s.market.at_or_before(ts)
            if vix is None or i < 0:
                continue
            spot = float(s.clock_spot[s.clock_index(ts)])
            c = self.center(s, spot, direction, sigma)
            if c is None:
                continue
            fly = Fly(direction, c - width, c, c + width)
            path = s.market.fly_path(fly)
            if path is None or not path.executable[i]:
                continue
            cost = float(path.mark[i])
            if min_debit <= cost <= cap:
                return [Entry(fly, ts, i, cost, direction, vix=vix[0], spot=spot, tag="sigma")]
        return []


@dataclass(frozen=True)
class ReleaseSkipEntry:
    """H-EV1: the base rule's entries, except on sessions with a CPI, NFP or PCE release
    scheduled strictly before 10:00 ET. Only events the calendar's leakage rule lets the
    session see count: published before the session, not withdrawn before it, never
    unscheduled. Whether the release was actually held is never used."""

    USES_FEATURES: ClassVar[bool] = True

    base: BaselineEntry
    event_types: tuple[str, ...] = ("CPI", "NFP", "PCE")
    before_et: tuple[int, int] = (10, 0)

    def skips(self, ctx: RunContext, d: dt.date) -> bool:
        calendar = session_features(ctx, self).calendar
        cutoff = dt.time(*self.before_et)
        return any(e.event_type in self.event_types and e.before(cutoff) is True
                   for e in calendar.events_for(d))

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        return [] if self.skips(ctx, s.date) else cached_entries(s, ctx, self.base)


@dataclass(frozen=True)
class EventDaySkipEntry:
    """H-EV2 (optional in the draft): the base rule's entries, except on sessions with a
    scheduled event of `event_types` (an FOMC statement) at any time of day, including
    after entry. Only events the calendar's leakage rule lets the session see count, as in
    `ReleaseSkipEntry`; whether the event was held is never used."""

    USES_FEATURES: ClassVar[bool] = True

    base: BaselineEntry
    event_types: tuple[str, ...] = ("FOMC",)

    def skips(self, ctx: RunContext, d: dt.date) -> bool:
        calendar = session_features(ctx, self).calendar
        return any(e.event_type in self.event_types for e in calendar.events_for(d))

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        return [] if self.skips(ctx, s.date) else cached_entries(s, ctx, self.base)


@dataclass(frozen=True)
class PriorRatioFilter:
    """H-TS1: the base rule's entries, except on sessions whose prior-session ratio (for
    example VIX1D/VIX, from closes on the previous SPX session only) is at or above
    `threshold`. The threshold is the `quantile` of that ratio over the qualifying
    sessions of the fit window, fitted once through a `WindowedLoader` and frozen with the
    definition; the hash covers the procedure, not the fitted value. A session without
    the ratio (no prior VIX1D close before 2022-05-16) is never skipped."""

    FITTED: ClassVar[tuple[str, ...]] = ("threshold", "fit_n")
    USES_FEATURES: ClassVar[bool] = True

    base: BaselineEntry
    ratio: str  # a features.RATIOS key, read as "<ratio>_prior"
    fit_start: dt.date
    fit_end: dt.date
    quantile: float = 2 / 3
    threshold: float | None = None
    fit_n: int | None = None

    def value(self, ctx: RunContext, d: dt.date) -> float | None:
        return session_features(ctx, self).term_structure(d).get(f"{self.ratio}_prior")

    def fit(self, loader: WindowedLoader, ctx: RunContext) -> PriorRatioFilter:
        values = []
        for d in loader.dates():
            if not self.fit_start <= d <= self.fit_end:
                raise LeakageError(
                    f"{d} is outside the fit window {self.fit_start}..{self.fit_end}")
            v = self.value(ctx, d)
            if v is not None:
                values.append(v)
        if not values:
            raise ValueError(f"no {self.ratio} observations in the fit window")
        return replace(self, threshold=float(np.quantile(values, self.quantile)),
                       fit_n=len(values))

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        if self.threshold is None:
            raise ValueError("PriorRatioFilter used before it was fitted")
        v = self.value(ctx, s.date)
        if v is not None and v >= self.threshold:
            return []
        return cached_entries(s, ctx, self.base)
