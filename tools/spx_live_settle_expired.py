"""Close an expired live SPX fly's OPEN DB row after the bot stopped managing it.

Reviewed replacement for the 2026-11-19 scratchpad script `settle_100000.py` (live trade
100000: the bot halted at 07:20 PT and the fly expired worthless). Read-only unless
--apply. Run it inside the live container, which has the DB, config and token mounts:

    docker exec -i butterfly_spx_live_app python - --trade-id 100000 \
        < $REL/tools/spx_live_settle_expired.py            # dry run: prints the plan
    docker exec -i butterfly_spx_live_app python - --trade-id 100000 --apply \
        < $REL/tools/spx_live_settle_expired.py

It refuses unless the trade is OPEN, its session closed at least two minutes ago, and one of:
  1. Schwab has posted the expiration transactions: the settlement is computed exactly as the
     bot computes it (broker_cash_settlement_from_transactions).
  2. Schwab has not posted them yet, but SPX closed at least OTM_MARGIN points beyond the
     fly's strikes, so every leg expires worthless, and Schwab's opening transactions match
     the three legs. Net P&L is then the opening net amount (fees included).
Anything else (SPX near or inside the strikes, mismatched legs) waits for Schwab's posting.
On --apply it closes the row as cash_settled and adds the net P&L to daily_risk_state, as
the bot's own close would.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import sys
from typing import Any
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
OTM_MARGIN = 20.0  # SPX points between the close and the nearest strike


class SettleRefusedError(RuntimeError):
    pass


def _opening_net(row: dict[str, Any], transactions: list[dict[str, Any]]) -> tuple[float, list]:
    """Net cash of the fly's opening transactions; refuse unless they are exactly the fly."""
    qty = float(row["quantity"])
    legs = {row["lower_symbol"]: qty, row["center_symbol"]: -2 * qty, row["upper_symbol"]: qty}
    opening, net, evidence = dict.fromkeys(legs, 0.0), 0.0, []
    for t in transactions:
        items = [i for i in t.get("transferItems") or []
                 if (i.get("instrument") or {}).get("symbol") in legs]
        if not items:
            continue
        if {i.get("positionEffect") for i in items} != {"OPENING"}:
            raise SettleRefusedError(
                f"a non-opening transaction touches the legs ({t.get('activityId')}); "
                "the fly was (partly) closed: settle from Schwab's records by hand"
            )
        net += float(t["netAmount"])
        for i in items:
            opening[i["instrument"]["symbol"]] += float(i["amount"])
        evidence.append({"time": t.get("time"), "net_amount": t["netAmount"],
                         "items": [(i["instrument"]["symbol"], i["amount"], i["price"])
                                   for i in items]})
    if any(abs(opening[s] - q) > 1e-9 for s, q in legs.items()):
        raise SettleRefusedError(f"opening transactions do not match the three legs: {opening}")
    if net >= 0:
        raise SettleRefusedError("opening transactions are not a debit")
    return round(net, 2), evidence


def plan_settlement(
    row: dict[str, Any], transactions: list[dict[str, Any]], spx_close: float | None,
) -> tuple[float, float, dict[str, Any]]:
    """Return (settlement value, pnl per contract, metadata) for close_trade, or refuse."""
    from butterfly_guy.data.schemas import TradeRecord
    from butterfly_guy.services.position_service import broker_cash_settlement_from_transactions

    if row["status"] != "OPEN":
        raise SettleRefusedError(f"trade {row['id']} is {row['status']}, not OPEN")
    qty = int(row["quantity"])
    trade = TradeRecord(
        trade_id=row["id"], trade_date=row["trade_date"], direction=row["direction"],
        lower_strike=float(row["lower_strike"]), center_strike=float(row["center_strike"]),
        upper_strike=float(row["upper_strike"]), entry_price=float(row["entry_price"]),
        lower_symbol=row["lower_symbol"], center_symbol=row["center_symbol"],
        upper_symbol=row["upper_symbol"], quantity=qty,
    )
    posted = broker_cash_settlement_from_transactions(transactions, trade)
    if posted is not None:
        return posted.settlement_value, posted.net_pnl_dollars / (100 * qty), {
            "settlement_source": "schwab_expiration_transactions",
            "settlement_spot": posted.settlement_spot,
            "gross_pnl_dollars": round(
                (posted.settlement_value - trade.entry_price) * 100 * qty, 2
            ),
            "net_pnl_dollars": posted.net_pnl_dollars,
            "entry_net_amount": posted.entry_net_amount,
            "settlement_net_amount": posted.settlement_net_amount,
            "broker_cash_settlement_evidence": posted.evidence,
        }

    if spx_close is None:
        raise SettleRefusedError("no SPX close and no posted settlement; wait for Schwab's posting")
    if trade.direction == "CALL":
        worthless = spx_close <= trade.lower_strike - OTM_MARGIN
    elif trade.direction == "PUT":
        worthless = spx_close >= trade.upper_strike + OTM_MARGIN
    else:
        raise SettleRefusedError(f"unknown direction {trade.direction!r}")
    if not worthless:
        raise SettleRefusedError(
            f"SPX {spx_close} is within {OTM_MARGIN:g} points of (or inside) the strikes; "
            "wait for Schwab's settlement posting"
        )
    net, evidence = _opening_net(row, transactions)
    return 0.0, net / (100 * qty), {
        "settlement_source": "operator_spx_close_all_legs_otm",
        "settlement_spot": spx_close,
        "gross_pnl_dollars": round(-trade.entry_price * 100 * qty, 2),
        "net_pnl_dollars": net,
        "entry_net_amount": net,
        "settlement_net_amount": 0.0,
        "entry_transactions": evidence,
    }


