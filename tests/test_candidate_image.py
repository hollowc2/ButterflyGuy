from pathlib import Path


def test_candidate_image_removes_broker_write_modules() -> None:
    root = Path(__file__).resolve().parents[1]
    dockerfile = (root / "Dockerfile.candidate").read_text()

    for path in (
        "butterfly_guy/execution",
        "butterfly_guy/data/schwab_client.py",
        "butterfly_guy/services/trade_service.py",
        "butterfly_guy/services/position_service.py",
        "butterfly_guy/scripts/run_live.py",
    ):
        assert path in dockerfile
