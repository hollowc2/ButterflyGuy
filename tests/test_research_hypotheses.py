"""Mechanics and leakage guards of the drafted hypothesis rules (H-SN1, H-EV1, H-TS1) on
synthetic data. They are not registered and are not run on any vendor data."""

from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import structlog

from butterfly_guy.core.config import AppConfig
from butterfly_guy.research import cli
from butterfly_guy.research.dataset import Dataset, SessionChain
from butterfly_guy.research.entry import PROFILES, RunContext, Series, Session, SessionLoader
from butterfly_guy.research.event_calendar import COLUMNS, EventCalendar
from butterfly_guy.research.features import DailyVol, SessionFeatures
from butterfly_guy.research.holdout import DEVELOPMENT
from butterfly_guy.research.hypotheses import (
    PriorRatioFilter,
    ReleaseSkipEntry,
    SigmaPlacedEntry,
    uses_features,
)
from butterfly_guy.research.learning import LeakageError, WindowedLoader, is_fitted
from butterfly_guy.research.market import DayMarket, et_us
from butterfly_guy.research.simulate import run_variants
from butterfly_guy.research.variants import CATALOG

FIXTURES = Path(__file__).parent / "fixtures" / "research"
DAY = dt.date(2024, 3, 14)
STRIKES = np.arange(5900.0, 6101.0, 5.0)


@pytest.fixture(autouse=True)
def _quiet():
    saved = structlog.get_config()
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    yield
    structlog.configure(**saved)


# ---------------------------------------------------------------------------
# H-SN1
# ---------------------------------------------------------------------------


def _session(quotes: dict[tuple[int, str, float], tuple[float, float]], times: list[int],
             open_: float = 6005.0, prev_close: float = 6000.0, spot: float = 6000.0) -> Session:
    ts = np.array(times, dtype=np.int64)
    fields = {f"{t}_{f}": np.full((len(ts), len(STRIKES)), np.nan)
              for t in "CP" for f in ("bid", "ask", "mark", "iv", "delta")}
    for (when, t, k), (bid, ask) in quotes.items():
        i, j = times.index(when), int(np.searchsorted(STRIKES, k))
        fields[f"{t}_bid"][i, j], fields[f"{t}_ask"][i, j] = bid, ask
        fields[f"{t}_mark"][i, j] = (bid + ask) / 2
    chain = SessionChain(DAY, ts, STRIKES.copy(), np.full(len(ts), spot), fields)
    return Session(date=DAY, market=DayMarket(chain), clock_ts=ts, clock_spot=chain.spot,
                   open=open_, prev_close=prev_close, close=None,
                   vix=Series(ts, np.full(len(ts), 18.0)), profile=PROFILES["live"])


def _straddle(when: int, total: float) -> dict:
    return {(when, "C", 6000.0): (total / 2 - 0.1, total / 2 + 0.1),
            (when, "P", 6000.0): (total / 2 - 0.1, total / 2 + 0.1)}


def _fly(when: int, t: str, legs: tuple[float, float, float],
         mids: tuple[float, float, float]) -> dict:
    return {(when, t, k): (m - 0.05, m + 0.05) for k, m in zip(legs, mids, strict=True)}


T0, T1 = et_us(DAY, 10, 0), et_us(DAY, 10, 1)
CTX = RunContext(AppConfig())


def test_sigma_placement_uses_the_1000_straddle_and_the_gap_direction():
    # sigma = 1.25 x 20 = 25: center 6000 + 1.58 x 25 = 6039.5 -> 6040; width 22 -> 20.
    s = _session({**_straddle(T0, 20.0),
                  **_fly(T0, "C", (6020.0, 6040.0, 6060.0), (3.1, 1.55, 0.65))}, [T0])
    (e,) = SigmaPlacedEntry().entries(s, CTX)
    assert (e.fly.direction, e.fly.lower, e.fly.center, e.fly.upper) == (
        "CALL", 6020.0, 6040.0, 6060.0)
    assert e.cost == pytest.approx(3.1 + 0.65 - 2 * 1.55) and e.ts_us == T0
    assert e.candidate is None and e.tag == "sigma"  # no tie-set: not the live selector


