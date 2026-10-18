"""Synthetic-only native SDK -> new local PostgreSQL cluster -> receipt/resource check.

No supplied DSN, broker URL, API key, live schema or service is accepted.
"""

from __future__ import annotations

import argparse
import asyncio
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
import tempfile
import time
from pathlib import Path

import asyncpg
import httpx
from schwab_gateway_sdk.client import GatewayMarketDataClient

from butterfly_guy.research.ndx_continuation import verify_parent
from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, write_json
from butterfly_guy.research.ndx_postgres_recording import (
    PostgresRecorder,
    ResearchGatewayHTTPClient,
    install_empty_schema,
)
from butterfly_guy.research.ndx_provenance import ROOT


def scale_body(body, target):
    """Deterministic synthetic stress recipe; never generates historical market data."""
    if target == 4:
        return body
    if target != 5000:
        raise ValueError("only registered native 4/5000-contract synthetic cases supported")
    raw = json.loads(body)
    chain = raw["option_chain"]
    template = copy.deepcopy(chain["contracts"][-1])
    for index in range(4996):
        strike = 35000 + index
        contract = dict(template, strike=strike, symbol=f"NDXP  300102C{strike * 1000:08d}")
        chain["contracts"].append(contract)
    chain.update(call_contract_count=4997, put_contract_count=3, strike_count=4999)
    # This is a generated synthetic body's own bytes, not reconstruction of a provider response.
    return (json.dumps(raw, allow_nan=False) + "\n").encode()


