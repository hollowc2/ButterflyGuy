from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from butterfly_guy.backtest.execution_accounting import price_frozen_trade
from butterfly_guy.backtest.prospective_execution import (
    EXECUTABLE_MODELS,
    MIDPOINT_MODEL,
    CohortSpec,
    LedgerConflictError,
    ManifestDriftError,
    SessionOutcome,
    SessionOutOfRangeError,
    build_manifest,
    build_trade_record,
    daily_runs_path,
    leg_provenance,
    manifest_drift,
    read_jsonl,
    record_session,
    summarize_cohort,
    trade_key,
    trades_path,
    verify_cohort,
    write_manifest,
)
from butterfly_guy.backtest.simulation_engine import DayResult
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote

COMMISSION = 0.65
ENTRY_COMMISSION = 4 * COMMISSION
STRESS_PER_SIDE = 4 * 0.05 * 100
START = dt.date(2026, 9, 22)
TRACKED = "src/butterfly_guy/backtest/execution_accounting.py"


# ---------------------------------------------------------------------------
# Fixtures and builders
# ---------------------------------------------------------------------------

def _candidate(direction: str = "CALL") -> ButterflyCandidate:
    return ButterflyCandidate(
        direction=direction,
        wing_width=10,
        center_strike=100.0,
        lower_strike=90.0,
        upper_strike=110.0,
        cost=0.5,
        ask=0.5,
        max_profit=9.5,
        reward_risk=19.0,
        lower_be=90.5,
        upper_be=109.5,
        distance_from_spot=0.0,
        spot_price=100.0,
    )


def _quotes(
    date: dt.date,
    direction: str,
    prices: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    *,
    drop: str | None = None,
) -> list[OptionQuote]:
    quotes = [
        OptionQuote(
            symbol=f"{direction[0]}{strike}",
            underlying="SPX",
            expiration=date,
            strike=strike,
            option_type=direction,
            bid=bid,
            ask=ask,
            mark=(bid + ask) / 2,
        )
        for strike, (bid, ask) in zip((90.0, 100.0, 110.0), prices, strict=True)
    ]
    if drop is not None:
        index = {"lower": 0, "center": 1, "upper": 2}[drop]
        quotes.pop(index)
    return quotes


def _baseline(
    date: dt.date,
    entry_time: dt.datetime,
    exit_time: dt.datetime,
    *,
    direction: str = "CALL",
    exit_reason: str = "drawdown_afternoon",
    exit_price: float = 0.0,
    peak_value: float = 1.0,
    settlement_spot: float | None = None,
) -> DayResult:
    return DayResult(
        date=date,
        traded=True,
        direction=direction,
        entry_time=entry_time,
        entry_price=0.5,
        exit_time=exit_time,
        exit_price=exit_price,
        exit_reason=exit_reason,
        pnl=exit_price - 0.5,
        peak_value=peak_value,
        center_strike=100.0,
        wing_width=10,
        settlement_spot=settlement_spot,
    )


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "configs").mkdir(parents=True)
    (root / "configs" / "config.yaml").write_text("frozen: true\n", encoding="utf-8")
    tracked = root / TRACKED
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text("# frozen source\n", encoding="utf-8")
    return root


def _cohort(tmp_path: Path, *, start: dt.date = START) -> tuple[Path, dict, Path]:
    repo_root = _repo(tmp_path)
    spec = CohortSpec(
        cohort_id="spx-test",
        asset="SPX",
        start_date=start,
        target_trades=120,
        min_cash_settlements=20,
        min_stressed_winners=15,
        max_drawdown=2500.0,
    )
    manifest = build_manifest(
        spec=spec,
        repo_root=repo_root,
        config_path=repo_root / "configs" / "config.yaml",
        strategy_parameters={"asset": "SPX", "wing": [10]},
        database_tables=("option_chain_snapshots",),
        init_command="init",
        commission_per_contract=COMMISSION,
    )
    cohort_dir = tmp_path / "cohort"
    write_manifest(cohort_dir, manifest)
    return cohort_dir, manifest, repo_root


