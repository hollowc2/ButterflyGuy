"""Fresh recovery must never turn the October 8 stale-wing outage into a price."""

import asyncio
import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from butterfly_guy.core.config import load_config
from butterfly_guy.data.providers import GatewayAuthoritativeMarketDataProvider
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.services.position_quote_recovery import HeldQuoteRecovery
from tests.test_position_data_diagnostics import (
    NOW,
    SYMBOLS,
    candidate,
    chain_quotes,
    observation,
    response,
    trade,
)
from tests.test_position_monitoring import _service
from tests.test_state_machine import make_pos


def recovery(result):
    client = SimpleNamespace(get_available_quotes=AsyncMock(return_value=result))
    return HeldQuoteRecovery(GatewayAuthoritativeMarketDataProvider(client)), client


@pytest.mark.asyncio
async def test_complete_fresh_response_recovers_all_legs_and_rate_limits():
    helper, client = recovery(response())
    with patch("butterfly_guy.services.position_quote_recovery.now_eastern", return_value=NOW):
        quotes, evidence = await helper.recover(trade(), candidate())
        skipped, skipped_evidence = await helper.recover(trade(), candidate())
    assert set(quotes) == {767, 771, 775}
    assert all(q.mark == (q.bid + q.ask) / 2 for q in quotes.values())
    assert evidence["status"] == "recovered"
    assert evidence["legs"][0]["event_timestamp"] == NOW.isoformat()
    assert skipped is None and skipped_evidence == {}
    client.get_available_quotes.assert_awaited_once_with(SYMBOLS)


@pytest.mark.asyncio
@pytest.mark.parametrize("problem", ["stale", "missing", "aged", "untimed", "flag", "duplicate"])
async def test_rejects_unusable_response_without_partial_or_stale_valuation(problem):
    result = response(
        stale=problem == "stale", missing=(SYMBOLS[0],) if problem == "missing" else (),
    )
    if problem in {"aged", "untimed", "flag"}:
        updates = {"event_timestamp": None} if problem == "untimed" else (
            {"event_timestamp": NOW - dt.timedelta(seconds=301)} if problem == "aged"
            else {"data_quality_flags": ("stale",)}
        )
        result = result.model_copy(update={"quotes": (
            result.quotes[0].model_copy(update=updates), *result.quotes[1:],
        )})
    if problem == "duplicate":
        result = result.model_copy(update={"quotes": (*result.quotes, result.quotes[0])})
    helper, _ = recovery(result)
    with patch("butterfly_guy.services.position_quote_recovery.now_eastern", return_value=NOW):
        quotes, evidence = await helper.recover(trade(), candidate())
    assert quotes is None
    assert evidence["status"] in {"incomplete_response", "unusable_quotes"}


@pytest.mark.asyncio
async def test_request_failure_is_bounded_and_cancellation_propagates():
    helper, client = recovery(response())
    client.get_available_quotes.side_effect = TimeoutError("sensitive transport detail")
    quotes, evidence = await helper.recover(trade(), candidate())
    assert quotes is None
    assert evidence["error_type"] == "TimeoutError"
    assert "sensitive" not in str(evidence)
    helper.next_attempt_at = 0
    client.get_available_quotes.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await helper.recover(trade(), candidate())


def test_recovery_is_disabled_by_default_and_restricted_to_xsp_paper():
    config = load_config(config_path="configs/config_xsp.yaml")
    assert not config.position_data.recover_held_quotes
    candidate_config = load_config(
        config_path="configs/research/config_xsp_protection.yaml"
    )
    assert candidate_config.position_data.recover_held_quotes
    for section, values in (("execution", {"paper_trading": False}),
                            ("strategy", {"underlying": "NDX"})):
        data = candidate_config.model_dump()
        data[section].update(values)
        with pytest.raises(ValueError, match="restricted to XSP paper"):
            type(config).model_validate(data)


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled,stale,exit_requested", [
    (True, False, False), (True, True, False), (False, False, False), (True, False, True),
])
async def test_monitor_only_evaluates_complete_fresh_recovery(enabled, stale, exit_requested):
    service = _service([])
    service.config = load_config(config_path="configs/research/config_xsp_protection.yaml")
    service.config.position_data.recover_held_quotes = enabled
    service.config.position_data.shadow_held_quotes = False
    helper, client = recovery(response(stale=stale))
    service.market_data = helper.provider
    service.market_data.get_option_chain_observed = AsyncMock(side_effect=[
        ({}, observation()), asyncio.CancelledError,
    ])
    incomplete = chain_quotes()
    del incomplete[767]
    service._extract_quotes.return_value = incomplete
    service._extract_quotes.side_effect = None
    if exit_requested:
        service.state_machine.evaluate.side_effect = None
        service.state_machine.evaluate.return_value = SimpleNamespace(
            reason="profitprotector_breakeven_floor", urgency="high",
        )

        async def record_event(name, *_args, **_kwargs):
            if name == "position_held_quote_recovery":
                # Recovery diagnostics must not delay the exit action.
                assert service.order_manager.execute_exit.await_count == 1

        service.decision_queries.log_event.side_effect = record_event
    with (
        patch("butterfly_guy.services.position_service.is_market_open", return_value=True),
        patch("butterfly_guy.services.position_service.session_date", return_value=NOW.date()),
        patch(
            "butterfly_guy.services.position_service.get_0dte_expiration", return_value=NOW.date(),
        ),
        patch("butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()),
        patch("butterfly_guy.services.position_quote_recovery.now_eastern", return_value=NOW),
        pytest.raises(asyncio.CancelledError),
    ):
        await service.monitor_loop(trade(), candidate())
    assert service.state_machine.evaluate.call_count == int(enabled and not stale)
    assert client.get_available_quotes.await_count == int(enabled)
    assert service.order_manager.execute_exit.await_count == int(exit_requested)
    if enabled:
        events = [c for c in service.decision_queries.log_event.await_args_list
                  if c.args[0] == "position_held_quote_recovery"]
        assert events[0].args[1]["status"] == ("unusable_quotes" if stale else "recovered")


def test_xsp_candidate_protects_october_8_giveback_after_confirmation():
    baseline = load_config(config_path="configs/config_xsp.yaml")
    config = load_config(config_path="configs/research/config_xsp_protection.yaml")
    baseline_machine = ProfitStateMachine(baseline.profit_management)
    candidate_machine = ProfitStateMachine(config.profit_management)
    pos = make_pos(entry=0.37, current=0.58, peak=1.74, drawdown=1 - 0.58 / 1.74,
                   regime="afternoon", position_age_minutes=270, spread_bid=0.54,
                   spread_ask=0.62, bid_to_mark_ratio=0.54 / 0.58,
                   max_leg_spread_to_mark_ratio=1.0, max_leg_spread_abs=0.02)
    for _ in range(2):
        assert baseline_machine.evaluate(pos) is None
        assert candidate_machine.evaluate(pos) is None
    assert baseline_machine.evaluate(pos) is None
    assert candidate_machine.evaluate(pos).reason == "drawdown_afternoon"
    pos.current_value = 0.36
    assert candidate_machine.evaluate(pos).reason == "profitprotector_breakeven_floor"
    pos.position_age_minutes = 10
    assert candidate_machine.evaluate(pos) is None
