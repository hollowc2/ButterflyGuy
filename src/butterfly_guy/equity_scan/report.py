"""Discord formatting for equity morning scans."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.equity_scan.config import EquityScanSettings
from butterfly_guy.equity_scan.scanner import EquitySnapshot, MarketContext, ScanResults

DISCORD_CHAR_LIMIT = 1900

_UNIVERSE_LABELS = {
    "sp500": "S&P",
    "nq100": "NDX",
    "liquid": "Liq",
    "custom": "★",
}

_SECTOR_SHORT = {
    "Information Technology": "Tech",
    "Consumer Discretionary": "Cons Disc",
    "Consumer Staples": "Cons Stap",
    "Health Care": "Health",
    "Communication Services": "Comm",
    "Real Estate": "RE",
}


def _fmt_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def _fmt_price(value: float) -> str:
    return f"${value:.2f}"


def _fmt_volume(volume: int) -> str:
    if volume >= 1_000_000:
        return f"{volume / 1_000_000:.1f}M"
    if volume >= 1_000:
        return f"{volume / 1_000:.0f}K"
    return str(volume)


def _fmt_universes(snapshot: EquitySnapshot) -> str:
    if not snapshot.universes:
        return ""
    labels = [_UNIVERSE_LABELS.get(tag, tag) for tag in snapshot.universes]
    return f" · {'+'.join(labels)}"


def _fmt_rvol(snapshot: EquitySnapshot) -> str:
    if snapshot.rvol is None:
        return ""
    label = "🔥" if snapshot.rvol >= 1.0 else ""
    return f" · {label}RVOL {snapshot.rvol:.1f}x"


def _direction_emoji(pct: float) -> str:
    return "🟢" if pct >= 0 else "🔴"


def _format_snapshot_line(snapshot: EquitySnapshot, *, pct_field: str) -> str:
    pct = getattr(snapshot, pct_field)
    return (
        f"{_direction_emoji(pct)} **{snapshot.symbol}** **{_fmt_pct(pct)}** "
        f"@ {_fmt_price(snapshot.price)} · {_fmt_volume(snapshot.volume)} vol"
        f"{_fmt_rvol(snapshot)}{_fmt_universes(snapshot)}"
    )


def _sector_label(sector: str) -> str:
    return _SECTOR_SHORT.get(sector, sector)


def _group_snapshots_by_sector(snapshots: list[EquitySnapshot]) -> list[tuple[str, list[EquitySnapshot]]]:
    grouped: dict[str, list[EquitySnapshot]] = {}
    for snapshot in snapshots:
        grouped.setdefault(snapshot.sector, []).append(snapshot)

    known = sorted(sector for sector in grouped if sector != "Unknown")
    if "Unknown" in grouped:
        known.append("Unknown")
    return [(sector, grouped[sector]) for sector in known]


def _format_snapshot_section(
    title: str,
    snapshots: list[EquitySnapshot],
    *,
    pct_field: str,
    empty_text: str,
    group_by_sector: bool,
) -> str:
    if not snapshots:
        return _format_section(title, [], empty_text=empty_text)

    if not group_by_sector:
        lines = [_format_snapshot_line(snapshot, pct_field=pct_field) for snapshot in snapshots]
        return _format_section(title, lines, empty_text=empty_text)

    lines: list[str] = []
    for sector, sector_snapshots in _group_snapshots_by_sector(snapshots):
        lines.append(f"**{_sector_label(sector)}** ({len(sector_snapshots)})")
        lines.extend(
            _format_snapshot_line(snapshot, pct_field=pct_field) for snapshot in sector_snapshots
        )
    return _format_section(title, lines, empty_text=empty_text)


def _format_section(title: str, lines: list[str], *, empty_text: str) -> str:
    body = "\n".join(lines) if lines else empty_text
    return f"{title}\n{body}"


def _format_market_context(context: list[MarketContext]) -> str:
    if not context:
        return "_No index quotes available._"

    priority = {"$SPX", "SPY", "QQQ", "$COMPX", "$DJI"}
    ordered = sorted(
        context,
        key=lambda ctx: (
            0 if ctx.symbol in priority else 1,
            list(priority).index(ctx.symbol) if ctx.symbol in priority else 99,
            ctx.symbol,
        ),
    )
    parts = [f"**{ctx.symbol}** {_fmt_pct(ctx.change_pct)}" for ctx in ordered]
    return " · ".join(parts)


def _format_header(
    results: ScanResults,
    *,
    settings: EquityScanSettings,
    ts: dt.datetime,
) -> str:
    universe_labels = [_UNIVERSE_LABELS.get(u, u) for u in settings.universes]
    tape = _format_market_context(results.market_context)
    return (
        f"📈 **Morning Equity Scan** · {ts.strftime('%a %b %d')} · "
        f"{ts.strftime('%I:%M %p').lstrip('0')} ET\n"
        f"**Tape:** {tape}\n"
        f"_Scanned {results.scanned_symbols:,} names ({', '.join(universe_labels)}) "
        f"· {results.matched_symbols:,} passed filters_"
    )


def build_report(
    results: ScanResults,
    *,
    settings: EquityScanSettings,
    generated_at: dt.datetime | None = None,
) -> list[str]:
    """Build one or more Discord messages within the 2000-char limit."""
    ts = generated_at or dt.datetime.now(EASTERN)
    header = _format_header(results, settings=settings, ts=ts)

    sections: list[str] = []
    group_by_sector = settings.group_by_sector

    prior_min = settings.filters.prior_day_min_pct
    sections.append(
        _format_snapshot_section(
            f"**📊 Yesterday's Rallies** ({len(results.prior_gainers)}) · >{prior_min:.0f}%",
            results.prior_gainers,
            pct_field="prior_day_pct",
            empty_text="_Nothing cleared the rally threshold._",
            group_by_sector=group_by_sector,
        )
    )
    sections.append(
        _format_snapshot_section(
            f"**📉 Yesterday's Selloffs** ({len(results.prior_losers)}) · <-{prior_min:.0f}%",
            results.prior_losers,
            pct_field="prior_day_pct",
            empty_text="_Nothing cleared the selloff threshold._",
            group_by_sector=group_by_sector,
        )
    )

    gap_min = settings.filters.premarket_min_gap_pct
    if results.show_premarket:
        sections.append(
            _format_snapshot_section(
                f"**🌅 Premarket Gap-Ups** ({len(results.premarket_gainers)}) · >{gap_min:.0f}%",
                results.premarket_gainers,
                pct_field="session_gap_pct",
                empty_text="_No meaningful gap-ups yet._",
                group_by_sector=group_by_sector,
            )
        )
        sections.append(
            _format_snapshot_section(
                f"**🌧 Premarket Gap-Downs** ({len(results.premarket_losers)}) · <-{gap_min:.0f}%",
                results.premarket_losers,
                pct_field="session_gap_pct",
                empty_text="_No meaningful gap-downs yet._",
                group_by_sector=group_by_sector,
            )
        )
    else:
        sections.append(
            _format_section(
                "**🌅 Premarket Gaps**",
                [],
                empty_text=(
                    f"_Gap scan starts at {settings.premarket_start_et} ET — "
                    "yesterday's moves above are still current._"
                ),
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


def archive_report(
    messages: list[str],
    *,
    report_dir: str,
    generated_at: dt.datetime,
) -> Path:
    """Write the scan report to a dated markdown file under report_dir."""
    out_dir = Path(report_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{generated_at.strftime('%Y-%m-%d')}.md"
    path.write_text("\n\n---\n\n".join(messages) + "\n")
    return path
