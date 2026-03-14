"""Option chain collector — fetches and stores SPX chain snapshots."""

from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import (
    chain_snapshot_duration,
    chain_snapshot_rows,
    chain_snapshots_total,
)
from butterfly_guy.core.time_utils import (
    get_0dte_expiration,
    is_market_open,
    now_eastern,
)
from butterfly_guy.backtest.chain_cache import save_snapshot
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.db.queries import ChainQueries, SpotQueries

log = get_logger(__name__)


class OptionChainCollector:
    """Collects option chain snapshots at regular intervals."""

    def __init__(
        self,
        config: AppConfig,
        schwab: SchwabClientWrapper,
        chain_queries: ChainQueries,
        spot_queries: SpotQueries,
    ) -> None:
        self.config = config
        self.schwab = schwab
        self.chain_queries = chain_queries
        self.spot_queries = spot_queries

    def _parse_chain_response(
        self,
        data: dict[str, Any],
        snapshot_time: dt.datetime,
        expiration: dt.date,
        spot_price: float,
    ) -> list[dict[str, Any]]:
        """Parse Schwab callExpDateMap/putExpDateMap into flat rows."""
        rows: list[dict[str, Any]] = []
        underlying = self.config.strategy.underlying

        for option_type, map_key in [("CALL", "callExpDateMap"), ("PUT", "putExpDateMap")]:
            exp_map = data.get(map_key, {})
            for exp_key, strikes in exp_map.items():
                # exp_key format: "2026-03-10:0"
                if str(expiration) not in exp_key:
                    continue
                for strike_str, options in strikes.items():
                    for opt in options:
                        rows.append({
                            "snapshot_time": snapshot_time,
                            "underlying": underlying,
                            "expiration": expiration,
                            "strike": float(strike_str),
                            "option_type": option_type,
                            "bid": opt.get("bid"),
                            "ask": opt.get("ask"),
                            "mark": opt.get("mark"),
                            "last": opt.get("last"),
                            "volume": opt.get("totalVolume", 0),
                            "open_interest": opt.get("openInterest", 0),
                            "iv": opt.get("volatility"),
                            "delta": opt.get("delta"),
                            "gamma": opt.get("gamma"),
                            "theta": opt.get("theta"),
                            "vega": opt.get("vega"),
                            "symbol": opt.get("symbol"),
                            "spot_price": spot_price,
                        })
        return rows

    async def collect_snapshot(self) -> int:
        """Fetch current chain and store snapshot. Returns row count."""
        snapshot_time = now_eastern()
        expiration = get_0dte_expiration()

        with chain_snapshot_duration.time():
            # Get spot price
            spot_price = await self.schwab.get_spot_price()
            await self.spot_queries.insert(
                self.config.strategy.underlying, spot_price, snapshot_time
            )

            # Get VIX spot price
            try:
                vix_price = await self.schwab.get_spot_price("$VIX")
                await self.spot_queries.insert("$VIX", vix_price, snapshot_time)
                log.info("vix_snapshot_collected", vix=vix_price)
            except Exception as e:
                log.warning("vix_fetch_failed", error=str(e))

            # Get chain
            chain_data = await self.schwab.get_spx_option_chain(expiration)
            rows = self._parse_chain_response(chain_data, snapshot_time, expiration, spot_price)

            if rows:
                count = await self.chain_queries.bulk_insert_snapshot(rows)
                chain_snapshots_total.inc()
                chain_snapshot_rows.set(count)
                save_snapshot(expiration, snapshot_time, spot_price, rows)
                log.info("snapshot_collected", rows=count, spot=spot_price)
                return count

            log.warning("snapshot_empty", expiration=str(expiration))
            return 0

    async def run_loop(self) -> None:
        """Main collector loop — runs while market is open."""
        interval = self.config.collector.snapshot_interval_seconds
        log.info("collector_starting", interval=interval)

        while True:
            if not is_market_open():
                log.info("market_closed_waiting")
                await asyncio.sleep(30)
                continue

            try:
                await self.collect_snapshot()
            except Exception as e:
                log.error("snapshot_failed", error=str(e))

            await asyncio.sleep(interval)
