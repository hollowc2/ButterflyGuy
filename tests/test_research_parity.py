"""Parity of the research core with the frozen 2026-03-13 -> 2026-09-18 SPX replay.

`frozen_ledger_b83c2a18.json` is the per-trade output of `run_backtest_db.py` at commit
b83c2a18 (the frozen execution-accounting replay) with `--execution-accounting-report`.
The committed mini dataset (six sessions, trimmed by `build_fixture.py`) always runs; the
full 118-trade comparison runs when the local research cache is present.

Tolerance: none beyond float noise. Fly, entry time and exit reason must match exactly
and each model's P&L to within half a cent per trade.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

import pytest
import structlog

from butterfly_guy.research.cli import compare_to_ledger
from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.entry import PROFILES, RunContext, SessionLoader, load_spx_config
from butterfly_guy.research.report import trade_record
from butterfly_guy.research.simulate import run_variants
from butterfly_guy.research.variants import resolve

FIXTURES = Path(__file__).parent / "fixtures" / "research"
LEDGER = json.loads((FIXTURES / "frozen_ledger_b83c2a18.json").read_text())
EXPECTED = json.loads((FIXTURES / "mini_expected.json").read_text())
TOLERANCE = 0.005  # dollars per trade and model


@pytest.fixture(autouse=True)
def _quiet():
    saved = structlog.get_config()
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    yield
    structlog.configure(**saved)


def _run(ds: Dataset, profile: str, start: dt.date, end: dt.date):
    loader = SessionLoader(ds, PROFILES[profile])
    return run_variants(loader, resolve(["E0"]), RunContext(load_spx_config()),
                        start=start, end=end)


def test_mini_fixture_matches_the_frozen_replay_trade_by_trade():
    ds = Dataset(FIXTURES / "mini_spx")
    assert ds.verify() == []
    dates = [dt.date.fromisoformat(d) for d in EXPECTED["dates"]]
    result = _run(ds, "frozen_20260921", dates[0], dates[-1])
    ledger = [r for r in EXPECTED["frozen_ledger"].values() if r is not None]
    report = compare_to_ledger(result.runs["E0"].trades, ledger, TOLERANCE)
    assert report["mismatches"] == []
    traded = {t.date.isoformat() for t in result.runs["E0"].trades}
    no_entry = [d for d, r in EXPECTED["frozen_ledger"].items() if r is None]
    assert no_entry and not traded & set(no_entry)
    assert {r["exit_reason"] for r in ledger} >= {"cash_settled", "drawdown_morning",
                                                  "drawdown_late_morning", "drawdown_afternoon"}


def test_mini_fixture_reproduces_the_idea_sweep_harness():
    ds = Dataset(FIXTURES / "mini_spx")
    dates = [dt.date.fromisoformat(d) for d in EXPECTED["dates"]]
    result = _run(ds, "sweep_20260925", dates[0], dates[-1])
    got = {t.date.isoformat(): trade_record(t) for t in result.runs["E0"].trades}
    assert got == EXPECTED["sweep_e0"]


def _cache() -> Dataset | None:
    try:
        return Dataset.open()
    except (FileNotFoundError, ValueError):
        return None


@pytest.mark.research_data
def test_full_frozen_replay_parity():
    ds = _cache()
    if ds is None:
        pytest.skip("research cache not present (see docs/research/research-core.md)")
    result = _run(ds, "frozen_20260921", dt.date(2026, 3, 13), dt.date(2026, 9, 18))
    report = compare_to_ledger(result.runs["E0"].trades, LEDGER, TOLERANCE)
    assert report["mismatches"] == []
    assert report["trades"] == 118
    assert report["exits"] == {"cash_settled": 22, "intraday": 96}
    assert report["totals"]["stressed"]["research_core"] == 9890.60
    assert report["totals"]["midpoint"]["research_core"] == 17691.60
    assert report["totals"]["marketable"]["research_core"] == 14170.60
    assert {d.isoformat(): r for d, r in result.skipped.items()} == {
        "2026-03-13": "no_prev_close", "2026-03-16": "no_vix"}