def _session(
    date: dt.date,
    *,
    direction: str = "CALL",
    entry_prices=((1.00, 1.10), (0.50, 0.60), (0.20, 0.30)),
    exit_prices=((2.00, 2.10), (0.80, 0.90), (0.40, 0.50)),
    exit_reason: str = "drawdown_afternoon",
    exit_price: float = 0.0,
    settlement_spot: float | None = None,
    extra_snapshots: dict | None = None,
    drop_entry: str | None = None,
    drop_exit: str | None = None,
) -> SessionOutcome:
    """Build a traded session outcome priced by the shared accounting model."""
    entry_time = dt.datetime.combine(date, dt.time(14, 0), tzinfo=dt.timezone.utc)
    exit_time = entry_time + dt.timedelta(hours=2)
    chains = {
        entry_time: _quotes(date, direction, entry_prices, drop=drop_entry),
    }
    if exit_reason != "cash_settled":
        chains[exit_time] = _quotes(date, direction, exit_prices, drop=drop_exit)
    chains.update(extra_snapshots or {})
    candidate = _candidate(direction)
    baseline = _baseline(
        date,
        entry_time,
        exit_time,
        direction=direction,
        exit_reason=exit_reason,
        exit_price=exit_price,
        settlement_spot=settlement_spot if exit_reason == "cash_settled" else None,
    )
    executions = {
        model: price_frozen_trade(
            baseline=baseline,
            candidate=candidate,
            chains=chains,
            model=model,
            commission_per_contract=COMMISSION,
            settlement_spot=settlement_spot,
        )
        for model in EXECUTABLE_MODELS
    }
    return SessionOutcome(
        session_date=date,
        status="traded",
        detail="frozen_entry_selection",
        candidate=candidate,
        baseline=baseline,
        chains=chains,
        executions=executions,
        settlement_spot=settlement_spot,
        signal_time=entry_time,
        row_counts={"merged_snapshots": len(chains)},
        data_range={"first_snapshot": min(chains).isoformat()},
    )


def _record(outcome: SessionOutcome, manifest: dict) -> dict:
    return build_trade_record(
        cohort_id=manifest["cohort_id"],
        outcome=outcome,
        commission_per_contract=COMMISSION,
        run_timestamp=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
        git_commit="abc123",
        config_sha256=manifest["config"]["sha256"],
    )


# ---------------------------------------------------------------------------
# Cohort boundaries and manifest drift
# ---------------------------------------------------------------------------

def test_sessions_before_the_cohort_start_are_rejected(tmp_path):
    cohort_dir, manifest, repo_root = _cohort(tmp_path)
    outcome = _session(START - dt.timedelta(days=1))

    with pytest.raises(SessionOutOfRangeError):
        record_session(
            cohort_dir=cohort_dir,
            manifest=manifest,
            outcome=outcome,
            repo_root=repo_root,
            command="update",
        )

    assert read_jsonl(trades_path(cohort_dir)) == []
    assert read_jsonl(daily_runs_path(cohort_dir)) == []


@pytest.mark.parametrize(
    ("changed", "expected"),
    [("configs/config.yaml", "configuration changed"), (TRACKED, "source changed")],
)
def test_manifest_drift_refuses_to_append(tmp_path, changed, expected):
    cohort_dir, manifest, repo_root = _cohort(tmp_path)
    (repo_root / changed).write_text("# edited after the freeze\n", encoding="utf-8")

    assert any(reason.startswith(expected) for reason in manifest_drift(manifest, repo_root))
    with pytest.raises(ManifestDriftError):
        record_session(
            cohort_dir=cohort_dir,
            manifest=manifest,
            outcome=_session(START),
            repo_root=repo_root,
            command="update",
        )
    assert read_jsonl(trades_path(cohort_dir)) == []


def test_unchanged_research_version_reports_no_drift(tmp_path):
    _, manifest, repo_root = _cohort(tmp_path)

    assert manifest_drift(manifest, repo_root) == []


