"""Every idea-sweep variant reproduces its published row under `sweep_20260925`.

`docs/research/spx-idea-sweep-2026-09-25/results.json` and `results_round2.json` are
the numpy harness's output. Each ported variant must match its row to the dime: trade
count, stressed net, midpoint net, H1/H2, the paired 90% CI against E0 (rounded to
dollars, as published), P(better) and the settled-exit count.

Documented exceptions are float ties, where the harness's float32 arithmetic and this
core's float64 break an exact tie differently (see `docs/research/research-core.md`):

- D2 and D3 (its put leg), 2026-07-09: a drawdown of exactly the 60% threshold
  (5.55 -> 2.22) fires in float64 and not in float32: +$25.
- G2, 2026-09-23: the call and put 7630/7680/7730 flies have the same stressed debit
  ($22.55) and the same settlement payoff; the tie-break picks the call here and the
  put there. Stressed P&L is identical, midpoint differs by $15.

For those rows the core's own figures are pinned instead, and every other field must
still match.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

import pytest
import structlog

from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.entry import PROFILES, RunContext, SessionLoader, load_spx_config
from butterfly_guy.research.evaluate import EvalParams, evaluate
from butterfly_guy.research.simulate import run_variants
from butterfly_guy.research.variants import CATALOG, resolve

SWEEP = Path(__file__).resolve().parents[1] / "docs" / "research" / "spx-idea-sweep-2026-09-25"
PUBLISHED = {**json.loads((SWEEP / "results.json").read_text()),
             **json.loads((SWEEP / "results_round2.json").read_text())}
CODES = [c for c in CATALOG if c in PUBLISHED and c != "E0"]
EXCEPTIONS = {
    "D2": {"net": -7218.8, "mid": 1858.2, "h2": -4802.4, "ci": [-37844, -17302, 1091]},
    "D3": {"net": 3205.6, "mid": 20362.6, "h2": -11409.2, "ci": [-16420, -7678, 2392]},
    "G2": {"mid": 14479.8, "ci": [-35308, 116, 36846]},
}
EXCEPTION_P = {"D2": 0.0622, "D3": 0.103}


def test_every_published_variant_is_ported():
    published = {k for k in PUBLISHED if not k.startswith(("_", "diag"))}
    assert published <= set(CATALOG)


@pytest.fixture(scope="module")
def evaluation():
    try:
        ds = Dataset.open()
    except (FileNotFoundError, ValueError):
        pytest.skip("research cache not present (see docs/research/research-core.md)")
    saved = structlog.get_config()
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    try:
        result = run_variants(SessionLoader(ds, PROFILES["sweep_20260925"]),
                              resolve(["E0", *CODES]), RunContext(load_spx_config()),
                              start=dt.date(2026, 3, 13), end=dt.date(2026, 9, 24))
    finally:
        structlog.configure(**saved)
    return result, evaluate(result, "E0", EvalParams())


def _row(ev: dict, code: str) -> dict:
    arm = ev["arms"][code]
    s = arm["stressed"]
    vs = s.get("vs_baseline")
    return {"n": s["n"], "net": s.get("net", 0.0), "mid": arm["midpoint"].get("net", 0.0),
            "h1": s["h1_net"], "h2": s["h2_net"],
            "ci": [round(x) for x in vs["ci90"]] if vs else [0, 0, 0],
            "p": vs["p_better"] if vs else 0.0, "settled": arm["exits"].get("cash_settled", 0)}


def _published(code: str) -> dict:
    r = PUBLISHED[code]
    return {"n": r["n"], "net": r["net"], "mid": r["mid_net"], "h1": r["h1_net"],
            "h2": r["h2_net"], "ci": r["vs_base_ci90"], "p": r["p_better"],
            "settled": r["exits"].get("settled", 0)}


@pytest.mark.research_data
@pytest.mark.parametrize("code", ["E0", *CODES])
def test_variant_reproduces_the_idea_sweep(evaluation, code):
    result, ev = evaluation
    assert ev["sessions"] == 132
    got, want = _row(ev, code), {**_published(code), **EXCEPTIONS.get(code, {})}
    if code in EXCEPTION_P:
        want["p"] = EXCEPTION_P[code]
    for key in ("net", "mid", "h1", "h2"):
        assert got[key] == pytest.approx(want[key], abs=0.05), key
    for key in ("n", "ci", "settled"):
        assert got[key] == want[key], key
    assert got["p"] == pytest.approx(want["p"], abs=5e-4)


@pytest.mark.research_data
def test_fitted_thresholds_match_the_published_ones(evaluation):
    result, _ = evaluation
    k1 = result.runs["K1"].variant.entry
    assert round(k1.threshold, 3) == PUBLISHED["K1"]["threshold"]  # 0.05
    assert round(result.runs["R2"].variant.entry.threshold, 3) == 2.228  # round2.py printout
    assert k1.fit_n == 59


@pytest.mark.research_data
def test_learners_decide_only_from_earlier_sessions(evaluation):
    result, _ = evaluation
    for code in ("G1", "G2", "R3", "R4"):
        trades = result.runs[code].trades
        assert trades and all(t.history_n >= 20 and t.history_last < t.date for t in trades)
