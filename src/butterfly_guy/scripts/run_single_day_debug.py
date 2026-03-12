"""Single-day backtest debug script.

Runs a full simulation on one date and prints detailed bar-by-bar output
so you can see exactly what the strategy is doing and why.

Usage:
    # Schwab (real 1-min data, last ~48 days) — default
    uv run python src/butterfly_guy/scripts/run_single_day_debug.py 2026-03-05
    uv run python src/butterfly_guy/scripts/run_single_day_debug.py 2026-03-05 --source schwab

    # CSV (local 1-min data (data/spx_1min.csv), exhaustive)
    uv run python src/butterfly_guy/scripts/run_single_day_debug.py 2025-06-03 --source csv
"""

from __future__ import annotations

import asyncio
import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.backtest.simulation_engine import (
    EASTERN,
    ENTRY_END,
    ENTRY_START,
    SimulationParams,
)
from butterfly_guy.core.config import StrategySettings
from butterfly_guy.quant_engine.synthetic_chain import SyntheticChainGenerator
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter


def fmt(ts: dt.datetime) -> str:
    return ts.astimezone(EASTERN).strftime("%H:%M ET")


async def debug_day(date: dt.date, params: SimulationParams, loader) -> None:
    if hasattr(loader, "load_day_async"):
        day = await loader.load_day_async(date)
    else:
        # CsvDataLoader and others might be synchronous
        day = loader.load_day(date)

    if not day:
        print(f"No data for {date}")
        return

    print("=" * 60)
    print(f"  DATE:       {day.date}")
    print(f"  VIX:        {day.vix:.2f}")
    print(f"  PREV CLOSE: {day.prev_close:.2f}")
    print(f"  BARS:       {len(day.bars)}")
    print(f"  PARAMS:     wing={params.wing_width}  rr_min={params.rr_min}")
    print(f"              morning_dd={params.morning_drawdown}  "
          f"late_morning_dd={params.late_morning_drawdown}  "
          f"afternoon_dd={params.afternoon_drawdown}")
    print("=" * 60)

    print("\n--- ALL BARS ---")
    for bar in day.bars:
        bar_et = bar.ts.astimezone(EASTERN)
        in_window = ENTRY_START <= bar_et.time() <= ENTRY_END
        marker = " <-- ENTRY WINDOW" if in_window else ""
        print(f"  {fmt(bar.ts)}  O={bar.open:.2f}  H={bar.high:.2f}  "
              f"L={bar.low:.2f}  C={bar.close:.2f}{marker}")

    # --- Entry phase ---
    synth = SyntheticChainGenerator()
    direction_filter = DirectionFilter()
    entry_candidate = None
    entry_bar = None
    entry_price = 0.0

    print("\n--- ENTRY SCAN (10:00–10:30 ET) ---")
    for bar in day.bars:
        bar_et = bar.ts.astimezone(EASTERN)
        if not (ENTRY_START <= bar_et.time() <= ENTRY_END):
            continue

        direction = direction_filter.get_direction(bar.close, day.prev_close)
        print(f"\n  Bar {fmt(bar.ts)}  spot={bar.close:.2f}  "
              f"direction={direction}  gap={((bar.close - day.prev_close) / day.prev_close * 100):.3f}%")

        quotes = synth.generate_chain(
            spot=bar.close,
            vix=day.vix,
            expiration=day.date,
            snapshot_time=bar.ts,
            strike_min=bar.close - 110,
            strike_max=bar.close + 110,
        )

        settings = StrategySettings(
            wing_widths=[params.wing_width],
            rr_min=params.rr_min,
            spot_range=100,
        )
        builder = ButterflyBuilder(settings)
        candidates = builder.build_candidates(quotes, bar.close, direction)
        selector = ButterflySelector()
        best = selector.select_best(candidates)

        print(f"  Candidates found: {len(candidates)}")
        for c in candidates[:5]:
            print(f"    [{c.lower_strike:.0f}/{c.center_strike:.0f}/{c.upper_strike:.0f}]  "
                  f"cost={c.cost:.4f}  rr={c.reward_risk:.2f}  dist={c.distance_from_spot:.1f}")
        if len(candidates) > 5:
            print(f"    ... and {len(candidates) - 5} more")

        if best:
            entry_price = best.cost + params.slippage
            entry_candidate = best
            entry_bar = bar
            print(f"\n  ENTRY: [{best.lower_strike:.0f}/{best.center_strike:.0f}/{best.upper_strike:.0f}]  "
                  f"cost={best.cost:.4f}  slippage={params.slippage}  "
                  f"entry_price={entry_price:.4f}  rr={best.reward_risk:.2f}")
            break
        else:
            print("  No valid candidates.")

    if not entry_candidate or not entry_bar:
        print("\n  NO ENTRY — no valid butterfly found in window.")
        return

    # --- Monitor phase ---
    print("\n--- MONITORING ---")
    print(f"  Entry price: {entry_price:.4f}  Max profit at: "
          f"{entry_candidate.center_strike:.0f}")
    print(f"  Breakevens: {entry_candidate.lower_be:.2f} / {entry_candidate.upper_be:.2f}")
    print()
    print(f"  {'Time':>8}  {'Spot':>8}  {'Curr Val':>9}  {'Peak':>8}  "
          f"{'PnL':>7}  {'DD%':>6}  {'Regime':>12}  {'Thresh':>6}  Exit?")
    print("  " + "-" * 80)

    open_dt = dt.datetime(
        day.date.year, day.date.month, day.date.day, 9, 30, tzinfo=EASTERN
    )
    peak_value = entry_price

    for bar in day.bars:
        if bar.ts <= entry_bar.ts:
            continue

        bar_et = bar.ts.astimezone(EASTERN)
        mins_since_open = (bar_et - open_dt).total_seconds() / 60.0
        minutes_to_close = (
            dt.datetime(day.date.year, day.date.month, day.date.day, 16, 0, tzinfo=EASTERN)
            - bar_et
        ).total_seconds() / 60.0

        if mins_since_open < 120:
            regime = "morning"
            threshold = params.morning_drawdown
        elif mins_since_open < 240:
            regime = "late_morning"
            threshold = params.late_morning_drawdown
        else:
            regime = "afternoon"
            threshold = params.afternoon_drawdown

        # Compute current butterfly value
        quotes = synth.generate_chain(
            spot=bar.close,
            vix=day.vix,
            expiration=day.date,
            snapshot_time=bar.ts,
            strike_min=entry_candidate.lower_strike - 5,
            strike_max=entry_candidate.upper_strike + 5,
        )
        quote_map = {
            q.strike: q for q in quotes
            if q.option_type == entry_candidate.direction
        }
        lower_q = quote_map.get(entry_candidate.lower_strike)
        center_q = quote_map.get(entry_candidate.center_strike)
        upper_q = quote_map.get(entry_candidate.upper_strike)

        if lower_q and center_q and upper_q:
            current_value = max(0.0, lower_q.mark - 2 * center_q.mark + upper_q.mark)
        else:
            current_value = peak_value

        peak_value = max(peak_value, current_value)
        pnl = current_value - entry_price
        dd = (peak_value - current_value) / peak_value if peak_value > 0 else 0.0

        # Check exits
        exit_flag = ""
        if minutes_to_close <= 5:
            exit_flag = "EOD EXIT"
        elif peak_value > entry_price and dd >= threshold:
            exit_flag = f"DD EXIT ({dd:.1%} >= {threshold:.0%})"

        print(f"  {fmt(bar.ts):>8}  {bar.close:>8.2f}  {current_value:>9.4f}  "
              f"{peak_value:>8.4f}  {pnl:>+7.4f}  {dd:>5.1%}  "
              f"{regime:>12}  {threshold:>5.0%}  {exit_flag}")

        if exit_flag:
            exit_price = max(0.05, current_value - params.slippage)
            final_pnl = exit_price - entry_price
            print(f"\n  EXIT TRIGGERED: {exit_flag}")
            print(f"  Exit price (after slippage): {exit_price:.4f}")
            print(f"  Final PnL: {final_pnl:+.4f}")
            return

    # Expired
    final_pnl = 0.05 - entry_price
    print(f"\n  EXPIRED WORTHLESS")
    print(f"  Final PnL: {final_pnl:+.4f}")


