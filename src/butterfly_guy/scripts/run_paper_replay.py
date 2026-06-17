"""Historical paper trading replay.

Replays real DB chain snapshots through the exact OrderManager paper-path
logic to validate entry/exit ladder mechanics on historical data.

Each ladder step consumes the next DB snapshot, and asyncio.sleep is simulated
by advancing the snapshot index — no real sleeping, no real network calls.

Only runs on days with complete data (first snapshot at or before 09:35 ET),
auto-detected from the database. Set DATES to override.

Usage:
    uv run python -m butterfly_guy.scripts.run_paper_replay
"""

# Console report strings in this standalone diagnostic script intentionally exceed 100 columns.
# ruff: noqa: E501

from __future__ import annotations

import asyncio
import datetime as dt
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg
import yfinance as yf

from butterfly_guy.backtest.data_loader import MinuteBar
from butterfly_guy.core.config import StrategySettings, load_config
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.butterfly_builder import (
    VIX_SIGMA_BY_WIDTH,
    ButterflyBuilder,
    vix_expected_move,
    vix_target_center,
)
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_paper_replay")

EASTERN = ZoneInfo("America/New_York")


def resolve_db_dsn() -> str:
    return load_config().database.dsn

# ─────────────────────────────────────────────────────────────────────────── #
#  Config — edit these to change the replay                                   #
# ─────────────────────────────────────────────────────────────────────────── #
# DATES: leave empty [] to auto-detect complete days from DB
DATES: list[dt.date] = []
ASSET = "SPX"
WING_WIDTH = 20
DIRECTION: str | None = None   # None = gap-based bias filter; "CALL"/"PUT" to force
RR_MIN = 8.0
PRICE_LADDER_STEP = 0.05
PRICE_LADDER_STEPS = 4
ORDER_TIMEOUT_SECONDS = 300
SNAPSHOT_INTERVAL_SECONDS = 30   # approximate gap between DB snapshots (~31s measured)
RETRY_INTERVAL_SECONDS = 20      # mirrors ExecutionSettings.retry_interval_seconds

# Profit management drawdown thresholds (mirrors config.yaml)
MORNING_DD = 0.60        # 0–120 min after open
LATE_MORNING_DD = 0.60   # 120–240 min after open
AFTERNOON_DD = 0.40      # 240+ min after open
EXIT_BEFORE_CLOSE_MINUTES = 0
MAX_LOSS_FROM_COST = 0.50   # exit if position loses 50% of cost (no prior profit required)

# Print a monitoring update every N snapshots during position hold (~30s each)
MONITOR_PRINT_EVERY = 10  # ~5 min; regime changes and exit triggers always print
# ─────────────────────────────────────────────────────────────────────────── #

