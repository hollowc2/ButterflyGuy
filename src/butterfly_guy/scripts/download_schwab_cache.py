"""Download Schwab 1-min SPY data into local JSON cache.

Usage:
    uv run python src/butterfly_guy/scripts/download_schwab_cache.py
    uv run python src/butterfly_guy/scripts/download_schwab_cache.py 2026-01-01 2026-03-10
    uv run python src/butterfly_guy/scripts/download_schwab_cache.py --force
"""

from __future__ import annotations

import asyncio
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import dotenv_values

from butterfly_guy.backtest._cache_utils import day_cache_path, save_day
from butterfly_guy.backtest.schwab_loader import SchwabDataLoader
from butterfly_guy.core.logging import setup_logging

setup_logging(log_level="WARNING", json_output=False)

CACHE_DIR = Path("data/schwab")
MAX_HISTORY_DAYS = 48


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    dates, d = [], start
    while d <= end:
        if d.weekday() < 5:
            dates.append(d)
        d += dt.timedelta(days=1)
    return dates


async def main() -> None:
    force = "--force" in sys.argv
    date_args = [a for a in sys.argv[1:] if a.startswith("20")]

    today = dt.date.today()

    if len(date_args) >= 2:
        start = dt.date.fromisoformat(date_args[0])
        end = dt.date.fromisoformat(date_args[1])
    elif len(date_args) == 1:
        start = dt.date.fromisoformat(date_args[0])
        end = today - dt.timedelta(days=1)
    else:
        start = today - dt.timedelta(days=MAX_HISTORY_DAYS)
        end = today - dt.timedelta(days=1)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    env = dotenv_values(".env")
    loader = SchwabDataLoader(
        token_path=env.get("SCHWAB_TOKEN_PATH", "tokens.json"),
        api_key=env.get("SCHWAB_API_KEY", ""),
        secret_key=env.get("SCHWAB_SECRET_KEY", ""),
    )

    dates = date_range(start, end)
    print(f"\nDownloading {len(dates)} trading days ({start} → {end}) into {CACHE_DIR}/")
    if force:
        print("  --force: overwriting existing cache files")
    print()

    saved = skipped = failed = 0

    for date in dates:
        path = day_cache_path(date, CACHE_DIR)
        if path.exists() and not force:
            print(f"  skip  {date} (cached)")
            skipped += 1
            continue

        try:
            day = await loader.load_day(date)
            if day:
                save_day(day, path)
                print(f"  saved {date} ({len(day.bars)} bars)")
                saved += 1
            else:
                print(f"  empty {date} — no data returned")
                failed += 1
        except Exception as e:
            print(f"  error {date} — {e}")
            failed += 1

    await loader.close()

    print(f"\n--- Summary ---")
    print(f"  Saved:   {saved}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print(f"  Total:   {saved + skipped + failed}")


if __name__ == "__main__":
    asyncio.run(main())
