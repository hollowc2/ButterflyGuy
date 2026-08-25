from __future__ import annotations

import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.data.providers import (
    DirectSchwabMarketDataProvider,
    GatewayAuthoritativeMarketDataProvider,
    GatewayMarketDataError,
)


@pytest.fixture(autouse=True)
def _reset_readiness_after_provider_test():
    set_readiness(None)
    yield
    set_readiness(None)


@pytest.mark.asyncio
async def test_direct_provider_delegates_without_transforming_results() -> None:
    expiration = dt.date(2026, 8, 3)
    day = dt.date(2026, 7, 31)
    client = AsyncMock()
    client.get_spot_price.return_value = 6301.25
    client.get_option_chain.return_value = {"callExpDateMap": {}}
    client.get_intraday_bars.return_value = [{"datetime": 1}]
    client.get_intraday_bars_for_day.return_value = [{"datetime": 2}]
    client.get_daily_bars.return_value = [{"datetime": 3}]
    client.get_equity_quotes.return_value = {"AAPL": {"quote": {}}}
    client.get_market_movers.return_value = [{"symbol": "AAPL"}]
    provider = DirectSchwabMarketDataProvider(client)

    assert await provider.get_spot_price("$SPX") == 6301.25
    assert await provider.get_option_chain("$SPX", expiration) == {
        "callExpDateMap": {}
    }
    assert await provider.get_intraday_bars("$SPX", 2) == [{"datetime": 1}]
    assert await provider.get_intraday_bars_for_day(
        "AAPL", day, include_extended_hours=False
    ) == [{"datetime": 2}]
    assert await provider.get_daily_bars("$VIX", 20) == [{"datetime": 3}]
    assert await provider.get_equity_quotes(["AAPL"], batch_size=25) == {
        "AAPL": {"quote": {}}
    }
    assert await provider.get_market_movers(
        "$SPX", sort_order="PERCENT_CHANGE_DOWN", frequency=5
    ) == [{"symbol": "AAPL"}]

    client.get_spot_price.assert_awaited_once_with("$SPX")
    client.get_option_chain.assert_awaited_once_with("$SPX", expiration)
    client.get_intraday_bars.assert_awaited_once_with("$SPX", 2)
    client.get_intraday_bars_for_day.assert_awaited_once_with(
        "AAPL", day, include_extended_hours=False
    )
    client.get_daily_bars.assert_awaited_once_with("$VIX", 20)
    client.get_equity_quotes.assert_awaited_once_with(["AAPL"], batch_size=25)
    client.get_market_movers.assert_awaited_once_with(
        "$SPX", sort_order="PERCENT_CHANGE_DOWN", frequency=5
    )


def _observation(**values):
    fields = {
        "stale": False,
        "age_seconds": 0.2,
        "data_quality_flags": (),
        **values,
    }
    return SimpleNamespace(**fields)


def _contract(option_type: str, symbol: str, strike: float):
    return SimpleNamespace(
        option_type=option_type,
        symbol=symbol,
        expiration=dt.date(2026, 8, 24),
        strike=strike,
        bid=1.0,
        ask=1.2,
        mark=1.1,
        last=1.05,
        total_volume=12,
        open_interest=34,
        volatility=0.2,
        delta=0.3,
        gamma=0.04,
        theta=-0.1,
        vega=0.02,
        bid_size=5,
        ask_size=6,
        rho=0.01,
        intrinsic_value=0.0,
        time_value=1.1,
        in_the_money=False,
        days_to_expiration=0,
        multiplier=100.0,
        theoretical_option_value=1.08,
        stale=False,
        age_seconds=0.2,
        data_quality_flags=(),
    )


