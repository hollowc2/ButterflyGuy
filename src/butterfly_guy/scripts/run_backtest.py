"""Entry point: run parameter sweep backtest."""

from __future__ import annotations

import asyncio
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Set USE_YFINANCE=True for free data (hourly SPX bars, no API key needed).
# Set USE_YFINANCE=False to use Polygon (requires POLYGON_ACCESS_KEY_ID in .env,
# paid plan needed for I:SPX index data).
USE_YFINANCE = True

from butterfly_guy.backtest.data_loader import BacktestDataLoader
from butterfly_guy.backtest.parameter_sweeper import ParameterSweeper, SweepConfig
from butterfly_guy.backtest.yfinance_loader import YFinanceDataLoader
from butterfly_guy.core.logging import get_logger, setup_logging

setup_logging(log_level="INFO", json_output=False)
log = get_logger("run_backtest")


async def main() -> None:
    if USE_YFINANCE:
        loader = YFinanceDataLoader()
        log.info("data_source", source="yfinance", note="hourly SPX bars, free")
    else:
        from dotenv import dotenv_values
        env = dotenv_values(".env")
        polygon_key = env.get("POLYGON_ACCESS_KEY_ID", "")
        if not polygon_key:
            print("POLYGON_ACCESS_KEY_ID not set in .env")
            sys.exit(1)
        loader = BacktestDataLoader(polygon_key)
        log.info("data_source", source="polygon")

    config = SweepConfig(
        start_date=dt.date(2025, 1, 6),
        end_date=dt.date(2025, 1, 17),  # 2-week smoke test
        wing_widths=[10, 20],
        rr_mins=[6.0, 8.0],
        morning_drawdowns=[0.50],
        late_morning_drawdowns=[0.40],
        afternoon_drawdowns=[0.30],
    )

    sweeper = ParameterSweeper(loader)

    log.info("sweep_starting", start=str(config.start_date), end=str(config.end_date))
    results = await sweeper.sweep(config)

    await loader.close()

    if results.is_empty():
        log.warning("no_results")
        return

    print("\n=== TOP 20 PARAMETER COMBINATIONS ===")
    print(results.head(20))

    out_path = Path("backtest_results.csv")
    results.write_csv(out_path)
    log.info("results_saved", path=str(out_path))


if __name__ == "__main__":
    asyncio.run(main())
