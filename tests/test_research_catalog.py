"""`research catalog` reports each variant's exact definition against every registry."""

from __future__ import annotations

from butterfly_guy.research import cli
from butterfly_guy.research.registry import Registry
from butterfly_guy.research.variants import CATALOG

AT = "2026-09-29T00:00:00+00:00"


def _append(reg: Registry, event: str, name: str, definition_hash: str, **kw):
    return reg.append(event, variant=name, definition={"rule": name},
                      definition_hash=definition_hash, recorded_at=AT, **kw)


def test_history_counts_events_for_the_exact_definition(tmp_path):
    reg = Registry(tmp_path / "spx.jsonl")
    _append(reg, "register", "A", "h-a")
    _append(reg, "evaluate", "A", "h-a", dataset_hash="d1")
    _append(reg, "evaluate", "A", "h-a", dataset_hash="d1")
    _append(reg, "evaluate", "A", "h-a-old", dataset_hash="d1")
    _append(reg, "evaluate", "B", "h-b", dataset_hash="d1")

    hist = reg.history("A", "h-a")

    assert hist["events"] == {"register:pre": 1, "evaluate:pre": 2}
    assert hist["last"] == AT
    assert hist["other_hashes"] == ["h-a-old"]
    assert reg.history("C", "h-c") == {"events": {}, "last": None, "other_hashes": []}


def test_history_of_a_port_includes_its_placeholder(tmp_path):
    reg = Registry(tmp_path / "spx.jsonl")
    _append(reg, "backfill", "C1", "h-words", stage="pre")
    _append(reg, "port", "C1", "h-code", ported_from="h-words")
    _append(reg, "evaluate", "C1", "h-code", dataset_hash="d1")

    hist = reg.history("C1", "h-code")

    assert hist["events"] == {"backfill:pre": 1, "port:pre": 1, "evaluate:pre": 1}
    assert hist["other_hashes"] == []


def test_catalog_lists_hashes_registries_and_counts(tmp_path, capsys):
    e0 = CATALOG["E0"].definition_hash()
    _append(Registry(tmp_path / "spx_0dte.jsonl"), "evaluate", "E0", e0, dataset_hash="d1")
    dev = Registry(tmp_path / "development" / "vendor.jsonl")
    _append(dev, "evaluate", "E0", "h-stale", dataset_hash="d2")

    code = cli.main(["--registry", str(tmp_path), "catalog", "--variants", "E0,X1"])

    out = capsys.readouterr().out
    assert code == 0
    assert f"E0  {e0[:12]}" in out
    assert "    spx_0dte: evaluate:post x1; last 2026-09-29" in out
    assert "    development/vendor: other definitions under this name: h-stale" in out
    assert f"X1  {CATALOG['X1'].definition_hash()[:12]}\n" in out
    assert "not in any registry" in out
    assert "spx_0dte: 1 distinct definitions tried (1 post hoc)" in out


def test_catalog_fails_on_a_broken_chain(tmp_path, capsys):
    reg = Registry(tmp_path / "spx_0dte.jsonl")
    _append(reg, "evaluate", "A", "h-a", dataset_hash="d1")
    _append(reg, "evaluate", "B", "h-b", dataset_hash="d1")
    lines = reg.path.read_text().splitlines()
    reg.path.write_text(lines[1] + "\n")

    code = cli.main(["--registry", str(tmp_path), "catalog", "--variants", "E0"])

    assert code == 1
    assert "CHAIN BROKEN" in capsys.readouterr().out
