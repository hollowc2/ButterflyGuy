"""Read-only, redacted SPX pilot evidence export. Never submits or cancels orders."""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
from pathlib import Path

import asyncpg

from butterfly_guy.core.config import load_config
from butterfly_guy.data.schwab_client import SchwabClientWrapper


def redact(value):
    if isinstance(value, dict):
        return {
            key: redact(item) for key, item in value.items()
            if not any(word in key.lower() for word in (
                "account", "token", "secret", "orderid", "broker_order_id",
                "activityid", "executionid", "positionid", "destination", "deliverables",
            ))
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


async def export(day: dt.date, output: Path, config_path: str) -> None:
    config = load_config(config_path)
    broker = SchwabClientWrapper(config.schwab)
    await broker.initialize()
    try:
        orders = await broker.get_orders_for_day(day)
        orders = [o for o in orders if any(
            leg.get("instrument", {}).get("symbol", "").split()[0] in {"SPX", "SPXW"}
            for leg in o.get("orderLegCollection", [])
            if leg.get("instrument", {}).get("symbol", "").split()
        )]
        symbols = {
            leg["instrument"]["symbol"] for order in orders
            for leg in order.get("orderLegCollection", [])
        }
        transactions = await broker.get_transactions_for_day(day)
        transactions = [t for t in transactions if any(
            item.get("instrument", {}).get("symbol") in symbols
            for item in t.get("transferItems", [])
        )]
    finally:
        await broker.close()
    db = await asyncpg.connect(config.database.dsn)
    try:
        async with db.transaction(readonly=True):
            trades = await db.fetch(
                "SELECT * FROM butterfly_trades WHERE underlying='SPX' AND trade_date=$1", day
            )
            intents = await db.fetch(
                "SELECT * FROM broker_order_intents WHERE underlying='SPX' AND trade_date=$1", day
            )
    finally:
        await db.close()
    def decode(record):
        row = dict(record)
        for key in ("metadata", "candidate_snapshot", "order_spec", "raw_broker_payload"):
            if isinstance(row.get(key), str):
                row[key] = json.loads(row[key])
        return row
    evidence = redact({
        "session": day.isoformat(), "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": "Schwab orders/transactions; ButterflyGuy TimescaleDB",
        "orders": orders, "transactions": transactions,
        "trades": [decode(r) for r in trades], "intents": [decode(r) for r in intents],
        "limitations": [
            "Quotes at fill detection are after execution, not exchange execution-time NBBO.",
            "Expiration cash flows may post next day; export again after settlement.",
            "Account-wide manual trades are included when they share the pilot session and SPX root.",
        ],
    })
    # Refuse to overwrite prior evidence.
    output.mkdir(parents=True, exist_ok=False)
    path = output / "evidence.redacted.json"
    path.write_text(json.dumps(evidence, indent=2, default=str) + "\n")
    (output / "manifest.json").write_text(json.dumps({
        "session": str(day), "retrieved_at": evidence["retrieved_at"],
        "files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()},
        "counts": {k: len(evidence[k]) for k in ("orders", "transactions", "trades", "intents")},
    }, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()
    asyncio.run(export(args.date, args.out_dir, args.config))
