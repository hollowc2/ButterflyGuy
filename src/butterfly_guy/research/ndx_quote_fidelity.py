"""Offline constituent fidelity attribution. No economic replay or broker imports."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.metadata
import json
import platform
import shlex
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from butterfly_guy.research.ndx_continuation import ROOT, at, audit, stats, verify_parent
from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, verify, write_json
from butterfly_guy.research.ndx_execution_audit import cohort, rows


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def decimal(value):
    if value is None:
        return None
    result = Decimal(str(value))
    return result if result.is_finite() else None


def leg_record(quote, weight, meta, snapshot, tolerance, rounding_bound):
    """Keep missing and invalid distinct; calculations never repair a quote."""
    bid, ask, mark = [decimal(quote.get(k)) for k in ("bid", "ask", "mark")]
    known = all(v is not None for v in (bid, ask, mark))
    sane = known and min(bid, ask, mark) >= 0 and bid <= ask
    midpoint = (bid + ask) / 2 if bid is not None and ask is not None else None
    delta = mark - midpoint if mark is not None and midpoint is not None else None
    outside = mark < bid - tolerance or mark > ask + tolerance if known else None
    event = at(quote["quote_event_ts"]) if quote.get("quote_event_ts") else None
    done = at(meta["chain_fetch_completed_at"]) if meta.get("chain_fetch_completed_at") else None
    age = decimal(quote.get("quote_age_s"))
    return {
        "symbol": quote.get("symbol"),
        "root": (quote.get("symbol") or "").split()[0] if quote.get("symbol") else None,
        "expiration": quote.get("expiration"),
        "option_type": quote.get("option_type"),
        "strike": quote.get("strike"),
        "weight": weight,
        "bid": str(bid) if bid is not None else None,
        "ask": str(ask) if ask is not None else None,
        "provider_mark": str(mark) if mark is not None else None,
        "midpoint": str(midpoint) if midpoint is not None else None,
        "mark_minus_midpoint": str(delta) if delta is not None else None,
        "weighted_mark_minus_midpoint": str(weight * delta) if delta is not None else None,
        "price_sanity": "recorded_nonnegative_uncrossed"
        if sane
        else "invalid"
        if known
        else "unknown",
        "mark_outside_own_market": bool(outside) if outside is not None else None,
        "midpoint_difference_reportable": abs(delta) > tolerance if delta is not None else None,
        "compatible_with_half_cent_midpoint_rounding": abs(delta) <= rounding_bound
        if delta is not None
        else None,
        "quote_event_ts": quote.get("quote_event_ts"),
        "quote_age_s": quote.get("quote_age_s"),
        "bid_size": quote.get("bid_size"),
        "ask_size": quote.get("ask_size"),
        "recorded_auxiliary_fields": {
            k: quote.get(k) for k in ("last", "theoretical_value", "intrinsic_value", "time_value")
        },
        "event_after_pass_start_seconds": (event - at(snapshot)).total_seconds() if event else None,
        "event_to_local_fetch_completion_seconds": (done - event).total_seconds()
        if done and event
        else None,
        "reported_age_minus_completion_event_delta_seconds": float(age)
        - (done - event).total_seconds()
        if age is not None and done and event
        else None,
        "age_reference_clock": "unattested_historical_reference",
        "timing_coverage": "event_and_age"
        if event and age is not None
        else "partial"
        if event or age is not None
        else "unknown",
        "consumer_availability_time": None,
    }


def attribute(spec, observation, raw, contract):
    tol = Decimal(contract["reporting_tolerance_points"])
    bound = Decimal(contract["rounding_compatibility_bound_points"])
    meta = observation["snapshot_metadata"] or {}
    legs = []
    for symbol, weight in zip(spec["symbols"], [1, -2, 1]):
        row = next(r for r in raw if json.loads(r["raw_quote"])["symbol"] == symbol)
        quote = json.loads(row["raw_quote"])
        leg = leg_record(quote, weight, meta, observation["snapshot_time"], tol, bound)
        leg.update(
            id=spec["id"],
            session=spec["session"],
            snapshot_time=observation["snapshot_time"],
            raw_csv_record=row["_record"],
            raw_quote_json=row["raw_quote"],
            raw_meta_json=row["raw_meta"],
            structural_category="complete",
            R0_30_second_continuation_eligible=False,
            minute_replay_eligible=False,
        )
        legs.append(leg)
    mark = sum(Decimal(q["provider_mark"]) * q["weight"] for q in legs)
    bid = sum(Decimal(q["bid"] if q["weight"] > 0 else q["ask"]) * q["weight"] for q in legs)
    ask = sum(Decimal(q["ask"] if q["weight"] > 0 else q["bid"]) * q["weight"] for q in legs)
    midpoint = (bid + ask) / 2
    delta = mark - midpoint
    # Independent identity: composite discrepancy equals weighted constituent discrepancies.
    if delta != sum(Decimal(q["weighted_mark_minus_midpoint"]) for q in legs):
        raise ValueError("constituent arithmetic identity failed")
    for key, value in [
        ("provider_composite_mark", mark),
        ("raw_composite_bid", bid),
        ("raw_composite_ask", ask),
        ("mark_minus_composite_midpoint", delta),
    ]:
        if abs(value - Decimal(str(observation[key]))) > tol:
            raise ValueError("parent arithmetic mismatch")
    events = [at(q["quote_event_ts"]) for q in legs if q["quote_event_ts"]]
    ages = [q["quote_age_s"] for q in legs if q["quote_age_s"] is not None]
    coverage = (
        "all"
        if all(q["timing_coverage"] == "event_and_age" for q in legs)
        else ("partial" if any(q["timing_coverage"] != "unknown" for q in legs) else "unknown")
    )
    flags = {
        "negative_mark": mark < -tol,
        "negative_bid": bid < -tol,
        "midpoint_difference": abs(delta) > tol,
        "any_leg_outside_market": any(q["mark_outside_own_market"] for q in legs),
        "any_leg_midpoint_difference": any(q["midpoint_difference_reportable"] for q in legs),
    }
    record = {
        "id": spec["id"],
        "session": spec["session"],
        "symbols": spec["symbols"],
        "direction": spec["direction"],
        "strikes": spec["strikes"],
        "wing_widths": [
            str(Decimal(str(b)) - Decimal(str(a)))
            for a, b in zip(spec["strikes"], spec["strikes"][1:])
        ],
        "snapshot_time": observation["snapshot_time"],
        "structural_category": "complete",
        "price_sanity": "recorded_nonnegative_uncrossed_legs",
        "timing_coverage": coverage,
        "provider_composite_mark": str(mark),
        "raw_composite_bid": str(bid),
        "raw_composite_ask": str(ask),
        "composite_midpoint": str(midpoint),
        "mark_minus_composite_midpoint": str(delta),
        "signed_negative_mark": str(mark) if flags["negative_mark"] else None,
        "flags": flags,
        "overlap_mask": "|".join(k for k, v in flags.items() if v) or "none",
        "event_time_dispersion_seconds": (max(events) - min(events)).total_seconds()
        if len(events) == 3
        else None,
        "known_event_time_dispersion_seconds": (max(events) - min(events)).total_seconds()
        if len(events) >= 2
        else None,
        "known_event_count": len(events),
        "known_age_count": len(ages),
        "youngest_reported_age_seconds": min(ages) if ages else None,
        "oldest_reported_age_seconds": max(ages) if ages else None,
        "snapshot_metadata": observation["snapshot_metadata"],
        "attribution": {
            "negative_mark": "center_mark_times_two_exceeds_wing_marks"
            if flags["negative_mark"]
            else "not_negative_at_reporting_tolerance",
            "midpoint_difference": "weighted_recorded_leg_mark_midpoint_residuals",
            "rounding": "all_legs_compatible_with_half_cent_bound"
            if all(q["compatible_with_half_cent_midpoint_rounding"] for q in legs)
            else "some_leg_residual_exceeds_half_cent_bound",
            "historical_root_cause": "unresolved_without_payload_and_deployment_attestation",
        },
        "raw_csv_records": [q["raw_csv_record"] for q in legs],
        "consumer_availability_time": None,
        "freshness_verified": False,
        "R0_30_second_continuation_eligible": False,
        "minute_replay_eligible": False,
    }
    return record, legs


def aggregate(records):
    return {
        "observations": len(records),
        "legs": 3 * len(records),
        "flags": {
            k: sum(r["flags"][k] for r in records)
            for k in (
                "negative_mark",
                "negative_bid",
                "midpoint_difference",
                "any_leg_outside_market",
                "any_leg_midpoint_difference",
            )
        },
        "negative_mark_and_midpoint_difference": sum(
            r["flags"]["negative_mark"] and r["flags"]["midpoint_difference"] for r in records
        ),
        "overlap_masks": dict(Counter(r["overlap_mask"] for r in records)),
        "timing_coverage": dict(Counter(r["timing_coverage"] for r in records)),
    }


def analyze(specs, normalized, rejected, raw, contract):
    grouped = defaultdict(list)
    for i, row in enumerate(raw, 1):
        row = dict(row, _record=i)
        q = json.loads(row["raw_quote"])
        grouped[int(row["trade_id"]), at(q["snapshot_time"])].append(row)
    by_id = {s["id"]: s for s in specs}
    observations, legs, exclusions = [], [], []
    for obs in normalized:
        record, detail = attribute(
            by_id[obs["id"]], obs, grouped[obs["id"], at(obs["snapshot_time"])], contract
        )
        observations.append(record)
        legs.extend(detail)
    for excluded in rejected:
        raw_group = grouped[excluded["id"], at(excluded["snapshot_time"])]
        exclusions.append(
            excluded
            | {
                "raw_csv_records": [r["_record"] for r in raw_group],
                "minute_replay_eligible": False,
            }
        )
        spec = by_id[excluded["id"]]
        for row in raw_group:
            q = json.loads(row["raw_quote"])
            weight = (
                [1, -2, 1][spec["symbols"].index(q["symbol"])]
                if q["symbol"] in spec["symbols"]
                else 0
            )
            detail = leg_record(
                q,
                weight,
                json.loads(row["raw_meta"]) if row["raw_meta"] else {},
                excluded["snapshot_time"],
                Decimal(contract["reporting_tolerance_points"]),
                Decimal(contract["rounding_compatibility_bound_points"]),
            )
            legs.append(
                detail
                | {
                    "id": spec["id"],
                    "session": spec["session"],
                    "snapshot_time": excluded["snapshot_time"],
                    "structural_category": "excluded",
                    "reasons": excluded["reasons"],
                    "raw_csv_record": row["_record"],
                    "raw_quote_json": row["raw_quote"],
                    "raw_meta_json": row["raw_meta"],
                    "minute_replay_eligible": False,
                    "R0_30_second_continuation_eligible": False,
                }
            )
    breakdown = []
    for dimension in ["id", "session", "timing_coverage"]:
        for value in sorted({r[dimension] for r in observations}):
            breakdown.append(
                {"dimension": dimension, "value": value}
                | aggregate([r for r in observations if r[dimension] == value])
            )
    summary = aggregate(observations) | {
        "trades": len(specs),
        "raw_leg_rows": len(raw),
        "excluded_groups": len(exclusions),
        "excluded_by_trade": dict(Counter(r["id"] for r in exclusions)),
        "leg_market_outside_count_complete": sum(
            q["mark_outside_own_market"] is True
            for q in legs
            if q["structural_category"] == "complete"
        ),
        "complete_leg_residuals": stats(
            [
                float(q["mark_minus_midpoint"])
                for q in legs
                if q["structural_category"] == "complete"
            ]
        ),
        "complete_leg_residuals_exceed_half_cent": sum(
            q["compatible_with_half_cent_midpoint_rounding"] is False
            for q in legs
            if q["structural_category"] == "complete"
        ),
        "timing": {
            k: stats([r[k] for r in observations if r[k] is not None])
            for k in (
                "event_time_dispersion_seconds",
                "youngest_reported_age_seconds",
                "oldest_reported_age_seconds",
            )
        },
        "leg_timing": {
            k: stats(
                [q[k] for q in legs if q["structural_category"] == "complete" and q[k] is not None]
            )
            for k in (
                "event_to_local_fetch_completion_seconds",
                "reported_age_minus_completion_event_delta_seconds",
            )
        },
        "leg_counts_complete": {
            k: sum(q[k] is True for q in legs if q["structural_category"] == "complete")
            for k in ("mark_outside_own_market", "midpoint_difference_reportable")
        },
        "metadata_field_coverage": {
            k: sum((r["snapshot_metadata"] or {}).get(k) is not None for r in observations)
            for k in (
                "chain_source",
                "chain_flags",
                "scheduled_at",
                "chain_fetch_started_at",
                "chain_fetch_completed_at",
                "chain_gateway_received_at",
                "chain_event_ts",
                "chain_age_s",
            )
        },
        "event_after_pass_start_count": sum(
            q["event_after_pass_start_seconds"] is not None
            and q["event_after_pass_start_seconds"]
            > contract["timestamp_equality_tolerance_seconds"]
            for q in legs
            if q["structural_category"] == "complete"
        ),
        "event_after_local_completion_count": sum(
            q["event_to_local_fetch_completion_seconds"] is not None
            and q["event_to_local_fetch_completion_seconds"]
            < -contract["timestamp_equality_tolerance_seconds"]
            for q in legs
            if q["structural_category"] == "complete"
        ),
        "consumer_availability_known": 0,
        "R0_eligible_trades": 0,
        "minute_replay_eligible_trades": 0,
    }
    negative = [r for r in observations if r["flags"]["negative_mark"]]
    timed = [r for r in observations if r["timing_coverage"] == "all"]
    selections = [
        (
            "most_negative",
            min(negative, key=lambda r: Decimal(r["provider_composite_mark"]))
            if negative
            else None,
        ),
        (
            "near_zero_negative",
            max(negative, key=lambda r: Decimal(r["provider_composite_mark"]))
            if negative
            else None,
        ),
        (
            "largest_midpoint_difference",
            max(observations, key=lambda r: abs(Decimal(r["mark_minus_composite_midpoint"])))
            if observations
            else None,
        ),
        (
            "largest_timed_difference",
            max(timed, key=lambda r: abs(Decimal(r["mark_minus_composite_midpoint"])))
            if timed
            else None,
        ),
        (
            "largest_event_dispersion",
            max(timed, key=lambda r: r["event_time_dispersion_seconds"]) if timed else None,
        ),
        (
            "oldest_reported_leg",
            max(timed, key=lambda r: r["oldest_reported_age_seconds"]) if timed else None,
        ),
    ]
    examples = [
        {
            "selection": name,
            "observation": r,
            "legs": [q for q in legs if q["raw_csv_record"] in r["raw_csv_records"]],
        }
        for name, r in selections
        if r is not None
    ]
    return observations, legs, exclusions, breakdown, examples, summary


def run(
    evidence_root,
    manifest,
    continuation_parent,
    execution_parent,
    baseline_parent,
    config,
    source_lock,
    output,
):
    contract, lock = read_json(config), read_json(source_lock)
    if contract["model"] != "NDX-02-constituent-fidelity-v1":
        raise ValueError("unsupported fidelity contract")
    if lock["config_sha256"] != digest(config) or lock["manifest_sha256"] != digest(manifest):
        raise ValueError("source lock/config/manifest mismatch")
    snapshots = {}
    for key, binding in contract["inputs"].items():
        record_path = manifest if key == "continuation" else ROOT / binding["manifest"]
        if digest(record_path) != binding["manifest_sha256"]:
            raise ValueError("manifest identity mismatch")
        verified = verify(evidence_root / binding["root"], record_path)
        if not set(binding["required"]) <= verified["files"].keys():
            raise ValueError("unverified required input")
        snapshots[key] = {"manifest_sha256": digest(record_path), "files": verified["files"]}
    parents = {
        "continuation": continuation_parent,
        "execution": execution_parent,
        "baseline": baseline_parent,
    }
    for key, path in parents.items():
        verify_parent(path, contract["parents"][key]["run_sha256"])
        for name, expected in read_json(path / "run.json")["source_sha256"].items():
            if digest(ROOT / name) != expected:
                raise ValueError(f"parent source drift: {name}")
    for name, expected in lock["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"source drift: {name}")
    evidence = evidence_root / contract["inputs"]["continuation"]["root"]
    specs = read_json(evidence / "cohort.json")
    prior = lines(execution_parent / "execution-ledger.jsonl")
    if len({s["id"] for s in specs}) != len(specs) or {s["id"] for s in specs} != {
        r["id"] for r in prior
    }:
        raise ValueError("execution cohort mismatch")
    with (evidence / "prices/extract.csv").open(newline="") as stream:
        raw = list(csv.DictReader(stream))
    inventory = evidence_root / contract["inputs"]["inventory"]["root"]
    with (inventory / "extract.csv").open(newline="") as stream:
        inv = list(csv.DictReader(stream))
    selected = cohort(
        rows(evidence_root / contract["inputs"]["r0"]["root"] / "raw/trades.csv"),
        inv,
        lines(baseline_parent / "coverage.jsonl"),
        contract["timestamp_equality_tolerance_seconds"],
    )
    if selected != {s["id"] for s in specs}:
        raise ValueError("record-derived cohort mismatch")
    normalized, rejected, coverage, previous_summary = audit(
        specs, raw, inv, read_json(evidence / "contract.json")
    )
    if (
        normalized != lines(continuation_parent / "observations.jsonl")
        or rejected != lines(continuation_parent / "rejected-groups.jsonl")
        or previous_summary != read_json(continuation_parent / "summary.json")
    ):
        raise ValueError("raw/continuation parent reconciliation failed")
    if any(not r["inventory_matches"] for r in coverage):
        raise ValueError("inventory mismatch")
    results = analyze(specs, normalized, rejected, raw, contract)
    new_directory(output, evidence_root, *parents.values())
    for name, records in zip(
        ["observations", "legs", "exclusions", "breakdown", "examples"], results[:-1]
    ):
        with (output / f"{name}.jsonl").open("x") as stream:
            for row in records:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
    write_json(output / "summary.json", results[-1])
    write_json(output / "contract.json", contract)
    write_json(output / "source-lock.json", lock)
    source = output / "source"
    for name in lock["source_sha256"]:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    args = locals()
    command = [sys.executable, "-m", "butterfly_guy.research.ndx_quote_fidelity"]
    for key in [
        "evidence_root",
        "manifest",
        "continuation_parent",
        "execution_parent",
        "baseline_parent",
        "config",
        "source_lock",
        "output",
    ]:
        command.extend(["--" + key.replace("_", "-"), str(args[key].resolve())])
    write_json(
        output / "run.json",
        {
            "model": contract["model"],
            "run_id": str(output),
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "command": shlex.join(command),
            "config_sha256": digest(config),
            "source_lock_sha256": digest(source_lock),
            "inputs": snapshots,
            "parent_hashes": {k: digest(p / "run.json") for k, p in parents.items()},
            "source_sha256": lock["source_sha256"],
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
            "dependencies": {
                d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
            },
            "output_sha256": {
                str(p.relative_to(output)): digest(p) for p in output.rglob("*") if p.is_file()
            },
        },
    )
    return results[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in [
        "evidence-root",
        "manifest",
        "continuation-parent",
        "execution-parent",
        "baseline-parent",
        "config",
        "source-lock",
        "output",
    ]:
        parser.add_argument("--" + key, type=Path, required=True)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))


if __name__ == "__main__":
    main()
