"""Offline NDX-02 accounting attribution; no replay, broker imports or experiments."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.metadata
import json
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, verify, write_json

ROOT = Path(__file__).resolve().parents[3]


def rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def at(value):
    if not value:
        return None
    parsed = dt.datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError("naive timestamp")
    return parsed.astimezone(dt.timezone.utc)


def seconds(left, right):
    return (at(left) - at(right)).total_seconds() if left and right else None


def unique(records, key):
    result = {}
    for row in records:
        value = int(row[key])
        if value in result:
            raise ValueError(f"duplicate {key}: {value}")
        result[value] = row
    return result


def cohort(trades, inventory, coverage, tolerance):
    """Membership is determined from closed records, never an expected count."""
    selected = [
        t
        for t in trades
        if t["fill_model"] == "mark_v1"
        and t["status"] == "CLOSED"
        and t["exit_reason"] != "cash_settled"
    ]
    actual, recovered = unique(selected, "id"), unique(inventory, "id")
    if actual.keys() != recovered.keys():
        raise ValueError("discretionary membership differs from NDX-01 inventory")
    covered = unique(coverage, "id")
    for tid, trade in actual.items():
        for row, date_key, time_key in [
            (recovered[tid], "trade_date", "exit_time"),
            (covered[tid], "session", "recorded_exit_time_utc"),
        ]:
            if (
                row[date_key] != trade["trade_date"]
                or abs(seconds(row[time_key], trade["exit_time"])) > tolerance
            ):
                raise ValueError(f"cohort identity/time mismatch: {tid}")
        if not covered[tid]["identity_verified"]:
            raise ValueError(f"unverified contract: {tid}")
    return set(actual)


def side_audit(trade, side, events, contract):
    """Independent arithmetic on recorded values, not OrderManager execution."""
    qty = int(trade["quantity"])
    fee = contract["contracts_per_fly"] * qty * contract["commission_per_contract_dollars"] / 100
    fill = float(trade[f"{side}_price"])
    diagnostic = json.loads(trade[f"{side}_diagnostics"] or "{}")
    settlement = side == "exit" and trade["exit_reason"] == "cash_settled"
    # Runtime embeds quantity-dependent commission in price; preserve, don't normalize it.
    sign = 1 if side == "entry" else -1
    event_name = "trade_entered" if side == "entry" else "trade_exited"
    logs = [e for e in events if e["event_type"] == event_name]
    if len(logs) > 1:
        raise ValueError(f"ambiguous {event_name}: {trade['id']}")
    event = logs[0]["payload"] if logs else {}
    mark = diagnostic.get("observed_mark") if side == "entry" else event.get("mark_at_signal")
    source = "entry_diagnostics.observed_mark" if side == "entry" else "trade_exited.mark_at_signal"
    if settlement:
        mark, source = None, None
    expected = round(mark + sign * fee, 2) if mark is not None else None
    market_key = f"marketable_{side}_estimate"
    stored = diagnostic.get(market_key)
    quote_key = "observed_ask" if side == "entry" else "observed_bid"
    quote = diagnostic.get(quote_key)
    fallback = quote is None and diagnostic.get("observed_mark") is not None and not settlement
    basis = quote if quote is not None else diagnostic.get("observed_mark")
    slippage = diagnostic.get("configured_slippage")
    recomputed = (
        round(basis + sign * (slippage + fee), 2)
        if basis is not None and slippage is not None and not settlement
        else None
    )
    raw_proceeds = stored if side == "exit" and not settlement else None
    stressed = (
        fill if settlement else max(0, stored) if side == "exit" and stored is not None else stored
    )
    price_tol = contract["tolerances"]["rounded_price_points"]
    difference = fill - expected if expected is not None else None
    estimate_difference = (
        stored - recomputed if stored is not None and recomputed is not None else None
    )
    drag = ((stressed - fill) * sign * 100 * qty) if stressed is not None else None
    spread = (
        diagnostic["observed_ask"] - diagnostic["observed_bid"]
        if diagnostic.get("observed_ask") is not None and diagnostic.get("observed_bid") is not None
        else None
    )
    diagnostic_mark = diagnostic.get("observed_mark")
    change = (
        diagnostic_mark - mark
        if diagnostic_mark is not None and mark is not None and side == "exit"
        else None
    )
    entry_fill_event_time = event.get("fill_time") if side == "entry" else None
    event_fill = event.get("cost" if side == "entry" else "fill_price")
    signal_logs = (
        [e["payload"].get("mark_value") for e in events if e["event_type"] == "exit_signal_fired"]
        if side == "exit"
        else []
    )
    raw_drag = (stored - fill) * sign if stored is not None else None
    stored_drag = diagnostic.get("estimated_execution_drag")
    return {
        "signal_mark": mark if side == "exit" else None,
        "signal_mark_source": source if mark is not None and side == "exit" else None,
        "fill_input_mark": mark,
        "fill_input_mark_source": source if mark is not None else None,
        "signal_observation_time": None,
        "signal_quote_event_time": None,
        "signal_collection_time": None,
        "signal_availability_time": None,
        "signal_mark_inferred_from_fill": False,
        "paper_fill_price": fill,
        "recorded_fill_time": trade[f"{side}_time"],
        "event_fill_price": event_fill,
        "event_fill_price_matches": abs(event_fill - fill) <= price_tol
        if event_fill is not None
        else None,
        "signal_event_marks": signal_logs,
        "signal_event_marks_match": (
            all(abs(v - mark) <= contract["tolerances"]["unrounded_points"] for v in signal_logs)
            if signal_logs and mark is not None
            else None
        ),
        "event_recorded_fill_time": entry_fill_event_time,
        "event_fill_time_matches": (
            abs(seconds(entry_fill_event_time, trade["entry_time"]))
            <= contract["tolerances"]["timestamp_seconds"]
            if entry_fill_event_time
            else None
        ),
        "embedded_commission_points": 0 if settlement else fee,
        "paper_fill_recomputed": expected,
        "paper_fill_difference_points": difference,
        "rounded_paper_cost_points": (fill - mark) * sign if mark is not None else None,
        "paper_fill_matches": abs(difference) <= price_tol if difference is not None else None,
        "diagnostic": diagnostic,
        "diagnostic_kind": (
            "supplied_mark_fallback_no_separate_quote"
            if fallback
            else "separately_fetched_leg_composite"
            if quote is not None
            else "missing"
        ),
        "diagnostic_quote_event_time": None,
        "diagnostic_collection_time": None,
        "diagnostic_availability_time": None,
        "diagnostic_spread_points": spread,
        "diagnostic_spread_to_mark": (
            spread / diagnostic_mark if spread is not None and diagnostic_mark else None
        ),
        "diagnostic_minus_signal_points": change,
        "diagnostic_paper_fill_counterfactual": (
            round(diagnostic_mark - fee, 2)
            if side == "exit" and diagnostic_mark is not None and not settlement
            else None
        ),
        "stored_marketable_estimate": stored,
        "estimate_basis": "cash_settlement"
        if settlement
        else "mark_fallback"
        if fallback
        else quote_key
        if quote is not None
        else "missing",
        "estimate_recomputed": recomputed,
        "estimate_difference_points": estimate_difference,
        "estimate_matches": abs(estimate_difference) <= price_tol
        if estimate_difference is not None
        else None,
        "raw_estimated_drag_points": raw_drag,
        "stored_drag_matches": (
            abs(stored_drag - round(max(0, raw_drag), 2)) <= price_tol
            if stored_drag is not None and raw_drag is not None
            else None
        ),
        "raw_negative_proceeds": raw_proceeds is not None and raw_proceeds < 0,
        "raw_negative_bid": diagnostic.get("observed_bid") is not None
        and diagnostic["observed_bid"] < 0,
        "stress_proceeds_floor_applied": raw_proceeds is not None and raw_proceeds < 0,
        "stress_floor_benefit_dollars": max(0, -raw_proceeds) * 100 * qty
        if raw_proceeds is not None
        else 0,
        "historical_stress_price": stressed,
        "stress_drag_dollars": drag,
        "telemetry_write_times": [
            {"event_type": e["event_type"], "ts": e["ts"]}
            for e in events
            if e["event_type"].startswith(side) or e["event_type"] == event_name
        ],
        "signal_to_fill_latency_seconds": None,
        "telemetry_minus_fill_seconds": [
            {"event_type": e["event_type"], "seconds": seconds(e["ts"], trade[f"{side}_time"])}
            for e in events
            if e["event_type"] == event_name
            or (side == "exit" and e["event_type"] == "exit_signal_fired")
        ],
    }


def ledger_row(trade, events, held, coverage, contract):
    entry, exit_ = [side_audit(trade, side, events, contract) for side in ("entry", "exit")]
    qty = int(trade["quantity"])
    paper = (float(trade["exit_price"]) - float(trade["entry_price"])) * 100 * qty
    recorded = float(trade["pnl"]) * 100 * qty  # DB pnl is points per fly, not dollars.
    stress = (
        (exit_["historical_stress_price"] - entry["historical_stress_price"]) * 100 * qty
        if all(s["historical_stress_price"] is not None for s in (entry, exit_))
        else None
    )
    return {
        "id": int(trade["id"]),
        "session": trade["trade_date"],
        "quantity": qty,
        "fill_model": trade["fill_model"],
        "exit_reason": trade["exit_reason"],
        "contract": {
            k: trade[k] for k in ("direction", "lower_strike", "center_strike", "upper_strike")
        },
        "entry": entry,
        "exit": exit_,
        "held_collection_evidence": held,
        "NDX01_identity_verified": coverage["identity_verified"],
        "recorded_paper_pnl_dollars": recorded,
        "paper_pnl_recomputed_dollars": paper,
        "paper_pnl_difference_dollars": paper - recorded,
        "paper_pnl_matches": abs(paper - recorded) <= contract["tolerances"]["dollars"],
        "historical_stored_stress_pnl_dollars": stress,
        "drag_identity_difference_dollars": (
            paper - stress - entry["stress_drag_dollars"] - exit_["stress_drag_dollars"]
            if stress is not None
            else None
        ),
        "entry_selection_observations": [
            attempt
            for e in events
            if e["event_type"] == "entry_ladder_trace"
            for attempt in e["payload"].get("entry_attempts", [])
        ],
        "telemetry": events,
        "actual_broker_fills": None,
        "settlement_source": trade.get("settlement_source") or None,
        "settlement_spot_time": coverage.get("settlement_timestamp"),
        "official_settlement_verified": False,
    }


def distribution(values):
    values = [v for v in values if v is not None]
    return (
        {
            "n": len(values),
            "sum": sum(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
        }
        if values
        else {"n": 0}
    )


def summarize(ledger, contract):
    return {
        "n": len(ledger),
        "ids": [r["id"] for r in ledger],
        "recorded_paper_pnl_dollars": sum(r["recorded_paper_pnl_dollars"] for r in ledger),
        "historical_stored_stress_pnl_dollars": sum(
            r["historical_stored_stress_pnl_dollars"]
            for r in ledger
            if r["historical_stored_stress_pnl_dollars"] is not None
        ),
        "stress_pnl_coverage": sum(
            r["historical_stored_stress_pnl_dollars"] is not None for r in ledger
        ),
        "paper_pnl_failures": [r["id"] for r in ledger if not r["paper_pnl_matches"]],
        "sides": {
            side: {
                "fill_checks": sum(r[side]["paper_fill_matches"] is not None for r in ledger),
                "fill_failures": [
                    r["id"] for r in ledger if r[side]["paper_fill_matches"] is False
                ],
                "estimate_checks": sum(r[side]["estimate_matches"] is not None for r in ledger),
                "estimate_failures": [
                    r["id"] for r in ledger if r[side]["estimate_matches"] is False
                ],
                "event_fill_price_failures": [
                    r["id"] for r in ledger if r[side]["event_fill_price_matches"] is False
                ],
                "signal_mark_event_failures": [
                    r["id"] for r in ledger if r[side]["signal_event_marks_match"] is False
                ],
                "stored_drag_failures": [
                    r["id"] for r in ledger if r[side]["stored_drag_matches"] is False
                ],
                "mark_fallback_ids": [
                    r["id"] for r in ledger if r[side]["estimate_basis"] == "mark_fallback"
                ],
                "negative_bid_ids": [r["id"] for r in ledger if r[side]["raw_negative_bid"]],
                "proceeds_floor_ids": [
                    r["id"] for r in ledger if r[side]["stress_proceeds_floor_applied"]
                ],
                "floor_benefit_dollars": sum(
                    r[side]["stress_floor_benefit_dollars"] for r in ledger
                ),
                "drag_dollars": distribution([r[side]["stress_drag_dollars"] for r in ledger]),
                "spread_points": distribution(
                    [r[side]["diagnostic_spread_points"] for r in ledger]
                ),
                "spread_to_mark": distribution(
                    [r[side]["diagnostic_spread_to_mark"] for r in ledger]
                ),
                "diagnostic_minus_signal_points": distribution(
                    [r[side]["diagnostic_minus_signal_points"] for r in ledger]
                ),
                "diagnostic_price_change_ids": [
                    r["id"]
                    for r in ledger
                    if r[side]["diagnostic_minus_signal_points"] is not None
                    and abs(r[side]["diagnostic_minus_signal_points"])
                    > contract["tolerances"]["unrounded_points"]
                ],
                "signal_observation_timestamp_coverage": 0,
                "diagnostic_collection_timestamp_coverage": 0,
                "quote_event_timestamp_coverage": 0,
                "availability_timestamp_coverage": 0,
                "recorded_fill_timestamp_coverage": sum(
                    bool(r[side]["recorded_fill_time"]) for r in ledger
                ),
                "event_fill_time_failures": [
                    r["id"] for r in ledger if r[side]["event_fill_time_matches"] is False
                ],
                "telemetry_offsets_seconds": {
                    typ: distribution(
                        [
                            offset["seconds"]
                            for r in ledger
                            for offset in r[side]["telemetry_minus_fill_seconds"]
                            if offset["event_type"] == typ
                        ]
                    )
                    for typ in (
                        ["trade_entered"]
                        if side == "entry"
                        else ["trade_exited", "exit_signal_fired"]
                    )
                },
                "signal_mark_coverage": sum(r[side]["signal_mark"] is not None for r in ledger),
                "selection_collection_time_trade_coverage": sum(
                    any(a.get("chain_fetched_at") for a in r["entry_selection_observations"])
                    for r in ledger
                )
                if side == "entry"
                else 0,
            }
            for side in ("entry", "exit")
        },
    }


def run(
    evidence,
    manifest,
    supplement,
    supplement_manifest,
    inventory,
    inventory_manifest,
    runtime_source,
    runtime_manifest,
    parent,
    config,
    source_lock,
    output,
    previous_run=None,
):
    contract = read_json(config)
    if contract["model"] != "NDX-02-execution-accounting-v1":
        raise ValueError("unsupported audit model")
    inputs = [
        (
            evidence,
            manifest,
            "snapshot.json",
            ("raw/trades.csv", "raw/events.csv", "raw/paths.csv"),
        ),
        (supplement, supplement_manifest, "supplement-manifest.json", ("supplement.csv",)),
        (inventory, inventory_manifest, "continuation-inventory-manifest.json", ("extract.csv",)),
        (
            runtime_source,
            runtime_manifest,
            "runtime-source-manifest.json",
            ("container-source.tar.gz",),
        ),
    ]
    for root, record, key, required in inputs:
        verified = verify(root, record)
        if digest(record) != contract["manifest_sha256"][key]:
            raise ValueError(f"unexpected manifest: {key}")
        if not set(required).issubset(verified["files"]):
            raise ValueError(f"unverified required input: {key}")
    lock = read_json(source_lock)
    if lock["config_sha256"] != digest(config):
        raise ValueError("source lock/config mismatch")
    for name, expected in (contract["source_sha256"] | lock["source_sha256"]).items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"source drift: {name}; new contract/run and parent required")
    if digest(parent / "run.json") != contract["parent_run_sha256"]:
        raise ValueError("parent run mismatch")
    prior = read_json(parent / "run.json")
    # Parent uses output_sha256 rather than files; reuse the same safe path verifier below.
    for name, expected in prior["output_sha256"].items():
        path = (parent / name).resolve()
        if not path.is_relative_to(parent.resolve()) or digest(path) != expected:
            raise ValueError(f"parent output mismatch: {name}")
    if bool(previous_run) != bool(contract.get("correction_parent_sha256")):
        raise ValueError("correction requires explicit previous run and parent hash")
    if previous_run and digest(previous_run / "run.json") != contract["correction_parent_sha256"]:
        raise ValueError("correction parent mismatch")
    new_directory(
        output,
        evidence,
        supplement,
        inventory,
        runtime_source,
        parent,
        *([previous_run] if previous_run else []),
    )
    write_json(output / "contract.json", contract)
    write_json(output / "source-lock.json", lock)
    coverage = unique(
        [json.loads(line) for line in (parent / "coverage.jsonl").read_text().splitlines()], "id"
    )
    trades = rows(evidence / "raw/trades.csv")
    selected = cohort(
        trades,
        rows(inventory / "extract.csv"),
        list(coverage.values()),
        contract["tolerances"]["timestamp_seconds"],
    )
    modern = [t for t in trades if t["fill_model"] == "mark_v1" and t["status"] == "CLOSED"]
    provenance = unique(rows(supplement / "supplement.csv"), "id")
    events = defaultdict(list)
    for row in rows(evidence / "raw/events.csv"):
        payload = json.loads(row["data"])
        if payload.get("trade_id") is not None:
            events[int(payload["trade_id"])].append(
                {"event_type": row["event_type"], "ts": row["ts"], "payload": payload}
            )
    held = defaultdict(
        lambda: {
            "complete_count": 0,
            "incomplete_count": 0,
            "first_collection_time": None,
            "last_collection_time": None,
            "last_complete_mark": None,
            "meaning": "Held monitor collection/evaluation, not identified signal time",
        }
    )
    with (evidence / "raw/paths.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            tid = int(row["trade_id"])
            if tid not in coverage:
                raise ValueError("unknown held trade")
            h = held[tid]
            if row["legs"] != "3" or row["invalid_legs"] != "0":
                h["incomplete_count"] += 1
                continue
            h["complete_count"] += 1
            if h["first_collection_time"] is None or at(row["ts"]) < at(h["first_collection_time"]):
                h["first_collection_time"] = row["ts"]
            if h["last_collection_time"] is None or at(row["ts"]) > at(h["last_collection_time"]):
                h["last_collection_time"], h["last_complete_mark"] = (
                    row["ts"],
                    float(row["raw_mark"]),
                )
    ledger = []
    for trade in modern:
        tid = int(trade["id"])
        row = ledger_row(trade, events[tid], held[tid], coverage[tid], contract)
        row["in_discretionary_cohort"] = tid in selected
        row["symbol_identity"] = {
            k: provenance.get(tid, {}).get(k)
            for k in ("lower_symbol", "center_symbol", "upper_symbol", "roots", "expirations")
        }
        row["held_collection_evidence"]["last_collection_to_fill_seconds"] = seconds(
            trade["exit_time"], held[tid]["last_collection_time"]
        )
        ledger.append(row)
    discretionary = [r for r in ledger if r["in_discretionary_cohort"]]
    summary = {
        "model": contract["model"],
        "parent": contract["parent"],
        "discretionary": summarize(discretionary, contract),
        "all_modern_context": summarize(ledger, contract),
    }
    for name, records in [
        ("execution-ledger.jsonl", discretionary),
        ("modern-context.jsonl", ledger),
    ]:
        with (output / name).open("x") as stream:
            for row in records:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
    write_json(output / "summary.json", summary)
    source_dir = output / "runner-source"
    source_dir.mkdir()
    for name in lock["source_sha256"]:
        shutil.copy2(ROOT / name, source_dir / Path(name).name)
    arguments = locals()
    keys = [
        "evidence",
        "manifest",
        "supplement",
        "supplement_manifest",
        "inventory",
        "inventory_manifest",
        "runtime_source",
        "runtime_manifest",
        "parent",
        "config",
        "source_lock",
        "output",
    ]
    command = [sys.executable, "-m", "butterfly_guy.research.ndx_execution_audit"]
    for key in keys:
        command.extend(["--" + key.replace("_", "-"), str(arguments[key].resolve())])
    if previous_run:
        command.extend(["--previous-run", str(previous_run.resolve())])
    write_json(
        output / "run.json",
        {
            "run_id": output.name,
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "parent": contract["parent"],
            "parent_run_sha256": digest(parent / "run.json"),
            "command": shlex.join(command),
            "config_sha256": digest(config),
            "source_lock_sha256": digest(source_lock),
            "inputs": {
                str(record.resolve()): {
                    "sha256": digest(record),
                    "root": str(root.resolve()),
                    "files": read_json(record)["files"],
                }
                for root, record, _, _ in inputs
            },
            "source_sha256": contract["source_sha256"] | lock["source_sha256"],
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
            "correction_parent": (
                {
                    "path": str(previous_run.resolve()),
                    "run_sha256": digest(previous_run / "run.json"),
                }
                if previous_run
                else None
            ),
            "dependencies": {
                d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
            },
            "output_sha256": {
                str(p.relative_to(output)): digest(p) for p in output.rglob("*") if p.is_file()
            },
        },
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in (
        "evidence",
        "manifest",
        "supplement",
        "supplement-manifest",
        "inventory",
        "inventory-manifest",
        "runtime-source",
        "runtime-manifest",
        "parent",
        "config",
        "source-lock",
        "output",
    ):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--previous-run", type=Path)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))


if __name__ == "__main__":
    main()
