"""Held-leg diagnostics and isolation from strategy, readiness and broker writes."""

from __future__ import annotations

import asyncio
import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from schwab_gateway_sdk.client import GatewayUnavailableError
from schwab_gateway_sdk.models import PartialQuoteResponseV1, QuoteV1

from butterfly_guy.core.config import PositionDataSettings
from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.data.providers import (
    ChainObservation,
    ContractTiming,
    GatewayAuthoritativeMarketDataProvider,
    OmittedContract,
)
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.services.position_data_diagnostics import PositionQuoteShadow, held_leg_evidence

NOW = dt.datetime(2026, 10, 7, 17, 33, tzinfo=dt.UTC)
STRIKES = (767.0, 771.0, 775.0)
SYMBOLS = tuple(f"XSP   261007P{int(strike * 1000):08d}" for strike in STRIKES)


def candidate():
    return ButterflyCandidate(
        direction="PUT", wing_width=4, center_strike=771, lower_strike=767, upper_strike=775,
        cost=0.34, max_profit=3.66, reward_risk=10.76, lower_be=767.34,
        upper_be=774.66, distance_from_spot=9, spot_price=780.2,
        lower_symbol=SYMBOLS[0], center_symbol=SYMBOLS[1], upper_symbol=SYMBOLS[2],
    )


def trade():
    return TradeRecord(trade_id=334, trade_date=NOW.date(), direction="PUT", entry_price=0.34,
                       lower_symbol=SYMBOLS[0], center_symbol=SYMBOLS[1], upper_symbol=SYMBOLS[2])


def chain_quotes():
    return {strike: OptionQuote(symbol=symbol, underlying="XSP", expiration=NOW.date(),
                                strike=strike, option_type="PUT", bid=0, ask=0.02, mark=0.01)
            for strike, symbol in zip(STRIKES, SYMBOLS, strict=True)}


def observation(*, missing_age=301.0):
    omitted = OmittedContract(symbol=SYMBOLS[0], option_type="PUT", strike=767,
                              stale=True, age_seconds=missing_age,
                              flags=("stale",) if missing_age is not None
                              else ("stale", "missing_event_timestamp"),
                              event_timestamp=NOW - dt.timedelta(seconds=301)
                              if missing_age is not None else None,
                              bid=0.0, ask=0.01, mark=0.005)
    return ChainObservation(source="gateway", event_timestamp=NOW,
                            gateway_received_at=NOW, age_seconds=0, stale=False,
                            contracts={s: ContractTiming(NOW, 0) for s in SYMBOLS[1:]},
                            omitted=(omitted,))


@pytest.mark.parametrize("missing_age,reason", [
    (301.0, "stale_quote"), (None, "missing_quote_timestamp"),
])
def test_held_leg_records_the_filtered_quote_instead_of_losing_its_evidence(missing_age, reason):
    quotes = chain_quotes()
    del quotes[767]
    legs = held_leg_evidence(trade(), candidate(), quotes, observation(missing_age=missing_age))
    assert legs[0]["reason"] == reason
    assert legs[0]["age_seconds"] == missing_age
    assert legs[0]["bid"] == 0
    assert legs[0]["ask"] == 0.01
    assert legs[0]["symbol"] == SYMBOLS[0]
    assert legs[1]["reason"] == legs[2]["reason"] == "usable"


def test_missing_contract_and_chain_failure_are_distinct():
    quotes = chain_quotes()
    del quotes[767]
    chain = ChainObservation(source="gateway", gateway_received_at=NOW)
    assert held_leg_evidence(trade(), candidate(), quotes, chain)[0]["reason"] == (
        "missing_from_gateway_chain"
    )
    assert held_leg_evidence(trade(), candidate(), {}, None, chain_failed=True)[0]["reason"] == (
        "chain_read_failed"
    )


