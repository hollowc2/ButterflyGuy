"""Tests for OrderManager live mark repricing."""

from __future__ import annotations

import asyncio
import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import ExecutionSettings
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.execution.order_manager import LiveSpread, OrderManager


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def make_settings(**overrides) -> ExecutionSettings:
    defaults = dict(
        price_ladder_step=0.05,
        price_ladder_steps=4,
        retry_interval_seconds=0,
        order_timeout_seconds=300,
        paper_trading=False,
    )
    defaults.update(overrides)
    return ExecutionSettings(**defaults)


def make_quote(strike: float, expiration: dt.date) -> OptionQuote:
    return OptionQuote(
        symbol=f"SPXW_{strike}",
        underlying="SPX",
        expiration=expiration,
        strike=strike,
        option_type="PUT",
        bid=1.0,
        ask=1.2,
        mark=1.1,
    )


def make_candidate(
    lower: float,
    center: float,
    upper: float,
    cost: float,
    direction: str = "PUT",
) -> ButterflyCandidate:
    exp = dt.date(2026, 3, 21)
    return ButterflyCandidate(
        direction=direction,
        wing_width=50,
        center_strike=float(center),
        lower_strike=float(lower),
        upper_strike=float(upper),
        cost=cost,
        max_profit=10.0,
        reward_risk=5.0,
        lower_be=float(lower) + 5,
        upper_be=float(upper) - 5,
        distance_from_spot=0.5,
        spot_price=float(center),
        lower_quote=make_quote(float(lower), exp),
        center_quote=make_quote(float(center), exp),
        upper_quote=make_quote(float(upper), exp),
    )


def make_order_manager(settings: ExecutionSettings, underlying: str = "SPX"):
    schwab = MagicMock()
    schwab.get_option_chain = AsyncMock()
    schwab.place_order = AsyncMock(return_value="ORD1")
    schwab.cancel_order = AsyncMock()
    schwab.get_order_status = AsyncMock(return_value={"status": "WORKING"})

    builder = MagicMock()
    builder.build_butterfly_open = MagicMock(return_value={})
    builder.build_butterfly_close = MagicMock(return_value={})

    om = OrderManager(settings, schwab, builder, underlying)
    return om, schwab


def make_chain_data(
    expiration: dt.date,
    lower: float,
    center: float,
    upper: float,
    lower_mark: float,
    center_mark: float,
    upper_mark: float,
    direction: str = "PUT",
) -> dict:
    map_key = "callExpDateMap" if direction == "CALL" else "putExpDateMap"
    exp_key = f"{expiration}:0"
    return {
        map_key: {
            exp_key: {
                str(lower): [{"mark": lower_mark, "bid": lower_mark - 0.1, "ask": lower_mark + 0.1}],
                str(center): [{"mark": center_mark, "bid": center_mark - 0.1, "ask": center_mark + 0.1}],
                str(upper): [{"mark": upper_mark, "bid": upper_mark - 0.1, "ask": upper_mark + 0.1}],
            }
        }
    }


def make_chain_data_with_spread(
    expiration: dt.date,
    lower: float,
    center: float,
    upper: float,
    lower_bid: float,
    lower_mark: float,
    lower_ask: float,
    center_bid: float,
    center_mark: float,
    center_ask: float,
    upper_bid: float,
    upper_mark: float,
    upper_ask: float,
    direction: str = "PUT",
) -> dict:
    map_key = "callExpDateMap" if direction == "CALL" else "putExpDateMap"
    exp_key = f"{expiration}:0"
    return {
        map_key: {
            exp_key: {
                str(lower): [{"bid": lower_bid, "mark": lower_mark, "ask": lower_ask}],
                str(center): [{"bid": center_bid, "mark": center_mark, "ask": center_ask}],
                str(upper): [{"bid": upper_bid, "mark": upper_mark, "ask": upper_ask}],
            }
        }
    }


# ---------------------------------------------------------------------------
# _fetch_live_spread
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_live_spread_returns_correct_bid_mark_ask():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    # lower_bid=1.0, lower_mark=1.1, lower_ask=1.2
    # center_bid=1.4, center_mark=1.5, center_ask=1.6
    # upper_bid=2.3, upper_mark=2.4, upper_ask=2.5
    # spread_bid = 1.0 + 2.3 - 2*1.6 = -0.9
    # spread_mark = 1.1 + 2.4 - 2*1.5 = 0.5
    # spread_ask = 1.2 + 2.5 - 2*1.4 = 0.9
    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_spread(
            exp, 5900, 5950, 6000,
            1.0, 1.1, 1.2,
            1.4, 1.5, 1.6,
            2.3, 2.4, 2.5,
        )
    )

    result = await om._fetch_live_spread(candidate)

    assert result is not None
    assert result.mark == pytest.approx(0.5)
    assert result.bid == pytest.approx(1.0 + 2.3 - 2 * 1.6)
    assert result.ask == pytest.approx(1.2 + 2.5 - 2 * 1.4)


