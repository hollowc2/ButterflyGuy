"""Fail-closed ButterflyGuy client for SchwabGateway venue order books."""

from __future__ import annotations

import asyncio
import datetime as dt
import math
import re
from collections.abc import AsyncIterator, Sequence
from typing import Literal

import aiohttp
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

Venue = Literal["NASDAQ", "NYSE"]
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9$._/-]{1,32}$")


class OrderBookClientError(RuntimeError):
    """Base error for gateway order-book transport and contract failures."""


class OrderBookAuthenticationError(OrderBookClientError):
    pass


class OrderBookAuthorizationError(OrderBookClientError):
    pass


class OrderBookCapacityError(OrderBookClientError):
    pass


class OrderBookUnavailableError(OrderBookClientError):
    pass


class OrderBookContractError(OrderBookClientError):
    pass


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OrderBookParticipant(_Contract):
    exchange: str
    size: int = Field(ge=0)
    sequence: int | None = None

    @field_validator("exchange")
    @classmethod
    def exchange_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("order-book participant exchange must not be empty")
        return value


class OrderBookLevel(_Contract):
    price: float
    total_size: int = Field(ge=0)
    participant_count: int = Field(ge=0)
    participants: tuple[OrderBookParticipant, ...] = ()

    @field_validator("price")
    @classmethod
    def price_must_be_positive_and_finite(cls, value: float) -> float:
        if not math.isfinite(value) or value <= 0:
            raise ValueError("order-book price must be positive and finite")
        return value


