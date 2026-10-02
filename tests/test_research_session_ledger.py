"""Evidence consolidation contracts; fixtures contain no vendor prices."""
from __future__ import annotations

import datetime as dt
import json

import pyarrow as pa
import pytest

from butterfly_guy.research import session_ledger as ledger
from butterfly_guy.research.cli import main
from butterfly_guy.research.dataset import Manifest, sha256_file, write_table
from butterfly_guy.research.holdout import HoldoutSealedError

REFS = {k: k for k in ("manifest", "sessions", "quality", "calendar", "audit",
                       "eligibility", "replay")}


def reconcile(start="2023-11-22", end="2023-11-27", **kw):
    defaults = dict(dataset="spx_test", dataset_hash="hash", start=dt.date.fromisoformat(start),
                    end=dt.date.fromisoformat(end), accepted=set(), requested={}, skipped={},
                    availability={}, quality={"gates": {"Q1": True, "Q5": None}}, refs=REFS)
    defaults.update(kw)
    return ledger.reconcile(**defaults)


def test_calendar_early_close_and_accepted_no_trade():
    rows, summary = reconcile(
        accepted={"2023-11-24"}, requested={"2023-11-24": {}},
        availability={"2023-11-24": {"status": "successful_request"}},
        quality={"gates": {"Q1": True}, "vendor": {"sessions": [{"date": "2023-11-24"}]}},
        replay={"sessions": [{"date": "2023-11-24", "status": "no_trade"}]})
    by_date = {r["exchange_date"]: r for r in rows}
    assert by_date["2023-11-23"]["calendar"]["status"] == "holiday"
    assert by_date["2023-11-25"]["calendar"]["status"] == "weekend"
    r = by_date["2023-11-24"]
    assert r["calendar"]["scheduled_early_close"]
    assert r["calendar"]["close_et"] == "13:00"
    assert r["normalization"]["status"] == "accepted"
    assert not r["exclusion_reasons"]
    assert summary["research_counts"] == {"no_trade": 1}
    assert summary["primary_counts"]["absent_normalized"] == 2


def test_non_expiration_is_independently_documented_and_eom_is_preserved():
    rows, _ = reconcile(start="2022-01-04", end="2022-01-04",
                        eligibility={"sessions": [{"date": "2022-01-04", "status": "excluded",
                            "reasons": ["absent_option_data"],
                            "classification": ledger.NON_EXPIRATION}]})
    assert rows[0]["option_availability"]["status"] == "non_expiration"
    assert rows[0]["primary_classification"] == "non_expiration"
    assert not rows[0]["exclusion_reasons"]
    # Monday's holiday-shift Tuesday and Thursday EOM files predate regular weekdays.
    for date in ("2022-01-18", "2022-03-31"):
        rows, _ = reconcile(start=date, end=date, accepted={date}, requested={date: {}},
                            availability={date: {"status": "successful_request"}},
                            quality={"vendor": {"sessions": [{"date": date}]}})
        assert rows[0]["primary_classification"] == "accepted"
    rows, summary = reconcile(start="2022-01-04", end="2022-01-04")
    assert rows[0]["option_availability"]["status"] == "not_requested"
    assert summary["status"] == "blocked"


def test_missing_input_multiple_reasons_and_approved_exclusion():
    date = "2022-02-22"
    approved = "approved_quality_exclusion: owner approval; original explanation"
    audit = {"sessions": [{"date": date, "status": "excluded",
                           "reasons": ["missing_index_observations", "missing_vix"]}]}
    rows, summary = reconcile(start=date, end=date, requested={date: {}},
                             availability={date: {"status": "successful_request"}},
                             skipped={date: approved}, audit=audit)
    r = rows[0]
    assert r["normalization"]["status"] == "excluded"
    assert [x["text"] for x in r["exclusion_reasons"]] == [
        approved, "missing_index_observations", "missing_vix"]
    assert r["supporting_inputs"]["spx"]["status"] == "missing"
    assert r["supporting_inputs"]["vix"]["status"] == "missing"
    assert summary["status"] == "reconciled"


def test_quality_scope_not_evaluable_and_unassessed():
    rows, _ = reconcile(start="2026-03-17", end="2026-03-17", accepted={"2026-03-17"},
                        requested={"2026-03-17": {}},
                        availability={"2026-03-17": {"status": "successful_request"}},
                        quality={"gates": {"Q1": True, "Q5": None}, "vendor": {"sessions": [
                            {"date": "2026-03-17", "q5": {"evaluable": False}}]}})
    q = rows[0]["quality"]
    assert q["assessment_scope"] == "dataset"
    assert q["gates"] == {"Q1": "pass", "Q2": "unassessed", "Q3": "unassessed",
                          "Q4": "unassessed", "Q5": "not_evaluable", "Q6": "unassessed"}
    assert q["per_session_measurements"]["q5"]["evaluable"] is False
    assert rows[0]["supporting_inputs"]["open"]["status"] == "unknown"
    assert rows[0]["research_outcome"] is None


