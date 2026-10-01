"""Decision profiles, session loading and entry rules.

A decision profile fixes what a replay could see and when: the decision clock, the
spot used for selection, the direction inputs (session open and prior close), any
narrowing of the exported chain, and session qualification. Named profiles:

- `frozen_20260921`: `run_backtest_db.py` at b83c2a18, the frozen execution-accounting
  replay (and the open cohort). Clock and spot are the replay's bars (every underlying
  snapshot that UTC day); the open is the first bar at or after 09:30 ET; the prior close
  is the last SPX spot tick at or before 16:00 ET on an earlier day.
- `live`: as `frozen_20260921` but with the official gap inputs of commit 67ba7ce, which
  live uses: `daily_bars` open and prior close, each falling back to the old source.
- `vendor_1m`: vendor history (`history.py`). Clock and spot are the vendor's 1-minute
  grid, 09:31 -> 16:00 ET (13:00 on early closes), stamped at each grid point (the time
  the quote state applied), with the vendor's SPX index level (or a flagged parity spot);
  official open and prior close from the vendor's index EOD; integer strikes;
  prerequisites as `live`.
- `sweep_20260925`: the idea-sweep numpy harness (`docs/research/spx-idea-sweep-2026-09-25`).
  Clock and spot are 0-DTE chain snapshots between 09:30 and 16:00 ET, integer strikes
  within 200 of spot; the open is the first SPX spot tick at or after 09:30 ET; the prior
  close comes from `daily_bars`; no minimum-snapshot rule. Timestamps are rounded to
  whole seconds, as that export's `extract(epoch ...)::bigint` did (so a 09:59:59.6
  snapshot counts as 10:00:00); rounding happens after the 09:30-16:00 filter.

Entry selection always goes through the live pure `select_entry_candidate`.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

import numpy as np

from butterfly_guy.core.config import AppConfig, VixWidthBucket, load_config
from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.research.dataset import Dataset, SessionChain
from butterfly_guy.research.exits import REGULAR_CLOSE
from butterfly_guy.research.holdout import Unseal, guard, in_holdout
from butterfly_guy.research.market import (
    EASTERN,
    DayMarket,
    Direction,
    Fly,
    et_us,
    restrict_view,
)
from butterfly_guy.strategy.butterfly_builder import (
    resolve_wing_widths_for_vix,
    vix_expected_move,
)
from butterfly_guy.strategy.entry_selection import select_entry_candidate

REPO_ROOT = Path(__file__).resolve().parents[3]
SPX_CONFIG = REPO_ROOT / "configs" / "config.yaml"


def load_spx_config(path: Path = SPX_CONFIG) -> AppConfig:
    return load_config(config_path=path)


@dataclass(frozen=True)
class DecisionProfile:
    name: str
    clock: Literal["bars", "chain"]
    open_source: Literal["first_bar", "first_spot_tick", "official"]
    prev_close_source: Literal["spot_tick_1600", "official"]
    strike_band: float | None = None
    integer_strikes: bool = False
    chain_window: tuple[tuple[int, int], tuple[int, int]] | None = None
    min_snapshots: int = 0
    require_replay_prerequisites: bool = False  # VIX at 10:00 bar and prior VIX close
    round_to_seconds: bool = False


PROFILES: dict[str, DecisionProfile] = {
    "frozen_20260921": DecisionProfile(
        name="frozen_20260921", clock="bars", open_source="first_bar",
        prev_close_source="spot_tick_1600", min_snapshots=50,
        require_replay_prerequisites=True,
    ),
    "live": DecisionProfile(
        name="live", clock="bars", open_source="official", prev_close_source="official",
        min_snapshots=50, require_replay_prerequisites=True,
    ),
    "sweep_20260925": DecisionProfile(
        name="sweep_20260925", clock="chain", open_source="first_spot_tick",
        prev_close_source="official", strike_band=200.0, integer_strikes=True,
        chain_window=((9, 30), (16, 0)), round_to_seconds=True,
    ),
    "vendor_1m": DecisionProfile(
        name="vendor_1m", clock="bars", open_source="official", prev_close_source="official",
        integer_strikes=True, min_snapshots=50, require_replay_prerequisites=True,
    ),
}


def round_to_seconds(ts_us: np.ndarray) -> np.ndarray:
    """Round epoch microseconds to whole seconds, half away from zero (numeric::bigint)."""
    return (np.floor(ts_us / 1e6 + 0.5) * 1_000_000).astype(np.int64)


class Series:
    """A sorted tick series with an at-or-before lookup."""

    def __init__(self, ts: np.ndarray, px: np.ndarray) -> None:
        self.ts, self.px = ts, px

    def at_or_before(self, ts_us: int, max_age_s: float | None = None) -> tuple[float, int] | None:
        i = int(np.searchsorted(self.ts, ts_us, side="right")) - 1
        if i < 0:
            return None
        if max_age_s is not None and ts_us - self.ts[i] > max_age_s * 1e6:
            return None
        return float(self.px[i]), int(self.ts[i])


@dataclass
class Session:
    """Everything a rule may see for one session under a profile."""

    date: dt.date
    market: DayMarket
    clock_ts: np.ndarray
    clock_spot: np.ndarray
    open: float
    prev_close: float
    close: float | None  # official same-session close (cash settlement), if recorded
    vix: Series
    profile: DecisionProfile
    # The session's scheduled close: the dataset's `session_close_et` where it records one
    # (vendor datasets: 13:00 on early closes), else 16:00.
    scheduled_close: dt.time = REGULAR_CLOSE
    cache: dict = field(default_factory=dict)

    def clock_index(self, ts_us: int) -> int:
        return int(np.searchsorted(self.clock_ts, ts_us, side="right")) - 1


class SessionLoader:
    """Build `Session`s from a dataset under one decision profile. Sessions in the sealed
    holdout (`holdout.py`) are refused unless a verified `unseal` is given."""

    def __init__(self, dataset: Dataset, profile: DecisionProfile,
                 unseal: Unseal | None = None, *, lifecycle: str = "0dte") -> None:
        self.lifecycle = lifecycle
        self.dataset = dataset
        self.profile = profile
        self.unseal = unseal
        bars = dataset.daily_bars()
        spx = bars[bars["underlying"] == dataset.manifest.underlying]
        vix = bars[bars["underlying"] == "$VIX"]
        self.opens = dict(zip(spx["date"], spx["open"], strict=True))
        self.closes = dict(zip(spx["date"], spx["close"], strict=True))
        self.vix_closes = dict(zip(vix["date"], vix["close"], strict=True))
        self.vix = Series(*self._ticks(dataset, "$VIX"))
        self.spx = Series(*self._ticks(dataset, dataset.manifest.underlying))
        self.sessions = dataset.sessions()
        self.scheduled_close: dict[dt.date, dt.time] = (
            {d: dt.time.fromisoformat(c) for d, c in zip(
                self.sessions["date"], self.sessions["session_close_et"], strict=True)
             if isinstance(c, str)}
            if "session_close_et" in self.sessions.columns else {})
        self.skipped: dict[dt.date, str] = {}

    def _ticks(self, dataset: Dataset, underlying: str) -> tuple[np.ndarray, np.ndarray]:
        ts, px = dataset.spot_ticks(underlying)
        return (round_to_seconds(ts), px) if self.profile.round_to_seconds else (ts, px)

    def dates(self, start: dt.date | None = None, end: dt.date | None = None) -> list[dt.date]:
        out = []
        for row in self.sessions.itertuples():
            d = row.date
            if (start and d < start) or (end and d > end):
                continue
            self._guard(d)
            if row.snapshots < self.profile.min_snapshots:
                self.skipped[d] = "too_few_snapshots"
                continue
            if self.profile.clock == "chain" and d not in self.closes:
                # The sweep harness only kept sessions with a known settlement.
                self.skipped[d] = "no_official_close"
                continue
            out.append(d)
        return out

    def _guard(self, d: dt.date) -> None:
        if in_holdout(d):
            guard(d, d, what=f"loading session {d}", dataset=self.dataset.name,
                  unseal=self.unseal)

    def _prev_close(self, d: dt.date, *, official: bool) -> float | None:
        if official:
            prior = [x for x in self.closes if x < d]
            if prior:
                return float(self.closes[max(prior)])
        # Last SPX spot tick at or before 16:00 ET on an earlier ET date.
        start_of_day = et_us(d, 0, 0)
        ts, px = self.spx.ts, self.spx.px
        i = int(np.searchsorted(ts, start_of_day, side="left")) - 1
        while i >= 0:
            local = dt.datetime.fromtimestamp(ts[i] / 1e6, tz=EASTERN)
            if local.time() <= dt.time(16, 0):
                return float(px[i])
            i -= 1
        return None

    def _chain(self, d: dt.date) -> SessionChain:
        chain = self.dataset.chain(d)
        p = self.profile
        if p.chain_window or p.strike_band is not None or p.integer_strikes:
            lo = et_us(d, *p.chain_window[0]) if p.chain_window else None
            hi = et_us(d, *p.chain_window[1]) if p.chain_window else None
            chain = restrict_view(chain, start_us=lo, end_us=hi, strike_band=p.strike_band,
                                  integer_strikes=p.integer_strikes)
        if p.round_to_seconds:
            chain.ts = round_to_seconds(chain.ts)
        return chain

    def load(self, d: dt.date) -> Session | None:
        self._guard(d)
        p = self.profile
        chain = self._chain(d)
        market = DayMarket(chain)
        if p.clock == "bars":
            clock = self.dataset.clock(d)
            clock_ts, clock_spot = clock.ts, clock.spot
        else:
            finite = np.isfinite(chain.spot)
            clock_ts, clock_spot = chain.ts[finite], chain.spot[finite]
        if len(clock_ts) == 0 or len(chain.ts) == 0:
            self.skipped[d] = "no_data"
            return None

        if chain.option_root and chain.expiration != d and self.lifecycle == "0dte":
            raise ValueError("1-DTE requires replay-local with an explicit lifecycle")

        if p.require_replay_prerequisites:
            # run_backtest_db.load_date_data needs chain rows in 09:30-15:30 ET.
            window = (chain.ts >= et_us(d, 9, 30)) & (chain.ts <= et_us(d, 15, 30))
            if not window.any():
                self.skipped[d] = "no_entry_chains"
                return None

        if p.open_source == "first_spot_tick":
            i = int(np.searchsorted(self.spx.ts, et_us(d, 9, 30), side="left"))
            if i >= len(self.spx.ts) or self.spx.ts[i] >= et_us(d, 16, 0):
                self.skipped[d] = "no_open"
                return None
            open_ = float(self.spx.px[i])
        else:
            j = int(np.searchsorted(clock_ts, et_us(d, 9, 30), side="left"))
            first_bar = float(clock_spot[j] if j < len(clock_ts) else clock_spot[0])
            open_ = first_bar
            if p.open_source == "official" and d in self.opens:
                open_ = float(self.opens[d])
        prev_close = self._prev_close(d, official=p.prev_close_source == "official")
        if prev_close is None:
            self.skipped[d] = "no_prev_close"
            return None

        if p.require_replay_prerequisites:
            j = int(np.searchsorted(clock_ts, et_us(d, 10, 0), side="left"))
            entry_bar_ts = int(clock_ts[j] if j < len(clock_ts) else clock_ts[0])
            if self.vix.at_or_before(entry_bar_ts) is None:
                self.skipped[d] = "no_vix"
                return None
            if not any(x < d for x in self.vix_closes):
                self.skipped[d] = "no_vix_prev_close"
                return None

        close = self.closes.get(d) if market.expiration == d else None
        return Session(
            date=d, market=market, clock_ts=clock_ts, clock_spot=clock_spot, open=open_,
            prev_close=prev_close, close=None if close is None else float(close),
            vix=self.vix, profile=p, scheduled_close=self.scheduled_close.get(d, REGULAR_CLOSE),
        )


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------


@dataclass
class Entry:
    fly: Fly
    ts_us: int  # decision time
    index: int  # snapshot at or before the decision
    cost: float  # selection mark cost (midpoint debit before commission)
    direction: Direction
    vix: float | None = None
    spot: float | None = None
    candidate: ButterflyCandidate | None = None
    tag: str = ""
    # The selector inputs when they differ from the run's config and the entry VIX (the
    # straddle anchor), so tie-set scoring replays the same selection.
    select_config: AppConfig | None = None
    select_vix: float | None = None
    # Learning rules: how many prior-session observations the decision used, and the
    # latest of their dates (always before the session).
    history_n: int | None = None
    history_last: dt.date | None = None


class EntryRule(Protocol):
    def entries(self, s: Session, ctx: RunContext) -> list[Entry]: ...


@dataclass
class RunContext:
    config: AppConfig
    asset: str = "SPX"
    # Pre-entry session features (`features.SessionFeatures`) for rules that use them;
    # a run records their input hashes only when a rule does (`uses_features`).
    features: object | None = None

    @property
    def max_vix_age_s(self) -> float:
        return float(self.config.entry.max_vix_age_seconds)

    def window(self, d: dt.date) -> tuple[int, int]:
        """Configured entry window (PT in config) as ET microsecond bounds, inclusive."""
        tz = self.config.entry.timezone
        from zoneinfo import ZoneInfo

        def at(hhmm: str) -> int:
            h, m = (int(x) for x in hhmm.split(":"))
            return int(dt.datetime(d.year, d.month, d.day, h, m, tzinfo=ZoneInfo(tz))
                       .timestamp()) * 1_000_000

        return at(self.config.entry.start_time), at(self.config.entry.end_time)


def gap_direction(s: Session) -> Direction:
    return "CALL" if s.open >= s.prev_close else "PUT"


def selection_span(config: AppConfig) -> float:
    """Strike span around spot that covers every strike the selector can touch."""
    widths = [w for b in config.strategy.vix_width_buckets for w in b.widths]
    widths += list(config.strategy.wing_widths)
    return float(config.strategy.spot_range + max(widths) + 5)


def select_at(
    s: Session, ctx: RunContext, ts_us: int, direction: Direction, vix: float | None,
    config: AppConfig | None = None,
) -> tuple[ButterflyCandidate | None, int, float]:
    """Run live selection on the snapshot at or before `ts_us` with the clock spot."""
    config = config or ctx.config
    i = s.market.at_or_before(ts_us)
    k = s.clock_index(ts_us)
    spot = float(s.clock_spot[k])
    if i < 0:
        return None, i, spot
    quotes = s.market.quotes_at(i, direction, near=spot, span=selection_span(config))
    result = select_entry_candidate(
        quotes=quotes, spot=spot, direction=direction, vix=vix, config=config, asset=ctx.asset,
    )
    return result.candidate, i, spot


@dataclass(frozen=True)
class BaselineEntry:
    """The frozen entry: first clock time in the configured window with a fresh VIX and a
    qualifying live-selected fly, in the gap direction (or a fixed/faded direction)."""

    direction: Literal["gap", "fade", "CALL", "PUT", "momentum"] = "gap"
    start_et: tuple[int, int] | None = None  # override the configured window start (ET)
    window_minutes: int | None = None  # override the configured window length

    def _direction(self, s: Session, window_start: int) -> Direction:
        if self.direction == "gap":
            return gap_direction(s)
        if self.direction == "fade":
            return "PUT" if gap_direction(s) == "CALL" else "CALL"
        if self.direction == "momentum":
            # Spot at the first clock time in the window versus the session open.
            k = int(np.searchsorted(s.clock_ts, window_start, side="left"))
            return "CALL" if s.clock_spot[min(k, len(s.clock_ts) - 1)] >= s.open else "PUT"
        return self.direction  # type: ignore[return-value]

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        lo, hi = ctx.window(s.date)
        if self.start_et is not None:
            lo = et_us(s.date, *self.start_et)
            hi = lo + (hi - ctx.window(s.date)[0])
        if self.window_minutes is not None:
            hi = lo + self.window_minutes * 60_000_000
        direction = self._direction(s, lo)
        for ts in s.clock_ts[(s.clock_ts >= lo) & (s.clock_ts <= hi)]:
            ts = int(ts)
            vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
            if vix is None:
                continue
            cand, i, spot = select_at(s, ctx, ts, direction, vix[0])
            if cand is not None:
                return [Entry(Fly.from_candidate(cand), ts, i, cand.cost, direction,
                              vix=vix[0], spot=spot, candidate=cand)]
        return []


@dataclass(frozen=True)
class FilteredEntry:
    """Keep the base rule's entry only when a named pre-entry predicate holds."""

    base: BaselineEntry
    predicate: str  # key into PREDICATES
    params: tuple[tuple[str, float], ...] = ()

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        fn = PREDICATES[self.predicate]
        kw = dict(self.params)
        return [e for e in self.base.entries(s, ctx) if fn(s, e, **kw)]


