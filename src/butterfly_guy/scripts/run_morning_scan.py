"""Morning equity scan — premarket movers and prior-day rallies/dumps via Schwab."""

# ruff: noqa: E402

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
from butterfly_guy.equity_scan.news import fetch_news_impacts
from butterfly_guy.equity_scan.report import archive_report, archive_report_json, build_report
from butterfly_guy.equity_scan.scanner import (
    EquitySnapshot,
    attach_news_impacts,
    build_snapshots,
    parse_market_context,
    rank_scan_results,
)
from butterfly_guy.equity_scan.universes import (
    build_symbol_map,
    load_liquid_meta,
    load_sector_map,
    load_universes,
)
from butterfly_guy.equity_scan.volume import fetch_avg_volumes, symbols_needing_rvol_fetch
from butterfly_guy.services.notifier import DiscordNotifier

log = get_logger("run_morning_scan")


def _news_candidate_symbols(
    snapshots: list[EquitySnapshot],
    *,
    limit: int,
) -> list[str]:
    ordered = sorted(
        snapshots,
        key=lambda snap: (
            "custom" in snap.universes,
            abs(snap.session_gap_pct),
            abs(snap.prior_day_pct),
            snap.volume,
        ),
        reverse=True,
    )
    return [snapshot.symbol for snapshot in ordered[:limit]]


async def run_scan(
    *,
    app_config_path: str,
    scan_config_path: str,
    dry_run: bool = False,
    open_scan: bool = False,
) -> list[str]:
    app_config = load_config(app_config_path)
    scan_config = load_equity_scan_config(scan_config_path)
    env = {**dotenv_values(".env"), **os.environ}
    for key in (
        scan_config.news.alpha_vantage_api_key_env,
        scan_config.news.sec_user_agent_env,
    ):
        if env.get(key):
            os.environ.setdefault(key, str(env[key]))
    if open_scan:
        scan_config.include_movers = True

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
        liquid_meta = load_liquid_meta(scan_config.universe_dir)
        reference_prices = {
            symbol: float(payload["price"])
            for symbol, payload in liquid_meta.items()
            if isinstance(payload, dict) and payload.get("price") is not None
        }

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

        rejected_symbols: dict[str, int] = {}
        bad_data: list[dict] = []
        snapshots = build_snapshots(
            quotes,
            symbol_map,
            scan_config,
            avg_volumes=avg_volumes,
            sector_map=sector_map,
            reference_prices=reference_prices,
            in_premarket=in_premarket,
            generated_at=generated_at,
            rejected_symbols=rejected_symbols,
            bad_data=bad_data,
        )
        news_symbols = _news_candidate_symbols(
            snapshots,
            limit=scan_config.news.max_symbols,
        )
        news_impacts = await fetch_news_impacts(
            news_symbols,
            settings=scan_config.news,
            generated_at=generated_at,
        )
        snapshots = attach_news_impacts(snapshots, news_impacts)
        log.info(
            "equity_scan_news_loaded",
            candidates=len(news_symbols),
            matched=len(news_impacts),
            providers=scan_config.news.providers,
        )
        market_context = [
            ctx
            for symbol, payload in context_quotes.items()
            if (ctx := parse_market_context(symbol, payload)) is not None
        ]
        movers_up: list[dict] = []
        movers_down: list[dict] = []
        if scan_config.include_movers:
            for index in scan_config.mover_indexes:
                try:
                    movers_up.extend(
                        await schwab.get_market_movers(index, sort_order="PERCENT_CHANGE_UP")
                    )
                    movers_down.extend(
                        await schwab.get_market_movers(index, sort_order="PERCENT_CHANGE_DOWN")
                    )
                except Exception as exc:
                    log.warning("equity_scan_movers_failed", index=index, error=str(exc))

        results = rank_scan_results(
            snapshots,
            settings=scan_config,
            movers_up=movers_up,
            movers_down=movers_down,
            market_context=market_context,
            scanned_symbols=len(symbols),
            generated_at=generated_at,
            rejected_symbols=rejected_symbols,
            bad_data=bad_data,
        )
        messages = build_report(results, settings=scan_config, generated_at=generated_at)
        archive_path = archive_report(
            messages,
            report_dir=scan_config.report_dir,
            generated_at=generated_at,
        )
        json_archive_path = archive_report_json(
            results,
            report_dir=scan_config.report_dir,
            generated_at=generated_at,
        )
        log.info(
            "equity_scan_complete",
            open_scan=open_scan,
            prior_gainers=len(results.prior_gainers),
            prior_losers=len(results.prior_losers),
            premarket_gainers=len(results.premarket_gainers),
            premarket_losers=len(results.premarket_losers),
            opening_focus=len(results.opening_focus),
            matched_symbols=results.matched_symbols,
            show_premarket=results.show_premarket,
            show_movers=results.show_movers,
            rejected_symbols=rejected_symbols,
            messages=len(messages),
            archive=str(archive_path),
            json_archive=str(json_archive_path),
        )
        if dry_run:
            for message in messages:
                print(message)
                print("\n" + ("-" * 60) + "\n")
            return messages

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
    parser.add_argument(
        "--open-scan",
        action="store_true",
        help="Include after-open Schwab mover buckets and Opening Focus context",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    setup_logging(args.log_level, json_output=False)
    await run_scan(
        app_config_path=args.config,
        scan_config_path=args.scan_config,
        dry_run=args.dry_run,
        open_scan=args.open_scan,
    )


if __name__ == "__main__":
    asyncio.run(main())
