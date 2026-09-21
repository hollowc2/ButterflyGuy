"""All 108 entries, isolated quote sources, unchanged exit trials; offline only."""

import csv
import datetime as dt
import json
import math
import subprocess
import sys
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT / "exit_trials"))
from run_trials import (  # noqa: E402
    ProfitManagementSettings,
    compare,
    path_for,
    replay,
    sha,
    stats,
    timestamp,
    variants,
    write_csv,
)

STRESSES = {
    "mark": (0.0, 0.0),
    "quarter_halfspread_005": (0.25, 0.05),
    "halfspread_005": (0.5, 0.05),
    "crossed_010": (1.0, 0.10),
    "next_quote_halfspread_005": (0.5, 0.05),
}
PRIMARY = ("trail_60", "stop_50", "confirm_5")


def all_stresses(trade, path, settings, fee, seconds):
    """Costs do not alter signals: apply each scenario to one chronological replay."""
    mark = replay(trade, path, settings, fee, confirmation_seconds=seconds)
    if mark["status"] != "exit":
        return {stress: dict(mark) for stress in STRESSES}
    times = [p["time"] for p in path]
    signal_time = timestamp(mark["signal_time"])
    signal_index = bisect_right(times, signal_time) - 1
    assert times[signal_index] == signal_time
    results = {}
    for stress, (fraction, extra) in STRESSES.items():
        index = signal_index + (stress == "next_quote_halfspread_005")
        if index == len(path):
            results[stress] = {"status": "censored_fill_latency"}
            continue
        point = path[index]
        drag = fraction * max(0.0, point["mark"] - point["bid"]) + extra
        price = round(point["mark"] - drag - fee, 2)
        results[stress] = {
            **mark,
            "exit_time": point["time"].isoformat(),
            "exit_price": price,
            "fill_mark": point["mark"], "fill_bid": point["bid"], "fill_ask": point["ask"],
            "pnl": round((price - float(trade["entry_price"])) * 100 * int(trade["quantity"]), 2),
            "minutes": (point["time"] - timestamp(trade["entry_time"])).total_seconds() / 60,
            "exit_drag_dollars": round(drag * 100 * int(trade["quantity"]), 2),
        }
    return results


def select_sources(monitor_records):
    """Select on raw presence only; unusable/nonresolving monitoring still wins."""
    return {record["trade_id"]: "monitor" if record["rows"] else "collector"
            for record in monitor_records}


def assert_prior_result(actual, prior):
    for key, value in actual.items():
        assert key in prior, key
        if isinstance(value, (int, float)):
            assert math.isclose(value, float(prior[key]), rel_tol=0, abs_tol=1e-8), (
                key, value, prior[key])
        else:
            assert value == prior[key], (key, value, prior[key])


def ledger_parity(trade, result):
    recorded_pnl = round(float(trade["pnl"]) * 100 * int(trade["quantity"]), 2)
    row = {"id": trade["id"], "date": trade["trade_date"],
           "fill_model": trade["fill_model"] or "legacy",
           "recorded_pnl": recorded_pnl, "recorded_reason": trade["exit_reason"],
           "recorded_exit": trade["exit_time"], "status": result["status"],
           "resolved": "pnl" in result, "ledger_match": False}
    if "pnl" in result:
        error = result["pnl"] - recorded_pnl
        seconds = (timestamp(result["exit_time"]) - timestamp(trade["exit_time"])).total_seconds()
        same_reason = result["reason"] == trade["exit_reason"]
        row.update(replay_pnl=result["pnl"], replay_reason=result["reason"],
                   replay_exit=result["exit_time"], pnl_error=error,
                   time_error_seconds=seconds, reason_match=same_reason,
                   material_pnl_error=abs(error) > 5,
                   ledger_match=abs(error) < 0.01 and abs(seconds) <= 10 and same_reason)
    return row


def paired_comparison(baseline, candidate, parity):
    result = compare(baseline, candidate)
    paired_ids = set(result["paired_ids"])
    result.update(
        baseline_unresolved_ids=[r["id"] for r in baseline if "pnl" not in r],
        excluded_ids=sorted({r["id"] for r in baseline} - paired_ids),
        paired_baseline_ledger_matches=sum(parity[i]["ledger_match"] for i in paired_ids),
        paired_baseline_material_pnl_errors=sum(
            parity[i].get("material_pnl_error", False) for i in paired_ids),
    )
    n_legacy = sum(r["id"] in paired_ids and r["fill_model"] != "mark_v1" for r in baseline)
    result["paired_legacy_count"] = n_legacy
    for key in ("paired_baseline", "paired_candidate"):
        result[key]["net_extra_legacy_entry_fee"] = round(
            result[key]["net_pnl"] - n_legacy * 2.60, 2)
    return result