def _vix_at_least(s: Session, e: Entry, *, level: float) -> bool:
    return e.vix is not None and e.vix >= level


def _call_only(s: Session, e: Entry) -> bool:
    return e.direction == "CALL"


def _skip_low_vix_calls(s: Session, e: Entry, *, level: float) -> bool:
    return not (e.direction == "CALL" and e.vix is not None and e.vix < level)


PREDICATES = {
    "vix_at_least": _vix_at_least,
    "call_only": _call_only,
    "skip_low_vix_calls": _skip_low_vix_calls,
}


def cached_entries(s: Session, ctx: RunContext, rule: EntryRule) -> list[Entry]:
    """A stateless rule's entries, cached per session so every variant (and every rule
    wrapping it) sees the exact same decisions."""
    key = ("entries", rule)
    if key not in s.cache:
        s.cache[key] = rule.entries(s, ctx)
    return s.cache[key]


def baseline_window(rule: BaselineEntry, s: Session, ctx: RunContext) -> tuple[int, int]:
    """`BaselineEntry`'s decision window (its start/length overrides applied)."""
    lo, hi = ctx.window(s.date)
    if rule.start_et is not None:
        lo = et_us(s.date, *rule.start_et)
        hi = lo + (hi - ctx.window(s.date)[0])
    if rule.window_minutes is not None:
        hi = lo + rule.window_minutes * 60_000_000
    return lo, hi


