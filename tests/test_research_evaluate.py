"""Paired day-block bootstrap, session zero-fill and trade metrics."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from butterfly_guy.research.accounting import Fill, TradeFills
from butterfly_guy.research.evaluate import (
    EvalParams,
    block_bootstrap_indices,
    paired_bootstrap,
    session_vector,
    trade_metrics,
)
from butterfly_guy.research.market import Fly
from butterfly_guy.research.simulate import Trade

PARAMS = EvalParams(bootstrap_reps=2000, bootstrap_block=5, bootstrap_seed=1)


def test_one_index_draw_is_applied_to_both_arms():
    rng = np.random.default_rng(3)
    base = rng.normal(0, 800, 60)
    # Identical arms: every resample has exactly zero difference.
    same = paired_bootstrap(base.copy(), base, PARAMS)
    assert same["ci90"] == [0.0, 0.0, 0.0] and same["p_better"] == 0.0
    # A constant per-session edge c gives exactly n*c in every paired resample, however
    # noisy the arms are; unpaired resampling would smear it.
    shifted = paired_bootstrap(base + 10.0, base, PARAMS)
    assert shifted["ci90"] == [600.0, 600.0, 600.0] and shifted["p_better"] == 1.0


def test_paired_bootstrap_equals_explicit_resampling_with_shared_indices():
    rng = np.random.default_rng(4)
    a, b = rng.normal(50, 500, 40), rng.normal(0, 500, 40)
    idx = block_bootstrap_indices(40, PARAMS.bootstrap_reps, 5, 1)
    totals = a[idx].sum(axis=1) - b[idx].sum(axis=1)
    got = paired_bootstrap(a, b, PARAMS)
    assert got["ci90"] == [round(float(x), 2) for x in np.percentile(totals, [5, 50, 95])]
    assert got["p_better"] == round(float((totals > 0).mean()), 4)


def test_block_bootstrap_matches_the_idea_sweep_harness():
    """The algorithm of `boot_ci` in docs/research/spx-idea-sweep-2026-09-25/variants.py."""
    diff = np.random.default_rng(5).normal(0, 300, 132)
    rng = np.random.default_rng(1)
    n, block, reps = len(diff), 5, 5000
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(reps, nb))
    idx = (starts[:, :, None] + np.arange(block)).reshape(reps, -1)[:, :n]
    tot = diff[idx].sum(1)
    ours = paired_bootstrap(diff, np.zeros(n), EvalParams())
    assert ours["ci90"] == [round(float(x), 2) for x in np.percentile(tot, [5, 50, 95])]


def test_indices_are_consecutive_blocks():
    idx = block_bootstrap_indices(12, 50, 4, 9)
    assert idx.shape == (50, 12)
    blocks = idx.reshape(50, 3, 4)
    assert (np.diff(blocks, axis=2) == 1).all()


def _trade(day: int, pnl_points: float | None) -> Trade:
    fills = TradeFills({m: Fill(entry=1.0, exit=None if pnl_points is None else 1.0 + pnl_points)
                        for m in ("midpoint", "marketable", "stressed")})
    return Trade(dt.date(2026, 6, day), "V", Fly("CALL", 1, 2, 3), 0, 0, 1.0, None, None, "",
                 "cash_settled", None, None, None, 0.0, 0.0, fills)


def test_session_vector_zero_fills_no_trade_and_unpriced_sessions():
    dates = [dt.date(2026, 6, d) for d in (1, 2, 3, 4)]
    vec = session_vector([_trade(2, 1.5), _trade(4, None)], dates, "stressed")
    assert vec.tolist() == [0.0, 150.0, 0.0, 0.0]


def test_trade_metrics_top3_and_drawdown():
    pnls = np.array([-100.0, 500.0, -200.0, 300.0, 100.0, -50.0])
    m = trade_metrics(pnls)
    assert m["net"] == 550.0
    assert m["net_without_top3"] == pytest.approx(550.0 - 900.0)
    assert m["top3_share"] == 100.0
    assert m["max_drawdown"] == 200.0
    assert m["profit_factor"] == pytest.approx(900 / 350, abs=1e-3)


def _full_trade(day: int, pnl_points: float, variant: str, direction: str = "CALL") -> Trade:
    from butterfly_guy.research.accounting import MODELS

    fills = TradeFills({m: Fill(entry=1.0, exit=1.0 + pnl_points) for m in MODELS})
    return Trade(dt.date(2026, 6, day), variant, Fly(direction, 1, 2, 3), 0, 0, 1.0, None,
                 None, "", "cash_settled", None, None, None, 0.0, 0.0, fills)


def test_multi_trade_sessions_sum_and_any_exclusion_drops_the_session_for_every_arm():
    from butterfly_guy.research.entry import BaselineEntry, BothSides
    from butterfly_guy.research.evaluate import evaluate
    from butterfly_guy.research.simulate import RunResult, Variant, VariantRun

    dates = [dt.date(2026, 6, d) for d in (1, 2, 3, 4)]
    base = VariantRun(Variant("E0", BaselineEntry()),
                      [_full_trade(d, 1.0, "E0") for d in (1, 2, 3, 4)])
    both = VariantRun(Variant("D3", BothSides()), [
        _full_trade(1, 2.0, "D3", "CALL"), _full_trade(1, -0.5, "D3", "PUT"),  # two trades
        _full_trade(2, 1.0, "D3", "CALL"),
        _full_trade(3, 4.0, "D3", "CALL"),  # its PUT entry on day 3 could not be replayed
    ], excluded={dt.date(2026, 6, 3): "incomplete_data"})
    ev = evaluate(RunResult(dates, {"E0": base, "D3": both}, {}), "E0",
                  EvalParams(min_bootstrap_sessions=0))
    assert ev["sessions"] == 3 and ev["dropped_sessions"] == {"2026-06-03": "D3:incomplete_data"}
    d3, e0 = ev["arms"]["D3"]["stressed"], ev["arms"]["E0"]["stressed"]
    assert d3["n"] == 3 and d3["net"] == pytest.approx(150.0 + 100.0)  # day 1 sums, day 3 out
    assert e0["net"] == pytest.approx(300.0)  # the baseline loses day 3 too: still paired
    assert d3["vs_baseline"]["net_diff"] == pytest.approx(-50.0)
    assert d3["per_session"] == round(250.0 / 3, 2)


def test_bootstrap_is_not_reported_on_too_few_sessions():
    out = paired_bootstrap(np.ones(3), np.zeros(3), EvalParams())
    assert out == {"ci90": None, "p_better": None}
