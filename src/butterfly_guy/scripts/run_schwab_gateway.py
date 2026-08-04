"""Run the isolated read-only gateway foundation with explicit demo data."""

from __future__ import annotations

import argparse
import datetime as dt

from aiohttp import web

from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.gateway_client.models import QuoteV1
from butterfly_guy.schwab_gateway.api import StaticTokenReadinessProvider, create_app
from butterfly_guy.schwab_gateway.auth import InternalKeyAuthenticator
from butterfly_guy.schwab_gateway.config import GatewaySettings
from butterfly_guy.schwab_gateway.token_manager import TokenManagerState

log = get_logger(__name__)


class DemoQuoteUpstream:
    """Deterministic smoke-test upstream; never contacts Schwab."""

    async def get_quotes(self, symbols: tuple[str, ...]) -> tuple[QuoteV1, ...]:
        received_at = dt.datetime.now(dt.timezone.utc)
        return tuple(
            QuoteV1(
                symbol=symbol,
                gateway_received_at=received_at,
                source="foundation_demo",
                mark=100.0,
                stale=False,
                data_quality_flags=("demo_data_not_for_trading",),
            )
            for symbol in symbols
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="serve deterministic fake quotes; no Schwab credentials are read",
    )
    args = parser.parse_args()
    if not args.demo:
        parser.error("the foundation runner supports only --demo")

    settings = GatewaySettings()
    setup_logging(settings.log_level, json_output=True)
    authenticator = InternalKeyAuthenticator.from_file(settings.internal_keys_path)
    app = create_app(
        DemoQuoteUpstream(),
        authenticator,
        upstream_timeout_seconds=settings.upstream_timeout_seconds,
        token_readiness_provider=StaticTokenReadinessProvider(TokenManagerState.READY),
    )
    log.info(
        "schwab_gateway_foundation_starting",
        bind_host=settings.bind_host,
        port=settings.port,
        upstream="demo",
        order_writes_enabled=False,
    )
    web.run_app(app, host=settings.bind_host, port=settings.port)


if __name__ == "__main__":
    main()
