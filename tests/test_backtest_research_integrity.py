from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

import butterfly_guy.backtest.simulation_engine as simulation_engine
from butterfly_guy.backtest.csv_loader import CsvDataLoader
from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.backtest.simulation_engine import DayResult, SimulationEngine, SimulationParams
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.scripts.run_backtest_db import _summarize_combo


def _write_bars(path, rows: list[tuple[str, float]]) -> None:
    pd.DataFrame(
        [
            {"ts": ts, "open": close, "high": close, "low": close, "close": close}
            for ts, close in rows
        ]
    ).to_csv(path, index=False)


def test_csv_loader_uses_prior_vix_close_and_preserves_underlying(tmp_path):
    asset_path = tmp_path / "ndx_1min.csv"
    vix_path = tmp_path / "vix_1min.csv"
    _write_bars(
        asset_path,
        [
            ("2026-07-01 16:00:00", 25000.0),
            ("2026-07-02 10:00:00", 25100.0),
        ],
    )
    _write_bars(
        vix_path,
        [
            ("2026-07-01 16:00:00", 18.0),
            ("2026-07-02 16:00:00", 30.0),
        ],
    )

    day = CsvDataLoader(asset_path, vix_path, underlying="NDX").load_day(
        dt.date(2026, 7, 2)
    )

    assert day is not None
    assert day.vix == 18.0
    assert day.underlying == "NDX"


def test_csv_loader_rejects_a_day_without_prior_inputs(tmp_path):
    asset_path = tmp_path / "spx_1min.csv"
    vix_path = tmp_path / "vix_1min.csv"
    _write_bars(asset_path, [("2026-07-01 10:00:00", 6200.0)])
    _write_bars(vix_path, [("2026-07-01 10:00:00", 18.0)])

    day = CsvDataLoader(asset_path, vix_path).load_day(dt.date(2026, 7, 1))

    assert day is None


def test_simulation_requests_the_matching_underlying_cache(monkeypatch):
    seen: list[str | None] = []

    def fake_load(_date, cache_dir=None, underlying=None):
        seen.append(underlying)
        return None

    monkeypatch.setattr(simulation_engine, "load_chain_day", fake_load)
    day = DayData(
        date=dt.date(2026, 7, 2),
        bars=[],
        vix=18.0,
        prev_close=25000.0,
        underlying="NDX",
    )

    SimulationEngine().simulate_day(day, SimulationParams())

    assert seen == ["NDX"]


def test_end_of_data_exit_applies_exit_slippage_and_commission(monkeypatch):
    date = dt.date(2026, 7, 2)
    entry_time = dt.datetime(2026, 7, 2, 10, 0, tzinfo=simulation_engine.EASTERN)
    exit_time = dt.datetime(2026, 7, 2, 15, 59, tzinfo=simulation_engine.EASTERN)
    candidate = ButterflyCandidate(
        direction="CALL",
        wing_width=10,
        center_strike=100.0,
        lower_strike=90.0,
        upper_strike=110.0,
        cost=1.0,
        ask=1.0,
        max_profit=9.0,
        reward_risk=9.0,
        lower_be=91.0,
        upper_be=109.0,
        distance_from_spot=0.0,
        spot_price=100.0,
    )
    quotes = [
        OptionQuote(
            symbol=f"C{strike}",
            underlying="SPX",
            expiration=date,
            strike=strike,
            option_type="CALL",
            bid=mark,
            ask=mark,
            mark=mark,
        )
        for strike, mark in ((90.0, 3.0), (100.0, 2.0), (110.0, 3.0))
    ]
    monkeypatch.setattr(
        simulation_engine,
        "load_chain_day",
        lambda _date, cache_dir=None, underlying=None: {exit_time: quotes},
    )
    day = DayData(
        date=date,
        bars=[
            MinuteBar(entry_time, 100.0, 100.0, 100.0, 100.0, 0),
            MinuteBar(exit_time, 100.0, 100.0, 100.0, 100.0, 0),
        ],
        vix=18.0,
        prev_close=99.0,
    )
    params = SimulationParams(
        hold_to_expiry=True,
        slippage=0.10,
        paper_commission_per_contract=0.65,
    )

    result = SimulationEngine().simulate_day_from_entry(
        day,
        params,
        entry_candidate=candidate,
        entry_price=1.0,
        entry_time=entry_time,
    )

    assert result.exit_reason == "end_of_day"
    assert result.exit_price == pytest.approx(1.874)
    assert result.pnl == pytest.approx(0.874)


def test_partial_session_is_excluded_instead_of_fabricating_an_exit(monkeypatch):
    date = dt.date(2026, 7, 2)
    entry_time = dt.datetime(2026, 7, 2, 10, 0, tzinfo=simulation_engine.EASTERN)
    partial_end = dt.datetime(2026, 7, 2, 11, 0, tzinfo=simulation_engine.EASTERN)
    candidate = ButterflyCandidate(
        direction="CALL",
        wing_width=10,
        center_strike=100.0,
        lower_strike=90.0,
        upper_strike=110.0,
        cost=1.0,
        ask=1.0,
        max_profit=9.0,
        reward_risk=9.0,
        lower_be=91.0,
        upper_be=109.0,
        distance_from_spot=0.0,
        spot_price=100.0,
    )
    monkeypatch.setattr(
        simulation_engine,
        "load_chain_day",
        lambda _date, cache_dir=None, underlying=None: None,
    )
    day = DayData(
        date=date,
        bars=[
            MinuteBar(entry_time, 100.0, 100.0, 100.0, 100.0, 0),
            MinuteBar(partial_end, 100.0, 100.0, 100.0, 100.0, 0),
        ],
        vix=18.0,
        prev_close=99.0,
    )

    result = SimulationEngine().simulate_day_from_entry(
        day,
        SimulationParams(hold_to_expiry=True),
        entry_candidate=candidate,
        entry_price=1.0,
        entry_time=entry_time,
    )

    assert result.traded is False
    assert result.exit_reason == "incomplete_data"
    assert result.pnl == 0.0


def test_sweep_summary_reports_research_coverage_and_costs():
    date = dt.date(2026, 7, 2)
    entry = dt.datetime(2026, 7, 2, 10, 0, tzinfo=dt.timezone.utc)
    exit_ = entry + dt.timedelta(minutes=195)
    winner = DayResult(
        date=date,
        traded=True,
        entry_time=entry,
        exit_time=exit_,
        exit_reason="end_of_day",
        pnl=2.0,
    )
    loser = DayResult(
        date=date + dt.timedelta(days=1),
        traded=True,
        entry_time=entry,
        exit_time=exit_,
        exit_reason="absolute_loss_stop",
        pnl=-1.0,
    )
    incomplete = DayResult(
        date=date + dt.timedelta(days=2),
        traded=False,
        exit_reason="incomplete_data",
    )

    summary = _summarize_combo(
        {"slippage": 0.05, "commission_per_contract": 0.65},
        [(winner.date, winner), (loser.date, loser), (incomplete.date, incomplete)],
    )

    assert summary["loaded_days"] == 3
    assert summary["evaluated_days"] == 2
    assert summary["incomplete_days"] == 1
    assert summary["trade_count"] == 2
    assert summary["trade_day_rate"] == 1.0
    assert summary["exposure"] == 0.5
    assert summary["expectancy"] == 0.5
    assert summary["avg_win"] == 2.0
    assert summary["avg_loss"] == -1.0
    assert summary["estimated_commission"] == pytest.approx(0.104)
    assert summary["estimated_slippage"] == 0.2
