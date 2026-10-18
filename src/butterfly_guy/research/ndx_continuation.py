"""Offline import/quality audit of independent NDX minute continuations; no replay."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.metadata
import json
import math
import platform
import re
import shlex
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, verify, write_json

ROOT = Path(__file__).resolve().parents[3]


def at(value):
    parsed = dt.datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError("naive timestamp")
    return parsed.astimezone(dt.timezone.utc)


def number(value):
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def stats(values):
    values = sorted(values)
    return (
        {
            "n": len(values),
            "min": values[0],
            "median": statistics.median(values),
            "p95_nearest_rank": values[math.ceil(len(values) * 0.95) - 1],
            "max": values[-1],
        }
        if values
        else {"n": 0}
    )


def normalize_group(spec, timestamp, raw, contract):
    """Validate the original three legs without repairing or clipping prices."""
    reasons = []
    quotes = [r["quote"] for r in raw]
    symbols = [q.get("symbol") for q in quotes]
    if len(symbols) != len(set(symbols)):
        reasons.append("duplicate_symbol_key")
    if len(quotes) != 3 or set(symbols) != set(spec["symbols"]):
        reasons.append("incomplete_or_unexpected_symbols")
    if not at(spec["exit_time"]) < timestamp <= at(spec["close_time"]):
        reasons.append("outside_exit_close_window")
    for q in quotes:
        symbol = q.get("symbol", "")
        match = re.fullmatch(r"([A-Z]+)\s+(\d{6})([CP])(\d{8})", symbol)
        if (
            not match
            or match[1] != contract["root"]
            or match[2] != at(spec["exit_time"]).strftime("%y%m%d")
            or match[3] != spec["direction"][0]
        ):
            reasons.append("wrong_contract_symbol_identity")
        if (
            q.get("underlying") != "NDX"
            or q.get("expiration") != spec["session"]
            or q.get("option_type") != spec["direction"]
        ):
            reasons.append("wrong_underlying_expiration_or_type")
        if symbol in spec["symbols"]:
            expected = float(spec["strikes"][spec["symbols"].index(symbol)])
            if number(q.get("strike")) != expected or (match and int(match[4]) / 1000 != expected):
                reasons.append("wrong_strike")
        prices = [number(q.get(k)) for k in ("bid", "ask", "mark")]
        if any(p is None for p in prices):
            reasons.append("missing_or_nonfinite_price")
        elif min(prices) < 0 or prices[0] > prices[1]:
            reasons.append("negative_or_crossed_leg_quote")
    metas = {json.dumps(r["meta"], sort_keys=True) for r in raw}
    if len(metas) > 1:
        reasons.append("inconsistent_snapshot_metadata")
    record = {
        "id": spec["id"],
        "snapshot_time": timestamp.isoformat(),
        "leg_rows": len(quotes),
        "reasons": sorted(set(reasons)),
        "eligible": not reasons,
    }
    if reasons:
        return record
    ordered = [next(q for q in quotes if q["symbol"] == s) for s in spec["symbols"]]
    lo, ce, up = ordered
    mark = sum(number(q["mark"]) * weight for q, weight in zip(ordered, [1, -2, 1]))
    bid = number(lo["bid"]) - 2 * number(ce["ask"]) + number(up["bid"])
    ask = number(lo["ask"]) - 2 * number(ce["bid"]) + number(up["ask"])
    width = float(spec["strikes"][1]) - float(spec["strikes"][0])
    tol = contract["negative_composite_tolerance_points"]
    return record | {
        "provider_composite_mark": round(mark, 8),
        "raw_composite_bid": round(bid, 8),
        "raw_composite_ask": round(ask, 8),
        "composite_spread": round(ask - bid, 8),
        "mark_minus_composite_midpoint": round(mark - (bid + ask) / 2, 8),
        "negative_composite_bid": bid < -tol,
        "negative_composite_mark": mark < -tol,
        "mark_above_width": mark > width + tol,
        "crossed_composite": bid > ask + tol,
        "provider_mark_outside_composite_market": mark < bid - tol or mark > ask + tol,
        "legs": ordered,
        "snapshot_metadata": raw[0]["meta"],
        "availability_time": None,
        "freshness_verified": False,
        "R0_30_second_continuation_eligible": False,
        "minute_replay_eligible": False,
    }


def historical_inventory_group(spec, raw):
    """Reproduce the inventory's weaker SQL predicate separately from normalization."""
    if len(raw) != 3 or len({r["quote"].get("strike") for r in raw}) != 3:
        return False
    for r in raw:
        q = r["quote"]
        bid, ask = number(q.get("bid")), number(q.get("ask"))
        if (
            q.get("expiration") != spec["session"]
            or q.get("option_type") != spec["direction"]
            or bid is None
            or ask is None
            or bid < 0
            or ask < bid
            or q.get("mark") is None
        ):
            return False
    return True


