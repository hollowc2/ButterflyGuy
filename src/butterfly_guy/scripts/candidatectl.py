"""Validate, render, plan, and apply the isolated SPX candidate fleet."""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from butterfly_guy.candidate_fleet.registry import (
    DATABASE_PATTERN,
    CandidateRegistry,
    RenderedRuntime,
    load_registry,
    render_runtime,
    validate_registry,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = ROOT / "configs/candidates.yaml"
GENERATED = ROOT / "infra/generated"
COMPOSE_PATH = GENERATED / "docker-compose.candidates.yml"
PROMETHEUS_PATH = GENERATED / "prometheus-candidates.json"
DATASOURCE_PATH = GENERATED / "grafana-candidate-datasources.yml"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def _validated(path: Path) -> CandidateRegistry:
    registry = load_registry(path)
    errors = validate_registry(registry, repository_root=ROOT)
    if errors:
        raise RuntimeError("\n".join(errors))
    return registry


def _rendered(registry: CandidateRegistry) -> RenderedRuntime:
    return render_runtime(registry, git_sha=_git_sha())


def _write_runtime(runtime: RenderedRuntime) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    COMPOSE_PATH.write_text(runtime.compose)
    PROMETHEUS_PATH.write_text(runtime.prometheus_targets)
    DATASOURCE_PATH.write_text(runtime.grafana_datasources)


def _changed(path: Path, content: str) -> bool:
    return not path.exists() or path.read_text() != content


async def _database_states(registry: CandidateRegistry) -> dict[str, bool] | None:
    password = os.getenv("DATABASE_PASSWORD")
    if password is None:
        return None
    connection = await asyncpg.connect(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        database=os.getenv("DATABASE_ADMIN_NAME", "postgres"),
        user=os.getenv("DATABASE_USER", "butterfly"),
        password=password,
    )
    try:
        names = [
            "butterfly_guy_candidate_market",
            *(candidate.database_name for candidate in registry.candidates),
        ]
        rows = await connection.fetch(
            "SELECT datname FROM pg_database WHERE datname = ANY($1::text[])",
            names,
        )
        existing = {row["datname"] for row in rows}
        return {name: name in existing for name in names}
    finally:
        await connection.close()


async def _provision_databases(registry: CandidateRegistry) -> None:
    states = await _database_states(registry)
    if states is None:
        raise RuntimeError("DATABASE_PASSWORD is required to provision databases")
    missing = [name for name, exists in states.items() if not exists]
    if not missing:
        return
    connection = await asyncpg.connect(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        database=os.getenv("DATABASE_ADMIN_NAME", "postgres"),
        user=os.getenv("DATABASE_USER", "butterfly"),
        password=os.environ["DATABASE_PASSWORD"],
    )
    try:
        for name in missing:
            if not DATABASE_PATTERN.fullmatch(name):
                raise RuntimeError(f"refusing invalid database name: {name}")
            try:
                await connection.execute(f'CREATE DATABASE "{name}"')
            except asyncpg.DuplicateDatabaseError:
                pass
    finally:
        await connection.close()


async def _run(args: argparse.Namespace) -> int:
    registry = _validated(Path(args.registry))
    runtime = _rendered(registry)
    if args.command == "validate":
        print(f"valid: {len(registry.candidates)} candidate(s)")
        return 0
    if args.command == "render":
        _write_runtime(runtime)
        print(f"rendered: {GENERATED}")
        return 0
    if args.command == "plan":
        changes = {
            str(COMPOSE_PATH.relative_to(ROOT)): _changed(COMPOSE_PATH, runtime.compose),
            str(PROMETHEUS_PATH.relative_to(ROOT)): _changed(
                PROMETHEUS_PATH,
                runtime.prometheus_targets,
            ),
            str(DATASOURCE_PATH.relative_to(ROOT)): _changed(
                DATASOURCE_PATH,
                runtime.grafana_datasources,
            ),
        }
        states = await _database_states(registry)
        for path, changed in changes.items():
            print(f"{'change' if changed else 'unchanged'} {path}")
        if states is None:
            print("database status unavailable (DATABASE_PASSWORD not set)")
        else:
            for name, exists in states.items():
                print(f"{'existing' if exists else 'create'} database {name}")
        for candidate in registry.candidates:
            action = "start/recreate" if candidate.enabled else "preserve stopped state"
            print(f"{action} candidate {candidate.id}")
        print("no databases will be dropped")
        return 0
    if args.command == "apply":
        _write_runtime(runtime)
        await _provision_databases(registry)
        command = [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_PATH),
            "up",
            "-d",
        ]
        enabled_services = ["spx_candidate_feed"] + [
            f"spx_candidate_{candidate.id.replace('-', '_')}"
            for candidate in registry.candidates
            if candidate.enabled
        ]
        subprocess.run([*command, *enabled_services], cwd=ROOT, check=True)
        if args.stop_disabled:
            disabled = [
                f"spx_candidate_{candidate.id.replace('-', '_')}"
                for candidate in registry.candidates
                if not candidate.enabled
            ]
            if disabled:
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(COMPOSE_PATH),
                        "stop",
                        *disabled,
                    ],
                    cwd=ROOT,
                    check=True,
                )
        print("applied enabled services; no databases were dropped")
        return 0
    raise RuntimeError(f"unknown command: {args.command}")


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(prog="candidatectl")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    subparsers.add_parser("render")
    subparsers.add_parser("plan")
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument(
        "--stop-disabled",
        action="store_true",
        help="explicitly stop disabled candidate containers; databases are preserved",
    )
    try:
        return asyncio.run(_run(parser.parse_args()))
    except Exception as exc:
        parser.exit(1, f"candidatectl: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
