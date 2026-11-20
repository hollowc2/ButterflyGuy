"""Independent journal and raw-price review of the bounded XSP investigation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BASELINES = {"MR1": "MRB", "MR2": "MRB", "T1": "B1", "T2": "B2"}
NAMES = {"failed_breakout": "MR1", "excursion_reversal": "MR2", "time_1005": "MRB"}


def load_records(reversion: Path, trend: Path) -> list[dict]:
    records = []
    for line in (reversion / "journal.jsonl").read_text().splitlines():
        r = json.loads(line)
        row = {"date": r["date"], "variant": NAMES[r["arm"]], "width": r["width"],
               "status": r["status"]}
        if r["status"] == "completed":
            row.update({k: r[k] for k in ("center", "right", "entry_ask", "liquidation_bid",
                                         "entry_mark", "exit_mark")})
            for src, dest in (("signal_time", "signal_ts"), ("entry_time", "entry_ts"),
                              ("exit_time", "exit_ts"), ("midpoint", "pnl_mark"),
                              ("marketable", "pnl_marketable"), ("stressed", "pnl_stressed"),
                              ("initial_risk_dollars", "initial_risk")):
                row[dest] = r[src]
        records.append(row)
    journal = pd.read_csv(trend / "journal.csv")
    records.extend(journal.to_dict("records"))
    for line in (trend / "session-status.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["status"] == "completed":
            continue
        for width in ([int(r["width"])] if "width" in r else [2, 4]):
            records.append({"date": r["date"], "variant": r["family"], "width": width,
                            "status": "no_signal" if r["status"] == "valid_no_setup"
                            else r["status"]})
    return records


def validate_cash_and_clock(row: dict) -> None:
    """Check the journal against an independent cash-flow equation and clock."""
    from tools.research_studies.xsp_independent.common import session_end

    signal, entry, exit_time = (pd.Timestamp(row[k]) for k in ("signal_ts", "entry_ts", "exit_ts"))
    cutoff = session_end(row["date"]) - pd.Timedelta(minutes=15)
    target = min(entry + pd.Timedelta(minutes=60), cutoff)
    assert pd.Timedelta(0) < entry - signal <= pd.Timedelta(minutes=2), row
    assert entry < exit_time <= cutoff, row
    assert target <= exit_time <= target + pd.Timedelta(minutes=2), row
    assert 0 < row["entry_ask"] < row["width"], row
    entry_cash = -100 * row["entry_ask"] - 4 * .65
    exit_cash = 100 * row["liquidation_bid"] - 4 * .65
    expected = entry_cash + exit_cash
    assert np.isclose(row["pnl_marketable"], expected, atol=1e-8), row
    assert np.isclose(row["pnl_stressed"], expected - 10, atol=1e-8), row
    assert np.isclose(row["initial_risk"], 100 * row["entry_ask"] + 2.6, atol=1e-8), row
    assert np.isclose(row["pnl_mark"], 100 * (row["exit_mark"] - row["entry_mark"]) - 5.2,
                      atol=1e-8), row


def cell_metrics(rows: list[dict], split: str) -> dict:
    completed = sorted((r for r in rows if r["status"] == "completed"), key=lambda r: r["date"])
    x = np.array([r["pnl_stressed"] for r in completed])
    wins, losses = x[x > 0], x[x < 0]
    equity = np.r_[0., x.cumsum()]
    months = sorted({r["date"][:7] for r in rows})
    return {"completed": len(completed), "valid_no_signal": sum(r["status"] == "no_signal" for r in rows),
            "excluded": sum(r["status"] not in ("completed", "no_signal") for r in rows),
            "midpoint_net": sum(r["pnl_mark"] for r in completed),
            "marketable_net": sum(r["pnl_marketable"] for r in completed),
            "stressed_net": float(x.sum()), "stressed_expectancy": float(x.mean()) if len(x) else None,
            "win_rate": float((x > 0).mean()) if len(x) else None,
            "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
            "average_win": float(wins.mean()) if len(wins) else None,
            "average_loss": float(losses.mean()) if len(losses) else None,
            "top3_positive_wins_removed_stressed": float(x.sum() - np.sort(wins)[-3:].sum()),
            "drawdown_trade_close_stressed": float((np.maximum.accumulate(equity) - equity).max()),
            "first_half_stressed": sum(r["pnl_stressed"] for r in completed if r["date"] < split),
            "second_half_stressed": sum(r["pnl_stressed"] for r in completed if r["date"] >= split),
            "monthly_stressed": {m: sum(r["pnl_stressed"] for r in completed if r["date"].startswith(m))
                                 for m in months},
            "mean_initial_risk": float(np.mean([r["initial_risk"] for r in completed])) if completed else None,
            "mean_stressed_r": float(np.mean([r["pnl_stressed"] / (r["initial_risk"] + 5)
                                              for r in completed])) if completed else None,
            "spread_drag": sum(r["pnl_mark"] - r["pnl_marketable"] for r in completed),
            "assumed_roundtrip_fees": 5.2 * len(completed), "additional_stress_drag": 10 * len(completed),
            "negative_liquidation_count": sum(r["liquidation_bid"] < 0 for r in completed)}


def paired_metrics(candidate: list[dict], benchmark: list[dict]) -> dict:
    a = {r["date"]: r for r in candidate if r["status"] in ("completed", "no_signal")}
    b = {r["date"]: r for r in benchmark if r["status"] == "completed"}
    dates = sorted(a.keys() & b.keys())
    diffs = [a[d].get("pnl_stressed", 0) - b[d]["pnl_stressed"] for d in dates]
    return {"eligible_days": len(dates), "candidate_no_signal_days": sum(a[d]["status"] == "no_signal" for d in dates),
            "stressed_candidate": sum(a[d].get("pnl_stressed", 0) for d in dates),
            "stressed_benchmark": sum(b[d]["pnl_stressed"] for d in dates),
            "stressed_difference": sum(diffs), "excluded_days_are_not_zero": True}


def check_raw_prices(rows: list[dict]) -> list[dict]:
    """First/last completed trade in every cell, recomputed directly from raw legs."""
    selected = []
    for key in sorted({(r["variant"], r["width"]) for r in rows}):
        cell = sorted((r for r in rows if (r["variant"], r["width"]) == key
                       and r["status"] == "completed"), key=lambda r: r["date"])
        if cell:
            selected.extend(cell[:1] + cell[-1:])
    checks = []
    for day in sorted({r["date"] for r in selected}):
        raw = pd.read_parquet(ROOT / f"data/thetadata/xsp_0dte/quote_1m/2026/{day}.parquet")
        for row in (r for r in selected if r["date"] == day):
            result = {"date": day, "variant": row["variant"], "width": row["width"]}
            for phase, stamp, saved in (("entry", row["entry_ts"], row["entry_ask"]),
                                         ("exit", row["exit_ts"], row["liquidation_bid"])):
                snap = raw[(raw.timestamp == pd.Timestamp(stamp)) & (raw.right == row["right"])]
                value = 0.
                for strike, quantity in ((row["center"] - row["width"], 1), (row["center"], -2),
                                         (row["center"] + row["width"], 1)):
                    leg = snap[snap.strike == strike]
                    assert len(leg) == 1, row
                    leg = leg.iloc[0]
                    side = "ask" if (phase == "entry") == (quantity > 0) else "bid"
                    assert leg[side + "_size"] >= abs(quantity), row
                    assert 0 <= leg.bid <= leg.ask and leg.ask > 0, row
                    value += quantity * leg[side]
                assert np.isclose(value, saved, atol=1e-8), (row, phase, value)
                result[phase + "_recomputed"] = value
            checks.append(result)
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reversion-run", type=Path, required=True)
    parser.add_argument("--trend-run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    rows = load_records(args.reversion_run, args.trend_run)
    keys = [(r["date"], r["variant"], r["width"]) for r in rows]
    assert len(keys) == len(set(keys)), "duplicate session/cell records"
    complete = [r for r in rows if r["status"] == "completed"]
    for row in complete:
        validate_cash_and_clock(row)
    days = sorted({r["date"] for r in rows})
    split = days[len(days) // 2]
    cells = {}
    for variant, width in sorted({(r["variant"], r["width"]) for r in rows}):
        selected = [r for r in rows if r["variant"] == variant and r["width"] == width]
        metrics = cell_metrics(selected, split)
        if variant in BASELINES:
            bench = [r for r in rows if r["variant"] == BASELINES[variant] and r["width"] == width]
            metrics["paired_benchmark"] = paired_metrics(selected, bench)
            metrics["gates"] = {
                "stressed_positive": metrics["stressed_net"] > 0,
                "top3_removed_positive": metrics["top3_positive_wins_removed_stressed"] > 0,
                "both_halves_positive": metrics["first_half_stressed"] > 0 and metrics["second_half_stressed"] > 0,
                "beats_time_benchmark": metrics["paired_benchmark"]["stressed_difference"] > 0}
            metrics["interesting_lead"] = all(metrics["gates"].values())
        cells[f"{variant}/w{width}"] = metrics
    raw_checks = check_raw_prices(rows)
    result = {"decision": "retrospective exploratory review; no promotion", "archive_sessions": len(days),
              "split_date": split, "primary_cells": 8, "cash_clock_rows_checked": len(complete),
              "raw_price_trades_checked": len(raw_checks), "cells": cells,
              "interesting_leads": [k for k, v in cells.items() if v.get("interesting_lead")],
              "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
                  args.reversion_run / "journal.jsonl", args.trend_run / "journal.csv",
                  args.trend_run / "session-status.jsonl")},
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.out / "review.json").write_text(json.dumps(result, indent=2))
    (args.out / "raw-price-checks.json").write_text(json.dumps(raw_checks, indent=2))
    pd.DataFrame(rows).to_csv(args.out / "normalized-journal.csv", index=False)
    print(json.dumps({"checks": len(complete), "raw_trade_checks": len(raw_checks),
                      "interesting_leads": result["interesting_leads"],
                      "primary": {k: {x: v[x] for x in ("completed", "midpoint_net", "marketable_net", "stressed_net", "gates")}
                                  for k, v in cells.items() if "gates" in v}}, indent=2))


if __name__ == "__main__":
    main()
