"""Discord formatting for the daily report card."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from butterfly_guy.reports.daily_report_card import (
    DailyReportCard,
    TradeResult,
    effective_pnl,
    effective_pnl_pct,
    effective_start_balance,
    transfer_total,
)

DISCORD_CHAR_LIMIT = 1900


def _fmt_money(value: float) -> str:
    return f"${value:,.2f}"


def _fmt_signed(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{_fmt_money(value)}"


def _fmt_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def _direction_emoji(value: float) -> str:
    if value > 0:
        return "🟢"
    if value < 0:
        return "🔴"
    return "⚪"


def _format_trade_line(trade: TradeResult) -> str:
    return f"{_direction_emoji(trade.pnl)} {trade.label} {_fmt_signed(trade.pnl)}"


def _format_trade_section(title: str, trades: list[TradeResult], empty_text: str) -> str:
    if not trades:
        return f"**{title}**\n{empty_text}"
    lines = [_format_trade_line(t) for t in trades]
    return f"**{title}**\n" + "\n".join(lines)


def _format_transfers(card: DailyReportCard) -> str:
    if not card.cash_movements:
        return ""
    lines = [f"• {m.label}: {_fmt_signed(m.amount)}" for m in card.cash_movements]
    return "**💸 Transfers**\n" + "\n".join(lines)


def _format_account_section(card: DailyReportCard) -> str:
    start = effective_start_balance(card)
    pnl = effective_pnl(card)
    pnl_pct = effective_pnl_pct(card)
    schwab_open = card.balances.starting_liquidation

    lines = [
        "**💰 Account**",
        f"Start: {_fmt_money(start)} → End: {_fmt_money(card.balances.ending_liquidation)}",
        f"**{_fmt_signed(pnl)} ({_fmt_pct(pnl_pct)})** {_direction_emoji(pnl)}",
    ]

    if card.cash_movements and abs(start - schwab_open) > 0.01:
        lines.append(
            f"_Schwab open: {_fmt_money(schwab_open)} · "
            f"transfers {_fmt_signed(transfer_total(card))}_"
        )

    return "\n".join(lines)


def _format_problems(problems: list[str]) -> str:
    if not problems:
        return "**✅ Watchlist**\n_No issues flagged today._"
    lines = [f"• {p}" for p in problems]
    return "**⚠️ Watchlist**\n" + "\n".join(lines)


def build_report_messages(card: DailyReportCard) -> list[str]:
    """Build Discord messages, chunking to stay under the char limit."""
    date_str = card.report_date.strftime("%a %b %-d, %Y")
    header = (
        f"📋 **Daily Report Card — {date_str}**\n"
        f"_{card.balances.account_type} account · "
        f"as of {card.generated_at.strftime('%H:%M')} ET_"
    )

    account_section = _format_account_section(card)

    if card.activity.trade_count:
        activity_section = (
            "**📊 Today's Activity**\n"
            f"Trades: {card.activity.trade_count} closed · "
            f"{card.activity.winners}W / {card.activity.losers}L"
            + (f" / {card.activity.breakeven}BE" if card.activity.breakeven else "")
            + f" · Win rate {card.activity.win_rate:.0f}%"
        )
    else:
        activity_section = "**📊 Today's Activity**\n_No closed trades today._"

    transfers_section = _format_transfers(card)

    winners_section = _format_trade_section(
        "🏆 Big Winners",
        card.top_winners,
        "_No winning trades._",
    )
    losers_section = _format_trade_section(
        "📉 Big Losers",
        card.top_losers,
        "_No losing trades._",
    )
    problems_section = _format_problems(card.problems)

    sections = [account_section, activity_section]
    if transfers_section:
        sections.append(transfers_section)
    sections.extend([winners_section, losers_section, problems_section])

    messages: list[str] = []
    current = header
    for section in sections:
        candidate = f"{current}\n\n{section}"
        if len(candidate) > DISCORD_CHAR_LIMIT:
            messages.append(current)
            current = section
        else:
            current = candidate
    if current:
        messages.append(current)
    return messages


def archive_report(
    messages: list[str],
    *,
    report_dir: str,
    report_date: dt.date,
) -> Path:
    out_dir = Path(report_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{report_date.isoformat()}.md"
    path.write_text("\n\n---\n\n".join(messages) + "\n")
    return path