def response(*, missing=(), stale=False):
    return PartialQuoteResponseV1(quotes=tuple(
        QuoteV1(symbol=symbol, bid=0, ask=0.02, mark=0.01, source="schwab_rest_quote",
                gateway_received_at=NOW, event_timestamp=NOW - dt.timedelta(seconds=301)
                if stale else NOW, stale=stale, age_seconds=301 if stale else 0,
                data_quality_flags=("stale",) if stale else ())
        for symbol in SYMBOLS if symbol not in missing
    ), missing_symbols=missing)


def shadow(client, *, timeout=0.05):
    provider = GatewayAuthoritativeMarketDataProvider(client)
    decisions = SimpleNamespace(log_event=AsyncMock())
    sampler = PositionQuoteShadow(provider, decisions,
                                  PositionDataSettings(shadow_held_quotes=True,
                                                       shadow_timeout_seconds=timeout),
                                  trade_id=334, underlying="XSP")
    return sampler, decisions


@pytest.mark.asyncio
@pytest.mark.parametrize("missing,stale", [((), False), ((SYMBOLS[0],), False), ((), True)])
async def test_shadow_comparison_preserves_missing_and_stale_legs(missing, stale):
    client = SimpleNamespace(get_available_quotes=AsyncMock(return_value=response(
        missing=missing, stale=stale,
    )))
    sampler, decisions = shadow(client)
    baseline = readiness_snapshot()
    sampler.submit(held_leg_evidence(trade(), candidate(), chain_quotes(), None), None)
    await sampler.task
    data = decisions.log_event.await_args.args[1]
    assert data["mode"] == "shadow_only"
    assert data["targeted_all_usable"] is (not missing and not stale)
    assert data["targeted_fly_mark"] == (0.0 if not missing and not stale else None)
    assert data["chain_fly_mark"] == 0.0
    assert data["targeted_legs"][0]["symbol"] == SYMBOLS[0]
    assert data["targeted_legs"][1]["source"] == "schwab_rest_quote"
    if missing:
        assert data["targeted_legs"][0]["reason"] == "missing_from_quote_response"
    assert readiness_snapshot() == baseline
    client.get_available_quotes.assert_awaited_once_with(SYMBOLS)
    await sampler.close()
    set_readiness(None)


@pytest.mark.asyncio
async def test_shadow_has_one_inflight_request_and_cancels_on_position_close():
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def blocked(_symbols):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    client = SimpleNamespace(get_available_quotes=AsyncMock(side_effect=blocked))
    sampler, decisions = shadow(client)
    legs = held_leg_evidence(trade(), candidate(), chain_quotes(), None)
    sampler.submit(legs, None)
    task = sampler.task
    await started.wait()
    sampler.submit(legs, None)
    assert sampler.task is task
    await sampler.close()
    assert cancelled.is_set()
    assert task.done()
    decisions.log_event.assert_not_awaited()
    set_readiness(None)


@pytest.mark.asyncio
async def test_shadow_timeout_records_failure_and_never_changes_readiness():
    async def blocked(_symbols):
        await asyncio.Event().wait()

    client = SimpleNamespace(get_available_quotes=AsyncMock(side_effect=blocked))
    sampler, decisions = shadow(client, timeout=0.01)
    baseline = readiness_snapshot()
    sampler.submit(held_leg_evidence(trade(), candidate(), chain_quotes(), None), None)
    await asyncio.wait_for(sampler.task, timeout=1)
    data = decisions.log_event.await_args.args[1]
    assert data["targeted_status"] == "request_failed"
    assert data["error_type"] == "TimeoutError"
    assert "targeted_fly_mark" not in data
    assert readiness_snapshot() == baseline
    await sampler.close()
    set_readiness(None)


@pytest.mark.asyncio
async def test_shadow_transport_failure_and_slow_db_are_bounded_without_secret_logging(caplog):
    client = SimpleNamespace(get_available_quotes=AsyncMock(side_effect=GatewayUnavailableError(
        "secret-in-connection-details",
    )))
    sampler, decisions = shadow(client, timeout=0.01)

    async def slow_db(*args, **kwargs):
        await asyncio.Event().wait()

    decisions.log_event.side_effect = slow_db
    sampler.submit(held_leg_evidence(trade(), candidate(), chain_quotes(), None), None)
    await asyncio.wait_for(sampler.task, timeout=1)
    data = decisions.log_event.await_args.args[1]
    assert data["error_type"] == "GatewayUnavailableError"
    assert "secret-in-connection-details" not in str(data)
    assert "secret-in-connection-details" not in caplog.text
    await sampler.close()
    set_readiness(None)


