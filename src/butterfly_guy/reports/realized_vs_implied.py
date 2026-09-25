"""Weekly realized-vs-implied tracking for SPX 0-DTE (diagnostic only, never a trading rule).

Definitions match docs/research/strategy-discovery-journal.md (2026-09-25):
- implied sigma of the rest of the session = 1.25 x the 10:00 ET ATM straddle mid
  (the straddle is about 0.8 sigma of the remaining move);
- z = (official close - 10:00 spot) / sigma;
- realized/implied = RMS of z (1.0 means the chain priced the move correctly);
- a "landing" is a close 0.9-2.3 sigma in the opening-gap direction, where the baseline
  butterfly's tent sits.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass

STRADDLE_TO_SIGMA = 1.25
LANDING_ZONE = (0.9, 2.3)

# Development-sample references (2026-09-25 journal), recomputed with this module's exact
# 10:00 snapshot rule: H1 61 sessions, H2 63 (collector-outage mornings excluded).
REFERENCE_PERIODS = (
    ("H1 Mar 13-Jun 18 (strategy +$17.0k)", 1.03, 0.213),
    ("H2 Jun 19-Sep 24 (strategy -$6.6k)", 0.92, 0.095),
)


@dataclass(frozen=True)
class SessionMove:
    date: dt.date
    spot_10: float
    straddle: float
    close: float | None  # None until the official close is recorded
    gap_sign: int  # +1 gap up (CALL day), -1 gap down (PUT day)

    @property
    def sigma(self) -> float:
        return STRADDLE_TO_SIGMA * self.straddle

    @property
    def z(self) -> float | None:
        if self.close is None:
            return None
        return (self.close - self.spot_10) / self.sigma

    @property
    def landed(self) -> bool | None:
        z = self.z
        if z is None:
            return None
        lo, hi = LANDING_ZONE
        return lo <= self.gap_sign * z <= hi


@dataclass(frozen=True)
class MoveSummary:
    sessions: int
    rms_z: float | None
    mean_abs_z: float | None
    share_over_1sd: float | None
    landing_rate: float | None
    straddle_pnl_mean: float | None  # long 10:00 straddle held to close, index points


def atm_straddle(rows: list[tuple[float, str, float]], spot: float) -> float | None:
    """Straddle mid at the listed strike nearest spot that has both a call and a put mark."""
    marks: dict[float, dict[str, float]] = {}
    for strike, option_type, mark in rows:
        if mark is None or not math.isfinite(mark):
            continue
        marks.setdefault(float(strike), {})[option_type[0].upper()] = float(mark)
    if not marks:
        return None
    strike = min(marks, key=lambda k: (abs(k - spot), k))
    pair = marks[strike]
    if "C" not in pair or "P" not in pair:
        return None
    return pair["C"] + pair["P"]


def summarize(moves: list[SessionMove]) -> MoveSummary:
    done = [m for m in moves if m.close is not None]
    if not done:
        return MoveSummary(0, None, None, None, None, None)
    zs = [m.z for m in done]
    n = len(done)
    return MoveSummary(
        sessions=n,
        rms_z=math.sqrt(sum(z * z for z in zs) / n),
        mean_abs_z=sum(abs(z) for z in zs) / n,
        share_over_1sd=sum(abs(z) > 1 for z in zs) / n,
        landing_rate=sum(bool(m.landed) for m in done) / n,
        straddle_pnl_mean=sum(abs(m.close - m.spot_10) - m.straddle for m in done) / n,
    )


def _fmt(value: float | None, spec: str) -> str:
    return "  n/a" if value is None else format(value, spec)


def _summary_line(label: str, s: MoveSummary) -> str:
    return (
        f"{label:<15} {s.sessions:>3} {_fmt(s.rms_z, '5.2f')} {_fmt(s.share_over_1sd, '6.0%')}"
        f" {_fmt(s.landing_rate, '6.0%')} {_fmt(s.straddle_pnl_mean, '+7.2f')}"
    )


def verdict(rms_z: float | None) -> str:
    if rms_z is None:
        return "no completed sessions"
    if rms_z >= 1.0:
        return "moves at/above priced: conditions like H1, when the strategy made money"
    if rms_z >= 0.95:
        return "moves slightly below priced: neutral"
    return "moves below priced: conditions like H2, when the strategy lost"


def format_message(
    *,
    week_start: dt.date,
    week_end: dt.date,
    week: list[SessionMove],
    cohort: list[SessionMove],
    cohort_start: dt.date,
    trailing: list[SessionMove],
) -> str:
    rows = []
    for m in week:
        if m.close is None:
            rows.append(f"{m.date:%a %m-%d} {m.straddle:6.2f} {'pending close':>22}")
            continue
        move = m.close - m.spot_10
        landed = "yes" if m.landed else "-"
        gap = "up" if m.gap_sign > 0 else "dn"
        rows.append(
            f"{m.date:%a %m-%d} {m.straddle:6.2f} {move:+7.1f} {m.z:+6.2f} {gap:>4} {landed:>4}"
        )
    ws, cs, ts = summarize(week), summarize(cohort), summarize(trailing)
    lines = [
        f"**SPX realized vs implied — week {week_start:%b %d}–{week_end:%b %d}**",
        f"Last {ts.sessions} sessions realized/implied: **{_fmt(ts.rms_z, '.2f')}** — "
        f"{verdict(ts.rms_z)} (this week {_fmt(ws.rms_z, '.2f')} on {ws.sessions}, noisy)",
        "```",
        "session    strdl   move      z  gap land",
        *(rows or ["no sessions recorded this week"]),
        "",
        "window          n   RMSz  >1sd   land  strdl$",
        _summary_line("this week", ws),
        _summary_line(f"cohort {cohort_start:%m-%d}+", cs),
        _summary_line("last 20 sess", ts),
        *(f"{name:<37} {rms:4.2f}   land {land:.0%}" for name, rms, land in REFERENCE_PERIODS),
        "```",
        "z = (close − 10:00 spot) / (1.25 × 10:00 ATM straddle). RMSz 1.0 = the chain priced "
        "the move correctly. land = close 0.9–2.3σ in the gap direction (the fly's profit zone). "
        "strdl$ = long 10:00 straddle held to close, pts. Diagnostic only; no rule uses it.",
    ]
    return "\n".join(lines)
