import yaml

from butterfly_guy.candidate_fleet.registry import (
    CandidateRegistration,
    CandidateRegistry,
    render_runtime,
)


def test_ten_candidate_runtime_stays_within_declared_resource_bounds() -> None:
    registry = CandidateRegistry(
        candidates=[
            CandidateRegistration(
                id=f"variant-{index}",
                enabled=True,
                slot=index,
                config_path=f"configs/variant-{index}.yaml",
                database_name=f"butterfly_guy_variant_{index}",
                review_trade_count=20,
            )
            for index in range(10)
        ]
    )

    runtime = render_runtime(registry, git_sha="acceptance")
    compose = yaml.safe_load(runtime.compose)
    services = compose["services"]
    evaluators = {
        name: service
        for name, service in services.items()
        if name.startswith("spx_candidate_variant_")
    }

    assert list(services).count("spx_candidate_feed") == 1
    assert len(evaluators) == 10
    assert {
        service["ports"][0].split(":")[1]
        for service in evaluators.values()
    } == {str(port) for port in range(8100, 8110)}
    assert len(
        {
            service["environment"]["DATABASE__NAME"]
            for service in evaluators.values()
        }
    ) == 10
    fleet_memory_mib = 384 + sum(
        int(service["mem_limit"].removesuffix("m"))
        for service in evaluators.values()
    )
    assert fleet_memory_mib < 3 * 1024
    assert runtime.prometheus_targets.count("spx_candidate_feed:8099") == 1
