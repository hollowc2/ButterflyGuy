import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import AppConfig, EntrySettings, StrategySettings, VixWidthBucket
from butterfly_guy.services.trade_service import (
    TradeService,
    _session_open_from_intraday_candles,
    now_eastern,
)


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


@pytest.mark.asyncio
async def test_attempt_entry_blocks_stale_vix_before_chain_fetch():
    config = AppConfig(
        strategy=StrategySettings(
            underlying="SPX",
            vix_width_buckets=[VixWidthBucket(vix_max=9999.0, widths=[10, 20, 30])],
        ),
        entry=EntrySettings(strike_selection_method="VIX", max_vix_age_seconds=300),
    )
    schwab = AsyncMock()
    schwab.get_spot_price.return_value = 6000.0
    risk_engine = AsyncMock()
    risk_engine.can_trade.return_value = (True, "ok")
    direction_filter = MagicMock()
    direction_filter.get_direction.return_value = "CALL"
    chain_queries = MagicMock()
    chain_queries.db.pool.fetchval = AsyncMock(return_value=5900.0)
    stale_vix_ts = now_eastern() - dt.timedelta(minutes=10)
    chain_queries.db.pool.fetchrow = AsyncMock(
        return_value={"ts": stale_vix_ts, "price": 18.0}
    )
    decision_queries = MagicMock()
    decision_queries.log_event = AsyncMock()
    service = TradeService(
        config=config,
        schwab=schwab,
        risk_engine=risk_engine,
        order_manager=AsyncMock(),
        builder=MagicMock(),
        selector=MagicMock(),
        direction_filter=direction_filter,
        chain_queries=chain_queries,
        trade_queries=MagicMock(),
        candidate_queries=MagicMock(),
        decision_queries=decision_queries,
    )
    service._session_open_price = AsyncMock(return_value=6001.0)

    with patch("butterfly_guy.services.trade_service.time_in_window", return_value=True), \
         patch("butterfly_guy.risk.risk_engine.is_trading_day", return_value=True), \
         patch("butterfly_guy.risk.risk_engine.is_market_open", return_value=True):
        result = await service.attempt_entry()

    assert result is None
    schwab.get_option_chain.assert_not_called()
    event_payloads = [
        call.args[1]
        for call in decision_queries.log_event.await_args_list
        if call.args[0] == "entry_blocked"
    ]
    assert any(
        payload["reason"] == "vix_stale"
        and payload["vix_timestamp"] == stale_vix_ts.isoformat()
        and payload["vix_age_seconds"] >= 600
        and payload["max_vix_age_seconds"] == 300
        for payload in event_payloads
    )
