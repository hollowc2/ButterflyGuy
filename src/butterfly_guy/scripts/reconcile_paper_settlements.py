"""Re-settle paper cash-settled trades at the official index close.

Paper trades settle at 16:00 ET on a provisional price (Schwab's final regular-session
1-minute close, or a fallback), because the official close only reaches ``daily_bars``
when the next session's collector runs. The two can differ by a few index points. This
script values each provisional paper settlement at the official ``daily_bars`` close,
keeping the original values under ``metadata.settlement_correction``.

Live broker settlements (``schwab_expiration_transactions``) are never touched.

Usage (dry run by default):
    uv run python src/butterfly_guy/scripts/reconcile_paper_settlements.py
    uv run python src/butterfly_guy/scripts/reconcile_paper_settlements.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
from types import SimpleNamespace
from typing import Any

import asyncpg

from butterfly_guy.core.config import load_config
from butterfly_guy.position.position_manager import fly_settlement_value

OFFICIAL_SOURCE = "official_daily_close"
PROVISIONAL_SOURCES = (
    "market_data_final_regular_session_1m_close",
    "schwab_final_regular_session_1m_close",
    "market_data_spot_quote_fallback",
    "option_chain_mark_fallback",
)


def official_settlement(trade: dict[str, Any], official_close: float) -> dict[str, Any] | None:
    """Return the corrected exit fields for *trade*, or None if nothing changes."""
    metadata = trade["metadata"]
    fly = SimpleNamespace(
        direction=trade["direction"],
        lower_strike=float(trade["lower_strike"]),
        center_strike=float(trade["center_strike"]),
        upper_strike=float(trade["upper_strike"]),
    )
    exit_price = fly_settlement_value(fly, official_close)
    pnl = round(exit_price - float(trade["entry_price"]), 4)
    if exit_price == float(trade["exit_price"]) and pnl == float(trade["pnl"]):
        return None
    return {
        "exit_price": exit_price,
        "pnl": pnl,
        "metadata": {
            "settlement_source": OFFICIAL_SOURCE,
            "settlement_spot": official_close,
            "exit_mark_at_signal": exit_price,
            "settlement_correction": {
                "reason": "provisional_paper_settlement_replaced_by_official_close",
                "corrected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "original_exit_price": float(trade["exit_price"]),
                "original_pnl": float(trade["pnl"]),
                "original_settlement_source": metadata.get("settlement_source"),
                "original_settlement_spot": metadata.get("settlement_spot"),
                "original_settlement_spot_time": metadata.get("settlement_spot_time"),
            },
        },
    }


async def reconcile(conn: asyncpg.Connection, *, apply: bool) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT t.id, t.underlying, t.trade_date, t.direction, t.lower_strike,
               t.center_strike, t.upper_strike, t.entry_price, t.exit_price, t.pnl,
               t.metadata, b.close AS official_close
        FROM butterfly_trades t
        JOIN daily_bars b ON b.underlying = t.underlying AND b.date = t.trade_date
        WHERE t.status = 'CLOSED'
          AND t.exit_reason = 'cash_settled'
          AND t.metadata->>'settlement_source' = ANY($1::text[])
        ORDER BY t.trade_date, t.id
        """,
        list(PROVISIONAL_SOURCES),
    )
    changes = []
    for row in rows:
        trade = dict(row)
        if isinstance(trade["metadata"], str):
            trade["metadata"] = json.loads(trade["metadata"])
        change = official_settlement(trade, float(row["official_close"]))
        if change is None:
            continue
        changes.append({"trade": trade, **change})
        if apply:
            await conn.execute(
                """
                UPDATE butterfly_trades
                SET exit_price = $2, pnl = $3, metadata = metadata || $4::jsonb
                WHERE id = $1 AND status = 'CLOSED'
                  AND metadata->>'settlement_source' = ANY($5::text[])
                """,
                row["id"], change["exit_price"], change["pnl"],
                json.dumps(change["metadata"]), list(PROVISIONAL_SOURCES),
            )
    return changes


async def _run(apply: bool) -> None:
    conn = await asyncpg.connect(load_config().database.dsn)
    try:
        changes = await reconcile(conn, apply=apply)
    finally:
        await conn.close()
    total = 0.0
    for change in changes:
        trade = change["trade"]
        delta = (change["pnl"] - float(trade["pnl"])) * 100
        total += delta
        print(
            f"{trade['id']:>5} {trade['underlying']:<4} {trade['trade_date']}  "
            f"spot {trade['metadata'].get('settlement_spot')} -> "
            f"{change['metadata']['settlement_spot']:.2f}  "
            f"exit {float(trade['exit_price']):.4f} -> {change['exit_price']:.4f}  "
            f"P&L {delta:+.2f} $/ct"
        )
    verb = "Corrected" if apply else "Would correct (dry run; pass --apply)"
    print(f"{verb}: {len(changes)} trade(s), total P&L change {total:+.2f} $/ct")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--apply", action="store_true", help="write corrections to the DB")
    asyncio.run(_run(p.parse_args().apply))


if __name__ == "__main__":
    main()
