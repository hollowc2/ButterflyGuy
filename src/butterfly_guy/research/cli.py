"""Research CLI: `uv run python -m butterfly_guy.research <command> ...`

  export             read-only export of SPX 0-DTE data into the Parquet cache
  verify             check the dataset manifest hashes and the registry chain
  register           pre-register catalog variants before evaluating them
  port               link ported variants to their placeholder backfill records
  run                evaluate variants against a baseline and write artifacts
  shadow             exploratory paired shadow on an open cohort's recorded sessions
  parity             replay E0 under the frozen profile against the frozen replay ledger
  calibrate-latency  read-only exit latency of recorded paper trades
  export-vol         Cboe daily VIX-family history (and a gateway intraday dump) as aux files
  diagnose           DESCRIPTIVE E0 breakdowns by scheduled event and term structure
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import shlex
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

import structlog

from butterfly_guy.research.dataset import DEFAULT_DATASET, Dataset, default_cache_root, sha256_file
from butterfly_guy.research.entry import (
    PROFILES,
    REPO_ROOT,
    SPX_CONFIG,
    RunContext,
    SessionLoader,
    load_spx_config,
)
from butterfly_guy.research.evaluate import EvalParams, common_dates, evaluate
from butterfly_guy.research.registry import Registry
from butterfly_guy.research.report import dump_canonical, trade_record, write_run
from butterfly_guy.research.simulate import DEFAULT_EXIT_DELAY, canonical_json, run_variants
from butterfly_guy.research.tieset import TiesetScorer
from butterfly_guy.research.variants import CATALOG, resolve

REPORTS = REPO_ROOT / "reports" / "research"
REGISTRY_DIR = REPORTS / "registry"
FROZEN_LEDGER = REPO_ROOT / "tests" / "fixtures" / "research" / "frozen_ledger_b83c2a18.json"


def _quiet_logs() -> None:
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))


def _date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def _git() -> tuple[str, bool]:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             check=True, cwd=REPO_ROOT).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "src", "configs"],
                                    capture_output=True, text=True, check=True,
                                    cwd=REPO_ROOT).stdout.strip())
        return sha, dirty
    except (OSError, subprocess.CalledProcessError):
        return "", True


def _dataset(args: argparse.Namespace) -> Dataset:
    return Dataset.open(args.dataset, Path(args.cache) if args.cache else None)


def cmd_export(args: argparse.Namespace) -> int:
    from butterfly_guy.research.export import (
        DockerExecSource,
        ExportPlan,
        PostgresSource,
        run_export,
    )

    source = DockerExecSource() if args.source == "docker" else PostgresSource()
    try:
        run_export(source, ExportPlan(args.start, args.end, dataset=args.dataset,
                                      refresh=args.refresh, bars_only=args.bars_only),
                   Path(args.cache) if args.cache else None)
    finally:
        source.close()
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    from butterfly_guy.research.export import DockerExecSource, PostgresSource
    from butterfly_guy.research.latency import collect, summarize

    source = DockerExecSource() if args.source == "docker" else PostgresSource()
    try:
        rows = collect(source, args.start, args.end)
    finally:
        source.close()
    summary = summarize(rows, _dataset(args))
    out = {"range": [str(args.start), str(args.end)], "summary": summary, "trades": rows}
    path = Path(args.out) / "calibration" / f"exit_latency_{args.start}_{args.end}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_canonical(out))
    print(json.dumps(summary, indent=1))
    print(f"written: {path}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    from butterfly_guy.research.event_calendar import EventCalendar

    ds = _dataset(args)
    problems = ds.verify()
    reg = Registry.for_dataset(Path(args.registry), ds.name)
    problems += [f"registry: {p}" for p in reg.verify()]
    print(f"dataset {ds.name} hash {ds.hash}: {len(ds.manifest.files)} files")
    if ds.manifest.aux:
        print(f"aux hash {ds.aux_hash}: {', '.join(sorted(ds.manifest.aux))}")
    try:
        cal = EventCalendar()
        print(f"event calendar {cal.path.name} ({cal.version}) sha256 {cal.sha256}: "
              f"{len(cal.events)} rows")
    except (OSError, ValueError) as exc:
        problems.append(f"event calendar: {exc}")
    for p in problems:
        print("  PROBLEM", p)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_register(args: argparse.Namespace) -> int:
    reg = Registry.for_dataset(Path(args.registry), args.dataset)
    for v in resolve(args.variants.split(",")):
        rec = reg.append("register", variant=v.name, definition=v.definition(),
                         definition_hash=v.definition_hash(), note=args.note or "")
        print(f"registered {v.name} {rec['definition_hash'][:12]} (seq {rec['seq']})")
    return 0


def cmd_port(args: argparse.Namespace) -> int:
    reg = Registry.for_dataset(Path(args.registry), args.dataset)
    for v in resolve(args.variants.split(",")):
        placeholder = reg.placeholder(v.name)
        if placeholder is None:
            raise SystemExit(f"{v.name}: no unported placeholder backfill record")
        rec = reg.append("port", variant=v.name, definition=v.definition(),
                         definition_hash=v.definition_hash(),
                         ported_from=placeholder["definition_hash"], note=args.note or "")
        print(f"ported {v.name} {rec['definition_hash'][:12]} <- "
              f"{placeholder['definition_hash'][:12]} ({rec['stage']}, seq {rec['seq']})")
    return 0


def _simulate(args: argparse.Namespace, ds: Dataset, profile_name: str, names: list[str],
              start: dt.date | None, end: dt.date | None, tieset: bool):
    """Replay the baseline and `names`; returns the run result, tie-set scorer and meta."""
    profile = PROFILES[profile_name]
    ctx = RunContext(load_spx_config())
    names = [n for n in names if n != args.baseline]
    scorer = TiesetScorer() if tieset else None
    result = run_variants(SessionLoader(ds, profile), resolve([args.baseline, *names]), ctx,
                          start=start, end=end, exit_delay=args.exit_delay, tieset=scorer)
    params = EvalParams(split=args.split, bootstrap_reps=args.reps,
                        bootstrap_block=args.block, rolling_block=args.rolling_block)
    meta = {
        "dataset": ds.name, "dataset_hash": ds.hash, "profile": asdict(profile),
        "config_sha256": sha256_file(SPX_CONFIG), "start": str(start), "end": str(end),
        "baseline": args.baseline, "eval": params.as_dict(),
        "accounting": {"exit_delay_snapshots": args.exit_delay},
        "variants": {n: {"definition": r.variant.definition(),
                         "definition_hash": r.variant.definition_hash()}
                     for n, r in result.runs.items()},
    }
    if scorer is not None:
        meta["tieset"] = scorer.params()
    return result, scorer, params, meta


def _record(args: argparse.Namespace, ds: Dataset, result, meta: dict, results: dict,
            **extra: object) -> tuple[str, Path, dict]:
    """Write artifacts' provenance and registry records; returns run id, dir, provenance."""
    run_id = hashlib.sha256(canonical_json(meta).encode()).hexdigest()[:12]
    out_dir = Path(args.out) / ds.name / run_id
    git_sha, dirty = _git()
    reg = Registry.for_dataset(Path(args.registry), ds.name)
    stages = {}
    results_hash = hashlib.sha256(dump_canonical(results).encode()).hexdigest()
    if not args.no_registry:
        for name, run in result.runs.items():
            v = run.variant
            rec = reg.append(
                "evaluate", variant=name, definition=v.definition(),
                definition_hash=v.definition_hash(), dataset_hash=ds.hash, git_sha=git_sha,
                git_dirty=dirty, run_id=run_id, profile=meta["profile"]["name"],
                config_sha256=meta["config_sha256"], results_sha256=results_hash, **extra,
            )
            stages[name] = rec["stage"]
    provenance = {
        "run_id": run_id, "git_sha": git_sha, "git_dirty": dirty,
        "command": " ".join(shlex.quote(a) for a in ["python", "-m", "butterfly_guy.research",
                                                      *sys.argv[1:]]),
        "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "registry": {"path": str(reg.path.relative_to(REPO_ROOT)) if reg.path.is_relative_to(
            REPO_ROOT) else str(reg.path), "tried": reg.tried(ds.hash),
            "recorded": not args.no_registry},
        "stages": stages,
    }
    return run_id, out_dir, provenance


