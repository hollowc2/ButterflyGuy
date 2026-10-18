"""Exercise the dormant research recorder with synthetic inputs on a local filesystem."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.metadata
import json
import platform
import resource
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from butterfly_guy.research.ndx_continuation import verify_parent
from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, write_json
from butterfly_guy.research.ndx_provenance import ROOT
from butterfly_guy.research.ndx_recording import Recorder, export_receipt


def run(input_path, response, config, source_lock, output):
    contract, lock = read_json(config), read_json(source_lock)
    if contract["model"] != "NDX-recording-offline-v1":
        raise ValueError("unsupported recording check contract")
    if digest(config) != lock["config_sha256"]:
        raise ValueError("config/source lock mismatch")
    for name, expected in lock["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"source drift: {name}")
    if digest(input_path) != contract["input_sha256"] \
            or digest(response) != contract["response_sha256"]:
        raise ValueError("synthetic input hash mismatch")
    verify_parent(ROOT / contract["parent"], contract["parent_run_sha256"])
    correction = contract.get("correction_parent")
    if correction:
        verify_parent(ROOT / correction["path"], correction["run_sha256"])
    raw, body = read_json(input_path), response.read_bytes()
    if raw["evidence_kind"] != "synthetic":
        raise ValueError("this runner accepts synthetic evidence only")
    count = contract["samples"]
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 100:
        raise ValueError("sample count must be 1..100")
    new_directory(output, input_path.parent, response.parent, config.parent)
    shutil.copy2(input_path, output / "input.json")
    shutil.copy2(response, output / "input-response.json")
    shutil.copy2(config, output / "contract.json")
    shutil.copy2(source_lock, output / "source-lock.json")
    recorder = Recorder(output / "recording.sqlite", create=True)
    measurements = []
    try:
        for i in range(count):
            sample = copy.deepcopy(raw)
            sample.update(record_id=f"synthetic-record-{i}", snapshot_id=f"synthetic-snapshot-{i}")
            sample["consumer"]["returned_snapshot_id"] = sample["snapshot_id"]
            sample["publication"].update(complete_manifest_path=None,
                complete_manifest_sha256=None, snapshot_id=sample["snapshot_id"])
            wall, cpu = time.perf_counter(), time.process_time()
            result = recorder.publish(sample, body)
            if not result.published or not result.acknowledgement_recorded:
                raise ValueError(f"synthetic publication failed: {result.failure}")
            receipt = recorder.read(sample["snapshot_id"], 1,
                consumer="offline-synthetic-research-reader", build_sha256=digest(Path(__file__)))
            if receipt is None or not receipt["receipt_journaled"]:
                raise ValueError("synthetic receipt not journaled")
            measurements.append({"publish_and_read_wall_seconds": time.perf_counter() - wall,
                                 "publish_and_read_cpu_seconds": time.process_time() - cpu})
            export_receipt(receipt, output / f"receipt-{i:03d}")
        write_json(output / "recovery.json", recorder.recovery_inventory())
    finally:
        recorder.close()
    duration = sorted(r["publish_and_read_wall_seconds"] for r in measurements)
    assessments = [read_json(p) for p in output.glob("receipt-*/assessment.json")]
    if any(a["rejected"] or a["replay_eligible"] for a in assessments):
        raise ValueError("synthetic receipt violates provenance boundaries")
    summary = {
        "samples": count, "evidence_kind": "synthetic", "new_historical_coverage": 0,
        "publication_and_receipt_successes": count,
        "wall_seconds_min": duration[0], "wall_seconds_max": duration[-1],
        "wall_seconds_p95_nearest_rank": duration[(95 * count + 99) // 100 - 1],
        "wall_seconds_total": sum(duration),
        "cpu_seconds_total": sum(r["publish_and_read_cpu_seconds"] for r in measurements),
        "process_peak_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "closed_database_bytes": (output / "recording.sqlite").stat().st_size,
        "measurement_scope": "local synthetic 3-leg input; excludes export writes; no broker/Timescale",
        "production_budget_validated": False, "freshness_verified": False,
        "replay_eligible": False,
    }
    write_json(output / "measurements.json", measurements)
    write_json(output / "summary.json", summary)
    for name in lock["source_sha256"]:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    write_json(output / "run.json", {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": shlex.join([sys.executable, str(Path(__file__).resolve()),
            "--input", str(input_path.resolve()), "--response", str(response.resolve()),
            "--config", str(config.resolve()), "--source-lock", str(source_lock.resolve()),
            "--output", str(output.resolve())]),
        "config_sha256": digest(config), "source_lock_sha256": digest(source_lock),
        "input_sha256": digest(input_path), "response_sha256": digest(response),
        "parent_run_sha256": contract["parent_run_sha256"],
        "source_sha256": lock["source_sha256"],
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "python": sys.version,
        "platform": {"system": platform.system(), "release": platform.release(),
                     "machine": platform.machine()},
        "dependencies": {d.metadata["Name"]: d.version
                         for d in importlib.metadata.distributions()},
        "output_sha256": {str(p.relative_to(output)): digest(p)
                          for p in output.rglob("*") if p.is_file()},
    })
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "response", "config", "source-lock", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = vars(parser.parse_args())
    args["input_path"] = args.pop("input")
    print(json.dumps(run(**args), indent=2))


if __name__ == "__main__":
    main()
