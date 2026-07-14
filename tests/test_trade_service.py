import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import (
    AppConfig,
    EntrySettings,
    ExecutionSettings,
    StrategySettings,
    VixWidthBucket,
)
from butterfly_guy.execution.order_manager import AmbiguousOrderError, TerminalOrderError
from butterfly_guy.services.trade_service import (
    TradeService,
    _session_open_from_intraday_candles,
    now_eastern,
)
from butterfly_guy.strategy.entry_selection import EntrySelectionResult


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


@pytest.mark.asyncio
async def test_live_attempt_entry_blocks_stale_chain_snapshot_before_spot_fetch():
    config = AppConfig(
        execution=ExecutionSettings(
            paper_trading=False,
            allow_live_trading=True,
        ),
        entry=EntrySettings(max_chain_snapshot_age_seconds=120),
    )
    schwab = AsyncMock()
    schwab.get_account_balances.return_value = {"buying_power": 10_000.0}
    risk_engine = AsyncMock()
    risk_engine.can_trade.return_value = (True, "ok")
    chain_queries = MagicMock()
    stale_snapshot = now_eastern() - dt.timedelta(minutes=5)
    chain_queries.get_latest_snapshot_time = AsyncMock(return_value=stale_snapshot)
    decision_queries = MagicMock()
    decision_queries.log_event = AsyncMock()
    service = TradeService(
        config=config,
        schwab=schwab,
        risk_engine=risk_engine,
        order_manager=AsyncMock(),
        builder=MagicMock(),
        selector=MagicMock(),
        direction_filter=MagicMock(),
        chain_queries=chain_queries,
        trade_queries=MagicMock(),
        candidate_queries=MagicMock(),
        decision_queries=decision_queries,
    )

    with patch("butterfly_guy.services.trade_service.time_in_window", return_value=True), patch(
        "butterfly_guy.services.trade_service.get_0dte_expiration",
        return_value=dt.date(2026, 6, 25),
    ):
        result = await service.attempt_entry()

    assert result is None
    schwab.get_spot_price.assert_not_called()
    schwab.get_option_chain.assert_not_called()
    assert any(
        call.args[1]["reason"] == "chain_snapshot_stale"
        for call in decision_queries.log_event.await_args_list
    )


@pytest.mark.asyncio
async def test_attempt_entry_does_not_restart_after_terminal_rejection():
    config = AppConfig(
        execution=ExecutionSettings(paper_trading=True, price_ladder_steps=2),
        entry=EntrySettings(strike_selection_method="TARGET_COST"),
    )
    schwab = AsyncMock()
    schwab.get_spot_price.return_value = 6000.0
    schwab.get_option_chain.return_value = {}
    risk_engine = AsyncMock()
    risk_engine.can_trade.return_value = (True, "ok")
    order_manager = AsyncMock()
    order_manager.execute_single_attempt.side_effect = TerminalOrderError(
        "REJECTED", "ORD1"
    )
    chain_queries = MagicMock()
    chain_queries.db.pool.fetchval = AsyncMock(return_value=5990.0)
    chain_queries.db.pool.fetchrow = AsyncMock(return_value=None)
    candidate_queries = MagicMock()
    candidate_queries.bulk_insert = AsyncMock()
    decision_queries = MagicMock()
    decision_queries.log_event = AsyncMock()
    best = MagicMock()
    best.direction = "CALL"
    best.wing_width = 10
    best.center_strike = 6000.0
    best.lower_strike = 5990.0
    best.upper_strike = 6010.0
    best.cost = 1.0
    best.ask = 1.1
    best.max_profit = 9.0
    best.reward_risk = 9.0
    best.lower_be = 5991.0
    best.upper_be = 6009.0
    best.distance_from_spot = 0.0
    best.spot_price = 6000.0
    selection = EntrySelectionResult(
        candidate=best,
        candidates=(best,),
        active_widths=(10,),
        active_sigmas=(None,),
        per_width_bests=(best,),
        selection_method="TARGET_COST",
    )
    service = TradeService(
        config=config,
        schwab=schwab,
        risk_engine=risk_engine,
        order_manager=order_manager,
        builder=MagicMock(),
        selector=MagicMock(),
        direction_filter=MagicMock(get_direction=MagicMock(return_value="CALL")),
        chain_queries=chain_queries,
        trade_queries=MagicMock(),
        candidate_queries=candidate_queries,
        decision_queries=decision_queries,
    )
    service._session_open_price = AsyncMock(return_value=6000.0)
    service._parse_chain_to_quotes = MagicMock(return_value=[MagicMock()])
    service._entry_selection_parity_report = AsyncMock(return_value={})

    with patch("butterfly_guy.services.trade_service.time_in_window", return_value=True), \
         patch(
             "butterfly_guy.services.trade_service.select_entry_candidate",
             return_value=selection,
         ), pytest.raises(TerminalOrderError, match="REJECTED"):
        await service.attempt_entry()

    order_manager.execute_single_attempt.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_point", ["trade", "intent", "risk"])
