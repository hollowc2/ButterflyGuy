import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import butterfly_guy.candidate_fleet.evaluator as evaluator_module
from butterfly_guy.candidate_fleet.evaluator import (
    CandidateEvaluator,
    candidate_closed_trade_count,
    candidate_data_quality_failures,
    candidate_fill_parity_failures,
    candidate_open_positions,
    candidate_parity_failures,
    candidate_performance_stats,
    candidate_review_progress,
    candidate_trade_count,
)
from butterfly_guy.candidate_fleet.models import MarketSnapshot, SnapshotIdentity
from butterfly_guy.core.config import AppConfig


class MetricsPool:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.trade_query = ""
        self.failure_query = ""

    async def fetch(self, query: str) -> list[dict[str, object]]:
        self.trade_query = query
        return self.rows

    async def fetchrow(self, query: str, candidate_id: str) -> dict[str, int]:
        self.failure_query = query
        assert candidate_id == "nineteen-closed"
        return {"data_quality_failures": 3, "parity_failures": 2}


def _gauge_value(gauge, candidate_id: str) -> float:
    return gauge.labels(candidate_id=candidate_id)._value.get()


def test_candidate_performance_stats_reports_outlier_dependence() -> None:
    stats = candidate_performance_stats([100.0, -50.0, 25.0])

    assert stats.closed_trade_count == 3
    assert stats.total_pnl == 75.0
    assert stats.average_pnl == 25.0
    assert stats.win_rate == pytest.approx(2 / 3)
    assert stats.profit_factor == 2.5
    assert stats.max_drawdown == 50.0
    assert stats.largest_winner_share == 0.8
    assert stats.pnl_without_largest_winner == -25.0


def test_candidate_fill_parity_counts_entry_exit_mismatch_or_missing_evidence() -> None:
    matching = {
        "status": "CLOSED",
        "entry_price": 1.0,
        "exit_price": 2.0,
        "metadata": {
            "entry_execution_diagnostics": {"observed_mark": 1.0},
            "exit_execution_diagnostics": {"observed_mark": 2.0},
        },
    }
    entry_mismatch = {
        **matching,
        "entry_price": 1.1,
    }
    missing_exit = {
        **matching,
        "metadata": {
            "entry_execution_diagnostics": {"observed_mark": 1.0},
        },
    }

    assert candidate_fill_parity_failures(
        [matching, entry_mismatch, missing_exit]
    ) == 2


@pytest.mark.asyncio
async def test_review_progress_counts_only_closed_mark_v1_trades() -> None:
    rows: list[dict[str, object]] = [
        {
            "status": "CLOSED",
            "pnl": 10.0,
            "entry_price": 1.0,
            "exit_price": 1.1,
            "metadata": {
                "entry_execution_diagnostics": {"observed_mark": 1.0},
                "exit_execution_diagnostics": {"observed_mark": 1.1},
            },
        }
        for _ in range(19)
    ]
    rows.append(
        {
            "status": "OPEN",
            "pnl": 0.0,
            "entry_price": 1.0,
            "exit_price": None,
            "metadata": {
                "entry_execution_diagnostics": {"observed_mark": 1.0},
            },
        }
    )
    pool = MetricsPool(rows)
    evaluator = CandidateEvaluator.__new__(CandidateEvaluator)
    evaluator.candidate_id = "nineteen-closed"
    evaluator.review_trade_count = 20
    evaluator.trades = SimpleNamespace(db=SimpleNamespace(pool=pool))

    await evaluator.refresh_metrics()

    assert "metadata->>'paper_fill_model' = 'mark_v1'" in pool.trade_query
    assert "data->>'candidate_id' = $1" in pool.failure_query
    assert _gauge_value(candidate_trade_count, evaluator.candidate_id) == 20
    assert _gauge_value(candidate_closed_trade_count, evaluator.candidate_id) == 19
    assert _gauge_value(candidate_open_positions, evaluator.candidate_id) == 1
    assert _gauge_value(candidate_review_progress, evaluator.candidate_id) == 0.95
    assert _gauge_value(candidate_data_quality_failures, evaluator.candidate_id) == 3
    assert _gauge_value(candidate_parity_failures, evaluator.candidate_id) == 2


@pytest.mark.asyncio
async def test_min_gap_filter_logs_no_trade_before_candidate_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_at = dt.datetime.now(dt.timezone.utc)
    snapshot = MarketSnapshot(
        identity=SnapshotIdentity("feed", 7),
        captured_at=captured_at,
        expiration=captured_at.date(),
        spot=6301.0,
        vix=18.0,
        session_open=6301.0,
        previous_close=6300.0,
        quotes=(),
    )
    provider = AsyncMock()
    provider.snapshot.return_value = snapshot
    evaluator = CandidateEvaluator.__new__(CandidateEvaluator)
    evaluator.candidate_id = "gap-conviction"
    evaluator.config = AppConfig(entry={"min_gap_pct": 0.0025})
    evaluator.provider = provider
    evaluator.risk = AsyncMock()
    evaluator.risk.can_trade.return_value = (True, "")
    evaluator.decisions = AsyncMock()
    evaluator._last_identity = None
    monkeypatch.setattr(evaluator_module, "time_in_window", lambda *args: True)
    monkeypatch.setattr(
        evaluator_module,
        "select_entry_candidate",
        lambda **kwargs: pytest.fail("selection must not run below the gap threshold"),
    )

    result = await evaluator.attempt_entry()

    assert result is None
    event_type, data, event_snapshot = evaluator.decisions.log.await_args.args
    assert event_type == "entry_gap_filtered"
    assert data["reason"] == "gap_below_min"
    assert data["gap_pct"] == pytest.approx(1 / 6300)
    assert data["min_gap_pct"] == 0.0025
    assert event_snapshot is snapshot
    provider.release_lease.assert_awaited_once_with("gap-conviction")


@pytest.mark.asyncio
async def test_min_gap_filter_preserves_direction_above_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_at = dt.datetime.now(dt.timezone.utc)
    snapshot = MarketSnapshot(
        identity=SnapshotIdentity("feed", 8),
        captured_at=captured_at,
        expiration=captured_at.date(),
        spot=6321.0,
        vix=18.0,
        session_open=6320.0,
        previous_close=6300.0,
        quotes=(),
    )
    provider = AsyncMock()
    provider.snapshot.return_value = snapshot
    evaluator = CandidateEvaluator.__new__(CandidateEvaluator)
    evaluator.candidate_id = "gap-conviction-pass"
    evaluator.config = AppConfig(entry={"min_gap_pct": 0.0025})
    evaluator.provider = provider
    evaluator.risk = AsyncMock()
    evaluator.risk.can_trade.return_value = (True, "")
    evaluator.decisions = AsyncMock()
    evaluator.candidates = AsyncMock()
    evaluator._last_identity = None
    selected = SimpleNamespace(
        candidates=(),
        candidate=None,
        selection_method="BEST_RR",
    )
    select = Mock(return_value=selected)
    monkeypatch.setattr(evaluator_module, "time_in_window", lambda *args: True)
    monkeypatch.setattr(evaluator_module, "select_entry_candidate", select)

    result = await evaluator.attempt_entry()

    assert result is None
    assert select.call_args.kwargs["direction"] == "CALL"
    assert select.call_args.kwargs["spot"] == 6321.0
    assert evaluator.decisions.log.await_args.args[0] == "no_candidates"
