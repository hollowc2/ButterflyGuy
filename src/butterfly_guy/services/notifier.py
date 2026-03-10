"""Discord webhook notifications."""

from __future__ import annotations

import datetime as dt

import aiohttp

from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)


class DiscordNotifier:
    """Sends trading notifications to Discord via webhook."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def _post(self, content: str) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json={"content": content},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status not in (200, 204):
                        log.warning("discord_post_failed", status=resp.status)
        except Exception as e:
            log.error("discord_error", error=str(e))

    async def notify_entry(
        self,
        trade_id: int,
        direction: str,
        center_strike: float,
        wing_width: int,
        entry_price: float,
        spot: float,
    ) -> None:
        emoji = "🦋"
        msg = (
            f"{emoji} **BUTTERFLY ENTERED** #{trade_id}\n"
            f"> Direction: {direction}\n"
            f"> Center: {center_strike} | Width: ±{wing_width}\n"
            f"> Cost: ${entry_price:.2f} | Spot: {spot:.2f}\n"
            f"> Max Profit: ${wing_width - entry_price:.2f} | R/R: {(wing_width - entry_price) / entry_price:.1f}x\n"
            f"> Time: {dt.datetime.now().strftime('%H:%M:%S')}"
        )
        await self._post(msg)

    async def notify_exit(
        self,
        trade_id: int,
        exit_reason: str,
        pnl: float,
        peak_value: float,
        exit_price: float,
    ) -> None:
        emoji = "✅" if pnl > 0 else "❌"
        pnl_str = f"+${pnl:.2f}" if pnl > 0 else f"-${abs(pnl):.2f}"
        msg = (
            f"{emoji} **BUTTERFLY EXITED** #{trade_id}\n"
            f"> P&L: {pnl_str}\n"
            f"> Exit Reason: {exit_reason}\n"
            f"> Exit Price: ${exit_price:.2f} | Peak: ${peak_value:.2f}\n"
            f"> Time: {dt.datetime.now().strftime('%H:%M:%S')}"
        )
        await self._post(msg)

    async def notify_daily_summary(
        self,
        date: dt.date,
        trades: int,
        total_pnl: float,
        win_rate: float,
    ) -> None:
        emoji = "📊"
        pnl_str = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"
        msg = (
            f"{emoji} **DAILY SUMMARY** {date}\n"
            f"> Trades: {trades}\n"
            f"> Total P&L: {pnl_str}\n"
            f"> Win Rate: {win_rate * 100:.0f}%"
        )
        await self._post(msg)

    async def notify_error(self, error: str, context: str = "") -> None:
        msg = f"🚨 **ERROR** {context}\n```{error[:1500]}```"
        await self._post(msg)
