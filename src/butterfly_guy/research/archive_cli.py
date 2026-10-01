"""Local source commands on the canonical research CLI; never register/evaluate holdout."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
import tempfile
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa

from butterfly_guy.core.config import load_config
from butterfly_guy.research.accounting import Costs
from butterfly_guy.research.dataset import Dataset, Manifest, sha256_file, write_table
from butterfly_guy.research.entry import PROFILES, REPO_ROOT, RunContext, SessionLoader
from butterfly_guy.research.history import HistoryPlan, QualityNotPassedError
from butterfly_guy.research.holdout import guard
from butterfly_guy.research.lifecycle import replay_position
from butterfly_guy.research.local import SETS, LocalThetaDataSource, audit, import_local, inventory


def _clean(value):
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_clean(v) for v in value]
    if isinstance(value, (float, np.floating)) and not math.isfinite(value):
        return None
    return value


def _artifact(args, kind: str, body: dict) -> Path:
    body = _clean(body)
    payload = json.dumps(body, sort_keys=True, indent=1, default=str, allow_nan=False) + "\n"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    folder = Path(args.out) / args.dataset / kind / digest[:12]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{kind}.json"
    if path.exists() and path.read_text() != payload:
        raise ValueError("artifact identity collision")
    path.write_text(payload)
    provenance = {"command": sys.argv, "git_sha": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, cwd=REPO_ROOT).strip(),
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain", "--", "src"],
                                                  text=True, cwd=REPO_ROOT)),
        "created_at": dt.datetime.now(dt.UTC).isoformat(), "sha256": digest,
        "source_sha256": {str(p.relative_to(REPO_ROOT)): sha256_file(p)
                          for p in sorted((REPO_ROOT / "src").rglob("*.py"))},
        "python": platform.python_version(), "dependencies": {
            x: importlib.metadata.version(x) for x in ("pandas", "numpy", "pyarrow")}}
    # Never rewrite an existing reproducibility record on a repeat run.
    prov = folder / "provenance.json"
    if not prov.exists():
        prov.write_text(json.dumps(provenance, indent=1))
    print(f"{kind}: {path}")
    return path


def _source(args) -> LocalThetaDataSource:
    # Guard before resolving even the input dataset or constructing the archive source.
    guard(args.start, args.end, what="local archive command", dataset=args.dataset)
    support = Dataset.open(args.support, Path(args.cache) if args.cache else None)
    minutes = {}
    for symbol, path in ((SETS[args.set][1], args.index_minutes), ("$VIX", args.vix_minutes)):
        if path:
            minutes[symbol] = Path(path)
    return LocalThetaDataSource(Path(args.archive), args.set, args.dataset, support,
                                minutes=minutes,
                                daily_cache=Path(args.daily_cache) if args.daily_cache else None)


def cmd_inventory(args) -> int:
    _artifact(args, "inventory", inventory([Path(x) for x in args.archive]))
    return 0


def cmd_audit(args) -> int:
    source = _source(args)
    rows = audit(source, args.start, args.end)
    _artifact(args, "input-audit", {"source": source.describe(), "set": args.set,
                                   "range": [str(args.start), str(args.end)], "sessions": rows,
                                   "usable": sum(r["status"] == "usable" for r in rows)})
    return 0


def cmd_import(args) -> int:
    source = _source(args)
    quality = (Dataset.open(args.quality_dataset, Path(args.cache) if args.cache else None)
               if args.quality_dataset else None)
    try:
        m = import_local(source, HistoryPlan(args.start, args.end, args.dataset,
                                             strike_margin=args.strike_margin),
                         Path(args.cache) if args.cache else None, quality)
    except QualityNotPassedError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _artifact(args, "normalization", {"dataset": m.dataset, "hash": m.dataset_hash,
                                     "export": m.export, "source": m.source,
                                     "history": m.history})
    return 0


def cmd_cache_inputs(args) -> int:
    """Explicit, offline snapshot of existing observations and their source manifests."""
    guard(args.start, args.end, what="supporting-input snapshot", dataset=args.dataset)
    cache = Path(args.cache) if args.cache else None
    src = Dataset.open(args.input_dataset, cache)
    daily = Dataset.open(args.daily_dataset, cache) if args.daily_dataset else src
    root = Path(args.output_cache) / args.dataset
    if root.exists():
        raise ValueError("supporting-input output exists; choose a new identity")
    published = root
    root.parent.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix=f".{args.dataset}.", dir=root.parent))
    m = Manifest(args.dataset, src.manifest.underlying,
                 {"kind": "offline_support_snapshot", "inputs": {
                     src.name: {"hash": src.hash, "source": src.manifest.source},
                     daily.name: {"hash": daily.hash, "source": daily.manifest.source}},
                  "approved_exclusions": [h for h in daily.manifest.history
                                          if h.get("mode") == "exclude_sessions"],
                  "settlement": daily.manifest.source.get("settlement", {}),
                  "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
                  "timezone": "UTC; daily available only after official session close"},
                 {"range": [str(args.start), str(args.end)]})
    bars = daily.daily_bars()
    bars = bars[bars.date.between(args.start, args.end)]
    m.files["daily_bars.parquet"] = write_table(pa.Table.from_pandas(bars, preserve_index=False),
                                              root / "daily_bars.parquet")
    ticks = []
    for symbol in (src.manifest.underlying, "$VIX"):
        ts, px = src.spot_ticks(symbol)
        from butterfly_guy.research.market import et_us
        keep = (ts >= et_us(args.start, 0, 0)) & (ts <= et_us(args.end, 23, 59))
        ticks.append(pd.DataFrame({"ts_us": ts[keep], "price": px[keep], "underlying": symbol}))
    m.files["spot_ticks.parquet"] = write_table(pa.Table.from_pandas(pd.concat(ticks),
                                                                    preserve_index=False),
                                              root / "spot_ticks.parquet")
    m.save(root / "manifest.json")
    root.rename(published)
    _artifact(args, "supporting-inputs", {"dataset": args.dataset, "hash": m.dataset_hash,
                                        "source": m.source})
    return 0


def cmd_replay(args) -> int:
    guard(args.start, args.end, what="local lifecycle replay", dataset=args.dataset)
    if args.lifecycle != "0dte" and args.entry_spec != "borrowed-0dte-controls":
        raise ValueError("1-DTE requires explicit --entry-spec borrowed-0dte-controls; "
                         "this verifies mechanics, not strategy suitability")
    from butterfly_guy.research.cli import _quiet_logs
    _quiet_logs()
    cache = Path(args.cache) if args.cache else None
    ds = Dataset.open(args.dataset, cache)
    if ds.manifest.export.get("kind") != "local_parquet":
        raise ValueError("replay-local requires a normalized local archive dataset")
    asset = ds.manifest.underlying
    config_path = Path(args.config) if args.config else REPO_ROOT / "configs" / {
        "SPX": "config.yaml", "NDX": "config_ndx.yaml", "XSP": "config_xsp.yaml"}[asset]
    ctx = RunContext(load_config(config_path=config_path), asset=asset)
    profile = replace(PROFILES["vendor_1m"], name="local_observed_1m", integer_strikes=False)
    loader = SessionLoader(ds, profile, lifecycle=args.lifecycle)
    expiry = Dataset.open(args.expiry_dataset, cache) if args.expiry_dataset else None
    expiry_loader = SessionLoader(expiry, profile) if expiry else None
    if args.floor_stressed_exits and asset != "SPX":
        raise ValueError("approved vendor stressed-exit floor applies only to SPX")
    if args.exit_policy == "hold-to-expiry" and args.lifecycle != "carry":
        raise ValueError("hold-to-expiry exit policy requires the carry lifecycle")
    costs = Costs(ctx.config.execution.paper_commission_per_contract,
                  stressed_exit_floor=0.0 if args.floor_stressed_exits else None)
    records = [replay_position(loader, d, ctx, lifecycle=args.lifecycle,
                               expiry_loader=expiry_loader, end=args.end, costs=costs,
                               required=tuple(args.require_capability or ()),
                               rules=() if args.exit_policy == "hold-to-expiry" else None)
               for d in loader.dates(args.start, args.end)]
    body = {"dataset": ds.name, "dataset_hash": ds.hash, "source": ds.manifest.source,
            "raw_inputs": ds.manifest.history[0]["raw_inputs"],
            "profile": asdict(profile), "lifecycle": args.lifecycle,
            "entry_spec": args.entry_spec or "configured-0dte", "exit_policy": args.exit_policy,
            "one_dte_model_limit": "borrowed VIX intraday anchoring is not a total "
                                   "time-to-expiration model; no suitability claim",
            "config_sha256": sha256_file(config_path), "range": [str(args.start), str(args.end)],
            "expiry_dataset_hash": expiry.hash if expiry else None,
            "costs": asdict(costs), "multiplier": 100, "slippage_per_leg": 0.05,
            "exit_delay_grid_ticks": 1, "quote_observation_max_age_s": 120,
            "trades": records, "exclusions": {str(d): r for d, r in loader.skipped.items()},
            "portfolio_returns": "undefined; independent one-fly mechanics",
            "floor_uses": sum(t.get("floor_uses", 0) for t in records)}
    _artifact(args, "replay", body)
    failed = any(t["status"] in {"unresolved", "unpriceable", "excluded"} for t in records)
    return 1 if failed else 0


def cmd_cache_daily(args) -> int:
    """Explicit acquisition; evaluation never invokes this command implicitly."""
    from butterfly_guy.research.thetadata import CBOE_URL, fetch_cboe
    root = Path(args.directory)
    root.mkdir(parents=True, exist_ok=True)
    records = {}
    for symbol in ("SPX", "VIX"):
        raw = fetch_cboe(symbol)
        digest = hashlib.sha256(raw).hexdigest()
        path = root / f"{symbol}_{digest}.csv"
        if not path.exists():
            temp = path.with_suffix(".tmp")
            temp.write_bytes(raw)
            temp.replace(path)
        records[symbol] = {"path": str(path.resolve()), "source_url": CBOE_URL.format(index=symbol),
                           "retrieved_at": dt.datetime.now(dt.UTC).isoformat(), "sha256": digest,
                           "symbol": symbol, "timezone": "America/New_York",
                           "availability": "daily closing observation; usable for prior-session "
                                           "features only on later sessions; historical vendor "
                                           "publication time is not recorded"}
    text = json.dumps(records, sort_keys=True, indent=1)
    path = root / (hashlib.sha256(text.encode()).hexdigest()[:12] + ".json")
    path.write_text(text)
    print(f"cached daily observations: {path}")
    return 0


def add_commands(sub, date_type, reports):
    daily = sub.add_parser("cache-daily", help="explicit Cboe daily acquisition, before evaluation")
    daily.add_argument("--directory", required=True)
    daily.set_defaults(func=cmd_cache_daily)
    inv = sub.add_parser("inventory-local", help="catalog/Parquet reconciliation, no holdout I/O")
    inv.add_argument("--archive", action="append", required=True)
    inv.add_argument("--out", default=str(reports))
    inv.set_defaults(func=cmd_inventory)
    for name, func in (("audit-local", cmd_audit), ("import-local", cmd_import)):
        p = sub.add_parser(name, help="offline local ThetaData input " + name.split("-")[0])
        p.add_argument("--archive", required=True)
        p.add_argument("--set", choices=sorted(SETS), required=True)
        p.add_argument("--support", required=True, help="cached normalized supporting observations")
        p.add_argument("--daily-cache", help="cache-daily JSON with source hashes/retrieval times")
        p.add_argument("--index-minutes", help="owner index CSV, Central timezone/bar end")
        p.add_argument("--vix-minutes", help="owner VIX CSV, Central timezone/bar end")
        p.add_argument("--start", type=date_type, required=True)
        p.add_argument("--end", type=date_type, required=True)
        p.add_argument("--out", default=str(reports))
        if name == "import-local":
            p.add_argument("--strike-margin", type=float, default=400.0)
            p.add_argument("--quality-dataset",
                           help="passing local validation dataset, same inputs")
        p.set_defaults(func=func)
    p = sub.add_parser("cache-inputs", help="explicit offline snapshot of supporting observations")
    p.add_argument("--output-cache", required=True)
    p.add_argument("--input-dataset", required=True)
    p.add_argument("--daily-dataset")
    p.add_argument("--start", type=date_type, required=True)
    p.add_argument("--end", type=date_type, required=True)
    p.add_argument("--out", default=str(reports))
    p.set_defaults(func=cmd_cache_inputs)
    p = sub.add_parser("replay-local", help="one-fly lifecycle and leg accounting verification")
    p.add_argument("--start", type=date_type, required=True)
    p.add_argument("--end", type=date_type, required=True)
    p.add_argument("--lifecycle", choices=["0dte", "intraday", "carry"], required=True)
    p.add_argument("--exit-policy", choices=["configured", "hold-to-expiry"],
                   default="configured")
    p.add_argument("--expiry-dataset")
    p.add_argument("--entry-spec", choices=["borrowed-0dte-controls"])
    p.add_argument("--config")
    p.add_argument("--require-capability", action="append")
    p.add_argument("--floor-stressed-exits", action="store_true")
    p.add_argument("--out", default=str(reports))
    p.set_defaults(func=cmd_replay)