def cadence(spec, times, thresholds):
    times = sorted(times)
    start, end = at(spec["exit_time"]), at(spec["close_time"])
    pairs = [
        {"previous": a.isoformat(), "current": b.isoformat(), "seconds": (b - a).total_seconds()}
        for a, b in zip(times, times[1:])
    ]
    bucket = start.replace(second=0, microsecond=0)
    first_full = bucket if bucket == start else bucket + dt.timedelta(minutes=1)
    expected = []
    while first_full < end:
        expected.append(first_full)
        first_full += dt.timedelta(minutes=1)
    occupied = Counter(t.replace(second=0, microsecond=0) for t in times)
    return {
        "intervals": pairs,
        "interval_seconds": stats([p["seconds"] for p in pairs]),
        "gaps_above_seconds": {str(x): sum(p["seconds"] > x for p in pairs) for x in thresholds},
        "exit_to_first_seconds": (times[0] - start).total_seconds() if times else None,
        "last_to_close_seconds": (end - times[-1]).total_seconds() if times else None,
        "expected_full_minute_buckets": len(expected),
        "missing_full_minute_buckets": [t.isoformat() for t in expected if not occupied[t]],
        "multiply_occupied_buckets": {t.isoformat(): n for t, n in occupied.items() if n > 1},
        "partial_exit_bucket": bucket.isoformat() if start != bucket else None,
        "partial_exit_bucket_observations": occupied[bucket] if start != bucket else 0,
        "exact_close_observations": sum(t == end for t in times),
        "seconds_into_minute": stats([t.second + t.microsecond / 1e6 for t in times]),
    }


def timing_diagnostics(spec, observations, tolerance):
    """Describe recorded clocks without treating start-of-pass as availability."""
    ages, fetch_lags, fetch_durations, schedule_lags, gateway_lags = [], [], [], [], []
    counts = Counter(
        event_after_snapshot_start=0,
        event_after_fetch_completed=0,
        event_before_recorded_exit=0,
        event_after_regular_close=0,
        fetch_completed_after_regular_close=0,
        negative_fetch_duration=0,
    )
    for obs in observations:
        snapshot = at(obs["snapshot_time"])
        meta = obs["snapshot_metadata"] or {}
        done = (
            at(meta["chain_fetch_completed_at"]) if meta.get("chain_fetch_completed_at") else None
        )
        started = at(meta["chain_fetch_started_at"]) if meta.get("chain_fetch_started_at") else None
        if done:
            fetch_lags.append((done - snapshot).total_seconds())
            counts["fetch_completed_after_regular_close"] += done > at(spec["close_time"])
        if done and started:
            duration = (done - started).total_seconds()
            fetch_durations.append(duration)
            counts["negative_fetch_duration"] += duration < -tolerance
        if meta.get("scheduled_at"):
            schedule_lags.append((snapshot - at(meta["scheduled_at"])).total_seconds())
        if done and meta.get("chain_gateway_received_at"):
            gateway_lags.append((done - at(meta["chain_gateway_received_at"])).total_seconds())
        for quote in obs["legs"]:
            if not quote.get("quote_event_ts"):
                continue
            event = at(quote["quote_event_ts"])
            counts["event_after_snapshot_start"] += (event - snapshot).total_seconds() > tolerance
            counts["event_before_recorded_exit"] += event < at(spec["exit_time"])
            counts["event_after_regular_close"] += event > at(spec["close_time"])
            if done:
                age = (done - event).total_seconds()
                ages.append(age)
                counts["event_after_fetch_completed"] += age < -tolerance
    return {
        "counts": dict(counts),
        "event_to_local_fetch_completed_seconds": stats(ages),
        "snapshot_start_to_fetch_completed_seconds": stats(fetch_lags),
        "chain_fetch_duration_seconds": stats(fetch_durations),
        "scheduled_to_snapshot_start_seconds": stats(schedule_lags),
        "gateway_receive_to_local_fetch_completed_seconds": stats(gateway_lags),
        "meaning": "Observed clock differences; no clock-sync attestation or freshness threshold",
    }


