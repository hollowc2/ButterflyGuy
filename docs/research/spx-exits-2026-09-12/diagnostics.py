"""Produce ledger, paired sensitivity, winner, and parity diagnostics offline."""

import csv
import json
from collections import Counter

from replay import ROOT, metrics, path_for, timestamp, write_csv


def main():
    ex = [json.loads(line) for line in (ROOT / "raw/export.jsonl").open()]
    trades = ex[1]["rows"]
    ts = {t["id"]: t for t in trades}
    records = list(csv.DictReader((ROOT / "results/trade_results.csv").open()))
    for r in records:
        r["id"] = int(r["id"])
        for k in ("pnl", "minutes", "exit_price"):
            if r.get(k):
                r[k] = float(r[k])
    ledger = []
    for t in trades:
        ledger.append(
            {
                **t,
                "pnl": float(t["pnl"]) * 100 * int(t["quantity"]),
                "minutes": (timestamp(t["exit_time"]) - timestamp(t["entry_time"])).total_seconds()
                / 60,
            }
        )
    ledger_summary = []
    for cohort in ["all", "mark_v1"] + sorted({t["trade_date"][:7] for t in trades}):
        rs = [
            r
            for r in ledger
            if cohort == "all"
            or (cohort == "mark_v1" and r["fill_model"] == "mark_v1")
            or r["trade_date"].startswith(cohort)
        ]
        ledger_summary.append({"cohort": cohort, **metrics(rs)})
    write_csv("recorded_trades.csv", ledger)
    write_csv("recorded_summary.csv", ledger_summary)
    biggest = sorted(ledger, key=lambda r: r["pnl"], reverse=True)[:10]
    six = [
        t
        for t in trades
        if t["fill_model"] == "mark_v1"
        and float(t["pnl"]) < 0
        and float(t["peak_value"]) >= 2 * float(t["entry_price"])
    ]
    focus = []
    for t in biggest + six:
        for r in records:
            if r["id"] == t["id"] and r["stress"] == "mark":
                focus.append(
                    {
                        "classification": "top10_recorded"
                        if t in biggest
                        else "six_doubled_losers",
                        "recorded_pnl": float(ts[t["id"]]["pnl"]) * 100,
                        "recorded_exit_time": t["exit_time"],
                        "recorded_peak_diagnostic_only": t["peak_value"],
                        **r,
                    }
                )
    write_csv("focus_trades.csv", focus)
    attribution = []
    for r in records:
        if (
            r["source"] != "monitor"
            or r["policy"] != "peakvaluetrailer"
            or r["stress"] != "mark"
            or not r.get("signal_mark")
        ):
            continue
        t = ts[r["id"]]
        actual = float(t["exit_mark_at_signal"]) if t["exit_mark_at_signal"] is not None else None
        attribution.append(
            {
                "id": r["id"],
                "date": r["date"],
                "fill_model": r["fill_model"],
                "recorded_signal_mark": actual,
                "replayed_signal_mark": r["signal_mark"],
                "signal_mark_difference": float(r["signal_mark"]) - actual
                if actual is not None
                else None,
                "recorded_fill": t["exit_price"],
                "replayed_fill": r["exit_price"],
                "recorded_ladder_steps": len(json.loads(t["exit_ladder_steps"] or "[]")),
            }
        )
    write_csv("signal_attribution.csv", attribution)
    # Preserve a small chronological trace surrounding each focus-policy exit.
    trace = []
    focus_ids = {t["id"] for t in biggest + six}
    for file, source in [("export.jsonl", "collector"), ("monitor.jsonl", "monitor")]:
        for line in (ROOT / "raw" / file).open():
            q = json.loads(line)
            if q.get("trade_id") not in focus_ids:
                continue
            path, _ = path_for(ts[q["trade_id"]], q["rows"])
            for r in focus:
                if r["source"] != source or r["id"] != q["trade_id"] or r["status"] != "exit":
                    continue
                time = timestamp(r["exit_time"])
                index = min(
                    range(len(path)), key=lambda i: abs((path[i]["time"] - time).total_seconds())
                )
                for point in path[max(0, index - 2) : index + 3]:
                    trace.append(
                        {
                            "source": source,
                            "id": r["id"],
                            "policy": r["policy"],
                            "time": point["time"].isoformat(),
                            "signal": point["time"] == time,
                            "mark": point["mark"],
                            "bid": point["bid"],
                            "ask": point["ask"],
                        }
                    )
    write_csv("focus_quote_windows.csv", trace)
    sensitivity = []
    for source in ("collector", "monitor", "best_available"):
        for stress in sorted({r["stress"] for r in records}):
            selected = [
                r
                for r in records
                if r["source"] == source and r["stress"] == stress and isinstance(r["pnl"], float)
            ]
            ids = {
                p: {r["id"] for r in selected if r["policy"] == p}
                for p in ("peakvaluetrailer", "profitprotector")
            }
            common = ids["peakvaluetrailer"] & ids["profitprotector"]
            for cohort in ("all", "mark_v1"):
                paired = [
                    r
                    for r in selected
                    if r["id"] in common and (cohort == "all" or r["fill_model"] == "mark_v1")
                ]
                base = sorted(
                    [r for r in paired if r["policy"] == "peakvaluetrailer"],
                    key=lambda r: r["pnl"],
                    reverse=True,
                )
                for k in (0, 1, 2, 5):
                    excluded = (
                        {r["id"] for r in base if r["pnl"] > 0}
                        if k >= len(base)
                        else {r["id"] for r in base[:k] if r["pnl"] > 0}
                    )
                    for policy in ids:
                        rs = [
                            r for r in paired if r["policy"] == policy and r["id"] not in excluded
                        ]
                        for fee_case in (
                            "embedded_entry",
                            "legacy_entry_extra_260",
                            "industry_extra_520",
                        ):
                            adjusted = [
                                dict(
                                    r,
                                    pnl=r["pnl"]
                                    - (
                                        2.6
                                        if fee_case == "legacy_entry_extra_260"
                                        and r["fill_model"] != "mark_v1"
                                        else 5.2
                                        if fee_case == "industry_extra_520"
                                        else 0
                                    ),
                                )
                                for r in rs
                            ]
                            sensitivity.append(
                                {
                                    "source": source,
                                    "stress": stress,
                                    "cohort": cohort,
                                    "policy": policy,
                                    "remove_same_baseline_top_n": k,
                                    "removed_ids": ";".join(map(str, sorted(excluded))),
                                    "fee_case": fee_case,
                                    **metrics(adjusted),
                                }
                            )
    write_csv("paired_sensitivity.csv", sensitivity)
    parity = list(csv.DictReader((ROOT / "results/baseline_parity.csv").open()))
    summary = []
    for source in ("collector", "monitor"):
        for cohort in ("all", "mark_v1"):
            rows = [
                r
                for r in parity
                if r["source"] == source and (cohort == "all" or r["fill_model"] == "mark_v1")
            ]
            valid = [r for r in rows if r["pnl_difference"]]
            summary.append(
                {
                    "source": source,
                    "cohort": cohort,
                    "attempted": len(rows),
                    "resolved": len(valid),
                    "exact_pnl": sum(abs(float(r["pnl_difference"])) < 0.01 for r in valid),
                    "material_pnl_over_5": sum(abs(float(r["pnl_difference"])) > 5 for r in valid),
                    "reason_match": sum(r["reason"] == r["recorded_reason"] for r in valid),
                    "time_within_10s": sum(
                        abs(float(r["exit_time_difference_seconds"])) <= 10 for r in valid
                    ),
                    "absolute_pnl_error": sum(abs(float(r["pnl_difference"])) for r in valid),
                    "status_counts": dict(Counter(r["status"] for r in rows)),
                }
            )
    (ROOT / "results/parity_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
