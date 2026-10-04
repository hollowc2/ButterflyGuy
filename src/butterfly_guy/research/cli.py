"""Research CLI: `uv run python -m butterfly_guy.research <command> ...`

  export             read-only export of SPX 0-DTE data into the Parquet cache
  verify             check the dataset manifest hashes and the registry chain
  catalog            list catalog variants, their definition hashes and registry history
  register           pre-register catalog variants before evaluating them
  port               link ported variants to their placeholder backfill records
  run                evaluate variants against a baseline and write artifacts
  holdout            the pre-registered holdout evaluation of the registered variants
  shadow             exploratory paired shadow on an open cohort's recorded sessions
  parity             replay E0 under the frozen profile against the frozen replay ledger
  calibrate-latency  read-only exit latency of recorded paper trades
  export-vol         Cboe daily VIX-family history (and a gateway intraday dump) as aux files
  diagnose           DESCRIPTIVE E0 breakdowns by scheduled event and term structure
  export-history     vendor history into spx_0dte_<vendor> (ThetaData)
  vendor-quality     data-quality gates Q1-Q6 on a vendor dataset (opens earlier pulls)
  exclude-sessions   take sessions out of a vendor dataset for a data-quality reason
  validate-vendor    fidelity validation of a vendor dataset against the Helios export
  coverage           per-session quote, spot, VIX and official-bar coverage of a dataset
  mechanism          DESCRIPTIVE H-TS1 mechanism check on Cboe daily closes (development window)
  schwab-fidelity    report-only agreement of recorded Helios chains with ThetaData
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

from butterfly_guy.research.accounting import Costs
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
from butterfly_guy.research.holdout import VALIDATION
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


def cmd_catalog(args: argparse.Namespace) -> int:
    """Every catalog variant (or those named) with its definition hash and what each
    registry under `--registry` holds for that exact definition."""
    root = Path(args.registry)
    registries = {str(p.relative_to(root).with_suffix("")): Registry(p)
                  for p in sorted(root.rglob("*.jsonl"))}
    names = args.variants.split(",") if args.variants else list(CATALOG)
    for v in resolve(names):
        h = v.definition_hash()
        print(f"{v.name}  {h[:12]}")
        print(f"    {v.description}")
        lines = []
        for label, reg in registries.items():
            hist = reg.history(v.name, h)
            if hist["events"]:
                events = ", ".join(f"{k} x{n}" for k, n in sorted(hist["events"].items()))
                lines.append(f"    {label}: {events}; last {hist['last'][:10]}")
            if hist["other_hashes"]:
                lines.append(f"    {label}: other definitions under this name: "
                             + ", ".join(x[:12] for x in hist["other_hashes"]))
        print("\n".join(lines) if lines else "    not in any registry")
    print()
    broken = 0
    for label, reg in registries.items():
        problems = reg.verify()
        broken += bool(problems)
        tried = reg.tried()
        print(f"{label}: {tried['dataset']} distinct definitions tried "
              f"({tried['post_hoc']} post hoc)"
              + (f"; CHAIN BROKEN: {len(problems)} problem(s)" if problems else ""))
    return 1 if broken else 0


def _fit_for_registration(v, ds: Dataset | None, profile_name: str) -> dict:
    """A fitted rule's values, fitted on its own window as a run would fit them, so that the
    holdout evaluation can check its re-fit against the registered value."""
    from butterfly_guy.research.features import SessionFeatures
    from butterfly_guy.research.hypotheses import uses_features
    from butterfly_guy.research.simulate import fit_variants

    if ds is None:
        raise SystemExit(f"{v.name} is fitted on its window: export the dataset before "
                         "registering it")
    features = SessionFeatures.load(ds) if uses_features(v.entry) else None
    ctx = RunContext(load_spx_config(), features=features)
    (fitted,) = fit_variants([v], SessionLoader(ds, PROFILES[profile_name]), ctx)
    return fitted.definition()["entry"]["fitted"]


def _calibrate_for_registration(variants, ds: Dataset, holdout_sessions: int) -> dict:
    """Gate-1 levels (protocol Revision 4) from each rule's development-window paired
    difference against E0, replayed as the holdout evaluation replays. Empty when the dataset
    has too few development sessions (a Helios dataset); the holdout command then refuses."""
    from butterfly_guy.research import protocol
    from butterfly_guy.research.evaluate import session_vector
    from butterfly_guy.research.features import SessionFeatures
    from butterfly_guy.research.holdout import DEVELOPMENT
    from butterfly_guy.research.hypotheses import uses_features

    names = [v.name for v in variants if v.name != protocol.BASELINE]
    dev = [d for d in ds.sessions()["date"] if DEVELOPMENT[0] <= d <= DEVELOPMENT[1]]
    if not names or len(dev) < 2 * protocol.BLOCK:
        return {}
    arms = resolve([protocol.BASELINE, *names])
    features = (SessionFeatures.load(ds) if any(uses_features(v.entry) for v in arms)
                else None)
    ctx = RunContext(load_spx_config(), features=features)
    costs = Costs(ctx.config.execution.paper_commission_per_contract,
                  stressed_exit_floor=protocol.STRESSED_EXIT_FLOOR)
    result = run_variants(SessionLoader(ds, PROFILES[protocol.PROFILE]), arms, ctx,
                          start=DEVELOPMENT[0], end=DEVELOPMENT[1], costs=costs,
                          exit_delay=protocol.EXIT_DELAY)
    dates, _ = common_dates(result, list(result.runs))
    base = session_vector(result.runs[protocol.BASELINE].trades, dates, "stressed")
    return {n: protocol.calibrate_gate1(
        session_vector(result.runs[n].trades, dates, "stressed") - base, holdout_sessions)
        for n in names}


def cmd_register(args: argparse.Namespace) -> int:
    reg = Registry.for_dataset(Path(args.registry), args.dataset)
    git_sha, dirty = _git()
    try:
        ds = _dataset(args)
    except FileNotFoundError:
        ds = None  # not exported yet
    variants = resolve(args.variants.split(","))
    # Fit every fitted rule before appending anything, so a failed fit registers nothing.
    fitted = {v.name: _fit_for_registration(v, ds, args.profile)
              for v in variants if v.fit_window is not None}
    gate1 = _calibrate_for_registration(variants, ds, args.holdout_sessions) if ds else {}
    for v in variants:
        extra = ({"fitted": fitted[v.name], "fit_profile": args.profile}
                 if v.name in fitted else {})
        if v.name in gate1:
            extra["gate1"] = gate1[v.name]
        rec = reg.append("register", variant=v.name, definition=v.definition(),
                         definition_hash=v.definition_hash(), note=args.note or "",
                         git_sha=git_sha, git_dirty=dirty,
                         dataset_hash=ds.hash if ds is not None else None, **extra)
        shown = f"; fitted {rec['fitted']} under {args.profile}" if "fitted" in rec else ""
        if "gate1" in rec:
            shown += f"; gate-1 levels {rec['gate1']['levels']}"
            missed = [k for k, ok in rec["gate1"]["reached"].items() if not ok]
            if missed:
                shown += f" (cannot be calibrated for k = {', '.join(missed)})"
        print(f"registered {v.name} {rec['definition_hash'][:12]} (seq {rec['seq']}){shown}")
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
    from butterfly_guy.research.features import SessionFeatures
    from butterfly_guy.research.hypotheses import uses_features

    if ds.manifest.underlying != "SPX":
        raise ValueError("alternate instruments require replay-local with their own config")
    profile = PROFILES[profile_name]
    names = [n for n in names if n != args.baseline]
    variants = resolve([args.baseline, *names])
    features = (SessionFeatures.load(ds) if any(uses_features(v.entry) for v in variants)
                else None)
    ctx = RunContext(load_spx_config(), features=features)
    floor = 0.0 if args.floor_stressed_exits else None
    costs = Costs(ctx.config.execution.paper_commission_per_contract, stressed_exit_floor=floor)
    scorer = TiesetScorer() if tieset else None
    result = run_variants(SessionLoader(ds, profile), variants, ctx, start=start, end=end,
                          costs=costs, exit_delay=args.exit_delay, tieset=scorer)
    params = EvalParams(split=args.split, bootstrap_reps=args.reps,
                        bootstrap_block=args.block, rolling_block=args.rolling_block)
    accounting: dict = {"exit_delay_snapshots": args.exit_delay}
    if floor is not None:  # recorded only when set, so unfloored run ids are unchanged
        accounting["stressed_exit_floor"] = floor
    meta = {
        "dataset": ds.name, "dataset_hash": ds.hash, "profile": asdict(profile),
        "config_sha256": sha256_file(SPX_CONFIG), "start": str(start), "end": str(end),
        "baseline": args.baseline, "eval": params.as_dict(),
        "accounting": accounting,
        "variants": {n: {"definition": r.variant.definition(),
                         "definition_hash": r.variant.definition_hash()}
                     for n, r in result.runs.items()},
    }
    if features is not None:
        meta["inputs"] = features.inputs
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


def _code_unchanged_since(sha: str) -> bool:
    """Whether `src/` and `configs/` at HEAD are identical to those at commit `sha`."""
    if not sha:
        return False
    diff = subprocess.run(["git", "diff", "--quiet", sha, "HEAD", "--", "src", "configs"],
                          capture_output=True, cwd=REPO_ROOT)
    return diff.returncode == 0


def cmd_holdout(args: argparse.Namespace) -> int:
    """The pre-registered holdout evaluation (`protocol.py`). Every check that can refuse
    runs before any holdout session is replayed, and every evaluation is recorded."""
    from butterfly_guy.research import protocol
    from butterfly_guy.research.evaluate import session_vector
    from butterfly_guy.research.features import SessionFeatures
    from butterfly_guy.research.hypotheses import uses_features
    from butterfly_guy.research.report import markdown
    from butterfly_guy.research.simulate import fit_variants

    _quiet_logs()
    t0 = time.monotonic()
    ds = _dataset(args)
    reg = Registry.for_dataset(Path(args.registry), ds.name)
    unseal = _unseal(args, ds.name)
    records = reg.records()
    regs = protocol.registrations(records, unseal.registry_seq)
    protocol.check_registered(regs, CATALOG)
    git_sha, dirty = _git()
    if dirty:
        raise protocol.ProtocolError("src/ or configs/ has uncommitted changes")
    for sha in sorted({r.get("git_sha", "") for r in regs}):
        if not _code_unchanged_since(sha):
            raise protocol.ProtocolError(
                f"src/ or configs/ changed since the registration commit {sha[:12]}")
    if not any(h.get("holdout_sessions", 0) > 0 for h in ds.manifest.history):
        raise protocol.ProtocolError(f"{ds.name} holds no holdout sessions yet")
    names = [protocol.BASELINE, *(r["variant"] for r in regs)]
    first = protocol.check_rerun(records, unseal_seq=unseal.registry_seq,
                                 dataset_hash=ds.hash, variants=names,
                                 code_unchanged_since=_code_unchanged_since)

    variants = resolve(names)
    features = (SessionFeatures.load(ds) if any(uses_features(v.entry) for v in variants)
                else None)
    ctx = RunContext(load_spx_config(), features=features)
    profile = PROFILES[protocol.PROFILE]
    loader = SessionLoader(ds, profile, unseal)
    variants = fit_variants(variants, loader, ctx)  # each on its own development window
    fitted = {v.name: v.definition()["entry"]["fitted"] for v in variants
              if v.fit_window is not None}
    protocol.check_fitted(regs, fitted)

    costs = Costs(ctx.config.execution.paper_commission_per_contract,
                  stressed_exit_floor=protocol.STRESSED_EXIT_FLOOR)
    scorer = TiesetScorer()
    result = run_variants(loader, variants, ctx, start=protocol.WINDOW[0],
                          end=protocol.WINDOW[1], costs=costs, exit_delay=protocol.EXIT_DELAY,
                          tieset=scorer)
    params = EvalParams(split=protocol.SPLIT, bootstrap_reps=protocol.REPS,
                        bootstrap_block=protocol.BLOCK, bootstrap_seed=protocol.SEED)
    ev = evaluate(result, protocol.BASELINE, params)
    dates, _ = common_dates(result, list(result.runs))
    if not dates:
        raise protocol.ProtocolError("no holdout session could be evaluated")
    vec = {n: {m: session_vector(r.trades, dates, m) for m in ("stressed", "stressed_delayed")}
           for n, r in result.runs.items()}
    base = vec[protocol.BASELINE]
    k = len(regs)
    gate_rows = {r["variant"]: protocol.gates(
        vec[r["variant"]]["stressed"], base["stressed"], vec[r["variant"]]["stressed_delayed"],
        base["stressed_delayed"], dates, k, tail=float(r["gate1"]["levels"][str(k)]))
        for r in regs}

    meta = {
        "dataset": ds.name, "dataset_hash": ds.hash, "profile": asdict(profile),
        "config_sha256": sha256_file(SPX_CONFIG), "start": str(protocol.WINDOW[0]),
        "end": str(protocol.WINDOW[1]), "baseline": protocol.BASELINE, "eval": params.as_dict(),
        "accounting": {"exit_delay_snapshots": protocol.EXIT_DELAY,
                       "stressed_exit_floor": protocol.STRESSED_EXIT_FLOOR},
        "variants": {n: {"definition": r.variant.definition(),
                         "definition_hash": r.variant.definition_hash()}
                     for n, r in result.runs.items()},
        "protocol": protocol.describe(),
        "unseal": {"registry_seq": unseal.registry_seq, "registered": list(unseal.registered)},
        "tieset": scorer.params(),
    }
    if features is not None:
        meta["inputs"] = features.inputs
    results = {"meta": meta, "evaluation": ev, "gates": gate_rows,
               "tiesets": scorer.summary(list(result.runs), dates)}

    run_id = hashlib.sha256(canonical_json(meta).encode()).hexdigest()[:12]
    out_dir = Path(args.out) / ds.name / "holdout" / run_id
    results_hash = hashlib.sha256(dump_canonical(results).encode()).hexdigest()
    reproduction = None
    if first is not None:
        reproduction = {"of": first["run_id"],
                        "same_results": first.get("results_sha256") == results_hash}
    stages = {}
    for name, run in result.runs.items():
        rec = reg.append(
            "evaluate", variant=name, definition=run.variant.definition(),
            definition_hash=run.variant.definition_hash(), dataset_hash=ds.hash,
            git_sha=git_sha, git_dirty=dirty, run_id=run_id, profile=protocol.PROFILE,
            config_sha256=meta["config_sha256"], results_sha256=results_hash,
            scope=protocol.SCOPE, unseal_seq=unseal.registry_seq, k=len(regs),
            gates=gate_rows.get(name), reproduction=reproduction)
        stages[name] = rec["stage"]
    provenance = {
        "run_id": run_id, "git_sha": git_sha, "git_dirty": dirty,
        "command": " ".join(shlex.quote(a) for a in ["python", "-m", "butterfly_guy.research",
                                                      *sys.argv[1:]]),
        "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "registry": {"path": str(reg.path.relative_to(REPO_ROOT)) if reg.path.is_relative_to(
            REPO_ROOT) else str(reg.path), "tried": reg.tried(ds.hash), "recorded": True},
        "stages": stages, "reproduction": reproduction,
        "run_seconds": round(time.monotonic() - t0, 1),
    }

    def render(res: dict, prov: dict) -> str:
        text = markdown(res, prov)
        cut = text.index("Primary accounting")
        section = protocol.markdown_section(res["gates"], fitted,
                                            reproduction["of"] if reproduction else None)
        return text[:cut] + "\n".join(section) + "\n" + text[cut:]

    _finish(out_dir, results, result, provenance, render)
    if reproduction and not reproduction["same_results"]:
        print(f"WARNING: results differ from the first holdout run {reproduction['of']}")
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


def cmd_mechanism(args: argparse.Namespace) -> int:
    from butterfly_guy.research import mechanism
    from butterfly_guy.research.volindex import DAILY_FILE

    ds = _dataset(args)
    read_at = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    if args.spx_csv:
        raw, source = Path(args.spx_csv).read_bytes(), f"local file {args.spx_csv}"
    else:
        raw, source = mechanism.fetch_spx(), mechanism.SPX_URL
    results, table = mechanism.run(mechanism.parse_spx_csv(raw), ds.aux_table(DAILY_FILE),
                                   args.start, args.end)
    inputs = {
        "spx_csv": {"source": source, "sha256": hashlib.sha256(raw).hexdigest(),
                    "bytes": len(raw), "read_at": read_at},
        "vol_daily": {"dataset": ds.name, "file": DAILY_FILE,
                      "sha256": ds.manifest.aux[DAILY_FILE]["sha256"], "aux_hash": ds.aux_hash},
    }
    # The run id covers the in-window inputs and the rule, not the raw file, which Cboe
    # extends every day.
    run_id = hashlib.sha256(canonical_json({
        "window": results["window"], "inputs_in_window": results["inputs_in_window"],
        "decision_rule": results["decision_rule"]}).encode()).hexdigest()[:12]
    out_dir = Path(args.out) / "mechanism" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {"mechanism.json": dump_canonical(results),
             "sessions.csv": table.to_csv(index=False, lineterminator="\n")}
    hashes = {}
    for name, text in files.items():
        (out_dir / name).write_text(text)
        hashes[name] = hashlib.sha256(text.encode()).hexdigest()
    git_sha, dirty = _git()
    provenance = {
        "run_id": run_id, "label": mechanism.LABEL, "git_sha": git_sha, "git_dirty": dirty,
        "command": " ".join(shlex.quote(a) for a in ["python", "-m", "butterfly_guy.research",
                                                      *sys.argv[1:]]),
        "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "registry": "not recorded: a descriptive mechanism check is not a rule evaluation",
        "inputs": inputs, "hashes": hashes,
    }
    (out_dir / "provenance.json").write_text(dump_canonical(provenance))
    (out_dir / "report.md").write_text(mechanism.markdown(results, provenance))
    print((out_dir / "report.md").read_text())
    print(f"artifacts: {out_dir}")
    return 0

def _unseal(args: argparse.Namespace, ds_name: str):
    """A registry-verified holdout unseal, or None when not asked for."""
    if args.unseal_holdout is None:
        return None
    from butterfly_guy.research.dataset import Manifest
    from butterfly_guy.research.holdout import verify_unseal

    root = (Path(args.cache) if args.cache else default_cache_root()) / ds_name
    return verify_unseal(Registry.for_dataset(Path(args.registry), ds_name),
                         Manifest.load(root / "manifest.json"), args.unseal_holdout)


def cmd_export_history(args: argparse.Namespace) -> int:
    from butterfly_guy.research.history import (
        HistoryPlan,
        QualityNotPassedError,
        get_source,
        write_history,
    )

    options = {k: v for k, v in (("spx_minutes", args.spx_minutes),
                                 ("vix_minutes", args.vix_minutes)) if v}
    if args.recorded:
        options["recorded"] = Dataset.open(args.recorded, Path(args.cache) if args.cache else None)
    try:
        source = get_source(args.provider, **options)
    except (NotImplementedError, FileNotFoundError, TypeError) as exc:
        print(exc, file=sys.stderr)
        return 2
    dataset = (args.dataset if args.dataset != DEFAULT_DATASET
               else f"{DEFAULT_DATASET}_{args.provider}")
    plan = HistoryPlan(args.start, args.end, dataset, max_cost=args.max_cost,
                       unseal=_unseal(args, dataset))
    try:
        write_history(source, plan, Path(args.cache) if args.cache else None)
    except QualityNotPassedError as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


def cmd_exclude_sessions(args: argparse.Namespace) -> int:
    from butterfly_guy.research.history import exclude_sessions

    dates = [_date(x) for x in args.dates.split(",")]
    m = exclude_sessions(args.dataset, dates, args.reason, args.evidence,
                         Path(args.cache) if args.cache else None)
    print(f"{args.dataset}: excluded {', '.join(d.isoformat() for d in dates)}; "
          f"dataset hash {m.dataset_hash}")
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    from butterfly_guy.research.history import coverage

    ds = _dataset(args)
    out = coverage(ds, args.start, args.end, _unseal(args, ds.name))
    path = Path(args.out) / ds.name / "coverage" / f"coverage_{out['summary']['first']}_" \
        f"{out['summary']['last']}_{ds.hash[:12]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_canonical({"label": args.label, **out}))
    print(json.dumps({"label": args.label, "dataset": ds.name, "dataset_hash": ds.hash,
                      **out["summary"]}, indent=1))
    print(f"written: {path}")
    return 0


def cmd_validate_vendor(args: argparse.Namespace) -> int:
    from butterfly_guy.research import validate
    from butterfly_guy.research.volindex import fetch_cboe

    _quiet_logs()
    cache = Path(args.cache) if args.cache else None
    helios = Dataset.open(args.reference, cache)
    vendor = Dataset.open(args.vendor_dataset, cache)
    if getattr(args, "cboe_spx", None):
        raw = Path(args.cboe_spx).read_bytes()
        url = "explicit cached Cboe SPX_History.csv"
    else:
        url, raw = fetch_cboe(("SPX",))["SPX"]
    t0 = time.monotonic()
    results = validate.validate(helios, vendor, args.start, args.end,
                                RunContext(load_spx_config()), validate.parse_cboe_spx(raw))
    results["meta"]["cboe_spx"] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest()}
    run_id = hashlib.sha256(canonical_json(results["meta"]).encode()).hexdigest()[:12]
    out_dir = Path(args.out) / vendor.name / "validation" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    git_sha, dirty = _git()
    provenance = {"run_id": run_id, "git_sha": git_sha, "git_dirty": dirty,
                  "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                  "run_seconds": round(time.monotonic() - t0, 1),
                  "config_sha256": sha256_file(SPX_CONFIG)}
    text = dump_canonical(results)
    (out_dir / "validation.json").write_text(text)
    provenance["validation_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    (out_dir / "provenance.json").write_text(dump_canonical(provenance))
    (out_dir / "report.md").write_text(validate.markdown(results, provenance))
    print((out_dir / "report.md").read_text())
    print(f"artifacts: {out_dir}")
    return 0 if results["pass"] else 1


def _index_crosscheck(files: dict, start: dt.date, end: dt.date) -> dict:
    """The owner's minute files against Yahoo `^GSPC` and Cboe VIX daily OHLC (report only)."""
    import pandas as pd
    import yfinance

    from butterfly_guy.research import quality
    from butterfly_guy.research.thetadata import fetch_cboe, load_minute_file, parse_cboe

    minutes, notes = {}, {}
    for sym, meta in files.items():
        path = Path(meta["path"])
        if not path.is_file() or sha256_file(path) != meta["sha256"]:
            notes[sym] = "minute file missing or changed since the pull"
            continue
        minutes[sym] = load_minute_file(path)[0]
    raw = yfinance.download("^GSPC", start=start.isoformat(),
                            end=(end + dt.timedelta(days=1)).isoformat(), interval="1d",
                            auto_adjust=False, progress=False)
    raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
    spx = pd.DataFrame({"date": raw.index.date, "high": raw["High"].to_numpy(),
                        "low": raw["Low"].to_numpy()})
    vix = parse_cboe(fetch_cboe("VIX"), "VIX")
    out = quality.index_file_crosscheck(minutes, {"SPX": spx, "$VIX": vix}, start, end)
    spx_hash = hashlib.sha256(spx.to_csv(index=False).encode()).hexdigest()
    out["sources"] = {"SPX": {"yahoo": "^GSPC", "rows": len(spx), "sha256": spx_hash},
                      "$VIX": {"url": "cboe VIX_History.csv"}, "notes": notes}
    return out


