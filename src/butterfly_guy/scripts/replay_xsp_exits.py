"""Offline fixed-entry XSP monitor replay; never connects to a broker or DB.

Uses exported trade JSONL and monitor CSV at their recorded poll timestamps.
Baseline parity must be established before running an earlier-trailer trial.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import itertools
import json
from pathlib import Path

from butterfly_guy.core.config import AppConfig, load_config
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.core.time_utils import EASTERN, is_market_open
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.position.position_manager import PositionManager
from butterfly_guy.position.state_machine import ProfitStateMachine


def replay_trade(
    trade: dict,
    observations: list[list[dict]],
    config: AppConfig,
    *,
    earlier_trailer: bool = False,
) -> dict:
    """Compare actual peak acceptance and first eligible exit with recorded polls.

    Hypothetical exits use component-leg bid less the configured fee/slippage,
    floored at zero. A floor is explicitly counted; this is not a broker fill.
    Gaps and baseline mismatches remain visible rather than being interpolated.
    """
    if config.strategy.underlying != "XSP":
        raise ValueError("this replay requires the XSP configuration")
    settings = config.profit_management.model_copy(deep=True)
    if earlier_trailer:
        for regime in settings.regimes.values():
            regime.drawdown_threshold = 0.50
    manager = PositionManager("XSP", settings)
    machine = ProfitStateMachine(settings)
    entry = float(trade["entry_price"])
    manager.reset(entry)
    width = int(trade["wing_width"])
    center = float(trade["center_strike"])
    candidate = ButterflyCandidate(
        direction=trade["direction"],
        wing_width=width,
        center_strike=center,
        lower_strike=center - width,
        upper_strike=center + width,
        cost=entry,
        max_profit=width - entry,
        reward_risk=(width - entry) / entry,
        lower_be=center - width + entry,
        upper_be=center + width - entry,
        distance_from_spot=0.0,
        spot_price=float(trade["entry_spot"]),
    )
    entry_time = dt.datetime.fromisoformat(trade["entry_time"])
    day = dt.date.fromisoformat(trade["trade_date"])
    count = mismatches = 0
    max_difference = max_gap = 0.0
    previous = entry_time
    first_exit = None
    for batch in observations:
        at = dt.datetime.fromisoformat(batch[0]["ts"])
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("monitor timestamp must be timezone-aware")
        if at < previous:
            raise ValueError("monitor observations are out of order or before entry")
        if at.astimezone(EASTERN).date() != day:
            raise ValueError("monitor observation belongs to a different session")
        max_gap = max(max_gap, (at - previous).total_seconds())
        previous = at
        # A poll can finish after close; runtime already evaluated that poll.
        quotes = {}
        for row in batch:
            if (
                int(row["trade_id"]) != int(trade["id"])
                or row["option_type"] != trade["direction"]
                or dt.date.fromisoformat(row["expiration"]) != day
            ):
                raise ValueError("foreign trade, direction or expiration in monitor quotes")
            strike = float(row["strike"])
            if strike in quotes:
                raise ValueError("duplicate leg in monitor observation")
            bid, ask, mark = (float(row[k]) for k in ("bid", "ask", "mark"))
            if bid < 0 or ask < bid or mark < 0:
                raise ValueError("invalid monitor market")
            quotes[strike] = OptionQuote(
                symbol=row["symbol"],
                underlying="XSP",
                expiration=day,
                strike=strike,
                option_type=row["option_type"],
                bid=bid,
                ask=ask,
                mark=mark,
            )
        if set(quotes) != {center - width, center, center + width}:
            raise ValueError("monitor observation does not contain exactly the held legs")
        state = manager.update_position_value(
            candidate, quotes, at=at, include_tent_boundaries=False
        )
        state.position_age_minutes = (at - entry_time).total_seconds() / 60
        count += 1
        difference = abs(state.peak_value - float(batch[0]["peak_value"]))
        max_difference = max(max_difference, difference)
        mismatches += difference > 0.00011
        signal = machine.evaluate(state)
        if signal and first_exit is None:
            fee = 4 * config.execution.paper_commission_per_contract / 100
            raw_exit = float(state.spread_bid) - fee - config.execution.paper_slippage_per_spread
            first_exit = {
                "time": at.isoformat(),
                "reason": signal.reason,
                "observed_mark": state.current_value,
                "observed_bid": state.spread_bid,
                "estimated_exit_price": round(max(0.0, raw_exit), 2),
                "exit_floor_used": raw_exit < 0,
            }
    if count == 0:
        raise ValueError("no monitor observations for trade")
    end = previous.astimezone(EASTERN)
    terminal_coverage = not is_market_open(end + dt.timedelta(seconds=10))
    marketable_entry = float(trade["entry_diagnostics"]["marketable_entry_estimate"])
    quantity = int(trade["quantity"])
    settlement_pnl = (
        (float(trade["exit_price"]) - marketable_entry) * 100 * quantity
        if trade.get("exit_reason") == "cash_settled" and trade.get("exit_price") is not None
        else None
    )
    hypothetical_pnl = settlement_pnl
    if first_exit:
        hypothetical_pnl = (first_exit["estimated_exit_price"] - marketable_entry) * 100 * quantity
    return {
        "trade_id": trade["id"],
        "date": day.isoformat(),
        "direction": trade["direction"],
        "polls": count,
        "max_gap_seconds": round(max_gap, 3),
        "terminal_coverage": terminal_coverage,
        "peak_mismatch_polls": mismatches,
        "max_peak_difference": round(max_difference, 6),
        "first_exit": first_exit,
        "settlement_pnl_dollars": round(settlement_pnl, 2) if settlement_pnl is not None else None,
        "policy_pnl_dollars": round(hypothetical_pnl, 2) if hypothetical_pnl is not None else None,
        "settlement_source": trade.get("settlement_source"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--quotes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    candidates = parser.add_mutually_exclusive_group()
    candidates.add_argument("--earlier-trailer", action="store_true")
    candidates.add_argument("--candidate-config", type=Path)
    parser.add_argument("--include-open", action="store_true",
                        help="Allow partial-session OPEN trades; never invent settlement")
    args = parser.parse_args()
    setup_logging(log_level="ERROR", json_output=False)
    config = load_config(config_path="configs/config_xsp.yaml")
    candidate_config = (
        load_config(config_path=args.candidate_config) if args.candidate_config else None
    )
    sections = [json.loads(line) for line in args.trades.read_text().splitlines()]
    trades = {int(t["id"]): t for s in sections if s["section"] == "trades" for t in s["rows"]}
    results = []
    with args.quotes.open() as handle:
        groups = itertools.groupby(csv.DictReader(handle), key=lambda r: int(r["trade_id"]))
        for trade_id, rows in groups:
            observations = [
                list(batch) for _, batch in itertools.groupby(rows, key=lambda r: r["ts"])
            ]
            trade = trades[trade_id]
            open_trade = args.include_open and trade.get("status") == "OPEN"
            if trade["fill_model"] != "mark_v1" or (
                trade["exit_reason"] != "cash_settled" and not open_trade
            ):
                raise ValueError("replay cohort requires mark_v1 cash-settled trades")
            try:
                baseline = replay_trade(trade, observations, config)
            except ValueError as exc:
                results.append(
                    {
                        "trade_id": trade_id,
                        "date": trade["trade_date"],
                        "baseline_parity": False,
                        "data_error": str(exc),
                    }
                )
                continue
            baseline["baseline_parity"] = (
                baseline["peak_mismatch_polls"] == 0
                and baseline["first_exit"] is None
                and (baseline["terminal_coverage"] or open_trade)
            )
            if args.earlier_trailer and baseline["baseline_parity"]:
                baseline["earlier_trailer"] = replay_trade(
                    trade, observations, config, earlier_trailer=True
                )
            if candidate_config is not None and baseline["baseline_parity"]:
                baseline["candidate_policy"] = replay_trade(trade, observations, candidate_config)
            results.append(baseline)
    report = {
        "scope": "XSP fixed observed entries; monitor policy replay, not entry selection",
        "candidate": str(args.candidate_config) if args.candidate_config else (
            "50% trailing drawdown in all regimes; "
            "all other quality/hold/confirmation rules unchanged"
        ),
        "earlier_trailer_requested": args.earlier_trailer,
        "include_open": args.include_open,
        "candidate_policy_settings": (
            candidate_config.profit_management.model_dump(mode="json")
            if candidate_config is not None else None
        ),
        "policy_settings": config.profit_management.model_dump(mode="json"),
        "source_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                Path(__file__),
                Path("src/butterfly_guy/position/position_manager.py"),
                Path("src/butterfly_guy/position/state_machine.py"),
                Path("src/butterfly_guy/position/profit_policy.py"),
            )
        },
        "input_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (args.trades, args.quotes, Path("configs/config_xsp.yaml"),
                      *([args.candidate_config] if args.candidate_config else []))
        },
        "trades": results,
        "limitations": [
            "No IV/tent geometry in monitor export",
            "Quote-event age and failed polls are not recorded",
            "Recorded timestamps follow valuation; boundary timing can differ",
            "Settlement uses recorded market-data proxy",
            "Missing telemetry is not interpolated",
            "Candidate evaluated only on exact baseline peak/exit parity",
            "Component-bid exits are hypothetical, not fills",
            "OPEN trades have partial coverage and no settlement P&L",
            "Held-quote recovery is not simulated by the monitor policy replay",
        ],
    }
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(
        f"{len(results)} trades; {sum(r['baseline_parity'] for r in results)} "
        "with exact recorded baseline parity"
    )


if __name__ == "__main__":
    main()
