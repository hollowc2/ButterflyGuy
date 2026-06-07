"""Matplotlib performance charts for Discord (equity + drawdown)."""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from butterfly_guy.reports.live_performance import (
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
    ax.set_title(title, color=_TEXT, fontsize=10, pad=6)
    ax.set_ylabel(y_label, color=_TEXT, fontsize=8)
    ax.tick_params(colors=_TEXT, labelsize=7)
    ax.grid(True, color=_GRID, alpha=0.5, linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_color(_GRID)


def build_performance_chart_png(
    trades: list[TradePoint],
    *,
    title: str,
    period_label: str,
) -> bytes:
    pnls = [t.pnl_dollars for t in trades]
    stats = compute_stats(pnls)
    dd_points = drawdown_series(pnls)
    labels = [t.trade_date.isoformat() for t in trades]
    x = list(range(1, len(trades) + 1))
    equity = [dd.equity for dd in dd_points]
    drawdown_pct = [-dd.drawdown_pct for dd in dd_points]

    pnl_str = f"+{stats.total_pnl:.2f}" if stats.total_pnl >= 0 else f"{stats.total_pnl:.2f}"
    subtitle = (
        f"{period_label} | {stats.trade_count} trades | PnL {pnl_str} USD | "
        f"WR {stats.win_rate:.0f} pct | PF {stats.profit_factor:.2f} | "
        f"Max DD {stats.max_drawdown:.2f} USD"
    )

    point_colors = [
        _DD_EXIT if is_drawdown_exit(t.exit_reason) else _DEFAULT_POINT for t in trades
    ]

    fig, (ax_equity, ax_dd) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    fig.patch.set_facecolor(_BG)
    fig.suptitle(title, color=_TEXT, fontsize=12, y=0.98)
    fig.text(0.5, 0.94, subtitle, ha="center", color=_TEXT, fontsize=8)

    _setup_axes(ax_equity, "Equity Curve", "Cumulative P&L ($)")
    if x:
        ax_equity.plot(x, equity, color=_EQUITY, linewidth=1.8)
        ax_equity.scatter(x, equity, c=point_colors, s=24, zorder=5)
    ax_equity.axhline(0, color=_GRID, linewidth=0.8, linestyle="--")

    _setup_axes(ax_dd, "Drawdown", "Drawdown (%)")
    if x:
        ax_dd.fill_between(x, drawdown_pct, 0, color=_DRAWDOWN, alpha=0.35)
        ax_dd.plot(x, drawdown_pct, color=_DRAWDOWN, linewidth=1.2)

    if labels:
        tick_step = max(1, len(labels) // 8)
        tick_x = x[::tick_step]
        tick_labels = labels[::tick_step]
        ax_dd.set_xticks(tick_x)
        ax_dd.set_xticklabels(tick_labels, rotation=45, ha="right")
    ax_dd.set_xlabel("Trade date", color=_TEXT, fontsize=8)

    fig.subplots_adjust(top=0.88, hspace=0.35)
    return _fig_to_png(fig)