def straddle_selection(config: AppConfig, vix: float, spot: float, move: float
                       ) -> tuple[AppConfig, float]:
    """Selector inputs that place centers by `move` instead of the VIX-implied move while
    keeping the entry VIX's width bucket: a one-bucket config holding that bucket's widths
    (so its positional sigmas are unchanged) and the VIX whose implied move is `move`."""
    widths, _ = resolve_wing_widths_for_vix(vix, config.strategy.vix_width_buckets)
    strategy = config.strategy.model_copy(update={
        "vix_width_buckets": [VixWidthBucket(vix_max=9999.0, widths=list(widths))]})
    return config.model_copy(update={"strategy": strategy}), move / vix_expected_move(1.0, spot)


@dataclass(frozen=True)
class StraddleAnchoredEntry:
    """The baseline entry with centers anchored on the chain-implied remaining move,
    `multiple` x the ATM straddle mark, instead of the VIX daily move (idea sweep C1/C2
    and, with a later window, T1-T6). Widths still come from the entry VIX bucket, and
    selection still runs through the live selector. A snapshot without a straddle is
    skipped."""

    base: BaselineEntry = BaselineEntry()
    multiple: float = 1.25

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        lo, hi = baseline_window(self.base, s, ctx)
        direction = self.base._direction(s, lo)
        for ts in s.clock_ts[(s.clock_ts >= lo) & (s.clock_ts <= hi)]:
            ts = int(ts)
            vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
            if vix is None:
                continue
            i = s.market.at_or_before(ts)
            straddle = s.market.atm_straddle(i) if i >= 0 else None
            if straddle is None:
                continue
            spot = float(s.clock_spot[s.clock_index(ts)])
            config, anchor_vix = straddle_selection(ctx.config, vix[0], spot,
                                                    self.multiple * straddle)
            cand, i, spot = select_at(s, ctx, ts, direction, anchor_vix, config=config)
            if cand is not None:
                return [Entry(Fly.from_candidate(cand), ts, i, cand.cost, direction,
                              vix=vix[0], spot=spot, candidate=cand, tag="straddle",
                              select_config=config, select_vix=anchor_vix)]
        return []