def test_put_side_and_sigma_fixed_at_1000_when_entry_is_later():
    # 10:00 fly over the width-20 cap ($2.00); at 10:01 it qualifies. The 10:01 straddle
    # (40) must not move the placement: sigma stays 1.25 x 20.
    legs = (5940.0, 5960.0, 5980.0)  # 6000 - 39.5 -> 5960.5 -> 5960
    s = _session({**_straddle(T0, 20.0), **_straddle(T1, 40.0),
                  **_fly(T0, "P", legs, (1.0, 0.5, 3.5)),  # cost 3.5
                  **_fly(T1, "P", legs, (1.0, 1.5, 2.9))},  # cost 0.9
                 [T0, T1], open_=5990.0)
    (e,) = SigmaPlacedEntry().entries(s, CTX)
    assert (e.fly.direction, e.fly.lower, e.fly.center, e.fly.upper) == ("PUT", *legs)
    assert e.ts_us == T1 and e.cost == pytest.approx(0.9)


def test_no_entry_without_a_straddle_crossed_legs_or_an_itm_center():
    rule = SigmaPlacedEntry()
    no_straddle = _session(_fly(T0, "C", (6020.0, 6040.0, 6060.0), (3.1, 1.55, 0.65)), [T0])
    assert rule.entries(no_straddle, CTX) == []
    crossed = _fly(T0, "C", (6020.0, 6040.0, 6060.0), (3.1, 1.55, 0.65))
    crossed[(T0, "C", 6040.0)] = (1.7, 1.4)
    assert rule.entries(_session({**_straddle(T0, 20.0), **crossed}, [T0]), CTX) == []
    # sigma = 1.25 x 0.8 = 1: the nearest strike to 6001.58 is 6000, not out of the money.
    tiny = _session({**_straddle(T0, 0.8),
                     **_fly(T0, "C", (5995.0, 6000.0, 6005.0), (3.0, 1.0, 0.1))}, [T0])
    assert rule.entries(tiny, CTX) == []


def test_width_rounding_and_cost_caps():
    rule = SigmaPlacedEntry()
    assert [rule.width(x) for x in (2.0, 25.0, 26.1, 40.0)] == [5, 20, 25, 35]
    assert rule.cost_cap(CTX, 20) == 2.0
    assert rule.cost_cap(CTX, 15) == pytest.approx(1.5)  # the single $0.10/pt rate
    strategy = CTX.config.strategy.model_copy(update={"max_cost_per_width": {
        10: 1.0, 20: 2.5, 30: 3.0}})
    uneven = RunContext(CTX.config.model_copy(update={"strategy": strategy}))
    with pytest.raises(ValueError, match="single per-point rate"):
        rule.cost_cap(uneven, 15)


# ---------------------------------------------------------------------------
# H-EV1
# ---------------------------------------------------------------------------


def _calendar(tmp_path, rows: list[dict]) -> EventCalendar:
    lines = [",".join(COLUMNS)]
    for r in rows:
        full = {c: "" for c in COLUMNS} | {"published_basis": "notice", "source": "test",
                                             "published_source": "test", "kind": "scheduled"}
        full.update(r)
        lines.append(",".join(full[c] for c in COLUMNS))
    path = tmp_path / "market_events_v1.csv"
    path.write_text("\n".join(lines) + "\n")
    return EventCalendar(path)


@dataclass(frozen=True)
class StubBase:
    def entries(self, s, ctx):
        return ["E0 entry"]


def test_release_skip_obeys_the_calendar_leakage_rule(tmp_path):
    cal = _calendar(tmp_path, [
        {"event_date": "2024-03-12", "event_type": "CPI", "release_time_et": "08:30",
         "published_on": "2024-02-13", "held": "false"},  # held is never used
        {"event_date": "2024-03-20", "event_type": "FOMC", "release_time_et": "14:00",
         "published_on": "2023-06-01"},
        {"event_date": "2024-04-05", "event_type": "NFP", "release_time_et": "08:30",
         "published_on": "2024-04-05"},  # published on the session: not yet known
        {"event_date": "2024-05-10", "event_type": "PCE", "release_time_et": "08:30",
         "published_on": "2024-04-26", "withdrawn_on": "2024-05-01", "held": "false"},
        {"event_date": "2024-05-15", "event_type": "CPI", "release_time_et": "10:00",
         "published_on": "2024-04-10"},  # at 10:00, not before it
        {"event_date": "2024-06-12", "event_type": "CPI", "release_time_et": "08:30",
         "kind": "unscheduled", "published_on": "2024-06-11"},
        {"event_date": "2024-06-28", "event_type": "PCE", "release_time_et": "08:30",
         "published_on": "2024-05-31", "withdrawn_on": "2024-06-28", "held": "false"},
    ])
    ctx = RunContext(AppConfig(), features=SimpleNamespace(calendar=cal))
    rule = ReleaseSkipEntry(StubBase())
    skipped = {d for d in ("2024-03-12", "2024-03-20", "2024-04-05", "2024-05-10",
                           "2024-05-15", "2024-06-12", "2024-06-28", "2024-07-01")
               if rule.skips(ctx, dt.date.fromisoformat(d))}
    assert skipped == {"2024-03-12", "2024-06-28"}  # withdrawn on the day: still expected
    s = SimpleNamespace(date=dt.date(2024, 3, 12), cache={})
    assert rule.entries(s, ctx) == []
    s = SimpleNamespace(date=dt.date(2024, 3, 20), cache={})
    assert rule.entries(s, ctx) == ["E0 entry"]


