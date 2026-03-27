"""Multi-day DB backtest across all dates with full chain data.

Runs multiple wing widths + direction modes across every day that has
complete chain data in the DB (entry window 10:00–10:30 ET covered).

Focus: ENTRY ANALYSIS — why, when, and at what price entries happen.

Usage:
    uv run python -m butterfly_guy.scripts.run_all_db_days
"""

from __future__ import annotations

import asyncio
import datetime as dt
import math
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg
import yfinance as yf

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.data.schemas import OptionQuote
from butterfly_guy.strategy.butterfly_builder import (
    VIX_SIGMA_BY_WIDTH,
    vix_expected_move,
    vix_target_center,
)

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_all_db_days")

EASTERN = ZoneInfo("America/New_York")
DB_DSN = "postgresql://butterfly:butterfly_dev@localhost:5432/butterfly_guy"

# Days confirmed to have full data covering the 10:00-10:30 ET entry window
FULL_DATA_DATES = [
    dt.date(2026, 3, 16),
    dt.date(2026, 3, 17),
    dt.date(2026, 3, 19),
    dt.date(2026, 3, 20),
    dt.date(2026, 3, 23),
    dt.date(2026, 3, 24),
]

# Wing widths to test
WING_WIDTHS = [10, 20, 30]

# Strategies to run (label, params)
STRATEGIES = [
    ("gap-auto",      dict(direction_override=None, use_bias_filter=False, use_vix_center=False, use_absolute_loss_stop=True)),
    ("gap-auto-nals", dict(direction_override=None, use_bias_filter=False, use_vix_center=False, use_absolute_loss_stop=False)),
    ("bias-filt",     dict(direction_override=None, use_bias_filter=True,  use_vix_center=False, use_absolute_loss_stop=True)),
    ("bias-nals",     dict(direction_override=None, use_bias_filter=True,  use_vix_center=False, use_absolute_loss_stop=False)),
]