@pytest.mark.asyncio
async def test_fetch_live_spread_returns_none_on_exception():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    schwab.get_option_chain = AsyncMock(side_effect=RuntimeError("network error"))

    result = await om._fetch_live_spread(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_live_spread_returns_none_on_missing_strikes():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    schwab.get_option_chain = AsyncMock(return_value={
        "putExpDateMap": {
            f"{exp}:0": {
                "5900.0": [{"bid": 0.9, "mark": 1.0, "ask": 1.1}],
                "5950.0": [{"bid": 1.4, "mark": 1.5, "ask": 1.6}],
            }
        }
    })

    result = await om._fetch_live_spread(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_live_spread_returns_none_on_nonpositive_mark():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    # mark = 1.0 + 1.0 - 2*2.0 = -2.0
    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_spread(
            exp, 5900, 5950, 6000,
            0.9, 1.0, 1.1,
            1.9, 2.0, 2.1,
            0.9, 1.0, 1.1,
        )
    )

    result = await om._fetch_live_spread(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_live_mark_delegates_to_fetch_live_spread():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=-0.9, mark=0.5, ask=0.9)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)):
        result = await om._fetch_live_mark(candidate)

    assert result == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# _fetch_live_mark (existing tests preserved via make_chain_data)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_live_mark_returns_net_debit():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data(exp, 5900, 5950, 6000, 1.0, 1.5, 2.5)
    )

    result = await om._fetch_live_mark(candidate)

    # lower + upper - 2*center = 1.0 + 2.5 - 3.0 = 0.5
    assert result == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_fetch_live_mark_returns_none_on_exception():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    schwab.get_option_chain = AsyncMock(side_effect=RuntimeError("network error"))

    result = await om._fetch_live_mark(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_live_mark_returns_none_on_missing_strikes():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    # Only 2 strikes present
    schwab.get_option_chain = AsyncMock(return_value={
        "putExpDateMap": {
            f"{exp}:0": {
                "5900.0": [{"mark": 1.0, "bid": 0.9, "ask": 1.1}],
                "5950.0": [{"mark": 1.5, "bid": 1.4, "ask": 1.6}],
            }
        }
    })

    result = await om._fetch_live_mark(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_live_mark_returns_none_on_nonpositive():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    # lower + upper - 2*center = 1.0 + 1.0 - 2*2.0 = -2.0
    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data(exp, 5900, 5950, 6000, 1.0, 2.0, 1.0)
    )

    result = await om._fetch_live_mark(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_live_mark_uses_correct_spx_symbol():
    settings = make_settings()
    om, schwab = make_order_manager(settings, underlying="SPX")
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data(exp, 5900, 5950, 6000, 1.0, 1.5, 2.5)
    )

    await om._fetch_live_mark(candidate)

    schwab.get_option_chain.assert_called_once_with("$SPX", exp)


@pytest.mark.asyncio
async def test_fetch_live_mark_uses_correct_ndx_symbol():
    settings = make_settings()
    om, schwab = make_order_manager(settings, underlying="NDX")
    candidate = make_candidate(20000, 20050, 20100, 3.00)
    exp = dt.date(2026, 3, 21)
    candidate.lower_quote.expiration = exp

    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data(exp, 20000, 20050, 20100, 1.0, 1.5, 2.5)
    )

    await om._fetch_live_mark(candidate)

    schwab.get_option_chain.assert_called_once_with("$NDX", exp)


# ---------------------------------------------------------------------------
# Paper trading — entry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_entry_fills_when_at_ask():
    # spread.mark = 2.30, ask = 2.40; limit steps up 0.05 each step
    # step 0 = 2.30 (< 2.40), step 1 = 2.35 (< 2.40), step 2 = 2.40 (>= 2.40) → fills
    settings = make_settings(paper_trading=True, price_ladder_steps=4, price_ladder_step=0.05)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.20, mark=2.30, ask=2.40)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    assert result["order_id"] == "PAPER"
    assert result["fill_price"] == pytest.approx(2.40)  # fills when limit reaches ask


