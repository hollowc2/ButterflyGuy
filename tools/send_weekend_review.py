"""Send SPX weekend review to Discord #weekend-review.

Cron: Saturday 9:00 AM PT
  0 16 * * 6 cd /opt/butterflyguy && /opt/butterflyguy/.venv/bin/python tools/send_weekend_review.py >> /opt/butterflyguy/weekend_review.log 2>&1
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

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.core.time_utils import now_pacific
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.services.notifier import DiscordNotifier
from butterfly_guy.services.weekend_review import send_weekend_review

log = get_logger(__name__)


def parse_reference_date(week_ending: str | None) -> dt.date:
    if week_ending:
        return dt.date.fromisoformat(week_ending)
    return now_pacific().date()


async def main() -> int:
    parser = argparse.ArgumentParser(description="Send SPX weekend review to Discord")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument(
        "--week-ending",
        default=None,
        help="Friday ending the review week (YYYY-MM-DD); default: previous week from today",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print messages and write PNGs to /tmp without posting to Discord",
    )
    parser.add_argument(
        "--dry-run-dir",
        type=Path,
        default=Path("/tmp/butterfly-weekend-review"),
        help="Directory for --dry-run PNG output",
    )
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)
    reference = parse_reference_date(args.week_ending)

    webhook = os.environ.get("DISCORD_WEEKEND_REVIEW_WEBHOOK") or dotenv_values(ROOT / ".env").get(
        "DISCORD_WEEKEND_REVIEW_WEBHOOK",
        "",
    )
    if not args.dry_run and not webhook:
        print("ERROR: DISCORD_WEEKEND_REVIEW_WEBHOOK not configured")
        return 1

    notifier = DiscordNotifier(webhook) if webhook and not args.dry_run else None
    db = DatabasePool(config.database.dsn)
    await db.initialize()
    try:
        result = await send_weekend_review(
            db,
            underlying=config.strategy.underlying,
            reference=reference,
            notifier=notifier,
            dry_run=args.dry_run,
            dry_run_dir=args.dry_run_dir if args.dry_run else None,
        )
    finally:
        await db.close()

    if result.skipped:
        print(f"Skipped: {result.reason}")
        return 0

    if args.dry_run:
        print(
            f"Dry run complete: {result.weekly_trade_count} weekly trades, "
            f"{result.messages_sent} messages, PNGs in {args.dry_run_dir}"
        )
    else:
        print(
            f"OK: sent weekend review ({result.weekly_trade_count} trades, "
            f"{result.messages_sent} messages)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