def main():
    original_manifest = json.loads((PARENT / "manifest.json").read_text())
    for relative, expected in original_manifest["files"].items():
        assert sha(PARENT / relative) == expected, relative
    for relative, expected in json.loads((PARENT / "source-hashes.json").read_text()).items():
        assert sha(PARENT / "frozen/butterfly_guy" / relative) == expected, relative
    prior_manifest = json.loads((PARENT / "exit_trials/manifest.json").read_text())
    for relative, expected in prior_manifest["input_hashes"].items():
        assert sha(PARENT / relative) == expected, relative
    for relative, expected in prior_manifest["output_hashes"].items():
        assert sha(PARENT / "exit_trials" / relative) == expected, relative
    with (PARENT / "raw/export.jsonl").open() as f:
        raw_baseline = json.loads(next(f))
        trades = json.loads(next(f))["rows"]
        collector = [json.loads(line) for line in f]
    with (PARENT / "raw/monitor.jsonl").open() as f:
        monitor = [json.loads(line) for line in f]
    assert len(trades) == len(collector) == len(monitor) == 108
    trade_map = {t["id"]: t for t in trades}
    assert len(trade_map) == 108 and all(int(t["quantity"]) == 1 for t in trades)
    assert min(t["trade_date"] for t in trades) == "2026-03-17"
    assert max(t["trade_date"] for t in trades) == "2026-09-11"
    source_choices = select_sources(monitor)
    assert set(source_choices) == set(trade_map)
    assert sum(v == "monitor" for v in source_choices.values()) == 64
    base = ProfitManagementSettings(**raw_baseline["effective"]["profit_management"])
    configurations = variants(base)
    # Require identical predeclared settings, including inherited defaults and gap rule.
    config_record = {name: {"profit_management": cfg.model_dump(),
                           "confirmation_seconds": seconds, "confirmation_max_gap_seconds": 10}
                     for name, (cfg, seconds) in configurations.items()}
    assert config_record == json.loads((PARENT / "exit_trials/configs.json").read_text())
    fee = raw_baseline["effective"]["execution"]["paper_commission_per_contract"] * 4 / 100
    original = list(csv.DictReader((PARENT / "results/trade_results.csv").open()))
    original = {(r["source"], int(r["id"]), r["stress"]): r for r in original
                if r["policy"] == "peakvaluetrailer" and r["source"] in ("collector", "monitor")}
    prior_path = PARENT / "exit_trials/results/trade_results.csv"
    previous_trials = list(csv.DictReader(prior_path.open()))
    previous_trials = {(int(r["id"]), r["variant"], r["stress"]): r for r in previous_trials}
    results, coverage, parity = [], [], []
    baseline_checks = previous_checks = 0
    for source, records in (("collector", collector), ("monitor", monitor)):
        assert {r["trade_id"] for r in records} == set(trade_map)
        for number, record in enumerate(records, 1):
            trade = trade_map[record["trade_id"]]
            path, audit = path_for(trade, record["rows"])
            coverage.append({"source": source, "id": trade["id"],
                             "date": trade["trade_date"],
                             "fill_model": trade["fill_model"], **audit})
            for name, (cfg, seconds) in configurations.items():
                outcomes = all_stresses(trade, path, cfg, fee, seconds)
                if name == "baseline":
                    parity.append({"source": source, **ledger_parity(trade, outcomes["mark"])})
                for stress, result in outcomes.items():
                    if name == "baseline":
                        assert_prior_result(result, original[source, trade["id"], stress])
                        baseline_checks += 1
                    if source == "monitor" and trade["fill_model"] == "mark_v1":
                        assert_prior_result(result, previous_trials[trade["id"], name, stress])
                        previous_checks += 1
                    results.append({"source": source, "quote_source": source, "id": trade["id"],
                                    "date": trade["trade_date"], "direction": trade["direction"],
                                    "fill_model": trade["fill_model"] or "legacy",
                                    "variant": name, "stress": stress, **result})
            if number % 20 == 0 or number == 108:
                print(source, number, "/ 108 processed", flush=True)
    assert baseline_checks == 1080 and previous_checks == 1650
    validated = [r for r in parity if r["source"] == "monitor" and r["fill_model"] == "mark_v1"]
    assert len(validated) == 33 and all(r["ledger_match"] for r in validated)
    # This is a fixed source-choice view, not a third independent dataset.
    results += [{**r, "source": "best_available"} for r in results
                if source_choices[r["id"]] == r["source"]]
    parity += [{**r, "source": "best_available"} for r in parity
               if source_choices[r["id"]] == r["source"]]
    assert len(results) == 16200 and len(parity) == 324
    assert len({(r["source"], r["id"], r["variant"], r["stress"]) for r in results}) == 16200
    grouped = defaultdict(list)
    for r in results:
        grouped[r["source"], r["variant"], r["stress"]].append(r)
    comparisons, breakdowns, parity_summaries = [], [], []
    cohorts = {"all_108": lambda r: True,
               "legacy_75": lambda r: r["fill_model"] != "mark_v1",
               "mark_v1_33": lambda r: r["fill_model"] == "mark_v1"}
    for source in ("monitor", "collector", "best_available"):
        source_parity = {r["id"]: r for r in parity if r["source"] == source}
        for cohort, predicate in cohorts.items():
            pr = [r for r in source_parity.values() if predicate(r)]
            parity_summaries.append({
                "source": source, "cohort": cohort, "attempted": len(pr),
                "resolved": sum(r["resolved"] for r in pr),
                "ledger_matches": sum(r["ledger_match"] for r in pr),
                "material_pnl_errors": sum(r.get("material_pnl_error", False) for r in pr),
                "unresolved_ids": [r["id"] for r in pr if not r["resolved"]],
            })
            for name in configurations:
                if name == "baseline":
                    continue
                for stress in STRESSES:
                    b = [r for r in grouped[source, "baseline", stress] if predicate(r)]
                    c = [r for r in grouped[source, name, stress] if predicate(r)]
                    identity = {"source": source, "cohort": cohort,
                                "variant": name, "stress": stress}
                    comparisons.append({**identity, **paired_comparison(b, c, source_parity)})
                    if cohort == "all_108":
                        for dimension in ("month", "direction"):
                            key = (lambda r: r["date"][:7]) if dimension == "month" else (
                                lambda r: r["direction"])
                            for value in sorted({key(r) for r in b}):
                                subset = paired_comparison([r for r in b if key(r) == value],
                                                           [r for r in c if key(r) == value],
                                                           source_parity)
                                breakdowns.append({**identity, "dimension": dimension,
                                                   "value": value, **subset})
    recorded = [{"id": t["id"], "date": t["trade_date"], "direction": t["direction"],
                 "fill_model": t["fill_model"] or "legacy", "exit_time": t["exit_time"],
                 "pnl": round(float(t["pnl"]) * 100 * int(t["quantity"]), 2),
                 "minutes": (timestamp(t["exit_time"]) - timestamp(t["entry_time"])
                             ).total_seconds() / 60, "exit_drag_dollars": 0}
                for t in trades]
    top_ids = {r["id"] for r in sorted(recorded, key=lambda r: r["pnl"], reverse=True)[:10]}
    recorded_map = {r["id"]: r for r in recorded}
    focus = [{**r, "recorded_pnl": recorded_map[r["id"]]["pnl"],
              "baseline_ledger_match": next(p["ledger_match"] for p in parity
                                            if p["source"] == r["source"] and p["id"] == r["id"])}
             for r in results if r["id"] in top_ids and r["stress"] == "mark"]
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    for name, rows in (("trade_results.csv", results), ("coverage.csv", coverage),
                       ("baseline_parity.csv", parity), ("focus_winners.csv", focus),
                       ("recorded_trades.csv", recorded)):
        write_csv(out / name, rows)
    for name, data in (("comparisons.json", comparisons), ("breakdowns.json", breakdowns),
                       ("parity_summary.json", parity_summaries),
                       ("recorded_summary.json", {k: stats([r for r in recorded if pred(r)])
                                                  for k, pred in cohorts.items()})):
        (out / name).write_text(json.dumps(data, indent=2) + "\n")
    (HERE / "configs.json").write_text(json.dumps(config_record, indent=2) + "\n")
    write_csv(out / "source_choices.csv", [{"id": i, "quote_source": source_choices[i]}
                                          for i in sorted(source_choices)])
    manifest = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "range": ["2026-03-17", "2026-09-11"], "trades": 108,
        "provider": original_manifest["provider"],
        "original_acquisition_utc": original_manifest["created_utc"],
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "python": sys.version, "dependency_lock_sha256": sha(PARENT.parents[2] / "uv.lock"),
        "environment_variables": "none required or overridden",
        "command": ".venv/bin/python docs/research/spx-exits-2026-09-12/"
                   "all_history_trials/run_all_history.py",
        "quote_interval": "irregular observations; see per-source coverage.csv",
        "timestamps": "UTC-offset source times; session grouping America/New_York",
        "baseline_scenario_regressions": baseline_checks,
        "prior_mark_v1_trial_regressions": previous_checks,
        "source_choice": "64 monitoring / 44 collector, fixed by raw presence",
        "account_return_sharpe_marked_drawdown": "unavailable",
        "input_hashes": {str(p.relative_to(PARENT)): sha(p) for p in (
            PARENT / "raw/export.jsonl", PARENT / "raw/monitor.jsonl",
            PARENT / "manifest.json", PARENT / "source-hashes.json", PARENT / "replay.py",
            PARENT / "results/trade_results.csv", PARENT / "exit_trials/run_trials.py",
            PARENT / "exit_trials/configs.json", PARENT / "exit_trials/results/trade_results.csv",
            HERE / "PLAN.md", HERE / "run_all_history.py")},
        "output_hashes": {str(p.relative_to(HERE)): sha(p)
                          for p in [HERE / "configs.json", *sorted(out.iterdir())]},
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for r in comparisons:
        if r["cohort"] == "all_108" and r["variant"] in PRIMARY and r["stress"] == "mark":
            print(r["source"], r["variant"], "pairs", r["paired_count"],
                  "baseline", r["paired_baseline"]["net_pnl"],
                  "candidate", r["paired_candidate"]["net_pnl"],
                  "ledger matches", r["paired_baseline_ledger_matches"], flush=True)


if __name__ == "__main__":
    main()
