"""Offline NDX provenance sufficiency checks; no replay or runtime integration."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import json
import platform
import re
import shlex
import shutil
import subprocess
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from butterfly_guy.research.ndx_continuation import ROOT, at, verify_parent
from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, verify, write_json

Hash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Text = Annotated[str, Field(min_length=1)]
Number = Annotated[str, Field(pattern=r"^-?[0-9]+(?:\.[0-9]+)?$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Clock(Model):
    owner: Text
    process: Text
    boot: Text
    source: Text
    sync_evidence: Text | None
    uncertainty_seconds: Number | None
    discontinuity: bool


class Stamp(Model):
    wall_utc: Text
    monotonic_ns: Annotated[int, Field(ge=0)] | None
    clock: Text


class Leg(Model):
    symbol: Text
    root: Literal["NDXP"]
    expiry: Text
    option_type: Literal["CALL", "PUT"]
    strike: Number
    multiplier: Number
    bid: Number | None
    ask: Number | None
    provider_mark: Number | None
    bid_size: Annotated[int, Field(ge=0)] | None
    ask_size: Annotated[int, Field(ge=0)] | None
    event: Stamp | None
    age_seconds: Number | None
    age_reference: Stamp | None
    age_semantics: Text | None
    source: Text | None
    flags: list[str]
    normalization: Text | None


class Payload(Model):
    response_id: Text
    path: Text | None
    sha256: Hash | None
    scope: Literal["market-only-body-v1"]
    redaction: Text


class Publication(Model):
    publication_id: Text | None
    transaction_id: Text | None
    snapshot_id: Text | None
    quote_write: Literal["success", "failed", "unknown"]
    metadata_write: Literal["success", "failed", "unknown"]
    complete_manifest_sha256: Hash | None
    complete_manifest_path: Text | None
    visibility_evidence: Text | None
    failure: Text | None


class Consumer(Model):
    identity: Text
    build_sha256: Hash | None
    returned_snapshot_id: Text | None
    returned_symbols: list[str]
    read_status: Literal["success", "failed", "unknown"]


class Record(Model):
    schema_version: Literal["NDX-provenance-v1"]
    evidence_kind: Literal["synthetic", "historical", "prospective"]
    record_id: Text
    snapshot_id: Text
    version: Annotated[int, Field(ge=1)]
    acquisition_id: Text
    pass_id: Text
    request_id: Text
    channel: Literal["collector-direct", "db-research"]
    session: Text
    close_utc: Text
    parent_record_sha256: Hash | None
    expected_symbols: list[str]
    payload: Payload
    clocks: dict[str, Clock]
    stamps: dict[str, Stamp | None]
    legs: list[Leg]
    chain_source: Text | None
    chain_flags: list[str]
    builds: dict[str, Hash | None]
    effective_settings: dict[str, str | None]
    publication: Publication
    consumer: Consumer
    dropped_records: Annotated[int, Field(ge=0)] | None
    gap_before_seconds: Number | None


STAGES = (
    "scheduled_deadline", "pass_start", "request_start", "gateway_receipt",
    "response_receipt", "fetch_completion", "normalization_completion", "insert_start",
    "transaction_start", "commit_ack", "publication_ack", "read_start", "read_end",
    "consumer_receipt",
)
BUILDS = ("collector", "adapter", "gateway", "schema", "config", "dependencies")
SETTINGS = ("provider_channel", "age_normalization", "clock_policy", "selected_universe")


def assess(raw, input_root):
    """Return structural rejection separately from missing provenance and replay policy."""
    result = {
        "record_id": raw.get("record_id"), "status": "insufficient", "rejected": [],
        "unknown": [], "diagnostics": [], "receipt_observed_at": None,
        "earliest_availability": None, "freshness_verified": False,
        "replay_eligible": False, "decision": None, "fill": None,
        "raw_composites": None,
    }
    try:
        r = Record.model_validate(raw)
    except ValidationError as exc:
        result["status"] = "rejected"
        result["rejected"] = [
            f"schema:{'.'.join(map(str, e['loc']))}:{e['type']}"
            for e in exc.errors(include_input=False)
        ]
        return result
    reject, unknown, notes = result["rejected"], result["unknown"], result["diagnostics"]

    def timing(stamp, label):
        if stamp is None:
            unknown.append(f"missing_time:{label}")
            return None
        if stamp.clock not in r.clocks:
            reject.append(f"unknown_clock:{label}")
            return None
        try:
            value = at(stamp.wall_utc)
            if not stamp.wall_utc.endswith(("Z", "+00:00")):
                raise ValueError("UTC required")
        except ValueError:
            reject.append(f"invalid_utc:{label}")
            return None
        clock = r.clocks[stamp.clock]
        if clock.discontinuity:
            unknown.append(f"clock_discontinuity:{label}")
        if clock.sync_evidence is None or clock.uncertainty_seconds is None:
            unknown.append(f"unattested_clock:{label}")
        elif Decimal(clock.uncertainty_seconds) < 0:
            reject.append(f"negative_clock_uncertainty:{label}")
        return value

    if set(r.stamps) != set(STAGES):
        reject.append("stage_membership_mismatch")
    times = {key: timing(s, key) for key, s in r.stamps.items() if s is not None}
    required = ["pass_start", "request_start", "response_receipt", "fetch_completion",
                "normalization_completion", "read_start", "read_end", "consumer_receipt"]
    if r.channel == "db-research":
        required += ["insert_start", "commit_ack", "publication_ack"]
    for key in required:
        if r.stamps.get(key) is None:
            unknown.append(f"missing_time:{key}")
    # No global ordering of wall clocks is assumed across different clock domains.
    sequence = [key for key in STAGES if key not in
                ("scheduled_deadline", "gateway_receipt", "transaction_start")]
    present = [(key, r.stamps[key]) for key in sequence if r.stamps.get(key)]
    for (ka, a), (kb, b) in zip(present, present[1:]):
        if a.clock != b.clock:
            unknown.append(f"cross_domain_order_unproven:{ka}:{kb}")
            continue
        if times.get(ka) is not None and times.get(kb) is not None and times[ka] > times[kb]:
            reject.append(f"wall_clock_reversal:{ka}:{kb}")
        if a.monotonic_ns is None or b.monotonic_ns is None:
            unknown.append(f"missing_monotonic_order:{ka}:{kb}")
        elif a.monotonic_ns > b.monotonic_ns:
            reject.append(f"monotonic_reversal:{ka}:{kb}")
    try:
        close = at(r.close_utc)
    except ValueError:
        reject.append("invalid_close")
        close = None
    receipt = times.get("consumer_receipt")
    if receipt is not None and r.consumer.read_status == "success":
        result["receipt_observed_at"] = r.stamps["consumer_receipt"].wall_utc
        if close is not None and receipt > close:
            notes.append("receipt_after_close_no_decision_or_fill")
    else:
        unknown.append("consumer_availability_unknown")
    if r.consumer.returned_snapshot_id != r.snapshot_id:
        reject.append("consumer_snapshot_mismatch")
    if r.consumer.read_status != "success":
        unknown.append(f"consumer_read:{r.consumer.read_status}")
    if r.consumer.build_sha256 is None:
        unknown.append("missing_consumer_build")
    symbols = [leg.symbol for leg in r.legs]
    if len(r.expected_symbols) != 3 or len(set(r.expected_symbols)) != 3:
        reject.append("invalid_expected_universe")
    if len(symbols) != len(set(symbols)):
        reject.append("duplicate_leg")
    if len(symbols) != 3 or set(symbols) != set(r.expected_symbols):
        reject.append("incomplete_or_mismatched_legs")
    if sorted(r.consumer.returned_symbols) != sorted(r.expected_symbols):
        unknown.append("consumer_complete_snapshot_unproven")
    for leg in r.legs:
        label = leg.symbol
        match = re.fullmatch(r"(NDXP)\s+(\d{6})([CP])(\d{8})", label)
        try:
            expiry = dt.date.fromisoformat(leg.expiry)
            identity = (match and match[2] == expiry.strftime("%y%m%d")
                        and match[3] == leg.option_type[0]
                        and Decimal(match[4]) / 1000 == Decimal(leg.strike)
                        and leg.expiry == r.session and Decimal(leg.multiplier) > 0)
        except ValueError:
            identity = False
        if not identity:
            reject.append(f"instrument_identity_mismatch:{label}")
        for key in ("bid", "ask", "provider_mark", "bid_size", "ask_size", "source",
                    "normalization", "age_seconds", "age_semantics"):
            if getattr(leg, key) is None:
                unknown.append(f"missing_leg:{label}:{key}")
        event = timing(leg.event, f"leg_event:{label}")
        done = r.stamps.get("fetch_completion")
        if (event is not None and done is not None and leg.event.clock == done.clock
                and times.get("fetch_completion") is not None
                and event > times["fetch_completion"]):
            reject.append(f"event_after_fetch_in_same_clock:{label}")
        timing(leg.age_reference, f"age_reference:{label}")
        if leg.age_seconds is not None and Decimal(leg.age_seconds) < 0:
            reject.append(f"negative_age:{label}")
        if leg.bid is not None and leg.ask is not None:
            if Decimal(leg.bid) < 0 or Decimal(leg.ask) < Decimal(leg.bid):
                reject.append(f"invalid_leg_market:{label}")
        if leg.bid_size == 0:
            notes.append(f"zero_bid_size:{label}:no_automatic_stale_inference")
    if len(symbols) == 3 and len(set(symbols)) == 3 and all(
        all(getattr(q, k) is not None for k in ("bid", "ask", "provider_mark")) for q in r.legs
    ):
        lo, ce, hi = sorted(r.legs, key=lambda q: Decimal(q.strike))
        mark = Decimal(lo.provider_mark) - 2 * Decimal(ce.provider_mark) + Decimal(hi.provider_mark)
        bid = Decimal(lo.bid) - 2 * Decimal(ce.ask) + Decimal(hi.bid)
        ask = Decimal(lo.ask) - 2 * Decimal(ce.bid) + Decimal(hi.ask)
        result["raw_composites"] = {"provider_mark": str(mark), "bid": str(bid), "ask": str(ask),
                                    "midpoint": str((bid + ask) / 2)}
    payload = r.payload
    if payload.path is None or payload.sha256 is None:
        unknown.append("original_response_missing")
    else:
        target = (input_root / payload.path).resolve()
        if not target.is_relative_to(input_root.resolve()):
            reject.append("unsafe_payload_path")
        elif not target.is_file() or digest(target) != payload.sha256:
            reject.append("original_response_hash_mismatch")
    for key in BUILDS:
        if r.builds.get(key) is None:
            unknown.append(f"missing_build:{key}")
    for key in SETTINGS:
        if r.effective_settings.get(key) is None:
            unknown.append(f"missing_setting:{key}")
    pub = r.publication
    if r.channel == "db-research":
        for key in ("publication_id", "transaction_id", "complete_manifest_sha256",
                    "complete_manifest_path",
                    "visibility_evidence"):
            if getattr(pub, key) is None:
                unknown.append(f"publication_missing:{key}")
        if pub.complete_manifest_path and pub.complete_manifest_sha256:
            target = (input_root / pub.complete_manifest_path).resolve()
            if not target.is_relative_to(input_root.resolve()):
                reject.append("unsafe_publication_path")
            elif not target.is_file() or digest(target) != pub.complete_manifest_sha256:
                reject.append("publication_manifest_hash_mismatch")
            else:
                manifest = read_json(target)
                if (manifest.get("snapshot_id") != r.snapshot_id
                        or sorted(manifest.get("symbols", [])) != sorted(r.expected_symbols)
                        or manifest.get("response_sha256") != r.payload.sha256
                        or manifest.get("quote_write") != "success"
                        or manifest.get("metadata_write") != "success"):
                    reject.append("publication_manifest_identity_mismatch")
        if pub.snapshot_id != r.snapshot_id:
            unknown.append("publication_snapshot_unproven")
        if pub.quote_write != "success" or pub.metadata_write != "success":
            unknown.append("publication_incomplete_quote_and_metadata_separate")
        if r.stamps.get("transaction_start") and not r.stamps.get("commit_ack"):
            notes.append("transaction_start_is_not_commit_or_visibility")
    if r.dropped_records is None or r.dropped_records > 0:
        unknown.append("dropped_record_coverage_unknown")
    if r.gap_before_seconds is not None:
        notes.append("gap_recorded_policy_unresolved")
    notes.append("freshness_dispersion_gap_bounds_unregistered")
    result["rejected"], result["unknown"] = sorted(set(reject)), sorted(set(unknown))
    result["status"] = "rejected" if reject else "insufficient" if unknown else "sufficient"
    return result


def run(input_path, config, source_lock, output):
    contract, lock = read_json(config), read_json(source_lock)
    if contract["model"] != "NDX-provenance-v1":
        raise ValueError("unsupported provenance contract")
    if digest(config) != lock["config_sha256"]:
        raise ValueError("config/source lock mismatch")
    for name, expected in lock["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"source drift: {name}")
    if digest(input_path) != contract["input_sha256"]:
        raise ValueError("input hash mismatch")
    if digest(ROOT / contract["fixture_manifest"]) != contract["fixture_manifest_sha256"]:
        raise ValueError("fixture manifest hash mismatch")
    verified_fixtures = verify(input_path.parent, ROOT / contract["fixture_manifest"])
    if input_path.name not in verified_fixtures["files"]:
        raise ValueError("input absent from fixture manifest")
    if digest(ROOT / contract["schema"]) != contract["schema_sha256"]:
        raise ValueError("schema hash mismatch")
    if read_json(ROOT / contract["schema"]) != Record.model_json_schema():
        raise ValueError("schema/source mismatch")
    # Missing private dependencies never become a successful private verification.
    parents = {}
    for key, binding in contract["parents"].items():
        path = ROOT / binding["path"]
        verify_parent(path, binding["run_sha256"])
        for name, expected in read_json(path / "run.json")["source_sha256"].items():
            if digest(ROOT / name) != expected:
                raise ValueError(f"parent source drift: {name}")
        parents[key] = {"path": str(path), "sha256": digest(path / "run.json")}
    snapshots = {}
    for key, binding in contract["snapshots"].items():
        manifest = ROOT / binding["manifest"]
        if digest(manifest) != binding["manifest_sha256"]:
            raise ValueError(f"manifest mismatch:{key}")
        record = verify(ROOT / binding["root"], manifest)
        if not set(binding["required"]) <= record["files"].keys():
            raise ValueError(f"required input missing:{key}")
        snapshots[key] = record["files"]
    raw = [json.loads(line) for line in input_path.read_text().splitlines()]
    results = [assess(row, input_path.parent) for row in raw]
    identities = Counter(r.get("record_id") for r in raw)
    versions = Counter((r.get("snapshot_id"), r.get("version"), r.get("channel")) for r in raw)
    for row, result in zip(raw, results):
        if (identities[row.get("record_id")] > 1
                or versions[row.get("snapshot_id"), row.get("version"), row.get("channel")] > 1):
            result["rejected"].append("duplicate_record_identity")
            result["status"] = "rejected"
    new_directory(output, input_path.parent, config.parent, *(ROOT / p["path"]
                                                           for p in contract["parents"].values()))
    with (output / "results.jsonl").open("x") as stream:
        for result in results:
            stream.write(json.dumps(result, allow_nan=False) + "\n")
    summary = {"model": contract["model"], "records": len(results),
               "status_counts": dict(Counter(r["status"] for r in results)),
               "synthetic_records": sum(r.get("evidence_kind") == "synthetic" for r in raw),
               "new_historical_coverage": 0, "historical_replay_eligibility_changed": False}
    write_json(output / "summary.json", summary)
    for name, path in {"contract.json": config, "source-lock.json": source_lock,
                       "fixtures.jsonl": input_path, "schema.json": ROOT / contract["schema"],
                       "fixture-manifest.json": ROOT / contract["fixture_manifest"]}.items():
        shutil.copy2(path, output / name)
    for name in lock["source_sha256"]:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    write_json(output / "run.json", {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": shlex.join([sys.executable, "-m", "butterfly_guy.research.ndx_provenance",
                               "--input", str(input_path.resolve()),
                               "--config", str(config.resolve()),
                               "--source-lock", str(source_lock.resolve()),
                               "--output", str(output.resolve())]),
        "config_sha256": digest(config), "source_lock_sha256": digest(source_lock),
        "input_sha256": digest(input_path), "source_sha256": lock["source_sha256"],
        "parent_hashes": parents, "verified_snapshot_files": snapshots,
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "python": sys.version, "platform": {"system": platform.system(),
                                            "release": platform.release(),
                                            "machine": platform.machine()},
        "dependencies": {d.metadata["Name"]: d.version
                         for d in importlib.metadata.distributions()},
        "output_sha256": {str(p.relative_to(output)): digest(p)
                          for p in output.rglob("*") if p.is_file()},
    })
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "config", "source-lock", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = vars(parser.parse_args())
    args["input_path"] = args.pop("input")
    print(json.dumps(run(**args), indent=2))


if __name__ == "__main__":
    main()
