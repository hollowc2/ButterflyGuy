"""Deploy gate: fail unless Schwab shows no positions or active orders for any asset.

Run inside the SPX app container, which has the Schwab config and token mounted:

    docker exec -i butterfly_spx_app python - < tools/deploy_broker_flat_check.py

Read-only: it lists the last 59 days of orders and the account snapshot. Moved
verbatim from the retired deploy.yml "Check runtime is flat" step.

`python - --ignore-expired` (SPX live close-out and stop only) skips option positions that
have already expired: Schwab lists a cash-settled 0DTE leg until its overnight posting.
Active orders still fail, and so does any unexpired or unparseable position.
"""
import asyncio
import datetime as dt
import re
import sys

from butterfly_guy.core.config import load_config
from butterfly_guy.core.time_utils import market_close_time, now_eastern, session_date
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.execution.order_manager import (
    CANCEL_PENDING_STATUSES,
    PARTIAL_FILL_STATUSES,
    TERMINAL_ORDER_STATUSES,
    WORKING_ORDER_STATUSES,
    order_statuses,
    walk_orders,
)
from butterfly_guy.scripts.run_live import (
    _broker_option_positions,
    _matches_underlying,
    _order_symbols,
)

OCC_EXPIRY = re.compile(r"(\d{2})(\d{2})(\d{2})[CP]\d{8}$")


def expired(symbol: str, now: dt.datetime) -> bool:
    """True once an option's expiration session has closed (OCC symbol, Eastern time)."""
    match = OCC_EXPIRY.search(symbol.replace(" ", ""))
    if match is None:
        return False
    yy, mm, dd = (int(part) for part in match.groups())
    expiry = dt.date(2000 + yy, mm, dd)
    return expiry < now.date() or (
        expiry == now.date() and now.time() >= market_close_time(expiry)
    )


async def check() -> None:
    ignore_expired = "--ignore-expired" in sys.argv[1:]
    schwab = SchwabClientWrapper(load_config("configs/config.yaml").schwab)
    await schwab.initialize()
    try:
        today = session_date()
        response = await schwab._retry(
            schwab.client.get_orders_for_account,
            schwab.account_hash,
            from_entered_datetime=dt.datetime.combine(
                today - dt.timedelta(days=59), dt.time.min
            ),
            to_entered_datetime=dt.datetime.combine(today, dt.time.max),
            endpoint="deployment_order_gate",
        )
        broker_orders = response.json()
        if not isinstance(broker_orders, list):
            raise RuntimeError("Schwab order history response is not a list")
        snapshot = await schwab.get_account_snapshot()
        known_statuses = (
            WORKING_ORDER_STATUSES
            | PARTIAL_FILL_STATUSES
            | CANCEL_PENDING_STATUSES
            | TERMINAL_ORDER_STATUSES
            # Historical replacements are terminal for this read-only audit.
            # Keep execution status handling unchanged; replacement orders are
            # independently checked for active/unknown states below.
            | {"REPLACED"}
        )
        active_statuses = (
            WORKING_ORDER_STATUSES
            | PARTIAL_FILL_STATUSES
            | CANCEL_PENDING_STATUSES
        )
        for underlying in ("SPX", "NDX", "XSP"):
            positions = _broker_option_positions(snapshot, underlying)
            if ignore_expired:
                now = now_eastern()
                skipped = sorted(symbol for symbol in positions if expired(symbol, now))
                if skipped:
                    print(f"ignoring {len(skipped)} expired {underlying} leg(s): {skipped}")
                positions = {s: q for s, q in positions.items() if s not in skipped}
            if positions:
                raise RuntimeError(
                    f"Broker has {len(positions)} {underlying} option "
                    "position(s) while the DB is flat"
                )
            relevant = [
                order
                for order in broker_orders
                if any(
                    _matches_underlying(symbol, underlying)
                    for symbol in _order_symbols(order)
                )
            ]
            if any(
                not node.get("status")
                for order in relevant
                for node in walk_orders(order)
            ):
                raise RuntimeError(
                    f"Broker has missing {underlying} order status"
                )
            statuses = set().union(
                *(order_statuses(order) for order in relevant)
            )
            unknown = statuses - known_statuses
            if unknown:
                raise RuntimeError(
                    f"Broker has unmapped {underlying} order status(es)"
                )
            if statuses & active_statuses:
                raise RuntimeError(
                    f"Broker has active {underlying} order(s)"
                )
    finally:
        await schwab.close()


asyncio.run(check())
