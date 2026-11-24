"""Tests for tools/compress_chains.py."""

from __future__ import annotations

import datetime as dt
import fcntl
import importlib.util
import os
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


def test_compress_file_rejects_truncated_existing_zst(tmp_path):
    path = _save_day(tmp_path, dt.date(2026, 11, 2))
    zst = path.with_name(path.name + ".zst")
    full = zstandard.ZstdCompressor(write_checksum=True).compress(path.read_bytes())
    zst.write_bytes(full[:-1])

    with pytest.raises(RuntimeError, match="truncated"):
        compress_chains.compress_file(path)

    assert path.exists()


def test_compress_file_keeps_both_when_source_changes_before_delete(tmp_path, monkeypatch):
    date = dt.date(2026, 11, 2)
    path = _save_day(tmp_path, date)
    late = dt.datetime.combine(date, dt.time(15, 0), tzinfo=dt.timezone.utc)
    real_fsync_dir = compress_chains._fsync_dir

    def append_then_fsync(directory):
        save_snapshot(date, late, 7351.0, _ROWS, cache_dir=tmp_path)  # late writer
        real_fsync_dir(directory)

    monkeypatch.setattr(compress_chains, "_fsync_dir", append_then_fsync)

    with pytest.raises(RuntimeError, match="changed while compressing"):
        compress_chains.compress_file(path)

    assert path.exists()
    chains = load_chain_day(date, cache_dir=tmp_path, underlying="SPX")
    assert late in chains


def test_compress_file_recovery_keeps_plain_when_it_changes_after_hashing(
    tmp_path, monkeypatch
):
    date = dt.date(2026, 11, 2)
    path = _save_day(tmp_path, date)
    zst = path.with_name(path.name + ".zst")
    zst.write_bytes(zstandard.ZstdCompressor().compress(path.read_bytes()))
    late = dt.datetime.combine(date, dt.time(15, 0), tzinfo=dt.timezone.utc)
    real_plain_sha256 = compress_chains._plain_sha256

    def hash_then_append(p):
        digest = real_plain_sha256(p)
        save_snapshot(date, late, 7351.0, _ROWS, cache_dir=tmp_path)  # late writer
        return digest

    monkeypatch.setattr(compress_chains, "_plain_sha256", hash_then_append)

    with pytest.raises(RuntimeError, match="changed while compressing"):
        compress_chains.compress_file(path)

    assert path.exists()
    assert late in load_chain_day(date, cache_dir=tmp_path, underlying="SPX")


def test_main_skips_while_another_run_holds_the_lock(tmp_path, capsys):
    path = _save_day(tmp_path, dt.date(2020, 1, 2))
    held = os.open(tmp_path, os.O_RDONLY)
    fcntl.flock(held, fcntl.LOCK_EX)
    try:
        assert compress_chains.main(["--root", str(tmp_path)]) == 0
    finally:
        os.close(held)

    assert path.exists()
    assert "skipping" in capsys.readouterr().out
    assert compress_chains.main(["--root", str(tmp_path)]) == 0
    assert not path.exists()
