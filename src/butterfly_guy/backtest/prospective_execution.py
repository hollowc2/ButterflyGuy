"""Append-only prospective execution-validation cohorts for a frozen strategy.

A cohort freezes the strategy source and configuration behind a manifest, then
appends one immutable record per prospective session. Nothing here decides or
re-decides a trade: the frozen simulation supplies the decision, and this module
records executable accounting, quote provenance, coverage, and integrity.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import statistics
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from butterfly_guy.backtest.execution_accounting import (
    CONTRACTS_PER_BUTTERFLY,
    STRESSED_LEG_SLIPPAGE,
    ExecutableTrade,
    inspect_quote_market,
    snapshot_at_or_before,
)
from butterfly_guy.backtest.metrics import max_drawdown, profit_factor
from butterfly_guy.backtest.simulation_engine import DayResult
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote

SCHEMA_VERSION = 1
COHORT_ROOT = Path("reports/prospective_execution")
MIDPOINT_MODEL = "corrected_midpoint"
EXECUTABLE_MODELS = ("marketable", "stressed_marketable")
ACCOUNTING_MODELS = (MIDPOINT_MODEL, *EXECUTABLE_MODELS)
PRIMARY_MODEL = "stressed_marketable"
CONTRACT_MULTIPLIER = 100.0
DAILY_RUNS_FILE = "daily_runs.jsonl"
TRADES_FILE = "trades.jsonl"
MANIFEST_FILE = "manifest.json"
SUMMARY_JSON_FILE = "summary.json"
SUMMARY_MD_FILE = "summary.md"

SessionStatus = Literal["no_signal", "incomplete_data", "traded"]

#: Source files whose content defines the frozen decision and its accounting.
TRACKED_SOURCES: tuple[str, ...] = (
    "src/butterfly_guy/backtest/execution_accounting.py",
    "src/butterfly_guy/backtest/prospective_execution.py",
    "src/butterfly_guy/backtest/simulation_engine.py",
    "src/butterfly_guy/backtest/db_loader.py",
    "src/butterfly_guy/backtest/chain_cache.py",
    "src/butterfly_guy/scripts/run_backtest_db.py",
    "src/butterfly_guy/scripts/run_prospective_execution.py",
    "src/butterfly_guy/strategy/entry_selection.py",
    "src/butterfly_guy/strategy/butterfly_builder.py",
    "src/butterfly_guy/strategy/butterfly_selector.py",
    "src/butterfly_guy/strategy/direction_filter.py",
    "src/butterfly_guy/strategy/gap_regime_filter.py",
    "src/butterfly_guy/strategy/regime_classifier.py",
    "src/butterfly_guy/strategy/width_selection.py",
    "src/butterfly_guy/position/position_manager.py",
    "src/butterfly_guy/position/profit_policy.py",
)

#: Each butterfly leg as (role, signed contract quantity).
LEG_ROLES: tuple[tuple[str, int], ...] = (("lower", 1), ("center", -2), ("upper", 1))


class CohortError(Exception):
    """Base class for cohort integrity failures."""


class ManifestDriftError(CohortError):
    """Frozen source or configuration no longer matches the cohort manifest."""


class SessionOutOfRangeError(CohortError):
    """A session predates the cohort start and may not be appended."""


class LedgerConflictError(CohortError):
    """A rerun produced a different record for an already-recorded key."""


# ---------------------------------------------------------------------------
# Hashing and repository state
# ---------------------------------------------------------------------------

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(payload: Any) -> str:
    """Hash a record independent of key order and file formatting."""
    return sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))


def git_state(repo_root: Path) -> dict[str, Any]:
    """Return the current commit and whether the worktree carries edits."""
    def run(*args: str) -> str | None:
        try:
            done = subprocess.run(
                ["git", "-C", str(repo_root), *args],
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        return done.stdout.strip()

    sha = run("rev-parse", "HEAD")
    status = run("status", "--porcelain")
    return {
        "commit": sha,
        "dirty": bool(status) if status is not None else None,
    }


def source_hashes(repo_root: Path, sources: tuple[str, ...] = TRACKED_SOURCES) -> dict[str, str]:
    """Hash every tracked source that exists, so drift is detectable per file."""
    hashes: dict[str, str] = {}
    for relative in sources:
        path = repo_root / relative
        hashes[relative] = sha256_path(path) if path.exists() else "MISSING"
    return hashes


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CohortSpec:
    """Operator-chosen, pre-registered cohort boundaries."""

    cohort_id: str
    asset: str
    start_date: dt.date
    target_trades: int
    min_cash_settlements: int
    min_stressed_winners: int
    max_drawdown: float
    timezone: str = "America/New_York"
    label: str = "prospective"


def build_manifest(
    *,
    spec: CohortSpec,
    repo_root: Path,
    config_path: Path,
    strategy_parameters: dict[str, Any],
    database_tables: tuple[str, ...],
    init_command: str,
    commission_per_contract: float,
    created_at: dt.datetime | None = None,
) -> dict[str, Any]:
    """Freeze everything a later run must reproduce before appending data."""
    created = created_at or dt.datetime.now(dt.timezone.utc)
    return {
        "schema_version": SCHEMA_VERSION,
        "cohort_id": spec.cohort_id,
        "label": spec.label,
        "created_at": created.isoformat(),
        "asset": spec.asset,
        "timezone": spec.timezone,
        "prospective_start_date": spec.start_date.isoformat(),
        "git": git_state(repo_root),
        "config": {
            "path": str(config_path),
            "sha256": sha256_path(config_path),
        },
        "source_hashes": source_hashes(repo_root),
        "strategy_parameters": strategy_parameters,
        "fill_models": {
            MIDPOINT_MODEL: (
                "frozen simulation baseline: midpoint marks, entry commission, "
                "settlement-correct close"
            ),
            "marketable": (
                "buy outer legs at ask and sell two center contracts at bid on entry; "
                "inverse sides on an intraday exit; no closing order at cash settlement"
            ),
            "stressed_marketable": (
                "marketable plus $%.2f adverse slippage on every executable contract leg"
                % STRESSED_LEG_SLIPPAGE
            ),
        },
        "assumptions": {
            "commission_per_contract": commission_per_contract,
            "contracts_per_butterfly": CONTRACTS_PER_BUTTERFLY,
            "stressed_leg_slippage": STRESSED_LEG_SLIPPAGE,
            "contract_multiplier": CONTRACT_MULTIPLIER,
            "quantity": 1,
        },
        "endpoint": {
            "target_trades": spec.target_trades,
            "min_cash_settlements": spec.min_cash_settlements,
            "min_stressed_winners": spec.min_stressed_winners,
            "rule": "continue until every endpoint condition is met",
        },
        "decision_rules": {
            "primary_model": PRIMARY_MODEL,
            "primary_hypothesis": (
                "the frozen strategy produces positive net P&L and positive expectancy "
                "over the registered prospective sample under stressed-marketable accounting"
            ),
            "checkpoint_trades": 20,
            "early_failure_trades": 60,
            "max_drawdown": spec.max_drawdown,
            "min_executable_entry_coverage": 0.95,
            "max_top3_gross_profit_share": 0.50,
            "min_profit_factor": 1.0,
        },
        "database_tables": list(database_tables),
        "quote_rules": {
            "selection": "latest quote with timestamp <= simulated decision time",
            "missing_market": "absent, null, non-finite, or negative required side",
            "crossed_market": "ask < bid",
            "entry_gap": "unpriced; excluded from P&L and counted in coverage",
            "exit_gap": (
                "skip the observation and roll forward to the next monitoring time; "
                "fall back to settlement-correct value when no executable exit remains"
            ),
            "substitution": "never; no midpoint, theoretical, adjacent-strike, or carried quotes",
        },
        "init_command": init_command,
    }


def manifest_path(cohort_dir: Path) -> Path:
    return cohort_dir / MANIFEST_FILE


def write_manifest(cohort_dir: Path, manifest: dict[str, Any]) -> Path:
    cohort_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_path(cohort_dir)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_manifest(cohort_dir: Path) -> dict[str, Any]:
    path = manifest_path(cohort_dir)
    if not path.exists():
        raise CohortError(f"no cohort manifest at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_drift(manifest: dict[str, Any], repo_root: Path) -> list[str]:
    """Return one human-readable reason per artifact that changed since freeze."""
    reasons: list[str] = []
    config_path = Path(manifest["config"]["path"])
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    if not config_path.exists():
        reasons.append(f"configuration missing: {config_path}")
    elif sha256_path(config_path) != manifest["config"]["sha256"]:
        reasons.append(f"configuration changed: {config_path}")
    current = source_hashes(repo_root, tuple(manifest["source_hashes"]))
    for relative, frozen in sorted(manifest["source_hashes"].items()):
        if current.get(relative) != frozen:
            reasons.append(f"source changed: {relative}")
    return reasons


def require_frozen_manifest(manifest: dict[str, Any], repo_root: Path) -> None:
    """Refuse to append data when the frozen research version has moved."""
    reasons = manifest_drift(manifest, repo_root)
    if reasons:
        raise ManifestDriftError(
            "cohort "
            f"{manifest['cohort_id']} is frozen against a different research version; "
            "close this cohort and start a new one. Changed: " + "; ".join(reasons)
        )


def require_session_in_cohort(manifest: dict[str, Any], session_date: dt.date) -> None:
    start = dt.date.fromisoformat(manifest["prospective_start_date"])
    if session_date < start:
        raise SessionOutOfRangeError(
            f"session {session_date} predates cohort start {start}; "
            "prospective cohorts never absorb earlier sessions"
        )


# ---------------------------------------------------------------------------
# Quote provenance
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LegQuote:
    """One recorded leg quote and the side that leg actually executes against."""

    role: str
    strike: float
    quantity: int
    executable_side: str
    bid: float | None
    ask: float | None
    snapshot_time: dt.datetime | None
    age_seconds: float | None

    def as_record(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "strike": self.strike,
            "quantity": self.quantity,
            "executable_side": self.executable_side,
            "bid": self.bid,
            "ask": self.ask,
            "snapshot_time": self.snapshot_time.isoformat() if self.snapshot_time else None,
            "age_seconds": self.age_seconds,
        }


def executable_side(role: str, stage: str) -> str:
    """Return the quote side a leg trades against: long legs buy at ask, sell at bid."""
    long_leg = role in {"lower", "upper"}
    if stage == "entry":
        return "ask" if long_leg else "bid"
    return "bid" if long_leg else "ask"


def leg_provenance(
    chains: dict[dt.datetime, list[OptionQuote]],
    decision_time: dt.datetime,
    candidate: ButterflyCandidate,
    stage: str,
) -> dict[str, Any]:
    """Record the exact quotes a stage would have executed against, never later ones."""
    snapshot_time, quotes = snapshot_at_or_before(chains, decision_time)
    market = inspect_quote_market(quotes, candidate)
    strikes = {
        "lower": candidate.lower_strike,
        "center": candidate.center_strike,
        "upper": candidate.upper_strike,
    }
    age = (decision_time - snapshot_time).total_seconds() if snapshot_time else None
    legs = []
    for role, quantity in LEG_ROLES:
        quote = getattr(market, role)
        legs.append(
            LegQuote(
                role=role,
                strike=strikes[role],
                quantity=quantity,
                executable_side=executable_side(role, stage),
                bid=quote.bid if quote is not None else None,
                ask=quote.ask if quote is not None else None,
                snapshot_time=snapshot_time,
                age_seconds=age,
            )
        )
    if market.missing_strikes:
        status = "missing"
    elif market.crossed_strikes:
        status = "crossed"
    else:
        status = "usable"
    return {
        "stage": stage,
        "decision_time": decision_time.isoformat(),
        "snapshot_time": snapshot_time.isoformat() if snapshot_time else None,
        "age_seconds": age,
        "status": status,
        "missing_strikes": list(market.missing_strikes),
        "crossed_strikes": list(market.crossed_strikes),
        "legs": [leg.as_record() for leg in legs],
    }


# ---------------------------------------------------------------------------
# Session outcomes and trade records
# ---------------------------------------------------------------------------

@dataclass
class SessionOutcome:
    """What the frozen strategy did on one prospective session."""

    session_date: dt.date
    status: SessionStatus
    detail: str = ""
    candidate: ButterflyCandidate | None = None
    baseline: DayResult | None = None
    chains: dict[dt.datetime, list[OptionQuote]] = field(default_factory=dict)
    executions: dict[str, ExecutableTrade] = field(default_factory=dict)
    settlement_spot: float | None = None
    signal_time: dt.datetime | None = None
    row_counts: dict[str, int] = field(default_factory=dict)
    data_range: dict[str, str | None] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def trade_key(
    cohort_id: str,
    session_date: dt.date,
    decision_time: dt.datetime,
    direction: str,
    strikes: tuple[float, float, float],
) -> str:
    """Deterministic identity for one frozen decision."""
    parts = "|".join(
        [
            cohort_id,
            session_date.isoformat(),
            decision_time.isoformat(),
            direction,
            *(f"{strike:.4f}" for strike in strikes),
        ]
    )
    return sha256_text(parts)[:16]


def _model_costs(
    *,
    model: str,
    exit_reason: str,
    commission_per_contract: float,
    settled: bool,
) -> dict[str, float]:
    """Per-trade dollar commissions and stress for one accounting model."""
    entry_commission = CONTRACTS_PER_BUTTERFLY * commission_per_contract
    closes_an_order = exit_reason != "cash_settled" and not settled
    exit_commission = entry_commission if closes_an_order else 0.0
    stress_leg = (
        CONTRACTS_PER_BUTTERFLY * STRESSED_LEG_SLIPPAGE * CONTRACT_MULTIPLIER
        if model == "stressed_marketable"
        else 0.0
    )
    return {
        "entry_commission": round(entry_commission, 4),
        "exit_commission": round(exit_commission, 4),
        "stress_cost": round(stress_leg + (stress_leg if closes_an_order else 0.0), 4),
    }


def _midpoint_accounting(
    baseline: DayResult,
    commission_per_contract: float,
) -> dict[str, Any]:
    pnl = baseline.pnl * CONTRACT_MULTIPLIER
    mfe = max(0.0, baseline.peak_value - baseline.entry_price) * CONTRACT_MULTIPLIER
    costs = _model_costs(
        model=MIDPOINT_MODEL,
        exit_reason=baseline.exit_reason,
        commission_per_contract=commission_per_contract,
        settled=False,
    )
    return {
        "model": MIDPOINT_MODEL,
        "status": "priced",
        "entry_price": round(baseline.entry_price, 4),
        "exit_price": round(baseline.exit_price, 4),
        "net_pnl": round(pnl, 4),
        "gross_pnl": round(pnl + costs["entry_commission"] + costs["exit_commission"], 4),
        "mfe": round(mfe, 4),
        "exit_snapshot_time": None,
        "skipped_exit_observations": 0,
        "settlement_fallback": False,
        "path_snapshots": 0,
        "usable_path_snapshots": 0,
        "missing_path_snapshots": 0,
        "crossed_path_snapshots": 0,
        **costs,
    }


def _executable_accounting(
    execution: ExecutableTrade,
    commission_per_contract: float,
) -> dict[str, Any]:
    costs = _model_costs(
        model=execution.model,
        exit_reason=execution.exit_reason,
        commission_per_contract=commission_per_contract,
        settled=execution.settlement_fallback,
    )
    priced = execution.priced
    net = execution.pnl * CONTRACT_MULTIPLIER if priced and execution.pnl is not None else None
    gross = (
        round(net + costs["entry_commission"] + costs["exit_commission"] + costs["stress_cost"], 4)
        if net is not None
        else None
    )
    return {
        "model": execution.model,
        "status": execution.status,
        "entry_price": (
            round(execution.entry_price, 4) if execution.entry_price is not None else None
        ),
        "exit_price": round(execution.exit_price, 4) if execution.exit_price is not None else None,
        "net_pnl": round(net, 4) if net is not None else None,
        "gross_pnl": gross,
        "mfe": (
            round(execution.mfe * CONTRACT_MULTIPLIER, 4)
            if priced and execution.mfe is not None
            else None
        ),
        "exit_snapshot_time": (
            execution.exit_snapshot_time.isoformat() if execution.exit_snapshot_time else None
        ),
        "skipped_exit_observations": execution.skipped_exit_observations,
        "settlement_fallback": execution.settlement_fallback,
        "missing_strikes": list(execution.missing_strikes),
        "crossed_strikes": list(execution.crossed_strikes),
        "path_snapshots": execution.path_snapshots,
        "usable_path_snapshots": execution.usable_path_snapshots,
        "missing_path_snapshots": execution.missing_path_snapshots,
        "crossed_path_snapshots": execution.crossed_path_snapshots,
        **costs,
    }


def build_trade_record(
    *,
    cohort_id: str,
    outcome: SessionOutcome,
    commission_per_contract: float,
    run_timestamp: dt.datetime,
    git_commit: str | None,
    config_sha256: str,
) -> dict[str, Any]:
    """Assemble one immutable trade record from an already-frozen decision."""
    baseline = outcome.baseline
    candidate = outcome.candidate
    if baseline is None or candidate is None or not baseline.traded:
        raise CohortError("a trade record needs a completed, traded frozen decision")
    if baseline.entry_time is None or baseline.exit_time is None:
        raise CohortError("a trade record needs frozen entry and exit times")

    strikes = (candidate.lower_strike, candidate.center_strike, candidate.upper_strike)
    accounting = {MIDPOINT_MODEL: _midpoint_accounting(baseline, commission_per_contract)}
    for model in EXECUTABLE_MODELS:
        execution = outcome.executions.get(model)
        if execution is not None:
            accounting[model] = _executable_accounting(execution, commission_per_contract)

    cash_settled = baseline.exit_reason == "cash_settled"
    record = {
        "schema_version": SCHEMA_VERSION,
        "cohort_id": cohort_id,
        "trade_id": trade_key(
            cohort_id, baseline.date, baseline.entry_time, baseline.direction, strikes
        ),
        "session_date": baseline.date.isoformat(),
        "run_timestamp": run_timestamp.isoformat(),
        "git_commit": git_commit,
        "config_sha256": config_sha256,
        "signal_time": outcome.signal_time.isoformat() if outcome.signal_time else None,
        "decision_time": baseline.entry_time.isoformat(),
        "exit_time": baseline.exit_time.isoformat(),
        "direction": baseline.direction,
        "wing_width": candidate.wing_width,
        "lower_strike": candidate.lower_strike,
        "center_strike": candidate.center_strike,
        "upper_strike": candidate.upper_strike,
        "entry_reason": outcome.detail or "frozen_entry_selection",
        "exit_reason": baseline.exit_reason,
        "cash_settled": cash_settled,
        "settlement_spot": baseline.settlement_spot if cash_settled else None,
        "settlement_source": "official_close" if cash_settled else None,
        "entry_provenance": leg_provenance(
            outcome.chains, baseline.entry_time, candidate, "entry"
        ),
        "exit_provenance": (
            None
            if cash_settled
            else leg_provenance(outcome.chains, baseline.exit_time, candidate, "exit")
        ),
        "accounting": accounting,
    }
    record["record_hash"] = canonical_hash(record)
    return record


def build_daily_run_record(
    *,
    cohort_id: str,
    outcome: SessionOutcome,
    run_timestamp: dt.datetime,
    git_commit: str | None,
    config_sha256: str,
    command: str,
    trade_id: str | None,
) -> dict[str, Any]:
    """Assemble the per-session run record, traded or not."""
    record = {
        "schema_version": SCHEMA_VERSION,
        "cohort_id": cohort_id,
        "session_date": outcome.session_date.isoformat(),
        "run_timestamp": run_timestamp.isoformat(),
        "git_commit": git_commit,
        "config_sha256": config_sha256,
        "status": outcome.status,
        "detail": outcome.detail,
        "trade_id": trade_id,
        "data_range": dict(outcome.data_range),
        "row_counts": dict(outcome.row_counts),
        "warnings": list(outcome.warnings),
        "warning_count": len(outcome.warnings),
        "command": command,
    }
    record["record_hash"] = canonical_hash(record)
    return record


# ---------------------------------------------------------------------------
# Append-only ledgers
# ---------------------------------------------------------------------------

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")


def _comparable(record: dict[str, Any]) -> dict[str, Any]:
    """Drop fields that legitimately differ between identical reruns."""
    return {
        key: value
        for key, value in record.items()
        if key not in {"run_timestamp", "record_hash", "command"}
    }


def append_unique(path: Path, record: dict[str, Any], key: str) -> bool:
    """Append once per key; reruns must reproduce the record or raise.

    Returns True when the record was appended and False when an identical record
    was already present.
    """
    identity = record[key]
    for existing in read_jsonl(path):
        if existing.get(key) != identity:
            continue
        if canonical_hash(_comparable(existing)) == canonical_hash(_comparable(record)):
            return False
        raise LedgerConflictError(
            f"{path.name} already holds a different record for {key}={identity}; "
            "append an explicit amendment instead of overwriting history"
        )
    append_jsonl(path, record)
    return True


def trades_path(cohort_dir: Path) -> Path:
    return cohort_dir / TRADES_FILE


def daily_runs_path(cohort_dir: Path) -> Path:
    return cohort_dir / DAILY_RUNS_FILE


def record_session(
    *,
    cohort_dir: Path,
    manifest: dict[str, Any],
    outcome: SessionOutcome,
    repo_root: Path,
    command: str,
    run_timestamp: dt.datetime | None = None,
) -> dict[str, Any]:
    """Validate, then append one session to both ledgers. Reruns are idempotent.

    Sessions whose quotes or official settlement are still incomplete are reported
    but never appended, so a later complete run records them without amending history.
    """
    require_frozen_manifest(manifest, repo_root)
    require_session_in_cohort(manifest, outcome.session_date)
    if outcome.status == "incomplete_data":
        return {
            "session_date": outcome.session_date.isoformat(),
            "status": outcome.status,
            "trade_id": None,
            "trade_appended": False,
            "daily_run_appended": False,
            "deferred": True,
        }

    run_at = run_timestamp or dt.datetime.now(dt.timezone.utc)
    commit = manifest["git"].get("commit")
    config_sha = manifest["config"]["sha256"]
    commission = manifest["assumptions"]["commission_per_contract"]

    trade_record: dict[str, Any] | None = None
    trade_appended = False
    if outcome.status == "traded":
        trade_record = build_trade_record(
            cohort_id=manifest["cohort_id"],
            outcome=outcome,
            commission_per_contract=commission,
            run_timestamp=run_at,
            git_commit=commit,
            config_sha256=config_sha,
        )
        trade_appended = append_unique(trades_path(cohort_dir), trade_record, "trade_id")

    daily_record = build_daily_run_record(
        cohort_id=manifest["cohort_id"],
        outcome=outcome,
        run_timestamp=run_at,
        git_commit=commit,
        config_sha256=config_sha,
        command=command,
        trade_id=trade_record["trade_id"] if trade_record else None,
    )
    daily_appended = append_unique(daily_runs_path(cohort_dir), daily_record, "session_date")
    return {
        "session_date": outcome.session_date.isoformat(),
        "status": outcome.status,
        "trade_id": trade_record["trade_id"] if trade_record else None,
        "trade_appended": trade_appended,
        "daily_run_appended": daily_appended,
        "deferred": False,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _model_slice(trades: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
    return [
        trade["accounting"][model]
        for trade in trades
        if model in trade.get("accounting", {})
    ]


def _pnl_metrics(pnls: list[float], mfes: list[float]) -> dict[str, float | int]:
    if not pnls:
        return {
            "trade_count": 0,
            "net_pnl": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "median_trade": 0.0,
            "max_drawdown": 0.0,
            "average_mfe": 0.0,
            "mfe_capture": 0.0,
            "top3_concentration": 0.0,
        }
    wins = [pnl for pnl in pnls if pnl > 0]
    gross_wins = sum(wins)
    aggregate_mfe = sum(max(0.0, mfe) for mfe in mfes)
    return {
        "trade_count": len(pnls),
        "net_pnl": round(sum(pnls), 4),
        "expectancy": round(statistics.mean(pnls), 4),
        "profit_factor": profit_factor(pnls),
        "win_rate": round(len(wins) / len(pnls), 4),
        "median_trade": round(statistics.median(pnls), 4),
        "max_drawdown": round(max_drawdown(pnls), 4),
        "average_mfe": round(statistics.mean(mfes), 4) if mfes else 0.0,
        "mfe_capture": round(gross_wins / aggregate_mfe, 4) if aggregate_mfe else 0.0,
        "top3_concentration": (
            round(sum(sorted(wins, reverse=True)[:3]) / gross_wins, 4) if gross_wins else 0.0
        ),
    }


def _model_summary(
    trades: list[dict[str, Any]],
    daily_runs: list[dict[str, Any]],
    model: str,
) -> dict[str, Any]:
    entries = _model_slice(trades, model)
    priced = [entry for entry in entries if entry["status"] == "priced"]
    pnls = [entry["net_pnl"] for entry in priced]
    mfes = [entry["mfe"] for entry in priced]
    gross = sum(entry["gross_pnl"] for entry in priced)
    eligible = sum(1 for run in daily_runs if run["status"] == "traded")
    return {
        "model": model,
        "eligible_signals": eligible,
        "priced_trades": len(priced),
        "unpriced_trades": len(entries) - len(priced),
        "complete_fill_coverage": round(len(priced) / len(entries), 4) if entries else 0.0,
        "missing_entry_markets": sum(
            1 for entry in entries if entry["status"] == "missing_entry_market"
        ),
        "crossed_entry_markets": sum(
            1 for entry in entries if entry["status"] == "crossed_entry_market"
        ),
        "missing_exit_markets": sum(
            1 for entry in entries if entry["status"] == "missing_exit_market"
        ),
        "crossed_exit_markets": sum(
            1 for entry in entries if entry["status"] == "crossed_exit_market"
        ),
        "skipped_exit_observations": sum(
            entry.get("skipped_exit_observations", 0) for entry in entries
        ),
        "settlement_fallbacks": sum(
            1 for entry in entries if entry.get("settlement_fallback")
        ),
        "missing_exit_observations": sum(
            entry.get("missing_path_snapshots", 0) for entry in entries
        ),
        "crossed_exit_observations": sum(
            entry.get("crossed_path_snapshots", 0) for entry in entries
        ),
        "gross_pnl": round(gross, 4),
        **_pnl_metrics(pnls, mfes),
    }


def _breakdown(
    trades: list[dict[str, Any]],
    model: str,
    key: Any,
) -> dict[str, dict[str, float | int]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for trade in trades:
        entry = trade.get("accounting", {}).get(model)
        if entry is None or entry["status"] != "priced":
            continue
        groups.setdefault(str(key(trade)), []).append(entry)
    return {
        name: _pnl_metrics(
            [entry["net_pnl"] for entry in entries],
            [entry["mfe"] for entry in entries],
        )
        for name, entries in sorted(groups.items())
    }


def _half_label(trades: list[dict[str, Any]]) -> dict[str, str]:
    ordered = sorted(trades, key=lambda trade: (trade["session_date"], trade["decision_time"]))
    midpoint = len(ordered) // 2 + len(ordered) % 2
    return {
        trade["trade_id"]: ("first_half" if index < midpoint else "second_half")
        for index, trade in enumerate(ordered)
    }


def summarize_cohort(
    *,
    manifest: dict[str, Any],
    trades: list[dict[str, Any]],
    daily_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the cumulative report over every appended record."""
    halves = _half_label(trades)
    models = {model: _model_summary(trades, daily_runs, model) for model in ACCOUNTING_MODELS}
    breakdowns = {
        model: {
            "half": _breakdown(trades, model, lambda trade: halves[trade["trade_id"]]),
            "settlement": _breakdown(
                trades,
                model,
                lambda trade: "cash_settled" if trade["cash_settled"] else "intraday_exit",
            ),
            "direction": _breakdown(trades, model, lambda trade: trade["direction"]),
            "month": _breakdown(trades, model, lambda trade: trade["session_date"][:7]),
            "exit_reason": _breakdown(trades, model, lambda trade: trade["exit_reason"]),
        }
        for model in ACCOUNTING_MODELS
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "cohort_id": manifest["cohort_id"],
        "label": manifest["label"],
        "asset": manifest["asset"],
        "primary_model": PRIMARY_MODEL,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "prospective_start_date": manifest["prospective_start_date"],
        "sessions_recorded": len(daily_runs),
        "sessions_without_signal": sum(
            1 for run in daily_runs if run["status"] == "no_signal"
        ),
        "sessions_with_incomplete_data": sum(
            1 for run in daily_runs if run["status"] == "incomplete_data"
        ),
        "eligible_trades": len(trades),
        "cash_settled_trades": sum(1 for trade in trades if trade["cash_settled"]),
        "models": models,
        "breakdowns": breakdowns,
    }
    summary["endpoint"] = evaluate_endpoint(manifest, summary)
    summary["gates"] = evaluate_gates(manifest, summary)
    return summary


