"""aiohttp API for the minimal read-only Schwab gateway."""

from __future__ import annotations

import asyncio
import datetime as dt
import re
import time
from typing import Protocol

from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from butterfly_guy.core.logging import get_logger
from butterfly_guy.gateway_client.models import (
    GatewayHealthV1,
    GatewayReadinessV1,
    QuoteResponseV1,
)
from butterfly_guy.schwab_gateway.auth import (
    AUTHENTICATOR_KEY,
    PRINCIPAL_KEY,
    InternalKeyAuthenticator,
    authentication_middleware,
    require_capability,
)
from butterfly_guy.schwab_gateway.token_manager import (
    TokenManagerHealth,
    TokenManagerState,
)
from butterfly_guy.schwab_gateway.upstream import (
    QuoteUpstream,
    UpstreamMalformedError,
    UpstreamUnavailableError,
)

log = get_logger(__name__)
UTC = dt.timezone.utc
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9$._/-]{1,32}$")
MAX_SYMBOLS = 100

gateway_requests = Counter(
    "gateway_client_requests_total",
    "Internal gateway client requests",
    ["operation", "status"],
)
gateway_latency = Histogram(
    "gateway_client_request_latency_seconds",
    "Internal gateway request latency",
    ["operation"],
)

UPSTREAM_KEY = web.AppKey("gateway_quote_upstream", QuoteUpstream)
UPSTREAM_TIMEOUT_KEY = web.AppKey("gateway_upstream_timeout", float)
TOKEN_READINESS_PROVIDER_KEY = web.AppKey(
    "gateway_token_readiness_provider", "TokenReadinessProvider"
)


class TokenReadinessProvider(Protocol):
    """Injected boundary for the token manager's bounded readiness state."""

    def health(self) -> TokenManagerHealth: ...


class StaticTokenReadinessProvider:
    """Deterministic fake-only readiness provider for the demo runner."""

    def __init__(self, state: TokenManagerState) -> None:
        self._state = state

    def health(self) -> TokenManagerHealth:
        return TokenManagerHealth(
            state=self._state,
            reason="static_provider",
            updated_at=dt.datetime.now(UTC),
        )


class _UnavailableTokenReadinessProvider:
    """Fail closed when an app has no injected readiness dependency."""

    def health(self) -> TokenManagerHealth:
        return TokenManagerHealth(
            state=TokenManagerState.UNINITIALIZED,
            reason="provider_not_configured",
            updated_at=dt.datetime.now(UTC),
        )


READINESS_REASON_BY_STATE = {
    TokenManagerState.UNINITIALIZED: "token_not_checked",
    TokenManagerState.READY: "token_ready",
    TokenManagerState.REFRESHING: "token_refreshing",
    TokenManagerState.MISSING: "token_missing",
    TokenManagerState.CORRUPT: "token_corrupt",
    TokenManagerState.EXPIRED: "refresh_token_expired",
    TokenManagerState.REVOKED: "token_revoked",
    TokenManagerState.REAUTHORIZATION_REQUIRED: "token_reauthorization_required",
    TokenManagerState.LOCK_TIMEOUT: "token_lock_timeout",
    TokenManagerState.REFRESH_FAILED: "token_refresh_failed",
    TokenManagerState.PERSISTENCE_FAILED: "token_persistence_failed",
}
READINESS_UNAVAILABLE_REASON = "token_readiness_unavailable"


def _json(model, *, status: int = 200) -> web.Response:
    return web.json_response(model.model_dump(mode="json"), status=status)


def _error(code: str, message: str, status: int) -> web.Response:
    return web.json_response(
        {
            "schema_version": "1.0",
            "error": {"code": code, "message": message},
        },
        status=status,
    )


def _parse_symbols(request: web.Request) -> tuple[str, ...]:
    value = request.query.get("symbols", "")
    symbols = tuple(part.strip().upper() for part in value.split(",") if part.strip())
    if not symbols:
        raise ValueError("at least one symbol is required")
    if len(symbols) > MAX_SYMBOLS:
        raise ValueError(f"at most {MAX_SYMBOLS} symbols are allowed")
    if len(set(symbols)) != len(symbols):
        raise ValueError("symbols must be unique")
    if any(not SYMBOL_PATTERN.fullmatch(symbol) for symbol in symbols):
        raise ValueError("one or more symbols are invalid")
    return symbols


