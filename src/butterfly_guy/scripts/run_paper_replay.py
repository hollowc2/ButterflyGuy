"""Historical paper trading replay.

Replays real DB chain snapshots through the exact OrderManager paper-path
logic to validate entry/exit ladder mechanics on historical data.

Each ladder step consumes the next DB snapshot, and asyncio.sleep is simulated
by advancing the snapshot index — no real sleeping, no real network calls.

Usage:
    uv run python -m butterfly_guy.scripts.run_paper_replay
"""

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
from butterfly_guy.core.config import StrategySettings
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder, vix_target_center
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_paper_replay")

EASTERN = ZoneInfo("America/New_York")
DB_DSN = "postgresql://butterfly:butterfly_dev@localhost:5432/butterfly_guy"

# ─────────────────────────────────────────────────────────────────────────── #
#  Config — edit these to change the replay                                   #
# ─────────────────────────────────────────────────────────────────────────── #
DATES = [
    dt.date(2026, 3, 16),
    dt.date(2026, 3, 17),
    dt.date(2026, 3, 19),
    dt.date(2026, 3, 20),
]
WING_WIDTH = 20
DIRECTION: str | None = None   # None = gap-based bias filter; "CALL"/"PUT" to force
RR_MIN = 8.0
PRICE_LADDER_STEP = 0.05
PRICE_LADDER_STEPS = 4
ORDER_TIMEOUT_SECONDS = 300
SNAPSHOT_INTERVAL_SECONDS = 30   # approximate gap between DB snapshots (~31s measured)
RETRY_INTERVAL_SECONDS = 20      # mirrors ExecutionSettings.retry_interval_seconds
# ─────────────────────────────────────────────────────────────────────────── #

# Snapshots advanced per sleep(RETRY_INTERVAL_SECONDS) call.
# round(20/30) = 1 — each ladder step consumes one new snapshot.
_SNAPS_PER_STEP = max(1, round(RETRY_INTERVAL_SECONDS / SNAPSHOT_INTERVAL_SECONDS))