async def main() -> None:
    from butterfly_guy.core.config import load_config
    from butterfly_guy.core.time_utils import market_close_time
    from butterfly_guy.data.schwab_client import SchwabClientWrapper
    from butterfly_guy.db.connection import DatabasePool
    from butterfly_guy.db.queries import RiskQueries, TradeQueries

    parser = argparse.ArgumentParser()
    parser.add_argument("--trade-id", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    cfg = load_config("configs/config.yaml")
    db = DatabasePool(cfg.database.dsn)
    await db.initialize()
    schwab = SchwabClientWrapper(cfg.schwab)
    await schwab.initialize()
    try:
        record = await db.pool.fetchrow("SELECT * FROM butterfly_trades WHERE id = $1", args.trade_id)
        if record is None:
            raise SettleRefusedError(f"no trade {args.trade_id}")
        row = dict(record)
        day = row["trade_date"]
        close_et = dt.datetime.combine(day, market_close_time(day), tzinfo=ET)
        if dt.datetime.now(ET) < close_et + dt.timedelta(minutes=2):
            raise SettleRefusedError(f"the {day} session has not closed (+2 min)")
        transactions: list[dict[str, Any]] = []
        d = day
        while d <= dt.datetime.now(ET).date():
            transactions.extend(await schwab.get_transactions_for_day(d))
            d += dt.timedelta(days=1)
        quote = (await schwab._retry(
            schwab.client.get_quotes, ["$SPX"], endpoint="operator_settle"
        )).json()["$SPX"]["quote"]
        # closePrice is the prior close until the session ends; after it, lastPrice is today's.
        spx_close = float(quote.get("lastPrice") or quote.get("closePrice"))
        print("trade", {k: row[k] for k in ("id", "status", "trade_date", "direction",
              "lower_strike", "center_strike", "upper_strike", "entry_price", "quantity")})
        print("SPX", {k: quote.get(k) for k in ("lastPrice", "closePrice", "tradeTime")})

        value, pnl, meta = plan_settlement(row, transactions, spx_close)
        meta = {"exit_ladder_steps": [], "exit_signal_reason": "cash_settled",
                "exit_mark_at_signal": value, "settlement_spot_time": close_et.isoformat(),
                "operator_settlement": "tools/spx_live_settle_expired.py", **meta}
        close_args = (row["id"], value, close_et, "cash_settled", pnl,
                      float(row["peak_value"] or 0))
        print("close_trade", close_args, json.dumps(meta, default=str)[:800])
        if not args.apply:
            print("dry run; pass --apply to write")
            return
        if not await TradeQueries(db).close_trade(*close_args, metadata=meta):
            raise SettleRefusedError("NOT APPLIED: the row is no longer OPEN")
        risk = RiskQueries(db)
        await risk.get_or_create(day, row["underlying"])
        await risk.update_pnl(day, meta["net_pnl_dollars"], row["underlying"])
        print("APPLIED: trade closed and daily_risk_state realized_pnl updated")
    finally:
        await schwab.close()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SettleRefusedError as e:
        sys.exit(f"REFUSED: {e}")
