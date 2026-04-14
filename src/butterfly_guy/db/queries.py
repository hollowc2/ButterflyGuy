"""Database query helpers for all tables."""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

from butterfly_guy.db.connection import DatabasePool


class ChainQueries:
    """Queries for option_chain_snapshots table."""

    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def bulk_insert_snapshot(self, rows: list[dict[str, Any]]) -> int:
        """Bulk insert option chain snapshot rows using COPY."""
        if not rows:
            return 0

        columns = [
            "snapshot_time", "underlying", "expiration", "strike", "option_type",
            "bid", "ask", "mark", "last", "volume", "open_interest",
            "iv", "delta", "gamma", "theta", "vega", "symbol", "spot_price",
            "bid_size", "ask_size", "rho", "intrinsic_value", "time_value",
            "in_the_money", "days_to_expiration", "multiplier", "theoretical_value",
        ]

        records = [
            tuple(row.get(col) for col in columns) for row in rows
        ]

        async with self.db.pool.acquire() as conn:
            await conn.copy_records_to_table(
                "option_chain_snapshots",
                records=records,
                columns=columns,
            )
        return len(records)

    async def get_latest_chain(
        self, underlying: str, expiration: dt.date
    ) -> list[dict]:
        rows = await self.db.fetch(
            """
            SELECT * FROM option_chain_snapshots
            WHERE underlying = $1 AND expiration = $2
              AND snapshot_time = (
                SELECT MAX(snapshot_time) FROM option_chain_snapshots
                WHERE underlying = $1 AND expiration = $2
              )
            ORDER BY strike, option_type
            """,
            underlying, expiration,
        )
        return [dict(r) for r in rows]

    async def get_chain_at_time(
        self, underlying: str, expiration: dt.date, at: dt.datetime
    ) -> list[dict]:
        rows = await self.db.fetch(
            """
            SELECT * FROM option_chain_snapshots
            WHERE underlying = $1 AND expiration = $2
              AND snapshot_time <= $3
            ORDER BY snapshot_time DESC, strike, option_type
            LIMIT 2000
            """,
            underlying, expiration, at,
        )
        return [dict(r) for r in rows]


class SpotQueries:
    """Queries for spot_prices table."""

    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def insert(self, underlying: str, price: float, ts: dt.datetime | None = None) -> None:
        ts = ts or dt.datetime.now(dt.timezone.utc)
        await self.db.execute(
            "INSERT INTO spot_prices (ts, underlying, price) VALUES ($1, $2, $3)",
            ts, underlying, price,
        )

    async def get_latest(self, underlying: str) -> float | None:
        return await self.db.fetchval(
            "SELECT price FROM spot_prices WHERE underlying = $1 ORDER BY ts DESC LIMIT 1",
            underlying,
        )


class TradeQueries:
    """Queries for trades table."""

    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def insert_trade(self, trade: dict[str, Any]) -> int:
        return await self.db.fetchval(
            """
            INSERT INTO butterfly_trades (
                underlying, trade_date, direction, wing_width, center_strike,
                lower_strike, upper_strike, entry_price, entry_time,
                lower_symbol, center_symbol, upper_symbol, quantity, status, metadata
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
            RETURNING id
            """,
            trade["underlying"],
            trade["trade_date"], trade["direction"], trade["wing_width"],
            trade["center_strike"], trade["lower_strike"], trade["upper_strike"],
            trade["entry_price"], trade["entry_time"],
            trade.get("lower_symbol"), trade.get("center_symbol"),
            trade.get("upper_symbol"), trade.get("quantity", 1),
            "OPEN", json.dumps(trade.get("metadata", {})),
        )

    async def close_trade(
        self, trade_id: int, exit_price: float, exit_time: dt.datetime,
        exit_reason: str, pnl: float, peak_value: float
    ) -> None:
        await self.db.execute(
            """
            UPDATE butterfly_trades SET
                exit_price = $2, exit_time = $3, exit_reason = $4,
                pnl = $5, peak_value = $6, status = 'CLOSED'
            WHERE id = $1
            """,
            trade_id, exit_price, exit_time, exit_reason, pnl, peak_value,
        )

    async def get_open_trades(self, underlying: str) -> list[dict]:
        rows = await self.db.fetch(
            "SELECT * FROM butterfly_trades WHERE status = 'OPEN' AND underlying = $1 ORDER BY entry_time",
            underlying,
        )
        return [dict(r) for r in rows]

    async def get_trades_for_date(self, trade_date: dt.date, underlying: str) -> list[dict]:
        rows = await self.db.fetch(
            "SELECT * FROM butterfly_trades WHERE trade_date = $1 AND underlying = $2 ORDER BY entry_time",
            trade_date, underlying,
        )
        return [dict(r) for r in rows]


