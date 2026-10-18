"""Registered exact-image synthetic resources and schema restore; never a live DSN."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import importlib.metadata
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from decimal import Decimal
from pathlib import Path

import asyncpg

from butterfly_guy.research.ndx_continuation import ROOT
from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, write_json
from butterfly_guy.research.ndx_postgres_recording import PostgresRecorder
from butterfly_guy.research.ndx_recording import encode, sha


class IsolatedTarget:
    def __init__(self, output, image):
        token = uuid.uuid4().hex
        self.name = "ndx-target-restore-" + token
        self.root = Path("/tmp") / ("ndx-timescale-" + token)
        self.root.mkdir(mode=0o700)
        self.socket = self.root / "socket"
        self.socket.mkdir()
        self.socket.chmod(0o777)
        self.output, self.image = output, image
        self.commands = []
        self.created = self.stopped = False
        self.container_id = None

    def command(self, args, *, timeout=60, stdin=None, binary_output=None):
        started = time.perf_counter()
        proc = subprocess.run(args, input=stdin, capture_output=True, timeout=timeout)
        entry = {"command": shlex.join(args), "returncode": proc.returncode,
                 "elapsed_seconds": time.perf_counter() - started,
                 "stderr": proc.stderr.decode(errors="replace")}
        if binary_output:
            binary_output.write_bytes(proc.stdout)
            entry.update(output_sha256=digest(binary_output), output_bytes=len(proc.stdout))
        else:
            entry["stdout"] = proc.stdout.decode(errors="replace")
        self.commands.append(entry)
        if proc.returncode:
            raise RuntimeError("isolated_fixture_command_failed")
        return entry.get("stdout")

    def start(self):
        identity = [json.loads(part) for part in self.command([
            "docker", "image", "inspect", self.image, "--format",
            '{{json .Id}}|{{json .RepoDigests}}|{{json .Architecture}}']).strip().split("|")]
        if self.image not in identity[1] or identity[2] != "amd64":
            raise ValueError("exact image identity mismatch")
        self.identity = identity
        self.container_id = self.command(["docker", "run", "--detach", "--name", self.name,
            "--label", "ndx.observer-restore=" + self.name, "--network", "none",
            "--memory", "1g", "--cpus", "1", "--pids-limit", "128",
            "--tmpfs", "/var/lib/postgresql/data:rw,size=512m",
            "--mount", f"type=bind,src={self.socket},dst=/socket",
            "--env", "POSTGRES_HOST_AUTH_METHOD=trust", "--env", "POSTGRES_USER=ndx_research_test",
            "--env", "PGHOST=/socket",
            self.image, "postgres", "-c", "listen_addresses=", "-c",
            "unix_socket_directories=/var/run/postgresql,/socket", "-c",
            "shared_preload_libraries=timescaledb"]).strip()
        self.created = True

    def process_sample(self, pid):
        # Backend PIDs are in the container namespace; never read host /proc/PID.
        stat = self.command(["docker", "exec", self.name, "cat", f"/proc/{int(pid)}/stat"])
        fields = stat.rsplit(")", 1)[1].split()
        return {"cpu_ticks": int(fields[11]) + int(fields[12]),
                "rss_bytes": int(fields[21]) * os.sysconf("SC_PAGE_SIZE"),
                "shared_kernel_page_size_bytes": os.sysconf("SC_PAGE_SIZE"),
                "pid_namespace": "owned exact-image container"}

    def close(self):
        if self.created:
            try:
                self.command(["docker", "logs", self.name])
            finally:
                self.command(["docker", "stop", "--time", "5", self.name], timeout=15)
                state = json.loads(self.command(["docker", "inspect", "--format",
                    '{"status":{{json .State.Status}},"running":{{json .State.Running}}}',
                    self.name]))
                self.stopped = state["running"] is False and state["status"] == "exited"


async def initialize_database(conn):
    await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb VERSION '2.25.2'")
    if await conn.fetchval("SHOW server_version") != "16.11" or await conn.fetchval(
            "SELECT extversion FROM pg_extension WHERE extname='timescaledb'") != "2.25.2":
        raise ValueError("actual target engine mismatch")


async def wait_ready(params, fixture):
    for _ in range(100):
        try:
            pidfile = fixture.command(["docker", "exec", fixture.name, "cat",
                "/var/lib/postgresql/data/postmaster.pid"], timeout=2)
            if pidfile.splitlines()[0] != "1":
                await asyncio.sleep(.2)
                continue
        except (RuntimeError, IndexError):
            await asyncio.sleep(.2)
            continue
        try:
            conn = await asyncpg.connect(**params, timeout=1, command_timeout=2)
        except (OSError, asyncpg.PostgresError):
            await asyncio.sleep(.2)
            continue
        try:
            await initialize_database(conn)
            return
        finally:
            await conn.close()
    raise TimeoutError("owned fixture startup timeout")


async def fingerprint(conn):
    result = {}
    for table in ("schema_identity", "quotes", "provenance", "publications", "journal"):
        rows = await conn.fetch(f"SELECT * FROM ndx_provenance_v1.{table}")
        hashes = sorted(sha(json.dumps({key: sha(value) if isinstance(value, bytes) else value
            for key, value in row.items()}, sort_keys=True, default=str)) for row in rows)
        result[table] = {"rows": len(rows), "row_hashes": hashes}
    return result


async def restore_check(params, contract, output, fixture):
    source_params = dict(params, database="ndx_observer_resources")
    source = await asyncpg.connect(**source_params, command_timeout=5)
    try:
        recorder = PostgresRecorder(source)
        await recorder.journal(("synthetic-unresolved-restore", 1), "attempt", {
            "evidence_kind": "synthetic", "reason": "intentionally_unpublished_restore_fixture",
            "observed": recorder.clock.stamp()})
        before = await fingerprint(source)
        installation = await recorder.check_schema()
        inventory = [dict(row) for row in await recorder.recovery_inventory()]
        keys = await source.fetch("SELECT snapshot_id,version FROM ndx_provenance_v1.publications "
                                  "ORDER BY snapshot_id,version")
        ack_count = await source.fetchval("SELECT count(*) FROM ndx_provenance_v1.journal "
                                          "WHERE kind='commit_ack'")
    finally:
        await source.close()
    write_json(output / "source-fingerprint.json", before)
    write_json(output / "source-recovery.json", inventory)
    dump = output / "research-schema.dump"
    started = time.perf_counter()
    fixture.command(["docker", "exec", fixture.name, "pg_dump", "-h", "/socket", "-U",
        "ndx_research_test", "-d", "ndx_observer_resources", "--schema=ndx_provenance_v1",
        "--no-owner", "--no-privileges", "--format=custom"], binary_output=dump)
    dump_seconds = time.perf_counter() - started
    expected_dump_hash = digest(dump)
    write_json(output / "dump-manifest.json", {"research-schema.dump": expected_dump_hash})
    if digest(dump) != read_json(output / "dump-manifest.json")[dump.name]:
        raise ValueError("dump manifest verification failed")
    admin = await asyncpg.connect(**params, command_timeout=5)
    try:
        await admin.execute("CREATE DATABASE ndx_observer_restore")
    finally:
        await admin.close()
    restored_params = dict(params, database="ndx_observer_restore")
    restored = await asyncpg.connect(**restored_params, command_timeout=5)
    try:
        await initialize_database(restored)
    finally:
        await restored.close()
    started = time.perf_counter()
    fixture.command(["docker", "exec", "-i", fixture.name, "pg_restore", "-h", "/socket", "-U",
        "ndx_research_test", "-d", "ndx_observer_restore", "--no-owner", "--no-privileges",
        "--single-transaction", "--exit-on-error"], stdin=dump.read_bytes())
    restore_seconds = time.perf_counter() - started
    restored = await asyncpg.connect(**restored_params, command_timeout=5)
    try:
        await restored.execute((ROOT / contract["restore_grants"]).read_text())
        after = await fingerprint(restored)
        if before != after:
            raise ValueError("restored research rows differ")
        recovered = PostgresRecorder(restored)
        if installation != await recovered.check_schema() or inventory != [
                dict(row) for row in await recovered.recovery_inventory()]:
            raise ValueError("restored installation/recovery identity differs")
        await restored.execute("CREATE ROLE ndx_restore_reader LOGIN IN ROLE ndx_evidence_reader")
        write_json(output / "restored-fingerprint.json", after)
        readers = await asyncpg.create_pool(**dict(restored_params, user="ndx_restore_reader"),
                                            min_size=1, max_size=1, command_timeout=2)
        receipts = []
        try:
            consumer = PostgresRecorder(readers)
            for key in keys:
                result = await consumer.read(key["snapshot_id"], key["version"],
                    consumer="synthetic-restored-reader", build_sha256=digest(Path(__file__)))
                if result is None or not result["receipt_journaled"]:
                    raise ValueError("restricted restored read/receipt failed")
                name = next(case["name"] for case in contract["resource_cases"]
                            if key["snapshot_id"].startswith("synthetic-" + case["name"] + "-"))
                if result["response"] != (output / "resources" / (name + ".json")).read_bytes():
                    raise ValueError("restored native body differs from frozen synthetic input")
                if result["assessment"]["replay_eligible"]:
                    raise ValueError("restore must not promote replay eligibility")
                selected = result["document"]["selected"]
                composite = sum(Decimal(q["mark"]) * weight
                                for q, weight in zip(selected, (1, -2, 1)))
                if composite != Decimal("-4.02"):
                    raise ValueError("restored signed composite was changed")
                receipts.append(result["receipt"])
        finally:
            await readers.close()
        write_json(output / "restored-new-receipts.json", receipts)
        if ack_count != await restored.fetchval("SELECT count(*) FROM ndx_provenance_v1.journal "
                                               "WHERE kind='commit_ack'"):
            raise ValueError("restore fabricated an acknowledgement")
        last_inventory = [dict(row) for row in await recovered.recovery_inventory()]
        if last_inventory != inventory or len(receipts) != 9:
            raise ValueError("unexpected restored recovery or receipt count")
        unresolved = [r for r in last_inventory if r["snapshot_id"] == "synthetic-unresolved-restore"]
        if len(unresolved) != 1 or unresolved[0]["published"] or unresolved[0]["acknowledgement_recorded"]:
            raise ValueError("unpublished fixture outcome was altered")
        return {"status": "passed", "dump_sha256": expected_dump_hash,
            "dump_bytes": dump.stat().st_size, "dump_seconds": dump_seconds,
            "restore_seconds": restore_seconds, "installation_id": installation,
            "all_research_rows_identical_before_new_receipts": True,
            "restored_publications": len(keys), "new_restricted_reader_receipts": len(receipts),
            "commit_ack_count_preserved": ack_count, "unpublished_attempt_preserved": True,
            "restore_database_bytes": await restored.fetchval("SELECT pg_database_size("
                                                              "current_database())"),
            "storage_scope": "same task-owned container/local tmpfs; not independent backup"}
    finally:
        await restored.close()


def run(config, source_lock, output):
    sys.path.insert(0, str(ROOT))
    from tools.check_ndx_observer_resources import evaluate
    from tools.check_ndx_timescale import IMAGE, verify_registration

    contract, lock = verify_registration(config, source_lock)
    if contract["model"] != "NDX-exact-target-resources-restore-v1" or contract["target"][
            "image"] != IMAGE:
        raise ValueError("target resource/restore registration mismatch")
    new_directory(output, config.parent)
    (output / "resources").mkdir()
    for filename, path in (("contract.json", config), ("source-lock.json", source_lock)):
        shutil.copy2(path, output / filename)
    for path in lock["source_sha256"]:
        target = output / "source" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    fixture = IsolatedTarget(output, IMAGE)
    summary = {"status": "incomplete", "production_budget_validated": False,
               "independent_backup_validated": False}
    try:
        fixture.start()
        params = {"host": str(fixture.socket), "user": "ndx_research_test", "database": "postgres"}
        asyncio.run(wait_ready(params, fixture))
        resource_contract = dict(contract, self_hash=digest(config))
        resources = asyncio.run(evaluate(params, resource_contract, output / "resources",
            initialize_database=initialize_database, process_sampler=fixture.process_sample))
        if resources["timescaledb"] != "2.25.2":
            raise ValueError("resource database is not the registered target")
        # The helper's own exact_target_gate remains unchanged; this enclosing
        # runner independently verifies actual engine/image identities.
        write_json(output / "target-resources.json", resources)
        restore = asyncio.run(restore_check(params, contract, output, fixture))
        write_json(output / "restore.json", restore)
        fixture.command(["docker", "stats", "--no-stream", "--format", "{{json .}}", fixture.name])
        summary.update(status="passed", image_identity=fixture.identity,
                       target_versions={"postgres": "16.11", "timescaledb": "2.25.2"},
                       resource_acquisitions=12, published=9, oversized=3, restore=restore)
    except Exception as exc:
        summary["failure_category"] = type(exc).__name__
    finally:
        try:
            fixture.close()
        except Exception as exc:
            summary.update(status="incomplete", shutdown_failure=type(exc).__name__)
        summary.update(container_name=fixture.name, container_id=fixture.container_id,
                       container_created=fixture.created, container_stopped=fixture.stopped,
                       retained_local_root=str(fixture.root))
        write_json(output / "summary.json", summary)
        write_json(output / "commands.json", fixture.commands)
        write_json(output / "run.json", {
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "command": shlex.join([sys.executable, *sys.argv]), "python": sys.version,
            "platform": platform.platform(), "config_sha256": digest(config),
            "source_lock_sha256": digest(source_lock), "source_sha256": lock["source_sha256"],
            "parent_hashes": contract["parents"], "dependencies": {
                d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
            "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
            "output_sha256": {str(p.relative_to(output)): digest(p)
                              for p in output.rglob("*") if p.is_file()}})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("config", "source-lock", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    args = vars(parser.parse_args())
    result = run(**args)
    print(encode(result))
    raise SystemExit(0 if result["status"] == "passed" else 1)
