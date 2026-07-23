from pathlib import Path

from butterfly_guy.candidate_fleet.registry import (
    CandidateRegistration,
    CandidateRegistry,
    render_runtime,
    validate_registry,
)

ROOT = Path(__file__).resolve().parents[1]


def registry() -> CandidateRegistry:
    return CandidateRegistry(
        candidates=[
            CandidateRegistration(
                id="best-rr",
                enabled=True,
                slot=0,
                config_path="configs/config_spx_candidate.yaml",
                database_name="butterfly_guy_spx_candidate",
                review_trade_count=20,
            )
        ]
    )


def test_registry_validates_candidate_safety() -> None:
    assert validate_registry(registry(), repository_root=ROOT) == []


def test_runtime_generation_is_deterministic_and_candidate_env_is_safe() -> None:
    first = render_runtime(registry(), git_sha="abc123")
    second = render_runtime(registry(), git_sha="abc123")

    assert first == second
    assert "butterfly_guy_spx_candidate" in first.compose
    assert "127.0.0.1:8100:8000" in first.compose
    assert "Dockerfile.candidate" in first.compose
    assert "mem_limit: 256m" in first.compose
    assert "env_file" not in first.compose.split("spx_candidate_best_rr:", 1)[1]
    candidate_section = first.compose.split("spx_candidate_best_rr:", 1)[1]
    for forbidden in (
        "SCHWAB_API_KEY",
        "SCHWAB_ACCOUNT_ID",
        "tokens.json",
        "ALLOW_LIVE_TRADING",
        "DISCORD",
        "TELEGRAM",
    ):
        assert forbidden not in candidate_section
    assert "Candidate best-rr" in first.grafana_datasources


def test_disabling_candidate_preserves_database_and_requires_explicit_profile() -> None:
    disabled = registry()
    disabled.candidates[0].enabled = False

    runtime = render_runtime(disabled)

    assert "spx_candidate_best_rr:" in runtime.compose
    assert "candidate-disabled" in runtime.compose
    assert "Candidate best-rr" in runtime.grafana_datasources
    assert "spx_candidate_best_rr:8000" not in runtime.prometheus_targets
    assert "DROP DATABASE" not in runtime.compose
