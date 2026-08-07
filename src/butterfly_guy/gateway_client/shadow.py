"""Phase 3 shadow comparison for the collector's spot and chain reads.

This decorator is deliberately not constructed by any service. It exists so a shadow
comparison can be reviewed and enabled as its own decision. The direct result is always
what the caller receives; the gateway is observed and never trusted.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import math
from dataclasses import dataclass
from typing import Any

from butterfly_guy.core.logging import get_logger
from butterfly_guy.data.providers import CollectorMarketDataProvider
from butterfly_guy.gateway_client.chain_metadata import extract_chain_metadata
from butterfly_guy.gateway_client.client import (
    GatewayAuthenticationError,
    GatewayAuthorizationError,
    GatewayCapacityError,
    GatewayMarketDataClient,
    GatewayResponseError,
    GatewayTimeoutError,
    GatewayUnavailableError,
)

log = get_logger(__name__)

SHADOW_CLASSIFICATIONS = ("timing", "cache", "parsing", "upstream")

#: Every diagnostic this module can emit. Nothing outside this table reaches a log.
CLASSIFICATION_BY_CODE: dict[str, str] = {
    "gateway_timeout": "timing",
    "gateway_unknown_age": "timing",
    "gateway_stale_value": "cache",
    "gateway_value_mismatch": "parsing",
    "gateway_contract_invalid": "parsing",
    "direct_payload_invalid": "parsing",
    "gateway_unavailable": "upstream",
    "gateway_capacity_exceeded": "upstream",
    "gateway_authentication_failed": "upstream",
    "gateway_authorization_failed": "upstream",
    "gateway_unexpected_error": "upstream",
}

_CODE_BY_ERROR: tuple[tuple[type[Exception], str], ...] = (
    (GatewayTimeoutError, "gateway_timeout"),
    (GatewayCapacityError, "gateway_capacity_exceeded"),
    (GatewayAuthenticationError, "gateway_authentication_failed"),
    (GatewayAuthorizationError, "gateway_authorization_failed"),
    (GatewayResponseError, "gateway_contract_invalid"),
    (GatewayUnavailableError, "gateway_unavailable"),
)

SPOT_FIELDS = ("price",)
CHAIN_COUNT_FIELDS = (
    "call_contract_count",
    "put_contract_count",
    "strike_count",
)


@dataclass(frozen=True)
class ShadowDiscrepancy:
    """A bounded, fixed-shape observation. Carries no payload, path, or exception text."""

    operation: str
    code: str
    classification: str
    fields: tuple[str, ...] = ()


class ShadowDiscrepancyRecorder:
    """Tally discrepancies over a fixed key space; retains no observed values."""

    def __init__(self) -> None:
        self._counts: dict[ShadowDiscrepancy, int] = {}

    def record(self, discrepancy: ShadowDiscrepancy) -> None:
        self._counts[discrepancy] = self._counts.get(discrepancy, 0) + 1

    def counts(self) -> dict[ShadowDiscrepancy, int]:
        return dict(self._counts)

    def total(self) -> int:
        return sum(self._counts.values())


def _error_code(exc: Exception) -> str:
    for error_type, code in _CODE_BY_ERROR:
        if isinstance(exc, error_type):
            return code
    return "gateway_unexpected_error"


def _mismatch_code(*, stale: bool, age_seconds: float | None) -> str:
    """Classify a value difference by what the gateway could prove about its freshness."""
    if age_seconds is None:
        return "gateway_unknown_age"
    if stale:
        return "gateway_stale_value"
    return "gateway_value_mismatch"


def _numbers_agree(direct: float | None, gateway: float | None, tolerance: float) -> bool:
    if direct is None or gateway is None:
        return direct is None and gateway is None
    return math.isclose(direct, gateway, rel_tol=0.0, abs_tol=tolerance)


class ShadowComparingMarketDataProvider:
    """Return the direct read always; compare a gateway read alongside it when enabled.

    A gateway failure of any kind is recorded and swallowed. The wrapped direct provider
    is the only source of the returned value, on every path.
    """

    def __init__(
        self,
        direct: CollectorMarketDataProvider,
        gateway: GatewayMarketDataClient | None = None,
        *,
        shadow_reads: bool = False,
        recorder: ShadowDiscrepancyRecorder | None = None,
        price_tolerance: float = 0.01,
    ) -> None:
        if price_tolerance < 0:
            raise ValueError("price tolerance must be nonnegative")
        self._direct = direct
        self._gateway = gateway
        self._shadow_reads = shadow_reads
        self._price_tolerance = price_tolerance
        self.recorder = recorder or ShadowDiscrepancyRecorder()
        self._background_tasks: set[asyncio.Task[None]] = set()

    @property
    def shadow_enabled(self) -> bool:
        return self._shadow_reads and self._gateway is not None

    def _spawn_background(self, coro: Any, *, name: str) -> None:
        """Run a shadow comparison off the caller's critical path.

        The comparison methods already catch every gateway/comparison failure
        internally, so this task should never raise -- the broad except here is
        only a defensive backstop against "exception was never retrieved".
        """
        task = asyncio.create_task(coro, name=name)
        self._background_tasks.add(task)

        def _on_done(finished: asyncio.Task[None]) -> None:
            self._background_tasks.discard(finished)
            if finished.cancelled():
                return
            exc = finished.exception()
            if exc is not None:
                log.warning("gateway_shadow_task_failed", error=str(exc))

        task.add_done_callback(_on_done)

    async def wait_for_shadow_reads(self) -> None:
        """Wait for any in-flight shadow comparisons to finish.

        Not used on the collector's hot path -- only for tests and graceful
        shutdown, where deterministically observing the recorder matters.
        """
        pending = tuple(self._background_tasks)
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    def _record(self, operation: str, code: str, fields: tuple[str, ...] = ()) -> None:
        discrepancy = ShadowDiscrepancy(
            operation=operation,
            code=code,
            classification=CLASSIFICATION_BY_CODE[code],
            fields=fields,
        )
        self.recorder.record(discrepancy)
        log.warning(
            "gateway_shadow_discrepancy",
            operation=discrepancy.operation,
            code=discrepancy.code,
            classification=discrepancy.classification,
            fields=discrepancy.fields,
        )

    async def get_spot_price(self, symbol: str = "$SPX") -> float:
        direct_task: asyncio.Task[float] = asyncio.create_task(
            self._direct.get_spot_price(symbol)
        )
        if self.shadow_enabled:
            gateway_task = asyncio.create_task(self._gateway.get_spot(symbol))
            self._spawn_background(
                self._shadow_spot(direct_task, gateway_task),
                name="gateway_shadow_spot",
            )
        return await direct_task

    async def _shadow_spot(
        self,
        direct_task: asyncio.Task[float],
        gateway_task: asyncio.Task[Any],
    ) -> None:
        try:
            response = await gateway_task
        except Exception as exc:  # every gateway failure is observed, never propagated
            self._record("spot", _error_code(exc))
            return
        try:
            direct_price = await direct_task
        except Exception:
            # The direct failure is the caller's problem; nothing to shadow.
            return
        observed = response.spot
        if _numbers_agree(direct_price, observed.price, self._price_tolerance):
            return
        self._record(
            "spot",
            _mismatch_code(stale=observed.stale, age_seconds=observed.age_seconds),
            SPOT_FIELDS,
        )

    async def get_option_chain(
        self, symbol: str, expiration: dt.date
    ) -> dict[str, Any]:
        direct_task: asyncio.Task[dict[str, Any]] = asyncio.create_task(
            self._direct.get_option_chain(symbol, expiration)
        )
        if self.shadow_enabled:
            gateway_task = asyncio.create_task(
                self._gateway.get_chain_metadata(symbol, expiration)
            )
            self._spawn_background(
                self._shadow_chain(expiration, direct_task, gateway_task),
                name="gateway_shadow_chain",
            )
        return await direct_task

    async def _shadow_chain(
        self,
        expiration: dt.date,
        direct_task: asyncio.Task[dict[str, Any]],
        gateway_task: asyncio.Task[Any],
    ) -> None:
        try:
            response = await gateway_task
        except Exception as exc:  # every gateway failure is observed, never propagated
            self._record("chain", _error_code(exc))
            return
        try:
            payload = await direct_task
        except Exception:
            # The direct failure is the caller's problem; nothing to shadow.
            return
        try:
            direct_fields = extract_chain_metadata(payload, expiration)
        except ValueError:
            self._record("chain", "direct_payload_invalid")
            return

        observed = response.chain
        differing: list[str] = []
        if not _numbers_agree(
            direct_fields.underlying_price,
            observed.underlying_price,
            self._price_tolerance,
        ):
            differing.append("underlying_price")
        for field in CHAIN_COUNT_FIELDS:
            if getattr(direct_fields, field) != getattr(observed, field):
                differing.append(field)
        if not differing:
            return
        self._record(
            "chain",
            _mismatch_code(stale=observed.stale, age_seconds=observed.age_seconds),
            tuple(differing),
        )

    async def get_intraday_bars(
        self, symbol: str = "$SPX", days_back: int = 1
    ) -> list[dict]:
        return await self._direct.get_intraday_bars(symbol, days_back)

    async def get_intraday_bars_for_day(
        self,
        symbol: str,
        day: dt.date,
        *,
        include_extended_hours: bool = True,
    ) -> list[dict]:
        return await self._direct.get_intraday_bars_for_day(
            symbol,
            day,
            include_extended_hours=include_extended_hours,
        )

    async def get_daily_bars(self, symbol: str, days_back: int = 10) -> list[dict]:
        return await self._direct.get_daily_bars(symbol, days_back)
