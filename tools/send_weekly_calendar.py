"""Send the upcoming week's USD economic calendar to Discord #upcoming-week-prep.

Cron example:
  0 2 * * 1 cd /opt/butterflyguy && .venv/bin/python tools/send_weekly_calendar.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from butterfly_guy.services.forex_calendar import fetch_usd_events, format_usd_calendar_text
from butterfly_guy.services.notifier import DiscordNotifier


async def main() -> None:
    webhook = os.environ.get("DISCORD_UPCOMING_WEEK_PREP_WEBHOOK") or dotenv_values(
        ROOT / ".env"
    ).get(
        "DISCORD_UPCOMING_WEEK_PREP_WEBHOOK",
        "",
    )
    if not webhook:
        print("ERROR: DISCORD_UPCOMING_WEEK_PREP_WEBHOOK not configured")
        sys.exit(1)

    events = await fetch_usd_events()
    calendar_text = format_usd_calendar_text(events)
    await DiscordNotifier(webhook).notify_weekly_calendar(calendar_text)
    print(f"OK: sent weekly USD calendar ({len(events)} events)")


if __name__ == "__main__":
    asyncio.run(main())