_SNAPS_PER_STEP = max(1, round(RETRY_INTERVAL_SECONDS / SNAPSHOT_INTERVAL_SECONDS))
_MAX_OUTER = (ORDER_TIMEOUT_SECONDS // (PRICE_LADDER_STEPS * RETRY_INTERVAL_SECONDS)) + 2

MARKET_OPEN = dt.time(9, 30)
MARKET_CLOSE = dt.time(16, 0)


# ─── Data types ─────────────────────────────────────────────────────────── #

class LiveSpread(NamedTuple):
    bid: float
    mark: float
    ask: float


@dataclass
class StepLog:
    step: int
    ladder_i: int
    limit: float
    bid: float | None
    mark: float | None
    ask: float | None
    filled: bool
    snap_time: dt.datetime | None = None


@dataclass
class MonitorStep:
    snap_time: dt.datetime
    current_value: float
    peak_value: float
    drawdown_pct: float
    threshold: float
    regime: str
    mins_since_open: float
    mins_to_close: float


# ─── ReplaySchwab ────────────────────────────────────────────────────────── #

class ReplaySchwab:
    """Serves chain snapshots sequentially, advancing with each ladder step."""

    def __init__(self, snapshots: list[tuple[dt.datetime, list[OptionQuote]]]) -> None:
        self._snaps = snapshots
        self._idx = 0

    def get_spread(self, candidate: ButterflyCandidate) -> LiveSpread | None:
        if not self._snaps:
            return None
        _, quotes = self._snaps[min(self._idx, len(self._snaps) - 1)]
        return _compute_spread(quotes, candidate)

    def get_quotes(self) -> list[OptionQuote]:
        if not self._snaps:
            return []
        _, quotes = self._snaps[min(self._idx, len(self._snaps) - 1)]
        return quotes

    def advance(self, n: int = 1) -> None:
        self._idx = min(self._idx + n, len(self._snaps) - 1)

    def seek_to_time(self, ts: dt.datetime) -> None:
        for i, (snap_ts, _) in enumerate(self._snaps):
            if snap_ts >= ts:
                self._idx = i
                return
        self._idx = len(self._snaps) - 1

    @property
    def current_time(self) -> dt.datetime | None:
        if not self._snaps:
            return None
        return self._snaps[min(self._idx, len(self._snaps) - 1)][0]

    def exhausted(self) -> bool:
        return self._idx >= len(self._snaps) - 1


# ─── Spread helpers ──────────────────────────────────────────────────────── #

def _compute_spread(
    quotes: list[OptionQuote], candidate: ButterflyCandidate
) -> LiveSpread | None:
    by_strike = {q.strike: q for q in quotes if q.option_type == candidate.direction}
    lo, ce, up = candidate.lower_strike, candidate.center_strike, candidate.upper_strike
    if lo not in by_strike or ce not in by_strike or up not in by_strike:
        return None
    lo_q, ce_q, up_q = by_strike[lo], by_strike[ce], by_strike[up]
    spread_bid = lo_q.bid + up_q.bid - 2 * ce_q.ask
    spread_mark = lo_q.mark + up_q.mark - 2 * ce_q.mark
    spread_ask = lo_q.ask + up_q.ask - 2 * ce_q.bid
    if spread_mark <= 0:
        return None
    return LiveSpread(
        bid=round(spread_bid, 4),
        mark=round(spread_mark, 4),
        ask=round(spread_ask, 4),
    )


def _butterfly_value(quotes: list[OptionQuote], candidate: ButterflyCandidate) -> float | None:
    """Mark-based mid value of the butterfly (used for P&L monitoring)."""
    by_strike = {q.strike: q for q in quotes if q.option_type == candidate.direction}
    lo_q = by_strike.get(candidate.lower_strike)
    ce_q = by_strike.get(candidate.center_strike)
    up_q = by_strike.get(candidate.upper_strike)
    if not (lo_q and ce_q and up_q):
        return None
    val = lo_q.mark - 2 * ce_q.mark + up_q.mark
    return max(0.0, round(val, 4))


# ─── DB loaders ──────────────────────────────────────────────────────────── #

async def detect_complete_days(conn: asyncpg.Connection, asset: str = ASSET) -> list[dt.date]:
    """Return 0-DTE days where first snapshot is at or before 09:35 ET."""
    rows = await conn.fetch(
        """
        SELECT
            snapshot_time::date AS day,
            MIN(snapshot_time AT TIME ZONE 'America/New_York') AS first_snap,
            MAX(snapshot_time AT TIME ZONE 'America/New_York') AS last_snap,
            COUNT(DISTINCT snapshot_time) AS snap_count
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = snapshot_time::date
        GROUP BY 1
        ORDER BY 1
        """,
        asset,
    )
    complete = []
    for r in rows:
        first_et = r["first_snap"]
        if first_et.hour < 9 or (first_et.hour == 9 and first_et.minute <= 35):
            complete.append(r["day"])
    return complete


async def load_chains_from_db(
    conn: asyncpg.Connection, date: dt.date, asset: str = ASSET
) -> dict[dt.datetime, list[OptionQuote]]:
    rows = await conn.fetch(
        """
        SELECT snapshot_time, strike, option_type, bid, ask, mark, last,
               volume, open_interest, iv, delta, gamma, theta, vega, symbol, spot_price
        FROM option_chain_snapshots
        WHERE underlying = $2
          AND expiration = $1
          AND snapshot_time::date = $1
        ORDER BY snapshot_time, strike, option_type
        """,
        date, asset,
    )
    chains: dict[dt.datetime, list[OptionQuote]] = defaultdict(list)
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        chains[ts].append(
            OptionQuote(
                symbol=r["symbol"] or f"DB_{r['option_type'][0]}{int(r['strike'])}",
                underlying=asset,
                expiration=date,
                strike=float(r["strike"]),
                option_type=r["option_type"],
                bid=float(r["bid"] or 0),
                ask=float(r["ask"] or 0),
                mark=float(r["mark"] or 0),
                last=float(r["last"] or 0),
                volume=int(r["volume"] or 0),
                open_interest=int(r["open_interest"] or 0),
                iv=float(r["iv"] or 0),
                delta=float(r["delta"] or 0),
                gamma=float(r["gamma"] or 0),
                theta=float(r["theta"] or 0),
                vega=float(r["vega"] or 0),
            )
        )
    return dict(chains)


async def load_bars_from_db(
    conn: asyncpg.Connection, date: dt.date, asset: str = ASSET
) -> list[MinuteBar]:
    rows = await conn.fetch(
        """
        SELECT DISTINCT ON (snapshot_time)
            snapshot_time,
            spot_price
        FROM option_chain_snapshots
        WHERE underlying = $2
          AND snapshot_time::date = $1
          AND spot_price IS NOT NULL
          AND spot_price > 0
        ORDER BY snapshot_time
        """,
        date, asset,
    )
    bars: list[MinuteBar] = []
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        price = float(r["spot_price"])
        bars.append(MinuteBar(ts=ts, open=price, high=price, low=price, close=price, volume=0))
    return bars


def get_prev_close(date: dt.date) -> float:
    start = date - dt.timedelta(days=7)
    hist = yf.Ticker("^GSPC").history(start=start, end=date, interval="1d")
    if not hist.empty:
        return float(hist["Close"].iloc[-1])
    return 5500.0


def get_vix(date: dt.date) -> float:
    end = date + dt.timedelta(days=1)
    hist = yf.Ticker("^VIX").history(start=date, end=end, interval="1d")
    if not hist.empty:
        return float(hist["Close"].iloc[0])
    return 18.0


# ─── Entry candidate finder ──────────────────────────────────────────────── #

@dataclass
class EntryDecision:
    candidate: ButterflyCandidate
    entry_ts: dt.datetime
    spot: float
    prev_close: float
    vix: float
    direction: str
    gap_pts: float
    gap_pct: float
    expected_move: float
    target_center: float
    sigma_fraction: float
    all_candidates: list[ButterflyCandidate]


def find_entry_candidate(
    chains: dict[dt.datetime, list[OptionQuote]],
    bars: list[MinuteBar],
    vix: float,
    prev_close: float,
    date: dt.date,
) -> EntryDecision | None:
    """Find best candidate in the 10:00–10:30 ET window, returning full decision context."""
    start_utc = dt.datetime(date.year, date.month, date.day, 10, 0, 0,
                            tzinfo=EASTERN).astimezone(dt.timezone.utc)
    end_utc = dt.datetime(date.year, date.month, date.day, 10, 30, 0,
                          tzinfo=EASTERN).astimezone(dt.timezone.utc)

    entry_snaps = [(ts, q) for ts, q in sorted(chains.items())
                   if start_utc <= ts <= end_utc]
    if not entry_snaps:
        before = [(ts, q) for ts, q in sorted(chains.items()) if ts <= end_utc]
        if not before:
            return None
        entry_snaps = [before[-1]]

    entry_ts, entry_quotes = entry_snaps[0]

    bar_before = [b for b in bars if b.ts <= entry_ts]
    if not bar_before:
        bar_before = bars[:1]
    if not bar_before:
        return None
    spot = bar_before[-1].close

    if DIRECTION is not None:
        direction = DIRECTION
    else:
        direction = DirectionFilter().get_direction(spot, prev_close)

    gap_pts = spot - prev_close
    gap_pct = gap_pts / prev_close * 100

    settings = StrategySettings(wing_widths=[WING_WIDTH], rr_min=RR_MIN, spot_range=150)
    builder = ButterflyBuilder(settings)
    all_candidates = builder.build_candidates(entry_quotes, spot, direction)
    if not all_candidates:
        return None

    expected_move = vix_expected_move(vix, spot)
    sigma_fraction = VIX_SIGMA_BY_WIDTH.get(WING_WIDTH, 0.50)
    target_center = vix_target_center(
        vix=vix, spot=spot, direction=direction, wing_width=WING_WIDTH
    )

    best = ButterflySelector(settings).select_best(
        all_candidates,
        target_center=target_center,
    )
    if not best:
        return None

    return EntryDecision(
        candidate=best,
        entry_ts=entry_ts,
        spot=spot,
        prev_close=prev_close,
        vix=vix,
        direction=direction,
        gap_pts=gap_pts,
        gap_pct=gap_pct,
        expected_move=expected_move,
        target_center=target_center,
        sigma_fraction=sigma_fraction,
        all_candidates=all_candidates,
    )


# ─── Regime helpers ──────────────────────────────────────────────────────── #

def _regime_for(mins_since_open: float) -> tuple[str, float]:
    """Return (regime_name, drawdown_threshold) for minutes since open."""
    if mins_since_open < 120:
        return "morning", MORNING_DD
    elif mins_since_open < 240:
        return "late_morning", LATE_MORNING_DD
    else:
        return "afternoon", AFTERNOON_DD


def _mins_since_open(ts: dt.datetime, date: dt.date) -> float:
    open_dt = dt.datetime(date.year, date.month, date.day, 9, 30, tzinfo=EASTERN)
    return (ts.astimezone(EASTERN) - open_dt).total_seconds() / 60.0


def _mins_to_close(ts: dt.datetime, date: dt.date) -> float:
    close_dt = dt.datetime(date.year, date.month, date.day, 16, 0, tzinfo=EASTERN)
    return (close_dt - ts.astimezone(EASTERN)).total_seconds() / 60.0


# ─── Ladder replay ───────────────────────────────────────────────────────── #

def replay_entry_ladder(
    replay: ReplaySchwab,
    candidate: ButterflyCandidate,
) -> tuple[dict | None, list[StepLog]]:
    steps: list[StepLog] = []
    price_floor: float | None = None
    total_step = 0

    for _outer in range(_MAX_OUTER):
        for i in range(PRICE_LADDER_STEPS):
            spread = replay.get_spread(candidate)
            if spread is not None:
                price_floor = spread.mark if price_floor is None else max(price_floor, spread.mark)
            mid_price = price_floor if price_floor is not None else candidate.cost

            limit_price = round(mid_price + i * PRICE_LADDER_STEP, 2)
            filled = spread is not None and limit_price >= spread.ask

            steps.append(StepLog(
                step=total_step,
                ladder_i=i,
                limit=limit_price,
                bid=spread.bid if spread else None,
                mark=spread.mark if spread else None,
                ask=spread.ask if spread else None,
                filled=filled,
                snap_time=replay.current_time,
            ))

            if filled:
                return {"fill_price": limit_price, "step": total_step}, steps

            replay.advance(_SNAPS_PER_STEP)
            total_step += 1

            if replay.exhausted():
                return None, steps

    return None, steps


def replay_exit_ladder(
    replay: ReplaySchwab,
    candidate: ButterflyCandidate,
    entry_fill_price: float,
) -> tuple[dict | None, list[StepLog]]:
    steps: list[StepLog] = []
    price_ceiling: float | None = None
    total_step = 0

    for _outer in range(_MAX_OUTER):
        for i in range(PRICE_LADDER_STEPS):
            spread = replay.get_spread(candidate)
            if spread is not None:
                price_ceiling = spread.bid if price_ceiling is None else min(price_ceiling, spread.bid)
            mid_price = price_ceiling if price_ceiling is not None else entry_fill_price

            limit_price = round(
                max(0.05, mid_price + (PRICE_LADDER_STEPS - 1 - i) * PRICE_LADDER_STEP), 2
            )
            filled = spread is not None and limit_price <= spread.bid

            steps.append(StepLog(
                step=total_step,
                ladder_i=i,
                limit=limit_price,
                bid=spread.bid if spread else None,
                mark=spread.mark if spread else None,
                ask=spread.ask if spread else None,
                filled=filled,
                snap_time=replay.current_time,
            ))

            if filled:
                return {"fill_price": limit_price, "step": total_step}, steps

            replay.advance(_SNAPS_PER_STEP)
            total_step += 1

            if replay.exhausted():
                return None, steps

    # Ladder exhausted without fill — force-fill at current bid (safety fallback)
    spread = replay.get_spread(candidate)
    force_bid = spread.bid if spread and spread.bid and spread.bid > 0 else 0.05
    print(f"  *** FORCED EXIT AT BID — ladder exhausted after {total_step} steps; fill at {force_bid:.2f} ***")
    return {
        "fill_price": round(force_bid, 2),
        "step": total_step,
        "force_fill": True,
    }, steps


# ─── Profit management monitor ───────────────────────────────────────────── #

@dataclass
class MonitorResult:
    exit_reason: str          # "drawdown_morning" / "drawdown_late_morning" / "drawdown_afternoon" / "end_of_day"
    trigger_time: dt.datetime
    trigger_value: float
    peak_value: float
    steps: list[MonitorStep]


def monitor_position(
    replay: ReplaySchwab,
    candidate: ButterflyCandidate,
    entry_fill_price: float,
    date: dt.date,
) -> MonitorResult:
    """
    Walk forward through snapshots after entry fill, computing butterfly value
    and checking drawdown / EOD exit conditions — exactly as the live system does.
    """
    steps: list[MonitorStep] = []
    peak_value = entry_fill_price
    snap_counter = 0
    prev_regime = ""

    while not replay.exhausted():
        replay.advance(1)
        snap_counter += 1
        snap_time = replay.current_time
        if snap_time is None:
            break

        quotes = replay.get_quotes()
        val = _butterfly_value(quotes, candidate)
        if val is None:
            val = peak_value  # hold last known if strikes drop out of chain

        peak_value = max(peak_value, val)
        drawdown = (peak_value - val) / peak_value if peak_value > 0 else 0.0

        mins_open = _mins_since_open(snap_time, date)
        mins_close = _mins_to_close(snap_time, date)
        regime, threshold = _regime_for(mins_open)

        step = MonitorStep(
            snap_time=snap_time,
            current_value=val,
            peak_value=peak_value,
            drawdown_pct=drawdown,
            threshold=threshold,
            regime=regime,
            mins_since_open=mins_open,
            mins_to_close=mins_close,
        )

        regime_changed = regime != prev_regime
        at_print_interval = snap_counter % MONITOR_PRINT_EVERY == 0

        # Optional pre-close exit; disabled by default for cash-settled indexes.
        if EXIT_BEFORE_CLOSE_MINUTES > 0 and mins_close <= EXIT_BEFORE_CLOSE_MINUTES:
            steps.append(step)
            _print_monitor_step(step, trigger="EOD EXIT")
            return MonitorResult(
                exit_reason="end_of_day",
                trigger_time=snap_time,
                trigger_value=val,
                peak_value=peak_value,
                steps=steps,
            )

        # Absolute loss stop — fires regardless of peak (no prior profit required)
        loss_from_cost = (entry_fill_price - val) / entry_fill_price if entry_fill_price > 0 else 0.0
        if loss_from_cost >= MAX_LOSS_FROM_COST:
            steps.append(step)
            _print_monitor_step(
                step,
                trigger=f"ABSOLUTE LOSS STOP ({loss_from_cost*100:.1f}% of cost lost)"
            )
            return MonitorResult(
                exit_reason="absolute_loss_stop",
                trigger_time=snap_time,
                trigger_value=val,
                peak_value=peak_value,
                steps=steps,
            )

        # Drawdown exit (only after we've been in profit)
        if peak_value > entry_fill_price and drawdown >= threshold:
            steps.append(step)
            _print_monitor_step(
                step,
                trigger=f"DRAWDOWN EXIT ({drawdown*100:.1f}% >= {threshold*100:.0f}% threshold)"
            )
            return MonitorResult(
                exit_reason=f"drawdown_{regime}",
                trigger_time=snap_time,
                trigger_value=val,
                peak_value=peak_value,
                steps=steps,
            )

        # Print periodic updates
        if regime_changed or at_print_interval:
            trigger_note = f"[regime → {regime}]" if regime_changed else None
            steps.append(step)
            _print_monitor_step(step, trigger=trigger_note)
        else:
            steps.append(step)

        prev_regime = regime

    # Exhausted snapshots without hitting a trigger
    last = steps[-1] if steps else MonitorStep(
        snap_time=replay.current_time or dt.datetime.now(dt.timezone.utc),
        current_value=entry_fill_price,
        peak_value=peak_value,
        drawdown_pct=0.0,
        threshold=AFTERNOON_DD,
        regime="afternoon",
        mins_since_open=390,
        mins_to_close=0,
    )
    return MonitorResult(
        exit_reason="end_of_day",
        trigger_time=last.snap_time,
        trigger_value=last.current_value,
        peak_value=peak_value,
        steps=steps,
    )


# ─── Output helpers ──────────────────────────────────────────────────────── #

def _et(ts: dt.datetime) -> str:
    return ts.astimezone(EASTERN).strftime("%H:%M:%S")


def _print_monitor_step(step: MonitorStep, trigger: str | None = None) -> None:
    dd_str = f"{step.drawdown_pct*100:.1f}%"
    thr_str = f"{step.threshold*100:.0f}%"
    flag = f"  ← {trigger}" if trigger else ""
    print(
        f"    {_et(step.snap_time)} ET  [{step.regime:12s} {step.mins_since_open:5.1f}min]"
        f"  val={step.current_value:.2f}  peak={step.peak_value:.2f}"
        f"  DD={dd_str:>5} / {thr_str} limit{flag}"
    )


def _print_step(s: StepLog) -> None:
    b = f"{s.bid:.2f}" if s.bid is not None else " N/A"
    m = f"{s.mark:.2f}" if s.mark is not None else " N/A"
    a = f"{s.ask:.2f}" if s.ask is not None else " N/A"
    result = "→ FILLED" if s.filled else "→ no fill"
    snap = f"  [{_et(s.snap_time)} ET]" if s.snap_time else ""
    print(f"    Step {s.step:2d} (i={s.ladder_i}): limit={s.limit:.2f}"
          f"  bid={b}  mark={m}  ask={a}  {result}{snap}")


def _elapsed(steps: list[StepLog], fill_step: int) -> str:
    if not steps:
        return "?"
    t0 = steps[0].snap_time
    t1 = steps[fill_step].snap_time if fill_step < len(steps) else steps[-1].snap_time
    if t0 and t1:
        secs = (t1 - t0).total_seconds()
        return f"~{secs:.0f}s (~{secs/60:.1f}m)"
    secs = fill_step * _SNAPS_PER_STEP * SNAPSHOT_INTERVAL_SECONDS
    return f"~{secs}s (~{secs/60:.1f}m, estimated)"


# ─── Per-day replay ──────────────────────────────────────────────────────── #

async def replay_day(conn: asyncpg.Connection, date: dt.date) -> None:
    chains = await load_chains_from_db(conn, date)
    bars = await load_bars_from_db(conn, date)

    if not chains or not bars:
        print(f"\n  {date}: no data in DB — skipping")
        return

    prev_close, vix = await asyncio.gather(
        asyncio.to_thread(get_prev_close, date),
        asyncio.to_thread(get_vix, date),
    )

    sorted_snaps = sorted(chains.items())
    snap_count = len(chains)
    bar_range = (
        f"{bars[0].ts.astimezone(EASTERN).strftime('%H:%M')}"
        f"–{bars[-1].ts.astimezone(EASTERN).strftime('%H:%M')} ET"
    )
    spx_lo = min(b.close for b in bars)
    spx_hi = max(b.close for b in bars)

    print(f"\n{'='*76}")
    print(f"  PAPER REPLAY — {date}")
    print(f"  {snap_count} snapshots  |  {bar_range}  |  SPX range {spx_lo:.0f}–{spx_hi:.0f}")
    print(f"{'='*76}")

    # ── DIRECTION DECISION ───────────────────────────────────────────────── #
    decision = find_entry_candidate(chains, bars, vix, prev_close, date)

    # Print direction context even if no candidate found
    if decision:
        spot = decision.spot
        gap_pts = decision.gap_pts
        gap_pct = decision.gap_pct
        direction = decision.direction
    else:
        # Still show direction logic from first bar near open
        open_utc = dt.datetime(date.year, date.month, date.day, 9, 30, tzinfo=EASTERN).astimezone(dt.timezone.utc)
        early_bars = [b for b in bars if b.ts >= open_utc]
        spot = early_bars[0].close if early_bars else bars[0].close
        gap_pts = spot - prev_close
        gap_pct = gap_pts / prev_close * 100
        direction = "CALL" if spot >= prev_close else "PUT"

    gap_sign = "+" if gap_pts >= 0 else ""
    dir_reason = "above prev close → bullish bias → CALL fly" if direction == "CALL" \
        else "below prev close → bearish bias → PUT fly"
    print("\n  DIRECTION")
    print(f"    Prev close : SPX {prev_close:.2f}")
    print(f"    Open spot  : SPX {spot:.2f}  ({gap_sign}{gap_pts:.2f}pts, {gap_sign}{gap_pct:.2f}%)")
    print(f"    Decision   : {direction}  [{dir_reason}]")
    if DIRECTION:
        print(f"    Override   : forced to {DIRECTION}")

    # ── VIX / EXPECTED MOVE ─────────────────────────────────────────────── #
    if decision:
        em = decision.expected_move
        sf = decision.sigma_fraction
        tc = decision.target_center
        print("\n  VIX & CENTER TARGETING")
        print(f"    VIX        : {vix:.2f}")
        print(f"    Exp. move  : ±{em:.1f}pts  (SPX × VIX/100 ÷ √252)")
        print(f"    Sigma frac : {sf:.2f}  (from VIX_SIGMA_BY_WIDTH[{WING_WIDTH}])")
        offset = em * sf
        raw = spot + offset if direction == "CALL" else spot - offset
        print(f"    Target ctr : {spot:.0f} {'+'if direction=='CALL' else '-'} {offset:.1f}pts = {raw:.1f} → rounded to {tc:.0f}")

    # ── CANDIDATE SELECTION ──────────────────────────────────────────────── #
    if decision:
        all_c = decision.all_candidates
        best = decision.candidate
        tc = decision.target_center
        tol = 15.0

        print(f"\n  CANDIDATE POOL  ({len(all_c)} total, {WING_WIDTH}-wide {direction}, RR≥{RR_MIN})")
        print(f"    {'Strike':>8}  {'Cost':>5}  {'RR':>6}  {'Dist':>5}  {'|Δ ctr|':>7}  Note")
        print(f"    {'-'*60}")
        shown = sorted(all_c, key=lambda c: abs(c.center_strike - tc))[:10]
        for c in shown:
            delta_ctr = abs(c.center_strike - tc)
            in_win = delta_ctr <= tol
            note = ""
            if c is best:
                note = "← SELECTED (farthest OTM valid candidate in VIX window)"
            elif not in_win:
                note = f"outside ±{tol:.0f}pt VIX window"
            print(
                f"    {c.center_strike:>8.0f}  {c.cost:>5.2f}  {c.reward_risk:>6.1f}x"
                f"  {c.distance_from_spot:>4.0f}pt  {delta_ctr:>6.0f}pt  {note}"
            )
        if len(all_c) > 10:
            print(f"    ... {len(all_c)-10} more candidates not shown")

        entry_et = _et(decision.entry_ts)
        struct = (
            f"{best.lower_strike:.0f} / {best.center_strike:.0f} / {best.upper_strike:.0f}"
        )
        print(f"\n  SELECTED: {struct} {direction}")
        print(f"    Entry snap : {entry_et} ET")
        print(f"    Cost (mark): ${best.cost:.2f}   RR={best.reward_risk:.1f}x"
              f"   Max profit=${best.max_profit:.2f}")
        print(f"    Break-evens: {best.lower_be:.0f} / {best.upper_be:.0f}")
        print(f"    Distance   : {best.distance_from_spot:.0f}pts from spot")

    if decision is None:
        print(f"\n  NO CANDIDATE — no qualifying {WING_WIDTH}-wide {direction} fly"
              f" found in 10:00–10:30 ET window.")
        return

    # ── ENTRY LADDER ─────────────────────────────────────────────────────── #
    replay = ReplaySchwab(sorted_snaps)
    replay.seek_to_time(decision.entry_ts)

    print(f"\n  ENTRY LADDER  (starting {_et(decision.entry_ts)} ET)")
    print("    Logic: offer at mark+0, mark+0.05, mark+0.10, mark+0.15")
    print("           fill when limit ≥ ask; ratchets mark floor up if spread moves")
    entry_fill, entry_steps = replay_entry_ladder(replay, decision.candidate)

    for s in entry_steps:
        _print_step(s)

    if entry_fill is None:
        sims = len(entry_steps) * RETRY_INTERVAL_SECONDS
        print(f"\n  TIMEOUT — no entry fill after {len(entry_steps)} steps (~{sims}s)")
        return

    elapsed = _elapsed(entry_steps, entry_fill["step"])
    fill_et = f"  [{_et(entry_steps[-1].snap_time)} ET]" if entry_steps and entry_steps[-1].snap_time else ""
    print(f"\n  ENTRY FILLED: ${entry_fill['fill_price']:.2f}  (step {entry_fill['step']}, {elapsed}){fill_et}")

    # ── PROFIT MANAGEMENT MONITOR ────────────────────────────────────────── #
    print(f"\n  POSITION MONITOR  (holding from {_et(entry_steps[-1].snap_time) if entry_steps and entry_steps[-1].snap_time else '?'} ET)")
    print(f"    Regimes: morning DD≥{MORNING_DD*100:.0f}%  |"
          f"  late_morning DD≥{LATE_MORNING_DD*100:.0f}%  |"
          f"  afternoon DD≥{AFTERNOON_DD*100:.0f}%")
    if EXIT_BEFORE_CLOSE_MINUTES > 0:
        print(f"    EOD exit {EXIT_BEFORE_CLOSE_MINUTES}min before 16:00 ET")
    else:
        print("    EOD pre-close exit disabled; monitor runs to 16:00 ET")
    print(f"    (printing every ~{MONITOR_PRINT_EVERY*30//60}min; regime changes always shown)")
    print()

    monitor = monitor_position(replay, decision.candidate, entry_fill["fill_price"], date)

    trigger_et = _et(monitor.trigger_time)
    print(f"\n  EXIT TRIGGER: {monitor.exit_reason}  at {trigger_et} ET")
    print(f"    Peak value  : ${monitor.peak_value:.2f}  (entry cost ${entry_fill['fill_price']:.2f})")
    print(f"    Value at exit trigger: ${monitor.trigger_value:.2f}")

    # ── EXIT LADDER ──────────────────────────────────────────────────────── #
    print(f"\n  EXIT LADDER  (starting {trigger_et} ET)")
    print("    Logic: bid at mark+0.15, mark+0.10, mark+0.05, mark+0")
    print("           fill when limit ≤ bid; ratchets mark ceiling down if spread moves")
    exit_fill, exit_steps = replay_exit_ladder(replay, decision.candidate, entry_fill["fill_price"])

    for s in exit_steps:
        _print_step(s)

    if exit_fill is None:
        sims = len(exit_steps) * RETRY_INTERVAL_SECONDS
        print(f"\n  TIMEOUT — no exit fill after {len(exit_steps)} steps (~{sims}s)")
        return

    elapsed_exit = _elapsed(exit_steps, exit_fill["step"])
    exit_et = f"  [{_et(exit_steps[-1].snap_time)} ET]" if exit_steps and exit_steps[-1].snap_time else ""
    pnl = exit_fill["fill_price"] - entry_fill["fill_price"]
    pnl_contract = pnl * 100

    print(f"\n  EXIT FILLED:  ${exit_fill['fill_price']:.2f}  (step {exit_fill['step']}, {elapsed_exit}){exit_et}")
    print("\n  ─── RESULT ─────────────────────────────────────────────────────────────")
    print(f"  Entry  : ${entry_fill['fill_price']:.2f}   Exit: ${exit_fill['fill_price']:.2f}")
    print(f"  PnL    : ${pnl:+.2f} / spread   ${pnl_contract:+.2f} / contract")
    print(f"  Reason : {monitor.exit_reason}")
    print("  ────────────────────────────────────────────────────────────────────────")


# ─── Main ────────────────────────────────────────────────────────────────── #

async def main() -> None:
    conn = await asyncpg.connect(resolve_db_dsn())
    try:
        dates = DATES if DATES else await detect_complete_days(conn)
        if not dates:
            print("No complete days found in DB.")
            return
        print(f"Running replay on {len(dates)} complete day(s): {[str(d) for d in dates]}")
        for date in dates:
            await replay_day(conn, date)
    finally:
        await conn.close()
    print()


if __name__ == "__main__":
    asyncio.run(main())
