"""Real Schwab market-data reads bound to the single locked token manager.

This is the bridge between the proven token machinery and the gateway's three read
surfaces. It exposes only ``SpotPriceProvider``, ``OptionChainProvider``, and
``EquityQuoteProvider``; there is no account, order, transaction, or streaming method to
call, so no such request can be issued through this object.

Three properties are deliberate and load-bearing:

- **One transaction per call.** Every read runs inside its own
  ``LockedSchwabClientAdapter.execute``, which constructs a client, performs one
  operation, persists any rotation, and invalidates its callbacks before releasing the
  token lock. That is the lifecycle the adapter was fake-proven and host-proven under, and
  it is why the gateway can hold a production token safely.
- **The lock serializes everything.** The token manager holds an exclusive lock for the
  duration of each transaction, so concurrent gateway requests queue behind one another
  regardless of the admission policy's capacities. Admission bounds queue depth here, not
  parallelism.
- **No retries.** ``SchwabClientWrapper._retry`` retries three times with backoff on the
  direct path. This one does not, because retrying inside a held token lock multiplies
  the time every other caller waits, and the gateway client is specified to add no
  retries of its own. A failed read is a failed read.
"""

from __future__ import annotations

import asyncio
import datetime as dt
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from butterfly_guy.schwab_gateway.token_adapter import LockedSchwabClientAdapter

DEFAULT_QUOTE_BATCH_SIZE = 150


class GatewayUpstreamSettings(BaseSettings):
    """Real credential inputs for a live-serving gateway process.

    Deliberately a separate class from ``GatewayCredentialProbeSettings`` rather than a
    reuse of it. That class and the module it lives in are members of the credential
    proof's reviewed archive, whose SHA-256 is gated on Helios; editing or widening it
    would change the archive hash for a proof that is already complete.
    """

    model_config = SettingsConfigDict(extra="ignore")

    api_key: SecretStr = Field(validation_alias="SCHWAB_API_KEY")
    app_secret: SecretStr = Field(validation_alias="SCHWAB_SECRET_KEY")
    token_path: Path = Field(validation_alias="SCHWAB_TOKEN_PATH", repr=False)

    @field_validator("token_path")
    @classmethod
    def token_path_must_be_absolute(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("gateway token path must be absolute")
        return value


def extract_spot_price(payload: Any, symbol: str) -> float:
    """Pull a spot price out of a Schwab quote response.

    This mirrors ``SchwabClientWrapper.get_spot_price`` (``data/schwab_client.py:122-130``)
    exactly, including the ``lastPrice`` -> ``mark`` -> ``closePrice`` preference and the
    unprefixed-symbol fallback, so a gateway spot read and a direct spot read cannot
    disagree about the same payload. ``data/schwab_client.py`` is not modified to share
    this helper; the duplication is pinned by a differential test instead.
    """
    if not isinstance(payload, dict):
        raise ValueError("spot response was not an object")
    quote = payload.get(symbol, payload.get(symbol.lstrip("$"), {}))
    if not isinstance(quote, dict):
        raise ValueError("spot response entry was not an object")
    if "quote" in quote:
        quote = quote["quote"]
    if not isinstance(quote, dict):
        raise ValueError("spot response quote was not an object")
    price = quote.get("lastPrice") or quote.get("mark") or quote.get("closePrice")
    if not price:
        raise ValueError("spot response carried no usable price")
    return float(price)


@contextmanager
def _closing_session(client: Any) -> Iterator[None]:
    """Close the per-transaction HTTP session the client factory opened.

    Each transaction builds its own client, so each one owns a session that would
    otherwise leak. This is the same teardown the credential probe uses.
    """
    try:
        yield
    finally:
        close = getattr(getattr(client, "session", None), "close", None)
        if callable(close):
            close()


class LockedSchwabMarketDataProvider:
    """Read-only Schwab market data through one locked token transaction per call."""

    def __init__(self, adapter: LockedSchwabClientAdapter) -> None:
        self._adapter = adapter

    async def _execute(self, operation: Any) -> Any:
        """Run one synchronous locked transaction without blocking the event loop."""
        return await asyncio.to_thread(self._adapter.execute, operation)

    async def get_spot_price(self, symbol: str = "$SPX") -> float:
        def operation(client: Any) -> float:
            with _closing_session(client):
                response = client.get_quote(symbol)
                response.raise_for_status()
                return extract_spot_price(response.json(), symbol)

        return await self._execute(operation)

    async def get_option_chain(
        self, symbol: str, expiration: dt.date
    ) -> dict[str, Any]:
        def operation(client: Any) -> dict[str, Any]:
            with _closing_session(client):
                response = client.get_option_chain(
                    symbol,
                    from_date=expiration,
                    to_date=expiration,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("option chain response was not an object")
                return payload

        return await self._execute(operation)

    async def get_equity_quotes(
        self,
        symbols: list[str],
        *,
        batch_size: int = DEFAULT_QUOTE_BATCH_SIZE,
    ) -> dict[str, dict[str, Any]]:
        if not symbols:
            return {}
        if batch_size < 1:
            raise ValueError("quote batch size must be positive")

        def operation(client: Any) -> dict[str, dict[str, Any]]:
            with _closing_session(client):
                fields = [client.Quote.Fields.QUOTE, client.Quote.Fields.EXTENDED]
                results: dict[str, dict[str, Any]] = {}
                for start in range(0, len(symbols), batch_size):
                    response = client.get_quotes(
                        symbols[start : start + batch_size],
                        fields=fields,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if isinstance(payload, dict):
                        results.update(payload)
                return results

        # Every batch shares one transaction, so a multi-batch scanner request takes the
        # token lock once rather than once per batch.
        return await self._execute(operation)
