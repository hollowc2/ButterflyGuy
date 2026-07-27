from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from butterfly_guy.candidate_fleet.registry import (
    CandidateRegistration,
    CandidateRegistry,
    load_registry,
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


def _leaf_values(value: object, prefix: str = "") -> dict[str, object]:
    if not isinstance(value, dict):
        return {prefix: value}
    leaves: dict[str, object] = {}
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        leaves.update(_leaf_values(child, path))
    return leaves


def test_review_gate_rejects_fewer_than_twenty_closed_trades() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 20"):
        CandidateRegistration(
            id="too-short",
            enabled=False,
            slot=1,
            config_path="configs/config_spx_candidate.yaml",
            database_name="butterfly_guy_spx_candidate_too_short",
            review_trade_count=19,
        )


def test_candidate_registration_defaults_to_disabled() -> None:
    registration = CandidateRegistration(
        id="safe-default",
        slot=1,
        config_path="configs/config_spx_candidate.yaml",
        database_name="butterfly_guy_spx_candidate_safe_default",
        review_trade_count=20,
    )

    assert registration.enabled is False


def test_approved_candidate_registry_is_activated_isolated_and_safe() -> None:
    approved = load_registry(ROOT / "configs/candidates.yaml")

    assert [(item.id, item.slot, item.enabled) for item in approved.candidates] == [
        ("best-rr", 0, False),
        ("vix-center", 1, True),
        ("target-cost", 2, True),
        ("gap-conviction", 3, True),
        ("peak-trailer", 4, True),
        ("absolute-stop", 5, True),
    ]
    assert len({item.database_name for item in approved.candidates}) == 6
    assert validate_registry(approved, repository_root=ROOT) == []

    runtime = render_runtime(approved, git_sha="review")
    compose = yaml.safe_load(runtime.compose)
    feed = compose["services"]["spx_candidate_feed"]
    assert "env_file" not in feed
    assert feed["volumes"] == ["../../tokens.json:/app/tokens.json:ro"]
    assert set(feed["environment"]) == {
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD",
        "SCHWAB_API_KEY",
        "SCHWAB_SECRET_KEY",
        "SCHWAB_TOKEN_PATH",
    }
    assert feed["read_only"] is True
    assert feed["cap_drop"] == ["ALL"]
    for item in approved.candidates:
        service = compose["services"][f"spx_candidate_{item.id.replace('-', '_')}"]
        if item.id == "best-rr":
            assert service["profiles"] == ["candidate-disabled"]
        else:
            assert "profiles" not in service
        assert service["ports"] == [f"127.0.0.1:{8100 + item.slot}:8000"]
        assert service["environment"]["DATABASE__NAME"] == item.database_name
        assert service["environment"]["CANDIDATE_FEED_URL"] == (
            "http://spx_candidate_feed:8099"
        )
        assert service["read_only"] is True
        assert service["cap_drop"] == ["ALL"]
    assert "spx_candidate_best_rr:8000" not in runtime.prometheus_targets
    assert runtime.prometheus_targets.count('"job": "spx_candidate_evaluator"') == 5


def test_candidate_configs_each_change_only_the_approved_decision() -> None:
    baseline = yaml.safe_load((ROOT / "configs/config_spx_candidate.yaml").read_text())
    baseline_leaves = _leaf_values(baseline)
    expected_changes = {
        "config_spx_candidate_vix_center.yaml": {
            "entry.strike_selection_method": "VIX"
        },
        "config_spx_candidate_target_cost.yaml": {
            "entry.strike_selection_method": "TARGET_COST"
        },
        "config_spx_candidate_gap_conviction.yaml": {"entry.min_gap_pct": 0.0025},
        "config_spx_candidate_peak_trailer.yaml": {
            "profit_management.strategy": "peakvaluetrailer"
        },
        "config_spx_candidate_absolute_stop.yaml": {
            "profit_management.use_absolute_loss_stop": True
        },
    }

    for filename, expected in expected_changes.items():
        candidate = yaml.safe_load((ROOT / "configs" / filename).read_text())
        candidate_leaves = _leaf_values(candidate)
        changed = {
            key: value
            for key, value in candidate_leaves.items()
            if baseline_leaves.get(key) != value
        }
        removed = set(baseline_leaves) - set(candidate_leaves)

        assert changed == expected
        assert removed == set()
        assert candidate["execution"]["paper_trading"] is True
        assert candidate["execution"]["allow_live_trading"] is False
        assert candidate["risk"]["max_position_size"] == 1
        assert candidate["risk"]["max_trades_per_day"] == 1
        assert "notifications" not in candidate
        assert "database" not in candidate


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        (("risk", "max_trades_per_day", 2), "risk.max_trades_per_day must be 1"),
        (("monitoring", "metrics_port", 9000), "monitoring.metrics_port must be 8000"),
        (
            ("database", "name", "butterfly_guy_other"),
            "candidate config must not override database",
        ),
    ],
)
def test_registry_rejects_candidate_safety_drift(
    tmp_path: Path,
    mutation: tuple[str, str, object],
    expected_error: str,
) -> None:
    payload = yaml.safe_load((ROOT / "configs/config_spx_candidate.yaml").read_text())
    section, key, value = mutation
    payload.setdefault(section, {})[key] = value
    config_path = tmp_path / "candidate.yaml"
    config_path.write_text(yaml.safe_dump(payload))
    candidate = CandidateRegistry(
        candidates=[
            CandidateRegistration(
                id="safety-drift",
                enabled=False,
                slot=1,
                config_path=config_path.name,
                database_name="butterfly_guy_spx_candidate_safety_drift",
                review_trade_count=20,
            )
        ]
    )

    assert any(
        expected_error in error
        for error in validate_registry(candidate, repository_root=tmp_path)
    )


