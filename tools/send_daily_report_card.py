"""Send daily margin-account report card to Discord #daily-report-card.

Cron: weekdays 6:00 PM Eastern / 22:00 UTC
  See infra/cron/daily_report_card.cron.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import os
import sys
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values
from schwab_gateway_sdk.client import GatewayMarketDataClient
from schwab_gateway_sdk.config import GatewayClientSettings

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from butterfly_guy.core.config import load_config  # noqa: E402
from butterfly_guy.core.logging import get_logger, setup_logging  # noqa: E402
from butterfly_guy.core.time_utils import is_trading_day, now_eastern  # noqa: E402
from butterfly_guy.data.providers import (  # noqa: E402
    DirectSchwabMarketDataProvider,
    GatewayAuthoritativeMarketDataProvider,
)
from butterfly_guy.data.schwab_client import SchwabClientWrapper  # noqa: E402
from butterfly_guy.reports.daily_report_card_config import (  # noqa: E402
    load_daily_report_card_config,
)
from butterfly_guy.services.daily_report_card import send_daily_report_card  # noqa: E402
from butterfly_guy.services.notifier import DiscordNotifier  # noqa: E402

log = get_logger(__name__)


def parse_report_date(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return now_eastern().date()


def load_report_gateway_settings(
    *,
    infra_env_path: Path = ROOT / "infra" / ".env",
    process_env: Mapping[str, str] | None = None,
) -> GatewayClientSettings:
    """Load the host cron's market-data settings without exposing key material."""
    environment = os.environ if process_env is None else process_env
    infra_values = dotenv_values(infra_env_path)

    def value(name: str, default: str = "") -> str:
        return str(environment.get(name) or infra_values.get(name) or default)

    return GatewayClientSettings(
        SCHWAB_ACCESS_MODE=value("SCHWAB_ACCESS_MODE_REPORT", "direct"),
        # The report runs on the host, so never inherit the trading containers'
        # Docker-only `http://schwab-gateway:8011` alias.
        SCHWAB_GATEWAY_URL=value(
            "SCHWAB_GATEWAY_REPORT_URL",
            "http://127.0.0.1:8011",
        ),
        SCHWAB_GATEWAY_API_KEY=value("SCHWAB_GATEWAY_API_KEY"),
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Send daily report card to Discord")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument(
        "--report-card-config",
        default="configs/daily_report_card.yaml",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Report date (YYYY-MM-DD); default: today in Eastern",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print messages and archive locally without posting to Discord",
    )
    parser.add_argument(
        "--dump-raw",
        action="store_true",
        help="Write raw Schwab JSON to reports/daily_report_card/raw/",
    )
    args = parser.parse_args()

    setup_logging()
    app_config = load_config(args.config)
    card_config = load_daily_report_card_config(args.report_card_config)
    report_date = parse_report_date(args.date)

    if not is_trading_day(report_date) and not args.dry_run:
        print(f"Skipped: {report_date} is not a trading day")
        return 0

    webhook = os.environ.get("DISCORD_DAILY_REPORT_CARD_WEBHOOK") or dotenv_values(
        ROOT / ".env"
    ).get("DISCORD_DAILY_REPORT_CARD_WEBHOOK", "")
    if not args.dry_run and not webhook:
        print("ERROR: DISCORD_DAILY_REPORT_CARD_WEBHOOK not configured")
        return 1

    notifier = DiscordNotifier(webhook) if webhook and not args.dry_run else None
    gateway_settings = load_report_gateway_settings()
    schwab = SchwabClientWrapper(app_config.schwab)
    gateway = None
    try:
        await schwab.initialize()
        market_data = DirectSchwabMarketDataProvider(schwab)
        if gateway_settings.access_mode == "gateway":
            gateway = GatewayMarketDataClient(
                gateway_settings.gateway_url,
                gateway_settings.gateway_api_key.get_secret_value(),
            )
            market_data = GatewayAuthoritativeMarketDataProvider(gateway)
        result = await send_daily_report_card(
            schwab,
            report_date=report_date,
            generated_at=now_eastern(),
            settings=card_config,
            notifier=notifier,
            dry_run=args.dry_run,
            dump_raw=args.dump_raw,
            dump_raw_dir=Path(card_config.report_dir) / "raw" if args.dump_raw else None,
            market_data=market_data,
        )
    finally:
        try:
            if gateway is not None:
                await gateway.close()
        finally:
            await schwab.close()

    if result.skipped:
        print(f"Skipped: {result.reason}")
        return 0

    if args.dry_run:
        print(
            f"Dry run complete: {result.trade_count} trades, "
            f"{result.messages_sent} messages, {result.charts_sent} charts, "
            f"archived under {card_config.report_dir}"
        )
    else:
        print(
            f"OK: sent daily report card ({result.trade_count} trades, "
            f"{result.messages_sent} messages, {result.charts_sent} charts)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
