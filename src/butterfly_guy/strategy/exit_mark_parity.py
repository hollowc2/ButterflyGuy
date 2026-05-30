"""Compare live Schwab exit marks against nearest DB collector snapshot."""

from __future__ import annotations

from typing import Any

from butterfly_guy.data.db_chain_quotes import rows_to_option_quotes
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, fly_mark_value

DB_EXIT_PARITY_MAX_LAG_SECONDS = 60


def _legs_payload(
    quotes: dict[float, OptionQuote],
    strikes: list[float],
) -> list[dict[str, float]]:
    legs: list[dict[str, float]] = []
    for strike in strikes:
        quote = quotes.get(strike)
        if quote is None:
            legs.append({"strike": strike, "bid": 0.0, "ask": 0.0, "mark": 0.0})
            continue
        legs.append(
            {
                "strike": strike,
                "bid": round(quote.bid, 4),
                "ask": round(quote.ask, 4),
                "mark": round(quote.mark, 4),
            }
        )
    return legs


def _fly_mark_from_quotes(
    quotes: dict[float, OptionQuote],
    candidate: ButterflyCandidate,
) -> float | None:
    lower_q = quotes.get(candidate.lower_strike)
    center_q = quotes.get(candidate.center_strike)
    upper_q = quotes.get(candidate.upper_strike)
    if not all([lower_q, center_q, upper_q]):
        return None
    return round(fly_mark_value(lower_q, center_q, upper_q), 4)


def build_exit_mark_parity(
    *,
    candidate: ButterflyCandidate,
    live_quotes: dict[float, OptionQuote],
    live_fly_mark: float,
    live_peak: float,
    live_drawdown_pct: float,
    exit_reason: str,
    live_spread_bid: float | None = None,
    snapshot: dict[str, Any] | None,
    underlying: str,
    expiration,
) -> dict[str, object]:
    """Return a JSON-serializable Schwab vs DB exit mark comparison."""
    strikes = [candidate.lower_strike, candidate.center_strike, candidate.upper_strike]
    base: dict[str, object] = {
        "exit_reason": exit_reason,
        "live_fly_mark": round(live_fly_mark, 4),
        "live_peak": round(live_peak, 4),
        "live_drawdown_pct": round(live_drawdown_pct, 1),
        "live_spread_bid": round(live_spread_bid, 4) if live_spread_bid is not None else None,
        "live_legs": _legs_payload(live_quotes, strikes),
        "wing_width": candidate.wing_width,
        "center_strike": candidate.center_strike,
    }

    if snapshot is None:
        base["available"] = False
        base["reason"] = f"no_db_snapshot_within_{DB_EXIT_PARITY_MAX_LAG_SECONDS}s"
        return base

    db_quotes = rows_to_option_quotes(
        snapshot["rows"],
        underlying=underlying,
        expiration=expiration,
    )
    db_by_strike = {
        quote.strike: quote
        for quote in db_quotes
        if quote.option_type == candidate.direction
    }
    db_fly_mark = _fly_mark_from_quotes(db_by_strike, candidate)
    if db_fly_mark is None:
        base["available"] = False
        base["reason"] = "missing_db_leg_quotes"
        base["snapshot_lag_seconds"] = snapshot["lag_seconds"]
        base["db_snapshot_time"] = snapshot["snapshot_time"].isoformat()
        return base

    fly_delta = round(live_fly_mark - db_fly_mark, 4)
    drawdown_exit = exit_reason.startswith("drawdown_")
    replay_would_miss = drawdown_exit and fly_delta < -0.01

    base.update(
        {
            "available": True,
            "snapshot_lag_seconds": snapshot["lag_seconds"],
            "db_snapshot_time": snapshot["snapshot_time"].isoformat(),
            "db_fly_mark": db_fly_mark,
            "fly_mark_delta": fly_delta,
            "db_legs": _legs_payload(db_by_strike, strikes),
            "replay_would_miss_drawdown": replay_would_miss,
        }
    )
    return base
