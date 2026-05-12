import datetime as dt

from butterfly_guy.services.trade_service import _session_open_from_intraday_candles


def _candle(ts: dt.datetime, open_price: float) -> dict:
    return {
        "datetime": int(ts.timestamp() * 1000),
        "open": open_price,
        "high": open_price,
        "low": open_price,
        "close": open_price,
    }


def test_session_open_uses_first_regular_session_bar_for_requested_date():
    session_date = dt.date(2026, 5, 12)
    candles = [
        _candle(dt.datetime(2026, 5, 11, 13, 30, tzinfo=dt.timezone.utc), 29185.82),
        _candle(dt.datetime(2026, 5, 12, 13, 30, tzinfo=dt.timezone.utc), 29067.35),
        _candle(dt.datetime(2026, 5, 12, 13, 31, tzinfo=dt.timezone.utc), 29056.21),
    ]

    assert _session_open_from_intraday_candles(candles, session_date) == 29067.35


def test_session_open_ignores_premarket_and_missing_open_values():
    session_date = dt.date(2026, 5, 12)
    no_open_bar = {
        "datetime": int(
            dt.datetime(2026, 5, 12, 13, 30, tzinfo=dt.timezone.utc).timestamp()
            * 1000
        )
    }
    candles = [
        _candle(dt.datetime(2026, 5, 12, 13, 29, tzinfo=dt.timezone.utc), 29320.66),
        no_open_bar,
        _candle(dt.datetime(2026, 5, 12, 13, 31, tzinfo=dt.timezone.utc), 29056.21),
    ]

    assert _session_open_from_intraday_candles(candles, session_date) == 29056.21


def test_session_open_returns_none_when_no_regular_session_bar_exists():
    session_date = dt.date(2026, 5, 12)
    candles = [
        _candle(dt.datetime(2026, 5, 11, 13, 30, tzinfo=dt.timezone.utc), 29185.82),
        _candle(dt.datetime(2026, 5, 12, 13, 29, tzinfo=dt.timezone.utc), 29320.66),
    ]

    assert _session_open_from_intraday_candles(candles, session_date) is None