def _finish(out_dir: Path, results: dict, result, provenance: dict, render=None) -> None:
    trades = [t for r in result.runs.values() for t in r.trades]
    hashes = write_run(out_dir, results, trades, provenance, render)
    print((out_dir / "report.md").read_text())
    print(f"artifacts: {out_dir}")
    for f, h in hashes.items():
        print(f"  {f} {h}")


def cmd_run(args: argparse.Namespace) -> int:
    _quiet_logs()
    ds = _dataset(args)
    t0 = time.monotonic()
    result, scorer, params, meta = _simulate(args, ds, args.profile, args.variants.split(","),
                                             args.start, args.end, not args.no_tieset)
    ev = evaluate(result, args.baseline, params)
    results = {"meta": meta, "evaluation": ev}
    if scorer is not None:
        common, _ = common_dates(result, list(result.runs))
        results["tiesets"] = scorer.summary(list(result.runs), common)
    run_id, out_dir, provenance = _record(args, ds, result, meta, results)
    provenance["run_seconds"] = round(time.monotonic() - t0, 1)
    _finish(out_dir, results, result, provenance)
    print(f"run time {provenance['run_seconds']} s")
    return 0


def cmd_shadow(args: argparse.Namespace) -> int:
    from butterfly_guy.research import shadow

    _quiet_logs()
    ds = _dataset(args)
    ledger = shadow.read_cohort_ledger(args.cohort, args.ref)
    sessions = ledger.sessions
    if not sessions:
        raise SystemExit(f"cohort {args.cohort} has no recorded sessions at {ledger.commit}")
    args.split = sessions[0]  # H1/H2 are meaningless on a handful of sessions
    result, _, params, meta = _simulate(args, ds, shadow.COHORT_PROFILE,
                                        args.variants.split(","), sessions[0], sessions[-1],
                                        tieset=False)
    missing = [d for d in sessions if d not in set(result.dates)]
    ev = evaluate(result, args.baseline, params, only=sessions)
    meta["shadow"] = {"cohort": ledger.cohort_id, "ref": ledger.ref, "commit": ledger.commit,
                      "sessions": [d.isoformat() for d in sessions]}
    evaluated = [d for d in sessions if d not in missing]
    results = {"meta": meta, "evaluation": ev, "shadow": {
        "exploratory": True,
        "sessions": [d.isoformat() for d in evaluated],
        "not_evaluated": {d.isoformat(): result.skipped.get(d, "not in dataset")
                          for d in missing},
        "e0_vs_cohort": shadow.compare_with_cohort(
            [t for t in result.runs[args.baseline].trades if t.date in set(sessions)], ledger),
        "rows": shadow.session_rows(result, list(result.runs), evaluated, args.baseline),
    }}
    run_id, out_dir, provenance = _record(
        args, ds, result, meta, results, scope=f"shadow:{ledger.cohort_id}",
        cohort_commit=ledger.commit, sessions=[d.isoformat() for d in evaluated])
    _finish(out_dir, results, result, provenance,
            lambda r, p: shadow.markdown(ledger, r, p))
    return 0