def audit(specs, raw_rows, inventory, contract):
    by_id = {s["id"]: s for s in specs}
    if len(by_id) != len(specs):
        raise ValueError("duplicate cohort trade")
    inv = {int(r["id"]): r for r in inventory}
    if len(inv) != len(inventory) or inv.keys() != by_id.keys():
        raise ValueError("inventory/cohort membership mismatch")
    groups = defaultdict(list)
    for row in raw_rows:
        tid = int(row["trade_id"])
        if tid not in by_id:
            raise ValueError("unexpected trade in extract")
        q = json.loads(row["raw_quote"])
        groups[tid, at(q["snapshot_time"])].append(
            {"quote": q, "meta": json.loads(row["raw_meta"]) if row.get("raw_meta") else None}
        )
    normalized, rejected, coverage = [], [], []
    for tid, spec in by_id.items():
        raw_times, good_times, inventory_times, trade_good, trade_bad = [], [], [], [], []
        for (trade_id, ts), raw in sorted(groups.items()):
            if trade_id != tid:
                continue
            raw_times.append(ts)
            if historical_inventory_group(spec, raw):
                inventory_times.append(ts)
            obs = normalize_group(spec, ts, raw, contract)
            if obs["eligible"]:
                good_times.append(ts)
                trade_good.append(obs)
            else:
                trade_bad.append(obs)
        old = inv[tid]
        recomputed = {
            "complete_timestamps": len(inventory_times),
            "first_ts": inventory_times[0].isoformat() if inventory_times else None,
            "last_ts": inventory_times[-1].isoformat() if inventory_times else None,
        }
        matches = int(old["complete_timestamps"]) == len(inventory_times)
        for k in ("first_ts", "last_ts"):
            new, previous = recomputed[k], old[k] or None
            matches &= (
                abs((at(new) - at(previous)).total_seconds())
                <= contract["timestamp_equality_tolerance_seconds"]
                if new and previous
                else new == previous
            )
        if (
            old["trade_date"] != spec["session"]
            or abs((at(old["exit_time"]) - at(spec["exit_time"])).total_seconds())
            > contract["timestamp_equality_tolerance_seconds"]
        ):
            raise ValueError("inventory lifecycle mismatch")
        metas = [o["snapshot_metadata"] for o in trade_good]
        legs = [q for o in trade_good for q in o["legs"]]
        quote_ages = [number(q.get("quote_age_s")) for q in legs]
        timing = {
            "leg_rows": len(legs),
            "quote_event_ts_present": sum(bool(q.get("quote_event_ts")) for q in legs),
            "quote_age_s_present": sum(v is not None for v in quote_ages),
            "reported_quote_age_seconds": stats([v for v in quote_ages if v is not None]),
            "negative_reported_quote_ages": sum(v is not None and v < 0 for v in quote_ages),
            "bid_size_present": sum(q.get("bid_size") is not None for q in legs),
            "ask_size_present": sum(q.get("ask_size") is not None for q in legs),
            "metadata_rows_present": sum(m is not None for m in metas),
            "metadata_field_coverage": {
                k: sum(m is not None and m.get(k) is not None for m in metas)
                for k in [
                    "scheduled_at",
                    "chain_fetch_started_at",
                    "chain_fetch_completed_at",
                    "chain_gateway_received_at",
                    "chain_event_ts",
                    "chain_age_s",
                ]
            },
            "chain_sources": dict(Counter(m.get("chain_source") for m in metas if m)),
            "publication_availability_time_present": 0,
        }
        coverage.append(
            {
                "id": tid,
                "session": spec["session"],
                "symbols": spec["symbols"],
                "exit_time": spec["exit_time"],
                "close_time": spec["close_time"],
                "raw_leg_rows": sum(o["leg_rows"] for o in trade_good + trade_bad),
                "raw_groups": len(raw_times),
                "valid_groups": len(good_times),
                "rejected_groups": len(trade_bad),
                "inventory_original": old,
                "inventory_recomputed": recomputed,
                "inventory_matches": bool(matches),
                "raw_cadence": cadence(spec, raw_times, contract["gap_diagnostics_seconds"]),
                "usable_cadence": cadence(spec, good_times, contract["gap_diagnostics_seconds"]),
                "price_flags": {
                    k: sum(o[k] for o in trade_good)
                    for k in [
                        "negative_composite_bid",
                        "negative_composite_mark",
                        "mark_above_width",
                        "crossed_composite",
                        "provider_mark_outside_composite_market",
                    ]
                },
                "mark_midpoint_difference_count": sum(
                    abs(o["mark_minus_composite_midpoint"])
                    > contract["mark_midpoint_difference_reporting_tolerance_points"]
                    for o in trade_good
                ),
                "timing_coverage": timing,
                "timing_diagnostics": timing_diagnostics(
                    spec, trade_good, contract["timestamp_equality_tolerance_seconds"]
                ),
                "R0_30_second_continuation_eligible": False,
                "minute_replay_eligible": False,
                "exclusions": [
                    "independent minute cadence; no R0 substitution",
                    "no causal minute signal/fill/gap/freshness policy registered",
                ],
            }
        )
        normalized.extend(trade_good)
        rejected.extend(trade_bad)
    summary = {
        "trades": len(specs),
        "raw_leg_rows": sum(r["raw_leg_rows"] for r in coverage),
        "valid_groups": len(normalized),
        "rejected_groups": len(rejected),
        "inventory_mismatch_ids": [r["id"] for r in coverage if not r["inventory_matches"]],
        "price_flags": {
            k: sum(r["price_flags"][k] for r in coverage) for k in coverage[0]["price_flags"]
        },
        "interval_seconds": stats(
            [p["seconds"] for r in coverage for p in r["usable_cadence"]["intervals"]]
        ),
        "gaps_above_seconds": {
            str(x): sum(r["usable_cadence"]["gaps_above_seconds"][str(x)] for r in coverage)
            for x in contract["gap_diagnostics_seconds"]
        },
        "missing_full_minute_buckets": sum(
            len(r["usable_cadence"]["missing_full_minute_buckets"]) for r in coverage
        ),
        "multiply_occupied_buckets": sum(
            len(r["usable_cadence"]["multiply_occupied_buckets"]) for r in coverage
        ),
        "R0_eligible_trades": 0,
        "minute_replay_eligible_trades": 0,
    }
    return normalized, rejected, coverage, summary