BASE_PARAMS = dict(
    rr_min=8.0,
    morning_drawdown=0.50,
    late_morning_drawdown=0.40,
    afternoon_drawdown=0.30,
    slippage=0.05,
)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

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
            snapshot_time, spot_price
        FROM option_chain_snapshots
        WHERE underlying = 'SPX'
          AND snapshot_time::date = $1
          AND spot_price IS NOT NULL AND spot_price > 0
        ORDER BY snapshot_time
        """,
        date,
    )
    bars = []
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
    return float(hist["Close"].iloc[-1]) if not hist.empty else 5500.0


def get_vix(date: dt.date) -> float:
    end = date + dt.timedelta(days=1)
    hist = yf.Ticker("^VIX").history(start=date, end=end, interval="1d")
    return float(hist["Close"].iloc[0]) if not hist.empty else 18.0


def nearest_snapshot(
    chains: dict[dt.datetime, list[OptionQuote]], bar_ts: dt.datetime
) -> list[OptionQuote] | None:
    candidates = [ts for ts in chains if ts <= bar_ts]
    return chains[max(candidates)] if candidates else None


# ---------------------------------------------------------------------------
# Entry scanner — captures all entry signals for a day
# ---------------------------------------------------------------------------

def scan_entry_window(
    bars: list[MinuteBar],
    chains: dict[dt.datetime, list[OptionQuote]],
    day: DayData,
    wing_widths: list[int],
) -> list[dict]:
    """Walk the 10:00-10:30 ET window and record every bar's entry signals."""
    from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder
    from butterfly_guy.strategy.butterfly_selector import ButterflySelector
    from butterfly_guy.strategy.direction_filter import DirectionFilter
    from butterfly_guy.strategy.bias_filter import BiasScoreFilter
    from butterfly_guy.core.config import StrategySettings

    ENTRY_START = dt.time(10, 0)
    ENTRY_END = dt.time(10, 30)

    direction_filter = DirectionFilter()
    bias_filter = BiasScoreFilter()

    records = []

    for bar in bars:
        bar_et = bar.ts.astimezone(EASTERN)
        if not (ENTRY_START <= bar_et.time() <= ENTRY_END):
            continue

        bars_so_far = [b for b in bars if b.ts <= bar.ts]
        quotes = nearest_snapshot(chains, bar.ts)
        if not quotes:
            continue

        gap_dir = direction_filter.get_direction(bar.close, day.prev_close)
        bias_dir = bias_filter.get_direction(
            bars=bars_so_far, prev_close=day.prev_close, entry_close=bar.close
        )
        gap_pct = (bar.close - day.prev_close) / day.prev_close * 100

        # Compute VWAP for context
        if bars_so_far:
            tv = sum(b.close * b.volume for b in bars_so_far if b.volume > 0)
            vol = sum(b.volume for b in bars_so_far if b.volume > 0)
            vwap = tv / vol if vol > 0 else bar.close
        else:
            vwap = bar.close

        em = vix_expected_move(day.vix, bar.close)

        per_bar = {
            "time_et": bar_et.strftime("%H:%M"),
            "spx": bar.close,
            "gap_pct": gap_pct,
            "gap_dir": gap_dir,
            "bias_dir": bias_dir,
            "vwap": vwap,
            "above_vwap": bar.close > vwap,
            "expected_move_1sd": em,
            "candidates_by_width": {},
        }

        for w in wing_widths:
            settings = StrategySettings(wing_widths=[w], rr_min=8.0, spot_range=100)
            builder = ButterflyBuilder(settings)
            selector = ButterflySelector(settings)

            # --- gap direction ---
            cands = builder.build_candidates(quotes, bar.close, gap_dir)
            best_gap = selector.select_best(cands)

            # --- VIX-centered gap direction ---
            vix_center = vix_target_center(day.vix, bar.close, gap_dir, wing_width=w)
            best_vix = selector.select_best(cands, target_center=vix_center)

            # --- bias direction (if signal) ---
            best_bias = None
            if bias_dir:
                bias_cands = builder.build_candidates(quotes, bar.close, bias_dir)
                best_bias = selector.select_best(bias_cands)

            per_bar["candidates_by_width"][w] = {
                "gap": best_gap,
                "vix": best_vix,
                "bias": best_bias,
                "vix_center_target": vix_center,
                "n_candidates_gap": len(cands),
            }

        records.append(per_bar)

    return records


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def fmt_candidate(c, direction: str = "") -> str:
    if c is None:
        return "  NO TRADE (no candidate)"
    rr = (c.wing_width - c.cost) / c.cost if c.cost > 0 else 0
    lo_delta = c.lower_quote.delta if c.lower_quote else float("nan")
    ctr_delta = c.center_quote.delta if c.center_quote else float("nan")
    return (
        f"  {direction or c.direction:>4}  {c.lower_strike:.0f}/{c.center_strike:.0f}/{c.upper_strike:.0f}"
        f"  cost=${c.cost:.2f}  R/R={rr:.1f}x  BE=[{c.lower_be:.1f},{c.upper_be:.1f}]"
        f"  δlo={lo_delta:.3f} δctr={ctr_delta:.3f}"
    )


def print_day_header(date: dt.date, vix: float, prev_close: float, bars: list[MinuteBar]) -> None:
    open_bar = next((b for b in bars if b.ts.astimezone(EASTERN).time() >= dt.time(9, 30)), None)
    first_entry_bar = next((b for b in bars if b.ts.astimezone(EASTERN).time() >= dt.time(10, 0)), None)

    open_spx = open_bar.close if open_bar else 0
    entry_spx = first_entry_bar.close if first_entry_bar else 0
    gap = entry_spx - prev_close
    gap_pct = gap / prev_close * 100 if prev_close else 0
    day_range = f"{min(b.close for b in bars):.2f} – {max(b.close for b in bars):.2f}"
    em = vix_expected_move(vix, entry_spx)

    print(f"\n{'='*72}")
    print(f"  {date}  ({date.strftime('%A')})")
    print(f"{'='*72}")
    print(f"  VIX          : {vix:.2f}")
    print(f"  Prev close   : {prev_close:.2f}")
    print(f"  Open (9:30)  : {open_spx:.2f}  gap {gap:+.2f} ({gap_pct:+.2f}%)")
    print(f"  Day range    : {day_range}")
    print(f"  1σ daily mv  : ±{em:.0f} pts  (VIX/100/√252 × spot)")
    print()


