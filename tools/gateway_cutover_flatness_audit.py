#!/usr/bin/env python3
"""Run a redacted, read-only ButterflyGuy cutover flatness audit."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
from collections import Counter
from typing import Any

from butterfly_guy.core.config import load_config
from butterfly_guy.core.time_utils import session_date
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.execution.order_manager import (
    CANCEL_PENDING_STATUSES,
    PARTIAL_FILL_STATUSES,
    TERMINAL_ORDER_STATUSES,
    WORKING_ORDER_STATUSES,
    walk_orders,
)
from butterfly_guy.scripts.run_live import (
    _broker_option_positions,
    _matches_underlying,
    _order_symbols,
)

UNDERLYINGS = ("SPX", "NDX", "XSP")
AUDIT_TERMINAL_STATUSES = TERMINAL_ORDER_STATUSES | {"REPLACED"}
ACTIVE_STATUSES = (
    WORKING_ORDER_STATUSES | PARTIAL_FILL_STATUSES | CANCEL_PENDING_STATUSES
)


def _redacted_order_audit(
    orders: list[dict[str, Any]], underlying: str
) -> dict[str, Any]:
    relevant = [
        order
        for order in orders
        if any(_matches_underlying(symbol, underlying) for symbol in _order_symbols(order))
    ]
    nodes = [node for order in relevant for node in walk_orders(order)]
    statuses = [str(node["status"]) for node in nodes if node.get("status")]
    missing_status_nodes = sum(not node.get("status") for node in nodes)
    unknown_statuses = sorted(
        set(statuses) - ACTIVE_STATUSES - AUDIT_TERMINAL_STATUSES
    )
    order_ids = [
        str(node.get("orderId") or node.get("order_id"))
        for node in nodes
        if node.get("orderId") or node.get("order_id")
    ]
    duplicate_order_ids = sum(count - 1 for count in Counter(order_ids).values() if count > 1)
    return {
        "top_level_orders": len(relevant),
        "order_nodes": len(nodes),
        "active_order_nodes": sum(status in ACTIVE_STATUSES for status in statuses),
        "missing_status_nodes": missing_status_nodes,
        "unmapped_statuses": unknown_statuses,
        "replaced_terminal_nodes": statuses.count("REPLACED"),
        "duplicate_order_ids": duplicate_order_ids,
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--date", type=dt.date.fromisoformat)
    args = parser.parse_args()

    config = load_config(args.config)
    day = args.date or session_date()
    db = DatabasePool(config.database.dsn, min_size=1, max_size=1)
    schwab = SchwabClientWrapper(config.schwab)
    await db.initialize()
    await schwab.initialize()
    try:
        open_trades = await db.pool.fetchval(
            "SELECT count(*) FROM butterfly_trades WHERE status = 'OPEN'"
        )
        nonterminal_intents = await db.pool.fetchval(
            """
            SELECT count(*) FROM broker_order_intents
            WHERE status IS NULL
               OR status NOT IN ('FILLED', 'CANCELED', 'REJECTED', 'EXPIRED')
            """
        )
        account = await schwab.get_account_snapshot()
        orders = await schwab.get_orders_for_day(day)
    finally:
        await schwab.close()
        await db.close()

    broker_positions = {
        underlying: len(_broker_option_positions(account, underlying))
        for underlying in UNDERLYINGS
    }
    order_audit = {
        underlying: _redacted_order_audit(orders, underlying)
        for underlying in UNDERLYINGS
    }
    flat = (
        open_trades == 0
        and nonterminal_intents == 0
        and not any(broker_positions.values())
        and all(
            result["active_order_nodes"] == 0
            and result["missing_status_nodes"] == 0
            and not result["unmapped_statuses"]
            and result["duplicate_order_ids"] == 0
            for result in order_audit.values()
        )
    )
    print(
        json.dumps(
            {
                "date": day.isoformat(),
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "database_open_trades": open_trades,
                "database_nonterminal_intents": nonterminal_intents,
                "broker_option_position_counts": broker_positions,
                "orders": order_audit,
                "flat": flat,
            },
            sort_keys=True,
        )
    )
    return 0 if flat else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
