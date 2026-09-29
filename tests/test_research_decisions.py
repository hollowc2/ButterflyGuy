"""No-future-quote selection and the monitoring loop's observation rules."""

from __future__ import annotations

import numpy as np
import pytest

from butterfly_guy.core.config import AppConfig, EntrySettings, StrategySettings
from butterfly_guy.research.accounting import Costs
from butterfly_guy.research.entry import (
    PROFILES,
    BaselineEntry,
    Entry,
    RunContext,
    Series,
    Session,
    select_at,
)
from butterfly_guy.research.exits import HELD, INCOMPLETE, PeakTrailer, monitor
from butterfly_guy.research.market import DayMarket, Fly, restrict_view
from butterfly_guy.research.simulate import simulate_entry
from tests.research_synth import DAY, fly_quotes, make_chain, minute

FLY_A = (5970.0, 5980.0, 5990.0)


def _config() -> AppConfig:
    return AppConfig(
        strategy=StrategySettings(wing_widths=[10], vix_width_buckets=[], rr_min=1.0,
                                  rr_target=10.0, rr_max=12.0, spot_range=100),
        entry=EntrySettings(strike_selection_method="BEST_RR", start_time="07:00",
                            end_time="07:45", timezone="America/Los_Angeles"),
    )


def _session(chain, clock_ts=None, close=5985.0, vix_ts=None) -> Session:
    clock_ts = chain.ts if clock_ts is None else np.asarray(clock_ts, dtype=np.int64)
    vix_ts = np.array([minute(9, 30)] if vix_ts is None else vix_ts, dtype=np.int64)
    return Session(
        date=DAY, market=DayMarket(chain), clock_ts=clock_ts,
        clock_spot=np.full(len(clock_ts), 5960.0), open=5960.0, prev_close=5950.0,
        close=close, vix=Series(vix_ts, np.full(len(vix_ts), 18.0)), profile=PROFILES["live"],
    )


def _two_fly_chain(extra_times=()):
    # Fly A is the only buildable fly (mark 0.975, RR ~9.3). Extra snapshots re-quote it
    # at a different price, so using one would change the selected cost.
    quotes = {**fly_quotes(minute(10, 0), (2.0, 2.1), (1.0, 1.05), (0.95, 1.0), FLY_A),
              **fly_quotes(minute(10, 5), (2.0, 2.1), (1.0, 1.05), (0.95, 1.0), FLY_A)}
    for t in extra_times:
        quotes |= fly_quotes(t, (2.4, 2.5), (1.0, 1.05), (0.95, 1.0), FLY_A)
    return make_chain([minute(10, 0), minute(10, 5), *extra_times], quotes)


def test_selection_uses_only_the_snapshot_at_or_before_the_decision():
    chain = _two_fly_chain()
    s = _session(chain)
    ctx = RunContext(_config())
    cand, i, _ = select_at(s, ctx, minute(10, 4, 59), "CALL", 18.0)
    assert i == 0 and s.market.ts[i] <= minute(10, 4, 59)
    assert (cand.lower_strike, cand.center_strike, cand.upper_strike) == FLY_A
    before = s.market.at_or_before(minute(9, 59, 59))
    assert before == -1  # nothing recorded yet: no quote may be borrowed from the future


def test_a_later_quote_never_changes_an_earlier_decision():
    ctx = RunContext(_config())
    base = select_at(_session(_two_fly_chain()), ctx, minute(10, 2), "CALL", 18.0)
    later = select_at(_session(_two_fly_chain([minute(10, 2, 1)])), ctx, minute(10, 2),
                      "CALL", 18.0)
    assert base[1] == later[1] == 0
    assert base[0].cost == later[0].cost


def test_entry_requires_a_fresh_vix_and_prices_at_the_decision_snapshot():
    chain = _two_fly_chain()
    ctx = RunContext(_config())
    stale = _session(chain, vix_ts=[minute(9, 50)])  # 10 min old at 10:00, max age 300 s
    fresh_later = _session(chain, vix_ts=[minute(9, 50), minute(10, 4)])
    assert BaselineEntry().entries(stale, ctx) == []
    (e,) = BaselineEntry().entries(fresh_later, ctx)
    assert e.ts_us == minute(10, 5) and e.index == 1  # first clock time with fresh VIX


def _path_session(marks, missing_at=(), last=(15, 59)):
    """Fly A path with the given mid marks at 10:00, 10:01, ... and a closing snapshot."""
    times = [minute(10, i) for i in range(len(marks))] + [minute(*last)]
    quotes = {}
    for t, m in zip(times, [*marks, marks[-1]], strict=True):
        # symmetric legs so that the fly mark equals m
        quotes |= fly_quotes(t, (m + 1.0, m + 1.0), (0.5, 0.5), (0.0, 0.0), FLY_A)
    for i in missing_at:
        del quotes[(times[i], FLY_A[1])]
    return make_chain(times, quotes)


def _monitor(chain, rule, entry_price=1.0):
    s = _session(chain)
    path = s.market.fly_path(Fly("CALL", *FLY_A))
    return monitor(date=DAY, clock_ts=s.clock_ts, snapshot_ts=s.market.ts, path=path,
                   entry_ts_us=int(chain.ts[0]), entry_price=entry_price, rules=(rule,))


def test_incomplete_observation_cannot_move_the_peak_or_trigger_an_exit():
    # 10:01 would be a new peak of 5.0 and 10:02 a 62% drawdown from it, but 10:01 is
    # missing a leg, so the peak only reaches 1.9 and nothing triggers.
    chain = _path_session([1.0, 5.0, 1.9, 1.9], missing_at=(1,))
    out = _monitor(chain, PeakTrailer())
    assert out.reason == HELD and out.peak == pytest.approx(1.9)


def test_confirmation_count_is_not_advanced_by_incomplete_observations():
    chain = _path_session([1.0, 3.0, 1.0, 1.0, 1.0, 1.0], missing_at=(3,))
    out = _monitor(chain, PeakTrailer(confirmation_polls=2))
    assert out.reason == "drawdown_morning"
    assert out.index == 4  # 10:02 counts once, 10:03 is skipped, 10:04 confirms


def test_short_session_is_incomplete_not_imputed():
    chain = _path_session([1.0, 1.1, 1.2], last=(14, 30))
    assert _monitor(chain, PeakTrailer()).reason == INCOMPLETE


def test_held_trade_without_official_close_is_excluded():
    chain = _path_session([1.0, 1.1, 1.2])
    s = _session(chain, close=None)
    e = Entry(Fly("CALL", *FLY_A), int(chain.ts[0]), 0, 1.0, "CALL")
    out = simulate_entry(s, RunContext(_config()), e, (), "X1", Costs())
    assert out == "missing_settlement"
    s_closed = _session(chain, close=5980.0)
    trade = simulate_entry(s_closed, RunContext(_config()), e, (), "X1", Costs())
    assert trade.exit_reason == HELD and trade.settlement == 10.0


def test_restrict_view_removes_quotes_outside_the_band():
    chain = make_chain([minute(10, 0)], fly_quotes(minute(10, 0), (1, 1.1), (1, 1.1), (1, 1.1)),
                       spot=5975.0)
    narrow = restrict_view(chain, strike_band=10.0)
    marks = narrow.fields["C_mark"][0]
    assert np.isfinite(marks[np.searchsorted(narrow.strikes, 5970.0)])
    assert np.isnan(marks[np.searchsorted(narrow.strikes, 5990.0)])
