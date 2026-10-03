"""H-TS1 mechanism check: window confinement, the statistic and the tercile split."""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd
import pytest

from butterfly_guy.research import mechanism
from butterfly_guy.research.holdout import HoldoutSealedError

D = dt.date


def _sessions(start: dt.date, end: dt.date) -> list[dt.date]:
    return [d.date() for d in pd.bdate_range(start, end)]


def _inputs(dates: list[dt.date], spx: list[float], vix1d: list[float], vix: list[float]
            ) -> tuple[pd.DataFrame, pd.DataFrame]:
    spx_df = pd.DataFrame({"date": dates, "close": spx})
    vol = pd.concat([
        pd.DataFrame({"date": pd.to_datetime(dates), "index": name, "open": v, "high": v,
                      "low": v, "close": v})
        for name, v in (("VIX1D", vix1d), ("VIX", vix))], ignore_index=True)
    return spx_df, vol


def _synthetic(start=D(2022, 5, 13), end=D(2024, 6, 28), seed=0, plant=0.0):
    """Random SPX closes; sessions after a high prior VIX1D/VIX move `plant` less."""
    dates = _sessions(start, end)
    rng = np.random.default_rng(seed)
    n = len(dates)
    vix = rng.uniform(15, 30, n)
    ratio = rng.uniform(0.5, 1.1, n)
    vix1d = vix * ratio
    closes = [4000.0]
    for i in range(1, n):
        sigma = vix1d[i - 1] / 100 / math.sqrt(252)
        scale = 1 - plant if ratio[i - 1] >= np.quantile(ratio, 2 / 3) else 1.0
        closes.append(closes[-1] * math.exp(rng.normal(0, sigma * scale)))
    return _inputs(dates, closes, list(vix1d), list(vix))


def test_statistic_matches_a_hand_computation():
    dates = [D(2023, 1, 3), D(2023, 1, 4), D(2023, 1, 5)]
    spx, vol = _inputs(dates, [4000.0, 4040.0, 4020.0], [16.0, 20.0, 12.0],
                       [20.0, 20.0, 20.0])
    table, excluded = mechanism.session_table(*mechanism.confine(spx, vol, dates[1],
                                                                 dates[2])[:2], dates[1])
    assert excluded == {}
    assert table["session"].tolist() == dates[1:]
    assert table["r"].tolist() == pytest.approx([
        abs(math.log(4040 / 4000)) / (16.0 / 100 / math.sqrt(252)),
        abs(math.log(4020 / 4040)) / (20.0 / 100 / math.sqrt(252))])
    assert table["ratio_prior"].tolist() == pytest.approx([0.8, 1.0])


def test_prior_values_come_from_the_previous_spx_session():
    # A VIX-family print on an SPX holiday (2023-01-16) is not the previous session.
    dates = [D(2023, 1, 13), D(2023, 1, 17)]
    spx = pd.DataFrame({"date": dates, "close": [4000.0, 4010.0]})
    _, vol = _inputs([D(2023, 1, 13), D(2023, 1, 16)], [0, 0], [16.0, 99.0], [20.0, 99.0])
    table, _ = mechanism.session_table(spx, vol, dates[1])
    assert table["vix1d_prior"].tolist() == [16.0]
    assert table["prior_session"].tolist() == [D(2023, 1, 13)]


def test_session_without_a_prior_vix1d_is_excluded():
    dates = [D(2023, 1, 3), D(2023, 1, 4)]
    spx = pd.DataFrame({"date": dates, "close": [4000.0, 4010.0]})
    _, vol = _inputs([D(2023, 1, 3)], [0], [float("nan")], [20.0])
    vol = vol[vol["index"] == "VIX"]
    table, excluded = mechanism.session_table(spx, vol, dates[1])
    assert table.empty and list(excluded) == ["2023-01-04"]


