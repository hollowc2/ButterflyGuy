"""Same-day paired comparison of the paper and live SPX bots (read-only).

Each bot has its own database (docs/operations/concurrent-paper-live-spx-design.md §12).
Selection marks come from the trade's per_width_bests entry for its chosen width; exit marks
from exit_mark_at_signal. P&L is the DB's pre-fee figure.

The two bots often pick different flies from near-tied candidates, so live minus paper P&L
mixes selection, path and fills. The live fill check prices live's own fly at its marks
(paper's mark model, before fees) and isolates the fill cost on every live trade.

Each bot reads its own market data, so the report also shows when each read its entry inputs
(chain, spot, VIX) and how often its monitor polled: two bots on the same day can pick different
flies or exit at different times because they read the market seconds apart, not because of
fills (docs/operations/schwab-429-concurrent-spx.md §2.7).
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

from butterfly_guy.core.time_utils import EASTERN, PACIFIC

# Entry decisions worth showing when a bot did not trade.
NO_TRADE_EVENTS = (
    "entry_blocked",
    "entry_exhausted",
    "gap_regime_skip",
    "bias_filter_no_signal",
)

TRADES_SQL = """
SELECT * FROM butterfly_trades
WHERE underlying = 'SPX' AND trade_date = $1
ORDER BY entry_time
"""
BLOCKS_SQL = """
SELECT ts, event_type, data FROM decision_log
WHERE underlying = 'SPX' AND event_type = ANY($1::text[]) AND ts >= $2 AND ts < $3
ORDER BY ts DESC
LIMIT 3
"""
POLLS_SQL = """
SELECT count(*) AS polls,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY gap) AS median_gap_s
FROM (
    SELECT extract(epoch FROM ts - lag(ts) OVER (ORDER BY ts)) AS gap
    FROM (SELECT DISTINCT ts FROM monitoring_leg_quotes WHERE trade_id = $1) p
) g
"""
# Entry inputs read this far apart are flagged: the market can move a strike in a few seconds.
ENTRY_INPUT_GAP_FLAG_SECONDS = 2.0


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("metadata") or {}
    return json.loads(raw) if isinstance(raw, str) else dict(raw)


def _num(value: Any) -> float | None:
    return None if value is None else round(float(value), 4)


def _pt(ts: dt.datetime | None) -> str | None:
    return None if ts is None else ts.astimezone(PACIFIC).strftime("%H:%M:%S")


def _iso(value: Any) -> dt.datetime | None:
    return dt.datetime.fromisoformat(value) if isinstance(value, str) else None


def _pt_tenths(ts: dt.datetime | None) -> str | None:
    return None if ts is None else ts.astimezone(PACIFIC).strftime("%H:%M:%S.%f")[:10]


def summarize_trade(row: dict[str, Any]) -> dict[str, Any]:
    meta = _metadata(row)
    width = row["wing_width"]
    best = next(
        (b for b in meta.get("per_width_bests") or [] if b.get("width") == width), {}
    )
    entry_mark = _num(best.get("cost"))
    exit_mark = _num(meta.get("exit_mark_at_signal"))
    entry_fill = _num(row["entry_price"])
    exit_fill = _num(row.get("exit_price"))
    quantity = int(row.get("quantity") or 1)
    pnl = row.get("pnl")
    return {
        "trade_id": row["id"],
        "status": row["status"],
        "entry_time_pt": _pt(row["entry_time"]),
        "direction": row["direction"],
        "strikes": [float(row["lower_strike"]), float(row["center_strike"]),
                    float(row["upper_strike"])],
        "width": width,
        "vix": _num(meta.get("vix")),
        "vix_time_pt": _pt_tenths(_iso(meta.get("vix_timestamp"))),
        "chain_fetched_at": meta.get("selected_chain_snapshot_time"),
        "chain_fetched_pt": _pt_tenths(_iso(meta.get("selected_chain_snapshot_time"))),
        "entry_spot": _num(meta.get("entry_spot")),
        "reward_risk": _num(best.get("reward_risk")),
        "entry_mark": entry_mark,
        "entry_fill": entry_fill,
        "entry_vs_mark": (
            None if entry_mark is None else round(entry_fill - entry_mark, 4)
        ),
        "exit_time_pt": _pt(row.get("exit_time")),
        "exit_reason": row.get("exit_reason"),
        "exit_mark": exit_mark,
        "exit_fill": exit_fill,
        "exit_vs_mark": (
            None if exit_mark is None or exit_fill is None else round(exit_fill - exit_mark, 4)
        ),
        "pnl_usd": None if pnl is None else round(float(pnl) * 100 * quantity, 2),
        "paper_fill_model": meta.get("paper_fill_model"),
        "per_width_bests": meta.get("per_width_bests") or [],
        "monitor_polls": row.get("monitor_polls"),
        "monitor_median_gap_s": _num(row.get("monitor_median_gap_s")),
    }


def live_fill_check(trade: dict[str, Any], quantity: int = 1) -> dict[str, Any] | None:
    """Live's actual P&L against its own fly at the entry and exit marks, before fees."""
    marks = (trade["entry_mark"], trade["exit_mark"])
    if None in marks or trade["pnl_usd"] is None:
        return None
    mark_pnl = round((marks[1] - marks[0]) * 100 * quantity, 2)
    return {
        "mark_pnl_usd": mark_pnl,
        "actual_pnl_usd": trade["pnl_usd"],
        "fill_cost_usd": round(trade["pnl_usd"] - mark_pnl, 2),
        "entry_fill_usd": round(-trade["entry_vs_mark"] * 100 * quantity, 2),
        "exit_fill_usd": round(trade["exit_vs_mark"] * 100 * quantity, 2),
    }


