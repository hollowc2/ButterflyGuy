"""Date extension of the frozen Batman matrix; research inputs and outputs only."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import shutil
import subprocess
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from butterfly_guy.research.thetadata import FILE_TZ, MINUTE_FILE_ORIGIN, STALE_RUN
from tools.research_studies.xsp_independent import batman
from tools.research_studies.xsp_independent.common import calendar, load_session, session_end
from tools.research_studies.xsp_independent.mean_reversion import digest, write_new
from tools.research_studies.xsp_independent.quiet_flies import (
    SUPPORT,
    features,
    metrics,
    spx_minutes,
)
from tools.research_studies.xsp_independent.settlement_data import SOURCE_TYPE

ROOT = batman.ROOT
START, END, SPLIT = "2022-01-03", "2026-09-28", "2024-07-01"
ORIGINAL = ROOT / "reports/research/xsp-batman-2026-11-12/run-01"
OWNER = ROOT / "data/spx_1min.csv"


def reference(path: Path) -> str:
    """Canonical repo paths stay relative; external reproduction roots stay absolute."""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def rules() -> dict:
    return {**batman.RULES,
            "period_inclusive_et": [START, END],
            "utc_session_bounds": "DST-aware 09:31 ET through actual calendar close exclusive, inherited loader; published early-close calendar covers 2022 onward.",
            "prior_inspection": "Owner explicitly requested wider dates after rejecting the original eight cells. All2026 Batman outcomes known. 2022-2025 SPX minute files and dates previously used in other SPX research; 2024Jul-2026Mar spent SPX holdout. New XSP Batman outcomes not inspected before this freeze. No untouched independent holdout claimed.",
            "quiet_baseline": "Quiet iron is outside this follow-up. Preserve original report and policies; compare the eight Batman cells to their exact 2026 original rows.",
            "budget": "Exactly the original8 Batman cells, evaluated on a larger fixed date window. No new geometries, gates, widths, costs or exits; no outcome-led expansion.",
            "signal_sources": "2022-2025: owner SPX minute CSV, original third-party provider unknown, America/Chicago BAR ENDS. Map close at end to start=end-1min so availability remains start+1min; /10 proxy. 2026: unchanged local_support_v1 recorded SPX tick last per minute, no substitution on missing dates. Source-separated results required. Neither is native XSP.",
            "owner_quality": f"Finite positive and internally consistent OHLC required. Duplicates fail closed. Same documented STALE_RUN={STALE_RUN}: after30 consecutive unchanged full OHLC comparisons within session, quarantine signal observations from the detection minute's availability through end of day, never retroactively exclude earlier entries. First29 repeats may remain undetected. No interpolation. Preserve all detected times, including post-entry failures that cause the original settlement fallback. Invalid OHLC starts same causal quarantine. This differs deliberately from canonical whole-day stale exclusions, which would use future quality to admit entries.",
            "settlement_provenance": "Preserve native Cboe W/S/M historical JSON for2022-2025. Exact trading_symbol=XSP AND settlement_symbol=XSP; duplicate/conflicting values fail closed. Reuse hashed2026 native CSV/receipt unchanged. Published cash terminal only; missing settlement never zero or retrospective entry exclusion.",
            "evaluation": f"Original net/stress/R/top3/DD metrics; monthly, yearly and source cohorts. Fixed chronological split {SPLIT} (existing archive boundary), not median accepted trade. Compare movement/unconditional on matched valid dates; compare identical2026 rows as a strict reproduction check. Prior2026 May15 split retained through original report. All retrospective development.",
            "decision": "Same numeric screen: complete terminal cohort, stressed total>0, both fixed halves>0, top3removed>0, and movement participation improves unconditional on matched valid dates. Failure=>reject exact policy; unresolved outcomes=>insufficient evidence. Passing historical screen=>refine only, no promotion/activation from this extension."}


def owner_minutes(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Causal quarantine, retaining all pre-detection observations and admissions."""
    x = raw.copy()
    end = pd.to_datetime(x.ts, format="%Y-%m-%d %H:%M:%S").dt.tz_localize(FILE_TZ).dt.tz_convert("America/New_York")
    hm = end.dt.hour*60 + end.dt.minute
    keep = (hm >= 9*60+31) & (hm <= 16*60)
    x, end = x.loc[keep].copy(), end.loc[keep]
    if end.duplicated().any() or not end.is_monotonic_increasing:
        raise ValueError("Owner signal timestamps duplicate or unordered")
    x["date"] = end.dt.strftime("%Y-%m-%d").to_numpy()
    x["available_time"] = end.to_numpy()
    ohlc = x[["open", "high", "low", "close"]].astype(float)
    valid = (np.isfinite(ohlc).all(axis=1) & (ohlc > 0).all(axis=1)
             & (ohlc.high >= ohlc[["open", "close", "low"]].max(axis=1))
             & (ohlc.low <= ohlc[["open", "close", "high"]].min(axis=1)))
    same = (ohlc == ohlc.groupby(x.date).shift()).all(axis=1)
    runs = same.groupby([x.date, (~same).cumsum()]).cumsum()
    bad_now = (~valid) | (runs >= STALE_RUN)
    quarantined = bad_now.groupby(x.date).cummax()
    events = []
    for day, g in x.loc[bad_now].groupby("date", sort=True):
        first = g.index[0]
        events.append({"date": day, "known_at": x.loc[first, "available_time"].isoformat(),
                       "reason": "invalid_ohlc" if not valid.loc[first] else "unchanged_ohlc_run",
                       "consecutive_same_comparisons": int(runs.loc[first])})
    result = pd.DataFrame({"timestamp": pd.DatetimeIndex(x.available_time)-pd.Timedelta(minutes=1),
                           "forward_proxy": x.close.to_numpy(dtype=float)/10,
                           "date": x.date.to_numpy()})
    return result.loc[~quarantined.to_numpy()].reset_index(drop=True), events


