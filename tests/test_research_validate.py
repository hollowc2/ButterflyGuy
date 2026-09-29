"""The fidelity-validation harness, exercised on the committed six-session fixture: a
dataset validated against itself must pass, and a perturbed copy must fail the right
checks. No vendor data exists yet."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

import numpy as np
import pytest
import structlog

from butterfly_guy.research import validate
from butterfly_guy.research.dataset import Dataset, chain_to_table, session_dir, write_table
from butterfly_guy.research.entry import RunContext, load_spx_config

FIXTURES = Path(__file__).parent / "fixtures" / "research"
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _quiet():
    saved = structlog.get_config()
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    yield
    structlog.configure(**saved)


@pytest.fixture(scope="module")
def mini() -> Dataset:
    return Dataset(FIXTURES / "mini_spx")


def _dates(ds: Dataset):
    return list(ds.sessions()["date"])


def _perturbed(tmp_path: Path, mini: Dataset) -> Dataset:
    """A copy of the fixture with every bid $0.10 and every ask $0.20 higher (marks kept;
    a uniform shift would cancel across a fly's +1/-2/+1 legs)."""
    root = tmp_path / "spx_0dte_perturbed"
    shutil.copytree(mini.root, root)
    ds = Dataset(root)
    m = ds.manifest
    m.dataset = root.name
    for d in _dates(ds):
        chain = ds.chain(d)
        for t in ("C", "P"):
            for f, shift in (("bid", 0.10), ("ask", 0.20)):
                chain.fields[f"{t}_{f}"] = chain.fields[f"{t}_{f}"] + shift
        rel = f"{session_dir(d)}/chain.parquet"
        m.files[rel] = write_table(chain_to_table(chain), root / rel)
    m.save(root / "manifest.json")
    return Dataset(root)


def _cboe(ds: Dataset):
    b = ds.daily_bars()
    b = b[b["underlying"] == "SPX"]
    import pandas as pd
    return pd.DataFrame({"date": b["date"], "close": b["close"]})


def test_criteria_are_verbatim_from_the_readiness_doc():
    doc = (REPO / validate.SOURCE_DOC).read_text()
    flat = re.sub(r"\s+", " ", doc)
    for text in validate.CRITERIA.values():
        assert text in flat


def test_a_dataset_validated_against_itself_passes_steps_1_2_and_4(tmp_path, mini):
    dates = _dates(mini)
    s1 = validate.step1(mini, mini, dates)
    assert s1["pass"] and s1["region_share_within"] == 1.0 and s1["best_offset_s"] == 0
    assert s1["presence"]["only_helios"] == s1["presence"]["only_vendor"] == 0
    assert s1["median_abs_diff"] == 0.0
    hybrid = validate.build_helios_clock_dataset(mini, mini, dates, tmp_path / "hyb")
    assert hybrid.verify() == []
    s2 = validate.step2(mini, hybrid, dates, RunContext(load_spx_config()))
    assert s2["pass"]
    for p in s2["profiles"].values():
        assert p["disagreements"] == [] and p["same_fly_share"] == 1.0
    s4 = validate.step4(mini, mini, dates, _cboe(mini))
    assert s4["pass"] and s4["spot"]["median_abs"] == 0.0


def test_perturbed_quotes_fail_step_1_and_every_step_2_difference_is_explained(tmp_path, mini):
    vendor = _perturbed(tmp_path, mini)
    dates = _dates(mini)
    s1 = validate.step1(mini, vendor, dates)
    assert not s1["pass"] and s1["region_share_within"] == 0.0
    assert s1["median_abs_diff"] == pytest.approx(0.10)  # lower median of 0.10s and 0.20s
    hybrid = validate.build_helios_clock_dataset(mini, vendor, dates, tmp_path / "hyb")
    s2 = validate.step2(mini, hybrid, dates, RunContext(load_spx_config()))
    frozen = s2["profiles"]["frozen_20260921"]
    assert frozen["disagreements"], "shifted bids and asks change executable P&L"
    assert all(r["explained_by"] is not None for r in frozen["disagreements"])
    assert frozen["checks"]["disagreements_explained"]


def test_a_close_that_differs_from_cboe_fails_step_4(mini):
    cboe = _cboe(mini)
    cboe.loc[cboe.index[-1], "close"] += 0.01
    s4 = validate.step4(mini, mini, _dates(mini), cboe)
    assert not s4["pass"] and len(s4["closes"]["mismatches"]) == 1


def test_step_3_band_check_and_report_format(tmp_path, mini, monkeypatch):
    dates = _dates(mini)
    s3 = validate.step3(mini, mini, dates, RunContext(load_spx_config()))
    for p in s3["profiles"].values():
        lo, hi = p["band"]
        assert p["pass"] == (lo is not None and lo <= p["vendor"]["stressed_total"] <= hi)
    results = {
        "meta": {"helios": {"dataset": "spx_0dte", "dataset_hash": "a" * 64},
                 "vendor": {"dataset": "spx_0dte_x", "dataset_hash": "b" * 64},
                 "range": ["2026-03-13", "2026-09-25"], "sessions": len(dates),
                 "criteria_source": validate.SOURCE_DOC},
        "steps": {"1": validate.step1(mini, mini, dates),
                  "2": {"profiles": {}, "pass": True}, "3": s3,
                  "4": validate.step4(mini, mini, dates, _cboe(mini))},
    }
    results["pass"] = all(s["pass"] for s in results["steps"].values())
    md = validate.markdown(results, {"run_id": "abc"})
    assert "| Step | Criterion | Measured | Threshold | Result |" in md
    for text in (validate.CRITERIA[1], validate.CRITERIA[3], validate.CRITERIA[4]):
        assert text in md
    assert np.isfinite(results["steps"]["1"]["region_share_within"])