# ---------------------------------------------------------------------------
# Quote provenance
# ---------------------------------------------------------------------------

def test_provenance_never_selects_a_quote_after_the_decision_time():
    date = START
    decision = dt.datetime.combine(date, dt.time(14, 0), tzinfo=dt.timezone.utc)
    stale = decision - dt.timedelta(seconds=30)
    chains = {
        stale: _quotes(date, "CALL", ((1.0, 1.1), (0.5, 0.6), (0.2, 0.3))),
        decision + dt.timedelta(seconds=1): _quotes(
            date, "CALL", ((9.0, 9.1), (9.5, 9.6), (9.2, 9.3))
        ),
    }

    provenance = leg_provenance(chains, decision, _candidate(), "entry")

    assert provenance["snapshot_time"] == stale.isoformat()
    assert provenance["age_seconds"] == 30.0
    assert all(leg["age_seconds"] == 30.0 for leg in provenance["legs"])


def test_entry_provenance_records_long_ask_short_bid_and_doubled_center():
    date = START
    decision = dt.datetime.combine(date, dt.time(14, 0), tzinfo=dt.timezone.utc)
    chains = {decision: _quotes(date, "CALL", ((1.0, 1.1), (0.5, 0.6), (0.2, 0.3)))}

    provenance = leg_provenance(chains, decision, _candidate(), "entry")
    legs = {leg["role"]: leg for leg in provenance["legs"]}

    assert legs["lower"]["executable_side"] == "ask"
    assert legs["upper"]["executable_side"] == "ask"
    assert legs["center"]["executable_side"] == "bid"
    assert (legs["lower"]["quantity"], legs["center"]["quantity"], legs["upper"]["quantity"]) == (
        1,
        -2,
        1,
    )


def test_exit_provenance_records_the_inverse_sides():
    date = START
    decision = dt.datetime.combine(date, dt.time(16, 0), tzinfo=dt.timezone.utc)
    chains = {decision: _quotes(date, "CALL", ((2.0, 2.1), (0.8, 0.9), (0.4, 0.5)))}

    provenance = leg_provenance(chains, decision, _candidate(), "exit")
    legs = {leg["role"]: leg for leg in provenance["legs"]}

    assert legs["lower"]["executable_side"] == "bid"
    assert legs["upper"]["executable_side"] == "bid"
    assert legs["center"]["executable_side"] == "ask"


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"entry_prices": ((1.0, 1.1), (0.5, 0.6), (0.2, 0.3)), "drop_entry": "center"}, "missing"),
        ({"entry_prices": ((1.2, 1.1), (0.5, 0.6), (0.2, 0.3))}, "crossed"),
    ],
)
def test_provenance_flags_missing_and_crossed_entry_markets(tmp_path, kwargs, expected):
    _, manifest, _ = _cohort(tmp_path)
    record = _record(_session(START, **kwargs), manifest)

    assert record["entry_provenance"]["status"] == expected


# ---------------------------------------------------------------------------
# Executable accounting inside the record
# ---------------------------------------------------------------------------

def test_marketable_record_prices_both_sides_and_charges_both_commissions(tmp_path):
    _, manifest, _ = _cohort(tmp_path)
    record = _record(_session(START), manifest)
    marketable = record["accounting"]["marketable"]

    assert marketable["entry_price"] == pytest.approx(1.10 + 0.30 - 2 * 0.50 + 0.026)
    assert marketable["exit_price"] == pytest.approx(2.00 + 0.40 - 2 * 0.90 - 0.026)
    assert marketable["net_pnl"] == pytest.approx(14.8)
    assert marketable["entry_commission"] == pytest.approx(ENTRY_COMMISSION)
    assert marketable["exit_commission"] == pytest.approx(ENTRY_COMMISSION)
    assert marketable["gross_pnl"] == pytest.approx(14.8 + 2 * ENTRY_COMMISSION)


