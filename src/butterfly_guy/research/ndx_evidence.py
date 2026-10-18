"""NDX evidence integrity and explicitly separate read-only extraction.

Verification uses only the standard library. No broker, database or SSH import
is needed by the offline commands. Manifests are trusted small research records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value) -> None:
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def verify(root: Path, manifest: Path) -> dict:
    record = read_json(manifest)
    if not record.get("files"):
        raise ValueError("manifest has no files")
    for name, expected in record["files"].items():
        target = (root / name).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError(f"unsafe manifest path: {name}")
        if not target.is_file() or digest(target) != expected:
            raise ValueError(f"input hash mismatch or missing file: {name}")
    return record


def new_directory(path: Path, *inputs: Path) -> None:
    target = path.resolve()
    if any(target.is_relative_to(p.resolve()) for p in inputs):
        raise ValueError("output must be outside evidence directories")
    path.mkdir(parents=True, exist_ok=False)


def extract(query: Path, output: Path, host: str) -> None:
    """Only run a checked-in, read-only study query; never overwrite an export."""
    sql_root = Path(__file__).resolve().parents[3] / "docs/research/ndx-strategy/sql"
    if query.resolve().parent != sql_root or query.suffix != ".sql":
        raise ValueError("extraction requires a versioned NDX study SQL file")
    sql = query.read_bytes()
    if b"BEGIN READ ONLY;" not in sql or b"TO STDOUT" not in sql:
        raise ValueError("expected read-only COPY query")
    new_directory(output)
    (output / query.name).write_bytes(sql)
    # Deliberately separate from every offline path; no credentials are read.
    command = [
        "ssh",
        "-F",
        "/dev/null",
        "-o",
        "BatchMode=yes",
        host,
        "docker exec -i butterfly_timescaledb psql -X -q "
        "-v ON_ERROR_STOP=1 -U butterfly -d butterfly_guy",
    ]
    with (output / "extract.csv").open("xb") as stream:
        subprocess.run(command, input=sql, stdout=stream, check=True)
    write_json(
        output / "manifest.json",
        {
            "provider": "Helios TimescaleDB read-only export",
            "host": host,
            "query": query.name,
            "files": {p.name: digest(p) for p in output.iterdir() if p.is_file()},
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--evidence", type=Path, required=True)
    check.add_argument("--manifest", type=Path, required=True)
    export = commands.add_parser("extract")
    export.add_argument("--query", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--host", default="billy@helios")
    args = parser.parse_args()
    if args.command == "verify":
        result = verify(args.evidence, args.manifest)
        print(
            json.dumps(
                {"verified_files": len(result["files"]), "manifest_sha256": digest(args.manifest)}
            )
        )
    else:
        extract(args.query, args.output, args.host)


if __name__ == "__main__":
    main()
