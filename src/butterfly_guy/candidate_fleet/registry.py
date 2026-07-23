"""Validated source of truth and deterministic runtime rendering for candidates."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from butterfly_guy.core.config import AppConfig

ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATABASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


class CandidateRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    enabled: bool = True
    slot: int = Field(ge=0, le=9)
    config_path: str
    database_name: str
    review_trade_count: int = Field(gt=0)


class CandidateRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[CandidateRegistration]

    @model_validator(mode="after")
    def validate_unique_runtime_resources(self) -> CandidateRegistry:
        errors: list[str] = []
        for field in ("id", "slot", "config_path", "database_name"):
            values = [getattr(candidate, field) for candidate in self.candidates]
            duplicates = sorted({value for value in values if values.count(value) > 1})
            if duplicates:
                errors.append(f"duplicate {field}: {duplicates}")
        if len(self.candidates) > 10:
            errors.append("at most 10 candidates may be registered")
        if errors:
            raise ValueError("; ".join(errors))
        return self


@dataclass(frozen=True)
class RenderedRuntime:
    compose: str
    prometheus_targets: str
    grafana_datasources: str


def load_registry(path: str | Path) -> CandidateRegistry:
    registry_path = Path(path)
    with registry_path.open() as file:
        return CandidateRegistry(**(yaml.safe_load(file) or {}))


def validate_registry(
    registry: CandidateRegistry,
    *,
    repository_root: str | Path,
) -> list[str]:
    root = Path(repository_root).resolve()
    errors: list[str] = []
    for candidate in registry.candidates:
        prefix = candidate.id
        if not ID_PATTERN.fullmatch(candidate.id):
            errors.append(f"{prefix}: id must be a stable lowercase slug")
        if not DATABASE_PATTERN.fullmatch(candidate.database_name):
            errors.append(f"{prefix}: invalid PostgreSQL database name")
        config_path = (root / candidate.config_path).resolve()
        try:
            config_path.relative_to(root)
        except ValueError:
            errors.append(f"{prefix}: config_path escapes repository root")
            continue
        if not config_path.is_file():
            errors.append(f"{prefix}: config_path does not exist")
            continue
        try:
            with config_path.open() as config_file:
                payload = yaml.safe_load(config_file) or {}
            payload["schwab"] = {}
            config = AppConfig(**payload)
        except Exception as exc:
            errors.append(f"{prefix}: invalid config: {exc}")
            continue
        if config.strategy.underlying != "SPX":
            errors.append(f"{prefix}: strategy.underlying must be SPX")
        if not config.execution.paper_trading:
            errors.append(f"{prefix}: execution.paper_trading must be true")
        if config.execution.allow_live_trading:
            errors.append(f"{prefix}: execution.allow_live_trading must be false")
        if config.risk.max_position_size != 1:
            errors.append(f"{prefix}: risk.max_position_size must be 1")
        if "notifications" in payload:
            errors.append(f"{prefix}: candidate notification config is not allowed")
    return errors


def render_runtime(
    registry: CandidateRegistry,
    *,
    git_sha: str = "unknown",
) -> RenderedRuntime:
    services: dict[str, Any] = {
        "spx_candidate_feed": {
            "build": {"context": "../..", "dockerfile": "Dockerfile"},
            "container_name": "butterfly_spx_candidate_feed",
            "restart": "unless-stopped",
            "command": [
                "python",
                "-m",
                "butterfly_guy.scripts.run_candidate_feed",
                "--port",
                "8099",
            ],
            "env_file": ["../../.env"],
            "volumes": ["../../tokens.json:/app/tokens.json:ro"],
            "environment": {
                "DATABASE_HOST": "timescaledb",
                "DATABASE_PORT": "5432",
                "DATABASE_NAME": "butterfly_guy_candidate_market",
                "DATABASE_USER": "butterfly",
                "SCHWAB_TOKEN_PATH": "tokens.json",
            },
            "read_only": True,
            "mem_limit": "384m",
            "tmpfs": ["/tmp"],
            "security_opt": ["no-new-privileges:true"],
            "cap_drop": ["ALL"],
            "networks": ["monitoring_net"],
        }
    }
    targets = [
        {
            "targets": ["spx_candidate_feed:8099"],
            "labels": {"job": "spx_candidate_feed", "service": "shared-feed"},
        }
    ]
    datasources: list[dict[str, Any]] = []
    for candidate in sorted(registry.candidates, key=lambda item: (item.slot, item.id)):
        service_name = f"spx_candidate_{candidate.id.replace('-', '_')}"
        container_name = f"butterfly_spx_candidate_{candidate.id}"
        config_name = Path(candidate.config_path).name
        services[service_name] = {
            "build": {"context": "../..", "dockerfile": "Dockerfile.candidate"},
            "container_name": container_name,
            "restart": "unless-stopped",
            "depends_on": ["spx_candidate_feed"],
            "command": [
                "python",
                "-m",
                "butterfly_guy.scripts.run_candidate",
                "--config",
                f"configs/{config_name}",
            ],
            "volumes": [
                f"../../{candidate.config_path}:/app/configs/{config_name}:ro"
            ],
            "environment": {
                "CANDIDATE_ID": candidate.id,
                "CANDIDATE_FEED_URL": "http://spx_candidate_feed:8099",
                "CANDIDATE_REVIEW_TRADE_COUNT": str(candidate.review_trade_count),
                "DATABASE__HOST": "timescaledb",
                "DATABASE__PORT": "5432",
                "DATABASE__NAME": candidate.database_name,
                "DATABASE__USER": "butterfly",
                "DATABASE__PASSWORD": "${DATABASE_PASSWORD}",
                "DEPLOYED_GIT_SHA": git_sha,
            },
            "read_only": True,
            "mem_limit": "256m",
            "tmpfs": ["/tmp"],
            "security_opt": ["no-new-privileges:true"],
            "cap_drop": ["ALL"],
            "networks": ["monitoring_net"],
            "ports": [f"127.0.0.1:{8100 + candidate.slot}:8000"],
        }
        if not candidate.enabled:
            services[service_name]["profiles"] = ["candidate-disabled"]
        else:
            targets.append(
                {
                    "targets": [f"{service_name}:8000"],
                    "labels": {
                        "job": "spx_candidate_evaluator",
                        "candidate_id": candidate.id,
                        "slot": str(candidate.slot),
                        "review_trade_count": str(candidate.review_trade_count),
                    },
                },
            )
        datasources.append(
            {
                "name": f"Candidate {candidate.id}",
                "uid": f"candidate-{candidate.id}",
                "type": "postgres",
                "url": "timescaledb:5432",
                "user": "butterfly",
                "jsonData": {
                    "database": candidate.database_name,
                    "sslmode": "disable",
                    "postgresVersion": 1600,
                    "timescaledb": True,
                },
                "secureJsonData": {"password": "${DATABASE_PASSWORD}"},
                "editable": False,
            }
        )
    compose = yaml.safe_dump(
        {
            "networks": {"monitoring_net": {"external": True}},
            "services": services,
        },
        sort_keys=False,
    )
    prometheus = json.dumps(targets, indent=2, sort_keys=True) + "\n"
    grafana = yaml.safe_dump(
        {"apiVersion": 1, "datasources": datasources},
        sort_keys=False,
    )
    return RenderedRuntime(compose, prometheus, grafana)
