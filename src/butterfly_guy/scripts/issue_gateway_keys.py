"""Issue or append internal gateway consumer keys in a digest-only keys file.

The gateway never stores a consumer key, only its SHA-256. This command generates the
requested keys, writes the file the gateway reads, and prints each newly generated
plaintext key exactly once so the operator can distribute it. There is no way to recover
a key afterwards.

Without ``--existing-input``, the output contains only the requested clients. With
``--existing-input``, that digest-only document is validated by the gateway's real
authenticator and copied to the new output before the requested clients are added. The
existing input and new output are always distinct paths: output is created at mode 0600
and an existing output is never overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

from butterfly_guy.schwab_gateway.auth import (
    EXPECTED_PRIORITY_BY_CLIENT,
    KNOWN_CAPABILITIES,
    KNOWN_CLIENT_IDS,
    InternalKeyAuthenticator,
)

KEY_BYTES = 32


def generate_key() -> str:
    return secrets.token_urlsafe(KEY_BYTES)


def key_digest(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def build_keys_document(client_ids: list[str]) -> tuple[dict, dict[str, str]]:
    """Return the digest-only document and the plaintext keys, keyed by client id."""
    unknown = sorted(set(client_ids) - KNOWN_CLIENT_IDS)
    if unknown:
        raise ValueError(f"unknown gateway client ids: {unknown}")
    if len(set(client_ids)) != len(client_ids):
        raise ValueError("duplicate gateway client id")
    if not client_ids:
        raise ValueError("at least one gateway client id is required")

    plaintext = {client_id: generate_key() for client_id in client_ids}
    document = {
        "version": 1,
        "clients": [
            {
                "id": client_id,
                "key_sha256": key_digest(plaintext[client_id]),
                "capabilities": sorted(KNOWN_CAPABILITIES),
                "priority_class": EXPECTED_PRIORITY_BY_CLIENT[client_id].value,
            }
            for client_id in client_ids
        ],
    }
    return document, plaintext


def append_keys_document(
    existing_input: Path,
    client_ids: list[str],
) -> tuple[dict, dict[str, str]]:
    """Return a validated existing document plus newly issued client keys."""
    # Validate with the exact loader used by the running gateway before preserving any
    # existing entry. This rejects bad schemas, unknown identities, duplicate identities
    # or digests, invalid capabilities/priorities, and unsafe write permissions.
    _, existing_document = InternalKeyAuthenticator.load_file(existing_input)
    existing_clients = existing_document["clients"]
    existing_ids = {client["id"] for client in existing_clients}

    overlap = sorted(existing_ids & set(client_ids))
    if overlap:
        raise ValueError(f"gateway client ids already exist: {overlap}")
    additions, plaintext = build_keys_document(client_ids)

    # Copy each mapping so the result cannot mutate a caller-owned parsed document. The
    # existing entries retain their original order and digest values byte-for-byte.
    document = {
        "version": existing_document["version"],
        "clients": [dict(client) for client in existing_clients]
        + additions["clients"],
    }
    return document, plaintext


def write_private_json(path: Path, document: dict) -> None:
    """Create the file at mode 0600, refusing to overwrite an existing path."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--existing-input",
        type=Path,
        help=(
            "validated digest-only keys file to preserve while appending clients; "
            "never modified"
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="new mode-0600 keys file; must not already exist",
    )
    parser.add_argument(
        "--client",
        action="append",
        dest="clients",
        default=None,
        metavar="ID",
        help=f"repeatable; one of {sorted(KNOWN_CLIENT_IDS)}",
    )
    args = parser.parse_args(argv)

    if args.output.exists():
        parser.error("output path already exists; choose a new output path")

    client_ids = args.clients or []
    try:
        if args.existing_input is None:
            document, plaintext = build_keys_document(client_ids)
        else:
            document, plaintext = append_keys_document(
                args.existing_input,
                client_ids,
            )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    write_private_json(args.output, document)

    # Round-trip through the real loader so a file that the gateway would reject is
    # never left behind as if it had succeeded.
    try:
        InternalKeyAuthenticator.from_file(args.output)
    except ValueError:
        args.output.unlink(missing_ok=True)
        parser.error("generated keys file failed the gateway's own validation")

    # The only time these values are ever printed. Nothing is logged.
    sys.stdout.write("Distribute these new keys now; they cannot be recovered.\n\n")
    for client_id in client_ids:
        sys.stdout.write(f"{client_id}: {plaintext[client_id]}\n")
    sys.stdout.write(
        f"\nAdded {len(client_ids)} new digest(s); "
        f"wrote {len(document['clients'])} total digest(s) at mode 0600.\n"
    )


if __name__ == "__main__":
    main()