def native_values(documents: dict[str, list[dict]], dates: set[str]) -> list[dict]:
    """No daily-SPX scaling, rounding or proxy substitution."""
    found = {}
    for url, records in documents.items():
        seen = set()
        for record in records:
            if record.get("trading_symbol") != "XSP" or record.get("settlement_symbol") != "XSP":
                continue
            day = record["expiration_date"]
            if day not in dates:
                continue
            if day in seen:
                raise ValueError("Duplicate native instrument/date within source")
            seen.add(day)
            value = Decimal(str(record["settlement_value"]))
            if not value.is_finite() or value <= 0:
                raise ValueError("Invalid native XSP settlement")
            if day in found and found[day][0] != value:
                raise ValueError("Conflicting native XSP settlements")
            found.setdefault(day, (value, []))[1].append(url)
    return [{"date": d, "settlement": str(found[d][0]) if d in found else None,
             "source_type": SOURCE_TYPE if d in found else "missing_native_settlement",
             "source_url": "|".join(found[d][1]) if d in found else None} for d in sorted(dates)]


def acquire(out: Path) -> None:
    """Only public historical settlement downloads, append-only paths."""
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    receipts = []
    for year in range(2022, 2026):
        for category in ("W", "S", "M"):
            path = raw / f"cboe-{category}-{year}.json"
            url = f"https://www.cboe.com/index_settlement_values/get_sv_data/{category}/{year}/"
            if not path.exists():
                response = httpx.get(url, timeout=45, follow_redirects=True)
                response.raise_for_status()
                content = response.content
                if not isinstance(json.loads(content).get("data"), list):
                    raise ValueError("Unexpected public settlement response")
                with path.open("xb") as handle:
                    handle.write(content)
            records = json.loads(path.read_text())["data"]
            receipts.append({"path": reference(path), "sha256": digest(path),
                             "url": url, "rows": len(records),
                             "retrieved_at_utc": dt.datetime.fromtimestamp(path.stat().st_mtime, dt.UTC).isoformat()})
            print(f"Preserved {category}/{year}: {len(records)} source rows", flush=True)
    write_new(out / "acquisition-manifest.json", {"created": dt.datetime.now(dt.UTC), "documents": receipts})


