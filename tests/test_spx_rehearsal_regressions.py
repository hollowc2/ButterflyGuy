"""Promoted November 23 probes; recorded quote input and isolated broker fixtures."""

import asyncio
import datetime as dt
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from butterfly_guy.core.config import ProfitManagementSettings
from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.execution.order_manager import OperatorExitTakeoverError
from butterfly_guy.position.position_manager import PositionManager, fly_settlement_value
from tests.test_position_monitoring import _service
from tests.test_spx_live_test import (
    FLAT,
    HELD,
    _persisted_metadata,
    _restarted_trade,
    assert_manual_close_recorded,
    live_service,
    manual_close_order,
    run_live_monitor,
)

DAY = dt.date(2026, 11, 23)
ROWS = json.loads((Path(__file__).parent / "fixtures/spx_rehearsal_20261123_quotes.json")
                  .read_text())["rows"]
COMPLETE = {
    float(row["strike"]): OptionQuote(
        symbol=row["symbol"], underlying="SPX", expiration=DAY,
        strike=float(row["strike"]), option_type="CALL", bid=float(row["bid"]),
        ask=float(row["ask"]), mark=float(row["mark"]),
    ) for row in ROWS
}
CANDIDATE = ButterflyCandidate(
    direction="CALL", wing_width=40, center_strike=7360, lower_strike=7320, upper_strike=7400,
    cost=3.75, max_profit=36.25, reward_risk=36.25 / 3.75, lower_be=7323.75,
    upper_be=7396.25, distance_from_spot=98.63, spot_price=7261.37,
)


@pytest.mark.parametrize("missing_strike", [7320.0, 7360.0, 7400.0])
async def test_each_observed_spx_leg_missing_then_recovers(missing_strike):
    set_readiness(None)
    incomplete = {strike: quote for strike, quote in COMPLETE.items() if strike != missing_strike}
    service = _service([COMPLETE, incomplete, incomplete, incomplete, incomplete, COMPLETE])
    service.config.strategy.underlying = "SPX"
    service.config.execution.paper_trading = True
    service.position_manager = PositionManager("SPX", ProfitManagementSettings())
    service.state_machine.evaluate.side_effect = None
    service.state_machine.evaluate.return_value = None
    calls = 0
    observed_readiness = []

    async def chain(*args, **kwargs):
        nonlocal calls
        calls += 1
        observed_readiness.append(readiness_snapshot())
        if calls == 7:
            raise asyncio.CancelledError
        return {"underlyingPrice": float(ROWS[0]["spot_price"])}

    service.market_data.get_option_chain.side_effect = chain
    trade = TradeRecord(
        trade_id=100001, trade_date=DAY, direction="CALL", entry_price=3.75,
        lower_symbol=COMPLETE[7320.0].symbol, center_symbol=COMPLETE[7360.0].symbol,
        upper_symbol=COMPLETE[7400.0].symbol,
    )
    try:
        with (
            patch("butterfly_guy.services.position_service.is_market_open", return_value=True),
            patch("butterfly_guy.services.position_service.session_date", return_value=DAY),
            patch("butterfly_guy.services.position_service.get_0dte_expiration", return_value=DAY),
            patch("butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()),
            patch("butterfly_guy.services.position_service.notify_telegram", new=AsyncMock()),
            pytest.raises(asyncio.CancelledError),
        ):
            await service.monitor_loop(trade, CANDIDATE)
        events = [call.args[0] for call in service.decision_queries.log_event.await_args_list]
        assert events.count("position_market_data_unavailable") == 1
        assert events.count("position_market_data_recovered") == 1
        assert any(not ready for ready, _ in observed_readiness)
        assert service.state_machine.evaluate.call_count == 2
        service.order_manager.execute_exit.assert_not_awaited()
        assert readiness_snapshot() == (True, None)
    finally:
        set_readiness(None)


@pytest.mark.parametrize("trigger", ["operator_order", "ladder_takeover"])
async def test_operator_ownership_across_two_restarts_and_cancellation(trigger):
    if trigger == "operator_order":
        first = live_service([HELD] * 10, [[manual_close_order("WORKING")]] * 10)
    else:
        first = live_service([HELD] * 10, [[]] * 10, execute_exit=OperatorExitTakeoverError(
            "isolated fixture: operator canceled bot order",
        ))
    await run_live_monitor(first, polls=2)
    trade = _restarted_trade(_persisted_metadata(first))
    assert trade.operator_exit
    second = live_service([HELD] * 10, [[manual_close_order("CANCELED")]] * 10)
    await run_live_monitor(second, polls=6, trade=trade)
    second.order_manager.execute_exit.assert_not_awaited()
    third = live_service([HELD, FLAT], [[], [manual_close_order()]])
    await run_live_monitor(third, trade=trade)
    third.order_manager.execute_exit.assert_not_awaited()
    assert_manual_close_recorded(third)


@pytest.mark.parametrize("spot,intrinsic", [(7200, 0), (7320, 0), (7340, 20), (7360, 40),
                                          (7380, 20), (7400, 0), (7500, 0)])
@pytest.mark.parametrize("quantity", [1, 2, 3])
def test_hypothetical_settlement_at_actual_strikes(spot, intrinsic, quantity):
    # Hypothetical spots, not the official close. Entry already embeds its fee;
    # expiration settlement has no modeled exit commission in this convention.
    assert fly_settlement_value(CANDIDATE, spot) == intrinsic
    assert (intrinsic - 3.75) * 100 * quantity == (100 * intrinsic - 375) * quantity
