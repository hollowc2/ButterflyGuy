"""Prometheus metrics for monitoring."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Chain collection
chain_snapshots_total = Counter(
    "butterfly_chain_snapshots_total", "Total option chain snapshots collected"
)
chain_snapshot_duration = Histogram(
    "butterfly_chain_snapshot_duration_seconds", "Time to collect a chain snapshot"
)
chain_snapshot_rows = Gauge(
    "butterfly_chain_snapshot_rows", "Number of rows in last chain snapshot"
)

# Butterfly scanning
butterfly_scans_total = Counter(
    "butterfly_scans_total", "Total butterfly scans performed"
)
butterfly_candidates_found = Gauge(
    "butterfly_candidates_found", "Candidates found in last scan"
)

# Trading
trades_total = Counter(
    "butterfly_trades_total", "Total trades executed", ["direction", "outcome"]
)
trades_active = Gauge("butterfly_trades_active", "Currently active trades")
daily_pnl = Gauge("butterfly_daily_pnl_dollars", "Daily realized PnL in dollars")
daily_trade_count = Gauge("butterfly_daily_trade_count", "Trades executed today")

# Position
position_value = Gauge("butterfly_position_value", "Current position mark value")
position_peak_value = Gauge("butterfly_position_peak_value", "Peak position value")
position_pnl = Gauge("butterfly_position_pnl", "Current position unrealized PnL")

# Entry details — set at trade entry, held until next trade
entry_vix = Gauge("butterfly_entry_vix", "VIX at time of entry")
entry_expected_move = Gauge("butterfly_entry_expected_move_pts", "VIX-implied 1σ daily move in SPX points")
entry_center_strike = Gauge("butterfly_entry_center_strike", "Selected center strike")
entry_wing_width = Gauge("butterfly_entry_wing_width", "Selected wing width")
entry_cost = Gauge("butterfly_entry_cost", "Entry cost per spread")
entry_max_profit = Gauge("butterfly_entry_max_profit", "Max profit per spread at expiry")
entry_lower_be = Gauge("butterfly_entry_lower_be", "Lower breakeven strike")
entry_upper_be = Gauge("butterfly_entry_upper_be", "Upper breakeven strike")

# Orders
orders_placed = Counter(
    "butterfly_orders_placed_total", "Total orders placed", ["order_type"]
)
orders_filled = Counter(
    "butterfly_orders_filled_total", "Total orders filled", ["order_type"]
)
order_fill_duration = Histogram(
    "butterfly_order_fill_duration_seconds", "Time from order to fill"
)

# System
schwab_api_calls = Counter(
    "butterfly_schwab_api_calls_total", "Total Schwab API calls", ["endpoint"]
)
schwab_api_errors = Counter(
    "butterfly_schwab_api_errors_total", "Total Schwab API errors", ["endpoint"]
)


def start_metrics_server(port: int = 8000) -> None:
    """Start the Prometheus metrics HTTP server."""
    start_http_server(port)