async def test_filled_entry_persistence_failure_stops_for_reconciliation(
    failure_point,
):
    config = AppConfig(
        execution=ExecutionSettings(
            paper_trading=False,
            allow_live_trading=True,
            price_ladder_steps=1,
        ),
        entry=EntrySettings(strike_selection_method="TARGET_COST"),
    )
    schwab = AsyncMock()
    schwab.get_account_balances.return_value = {"buying_power": 10_000.0}
    schwab.get_spot_price.return_value = 6000.0
    schwab.get_option_chain.return_value = {}
    risk_engine = AsyncMock()
    risk_engine.can_trade.return_value = (True, "ok")
    order_manager = AsyncMock()
    order_manager.execute_single_attempt.return_value = {
        "fill_price": 1.0,
        "fill_time": dt.datetime(2026, 7, 14, 14, 0, tzinfo=dt.timezone.utc),
        "intent_id": 42,
        "broker_fill_evidence": {"status": "FILLED"},
    }
    order_manager.intent_queries = AsyncMock()
    chain_queries = MagicMock()
    chain_queries.db.pool.fetchval = AsyncMock(return_value=5990.0)
    chain_queries.db.pool.fetchrow = AsyncMock(return_value=None)
    trade_queries = MagicMock(insert_trade=AsyncMock(return_value=99))
    candidate_queries = MagicMock(bulk_insert=AsyncMock())
    decision_queries = MagicMock(log_event=AsyncMock())
    best = MagicMock(
        direction="CALL",
        wing_width=10,
        center_strike=6000.0,
        lower_strike=5990.0,
        upper_strike=6010.0,
        cost=1.0,
        ask=1.0,
        max_profit=9.0,
        reward_risk=9.0,
        lower_be=5991.0,
        upper_be=6009.0,
        distance_from_spot=0.0,
        spot_price=6000.0,
        lower_symbol="LOWER",
        center_symbol="CENTER",
        upper_symbol="UPPER",
    )
    selection = EntrySelectionResult(
        candidate=best,
        candidates=(best,),
        active_widths=(10,),
        active_sigmas=(None,),
        per_width_bests=(best,),
        selection_method="TARGET_COST",
    )
    service = TradeService(
        config=config,
        schwab=schwab,
        risk_engine=risk_engine,
        order_manager=order_manager,
        builder=MagicMock(),
        selector=MagicMock(),
        direction_filter=MagicMock(get_direction=MagicMock(return_value="CALL")),
        chain_queries=chain_queries,
        trade_queries=trade_queries,
        candidate_queries=candidate_queries,
        decision_queries=decision_queries,
    )
    service._live_chain_snapshot_fresh = AsyncMock(return_value=True)
    service._session_open_price = AsyncMock(return_value=6000.0)
    service._parse_chain_to_quotes = MagicMock(return_value=[MagicMock()])
    service._entry_selection_parity_report = AsyncMock(return_value={})
    service._acquire_entry_lock = AsyncMock(return_value=(MagicMock(), "lock"))
    service._release_entry_lock = AsyncMock()

    if failure_point == "trade":
        trade_queries.insert_trade.side_effect = RuntimeError("db unavailable")
    elif failure_point == "intent":
        order_manager.intent_queries.link_trade.side_effect = RuntimeError(
            "intent unavailable"
        )
    else:
        risk_engine.record_trade.side_effect = RuntimeError("risk unavailable")

    with patch("butterfly_guy.services.trade_service.time_in_window", return_value=True), patch(
        "butterfly_guy.services.trade_service.get_0dte_expiration",
        return_value=dt.date(2026, 7, 14),
    ), patch(
        "butterfly_guy.services.trade_service.select_entry_candidate",
        return_value=selection,
    ), pytest.raises(AmbiguousOrderError, match="broker fill was not fully persisted"):
        await service.attempt_entry()

    order_manager.execute_single_attempt.assert_awaited_once()
    service._release_entry_lock.assert_awaited_once()