def _blocks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        data = row["data"]
        data = json.loads(data) if isinstance(data, str) else dict(data or {})
        out.append({"time_pt": _pt(row["ts"]), "event": row["event_type"],
                    "reason": data.get("reason")})
    return out


def pair_report(
    session: dt.date,
    paper_trades: list[dict[str, Any]],
    live_trades: list[dict[str, Any]],
    paper_blocks: list[dict[str, Any]],
    live_blocks: list[dict[str, Any]],
    rate_limited: dict[str, int] | None = None,
) -> dict[str, Any]:
    """``rate_limited`` is each bot's Schwab 429 count for the session, when the caller has it."""
    paper = [summarize_trade(r) for r in paper_trades]
    live = [summarize_trade(r) for r in live_trades]
    report: dict[str, Any] = {
        "date": session.isoformat(),
        "paper": paper,
        "live": live,
        "flags": [],
    }
    if rate_limited is not None:
        report["rate_limited"] = rate_limited
    flags = report["flags"]
    if live and any(t["paper_fill_model"] for t in live):
        flags.append("live DB holds a paper trade (rehearsal or misconfiguration)")
    if live:
        check = live_fill_check(live[0], int(live_trades[0].get("quantity") or 1))
        if check is not None:
            report["live_fill_check"] = check
    if not paper or not live:
        for name, trades, blocks in (("paper", paper, paper_blocks),
                                     ("live", live, live_blocks)):
            if not trades:
                report[f"{name}_no_trade_reasons"] = _blocks(blocks)
        if paper or live:
            flags.append(f"only {'paper' if paper else 'live'} traded")
        return report

    p, q = paper[0], live[0]
    p_read, q_read = _iso(p["chain_fetched_at"]), _iso(q["chain_fetched_at"])
    if p_read and q_read:
        inputs: dict[str, Any] = {
            "chain_read_gap_s": round((q_read - p_read).total_seconds(), 1),
            "spot_diff": None if None in (p["entry_spot"], q["entry_spot"])
            else round(q["entry_spot"] - p["entry_spot"], 2),
            "vix_diff": None if None in (p["vix"], q["vix"]) else round(q["vix"] - p["vix"], 2),
        }
        report["entry_inputs_live_minus_paper"] = inputs
        if abs(inputs["chain_read_gap_s"]) >= ENTRY_INPUT_GAP_FLAG_SECONDS:
            flags.append(
                f"entry inputs read {inputs['chain_read_gap_s']:+} s apart (live minus paper; "
                f"spot {inputs['spot_diff']}, VIX {inputs['vix_diff']}): selection and price "
                "differences may be timing, not fills"
            )
    same_fly = (p["direction"], p["strikes"]) == (q["direction"], q["strikes"])
    if not same_fly:
        flags.append(
            f"different fly: paper {p['direction']} {p['strikes']} vs "
            f"live {q['direction']} {q['strikes']}"
        )
    if p["exit_reason"] != q["exit_reason"]:
        flags.append(f"different exit: paper {p['exit_reason']} vs live {q['exit_reason']}")
    p_exit, q_exit = paper_trades[0].get("exit_time"), live_trades[0].get("exit_time")
    if p_exit and q_exit:
        gap = round((q_exit - p_exit).total_seconds() / 60, 1)
        report["exit_gap_minutes"] = gap
        if abs(gap) >= 1:
            flags.append(f"exit time gap {gap:+} min (live minus paper)")
    if p["pnl_usd"] is not None and q["pnl_usd"] is not None:
        diff = round(q["pnl_usd"] - p["pnl_usd"], 2)
        attribution: dict[str, Any] = {"live_minus_paper_usd": diff}
        if same_fly:
            entry = -(q["entry_vs_mark"] or 0) * 100
            exit_ = (q["exit_vs_mark"] or 0) * 100
            attribution.update(
                entry_fill_usd=round(entry, 2),
                exit_fill_usd=round(exit_, 2),
                path_and_timing_usd=round(diff - entry - exit_, 2),
            )
        report["pnl_attribution"] = attribution
    return report


