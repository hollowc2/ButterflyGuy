"""Executable-side pricing, stress, roll-forward exits and the settlement fallback."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from butterfly_guy.backtest.execution_accounting import price_frozen_trade
from butterfly_guy.backtest.simulation_engine import DayResult
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.research.accounting import Costs, price_trade
from butterfly_guy.research.market import DayMarket, Fly, us_to_datetime
from tests.research_synth import DAY, fly_quotes, make_chain, minute

FLY = Fly("CALL", 5970.0, 5980.0, 5990.0)
COSTS = Costs(0.65)
T0, T1, T2 = minute(10, 0), minute(10, 1), minute(10, 2)


def _path(quotes, times=(T0, T1, T2)):
    return DayMarket(make_chain(list(times), quotes)).fly_path(FLY)


def test_marketable_and_stressed_use_executable_sides():
    quotes = {
        **fly_quotes(T0, lo=(3.0, 3.2), c=(1.5, 1.6), hi=(0.5, 0.6)),
        **fly_quotes(T1, lo=(4.0, 4.2), c=(1.0, 1.1), hi=(0.2, 0.3)),
    }
    fills = price_trade(_path(quotes, (T0, T1)), entry_index=0, entry_mark=0.45,
                        exit_index=1, exit_mark=2.25, settlement=None, costs=COSTS).fills
    commission = 4 * 0.65 / 100
    # Entry buys the outer legs at ask and sells two centers at bid.
    assert fills["marketable"].entry == pytest.approx(3.2 + 0.6 - 2 * 1.5 + commission)
    # Exit sells the outer legs at bid and buys two centers back at ask.
    assert fills["marketable"].exit == pytest.approx(4.0 + 0.2 - 2 * 1.1 - commission)
    # Stress moves each of the four contract fills $0.05 against us on each side.
    assert fills["stressed"].entry == pytest.approx(fills["marketable"].entry + 0.20)
    assert fills["stressed"].exit == pytest.approx(fills["marketable"].exit - 0.20)
    assert fills["midpoint"].entry == pytest.approx(0.45 + commission)
    assert fills["midpoint"].exit == pytest.approx(2.25 - commission)


def test_cash_settlement_is_free_in_every_model():
    quotes = fly_quotes(T0, lo=(3.0, 3.2), c=(1.5, 1.6), hi=(0.5, 0.6))
    out = price_trade(_path(quotes, (T0,)), entry_index=0, entry_mark=0.45, exit_index=None,
                      exit_mark=None, settlement=7.5, costs=COSTS)
    for model in ("midpoint", "marketable", "stressed"):
        assert out.fills[model].exit == 7.5
    assert out.pnl_dollars("stressed") == pytest.approx(100 * (7.5 - (0.8 + 0.026 + 0.20)))


def test_midpoint_exit_is_floored_like_paper_exit_price():
    quotes = {**fly_quotes(T0, (1, 1.2), (0.5, 0.6), (0.1, 0.2)),
              **fly_quotes(T1, (0.1, 0.2), (0.05, 0.1), (0.0, 0.05))}
    fills = price_trade(_path(quotes, (T0, T1)), entry_index=0, entry_mark=0.3, exit_index=1,
                        exit_mark=0.01, settlement=None, costs=COSTS).fills
    assert fills["midpoint"].exit == 0.05


@pytest.mark.parametrize("bad", ["missing", "crossed"])
def test_unusable_entry_market_is_not_priced_or_imputed(bad):
    lo = (3.0, 3.2) if bad == "missing" else (3.3, 3.2)  # crossed: bid > ask
    quotes = fly_quotes(T0, lo=lo, c=(1.5, 1.6), hi=(0.5, 0.6))
    if bad == "missing":
        del quotes[(T0, 5990.0)]
    out = price_trade(_path(quotes, (T0,)), entry_index=0, entry_mark=0.45, exit_index=None,
                      exit_mark=None, settlement=5.0, costs=COSTS)
    assert out.fills["marketable"].status == f"{bad}_entry_market"
    assert out.pnl_dollars("stressed") is None
    assert out.pnl_dollars("midpoint") is not None


def test_exit_rolls_forward_past_missing_and_crossed_snapshots():
    quotes = {
        **fly_quotes(T0, (3.0, 3.2), (1.5, 1.6), (0.5, 0.6)),
        **fly_quotes(T1, (4.0, 4.2), (1.0, 1.1), (0.2, 0.3)),
        **fly_quotes(T2, (3.5, 3.4), (1.0, 1.1), (0.2, 0.3)),  # crossed lower leg
        **fly_quotes(minute(10, 3), (3.8, 4.0), (1.0, 1.1), (0.2, 0.3)),
    }
    del quotes[(T1, 5980.0)]  # missing center at the trigger snapshot
    times = (T0, T1, T2, minute(10, 3))
    fills = price_trade(_path(quotes, times), entry_index=0, entry_mark=0.45, exit_index=1,
                        exit_mark=2.0, settlement=9.0, costs=COSTS).fills
    stressed = fills["stressed"]
    assert stressed.exit_index == 3 and stressed.exit_roll == 2
    assert stressed.exit == pytest.approx(3.8 + 0.2 - 2 * 1.1 - 0.026 - 0.20)
    assert not stressed.settlement_fallback


def test_exit_falls_back_to_settlement_when_no_executable_snapshot_remains():
    quotes = {**fly_quotes(T0, (3.0, 3.2), (1.5, 1.6), (0.5, 0.6)),
              **fly_quotes(T1, (4.0, 4.2), (1.0, 1.1), (0.2, 0.3))}
    del quotes[(T1, 5990.0)]
    fills = price_trade(_path(quotes, (T0, T1)), entry_index=0, entry_mark=0.45, exit_index=1,
                        exit_mark=2.0, settlement=6.25, costs=COSTS).fills
    assert fills["stressed"].settlement_fallback
    assert fills["stressed"].exit == 6.25  # no commission or stress on settlement
    unsettled = price_trade(_path(quotes, (T0, T1)), entry_index=0, entry_mark=0.45,
                            exit_index=1, exit_mark=2.0, settlement=None, costs=COSTS)
    assert unsettled.fills["stressed"].status == "missing_exit_market"
    assert unsettled.pnl_dollars("stressed") is None


def _option_quotes(quotes, when):
    return [
        OptionQuote(symbol="", underlying="SPX", expiration=DAY, strike=k, option_type="CALL",
                    bid=b, ask=a, mark=m)
        for (ts, k), (b, a, m) in quotes.items() if ts == when
    ]


@pytest.mark.parametrize("model,ours", [("marketable", "marketable"),
                                        ("stressed_marketable", "stressed")])
def test_matches_execution_accounting_price_frozen_trade(model, ours):
    """Same entry, a missing trigger snapshot and a crossed one, then a usable exit."""
    times = (T0, T1, T2, minute(10, 3))
    quotes = {
        **fly_quotes(T0, (3.0, 3.25), (1.45, 1.6), (0.5, 0.65)),
        **fly_quotes(T1, (4.0, 4.2), (1.0, 1.1), (0.2, 0.3)),
        **fly_quotes(T2, (3.5, 3.4), (1.0, 1.1), (0.2, 0.3)),
        **fly_quotes(minute(10, 3), (3.8, 4.05), (0.95, 1.1), (0.15, 0.3)),
    }
    del quotes[(T1, 5980.0)]
    chains = {us_to_datetime(t): _option_quotes(quotes, t) for t in times}
    candidate = ButterflyCandidate(
        direction="CALL", wing_width=10, center_strike=5980.0, lower_strike=5970.0,
        upper_strike=5990.0, cost=0.45, max_profit=9.55, reward_risk=21.2, lower_be=0,
        upper_be=0, distance_from_spot=20, spot_price=5960,
    )
    baseline = DayResult(date=DAY, traded=True, direction="CALL",
                         entry_time=us_to_datetime(T0) + dt.timedelta(seconds=20),
                         exit_time=us_to_datetime(T1) + dt.timedelta(seconds=5),
                         exit_reason="drawdown_morning", exit_price=1.0)
    ref = price_frozen_trade(baseline=baseline, candidate=candidate, chains=chains, model=model)
    fills = price_trade(_path(quotes, times), entry_index=0, entry_mark=0.45, exit_index=1,
                        exit_mark=2.0, settlement=None, costs=COSTS).fills[ours]
    assert ref.status == "priced"
    assert fills.entry == pytest.approx(ref.entry_price, abs=1e-12)
    assert fills.exit == pytest.approx(ref.exit_price, abs=1e-12)
    assert fills.exit_roll == ref.skipped_exit_observations


# ---------------------------------------------------------------------------
# Exit-latency stress (stressed_delayed)
# ---------------------------------------------------------------------------

T3 = minute(10, 3)


def _delayed(quotes, times, delayed_index, settlement=9.0, exit_index=1):
    return price_trade(_path(quotes, times), entry_index=0, entry_mark=0.45,
                       exit_index=exit_index, exit_mark=2.0, settlement=settlement,
                       costs=COSTS, delayed_exit_index=delayed_index).fills


def test_delayed_exit_fills_one_snapshot_after_the_trigger():
    quotes = {**fly_quotes(T0, (3.0, 3.2), (1.5, 1.6), (0.5, 0.6)),
              **fly_quotes(T1, (4.0, 4.2), (1.0, 1.1), (0.2, 0.3)),
              **fly_quotes(T2, (3.6, 3.8), (1.0, 1.1), (0.2, 0.3))}
    fills = _delayed(quotes, (T0, T1, T2), delayed_index=2)
    assert fills["stressed"].exit_index == 1  # the undelayed models are unchanged
    d = fills["stressed_delayed"]
    assert d.exit_index == 2 and d.exit_roll == 0 and not d.settlement_fallback
    assert d.exit == pytest.approx(3.6 + 0.2 - 2 * 1.1 - 0.026 - 0.20)
    assert d.entry == fills["stressed"].entry


def test_delayed_exit_rolls_forward_past_unusable_snapshots():
    quotes = {**fly_quotes(T0, (3.0, 3.2), (1.5, 1.6), (0.5, 0.6)),
              **fly_quotes(T1, (4.0, 4.2), (1.0, 1.1), (0.2, 0.3)),
              **fly_quotes(T2, (3.9, 3.8), (1.0, 1.1), (0.2, 0.3)),  # crossed
              **fly_quotes(T3, (3.5, 3.7), (1.0, 1.1), (0.2, 0.3))}
    d = _delayed(quotes, (T0, T1, T2, T3), delayed_index=2)["stressed_delayed"]
    assert d.exit_index == 3 and d.exit_roll == 1
    assert d.exit == pytest.approx(3.5 + 0.2 - 2 * 1.1 - 0.026 - 0.20)


def test_delayed_exit_falls_back_to_settlement_or_stays_unpriced():
    quotes = {**fly_quotes(T0, (3.0, 3.2), (1.5, 1.6), (0.5, 0.6)),
              **fly_quotes(T1, (4.0, 4.2), (1.0, 1.1), (0.2, 0.3))}
    # The trigger was the last snapshot: no later market exists.
    d = _delayed(quotes, (T0, T1), delayed_index=2)["stressed_delayed"]
    assert d.settlement_fallback and d.exit == 9.0
    none = _delayed(quotes, (T0, T1), delayed_index=2, settlement=None)
    assert none["stressed_delayed"].status == "missing_exit_market"
    assert none["stressed"].exit_index == 1  # the trigger snapshot itself was usable


def test_held_trades_are_not_affected_by_the_delay():
    quotes = fly_quotes(T0, (3.0, 3.2), (1.5, 1.6), (0.5, 0.6))
    out = price_trade(_path(quotes, (T0,)), entry_index=0, entry_mark=0.45, exit_index=None,
                      exit_mark=None, settlement=7.5, costs=COSTS, delayed_exit_index=None)
    assert out.pnl_dollars("stressed_delayed") == out.pnl_dollars("stressed")


def _clock_session(chain_times, clock_times):
    from butterfly_guy.research.entry import PROFILES, Series, Session

    chain = make_chain(list(chain_times), {})
    clock = np.array(clock_times, dtype=np.int64)
    return Session(date=DAY, market=DayMarket(chain), clock_ts=clock,
                   clock_spot=np.full(len(clock), 5960.0), open=5960.0, prev_close=5950.0,
                   close=5980.0, vix=Series(clock, np.full(len(clock), 18.0)),
                   profile=PROFILES["live"])


def test_delayed_index_uses_the_next_clock_time_and_at_least_one_snapshot():
    from butterfly_guy.research.simulate import delayed_exit_index

    s = _clock_session((T0, T1, T2), (T0, T1, T2))
    assert delayed_exit_index(s, T1, 1, 1) == 2
    assert delayed_exit_index(s, T2, 2, 1) == 3  # past the end: settlement fallback
    # A clock denser than the chain: the next clock time maps back to the trigger's
    # snapshot, so the delay still moves to the next recorded snapshot.
    dense = _clock_session((T0, T1, T2), (T0, T1, minute(10, 1, 20), T2))
    assert delayed_exit_index(dense, T1, 1, 1) == 2
    # Two clock times reach only 10:02, but a delay of two means two recorded snapshots.
    assert delayed_exit_index(dense, T1, 1, 2) == 3
    assert delayed_exit_index(dense, T1, 1, 0) == 1


# ---------------------------------------------------------------------------
# Stressed-exit floor (owner's decision, 2026-09-29; off by default)
# ---------------------------------------------------------------------------

# At T1 and T2 the centers' ask blows out: selling the outer legs at bid and buying two
# centers at ask nets less than zero.
BLOWN_OUT = {
    **fly_quotes(T0, lo=(3.0, 3.2), c=(1.5, 1.6), hi=(0.5, 0.6)),
    **fly_quotes(T1, lo=(0.1, 0.2), c=(0.5, 0.9), hi=(0.0, 0.05)),
    **fly_quotes(T2, lo=(0.1, 0.2), c=(0.5, 0.8), hi=(0.0, 0.05)),
}


def _blown_out(costs, **kw):
    return price_trade(_path(BLOWN_OUT), entry_index=0, entry_mark=0.45, exit_index=1,
                       exit_mark=0.1, settlement=None, costs=costs, **kw).fills


def test_stressed_exits_are_not_floored_by_default():
    fills = _blown_out(COSTS, delayed_exit_index=2)
    assert fills["stressed"].exit == pytest.approx(0.1 - 1.8 - 0.026 - 0.20)
    assert fills["stressed_delayed"].exit == pytest.approx(0.1 - 1.6 - 0.026 - 0.20)
    assert not any(f.exit_floored for f in fills.values())


def test_floor_books_stressed_and_delayed_exits_below_zero_at_zero_only():
    floored = Costs(0.65, stressed_exit_floor=0.0)
    fills = _blown_out(floored, delayed_exit_index=2)
    for model in ("stressed", "stressed_delayed"):
        assert fills[model].exit == 0.0
        assert fills[model].exit_floored
        assert fills[model].exit_index == (1 if model == "stressed" else 2)
    # Marketable, midpoint and entries are unchanged.
    plain = _blown_out(COSTS, delayed_exit_index=2)
    assert fills["marketable"].exit == plain["marketable"].exit < 0
    assert not fills["marketable"].exit_floored
    assert fills["midpoint"].exit == plain["midpoint"].exit
    assert fills["stressed"].entry == plain["stressed"].entry


def test_floor_leaves_positive_exits_and_settlement_alone():
    floored = Costs(0.65, stressed_exit_floor=0.0)
    quotes = {**fly_quotes(T0, lo=(3.0, 3.2), c=(1.5, 1.6), hi=(0.5, 0.6)),
              **fly_quotes(T1, lo=(4.0, 4.2), c=(1.0, 1.1), hi=(0.2, 0.3))}
    args = dict(entry_index=0, entry_mark=0.45, exit_index=1, exit_mark=2.25, settlement=None)
    a = price_trade(_path(quotes, (T0, T1)), costs=floored, **args).fills
    b = price_trade(_path(quotes, (T0, T1)), costs=COSTS, **args).fills
    assert a["stressed"].exit == b["stressed"].exit > 0 and not a["stressed"].exit_floored
    held = price_trade(_path(quotes, (T0, T1)), entry_index=0, entry_mark=0.45, exit_index=None,
                       exit_mark=None, settlement=0.0, costs=floored).fills
    assert held["stressed"].exit == 0.0 and not held["stressed"].exit_floored


def test_trade_record_marks_floored_exits_only_when_floored():
    from butterfly_guy.research.report import trade_record
    from butterfly_guy.research.simulate import Trade

    def record(costs):
        fills = price_trade(_path(BLOWN_OUT), entry_index=0, entry_mark=0.45, exit_index=1,
                            exit_mark=0.1, settlement=None, costs=costs)
        return trade_record(Trade(DAY, "E0", FLY, T0, 0, 0.45, 18.0, 5960.0, "", "x", T1, 1,
                                  0.1, 0.45, None, fills))

    assert record(Costs(0.65, stressed_exit_floor=0.0))["stressed"]["exit_floored"] is True
    plain = record(COSTS)
    assert all("exit_floored" not in plain[m]
               for m in ("midpoint", "marketable", "stressed", "stressed_delayed"))


def test_run_records_the_floor_only_when_asked(tmp_path):
    import json
    from pathlib import Path

    from butterfly_guy.research import cli

    fixtures = Path(__file__).parent / "fixtures" / "research"
    metas = {}
    for flag in ([], ["--floor-stressed-exits"]):
        out = tmp_path / ("floored" if flag else "plain")
        assert cli.main(["--dataset", "mini_spx", "--cache", str(fixtures), "run", "--variants",
                         "E0", "--profile", "frozen_20260921", "--no-registry", "--no-tieset",
                         "--reps", "50", "--out", str(out), *flag]) == 0
        (results,) = out.glob("mini_spx/*/results.json")
        metas[bool(flag)] = json.loads(results.read_text())["meta"]
        report = (results.parent / "report.md").read_text()
        assert ("floored at $0.00" in report) is bool(flag)
    assert "stressed_exit_floor" not in metas[False]["accounting"]
    assert metas[True]["accounting"]["stressed_exit_floor"] == 0.0
