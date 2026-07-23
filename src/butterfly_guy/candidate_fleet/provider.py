"""Market-data provider contract and shared-feed HTTP implementation."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

import httpx

from butterfly_guy.candidate_fleet.models import (
    LeaseKind,
    MarketSnapshot,
    SnapshotIdentity,
    SnapshotUnavailableError,
)


@runtime_checkable
class MarketDataProvider(Protocol):
    """The complete market-data surface available to a strategy evaluator."""

    async def snapshot(
        self,
        *,
        after: SnapshotIdentity | None = None,
        wait_seconds: float = 0,
        max_age_seconds: float = 65,
    ) -> MarketSnapshot: ...

    async def legs(
        self,
        symbols: tuple[str, ...],
        *,
        after: SnapshotIdentity | None = None,
        wait_seconds: float = 0,
        max_age_seconds: float = 3,
    ) -> MarketSnapshot: ...

    async def refresh_lease(self, candidate_id: str, kind: LeaseKind) -> None: ...

    async def release_lease(self, candidate_id: str) -> None: ...

    async def pin(self, identity: SnapshotIdentity) -> None: ...

    async def close(self) -> None: ...


class HttpMarketDataProvider:
    """Fail-closed client for the internal candidate feed."""

    def __init__(
        self,
        base_url: str,
        *,
        request_timeout_seconds: float = 35,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=request_timeout_seconds,
        )

    async def snapshot(
        self,
        *,
        after: SnapshotIdentity | None = None,
        wait_seconds: float = 0,
        max_age_seconds: float = 65,
    ) -> MarketSnapshot:
        params = self._wait_params(after, wait_seconds)
        return await self._get_snapshot("/v1/snapshot", params, max_age_seconds)

    async def legs(
        self,
        symbols: tuple[str, ...],
        *,
        after: SnapshotIdentity | None = None,
        wait_seconds: float = 0,
        max_age_seconds: float = 3,
    ) -> MarketSnapshot:
        if not symbols:
            raise ValueError("at least one symbol is required")
        params: list[tuple[str, str | int | float]] = [
            ("symbol", symbol) for symbol in symbols
        ]
        params.extend(self._wait_params(after, wait_seconds).items())
        return await self._get_snapshot("/v1/legs", params, max_age_seconds)

    async def refresh_lease(self, candidate_id: str, kind: LeaseKind) -> None:
        response = await self._request_with_retry(
            "PUT",
            f"/v1/leases/{candidate_id}",
            json={"kind": kind},
        )
        response.raise_for_status()

    async def release_lease(self, candidate_id: str) -> None:
        response = await self._request_with_retry(
            "DELETE",
            f"/v1/leases/{candidate_id}",
        )
        if response.status_code not in {204, 404}:
            response.raise_for_status()

    async def pin(self, identity: SnapshotIdentity) -> None:
        response = await self._request_with_retry(
            "POST",
            f"/v1/snapshots/{identity.instance}/{identity.sequence}/pin",
        )
        response.raise_for_status()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    @staticmethod
    def _wait_params(
        after: SnapshotIdentity | None,
        wait_seconds: float,
    ) -> dict[str, str | int | float]:
        params: dict[str, str | int | float] = {
            "wait_seconds": min(max(wait_seconds, 0), 30),
        }
        if after is not None:
            params["after_instance"] = after.instance
            params["after_sequence"] = after.sequence
        return params

    async def _get_snapshot(
        self,
        path: str,
        params: object,
        max_age_seconds: float,
    ) -> MarketSnapshot:
        try:
            response = await self._request_with_retry("GET", path, params=params)
            response.raise_for_status()
            return MarketSnapshot.from_dict(response.json()).require_fresh(max_age_seconds)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise SnapshotUnavailableError(f"candidate feed unavailable: {exc}") from exc

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: object,
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await self._client.request(method, path, **kwargs)
                if response.status_code < 500:
                    return response
                last_error = httpx.HTTPStatusError(
                    "candidate feed server error",
                    request=response.request,
                    response=response,
                )
            except httpx.TransportError as exc:
                last_error = exc
            if attempt < 2:
                await asyncio.sleep(0.2 * 2**attempt)
        assert last_error is not None
        raise last_error


class SchwabMarketDataProvider:
    """Direct-provider adapter for primary/parity paths that normalize Schwab data."""

    def __init__(
        self,
        snapshot_loader: Callable[[], Awaitable[MarketSnapshot]],
        *,
        close_callback: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self._snapshot_loader = snapshot_loader
        self._close_callback = close_callback

    async def snapshot(
        self,
        *,
        after: SnapshotIdentity | None = None,
        wait_seconds: float = 0,
        max_age_seconds: float = 65,
    ) -> MarketSnapshot:
        snapshot = await self._snapshot_loader()
        if (
            after is not None
            and after == snapshot.identity
            and wait_seconds > 0
        ):
            await asyncio.sleep(min(wait_seconds, 30))
            snapshot = await self._snapshot_loader()
        return snapshot.require_fresh(max_age_seconds)

    async def legs(
        self,
        symbols: tuple[str, ...],
        *,
        after: SnapshotIdentity | None = None,
        wait_seconds: float = 0,
        max_age_seconds: float = 3,
    ) -> MarketSnapshot:
        snapshot = await self.snapshot(
            after=after,
            wait_seconds=wait_seconds,
            max_age_seconds=max_age_seconds,
        )
        return snapshot.leg_quotes(symbols)

    async def refresh_lease(self, candidate_id: str, kind: LeaseKind) -> None:
        return None

    async def release_lease(self, candidate_id: str) -> None:
        return None

    async def pin(self, identity: SnapshotIdentity) -> None:
        return None

    async def close(self) -> None:
        if self._close_callback is not None:
            await self._close_callback()
