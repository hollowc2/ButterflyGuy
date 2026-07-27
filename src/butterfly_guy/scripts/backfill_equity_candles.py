"""Backfill one session of one-minute equity candles from Schwab."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
from pathlib import Path

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.data.equity_market_data import symbol_directory, write_candle_snapshot
from butterfly_guy.data.schwab_client import SchwabClientWrapper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill one-minute Schwab candles for an equity session."
    )
    parser.add_argument("symbol", help="Equity symbol, for example BMNR")
    parser.add_argument("date", type=dt.date.fromisoformat, help="Session date, YYYY-MM-DD")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/equity_market_data"),
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> Path:
    symbol = args.symbol.upper()
    config = load_config(args.config)
    schwab = SchwabClientWrapper(config.schwab)
    await schwab.initialize()
    candles = await schwab.get_intraday_bars_for_day(
        symbol,
        args.date,
        include_extended_hours=True,
    )
    if not candles:
        raise RuntimeError(f"Schwab returned no candles for {symbol} on {args.date}")

    output_dir = symbol_directory(args.output_dir, symbol, args.date)
    path = output_dir / "candles_1m.json"
    write_candle_snapshot(
        path,
        symbol=symbol,
        session_date=args.date,
        candles=candles,
    )
    return path


async def async_main() -> None:
    args = parse_args()
    setup_logging(log_level="INFO", json_output=False)
    path = await run(args)
    print(path)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
