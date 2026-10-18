"""Validate ONLY the frozen target image in a private task-owned Docker fixture.

Never starts a daemon or accepts a DSN, image override, existing container/volume,
broker endpoint or secret. Failed runs are retained with an incomplete gate.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import asyncpg

from butterfly_guy.research.ndx_continuation import ROOT, verify_parent
from butterfly_guy.research.ndx_evidence import digest, new_directory, read_json, write_json

IMAGE = "timescale/timescaledb@sha256:0af03ecf697825f6ddae76fd275d16bf46007bed6d00eb3d754779cb7db96fa6"


def verify_registration(config, source_lock):
    contract, lock = read_json(config), read_json(source_lock)
    if lock["config_sha256"] != digest(config):
        raise ValueError("observer contract drift")
    for path, expected in lock["source_sha256"].items():
        if digest(ROOT / path) != expected:
            raise ValueError(f"source drift: {path}")
    for parent in contract["parents"].values():
        verify_parent(ROOT / parent["path"], parent["run_sha256"])
    return contract, lock


def run(config, source_lock, output):
    contract, lock = verify_registration(config, source_lock)
    if contract["target"]["image"] != IMAGE or contract["target"]["architecture"] != "amd64":
        raise ValueError("exact target contract mismatch")
    new_directory(output, config.parent)
    token = uuid.uuid4().hex
    root = Path("/tmp") / ("ndx-timescale-" + token)
    root.mkdir(mode=0o700)
    socket = root / "socket"
    socket.mkdir(mode=0o777)
    socket.chmod(0o777)  # Container postgres UID; private parent remains mode 0700.
    name = "ndx-timescale-" + token
    commands = []
    created = False
    result = {"gate": "incomplete", "reason": "not_executed", "container_name": name,
              "container_created": False, "container_stopped": None,
              "owned_local_root": str(root), "requested_image": IMAGE}

    def command(args, *, timeout=60):
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        entry = {"command": shlex.join(args), "returncode": proc.returncode,
                 "stdout": proc.stdout, "stderr": proc.stderr}
        commands.append(entry)
        if proc.returncode:
            raise RuntimeError("isolated_command_failed")
        return proc.stdout

    try:
        command(["docker", "version"])
        command(["docker", "pull", "--platform", "linux/amd64", IMAGE], timeout=300)
        identity = [json.loads(part) for part in command([
            "docker", "image", "inspect", IMAGE, "--format",
            '{{json .Id}}|{{json .RepoDigests}}|{{json .Architecture}}']).strip().split("|")]
        result["image_identity"] = identity
        if IMAGE not in identity[1] or identity[2] != "amd64":
            raise ValueError("resolved target manifest/architecture discrepancy")
        result["container_id"] = command(["docker", "run", "--detach", "--name", name,
            "--label", "ndx.observer-test=" + token, "--network", "none",
            "--memory", "1g", "--cpus", "1", "--pids-limit", "128",
            "--tmpfs", "/var/lib/postgresql/data:rw,size=512m",
            "--mount", f"type=bind,src={socket},dst=/socket",
            "--env", "POSTGRES_HOST_AUTH_METHOD=trust", "--env", "POSTGRES_USER=ndx_research_test",
            "--env", "PGHOST=/socket",
            "--entrypoint", "/bin/sh", IMAGE, "-c",
            "trap 'exit 0' TERM INT; "
            "docker-entrypoint.sh postgres -c listen_addresses= "
            "-c unix_socket_directories=/var/run/postgresql,/socket "
            "-c shared_preload_libraries=timescaledb & "
            "echo $! > /tmp/ndx-server-owner.pid; "
            "while :; do sleep 1; done"]).strip()
        # Shell PID 1 keeps the private tmpfs alive during the pg_ctl restart test.
        # A Docker container restart would discard tmpfs and cannot test recovery.
        created = result["container_created"] = True
        async def ready():
            for _ in range(100):
                try:
                    owner = command(["docker", "exec", name, "cat", "/tmp/ndx-server-owner.pid"])
                except RuntimeError:
                    await asyncio.sleep(.2)
                    continue
                # Match the original entrypoint child, which execs the final
                # postmaster only AFTER bootstrap SQL and its temporary server end.
                probe = subprocess.run(["docker", "exec", name, "head", "-n", "1",
                    "/var/lib/postgresql/data/postmaster.pid"], capture_output=True,
                    text=True, timeout=2)
                if probe.returncode or probe.stdout.strip() != owner.strip():
                    await asyncio.sleep(.2)
                    continue
                try:
                    conn = await asyncpg.connect(host=str(socket), user="ndx_research_test",
                                                 database="postgres", timeout=1)
                except (OSError, asyncpg.PostgresError):
                    await asyncio.sleep(.2)
                    continue
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb VERSION '2.25.2'")
                    server = await conn.fetchval("SHOW server_version")
                    extension = await conn.fetchval("SELECT extversion FROM pg_extension "
                                                     "WHERE extname='timescaledb'")
                    if (server, extension) != ("16.11", "2.25.2"):
                        raise ValueError("actual target engine/extension mismatch")
                    return {"server_version": server, "timescaledb": extension}
                finally:
                    await conn.close()
            raise TimeoutError("isolated_target_startup_timeout")
        result["engine"] = asyncio.run(ready())
        env = dict(os.environ, NDX_TIMESCALE_SOCKET=str(socket))
        tests = [sys.executable, "-m", "pytest", "tests/test_ndx_postgres_recording.py",
                 "tests/test_ndx_native_response.py", "tests/test_ndx_observer.py", "-q",
                 "--junitxml=" + str((output / "tests.xml").resolve())]
        proc = subprocess.run(tests, env=env, capture_output=True, text=True, timeout=180)
        commands.append({"command": shlex.join(tests), "environment": {
            "NDX_TIMESCALE_SOCKET": str(socket)}, "returncode": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr})
        if proc.returncode:
            raise RuntimeError("exact_target_tests_failed")
        result["gate"] = "passed"
        result["reason"] = "actual_exact_engine_and_restricted_role_checks_passed"
        command(["docker", "stats", "--no-stream", "--format", "{{json .}}", name])
        command(["docker", "exec", name, "cat", "/tmp/ndx-restart.log"])
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as exc:
        # Command diagnostics contain only our synthetic fixture, never live environments.
        result["reason"] = type(exc).__name__ + ":exact_target_unavailable_or_failed"
    finally:
        if created:
            try:
                command(["docker", "logs", name])
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                result["log_capture_failed"] = True
            finally:
                try:
                    command(["docker", "stop", "--time", "5", name], timeout=15)
                    result["container_stopped"] = True
                except (RuntimeError, OSError, subprocess.TimeoutExpired):
                    result["container_stopped"] = False
                    result["gate"] = "incomplete"
        write_json(output / "commands.json", commands)
        write_json(output / "summary.json", result)
        for file, path in (("contract.json", config), ("source-lock.json", source_lock)):
            shutil.copy2(path, output / file)
        for path in lock["source_sha256"]:
            target = output / "source" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, target)
        write_json(output / "run.json", {
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "command": shlex.join([sys.executable, *sys.argv]),
            "python": sys.version, "platform": platform.platform(),
            "config_sha256": digest(config), "source_lock_sha256": digest(source_lock),
            "parents": contract["parents"],
            "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
            "output_sha256": {str(p.relative_to(output)): digest(p)
                              for p in output.rglob("*") if p.is_file()}})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("config", "source-lock", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.config, args.source_lock, args.output), indent=2))
