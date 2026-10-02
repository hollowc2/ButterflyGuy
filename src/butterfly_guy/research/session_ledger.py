"""Offline SPXW session evidence consolidation; never evaluates a strategy or quality gate."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shlex
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from butterfly_guy.core import time_utils
from butterfly_guy.research.dataset import Dataset, sha256_file
from butterfly_guy.research.event_calendar import CALENDAR_PATH, EventCalendar
from butterfly_guy.research.history import session_close
from butterfly_guy.research.holdout import guard

SCHEMA = "spx-session-quality-ledger-1"
NON_EXPIRATION = "non_expiration_before_first_regular_weekday_expiration"
LIMITATIONS = [
    "Quality gates are inherited dataset assessments, not newly computed session passes.",
    "Independent full vendor expiration-list snapshot is unavailable; weekday absences "
    "require the documented eligibility reconciliation, never a blanket weekday rule.",
    "Owner SPX/VIX minute provider is unknown; America/Chicago bar ends; last usable "
    "date 2025-12-09. Recorded supporting observations have separate attribution.",
    "Independent minute-file daily OHLC cross-check was not acquired.",
    "Unchecked supporting fields remain unknown; missing research outcomes are not failures.",
    "Remote continuity, NDX/XSP readiness, backups/restore, scheduling, and broader imports "
    "remain separate follow-ups.",
]


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, indent=1, allow_nan=False) + "\n"


class Evidence:
    """Hash only explicitly selected unprotected payloads and evidence metadata."""

    def __init__(self) -> None:
        self.inputs: dict[str, str] = {}

    def file(self, path: Path, expected: str | None = None) -> str:
        path = path.resolve()
        actual = sha256_file(path)
        if expected is not None and actual != expected:
            raise ValueError(f"changed input {path}: sha256 {actual}, expected {expected}")
        old = self.inputs.get(str(path))
        if old is not None and old != actual:
            raise ValueError(f"input changed during generation: {path}")
        self.inputs[str(path)] = actual
        return actual

    def json(self, path: Path, expected: str | None = None) -> dict:
        self.file(path, expected)
        return json.loads(path.read_text())


def indexed(rows: list[dict], label: str) -> dict[str, dict]:
    out = {}
    for row in rows:
        date = row["date"]
        if date in out:
            raise ValueError(f"duplicate date {date} in {label}")
        out[date] = row
    return out


def gate_status(gates: dict) -> dict:
    return {f"Q{i}": ("unassessed" if f"Q{i}" not in gates else
                       "not_evaluable" if gates[f"Q{i}"] is None else
                       "pass" if gates[f"Q{i}"] is True else "fail") for i in range(1, 7)}


def reconcile(*, dataset: str, dataset_hash: str, start: dt.date, end: dt.date,
              accepted: set[str], requested: dict, skipped: dict, availability: dict,
              quality: dict, refs: dict, eligibility: dict | None = None,
              audit: dict | None = None, replay: dict | None = None) -> tuple[list, dict]:
    """Keep independent dimensions and contradictions visible. No new thresholds."""
    guard(start, end, what="session quality ledger", dataset=dataset)
    eligible_rows = indexed((eligibility or {}).get("sessions", []), "eligibility")
    audit_rows = indexed((audit or {}).get("sessions", []), "audit")
    replay_rows = indexed((replay or {}).get("sessions", []), "replay")
    metrics = indexed(quality.get("vendor", {}).get("sessions", []), "quality")
    cal = EventCalendar()
    rows, issues = [], []
    for offset in range((end - start).days + 1):
        d = start + dt.timedelta(days=offset)
        date = str(d)
        calendar = ("weekend" if d.weekday() >= 5 else "trading_session"
                    if time_utils.is_trading_day(d) else "holiday")
        early = calendar == "trading_session" and session_close(d, cal) == dt.time(13)
        er, ar, rr = eligible_rows.get(date), audit_rows.get(date), replay_rows.get(date)
        conflicts = []
        reasons = []
        audit_reasons = (ar or er or {}).get("reasons", [])
        if er is not None and ar is not None:
            if er.get("reasons") != ar.get("reasons") or er.get("status") != ar.get("status"):
                conflicts.append("eligibility/audit reasons or status disagree")
        excluded = date in skipped
        if excluded:
            original = skipped[date]
            for reason in original if isinstance(original, list) else [original]:
                code = reason.split(":", 1)[0]
                reasons.append({"code": code, "text": reason,
                                "evidence": refs["manifest"]
                                + "#/history/local_import/sessions_skipped/"
                                + date})
        if excluded or (calendar == "trading_session" and ar and ar["status"] == "excluded"
                        and (er or {}).get("classification") != NON_EXPIRATION):
            for reason in audit_reasons:
                reasons.append({"code": reason.split(":", 1)[0], "text": reason,
                                "evidence": refs.get("audit", refs.get("eligibility"))
                                + "#/sessions/" + date})
            excluded = True
        option = availability.get(date, {"status": "not_requested", "evidence": []})
        non_expiration = (er or {}).get("classification") == NON_EXPIRATION
        if non_expiration:
            if date in requested or option["status"] != "not_requested":
                conflicts.append("documented non-expiration conflicts with option evidence")
            else:
                option = {**option, "status": "non_expiration", "evidence": [
                    refs["eligibility"] + "#/sessions/" + date],
                    "expiration_source": eligibility.get("expiration_source")}
        if er:
            ec = er["classification"]
            if ec in {"weekend", "holiday"} and ec != calendar:
                conflicts.append("eligibility/calendar disagree")
            if ec == "eligible" and date not in accepted:
                conflicts.append("eligible date absent from normalized sessions")
            if ec in {"approved_quality_exclusion", "missing_supporting_inputs"} and not excluded:
                conflicts.append("eligibility exclusion absent from import exclusions")
        if date in accepted and (excluded or non_expiration or calendar != "trading_session"):
            conflicts.append("normalized acceptance contradicts exclusion/calendar")
        if date in accepted and date not in requested:
            conflicts.append("accepted date absent from requested raw inputs")
        if option["status"] == "conflict":
            conflicts.append("option evidence conflicts")
        if date in requested and option["status"] not in {"successful_request", "missing_file"}:
            conflicts.append("import request contradicts catalog")
        if option["status"] == "missing_file":
            conflicts.append("successful request file missing")
        if calendar != "trading_session" and date in requested:
            conflicts.append("option request on a non-session calendar date")
        if ar and ar["status"] in {"usable", "excluded"}:
            audit_missing = set(ar["reasons"])
            importer_missing = {r["code"] for r in reasons}
            for importer_code, audit_code in (("no_spx_index", "missing_index_observations"),
                                               ("no_vix", "missing_vix")):
                if importer_code in importer_missing and audit_code not in audit_missing:
                    conflicts.append("audit/import supporting evidence disagrees: " + importer_code)
        if date in accepted and date not in metrics:
            conflicts.append("accepted date absent from matched quality measurements")
        if date in metrics and date not in accepted:
            conflicts.append("quality measurements for a non-accepted date")
        if rr and rr["status"] in {"traded", "no_trade"} and date not in accepted:
            conflicts.append("research outcome on a non-accepted date")
        if rr and date in accepted and rr["status"] not in {"traded", "no_trade"}:
            conflicts.append("research exclusion contradicts normalized acceptance")
        if conflicts:
            primary = "conflict"
        elif calendar != "trading_session":
            primary = calendar
        elif non_expiration:
            primary = "non_expiration"
        elif excluded:
            primary = "excluded"
        elif date in accepted:
            primary = "accepted"
        else:
            primary = "absent_normalized"
            issues.append({"date": date, "reason": "trading date has no normalized disposition"})
        for conflict in conflicts:
            issues.append({"date": date, "reason": conflict})
        normalization = ("conflict" if conflicts else "accepted" if date in accepted
                         else "excluded" if excluded else "absent")
        # A usable audit checked every supporting field below. Import acceptance establishes
        # only SPX and VIX; importer short circuits on the first missing input.
        missing_map = {"spx": {"missing_index_observations", "no_spx_index"},
                       "vix": {"missing_vix", "no_vix"}, "open": {"missing_open"},
                       "prior_close_spx": {"missing_prior_close:SPX"},
                       "prior_close_vix": {"missing_prior_close:$VIX"},
                       "settlement": {"missing_settlement"}}
        supporting = {}
        reason_texts = {r["text"] for r in reasons} | set(audit_reasons)
        for field, missing in missing_map.items():
            status = ("missing" if missing & reason_texts else "available"
                      if ar and ar["status"] in {"usable", "excluded"}
                      and calendar == "trading_session" else "available"
                      if date in accepted and field in {"spx", "vix"} else "unknown")
            supporting[field] = {"status": status, "evidence": (
                refs.get("audit", refs["manifest"]) if status != "unknown" else None)}
        outcome = None
        if rr:
            outcome = {"status": rr["status"], "scope": "existing_E0_overlay",
                       "evidence": refs["replay"] + "#/sessions/" + date}
        rows.append({"schema_version": SCHEMA, "instrument": "SPX", "option_root": "SPXW",
                     "lifecycle": "0dte", "exchange_date": date,
                     "exchange_timezone": "America/New_York", "dataset": dataset,
                     "dataset_hash": dataset_hash, "primary_classification": primary,
                     "calendar": {"status": calendar, "scheduled_early_close": early,
                                  "close_et": session_close(d, cal).strftime("%H:%M")
                                  if calendar == "trading_session" else None,
                                  "evidence": refs["calendar"]},
                     "option_availability": option, "supporting_inputs": supporting,
                     "normalization": {"status": normalization,
                                       "evidence": refs["manifest"],
                                       "sessions_evidence": refs["sessions"]},
                     "exclusion_reasons": reasons, "original_audit": ar or er,
                     "quality": {"assessment_scope": "dataset", "evidence": refs["quality"],
                                 "gates": gate_status(quality.get("gates", {})),
                                 "applies_to_session": date in metrics,
                                 "per_session_measurements": metrics.get(date),
                                 "per_session_scope": "recorded measurements; no new gate verdict"},
                     "research_outcome": outcome, "conflicts": conflicts,
                     "evidence_references": refs})
    counts = dict(sorted(Counter(r["primary_classification"] for r in rows).items()))
    summary = {"schema_version": SCHEMA, "dataset": dataset, "dataset_hash": dataset_hash,
               "range": [str(start), str(end)], "calendar_dates": len(rows),
               "primary_counts": counts,
               "option_counts": dict(sorted(Counter(
                   r["option_availability"]["status"] for r in rows).items())),
               "exclusion_reason_counts": dict(sorted(Counter(
                   code for r in rows
                   for code in {reason["code"] for reason in r["exclusion_reasons"]}).items())),
               "research_counts": dict(sorted(Counter(
                   r["research_outcome"]["status"] for r in rows
                   if r["research_outcome"] is not None).items())),
               "unknown_supporting_counts": {f: sum(r["supporting_inputs"][f]["status"]
                                                    == "unknown" for r in rows)
                                             for f in missing_map},
               "quality_scope": "inherited dataset assessment",
               "quality_gates": gate_status(quality.get("gates", {})),
               "issues": issues, "status": "reconciled" if not issues else "blocked",
               "missing_source_count": sum(r["option_availability"]["status"] == "missing_file"
                                           for r in rows),
               "inconsistent_session_count": counts.get("conflict", 0),
               "limitations": LIMITATIONS}
    return rows, summary


def build(*, cache: Path, dataset: str, start: dt.date, end: dt.date, inventory: Path,
          evidence_root: Path, out: Path, eligibility: Path | None = None,
          replay: Path | None = None, catalogs: list[Path] | None = None) -> Path:
    guard(start, end, what="session quality ledger", dataset=dataset)  # Before any input I/O.
    if Path(dataset).name != dataset:
        raise ValueError("dataset must be an explicit name")
    ev = Evidence()
    snapshot_checksums = ev.json(inventory.parent / "checksums.json")
    inv = ev.json(inventory, snapshot_checksums[inventory.name])
    manifest_path = cache / dataset / "manifest.json"
    recorded = [x for x in inv["normalized_datasets"] if x["dataset"] == dataset]
    if len(recorded) != 1:
        raise ValueError(f"inventory has no unique identity for {dataset}")
    ev.file(manifest_path, recorded[0]["manifest_sha256"])
    ds = Dataset(cache / dataset)
    m = ds.manifest
    if ds.hash != recorded[0]["dataset_hash"]:
        raise ValueError("inventory/dataset hash mismatch")
    if (m.underlying != "SPX" or m.source.get("option_root") != "SPXW"
            or m.source.get("set") != "spxw_0dte" or m.export.get("kind") != "local_parquet"):
        raise ValueError("ledger requires the local SPXW 0-DTE mapping")
    # The verifier reads all listed files: reject a mixed/protected dataset first.
    for rel in m.files:
        if rel.startswith("sessions/"):
            d = dt.date.fromisoformat(rel.split("/")[1])
            guard(d, d, what="normalized ledger input", dataset=dataset)
    if m.export.get("range") != [str(start), str(end)]:
        raise ValueError("requested range differs from the inventoried canonical import range")
    problems = ds.verify()
    if problems:
        raise ValueError("dataset verification failed: " + "; ".join(problems))
    for rel, entry in {**m.files, **m.aux}.items():
        ev.inputs[str((ds.root / rel).resolve())] = entry["sha256"]
    sessions = ds.sessions()
    accepted = set(sessions.date.astype(str))
    if len(accepted) != len(sessions):
        raise ValueError("duplicate normalized sessions")
    imports = [h for h in m.history if h.get("mode") == "local_import"
               and h.get("dataset_hash") == ds.hash and h.get("range") == m.export["range"]]
    if len(imports) != 1:
        raise ValueError("missing or ambiguous matching local import history")
    imported = imports[0]
    requested, skipped = imported["requested_raw_inputs"], imported["sessions_skipped"]
    for date, ref in requested.items():
        d = dt.date.fromisoformat(date)
        guard(d, d, what="requested option ledger input", dataset=dataset)
        if not start <= d <= end:
            raise ValueError(f"import request outside requested range: {date}")
        path = Path(ref["path"])
        path_date = dt.date.fromisoformat(path.stem)
        guard(path_date, path_date, what="raw option ledger input", dataset=dataset)
        if path_date != d:
            raise ValueError(f"raw path date differs from import request: {path}")
        if path.exists():
            ev.file(path, ref["sha256"])
    for date, ref in imported["raw_inputs"].items():
        if date not in requested or requested[date]["sha256"] != ref["sha256"]:
            raise ValueError(f"raw/ requested input identity mismatch: {date}")
    completion_ref = [x for x in inv["experiments"]
                      if x["path"].endswith("/completion-summary.json")]
    completion = ev.json(evidence_root / "completion-summary.json",
                         completion_ref[0]["sha256"] if completion_ref else None)
    freeze = ev.json(evidence_root / "frozen-supporting-inputs.json")
    for path, ref in freeze["files"].items():
        ev.file(Path(path), ref["sha256"])
    support = Dataset(cache / m.source["support"]["dataset"])
    if (support.hash != m.source["support"]["hash"]
            or support.manifest.source != m.source["support"]["source"]):
        raise ValueError("supporting snapshot identity/mapping mismatch")
    ev.file(support.root / "manifest.json")
    for rel, entry in support.manifest.files.items():
        ev.file(support.root / rel, entry["sha256"])
    for ref in [*m.source["index_files"].values(), *m.source["daily_cache"].values()]:
        ev.file(Path(ref["path"]), ref["sha256"])
    quality_history = [h for h in m.history if h.get("mode") == "vendor_quality"
                       and h.get("dataset_hash") == ds.hash and h.get("range") == m.export["range"]]
    if len(quality_history) != 1:
        raise ValueError("missing or ambiguous quality evidence for exact dataset/range")
    qh = quality_history[0]
    qdir = evidence_root / "artifacts" / dataset / "quality" / qh["run_id"]
    qpath = qdir / "quality.json"
    qprov = ev.json(qdir / "provenance.json", completion["artifact_sha256"][
        str((qdir / "provenance.json").relative_to(evidence_root))])
    quality = ev.json(qpath, qprov["quality_sha256"])
    expected_qhash = completion["artifact_sha256"][str(qpath.relative_to(evidence_root))]
    ev.file(qpath, expected_qhash)
    ev.file(qdir / "report.md", completion["artifact_sha256"][
        str((qdir / "report.md").relative_to(evidence_root))])
    if (quality["meta"]["vendor"] != {"dataset": ds.name, "dataset_hash": ds.hash}
            or quality["range"] != m.export["range"] or quality["gates"] != qh["gates"]
            or quality["pass"] != qh["pass"]
            or quality["meta"]["cboe_spx"]["sha256"] != m.source["daily_cache"]["SPX"]["sha256"]):
        raise ValueError("quality dataset hash/range/support identity mismatch")
    ev.file(CALENDAR_PATH)
    ev.file(Path(time_utils.__file__))
    refs = {"manifest": str(manifest_path.resolve()),
            "sessions": str((ds.root / "sessions.parquet").resolve()),
            "inventory": str(inventory.resolve()), "quality": str(qpath.resolve()),
            "calendar": [str(Path(time_utils.__file__).resolve()), str(CALENDAR_PATH.resolve())]}
    audit, elig, overlay = None, None, None
    if eligibility:
        elig = ev.json(eligibility)
        apath = evidence_root / "artifacts" / dataset / "input-audit" / (
            elig["audit_sha256"][:12]) / "input-audit.json"
        audit = ev.json(apath, elig["audit_sha256"])
        if audit["source"] != m.source or audit["range"] != m.export["range"]:
            raise ValueError("eligibility audit source/range mapping mismatch")
        refs.update(eligibility=str(eligibility.resolve()), audit=str(apath.resolve()))
    if replay:
        if not elig:
            raise ValueError("research overlay requires its eligibility/audit evidence")
        identities = [x for x in inv["experiments"] if x["path"].endswith("/" + replay.name)]
        if len(identities) != 1:
            raise ValueError("research overlay missing inventory identity")
        overlay = ev.json(replay, identities[0]["sha256"])
        run_prov_path = (evidence_root / "artifacts" / dataset / completion["run_id"]
                         / "provenance.json")
        run_prov = ev.json(run_prov_path, completion["artifact_sha256"][
            str(run_prov_path.relative_to(evidence_root))])
        result_path = run_prov_path.with_name("results.json")
        result = ev.json(result_path, run_prov["hashes"]["results.json"])
        meta = result["meta"]
        if (meta["dataset_hash"] != ds.hash or meta["dataset"] != ds.name
                or completion["dataset_hash"] != ds.hash
                or [meta["start"], meta["end"]] != m.export["range"]
                or meta.get("baseline") != "E0"):
            raise ValueError("research overlay dataset hash/range mismatch")
        if overlay["source_audit"] != refs["audit"]:
            raise ValueError("research overlay audit mismatch")
        refs["replay"] = str(replay.resolve())
    # Catalogs are metadata only, including a sealed archive's catalog. Never open its payloads.
    catalog_records: dict[str, list[dict]] = {}
    for cpath in catalogs or [Path(m.source["archive"]) / "catalog.jsonl"]:
        ev.file(cpath)
        for i, line in enumerate(cpath.read_text().splitlines(), 1):
            rec = json.loads(line)
            if (rec["set"] == "spxw_0dte" and rec["kind"] == "quote_1m"
                    and str(start) <= rec["date"] <= str(end)):
                catalog_records.setdefault(rec["date"], []).append({
                    "record": rec, "evidence": str(cpath.resolve()) + f"#line={i}",
                    "path": str(cpath.parent / rec["set"] / rec["kind"] / rec["date"][:4]
                                / (rec["date"] + ".parquet"))})
    available = {}
    for date in sorted(set(catalog_records) | set(requested)):
        records = catalog_records.get(date, [])
        statuses = {r["record"]["status"] for r in records}
        conflicting = len({canonical(r["record"]) for r in records}) > 1
        paths = [Path(r["path"]) for r in records if r["record"]["status"] == "ok"]
        if conflicting or (not statuses and date in requested):
            status = "conflict"
        elif statuses == {"ok"}:
            status = "successful_request" if all(p.is_file() for p in paths) else "missing_file"
        elif statuses == {"no_data"}:
            status = "no_data"
        else:
            status = "conflict"
        if date in requested and paths and not any(
                p.resolve() == Path(requested[date]["path"]).resolve() for p in paths):
            status = "conflict"
        available[date] = {"status": status, "requests": records,
                           "import_request": requested.get(date),
                           "evidence": [r["evidence"] for r in records]}
    rows, summary = reconcile(dataset=ds.name, dataset_hash=ds.hash, start=start, end=end,
                              accepted=accepted, requested=requested, skipped=skipped,
                              availability=available, quality=quality, refs=refs,
                              eligibility=elig, audit=audit, replay=overlay)
    # Audit classifications and original aggregate counts must reconcile too.
    for body, field, source in ((elig, "counts", "eligibility"),
                                (overlay, "summary", "replay")):
        if body:
            actual = dict(Counter(r["classification" if source == "eligibility" else "status"]
                                  for r in body["sessions"]))
            if actual != body[field] or set(indexed(body["sessions"], source)) != {
                    r["exchange_date"] for r in rows}:
                summary["issues"].append({"source": source,
                                          "reason": "aggregate counts/date coverage disagree"})
    summary["status"] = "blocked" if summary["issues"] else "reconciled"
    summary["input_sha256"] = ev.inputs
    return publish(out, ds.name, rows, summary, ev.inputs, m.source, m.export)


def publish(out: Path, dataset: str, rows: list, summary: dict, inputs: dict,
            source: dict, mapping: dict) -> Path:
    ledger = "".join(json.dumps(r, sort_keys=True, allow_nan=False) + "\n" for r in rows)
    payloads = {"ledger.jsonl": ledger, "summary.json": canonical(summary)}
    hashes = {name: hashlib.sha256(payload.encode()).hexdigest()
              for name, payload in payloads.items()}
    identity = hashlib.sha256(canonical(hashes).encode()).hexdigest()
    folder = out / dataset / "session-quality-ledger" / identity[:12]
    if folder.exists():
        verify_artifact(folder)
        if json.loads((folder / "provenance.json").read_text())["input_sha256"] != inputs:
            raise ValueError("artifact input identity mismatch")
        return folder
    repo = Path(__file__).resolve().parents[3]
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True))
    code = {str(p.relative_to(repo)): sha256_file(p)
            for p in sorted((repo / "src" / "butterfly_guy" / "research").glob("*.py"))}
    command = shlex.join([sys.executable, "-m", "butterfly_guy.research", *sys.argv[1:]])
    report = ["# SPXW session quality evidence ledger", "",
              f"Dataset: `{dataset}`; range: {' through '.join(summary['range'])}.",
              f"Status: **{summary['status']}**; result identity: `{identity}`.", "",
              "Primary counts (mutually exclusive):", ""]
    report += [f"- {k}: {v}" for k, v in summary["primary_counts"].items()]
    report += ["", "Inherited dataset quality gates:", ""]
    report += [f"- {k}: {v}" for k, v in summary["quality_gates"].items()]
    report += ["", "Exclusions (original text and evidence are retained in JSONL):", ""]
    report += [f"- {r['exchange_date']}: " + "; ".join(x["text"] for x in r["exclusion_reasons"])
               for r in rows if r["exclusion_reasons"]]
    report += ["", "Unknown supporting checks:", ""]
    report += [f"- {k}: {v} dates" for k, v in summary["unknown_supporting_counts"].items()]
    report += ["", "Evidence issues:", "", canonical(summary["issues"]),
               "Interpretation and follow-ups:", ""] + [f"- {x}" for x in LIMITATIONS]
    report += ["", "Reproduce offline:", "", "```bash", f"cd {shlex.quote(str(repo))}",
               command, "```", ""]
    payloads["report.md"] = "\n".join(report)
    hashes["report.md"] = hashlib.sha256(payloads["report.md"].encode()).hexdigest()
    provenance = {"schema_version": SCHEMA, "created_at": dt.datetime.now(dt.UTC).isoformat(),
                  "git_sha": git_sha, "git_dirty": dirty, "code_sha256": code,
                  "command": command, "dataset": dataset, "dataset_hash": summary["dataset_hash"],
                  "range": summary["range"], "result_sha256": identity,
                  "output_sha256": hashes, "input_sha256": inputs,
                  "source_semantics": source, "mapping": mapping,
                  "exchange_timezone": "America/New_York"}
    folder.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    stage = Path(tempfile.mkdtemp(prefix=".ledger-", dir=folder.parent))
    for name, payload in payloads.items():
        (stage / name).write_text(payload)
    (stage / "provenance.json").write_text(canonical(provenance))
    stage.rename(folder)
    verify_artifact(folder)
    return folder


def verify_artifact(folder: Path) -> None:
    """Verify published outputs against provenance without opening raw inputs."""
    prov = json.loads((folder / "provenance.json").read_text())
    for name, expected in prov["output_sha256"].items():
        if sha256_file(folder / name) != expected:
            raise ValueError(f"artifact sha256 mismatch: {folder / name}")
    identity = {k: prov["output_sha256"][k] for k in ("ledger.jsonl", "summary.json")}
    if hashlib.sha256(canonical(identity).encode()).hexdigest() != prov["result_sha256"]:
        raise ValueError("artifact result identity mismatch")


def cmd_ledger(args) -> int:
    path = build(cache=Path(args.cache), dataset=args.dataset, start=args.start, end=args.end,
                 inventory=Path(args.inventory), evidence_root=Path(args.evidence_root),
                 out=Path(args.out),
                 eligibility=Path(args.eligibility) if args.eligibility else None,
                 replay=Path(args.replay_ledger) if args.replay_ledger else None,
                 catalogs=[Path(x) for x in args.catalog] if args.catalog else None)
    summary = json.loads((path / "summary.json").read_text())
    print(f"session quality ledger: {path}")
    print(canonical({k: summary[k] for k in ("status", "primary_counts", "research_counts")}))
    return 0 if summary["status"] == "reconciled" else 1


def add_command(sub, date_type) -> None:
    p = sub.add_parser("session-quality-ledger", help="offline SPXW session evidence ledger")
    p.add_argument("--start", type=date_type, required=True)
    p.add_argument("--end", type=date_type, required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--evidence-root", required=True)
    p.add_argument("--eligibility", help="documented development calendar/expiration ledger")
    p.add_argument("--replay-ledger", help="optional existing E0 overlay; never reruns strategy")
    p.add_argument("--catalog", action="append", help="request metadata only; repeatable")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_ledger)
