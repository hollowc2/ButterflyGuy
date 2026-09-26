import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

from butterfly_guy.core.config import AppConfig, StrategySettings
from butterfly_guy.data.collector import OptionChainCollector

SESSION = dt.date(2026, 9, 24)


def _daily_candle(date: dt.date, close: float) -> dict:
    # Schwab daily candles are stamped at midnight Central.
    ts = dt.datetime.combine(date, dt.time(5, 0), tzinfo=dt.timezone.utc)
    return {
        "datetime": int(ts.timestamp() * 1000),
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 0,
    }


def _collector(underlying: str = "SPX") -> tuple[OptionChainCollector, MagicMock, MagicMock]:
    schwab = MagicMock()
    schwab.get_daily_bars = AsyncMock()
    daily_bar_queries = MagicMock()
    daily_bar_queries.bulk_upsert = AsyncMock(side_effect=lambda rows: len(rows))
    collector = OptionChainCollector(
        config=AppConfig(strategy=StrategySettings(underlying=underlying)),
        schwab=schwab,
        chain_queries=MagicMock(),
        spot_queries=MagicMock(),
        daily_bar_queries=daily_bar_queries,
    )
    return collector, schwab, daily_bar_queries


async def test_daily_bars_skip_todays_in_progress_candle():
    collector, schwab, daily_bar_queries = _collector()
    schwab.get_daily_bars.return_value = [
        _daily_candle(dt.date(2026, 9, 23), 6600.0),
        _daily_candle(SESSION, 6610.0),
    ]

    with patch("butterfly_guy.data.collector.session_date", return_value=SESSION):
        await collector.collect_daily_bars()

    for call in daily_bar_queries.bulk_upsert.await_args_list:
        dates = [row["date"] for row in call.args[0]]
        assert dates == [dt.date(2026, 9, 23)]
    assert collector._daily_bars_date == SESSION


async def test_daily_bars_failure_leaves_refresh_pending_and_retries():
    collector, schwab, daily_bar_queries = _collector()
    good = [_daily_candle(dt.date(2026, 9, 23), 6600.0)]
    # SPX succeeds, VIX fails on the first pass; both succeed on the retry.
    schwab.get_daily_bars.side_effect = [good, RuntimeError("schwab 503"), good, good]

    with patch("butterfly_guy.data.collector.session_date", return_value=SESSION):
        await collector.collect_daily_bars()
        assert collector._daily_bars_date is None

        await collector.collect_daily_bars()
        assert collector._daily_bars_date == SESSION

        await collector.collect_daily_bars()

    assert schwab.get_daily_bars.await_count == 4


async def test_daily_bars_use_eastern_session_date_not_host_date():
    collector, schwab, _ = _collector(underlying="NDX")
    schwab.get_daily_bars.return_value = []
    # 22:00 ET on Sep 24 is already Sep 25 in UTC.
    late_evening = dt.datetime(2026, 9, 25, 2, 0, tzinfo=dt.timezone.utc)

    with patch("butterfly_guy.core.time_utils.now_eastern", return_value=late_evening):
        await collector.collect_daily_bars()

    assert collector._daily_bars_date == SESSION
