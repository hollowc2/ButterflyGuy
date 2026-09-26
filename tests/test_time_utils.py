"""Tests for market time utilities."""

import datetime as dt

from butterfly_guy.core.config import ProfitManagementSettings, TimeRegime
from butterfly_guy.core.time_utils import (
    EASTERN,
    get_0dte_expiration,
    get_time_regime,
    get_us_market_early_closes,
    is_market_open,
    is_trading_day,
    market_close_time,
    minutes_since_open,
    minutes_to_close,
    session_date,
    time_in_window,
)


def et(year, month, day, hour, minute) -> dt.datetime:
    return dt.datetime(year, month, day, hour, minute, tzinfo=EASTERN)


def test_market_open_during_hours():
    assert is_market_open(at=et(2026, 3, 10, 10, 0))  # 10am ET Tuesday


def test_market_closed_before_open():
    assert not is_market_open(at=et(2026, 3, 10, 9, 0))  # 9am ET


def test_market_closed_after_close():
    assert not is_market_open(at=et(2026, 3, 10, 16, 1))  # 4:01pm


def test_market_closed_after_early_close():
    assert market_close_time(dt.date(2026, 11, 27)) == dt.time(13, 0)
    assert not is_market_open(at=et(2026, 11, 27, 13, 1))
    assert minutes_to_close(at=et(2026, 11, 27, 12, 30)) == 30.0


def test_early_closes_reproduce_previous_2026_set():
    assert get_us_market_early_closes(2026) == {
        dt.date(2026, 11, 27),
        dt.date(2026, 12, 24),
    }


def test_early_close_day_after_thanksgiving():
    assert market_close_time(dt.date(2027, 11, 26)) == dt.time(13, 0)
    assert dt.date(2025, 11, 28) in get_us_market_early_closes(2025)


def test_early_close_christmas_eve_weekday_only_when_not_observed_holiday():
    assert dt.date(2025, 12, 24) in get_us_market_early_closes(2025)  # Wednesday
    # 2027: Christmas falls on Saturday, so Friday Dec 24 is the observed holiday.
    assert dt.date(2027, 12, 24) not in get_us_market_early_closes(2027)
    # 2022: Dec 24 is a Saturday.
    assert dt.date(2022, 12, 24) not in get_us_market_early_closes(2022)


def test_early_close_july_3_weekday_only_when_not_observed_holiday():
    assert dt.date(2025, 7, 3) in get_us_market_early_closes(2025)  # Thursday
    assert market_close_time(dt.date(2029, 7, 3)) == dt.time(13, 0)  # Tuesday
    # 2026: July 4 is a Saturday, so Friday July 3 is the observed holiday.
    assert dt.date(2026, 7, 3) not in get_us_market_early_closes(2026)
    # 2027: July 3 is a Saturday.
    assert dt.date(2027, 7, 3) not in get_us_market_early_closes(2027)


def test_regular_close_on_ordinary_day():
    assert market_close_time(dt.date(2027, 11, 24)) == dt.time(16, 0)


def test_market_closed_on_weekend():
    assert not is_market_open(at=et(2026, 3, 7, 11, 0))  # Saturday


def test_market_closed_on_holiday():
    # Good Friday 2026 = April 3
    assert not is_market_open(at=et(2026, 4, 3, 10, 0))
    # Independence Day 2026 is observed on Friday, July 3.
    assert not is_trading_day(dt.date(2026, 7, 3))
    assert not is_market_open(at=et(2026, 7, 3, 10, 0))


def test_is_trading_day_monday():
    assert is_trading_day(dt.date(2026, 3, 9))  # Monday


def test_is_trading_day_weekend():
    assert not is_trading_day(dt.date(2026, 3, 7))
    assert not is_trading_day(dt.date(2026, 3, 8))


def test_minutes_to_close():
    mins = minutes_to_close(at=et(2026, 3, 10, 15, 0))  # 1 hour before close
    assert abs(mins - 60.0) < 1.0


def test_minutes_since_open():
    mins = minutes_since_open(at=et(2026, 3, 10, 10, 30))  # 1 hour after open
    assert abs(mins - 60.0) < 1.0


def test_time_in_window_pst():
    # 10:15 ET = 7:15 PST — within 7:00-7:30 PST window
    at = et(2026, 3, 10, 10, 15)
    assert time_in_window("07:00", "07:30", tz="America/Los_Angeles", at=at)


def test_time_outside_window():
    # 11:00 ET = 8:00 PST — outside 7:00-7:30 PST
    at = et(2026, 3, 10, 11, 0)
    assert not time_in_window("07:00", "07:30", tz="America/Los_Angeles", at=at)


def test_get_0dte_expiration():
    at = et(2026, 3, 10, 10, 0)
    exp = get_0dte_expiration(at=at)
    assert exp == dt.date(2026, 3, 10)


def test_session_date_uses_eastern_across_utc_midnight():
    assert session_date(dt.datetime(2026, 7, 13, 0, 0, tzinfo=dt.timezone.utc)) == dt.date(
        2026, 7, 12
    )


def test_get_time_regime_defaults_to_120_and_240_minute_bounds():
    assert get_time_regime(119.9) == "morning"
    assert get_time_regime(120) == "late_morning"
    assert get_time_regime(239.9) == "late_morning"
    assert get_time_regime(240) == "afternoon"


def test_get_time_regime_uses_configured_bounds():
    regimes = ProfitManagementSettings(
        regimes={
            name: TimeRegime(
                start_minutes_after_open=start,
                end_minutes_after_open=end,
                drawdown_threshold=0.5,
            )
            for name, start, end in (
                ("morning", 0, 90),
                ("late_morning", 90, 300),
                ("afternoon", 300, 390),
            )
        }
    ).regimes

    assert get_time_regime(89, regimes) == "morning"
    assert get_time_regime(90, regimes) == "late_morning"
    assert get_time_regime(299, regimes) == "late_morning"
    assert get_time_regime(300, regimes) == "afternoon"
