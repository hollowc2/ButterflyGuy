"""The ThetaData source is a stub until the subscription is active."""

from __future__ import annotations

import datetime as dt

import pytest

from butterfly_guy.research import history
from butterfly_guy.research.thetadata import NOT_PURCHASED, ThetaDataSource

D = dt.date


def test_thetadata_is_not_registered():
    assert "thetadata" not in history.SOURCES
    assert not any(f is ThetaDataSource for f in history.SOURCES.values())
    with pytest.raises(NotImplementedError, match="Data provider not chosen"):
        history.get_source("thetadata")


@pytest.mark.parametrize("call", [
    lambda s: s.sessions(D(2026, 3, 13), D(2026, 9, 25)),
    lambda s: s.quotes(D(2026, 3, 13), (6000.0, 7000.0)),
    lambda s: s.index_bars(D(2026, 3, 13), "SPX"),
    lambda s: s.daily_bars(D(2026, 3, 13), D(2026, 9, 25)),
    lambda s: s.cost_estimate(D(2026, 3, 13), D(2026, 9, 25)),
])
def test_every_data_method_raises(call):
    with pytest.raises(NotImplementedError, match="ThetaData not purchased yet"):
        call(ThetaDataSource())
    assert NOT_PURCHASED.startswith("ThetaData not purchased yet")


def test_describe_is_static_and_carries_no_credential():
    d = ThetaDataSource().describe()
    assert d["vendor"] == "ThetaData" and "not purchased" in d["status"]
    assert not any(k in str(d).lower() for k in ("api_key", "password", "token"))


def test_stub_satisfies_the_history_source_interface():
    names = [n for n in vars(history.HistorySource) if not n.startswith("_")]
    assert set(names) <= set(dir(ThetaDataSource))
