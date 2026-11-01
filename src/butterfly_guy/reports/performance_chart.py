"""Matplotlib performance chart for the Discord weekend review."""

from __future__ import annotations

import datetime as dt
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from butterfly_guy.reports.live_performance import TradePoint, drawdown_series

# Dark palette; series steps validated for the dark surface (dataviz skill).
_BG = "#1a1a2e"
_GRID = "#2d2d44"
_TEXT = "#e0e0e0"
_MUTED = "#8a8aa3"
_PAPER = "#3987e5"
_EXECUTABLE = "#d95926"
_GAIN = "#0ca30c"
_LOSS = "#d03b3b"
_DRAWDOWN = "#d03b3b"
_WINDOW = "#e0e0e0"


def _fig_to_png(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, facecolor=_BG, edgecolor=_BG, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _setup_axes(ax: plt.Axes, title: str, y_label: str) -> None:
    ax.set_facecolor(_BG)
    ax.set_title(title, color=_TEXT, fontsize=11, loc="left", pad=6)
    ax.set_ylabel(y_label, color=_MUTED, fontsize=10)
    ax.tick_params(colors=_MUTED, labelsize=9, length=0)
    ax.grid(True, axis="y", color=_GRID, alpha=0.6, linewidth=0.6)
    for side, spine in ax.spines.items():
        spine.set_visible(side == "bottom")
        spine.set_color(_GRID)


def _money(value: float) -> str:
    return f"+${value:,.0f}" if value >= 0 else f"-${abs(value):,.0f}"


def _cumulative(dates: list[dt.date], pnls: list[float]) -> tuple[list[dt.date], list[float]]:
    """Cumulative P&L anchored at $0 the day before the first trade."""
    xs = [dates[0] - dt.timedelta(days=1), *dates]
    ys = [0.0]
    for pnl in pnls:
        ys.append(ys[-1] + pnl)
    return xs, ys


def _plot_equity(
    ax_equity: plt.Axes,
    ax_dd: plt.Axes,
    all_time: list[TradePoint],
    *,
    window_starts: list[tuple[str, dt.date]],
) -> None:
    _setup_axes(ax_equity, "Cumulative P&L", "$")
    _setup_axes(ax_dd, "Drawdown from peak (paper)", "$")
    if not all_time:
        return

    dates = [t.trade_date for t in all_time]
    paper = [t.pnl_dollars for t in all_time]
    xs, paper_eq = _cumulative(dates, paper)
    ax_equity.axhline(0, color=_MUTED, linewidth=0.8)
    ax_equity.plot(xs, paper_eq, color=_PAPER, linewidth=2.0,
                   label=f"Paper (mark fills)  {_money(paper_eq[-1])}")

    executable = [t.executable_pnl_dollars for t in all_time]
    if all(value is not None for value in executable):
        _, exec_eq = _cumulative(dates, executable)
        ax_equity.plot(xs, exec_eq, color=_EXECUTABLE, linewidth=2.0, linestyle=(0, (5, 2)),
                       label=f"Executable (marketable est.)  {_money(exec_eq[-1])}")
    ax_equity.legend(loc="upper left", fontsize=9, frameon=False, labelcolor=_TEXT)

    drawdown = [0.0, *(-point.drawdown_dollars for point in drawdown_series(paper))]
    ax_dd.fill_between(xs, drawdown, 0, color=_DRAWDOWN, alpha=0.35, linewidth=0)
    ax_dd.plot(xs, drawdown, color=_DRAWDOWN, linewidth=1.2)
    worst = min(range(len(drawdown)), key=drawdown.__getitem__)
    if drawdown[worst] < 0:
        ax_dd.annotate(f"max {_money(drawdown[worst])}", (xs[worst], drawdown[worst]),
                       xytext=(6, 0), textcoords="offset points", color=_TEXT, fontsize=9,
                       va="center")

    for label, start in window_starts:
        for ax in (ax_equity, ax_dd):
            ax.axvspan(start, xs[-1], color=_WINDOW, alpha=0.05, linewidth=0)
        ax_equity.annotate(label, (start, 1.0), xycoords=("data", "axes fraction"),
                           xytext=(3, -3), textcoords="offset points", color=_MUTED,
                           fontsize=8, va="top")
    ax_dd.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))


def _plot_trade_bars(ax: plt.Axes, monthly: list[TradePoint], week_start: dt.date) -> None:
    _setup_axes(ax, "Month to date, per trade (this week labeled)", "Paper P&L ($)")
    ax.axhline(0, color=_MUTED, linewidth=0.8)
    if not monthly:
        return
    xs = list(range(len(monthly)))
    for x, trade in zip(xs, monthly, strict=True):
        this_week = trade.trade_date >= week_start
        color = _GAIN if trade.pnl_dollars >= 0 else _LOSS
        ax.bar(x, trade.pnl_dollars, width=0.75, color=color,
               alpha=1.0 if this_week else 0.35, linewidth=0)
        if this_week:
            offset = 4 if trade.pnl_dollars >= 0 else -4
            ax.annotate(_money(trade.pnl_dollars), (x, trade.pnl_dollars),
                        xytext=(0, offset), textcoords="offset points", ha="center",
                        va="bottom" if trade.pnl_dollars >= 0 else "top",
                        rotation=90, color=_TEXT, fontsize=8)
    ax.set_xticks(xs, [f"{t.trade_date:%m/%d}" for t in monthly], rotation=90)
    ax.margins(y=0.2)


def build_combined_performance_chart_png(
    *,
    weekly: list[TradePoint],
    monthly: list[TradePoint],
    all_time: list[TradePoint],
    title: str = "SPX Performance Summary",
    subtitle: str = "",
) -> bytes:
    """All-time equity + drawdown beside this month's per-trade P&L bars."""
    fig = plt.figure(figsize=(13, 6.6))
    fig.patch.set_facecolor(_BG)
    grid = fig.add_gridspec(2, 2, width_ratios=[3, 2], height_ratios=[3, 1.2],
                            hspace=0.12, wspace=0.18)
    ax_equity = fig.add_subplot(grid[0, 0])
    ax_dd = fig.add_subplot(grid[1, 0], sharex=ax_equity)
    ax_bars = fig.add_subplot(grid[:, 1])
    ax_equity.tick_params(labelbottom=False)

    fig.text(0.01, 0.995, title, color=_TEXT, fontsize=13, fontweight="bold",
             ha="left", va="top")
    if subtitle:
        fig.text(0.01, 0.955, subtitle, color=_MUTED, fontsize=10, ha="left", va="top")

    week_start = weekly[0].trade_date if weekly else None
    month_start = monthly[0].trade_date if monthly else None
    window_starts = [
        (label, start)
        for label, start in (("month", month_start), ("week", week_start))
        if start is not None
    ]
    _plot_equity(ax_equity, ax_dd, all_time, window_starts=window_starts)
    _plot_trade_bars(ax_bars, monthly, week_start or dt.date.max)

    fig.subplots_adjust(top=0.86)
    return _fig_to_png(fig)
