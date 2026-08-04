"""One bounded quote proof through the locked token adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from butterfly_guy.schwab_gateway.config import GatewayCredentialProbeSettings
from butterfly_guy.schwab_gateway.token_adapter import (
    LockedSchwabClientAdapter,
    SchwabAccessFunctionClientFactory,
    SchwabTokenAdapterError,
)
from butterfly_guy.schwab_gateway.token_manager import (
    AtomicFileTokenStore,
    AtomicTokenManager,
    TokenManagerError,
    TokenManagerState,
)

PROBE_SYMBOL = "AAPL"


class GatewayCredentialProbeError(RuntimeError):
    """Bounded failure safe for operator output."""


@dataclass(frozen=True)
class GatewayCredentialProbeResult:
    status: Literal["ok"]
    token_state: Literal["ready"]
    quote_count: Literal[1]


def run_gateway_credential_probe(
    settings: GatewayCredentialProbeSettings,
    client_factory: SchwabAccessFunctionClientFactory[Any],
) -> GatewayCredentialProbeResult:
    """Read one public quote without resolving an account or exposing response data."""

    manager = AtomicTokenManager(AtomicFileTokenStore(settings.token_path))
    adapter = LockedSchwabClientAdapter(
        manager,
        client_factory,
        api_key=settings.api_key.get_secret_value(),
        app_secret=settings.app_secret.get_secret_value(),
    )

    def quote_operation(client: Any) -> int:
        session = getattr(client, "session", None)
        close = getattr(session, "close", None)
        try:
            fields = [client.Quote.Fields.QUOTE, client.Quote.Fields.EXTENDED]
            response = client.get_quotes([PROBE_SYMBOL], fields=fields)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get(PROBE_SYMBOL), dict):
                raise ValueError("credential probe quote response is malformed")
            return 1
        finally:
            if callable(close):
                close()

    try:
        quote_count = adapter.execute(quote_operation)
    except (TokenManagerError, SchwabTokenAdapterError):
        raise GatewayCredentialProbeError("Schwab gateway credential probe failed") from None

    if manager.health().state is not TokenManagerState.READY or quote_count != 1:
        raise GatewayCredentialProbeError("Schwab gateway credential probe failed")
    return GatewayCredentialProbeResult(
        status="ok",
        token_state="ready",
        quote_count=1,
    )
