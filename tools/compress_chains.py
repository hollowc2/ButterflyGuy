"""Compress finished option-chain days to zstd, keeping the most recent week plain.

The collector appends to today's data/chains/<UNDERLYING>/YYYY-MM-DD.jsonl and
never writes an older day again. Each day file older than KEEP_DAYS (legacy
.json days too) is replaced by <file>.zst, which chain_cache reads transparently.

The plain file is only deleted after its .zst decompresses (complete frame,
checksum included) to exactly the same bytes, and the plain file's size, mtime
and inode are unchanged since it was first read. If a .zst already exists (a run
interrupted before the delete), the plain file is deleted only when the two
match. Otherwise both are kept, chain_cache merges them, and the run fails.
Each file is compressed under an exclusive flock on the file itself, so
overlapping runs (even with different --root values) skip files already taken.

Usage (from the repo root):
  .venv/bin/python tools/compress_chains.py [--dry-run] [--root data/chains]
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
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
    """Hash of path's decompressed bytes; raises if the zstd frame is incomplete."""
    decompressor = zstandard.ZstdDecompressor().decompressobj()
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            digest.update(decompressor.decompress(chunk))
    if not decompressor.eof:
        raise RuntimeError(f"{path} is a truncated zstd frame")
    return digest.digest()


def _plain_sha256(path: Path) -> bytes:
    with path.open("rb") as f:
        return _sha256(f)


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _identity(path: Path) -> tuple[int, int, int]:
    st = path.stat()
    return st.st_size, st.st_mtime_ns, st.st_ino


def _unlink_unchanged(path: Path, before: tuple[int, int, int]) -> None:
    if _identity(path) != before:
        raise RuntimeError(f"{path} changed while compressing; kept it and its .zst")
    path.unlink()


def compress_file(path: Path) -> int | None:
    """Replace path with a verified path.zst; return the bytes saved, or None when
    another run holds the file or has already compressed it."""
    try:
        fd = os.open(path, os.O_RDONLY)
    except FileNotFoundError:
        return None
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return None
        try:
            before = _identity(path)
        except FileNotFoundError:
            return None
        if before[2] != os.fstat(fd).st_ino:
            return None  # path was replaced after we opened it
        return _compress_locked(path, before)
    finally:
        os.close(fd)


def _compress_locked(path: Path, before: tuple[int, int, int]) -> int:
    target = path.with_name(path.name + ".zst")
    if target.exists():
        if _zst_sha256(target) != _plain_sha256(path):
            raise RuntimeError(f"{path} differs from existing {target.name}; kept both")
        _unlink_unchanged(path, before)
        return before[0]

    tmp = path.with_name(path.name + ".zst.tmp")
    digest = hashlib.sha256()
    compressor = zstandard.ZstdCompressor(level=LEVEL, write_checksum=True)
    with path.open("rb") as src, tmp.open("wb") as dst:
        with compressor.stream_writer(dst, closefd=False) as writer:
            for chunk in iter(lambda: src.read(CHUNK), b""):
                digest.update(chunk)
                writer.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())

    if _identity(path) != before or _zst_sha256(tmp) != digest.digest():
        tmp.unlink()
        raise RuntimeError(f"{path} failed verification; kept original")

    shutil.copystat(path, tmp)
    tmp.replace(target)
    _fsync_dir(path.parent)
    _unlink_unchanged(path, before)
    return before[0] - target.stat().st_size


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

    saved = skipped = failures = 0
    for path in files:
        try:
            result = compress_file(path)
        except Exception as e:
            failures += 1
            print(f"FAILED {path}: {e}", file=sys.stderr)
            continue
        if result is None:
            skipped += 1
            print(f"skipped {path}: another run has it")
        else:
            saved += result
    done = len(files) - skipped - failures
    print(f"{done}/{len(files)} files compressed, {skipped} skipped, {saved / 2**30:.2f} GiB saved")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
