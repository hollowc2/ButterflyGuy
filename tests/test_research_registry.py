"""The variant registry is append-only and hash-chained."""

from __future__ import annotations

import json

import pytest

from butterfly_guy.research.registry import Registry, RegistryError


def _add(reg: Registry, event: str, name: str, **kw):
    return reg.append(event, variant=name, definition={"rule": name},
                      definition_hash=f"h-{name}", recorded_at="2026-09-27T00:00:00+00:00", **kw)


def test_appends_never_rewrite_existing_bytes(tmp_path):
    reg = Registry(tmp_path / "spx.jsonl")
    _add(reg, "register", "A")
    before = reg.path.read_bytes()
    _add(reg, "evaluate", "A", dataset_hash="d1")
    after = reg.path.read_bytes()
    assert after.startswith(before) and len(after) > len(before)
    assert reg.verify() == []
    assert [r["seq"] for r in reg.records()] == [0, 1]


@pytest.mark.parametrize("tamper", ["edit", "delete", "reorder"])
def test_tampering_breaks_the_chain_and_blocks_writes(tmp_path, tamper):
    reg = Registry(tmp_path / "spx.jsonl")
    for name in ("A", "B", "C"):
        _add(reg, "evaluate", name, dataset_hash="d1")
    lines = reg.path.read_text().splitlines()
    if tamper == "edit":
        rec = json.loads(lines[1])
        rec["stage"] = "pre"
        lines[1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    elif tamper == "delete":
        del lines[1]
    else:
        lines[0], lines[1] = lines[1], lines[0]
    reg.path.write_text("\n".join(lines) + "\n")
    assert reg.verify()
    with pytest.raises(RegistryError):
        _add(reg, "evaluate", "D", dataset_hash="d1")


def test_stage_is_pre_only_when_registered_before_evaluation(tmp_path):
    reg = Registry(tmp_path / "spx.jsonl")
    _add(reg, "register", "A")
    assert _add(reg, "evaluate", "A", dataset_hash="d1")["stage"] == "pre"
    assert _add(reg, "evaluate", "B", dataset_hash="d1")["stage"] == "post"
    with pytest.raises(RegistryError):
        _add(reg, "register", "B")  # too late to pre-register after seeing results
    _add(reg, "backfill", "P", stage="pre")
    _add(reg, "backfill", "Q", stage="post")
    assert _add(reg, "evaluate", "P", dataset_hash="d1")["stage"] == "pre"
    assert _add(reg, "evaluate", "Q", dataset_hash="d1")["stage"] == "post"


def test_tried_counts_distinct_definitions(tmp_path):
    reg = Registry(tmp_path / "spx.jsonl")
    _add(reg, "backfill", "X", stage="post")
    _add(reg, "evaluate", "A", dataset_hash="d1")
    _add(reg, "evaluate", "A", dataset_hash="d2")
    _add(reg, "register", "C")  # registered but not yet evaluated: not counted
    assert reg.tried("d2") == {"dataset": 2, "post_hoc": 2, "this_hash": 1}


def _placeholder(reg: Registry, name: str, stage: str) -> dict:
    return reg.append("backfill", variant=name, definition={"name": name, "source_text": "x"},
                      definition_hash=f"words-{name}", stage=stage,
                      recorded_at="2026-09-27T00:00:00+00:00")


def test_a_port_inherits_the_placeholder_stage_and_counts_once(tmp_path):
    reg = Registry(tmp_path / "spx.jsonl")
    _placeholder(reg, "C1", "pre")
    _placeholder(reg, "R3", "post")
    assert reg.placeholder("C1")["definition_hash"] == "words-C1"
    assert _add(reg, "port", "C1", ported_from="words-C1")["stage"] == "pre"
    assert _add(reg, "port", "R3", ported_from="words-R3")["stage"] == "post"
    assert reg.placeholder("C1") is None  # already ported
    assert _add(reg, "evaluate", "C1", dataset_hash="d1")["stage"] == "pre"
    assert _add(reg, "evaluate", "R3", dataset_hash="d1")["stage"] == "post"
    # Two placeholders, each evaluated once as ported code: still two definitions.
    assert reg.tried("d1") == {"dataset": 2, "post_hoc": 1, "this_hash": 2}
    assert reg.verify() == []


def test_a_port_needs_a_matching_unported_placeholder(tmp_path):
    reg = Registry(tmp_path / "spx.jsonl")
    _placeholder(reg, "C1", "pre")
    # A backfill that already carries an executable definition is not a placeholder.
    reg.append("backfill", variant="E0", definition={"entry": {}, "source_text": "x"},
               definition_hash="h-E0", stage="pre")
    assert reg.placeholder("E0") is None
    with pytest.raises(RegistryError):
        _add(reg, "port", "C2", ported_from="words-C1")  # another variant's placeholder
    with pytest.raises(RegistryError):
        _add(reg, "port", "C1", ported_from="nothing")
    _add(reg, "port", "C1", ported_from="words-C1")
    with pytest.raises(RegistryError):
        reg.append("port", variant="C1", definition={}, definition_hash="h-other",
                   ported_from="words-C1")
