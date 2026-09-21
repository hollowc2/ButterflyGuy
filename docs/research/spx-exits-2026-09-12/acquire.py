"""Run over stdin inside the SPX container; SELECT-only, sanitized export."""

import asyncio
import datetime as dt
import hashlib
import json
from pathlib import Path

import asyncpg

import butterfly_guy
from butterfly_guy.core.config import load_config


async def main():
    cfg = load_config("configs/config.yaml")
    root = Path(butterfly_guy.__file__).parent
    sources = {}
    for p in sorted(root.rglob("*.py")):
        sources[str(p.relative_to(root))] = {
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "text": p.read_text(),
        }
    print(
        json.dumps(
            {
                "kind": "baseline",
                "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "package_path": str(root),
                "sources": sources,
                "config_yaml": Path("configs/config.yaml").read_text(),
                "effective": {
                    k: getattr(cfg, k).model_dump(mode="json")
                    for k in [
                        "strategy",
                        "entry",
                        "execution",
                        "profit_management",
                        "risk",
                        "collector",
                    ]
                },
            }
        ),
        flush=True,
    )
    conn = await asyncpg.connect(cfg.database.dsn)
    try:
        async with conn.transaction(readonly=True):
            await conn.execute("SET LOCAL statement_timeout='25s'")
            rows = await conn.fetch("""SELECT id,trade_date,direction,wing_width,
                lower_strike,center_strike,upper_strike,
                entry_price,exit_price,entry_time,exit_time,exit_reason,pnl,peak_value,quantity,status,
                metadata->>'paper_fill_model' AS fill_model,
                metadata->'exit_mark_at_signal' AS exit_mark_at_signal,
                metadata->'exit_mark_parity' AS exit_mark_parity,
                metadata->'exit_ladder_steps' AS exit_ladder_steps
                FROM butterfly_trades WHERE underlying='SPX'
                AND trade_date BETWEEN '2026-03-17' AND '2026-09-11'
                ORDER BY trade_date,entry_time,id""")
            print(
                json.dumps({"kind": "trades", "rows": [dict(r) for r in rows]}, default=str),
                flush=True,
            )
            for r in rows:
                qs = await conn.fetch(
                    """SELECT snapshot_time,strike,option_type,bid,ask,mark,symbol
                    FROM option_chain_snapshots WHERE underlying='SPX' AND expiration=$1
                    AND snapshot_time >= $2 AND snapshot_time < $3
                    AND option_type=$4 AND strike=ANY($5::numeric[])
                    ORDER BY snapshot_time,strike,symbol""",
                    r["trade_date"],
                    r["entry_time"] - dt.timedelta(minutes=2),
                    dt.datetime.combine(
                        r["trade_date"] + dt.timedelta(days=1), dt.time(), tzinfo=dt.timezone.utc
                    ),
                    r["direction"],
                    [r["lower_strike"], r["center_strike"], r["upper_strike"]],
                )
                print(
                    json.dumps(
                        {"kind": "quotes", "trade_id": r["id"], "rows": [dict(q) for q in qs]},
                        default=str,
                    ),
                    flush=True,
                )
    finally:
        await conn.close()


asyncio.run(main())
