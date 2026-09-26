"""Market timezone helpers for 0-DTE trading."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")
PACIFIC = ZoneInfo("America/Los_Angeles")

MARKET_OPEN = dt.time(9, 30)
MARKET_CLOSE = dt.time(16, 0)
PREMARKET_OPEN = dt.time(4, 0)
AFTERHOURS_CLOSE = dt.time(20, 0)
EARLY_CLOSE = dt.time(13, 0)


def _observed_date(holiday: dt.date) -> dt.date:
    if holiday.weekday() == 5:
        return holiday - dt.timedelta(days=1)
    if holiday.weekday() == 6:
        return holiday + dt.timedelta(days=1)
    return holiday


def _nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> dt.date:
    first = dt.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + dt.timedelta(days=offset + (occurrence - 1) * 7)


def _last_weekday(year: int, month: int, weekday: int) -> dt.date:
    if month == 12:
        next_month = dt.date(year + 1, 1, 1)
    else:
        next_month = dt.date(year, month + 1, 1)
    last = next_month - dt.timedelta(days=1)
    return last - dt.timedelta(days=(last.weekday() - weekday) % 7)


def _easter_sunday(year: int) -> dt.date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    line = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * line) // 451
    month = (h + line - 7 * m + 114) // 31
    day = (h + line - 7 * m + 114) % 31 + 1
    return dt.date(year, month, day)


def get_us_market_holidays(year: int) -> set[dt.date]:
    holidays = {
        _observed_date(dt.date(year, 1, 1)),
        _observed_date(dt.date(year, 7, 4)),
        _observed_date(dt.date(year, 12, 25)),
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        _last_weekday(year, 5, 0),
        _nth_weekday(year, 9, 0, 1),
        _nth_weekday(year, 11, 3, 4),
        _easter_sunday(year) - dt.timedelta(days=2),
    }
    if year >= 2022:
        holidays.add(_observed_date(dt.date(year, 6, 19)))
    next_nyny = _observed_date(dt.date(year + 1, 1, 1))
    if next_nyny.year == year:
        holidays.add(next_nyny)
    return holidays


def now_utc() -> dt.datetime:
    """Current time in UTC."""
    return dt.datetime.now(dt.timezone.utc)


def now_eastern() -> dt.datetime:
    """Current time in US/Eastern."""
    return dt.datetime.now(EASTERN)


def session_date(at: dt.datetime | None = None) -> dt.date:
    """Calendar date for the US/Eastern trading session."""
    return (at or now_eastern()).astimezone(EASTERN).date()


def now_pacific() -> dt.datetime:
    """Current time in US/Pacific."""
    return dt.datetime.now(PACIFIC)


def is_market_open(at: dt.datetime | None = None) -> bool:
    """Check if the market is currently open."""
    now = (at or now_eastern()).astimezone(EASTERN)
    if not is_trading_day(now.date()):
        return False
    return MARKET_OPEN <= now.time() < market_close_time(now.date())


def is_premarket_window(at: dt.datetime | None = None, *, start: str = "04:00") -> bool:
    """True during weekday premarket (default 4:00–9:30 AM ET)."""
    now = (at or now_eastern()).astimezone(EASTERN)
    if not is_trading_day(now.date()):
        return False
    start_time = dt.time.fromisoformat(start)
    return start_time <= now.time() < MARKET_OPEN


def is_trading_day(d: dt.date | None = None) -> bool:
    """Check if a given date is a trading day (weekday, not a holiday)."""
    d = d or now_eastern().date()
    if d.weekday() >= 5:
        return False
    if d in get_us_market_holidays(d.year):
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
    close = market_close_time(now.date())
    close_dt = now.replace(hour=close.hour, minute=close.minute, second=0, microsecond=0)
    delta = close_dt - now
    return max(0.0, delta.total_seconds() / 60.0)


def market_close_time(d: dt.date | None = None) -> dt.time:
    """Regular cash-market close for the date."""
    d = d or now_eastern().date()
    if d in get_us_market_early_closes(d.year):
        return EARLY_CLOSE
    return MARKET_CLOSE


def get_us_market_early_closes(year: int) -> set[dt.date]:
    """NYSE 1:00 PM ET early closes: day after Thanksgiving, and Jul 3 / Dec 24
    when each is a weekday that is not itself an observed holiday."""
    holidays = get_us_market_holidays(year)
    early_closes = {_nth_weekday(year, 11, 3, 4) + dt.timedelta(days=1)}
    for candidate in (dt.date(year, 7, 3), dt.date(year, 12, 24)):
        if candidate.weekday() < 5 and candidate not in holidays:
            early_closes.add(candidate)
    return early_closes


def get_time_regime(minutes_since_open: float) -> str:
    """Classify minutes since open into a named time regime."""
    if minutes_since_open < 120:
        return "morning"
    if minutes_since_open < 240:
        return "late_morning"
    return "afternoon"


def minutes_since_open(at: dt.datetime | None = None) -> float:
    """Minutes elapsed since market open."""
    now = (at or now_eastern()).astimezone(EASTERN)
    open_dt = now.replace(hour=9, minute=30, second=0, microsecond=0)
    delta = now - open_dt
    return max(0.0, delta.total_seconds() / 60.0)
