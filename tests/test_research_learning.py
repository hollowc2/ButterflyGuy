"""Leakage guards for learning and fitted rules, and the EV learners' decisions."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pytest
import structlog

from butterfly_guy.core.config import AppConfig
from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.entry import (
    PROFILES,
    BaselineEntry,
    RunContext,
    Series,
    Session,
    SessionLoader,
    cached_entries,
    load_spx_config,
    straddle_selection,
)
from butterfly_guy.research.evaluate import EvalParams, evaluate
from butterfly_guy.research.learning import (
    EVSelector,
    FittedFilter,
    History,
    LeakageError,
    WindowedLoader,
    entry_spread_ratio,
    settle_z,
)
from butterfly_guy.research.market import DayMarket
from butterfly_guy.research.simulate import Variant, entries_for, run_variants
from butterfly_guy.strategy.butterfly_builder import vix_expected_move
from tests.research_synth import DAY, STRIKES, make_chain, minute

MINI = Path(__file__).parent / "fixtures" / "research" / "mini_spx"
DATES = [dt.date(2026, 3, 19), dt.date(2026, 3, 26), dt.date(2026, 4, 7),
         dt.date(2026, 4, 16), dt.date(2026, 6, 12), dt.date(2026, 7, 13)]


@pytest.fixture(autouse=True)
def _quiet():
    saved = structlog.get_config()
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    yield
    structlog.configure(**saved)


@dataclass(frozen=True)
class Probe:
    """A learning rule that logs what it saw; it observes each session's official close."""

    log: list = field(default_factory=list, compare=False, hash=False)
    history_start: dt.date = DATES[0]

    def observe(self, s, ctx):
        self.log.append(("observe", s.date, s.close))
        return s.close

    def decide(self, s, ctx, history):
        self.log.append(("decide", s.date, history))
        return []


def _loader() -> SessionLoader:
    return SessionLoader(Dataset(MINI), PROFILES["frozen_20260921"])


def _ctx() -> RunContext:
    return RunContext(load_spx_config())


def _decisions(probe: Probe) -> dict[dt.date, tuple]:
    return {d: h for kind, d, h in probe.log if kind == "decide"}


def test_history_is_strictly_before_and_append_only_in_date_order():
    h = History()
    h.append(DATES[0], 1.0)
    h.append(DATES[1], 2.0)
    assert h.before(DATES[1]) == ((DATES[0], 1.0),)
    assert h.before(DATES[0]) == ()
    with pytest.raises(LeakageError):
        h.append(DATES[1], 3.0)  # a session is observed once, in order
    with pytest.raises(LeakageError):
        h.append(DATES[0], 3.0)


def test_learning_rule_sees_only_earlier_sessions_and_is_observed_after_deciding():
    probe = Probe()
    result = run_variants(_loader(), [Variant("E0", BaselineEntry()), Variant("P", probe, ())],
                          _ctx())
    assert result.dates  # the fixture replays
    order = [(kind, d) for kind, d, _ in probe.log]
    for d, history in _decisions(probe).items():
        assert all(h < d for h, _ in history)
        observed = [x for kind, x in order if kind == "observe" and x < d]
        assert [h for h, _ in history] == observed
        if ("observe", d) in order:
            assert order.index(("decide", d)) < order.index(("observe", d))


def test_warm_up_observes_earlier_sessions_without_scoring_them():
    probe = Probe()
    result = run_variants(_loader(), [Variant("E0", BaselineEntry()), Variant("P", probe, ())],
                          _ctx(), start=DATES[2])
    assert result.dates[0] >= DATES[2]
    assert all(t.date >= DATES[2] for t in result.runs["E0"].trades)
    first = _decisions(probe)[result.dates[0]]
    assert [d for d, _ in first] == [d for d in DATES[:2] if d < result.dates[0]]


def test_a_session_outcome_cannot_change_its_own_decision():
    base, bumped = Probe(), Probe()
    run_variants(_loader(), [Variant("P", base, ())], _ctx())
    loader = _loader()
    target = DATES[2]
    loader.closes[target] = loader.closes[target] + 500.0  # a wildly different settlement
    run_variants(loader, [Variant("P", bumped, ())], _ctx())
    a, b = _decisions(base), _decisions(bumped)
    assert a[target] == b[target]  # the decision on that session is unchanged
    later = [d for d in a if d > target]
    assert later and all(a[d] != b[d] for d in later)  # later sessions do learn from it


def test_a_learning_rule_cannot_decide_without_the_runner_history():
    loader = _loader()
    loader.dates(DATES[0], DATES[0])
    s = loader.load(DATES[0])
    with pytest.raises(LeakageError):
        entries_for(s, _ctx(), Probe())


class _Recording(SessionLoader):
    loaded: list

    def load(self, d):
        self.loaded.append(d)
        return super().load(d)


def test_windowed_loader_refuses_sessions_outside_the_fit_window():
    w = WindowedLoader(_loader(), DATES[0], DATES[2])
    assert w.dates() == DATES[:3]
    with pytest.raises(LeakageError):
        w.load(DATES[3])


