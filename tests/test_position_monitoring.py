"""Regression coverage for incomplete held-position market data."""

from __future__ import annotations

import asyncio
import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import ProfitManagementSettings
from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.data.providers import GatewayAuthoritativeMarketDataProvider
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.position.position_manager import PositionManager
from butterfly_guy.services.position_service import PositionService

EXPIRATION = dt.date(2026, 9, 10)
TRADE_282_EXPIRATION = dt.date(2026, 9, 11)
HELD_STRIKES = (746.0, 751.0, 756.0)


def _gateway_contract(
    option_type: str,
    strike: float,
    mark: float,
    *,
    age_seconds: float = 0.2,
    stale: bool = False,
) -> SimpleNamespace:
    option_code = "C" if option_type == "CALL" else "P"
    return SimpleNamespace(
        option_type=option_type,
        symbol=f"XSP   260911{option_code}{int(strike * 1000):08d}",
        expiration=TRADE_282_EXPIRATION,
        strike=strike,
        bid=max(0.0, mark - 0.01),
        ask=mark + 0.01,
        mark=mark,
        last=mark,
        total_volume=0,
        open_interest=0,
        volatility=0.2,
        delta=0.0,
        gamma=0.0,
        theta=0.0,
        vega=0.0,
        bid_size=0,
        ask_size=0,
        rho=0.0,
        intrinsic_value=0.0,
        time_value=mark,
        in_the_money=False,
        days_to_expiration=0,
        multiplier=100.0,
        theoretical_option_value=mark,
        stale=stale,
        age_seconds=age_seconds,
        data_quality_flags=("stale",) if stale else (),
    )