def test_stressed_record_charges_five_cents_on_every_executable_contract_leg(tmp_path):
    _, manifest, _ = _cohort(tmp_path)
    record = _record(_session(START), manifest)
    marketable = record["accounting"]["marketable"]
    stressed = record["accounting"]["stressed_marketable"]

    assert stressed["net_pnl"] == pytest.approx(marketable["net_pnl"] - 2 * STRESS_PER_SIDE)
    assert stressed["stress_cost"] == pytest.approx(2 * STRESS_PER_SIDE)
    assert stressed["gross_pnl"] == pytest.approx(
        stressed["net_pnl"] + 2 * ENTRY_COMMISSION + 2 * STRESS_PER_SIDE
    )


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"drop_entry": "upper"}, "missing_entry_market"),
        ({"entry_prices": ((1.0, 1.1), (0.7, 0.6), (0.2, 0.3))}, "crossed_entry_market"),
    ],
)
def test_unusable_entry_markets_leave_the_trade_unpriced(tmp_path, kwargs, expected):
    _, manifest, _ = _cohort(tmp_path)
    record = _record(_session(START, **kwargs), manifest)

    for model in EXECUTABLE_MODELS:
        assert record["accounting"][model]["status"] == expected
        assert record["accounting"][model]["net_pnl"] is None


@pytest.mark.parametrize(
    "bad_exit",
    [
        {"drop_exit": "center"},
        {"exit_prices": ((2.0, 2.1), (1.0, 0.9), (0.4, 0.5))},
    ],
)
def test_unusable_exit_observations_are_skipped_and_roll_forward(tmp_path, bad_exit):
    _, manifest, _ = _cohort(tmp_path)
    date = START
    later = dt.datetime.combine(date, dt.time(16, 10), tzinfo=dt.timezone.utc)
    outcome = _session(
        date,
        extra_snapshots={later: _quotes(date, "CALL", ((3.0, 3.1), (0.8, 0.9), (0.4, 0.5)))},
        **bad_exit,
    )
    marketable = _record(outcome, manifest)["accounting"]["marketable"]

    assert marketable["status"] == "priced"
    assert marketable["skipped_exit_observations"] == 1
    assert marketable["exit_snapshot_time"] == later.isoformat()
    assert marketable["exit_price"] == pytest.approx(3.00 + 0.40 - 2 * 0.90 - 0.026)


def test_exit_without_any_executable_observation_falls_back_to_settlement(tmp_path):
    _, manifest, _ = _cohort(tmp_path)
    outcome = _session(START, drop_exit="lower", settlement_spot=105.0)
    marketable = _record(outcome, manifest)["accounting"]["marketable"]

    # 105 settles the 90/100/110 call fly at 105 - 90 - 2 * 5 = 5.00, with no closing order.
    assert marketable["status"] == "priced"
    assert marketable["settlement_fallback"] is True
    assert marketable["exit_price"] == pytest.approx(5.0)
    assert marketable["exit_commission"] == 0.0


def test_cash_settlement_invents_no_closing_commission_or_stress(tmp_path):
    _, manifest, _ = _cohort(tmp_path)
    outcome = _session(
        START,
        exit_reason="cash_settled",
        exit_price=3.0,
        settlement_spot=105.0,
    )
    record = _record(outcome, manifest)

    assert record["cash_settled"] is True
    assert record["settlement_spot"] == 105.0
    assert record["settlement_source"] == "official_close"
    assert record["exit_provenance"] is None
    for model in EXECUTABLE_MODELS:
        accounting = record["accounting"][model]
        assert accounting["exit_price"] == 3.0
        assert accounting["exit_commission"] == 0.0
    assert record["accounting"]["stressed_marketable"]["stress_cost"] == pytest.approx(
        STRESS_PER_SIDE
    )