def prepare(out: Path, acquisition: Path) -> None:
    """Signal and terminal coverage only; never evaluate a new strategy outcome."""
    out.mkdir(parents=True, exist_ok=False)
    paths = [p for p in sorted(batman.QUOTES.rglob("*.parquet")) if START <= p.stem <= END]
    receipts = json.loads((acquisition / "acquisition-manifest.json").read_text())
    documents = {}
    for r in receipts["documents"]:
        path = ROOT / r["path"]
        if digest(path) != r["sha256"]:
            raise ValueError("Acquired source changed")
        documents[r["url"]] = json.loads(path.read_text(), parse_float=Decimal)["data"]
    old = pd.read_csv(batman.SETTLEMENTS)
    old_receipt = json.loads(batman.SETTLEMENTS.with_name("native-manifest.json").read_text())
    if old_receipt["files"][batman.SETTLEMENTS.name] != digest(batman.SETTLEMENTS):
        raise ValueError("Original native settlement changed")
    native = native_values(documents, {p.stem for p in paths if p.stem[:4] != "2026"})
    native += old[["date", "settlement", "source_type", "source_url"]].to_dict("records")
    settlements = pd.DataFrame(native).sort_values("date")
    if settlements.date.duplicated().any():
        raise ValueError("Duplicate terminal dates")
    settlements.to_csv(out / "settlements-native.csv", index=False, mode="x")
    raw = pd.read_csv(OWNER)
    raw = raw[(raw.ts >= START) & (raw.ts < "2026")].reset_index(drop=True)
    owner, events = owner_minutes(raw)
    recorded = spx_minutes(pd.read_parquet(SUPPORT / "spot_ticks.parquet"))
    recorded["date"] = recorded.timestamp.dt.strftime("%Y-%m-%d")
    owner["source"] = "owner_spx_unknown_provider"
    recorded["source"] = "recorded_spx_local_support_v1"
    combined = pd.concat([owner, recorded]).sort_values("timestamp").reset_index(drop=True)
    if combined.timestamp.duplicated().any():
        raise ValueError("Signal sources overlap")
    combined.to_parquet(out / "signal-minutes.parquet", index=False)
    batman.write_rows(out / "signal-quarantine.jsonl", events)
    groups = {day: g for day, g in combined.groupby("date", sort=False)}
    sessions = []
    for i, path in enumerate(paths):
        day = dt.date.fromisoformat(path.stem)
        # Read only the signal snapshot, not future option outcomes.
        when = pd.Timestamp(f"{day} 10:29", tz="America/New_York")
        snap = pd.read_parquet(path, filters=[("timestamp", "==", when)])
        p = groups.get(str(day), combined.iloc[:0])
        f = features(snap, p, day)
        sessions.append({"date": str(day), "path": str(path.relative_to(ROOT)),
                         "sha256": digest(path), "raw_rows": pq.ParquetFile(path).metadata.num_rows,
                         "feature_status": f["status"], "signal_minutes": len(p),
                         "source": "recorded_spx_local_support_v1" if day.year == 2026 else "owner_spx_unknown_provider",
                         "scheduled_close": session_end(day).isoformat()})
        if i % 100 == 0:
            print(f"Coverage {i+1}/{len(paths)} {day}", flush=True)
    inputs = [OWNER, SUPPORT / "spot_ticks.parquet", SUPPORT / "manifest.json", batman.SETTLEMENTS,
              batman.SETTLEMENTS.with_name("native-manifest.json"), calendar().path,
              acquisition / "acquisition-manifest.json"]
    hashes = {reference(p): digest(p) for p in inputs}
    hashes.update({r["path"]: r["sha256"] for r in receipts["documents"]})
    write_new(out / "coverage.json", {
        "created_utc": dt.datetime.now(dt.UTC), "period": [START, END],
        "sessions": sessions, "calendar": calendar().meta(), "input_hashes": hashes,
        "by_year": dict(Counter(p.stem[:4] for p in paths)),
        "feature_statuses": dict(Counter(s["feature_status"] for s in sessions)),
        "missing_settlements": settlements.loc[settlements.settlement.isna(), "date"].tolist(),
        "signal_quarantines": events, "owner_origin": MINUTE_FILE_ORIGIN,
        "prepared_hashes": {p.name: digest(p) for p in (out / "signal-minutes.parquet", out / "settlements-native.csv", out / "signal-quarantine.jsonl")},
        "prior_inspection": rules()["prior_inspection"], "source_policy": rules()["signal_sources"],
        "quality_policy": rules()["owner_quality"]})
    print(json.dumps({"sessions": len(sessions), "by_year": dict(Counter(p.stem[:4] for p in paths)),
                      "features": dict(Counter(s["feature_status"] for s in sessions)),
                      "missing_settlements": int(settlements.settlement.isna().sum()),
                      "quarantined_sessions": len(events)}, indent=2))


def freeze(out: Path, prepared: Path) -> None:
    out.mkdir(parents=True, exist_ok=False)
    write_new(out / "specification.json", {"frozen_at_utc": dt.datetime.now(dt.UTC), "rules": rules(),
              "cells": ["_".join(c) for c in batman.CELLS], "coverage_sha256": digest(prepared / "coverage.json"),
              "prepared": reference(prepared), "parent_spec_sha256": digest(ORIGINAL / "specification.json")})


