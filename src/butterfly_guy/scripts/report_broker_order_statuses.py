"""Write a read-only report of Schwab order statuses for one day."""

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


def _order_symbols(order: dict[str, Any]) -> list[str]:
    symbols: list[str] = []
    for leg in order.get("orderLegCollection") or []:
        symbol = (leg.get("instrument") or {}).get("symbol")
        if symbol:
            symbols.append(str(symbol))
    for child in order.get("childOrderStrategies") or []:
        symbols.extend(_order_symbols(child))
    return symbols


def _summarize(order: dict[str, Any]) -> dict[str, Any]:
    children = order.get("childOrderStrategies") or []
    return {
        "order_id": order.get("orderId"),
        "status": order.get("status"),
        "entered_time": order.get("enteredTime"),
        "close_time": order.get("closeTime"),
        "order_strategy_type": order.get("orderStrategyType"),
        "complex_order_strategy_type": order.get("complexOrderStrategyType"),
        "quantity": order.get("quantity"),
        "filled_quantity": order.get("filledQuantity"),
        "remaining_quantity": order.get("remainingQuantity"),
        "symbols": _order_symbols(order),
        "child_statuses": [child.get("status") for child in children],
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--date", default=dt.date.today().isoformat())
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

    summaries = [_summarize(order) for order in orders]
    payload = {
        "date": args.date,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status_counts": dict(Counter(s["status"] for s in summaries)),
        "orders": summaries,
        "raw_orders": orders,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"broker_order_statuses_{args.date}.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(out_path)


if __name__ == "__main__":
    asyncio.run(main())
