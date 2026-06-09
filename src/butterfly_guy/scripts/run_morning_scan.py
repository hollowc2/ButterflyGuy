"""Morning equity scan — premarket movers and prior-day rallies/dumps via Schwab."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import dotenv_values

root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "tools"))

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.core.time_utils import is_premarket_window, now_eastern
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.equity_scan.config import load_equity_scan_config
from butterfly_guy.equity_scan.report import archive_report, build_report
from butterfly_guy.equity_scan.scanner import (
    build_snapshots,
    parse_market_context,
    rank_scan_results,
)
from butterfly_guy.equity_scan.universes import build_symbol_map, load_sector_map, load_universes
from butterfly_guy.equity_scan.volume import fetch_avg_volumes, symbols_needing_rvol_fetch
from butterfly_guy.services.notifier import DiscordNotifier

log = get_logger("run_morning_scan")


async def run_scan(
    *,
    app_config_path: str,
    scan_config_path: str,
    dry_run: bool = False,
) -> list[str]:
    app_config = load_config(app_config_path)
    scan_config = load_equity_scan_config(scan_config_path)

    universes = load_universes(
        scan_config.universes,
        universe_dir=scan_config.universe_dir,
        custom_watchlist=scan_config.custom_watchlist,
    )
    symbol_map = build_symbol_map(universes)
    symbols = sorted(symbol_map)
    if not symbols:
        raise RuntimeError(
            "No symbols loaded. Refresh universes with refresh_equity_universes.py "
            "and add tickers to custom.txt."
        )

    schwab = SchwabClientWrapper(app_config.schwab)
    await schwab.initialize()
    try:
        generated_at = now_eastern()
        log.info(
            "equity_scan_start",
            universes=scan_config.universes,
            symbols=len(symbols),
        )
        quotes = await schwab.get_equity_quotes(symbols, batch_size=scan_config.batch_size)
        context_quotes = await schwab.get_equity_quotes(
            scan_config.context_symbols,
            batch_size=len(scan_config.context_symbols),
        )
        sector_map = load_sector_map(scan_config.universe_dir)

        in_premarket = is_premarket_window(
            generated_at,
            start=scan_config.premarket_start_et,
        )

        avg_volumes: dict[str, float] = {}
        if scan_config.filters.min_rvol > 0:
            rvol_symbols = symbols_needing_rvol_fetch(quotes)
            log.info(
                "equity_scan_rvol_targets",
                universe=len(symbols),
                needing_rvol=len(rvol_symbols),
            )
            avg_volumes = await fetch_avg_volumes(
                schwab,
                rvol_symbols,
                lookback_days=scan_config.rvol_lookback_days,
                concurrency=scan_config.rvol_fetch_concurrency,
            )
            log.info("equity_scan_rvol_loaded", symbols_with_avg_volume=len(avg_volumes))
        else:
            log.info("equity_scan_rvol_skipped", reason="min_rvol disabled")

        snapshots = build_snapshots(
            quotes,
            symbol_map,
            scan_config,
            avg_volumes=avg_volumes,
            sector_map=sector_map,
            in_premarket=in_premarket,
        )
        market_context = [
            ctx
            for symbol, payload in context_quotes.items()
            if (ctx := parse_market_context(symbol, payload)) is not None
        ]

        results = rank_scan_results(
            snapshots,
            settings=scan_config,
            movers_up=[],
            movers_down=[],
            market_context=market_context,
            scanned_symbols=len(symbols),
            generated_at=generated_at,
        )
        messages = build_report(results, settings=scan_config, generated_at=generated_at)
        archive_path = archive_report(
            messages,
            report_dir=scan_config.report_dir,
            generated_at=generated_at,
        )
        log.info(
            "equity_scan_complete",
            prior_gainers=len(results.prior_gainers),
            prior_losers=len(results.prior_losers),
            premarket_gainers=len(results.premarket_gainers),
            premarket_losers=len(results.premarket_losers),
            matched_symbols=results.matched_symbols,
            show_premarket=results.show_premarket,
            messages=len(messages),
            archive=str(archive_path),
        )
        if dry_run:
            for message in messages:
                print(message)
                print("\n" + ("-" * 60) + "\n")
            return messages

        env = {**dotenv_values(".env"), **os.environ}
        webhook = env.get("EQUITY_DISCORD_WEBHOOK_URL", "")
        if not webhook:
            raise RuntimeError(
                "EQUITY_DISCORD_WEBHOOK_URL not configured in .env or environment"
            )
        notifier = DiscordNotifier(webhook)
        await notifier.notify_messages(messages)
        return messages
    finally:
        await schwab.close()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Schwab equity morning scan.")
    parser.add_argument("--config", default="configs/config.yaml", help="Butterfly Guy config")
    parser.add_argument(
        "--scan-config",
        default="configs/equity_scan.yaml",
        help="Equity scan config",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the report instead of posting to Discord",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    setup_logging(args.log_level, json_output=False)
    await run_scan(
        app_config_path=args.config,
        scan_config_path=args.scan_config,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    asyncio.run(main())