# Max outer-loop repetitions before giving up (mirrors OrderManager deadline).
# Each outer iteration = PRICE_LADDER_STEPS steps × RETRY_INTERVAL_SECONDS.
_MAX_OUTER = (ORDER_TIMEOUT_SECONDS // (PRICE_LADDER_STEPS * RETRY_INTERVAL_SECONDS)) + 2


# ─── Data types ─────────────────────────────────────────────────────────── #

class LiveSpread(NamedTuple):
    bid: float
    mark: float
    ask: float


@dataclass
class StepLog:
    step: int        # total step counter across outer loops
    ladder_i: int    # position within current inner ladder (0..PRICE_LADDER_STEPS-1)
    limit: float
    bid: float | None
    mark: float | None
    ask: float | None
    filled: bool
    snap_time: dt.datetime | None = None


# ─── ReplaySchwab ────────────────────────────────────────────────────────── #

class ReplaySchwab:
    """Serves chain snapshots sequentially, advancing with each ladder step."""

    def __init__(self, snapshots: list[tuple[dt.datetime, list[OptionQuote]]]) -> None:
        self._snaps = snapshots  # sorted by ts
        self._idx = 0

    def get_spread(self, candidate: ButterflyCandidate) -> LiveSpread | None:
        """Return butterfly spread from the current snapshot."""
        if not self._snaps:
            return None
        _, quotes = self._snaps[min(self._idx, len(self._snaps) - 1)]
        return _compute_spread(quotes, candidate)

    def advance(self, n: int = 1) -> None:
        self._idx = min(self._idx + n, len(self._snaps) - 1)

    def seek_to_time(self, ts: dt.datetime) -> None:
        """Move index to the first snapshot at or after ts."""
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


# ─── Spread helper ───────────────────────────────────────────────────────── #

def _compute_spread(
    quotes: list[OptionQuote], candidate: ButterflyCandidate
) -> LiveSpread | None:
    """Compute butterfly spread bid/mark/ask from a raw quote list."""
    by_strike = {q.strike: q for q in quotes if q.option_type == candidate.direction}
    lo, ce, up = candidate.lower_strike, candidate.center_strike, candidate.upper_strike
    if lo not in by_strike or ce not in by_strike or up not in by_strike:
        return None
    lo_q, ce_q, up_q = by_strike[lo], by_strike[ce], by_strike[up]
    # Mirror OrderManager._fetch_live_spread arithmetic exactly
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


# ─── DB loaders (copied from run_db_backtest.py) ─────────────────────────── #

async def load_chains_from_db(
    conn: asyncpg.Connection, date: dt.date
) -> dict[dt.datetime, list[OptionQuote]]:
    rows = await conn.fetch(
        """
        SELECT snapshot_time, strike, option_type, bid, ask, mark, last,
               volume, open_interest, iv, delta, gamma, theta, vega, symbol, spot_price
        FROM option_chain_snapshots
        WHERE underlying = 'SPX'
          AND expiration = $1
          AND snapshot_time::date = $1
        ORDER BY snapshot_time, strike, option_type
        """,
        date,
    )
    chains: dict[dt.datetime, list[OptionQuote]] = defaultdict(list)
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        chains[ts].append(
            OptionQuote(
                symbol=r["symbol"] or f"DB_{r['option_type'][0]}{int(r['strike'])}",
                underlying="SPX",
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
    conn: asyncpg.Connection, date: dt.date
) -> list[MinuteBar]:
    rows = await conn.fetch(
        """
        SELECT DISTINCT ON (snapshot_time)
            snapshot_time,
            spot_price
        FROM option_chain_snapshots
        WHERE underlying = 'SPX'
          AND snapshot_time::date = $1
          AND spot_price IS NOT NULL
          AND spot_price > 0
        ORDER BY snapshot_time
        """,
        date,
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

def find_entry_candidate(
    chains: dict[dt.datetime, list[OptionQuote]],
    bars: list[MinuteBar],
    vix: float,
    prev_close: float,
    date: dt.date,
) -> tuple[ButterflyCandidate | None, dt.datetime | None]:
    """Find best candidate using the 10:00–10:30 AM ET entry window."""
    start_utc = dt.datetime(date.year, date.month, date.day, 10, 0, 0,
                            tzinfo=EASTERN).astimezone(dt.timezone.utc)
    end_utc = dt.datetime(date.year, date.month, date.day, 10, 30, 0,
                          tzinfo=EASTERN).astimezone(dt.timezone.utc)

    entry_snaps = [(ts, q) for ts, q in sorted(chains.items())
                   if start_utc <= ts <= end_utc]
    if not entry_snaps:
        # Fall back to nearest snapshot before end of entry window
        before = [(ts, q) for ts, q in sorted(chains.items()) if ts <= end_utc]
        if not before:
            return None, None
        entry_snaps = [before[-1]]

    entry_ts, entry_quotes = entry_snaps[0]

    # Spot price from bars
    bar_before = [b for b in bars if b.ts <= entry_ts]
    if not bar_before:
        bar_before = bars[:1]
    if not bar_before:
        return None, None
    spot = bar_before[-1].close

    # Direction
    if DIRECTION is not None:
        direction = DIRECTION
    else:
        direction = DirectionFilter().get_direction(spot, prev_close)

    settings = StrategySettings(wing_widths=[WING_WIDTH], rr_min=RR_MIN, spot_range=150)
    builder = ButterflyBuilder(settings)
    candidates = builder.build_candidates(entry_quotes, spot, direction)
    if not candidates:
        return None, None

    target_center = vix_target_center(
        vix=vix, spot=spot, direction=direction, wing_width=WING_WIDTH
    )
    best = ButterflySelector(settings).select_best(candidates, target_center=target_center)
    return best, entry_ts


# ─── Ladder replay (mirrors OrderManager paper path exactly) ─────────────── #

def replay_entry_ladder(
    replay: ReplaySchwab,
    candidate: ButterflyCandidate,
) -> tuple[dict | None, list[StepLog]]:
    """
    Mirror OrderManager.execute_entry paper path:
      outer while True → inner for i in range(PRICE_LADDER_STEPS)
        spread = _fetch_live_spread()
        limit  = mark + i * step
        if limit >= ask → FILLED
        sleep(retry_interval)  [here: advance replay index]
    """
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
    """
    Mirror OrderManager.execute_exit paper path:
      outer while True → inner for i in range(PRICE_LADDER_STEPS)
        spread = _fetch_live_spread()
        limit  = mark + (max_steps-1-i) * step   [stepping down]
        if limit <= bid → FILLED
        sleep(retry_interval)  [here: advance replay index]
    """
    steps: list[StepLog] = []
    price_ceiling: float | None = None
    total_step = 0

    for _outer in range(_MAX_OUTER):
        for i in range(PRICE_LADDER_STEPS):
            spread = replay.get_spread(candidate)
            if spread is not None:
                price_ceiling = spread.mark if price_ceiling is None else min(price_ceiling, spread.mark)
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

    return None, steps


# ─── Output helpers ──────────────────────────────────────────────────────── #

def _fmt_spread(spread: tuple[float | None, float | None, float | None]) -> str:
    bid, mark, ask = spread
    b = f"{bid:.2f}" if bid is not None else " N/A"
    m = f"{mark:.2f}" if mark is not None else " N/A"
    a = f"{ask:.2f}" if ask is not None else " N/A"
    return f"bid={b}  mark={m}  ask={a}"


def _print_step(s: StepLog) -> None:
    spread = _fmt_spread((s.bid, s.mark, s.ask))
    snap = ""
    if s.snap_time:
        snap = f"  [{s.snap_time.astimezone(EASTERN).strftime('%H:%M:%S')} ET]"
    result = "→ FILLED" if s.filled else "→ no fill"
    print(f"    Step {s.step:2d} (i={s.ladder_i}): limit={s.limit:.2f}  {spread}  {result}{snap}")


def _elapsed(steps: list[StepLog], fill_step: int) -> str:
    """Compute wall-clock elapsed time from first to fill step using snapshot timestamps."""
    if not steps:
        return "?"
    t0 = steps[0].snap_time
    t1 = steps[fill_step].snap_time if fill_step < len(steps) else steps[-1].snap_time
    if t0 and t1:
        secs = (t1 - t0).total_seconds()
        return f"~{secs:.0f}s (~{secs / 60:.1f}m)"
    # Fall back to estimated
    secs = fill_step * _SNAPS_PER_STEP * SNAPSHOT_INTERVAL_SECONDS
    return f"~{secs}s (~{secs / 60:.1f}m, estimated)"


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

    candidate, entry_ts = find_entry_candidate(chains, bars, vix, prev_close, date)

    snap_count = len(chains)
    bar_range = (
        f"{bars[0].ts.astimezone(EASTERN).strftime('%H:%M')}–"
        f"{bars[-1].ts.astimezone(EASTERN).strftime('%H:%M')} ET"
    )
    dir_str = candidate.direction if candidate else (DIRECTION or "?")

    print(f"\n{'='*72}")
    print(f"  PAPER REPLAY — {date}  "
          f"(VIX={vix:.1f}, {WING_WIDTH}-wide {dir_str}, RR≥{RR_MIN:.0f})")
    print(f"  {snap_count} snapshots  |  {bar_range}  "
          f"|  SPX {min(b.close for b in bars):.0f}–{max(b.close for b in bars):.0f}")
    print(f"{'='*72}")

    if candidate is None:
        print("  NO CANDIDATE — no qualifying butterfly found in entry window.")
        return

    struct = (
        f"{candidate.lower_strike:.0f} / {candidate.center_strike:.0f} "
        f"/ {candidate.upper_strike:.0f}"
    )
    entry_et = entry_ts.astimezone(EASTERN).strftime("%H:%M:%S") if entry_ts else "N/A"
    print(f"\n  Candidate  : {struct}  ({candidate.direction})")
    print(f"  Entry snap : {entry_et} ET")
    print(f"  Mark cost  : ${candidate.cost:.2f}   "
          f"RR={candidate.reward_risk:.1f}x   "
          f"max_profit=${candidate.max_profit:.2f}")

    sorted_snaps = sorted(chains.items())
    replay = ReplaySchwab(sorted_snaps)
    if entry_ts:
        replay.seek_to_time(entry_ts)

    # ── ENTRY ────────────────────────────────────────────────────────────── #
    print(f"\n  ENTRY  (ladder starts at {entry_et} ET):")
    entry_fill, entry_steps = replay_entry_ladder(replay, candidate)

    for s in entry_steps:
        _print_step(s)

    if entry_fill is None:
        sims = len(entry_steps) * RETRY_INTERVAL_SECONDS
        print(f"\n  TIMEOUT — no entry fill ({len(entry_steps)} steps, ~{sims}s simulated)")
        return

    elapsed = _elapsed(entry_steps, entry_fill["step"])
    fill_et = ""
    if entry_steps and entry_steps[-1].snap_time:
        fill_et = f"  [{entry_steps[-1].snap_time.astimezone(EASTERN).strftime('%H:%M:%S')} ET]"
    print(f"\n  ENTRY FILLED: ${entry_fill['fill_price']:.2f}  "
          f"(step {entry_fill['step']},  {elapsed}){fill_et}")

    # ── EXIT ─────────────────────────────────────────────────────────────── #
    print(f"\n  EXIT  (ladder starts immediately after entry fill):")
    print(f"  [In production, exit is triggered by the drawdown monitor]")
    exit_fill, exit_steps = replay_exit_ladder(replay, candidate, entry_fill["fill_price"])

    for s in exit_steps:
        _print_step(s)

    if exit_fill is None:
        sims = len(exit_steps) * RETRY_INTERVAL_SECONDS
        print(f"\n  TIMEOUT — no exit fill ({len(exit_steps)} steps, ~{sims}s simulated)")
        return

    elapsed_exit = _elapsed(exit_steps, exit_fill["step"])
    exit_et = ""
    if exit_steps and exit_steps[-1].snap_time:
        exit_et = f"  [{exit_steps[-1].snap_time.astimezone(EASTERN).strftime('%H:%M:%S')} ET]"
    pnl = exit_fill["fill_price"] - entry_fill["fill_price"]

    print(f"\n  EXIT FILLED:  ${exit_fill['fill_price']:.2f}  "
          f"(step {exit_fill['step']},  {elapsed_exit}){exit_et}")
    print(f"  PnL         : ${pnl:+.2f} / spread   ${pnl * 100:+.2f} / contract")


# ─── Main ────────────────────────────────────────────────────────────────── #

async def main() -> None:
    conn = await asyncpg.connect(DB_DSN)
    try:
        for date in DATES:
            await replay_day(conn, date)
    finally:
        await conn.close()
    print()


if __name__ == "__main__":
    asyncio.run(main())
