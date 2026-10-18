"""Registered synthetic observer resources on a NEW local PG cluster, not target proof."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import importlib.metadata
import json
import os
import platform
import random
import resource
import shlex
import shutil
import subprocess
import sys
import time
import zlib
from dataclasses import asdict
from pathlib import Path

import asyncpg
import httpx
from schwab_gateway_sdk.client import GatewayMarketDataClient

from butterfly_guy.research.ndx_continuation import ROOT
from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, write_json
from butterfly_guy.research.ndx_observer import Acquisition, ObserverLimits, create_observer
from butterfly_guy.research.ndx_postgres_recording import install_empty_schema


def process_sample(pid):
    """Linux process counters; no command line or environment inspection."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return {"cpu_ticks": int(stat[11]) + int(stat[12]),
                "rss_bytes": int(stat[21]) * os.sysconf("SC_PAGE_SIZE")}
    except FileNotFoundError:
        return None


async def evaluate(params, contract, output, *, initialize_database=None,
                   process_sampler=process_sample):
    from tools.check_ndx_postgres_recording import scale_body

    admin = await asyncpg.connect(**params)
    try:
        await admin.execute("CREATE DATABASE ndx_observer_resources")
    finally:
        await admin.close()
    params = dict(params, database="ndx_observer_resources")
    admin = await asyncpg.connect(**params)
    try:
        if initialize_database is not None:
            await initialize_database(admin)
        await install_empty_schema(admin)
        await admin.execute((ROOT / contract["roles"]).read_text())
        await admin.execute("CREATE ROLE ndx_resource_fixture LOGIN IN ROLE ndx_evidence_recorder")
        version = await admin.fetchval("SELECT version()")
        extension = await admin.fetchval("SELECT extversion FROM pg_extension WHERE extname='timescaledb'")
        db_before = await admin.fetchval("SELECT pg_database_size(current_database())")
        body = (ROOT / contract["input"]).read_bytes()
        universe = read_json(ROOT / contract["universe"])
        large = json.loads(scale_body(body, 5000))
        rng = random.Random(78020301)
        for quote in large["option_chain"]["contracts"][4:]:
            quote["data_quality_flags"] = [rng.randbytes(32).hex()]
            quote["bid"] = rng.randrange(1, 1000000) / 10000
            quote["ask"] = quote["bid"] + .01
        varied = json.dumps(large).encode()
        limits = ObserverLimits(**contract["limits"])
        boundary = body + b" " * (limits.body_bytes - len(body))
        bodies = {"small": body, "varied-5000": varied, "byte-boundary": boundary,
                  "over-boundary": boundary + b" "}
        samples = []
        for scenario in contract["resource_cases"]:
            name = scenario["name"]
            native = bodies[name]
            (output / (name + ".json")).write_bytes(native)
            calls = []
            def handle(request):
                calls.append(request.url.path)
                return httpx.Response(200, content=native)
            transport = httpx.MockTransport(handle)
            client = httpx.AsyncClient(base_url="https://synthetic.invalid", transport=transport)
            sdk = GatewayMarketDataClient("https://synthetic.invalid", "synthetic-key", client=client)
            baseline = []
            try:
                for _ in range(scenario["samples"]):
                    start, cpu = time.perf_counter(), time.process_time()
                    await sdk.get_option_chain("$NDX", dt.date.fromisoformat(universe["session"]))
                    baseline.append({"wall_seconds": time.perf_counter() - start,
                                     "cpu_seconds": time.process_time() - cpu})
            finally:
                await client.aclose()
            item = create_observer(enabled=True,
                connection_factory=lambda: dict(params, user="ndx_resource_fixture"),
                gateway_url="https://synthetic.invalid", gateway_api_key="synthetic-key",
                limits=limits, transport=transport)
            await item.start()
            measurements = []
            peak_connections = 0
            try:
                pids = await admin.fetch("SELECT pid FROM pg_stat_activity WHERE "
                    "datname=current_database() AND application_name='ndx-research-observer'")
                db_process_before = {str(r["pid"]): process_sampler(r["pid"]) for r in pids}
                for index in range(scenario["samples"]):
                    identity = f"synthetic-{name}-{index}"
                    context = Acquisition(snapshot_id=identity, record_id=identity,
                        request_id=identity, pass_id=identity, acquisition_id="synthetic-resources",
                        session=universe["session"], expected_symbols=tuple(universe["symbols"]),
                        calendar="synthetic-calendar", close_utc="2030-01-02T21:00:00+00:00",
                        build_sha256=digest(Path(__file__)), config_sha256=contract["self_hash"],
                        consumer="synthetic-resources", evidence_kind="synthetic")
                    start, cpu = time.perf_counter(), time.process_time()
                    result = await item.acquire(context)
                    elapsed = time.perf_counter() - start
                    measurements.append({"wall_seconds": elapsed,
                        "cpu_seconds": time.process_time() - cpu,
                        "quote_status": result.quote_status,
                        "recording_status": result.recording_status,
                        "receipt_recorded": bool(result.receipt and result.receipt["receipt_journaled"]),
                        "consumer_lag_upper_bound_seconds": elapsed if result.receipt else None})
                    if result.quote_status != "success" or (name != "over-boundary" and (
                            result.receipt is None or result.receipt["response"] != native)):
                        raise ValueError("synthetic resource roundtrip failed")
                    peak_connections = max(peak_connections, await admin.fetchval(
                        "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() "
                        "AND application_name='ndx-research-observer'"))
                pids = await admin.fetch("SELECT pid FROM pg_stat_activity WHERE "
                    "datname=current_database() AND application_name='ndx-research-observer'")
                db_process_after = {str(r["pid"]): process_sampler(r["pid"]) for r in pids}
            finally:
                start = time.perf_counter()
                await item.close()
                shutdown = time.perf_counter() - start
            if len(calls) != scenario["samples"] * 2:
                raise ValueError("unexpected synthetic request/retry count")
            samples.append({"case": name, "body_bytes": len(native),
                "zlib_bytes": len(zlib.compress(native)), "sdk_only": baseline,
                "sdk_observer_publish_read": measurements, "shutdown_seconds": shutdown,
                "counts": dict(item.counts), "peak_retained_body_bytes": item.peak_retained_bytes,
                "queue_items": 0, "peak_connections_sampled": peak_connections,
                "db_process_before": db_process_before, "db_process_after": db_process_after})
        await admin.execute("CHECKPOINT")
        return {"cases": samples, "server_version": version, "timescaledb": extension,
            "database_size_growth_bytes": await admin.fetchval(
                "SELECT pg_database_size(current_database())") - db_before,
            "python_peak_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "limits": asdict(limits), "db_cpu_ticks_per_second": os.sysconf("SC_CLK_TCK"),
            "storage": "local /tmp fixture; not network/durable storage validation",
            "exact_target_gate": "not_tested_by_this_runner", "production_budget_validated": False,
            "replay_eligible": False, "new_historical_coverage": 0,
            "limitations": ["RSS/CPU are endpoint samples, not DB peak profiling",
                "consumer lag is an operation-duration upper bound, not earliest availability",
                "synchronous parsing cannot be preempted by asyncio timeouts",
                "varied random hex is not a production compression estimate",
                "pressure/outage/cancellation mechanisms are covered by separately recorded tests"]}
    finally:
        await admin.close()


