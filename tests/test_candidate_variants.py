from pathlib import Path

import pytest

import butterfly_guy.strategy.entry_selection as entry_selection_module
from butterfly_guy.candidate_fleet.evaluator import CandidateEvaluator
from butterfly_guy.core.config import AppConfig
from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.position.position_manager import PositionState
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.scripts.run_candidate import load_candidate_config
from butterfly_guy.strategy.entry_selection import select_entry_candidate

ROOT = Path(__file__).resolve().parents[1]


def _config(name: str) -> AppConfig:
    return load_candidate_config(str(ROOT / "configs" / name))


def _candidate(
    *,
    center: float,
    cost: float,
    reward_risk: float,
    width: int = 20,
) -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="CALL",
        wing_width=width,
        center_strike=center,
        lower_strike=center - width,
        upper_strike=center + width,
        cost=cost,
        max_profit=width - cost,
        reward_risk=reward_risk,
        lower_be=center - width + cost,
        upper_be=center + width - cost,
        distance_from_spot=abs(center - 6300),
        spot_price=6300,
        lower_symbol=f"L{center}",
        center_symbol=f"C{center}",
        upper_symbol=f"U{center}",
    )


def _state(
    *,
    entry: float,
    current: float,
    peak: float,
    drawdown: float,
) -> PositionState:
    return PositionState(
        entry_price=entry,
        current_value=current,
        peak_value=peak,
        pnl=current - entry,
        drawdown_from_peak=drawdown,
        time_regime="morning",
        minutes_to_close=300,
        minutes_since_open=60,
    )


def test_vix_center_changes_only_where_the_entry_tent_is_placed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vix_centered = _candidate(center=6200, cost=1.8, reward_risk=8.0)
    best_rr = _candidate(center=6250, cost=1.0, reward_risk=10.0)
    monkeypatch.setattr(
        entry_selection_module.ButterflyBuilder,
        "build_candidates",
        lambda *_args, **_kwargs: [vix_centered, best_rr],
    )
    monkeypatch.setattr(
        entry_selection_module,
        "vix_target_center",
        lambda **_kwargs: 6200.0,
    )

    baseline = select_entry_candidate(
        quotes=[],
        spot=6300,
        direction="CALL",
        vix=18,
        config=_config("config_spx_candidate.yaml"),
        asset="SPX",
        wing_widths=[20],
    )
    variant = select_entry_candidate(
        quotes=[],
        spot=6300,
        direction="CALL",
        vix=18,
        config=_config("config_spx_candidate_vix_center.yaml"),
        asset="SPX",
        wing_widths=[20],
    )

    assert baseline.candidate is best_rr
    assert variant.candidate is vix_centered


def test_target_cost_prefers_debit_target_instead_of_best_rr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    best_rr = _candidate(center=6250, cost=1.0, reward_risk=10.0)
    target_cost = _candidate(center=6230, cost=1.9, reward_risk=8.0)
    monkeypatch.setattr(
        entry_selection_module.ButterflyBuilder,
        "build_candidates",
        lambda *_args, **_kwargs: [best_rr, target_cost],
    )

    baseline = select_entry_candidate(
        quotes=[],
        spot=6300,
        direction="CALL",
        vix=18,
        config=_config("config_spx_candidate.yaml"),
        asset="SPX",
        wing_widths=[20],
    )
    variant = select_entry_candidate(
        quotes=[],
        spot=6300,
        direction="CALL",
        vix=18,
        config=_config("config_spx_candidate_target_cost.yaml"),
        asset="SPX",
        wing_widths=[20],
    )

    assert baseline.candidate is best_rr
    assert variant.candidate is target_cost


def test_peak_trailer_retains_winner_that_profitprotector_floors() -> None:
    position = _state(entry=1.0, current=1.75, peak=3.0, drawdown=1.25 / 3.0)
    baseline = ProfitStateMachine(
        _config("config_spx_candidate.yaml").profit_management
    )
    variant = ProfitStateMachine(
        _config("config_spx_candidate_peak_trailer.yaml").profit_management
    )

    baseline_signal = baseline.evaluate(position)
    variant_signal = variant.evaluate(position)

    assert baseline_signal is not None
    assert baseline_signal.reason == "profitprotector_profit_floor"
    assert variant_signal is None


def test_absolute_stop_truncates_never_profitable_loss() -> None:
    position = _state(entry=1.0, current=0.45, peak=1.0, drawdown=0.55)
    baseline = ProfitStateMachine(
        _config("config_spx_candidate.yaml").profit_management
    )
    variant = ProfitStateMachine(
        _config("config_spx_candidate_absolute_stop.yaml").profit_management
    )

    assert baseline.evaluate(position) is None
    signal = variant.evaluate(position)
    assert signal is not None
    assert signal.reason == "absolute_loss_stop"


def test_gap_conviction_threshold_is_wired_into_candidate_evaluator() -> None:
    baseline = _config("config_spx_candidate.yaml")
    variant = _config("config_spx_candidate_gap_conviction.yaml")

    assert baseline.entry.min_gap_pct is None
    assert variant.entry.min_gap_pct == 0.0025
    assert "min_gap_pct" in CandidateEvaluator.attempt_entry.__code__.co_names