def evaluate_endpoint(manifest: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    """Report progress toward the registered stopping rule."""
    endpoint = manifest["endpoint"]
    primary = summary["models"][PRIMARY_MODEL]
    stressed_winners = round(primary["win_rate"] * primary["trade_count"])
    conditions = {
        "eligible_trades": (summary["eligible_trades"], endpoint["target_trades"]),
        "cash_settled_trades": (
            summary["cash_settled_trades"],
            endpoint["min_cash_settlements"],
        ),
        "stressed_winners": (stressed_winners, endpoint["min_stressed_winners"]),
    }
    return {
        "conditions": {
            name: {"observed": observed, "required": required, "met": observed >= required}
            for name, (observed, required) in conditions.items()
        },
        "reached": all(observed >= required for observed, required in conditions.values()),
    }


def evaluate_gates(manifest: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    """Apply the pre-registered decision gates without softening any of them."""
    rules = manifest["decision_rules"]
    stressed = summary["models"][PRIMARY_MODEL]
    halves = summary["breakdowns"]["marketable"]["half"]
    entries = stressed["eligible_signals"]
    coverage = (
        (entries - stressed["missing_entry_markets"] - stressed["crossed_entry_markets"]) / entries
        if entries
        else 0.0
    )
    checks = {
        "stressed_net_pnl_positive": stressed["net_pnl"] > 0,
        "stressed_expectancy_positive": stressed["expectancy"] > 0,
        "stressed_profit_factor_above_one": stressed["profit_factor"] > rules["min_profit_factor"],
        "marketable_positive_in_both_halves": bool(halves)
        and all(half["net_pnl"] > 0 for half in halves.values())
        and len(halves) == 2,
        "executable_entry_coverage": coverage >= rules["min_executable_entry_coverage"],
        "top3_within_limit": stressed["top3_concentration"] <= rules["max_top3_gross_profit_share"],
        "drawdown_within_limit": stressed["max_drawdown"] <= rules["max_drawdown"],
    }
    settlement = summary["breakdowns"][PRIMARY_MODEL]["settlement"]
    intraday = settlement.get("intraday_exit", {})
    cash = settlement.get("cash_settled", {})
    if stressed["trade_count"] == 0:
        classification = "insufficient_data"
    elif not all(checks.values()):
        classification = "no_executable_edge"
    elif intraday.get("net_pnl", 0.0) > 0 and intraday.get("trade_count", 0) > 0:
        classification = "general_executable_edge"
    elif cash.get("net_pnl", 0.0) > 0:
        classification = "settlement_dependent_edge_only"
    else:
        classification = "no_executable_edge"
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "entry_coverage": round(coverage, 4),
        "edge_classification": classification,
        "early_failure_review_due": summary["eligible_trades"] >= rules["early_failure_trades"],
        "integrity_checkpoint_due": summary["eligible_trades"] >= rules["checkpoint_trades"],
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    """Render the human-readable cumulative report, stressed-marketable first."""
    lines = [
        f"# Prospective execution validation — {summary['cohort_id']}",
        "",
        f"- Asset: {summary['asset']}",
        f"- Cohort label: {summary['label']}",
        f"- Prospective start: {summary['prospective_start_date']}",
        f"- Generated: {summary['generated_at']}",
        f"- Primary result: **{summary['primary_model']}** "
        "(corrected midpoint is a comparison baseline only)",
        "",
        "## Sessions",
        "",
        f"- Sessions recorded: {summary['sessions_recorded']}",
        f"- No signal: {summary['sessions_without_signal']}",
        f"- Incomplete data: {summary['sessions_with_incomplete_data']}",
        f"- Eligible trades: {summary['eligible_trades']}",
        f"- Cash-settled trades: {summary['cash_settled_trades']}",
        "",
        "## Accounting models",
        "",
        "| Model | Trades | Net P&L | Expectancy | PF | Win% | Median | Max DD | "
        "Avg MFE | MFE cap | Top-3 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    ordered = [PRIMARY_MODEL, "marketable", MIDPOINT_MODEL]
    for model in ordered:
        row = summary["models"][model]
        lines.append(
            f"| {model} | {row['trade_count']} | ${row['net_pnl']:,.2f} | "
            f"${row['expectancy']:,.2f} | {row['profit_factor']:.3f} | "
            f"{row['win_rate'] * 100:.1f}% | ${row['median_trade']:,.2f} | "
            f"${row['max_drawdown']:,.2f} | ${row['average_mfe']:,.2f} | "
            f"{row['mfe_capture'] * 100:.1f}% | {row['top3_concentration'] * 100:.1f}% |"
        )
    lines += ["", "## Coverage", ""]
    for model in ordered:
        row = summary["models"][model]
        lines.append(
            f"- {model}: eligible={row['eligible_signals']} priced={row['priced_trades']} "
            f"unpriced={row['unpriced_trades']} "
            f"coverage={row['complete_fill_coverage'] * 100:.1f}% "
            f"missing_entry={row['missing_entry_markets']} "
            f"crossed_entry={row['crossed_entry_markets']} "
            f"missing_exit={row['missing_exit_markets']} "
            f"crossed_exit={row['crossed_exit_markets']} "
            f"skipped_exit_obs={row['skipped_exit_observations']} "
            f"settlement_fallbacks={row['settlement_fallbacks']}"
        )
    for name in ("half", "settlement", "direction", "month", "exit_reason"):
        lines += ["", f"## {PRIMARY_MODEL} by {name}", ""]
        groups = summary["breakdowns"][PRIMARY_MODEL][name]
        if not groups:
            lines.append("_No priced trades yet._")
            continue
        lines += [
            "| Group | Trades | Net P&L | Expectancy | PF | Win% |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
        for group, row in groups.items():
            lines.append(
                f"| {group} | {row['trade_count']} | ${row['net_pnl']:,.2f} | "
                f"${row['expectancy']:,.2f} | {row['profit_factor']:.3f} | "
                f"{row['win_rate'] * 100:.1f}% |"
            )
    endpoint = summary["endpoint"]
    lines += ["", "## Registered endpoint", ""]
    for name, state in endpoint["conditions"].items():
        mark = "met" if state["met"] else "not met"
        lines.append(f"- {name}: {state['observed']}/{state['required']} ({mark})")
    lines.append(f"- Endpoint reached: {'yes' if endpoint['reached'] else 'no'}")
    gates = summary["gates"]
    lines += ["", "## Decision gates", ""]
    for name, passed in gates["checks"].items():
        lines.append(f"- {name}: {'pass' if passed else 'fail'}")
    lines += [
        f"- Entry coverage: {gates['entry_coverage'] * 100:.1f}%",
        f"- Edge classification: **{gates['edge_classification']}**",
        "",
        (
            "Conclusion is provisional until the registered endpoint is reached."
            if not endpoint["reached"]
            else (
                "Endpoint reached: "
                + (
                    "a stressed executable edge remains."
                    if gates["passed"]
                    else "the prospective study did not demonstrate an executable edge."
                )
            )
        ),
        "",
    ]
    return "\n".join(lines)


def write_reports(cohort_dir: Path, summary: dict[str, Any]) -> tuple[Path, Path]:
    json_path = cohort_dir / SUMMARY_JSON_FILE
    md_path = cohort_dir / SUMMARY_MD_FILE
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_summary_markdown(summary), encoding="utf-8")
    return json_path, md_path


# ---------------------------------------------------------------------------
# Integrity audit
# ---------------------------------------------------------------------------

def verify_cohort(cohort_dir: Path, repo_root: Path) -> list[str]:
    """Return every integrity problem found in a cohort; empty means clean."""
    problems: list[str] = []
    manifest = load_manifest(cohort_dir)
    problems += [f"manifest drift: {reason}" for reason in manifest_drift(manifest, repo_root)]

    start = dt.date.fromisoformat(manifest["prospective_start_date"])
    trades = read_jsonl(trades_path(cohort_dir))
    daily_runs = read_jsonl(daily_runs_path(cohort_dir))

    for label, records, key in (
        ("trades.jsonl", trades, "trade_id"),
        ("daily_runs.jsonl", daily_runs, "session_date"),
    ):
        seen: set[str] = set()
        for record in records:
            identity = record.get(key)
            if identity in seen:
                problems.append(f"{label}: duplicate {key}={identity}")
            seen.add(identity)
            stored = dict(record)
            recorded_hash = stored.pop("record_hash", None)
            if recorded_hash != canonical_hash(stored):
                problems.append(f"{label}: record hash mismatch for {key}={identity}")
            if record.get("cohort_id") != manifest["cohort_id"]:
                problems.append(f"{label}: foreign cohort_id for {key}={identity}")
            session = dt.date.fromisoformat(record["session_date"])
            if session < start:
                problems.append(f"{label}: session {session} predates cohort start {start}")

    run_by_date = {run["session_date"]: run for run in daily_runs}
    for trade in trades:
        run = run_by_date.get(trade["session_date"])
        if run is None:
            problems.append(f"trades.jsonl: no daily run for session {trade['session_date']}")
        elif run.get("trade_id") != trade["trade_id"]:
            problems.append(
                f"daily_runs.jsonl: session {trade['session_date']} does not reference "
                f"trade {trade['trade_id']}"
            )
        expected = trade_key(
            manifest["cohort_id"],
            dt.date.fromisoformat(trade["session_date"]),
            dt.datetime.fromisoformat(trade["decision_time"]),
            trade["direction"],
            (trade["lower_strike"], trade["center_strike"], trade["upper_strike"]),
        )
        if expected != trade["trade_id"]:
            problems.append(f"trades.jsonl: non-deterministic trade_id {trade['trade_id']}")
    return problems