@web.middleware
async def audit_middleware(request: web.Request, handler) -> web.StreamResponse:
    started = time.perf_counter()
    status = 500
    operation = request.match_info.route.name or "unknown"
    caller = "anonymous"
    try:
        response = await handler(request)
        status = response.status
        principal = request.get(PRINCIPAL_KEY)
        if principal is not None:
            caller = principal.client_id
        return response
    except web.HTTPException as exc:
        status = exc.status
        raise
    finally:
        elapsed = time.perf_counter() - started
        gateway_requests.labels(operation=operation, status=str(status)).inc()
        gateway_latency.labels(operation=operation).observe(elapsed)
        log.info(
            "gateway_request",
            caller=caller,
            operation=operation,
            status=status,
            latency_ms=round(elapsed * 1000, 2),
        )


async def health(_request: web.Request) -> web.Response:
    return _json(
        GatewayHealthV1(
            status="ok",
            timestamp=dt.datetime.now(UTC),
        )
    )


async def ready(_request: web.Request) -> web.Response:
    try:
        manager_health = _request.app[TOKEN_READINESS_PROVIDER_KEY].health()
        state = manager_health.state
        reason = READINESS_REASON_BY_STATE.get(state)
    except Exception:
        state = TokenManagerState.UNINITIALIZED
        reason = None
        log.warning("gateway_readiness_provider_failed", reason="provider_unavailable")
    if reason is None:
        state = TokenManagerState.UNINITIALIZED
        reason = READINESS_UNAVAILABLE_REASON
    is_ready = state is TokenManagerState.READY
    return _json(
        GatewayReadinessV1(
            status="ready" if is_ready else "not_ready",
            timestamp=dt.datetime.now(UTC),
            token_state=state.value,
            reason=reason,
        ),
        status=200 if is_ready else 503,
    )


async def metrics(_request: web.Request) -> web.Response:
    return web.Response(body=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})


async def quotes(request: web.Request) -> web.Response:
    denied = require_capability(request, "market_data:read")
    if denied is not None:
        return denied
    try:
        symbols = _parse_symbols(request)
    except ValueError as exc:
        return _error("invalid_request", str(exc), 400)

    try:
        async with asyncio.timeout(request.app[UPSTREAM_TIMEOUT_KEY]):
            result = await request.app[UPSTREAM_KEY].get_quotes(symbols)
        by_symbol = {quote.symbol: quote for quote in result}
        if set(by_symbol) != set(symbols):
            raise UpstreamMalformedError("upstream returned a partial symbol set")
        ordered = tuple(by_symbol[symbol] for symbol in symbols)
        return _json(QuoteResponseV1(quotes=ordered))
    except TimeoutError:
        return _error("upstream_timeout", "quote upstream timed out", 504)
    except UpstreamUnavailableError:
        return _error("upstream_unavailable", "quote upstream is unavailable", 503)
    except (UpstreamMalformedError, ValueError):
        return _error("upstream_malformed", "quote upstream returned invalid data", 502)


def create_app(
    upstream: QuoteUpstream,
    authenticator: InternalKeyAuthenticator,
    *,
    upstream_timeout_seconds: float = 3.0,
    token_readiness_provider: TokenReadinessProvider | None = None,
) -> web.Application:
    if upstream_timeout_seconds <= 0:
        raise ValueError("upstream timeout must be positive")
    app = web.Application(middlewares=[audit_middleware, authentication_middleware])
    app[UPSTREAM_KEY] = upstream
    app[AUTHENTICATOR_KEY] = authenticator
    app[UPSTREAM_TIMEOUT_KEY] = upstream_timeout_seconds
    app[TOKEN_READINESS_PROVIDER_KEY] = (
        token_readiness_provider or _UnavailableTokenReadinessProvider()
    )
    app.router.add_get("/health", health, name="health")
    app.router.add_get("/ready", ready, name="ready")
    app.router.add_get("/metrics", metrics, name="metrics")
    app.router.add_get("/v1/quotes", quotes, name="quotes_v1")
    return app
