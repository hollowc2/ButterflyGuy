"""Run one explicitly authorized Schwab gateway credential proof without starting a server."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorize-real-credential-read", action="store_true")
    parser.add_argument("--confirm-single-token-writer", action="store_true")
    parser.add_argument("--confirm-no-deployment", action="store_true")
    return parser


def _load_runtime_dependencies():
    """Import failure-prone runtime dependencies inside the bounded CLI path."""
    from butterfly_guy.core.logging import setup_logging
    from butterfly_guy.schwab_gateway.config import GatewayCredentialProbeSettings
    from butterfly_guy.schwab_gateway.credential_probe import run_gateway_credential_probe

    return setup_logging, GatewayCredentialProbeSettings, run_gateway_credential_probe


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if not all(
        (
            args.authorize_real_credential_read,
            args.confirm_single_token_writer,
            args.confirm_no_deployment,
        )
    ):
        _parser().error(
            "credential proof requires explicit credential, single-writer, "
            "and no-deploy confirmations"
        )

    try:
        setup_logging, settings_type, run_probe = _load_runtime_dependencies()
        setup_logging("CRITICAL", json_output=True)
        settings = settings_type()
        from schwab.auth import client_from_access_functions

        result = run_probe(settings, client_from_access_functions)
        print(json.dumps(asdict(result), separators=(",", ":"), sort_keys=True))
    except Exception:
        _parser().exit(status=1, message="Schwab gateway credential proof failed\n")


if __name__ == "__main__":
    main()