def test_registry_rejects_reserved_database_for_new_candidate() -> None:
    candidate = CandidateRegistry(
        candidates=[
            CandidateRegistration(
                id="database-reuse",
                enabled=False,
                slot=1,
                config_path="configs/config_spx_candidate.yaml",
                database_name="butterfly_guy_spx_candidate",
                review_trade_count=20,
            )
        ]
    )

    assert any(
        "database_name is reserved" in error
        for error in validate_registry(candidate, repository_root=ROOT)
    )


def test_registry_pins_standalone_candidate_resources() -> None:
    candidate = CandidateRegistry(
        candidates=[
            CandidateRegistration(
                id="best-rr",
                enabled=False,
                slot=1,
                config_path="configs/config_spx_candidate_vix_center.yaml",
                database_name="butterfly_guy_spx_candidate_vix_center",
                review_trade_count=20,
            )
        ]
    )

    errors = validate_registry(candidate, repository_root=ROOT)

    assert any("slot must remain 0" in error for error in errors)
    assert any(
        "config_path must remain 'configs/config_spx_candidate.yaml'" in error
        for error in errors
    )
    assert any(
        "database_name must remain 'butterfly_guy_spx_candidate'" in error
        for error in errors
    )


def test_registry_requires_comparable_risk_profiles(tmp_path: Path) -> None:
    baseline = yaml.safe_load((ROOT / "configs/config_spx_candidate.yaml").read_text())
    drifted = yaml.safe_load((ROOT / "configs/config_spx_candidate.yaml").read_text())
    drifted["risk"]["max_daily_loss"] = 750.0
    (tmp_path / "baseline.yaml").write_text(yaml.safe_dump(baseline))
    (tmp_path / "drifted.yaml").write_text(yaml.safe_dump(drifted))
    candidate = CandidateRegistry(
        candidates=[
            CandidateRegistration(
                id="baseline",
                enabled=False,
                slot=1,
                config_path="baseline.yaml",
                database_name="butterfly_guy_spx_candidate_baseline",
                review_trade_count=20,
            ),
            CandidateRegistration(
                id="risk-drift",
                enabled=False,
                slot=2,
                config_path="drifted.yaml",
                database_name="butterfly_guy_spx_candidate_risk_drift",
                review_trade_count=20,
            ),
        ]
    )

    assert any(
        error == "risk-drift: risk settings must match baseline"
        for error in validate_registry(candidate, repository_root=tmp_path)
    )