def compare_to_ledger(trades: list, ledger: list[dict], tolerance: float) -> dict:
    """Trade-by-trade comparison with the frozen replay ledger (P&L in dollars)."""
    ours = {t.date.isoformat(): trade_record(t) for t in trades}
    ref = {r["date"]: r for r in ledger if r["traded"]}
    mismatches = []
    for d in sorted(set(ours) | set(ref)):
        a, b = ours.get(d), ref.get(d)
        if a is None or b is None:
            mismatches.append({"date": d, "issue": "only in " + ("ledger" if a is None
                                                                 else "research core")})
            continue
        issues = []
        if (a["direction"], a["lower"], a["center"], a["upper"]) != (
                b["direction"], b["lower"], b["center"], b["upper"]):
            issues.append(f"fly {a['direction']} {a['lower']}/{a['center']}/{a['upper']} vs "
                          f"{b['direction']} {b['lower']}/{b['center']}/{b['upper']}")
        if a["entry_time"] != b["entry_time"]:
            issues.append(f"entry {a['entry_time']} vs {b['entry_time']}")
        if a["exit_reason"] != b["exit_reason"]:
            issues.append(f"exit {a['exit_reason']} vs {b['exit_reason']}")
        for m, key in (("midpoint", "pnl_midpoint"), ("marketable", "marketable_pnl"),
                       ("stressed", "stressed_marketable_pnl")):
            pa, pb = a[m]["pnl"], b.get(key)
            if pa is None or pb is None or abs(pa - pb) > tolerance:
                issues.append(f"{m} {pa} vs {pb}")
        if issues:
            mismatches.append({"date": d, "issue": "; ".join(issues)})
    totals = {}
    for m, key in (("midpoint", "pnl_midpoint"), ("marketable", "marketable_pnl"),
                   ("stressed", "stressed_marketable_pnl")):
        totals[m] = {
            "research_core": round(sum(r[m]["pnl"] or 0 for r in ours.values()), 2),
            "frozen_ledger": round(sum(r.get(key) or 0 for r in ref.values()), 2),
        }
    return {"trades": len(ours), "ledger_trades": len(ref), "mismatches": mismatches,
            "totals": totals,
            "exits": {"cash_settled": sum(r["exit_reason"] == "cash_settled"
                                          for r in ours.values()),
                      "intraday": sum(r["exit_reason"] != "cash_settled" for r in ours.values())}}