@pytest.mark.asyncio
async def test_shadow_requests_do_not_retry_or_accept_a_foreign_symbol():
    foreign = response().model_copy(update={"missing_symbols": ("FOREIGN",)})
    client = SimpleNamespace(get_available_quotes=AsyncMock(return_value=foreign))
    sampler, decisions = shadow(client)
    sampler.submit(held_leg_evidence(trade(), candidate(), chain_quotes(), None), None)
    await sampler.task
    assert decisions.log_event.await_args.args[1]["error_type"] == "GatewayMarketDataError"
    client.get_available_quotes.assert_awaited_once()
    await sampler.close()
    set_readiness(None)


@pytest.mark.asyncio
async def test_completed_shadow_samples_are_rate_limited():
    client = SimpleNamespace(get_available_quotes=AsyncMock(return_value=response()))
    sampler, decisions = shadow(client)
    legs = held_leg_evidence(trade(), candidate(), chain_quotes(), None)
    sampler.submit(legs, None)
    await sampler.task
    sampler.submit(legs, None)
    client.get_available_quotes.assert_awaited_once()
    sampler.next_sample_at = 0
    sampler.submit(legs, None)
    await sampler.task
    assert client.get_available_quotes.await_count == 2
    assert decisions.log_event.await_count == 2
    await sampler.close()
    set_readiness(None)


@pytest.mark.asyncio
@pytest.mark.parametrize("shadow_failure", [False, True])
async def test_position_monitor_never_values_or_exits_using_shadow_prices(shadow_failure):
    from tests.test_position_monitoring import _service

    targeted = response()
    targeted = targeted.model_copy(update={"quotes": tuple(
        quote.model_copy(update={"mark": 1000.0 if index != 1 else 0.01})
        for index, quote in enumerate(targeted.quotes)
    )})
    client = SimpleNamespace(get_available_quotes=AsyncMock(
        return_value=targeted,
        side_effect=GatewayUnavailableError("shadow unavailable") if shadow_failure else None,
    ))
    provider = GatewayAuthoritativeMarketDataProvider(client)
    provider.get_option_chain_observed = AsyncMock(side_effect=[
        ({"underlyingPrice": 780.2}, ChainObservation(source="gateway")),
        asyncio.CancelledError,
    ])
    service = _service([chain_quotes()])
    service.config.position_data = PositionDataSettings(shadow_held_quotes=True)
    service.market_data = provider
    original_sleep = asyncio.sleep

    async def yield_to_shadow(_seconds):
        await original_sleep(0.01)

    with patch("butterfly_guy.services.position_service.is_market_open", return_value=True), \
            patch("butterfly_guy.services.position_service.session_date",
                  return_value=NOW.date()), \
            patch("butterfly_guy.services.position_service.get_0dte_expiration",
                  return_value=NOW.date()), \
            patch("butterfly_guy.services.position_service.asyncio.sleep",
                  side_effect=yield_to_shadow), pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade(), candidate())
    assert service.state_machine.evaluate.call_count == 1
    state = service.state_machine.evaluate.call_args.args[0]
    assert state.current_value == 0
    assert state.peak_value == 0.34
    service.order_manager.execute_exit.assert_not_awaited()
    service.trade_queries.update_peak_value.assert_not_awaited()
    service.schwab.assert_not_awaited()
    assert service._held_quote_shadow is None
    shadow_data = [call.args[1] for call in service.decision_queries.log_event.await_args_list
                   if call.args[0] == "position_held_quote_shadow"]
    assert len(shadow_data) == 1
    if shadow_failure:
        assert shadow_data[0]["targeted_status"] == "request_failed"
    else:
        assert shadow_data[0]["targeted_fly_mark"] == 1999.98
    set_readiness(None)