async def evaluate(params, body, universe, contract, output):
    pool = await asyncpg.create_pool(**params, min_size=1, max_size=5, command_timeout=5)
    try:
        async with pool.acquire() as conn:
            await install_empty_schema(conn)
        recorder = PostgresRecorder(pool)
        baseline_size = await pool.fetchval("SELECT pg_database_size(current_database())")
        version = await pool.fetchval("SELECT version()")
        extensions = [r["name"] for r in await pool.fetch("SELECT name FROM pg_available_extensions")]
        summaries = []
        for case in contract["cases"]:
            case_output = output / case["name"]
            new_directory(case_output)
            native = scale_body(body, case["contracts"])
            (case_output / "native-body.json").write_bytes(native)
            observed_requests = []
            def handle(request):
                observed_requests.append(request.url.path)
                return httpx.Response(200, content=native)
            measurements = []
            async with ResearchGatewayHTTPClient(base_url="https://synthetic.invalid",
                    transport=httpx.MockTransport(handle), recorder=recorder) as client:
                sdk = GatewayMarketDataClient("https://synthetic.invalid", "synthetic-test-key",
                                             client=client)
                for sample in range(case["samples"]):
                    identity = f"synthetic-{case['name']}-{sample}"
                    client.context_factory = lambda: dict(
                        snapshot_id=identity, record_id=identity, request_id=identity,
                        pass_id=identity, acquisition_id="synthetic-resource-check",
                        expected_symbols=universe["symbols"], session=universe["session"],
                        evidence_kind="synthetic")
                    started, cpu = time.perf_counter(), time.process_time()
                    await sdk.get_option_chain("$NDX", dt.date.fromisoformat(universe["session"]))
                    receipt = await recorder.read(identity, 1, consumer="synthetic-resource-reader",
                                                 build_sha256=digest(Path(__file__)))
                    measurements.append({"wall_seconds": time.perf_counter() - started,
                                         "cpu_seconds": time.process_time() - cpu})
                    if receipt is None or not receipt["receipt_journaled"] \
                            or receipt["response"] != native or client.recording_failures:
                        raise ValueError("native PostgreSQL roundtrip or receipt recording failed")
                    if sample == case["samples"] - 1:
                        for name, value in (("producer", receipt["document"]),
                                            ("receipt", receipt["receipt"]),
                                            ("assessment", receipt["assessment"]),
                                            ("commit-ack", receipt["commit_ack"])):
                            write_json(case_output / f"{name}.json", value)
                        (case_output / "publication.json").write_text(receipt["manifest"])
            if observed_requests != ["/v1/option-chain"] * case["samples"]:
                raise ValueError("unexpected request count or endpoint")
            write_json(case_output / "measurements.json", measurements)
            durations = sorted(s["wall_seconds"] for s in measurements)
            summaries.append({"case": case["name"], "contracts_per_body": case["contracts"],
                "body_bytes": len(native), "samples": case["samples"],
                "request_count": len(observed_requests), "wall_seconds_max": durations[-1],
                "wall_seconds_p95_nearest_rank": durations[(95 * len(durations) + 99) // 100 - 1],
                "cpu_seconds_total": sum(m["cpu_seconds"] for m in measurements)})
        inventory = [dict(r) for r in await recorder.recovery_inventory()]
        write_json(output / "recovery.json", inventory)
        counts = {table: await pool.fetchval(f"SELECT count(*) FROM ndx_provenance_v1.{table}")
                  for table in ("quotes", "provenance", "publications", "journal")}
        return {"model": contract["model"], "cases": summaries, "table_rows": counts,
            "new_historical_coverage": 0, "evidence_kind": "synthetic",
            "database_size_growth_bytes": await pool.fetchval(
                "SELECT pg_database_size(current_database())") - baseline_size,
            "server_version": version, "timescaledb_extension_available": "timescaledb" in extensions,
            "process_peak_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "resource_scope": "Native synthetic SDK parsing, actual PostgreSQL publish/read; excludes exports",
            "production_budget_validated": False, "replay_eligible": False}
    finally:
        await pool.close()


def run(input_path, universe, postgres_bin, config, source_lock, output):
    contract, lock = read_json(config), read_json(source_lock)
    if contract["model"] != "NDX-native-postgres-check-v1":
        raise ValueError("unsupported check contract")
    if digest(config) != lock["config_sha256"]:
        raise ValueError("config/source lock mismatch")
    for name, expected in lock["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"source drift: {name}")
    if digest(input_path) != contract["input_sha256"] or digest(universe) != contract["universe_sha256"]:
        raise ValueError("synthetic input/universe hash mismatch")
    for binding in contract["parents"].values():
        verify_parent(ROOT / binding["path"], binding["run_sha256"])
    specification = read_json(universe)
    if specification["evidence_kind"] != "synthetic":
        raise ValueError("synthetic inputs required")
    if contract["cases"] != [{"name": "native-small", "contracts": 4, "samples": 5},
                             {"name": "sdk-contract-limit", "contracts": 5000, "samples": 3}]:
        raise ValueError("unregistered case recipe")
    new_directory(output, input_path.parent, universe.parent, config.parent)
    for name, path in (("contract.json", config), ("source-lock.json", source_lock),
                       ("input.json", input_path), ("universe.json", universe)):
        shutil.copy2(path, output / name)
    cluster = Path(tempfile.mkdtemp(prefix="ndx-pg-run-"))
    data, sockets = cluster / "data", cluster / "socket"
    sockets.mkdir(mode=0o700)
    subprocess.run([str(postgres_bin / "initdb"), "-D", str(data), "-A", "trust",
        "-U", "ndx_research_test", "--no-locale", "-E", "UTF8"],
        check=True, capture_output=True, text=True)
    options = shlex.join(["-c", "listen_addresses=", "-k", str(sockets), "-p", "55483"])
    subprocess.run([str(postgres_bin / "pg_ctl"), "-D", str(data), "-l", str(cluster / "postgres.log"),
        "-o", options, "-w", "start"], check=True, capture_output=True, text=True)
    params = {"host": str(sockets), "port": 55483, "user": "ndx_research_test", "database": "postgres"}
    try:
        summary = asyncio.run(evaluate(params, input_path.read_bytes(), specification, contract, output))
        subprocess.run([str(postgres_bin / "pg_dump"), "-h", str(sockets), "-p", "55483",
            "-U", "ndx_research_test", "-d", "postgres", "--no-owner", "--no-privileges",
            "--schema=ndx_provenance_v1", "-Fc", "-f", str((output / "research-schema.dump").resolve())],
            check=True, capture_output=True, text=True)
    finally:
        subprocess.run([str(postgres_bin / "pg_ctl"), "-D", str(data), "-m", "fast", "-w", "stop"],
                       check=True, capture_output=True, text=True)
    write_json(output / "summary.json", summary)
    for name in lock["source_sha256"]:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    arguments = locals()
    command = [sys.executable, str(Path(__file__).resolve())]
    for key in ("input_path", "universe", "postgres_bin", "config", "source_lock", "output"):
        option = "--input" if key == "input_path" else "--" + key.replace("_", "-")
        command.extend([option, str(arguments[key].resolve())])
    write_json(output / "run.json", {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "command": shlex.join(command),
        "config_sha256": digest(config), "source_lock_sha256": digest(source_lock),
        "input_sha256": digest(input_path), "universe_sha256": digest(universe),
        "source_sha256": lock["source_sha256"], "parent_hashes": contract["parents"],
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "python": sys.version, "platform": {"system": platform.system(),
            "release": platform.release(), "machine": platform.machine()},
        "dependencies": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "postgres_binary_sha256": {name: digest(postgres_bin / name)
                                   for name in ("postgres", "initdb", "pg_ctl", "pg_dump")},
        "retained_test_cluster": str(cluster), "test_cluster_stopped": True,
        "output_sha256": {str(p.relative_to(output)): digest(p)
                          for p in output.rglob("*") if p.is_file()},
    })
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "universe", "postgres-bin", "config", "source-lock", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = vars(parser.parse_args())
    args["input_path"] = args.pop("input")
    print(json.dumps(run(**args), indent=2))


if __name__ == "__main__":
    main()