def _trade_282_candidate() -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="CALL",
        wing_width=4,
        center_strike=774.0,
        lower_strike=770.0,
        upper_strike=778.0,
        cost=0.24,
        max_profit=3.76,
        reward_risk=15.67,
        lower_be=770.24,
        upper_be=777.76,
        distance_from_spot=0.0,
        spot_price=774.0,
    )


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
async def test_trade_282_uses_gateway_held_leg_when_contract_is_not_stale() -> None:
    """A quiet 778 quote is usable when the gateway explicitly says it is fresh."""
    contracts = (
        _gateway_contract("CALL", 770.0, 0.08),
        _gateway_contract("CALL", 774.0, 0.03),
        # Production evidence showed this exact shape: the chain was fresh and
        # the contract was not stale, but its last event was more than 30s old.
        _gateway_contract("CALL", 778.0, 0.01, age_seconds=66.5),
        _gateway_contract("CALL", 760.0, 0.01, age_seconds=120.0, stale=True),
        _gateway_contract("PUT", 774.0, 0.50),
    )
    chain = SimpleNamespace(
        symbol="$XSP",
        expiration=TRADE_282_EXPIRATION,
        underlying_price=774.0,
        call_contract_count=4,
        put_contract_count=1,
        strike_count=4,
        contracts=contracts,
        stale=False,
        age_seconds=3.0,
        data_quality_flags=("stale_contracts_present",),
    )
    gateway = AsyncMock()
    gateway.get_option_chain.side_effect = (
        SimpleNamespace(option_chain=chain),
        asyncio.CancelledError,
    )
    provider = GatewayAuthoritativeMarketDataProvider(
        gateway,
        max_current_age_seconds=30.0,
    )

    service = _service([])
    service.market_data = provider
    service._extract_quotes = PositionService._extract_quotes.__get__(
        service,
        PositionService,
    )
    candidate = _trade_282_candidate()
    trade = TradeRecord(
        trade_id=282,
        trade_date=TRADE_282_EXPIRATION,
        entry_price=0.24,
    )

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=True
    ), patch(
        "butterfly_guy.services.position_service.session_date",
        return_value=TRADE_282_EXPIRATION,
    ), patch(
        "butterfly_guy.services.position_service.get_0dte_expiration",
        return_value=TRADE_282_EXPIRATION,
    ), patch(
        "butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()
    ), pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade, candidate)

    service.state_machine.evaluate.assert_called_once()
    assert service.state_machine.evaluate.call_args.args[0].current_value == 0.03
    service.order_manager.execute_exit.assert_not_awaited()


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
    ), patch(
        "butterfly_guy.services.position_service.notify_telegram", new=AsyncMock(return_value=True)
    ) as telegram_notify, patch(
        "butterfly_guy.services.position_service.log"
    ) as monitor_log, pytest.raises(
        asyncio.CancelledError
    ):
        await service.monitor_loop(trade, _candidate())

    event_names = [call.args[0] for call in service.decision_queries.log_event.await_args_list]
    assert event_names.count("position_market_data_unavailable") == 1
    assert event_names.count("position_market_data_recovered") == 1
    assert service.state_machine.evaluate.call_count == 2
    service.order_manager.execute_exit.assert_not_awaited()
    assert service.schwab.mock_calls == []
    assert telegram_notify.call_count == 2
    assert monitor_log.warning.call_count == 1
    assert monitor_log.error.call_count == 1
    set_readiness(None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fallback,notification_fails", [(False, False), (True, False), (True, True)],
)
async def test_prolonged_outage_reminders_are_rate_limited_and_reset_on_recovery(
    fallback: bool, notification_fails: bool,
) -> None:
    set_readiness(None)
    complete = _quotes()
    incomplete = {k: v for k, v in complete.items() if k != HELD_STRIKES[-1]}
    service = _service([incomplete] * 10 + [complete] + [incomplete] * 3 + [complete])
    service.state_machine.evaluate.side_effect = None
    service.state_machine.evaluate.return_value = None
    service.notifier = MagicMock(notify_text=AsyncMock())
    times = iter([0, 2, 4, 59, 60, 61, 299, 300, 301, 600, 601, 700, 702, 760, 761])
    clock = [0.0]
    helper = SimpleNamespace(recover=AsyncMock(return_value=(None, {})))
    calls = 0

    async def get_chain(*_args):
        nonlocal calls
        calls += 1
        try:
            clock[0] = next(times)
        except StopIteration:
            raise asyncio.CancelledError from None
        if fallback:
            service._held_quote_recovery = helper
            helper.recover.return_value = (
                None, {"status": "unusable_quotes"} if calls in {1, 12} else {},
            )
        return {"underlyingPrice": 756.0}

    service.market_data.get_option_chain.side_effect = get_chain
    telegram = AsyncMock(return_value=True)
    if notification_fails:
        # Initial alert succeeds; prolonged alerts must not stop monitoring.
        service.notifier.notify_text.side_effect = [None] + [TimeoutError()] * 3 + [None, None]
        telegram.side_effect = [True] + [TimeoutError()] * 3 + [True, True, True, True]
    with (
        patch("butterfly_guy.services.position_service.is_market_open", return_value=True),
        patch("butterfly_guy.services.position_service.session_date", return_value=EXPIRATION),
        patch("butterfly_guy.services.position_service.get_0dte_expiration",
              return_value=EXPIRATION),
        patch("butterfly_guy.services.position_service.monotonic", side_effect=lambda: clock[0]),
        patch("butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()),
        patch("butterfly_guy.services.position_service.notify_telegram", new=telegram),
        pytest.raises(asyncio.CancelledError),
    ):
        await service.monitor_loop(
            TradeRecord(trade_id=17, trade_date=EXPIRATION, entry_price=0.50), _candidate(),
        )
    events = service.decision_queries.log_event.await_args_list
    prolonged = [c.args[1] for c in events
                 if c.args[0] == "position_market_data_outage_prolonged"]
    assert [e["outage_seconds"] for e in prolonged] == [60, 300, 600, 60]
    assert {e["targeted_recovery_status"] for e in prolonged} == {
        "unusable_quotes" if fallback else "disabled",
    }
    assert all(e["held_legs"][-1]["strike"] == HELD_STRIKES[-1] for e in prolonged)
    messages = [c.args[0] for c in telegram.await_args_list]
    assert len(messages) == 8  # Two initial alerts, four reminders, two recoveries.
    assert "suspended for 60s" in messages[1]
    assert "after 601s; valuation-dependent exits resumed" in messages[4]
    assert "after 61s; valuation-dependent exits resumed" in messages[-1]
    assert service.state_machine.evaluate.call_count == 2
    service.order_manager.execute_exit.assert_not_awaited()
    assert service.schwab.mock_calls == []
    assert readiness_snapshot() == (True, None)
