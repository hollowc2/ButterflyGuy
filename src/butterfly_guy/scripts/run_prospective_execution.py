"""Run the prospective execution-validation study for a frozen strategy.

Read-only research workflow: it reproduces the frozen decision for each completed
session, prices it under the corrected-midpoint, marketable, and stressed-marketable
models, and appends immutable records to a pre-registered cohort. It never touches
production configuration, services, schemas, or order routing.

    init    create a cohort manifest and empty ledgers
    update  append every completed session through a date
    report  regenerate summary.json / summary.md without touching the ledger
    verify  audit manifest, ledgers, and record hashes
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import sys
from pathlib import Path

import asyncpg

from butterfly_guy.backtest.execution_accounting import price_frozen_trade
from butterfly_guy.backtest.prospective_execution import (
    COHORT_ROOT,
    EXECUTABLE_MODELS,
    CohortError,
    CohortSpec,
    SessionOutcome,
    build_manifest,
    daily_runs_path,
    load_manifest,
    read_jsonl,
    record_session,
    require_frozen_manifest,
    summarize_cohort,
    trades_path,
    verify_cohort,
    write_manifest,
    write_reports,
)
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.logging import get_logger
from butterfly_guy.scripts.run_backtest_db import (
    ASSET_CONFIG_PATHS,
    _patch_chain_cache,
    _sim_parity_fields_from_args,
    backtest_entry_price,
    day_with_monitoring_bars,
    discover_dates,
    find_entry_in_window,
    load_asset_config,
    load_date_data,
    load_monitoring_chains,
    merge_chains,
    resolve_db_dsn,
)
from butterfly_guy.scripts.run_backtest_db import (
    parse_args as parse_backtest_args,
)
from butterfly_guy.strategy.entry_selection import entry_selection_config

log = get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DATABASE_TABLES = (
    "option_chain_snapshots",
    "spot_prices",
    "daily_bars",
    "monitoring_leg_quotes",
)
DRY_RUN_LABEL = "dry-run"

#: Namespace fields that describe the run range or optional reports, not the strategy.
NON_STRATEGY_ARGS = frozenset(
    {
        "start",
        "end",
        "sweep",
        "top",
        "compare_synthetic",
        "compare_synthetic_same_entry",
        "execution_accounting_report",
        "html_report",
        "report",
        "live_pinned_replay",
        "selection_parity_report",
    }
)


# ---------------------------------------------------------------------------
# Frozen strategy parameters
# ---------------------------------------------------------------------------

def frozen_backtest_args(asset: str) -> argparse.Namespace:
    """Resolve the frozen backtest defaults for *asset* from the live config."""
    argv = sys.argv
    sys.argv = [
        "run_backtest_db.py",
        "--asset",
        asset,
        "--execution-accounting-report",
    ]
    try:
        return parse_backtest_args()
    finally:
        sys.argv = argv


def _jsonable(value):
    if isinstance(value, (dt.time, dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def strategy_parameter_snapshot(args: argparse.Namespace) -> dict:
    """Every strategy-affecting parameter, in a form the manifest can compare."""
    return {
        key: _jsonable(value)
        for key, value in sorted(vars(args).items())
        if key not in NON_STRATEGY_ARGS
    }


def require_frozen_parameters(manifest: dict, args: argparse.Namespace) -> None:
    """Refuse to append when resolved parameters differ from the frozen manifest."""
    current = strategy_parameter_snapshot(args)
    frozen = manifest["strategy_parameters"]
    changed = sorted(
        key
        for key in set(current) | set(frozen)
        if current.get(key) != frozen.get(key)
    )
    if changed:
        raise CohortError(
            f"cohort {manifest['cohort_id']} was frozen with different strategy "
            "parameters; close this cohort and start a new one. Changed: "
            + ", ".join(changed)
        )


# ---------------------------------------------------------------------------
# Session evaluation
# ---------------------------------------------------------------------------

async def evaluate_session(
    conn: asyncpg.Connection,
    *,
    date: dt.date,
    asset: str,
    args: argparse.Namespace,
    commission_per_contract: float,
) -> SessionOutcome:
    """Reproduce the frozen decision for one session using only that session's data."""
    live_config = load_asset_config(asset)
    method = args.method[0]
    selection_config = entry_selection_config(
        live_config,
        selection_method=method if args.method_provided else None,
        rr_min=args.rr_min[0] if args.rr_min_provided else None,
    )

    data = await load_date_data(conn, date, asset)
    if data is None:
        return SessionOutcome(
            session_date=date,
            status="incomplete_data",
            detail="no complete bar, chain, or VIX data for the session",
        )

    chain_times = sorted(data["chains"])
    data_range = {
        "first_snapshot": chain_times[0].isoformat() if chain_times else None,
        "last_snapshot": chain_times[-1].isoformat() if chain_times else None,
    }
    row_counts = {
        "entry_chain_snapshots": len(data["chains"]),
        "bars": len(data["bars"]),
    }
    if data["day"].settlement_spot is None:
        return SessionOutcome(
            session_date=date,
            status="incomplete_data",
            detail="official settlement not yet available",
            data_range=data_range,
            row_counts=row_counts,
        )

    entry = await find_entry_in_window(
        conn,
        data=data,
        date=date,
        asset=asset,
        direction_arg=args.direction[0],
        entry_pst=args.entry_time[0],
        args=args,
        config=selection_config,
        wing_widths=args.wing if args.wing_provided else None,
    )
    if entry is None:
        return SessionOutcome(
            session_date=date,
            status="no_signal",
            detail="no qualifying entry in the frozen entry window",
            data_range=data_range,
            row_counts=row_counts,
        )
    entry_bar, _entry_vix, direction, chosen = entry

    monitoring = await load_monitoring_chains(
        conn,
        date,
        asset,
        [chosen.lower_strike, chosen.center_strike, chosen.upper_strike],
        [chosen.direction],
    )
    full_chains = merge_chains(data["chains"], monitoring)
    row_counts["monitoring_snapshots"] = len(monitoring)
    row_counts["merged_snapshots"] = len(full_chains)

    params = SimulationParams(
        wing_width=chosen.wing_width,
        direction_override=direction,
        rr_min=args.rr_min[0],
        morning_drawdown=args.morning_dd[0],
        late_morning_drawdown=args.late_morning_dd[0],
        afternoon_drawdown=args.afternoon_dd[0],
        slippage=args.slippage,
        use_vix_center=(method == "VIX"),
        selection_method=method,
        max_cost_per_width=live_config.strategy.max_cost_per_width,
        max_loss_from_cost=live_config.profit_management.max_loss_from_cost,
        use_absolute_loss_stop=args.use_abs_stop,
        drawdown_schedule=args.dd_schedule[0],
        profit_management_strategy=args.profit_strategy[0],
        profitprotector=live_config.profit_management.profitprotector,
        legacy_end_of_day_mark=args.legacy_end_of_day_mark,
        **_sim_parity_fields_from_args(live_config, args),
    )

    engine = SimulationEngine()
    restore = _patch_chain_cache(full_chains, date)
    try:
        result = engine.simulate_day_from_entry(
            day_with_monitoring_bars(data["day"], monitoring),
            params,
            entry_candidate=chosen,
            entry_price=backtest_entry_price(chosen.cost, live_config, args.slippage),
            entry_time=entry_bar.ts,
        )
    finally:
        restore()

    if not result.traded:
        return SessionOutcome(
            session_date=date,
            status="no_signal",
            detail=f"frozen decision produced no completed trade: {result.exit_reason}",
            data_range=data_range,
            row_counts=row_counts,
        )

    executions = {
        model: price_frozen_trade(
            baseline=result,
            candidate=chosen,
            chains=full_chains,
            model=model,
            commission_per_contract=commission_per_contract,
            settlement_spot=data["day"].settlement_spot,
        )
        for model in EXECUTABLE_MODELS
    }
    warnings = [
        f"{model}: {execution.status}"
        for model, execution in executions.items()
        if not execution.priced
    ]
    warnings += [
        f"{model}: rolled past {execution.skipped_exit_observations} unusable exit observations"
        for model, execution in executions.items()
        if execution.skipped_exit_observations
    ]
    return SessionOutcome(
        session_date=date,
        status="traded",
        detail="frozen_entry_selection",
        candidate=chosen,
        baseline=result,
        chains=full_chains,
        executions=executions,
        settlement_spot=data["day"].settlement_spot,
        signal_time=entry_bar.ts,
        row_counts=row_counts,
        data_range=data_range,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _next_session_after(day: dt.date) -> dt.date:
    """Next weekday after *day*; holidays simply record no session."""
    nxt = day + dt.timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += dt.timedelta(days=1)
    return nxt


def cohort_dir_for(cohort_id: str, root: Path) -> Path:
    return root / cohort_id


def command_init(args: argparse.Namespace) -> int:
    created = dt.datetime.now(dt.timezone.utc)
    default_start = _next_session_after(created.date())
    start = args.start or default_start
    label = DRY_RUN_LABEL if args.dry_run_cohort else "prospective"
    if not args.dry_run_cohort and start < default_start:
        print(
            f"ERROR: prospective cohorts start at the next complete session "
            f"({default_start}); {start} is not prospective. Use --dry-run-cohort "
            "for the historical plumbing rehearsal.",
            file=sys.stderr,
        )
        return 2

    cohort_id = args.cohort_id or f"{args.asset.lower()}-{label}-{start.isoformat()}"
    cohort_dir = cohort_dir_for(cohort_id, args.root)
    if cohort_dir.exists():
        print(f"ERROR: cohort {cohort_dir} already exists.", file=sys.stderr)
        return 2

    frozen = frozen_backtest_args(args.asset)
    live_config = load_asset_config(args.asset)
    spec = CohortSpec(
        cohort_id=cohort_id,
        asset=args.asset,
        start_date=start,
        target_trades=args.target_trades,
        min_cash_settlements=args.min_cash_settlements,
        min_stressed_winners=args.min_stressed_winners,
        max_drawdown=args.max_drawdown,
        label=label,
    )
    manifest = build_manifest(
        spec=spec,
        repo_root=REPO_ROOT,
        config_path=Path(ASSET_CONFIG_PATHS[args.asset]),
        strategy_parameters=strategy_parameter_snapshot(frozen),
        database_tables=DATABASE_TABLES,
        init_command=" ".join([Path(sys.argv[0]).name, *sys.argv[1:]]),
        commission_per_contract=live_config.execution.paper_commission_per_contract,
        created_at=created,
    )
    path = write_manifest(cohort_dir, manifest)
    trades_path(cohort_dir).touch()
    daily_runs_path(cohort_dir).touch()
    print(f"Cohort {cohort_id} initialized at {cohort_dir}")
    print(f"  manifest        : {path}")
    print(f"  git commit      : {manifest['git']['commit']} (dirty={manifest['git']['dirty']})")
    print(f"  prospective from: {start}")
    print(
        f"  endpoint        : {spec.target_trades} trades, "
        f"{spec.min_cash_settlements} cash settlements, "
        f"{spec.min_stressed_winners} stressed winners"
    )
    if manifest["git"]["dirty"]:
        print("  WARNING: worktree is dirty; commit before the first prospective session.")
    return 0


async def command_update(args: argparse.Namespace) -> int:
    cohort_dir = args.cohort
    manifest = load_manifest(cohort_dir)
    require_frozen_manifest(manifest, REPO_ROOT)
    frozen = frozen_backtest_args(manifest["asset"])
    require_frozen_parameters(manifest, frozen)

    start = dt.date.fromisoformat(manifest["prospective_start_date"])
    through = args.through or dt.date.today()
    recorded = {run["session_date"] for run in read_jsonl(daily_runs_path(cohort_dir))}
    command = " ".join([Path(sys.argv[0]).name, *sys.argv[1:]])

    conn = await asyncpg.connect(resolve_db_dsn())
    appended = 0
    deferred = 0
    try:
        dates = await discover_dates(conn, manifest["asset"], start, through)
        pending = [date for date in dates if date.isoformat() not in recorded]
        if not pending:
            print(f"No unrecorded sessions in {start} → {through}.")
        for date in pending:
            outcome = await evaluate_session(
                conn,
                date=date,
                asset=manifest["asset"],
                args=frozen,
                commission_per_contract=manifest["assumptions"]["commission_per_contract"],
            )
            written = record_session(
                cohort_dir=cohort_dir,
                manifest=manifest,
                outcome=outcome,
                repo_root=REPO_ROOT,
                command=command,
            )
            if written["deferred"]:
                deferred += 1
                print(f"  {date}: deferred ({outcome.detail})")
                continue
            appended += 1
            suffix = f" trade={written['trade_id']}" if written["trade_id"] else ""
            print(f"  {date}: {outcome.status}{suffix}")
    finally:
        await conn.close()

    print(f"Recorded {appended} session(s); {deferred} deferred for incomplete data.")
    return command_report(args)


def command_report(args: argparse.Namespace) -> int:
    cohort_dir = args.cohort
    manifest = load_manifest(cohort_dir)
    summary = summarize_cohort(
        manifest=manifest,
        trades=read_jsonl(trades_path(cohort_dir)),
        daily_runs=read_jsonl(daily_runs_path(cohort_dir)),
    )
    json_path, md_path = write_reports(cohort_dir, summary)
    primary = summary["models"][summary["primary_model"]]
    print(f"\n{summary['cohort_id']}: {summary['eligible_trades']} eligible trade(s)")
    print(
        f"  {summary['primary_model']}: net=${primary['net_pnl']:,.2f} "
        f"expectancy=${primary['expectancy']:,.2f} pf={primary['profit_factor']:.3f} "
        f"win={primary['win_rate'] * 100:.1f}%"
    )
    print(f"  endpoint reached: {'yes' if summary['endpoint']['reached'] else 'no'}")
    print(f"  edge classification: {summary['gates']['edge_classification']}")
    print(f"  reports: {json_path}  {md_path}")
    return 0


def command_verify(args: argparse.Namespace) -> int:
    problems = verify_cohort(args.cohort, REPO_ROOT)
    if not problems:
        print(f"{args.cohort}: ledger integrity OK")
        return 0
    print(f"{args.cohort}: {len(problems)} integrity problem(s)", file=sys.stderr)
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prospective execution-validation study for a frozen strategy",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a cohort manifest and empty ledgers")
    init.add_argument("--asset", choices=sorted(ASSET_CONFIG_PATHS), default="SPX")
    init.add_argument(
        "--start",
        type=dt.date.fromisoformat,
        default=None,
        help="First eligible session (default: next complete session after today)",
    )
    init.add_argument("--cohort-id", default=None, help="Explicit cohort directory name")
    init.add_argument("--target-trades", type=int, default=120)
    init.add_argument("--min-cash-settlements", type=int, default=20)
    init.add_argument("--min-stressed-winners", type=int, default=15)
    init.add_argument(
        "--max-drawdown",
        type=float,
        required=True,
        help="Maximum acceptable stressed-marketable dollar drawdown, chosen before the cohort",
    )
    init.add_argument(
        "--dry-run-cohort",
        action="store_true",
        help="Historical plumbing rehearsal; never combine its results with a real cohort",
    )
    init.add_argument("--root", type=Path, default=COHORT_ROOT)
    init.set_defaults(func=command_init)

    update = sub.add_parser("update", help="append every completed session through a date")
    update.add_argument("--cohort", type=Path, required=True)
    update.add_argument("--through", type=dt.date.fromisoformat, default=None)
    update.set_defaults(func=command_update)

    report = sub.add_parser("report", help="regenerate reports without touching the ledger")
    report.add_argument("--cohort", type=Path, required=True)
    report.set_defaults(func=command_report)

    verify = sub.add_parser("verify", help="audit manifest, ledgers, and record hashes")
    verify.add_argument("--cohort", type=Path, required=True)
    verify.set_defaults(func=command_verify)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "update":
            return asyncio.run(command_update(args))
        return args.func(args)
    except CohortError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
