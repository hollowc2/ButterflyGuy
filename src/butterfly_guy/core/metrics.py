"""Prometheus metrics for monitoring."""

from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

# Chain collection
chain_snapshots_total = Counter(
    "butterfly_chain_snapshots_total", "Total option chain snapshots collected",
    ["underlying"],
)
chain_snapshot_duration = Histogram(
    "butterfly_chain_snapshot_duration_seconds", "Time to collect a chain snapshot",
    ["underlying"],
)
chain_snapshot_rows = Gauge(
    "butterfly_chain_snapshot_rows", "Number of rows in last chain snapshot",
    ["underlying"],
)

# Butterfly scanning
butterfly_scans_total = Counter(
    "butterfly_scans_total", "Total butterfly scans performed",
    ["underlying"],
)
butterfly_candidates_found = Gauge(
    "butterfly_candidates_found", "Candidates found in last scan",
    ["underlying"],
)

# Trading
trades_total = Counter(
    "butterfly_trades_total", "Total trades executed",
    ["underlying", "direction", "outcome"],
)
trades_active = Gauge("butterfly_trades_active", "Currently active trades", ["underlying"])
daily_pnl = Gauge("butterfly_daily_pnl_dollars", "Daily realized PnL in dollars", ["underlying"])
daily_trade_count = Gauge("butterfly_daily_trade_count", "Trades executed today", ["underlying"])
entry_loop_errors = Counter(
    "butterfly_entry_loop_errors_total", "Total entry loop errors", ["underlying"]
)

# Position
position_value = Gauge("butterfly_position_value", "Current position mark value", ["underlying"])
position_peak_value = Gauge("butterfly_position_peak_value", "Peak position value", ["underlying"])
position_pnl = Gauge("butterfly_position_pnl", "Current position unrealized PnL", ["underlying"])

# Entry details — set at trade entry, held until next trade
entry_vix = Gauge("butterfly_entry_vix", "VIX at time of entry", ["underlying"])
entry_expected_move = Gauge(
    "butterfly_entry_expected_move_pts", "VIX-implied 1σ daily move in index points",
    ["underlying"],
)
entry_center_strike = Gauge(
    "butterfly_entry_center_strike", "Selected center strike", ["underlying"]
)
entry_wing_width = Gauge("butterfly_entry_wing_width", "Selected wing width", ["underlying"])
entry_cost = Gauge("butterfly_entry_cost", "Entry cost per spread", ["underlying"])
entry_max_profit = Gauge(
    "butterfly_entry_max_profit", "Max profit per spread at expiry", ["underlying"]
)
entry_lower_be = Gauge("butterfly_entry_lower_be", "Lower breakeven strike", ["underlying"])
entry_upper_be = Gauge("butterfly_entry_upper_be", "Upper breakeven strike", ["underlying"])

# Orders
orders_placed = Counter(
    "butterfly_orders_placed_total", "Total orders placed",
    ["underlying", "order_type"],
)
orders_filled = Counter(
    "butterfly_orders_filled_total", "Total orders filled",
    ["underlying", "order_type"],
)
order_fill_duration = Histogram(
    "butterfly_order_fill_duration_seconds", "Time from order to fill",
    ["underlying"],
)

# System — no underlying label, shared infrastructure metrics
schwab_api_calls = Counter(
    "butterfly_schwab_api_calls_total", "Total Schwab API calls", ["endpoint"]
)
schwab_api_errors = Counter(
    "butterfly_schwab_api_errors_total", "Total Schwab API errors", ["endpoint"]
)


_server_start_time: float | None = None
_server_underlying: str = "unknown"
_readiness_lock = Lock()
_readiness_reasons: set[str] = {"starting"}


def set_readiness(reason: str | None) -> None:
    """Add a not-ready reason; ``None`` explicitly resets all reasons."""
    with _readiness_lock:
        if reason is None:
            _readiness_reasons.clear()
        else:
            _readiness_reasons.add(reason)


def clear_readiness(reason: str) -> None:
    """Clear only the recovered subsystem's not-ready reason."""
    with _readiness_lock:
        _readiness_reasons.discard(reason)


def readiness_snapshot() -> tuple[bool, str | None]:
    with _readiness_lock:
        reason = ",".join(sorted(_readiness_reasons)) or None
        return reason is None, reason


class _MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler serving both Prometheus metrics and health checks."""

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default request logging to stderr."""
        pass

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: int, content: str, content_type: str = "text/plain") -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            uptime = time.time() - _server_start_time if _server_start_time else 0.0
            self._send_json(200, {
                "status": "ok",
                "service": _server_underlying,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                "uptime_seconds": round(uptime, 1),
            })
        elif self.path == "/ready":
            ready, reason = readiness_snapshot()
            self._send_json(
                200 if ready else 503,
                {"status": "ready" if ready else "not_ready", "reason": reason},
            )
        elif self.path == "/metrics":
            self._send_text(200, generate_latest().decode("utf-8"), CONTENT_TYPE_LATEST)
        else:
            self._send_json(404, {"error": "not found"})


def start_metrics_server(port: int = 8000, underlying: str = "unknown") -> None:
    """Start HTTP server serving /metrics (Prometheus) and /health on *port*.

    Runs in a daemon thread so it does not block the main application.
    """
    global _server_start_time, _server_underlying
    _server_underlying = underlying
    _server_start_time = time.time()
    set_readiness("starting")

    server = ThreadingHTTPServer(("0.0.0.0", port), _MetricsHandler)
    thread = Thread(target=server.serve_forever, daemon=True, name=f"metrics-{port}")
    thread.start()