class OrderBookSnapshot(_Contract):
    schema_version: Literal["1.0"]
    symbol: str
    venue: Venue
    service: Literal["NASDAQ_BOOK", "NYSE_BOOK"]
    connection_id: int = Field(ge=1)
    continuity_epoch: int = Field(ge=1)
    sequence: int | None = None
    event_timestamp: dt.datetime | None = None
    gateway_received_at: dt.datetime
    source: Literal["schwab_streaming"]
    is_consolidated: Literal[False]
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    data_quality_flags: tuple[str, ...] = ()

    @field_validator("event_timestamp", "gateway_received_at")
    @classmethod
    def timestamps_must_be_aware(
        cls, value: dt.datetime | None
    ) -> dt.datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("order-book timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def venue_and_levels_must_match_contract(self) -> OrderBookSnapshot:
        if self.service != f"{self.venue}_BOOK":
            raise ValueError("order-book service does not match venue")
        if [level.price for level in self.bids] != sorted(
            (level.price for level in self.bids), reverse=True
        ):
            raise ValueError("order-book bids must be sorted highest first")
        if [level.price for level in self.asks] != sorted(
            level.price for level in self.asks
        ):
            raise ValueError("order-book asks must be sorted lowest first")
        return self


class RecentOrderBooks(_Contract):
    schema_version: Literal["1.0"]
    symbol: str
    venue: Venue
    is_consolidated: Literal[False]
    snapshots: tuple[OrderBookSnapshot, ...]
    generated_at: dt.datetime
    stale: Literal[False]
    age_seconds: float = Field(ge=0)

    @field_validator("generated_at")
    @classmethod
    def generated_at_must_be_aware(cls, value: dt.datetime) -> dt.datetime:
        if value.utcoffset() is None:
            raise ValueError("order-book response timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def snapshots_must_match_response(self) -> RecentOrderBooks:
        if any(
            snapshot.symbol != self.symbol or snapshot.venue != self.venue
            for snapshot in self.snapshots
        ):
            raise ValueError("order-book response contains mismatched snapshots")
        return self


class _StreamEnvelope(_Contract):
    schema_version: Literal["1.0"]
    type: Literal["order_book_snapshot"]
    snapshot: OrderBookSnapshot


def _normalize_venue(venue: str) -> Venue:
    normalized = venue.strip().upper()
    if normalized not in {"NASDAQ", "NYSE"}:
        raise ValueError("venue must be 'NASDAQ' or 'NYSE'")
    return normalized  # type: ignore[return-value]


def _normalize_symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(symbol.strip().upper() for symbol in symbols)
    if not normalized or any(not symbol for symbol in normalized):
        raise ValueError("at least one non-empty order-book symbol is required")
    if len(normalized) > 25:
        raise ValueError("at most 25 order-book symbols are allowed")
    if len(set(normalized)) != len(normalized):
        raise ValueError("order-book symbols must be unique")
    if any(not SYMBOL_PATTERN.fullmatch(symbol) for symbol in normalized):
        raise ValueError("one or more order-book symbols are invalid")
    return normalized


class GatewayOrderBookClient:
    """Read recent depth or consume the gateway's bounded live WebSocket."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: float = 5.0,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("gateway base URL is required")
        if not api_key:
            raise ValueError("gateway API key is required")
        if timeout_seconds <= 0:
            raise ValueError("gateway timeout must be positive")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._owns_session = session is None
        self._session = session or aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout_seconds)
        )

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Internal-API-Key": self._api_key}

    @staticmethod
    def _raise_status(status: int) -> None:
        if status == 401:
            raise OrderBookAuthenticationError("gateway authentication failed")
        if status == 403:
            raise OrderBookAuthorizationError("gateway capability denied")
        if status == 429:
            raise OrderBookCapacityError("gateway order-book capacity is unavailable")
        if status in {502, 503, 504}:
            raise OrderBookUnavailableError("gateway order book is unavailable")
        if status != 200:
            raise OrderBookContractError(
                f"gateway order-book request failed with status {status}"
            )

    async def recent(
        self,
        symbol: str,
        *,
        venue: str,
        limit: int = 100,
    ) -> RecentOrderBooks:
        symbols = _normalize_symbols((symbol,))
        normalized_venue = _normalize_venue(venue)
        if not 1 <= limit <= 1000:
            raise ValueError("order-book limit must be between 1 and 1000")
        try:
            async with self._session.get(
                f"{self._base_url}/v1/order-book/recent",
                params={
                    "symbol": symbols[0],
                    "venue": normalized_venue,
                    "limit": str(limit),
                },
                headers=self._headers,
            ) as response:
                self._raise_status(response.status)
                payload = await response.json()
        except asyncio.TimeoutError as exc:
            raise OrderBookUnavailableError("gateway order-book request timed out") from exc
        except aiohttp.ClientError as exc:
            raise OrderBookUnavailableError(
                "gateway order-book request failed"
            ) from exc
        try:
            result = RecentOrderBooks.model_validate(payload)
        except (ValueError, ValidationError) as exc:
            raise OrderBookContractError(
                "gateway returned an invalid or mismatched recent order-book contract"
            ) from exc
        if result.symbol != symbols[0] or result.venue != normalized_venue:
            raise OrderBookContractError(
                "gateway returned a different order-book symbol or venue"
            )
        return result

    async def stream(
        self,
        symbols: Sequence[str],
        *,
        venue: str,
    ) -> AsyncIterator[OrderBookSnapshot]:
        requested = _normalize_symbols(symbols)
        normalized_venue = _normalize_venue(venue)
        try:
            async with self._session.ws_connect(
                f"{self._base_url}/v1/order-book/stream",
                params={"symbols": ",".join(requested), "venue": normalized_venue},
                headers=self._headers,
                heartbeat=30,
            ) as socket:
                async for message in socket:
                    if message.type == aiohttp.WSMsgType.ERROR:
                        raise OrderBookUnavailableError(
                            "gateway order-book stream failed"
                        )
                    if message.type != aiohttp.WSMsgType.TEXT:
                        continue
                    try:
                        envelope = _StreamEnvelope.model_validate_json(message.data)
                    except (ValueError, ValidationError) as exc:
                        raise OrderBookContractError(
                            "gateway returned an invalid order-book stream contract"
                        ) from exc
                    snapshot = envelope.snapshot
                    if snapshot.symbol not in requested or snapshot.venue != normalized_venue:
                        raise OrderBookContractError(
                            "gateway streamed an unrequested order-book snapshot"
                        )
                    yield snapshot
        except aiohttp.WSServerHandshakeError as exc:
            self._raise_status(exc.status)
            raise OrderBookContractError(
                f"gateway WebSocket upgrade failed with status {exc.status}"
            ) from exc
        except asyncio.TimeoutError as exc:
            raise OrderBookUnavailableError("gateway order-book stream timed out") from exc
        except aiohttp.ClientError as exc:
            raise OrderBookUnavailableError("gateway order-book stream failed") from exc

    async def close(self) -> None:
        if self._owns_session:
            await self._session.close()

    async def __aenter__(self) -> GatewayOrderBookClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()