@pytest.mark.asyncio
async def test_paper_entry_no_fill_when_below_ask():
    # spread.ask = 10.0; limit 2.30→2.35→2.40→2.45 across 4 steps — never fills
    # Escape infinite outer loop via CancelledError after all 4 steps sleep
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.00, mark=2.30, ask=10.0)

    sleep_count = 0

    async def mock_sleep(_):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count >= 4:
            raise asyncio.CancelledError()

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=mock_sleep):
        try:
            result = await om.execute_entry(candidate, quantity=1)
        except asyncio.CancelledError:
            result = None

    assert result is None
    assert sleep_count == 4  # all 4 ladder steps slept without filling


@pytest.mark.asyncio
async def test_paper_entry_sleeps_between_steps():
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        retry_interval_seconds=5,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    # ask=2.40, mark=2.30 → limit at step 2 = 2.30+2*0.05 = 2.40 >= ask → fills at step 2
    spread = LiveSpread(bid=2.00, mark=2.30, ask=2.40)

    sleep_mock = AsyncMock()
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=sleep_mock):
        result = await om.execute_entry(candidate, quantity=1)

    # Steps 0 and 1 sleep, step 2 fills (no sleep after fill)
    assert result is not None
    assert sleep_mock.call_count == 2
    sleep_mock.assert_called_with(5)


@pytest.mark.asyncio
async def test_paper_entry_falls_back_on_fetch_failure():
    # fetch returns None → mid_price stays at candidate.cost; spread is None → no fill check
    # Escape via CancelledError after first sleep
    settings = make_settings(paper_trading=True, price_ladder_steps=4, price_ladder_step=0.05)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    async def mock_sleep(_):
        raise asyncio.CancelledError()

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)), \
         patch("asyncio.sleep", new=mock_sleep):
        try:
            result = await om.execute_entry(candidate, quantity=1)
        except asyncio.CancelledError:
            result = None

    # No fill possible when spread is None
    assert result is None


@pytest.mark.asyncio
async def test_paper_entry_respects_timeout():
    settings = make_settings(paper_trading=True, order_timeout_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    with patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is None


@pytest.mark.asyncio
async def test_paper_entry_does_not_mutate_candidate_cost():
    settings = make_settings(paper_trading=True, price_ladder_steps=4, price_ladder_step=0.05)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    original_cost = candidate.cost
    spread = LiveSpread(bid=2.00, mark=2.30, ask=2.40)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        await om.execute_entry(candidate, quantity=1)

    assert candidate.cost == original_cost


# ---------------------------------------------------------------------------
# Paper trading — exit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_exit_fills_when_at_bid():
    # spread.bid = 3.50; mid_price seed = 3.00 (current_value); step 0 → limit = 3.00 + 3*0.05 = 3.15
    # step 0: 3.15 <= 3.50? Yes → fills
    settings = make_settings(paper_trading=True, price_ladder_steps=4, price_ladder_step=0.05)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.50, mark=3.00, ask=3.60)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_exit(candidate, current_value=3.00, quantity=1)

    assert result is not None
    assert result["order_id"] == "PAPER"
    # limit at step 0 = spread.mark + (4-1)*0.05 = 3.15
    assert result["fill_price"] == pytest.approx(3.15)


@pytest.mark.asyncio
async def test_paper_exit_no_fill_when_above_bid():
    # spread.bid = 2.00; limit 3.45→3.40→3.35→3.30 across 4 steps — never fills
    # Escape infinite outer loop via CancelledError after all 4 steps sleep
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.00, mark=3.30, ask=3.60)

    sleep_count = 0

    async def mock_sleep(_):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count >= 4:
            raise asyncio.CancelledError()

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=mock_sleep):
        try:
            result = await om.execute_exit(candidate, current_value=3.30, quantity=1)
        except asyncio.CancelledError:
            result = None

    assert result is None
    assert sleep_count == 4  # all 4 ladder steps slept without filling


@pytest.mark.asyncio
async def test_paper_exit_sleeps_between_steps():
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        retry_interval_seconds=5,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    # mark=3.00, step down: step0=3.15, step1=3.10, step2=3.05, step3=3.00
    # bid=3.05 → fills at step 2 (3.05 <= 3.05)
    spread = LiveSpread(bid=3.05, mark=3.00, ask=3.60)

    sleep_mock = AsyncMock()
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=sleep_mock):
        result = await om.execute_exit(candidate, current_value=3.00, quantity=1)

    assert result is not None
    # Steps 0 and 1 sleep (not filled), step 2 fills (no sleep)
    assert sleep_mock.call_count == 2
    sleep_mock.assert_called_with(5)


