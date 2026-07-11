"""Write a redacted read-only report of Schwab order statuses for one day."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any

from butterfly_guy.core.config import load_config
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.execution.order_manager import (
    CANCEL_PENDING_STATUSES,
    PARTIAL_FILL_STATUSES,
    TERMINAL_ORDER_STATUSES,
    WORKING_ORDER_STATUSES,
    walk_orders,
)


def _order_symbols(order: dict[str, Any]) -> list[str]:
    symbols: list[str] = []
    for leg in order.get("orderLegCollection") or []:
        symbol = (leg.get("instrument") or {}).get("symbol")
        if symbol:
            symbols.append(str(symbol))
    for child in order.get("childOrderStrategies") or []:
        symbols.extend(_order_symbols(child))
    return symbols


def _status_category(status: Any) -> str:
    if not status:
        return "missing"
    status = str(status)
    if status == "FILLED":
        return "filled"
    if status in PARTIAL_FILL_STATUSES:
        return "partial"
    if status in CANCEL_PENDING_STATUSES:
        return "cancel_pending"
    if status in TERMINAL_ORDER_STATUSES:
        return status.lower()
    if status in WORKING_ORDER_STATUSES:
        return "working"
    return "unknown"


def _summarize(order: dict[str, Any], underlying: str = "SPX") -> dict[str, Any]:
    child_statuses = [child.get("status") for child in list(walk_orders(order))[1:]]
    symbol_roots = {symbol.upper().split()[0] for symbol in _order_symbols(order)}
    allowed_roots = {"SPX", "SPXW"} if underlying == "SPX" else {underlying}
    return {
        "status": order.get("status"),
        "status_category": _status_category(order.get("status")),
        "entered_time": order.get("enteredTime"),
        "close_time": order.get("closeTime"),
        "order_strategy_type": order.get("orderStrategyType"),
        "complex_order_strategy_type": order.get("complexOrderStrategyType"),
        "quantity": order.get("quantity"),
        "filled_quantity": order.get("filledQuantity"),
        "remaining_quantity": order.get("remainingQuantity"),
        "symbol_roots": sorted(symbol_roots & allowed_roots),
        "child_statuses": child_statuses,
        "child_status_categories": [_status_category(status) for status in child_statuses],
    }


def _build_payload(
    orders: list[dict[str, Any]], report_date: str, underlying: str = "SPX"
) -> dict[str, Any]:
    underlying = underlying.upper()
    allowed_roots = {"SPX", "SPXW"} if underlying == "SPX" else {underlying}
    orders = [
        order
        for order in orders
        if any(
            symbol.upper().split()[0] in allowed_roots
            for symbol in _order_symbols(order)
        )
    ]
    summaries = [_summarize(order, underlying) for order in orders]
    statuses = [
        status
        for summary in summaries
        for status in [summary["status"], *summary["child_statuses"]]
    ]
    return {
        "date": report_date,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status_counts": dict(
            Counter(str(status) if status else "<missing>" for status in statuses)
        ),
        "status_category_counts": dict(Counter(map(_status_category, statuses))),
        "orders": summaries,
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--underlying", choices=("SPX", "XSP"), default="SPX")
    parser.add_argument("--out-dir", default="reports")
    args = parser.parse_args()

    config = load_config(args.config)
    schwab = SchwabClientWrapper(config.schwab)
    await schwab.initialize()
    try:
        report_date = dt.date.fromisoformat(args.date)
        orders = await schwab.get_orders_for_day(report_date)
    finally:
        await schwab.close()

    payload = _build_payload(orders, args.date, args.underlying)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if args.underlying == "SPX" else f"_{args.underlying.lower()}"
    out_path = out_dir / f"broker_order_statuses{suffix}_{args.date}.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(out_path)


if __name__ == "__main__":
    asyncio.run(main())
