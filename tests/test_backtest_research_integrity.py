from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

import butterfly_guy.backtest.simulation_engine as simulation_engine
from butterfly_guy.backtest.csv_loader import CsvDataLoader
from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.backtest.execution_accounting import price_frozen_trade
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
) -> list[OptionQuote]:
    return [
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


def _baseline(
    date: dt.date,
    entry_time: dt.datetime,
    exit_time: dt.datetime,
    *,
    exit_reason: str = "drawdown_afternoon",
    exit_price: float = 0.0,
) -> DayResult:
    return DayResult(
        date=date,
        traded=True,
        direction="CALL",
        entry_time=entry_time,
        entry_price=0.5,
        exit_time=exit_time,
        exit_price=exit_price,
        exit_reason=exit_reason,
        pnl=exit_price - 0.5,
        peak_value=1.0,
        center_strike=100.0,
        wing_width=10,
    )


@pytest.mark.parametrize("direction", ["CALL", "PUT"])
def test_marketable_accounting_uses_entry_and_inverse_exit_sides(direction):
    date = dt.date(2026, 7, 2)
    entry_time = dt.datetime(2026, 7, 2, 14, 0, tzinfo=dt.timezone.utc)
    exit_time = entry_time + dt.timedelta(hours=2)
    chains = {
        entry_time: _quotes(
            date,
            direction,
            ((1.00, 1.10), (0.50, 0.60), (0.20, 0.30)),
        ),
        exit_time: _quotes(
            date,
            direction,
            ((2.00, 2.10), (0.80, 0.90), (0.40, 0.50)),
        ),
    }

    result = price_frozen_trade(
        baseline=_baseline(date, entry_time, exit_time),
        candidate=_candidate(direction),
        chains=chains,
        model="marketable",
    )

    # Entry: buy the two outer longs at ask, sell two center shorts at bid.
    assert result.entry_price == pytest.approx(1.10 + 0.30 - 2 * 0.50 + 0.026)
    # Exit: sell the outer longs at bid, buy two center shorts at ask.
    assert result.exit_price == pytest.approx(2.00 + 0.40 - 2 * 0.90 - 0.026)
    assert result.pnl == pytest.approx(0.148)


def test_stressed_marketable_charges_five_cents_per_contract_leg_per_side():
    date = dt.date(2026, 7, 2)
    entry_time = dt.datetime(2026, 7, 2, 14, 0, tzinfo=dt.timezone.utc)
    exit_time = entry_time + dt.timedelta(hours=2)
    chains = {
        entry_time: _quotes(date, "CALL", ((1.0, 1.1), (0.5, 0.6), (0.2, 0.3))),
        exit_time: _quotes(date, "CALL", ((2.0, 2.1), (0.8, 0.9), (0.4, 0.5))),
    }
    baseline = _baseline(date, entry_time, exit_time)
    marketable = price_frozen_trade(
        baseline=baseline,
        candidate=_candidate(),
        chains=chains,
        model="marketable",
    )
    stressed = price_frozen_trade(
        baseline=baseline,
        candidate=_candidate(),
        chains=chains,
        model="stressed_marketable",
    )

    assert stressed.entry_price == pytest.approx(marketable.entry_price + 4 * 0.05)
    assert stressed.exit_price == pytest.approx(marketable.exit_price - 4 * 0.05)
    assert stressed.pnl == pytest.approx(marketable.pnl - 8 * 0.05)


def test_cash_settlement_has_entry_commission_but_no_exit_fill_cost():
    date = dt.date(2026, 7, 2)
    entry_time = dt.datetime(2026, 7, 2, 14, 0, tzinfo=dt.timezone.utc)
    exit_time = entry_time + dt.timedelta(hours=6)
    baseline = _baseline(
        date,
        entry_time,
        exit_time,
        exit_reason="cash_settled",
        exit_price=3.0,
    )
    chains = {
        entry_time: _quotes(date, "CALL", ((1.0, 1.1), (0.5, 0.6), (0.2, 0.3))),
    }

    result = price_frozen_trade(
        baseline=baseline,
        candidate=_candidate(),
        chains=chains,
        model="marketable",
    )

    assert result.entry_price == pytest.approx(0.426)
    assert result.exit_price == 3.0
    assert result.pnl == pytest.approx(2.574)
    assert result.exit_snapshot_time is None


@pytest.mark.parametrize(
    ("bad_stage", "bad_market", "expected_status"),
    [
        ("entry", "missing", "missing_entry_market"),
        ("exit", "missing", "missing_exit_market"),
        ("entry", "crossed", "crossed_entry_market"),
        ("exit", "crossed", "crossed_exit_market"),
    ],
)
def test_marketable_accounting_rejects_missing_and_crossed_markets(
    bad_stage,
    bad_market,
    expected_status,
):
    date = dt.date(2026, 7, 2)
    entry_time = dt.datetime(2026, 7, 2, 14, 0, tzinfo=dt.timezone.utc)
    exit_time = entry_time + dt.timedelta(hours=2)
    valid = _quotes(date, "CALL", ((1.0, 1.1), (0.5, 0.6), (0.2, 0.3)))
    bad = valid[:2] if bad_market == "missing" else _quotes(
        date,
        "CALL",
        ((1.2, 1.1), (0.5, 0.6), (0.2, 0.3)),
    )
    chains = {
        entry_time: bad if bad_stage == "entry" else valid,
        exit_time: bad if bad_stage == "exit" else valid,
    }

    result = price_frozen_trade(
        baseline=_baseline(date, entry_time, exit_time),
        candidate=_candidate(),
        chains=chains,
        model="marketable",
    )

    assert result.status == expected_status
    assert result.priced is False
    assert result.pnl is None


def test_marketable_accounting_never_uses_a_future_quote():
    date = dt.date(2026, 7, 2)
    entry_time = dt.datetime(2026, 7, 2, 14, 0, tzinfo=dt.timezone.utc)
    exit_time = entry_time + dt.timedelta(hours=2)
    future_entry = entry_time + dt.timedelta(seconds=1)
    chains = {
        future_entry: _quotes(date, "CALL", ((1.0, 1.1), (0.5, 0.6), (0.2, 0.3))),
        exit_time: _quotes(date, "CALL", ((2.0, 2.1), (0.8, 0.9), (0.4, 0.5))),
    }

    result = price_frozen_trade(
        baseline=_baseline(date, entry_time, exit_time),
        candidate=_candidate(),
        chains=chains,
        model="marketable",
    )

    assert result.status == "missing_entry_market"
    assert result.entry_snapshot_time is None


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
        legacy_end_of_day_mark=True,
    )

    result = SimulationEngine().simulate_day_from_entry(
        day,
        params,
        entry_candidate=candidate,
        entry_price=1.0,
        entry_time=entry_time,
    )

    assert result.exit_reason == "legacy_end_of_day_mark"
    assert result.exit_price == pytest.approx(1.874)
    assert result.pnl == pytest.approx(0.874)


