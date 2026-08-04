"""Versioned, transport-neutral gateway API models."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class GatewayModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class QuoteV1(GatewayModel):
    symbol: str
    event_timestamp: dt.datetime | None = None
    gateway_received_at: dt.datetime
    source: str
    session: str | None = None
    bid: float | None = None
    ask: float | None = None
    bid_size: int | None = None
    ask_size: int | None = None
    last: float | None = None
    last_size: int | None = None
    mark: float | None = None
    volume: int | None = None
    stale: bool
    age_seconds: float | None = None
    data_quality_flags: tuple[str, ...] = ()

    @field_validator("event_timestamp", "gateway_received_at")
    @classmethod
    def timestamps_must_be_timezone_aware(
        cls, value: dt.datetime | None
    ) -> dt.datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("gateway timestamps must be timezone-aware")
        return value

    @field_validator("age_seconds")
    @classmethod
    def age_must_be_nonnegative(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("age_seconds must be nonnegative")
        return value


class QuoteResponseV1(GatewayModel):
    schema_version: Literal["1.0"] = "1.0"
    quotes: tuple[QuoteV1, ...]


class GatewayHealthV1(GatewayModel):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["ok", "ready", "not_ready"]
    service: Literal["schwab-gateway"] = "schwab-gateway"
    timestamp: dt.datetime


class GatewayReadinessV1(GatewayHealthV1):
    """Bounded token-readiness detail for gateway operators."""

    token_state: Literal[
        "uninitialized", "ready", "refreshing", "missing", "corrupt", "expired",
        "revoked", "reauthorization_required", "lock_timeout", "refresh_failed",
        "persistence_failed",
    ]
    reason: Literal[
        "token_not_checked", "token_ready", "token_refreshing", "token_missing",
        "token_corrupt", "refresh_token_expired", "token_revoked",
        "token_reauthorization_required", "token_lock_timeout", "token_refresh_failed",
        "token_persistence_failed", "token_readiness_unavailable",
    ]


class GatewayErrorDetailV1(GatewayModel):
    code: str
    message: str


class GatewayErrorV1(GatewayModel):
    schema_version: Literal["1.0"] = "1.0"
    error: GatewayErrorDetailV1