def test_feature_rules_refuse_to_run_without_features():
    s = SimpleNamespace(date=DAY, cache={})
    with pytest.raises(ValueError, match="needs session features"):
        ReleaseSkipEntry(StubBase()).entries(s, CTX)
    rule = PriorRatioFilter(StubBase(), "vix1d_vix", *DEVELOPMENT, threshold=1.0, fit_n=1)
    with pytest.raises(ValueError, match="needs session features"):
        rule.entries(s, CTX)


# ---------------------------------------------------------------------------
# H-TS1
# ---------------------------------------------------------------------------


def _vol(rows: dict[str, tuple[float, float]]) -> DailyVol:
    """{date: (VIX1D close, VIX close)}"""
    recs = []
    for d, (v1d, vix) in rows.items():
        recs += [{"date": pd.Timestamp(d), "index": "VIX1D", "open": 0, "high": 0, "low": 0,
                  "close": v1d},
                 {"date": pd.Timestamp(d), "index": "VIX", "open": 0, "high": 0, "low": 0,
                  "close": vix}]
    return DailyVol(pd.DataFrame(recs))


def _features(vol: DailyVol, sessions: list[str]) -> SessionFeatures:
    return SessionFeatures(EventCalendar(), vol, None, {},
                           np.array([dt.date.fromisoformat(d) for d in sessions]))


def test_term_structure_uses_the_prior_spx_session_close_only():
    vol = _vol({"2024-01-11": (10.0, 20.0), "2024-01-12": (12.0, 15.0),
                "2024-01-15": (30.0, 15.0),  # Cboe print on MLK day: not a session
                "2024-01-16": (99.0, 10.0)})  # the session's own close: never used
    ctx = RunContext(AppConfig(), features=_features(
        vol, ["2024-01-11", "2024-01-12", "2024-01-16"]))
    rule = PriorRatioFilter(StubBase(), "vix1d_vix", *DEVELOPMENT, threshold=0.8, fit_n=1)
    assert rule.value(ctx, dt.date(2024, 1, 16)) == pytest.approx(12.0 / 15.0)
    s = SimpleNamespace(date=dt.date(2024, 1, 16), cache={})
    assert rule.entries(s, ctx) == []  # 0.8 >= 0.8: skipped
    lower = PriorRatioFilter(StubBase(), "vix1d_vix", *DEVELOPMENT, threshold=0.81, fit_n=1)
    assert lower.entries(SimpleNamespace(date=dt.date(2024, 1, 16), cache={}), ctx) == [
        "E0 entry"]
    # No prior VIX1D close (before 2022-05-16): never skipped.
    assert rule.entries(SimpleNamespace(date=dt.date(2024, 1, 11), cache={}), ctx) == [
        "E0 entry"]
    with pytest.raises(ValueError, match="before it was fitted"):
        PriorRatioFilter(StubBase(), "vix1d_vix", *DEVELOPMENT).entries(s, ctx)


class StubLoader:
    def __init__(self, dates: list[dt.date], honest: bool = True) -> None:
        self._dates, self.honest = dates, honest

    def dates(self, start=None, end=None):
        if not self.honest:
            return list(self._dates)
        return [d for d in self._dates if (start is None or d >= start)
                and (end is None or d <= end)]


