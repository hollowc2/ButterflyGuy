"""Export recorded monitoring legs, SELECT only; no recorded peaks used."""

import asyncio
import datetime as dt
import json

import asyncpg

from butterfly_guy.core.config import load_config


async def main():
    conn = await asyncpg.connect(load_config("configs/config.yaml").database.dsn)
    try:
        async with conn.transaction(readonly=True):
            await conn.execute("SET LOCAL statement_timeout='25s'")
            trades = await conn.fetch(
                "SELECT id,trade_date FROM butterfly_trades WHERE underlying='SPX' "
                "AND trade_date BETWEEN '2026-03-17' AND '2026-09-11' ORDER BY trade_date,id"
            )
            for t in trades:
                start = dt.datetime.combine(t["trade_date"], dt.time(), tzinfo=dt.timezone.utc)
                rows = await conn.fetch(
                    """SELECT ts AS snapshot_time,strike,option_type,bid,ask,mark,symbol
                    FROM monitoring_leg_quotes WHERE trade_id=$1 AND underlying='SPX'
                    AND ts >= $2 AND ts < $3
                    ORDER BY ts,strike,symbol""",
                    t["id"],
                    start,
                    start + dt.timedelta(days=1),
                )
                print(
                    json.dumps(
                        {"kind": "monitor", "trade_id": t["id"], "rows": [dict(r) for r in rows]},
                        default=str,
                    ),
                    flush=True,
                )
    finally:
        await conn.close()


asyncio.run(main())