def test_corrected_midpoint_baseline_is_preserved_alongside_executable_models(tmp_path):
    _, manifest, _ = _cohort(tmp_path)
    outcome = _session(START, exit_reason="cash_settled", exit_price=3.0, settlement_spot=105.0)
    record = _record(outcome, manifest)
    midpoint = record["accounting"][MIDPOINT_MODEL]

    assert midpoint["entry_price"] == pytest.approx(outcome.baseline.entry_price)
    assert midpoint["exit_price"] == pytest.approx(outcome.baseline.exit_price)
    assert midpoint["net_pnl"] == pytest.approx(outcome.baseline.pnl * 100)
    assert midpoint["net_pnl"] > record["accounting"]["stressed_marketable"]["net_pnl"]


# ---------------------------------------------------------------------------
# Append-only ledgers
# ---------------------------------------------------------------------------

def test_trade_ids_are_deterministic_for_one_frozen_decision(tmp_path):
    _, manifest, _ = _cohort(tmp_path)
    outcome = _session(START)
    first = _record(outcome, manifest)
    second = _record(_session(START), manifest)

    assert first["trade_id"] == second["trade_id"]
    assert first["trade_id"] == trade_key(
        manifest["cohort_id"],
        START,
        outcome.baseline.entry_time,
        "CALL",
        (90.0, 100.0, 110.0),
    )
    assert first["trade_id"] != _record(_session(START, direction="PUT"), manifest)["trade_id"]


def test_rerunning_an_unchanged_session_appends_nothing_new(tmp_path):
    cohort_dir, manifest, repo_root = _cohort(tmp_path)
    for _ in range(2):
        written = record_session(
            cohort_dir=cohort_dir,
            manifest=manifest,
            outcome=_session(START),
            repo_root=repo_root,
            command="update",
        )

    assert written["trade_appended"] is False
    assert len(read_jsonl(trades_path(cohort_dir))) == 1
    assert len(read_jsonl(daily_runs_path(cohort_dir))) == 1
    assert verify_cohort(cohort_dir, repo_root) == []


def test_a_conflicting_rerun_is_refused_instead_of_duplicated(tmp_path):
    cohort_dir, manifest, repo_root = _cohort(tmp_path)
    record_session(
        cohort_dir=cohort_dir,
        manifest=manifest,
        outcome=_session(START),
        repo_root=repo_root,
        command="update",
    )

    with pytest.raises(LedgerConflictError):
        record_session(
            cohort_dir=cohort_dir,
            manifest=manifest,
            outcome=_session(
                START,
                exit_prices=((5.00, 5.10), (0.80, 0.90), (0.40, 0.50)),
            ),
            repo_root=repo_root,
            command="update",
        )

    assert len(read_jsonl(trades_path(cohort_dir))) == 1


def test_sessions_with_incomplete_data_are_deferred_not_recorded(tmp_path):
    cohort_dir, manifest, repo_root = _cohort(tmp_path)
    written = record_session(
        cohort_dir=cohort_dir,
        manifest=manifest,
        outcome=SessionOutcome(
            session_date=START,
            status="incomplete_data",
            detail="official settlement not yet available",
        ),
        repo_root=repo_root,
        command="update",
    )

    assert written["deferred"] is True
    assert read_jsonl(daily_runs_path(cohort_dir)) == []


def test_verify_detects_a_tampered_record(tmp_path):
    cohort_dir, manifest, repo_root = _cohort(tmp_path)
    record_session(
        cohort_dir=cohort_dir,
        manifest=manifest,
        outcome=_session(START),
        repo_root=repo_root,
        command="update",
    )
    path = trades_path(cohort_dir)
    tampered = path.read_text(encoding="utf-8").replace(
        '"direction": "CALL"', '"direction": "PUT"'
    )
    path.write_text(tampered, encoding="utf-8")

    problems = verify_cohort(cohort_dir, repo_root)

    assert any("record hash mismatch" in problem for problem in problems)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _recorded_cohort(tmp_path) -> tuple[Path, dict, Path]:
    cohort_dir, manifest, repo_root = _cohort(tmp_path)
    sessions = [
        _session(START),  # marketable winner, intraday exit
        _session(
            START + dt.timedelta(days=1),
            exit_prices=((0.10, 0.20), (0.80, 0.90), (0.05, 0.10)),
        ),  # loser, intraday exit
        _session(
            START + dt.timedelta(days=2),
            exit_reason="cash_settled",
            exit_price=3.0,
            settlement_spot=105.0,
        ),  # cash-settled winner
    ]
    for outcome in sessions:
        record_session(
            cohort_dir=cohort_dir,
            manifest=manifest,
            outcome=outcome,
            repo_root=repo_root,
            command="update",
        )
    return cohort_dir, manifest, repo_root


