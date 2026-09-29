"""Exit rules and the monitoring loop.

The loop mirrors `SimulationEngine.simulate_day_from_entry`: for every decision-clock
time after entry it reads the snapshot recorded at or before that time; an incomplete
fly (any leg quote absent) is not an observation and cannot move the peak, trigger an
exit or advance a confirmation count. The value is `max(0, fly mark)`. Rules are checked
in order and the first that fires exits at that snapshot. With no exit the fly is held
to the official close, provided the session's data runs to at least one hour before its
scheduled close: 15:00 ET on a regular session, as `SimulationEngine` requires, and 12:00
on a 13:00 early close (owner's decision D5, 2026-09-29). A session's scheduled close is
16:00 unless its dataset records another (vendor datasets record 13:00 on early closes).

Rules are small frozen dataclasses so a variant's exit policy has a canonical,
hashable definition. `PeakTrailer.from_config` reads the runtime profit settings and
uses the shared `effective_drawdown_threshold` / `profitprotector_floor_decision`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from functools import lru_cache
from types import SimpleNamespace
from typing import Protocol

import numpy as np

from butterfly_guy.core.config import AppConfig, ProfitProtectorSettings, TimeRegime
from butterfly_guy.core.time_utils import get_time_regime
from butterfly_guy.position.profit_policy import (
    effective_drawdown_threshold,
    profitprotector_floor_decision,
)
from butterfly_guy.research.market import FlyPath, et_us

REGULAR_CLOSE = dt.time(16, 0)
# Data must reach this long before the scheduled close: on a regular session that is
# SimulationEngine's MIN_END_OF_DAY_DATA_TIME, 15:00 (a test pins the equality).
END_OF_DAY_DATA_LEAD = dt.timedelta(hours=1)
HELD = "cash_settled"
INCOMPLETE = "incomplete_data"


@lru_cache(maxsize=16)
def _regime_bounds(morning_end: float, late_morning_end: float) -> dict[str, SimpleNamespace]:
    return {
        "morning": SimpleNamespace(end_minutes_after_open=morning_end),
        "late_morning": SimpleNamespace(end_minutes_after_open=late_morning_end),
    }


@lru_cache(maxsize=64)
def _threshold_regime(threshold: float) -> TimeRegime:
    return TimeRegime(start_minutes_after_open=0, end_minutes_after_open=0,
                      drawdown_threshold=threshold)


@lru_cache(maxsize=16)
def _protector_settings(items: tuple[tuple[str, float], ...]) -> ProfitProtectorSettings:
    return ProfitProtectorSettings(**dict(items))


@dataclass
class Observation:
    ts_us: int
    minutes_since_open: float
    minutes_to_close: float
    entry_age_minutes: float
    value: float
    peak: float
    entry_price: float


class ExitRule(Protocol):
    def reason(self, obs: Observation, memo: dict) -> str | None: ...


@dataclass(frozen=True)
class PreCloseExit:
    minutes_before_close: float

    def reason(self, obs: Observation, memo: dict) -> str | None:
        return "end_of_day" if obs.minutes_to_close <= self.minutes_before_close else None


@dataclass(frozen=True)
class AbsoluteLossStop:
    max_loss_from_cost: float

    def reason(self, obs: Observation, memo: dict) -> str | None:
        if obs.entry_price > 0 and (
            (obs.entry_price - obs.value) / obs.entry_price >= self.max_loss_from_cost
        ):
            return "absolute_loss_stop"
        return None


@dataclass(frozen=True)
class TimeExit:
    """Exit at the first observation at or after an ET wall-clock time."""

    hour: int
    minute: int

    def reason(self, obs: Observation, memo: dict) -> str | None:
        return "time_exit" if obs.minutes_since_open >= (self.hour - 9) * 60 + self.minute - 30 \
            else None


@dataclass(frozen=True)
class TakeProfit:
    """Exit when the value reaches `multiple` x the midpoint entry price."""

    multiple: float

    def reason(self, obs: Observation, memo: dict) -> str | None:
        return "take_profit" if obs.value >= self.multiple * obs.entry_price else None


@dataclass(frozen=True)
class StopLoss:
    """Exit when the value falls to (1 - fraction) x the midpoint entry price."""

    fraction: float

    def reason(self, obs: Observation, memo: dict) -> str | None:
        return "stop" if obs.value <= (1 - self.fraction) * obs.entry_price else None


@dataclass(frozen=True)
class PeakTrailer:
    """Peak-value trailer with time-regime drawdown thresholds and confirmation polls."""

    morning: float = 0.60
    late_morning: float = 0.90
    afternoon: float = 0.75
    morning_end: float = 120.0
    late_morning_end: float = 240.0
    confirmation_polls: int = 1
    min_peak_profit_ratio: float = 1.0
    min_hold_minutes: float = 0.0
    strategy: str = "peakvaluetrailer"
    protector: tuple[tuple[str, float], ...] = field(default=())

    @classmethod
    def from_config(cls, config: AppConfig) -> PeakTrailer:
        """Runtime profit settings, collapsed per regime as `run_backtest_db` does."""
        pm = config.profit_management
        regimes = pm.regimes
        return cls(
            morning=regimes["morning"].drawdown_threshold,
            late_morning=regimes["late_morning"].drawdown_threshold,
            afternoon=regimes["afternoon"].drawdown_threshold,
            morning_end=regimes["morning"].end_minutes_after_open,
            late_morning_end=regimes["late_morning"].end_minutes_after_open,
            confirmation_polls=max(r.confirmation_polls for r in regimes.values()),
            min_peak_profit_ratio=max(r.min_peak_profit_ratio for r in regimes.values()),
            min_hold_minutes=max(r.min_hold_minutes for r in regimes.values()),
            strategy=pm.strategy,
            protector=tuple(sorted(pm.profitprotector.model_dump().items())),
        )

    def reason(self, obs: Observation, memo: dict) -> str | None:
        armed = (
            obs.entry_age_minutes >= self.min_hold_minutes
            and obs.peak >= obs.entry_price * self.min_peak_profit_ratio
            and obs.peak > obs.entry_price
            and obs.peak > 0
        )
        if not armed:
            memo.clear()
            return None
        regime = get_time_regime(
            obs.minutes_since_open, _regime_bounds(self.morning_end, self.late_morning_end)
        )
        threshold = {"morning": self.morning, "late_morning": self.late_morning,
                     "afternoon": self.afternoon}[regime]
        drawdown = (obs.peak - obs.value) / obs.peak
        found = None
        protector = _protector_settings(self.protector)
        if self.strategy == "profitprotector":
            floor = profitprotector_floor_decision(
                entry_price=obs.entry_price, current_value=obs.value, peak_value=obs.peak,
                settings=protector,
            )
            if floor is not None:
                found = floor.reason
        if found is None:
            effective = effective_drawdown_threshold(
                strategy=self.strategy, entry_price=obs.entry_price, peak_value=obs.peak,
                regime_config=_threshold_regime(threshold),
                protector_settings=protector,
            )
            if drawdown >= effective:
                found = f"drawdown_{regime}"
        if found is None:
            memo.clear()
            return None
        if memo.get("pending") == found:
            memo["count"] += 1
        else:
            memo["pending"], memo["count"] = found, 1
        return found if memo["count"] >= max(1, self.confirmation_polls) else None


def config_exit_rules(config: AppConfig) -> tuple[ExitRule, ...]:
    """The runtime exit policy in `SimulationEngine` order."""
    pm = config.profit_management
    rules: list[ExitRule] = []
    if pm.exit_before_close_minutes > 0:
        rules.append(PreCloseExit(pm.exit_before_close_minutes))
    if pm.use_absolute_loss_stop:
        rules.append(AbsoluteLossStop(pm.max_loss_from_cost))
    rules.append(PeakTrailer.from_config(config))
    return tuple(rules)


@dataclass
class ExitDecision:
    reason: str  # a rule's reason, HELD, or INCOMPLETE
    index: int | None = None  # snapshot index of the exit decision (None when held)
    ts_us: int | None = None
    value: float | None = None  # max(0, mark) at the decision
    peak: float = 0.0


def monitor(
    *,
    date: dt.date,
    clock_ts: np.ndarray,
    snapshot_ts: np.ndarray,
    path: FlyPath,
    entry_ts_us: int,
    entry_price: float,
    rules: tuple[ExitRule, ...],
    session_close: dt.time = REGULAR_CLOSE,
) -> ExitDecision:
    open_us = et_us(date, 9, 30)
    close_us = et_us(date, 16, 0)
    peak = entry_price
    memos: list[dict] = [{} for _ in rules]
    start = int(np.searchsorted(clock_ts, entry_ts_us, side="right"))
    idx = np.searchsorted(snapshot_ts, clock_ts[start:], side="right") - 1
    for ts, i in zip(clock_ts[start:], idx, strict=True):
        if i < 0 or not path.observed[i]:
            continue
        value = max(0.0, float(path.mark[i]))
        peak = max(peak, value)
        obs = Observation(
            ts_us=int(ts),
            minutes_since_open=(ts - open_us) / 60e6,
            minutes_to_close=(close_us - ts) / 60e6,
            entry_age_minutes=(ts - entry_ts_us) / 60e6,
            value=value,
            peak=peak,
            entry_price=entry_price,
        )
        for rule, memo in zip(rules, memos, strict=True):
            why = rule.reason(obs, memo)
            if why is not None:
                return ExitDecision(why, int(i), int(ts), value, peak)
    needed = (et_us(date, session_close.hour, session_close.minute)
              - int(END_OF_DAY_DATA_LEAD.total_seconds() * 1e6))
    if len(clock_ts) == 0 or clock_ts[-1] < needed:
        return ExitDecision(INCOMPLETE, peak=peak)
    return ExitDecision(HELD, peak=peak)