async def main() -> None:
    args = sys.argv[1:]
    source = "schwab"
    date_str = None

    for arg in args:
        if arg == "--source" or arg.startswith("--source="):
            pass  # handled below
        elif arg in ("schwab", "yfinance", "polygon", "csv"):
            source = arg
        elif arg.startswith("20"):
            date_str = arg

    # Also handle --source schwab / --source yfinance
    for i, arg in enumerate(args):
        if arg == "--source" and i + 1 < len(args):
            source = args[i + 1]
        elif arg.startswith("--source="):
            source = arg.split("=", 1)[1]

    # Default date: use a recent trading day for Schwab, older date for others
    if date_str is None:
        if source == "schwab":
            # Default to last Friday (likely a trading day within 48-day window)
            today = dt.date.today()
            days_back = (today.weekday() + 3) % 7 + 1  # last weekday
            date_str = str(today - dt.timedelta(days=days_back))
        else:
            date_str = "2025-01-06"

    date = dt.date.fromisoformat(date_str)

    # Build loader
    if source == "schwab":
        from dotenv import dotenv_values
        from butterfly_guy.backtest.schwab_loader import SchwabDataLoader
        env = dotenv_values(".env")
        loader = SchwabDataLoader(
            token_path=env.get("SCHWAB_TOKEN_PATH", "tokens.json"),
            api_key=env.get("SCHWAB_API_KEY", ""),
            secret_key=env.get("SCHWAB_SECRET_KEY", ""),
        )
    elif source == "yfinance":
        from butterfly_guy.backtest.yfinance_loader import YFinanceDataLoader
        loader = YFinanceDataLoader()
    elif source == "csv":
        from butterfly_guy.backtest.csv_loader import CsvDataLoader
        loader = CsvDataLoader(Path("data/spx_1min.csv"), Path("data/vix_1min.csv"))
    else:
        from dotenv import dotenv_values
        from butterfly_guy.backtest.data_loader import BacktestDataLoader
        env = dotenv_values(".env")
        loader = BacktestDataLoader(env.get("POLYGON_ACCESS_KEY_ID", ""))

    print(f"Source: {source}  |  Date: {date}")

    params = SimulationParams(
        wing_width=30,
        rr_min=8.0,
        morning_drawdown=0.50,
        late_morning_drawdown=0.40,
        afternoon_drawdown=0.30,
        slippage=0.05,
    )

    await debug_day(date, params, loader)
    if hasattr(loader, "close"):
        if asyncio.iscoroutinefunction(loader.close):
            await loader.close()
        else:
            loader.close()


if __name__ == "__main__":
    asyncio.run(main())