@pytest.mark.parametrize("status", ["no_data", "missing_file", "conflict"])
def test_conflicts_are_visible(status):
    date = "2023-11-24"
    rows, summary = reconcile(start=date, end=date, accepted={date}, requested={date: {}},
                             availability={date: {"status": status, "evidence": ["a", "b"]}},
                             skipped={date: "no_vix"},
                             quality={"vendor": {"sessions": [{"date": date}]}})
    assert rows[0]["primary_classification"] == "conflict"
    assert rows[0]["option_availability"]["evidence"] == ["a", "b"]
    assert summary["status"] == "blocked"
    assert summary["inconsistent_session_count"] == 1
    assert summary["issues"]


def test_protected_request_rejected_before_input_read(monkeypatch, tmp_path):
    def forbidden(*a, **kw):
        pytest.fail("opened input before guard")
    monkeypatch.setattr(ledger.Evidence, "json", forbidden)
    with pytest.raises(HoldoutSealedError):
        ledger.build(cache=tmp_path, dataset="spx_test", start=dt.date(2024, 6, 28),
                     end=dt.date(2026, 3, 13), inventory=tmp_path / "protected",
                     evidence_root=tmp_path, out=tmp_path)


def save(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ledger.canonical(body))
    return path


@pytest.fixture
def evidence(tmp_path):
    """A miniature durable package with the same identity links as the real workflow."""
    dataset = "spx_0dte_local_test"
    cache, root = tmp_path / "cache", tmp_path / "evidence"
    date = "2026-03-17"
    raw = tmp_path / "archive/spxw_0dte/quote_1m/2026/2026-03-17.parquet"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"fabricated unprotected input")
    catalog = raw.parents[3] / "catalog.jsonl"
    catalog.write_text(json.dumps({"set": "spxw_0dte", "date": date, "kind": "quote_1m",
                                   "status": "ok", "expiration": date}) + "\n")
    index_file = tmp_path / "owner.csv"
    index_file.write_text("fabricated supporting source")
    source_ref = {"path": str(index_file), "sha256": sha256_file(index_file)}
    support = Manifest("support", "SPX", {"kind": "offline_support_snapshot"}, {})
    support.files["daily_bars.parquet"] = write_table(pa.table({"date": [date]}),
                                                      cache / "support/daily_bars.parquet")
    support.save(cache / "support/manifest.json")
    source = {"set": "spxw_0dte", "option_root": "SPXW", "archive": str(catalog.parent),
              "support": {"dataset": "support", "hash": support.dataset_hash,
                          "source": support.source}, "index_files": {"SPX": source_ref},
              "daily_cache": {"SPX": source_ref}}
    m = Manifest(dataset, "SPX", source,
                 {"kind": "local_parquet", "range": [date, date], "mapping_version": "test"})
    m.files["sessions.parquet"] = write_table(pa.table({"date": [date]}),
                                              cache / dataset / "sessions.parquet")
    ref = {"path": str(raw), "sha256": sha256_file(raw)}
    m.history = [{"mode": "local_import", "dataset_hash": m.dataset_hash,
                  "range": [date, date], "requested_raw_inputs": {date: ref},
                  "raw_inputs": {date: ref}, "sessions_skipped": {}},
                 {"mode": "vendor_quality", "dataset_hash": m.dataset_hash,
                  "range": [date, date], "run_id": "q", "pass": True,
                  "gates": {"Q1": True, "Q5": None}}]
    m.save(cache / dataset / "manifest.json")
    qpath = root / "artifacts" / dataset / "quality/q/quality.json"
    save(qpath, {"meta": {"vendor": {"dataset": dataset, "dataset_hash": m.dataset_hash},
                          "cboe_spx": {"sha256": source_ref["sha256"]}}, "range": [date, date],
                 "gates": {"Q1": True, "Q5": None}, "pass": True,
                 "vendor": {"sessions": [{"date": date, "q5": {"evaluable": False}}]}})
    save(qpath.with_name("provenance.json"), {"quality_sha256": sha256_file(qpath)})
    qpath.with_name("report.md").write_text("fabricated quality record")
    save(root / "completion-summary.json", {"artifact_sha256": {
        str(p.relative_to(root)): sha256_file(p) for p in qpath.parent.iterdir()}})
    save(root / "frozen-supporting-inputs.json", {"files": {
        str(index_file): {"sha256": source_ref["sha256"]}}})
    inv = save(tmp_path / "inventory/inventory.json", {"normalized_datasets": [
        {"dataset": dataset, "dataset_hash": m.dataset_hash,
         "manifest_sha256": sha256_file(cache / dataset / "manifest.json")}], "experiments": []})
    save(inv.with_name("checksums.json"), {"inventory.json": sha256_file(inv)})
    return dict(cache=cache, dataset=dataset, start=dt.date.fromisoformat(date),
                end=dt.date.fromisoformat(date), inventory=inv, evidence_root=root,
                out=tmp_path / "outputs")


