import datetime as dt
from unittest.mock import AsyncMock

import pytest

from butterfly_guy.candidate_fleet.evaluator import (
    CandidateAuditContext,
    CandidateEvaluator,
)
from butterfly_guy.candidate_fleet.models import (
    SessionClose,
    SessionCloseUnavailableError,
)
from butterfly_guy.data.schemas import ButterflyCandidate, TradeRecord


def _trade() -> TradeRecord:
    return TradeRecord(
        trade_id=17,
        trade_date=dt.date(2026, 7, 23),
        direction="CALL",
        wing_width=20,
        center_strike=6300,
        lower_strike=6280,
        upper_strike=6320,
        entry_price=1.0,
        entry_time=dt.datetime(2026, 7, 23, 14, 0, tzinfo=dt.timezone.utc),
        lower_symbol="L",
        center_symbol="C",
        upper_symbol="U",
        peak_value=4.0,
    )


def _candidate() -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="CALL",
        wing_width=20,
        center_strike=6300,
        lower_strike=6280,
        upper_strike=6320,
        cost=1.0,
        max_profit=19.0,
        reward_risk=19.0,
        lower_be=6281,
        upper_be=6319,
        distance_from_spot=0,
        spot_price=6300,
        lower_symbol="L",
        center_symbol="C",
        upper_symbol="U",
    )


def _evaluator(provider: AsyncMock) -> CandidateEvaluator:
    evaluator = CandidateEvaluator.__new__(CandidateEvaluator)
    evaluator.candidate_id = "vix-center"
    evaluator.provider = provider
    evaluator.audit = CandidateAuditContext("vix-center", "config-hash", "git-sha")
    evaluator.trades = AsyncMock()
    evaluator.trades.close_trade.return_value = True
    evaluator.risk = AsyncMock()
    evaluator.decisions = AsyncMock()
    evaluator.refresh_metrics = AsyncMock()
    return evaluator


@pytest.mark.asyncio
async def test_candidate_cash_settlement_uses_only_shared_feed_evidence() -> None:
    provider = AsyncMock()
    provider.session_close.return_value = SessionClose(
        session_date=dt.date(2026, 7, 23),
        close=6305.0,
        bar_timestamp=dt.datetime(2026, 7, 23, 19, 59, tzinfo=dt.timezone.utc),
        observed_at=dt.datetime(2026, 7, 23, 20, 1, tzinfo=dt.timezone.utc),
        source="schwab_spx_intraday_1m_regular_session_close",
        feed_instance="feed-close",
    )
    evaluator = _evaluator(provider)
    trade = _trade()

    await evaluator._cash_settle_position(trade, _candidate())

    provider.session_close.assert_awaited_once_with(trade.trade_date)
    close_args = evaluator.trades.close_trade.await_args
    assert close_args.args[:6] == (
        17,
        15.0,
        provider.session_close.return_value.bar_timestamp,
        "cash_settled",
        14.0,
        15.0,
    )
    metadata = close_args.kwargs["metadata"]
    assert metadata["paper_fill_model"] == "mark_v1"
    assert metadata["settlement_spot"] == 6305.0
    assert metadata["settlement_feed_instance"] == "feed-close"
    assert metadata["exit_execution_diagnostics"]["side"] == "settlement"
    evaluator.risk.record_pnl.assert_awaited_once_with(1400.0, trade.trade_date)
    evaluator.refresh_metrics.assert_awaited_once()


@pytest.mark.asyncio
async def test_candidate_cash_settlement_fails_closed_without_feed_evidence() -> None:
    provider = AsyncMock()
    provider.session_close.side_effect = SessionCloseUnavailableError("not ready")
    evaluator = _evaluator(provider)

    with pytest.raises(SessionCloseUnavailableError, match="not ready"):
        await evaluator._cash_settle_position(_trade(), _candidate())

    evaluator.trades.close_trade.assert_not_awaited()
    evaluator.risk.record_pnl.assert_not_awaited()
    evaluator.refresh_metrics.assert_not_awaited()