def print_entry_scan(records: list[dict], wing_widths: list[int]) -> None:
    if not records:
        print("  No bars in entry window (10:00–10:30 ET).")
        return

    print(f"  Entry window scan (10:00–10:30 ET)  —  {len(records)} bars")
    print()

    for rec in records:
        gap_arrow = "▲" if rec["gap_dir"] == "CALL" else "▼"
        bias_str = rec["bias_dir"] if rec["bias_dir"] else "NONE"
        bias_arrow = "▲" if bias_str == "CALL" else ("▼" if bias_str == "PUT" else " ")
        vwap_str = f"VWAP={rec['vwap']:.2f}  {'ABOVE' if rec['above_vwap'] else 'BELOW'}"

        print(f"  ── {rec['time_et']} ET  SPX={rec['spx']:.2f}  gap={rec['gap_pct']:+.3f}% {gap_arrow}  "
              f"bias={bias_str} {bias_arrow}  {vwap_str}")

        for w in wing_widths:
            cw = rec["candidates_by_width"].get(w, {})
            n = cw.get("n_candidates_gap", 0)
            g = cw.get("gap")
            v = cw.get("vix")
            b = cw.get("bias")
            vix_t = cw.get("vix_center_target", 0)

            print(f"     {w:>2}w  [{n} candidates]  vix_target={vix_t:.0f}")
            print(f"          gap-dir  :{fmt_candidate(g)}")
            if v and g and v.center_strike != g.center_strike:
                print(f"          vix-ctr  :{fmt_candidate(v, rec['gap_dir'])}")
            elif v:
                print(f"          vix-ctr  : (same as gap-dir)")
            if b:
                print(f"          bias-dir :{fmt_candidate(b)}")
            elif rec["bias_dir"] is None:
                print(f"          bias-dir : NO SIGNAL (score between -1 and +1)")
        print()