def run(config, source_lock, postgres_bin, output):
    # Direct `python tools/...py` exposes tools/, not the checkout root. These
    # are source-locked verification helpers, not installed runtime modules.
    sys.path.insert(0, str(ROOT))
    from tests.test_ndx_postgres_recording import postgres_cluster
    from tools.check_ndx_timescale import verify_registration

    contract, lock = verify_registration(config, source_lock)
    if os.environ.get("NDX_TIMESCALE_SOCKET"):
        raise ValueError("this runner requires its own fresh local PG cluster")
    new_directory(output, config.parent)
    os.environ["NDX_POSTGRES_BIN"] = str(postgres_bin)
    cluster = postgres_cluster.__wrapped__()
    params = next(cluster)
    contract = dict(contract, self_hash=digest(config))
    started = time.perf_counter()
    try:
        summary = asyncio.run(evaluate(params, contract, output))
    finally:
        try:
            next(cluster)
        except StopIteration:
            pass
    write_json(output / "summary.json", summary)
    for name, path in (("contract.json", config), ("source-lock.json", source_lock)):
        shutil.copy2(path, output / name)
    for path in lock["source_sha256"]:
        target = output / "source" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    write_json(output / "run.json", {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": shlex.join([sys.executable, *sys.argv]), "python": sys.version,
        "platform": platform.platform(), "dependencies": {
            d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "config_sha256": digest(config), "source_lock_sha256": digest(source_lock),
        "source_sha256": lock["source_sha256"], "parent_hashes": contract["parents"],
        "retained_test_cluster": str(Path(params["host"]).parent), "cluster_stopped": True,
        "elapsed_seconds": time.perf_counter() - started,
        "postgres_binary_sha256": {name: digest(postgres_bin / name)
                                   for name in ("postgres", "initdb", "pg_ctl")},
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
        "output_sha256": {str(p.relative_to(output)): digest(p)
                          for p in output.rglob("*") if p.is_file()}})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("config", "source-lock", "postgres-bin", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    args = vars(parser.parse_args())
    print(json.dumps(run(**args), indent=2))