class RiskQueries:
    """Queries for daily_risk_state table."""

    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def get_or_create(self, trade_date: dt.date, underlying: str) -> dict:
        row = await self.db.fetchrow(
            "SELECT * FROM daily_risk_state WHERE trade_date = $1 AND underlying = $2",
            trade_date, underlying,
        )
        if row:
            return dict(row)
        await self.db.execute(
            "INSERT INTO daily_risk_state (trade_date, underlying) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            trade_date, underlying,
        )
        row = await self.db.fetchrow(
            "SELECT * FROM daily_risk_state WHERE trade_date = $1 AND underlying = $2",
            trade_date, underlying,
        )
        return dict(row)

    async def increment_trade_count(self, trade_date: dt.date, underlying: str) -> None:
        await self.db.execute(
            """
            UPDATE daily_risk_state
            SET trade_count = trade_count + 1
            WHERE trade_date = $1 AND underlying = $2
            """,
            trade_date, underlying,
        )

    async def update_pnl(self, trade_date: dt.date, pnl_delta: float, underlying: str) -> None:
        await self.db.execute(
            """
            UPDATE daily_risk_state
            SET realized_pnl = realized_pnl + $2
            WHERE trade_date = $1 AND underlying = $3
            """,
            trade_date, pnl_delta, underlying,
        )

    async def set_halted(self, trade_date: dt.date, underlying: str) -> None:
        await self.db.execute(
            "UPDATE daily_risk_state SET halted = TRUE, max_loss_hit = TRUE WHERE trade_date = $1 AND underlying = $2",
            trade_date, underlying,
        )

    async def get_weekly_pnl(self, underlying: str) -> float:
        """Sum of realized PnL for the rolling 7-day window (closed trades only)."""
        val = await self.db.pool.fetchval(
            """
            SELECT COALESCE(SUM(pnl), 0)
            FROM butterfly_trades
            WHERE underlying = $1
              AND trade_date >= CURRENT_DATE - INTERVAL '7 days'
              AND status = 'CLOSED'
            """,
            underlying,
        )
        return float(val)

    async def get_recent_closed_pnls(self, underlying: str, n: int) -> list[float]:
        """PnL of the last N closed trades (most recent first), for consecutive loss detection."""
        rows = await self.db.fetch(
            """
            SELECT pnl FROM butterfly_trades
            WHERE underlying = $1 AND status = 'CLOSED' AND pnl IS NOT NULL
            ORDER BY exit_time DESC
            LIMIT $2
            """,
            underlying, n,
        )
        return [float(r["pnl"]) for r in rows]


class DecisionQueries:
    """Queries for decision_log table."""

    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def log_event(self, event_type: str, data: dict[str, Any], underlying: str | None = None) -> None:
        await self.db.execute(
            "INSERT INTO decision_log (event_type, data, underlying) VALUES ($1, $2::jsonb, $3)",
            event_type, json.dumps(data), underlying,
        )


class DailyBarQueries:
    """Queries for daily_bars table."""

    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def bulk_upsert(self, rows: list[dict[str, Any]]) -> int:
        """Upsert daily OHLCV rows. Updates close/open/high/low/volume on conflict."""
        if not rows:
            return 0
        records = [
            (row["date"], row["underlying"], row.get("open"), row.get("high"),
             row.get("low"), row["close"], row.get("volume", 0))
            for row in rows
        ]
        await self.db.pool.executemany(
            """
            INSERT INTO daily_bars (date, underlying, open, high, low, close, volume)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (date, underlying) DO UPDATE SET
                open   = EXCLUDED.open,
                high   = EXCLUDED.high,
                low    = EXCLUDED.low,
                close  = EXCLUDED.close,
                volume = EXCLUDED.volume
            """,
            records,
        )
        return len(rows)

    async def get_recent_closes(self, underlying: str, days: int) -> list[float]:
        """Return the last `days` daily closes in chronological order (oldest first)."""
        rows = await self.db.fetch(
            """
            SELECT close FROM daily_bars
            WHERE underlying = $1
            ORDER BY date DESC
            LIMIT $2
            """,
            underlying, days,
        )
        return [float(r["close"]) for r in reversed(rows)]


class TentQueries:
    """Queries for tent_boundaries table."""

    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def insert(
        self,
        ts: dt.datetime,
        underlying: str,
        lower_tent: float | None,
        upper_tent: float | None,
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO tent_boundaries (ts, underlying, lower_tent, upper_tent)
            VALUES ($1, $2, $3, $4)
            """,
            ts, underlying, lower_tent, upper_tent,
        )


class CandidateQueries:
    """Queries for butterfly_candidates table."""

    def __init__(self, db: DatabasePool) -> None:
        self.db = db

    async def bulk_insert(self, candidates: list[dict[str, Any]]) -> int:
        if not candidates:
            return 0
        columns = [
            "scan_time", "underlying", "direction", "wing_width", "center_strike",
            "lower_strike", "upper_strike", "cost", "max_profit",
            "reward_risk", "lower_be", "upper_be", "distance_from_spot",
            "spot_price", "selected",
        ]
        records = [tuple(c.get(col) for col in columns) for c in candidates]
        async with self.db.pool.acquire() as conn:
            await conn.copy_records_to_table(
                "butterfly_candidates", records=records, columns=columns,
            )
        return len(records)