def test_held_to_close_butterfly_uses_settlement_intrinsic_value(monkeypatch):
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
            MinuteBar(exit_time, 107.0, 107.0, 107.0, 107.0, 0),
        ],
        vix=18.0,
        prev_close=99.0,
        settlement_spot=107.0,
    )

    result = SimulationEngine().simulate_day_from_entry(
        day,
        SimulationParams(hold_to_expiry=True),
        entry_candidate=candidate,
        entry_price=1.0,
        entry_time=entry_time,
    )

    assert result.exit_reason == "cash_settled"
    assert result.exit_price == pytest.approx(3.0)
    assert result.pnl == pytest.approx(2.0)

    day.settlement_spot = None
    missing = SimulationEngine().simulate_day_from_entry(
        day,
        SimulationParams(hold_to_expiry=True),
        entry_candidate=candidate,
        entry_price=1.0,
        entry_time=entry_time,
    )

    assert missing.traded is False
    assert missing.exit_reason == "missing_settlement"
    assert missing.pnl == 0.0


def test_incomplete_monitoring_snapshot_is_skipped_without_carry_forward(monkeypatch):
    date = dt.date(2026, 7, 2)
    entry_time = dt.datetime(2026, 7, 2, 10, 0, tzinfo=simulation_engine.EASTERN)
    peak_time = entry_time + dt.timedelta(minutes=10)
    drop_time = entry_time + dt.timedelta(minutes=20)
    incomplete_time = entry_time + dt.timedelta(minutes=30)
    close_time = dt.datetime(2026, 7, 2, 15, 59, tzinfo=simulation_engine.EASTERN)
    candidate = _candidate()
    peak_quotes = _quotes(date, "CALL", ((3.0, 3.0), (2.0, 2.0), (3.0, 3.0)))
    drop_quotes = _quotes(date, "CALL", ((1.5, 1.5), (1.25, 1.25), (1.5, 1.5)))
    incomplete_quotes = drop_quotes[:2]
    monkeypatch.setattr(
        simulation_engine,
        "load_chain_day",
        lambda _date, cache_dir=None, underlying=None: {
            peak_time: peak_quotes,
            drop_time: drop_quotes,
            incomplete_time: incomplete_quotes,
        },
    )
    day = DayData(
        date=date,
        bars=[
            MinuteBar(timestamp, 100.0, 100.0, 100.0, 100.0, 0)
            for timestamp in (
                entry_time,
                peak_time,
                drop_time,
                incomplete_time,
                close_time,
            )
        ],
        vix=18.0,
        prev_close=99.0,
        settlement_spot=100.0,
    )

    result = SimulationEngine().simulate_day_from_entry(
        day,
        SimulationParams(
            min_hold_minutes=25,
            morning_drawdown=0.5,
            use_absolute_loss_stop=False,
        ),
        entry_candidate=candidate,
        entry_price=1.0,
        entry_time=entry_time,
    )

    assert result.exit_reason == "cash_settled"
    assert result.exit_time == close_time


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
