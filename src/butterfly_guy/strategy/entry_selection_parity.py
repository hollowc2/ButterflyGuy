"""Compare live Schwab entry selection against nearest DB chain snapshot."""

from __future__ import annotations

from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.strategy.entry_selection import EntrySelectionResult

RR_TARGET = 10.0


def _candidate_payload(candidate: ButterflyCandidate | None) -> dict[str, float | int] | None:
    if candidate is None:
        return None
    return {
        "width": candidate.wing_width,
        "center": candidate.center_strike,
        "mark": round(candidate.cost, 4),
        "cost": round(candidate.cost, 4),
        "reward_risk": round(candidate.reward_risk, 4),
        "rr_distance": round(abs(candidate.reward_risk - RR_TARGET), 4),
    }


def _per_width_payload(candidates: tuple[ButterflyCandidate, ...]) -> list[dict[str, float | int]]:
    return [
        {
            "width": candidate.wing_width,
            "center": candidate.center_strike,
            "mark": round(candidate.cost, 4),
            "cost": round(candidate.cost, 4),
            "reward_risk": round(candidate.reward_risk, 4),
            "rr_distance": round(abs(candidate.reward_risk - RR_TARGET), 4),
        }
        for candidate in candidates
    ]


def build_entry_selection_parity(
    *,
    live: EntrySelectionResult,
    db: EntrySelectionResult,
    snapshot_lag_seconds: float | None,
    db_snapshot_time: str | None,
    db_spot: float | None,
    live_spot: float,
) -> dict[str, object]:
    """Return a JSON-serializable Schwab vs DB selection comparison."""
    live_pick = live.candidate
    db_pick = db.candidate

    width_match = (
        live_pick is not None
        and db_pick is not None
        and live_pick.wing_width == db_pick.wing_width
    )
    center_match = (
        width_match
        and live_pick is not None
        and db_pick is not None
        and abs(live_pick.center_strike - db_pick.center_strike) < 0.5
    )
    ranking_flip = live_pick is not None and db_pick is not None and not width_match

    db_by_width = {candidate.wing_width: candidate for candidate in db.per_width_bests}
    per_width_deltas: list[dict[str, float | int | bool]] = []
    for live_width_best in live.per_width_bests:
        db_width_best = db_by_width.get(live_width_best.wing_width)
        if db_width_best is None:
            continue
        center_match = abs(live_width_best.center_strike - db_width_best.center_strike) < 0.5
        per_width_deltas.append(
            {
                "width": live_width_best.wing_width,
                "live_center": live_width_best.center_strike,
                "db_center": db_width_best.center_strike,
                "center_match": center_match,
                "live_mark": round(live_width_best.cost, 4),
                "db_mark": round(db_width_best.cost, 4),
                "live_cost": round(live_width_best.cost, 4),
                "db_cost": round(db_width_best.cost, 4),
                "mark_delta": round(live_width_best.cost - db_width_best.cost, 4),
                "cost_delta": round(live_width_best.cost - db_width_best.cost, 4),
                "live_rr": round(live_width_best.reward_risk, 4),
                "db_rr": round(db_width_best.reward_risk, 4),
                "rr_delta": round(live_width_best.reward_risk - db_width_best.reward_risk, 4),
            }
        )

    live_pick_distance = (
        abs(live_pick.reward_risk - RR_TARGET) if live_pick is not None else None
    )
    db_pick_distance = abs(db_pick.reward_risk - RR_TARGET) if db_pick is not None else None

    return {
        "snapshot_lag_seconds": snapshot_lag_seconds,
        "db_snapshot_time": db_snapshot_time,
        "live_spot": round(live_spot, 2),
        "db_spot": round(db_spot, 2) if db_spot is not None else None,
        "live_selected": _candidate_payload(live_pick),
        "db_selected": _candidate_payload(db_pick),
        "width_match": width_match,
        "center_match": center_match,
        "ranking_flip": ranking_flip,
        "live_per_width": _per_width_payload(live.per_width_bests),
        "db_per_width": _per_width_payload(db.per_width_bests),
        "per_width_deltas": per_width_deltas,
        "live_pick_rr_distance": live_pick_distance,
        "db_pick_rr_distance": db_pick_distance,
    }