def test_the_threshold_is_fitted_inside_its_window_only():
    days = [dt.date(2024, 6, 24) + dt.timedelta(days=i) for i in range(10)]
    days = [d for d in days if d.weekday() < 5]  # 06-24 .. 07-05
    ratios = {d: 0.5 + 0.05 * i for i, d in enumerate(days)}
    ratios[days[-1]] = 5.0  # an extreme value after the window
    vol = _vol({d.isoformat(): (r * 20.0, 20.0) for d, r in ratios.items()})
    ctx = RunContext(AppConfig(), features=_features(vol, [d.isoformat() for d in days]))
    rule = PriorRatioFilter(StubBase(), "vix1d_vix", days[0], dt.date(2024, 6, 28))
    assert is_fitted(rule) and uses_features(rule)
    fitted = rule.fit(WindowedLoader(StubLoader(days), rule.fit_start, rule.fit_end), ctx)
    # Sessions 06-25 .. 06-28 have a prior close (06-24 has none): ratios 0.5 .. 0.65.
    expected = np.quantile([0.5, 0.55, 0.6, 0.65], 2 / 3)
    assert fitted.threshold == pytest.approx(expected) and fitted.fit_n == 4
    with pytest.raises(LeakageError, match="outside the fit window"):
        rule.fit(WindowedLoader(StubLoader(days, honest=False), rule.fit_start,
                                rule.fit_end), ctx)


# ---------------------------------------------------------------------------
# Catalog and run wiring
# ---------------------------------------------------------------------------


def test_catalog_entries_and_their_procedures():
    hsn1, hev1, hts1 = CATALOG["HSN1"], CATALOG["HEV1"], CATALOG["HTS1"]
    assert hsn1.exits == hev1.exits == hts1.exits == "config"
    assert hts1.fit_window == DEVELOPMENT
    assert hts1.definition()["entry"]["params"]["quantile"] == pytest.approx(2 / 3)
    # The definition hash covers the procedure, not a fitted value.
    fitted = PriorRatioFilter(hts1.entry.base, "vix1d_vix", *DEVELOPMENT, threshold=0.9,
                              fit_n=400)
    from butterfly_guy.research.simulate import Variant
    assert Variant("HTS1", fitted, "config", hts1.description).definition_hash() == \
        hts1.definition_hash()


def test_a_run_with_a_feature_rule_records_the_feature_inputs(tmp_path):
    ds = Dataset(FIXTURES / "mini_spx")
    feats = SessionFeatures.load(ds)
    loader = SessionLoader(ds, PROFILES["frozen_20260921"])
    result = run_variants(loader, [CATALOG["E0"], CATALOG["HEV1"]],
                          RunContext(cli.load_spx_config(), features=feats))
    e0 = {t.date for t in result.runs["E0"].trades}
    hev1 = {t.date for t in result.runs["HEV1"].trades}
    rule = CATALOG["HEV1"].entry
    ctx = RunContext(AppConfig(), features=feats)
    assert hev1 == {d for d in e0 if not rule.skips(ctx, d)}

    assert cli.main(["--dataset", "mini_spx", "--cache", str(FIXTURES), "run", "--variants",
                     "HEV1", "--profile", "frozen_20260921", "--no-registry", "--no-tieset",
                     "--reps", "50", "--out", str(tmp_path)]) == 0
    (results,) = tmp_path.glob("mini_spx/*/results.json")
    meta = json.loads(results.read_text())["meta"]
    assert meta["inputs"]["event_calendar"]["sha256"] == EventCalendar().sha256


# The hashes `register` would record, as listed in research-core and the 2026-09
# registration decision package. A change to a rule's class source or parameters changes
# its hash: update these (and the docs) deliberately, never to make a test pass.
# HTS1 was documented as 2ec8c008... in stage 4; the committed code has always given
# fab8bf3e... (stage 6 fact fix).
DEFINITION_HASHES = {
    "HLV1": "6ed12752c07aeda2b857e3c7a04129f85e02bbdf5be40b2ab46e4feade2ed6d6",
    "HSN1": "4589760a17440ebc01b86451b52f2dae18905eebb13270497476a468c2988147",
    "HEV1": "9180c56d9a7deb480778906bd3c199b164150e8389e6e089bdb1eb9ba23d660f",
    "HTS1": "fab8bf3e0ab10805d8b6d8ee19617df7013c0fa776ed6fbf86314c6238ff69c6",
}


@pytest.mark.parametrize("name", sorted(DEFINITION_HASHES))
def test_hypothesis_definition_hashes_match_the_decision_package(name):
    assert CATALOG[name].definition_hash() == DEFINITION_HASHES[name]