@pytest.mark.asyncio
async def test_paper_exit_respects_timeout():
    settings = make_settings(paper_trading=True, order_timeout_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    with patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_exit(candidate, current_value=3.75, quantity=1)

    assert result is None


# ---------------------------------------------------------------------------
# execute_entry live mark repricing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_entry_uses_live_mark_not_candidate_cost():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_mark = 2.75

    with patch.object(om, "_fetch_live_mark", new=AsyncMock(return_value=live_mark)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=True)):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    limit_price_used = om.builder.build_butterfly_open.call_args[0][1]
    assert limit_price_used == live_mark


@pytest.mark.asyncio
async def test_entry_steps_up_from_live_mark():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_mark = 2.75

    with patch.object(om, "_fetch_live_mark", new=AsyncMock(return_value=live_mark)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(side_effect=[False, True])):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    calls = om.builder.build_butterfly_open.call_args_list
    assert len(calls) == 2
    assert calls[0][0][1] == pytest.approx(live_mark)
    assert calls[1][0][1] == pytest.approx(live_mark + 0.05)


@pytest.mark.asyncio
async def test_entry_falls_back_to_candidate_cost_when_fetch_fails():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    with patch.object(om, "_fetch_live_mark", new=AsyncMock(return_value=None)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=True)):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    limit_price_used = om.builder.build_butterfly_open.call_args[0][1]
    assert limit_price_used == candidate.cost


@pytest.mark.asyncio
async def test_entry_reprice_called_per_step():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    fetch_mock = AsyncMock(return_value=2.75)
    # Fill on the last step so we traverse all 4 steps
    wait_mock = AsyncMock(side_effect=[False, False, False, True])

    with patch.object(om, "_fetch_live_mark", new=fetch_mock), \
         patch.object(om, "_wait_for_fill", new=wait_mock):
        await om.execute_entry(candidate, quantity=1)

    assert fetch_mock.call_count == 4


@pytest.mark.asyncio
async def test_entry_returns_none_on_timeout():
    settings = make_settings(order_timeout_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    result = await om.execute_entry(candidate, quantity=1)

    assert result is None


@pytest.mark.asyncio
async def test_entry_does_not_mutate_candidate_cost():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    original_cost = candidate.cost
    live_mark = 2.75

    with patch.object(om, "_fetch_live_mark", new=AsyncMock(return_value=live_mark)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=True)):
        await om.execute_entry(candidate, quantity=1)

    assert candidate.cost == original_cost


# ---------------------------------------------------------------------------
# execute_exit live mark repricing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exit_uses_live_mark_not_current_value():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_mark = 3.20
    current_value = 2.50

    with patch.object(om, "_fetch_live_mark", new=AsyncMock(return_value=live_mark)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=True)):
        result = await om.execute_exit(candidate, current_value=current_value, quantity=1)

    assert result is not None
    limit_price_used = om.builder.build_butterfly_close.call_args[0][1]
    # Step 0: live_mark + (max_steps-1)*step = 3.20 + 3*0.05 = 3.35
    assert limit_price_used == pytest.approx(live_mark + 3 * 0.05)


@pytest.mark.asyncio
async def test_exit_falls_back_to_current_value_when_fetch_fails():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    current_value = 3.75

    with patch.object(om, "_fetch_live_mark", new=AsyncMock(return_value=None)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=True)):
        result = await om.execute_exit(candidate, current_value=current_value, quantity=1)

    assert result is not None
    limit_price_used = om.builder.build_butterfly_close.call_args[0][1]
    # fetch failed → mid_price = current_value; step 0 = current_value + (4-1)*0.05
    assert limit_price_used == pytest.approx(current_value + 3 * 0.05)


@pytest.mark.asyncio
async def test_exit_steps_down_from_live_mark():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_mark = 3.20

    with patch.object(om, "_fetch_live_mark", new=AsyncMock(return_value=live_mark)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(side_effect=[False, True])):
        result = await om.execute_exit(candidate, current_value=2.50, quantity=1)

    assert result is not None
    calls = om.builder.build_butterfly_close.call_args_list
    assert len(calls) == 2
    # Step 0: live_mark + (4-1)*0.05 = 3.35  (best price first)
    # Step 1: live_mark + (4-2)*0.05 = 3.30  (step down)
    assert calls[0][0][1] == pytest.approx(live_mark + 3 * 0.05)
    assert calls[1][0][1] == pytest.approx(live_mark + 2 * 0.05)


@pytest.mark.asyncio
async def test_exit_returns_none_on_timeout():
    settings = make_settings(order_timeout_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    result = await om.execute_exit(candidate, current_value=3.75, quantity=1)

    assert result is None
