"""Record raw Schwab equity chart, Level I, and Level II stream messages."""

from __future__ import annotations

import argparse
import asyncio
import signal
from pathlib import Path
from typing import Any

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.core.time_utils import now_eastern
from butterfly_guy.data.equity_market_data import (
    JsonlStreamRecorder,
    symbol_directory,
    utc_now,
)
from butterfly_guy.data.schwab_client import SchwabClientWrapper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record raw Schwab equity streams. This is read-only market data and "
            "does not place, modify, or cancel orders."
        )
    )
    parser.add_argument("symbol", help="Equity symbol, for example BMNR")
    parser.add_argument(
        "--venue",
        choices=("nyse", "nasdaq", "both"),
        default="nyse",
        help="Level II book service. BMNR is NYSE-listed.",
    )
    parser.add_argument(
        "--duration-seconds",
        type=int,
        default=0,
        help="Stop automatically after N seconds; 0 records until Ctrl-C/SIGTERM.",
    )
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/equity_market_data"),
    )
    parser.add_argument(
        "--book",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable Level II book subscriptions.",
    )
    return parser.parse_args()


def _install_signal_handlers(stop: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, name)
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass


async def _subscribe(
    stream: Any,
    recorder: JsonlStreamRecorder,
    *,
    symbol: str,
    venue: str,
    include_book: bool,
) -> None:
    stream.add_chart_equity_handler(recorder.handler("chart_equity"))
    stream.add_level_one_equity_handler(recorder.handler("level_one_equity"))
    if include_book and venue in {"nyse", "both"}:
        stream.add_nyse_book_handler(recorder.handler("nyse_book"))
    if include_book and venue in {"nasdaq", "both"}:
        stream.add_nasdaq_book_handler(recorder.handler("nasdaq_book"))

    await stream.chart_equity_subs([symbol])
    await stream.level_one_equity_subs([symbol])
    if include_book and venue in {"nyse", "both"}:
        await stream.nyse_book_subs([symbol])
    if include_book and venue in {"nasdaq", "both"}:
        await stream.nasdaq_book_subs([symbol])


async def run(args: argparse.Namespace) -> Path:
    from schwab.streaming import StreamClient

    symbol = args.symbol.upper()
    config = load_config(args.config)
    schwab = SchwabClientWrapper(config.schwab)
    await schwab.initialize()

    session_date = now_eastern().date()
    output_dir = symbol_directory(args.output_dir, symbol, session_date)
    recorder = JsonlStreamRecorder(output_dir, symbol=symbol)
    stop = asyncio.Event()
    _install_signal_handlers(stop)

    stream = StreamClient(
        schwab.client,
        account_id=config.schwab.account_id,
        enforce_enums=False,
    )
    started_at = utc_now()
    writer: asyncio.Task[None] | None = None
    timer: asyncio.Task[None] | None = None
    logged_in = False
    try:
        await stream.login()
        logged_in = True
        writer = asyncio.create_task(recorder.write_until_stopped(stop))
        await _subscribe(
            stream,
            recorder,
            symbol=symbol,
            venue=args.venue,
            include_book=args.book,
        )
        if args.duration_seconds > 0:

            async def stop_after_duration() -> None:
                await asyncio.sleep(args.duration_seconds)
                stop.set()

            timer = asyncio.create_task(stop_after_duration())

        while not stop.is_set():
            try:
                await asyncio.wait_for(stream.handle_message(), timeout=1.0)
            except TimeoutError:
                continue
    finally:
        stop.set()
        if timer:
            timer.cancel()
        if writer:
            await writer
        if logged_in:
            await stream.logout()

    return recorder.write_manifest(
        started_at=started_at,
        ended_at=utc_now(),
        venue=args.venue if args.book else "disabled",
    )


async def async_main() -> None:
    args = parse_args()
    setup_logging(log_level="INFO", json_output=False)
    path = await run(args)
    print(path)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
