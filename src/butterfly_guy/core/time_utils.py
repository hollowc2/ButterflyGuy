"""Market timezone helpers for 0-DTE trading."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")
PACIFIC = ZoneInfo("America/Los_Angeles")

MARKET_OPEN = dt.time(9, 30)
MARKET_CLOSE = dt.time(16, 0)

# US market holidays (2026) — extend as needed
HOLIDAYS_2026 = {
    dt.date(2026, 1, 1),   # New Year's Day
    dt.date(2026, 1, 19),  # MLK Day
    dt.date(2026, 2, 16),  # Presidents' Day
    dt.date(2026, 4, 3),   # Good Friday
    dt.date(2026, 5, 25),  # Memorial Day
    dt.date(2026, 7, 3),   # Independence Day (observed)
    dt.date(2026, 9, 7),   # Labor Day
    dt.date(2026, 11, 26), # Thanksgiving
    dt.date(2026, 12, 25), # Christmas
}


def now_eastern() -> dt.datetime:
    """Current time in US/Eastern."""
    return dt.datetime.now(EASTERN)


def now_pacific() -> dt.datetime:
    """Current time in US/Pacific."""
    return dt.datetime.now(PACIFIC)


def is_market_open(at: dt.datetime | None = None) -> bool:
    """Check if the market is currently open."""
    now = (at or now_eastern()).astimezone(EASTERN)
    if not is_trading_day(now.date()):
        return False
    return MARKET_OPEN <= now.time() < MARKET_CLOSE


def is_trading_day(d: dt.date | None = None) -> bool:
    """Check if a given date is a trading day (weekday, not a holiday)."""
    d = d or now_eastern().date()
    if d.weekday() >= 5:
        return False
    if d in HOLIDAYS_2026:
        return False
    return True


def time_in_window(
    start: str, end: str, tz: str = "US/Pacific", at: dt.datetime | None = None
) -> bool:
    """Check if current time is within the given window (HH:MM strings)."""
    zone = ZoneInfo(tz)
    now = (at or dt.datetime.now(zone)).astimezone(zone)
    start_time = dt.time.fromisoformat(start)
    end_time = dt.time.fromisoformat(end)
    return start_time <= now.time() <= end_time


def get_0dte_expiration(at: dt.datetime | None = None) -> dt.date:
    """Get today's date as the 0-DTE expiration (SPX has daily expirations)."""
    now = (at or now_eastern()).astimezone(EASTERN)
    return now.date()


def minutes_to_close(at: dt.datetime | None = None) -> float:
    """Minutes remaining until market close."""
    now = (at or now_eastern()).astimezone(EASTERN)
    close_dt = now.replace(hour=16, minute=0, second=0, microsecond=0)
    delta = close_dt - now
    return max(0.0, delta.total_seconds() / 60.0)


def minutes_since_open(at: dt.datetime | None = None) -> float:
    """Minutes elapsed since market open."""
    now = (at or now_eastern()).astimezone(EASTERN)
    open_dt = now.replace(hour=9, minute=30, second=0, microsecond=0)
    delta = now - open_dt
    return max(0.0, delta.total_seconds() / 60.0)