def test_deterministic_generation_resumption_and_artifact_verification(evidence):
    folder = ledger.build(**evidence)
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    assert ledger.build(**evidence) == folder
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
    ledger.verify_artifact(folder)
    (folder / "ledger.jsonl").write_text("tampered")
    with pytest.raises(ValueError, match="artifact sha256 mismatch"):
        ledger.build(**evidence)


def test_changed_source_identity_is_rejected(evidence):
    ledger.build(**evidence)
    (evidence["cache"].parent / "owner.csv").write_text("changed")
    with pytest.raises(ValueError, match="changed input"):
        ledger.build(**evidence)


def test_quality_hash_mismatch_is_rejected(evidence):
    root = evidence["evidence_root"]
    qpath = root / "artifacts" / evidence["dataset"] / "quality/q/quality.json"
    q = json.loads(qpath.read_text())
    q["meta"]["vendor"]["dataset_hash"] = "different_import"
    save(qpath, q)
    save(qpath.with_name("provenance.json"), {"quality_sha256": sha256_file(qpath)})
    save(root / "completion-summary.json", {"artifact_sha256": {
        str(p.relative_to(root)): sha256_file(p) for p in qpath.parent.iterdir()}})
    with pytest.raises(ValueError, match="quality dataset hash/range/support identity mismatch"):
        ledger.build(**evidence)


def test_cli_requires_dataset_and_cache():
    with pytest.raises(SystemExit):
        main(["session-quality-ledger", "--start", "2026-03-13", "--end", "2026-09-25",
              "--inventory", "x", "--evidence-root", "x", "--out", "x"])


def test_missing_successful_file_is_reported(evidence):
    raw = evidence["cache"].parent / "archive/spxw_0dte/quote_1m/2026/2026-03-17.parquet"
    raw.unlink()
    folder = ledger.build(**evidence)
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["status"] == "blocked"
    assert summary["missing_source_count"] == 1


def test_new_metadata_input_changes_result_identity(evidence):
    first = ledger.build(**evidence)
    path = evidence["cache"].parent / "archive/catalog.jsonl"
    path.write_text(path.read_text() + json.dumps({"set": "other", "kind": "quote_1m",
                                                  "date": "2026-03-17", "status": "ok"}) + "\n")
    second = ledger.build(**evidence)
    assert first != second
    ledger.verify_artifact(first)
    ledger.verify_artifact(second)


def test_audit_import_supporting_conflict_is_visible():
    date = "2022-02-25"
    rows, summary = reconcile(start=date, end=date, skipped={date: "no_spx_index"},
                             audit={"sessions": [{"date": date, "status": "usable",
                                                  "reasons": []}]})
    assert rows[0]["normalization"]["status"] == "conflict"
    assert any("supporting evidence disagrees" in x["reason"] for x in summary["issues"])


def test_normalized_acceptance_cannot_override_approved_exclusion():
    date = "2022-02-22"
    rows, summary = reconcile(start=date, end=date, accepted={date}, requested={date: {}},
                             availability={date: {"status": "successful_request"}},
                             skipped={date: "approved_quality_exclusion: owner decision"},
                             quality={"vendor": {"sessions": [{"date": date}]}})
    assert rows[0]["normalization"]["status"] == "conflict"
    assert rows[0]["exclusion_reasons"][0]["code"] == "approved_quality_exclusion"
    assert summary["status"] == "blocked"


def test_protected_raw_path_in_unprotected_metadata_rejected(evidence, monkeypatch):
    cache, dataset = evidence["cache"], evidence["dataset"]
    path = cache / dataset / "manifest.json"
    m = Manifest.load(path)
    m.history[0]["requested_raw_inputs"]["2026-03-17"]["path"] = str(
        cache.parent / "archive/2025-01-02.parquet")
    m.save(path)
    inv = json.loads(evidence["inventory"].read_text())
    inv["normalized_datasets"][0]["manifest_sha256"] = sha256_file(path)
    save(evidence["inventory"], inv)
    save(evidence["inventory"].with_name("checksums.json"),
         {"inventory.json": sha256_file(evidence["inventory"])})
    original = ledger.sha256_file
    def check(path):
        if path.name == "2025-01-02.parquet":
            pytest.fail("protected payload opened")
        return original(path)
    monkeypatch.setattr(ledger, "sha256_file", check)
    with pytest.raises(HoldoutSealedError):
        ledger.build(**evidence)