@pytest.mark.asyncio
async def test_gateway_provider_adapts_typed_spot_and_full_chain() -> None:
    expiration = dt.date(2026, 8, 24)
    gateway = AsyncMock()
    gateway.get_spot.return_value = SimpleNamespace(
        spot=_observation(symbol="$XSP", price=632.5)
    )
    gateway.get_option_chain.return_value = SimpleNamespace(
        option_chain=_observation(
            symbol="XSP",
            expiration=expiration,
            underlying_price=632.5,
            call_contract_count=1,
            put_contract_count=1,
            strike_count=1,
            contracts=(
                _contract("CALL", "XSP CALL", 632.0),
                _contract("PUT", "XSP PUT", 632.0),
            ),
        )
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    assert await provider.get_spot_price("$XSP") == 632.5
    chain = await provider.get_option_chain("XSP", expiration)

    assert chain["underlyingPrice"] == 632.5
    call = chain["callExpDateMap"]["2026-08-24:0"]["632"][0]
    put = chain["putExpDateMap"]["2026-08-24:0"]["632"][0]
    assert (call["symbol"], put["symbol"]) == ("XSP CALL", "XSP PUT")
    assert call["totalVolume"] == 12
    gateway.get_option_chain.assert_awaited_once_with("XSP", expiration)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"stale": True}, "stale"),
        ({"age_seconds": 31.0}, "too old"),
        ({"age_seconds": None}, "freshness is unknown"),
        ({"data_quality_flags": ("crossed_market",)}, "quality checks"),
    ],
)
async def test_gateway_provider_fails_closed_on_unusable_spot(
    overrides, message
) -> None:
    fields = {
        "symbol": "$SPX",
        "price": 6300.0,
        "stale": False,
        "age_seconds": 0.1,
        "data_quality_flags": (),
        **overrides,
    }
    gateway = AsyncMock()
    gateway.get_spot.return_value = SimpleNamespace(spot=SimpleNamespace(**fields))
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with pytest.raises(GatewayMarketDataError, match=message):
        await provider.get_spot_price("$SPX")


