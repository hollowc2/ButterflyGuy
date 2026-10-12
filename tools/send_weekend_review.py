"""Send the weekend review to Discord #weekend-review.

Posts one review per asset with paper and executable P&L side by side. SPX also
gets per-trade recaps with charts; NDX and XSP post their summary only.

Cron: Saturday 16:00 UTC; see infra/cron/weekend_review.cron for the isolated
reporting release used on Helios (SPX only).
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import os
import sys
from pathlib import Path

import yaml
from dotenv import dotenv_values, load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))

from butterfly_guy.core.config import DatabaseSettings
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.core.time_utils import now_pacific
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.services.notifier import DiscordNotifier
from butterfly_guy.services.weekend_review import send_weekend_review

log = get_logger(__name__)


class ReviewSettings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="ignore")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)


def load_review_database(config_path: str | Path, env_file: str | Path) -> DatabaseSettings:
    """Read only the reporting dependency; trading config may use a newer schema."""
    with Path(config_path).open() as config_file:
        config = yaml.safe_load(config_file) or {}
    load_dotenv(env_file)
    database = dict(config.get("database") or {})
    if os.getenv("DATABASE_PASSWORD") and not os.getenv("DATABASE__PASSWORD"):
        database.setdefault("password", os.environ["DATABASE_PASSWORD"])
    return ReviewSettings(database=database).database


def parse_reference_date(week_ending: str | None) -> dt.date:
    if week_ending:
        return dt.date.fromisoformat(week_ending)
    return now_pacific().date()


async def main() -> int:
    parser = argparse.ArgumentParser(description="Send the weekend review to Discord")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
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
    parser.add_argument(
        "--assets",
        default="SPX,NDX,XSP",
        help="Comma-separated underlyings to review, in posting order",
    )
    parser.add_argument(
        "--recap-assets",
        default="SPX",
        help="Underlyings that also get per-trade recaps with charts",
    )
    args = parser.parse_args()
    assets = [a.strip().upper() for a in args.assets.split(",") if a.strip()]
    recap_assets = {a.strip().upper() for a in args.recap_assets.split(",") if a.strip()}

    setup_logging()
    database = load_review_database(args.config, args.env_file)
    reference = parse_reference_date(args.week_ending)

    webhook = os.environ.get("DISCORD_WEEKEND_REVIEW_WEBHOOK") or dotenv_values(args.env_file).get(
        "DISCORD_WEEKEND_REVIEW_WEBHOOK",
        "",
    )
    if not args.dry_run and not webhook:
        print("ERROR: DISCORD_WEEKEND_REVIEW_WEBHOOK not configured")
        return 1

    notifier = DiscordNotifier(webhook) if webhook and not args.dry_run else None
    db = DatabasePool(database.dsn)
    await db.initialize()
    try:
        for asset in assets:
            result = await send_weekend_review(
                db,
                underlying=asset,
                reference=reference,
                notifier=notifier,
                dry_run=args.dry_run,
                dry_run_dir=args.dry_run_dir / asset if args.dry_run else None,
                include_trade_recaps=asset in recap_assets,
            )
            if result.skipped:
                print(f"{asset}: skipped ({result.reason})")
            elif args.dry_run:
                print(
                    f"{asset}: dry run complete: {result.weekly_trade_count} weekly trades, "
                    f"{result.messages_sent} messages, PNGs in {args.dry_run_dir / asset}"
                )
            else:
                print(
                    f"{asset}: sent weekend review ({result.weekly_trade_count} trades, "
                    f"{result.messages_sent} messages)"
                )
    finally:
        await db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
