"""Trading and risk notifications."""

from __future__ import annotations

import datetime as dt
import json

import aiohttp
from notify import send as send_telegram

from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.time_utils import EASTERN, now_eastern

log = get_logger(__name__)


class DiscordNotifier:
    """Sends trading notifications to Discord via webhook."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def _post(self, content: str, *, image_png: bytes | None = None, image_name: str = "chart.png") -> None:
        try:
            async with aiohttp.ClientSession() as session:
                if image_png:
                    payload = {
                        "content": content,
                        "embeds": [{"image": {"url": f"attachment://{image_name}"}}],
                    }
                    form = aiohttp.FormData()
                    form.add_field(
                        "payload_json",
                        json.dumps(payload),
                        content_type="application/json",
                    )
                    form.add_field(
                        "file",
                        image_png,
                        filename=image_name,
                        content_type="image/png",
                    )
                    request = session.post(
                        self.webhook_url,
                        data=form,
                        timeout=aiohttp.ClientTimeout(total=15),
                    )
                else:
                    request = session.post(
                        self.webhook_url,
                        json={"content": content},
                        timeout=aiohttp.ClientTimeout(total=10),
                    )
                async with request as resp:
                    if resp.status not in (200, 204):
                        log.warning("discord_post_failed", status=resp.status)
        except Exception as e:
            log.error("discord_error", error=str(e))

    async def notify_entry(
        self,
        trade_id: int,
        underlying: str,
        direction: str,
        expiration: "dt.date",
        lower_strike: float,
        center_strike: float,
        upper_strike: float,
        wing_width: int,
        entry_price: float,
        spot: float,
        order_id: str = "",
        entry_time: "dt.datetime | None" = None,
        mark_price: float | None = None,
        ask_price: float | None = None,
        selected_rr: float | None = None,
        vix: float | None = None,
        selection_method: str = "",
        entry_step: int = 0,
        distance_from_spot: float | None = None,
        chart_png: bytes | None = None,
    ) -> None:
        max_profit = wing_width - entry_price
        fill_rr = max_profit / entry_price if entry_price > 0 else 0
        order_str = (
            f" `{order_id}`"
            if order_id and order_id != "PAPER"
            else (" `PAPER`" if order_id == "PAPER" else "")
        )
        if entry_time is not None:
            entry_et = entry_time.astimezone(EASTERN)
        else:
            entry_et = now_eastern()
        time_str = entry_et.strftime("%H:%M:%S ET")

        method_str = f" | Method: {selection_method}" if selection_method else ""
        quote_parts: list[str] = []
        if mark_price is not None:
            quote_parts.append(f"Mark ${mark_price:.2f}")
        if ask_price is not None:
            quote_parts.append(f"Ask ${ask_price:.2f}")
        quote_parts.append(f"Fill **${entry_price:.2f}**")
        quotes_str = " | ".join(quote_parts)

        rr_str = f"{fill_rr:.1f}x"
        if selected_rr is not None:
            rr_str += f" (scan {selected_rr:.1f}x)"

        spot_parts = [f"Spot: {spot:.2f}"]
        if distance_from_spot is not None:
            spot_parts.append(f"Center dist: {distance_from_spot:.1f} pts")
        spot_str = " | ".join(spot_parts)

        extras: list[str] = []
        if vix is not None:
            extras.append(f"VIX: {vix:.2f}")
        if entry_step > 0:
            extras.append(f"Ladder step: {entry_step}")
        extras_str = " | ".join(extras)

        msg = (
            f"🦋 **{underlying} BUTTERFLY ENTERED** #{trade_id}{order_str}\n"
            f"> **{direction}** | Exp: {expiration}{method_str}\n"
            f"> Strikes: {lower_strike:.0f} / **{center_strike:.0f}** / "
            f"{upper_strike:.0f}  (±{wing_width} pts)\n"
            f"> {quotes_str}\n"
            f"> {spot_str}\n"
            f"> Max Profit: ${max_profit:.2f} | R/R: {rr_str}\n"
            f"> Breakevens: {lower_strike + entry_price:.2f} – {upper_strike - entry_price:.2f}\n"
        )
        if extras_str:
            msg += f"> {extras_str}\n"
        msg += f"> Entry: {time_str}"
        await self._post(msg, image_png=chart_png, image_name="entry_chart.png")

    async def notify_exit(
        self,
        trade_id: int,
        underlying: str,
        direction: str,
        exit_reason: str,
        entry_price: float,
        exit_price: float,
        pnl: float,
        peak_value: float,
        entry_time: "dt.datetime | None" = None,
    ) -> None:
        emoji = "✅" if pnl > 0 else "❌"
        pnl_str = f"+${pnl:.2f}" if pnl > 0 else f"-${abs(pnl):.2f}"
        pnl_pct = (pnl / entry_price * 100) if entry_price > 0 else 0
        pnl_pct_str = f"+{pnl_pct:.0f}%" if pnl_pct >= 0 else f"{pnl_pct:.0f}%"
        now_et = dt.datetime.now()
        duration_str = ""
        if entry_time is not None:
            try:
                held = now_et - entry_time.replace(tzinfo=None)
                mins = int(held.total_seconds() // 60)
                duration_str = f" | Held: {mins}m"
            except Exception:
                pass
        msg = (
            f"{emoji} **{underlying} BUTTERFLY EXITED** #{trade_id}\n"
            f"> **{direction}** | Reason: `{exit_reason}`\n"
            f"> Entry: ${entry_price:.2f} → Exit: ${exit_price:.2f}\n"
            f"> P&L: **{pnl_str}** ({pnl_pct_str}) | Peak: ${peak_value:.2f}\n"
            f"> Time: {now_et.strftime('%H:%M:%S ET')}{duration_str}\n"
            f"> EOD chart follows after market close."
        )
        await self._post(msg)

    async def notify_eod_chart(
        self,
        trade_id: int,
        underlying: str,
        trade_date: "dt.date",
        direction: str,
        exit_reason: str,
        pnl: float,
        tent_hit: bool | None,
        chart_png: bytes,
    ) -> None:
        tent_label = "HIT" if tent_hit else "MISSED" if tent_hit is not None else "N/A"
        pnl_str = f"+${pnl:.2f}" if pnl > 0 else f"-${abs(pnl):.2f}"
        msg = (
            f"📈 **{underlying} EOD CHART** #{trade_id} ({trade_date})\n"
            f"> **{direction}** | Exit: `{exit_reason}` | P&L: **{pnl_str}**\n"
            f"> Profit tent: **{tent_label}**"
        )
        await self._post(msg, image_png=chart_png, image_name="eod_chart.png")

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

    async def notify_consecutive_loss_warning(
        self,
        underlying: str,
        loss_count: int,
        recent_pnls: list[float],
    ) -> None:
        pnl_text = ", ".join(f"${pnl:.2f}" for pnl in recent_pnls[:10])
        msg = (
            f"⚠️ **{underlying} RISK WARNING**\n"
            f"> Recent closed trades show **{loss_count} consecutive losses**.\n"
            f"> Trading is **not blocked** by this warning.\n"
            f"> Recent P&L: {pnl_text}\n"
            f"> Suggested action: review strategy health and decide whether to pause, "
            f"reset, or adjust risk manually."
        )
        await self._post(msg)

    async def notify_error(self, error: str, context: str = "") -> None:
        msg = f"🚨 **ERROR** {context}\n```{error[:1500]}```"
        await self._post(msg)


class TelegramNotifier:
    """Sends risk notifications through the existing Telegram notify helper."""

    async def notify_consecutive_loss_warning(
        self,
        underlying: str,
        loss_count: int,
        recent_pnls: list[float],
    ) -> None:
        pnl_text = ", ".join(f"${pnl:.2f}" for pnl in recent_pnls[:10])
        msg = (
            f"⚠️ {underlying} RISK WARNING\n"
            f"Recent closed trades show {loss_count} consecutive losses.\n"
            f"Trading is not blocked by this warning.\n"
            f"Recent P&L: {pnl_text}\n"
            "Suggested action: review strategy health and decide whether to pause, "
            "reset, or adjust risk manually."
        )
        if not send_telegram(msg):
            log.warning("telegram_post_failed", context="consecutive_loss_warning")
