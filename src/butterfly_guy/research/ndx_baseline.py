"""Offline NDX-R0 baseline approximation and evidence coverage audit (no variants).

The contract pins source, assumptions and parent study. This is a fixed-entry
research replay, not a runtime simulator. All outputs go to a new directory.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.metadata
import json
import logging
import math
import platform
import re
import shlex
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from butterfly_guy.research.ndx_evidence import (
    digest,
    new_directory,
    read_json,
    verify,
    write_json,
)

EASTERN = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[3]


def rows(path: Path) -> list[dict]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def timestamp(value: str) -> dt.datetime:
    result = dt.datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("naive evidence timestamp")
    return result.astimezone(dt.timezone.utc)


def optional(value):
    return float(value) if value not in (None, "") else None


@dataclass(frozen=True)
class Observation:
    ts: dt.datetime
    mark: float
    bid: float
    ask: float
    max_abs: float | None
    max_ratio: float | None
    recorded_peak: float | None


def normalize(path: Path, tolerance: float) -> tuple[dict, dict]:
    paths = defaultdict(list)
    audit = defaultdict(lambda: Counter(rows=0, incomplete=0, mark_mismatches=0))
    seen = set()
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            tid = int(row["trade_id"])
            at = timestamp(row["ts"])
            if (tid, at) in seen:
                raise ValueError(f"duplicate grouped observation: {tid} {at}")
            seen.add((tid, at))
            audit[tid]["rows"] += 1
            values = [optional(row[k]) for k in ("raw_mark", "raw_bid", "raw_ask")]
            if (
                int(row["legs"]) != 3
                or int(row["invalid_legs"]) != 0
                or any(v is None or not math.isfinite(v) for v in values)
            ):
                audit[tid]["incomplete"] += 1
                continue
            mark, bid, ask = values
            recorded = optional(row["recorded_mark"])
            if recorded is None or abs(max(0, mark) - recorded) > tolerance:
                audit[tid]["mark_mismatches"] += 1
            paths[tid].append(
                Observation(
                    at,
                    max(0, mark),
                    max(0, bid),
                    ask,
                    optional(row["max_leg_spread_abs"]),
                    optional(row["max_leg_spread_to_mark_ratio"]),
                    optional(row["recorded_peak"]),
                )
            )
    for path_rows in paths.values():
        path_rows.sort(key=lambda obs: obs.ts)
    return paths, audit


def exit_prices(mark: float, bid: float, contract: dict) -> dict:
    # Preserve Python round and the historical clipping order, including bid<0.
    commission = contract["commission_points_per_side"]
    unclipped_stress = round(max(0, bid) - contract["slippage_points"] - commission, 2)
    return {
        "paper": max(0, round(max(0, mark) - commission, 2)),
        "stress": max(0, unclipped_stress),
        "stress_floor_applied": unclipped_stress < 0,
        "stress_floor_points": max(0, -unclipped_stress),
    }


def pnl(exit_price: float, embedded_entry: float, quantity: int) -> float:
    # mark_v1 prices already include commission. Settlement has no closing fee.
    return round((exit_price - embedded_entry) * 100 * quantity, 2)


def fill_after(path: list[Observation], index: int, trade: dict, seconds: float):
    signal = path[index].ts
    if index + 1 < len(path):
        nxt = path[index + 1]
        if 0 <= (nxt.ts - signal).total_seconds() <= seconds:
            return nxt.ts, nxt.mark, nxt.bid, False
    # A terminal diagnostic is independent of the final monitor observation,
    # but its collection/event time was not exported: exit_time is a proxy.
    else:
        terminal = json.loads(trade["exit_diagnostics"] or "{}")
        at = timestamp(trade["exit_time"])
        if (
            0 <= (at - signal).total_seconds() <= seconds
            and terminal.get("observed_mark") is not None
            and terminal.get("observed_bid") is not None
        ):
            return at, terminal["observed_mark"], terminal["observed_bid"], True
    return None


def settlement_payoff(trade: dict) -> float | None:
    spot = optional(trade.get("settlement_spot"))
    if spot is None:
        return None
    strikes = [float(trade[k]) for k in ("lower_strike", "center_strike", "upper_strike")]
    sign = -1 if trade["direction"] == "PUT" else 1
    legs = [max(0, sign * (spot - strike)) for strike in strikes]
    return max(0, round(legs[0] - 2 * legs[1] + legs[2], 4))


def replay(trade: dict, path: list[Observation], settings, contract: dict) -> dict:
    from butterfly_guy.core.time_utils import market_close_time
    from butterfly_guy.position.position_manager import PositionState
    from butterfly_guy.position.state_machine import ProfitStateMachine

    entry = float(trade["entry_price"])
    qty = int(trade["quantity"])
    result = {
        "id": int(trade["id"]),
        "date": trade["trade_date"],
        "modern": trade["fill_model"] == "mark_v1",
        "pnl": None,
        "executable_pnl": None,
        "reason": None,
        "signal_time": None,
        "exit_time": None,
        "stress_floor_applied": False,
    }
    if not path:
        return result | {"status": "missing_observations"}
    if qty != 1:
        return result | {"status": "unsupported_historical_quantity"}
    entry_ts = timestamp(trade["entry_time"])
    exit_ts = timestamp(trade["exit_time"])
    if path[0].ts < entry_ts or path[-1].ts > exit_ts:
        raise ValueError("held path outside recorded lifecycle")
    et = path[0].ts.astimezone(EASTERN)
    open_at = et.replace(hour=9, minute=30, second=0, microsecond=0)
    close_at = dt.datetime.combine(et.date(), market_close_time(et.date()), EASTERN)
    machine = ProfitStateMachine(settings)
    peak = entry
    prior = entry_ts
    entry_estimate = json.loads(trade["entry_diagnostics"] or "{}").get("marketable_entry_estimate")
    for index, obs in enumerate(path):
        peak = max(peak, obs.mark)
        mins = (obs.ts - open_at).total_seconds() / 60
        # R0 used fixed boundaries rather than the runtime regime resolver.
        regime = "morning" if mins < 120 else "late_morning" if mins < 240 else "afternoon"
        pos = PositionState(
            entry_price=entry,
            current_value=round(obs.mark, 4),
            peak_value=round(peak, 4),
            pnl=round(obs.mark - entry, 4),
            drawdown_from_peak=round((peak - obs.mark) / peak, 4) if peak else 0,
            time_regime=regime,
            minutes_to_close=max(0, (close_at - obs.ts).total_seconds() / 60),
            minutes_since_open=mins,
            spread_bid=round(obs.bid, 4),
            spread_ask=round(obs.ask, 4),
            bid_to_mark_ratio=round(obs.bid / obs.mark, 4) if obs.mark > 0 else None,
            position_age_minutes=(obs.ts - entry_ts).total_seconds() / 60,
            max_leg_spread_abs=obs.max_abs,
            max_leg_spread_to_mark_ratio=obs.max_ratio,
        )
        if (obs.ts - prior).total_seconds() > contract["continuity_seconds"]:
            machine._reset_pending_drawdown()
        prior = obs.ts
        signal = machine.evaluate(pos)
        if signal is None:
            continue
        result.update(reason=signal.reason, signal_time=obs.ts.isoformat(), peak=peak)
        fill = fill_after(path, index, trade, contract["fill_window_seconds"])
        if fill is None:
            return result | {"status": "censored_fill"}
        at, mark, bid, terminal = fill
        prices = exit_prices(mark, bid, contract)
        return result | {
            "status": "exit",
            "exit_time": at.isoformat(),
            "exit_mark": mark,
            "exit_bid": bid,
            "terminal_exit_observation": terminal,
            "paper_exit_price": prices["paper"],
            "stress_exit_price": prices["stress"],
            "stress_floor_applied": prices["stress_floor_applied"],
            "stress_floor_points": prices["stress_floor_points"],
            "pnl": pnl(prices["paper"], entry, qty),
            "executable_pnl": pnl(prices["stress"], entry_estimate, qty)
            if entry_estimate is not None
            else None,
        }
    if (
        trade["exit_reason"] == "cash_settled"
        and (close_at - path[-1].ts).total_seconds() <= contract["tail_seconds"]
    ):
        # Only reuse an ACTUAL recorded settlement. Never infer a later payoff
        # for a position whose recording ended with a discretionary exit.
        payoff = optional(trade["exit_price"])
        if payoff is not None:
            return result | {
                "status": "settlement",
                "reason": "cash_settled",
                "exit_time": exit_ts.isoformat(),
                "pnl": pnl(payoff, entry, qty),
                "executable_pnl": pnl(payoff, entry_estimate, qty)
                if entry_estimate is not None
                else None,
                "settlement_basis": "recorded_paper_proxy_unverified_XQC",
            }
    return result | {"status": "censored_continuation", "reason": "no_exit_before_recording_ends"}


def identity(trade: dict, supplement: dict) -> dict:
    symbols = [supplement.get(k, "") for k in ("lower_symbol", "center_symbol", "upper_symbol")]
    decoded = [re.fullmatch(r"([A-Z]+)\s+(\d{6})([CP])(\d{8})", s) for s in symbols]
    if not all(decoded):
        return {"option_root": None, "expiration": None, "identity_verified": False}
    roots = {m[1] for m in decoded}
    expiries = {dt.datetime.strptime(m[2], "%y%m%d").date().isoformat() for m in decoded}
    direction = "P" if trade["direction"] == "PUT" else "C"
    strikes = [float(trade[k]) for k in ("lower_strike", "center_strike", "upper_strike")]
    ok = len(roots) == len(expiries) == 1 and all(
        m[3] == direction and int(m[4]) / 1000 == strike
        for m, strike in zip(decoded, strikes, strict=True)
    )
    expiry = next(iter(expiries)) if len(expiries) == 1 else None
    root = next(iter(roots)) if len(roots) == 1 else None
    if supplement.get("expirations"):
        ok = ok and supplement["expirations"] == expiry and supplement["roots"] == root
    return {"option_root": root, "expiration": expiry, "identity_verified": ok}


def coverage(
    trade: dict,
    path: list[Observation],
    audit: dict,
    supplement: dict,
    contract: dict,
    result: dict,
) -> dict:
    entry = timestamp(trade["entry_time"])
    exit_at = timestamp(trade["exit_time"])
    previous = entry
    gaps = []
    for obs in path:
        seconds = (obs.ts - previous).total_seconds()
        if seconds > contract["continuity_seconds"]:
            gaps.append(
                {
                    "start": previous.isoformat(),
                    "end": obs.ts.isoformat(),
                    "seconds": seconds,
                    "affected_decisions": (
                        "unobserved signals/peaks; confirmation reset at next complete observation"
                    ),
                }
            )
        previous = obs.ts
    lead = (path[0].ts - entry).total_seconds() if path else None
    tail = (exit_at - path[-1].ts).total_seconds() if path else None
    eligible = (
        bool(path)
        and 0 <= lead <= contract["first_delay_seconds"]
        and 0 <= tail <= contract["tail_seconds"]
    )
    ident = identity(trade, supplement)
    reasons = []
    if not path:
        reasons.append("no_complete_held_observations")
    elif not eligible:
        reasons.append("first_or_final_observation_outside_R0_coverage_window")
    if trade["fill_model"] != "mark_v1":
        reasons.append("heterogeneous_legacy_fill_model")
    if result["status"] not in ("exit", "settlement"):
        reasons.append(result["status"])
    if gaps:
        reasons.append("gaps_over_30s")
    if not ident["identity_verified"]:
        reasons.append("contract_identity_not_verified")
    if audit.get("incomplete", 0):
        reasons.append("incomplete_observations_excluded_from_replay")
    entry_diag = json.loads(trade["entry_diagnostics"] or "{}")
    payoff = settlement_payoff(trade)
    recorded_settlement = (
        optional(trade["exit_price"]) if trade["exit_reason"] == "cash_settled" else None
    )
    settlement_match = (
        abs(payoff - recorded_settlement) <= contract["mark_tolerance_points"]
        if payoff is not None and recorded_settlement is not None
        else None
    )
    can_replay = eligible and trade["fill_model"] == "mark_v1"
    # This stricter eligibility is predeclared in the contract. R0's broader
    # continuity sensitivity remains separately named, so its cohorts reproduce.
    complete_exit = (
        can_replay
        and not gaps
        and not audit.get("incomplete", 0)
        and ident["identity_verified"]
        and ident["option_root"] == "NDXP"
        and ident["expiration"] == trade["trade_date"]
        and result["status"] in ("exit", "settlement")
    )
    return {
        "id": int(trade["id"]),
        "session": trade["trade_date"],
        "timezone": "America/New_York",
        "instrument": "NDX",
        "direction": trade["direction"],
        **ident,
        "entry_time_utc": entry.isoformat(),
        "recorded_exit_time_utc": exit_at.isoformat(),
        "entry_observation": "selected_composite_diagnostic" if entry_diag else "not_exported",
        "entry_opportunity_set": False,
        "selected_entry_diagnostics_eligible": all(
            entry_diag.get(k) is not None for k in ("observed_mark", "observed_bid", "observed_ask")
        ),
        "grouped_observations": audit.get("rows", 0),
        "complete_observations": len(path),
        "incomplete_observations": audit.get("incomplete", 0),
        "composite_mark_mismatches": audit.get("mark_mismatches", 0),
        "first_observation_utc": path[0].ts.isoformat() if path else None,
        "last_observation_utc": path[-1].ts.isoformat() if path else None,
        "first_delay_seconds": lead,
        "tail_seconds": tail,
        "gaps_over_30s": len(gaps),
        "gap_seconds": sum(g["seconds"] for g in gaps),
        "max_gap_seconds": max((g["seconds"] for g in gaps), default=None),
        "gaps": gaps,
        "observation_timestamp": "monitor collection/evaluation ts; no exchange event time",
        "quote_event_time": None,
        "availability_time": None,
        "freshness_verified": False,
        "entry_decision_snapshot": bool(trade["entry_strategy"]),
        "post_exit_leg_rows_in_db": int(supplement["post_exit_leg_rows"])
        if supplement.get("post_exit_leg_rows")
        else None,
        "continuation_observations_in_snapshot": 0,
        "continuation_eligible": False,
        "continuation_exclusion": "extraction ends at actual exit; no independent quote path",
        "settlement_value": recorded_settlement,
        "settlement_spot": optional(trade["settlement_spot"]),
        "settlement_source": trade["settlement_source"] or None,
        "settlement_timestamp": supplement.get("settlement_spot_time") or None,
        "settlement_payoff_recomputed": payoff,
        "settlement_payoff_matches": settlement_match,
        "official_XQC_verified": False,
        "official_settlement_eligible": False,
        "paper_proxy_settlement_eligible": settlement_match is True and ident["identity_verified"],
        "R0_exit_analysis_eligible": can_replay,
        "R0_resolved": result["status"] in ("exit", "settlement"),
        "uninterrupted_exit_analysis_eligible": can_replay and not gaps,
        "strict_runtime_parity_eligible": False,
        "complete_observed_exit_replay_eligible": complete_exit,
        "complete_exit_replay_exclusions": []
        if complete_exit
        else (
            reasons + ["requires resolved mark_v1 NDXP path, no incomplete rows or gaps over 30s"]
        ),
        "exclusions": reasons,
    }


def metrics(values: list[float]) -> dict | None:
    if not values:
        return None
    running = high = drawdown = 0
    for value in values:
        running += value
        high = max(high, running)
        drawdown = max(drawdown, high - running)
    wins = [v for v in values if v > 0]
    losses = [v for v in values if v < 0]
    return {
        "n": len(values),
        "pnl": round(sum(values), 2),
        "expectancy": round(sum(values) / len(values), 2),
        "win_rate": len(wins) / len(values),
        "profit_factor": sum(wins) / -sum(losses) if losses else None,
        "max_close_drawdown": round(drawdown, 2),
        "top3_removed": round(sum(values) - sum(sorted(values)[-3:]), 2),
    }


def recorded_stress(trade: dict) -> tuple[float | None, bool]:
    entry = json.loads(trade["entry_diagnostics"] or "{}").get("marketable_entry_estimate")
    if entry is None:
        return None, False
    if trade["exit_reason"] == "cash_settled":
        price = optional(trade["exit_price"])
        floor = False
    else:
        price = json.loads(trade["exit_diagnostics"] or "{}").get("marketable_exit_estimate")
        floor = price is not None and price < 0
        if price is not None:
            price = max(0, price)
    return (pnl(price, entry, int(trade["quantity"])) if price is not None else None), floor


def event_accounting(trades: list[dict], events: list[dict], contract: dict) -> list[dict]:
    """Reconcile independent trade-exited events; diagnostic mark is a later read."""
    by_id = {int(t["id"]): t for t in trades}
    result = []
    for event in events:
        if event["event_type"] != "trade_exited":
            continue
        data = json.loads(event["data"])
        trade = by_id.get(data.get("trade_id"))
        if not trade or trade["fill_model"] != "mark_v1":
            continue
        mark = data.get("mark_at_signal")
        if mark is None:
            continue
        expected = round(mark - contract["commission_points_per_side"], 2)
        result.append(
            {
                "id": int(trade["id"]),
                "event_log_time": event["ts"],
                "mark_at_signal": mark,
                "separately_fetched_spread_mark": data.get("spread_mark"),
                "recorded_fill": float(trade["exit_price"]),
                "signal_based_fill": expected,
                "accounting_difference_points": round(float(trade["exit_price"]) - expected, 4),
                "event_fill_price": data.get("fill_price"),
                "meaning": "event log time is not quote-event time or order-time availability",
            }
        )
    return result


def reinitialization_audit(events: list[dict], trades: list[dict], paths: dict) -> list[dict]:
    """Attribute telemetry evidence without claiming an attested process restart."""
    by_id = {int(t["id"]): t for t in trades}
    result = []
    for event in events:
        data = json.loads(event["data"])
        tid = data.get("trade_id")
        if (
            event["event_type"] != "profit_state_transition"
            or data.get("from") is not None
            or tid not in by_id
        ):
            continue
        at = timestamp(event["ts"])
        later = [o.mark for o in paths.get(tid, []) if o.ts >= at]
        entry = float(by_id[tid]["entry_price"])
        result.append(
            {
                "id": tid,
                "event_time": event["ts"],
                "logged_from": None,
                "logged_to": data.get("to"),
                "logged_mark": data.get("mark_value"),
                "logged_peak": data.get("peak_value"),
                "entry": entry,
                "max_complete_mark_after_event": max(later) if later else None,
                "any_later_complete_mark_at_or_above_entry": any(m >= entry for m in later)
                if later
                else None,
                "interpretation": (
                    "monitor state reinitialization indicated; process cause unattested"
                ),
            }
        )
    return result


def jsonl(path: Path, records: list[dict]) -> None:
    with path.open("x") as stream:
        for record in records:
            stream.write(json.dumps(record, allow_nan=False) + "\n")


def run(
    evidence: Path,
    manifest: Path,
    config: Path,
    output: Path,
    supplement: Path | None = None,
    supplement_manifest: Path | None = None,
) -> dict:
    snapshot = verify(evidence, manifest)
    contract = read_json(config)
    if digest(manifest) != contract["snapshot_manifest_sha256"]:
        raise ValueError("unexpected snapshot manifest")
    for name in (
        "trades.csv",
        "paths.csv",
        "replay-trades.csv",
        "metrics.json",
        "events.csv",
        contract["policy_file"],
    ):
        if "raw/" + name not in snapshot["files"]:
            raise ValueError(f"unverified required input: {name}")
    if contract["model"] != "NDX-R0-baseline-approximation-v1":
        raise ValueError("unsupported replay model")
    for name, expected in contract["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"source drift: {name}; register a new contract and parent run")
    if bool(supplement) != bool(supplement_manifest):
        raise ValueError("supplement directory and manifest must be supplied together")
    if supplement:
        verify(supplement, supplement_manifest)
        if digest(supplement_manifest) != contract["supplement_manifest_sha256"]:
            raise ValueError("unexpected provenance supplement")
    new_directory(output, evidence, *([supplement] if supplement else []))
    # Persist the contract before numerical assessment, including fixed tolerances.
    write_json(output / "contract.json", contract)
    import yaml

    from butterfly_guy.core.config import ProfitManagementSettings
    from butterfly_guy.core.time_utils import is_trading_day

    raw = evidence / "raw"
    settings = ProfitManagementSettings(
        **yaml.safe_load((raw / contract["policy_file"]).read_text())["profit_management"]
    )
    write_json(output / "effective-profit-management.json", settings.model_dump())
    trades = rows(raw / "trades.csv")
    paths, counts = normalize(raw / "paths.csv", contract["mark_tolerance_points"])
    event_audit = event_accounting(trades, rows(raw / "events.csv"), contract)
    reset_audit = reinitialization_audit(
        rows(supplement / "trade-222-events.csv") if supplement else [], trades, paths
    )
    extra = {int(r["id"]): r for r in rows(supplement / "supplement.csv")} if supplement else {}
    results = [replay(t, paths.get(int(t["id"]), []), settings, contract) for t in trades]
    ledger = [
        coverage(
            t,
            paths.get(int(t["id"]), []),
            counts.get(int(t["id"]), {}),
            extra.get(int(t["id"]), {}),
            contract,
            r,
        )
        for t, r in zip(trades, results, strict=True)
    ]
    old = {int(r["id"]): r for r in rows(raw / "replay-trades.csv") if r["variant"] == "baseline"}
    reconciliation = []
    for t, r in zip(trades, results, strict=True):
        archived = old.get(int(t["id"]))
        differences = []
        if archived:
            for key in ("status", "reason", "pnl", "executable_pnl", "signal_time", "exit_time"):
                a, b = archived.get(key) or None, r.get(key)
                if key in ("pnl", "executable_pnl"):
                    same = (a is None and b is None) or (
                        a is not None
                        and b is not None
                        and abs(float(a) - b) <= contract["dollar_tolerance"]
                    )
                elif key.endswith("time"):
                    same = (a is None and b is None) or (
                        a is not None
                        and b is not None
                        and abs((timestamp(a) - timestamp(b)).total_seconds())
                        <= contract["timestamp_tolerance_seconds"]
                    )
                else:
                    same = a == b
                if not same:
                    differences.append({"field": key, "archived": a, "new": b})
        resolved = r["pnl"] is not None
        reconciliation.append(
            {
                "id": int(t["id"]),
                "session": t["trade_date"],
                "modern": r["modern"],
                "archived_baseline_available": archived is not None,
                "archived_differences": differences,
                "replay_status": r["status"],
                "recorded_reason": t["exit_reason"],
                "replayed_reason": r["reason"],
                "pnl_delta_dollars": round(r["pnl"] - float(t["pnl"]) * 100 * int(t["quantity"]), 2)
                if resolved
                else None,
                "exit_time_delta_seconds": (
                    timestamp(r["exit_time"]) - timestamp(t["exit_time"])
                ).total_seconds()
                if resolved
                else None,
            }
        )
    modern = [t for t in trades if t["fill_model"] == "mark_v1"]
    stress = [recorded_stress(t) for t in modern]
    historical = read_json(raw / "metrics.json")
    common_ids = set(historical["replay"]["modern"]["common_ids"])
    eligible_ids = {c["id"] for c in ledger if c["R0_exit_analysis_eligible"]}
    common = [r for r in results if r["id"] in common_ids & eligible_ids]
    summary = {
        "parent_study": contract["parent"],
        "model": contract["model"],
        "snapshot_id": snapshot["snapshot_id"],
        "trades": len(trades),
        "covered_trades": len(paths),
        "grouped_observations": sum(c["rows"] for c in counts.values()),
        "incomplete_observations": sum(c["incomplete"] for c in counts.values()),
        "complete_observations": sum(len(p) for p in paths.values()),
        "complete_mark_mismatches": sum(c["mark_mismatches"] for c in counts.values()),
        "recorded_all": metrics([float(t["pnl"]) * 100 * int(t["quantity"]) for t in trades]),
        "recorded_mark_v1": metrics([float(t["pnl"]) * 100 * int(t["quantity"]) for t in modern]),
        "stored_marketable_stress": metrics([p for p, _ in stress if p is not None]),
        "stored_stress_floor_count": sum(f for _, f in stress),
        "baseline_status_modern": dict(Counter(r["status"] for r in results if r["modern"])),
        "baseline_modern_resolved": metrics(
            [r["pnl"] for r in results if r["modern"] and r["pnl"] is not None]
        ),
        "historical_common_ids": sorted(common_ids),
        "historical_common_paper": metrics([r["pnl"] for r in common if r["pnl"] is not None]),
        "historical_common_stress": metrics(
            [r["executable_pnl"] for r in common if r["executable_pnl"] is not None]
        ),
        "historical_common_uninterrupted_n": sum(
            c["id"] in common_ids and c["uninterrupted_exit_analysis_eligible"] for c in ledger
        ),
        "baseline_stress_floor_count_modern": sum(
            r["stress_floor_applied"] for r in results if r["modern"]
        ),
        "historical_reproduction_differences": [
            r for r in reconciliation if r["archived_differences"]
        ],
        "modern_runtime_differences": [
            r
            for r in reconciliation
            if r["modern"]
            and r["pnl_delta_dollars"] is not None
            and (
                abs(r["pnl_delta_dollars"]) > contract["dollar_tolerance"]
                or r["recorded_reason"] != r["replayed_reason"]
            )
        ],
        "identity_verified_trades": sum(c["identity_verified"] for c in ledger),
        "eligibility_counts": {
            key: sum(c[key] for c in ledger)
            for key in (
                "R0_exit_analysis_eligible",
                "uninterrupted_exit_analysis_eligible",
                "continuation_eligible",
                "official_settlement_eligible",
                "paper_proxy_settlement_eligible",
                "complete_observed_exit_replay_eligible",
                "selected_entry_diagnostics_eligible",
            )
        },
        "settlement_payoff_mismatches": [
            c["id"] for c in ledger if c["settlement_payoff_matches"] is False
        ],
        "signal_fill_accounting": event_audit,
        "monitor_reinitialization_evidence": reset_audit,
        "qualifications": contract["qualifications"],
    }
    by_day = defaultdict(list)
    for c in ledger:
        by_day[c["session"]].append(c)
    sessions = []
    day = dt.date.fromisoformat(min(t["trade_date"] for t in trades))
    end = dt.date.fromisoformat(max(t["trade_date"] for t in trades))
    while day <= end:
        if is_trading_day(day):
            entries = by_day[day.isoformat()]
            sessions.append(
                {
                    "session": day.isoformat(),
                    "timezone": "America/New_York",
                    "instrument": "NDX",
                    "trade_ids": [c["id"] for c in entries],
                    "entry_opportunity_set_eligible": False,
                    "exit_analysis_trade_ids": [
                        c["id"] for c in entries if c["R0_exit_analysis_eligible"]
                    ],
                    "continuation_eligible": False,
                    "official_settlement_eligible": False,
                    "exclusions": sorted({e for c in entries for e in c["exclusions"]})
                    + [
                        "no_full_entry_opportunity_set",
                        "no_independent_continuation",
                        "no_official_XQC",
                    ]
                    + (
                        []
                        if entries
                        else ["no_trade_in_export; opportunity/skip evidence unavailable"]
                    ),
                }
            )
        day += dt.timedelta(days=1)
    jsonl(output / "coverage.jsonl", ledger)
    jsonl(output / "sessions.jsonl", sessions)
    jsonl(output / "baseline.jsonl", results)
    jsonl(output / "reconciliation.jsonl", reconciliation)
    jsonl(output / "event-accounting.jsonl", event_audit)
    jsonl(output / "reinitializations.jsonl", reset_audit)
    write_json(output / "summary.json", summary)
    (output / "report.md").write_text(
        "# NDX-01 offline baseline reproduction\n\n"
        f"Parent: {contract['parent']}. Snapshot: {snapshot['snapshot_id']}.\n\n"
        f"{len(trades)} trades; {summary['complete_observations']} complete observations; "
        f"{summary['incomplete_observations']} incomplete observations excluded.\n\n"
        f"Historical reproduction differences: "
        f"{len(summary['historical_reproduction_differences'])}. "
        f"Runtime price/reason differences in resolved mark_v1 paths: "
        f"{len(summary['modern_runtime_differences'])}; see reconciliation.jsonl.\n\n"
        "Eligibility is defined by contract.json before replay; coverage.jsonl contains "
        "every trade, sessions.jsonl every exchange weekday in the export range. "
        "Missing observations and censored results have null P&L.\n\n"
        + "\n".join("- " + q for q in contract["qualifications"])
        + "\n"
    )
    environment = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}
    source_dir = output / "runner-source"
    source_dir.mkdir()
    for module in ("ndx_baseline.py", "ndx_evidence.py"):
        shutil.copy2(Path(__file__).with_name(module), source_dir / module)
    command = [
        sys.executable,
        "-m",
        "butterfly_guy.research.ndx_baseline",
        "--evidence",
        str(evidence.resolve()),
        "--manifest",
        str(manifest.resolve()),
        "--config",
        str(config.resolve()),
        "--output",
        str(output.resolve()),
    ]
    if supplement:
        command.extend(
            [
                "--supplement",
                str(supplement.resolve()),
                "--supplement-manifest",
                str(supplement_manifest.resolve()),
            ]
        )
    write_json(
        output / "run.json",
        {
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "run_id": output.name,
            "parent": contract["parent"],
            "command": shlex.join(command),
            "reproduce": "replace --output with a NEW directory; input files must match hashes",
            "git_sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "git_status": subprocess.check_output(
                ["git", "status", "--short"], cwd=ROOT, text=True
            ),
            "python": sys.version,
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "dependencies": environment,
            "snapshot_manifest_sha256": digest(manifest),
            "config_sha256": digest(config),
            "supplement_manifest_sha256": digest(supplement_manifest) if supplement else None,
            "source_sha256": contract["source_sha256"],
            "output_sha256": {
                str(p.relative_to(output)): digest(p) for p in output.rglob("*") if p.is_file()
            },
        },
    )
    return summary


def main() -> None:
    import structlog

    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("evidence", "manifest", "config", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--supplement", type=Path)
    parser.add_argument("--supplement-manifest", type=Path)
    args = parser.parse_args()
    summary = run(**vars(args))
    print(json.dumps(summary, indent=2))
    if summary["historical_reproduction_differences"]:
        raise SystemExit("historical baseline differs; see reconciliation.jsonl")


if __name__ == "__main__":
    main()
