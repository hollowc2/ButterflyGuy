"""Compress finished option-chain days to zstd, keeping the most recent week plain.

The collector appends to today's data/chains/<UNDERLYING>/YYYY-MM-DD.jsonl and
never writes an older day again. Each day file older than KEEP_DAYS (legacy
.json days too) is replaced by <file>.zst, which chain_cache reads transparently.

The plain file is only deleted after its .zst decompresses to exactly the same
bytes and the plain file's size and mtime are unchanged since it was read. If a
.zst already exists (a run interrupted before the delete), the plain file is
deleted only when the two match; otherwise both are kept and the run fails.

Usage (from the repo root):
  .venv/bin/python tools/compress_chains.py [--dry-run] [--root data/chains]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import shutil
import sys
from pathlib import Path

import zstandard

ROOT = Path(__file__).parent.parent
KEEP_DAYS = 7
# Level 9 compresses chain JSON ~13x at ~40 MB/s on one core; level 19 reaches
# ~19x but is ~50x slower, too much CPU for the 2-core trading host.
LEVEL = 9
CHUNK = 1 << 20
DAY_FILE = re.compile(r"(\d{4}-\d{2}-\d{2})\.jsonl?")


def _sha256(stream) -> bytes:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(CHUNK), b""):
        digest.update(chunk)
    return digest.digest()


def _zst_sha256(path: Path) -> bytes:
    with path.open("rb") as f, zstandard.ZstdDecompressor().stream_reader(f) as reader:
        return _sha256(reader)


def _plain_sha256(path: Path) -> bytes:
    with path.open("rb") as f:
        return _sha256(f)


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def compress_file(path: Path) -> int:
    """Replace path with a verified path.zst; return the bytes saved."""
    target = path.with_name(path.name + ".zst")
    size = path.stat().st_size
    if target.exists():
        if _zst_sha256(target) != _plain_sha256(path):
            raise RuntimeError(f"{path} differs from existing {target.name}; kept both")
        path.unlink()
        return size

    tmp = path.with_name(path.name + ".zst.tmp")
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as src, tmp.open("wb") as dst:
        with zstandard.ZstdCompressor(level=LEVEL).stream_writer(dst, closefd=False) as writer:
            for chunk in iter(lambda: src.read(CHUNK), b""):
                digest.update(chunk)
                writer.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())

    after = path.stat()
    changed = (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns)
    if changed or _zst_sha256(tmp) != digest.digest():
        tmp.unlink()
        raise RuntimeError(f"{path} failed verification; kept original")

    shutil.copystat(path, tmp)
    tmp.replace(target)
    _fsync_dir(path.parent)
    path.unlink()
    return size - target.stat().st_size


def due_files(root: Path, today: dt.date) -> list[Path]:
    """Plain day files under root older than the KEEP_DAYS most recent days."""
    cutoff = today - dt.timedelta(days=KEEP_DAYS)
    return [
        path
        for path in sorted(root.rglob("*.json*"))
        if (m := DAY_FILE.fullmatch(path.name)) and dt.date.fromisoformat(m[1]) <= cutoff
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT / "data" / "chains")
    parser.add_argument("--dry-run", action="store_true", help="list files without compressing")
    args = parser.parse_args(argv)

    files = due_files(args.root, dt.date.today())
    if args.dry_run:
        for path in files:
            print(f"would compress {path}")
        return 0

    saved = failures = 0
    for path in files:
        try:
            saved += compress_file(path)
        except Exception as e:
            failures += 1
            print(f"FAILED {path}: {e}", file=sys.stderr)
    print(f"{len(files) - failures}/{len(files)} files compressed, {saved / 2**30:.2f} GiB saved")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
