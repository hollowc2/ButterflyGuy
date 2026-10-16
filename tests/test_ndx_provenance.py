"""Independent expected categories and adversarial checks for provenance, never economics."""

import copy
import json
import os
import socket

import pytest

from butterfly_guy.research.ndx_evidence import digest, read_json
from butterfly_guy.research.ndx_provenance import ROOT, Record, assess, run

PACKAGE = ROOT / "docs/research/ndx-strategy/provenance-v1"
FIXTURES = [json.loads(s) for s in (PACKAGE / "fixtures.jsonl").read_text().splitlines()]
EXPECTED = read_json(PACKAGE / "expectations.json")
CONFIG = PACKAGE / "contract.json"
LOCK = PACKAGE / "source-lock.json"


@pytest.mark.parametrize("raw", FIXTURES, ids=lambda r: r["record_id"])
def test_independent_fixture_expectations(raw):
    result = assess(raw, PACKAGE)
    expected = EXPECTED[raw["record_id"]]
    assert result["status"] == expected["status"], result
    reason = expected["reason_contains"]
    if reason:
        assert any(reason in s for s in result["unknown"] + result["rejected"]
                   + result["diagnostics"]), result
    assert result["decision"] is result["fill"] is None
    assert result["earliest_availability"] is None
    assert not result["freshness_verified"] and not result["replay_eligible"]
    assert raw["evidence_kind"] == "synthetic"


def test_schema_is_the_registered_model():
    assert read_json(PACKAGE / "record.schema.json") == Record.model_json_schema()


def test_independent_signed_arithmetic_and_missingness():
    raw = FIXTURES[6]
    result = assess(raw, PACKAGE)
    # Hand calculation: 10.10 - 2*12.11 + 10.10; bid 10 - 2*12.2 + 10.
    assert result["raw_composites"] == {
        "provider_mark": "-4.02", "bid": "-4.40", "ask": "-3.60", "midpoint": "-4.00"
    }
    partial = FIXTURES[4]
    assert partial["legs"][0]["age_seconds"] is None
    assert partial["legs"][1]["age_seconds"] == "0"
    assert "missing_leg:" in "|".join(assess(partial, PACKAGE)["unknown"])


@pytest.mark.parametrize("mutation,reason", [
    (lambda r: r["payload"].update(sha256="0" * 64), "original_response_hash_mismatch"),
    (lambda r: r["payload"].update(path="../escape"), "unsafe_payload_path"),
    (lambda r: r["consumer"].update(returned_snapshot_id="wrong"), "consumer_snapshot_mismatch"),
    (lambda r: r["legs"][0].update(bid="NaN"), "schema:"),
    (lambda r: r["stamps"]["response_receipt"].update(wall_utc="2030-01-02T19:59:02"),
     "invalid_utc:"),
    (lambda r: r["stamps"]["read_end"].update(monotonic_ns=0), "monotonic_reversal:"),
    (lambda r: r["legs"][0]["event"].update(wall_utc="2030-01-02T20:01:00Z"),
     "event_after_fetch_in_same_clock:"),
])
def test_contradictions_are_rejections(mutation, reason):
    raw = copy.deepcopy(FIXTURES[0])
    mutation(raw)
    result = assess(raw, PACKAGE)
    assert result["status"] == "rejected"
    assert any(reason in s for s in result["rejected"])


def test_unknown_build_drop_and_read_are_not_zero_observations():
    raw = copy.deepcopy(FIXTURES[0])
    raw["builds"]["gateway"] = None
    raw["dropped_records"] = None
    raw["consumer"]["returned_symbols"].pop()
    result = assess(raw, PACKAGE)
    assert result["status"] == "insufficient"
    assert "missing_build:gateway" in result["unknown"]
    assert "dropped_record_coverage_unknown" in result["unknown"]
    assert "consumer_complete_snapshot_unproven" in result["unknown"]


def test_publication_hash_and_identity(tmp_path):
    raw = copy.deepcopy(FIXTURES[1])
    pub = raw["publication"]
    pub["complete_manifest_sha256"] = "0" * 64
    assert "publication_manifest_hash_mismatch" in assess(raw, PACKAGE)["rejected"]
    payload = PACKAGE / raw["payload"]["path"]
    (tmp_path / payload.name).write_bytes(payload.read_bytes())
    manifest = read_json(PACKAGE / pub["complete_manifest_path"])
    manifest["snapshot_id"] = "wrong"
    target = tmp_path / pub["complete_manifest_path"]
    target.write_text(json.dumps(manifest))
    pub["complete_manifest_sha256"] = digest(target)
    assert "publication_manifest_identity_mismatch" in assess(raw, tmp_path)["rejected"]


def test_changed_contract_refuses_before_private_access(tmp_path):
    config = tmp_path / "contract.json"
    config.write_text('{"model":"NDX-provenance-v1"}')
    lock = tmp_path / "lock.json"
    lock.write_text('{"config_sha256":"wrong"}')
    with pytest.raises(ValueError, match="config/source lock mismatch"):
        run(PACKAGE / "fixtures.jsonl", config, lock, tmp_path / "output")


@pytest.mark.skipif(not os.environ.get("NDX_FIDELITY_EVIDENCE"),
                    reason="private NDX parent snapshots required")
def test_offline_full_verification_overwrite_and_drift(tmp_path, monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "socket", blocked)
    output = tmp_path / "new-run"
    summary = run(PACKAGE / "fixtures.jsonl", CONFIG, LOCK, output)
    assert summary["records"] == len(FIXTURES)
    assert summary["synthetic_records"] == len(FIXTURES)
    assert summary["new_historical_coverage"] == 0
    manifest = read_json(output / "run.json")
    assert len(manifest["verified_snapshot_files"]) == 5
    for name, expected in manifest["output_sha256"].items():
        assert digest(output / name) == expected
    with pytest.raises(FileExistsError):
        run(PACKAGE / "fixtures.jsonl", CONFIG, LOCK, output)
    with pytest.raises(ValueError, match="outside evidence"):
        run(PACKAGE / "fixtures.jsonl", CONFIG, LOCK, PACKAGE / "must-not-create")
