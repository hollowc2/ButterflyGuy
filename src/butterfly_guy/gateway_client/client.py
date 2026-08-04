"""Fail-closed HTTP client for the read-only gateway contract."""

from __future__ import annotations

from collections.abc import Sequence

import httpx
from pydantic import ValidationError

from butterfly_guy.gateway_client.models import QuoteResponseV1


class GatewayClientError(RuntimeError):
    """Base error for gateway transport and contract failures."""


class GatewayAuthenticationError(GatewayClientError):
    pass


class GatewayAuthorizationError(GatewayClientError):
    pass


class GatewayTimeoutError(GatewayClientError):
    pass


class GatewayUnavailableError(GatewayClientError):
    pass


class GatewayCapacityError(GatewayClientError):
    pass


class GatewayResponseError(GatewayClientError):
    pass


class GatewayMarketDataClient:
    """Typed client for gateway market-data endpoints only."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: float = 5.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("gateway API key is required")
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def get_quotes(self, symbols: Sequence[str]) -> QuoteResponseV1:
        requested = tuple(symbols)
        if not requested:
            raise ValueError("at least one symbol is required")
        try:
            response = await self._client.get(
                "/v1/quotes",
                params={"symbols": ",".join(requested)},
                headers={"X-Internal-API-Key": self._api_key},
            )
        except httpx.TimeoutException as exc:
            raise GatewayTimeoutError("gateway quote request timed out") from exc
        except httpx.TransportError as exc:
            raise GatewayUnavailableError("gateway quote request unavailable") from exc

        if response.status_code == 401:
            raise GatewayAuthenticationError("gateway authentication failed")
        if response.status_code == 403:
            raise GatewayAuthorizationError("gateway capability denied")
        if response.status_code == 429:
            raise GatewayCapacityError("gateway request capacity is unavailable")
        if response.status_code == 504:
            raise GatewayTimeoutError("gateway quote upstream timed out")
        if response.status_code in {502, 503}:
            raise GatewayUnavailableError("gateway upstream is unavailable")
        if response.status_code != 200:
            raise GatewayResponseError(
                f"gateway quote request failed with status {response.status_code}"
            )
        try:
            return QuoteResponseV1.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise GatewayResponseError("gateway returned an invalid quote contract") from exc

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> GatewayMarketDataClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()
