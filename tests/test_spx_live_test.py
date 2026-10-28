"""Dated live pilot cannot open outside its session or lose audit evidence silently."""

import datetime as dt
from unittest.mock import AsyncMock, patch

import pytest

from butterfly_guy.core.config import AppConfig, ExecutionSettings
from butterfly_guy.db.queries import OrderIntentQueries
from butterfly_guy.services.trade_service import TradeService
from tests.test_order_manager import make_candidate, make_order_manager, make_settings

DAY = dt.date(2026, 10, 29)


@pytest.mark.parametrize(
    "changes",
    [
        {"paper_trading": True},
        {"record_live_execution": False},
    ],
)
def test_pilot_config_requires_live_audit(changes):
    execution = dict(live_test_date=DAY, paper_trading=False, record_live_execution=True)
    execution.update(changes)
    with pytest.raises(ValueError, match="dated live test"):
        AppConfig(execution=ExecutionSettings(**execution))


@pytest.mark.asyncio
async def test_no_account_or_market_reads_outside_pilot_day():
    service = TradeService.__new__(TradeService)
    service.config = AppConfig(
        execution=ExecutionSettings(
            live_test_date=DAY,
            paper_trading=False,
            record_live_execution=True,
        )
    )
    with patch(
        "butterfly_guy.services.trade_service.session_date", return_value=DAY.replace(day=30)
    ):
        assert await service.attempt_entry() is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "quantity,limit,day", [(2, 3, DAY), (1, 4.05, DAY), (1, 3, DAY.replace(day=30))]
)
async def test_order_boundary_blocks_size_debit_and_wrong_day(quantity, limit, day):
    om, schwab = make_order_manager(make_settings(live_test_date=DAY))
    with patch("butterfly_guy.core.time_utils.session_date", return_value=day):
        assert (
            await om.execute_single_attempt(make_candidate(5900, 5950, 6000, 3), limit, quantity)
            is None
        )
    schwab.place_order.assert_not_called()


@pytest.mark.asyncio
async def test_pilot_blocks_untimed_or_stale_leg_quotes():
    om, _ = make_order_manager(make_settings(live_test_date=DAY))
    assert await om._fetch_live_spread(make_candidate(5900, 5950, 6000, 3)) is None
    assert om._spread_observation is None


@pytest.mark.asyncio
async def test_observation_persistence_failure_blocks_submit_but_preserves_fill():
    om, _ = make_order_manager(make_settings(record_live_execution=True))
    om.intent_queries = AsyncMock()
    om.intent_queries.append_execution_observation.side_effect = RuntimeError("DB down")
    candidate = make_candidate(5900, 5950, 6000, 3)
    with pytest.raises(RuntimeError, match="DB down"):
        await om._record_execution_quote(candidate, 1, "before_submit")
    await om._record_execution_quote(candidate, 1, "fill_detected")


@pytest.mark.asyncio
async def test_observation_contains_leg_quotes_and_local_timing():
    om, _ = make_order_manager(make_settings(record_live_execution=True))
    candidate = make_candidate(5900, 5950, 6000, 3)
    await om._fetch_live_spread(candidate)
    om.intent_queries = AsyncMock()
    await om._record_execution_quote(candidate, 42, "before_submit", limit_price=3)
    args = om.intent_queries.append_execution_observation.call_args.args
    assert args[0] == 42
    assert args[1]["limit_price"] == 3
    assert len(args[1]["quote"]["legs"]) == 3
    assert args[1]["quote"]["requested_at"] <= args[1]["quote"]["received_at"]


@pytest.mark.asyncio
async def test_missing_intent_is_an_audit_failure():
    db = AsyncMock()
    db.pool.execute.return_value = "UPDATE 0"
    with pytest.raises(RuntimeError, match="no durable order intent"):
        await OrderIntentQueries(db).append_execution_observation(1, {"phase": "before_submit"})


@pytest.mark.asyncio
@pytest.mark.parametrize("age,allowed", [(1, True), (15, False), (-5, False)])
async def test_pilot_requires_recent_quote_timestamps(age, allowed):
    om, schwab = make_order_manager(make_settings(live_test_date=DAY))
    candidate = make_candidate(5900, 5950, 6000, 3)
    original = schwab.get_option_chain.side_effect
    now = dt.datetime(2026, 3, 21, 14, 0, tzinfo=dt.timezone.utc)

    def chain(symbol, expiry):
        data = original(symbol, expiry)
        for expirations in (data.get("putExpDateMap", {}), data.get("callExpDateMap", {})):
            for strikes in expirations.values():
                for contracts in strikes.values():
                    for contract in contracts:
                        contract["quoteTimeInLong"] = (now.timestamp() - age) * 1000
        return data

    schwab.get_option_chain.side_effect = chain
    with patch("butterfly_guy.execution.order_manager.now_utc", return_value=now):
        spread = await om._fetch_live_spread(candidate)
    assert (spread is not None) == allowed


@pytest.mark.asyncio
async def test_live_test_exit_does_not_submit_with_missing_fresh_quotes():
    om, schwab = make_order_manager(make_settings(live_test_date=DAY))
    with pytest.raises(Exception, match="requires fresh leg quotes"):
        await om.execute_exit(make_candidate(5900, 5950, 6000, 3), 3)
    schwab.place_order.assert_not_called()
