"""Research CLI: `uv run python -m butterfly_guy.research <command> ...`

  export    read-only export of SPX 0-DTE data into the Parquet cache
  verify    check the dataset manifest hashes and the registry chain
  register  pre-register catalog variants before evaluating them
  run       evaluate variants against a baseline and write artifacts
  parity    replay E0 under the frozen profile against the frozen replay ledger
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
from butterfly_guy.research.simulate import canonical_json, run_variants
from butterfly_guy.research.tieset import run_tiesets
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
                                      refresh=args.refresh),
                   Path(args.cache) if args.cache else None)
    finally:
        source.close()
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    ds = _dataset(args)
    problems = ds.verify()
    reg = Registry.for_dataset(Path(args.registry), ds.name)
    problems += [f"registry: {p}" for p in reg.verify()]
    print(f"dataset {ds.name} hash {ds.hash}: {len(ds.manifest.files)} files")
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


def cmd_run(args: argparse.Namespace) -> int:
    _quiet_logs()
    ds = _dataset(args)
    profile = PROFILES[args.profile]
    config = load_spx_config()
    ctx = RunContext(config)
    names = [n for n in args.variants.split(",") if n != args.baseline]
    variants = resolve([args.baseline, *names])
    params = EvalParams(split=args.split, bootstrap_reps=args.reps,
                        bootstrap_block=args.block, rolling_block=args.rolling_block)
    loader = SessionLoader(ds, profile)
    result = run_variants(loader, variants, ctx, start=args.start, end=args.end)
    ev = evaluate(result, args.baseline, params)
    config_sha = sha256_file(SPX_CONFIG)
    meta = {
        "dataset": ds.name, "dataset_hash": ds.hash, "profile": asdict(profile),
        "config_sha256": config_sha, "start": str(args.start), "end": str(args.end),
        "baseline": args.baseline, "eval": params.as_dict(),
        "variants": {v.name: {"definition": v.definition(),
                              "definition_hash": v.definition_hash()} for v in variants},
    }
    results = {"meta": meta, "evaluation": ev}
    if args.tieset:
        common, _ = common_dates(result, [v.name for v in variants])
        results["tiesets"] = run_tiesets(SessionLoader(ds, profile), variants, ctx, common)
        meta["tieset"] = {"thresholds": [0.10, 0.25], "draws": 5000, "seed": 7}
    run_id = hashlib.sha256(canonical_json(meta).encode()).hexdigest()[:12]
    out_dir = Path(args.out) / ds.name / run_id
    git_sha, dirty = _git()
    reg = Registry.for_dataset(Path(args.registry), ds.name)
    stages = {}
    trades = [t for r in result.runs.values() for t in r.trades]
    results_hash = hashlib.sha256(dump_canonical(results).encode()).hexdigest()
    if not args.no_registry:
        for v in variants:
            rec = reg.append(
                "evaluate", variant=v.name, definition=v.definition(),
                definition_hash=v.definition_hash(), dataset_hash=ds.hash, git_sha=git_sha,
                git_dirty=dirty, run_id=run_id, profile=profile.name,
                config_sha256=config_sha, results_sha256=results_hash,
            )
            stages[v.name] = rec["stage"]
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
    hashes = write_run(out_dir, results, trades, provenance)
    print((out_dir / "report.md").read_text())
    print(f"artifacts: {out_dir}")
    for f, h in hashes.items():
        print(f"  {f} {h}")
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
    e.set_defaults(func=cmd_export)

    v = sub.add_parser("verify", help="check dataset hashes and the registry chain")
    v.set_defaults(func=cmd_verify)

    r = sub.add_parser("register", help="pre-register catalog variants")
    r.add_argument("--variants", required=True, help=f"comma list from {', '.join(CATALOG)}")
    r.add_argument("--note", default="")
    r.set_defaults(func=cmd_register)

    run = sub.add_parser("run", help="evaluate variants against a baseline")
    run.add_argument("--variants", required=True)
    run.add_argument("--baseline", default="E0")
    run.add_argument("--profile", choices=sorted(PROFILES), default="live")
    run.add_argument("--start", type=_date, default=None)
    run.add_argument("--end", type=_date, default=None)
    run.add_argument("--split", type=_date, default=EvalParams.split)
    run.add_argument("--reps", type=int, default=EvalParams.bootstrap_reps)
    run.add_argument("--block", type=int, default=EvalParams.bootstrap_block)
    run.add_argument("--rolling-block", type=int, default=EvalParams.rolling_block)
    run.add_argument("--tieset", action="store_true", help="score near-tied flies")
    run.add_argument("--out", default=str(REPORTS))
    run.add_argument("--no-registry", action="store_true",
                     help="do not record the evaluation (the report says so)")
    run.set_defaults(func=cmd_run)

    par = sub.add_parser("parity", help="compare E0 with the frozen replay ledger")
    par.add_argument("--ledger", default=str(FROZEN_LEDGER))
    par.add_argument("--profile", choices=sorted(PROFILES), default="frozen_20260921")
    par.add_argument("--start", type=_date, default=dt.date(2026, 3, 13))
    par.add_argument("--end", type=_date, default=dt.date(2026, 9, 18))
    par.add_argument("--tolerance", type=float, default=0.005, help="dollars per trade")
    par.set_defaults(func=cmd_parity)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
