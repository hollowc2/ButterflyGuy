"""Retrospective completion audit of frozen MR2 width4 XSP butterfly lifecycles.

Every accepted entry gets a terminal outcome. Missing first-event evidence locks
native settlement irrevocably; it never restarts a search after quotes recover.
No strategy, order, service, or raw-data changes are performed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = ROOT / "reports/research/xsp-realization-2026-11-11/realization/run-01"
NATIVE = ROOT / "reports/research/xsp-realization-2026-11-11/settlement/settlements-native.csv"
OUT = ROOT / "reports/research/xsp-fallback-2026-11-12/replay/run-01"
POLICIES = ("baseline_60m", "center_cross", "net_profit_25pct", "settlement")
ENTRY_FIELDS = ("date", "family", "width", "center", "right", "entry_time", "entry_ask",
                "entry_mark", "initial_risk_dollars", "stressed_initial_risk_dollars")
FINANCE_FIELDS = ("exit_time", "marketable_net", "stressed_net", "midpoint_net",
                  "marketable_r", "stressed_r", "closing_fee_dollars", "closing_stress_dollars",
                  "exposure_minutes", "liquidation_bid", "exit_mark", "settlement",
                  "settlement_source", "settlement_intrinsic", "exit_reason")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def new_json(path: Path, value: object) -> None:
    with path.open("x") as f:
        json.dump(value, f, indent=2, default=str, allow_nan=False)
        f.write("\n")


def path_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def load_native(path: Path) -> tuple[dict[str, dict], dict]:
    receipt_path = path.with_name("native-manifest.json")
    receipt = json.loads(receipt_path.read_text())
    kind = "cboe_native_xsp_published_settlement"
    if receipt.get("source_type") != kind or receipt.get("files", {}).get(path.name) != sha(path):
        raise ValueError("Native settlement receipt source/hash mismatch")
    frame = pd.read_csv(path, dtype={"date": str})
    if (not {"date", "settlement", "source_type"}.issubset(frame.columns)
            or frame.date.duplicated().any() or set(frame.source_type) != {kind}
            or not np.isfinite(frame.settlement).all() or not (frame.settlement > 0).all()):
        raise ValueError("Invalid native XSP settlement observations")
    return {r["date"]: r for r in frame.to_dict("records")}, receipt


def fallback_event(trace: dict) -> dict:
    """Recover a causal failure-known time from the frozen first-failure trace.

    A gap is detected on the scheduled minute last usable +3, not at the later
    recovery quote that exposed it offline. A fill has until its inclusive +2min
    deadline (or cutoff) and then fails. These decisions never inspect P&L.
    """
    status = trace["status"]
    entry, cutoff = pd.Timestamp(trace["entry_time"]), pd.Timestamp(trace["cutoff"])
    evidence = {"fallback_reason": status, "original_failure_trace_time": trace.get("gap_time")}
    if status == "excluded_center_anchor_missing":
        when, rule = entry, "exact entry-minute proxy unavailable at entry observation"
    elif status in {"excluded_center_prefix_gap", "excluded_center_terminal_gap",
                    "excluded_profit_prefix_gap", "excluded_profit_terminal_gap"}:
        previous = pd.Timestamp(trace["gap_time"]) - pd.Timedelta(seconds=trace["gap_seconds"])
        when = previous + pd.Timedelta(minutes=3)
        rule = "scheduled minute observation at last usable +3min; first gap strictly >120s"
        evidence["last_usable_observation_time"] = previous
    elif status == "excluded_trigger_exit_quote":
        attempt = pd.Timestamp(trace["trigger_time"])
        when = min(attempt + pd.Timedelta(minutes=2), cutoff)
        rule = "first strictly-later trigger fill window exhausted; no new trigger or retry"
        evidence["fill_attempt_time"] = attempt
    elif status == "excluded_baseline_exit_quote":
        attempt = pd.Timestamp(trace["exit_deadline"])
        when = min(attempt + pd.Timedelta(minutes=2), cutoff)
        rule = "fixed60min scheduled fill window exhausted"
        evidence["fill_attempt_time"] = attempt
    elif status == "excluded_fallback_exit_quote":
        when, rule = cutoff, "scheduled close-minus15min liquidation unavailable at deadline"
    else:
        raise ValueError(f"Unrecognized first-failure status: {status}")
    if not entry <= when <= cutoff:
        raise ValueError("Failure-known time must follow entry and precede scheduled cutoff")
    return {**evidence, "fallback_known_at": when, "fallback_clock_rule": rule,
            "fallback_irrevocable": True}


def settlement_cash(entry: dict, native: dict, expiry: str | pd.Timestamp) -> dict:
    level = float(native["settlement"])
    intrinsic = max(0., entry["width"] - abs(level - entry["center"]))
    net = 100 * (intrinsic - entry["entry_ask"]) - 2.60
    stressed = net - 5.00
    return {"exit_time": expiry, "exit_reason": "native_published_settlement",
            "settlement": level, "settlement_source": native["source_type"],
            "settlement_intrinsic": intrinsic, "marketable_net": net, "stressed_net": stressed,
            "midpoint_net": 100 * (intrinsic - entry["entry_mark"]) - 2.60,
            "marketable_r": net / entry["initial_risk_dollars"],
            "stressed_r": stressed / entry["stressed_initial_risk_dollars"],
            "closing_fee_dollars": 0., "closing_stress_dollars": 0.,
            "exposure_minutes": (pd.Timestamp(expiry) - pd.Timestamp(entry["entry_time"])).total_seconds() / 60}


def complete_trace(entry: dict, trace: dict, native: dict, settlement_trace: dict) -> dict:
    for key in ENTRY_FIELDS:
        if trace[key] != entry[key] or settlement_trace[key] != entry[key]:
            raise ValueError(f"Frozen entry disagreement for {key}")
    if settlement_trace["status"] != "completed":
        raise ValueError("Every audit entry requires an original observed native settlement")
    settled = settlement_cash(entry, native, settlement_trace["exit_time"])
    for key in ("settlement", "settlement_intrinsic", "marketable_net", "stressed_net",
                "midpoint_net", "marketable_r", "stressed_r"):
        if not np.isclose(settled[key], settlement_trace[key], rtol=0, atol=1e-8):
            raise ValueError(f"Original native settlement cashflow mismatch: {key}")
    base = {**entry, "policy": trace["policy"], "status": "completed",
            "original_status": trace["status"], "original_exit_trace": trace,
            "original_trigger_time": trace.get("trigger_time"),
            "original_exit_reason": trace.get("exit_reason"),
            "retrospective_completion_audit": True}
    if trace["status"] == "completed":
        return {**base, **{k: trace[k] for k in FINANCE_FIELDS if k in trace},
                "terminal_mode": "native_settlement" if trace["policy"] == "settlement" else "original_priced_exit",
                "fallback_irrevocable": False, "fallback_reason": None, "fallback_known_at": None}
    return {**base, **fallback_event(trace), **settled, "terminal_mode": "fallback_native_settlement"}


def metrics(rows: list[dict], split: str) -> dict:
    rows = sorted(rows, key=lambda r: r["date"])
    out = {"count": len(rows), "terminal_modes": dict(Counter(r["terminal_mode"] for r in rows)),
           "original_statuses": dict(Counter(r["original_status"] for r in rows)),
           "fallback_reasons": dict(Counter(r["fallback_reason"] for r in rows if r["fallback_irrevocable"])),
           "priced_negative_liquidations": sum(r.get("liquidation_bid", 0) < 0 for r in rows),
           "average_opening_cash_risk": float(np.mean([r["initial_risk_dollars"] for r in rows])),
           "largest_opening_cash_risk": max(r["initial_risk_dollars"] for r in rows),
           "exposure_minutes": float(sum(r["exposure_minutes"] for r in rows)),
           "capital_return": None, "drawdown_resolution": "trade-close dollars; not intraday"}
    for model in ("marketable_net", "stressed_net", "midpoint_net"):
        values = np.array([r[model] for r in rows], dtype=float)
        wins, losses = values[values > 0], values[values < 0]
        equity = np.r_[0., values.cumsum()]
        risk_key = "stressed_initial_risk_dollars" if model == "stressed_net" else "initial_risk_dollars"
        out[model] = {"total": float(values.sum()), "expectancy": float(values.mean()),
                      "win_rate": float((values > 0).mean()),
                      "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
                      "average_win": float(wins.mean()) if len(wins) else None,
                      "average_loss": float(losses.mean()) if len(losses) else None,
                      "worst_trade": float(values.min()), "best_trade": float(values.max()),
                      "expectancy_r": float(np.mean([r[model] / r[risk_key] for r in rows])),
                      "worst_trade_r": float(min(r[model] / r[risk_key] for r in rows)),
                      "top3_removed": float(values.sum() - np.sort(wins)[-3:].sum()),
                      "drawdown_trade_close": float((np.maximum.accumulate(equity) - equity).max()),
                      "monthly": {m: float(sum(r[model] for r in rows if r["date"].startswith(m)))
                                  for m in sorted({r["date"][:7] for r in rows})},
                      "halves": {label: float(sum(r[model] for r in rows if (r["date"] < split) == first))
                                 for label, first in (("first", True), ("second", False))}}
    return out


def paired(rows: list[dict], benchmark: list[dict]) -> dict:
    reference = {r["date"]: r for r in benchmark}
    if {r["date"] for r in rows} != set(reference):
        raise ValueError("Complete-cohort comparisons require identical dates")
    return {model: {"matched_entries": len(rows),
                    "candidate": float(sum(r[model] for r in rows)),
                    "benchmark": float(sum(r[model] for r in benchmark)),
                    "difference": float(sum(r[model] - reference[r["date"]][model] for r in rows))}
            for model in ("marketable_net", "stressed_net", "midpoint_net")}


def freeze(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    new_json(out / "specification.json", {
        "recorded_at": dt.datetime.now(dt.UTC),
        "status": "Retrospective completion audit; prior missingness diagnostics already exposed settlement outcomes; no fresh holdout or preregistration claim",
        "universe": "Exactly105 frozen accepted MR2 width4 entries from realization/run-01/entries.jsonl; no entry, geometry, price, quotequality, or size changes",
        "baseline": "Original60min scheduled component exit; first missing fill through+120s/deadline irrevocably locks native settlement",
        "center": "Original exactentry proxy anchor, first sampledcenter equality/signflip with requiredprefix<=120s, strictlylaterfill<=120s. First requiredmissinganchor/gap/fill locks settlement forever. No trigger:original scheduledcutoff exit else settlement",
        "profit": "Original nominal net25% target and same decisions:100*(bid-entryask)-5.20>=.25*(100*entryask+2.60), nextlaterquote<=120s. Firstheldlegprefixgap or failedfill locks settlement forever; no retry/reactivation. No trigger:cutoffexit else settlement",
        "first_gap_known_at": "Scheduled minute lastusable+3min, first strictly>120s; never timestamp of future recovery quote",
        "failed_fill_known_at": "Inclusive attempt+2min window expiry, capped atscheduledcutoff; missingcutoffquote knownatcutoff",
        "preservation": "All39 previouslypricedcenter and20 previouslypricedtarget results remain exact; full original first-event trace retained alongside completion",
        "settlement": "ExactnativeCSV+auditorreceiptSHAguard, no scaling/proxy/rounding substitution; all105observed. Entryfee2.60andentryadverse5only, no closingfee/stress",
        "priced_costs": "Frozen4contract65c/sideassumption=$5.20roundtrip; adverse$5/transaction=$10roundtrip. Signednegativepricedliquidation retained",
        "benchmarks": "All105 timedbaselinewithsamefallback and all105alwayssettle; everyentrymatched, no missingaszero",
        "evaluation": "Dollars,debitR,worsttrade,top3removed,chronologicalhalvesfromsame185-sessiondatecutpoint,monthly,tradeclosedrawdown. No optimization or expansion"})


def run(out: Path, original: Path, native_path: Path) -> None:
    if not (out / "specification.json").exists():
        raise ValueError("Record specification first")
    entries_path, journal_path = original / "entries.jsonl", original / "journal.jsonl"
    entries = [r for r in read_rows(entries_path) if r["family"] == "MR2" and r["width"] == 4
               and r["status"] == "accepted"]
    if len(entries) != 105 or len({r["date"] for r in entries}) != 105:
        raise ValueError("Audit requires exactly105 unique frozen accepted entries")
    traces = [r for r in read_rows(journal_path) if r["family"] == "MR2" and r["width"] == 4]
    lookup = {(r["date"], r["policy"]): r for r in traces}
    if len(traces) != 420 or len(lookup) != 420:
        raise ValueError("Audit requires four original policy traces per entry")
    if sum(r["policy"] == "center_cross" and r["status"] == "completed" for r in traces) != 39:
        raise ValueError("Frozen39 center results changed")
    if sum(r["policy"] == "net_profit_25pct" and r["status"] == "completed" for r in traces) != 20:
        raise ValueError("Frozen20 target results changed")
    if sum(r["policy"] == "baseline_60m" and r["status"] == "completed" for r in traces) != 101:
        raise ValueError("Frozen101 baseline results changed")
    native, _ = load_native(native_path)
    old_manifest = json.loads((original / "manifest.json").read_text())
    for name, expected in old_manifest["sources"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Original frozen source changed: {name}")
    original_summary = json.loads((original / "summary.json").read_text())
    split = original_summary["split_date"]
    manifest = {"started_at": dt.datetime.now(dt.UTC), "command": sys.argv,
                "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "dirty_status": subprocess.check_output(["git", "status", "--short"], text=True),
                "sources": {str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))},
                "inputs": {path_label(p): sha(p) for p in (
                    entries_path, journal_path, original / "manifest.json", original / "summary.json",
                    native_path, native_path.with_name("native-manifest.json"), out / "specification.json",
                    ROOT / "reports/research/xsp-fallback-2026-11-12/protocol.json")},
                "pandas": pd.__version__, "numpy": np.__version__,
                "cohort": 105, "calendar_sessions": 185, "split_date": split}
    rows = []
    for entry in sorted(entries, key=lambda r: r["date"]):
        for policy in POLICIES:
            rows.append(complete_trace(entry, lookup[(entry["date"], policy)], native[entry["date"]],
                                       lookup[(entry["date"], "settlement")]))
    with (out / "journal.jsonl").open("x") as f:
        for row in rows:
            f.write(json.dumps(row, default=str, allow_nan=False) + "\n")
    flat = [{k: v for k, v in row.items() if k != "original_exit_trace"} for row in rows]
    pd.DataFrame(flat).to_csv(out / "journal.csv", index=False, mode="x")
    groups = {p: [r for r in rows if r["policy"] == p] for p in POLICIES}
    result = {"status": "retrospective completion audit, pending independent review",
              "accepted_entries": 105, "calendar_sessions": 185, "split_date": split,
              "policies": {p: {**metrics(group, split),
                               "original_completed_subset": {
                                   "count": sum(r["original_status"] == "completed" for r in group),
                                   **{model: float(sum(r[model] for r in group if r["original_status"] == "completed"))
                                      for model in ("marketable_net", "stressed_net", "midpoint_net")}},
                               "versus_timed_fallback": paired(group, groups["baseline_60m"]),
                               "versus_always_settle": paired(group, groups["settlement"])}
                           for p, group in groups.items()}}
    new_json(out / "summary.json", result)
    manifest["finished_at"] = dt.datetime.now(dt.UTC)
    manifest["outputs"] = {p.name: sha(p) for p in (
        out / "journal.jsonl", out / "journal.csv", out / "summary.json")}
    new_json(out / "manifest.json", manifest)
    print(json.dumps({p: {"stressed": m["stressed_net"]["total"],
                         "marketable": m["marketable_net"]["total"], "modes": m["terminal_modes"]}
                      for p, m in result["policies"].items()}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--original", type=Path, default=ORIGINAL)
    parser.add_argument("--native", type=Path, default=NATIVE)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        freeze(args.out)
    if args.run:
        run(args.out, args.original, args.native)


if __name__ == "__main__":
    main()