def verify_parent(path, expected):
    if digest(path / "run.json") != expected:
        raise ValueError("parent run mismatch")
    for name, expected_hash in read_json(path / "run.json")["output_sha256"].items():
        target = (path / name).resolve()
        if not target.is_relative_to(path.resolve()) or digest(target) != expected_hash:
            raise ValueError("parent output mismatch")


def run(
    evidence,
    manifest,
    inventory,
    inventory_manifest,
    execution_parent,
    baseline_parent,
    config,
    source_lock,
    output,
):
    contract = read_json(config)
    if contract["model"] != "NDX-02-minute-continuation-import-v1":
        raise ValueError("unsupported continuation audit")
    snapshot = verify(evidence, manifest)
    query_file = "prices/" + contract.get("query_file", "continuation-prices.sql")
    required = {
        "cohort.json",
        "prices/extract.csv",
        query_file,
        "schema/extract.csv",
        "schema/manifest.json",
        "contract.json",
    }
    if not required.issubset(snapshot["files"]):
        raise ValueError("unverified required input")
    verify(inventory, inventory_manifest)
    checks = [
        (inventory_manifest, contract["inventory_manifest_sha256"]),
        (evidence / "cohort.json", contract["cohort_sha256"]),
        (evidence / query_file, contract["query_sha256"]),
        (evidence / "schema/manifest.json", contract["schema_manifest_sha256"]),
        (evidence / "contract.json", digest(config)),
        (execution_parent / "execution-ledger.jsonl", contract["execution_ledger_sha256"]),
    ]
    if any(digest(p) != expected for p, expected in checks):
        raise ValueError("contract input identity mismatch")
    verify_parent(execution_parent, contract["execution_parent_run_sha256"])
    verify_parent(baseline_parent, contract["baseline_parent_run_sha256"])
    lock = read_json(source_lock)
    if lock["config_sha256"] != digest(config) or lock["snapshot_manifest_sha256"] != digest(
        manifest
    ):
        raise ValueError("source lock/config/snapshot mismatch")
    for name, expected in lock["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"source drift: {name}; new contract and run required")
    new_directory(output, evidence, inventory, execution_parent, baseline_parent)
    write_json(output / "contract.json", contract)
    with (evidence / "prices/extract.csv").open(newline="") as stream:
        raw = list(csv.DictReader(stream))
    with (inventory / "extract.csv").open(newline="") as stream:
        inv = list(csv.DictReader(stream))
    normalized, rejected, coverage, summary = audit(
        read_json(evidence / "cohort.json"), raw, inv, contract
    )
    prior = {
        r["id"]: r
        for r in [
            json.loads(line)
            for line in (execution_parent / "execution-ledger.jsonl").read_text().splitlines()
        ]
    }
    first = {}
    for observation in normalized:
        first.setdefault(observation["id"], observation)
    for row in coverage:
        last_poll = prior[row["id"]]["held_collection_evidence"]["last_collection_time"]
        obs = first.get(row["id"])
        row["source_boundary"] = {
            "last_held_monitor_collection_time": last_poll,
            "first_independent_minute_collection_time": obs["snapshot_time"] if obs else None,
            "collection_gap_seconds": (at(obs["snapshot_time"]) - at(last_poll)).total_seconds()
            if obs and last_poll
            else None,
            "meaning": "Different collection streams; not quote age or a causal execution path",
            "post_exit_scope_overlaps_held_path": False,
        }
    for name, records in [
        ("observations.jsonl", normalized),
        ("rejected-groups.jsonl", rejected),
        ("coverage.jsonl", coverage),
    ]:
        with (output / name).open("x") as stream:
            for row in records:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
    write_json(output / "summary.json", summary)
    source = output / "runner-source"
    source.mkdir()
    for name in [
        "src/butterfly_guy/research/ndx_continuation.py",
        "src/butterfly_guy/research/ndx_evidence.py",
        "tests/test_ndx_continuation.py",
    ]:
        shutil.copy2(ROOT / name, source / Path(name).name)
    write_json(output / "source-lock.json", lock)
    args = locals()
    command = [sys.executable, "-m", "butterfly_guy.research.ndx_continuation"]
    for key in [
        "evidence",
        "manifest",
        "inventory",
        "inventory_manifest",
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
            "run_id": output.name,
            "parent": contract["parent"],
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "command": shlex.join(command),
            "config_sha256": digest(config),
            "snapshot_manifest_sha256": digest(manifest),
            "inventory_manifest_sha256": digest(inventory_manifest),
            "inputs": {
                str(p.resolve()): {"sha256": digest(p), "files": read_json(p)["files"]}
                for p in [manifest, inventory_manifest]
            },
            "parent_hashes": {
                str(p.resolve()): digest(p / "run.json")
                for p in [execution_parent, baseline_parent]
            },
            "source_sha256": lock["source_sha256"],
            "source_lock_sha256": digest(source_lock),
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
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in [
        "evidence",
        "manifest",
        "inventory",
        "inventory-manifest",
        "execution-parent",
        "baseline-parent",
        "config",
        "source-lock",
        "output",
    ]:
        parser.add_argument("--" + key, required=True, type=Path)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))


if __name__ == "__main__":
    main()
