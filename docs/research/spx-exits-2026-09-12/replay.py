"""Exit-only, chronological research. Never seed a peak from ledger metadata.

Run with the repository virtualenv. Frozen deployed source is imported first.
No database, broker, environment config loader, or network is used here.
"""

import csv
import datetime as dt
import hashlib
import json
import logging
import math
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "frozen"))
import structlog  # noqa: E402 -- frozen deployed package must precede local source

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
from butterfly_guy.core.config import ProfitManagementSettings  # noqa: E402
from butterfly_guy.core.time_utils import get_time_regime, market_close_time  # noqa: E402
from butterfly_guy.position.position_manager import PositionState  # noqa: E402
from butterfly_guy.position.state_machine import ProfitStateMachine  # noqa: E402

ET = ZoneInfo("America/New_York")


def timestamp(x):
    t = dt.datetime.fromisoformat(x)
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def path_for(trade, rows):
    """Require exactly one valid contemporaneous quote per actual held strike."""
    groups = defaultdict(list)
    for r in rows:
        groups[r["snapshot_time"]].append(r)
    strikes = [float(trade[k]) for k in ("lower_strike", "center_strike", "upper_strike")]
    entry = timestamp(trade["entry_time"])
    close = dt.datetime.combine(
        dt.date.fromisoformat(trade["trade_date"]),
        market_close_time(dt.date.fromisoformat(trade["trade_date"])),
        tzinfo=ET,
    )
    out, bad, pre = [], 0, []
    mark_mid_deltas = []
    for ts, legs in sorted(groups.items(), key=lambda x: timestamp(x[0])):
        t = timestamp(ts)
        if t >= close:
            continue
        if len(legs) != 3 or sorted(float(q["strike"]) for q in legs) != strikes:
            bad += 1
            continue
        legs = sorted(legs, key=lambda q: float(q["strike"]))
        if any(
            q[k] is None or not math.isfinite(float(q[k])) or float(q[k]) < 0
            for q in legs
            for k in ("bid", "ask", "mark")
        ) or any(float(q["bid"]) > float(q["ask"]) for q in legs):
            bad += 1
            continue
        vals = {k: float(legs[0][k]) - 2 * float(legs[1][k]) + float(legs[2][k]) for k in ("mark",)}
        bid = float(legs[0]["bid"]) + float(legs[2]["bid"]) - 2 * float(legs[1]["ask"])
        ask = float(legs[0]["ask"]) + float(legs[2]["ask"]) - 2 * float(legs[1]["bid"])
        mark_mid_deltas.append(abs(vals["mark"] - (bid + ask) / 2))
        point = {"time": t, "mark": max(0.0, vals["mark"]), "bid": bid, "ask": ask}
        if t < entry:
            pre.append(point)
        else:
            out.append(point)
    gaps = [(b["time"] - a["time"]).total_seconds() for a, b in zip(out, out[1:])]
    audit = {
        "raw_rows": len(rows),
        "raw_timestamps": len(groups),
        "valid_post_entry": len(out),
        "invalid_groups": bad,
        "first": out[0]["time"].isoformat() if out else None,
        "last": out[-1]["time"].isoformat() if out else None,
        "entry_gap_seconds": (out[0]["time"] - entry).total_seconds() if out else None,
        "max_gap_seconds": max(gaps, default=None),
        "gaps_over_120s": sum(x > 120 for x in gaps),
        "mark_mid_max_difference": max(mark_mid_deltas, default=None),
    }
    return out, audit