@dataclass(frozen=True)
class ATMEntry:
    """Idea sweep D4: a call fly centered on the strike step nearest spot, with the middle
    width of the entry VIX bucket, at the first window time with a fresh VIX whose fly is
    observed. Not selected by the live selector (no tie-set)."""

    strike_step: int = 5

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        lo, hi = ctx.window(s.date)
        buckets = ctx.config.strategy.vix_width_buckets
        for ts in s.clock_ts[(s.clock_ts >= lo) & (s.clock_ts <= hi)]:
            ts = int(ts)
            vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
            i = s.market.at_or_before(ts)
            if vix is None or i < 0:
                continue
            widths, _ = resolve_wing_widths_for_vix(vix[0], buckets)
            w = widths[len(widths) // 2]
            spot = float(s.market.spot[i])
            c = float(round(spot / self.strike_step) * self.strike_step)
            fly = Fly("CALL", c - w, c, c + w)
            path = s.market.fly_path(fly)
            if path is None or not path.observed[i]:
                continue
            return [Entry(fly, ts, i, float(path.mark[i]), "CALL", vix=vix[0], spot=spot,
                          tag="ATM")]
        return []


@dataclass(frozen=True)
class BothSides:
    """Every entry of each rule on the same session (idea sweep D3: the baseline call fly
    and the baseline put fly). The session's P&L is the sum of its trades."""

    rules: tuple[BaselineEntry, ...] = (BaselineEntry(direction="CALL"),
                                        BaselineEntry(direction="PUT"))

    def entries(self, s: Session, ctx: RunContext) -> list[Entry]:
        return [e for rule in self.rules for e in cached_entries(s, ctx, rule)]