def session_window(session: dt.date) -> tuple[dt.datetime, dt.datetime]:
    start = dt.datetime.combine(session, dt.time(0), tzinfo=EASTERN)
    return start, start + dt.timedelta(days=1)


async def fetch_side(conn: Any, session: dt.date) -> tuple[list[dict], list[dict]]:
    trades = [dict(r) for r in await conn.fetch(TRADES_SQL, session)]
    for trade in trades:
        polls = await conn.fetchrow(POLLS_SQL, trade["id"])
        trade["monitor_polls"] = polls["polls"] if polls else None
        trade["monitor_median_gap_s"] = polls["median_gap_s"] if polls else None
    blocks = [
        dict(r)
        for r in await conn.fetch(BLOCKS_SQL, list(NO_TRADE_EVENTS), *session_window(session))
    ]
    return trades, blocks


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# SPX paper vs live, {report['date']} (times PT, P&L pre-fee)", ""]
    rows = [
        ("trade id", "trade_id"), ("entry", "entry_time_pt"), ("direction", "direction"),
        ("strikes", "strikes"), ("width", "width"), ("VIX", "vix"), ("VIX read", "vix_time_pt"),
        ("entry chain read", "chain_fetched_pt"), ("entry spot", "entry_spot"),
        ("RR", "reward_risk"),
        ("entry mark", "entry_mark"), ("entry fill", "entry_fill"),
        ("entry fill − mark", "entry_vs_mark"), ("exit", "exit_time_pt"),
        ("exit reason", "exit_reason"), ("exit mark", "exit_mark"), ("exit fill", "exit_fill"),
        ("exit fill − mark", "exit_vs_mark"), ("P&L $", "pnl_usd"),
        ("monitor polls", "monitor_polls"), ("median poll gap s", "monitor_median_gap_s"),
    ]
    paper = report["paper"][0] if report["paper"] else {}
    live = report["live"][0] if report["live"] else {}
    lines += ["| | paper | live |", "|---|---|---|"]
    for label, key in rows:
        lines.append(f"| {label} | {paper.get(key, '—')} | {live.get(key, '—')} |")
    if "rate_limited" in report:
        counts = report["rate_limited"]
        lines.append(
            f"| Schwab 429s | {counts.get('paper', '—')} | {counts.get('live', '—')} |"
        )
    lines.append("")
    for name in ("paper", "live"):
        reasons = report.get(f"{name}_no_trade_reasons")
        if reasons is not None:
            text = "; ".join(f"{r['time_pt']} {r['event']} {r['reason'] or ''}".strip()
                             for r in reasons) or "no entry decisions logged"
            lines.append(f"- **{name} did not trade:** {text}")
    if "entry_inputs_live_minus_paper" in report:
        lines.append(f"- **Entry inputs, live minus paper:** "
                     f"{report['entry_inputs_live_minus_paper']}")
    if "live_fill_check" in report:
        c = report["live_fill_check"]
        lines.append(
            f"- **Live fill check** (live's own fly at its marks, before fees; holds whether "
            f"or not the bots picked the same fly): marks ${c['mark_pnl_usd']}, actual "
            f"${c['actual_pnl_usd']}, fill cost ${c['fill_cost_usd']} "
            f"(entry ${c['entry_fill_usd']}, exit ${c['exit_fill_usd']})"
        )
    if "pnl_attribution" in report:
        lines.append(f"- **P&L attribution:** {report['pnl_attribution']}")
    if report.get("flags"):
        lines += ["", "## Flags", *[f"- {flag}" for flag in report["flags"]]]
    else:
        lines += ["", "No divergence flags."]
    if paper and live and paper.get("strikes") != live.get("strikes"):
        lines += [
            "",
            "## Candidates at selection (per_width_bests)",
            f"- paper: {paper['per_width_bests']}",
            f"- live: {live['per_width_bests']}",
        ]
    return "\n".join(lines) + "\n"