def replay(trade, path, settings, fee, stress="mark"):
    machine = ProfitStateMachine(settings)
    entry = float(trade["entry_price"])
    peak = entry
    entry_time = timestamp(trade["entry_time"])
    for i, point in enumerate(path):
        t, value = point["time"], point["mark"]
        peak = max(peak, value)
        local = t.astimezone(ET)
        mins = (
            local - local.replace(hour=9, minute=30, second=0, microsecond=0)
        ).total_seconds() / 60
        close = dt.datetime.combine(local.date(), market_close_time(local.date()), tzinfo=ET)
        pos = PositionState(
            entry_price=entry,
            current_value=round(value, 4),
            peak_value=round(peak, 4),
            pnl=round(value - entry, 4),
            drawdown_from_peak=round((peak - value) / peak, 4) if peak else 0.0,
            time_regime=get_time_regime(mins),
            minutes_to_close=(close - t).total_seconds() / 60,
            minutes_since_open=mins,
            position_age_minutes=(t - entry_time).total_seconds() / 60,
            spread_bid=max(0.0, point["bid"]),
            spread_ask=point["ask"],
            bid_to_mark_ratio=round(max(0.0, point["bid"]) / value, 4) if value else None,
        )
        signal = machine.evaluate(pos)
        if signal:
            fill_point = point
            if stress == "next_quote_halfspread_005":
                if i + 1 == len(path):
                    return {"status": "censored_fill_latency"}
                fill_point = path[i + 1]
            fraction, extra = {
                "mark": (0.0, 0.0),
                "quarter_halfspread_005": (0.25, 0.05),
                "halfspread_005": (0.5, 0.05),
                "crossed_010": (1.0, 0.10),
                "next_quote_halfspread_005": (0.5, 0.05),
            }[stress]
            drag = fraction * max(0.0, fill_point["mark"] - fill_point["bid"]) + extra
            price = round(fill_point["mark"] - drag - fee, 2)
            return {
                "status": "exit",
                "exit_time": fill_point["time"].isoformat(),
                "signal_time": t.isoformat(),
                "exit_price": price,
                "reason": signal.reason,
                "peak_replayed": peak,
                "signal_mark": value,
                "signal_bid": point["bid"],
                "signal_ask": point["ask"],
                "fill_mark": fill_point["mark"],
                "fill_bid": fill_point["bid"],
                "fill_ask": fill_point["ask"],
                "pnl": round((price - entry) * 100 * int(trade["quantity"]), 2),
                "minutes": (fill_point["time"] - entry_time).total_seconds() / 60,
                "exit_drag_dollars": round(drag * 100 * int(trade["quantity"]), 2),
            }
    # A recorded cash settlement is a terminal payoff of these identical strikes,
    # not a quoted peak or a fabricated last-quote liquidation. Require near-close path.
    if trade["exit_reason"] == "cash_settled" and path:
        last = path[-1]["time"].astimezone(ET)
        close = dt.datetime.combine(last.date(), market_close_time(last.date()), tzinfo=ET)
        if (close - last).total_seconds() <= 120:
            price = float(trade["exit_price"])
            return {
                "status": "settlement",
                "exit_time": close.isoformat(),
                "exit_price": price,
                "reason": "cash_settled",
                "peak_replayed": peak,
                "pnl": round((price - entry) * 100 * int(trade["quantity"]), 2),
                "minutes": (close - entry_time).total_seconds() / 60,
                "exit_drag_dollars": 0.0,
            }
    return {"status": "censored_no_exit"}


def metrics(rows):
    ordered = sorted(rows, key=lambda r: timestamp(r["exit_time"]))
    pnl = [r["pnl"] for r in ordered]
    wins = [x for x in pnl if x > 0]
    losses = [x for x in pnl if x < 0]
    cumulative = high = dd = 0.0
    for x in pnl:
        cumulative += x
        high = max(high, cumulative)
        dd = max(dd, high - cumulative)
    n = len(pnl)
    return {
        "trades": n,
        "win_rate": len(wins) / n if n else None,
        "net_pnl": round(sum(pnl), 2),
        "expectancy": sum(pnl) / n if n else None,
        "profit_factor": sum(wins) / -sum(losses) if losses else None,
        "average_win": sum(wins) / len(wins) if wins else None,
        "average_loss": sum(losses) / len(losses) if losses else None,
        "closed_trade_drawdown": round(dd, 2),
        "exposure_hours": sum(r["minutes"] for r in rows) / 60,
        "mean_hold_minutes": sum(r["minutes"] for r in rows) / n if n else None,
        **{
            f"net_excluding_top_{k}": round(sum(pnl) - sum(sorted(wins, reverse=True)[:k]), 2)
            for k in (1, 2, 5)
        },
    }


