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

from dotenv import dotenv_values

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from butterfly_guy.core.config import load_config  # noqa: E402
from butterfly_guy.core.logging import get_logger, setup_logging  # noqa: E402
from butterfly_guy.core.time_utils import is_trading_day, now_eastern  # noqa: E402
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
    schwab = SchwabClientWrapper(app_config.schwab)
    await schwab.initialize()
    try:
        result = await send_daily_report_card(
            schwab,
            report_date=report_date,
            generated_at=now_eastern(),
            settings=card_config,
            notifier=notifier,
            dry_run=args.dry_run,
            dump_raw=args.dump_raw,
            dump_raw_dir=Path(card_config.report_dir) / "raw" if args.dump_raw else None,
        )
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
