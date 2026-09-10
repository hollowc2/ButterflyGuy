"""Regression coverage for incomplete held-position market data."""

from __future__ import annotations

import asyncio
import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import ProfitManagementSettings
from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.position.position_manager import PositionManager
from butterfly_guy.services.position_service import PositionService

EXPIRATION = dt.date(2026, 9, 10)
HELD_STRIKES = (746.0, 751.0, 756.0)


def _candidate() -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="PUT",
        wing_width=5,
        center_strike=751.0,
        lower_strike=746.0,
        upper_strike=756.0,
        cost=0.50,
        max_profit=4.50,
        reward_risk=9.0,
        lower_be=746.50,
        upper_be=755.50,
        distance_from_spot=5.0,
        spot_price=756.0,
    )


def _quotes() -> dict[float, OptionQuote]:
    marks = {746.0: 1.10, 751.0: 0.55, 756.0: 0.40}
    return {
        strike: OptionQuote(
            symbol=f"XSPW  260910P00{int(strike * 1000):08d}",
            underlying="XSP",
            expiration=EXPIRATION,
            strike=strike,
            option_type="PUT",
            bid=mark - 0.05,
            ask=mark + 0.05,
            mark=mark,
        )
        for strike, mark in marks.items()
    }


def _service(observations: list[dict[float, OptionQuote]]) -> PositionService:
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "XSP"
    service.market_data = AsyncMock()
    service._extract_quotes = MagicMock(side_effect=observations)
    service.position_manager = PositionManager("XSP", ProfitManagementSettings())
    service.state_machine = MagicMock()
    service.state_machine.evaluate.side_effect = lambda state: (
        SimpleNamespace(reason="stale_peak_exit", urgency="NORMAL")
        if state.current_value == 0.50
        else None
    )
    service.state_machine.state.name = "INITIAL"
    service.decision_queries = MagicMock(log_event=AsyncMock())
    service.notifier = None
    service.monitoring_leg_queries = None
    service.tent_queries = MagicMock(insert=AsyncMock())
    service.trade_queries = MagicMock(
        update_peak_value=AsyncMock(),
        merge_metadata=AsyncMock(),
    )
    service.order_manager = MagicMock(execute_exit=AsyncMock())
    service.order_manager.execute_exit.return_value = None
    service.schwab = AsyncMock()
    service._exit_mark_parity_report = AsyncMock(return_value={})
    service._last_persisted_peak = 0.50
    service._last_profit_state = None
    return service


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_strike", HELD_STRIKES)
async def test_intermittent_missing_held_leg_degrades_then_recovers_without_broker_write(
    missing_strike: float,
) -> None:
    """Replay valid -> incomplete threshold -> valid for every held leg."""
    set_readiness(None)
    complete = _quotes()
    incomplete = {strike: quote for strike, quote in complete.items() if strike != missing_strike}
    next_strike = HELD_STRIKES[(HELD_STRIKES.index(missing_strike) + 1) % len(HELD_STRIKES)]
    still_incomplete = {
        strike: quote for strike, quote in complete.items() if strike != next_strike
    }
    service = _service(
        [complete, incomplete, incomplete, incomplete, still_incomplete, complete]
    )
    chain_calls = 0

    async def get_option_chain(*_args: object) -> dict:
        nonlocal chain_calls
        chain_calls += 1
        if chain_calls in {5, 6}:
            assert readiness_snapshot() == (False, "market_data_unavailable")
        if chain_calls == 7:
            assert readiness_snapshot() == (True, None)
            raise asyncio.CancelledError
        return {"underlyingPrice": 756.0}

    service.market_data.get_option_chain.side_effect = get_option_chain
    trade = TradeRecord(trade_id=17, trade_date=EXPIRATION, entry_price=0.50)

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=True
    ), patch(
        "butterfly_guy.services.position_service.session_date", return_value=EXPIRATION
    ), patch(
        "butterfly_guy.services.position_service.get_0dte_expiration",
        return_value=EXPIRATION,
    ), patch(
        "butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()
    ), patch("butterfly_guy.services.position_service.log") as monitor_log, pytest.raises(
        asyncio.CancelledError
    ):
        await service.monitor_loop(trade, _candidate())

    event_names = [call.args[0] for call in service.decision_queries.log_event.await_args_list]
    assert event_names.count("position_market_data_unavailable") == 1
    assert event_names.count("position_market_data_recovered") == 1
    assert service.state_machine.evaluate.call_count == 2
    service.order_manager.execute_exit.assert_not_awaited()
    assert service.schwab.mock_calls == []
    assert monitor_log.warning.call_count == 1
    assert monitor_log.error.call_count == 1
    set_readiness(None)
