"""Generate entry + EOD charts from a historic trade and post to Discord."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import os

from dotenv import dotenv_values

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.reports.live_performance import trade_pnl_dollars
from butterfly_guy.services.chart_data import load_spot_series
from butterfly_guy.services.notifier import DiscordNotifier
from butterfly_guy.services.trade_chart import (
    ButterflyChartSpec,
    build_entry_chart_png,
    summarize_exit_chart,
)

log = get_logger(__name__)


async def _load_trade(db: DatabasePool, trade_id: int | None) -> dict | None:
    if trade_id is not None:
        row = await db.pool.fetchrow(
            "SELECT * FROM butterfly_trades WHERE id = $1",
            trade_id,
        )
        return dict(row) if row else None

    row = await db.pool.fetchrow(
        """
        SELECT * FROM butterfly_trades
        WHERE status = 'CLOSED' AND entry_time IS NOT NULL
        ORDER BY entry_time DESC
        LIMIT 1
        """
    )
    return dict(row) if row else None


async def main() -> None:
    parser = argparse.ArgumentParser(description="Send historic trade charts to Discord")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument(
        "--trade-id", type=int, default=None, help="Trade ID (default: latest closed)"
    )
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)

    webhook = os.environ.get("DISCORD_WEBHOOK_URL") or dotenv_values(".env").get(
        "DISCORD_WEBHOOK_URL", ""
    )
    if not webhook:
        raise SystemExit("DISCORD_WEBHOOK_URL not configured")

    db = DatabasePool(config.database.dsn)
    await db.initialize()
    try:
        trade = await _load_trade(db, args.trade_id)
        if trade is None:
            raise SystemExit("No suitable historic trade found in database")

        entry_time = trade["entry_time"]
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=dt.timezone.utc)

        session_date = trade["trade_date"]
        if isinstance(session_date, dt.datetime):
            session_date = session_date.date()

        underlying = trade["underlying"]
        candles = await load_spot_series(db, underlying, session_date)
        if len(candles) < 10:
            raise SystemExit(
                f"Insufficient spot_prices for {underlying} on {session_date} ({len(candles)} rows)"
            )

        metadata = trade.get("metadata") or {}
        if isinstance(metadata, str):
            import json
            metadata = json.loads(metadata)
        entry_spot = metadata.get("entry_spot")

        spec = ButterflyChartSpec(
            underlying=underlying,
            direction=trade["direction"],
            lower_strike=float(trade["lower_strike"]),
            center_strike=float(trade["center_strike"]),
            upper_strike=float(trade["upper_strike"]),
            wing_width=int(trade["wing_width"]),
            entry_price=float(trade["entry_price"]),
            entry_time=entry_time,
            entry_spot=float(entry_spot) if entry_spot is not None else None,
            exit_time=trade.get("exit_time"),
            exit_reason=trade.get("exit_reason"),
        )

        entry_png = build_entry_chart_png(
            spec,
            candles,
            start_time=config.entry.start_time,
            timezone=config.entry.timezone,
        )
        exit_png, tent_hit = summarize_exit_chart(spec, candles, full_session=True)

        notifier = DiscordNotifier(webhook)
        tent_label = "HIT" if tent_hit else "MISSED" if tent_hit is not None else "N/A"
        pnl_dollars = trade_pnl_dollars(
            float(trade.get("pnl") or 0), int(trade.get("quantity") or 1)
        )
        header = (
            f"🧪 **TEST CHART** — historic trade #{trade['id']} ({session_date})\n"
            f"> {underlying} {trade['direction']} {trade['wing_width']}-wide | "
            f"P&L ${pnl_dollars:.2f} | Tent: {tent_label}"
        )

        if entry_png:
            await notifier._post(
                header + "\n> **Entry window chart**",
                image_png=entry_png,
                image_name="test_entry.png",
            )
            log.info("test_entry_chart_sent", trade_id=trade["id"], bytes=len(entry_png))
        else:
            log.warning("test_entry_chart_skipped", trade_id=trade["id"])

        if exit_png:
            await notifier._post("> **EOD chart**", image_png=exit_png, image_name="test_eod.png")
            log.info("test_eod_chart_sent", trade_id=trade["id"], bytes=len(exit_png))
        else:
            log.warning("test_eod_chart_skipped", trade_id=trade["id"])

        print(f"Sent test charts for trade #{trade['id']} ({underlying} {session_date})")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
