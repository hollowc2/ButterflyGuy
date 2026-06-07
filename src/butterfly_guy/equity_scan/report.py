"""Discord formatting for equity morning scans."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.equity_scan.config import EquityScanSettings
from butterfly_guy.equity_scan.scanner import EquitySnapshot, MarketContext, ScanResults

DISCORD_CHAR_LIMIT = 1900


def _fmt_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def _fmt_price(value: float) -> str:
    return f"${value:.2f}"


def _fmt_universes(snapshot: EquitySnapshot) -> str:
    if not snapshot.universes:
        return ""
    tags = ",".join(snapshot.universes)
    return f" `{tags}`"


def _format_snapshot_line(snapshot: EquitySnapshot, *, pct_field: str) -> str:
    pct = getattr(snapshot, pct_field)
    vol_m = snapshot.volume / 1_000_000
    return (
        f"**{snapshot.symbol}** {_fmt_pct(pct)} | "
        f"{_fmt_price(snapshot.price)} | vol {vol_m:.1f}M{_fmt_universes(snapshot)}"
    )


def _format_mover_line(item: dict) -> str:
    symbol = item.get("symbol") or item.get("ticker") or "?"
    description = item.get("description") or item.get("name") or ""
    change = item.get("change") or item.get("netChange")
    pct = item.get("changePercent") or item.get("netPercentChange")
    if pct is not None:
        try:
            pct_text = _fmt_pct(float(pct))
        except (TypeError, ValueError):
            pct_text = str(pct)
    elif change is not None:
        pct_text = str(change)
    else:
        pct_text = "n/a"
    suffix = f" — {description}" if description else ""
    return f"**{symbol}** {pct_text}{suffix}"


def _format_section(title: str, lines: list[str], *, empty_text: str) -> str:
    body = "\n".join(lines) if lines else empty_text
    return f"**{title}**\n{body}"


def build_report(
    results: ScanResults,
    *,
    settings: EquityScanSettings,
    generated_at: dt.datetime | None = None,
) -> list[str]:
    """Build one or more Discord messages within the 2000-char limit."""
    ts = generated_at or dt.datetime.now(EASTERN)
    header = (
        f"📈 **Equity Morning Scan** — {ts.strftime('%a %b %d, %Y %H:%M %Z')}\n"
        f"> Universes: {', '.join(settings.universes)} | "
        f"Scanned: {results.scanned_symbols} | Matched filters: {results.matched_symbols}"
    )

    sections: list[str] = []
    if results.market_context:
        ctx_lines = [
            f"**{ctx.symbol}** {_fmt_price(ctx.price)} ({_fmt_pct(ctx.change_pct)})"
            for ctx in results.market_context
        ]
        sections.append(_format_section("Market Context", ctx_lines, empty_text="No context quotes."))

    sections.append(
        _format_section(
            f"Prior-Day Rallies (>{settings.filters.prior_day_min_pct:.1f}%)",
            [_format_snapshot_line(s, pct_field="prior_day_pct") for s in results.prior_gainers],
            empty_text="_None above threshold._",
        )
    )
    sections.append(
        _format_section(
            f"Prior-Day Dumps (<-{settings.filters.prior_day_min_pct:.1f}%)",
            [_format_snapshot_line(s, pct_field="prior_day_pct") for s in results.prior_losers],
            empty_text="_None below threshold._",
        )
    )
    sections.append(
        _format_section(
            f"Premarket Gaps (>{settings.filters.premarket_min_gap_pct:.1f}%)",
            [_format_snapshot_line(s, pct_field="session_gap_pct") for s in results.premarket_gainers],
            empty_text="_No meaningful gap-up names._",
        )
    )
    sections.append(
        _format_section(
            f"Premarket Gaps (<-{settings.filters.premarket_min_gap_pct:.1f}%)",
            [_format_snapshot_line(s, pct_field="session_gap_pct") for s in results.premarket_losers],
            empty_text="_No meaningful gap-down names._",
        )
    )

    if settings.include_movers:
        sections.append(
            _format_section(
                "Schwab Movers (Up)",
                [_format_mover_line(item) for item in results.movers_up],
                empty_text="_Movers unavailable (market closed or no data)._",
            )
        )
        sections.append(
            _format_section(
                "Schwab Movers (Down)",
                [_format_mover_line(item) for item in results.movers_down],
                empty_text="_Movers unavailable (market closed or no data)._",
            )
        )

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