def test_tercile_split_uses_numpy_quantile_and_ties_go_to_the_top():
    ratio = np.array([0.5, 0.6, 0.7, 0.8, 0.9, 0.9])
    q13, q23, top = mechanism.tercile_split(ratio)
    assert q23 == float(np.quantile(ratio, 2 / 3)) and q13 == float(np.quantile(ratio, 1 / 3))
    assert top.tolist() == (ratio >= q23).tolist()
    assert mechanism.statistic(np.array([1.0, 1, 1, 1, 0.5, 0.5]), top) == pytest.approx(-0.5)
    assert math.isnan(mechanism.statistic(np.ones(3), np.zeros(3, bool)))


@pytest.mark.usefixtures("sealed_holdout")
def test_window_touching_the_holdout_raises():
    spx, vol = _synthetic(end=D(2024, 7, 31))
    with pytest.raises(HoldoutSealedError):
        mechanism.run(spx, vol, D(2022, 5, 16), D(2024, 7, 1))
    with pytest.raises(ValueError, match="development period"):
        mechanism.confine(spx, vol, D(2021, 12, 1), D(2022, 3, 1))


def test_rows_outside_the_window_are_dropped_before_computing():
    spx, vol = _synthetic(start=D(2022, 5, 13), end=D(2024, 6, 28))
    base, base_table = mechanism.run(spx, vol)
    # Poison every row after the window (holdout dates included) and before it.
    after = _sessions(D(2024, 7, 1), D(2025, 3, 31))
    before = _sessions(D(2022, 1, 3), D(2022, 5, 12))
    extra_spx, extra_vol = _inputs(before + after, [1e9] * len(before + after),
                                   [-5.0] * len(before + after), [0.0] * len(before + after))
    spx_p = pd.concat([spx, extra_spx]).sort_values("date", ignore_index=True)
    vol_p = pd.concat([vol, extra_vol], ignore_index=True)
    poisoned, poisoned_table = mechanism.run(spx_p, vol_p)
    assert poisoned == base
    pd.testing.assert_frame_equal(poisoned_table, base_table)
    assert base["inputs_in_window"]["max_date"] <= "2024-06-28"
    assert base_table["session"].min() == D(2022, 5, 16)


def test_first_session_uses_the_prior_development_session():
    spx, vol = _synthetic()
    spx_in, vol_in, lo = mechanism.confine(spx, vol, D(2022, 5, 16), D(2024, 6, 28))
    assert lo == D(2022, 5, 13)
    assert spx_in["date"].min() == lo and spx_in["date"].max() == D(2024, 6, 28)


def test_decision_rule_on_planted_and_null_effects():
    supported, _ = mechanism.run(*_synthetic(seed=3, plant=0.5))
    assert supported["result"]["difference"] < 0
    assert supported["verdict"] == "supported"
    assert supported["result"]["bootstrap"]["ci90"][1] < 0
    null, _ = mechanism.run(*_synthetic(seed=3, plant=0.0))
    assert null["verdict"] == "not supported"
    assert set(null["halves"]) == {"H1", "H2"}
    assert null["halves"]["H1"]["last"] < "2023-06-01" <= null["halves"]["H2"]["first"]
    b = null["result"]["bootstrap"]
    assert (b["block"], b["reps"], b["seed"]) == (10, 10_000, 1)


def test_bootstrap_is_deterministic():
    r = np.random.default_rng(1).uniform(0, 2, 200)
    top = np.arange(200) % 3 == 0
    assert mechanism.bootstrap(r, top) == mechanism.bootstrap(r, top)


def test_cboe_spx_parser():
    data = b"DATE,SPX\n01/03/2022,4796.56\n01/04/2022,4793.54\n"
    df = mechanism.parse_spx_csv(data)
    assert df["date"].tolist() == [D(2022, 1, 3), D(2022, 1, 4)]
    assert df["close"].tolist() == [4796.56, 4793.54]
    with pytest.raises(ValueError, match="columns"):
        mechanism.parse_spx_csv(b"DATE,OPEN,CLOSE\n01/03/2022,1,2\n")