def summarize(rows: list[dict]) -> dict:
    cells = {}
    for cell in sorted({r["cell"] for r in rows}):
        selected = [r for r in rows if r["cell"] == cell]
        m = metrics(selected)
        m["halves"] = {name: metrics([r for r in selected if (r["date"] < SPLIT) == first])
                       for name, first in (("first", True), ("second", False))}
        for label, prefix in (("yearly", 4), ("monthly", 7)):
            m[label] = {key: metrics([r for r in selected if r["date"][:prefix] == key])
                        for key in sorted({r["date"][:prefix] for r in selected})}
        m["source_cohorts"] = {key: metrics([r for r in selected if r["source"] == key])
                                for key in sorted({r["source"] for r in selected})}
        m["terminal_reasons"] = dict(Counter(r["reason"] for r in selected if r["status"] == "completed"))
        complete = [r for r in selected if r["status"] == "completed"]
        known = [r for r in complete if r["reach_prefix_complete"]]
        m["reach"] = {"complete_paths": len(known), "unknown_paths": len(complete)-len(known),
                       "zone_hits": sum(r["zone_reach"] for r in known),
                       "drift_side_hits": sum(r["drift_side_zone_reach"] for r in known)}
        m["expiry_possible"] = sum(r["expiry_peak_net"] > 0 for r in complete)
        baseline = cell.replace("_movement_", "_unconditional_")
        m["vs_unconditional_participation"] = batman.paired(selected, [r for r in rows if r["cell"] == baseline], True)
        passed = (m.get("stressed", 0) > 0 and m.get("top3_removed", 0) > 0
                  and all(h.get("stressed", 0) > 0 for h in m["halves"].values())
                  and ("_movement_" not in cell or m["vs_unconditional_participation"]["difference"] > 0))
        unresolved = any(r["status"].startswith("unresolved") for r in selected)
        pending = [r for r in selected if r["status"] == "unresolved_settlement"]
        m["accepted_entries"] = len(complete) + len(pending)
        m["unresolved_entries"] = len(pending)
        m["unresolved_dates"] = [r["date"] for r in pending]
        # Contract-payoff bounds, not substituted terminal values or zero outcomes.
        m["full_cohort_pnl_bounds"] = [m.get("stressed", 0) + sum(r["unresolved_pnl_bounds"][i] for r in pending)
                                        for i in (0, 1)]
        m["decision"] = "insufficient evidence" if unresolved or not m["trades"] else "refine" if passed else "reject"
        if complete:
            m["max_initial_risk"] = max(r["initial_risk"] for r in complete)
            m["spread_drag"] = m["midpoint"] - m["net"]
        cells[cell] = m
    return {"cells": cells, "split_date": SPLIT, "period": [START, END],
            "decision": "refine" if any(m["decision"] == "refine" for m in cells.values()) else
                        "insufficient evidence" if any(m["decision"] == "insufficient evidence" for m in cells.values()) else "reject",
            "interpretation": "Eight correlated date extensions; retrospective, source-qualified; no activation or paper-trade promotion. DD at terminal outcome once/session."}