def cmd_parity(args: argparse.Namespace) -> int:
    _quiet_logs()
    ds = _dataset(args)
    ledger = json.loads(Path(args.ledger).read_text())
    ctx = RunContext(load_spx_config())
    loader = SessionLoader(ds, PROFILES[args.profile])
    result = run_variants(loader, resolve(["E0"]), ctx, start=args.start, end=args.end)
    report = compare_to_ledger(result.runs["E0"].trades, ledger, args.tolerance)
    report["skipped"] = {d.isoformat(): r for d, r in sorted(result.skipped.items())}
    report["excluded"] = {d.isoformat(): r for d, r in sorted(result.runs["E0"].excluded.items())}
    print(json.dumps(report, indent=1))
    return 1 if report["mismatches"] else 0


def cmd_export_vol(args: argparse.Namespace) -> int:
    from butterfly_guy.research import volindex

    cache = Path(args.cache) if args.cache else None
    if not args.gateway_dump or args.cboe:
        volindex.export_daily(args.dataset, cache, log=sys.stdout)
    if args.gateway_dump:
        volindex.ingest_intraday(args.dataset, Path(args.gateway_dump), cache, log=sys.stdout)
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    from butterfly_guy.research import diagnose
    from butterfly_guy.research.features import SessionFeatures

    _quiet_logs()
    ds = _dataset(args)
    features = SessionFeatures.load(ds)
    t0 = time.monotonic()
    rows, info = diagnose.session_rows(features, ds, args.profile, args.start, args.end,
                                       args.split, args.exit_delay)
    meta = {
        "label": diagnose.LABEL, "dataset": ds.name, "dataset_hash": ds.hash,
        "inputs": features.inputs, "profile": args.profile,
        "config_sha256": sha256_file(SPX_CONFIG),
        "start": str(args.start), "end": str(args.end), "split": args.split.isoformat(),
        "exit_delay_snapshots": args.exit_delay, "baseline": "E0",
        "definition_hash": CATALOG["E0"].definition_hash(),
    }
    results = {"meta": meta, "sessions": info, "breakdowns": diagnose.breakdowns(rows),
               "coverage": diagnose.coverage(rows)}
    run_id = hashlib.sha256(canonical_json(meta).encode()).hexdigest()[:12]
    out_dir = Path(args.out) / ds.name / "diagnostics" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {"diagnostics.json": dump_canonical(results),
             "sessions.json": dump_canonical(diagnose.session_table(rows))}
    hashes = {}
    for name, text in files.items():
        (out_dir / name).write_text(text)
        hashes[name] = hashlib.sha256(text.encode()).hexdigest()
    git_sha, dirty = _git()
    provenance = {
        "run_id": run_id, "git_sha": git_sha, "git_dirty": dirty,
        "command": " ".join(shlex.quote(a) for a in ["python", "-m", "butterfly_guy.research",
                                                      *sys.argv[1:]]),
        "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "registry": "not recorded: diagnostics are not rule evaluations",
        "run_seconds": round(time.monotonic() - t0, 1), "hashes": hashes,
    }
    (out_dir / "provenance.json").write_text(dump_canonical(provenance))
    (out_dir / "report.md").write_text(diagnose.markdown(results, provenance))
    print((out_dir / "report.md").read_text())
    print(f"artifacts: {out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m butterfly_guy.research", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", default=DEFAULT_DATASET)
    p.add_argument("--cache", default=None, help=f"cache root (default {default_cache_root()})")
    p.add_argument("--registry", default=str(REGISTRY_DIR))
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("export", help="read-only export into the Parquet cache")
    e.add_argument("--start", type=_date, required=True)
    e.add_argument("--end", type=_date, required=True)
    e.add_argument("--source", choices=["tunnel", "docker"], default="tunnel")
    e.add_argument("--refresh", action="store_true", help="re-export existing sessions")
    e.add_argument("--bars-only", action="store_true",
                   help="re-read only daily_bars (official closes that had not landed)")
    e.set_defaults(func=cmd_export)

    c = sub.add_parser("calibrate-latency", help="read-only exit latency of paper trades")
    c.add_argument("--start", type=_date, required=True)
    c.add_argument("--end", type=_date, required=True)
    c.add_argument("--source", choices=["tunnel", "docker"], default="tunnel")
    c.add_argument("--out", default=str(REPORTS))
    c.set_defaults(func=cmd_calibrate)

    v = sub.add_parser("verify", help="check dataset hashes and the registry chain")
    v.set_defaults(func=cmd_verify)

    r = sub.add_parser("register", help="pre-register catalog variants")
    r.add_argument("--variants", required=True, help=f"comma list from {', '.join(CATALOG)}")
    r.add_argument("--note", default="")
    r.set_defaults(func=cmd_register)

    po = sub.add_parser("port", help="link ported variants to their placeholder backfill")
    po.add_argument("--variants", required=True)
    po.add_argument("--note", default="")
    po.set_defaults(func=cmd_port)

    def evaluation_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--variants", required=True)
        sp.add_argument("--baseline", default="E0")
        sp.add_argument("--split", type=_date, default=EvalParams.split)
        sp.add_argument("--reps", type=int, default=EvalParams.bootstrap_reps)
        sp.add_argument("--block", type=int, default=EvalParams.bootstrap_block)
        sp.add_argument("--rolling-block", type=int, default=EvalParams.rolling_block)
        sp.add_argument("--exit-delay", type=int, default=DEFAULT_EXIT_DELAY,
                        help="decision-clock times from exit trigger to the delayed fill")
        sp.add_argument("--out", default=str(REPORTS))
        sp.add_argument("--no-registry", action="store_true",
                        help="do not record the evaluation (the report says so)")

    run = sub.add_parser("run", help="evaluate variants against a baseline")
    evaluation_args(run)
    run.add_argument("--profile", choices=sorted(PROFILES), default="live")
    run.add_argument("--start", type=_date, default=None)
    run.add_argument("--end", type=_date, default=None)
    run.add_argument("--no-tieset", action="store_true", help="skip near-tied fly scoring")
    run.set_defaults(func=cmd_run)

    sh = sub.add_parser("shadow", help="exploratory shadow on a cohort's recorded sessions")
    evaluation_args(sh)
    sh.add_argument("--cohort", required=True)
    sh.add_argument("--ref", default=None, help="cohort branch (default origin/cohort/<id>)")
    sh.set_defaults(func=cmd_shadow)

    par = sub.add_parser("parity", help="compare E0 with the frozen replay ledger")
    par.add_argument("--ledger", default=str(FROZEN_LEDGER))
    par.add_argument("--profile", choices=sorted(PROFILES), default="frozen_20260921")
    par.add_argument("--start", type=_date, default=dt.date(2026, 3, 13))
    par.add_argument("--end", type=_date, default=dt.date(2026, 9, 18))
    par.add_argument("--tolerance", type=float, default=0.005, help="dollars per trade")
    par.set_defaults(func=cmd_parity)

    ev = sub.add_parser("export-vol", help="VIX-family history into separately hashed aux files")
    ev.add_argument("--cboe", action="store_true",
                    help="fetch Cboe's public daily files (the default without --gateway-dump)")
    ev.add_argument("--gateway-dump", default=None,
                    help="JSONL from tools/research_gateway_vol_dump.py (intraday bars)")
    ev.set_defaults(func=cmd_export_vol)

    dg = sub.add_parser("diagnose", help="DESCRIPTIVE E0 breakdowns (no registry record)")
    dg.add_argument("--profile", choices=sorted(PROFILES), default="sweep_20260925")
    dg.add_argument("--start", type=_date, default=dt.date(2026, 3, 13))
    dg.add_argument("--end", type=_date, default=dt.date(2026, 9, 24))
    dg.add_argument("--split", type=_date, default=EvalParams.split)
    dg.add_argument("--exit-delay", type=int, default=DEFAULT_EXIT_DELAY)
    dg.add_argument("--out", default=str(REPORTS))
    dg.set_defaults(func=cmd_diagnose)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