def test_fitted_threshold_comes_only_from_its_window():
    ctx = _ctx()
    rule = FittedFilter(BaselineEntry(), "entry_spread_ratio", DATES[0], DATES[2],
                        if_undefined="keep")
    recording = _Recording(Dataset(MINI), PROFILES["frozen_20260921"])
    recording.loaded = []
    fitted = rule.fit(WindowedLoader(recording, DATES[0], DATES[2]), ctx)
    assert recording.loaded and all(d <= DATES[2] for d in recording.loaded)

    loader = _loader()
    values = []
    for d in loader.dates(DATES[0], DATES[2]):
        s = loader.load(d)
        values += [v for e in cached_entries(s, ctx, BaselineEntry())
                   if (v := entry_spread_ratio(s, e)) is not None]
    assert fitted.threshold == float(np.median(values)) and fitted.fit_n == len(values)

    spec, done = Variant("K", rule, "config"), Variant("K", fitted, "config")
    assert done.definition()["entry"]["fitted"] == {"threshold": fitted.threshold,
                                                    "fit_n": fitted.fit_n}
    assert done.definition()["entry"]["params"]["fit_end"] == DATES[2]
    assert done.definition_hash() == spec.definition_hash()  # the procedure is the variant
    with pytest.raises(ValueError):
        rule.entries(loader.load(DATES[0]), ctx)  # unfitted rules cannot trade


def test_fitted_rule_runs_fitted_and_reports_its_fit_window():
    rule = FittedFilter(BaselineEntry(), "entry_spread_ratio", DATES[0], DATES[2],
                        if_undefined="keep")
    result = run_variants(_loader(), [Variant("E0", BaselineEntry()), Variant("K", rule)],
                          _ctx())
    assert result.runs["K"].variant.entry.threshold is not None
    arm = evaluate(result, "E0", EvalParams())["arms"]["K"]
    assert arm["fit_window"] == [DATES[0].isoformat(), DATES[2].isoformat()]
    in_window = sum(d <= DATES[2] for d in result.dates)
    assert arm["sessions_in_fit_window"] == in_window
    assert "after_fit_net" in arm["stressed"]


# ---------------------------------------------------------------------------
# EV selector on a synthetic chain
# ---------------------------------------------------------------------------

CALL_MID = {5950.0: 12.0, 5960.0: 6.0, 5970.0: 2.5, 5980.0: 1.0, 5990.0: 0.4, 6000.0: 0.15}


def _ev_session(crossed_center: float | None = None) -> Session:
    t = minute(10, 0)
    quotes = {(t, k): (m - 0.05, m + 0.05, m) for k, m in CALL_MID.items()}
    if crossed_center is not None:
        m = CALL_MID[crossed_center]
        quotes[(t, crossed_center)] = (m + 0.1, m - 0.1, m)  # bid above ask
    chain = make_chain([t], quotes, typ="C", spot=5960.0)
    chain.fields["P_mark"][0, list(STRIKES).index(5960.0)] = 14.0  # straddle = 20
    return Session(date=DAY, market=DayMarket(chain), clock_ts=chain.ts,
                   clock_spot=chain.spot, open=5960.0, prev_close=5950.0, close=5981.0,
                   vix=Series(chain.ts, np.array([18.0])), profile=PROFILES["live"])


def _history(n: int, z: float = 1.0) -> tuple:
    return tuple((dt.date(2026, 5, 1) + dt.timedelta(days=i), z) for i in range(n))


RULE = EVSelector(10, 0, widths=(10,), strike_step=10)


def test_ev_selector_trades_the_highest_edge_fly_from_prior_history_only():
    s = _ev_session()
    ctx = RunContext(AppConfig())
    assert RULE.decide(s, ctx, _history(19)) == []  # needs min_history observations
    (e,) = RULE.decide(s, ctx, _history(20))
    assert (e.fly.direction, e.fly.lower, e.fly.center, e.fly.upper) == (
        "CALL", 5970.0, 5980.0, 5990.0)  # settlements cluster at spot + 1 straddle
    assert e.cost == pytest.approx(2.5 + 0.4 - 2 * 1.0)
    assert e.history_n == 20 and e.history_last == dt.date(2026, 5, 20)
    # A crossed leg removes every fly using it (here all three 10-wide flies near the
    # settlement cluster), and the rest have no positive edge: no trade, nothing imputed.
    assert RULE.decide(_ev_session(crossed_center=5980.0), ctx, _history(20)) == []


def test_settle_z_uses_the_official_close_and_the_straddle():
    assert settle_z(_ev_session(), 10, 0) == pytest.approx((5981.0 - 5960.0) / 20.0)


def test_straddle_selection_keeps_the_vix_bucket_and_moves_the_anchor():
    config = load_spx_config()
    one_bucket, vix = straddle_selection(config, 18.0, 6000.0, 12.5)
    (bucket,) = one_bucket.strategy.vix_width_buckets
    assert bucket.widths == [20, 30, 40]  # the 17-24.5 bucket of the entry VIX
    assert vix_expected_move(vix, 6000.0) == pytest.approx(12.5, rel=1e-12)
