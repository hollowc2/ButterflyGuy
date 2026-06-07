"""Matplotlib performance charts for Discord (equity + drawdown)."""

from __future__ import annotations

import io
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from butterfly_guy.reports.live_performance import (
    ReportStats,
    TradePoint,
    compute_stats,
    drawdown_series,
    is_drawdown_exit,
)

_BG = "#1a1a2e"
_GRID = "#2d2d44"
_TEXT = "#e0e0e0"
_EQUITY = "#c8922a"
_DRAWDOWN = "#cc5555"
_DD_EXIT = "#ef5350"
_DEFAULT_POINT = "#c8922a"


def _fig_to_png(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=_BG, edgecolor=_BG, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _setup_axes(ax: plt.Axes, title: str, y_label: str) -> None:
    ax.set_facecolor(_BG)
    ax.set_title(title, color=_TEXT, fontsize=9, pad=4)
    ax.set_ylabel(y_label, color=_TEXT, fontsize=7)
    ax.tick_params(colors=_TEXT, labelsize=6)
    ax.grid(True, color=_GRID, alpha=0.5, linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_color(_GRID)


def _format_pnl(value: float) -> str:
    return f"+{value:.0f}" if value >= 0 else f"{value:.0f}"


def _period_subtitle(label: str, stats: ReportStats) -> str:
    return (
        f"{label}\n"
        f"PnL {_format_pnl(stats.total_pnl)} | {stats.trade_count} tr | "
        f"WR {stats.win_rate:.0f}% | PF {stats.profit_factor:.2f} | "
        f"DD {stats.max_drawdown:.0f}"
    )


def _plot_period_panels(
    ax_equity: plt.Axes,
    ax_dd: plt.Axes,
    trades: list[TradePoint],
    *,
    label: str,
) -> None:
    pnls = [t.pnl_dollars for t in trades]
    stats = compute_stats(pnls)
    dd_points = drawdown_series(pnls)
    x = list(range(1, len(trades) + 1))
    equity = [dd.equity for dd in dd_points]
    drawdown_pct = [-dd.drawdown_pct for dd in dd_points]
    point_colors = [
        _DD_EXIT if is_drawdown_exit(t.exit_reason) else _DEFAULT_POINT for t in trades
    ]
    panel_title = _period_subtitle(label, stats)

    _setup_axes(ax_equity, panel_title, "P&L ($)")
    if x:
        ax_equity.plot(x, equity, color=_EQUITY, linewidth=1.4)
        ax_equity.scatter(x, equity, c=point_colors, s=16, zorder=5)
    ax_equity.axhline(0, color=_GRID, linewidth=0.8, linestyle="--")

    _setup_axes(ax_dd, "Drawdown", "DD (%)")
    if x:
        ax_dd.fill_between(x, drawdown_pct, 0, color=_DRAWDOWN, alpha=0.35)
        ax_dd.plot(x, drawdown_pct, color=_DRAWDOWN, linewidth=1.0)


def build_performance_chart_png(
    trades: list[TradePoint],
    *,
    title: str,
    period_label: str,
) -> bytes:
    fig, (ax_equity, ax_dd) = plt.subplots(2, 1, figsize=(9, 6))
    fig.patch.set_facecolor(_BG)
    fig.suptitle(title, color=_TEXT, fontsize=12, y=0.98)
    _plot_period_panels(ax_equity, ax_dd, trades, label=period_label)
    fig.subplots_adjust(top=0.92, hspace=0.35)
    return _fig_to_png(fig)


def build_combined_performance_chart_png(
    periods: Sequence[tuple[str, list[TradePoint]]],
    *,
    title: str = "SPX Performance Summary",
) -> bytes:
    """Build one image with weekly, monthly, and all-time equity + drawdown panels."""
    fig, axes = plt.subplots(2, len(periods), figsize=(14, 7))
    fig.patch.set_facecolor(_BG)
    fig.suptitle(title, color=_TEXT, fontsize=13, y=0.98)

    for col, (label, trades) in enumerate(periods):
        _plot_period_panels(axes[0, col], axes[1, col], trades, label=label)

    fig.subplots_adjust(top=0.90, hspace=0.45, wspace=0.28)
    return _fig_to_png(fig)