def cmd_vendor_quality(args: argparse.Namespace) -> int:
    from butterfly_guy.research import quality
    from butterfly_guy.research.dataset import Manifest
    from butterfly_guy.research.validate import parse_cboe_spx
    from butterfly_guy.research.volindex import fetch_cboe

    cache = Path(args.cache) if args.cache else None
    helios = Dataset.open(args.reference, cache)
    vendor = Dataset.open(args.vendor_dataset, cache)
    if getattr(args, "cboe_spx", None):
        raw = Path(args.cboe_spx).read_bytes()
        url = "explicit cached Cboe SPX_History.csv"
    else:
        url, raw = fetch_cboe(("SPX",))["SPX"]
    t0 = time.monotonic()
    results = quality.run(vendor, helios, args.start, args.end, parse_cboe_spx(raw))
    results["meta"]["cboe_spx"] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest()}
    files = vendor.manifest.source.get("index_files")
    if files and args.start < VALIDATION[0]:
        if getattr(args, "cboe_spx", None):
            results["index_files_crosscheck"] = {"sources": {"status": "not acquired",
                "reason": "offline quality run; independent daily OHLC cross-check is separate"}}
        else:
            results["index_files_crosscheck"] = _index_crosscheck(files, args.start, args.end)
    run_id = hashlib.sha256(canonical_json({"meta": results["meta"], "range": results["range"],
                                            "thresholds": results["thresholds"]}).encode()
                            ).hexdigest()[:12]
    out_dir = Path(args.out) / vendor.name / "quality" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    git_sha, dirty = _git()
    at = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    provenance = {"run_id": run_id, "git_sha": git_sha, "git_dirty": dirty, "created_at": at,
                  "run_seconds": round(time.monotonic() - t0, 1)}
    text = dump_canonical(results)
    (out_dir / "quality.json").write_text(text)
    provenance["quality_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    (out_dir / "provenance.json").write_text(dump_canonical(provenance))
    (out_dir / "report.md").write_text(quality.markdown(results, provenance))
    manifest_path = vendor.root / "manifest.json"
    manifest = Manifest.load(manifest_path)
    manifest.history.append({**quality.history_entry(results, run_id, at),
                             "git_sha": git_sha, "git_dirty": dirty})
    manifest.save(manifest_path)
    print((out_dir / "report.md").read_text())
    print(f"artifacts: {out_dir}")
    return 0 if results["pass"] else 1


def cmd_schwab_fidelity(args: argparse.Namespace) -> int:
    from butterfly_guy.research import fidelity

    _quiet_logs()
    cache = Path(args.cache) if args.cache else None
    helios = Dataset.open(args.reference, cache)
    vendor = Dataset.open(args.vendor_dataset, cache)
    end = args.end or args.start
    summary, rows = fidelity.run(helios, vendor, args.start, end, load_spx_config())
    if not rows:
        print("no session in both datasets for the range", file=sys.stderr)
        return 2
    inputs = {"helios": summary["meta"]["helios"], "vendor": summary["meta"]["vendor"],
              "range": summary["range"], "config_sha256": sha256_file(SPX_CONFIG)}
    folder = fidelity.publish(Path(args.out), summary, rows, inputs,
                              args.run_date or dt.datetime.now(dt.UTC).date())
    print((folder / "report.md").read_text())
    print(fidelity.one_line(summary))
    print(f"artifacts: {folder}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m butterfly_guy.research", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", default=DEFAULT_DATASET)
    p.add_argument("--cache", default=None, help=f"cache root (default {default_cache_root()})")
    p.add_argument("--registry", default=str(REGISTRY_DIR))
    sub = p.add_subparsers(dest="command", required=True)
    from butterfly_guy.research.archive_cli import add_commands
    add_commands(sub, _date, REPORTS)
    from butterfly_guy.research.session_ledger import add_command
    add_command(sub, _date)

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

    ca = sub.add_parser("catalog", help="list catalog variants with their definition "
                        "hashes and registry history")
    ca.add_argument("--variants", default=None, help="comma list (default: all)")
    ca.set_defaults(func=cmd_catalog)

    r = sub.add_parser("register", help="pre-register catalog variants")
    r.add_argument("--variants", required=True, help=f"comma list from {', '.join(CATALOG)}")
    r.add_argument("--note", default="")
    r.add_argument("--profile", choices=sorted(PROFILES), default="vendor_1m",
                   help="profile a fitted rule is fitted under (recorded; the holdout "
                        "evaluation requires vendor_1m)")
    r.add_argument("--holdout-sessions", type=int, default=358,
                   help="planned holdout size the gate-1 calibration simulates (recorded; "
                        "358 without an Indices month, 421 with one)")
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
        sp.add_argument("--floor-stressed-exits", action="store_true",
                        help="book stressed and delayed intraday exits below $0 at $0 (the "
                        "vendor sweep's primary metric since 2026-09-29; recorded in the run)")

    run = sub.add_parser("run", help="evaluate variants against a baseline")
    evaluation_args(run)
    run.add_argument("--profile", choices=sorted(PROFILES), default="live")
    run.add_argument("--start", type=_date, default=None)
    run.add_argument("--end", type=_date, default=None)
    run.add_argument("--no-tieset", action="store_true", help="skip near-tied fly scoring")
    run.set_defaults(func=cmd_run)

    ho = sub.add_parser("holdout", help="the pre-registered holdout evaluation (registered "
                        "variants only; every look is recorded)")
    ho.add_argument("--unseal-holdout", type=int, required=True, metavar="SEQ",
                    help="registry seq of the last register record; verified against the "
                         "registry and the dataset history before the holdout opens")
    ho.add_argument("--out", default=str(REPORTS))
    ho.set_defaults(func=cmd_holdout)

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

    mc = sub.add_parser("mechanism",
                        help="DESCRIPTIVE H-TS1 mechanism check (development window, no registry)")
    mc.add_argument("--spx-csv", default=None,
                    help="a saved copy of Cboe's SPX_History.csv (default: fetch it)")
    mc.add_argument("--start", type=_date, default=dt.date(2022, 5, 16))
    mc.add_argument("--end", type=_date, default=dt.date(2024, 6, 28))
    mc.add_argument("--out", default=str(REPORTS))
    mc.set_defaults(func=cmd_mechanism)

    def unseal_arg(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--unseal-holdout", type=int, default=None, metavar="SEQ",
                        help="registry seq of the last register record; verified against the "
                             "registry and the dataset history before the holdout opens")

    eh = sub.add_parser("export-history", help="vendor history into spx_0dte_<provider>")
    eh.add_argument("--provider", required=True, help="thetadata")
    eh.add_argument("--spx-minutes", help="SPX 1-minute CSV (thetadata; US Central, bar end)")
    eh.add_argument("--vix-minutes", help="VIX 1-minute CSV (thetadata; US Central, bar end)")
    eh.add_argument("--recorded", default=None, metavar="DATASET",
                    help="recorded dataset for $VIX and the SPX open after the minute files end "
                         "(thetadata; e.g. spx_0dte)")
    eh.add_argument("--start", type=_date, required=True)
    eh.add_argument("--end", type=_date, required=True)
    eh.add_argument("--max-cost", type=float, default=None,
                    help="owner-approved dollars for a usage-billed pull")
    unseal_arg(eh)
    eh.set_defaults(func=cmd_export_history)

    xs = sub.add_parser("exclude-sessions",
                        help="take sessions out of a vendor dataset for a data-quality reason")
    xs.add_argument("--dates", required=True, help="comma-separated YYYY-MM-DD")
    xs.add_argument("--reason", required=True)
    xs.add_argument("--evidence", required=True, help="e.g. the vendor-quality run id")
    xs.set_defaults(func=cmd_exclude_sessions)

    vq = sub.add_parser("vendor-quality",
                        help="data-quality gates Q1-Q6 on a vendor dataset, Helios side by side")
    vq.add_argument("--vendor-dataset", required=True)
    vq.add_argument("--reference", default=DEFAULT_DATASET)
    vq.add_argument("--start", type=_date, default=VALIDATION[0])
    vq.add_argument("--end", type=_date, default=VALIDATION[1])
    vq.add_argument("--out", default=str(REPORTS))
    vq.add_argument("--cboe-spx", help="explicit cached Cboe daily CSV; avoids network")
    vq.set_defaults(func=cmd_vendor_quality)

    vv = sub.add_parser("validate-vendor", help="fidelity validation against the Helios export")
    vv.add_argument("--vendor-dataset", required=True)
    vv.add_argument("--reference", default=DEFAULT_DATASET)
    vv.add_argument("--start", type=_date, default=dt.date(2026, 3, 13))
    vv.add_argument("--end", type=_date, default=dt.date(2026, 9, 25))
    vv.add_argument("--out", default=str(REPORTS))
    vv.set_defaults(func=cmd_validate_vendor)

    sf = sub.add_parser("schwab-fidelity",
                        help="report-only agreement of recorded Helios chains with ThetaData")
    sf.add_argument("--vendor-dataset", required=True)
    sf.add_argument("--reference", default=DEFAULT_DATASET, help="recorded Helios dataset")
    sf.add_argument("--start", type=_date, required=True)
    sf.add_argument("--end", type=_date, default=None, help="default: --start")
    sf.add_argument("--out", default=str(REPO_ROOT / "reports" / "data_management"
                                         / "schwab_fidelity"))
    sf.add_argument("--run-date", type=_date, default=None,
                    help="artifact folder date (default: today, UTC)")
    sf.set_defaults(func=cmd_schwab_fidelity)

    cv = sub.add_parser("coverage", help="per-session coverage of a dataset")
    cv.add_argument("--start", type=_date, default=None)
    cv.add_argument("--end", type=_date, default=None)
    cv.add_argument("--label", default="",
                    help='e.g. "in-sample development data"')
    cv.add_argument("--out", default=str(REPORTS))
    unseal_arg(cv)
    cv.set_defaults(func=cmd_coverage)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(arguments)
    if args.command == "session-quality-ledger":
        if not any(x == "--dataset" or x.startswith("--dataset=") for x in arguments):
            parser.error("session-quality-ledger requires an explicit --dataset")
        if args.cache is None:
            parser.error("session-quality-ledger requires an explicit --cache")
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        if args.command not in {"inventory-local", "audit-local", "import-local",
                                "cache-inputs", "cache-daily", "replay-local",
                                "session-quality-ledger"}:
            raise
        print(str(exc), file=sys.stderr)
        return 2