@pytest.mark.asyncio
async def test_gateway_provider_has_no_direct_fallback_on_gateway_error() -> None:
    gateway = AsyncMock()
    gateway.get_option_chain.side_effect = RuntimeError("gateway unavailable")
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with pytest.raises(RuntimeError, match="gateway unavailable"):
        await provider.get_option_chain("SPX", dt.date(2026, 8, 24))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("mark", None, "missing bid, ask, or mark"),
        ("bid", 2.0, "invalid market"),
        ("total_volume", -1, "nonnegative integer"),
        ("open_interest", 1.5, "nonnegative integer"),
    ],
)
async def test_gateway_provider_rejects_invalid_option_contracts(
    field, value, message
) -> None:
    expiration = dt.date(2026, 8, 24)
    call = _contract("CALL", "XSP CALL", 632.0)
    setattr(call, field, value)
    gateway = AsyncMock()
    gateway.get_option_chain.return_value = SimpleNamespace(
        option_chain=_observation(
            symbol="XSP",
            expiration=expiration,
            underlying_price=632.5,
            call_contract_count=1,
            put_contract_count=1,
            strike_count=1,
            contracts=(call, _contract("PUT", "XSP PUT", 632.0)),
        )
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with pytest.raises(GatewayMarketDataError, match=message):
        await provider.get_option_chain("XSP", expiration)


@pytest.mark.asyncio
async def test_gateway_provider_rejects_negative_time_value_from_gateway_contract() -> None:
    """Pin the 2026-08-25 PAPER cutover failure at the consumer boundary."""
    expiration = dt.date(2026, 8, 24)
    call = _contract("CALL", "XSP CALL", 632.0)
    call.time_value = -14.6
    gateway = AsyncMock()
    gateway.get_option_chain.return_value = SimpleNamespace(
        option_chain=_observation(
            symbol="XSP",
            expiration=expiration,
            underlying_price=632.5,
            call_contract_count=1,
            put_contract_count=1,
            strike_count=1,
            contracts=(call, _contract("PUT", "XSP PUT", 632.0)),
        )
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with pytest.raises(
        GatewayMarketDataError,
        match="gateway option contract time_value must be nonnegative",
    ):
        await provider.get_option_chain("XSP", expiration)


@pytest.mark.asyncio
async def test_gateway_provider_defaults_normalized_null_time_value_to_zero() -> None:
    expiration = dt.date(2026, 8, 24)
    call = _contract("CALL", "SPXW  260824C06320000", 6320.0)
    call.time_value = None
    gateway = AsyncMock()
    gateway.get_option_chain.return_value = SimpleNamespace(
        option_chain=_observation(
            symbol="SPX",
            expiration=expiration,
            underlying_price=6320.5,
            call_contract_count=1,
            put_contract_count=1,
            strike_count=1,
            contracts=(call, _contract("PUT", "SPXW  260824P06320000", 6320.0)),
        )
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    chain = await provider.get_option_chain("SPX", expiration)

    normalized = chain["callExpDateMap"]["2026-08-24:0"]["6320"][0]
    assert normalized["timeValue"] == 0.0
    assert (normalized["bid"], normalized["ask"], normalized["mark"]) == (1.0, 1.2, 1.1)


@pytest.mark.asyncio
async def test_gateway_provider_omits_stale_contracts_after_integrity_validation() -> None:
    expiration = dt.date(2026, 8, 24)
    stale_call = _contract("CALL", "XSP STALE CALL", 632.0)
    stale_call.stale = True
    stale_call.data_quality_flags = ("stale",)
    stale_call.age_seconds = 60.0
    unknown_call = _contract("CALL", "XSP UNKNOWN CALL", 634.0)
    unknown_call.age_seconds = None
    unknown_call.data_quality_flags = ("missing_event_timestamp",)
    contracts = (
        stale_call,
        unknown_call,
        _contract("CALL", "XSP FRESH CALL", 633.0),
        _contract("PUT", "XSP PUT 632", 632.0),
        _contract("PUT", "XSP PUT 633", 633.0),
    )
    gateway = AsyncMock()
    gateway.get_option_chain.return_value = SimpleNamespace(
        option_chain=_observation(
            symbol="XSP",
            expiration=expiration,
            underlying_price=632.5,
            call_contract_count=3,
            put_contract_count=2,
            strike_count=3,
            contracts=contracts,
            data_quality_flags=(
                "stale_contracts_present",
                "missing_contract_event_timestamp",
            ),
        )
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    chain = await provider.get_option_chain("XSP", expiration)

    call_symbols = [
        option["symbol"]
        for strike_options in chain["callExpDateMap"]["2026-08-24:0"].values()
        for option in strike_options
    ]
    assert call_symbols == ["XSP FRESH CALL"]


@pytest.mark.asyncio
async def test_gateway_provider_rejects_chain_without_usable_call_and_put() -> None:
    expiration = dt.date(2026, 8, 24)
    stale_call = _contract("CALL", "XSP STALE CALL", 632.0)
    stale_call.age_seconds = None
    gateway = AsyncMock()
    gateway.get_option_chain.return_value = SimpleNamespace(
        option_chain=_observation(
            symbol="XSP",
            expiration=expiration,
            underlying_price=632.5,
            call_contract_count=1,
            put_contract_count=1,
            strike_count=1,
            contracts=(stale_call, _contract("PUT", "XSP PUT", 632.0)),
        )
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with pytest.raises(GatewayMarketDataError, match="calls and puts"):
        await provider.get_option_chain("XSP", expiration)


@pytest.mark.asyncio
async def test_gateway_provider_rejects_aggregate_stale_chain_with_warning_flags() -> None:
    expiration = dt.date(2026, 8, 24)
    gateway = AsyncMock()
    gateway.get_option_chain.return_value = SimpleNamespace(
        option_chain=_observation(
            symbol="XSP",
            expiration=expiration,
            underlying_price=632.5,
            call_contract_count=1,
            put_contract_count=1,
            strike_count=1,
            contracts=(
                _contract("CALL", "XSP CALL", 632.0),
                _contract("PUT", "XSP PUT", 632.0),
            ),
            stale=True,
            data_quality_flags=("stale_contracts_present",),
        )
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with pytest.raises(GatewayMarketDataError, match="data is stale"):
        await provider.get_option_chain("XSP", expiration)


def _bar(timestamp: dt.datetime, close: float):
    return SimpleNamespace(
        timestamp=timestamp,
        open=close - 1,
        high=close + 1,
        low=close - 2,
        close=close,
        volume=100,
    )


@pytest.mark.asyncio
async def test_gateway_provider_adapts_history_and_combines_sessions() -> None:
    day = dt.date(2026, 8, 24)
    regular = _observation(
        symbol="$SPX",
        date=day,
        session="regular",
        candles=(_bar(dt.datetime(2026, 8, 24, 13, 30, tzinfo=dt.timezone.utc), 6300),),
    )
    extended = _observation(
        symbol="SPX",
        date=day,
        session="extended",
        candles=(_bar(dt.datetime(2026, 8, 24, 12, 0, tzinfo=dt.timezone.utc), 6290),),
    )
    daily = _observation(
        symbol="SPX",
        bars=(_bar(dt.datetime(2026, 8, 21, 20, 0, tzinfo=dt.timezone.utc), 6280),),
    )
    gateway = AsyncMock()
    gateway.get_session_history.side_effect = (
        SimpleNamespace(session_history=regular),
        SimpleNamespace(session_history=extended),
    )
    gateway.get_history.return_value = SimpleNamespace(history=daily)
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    intraday = await provider.get_intraday_bars_for_day("$SPX", day)
    daily_bars = await provider.get_daily_bars("SPX", days_back=10)

    assert [bar["close"] for bar in intraday] == [6290.0, 6300.0]
    assert daily_bars[0]["close"] == 6280.0
    assert gateway.get_session_history.await_args_list[0].kwargs == {
        "session": "regular"
    }
    assert gateway.get_session_history.await_args_list[1].kwargs == {
        "session": "extended"
    }
    gateway.get_history.assert_awaited_once_with(
        "SPX", frequency="daily", days_back=10
    )


@pytest.mark.asyncio
async def test_minute_history_uses_interval_bound_during_market() -> None:
    now = dt.datetime(2026, 8, 24, 14, 0, tzinfo=dt.timezone(dt.timedelta(hours=-4)))
    history = _observation(
        symbol="SPX",
        bars=(_bar(now - dt.timedelta(minutes=1), 6300),),
    )
    gateway = AsyncMock()
    gateway.get_history.return_value = SimpleNamespace(history=history)
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with patch("butterfly_guy.data.providers._now_eastern", return_value=now):
        bars = await provider.get_intraday_bars("SPX")

    assert bars[0]["close"] == 6300.0

    history.age_seconds = 181.0
    with patch("butterfly_guy.data.providers._now_eastern", return_value=now), pytest.raises(
        GatewayMarketDataError, match="too old"
    ):
        await provider.get_intraday_bars("SPX")


@pytest.mark.asyncio
async def test_minute_history_accepts_complete_same_day_close_after_hours() -> None:
    now = dt.datetime(2026, 8, 24, 18, 0, tzinfo=dt.timezone(dt.timedelta(hours=-4)))
    close = dt.datetime(2026, 8, 24, 16, 0, tzinfo=now.tzinfo)
    history = _observation(
        symbol="SPX",
        bars=(_bar(close, 6300),),
    )
    history.stale = True
    history.age_seconds = 2 * 60 * 60
    history.data_quality_flags = ("stale",)
    gateway = AsyncMock()
    gateway.get_history.return_value = SimpleNamespace(history=history)
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with patch("butterfly_guy.data.providers._now_eastern", return_value=now):
        bars = await provider.get_intraday_bars("SPX")

    assert bars[-1]["close"] == 6300.0


@pytest.mark.asyncio
async def test_gateway_readiness_requires_all_live_surfaces_since_last_failure() -> None:
    expiration = dt.date(2026, 8, 24)
    now = dt.datetime(2026, 8, 24, 14, 0, tzinfo=dt.timezone(dt.timedelta(hours=-4)))
    gateway = AsyncMock()
    gateway.get_spot.return_value = SimpleNamespace(
        spot=_observation(symbol="XSP", price=632.5)
    )
    gateway.get_option_chain.return_value = SimpleNamespace(
        option_chain=_observation(
            symbol="XSP",
            expiration=expiration,
            underlying_price=632.5,
            call_contract_count=1,
            put_contract_count=1,
            strike_count=1,
            contracts=(
                _contract("CALL", "XSP CALL", 632.0),
                _contract("PUT", "XSP PUT", 632.0),
            ),
        )
    )
    gateway.get_history.return_value = SimpleNamespace(
        history=_observation(
            symbol="XSP",
            bars=(_bar(now - dt.timedelta(minutes=1), 632.5),),
        )
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    assert readiness_snapshot() == (False, "gateway_market_data_warming")
    await provider.get_spot_price("XSP")
    await provider.get_option_chain("XSP", expiration)
    assert readiness_snapshot() == (False, "gateway_market_data_warming")
    with patch("butterfly_guy.data.providers._now_eastern", return_value=now):
        await provider.get_intraday_bars("XSP")
    assert readiness_snapshot() == (True, None)

    gateway.get_spot.side_effect = RuntimeError("gateway unavailable")
    with pytest.raises(RuntimeError, match="gateway unavailable"):
        await provider.get_spot_price("XSP")
    assert readiness_snapshot() == (False, "gateway_market_data_unavailable")


@pytest.mark.asyncio
async def test_empty_extended_session_is_allowed_but_other_flags_remain_fatal() -> None:
    day = dt.date(2026, 8, 24)
    now = dt.datetime(2026, 8, 25, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=-4)))
    regular = _observation(
        symbol="SPX",
        date=day,
        session="regular",
        candles=(_bar(dt.datetime(2026, 8, 24, 20, 0, tzinfo=dt.timezone.utc), 6300),),
    )
    extended = _observation(
        symbol="SPX",
        date=day,
        session="extended",
        candles=(),
    )
    extended.stale = True
    extended.age_seconds = None
    extended.data_quality_flags = ("no_bars_returned", "stale")
    gateway = AsyncMock()
    gateway.get_session_history.side_effect = (
        SimpleNamespace(session_history=regular),
        SimpleNamespace(session_history=extended),
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with patch("butterfly_guy.data.providers._now_eastern", return_value=now):
        bars = await provider.get_intraday_bars_for_day("SPX", day)

    assert [bar["close"] for bar in bars] == [6300.0]

    extended.data_quality_flags = (
        "no_bars_returned",
        "malformed_bars_dropped",
        "stale",
    )
    gateway.get_session_history.side_effect = (
        SimpleNamespace(session_history=regular),
        SimpleNamespace(session_history=extended),
    )
    with patch("butterfly_guy.data.providers._now_eastern", return_value=now), pytest.raises(
        GatewayMarketDataError, match="invalid empty-session flags"
    ):
        await provider.get_intraday_bars_for_day("SPX", day)


@pytest.mark.asyncio
async def test_same_day_stale_empty_extended_session_is_allowed_only_for_extended() -> None:
    day = dt.date(2026, 8, 24)
    now = dt.datetime(2026, 8, 24, 14, 0, tzinfo=dt.timezone(dt.timedelta(hours=-4)))
    regular = _observation(
        symbol="SPX",
        date=day,
        session="regular",
        candles=(_bar(now - dt.timedelta(minutes=1), 6300),),
    )
    empty_extended = _observation(
        symbol="SPX",
        date=day,
        session="extended",
        candles=(),
        stale=True,
        age_seconds=None,
        data_quality_flags=("no_bars_returned", "stale"),
    )
    gateway = AsyncMock()
    gateway.get_session_history.side_effect = (
        SimpleNamespace(session_history=regular),
        SimpleNamespace(session_history=empty_extended),
    )
    provider = GatewayAuthoritativeMarketDataProvider(gateway)

    with patch("butterfly_guy.data.providers._now_eastern", return_value=now):
        bars = await provider.get_intraday_bars_for_day("SPX", day)

    assert [bar["close"] for bar in bars] == [6300.0]

    empty_regular = _observation(
        symbol="SPX",
        date=day,
        session="regular",
        candles=(),
        stale=True,
        age_seconds=None,
        data_quality_flags=("no_bars_returned", "stale"),
    )
    gateway.get_session_history.side_effect = (
        SimpleNamespace(session_history=empty_regular),
        SimpleNamespace(session_history=empty_extended),
    )
    with patch("butterfly_guy.data.providers._now_eastern", return_value=now), pytest.raises(
        GatewayMarketDataError, match="data is stale"
    ):
        await provider.get_intraday_bars_for_day("SPX", day)
