"""Tests for tools/compress_chains.py."""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

import pytest
import zstandard

from butterfly_guy.backtest.chain_cache import load_chain_day, save_snapshot

ROOT = Path(__file__).parent.parent

_spec = importlib.util.spec_from_file_location(
    "compress_chains", ROOT / "tools" / "compress_chains.py"
)
compress_chains = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(compress_chains)

_ROWS = [
    {
        "underlying": "SPX",
        "strike": 7350.0,
        "option_type": "CALL",
        "bid": 1.0,
        "ask": 1.2,
        "mark": 1.1,
    }
]


def _save_day(root: Path, date: dt.date) -> Path:
    ts = dt.datetime.combine(date, dt.time(14, 30), tzinfo=dt.timezone.utc)
    save_snapshot(date, ts, 7350.0, _ROWS, cache_dir=root)
    return root / "SPX" / f"{date.isoformat()}.jsonl"


def test_due_files_keeps_most_recent_week_plain(tmp_path):
    today = dt.date(2026, 11, 23)
    for days_ago in range(10):
        _save_day(tmp_path, today - dt.timedelta(days=days_ago))
    (tmp_path / "2026-03-10.json").write_text('{"snapshots": {}}', encoding="utf-8")
    (tmp_path / "SPX" / "2026-11-01.jsonl.zst").write_bytes(b"")
    (tmp_path / "notes.json").write_text("{}", encoding="utf-8")

    due = compress_chains.due_files(tmp_path, today)

    assert [p.name for p in due] == [
        "2026-03-10.json",
        "2026-11-14.jsonl",
        "2026-11-15.jsonl",
        "2026-11-16.jsonl",
    ]


def test_compress_file_round_trips_and_removes_original(tmp_path):
    date = dt.date(2026, 11, 2)
    path = _save_day(tmp_path, date)
    original = path.read_bytes()
    chains = load_chain_day(date, cache_dir=tmp_path, underlying="SPX")

    saved = compress_chains.compress_file(path)

    zst = path.with_name(path.name + ".zst")
    assert not path.exists()
    assert not path.with_name(path.name + ".zst.tmp").exists()
    assert zstandard.ZstdDecompressor().stream_reader(zst.open("rb")).read() == original
    assert saved == len(original) - zst.stat().st_size
    assert load_chain_day(date, cache_dir=tmp_path, underlying="SPX") == chains


def test_compress_file_finishes_interrupted_run(tmp_path):
    path = _save_day(tmp_path, dt.date(2026, 11, 2))
    zst = path.with_name(path.name + ".zst")
    zst.write_bytes(zstandard.ZstdCompressor().compress(path.read_bytes()))

    compress_chains.compress_file(path)

    assert not path.exists()
    assert zst.exists()


def test_compress_file_keeps_both_when_existing_zst_differs(tmp_path):
    path = _save_day(tmp_path, dt.date(2026, 11, 2))
    zst = path.with_name(path.name + ".zst")
    zst.write_bytes(zstandard.ZstdCompressor().compress(b"other\n"))

    with pytest.raises(RuntimeError, match="kept both"):
        compress_chains.compress_file(path)

    assert path.exists()
    assert zst.exists()


def test_main_dry_run_changes_nothing(tmp_path, capsys):
    path = _save_day(tmp_path, dt.date(2020, 1, 2))

    assert compress_chains.main(["--root", str(tmp_path), "--dry-run"]) == 0

    assert path.exists()
    assert "would compress" in capsys.readouterr().out