def test_summary_metrics_match_the_recorded_trades(tmp_path):
    cohort_dir, manifest, _ = _recorded_cohort(tmp_path)
    trades = read_jsonl(trades_path(cohort_dir))
    summary = summarize_cohort(
        manifest=manifest,
        trades=trades,
        daily_runs=read_jsonl(daily_runs_path(cohort_dir)),
    )
    marketable = summary["models"]["marketable"]
    pnls = [trade["accounting"]["marketable"]["net_pnl"] for trade in trades]

    assert summary["eligible_trades"] == 3
    assert summary["cash_settled_trades"] == 1
    assert marketable["trade_count"] == 3
    assert marketable["priced_trades"] == 3
    assert marketable["complete_fill_coverage"] == 1.0
    assert marketable["net_pnl"] == pytest.approx(sum(pnls))
    assert marketable["expectancy"] == pytest.approx(sum(pnls) / 3, abs=1e-3)
    assert marketable["win_rate"] == pytest.approx(2 / 3, abs=1e-3)
    assert marketable["median_trade"] == pytest.approx(sorted(pnls)[1])
    assert marketable["top3_concentration"] == pytest.approx(1.0)
    assert summary["models"]["stressed_marketable"]["net_pnl"] == pytest.approx(
        marketable["net_pnl"] - 5 * STRESS_PER_SIDE
    )


def test_summary_breaks_results_down_by_half_and_settlement(tmp_path):
    cohort_dir, manifest, _ = _recorded_cohort(tmp_path)
    summary = summarize_cohort(
        manifest=manifest,
        trades=read_jsonl(trades_path(cohort_dir)),
        daily_runs=read_jsonl(daily_runs_path(cohort_dir)),
    )
    breakdowns = summary["breakdowns"]["marketable"]

    assert breakdowns["half"]["first_half"]["trade_count"] == 2
    assert breakdowns["half"]["second_half"]["trade_count"] == 1
    assert breakdowns["settlement"]["cash_settled"]["trade_count"] == 1
    assert breakdowns["settlement"]["intraday_exit"]["trade_count"] == 2
    assert breakdowns["direction"]["CALL"]["trade_count"] == 3
    assert set(breakdowns["month"]) == {"2026-09"}
    assert set(breakdowns["exit_reason"]) == {"cash_settled", "drawdown_afternoon"}


def test_summary_reports_endpoint_progress_and_gates(tmp_path):
    cohort_dir, manifest, _ = _recorded_cohort(tmp_path)
    summary = summarize_cohort(
        manifest=manifest,
        trades=read_jsonl(trades_path(cohort_dir)),
        daily_runs=read_jsonl(daily_runs_path(cohort_dir)),
    )

    assert summary["primary_model"] == "stressed_marketable"
    assert summary["endpoint"]["reached"] is False
    assert summary["endpoint"]["conditions"]["eligible_trades"] == {
        "observed": 3,
        "required": 120,
        "met": False,
    }
    assert summary["gates"]["entry_coverage"] == 1.0
    assert set(summary["gates"]["checks"]) >= {
        "stressed_net_pnl_positive",
        "stressed_expectancy_positive",
        "stressed_profit_factor_above_one",
        "marketable_positive_in_both_halves",
        "executable_entry_coverage",
        "top3_within_limit",
        "drawdown_within_limit",
    }