def write_csv(name, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (ROOT / "results" / name).open("w") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    export = [json.loads(line) for line in (ROOT / "raw/export.jsonl").open()]
    monitor = [json.loads(line) for line in (ROOT / "raw/monitor.jsonl").open()]
    baseline = export[0]
    trades = export[1]["rows"]
    assert len(export[2:]) == len(trades) == len(monitor), "incomplete export"
    settings = ProfitManagementSettings(**baseline["effective"]["profit_management"])
    assert (
        settings.peak_tracking.confirmation_polls == 1
        and not settings.peak_tracking.require_quote_quality
    )
    assert (
        settings.peak_tracking.max_jump_ratio is None
        and settings.peak_tracking.max_jump_abs is None
    )
    assert not settings.quote_quality.enabled
    fee = 4 * baseline["effective"]["execution"]["paper_commission_per_contract"] / 100
    quotes = {
        "collector": {x["trade_id"]: x["rows"] for x in export[2:]},
        "monitor": {x["trade_id"]: x["rows"] for x in monitor},
    }
    results = []
    coverage = []
    parity = []
    summaries = []
    detail = []
    for source, mapping in quotes.items():
        for t in trades:
            path, audit = path_for(t, mapping[t["id"]])
            coverage.append({"source": source, "id": t["id"], "date": t["trade_date"], **audit})
            for policy in ("peakvaluetrailer", "profitprotector"):
                config = settings.model_copy(update={"strategy": policy})
                for stress in (
                    "mark",
                    "quarter_halfspread_005",
                    "halfspread_005",
                    "crossed_010",
                    "next_quote_halfspread_005",
                ):
                    r = replay(t, path, config, fee, stress)
                    results.append(
                        {
                            "source": source,
                            "id": t["id"],
                            "date": t["trade_date"],
                            "fill_model": t["fill_model"],
                            "policy": policy,
                            "stress": stress,
                            **r,
                        }
                    )
                    if policy == "peakvaluetrailer" and stress == "mark":
                        parity.append(
                            {
                                "source": source,
                                "id": t["id"],
                                "date": t["trade_date"],
                                "fill_model": t["fill_model"],
                                "recorded_reason": t["exit_reason"],
                                "recorded_pnl": float(t["pnl"]) * 100 * int(t["quantity"]),
                                "recorded_exit": t["exit_time"],
                                "recorded_exit_price": t["exit_price"],
                                **r,
                                "pnl_difference": round(
                                    r["pnl"] - float(t["pnl"]) * 100 * int(t["quantity"]), 2
                                )
                                if "pnl" in r
                                else None,
                                "exit_time_difference_seconds": (
                                    timestamp(r["exit_time"]) - timestamp(t["exit_time"])
                                ).total_seconds()
                                if "exit_time" in r
                                else None,
                            }
                        )
            if (
                t["fill_model"] == "mark_v1"
                and float(t["pnl"]) < 0
                and float(t["peak_value"]) >= 2 * float(t["entry_price"])
            ):
                detail.append(
                    {
                        "source": source,
                        "id": t["id"],
                        "date": t["trade_date"],
                        "classification": "six_doubled_losers",
                        "recorded_peak_diagnostic_only": t["peak_value"],
                        "observed_path_peak": max((p["mark"] for p in path), default=None),
                    }
                )
    # Explicitly labeled aggregate: monitor where any monitoring rows exist,
    # otherwise collector. Never switch source based on an outcome or fill a gap.
    preferred = {
        t["id"]: ("monitor" if quotes["monitor"][t["id"]] else "collector") for t in trades
    }
    results += [
        dict(r, source="best_available", quote_source=r["source"])
        for r in list(results)
        if r["source"] == preferred[r["id"]]
    ]
    for source in (*quotes, "best_available"):
        for stress in (
            "mark",
            "quarter_halfspread_005",
            "halfspread_005",
            "crossed_010",
            "next_quote_halfspread_005",
        ):
            subset = [r for r in results if r["source"] == source and r["stress"] == stress]
            valid = {
                policy: {r["id"] for r in subset if r["policy"] == policy and "pnl" in r}
                for policy in ("peakvaluetrailer", "profitprotector")
            }
            common = valid["peakvaluetrailer"] & valid["profitprotector"]
            for cohort in ["all", "mark_v1"] + sorted({t["trade_date"][:7] for t in trades}):
                for policy in valid:
                    rs = [
                        r
                        for r in subset
                        if r["policy"] == policy
                        and r["id"] in common
                        and (
                            cohort == "all"
                            or (cohort == "mark_v1" and r["fill_model"] == "mark_v1")
                            or r["date"].startswith(cohort)
                        )
                    ]
                    summaries.append(
                        {
                            "source": source,
                            "stress": stress,
                            "cohort": cohort,
                            "policy": policy,
                            **metrics(rs),
                        }
                    )
    write_csv("trade_results.csv", results)
    write_csv("coverage.csv", coverage)
    write_csv("baseline_parity.csv", parity)
    write_csv("summary.csv", summaries)
    write_csv("six_trades.csv", detail)
    (ROOT / "results/summary.json").write_text(json.dumps(summaries, indent=2))
    manifest = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "range": ["2026-03-17", "2026-09-11"],
        "provider": "Schwab via ButterflyGuy; collector and monitoring tables kept separate",
        "remote": "billy@helios:/opt/butterflyguy; butterfly_spx_app; TimescaleDB",
        "entry_prices": "unchanged recorded; embedded mark_v1 entry commission retained",
        "exit_commission_points": fee,
        "legacy_entry_commission": "unknown; extra $2.60/trade sensitivity required",
        "files": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "raw").glob("*"))
        },
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(
        json.dumps(
            [r for r in summaries if r["cohort"] in ("all", "mark_v1") and r["stress"] == "mark"],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