def run(out: Path) -> None:
    spec = json.loads((out / "specification.json").read_text())
    if spec["rules"] != rules():
        raise ValueError("Frozen extension rules changed")
    prepared = ROOT / spec["prepared"]
    if digest(prepared / "coverage.json") != spec["coverage_sha256"]:
        raise ValueError("Frozen coverage changed")
    coverage = json.loads((prepared / "coverage.json").read_text())
    for name, expected in coverage["input_hashes"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"Input changed: {name}")
    for name, expected in coverage["prepared_hashes"].items():
        if digest(prepared / name) != expected:
            raise ValueError(f"Prepared input changed: {name}")
    sources = sorted(Path(__file__).parent.glob("*.py")) + [ROOT / "src/butterfly_guy/research/thetadata.py", calendar().path]
    manifest = {"started_utc": dt.datetime.now(dt.UTC), "command": sys.argv,
                "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
                "source_hashes": {str(p.relative_to(ROOT)): digest(p) for p in sources},
                "spec_sha256": digest(out / "specification.json"), "coverage_sha256": spec["coverage_sha256"],
                "versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__}}
    write_new(out / "manifest.json", manifest)
    for p in sources:
        dest = out / "source" / p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    (out / "initial-working-tree.patch").write_bytes(subprocess.check_output(["git", "diff", "--no-ext-diff"]))
    signals = pd.read_parquet(prepared / "signal-minutes.parquet")
    groups = {d: g for d, g in signals.groupby("date", sort=False)}
    native = pd.read_csv(prepared / "settlements-native.csv")
    terminals = native.set_index("date").settlement.dropna().to_dict()
    rows, feature_rows = [], []
    parent = {(r["date"], r["cell"]): r for r in batman.read_rows(ORIGINAL / "journal.jsonl") if not r["cell"].startswith("prior_")}
    overlap_checks = 0
    # Append every date immediately; interrupted evidence is retained, not overwritten.
    with (out / "journal.jsonl").open("x") as journal:
        for i, receipt in enumerate(coverage["sessions"]):
            path = ROOT / receipt["path"]
            if digest(path) != receipt["sha256"]:
                raise ValueError("Quote input changed")
            day = dt.date.fromisoformat(receipt["date"])
            q = load_session(path)
            p = groups.get(str(day), signals.iloc[:0])
            f = features(q, p, day)
            feature_rows.append({"date": str(day), "source": receipt["source"], **f})
            # Retain signal universe, and every quote for every required contract.
            # Unrelated strikes cannot affect component fills; regression checks below.
            if f["status"] == "covered":
                signal_stamp = f["signal_time"] - pd.Timedelta(minutes=1)
                strikes = np.sort(q.loc[q.timestamp == signal_stamp, "strike"].unique())
                needed = set()
                for geometry in ("body", "all_strikes"):
                    centers = batman.select_centers(f, strikes, geometry)
                    if centers:
                        needed.update((right, strike) for pack in batman.packages(centers) for right, strike, _ in pack)
                mask = pd.MultiIndex.from_frame(q[["right", "strike"]]).isin(needed)
                q = q[(q.timestamp == signal_stamp) | mask]
            for geometry, gate, policy in batman.CELLS:
                r = batman.simulate(q, p, f, day, geometry, gate, policy, terminals.get(str(day)))
                # Serialized original and new core rows must match bit-for-bit.
                if day.year == 2026:
                    expected = parent[str(day), r["cell"]]
                    actual = json.loads(json.dumps(r, default=str, allow_nan=False))
                    if actual != expected:
                        raise AssertionError(f"2026 regression: {day} {r['cell']}")
                    overlap_checks += 1
                r["source"] = receipt["source"]
                if r["status"] == "unresolved_settlement":
                    debit = r["entry_debit"]
                    r["known_initial_risk"] = 100*debit + 15.20
                    peak = max(batman.payoff(r["centers"], center) for center in r["centers"])
                    r["unresolved_pnl_bounds"] = [-100*debit-15.20, 100*(peak-debit)-15.20]
                rows.append(r)
                journal.write(json.dumps(r, default=str, allow_nan=False) + "\n")
            journal.flush()
            if i % 50 == 0:
                print(f"Replay {i+1}/{len(coverage['sessions'])} {day}", flush=True)
    batman.write_rows(out / "features.jsonl", feature_rows)
    pd.DataFrame(rows).to_csv(out / "journal.csv", index=False, mode="x")
    result = summarize(rows)
    result["original_2026_rows_reproduced_exactly"] = overlap_checks
    write_new(out / "summary.json", result)
    write_new(out / "decision.json", {"decision": result["decision"], "cells": {k: m["decision"] for k, m in result["cells"].items()},
              "scope": "Exact8 policies, expanded dates, qualified historical signal source; no runtime change or activation"})
    manifest["finished_utc"] = dt.datetime.now(dt.UTC)
    write_new(out / "completed-manifest.json", manifest)
    print(json.dumps({k: {n: m.get(n) for n in ("trades", "stressed", "top3_removed", "decision")}
                      for k, m in result["cells"].items()}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("acquire", "prepare", "freeze", "run"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--acquisition", type=Path)
    parser.add_argument("--prepared", type=Path)
    args = parser.parse_args()
    args.out = args.out.resolve()
    if args.acquisition is not None:
        args.acquisition = args.acquisition.resolve()
    if args.prepared is not None:
        args.prepared = args.prepared.resolve()
    if args.action == "acquire":
        acquire(args.out)
    elif args.action == "prepare":
        if args.acquisition is None:
            parser.error("prepare requires --acquisition")
        prepare(args.out, args.acquisition)
    elif args.action == "freeze":
        if args.prepared is None:
            parser.error("freeze requires --prepared")
        freeze(args.out, args.prepared)
    else:
        run(args.out)


if __name__ == "__main__":
    main()
