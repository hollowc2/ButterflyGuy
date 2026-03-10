"""Tests for market time utilities."""

import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from butterfly_guy.core.time_utils import (
    EASTERN,
    is_market_open,
    is_trading_day,
    minutes_to_close,
    minutes_since_open,
    time_in_window,
    get_0dte_expiration,
)
from zoneinfo import ZoneInfo


def et(year, month, day, hour, minute) -> dt.datetime:
    return dt.datetime(year, month, day, hour, minute, tzinfo=EASTERN)


def test_market_open_during_hours():
    assert is_market_open(at=et(2026, 3, 10, 10, 0))  # 10am ET Tuesday


def test_market_closed_before_open():
    assert not is_market_open(at=et(2026, 3, 10, 9, 0))  # 9am ET


def test_market_closed_after_close():
    assert not is_market_open(at=et(2026, 3, 10, 16, 1))  # 4:01pm


def test_market_closed_on_weekend():
    assert not is_market_open(at=et(2026, 3, 7, 11, 0))  # Saturday


def test_market_closed_on_holiday():
    # Good Friday 2026 = April 3
    assert not is_market_open(at=et(2026, 4, 3, 10, 0))


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