def print_results_table(results_by_strat: dict, wing_widths: list[int]) -> None:
    print(f"\n{'─'*80}")
    print(f"  SIMULATION RESULTS")
    print(f"{'─'*80}")
    hdr = f"  {'Strategy':<12}  {'W':>3}  {'Direction':>9}  {'Entry':>6}  {'Exit':>6}  {'Peak':>6}  {'PnL':>8}  {'Reason'}"
    print(hdr)
    print(f"  {'─'*12}  {'─'*3}  {'─'*9}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*8}  {'─'*22}")

    for strat_label, by_width in results_by_strat.items():
        for w in wing_widths:
            r = by_width.get(w)
            if r is None:
                print(f"  {strat_label:<12}  {w:>3}  {'N/A':>9}  {'--':>6}  {'--':>6}  {'--':>6}  {'--':>8}  --")
            elif not r.traded:
                print(f"  {strat_label:<12}  {w:>3}  {'NO TRADE':>9}")
            else:
                entry_et = r.entry_time.astimezone(EASTERN) if r.entry_time else None
                exit_et = r.exit_time.astimezone(EASTERN) if r.exit_time else None
                t_entry = entry_et.strftime("%H:%M") if entry_et else "--"
                t_exit = exit_et.strftime("%H:%M") if exit_et else "--"
                struct = f"{r.center_strike-w:.0f}/{r.center_strike:.0f}/{r.center_strike+w:.0f}"
                print(
                    f"  {strat_label:<12}  {w:>3}  {r.direction:>9}  "
                    f"{t_entry:>6}@{r.entry_price:>.2f}  "
                    f"{t_exit:>6}@{r.exit_price:>.2f}  "
                    f"${r.peak_value:>5.2f}  "
                    f"{r.pnl*100:>+7.2f}$  "
                    f"{r.exit_reason}"
                )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print(f"\n{'#'*72}")
    print(f"  SPX DB BACKTEST — ALL FULL-DATA DAYS")
    print(f"  Dates: {FULL_DATA_DATES[0]} to {FULL_DATA_DATES[-1]}  ({len(FULL_DATA_DATES)} days)")
    print(f"  Wings: {WING_WIDTHS}    Strategies: {[s[0] for s in STRATEGIES]}")
    print(f"{'#'*72}")

    conn = await asyncpg.connect(DB_DSN)

    # Aggregate tracking
    all_trade_results = []  # (date, strat_label, width, DayResult)

    for date in FULL_DATA_DATES:
        # Load DB data
        chains = await load_chains_from_db(conn, date)
        bars = await load_bars_from_db(conn, date)

        if not chains or not bars:
            print(f"\n  {date}: No data, skipping.")
            continue

        # Fetch VIX + prev_close
        prev_close = await asyncio.to_thread(get_prev_close, date)
        vix = await asyncio.to_thread(get_vix, date)

        day = DayData(date=date, bars=bars, vix=vix, prev_close=prev_close)

        print_day_header(date, vix, prev_close, bars)

        # Detailed entry window scan
        entry_records = scan_entry_window(bars, chains, day, WING_WIDTHS)
        print_entry_scan(entry_records, WING_WIDTHS)

        # Patch chain cache for simulation
        import butterfly_guy.backtest.chain_cache as _cc
        _cc._DB_CHAINS = chains  # type: ignore[attr-defined]
        _original_load = _cc.load_chain_day

        def _patched(d, cache_dir=None, _date=date, _chains=chains):
            if d == _date:
                return _chains
            return _original_load(d, cache_dir) if cache_dir else _original_load(d)

        _cc.load_chain_day = _patched  # type: ignore[assignment]

        engine = SimulationEngine()
        results_by_strat: dict[str, dict] = {}

        for strat_label, strat_kw in STRATEGIES:
            results_by_strat[strat_label] = {}
            for w in WING_WIDTHS:
                params = SimulationParams(wing_width=w, **BASE_PARAMS, **strat_kw)
                result = engine.simulate_day(day, params)
                results_by_strat[strat_label][w] = result
                if result.traded:
                    all_trade_results.append((date, strat_label, w, result))

        _cc.load_chain_day = _original_load  # type: ignore[assignment]

        print_results_table(results_by_strat, WING_WIDTHS)

    await conn.close()

    # ---------------------------------------------------------------------------
    # Grand summary across all days
    # ---------------------------------------------------------------------------
    print(f"\n\n{'#'*72}")
    print(f"  AGGREGATE SUMMARY — ALL DAYS × ALL STRATEGIES × ALL WIDTHS")
    print(f"{'#'*72}")

    # Group by (strat, width)
    from collections import defaultdict as ddict
    grouped: dict[tuple, list] = ddict(list)
    for date, strat, w, r in all_trade_results:
        grouped[(strat, w)].append((date, r))

    print(f"\n  {'Strategy':<12}  {'W':>3}  {'Trades':>6}  {'WinRate':>8}  "
          f"{'TotalPnL':>10}  {'AvgPnL':>8}  {'PF':>6}  {'MaxDD':>8}")
    print(f"  {'─'*12}  {'─'*3}  {'─'*6}  {'─'*8}  {'─'*10}  {'─'*8}  {'─'*6}  {'─'*8}")

    for strat_label, _ in STRATEGIES:
        for w in WING_WIDTHS:
            trades = grouped.get((strat_label, w), [])
            if not trades:
                print(f"  {strat_label:<12}  {w:>3}  {'0':>6}")
                continue
            pnls = [r.pnl for _, r in trades]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p <= 0]
            total = sum(pnls)
            wr = len(wins) / len(pnls) * 100
            avg = total / len(pnls)
            pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else float("inf")

            # max drawdown
            eq = peak = dd = 0.0
            for p in pnls:
                eq += p
                peak = max(peak, eq)
                dd = max(dd, peak - eq)

            print(
                f"  {strat_label:<12}  {w:>3}  {len(pnls):>6}  {wr:>7.0f}%  "
                f"{total*100:>+9.2f}$  {avg*100:>+7.2f}$  {pf:>6.2f}  {dd*100:>7.2f}$"
            )

    # Exit reason breakdown
    print(f"\n  Exit reasons across all trades:")
    from collections import Counter
    reason_counts: Counter = Counter()
    for _, _, _, r in all_trade_results:
        reason_counts[r.exit_reason] += 1
    for reason, cnt in reason_counts.most_common():
        print(f"    {reason:<28} {cnt:>3}  ({cnt/len(all_trade_results)*100:.0f}%)")

    # Per-day direction summary
    print(f"\n  Per-day direction and entry time (gap-auto, 10w):")
    print(f"  {'Date':>12}  {'VIX':>5}  {'Gap%':>7}  {'Dir':>4}  {'Entry':>5}  {'Struct':>18}  {'PnL':>8}")
    print(f"  {'─'*12}  {'─'*5}  {'─'*7}  {'─'*4}  {'─'*5}  {'─'*18}  {'─'*8}")
    for date, strat, w, r in all_trade_results:
        if strat != "gap-auto" or w != 10:
            continue
        et = r.entry_time.astimezone(EASTERN).strftime("%H:%M") if r.entry_time else "--"
        struct = f"{r.center_strike-w:.0f}/{r.center_strike:.0f}/{r.center_strike+w:.0f}"
        # find vix for this date
        print(f"  {str(date):>12}  {'?':>5}  {'?':>7}  {r.direction:>4}  {et:>5}  {struct:>18}  {r.pnl*100:>+7.2f}$")

    print()


if __name__ == "__main__":
    asyncio.run(main())
