"""Causal filtering and winner-retention accounting for the offline study."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "activation_study", Path(__file__).resolve().parents[1]
    / "tools/research_studies/activation_study.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_history_is_prior_only_and_resets_across_missing_history():
    f = pd.DataFrame({"date": ["2024-01-02", "2024-01-03", "2024-01-04", "2024-03-01"],
                      "stressed": [-100., 500., -200., 900.]})
    history = study.add_history(f)
    assert history.prior_dd.tolist() == [0, 100, 0, 0]
    changed = f.copy()
    changed.loc[2, "stressed"] = -10000
    assert study.add_history(changed).prior_dd.iloc[2] == history.prior_dd.iloc[2]
    assert history.prior20_pnl.isna().all()


def test_missing_feature_keeps_trade_and_comparator_boundary_is_exact():
    f = pd.DataFrame({"vix": [None, 16.99, 17.]})
    assert study.skip_mask(f, ("low", "vix", "lt", 17)).tolist() == [False, True, False]


def test_losses_avoided_are_separate_from_winners_missed_and_no_trade_days():
    f = pd.DataFrame({"traded": [True, True, True, False],
                      "stressed": [-100., 1000., -200., 0.],
                      "midpoint": [-80., 1020., -180., 0.],
                      "fly_minutes": [10., 100., 20., 0.],
                      "max_loss_r": [-1., 5., -1., None]})
    m = study.summary(f, np.array([False, True, True, True]))
    assert m["net"] == 800
    assert m["net_diff"] == 100
    assert m["losses_avoided"] == 100
    assert m["winning_dollars_missed"] == 0
    assert m["gross_wins_retained_pct"] == 100
    assert m["top10_retained"] == 1
    assert m["kept_trades"] == 2
    assert m["max_drawdown"] == 200
    assert m["cost_drag_vs_midpoint"] == 40


def test_all_losing_sample_has_no_top_winners():
    f = pd.DataFrame({"traded": [True], "stressed": [-10.], "midpoint": [-5.],
                      "fly_minutes": [10.], "max_loss_r": [-1.]})
    m = study.summary(f, np.array([True]))
    assert m["top10_retained"] == 0
    assert m["top10_available"] == 0
    assert m["gross_wins_retained_pct"] is None
