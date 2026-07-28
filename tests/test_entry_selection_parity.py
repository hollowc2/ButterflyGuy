"""Tests for Schwab vs DB entry selection parity reporting."""

from __future__ import annotations

from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.strategy.entry_selection import EntrySelectionResult
from butterfly_guy.strategy.entry_selection_parity import build_entry_selection_parity


def _candidate(
    *,
    width: int,
    center: float,
    cost: float,
) -> ButterflyCandidate:
    max_profit = width - cost
    return ButterflyCandidate(
        direction="CALL",
        wing_width=width,
        center_strike=center,
        lower_strike=center - width,
        upper_strike=center + width,
        cost=cost,
        ask=cost + 0.1,
        max_profit=max_profit,
        reward_risk=max_profit / cost if cost > 0 else 0.0,
        lower_be=center - width + cost,
        upper_be=center + width - cost,
        distance_from_spot=abs(center - 7400.0),
        spot_price=7400.0,
        lower_symbol="L",
        center_symbol="C",
        upper_symbol="U",
    )


def _selection(*candidates: ButterflyCandidate) -> EntrySelectionResult:
    chosen = candidates[0]
    return EntrySelectionResult(
        candidate=chosen,
        candidates=tuple(candidates),
        active_widths=tuple(c.wing_width for c in candidates),
        active_sigmas=(0.25, 0.50, 0.75),
        per_width_bests=tuple(candidates),
        selection_method="VIX",
    )


def test_build_entry_selection_parity_detects_ranking_flip():
    live = _selection(
        _candidate(width=20, center=7430.0, cost=1.78),
        _candidate(width=30, center=7440.0, cost=2.95),
    )
    base = _selection(
        _candidate(width=20, center=7430.0, cost=1.76),
        _candidate(width=30, center=7440.0, cost=2.82),
    )
    db = EntrySelectionResult(
        candidate=base.per_width_bests[1],
        candidates=base.candidates,
        active_widths=base.active_widths,
        active_sigmas=base.active_sigmas,
        per_width_bests=base.per_width_bests,
        selection_method="VIX",
    )

    report = build_entry_selection_parity(
        live=live,
        db=db,
        snapshot_lag_seconds=31.0,
        db_snapshot_time="2026-05-20T14:00:00+00:00",
        db_spot=7378.0,
        live_spot=7378.31,
    )

    assert report["ranking_flip"] is True
    assert report["width_match"] is False
    assert report["live_selected"]["width"] == 20
    assert report["db_selected"]["width"] == 30
    assert len(report["per_width_deltas"]) == 2
    assert report["per_width_deltas"][1]["cost_delta"] == 0.13
    assert report["per_width_deltas"][1]["mark_delta"] == 0.13


def test_build_entry_selection_parity_marks_match_when_widths_agree():
    candidate = _candidate(width=25, center=7575.0, cost=2.32)
    live = _selection(candidate)
    db = _selection(_candidate(width=25, center=7575.0, cost=2.30))

    report = build_entry_selection_parity(
        live=live,
        db=db,
        snapshot_lag_seconds=12.0,
        db_snapshot_time="2026-05-26T14:00:00+00:00",
        db_spot=7525.0,
        live_spot=7525.11,
    )

    assert report["ranking_flip"] is False
    assert report["width_match"] is True
    assert report["center_match"] is True


def test_build_entry_selection_parity_uses_configured_rr_target():
    selection = _selection(_candidate(width=25, center=7575.0, cost=2.5))
    report = build_entry_selection_parity(
        live=selection,
        db=selection,
        snapshot_lag_seconds=0,
        db_snapshot_time=None,
        db_spot=7525,
        live_spot=7525,
        rr_target=selection.candidate.reward_risk,
    )
    assert report["live_pick_rr_distance"] == 0
