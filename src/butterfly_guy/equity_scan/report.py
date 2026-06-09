"""Discord formatting for equity morning scans."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

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


def _fmt_rvol(snapshot: EquitySnapshot) -> str:
    if snapshot.rvol is None:
        return ""
    return f" | RVOL {snapshot.rvol:.2f}x"


def _format_snapshot_line(snapshot: EquitySnapshot, *, pct_field: str) -> str:
    pct = getattr(snapshot, pct_field)
    vol_m = snapshot.volume / 1_000_000
    return (
        f"**{snapshot.symbol}** {_fmt_pct(pct)} | "
        f"{_fmt_price(snapshot.price)} | vol {vol_m:.1f}M"
        f"{_fmt_rvol(snapshot)}{_fmt_universes(snapshot)}"
    )


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
        lines.append(f"_{sector}_")
        lines.extend(
            _format_snapshot_line(snapshot, pct_field=pct_field) for snapshot in sector_snapshots
        )
    return _format_section(title, lines, empty_text=empty_text)


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

    group_by_sector = settings.group_by_sector
    sections.append(
        _format_snapshot_section(
            f"Prior-Day Rallies (>{settings.filters.prior_day_min_pct:.1f}%)",
            results.prior_gainers,
            pct_field="prior_day_pct",
            empty_text="_None above threshold._",
            group_by_sector=group_by_sector,
        )
    )
    sections.append(
        _format_snapshot_section(
            f"Prior-Day Dumps (<-{settings.filters.prior_day_min_pct:.1f}%)",
            results.prior_losers,
            pct_field="prior_day_pct",
            empty_text="_None below threshold._",
            group_by_sector=group_by_sector,
        )
    )
    if results.show_premarket:
        sections.append(
            _format_snapshot_section(
                f"Premarket Gaps (>{settings.filters.premarket_min_gap_pct:.1f}%)",
                results.premarket_gainers,
                pct_field="session_gap_pct",
                empty_text="_No meaningful gap-up names._",
                group_by_sector=group_by_sector,
            )
        )
        sections.append(
            _format_snapshot_section(
                f"Premarket Gaps (<-{settings.filters.premarket_min_gap_pct:.1f}%)",
                results.premarket_losers,
                pct_field="session_gap_pct",
                empty_text="_No meaningful gap-down names._",
                group_by_sector=group_by_sector,
            )
        )
    else:
        sections.append(
            _format_section(
                "Premarket Gaps",
                [],
                empty_text=(
                    f"_Premarket gaps populate between {settings.premarket_start_et}–9:30 ET "
                    "(prior-day section above is still current)._"
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
