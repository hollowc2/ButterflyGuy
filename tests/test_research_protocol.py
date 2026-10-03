"""The pre-registered holdout evaluation (`protocol.py`, `holdout` command). Synthetic data
only: nothing here registers on, unseals or reads a real dataset."""

from __future__ import annotations

import datetime as dt
import io
import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from butterfly_guy.research import cli, protocol
from butterfly_guy.research.dataset import Manifest
from butterfly_guy.research.evaluate import block_bootstrap_indices
from butterfly_guy.research.history import HistoryPlan, write_history
from butterfly_guy.research.holdout import HoldoutSealedError, verify_unseal
from butterfly_guy.research.protocol import ProtocolError
from butterfly_guy.research.registry import Registry
from butterfly_guy.research.variants import CATALOG
from butterfly_guy.research.volindex import DAILY_FILE, write_aux
from tests.research_synth import FakeSource, synthetic_day

DEV_DAY = dt.date(2024, 6, 27)
# Enough development sessions for the gate-1 calibration (Revision 4): 2024-05-28 -> DEV_DAY
DEV_DAYS = [d.date() for d in pd.bdate_range("2024-05-28", DEV_DAY)
            if d.date() != dt.date(2024, 6, 19)]
HOLD_DAY = dt.date(2024, 7, 2)
NAME = "spx_0dte_fake"
PRIOR = [{"date": dt.date(2024, 5, 24), "underlying": u, "open": 1.0, "high": 1.0,
          "low": 1.0, "close": c} for u, c in (("SPX", 5990.0), ("$VIX", 17.0))]
LEVELS = {str(k): 0.10 / k for k in range(1, 6)}
REACHED = {str(k): True for k in range(1, 6)}


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

DATES = ([dt.date(2024, 8, 1) + dt.timedelta(days=i) for i in range(20)]
         + [dt.date(2025, 6, 2) + dt.timedelta(days=i) for i in range(20)])


def _gates(arm, base=None, arm_d=None, base_d=None, k=1):
    base = np.zeros(len(arm)) if base is None else base
    return protocol.gates(np.asarray(arm, float), base, np.asarray(arm if arm_d is None
                                                                  else arm_d, float),
                          base if base_d is None else base_d, DATES, k)


def test_a_steady_gain_passes_every_gate():
    g = _gates(np.full(40, 100.0))
    assert g["lower_bound"] == 4000 and g["h1_diff"] == g["h2_diff"] == 2000
    assert (g["h1_sessions"], g["h2_sessions"]) == (20, 20)
    assert g["top3_removed_diff"] == 3700  # the tied top sessions: the last three
    assert g["gate1"] and g["gate2"] and g["gate3"] and g["gate4"] and g["gate6"]
    assert g["passed"]


def test_each_gate_can_fail_on_its_own():
    no_h2 = np.r_[np.full(20, 100.0), np.zeros(20)]
    assert not _gates(no_h2)["gate2"] and not _gates(no_h2)["passed"]
    top_only = np.r_[np.full(3, 1000.0), np.full(37, -10.0)]
    g = _gates(top_only)
    # The arm's top three and the baseline's (zeros: the last three) are both removed.
    assert g["diff"] > 0 and g["top3_removed_diff"] == -340 and not g["gate3"]
    g = _gates(np.full(40, 100.0), arm_d=np.full(40, -1.0))
    assert not g["gate4"] and not g["passed"]
    assert not _gates(np.full(40, -100.0))["gate1"]
    # Gate 6 (Revision 5): beating a losing baseline is not enough; the rule must make money.
    g = _gates(np.full(40, -50.0), base=np.full(40, -150.0), base_d=np.full(40, -150.0))
    assert g["gate1"] and g["gate2"] and g["gate3"] and g["gate4"]
    assert g["own_net"] == -2000 and not g["gate6"] and not g["passed"]


def test_gate_1_is_the_drafted_bootstrap_at_one_minus_alpha_over_k():
    diff = np.random.default_rng(3).normal(50, 400, 40)
    totals = diff[block_bootstrap_indices(40, 10_000, 10, 1)].sum(axis=1)
    g1, g4 = _gates(diff, k=1), _gates(diff, k=4)
    assert g1["level"] == pytest.approx(0.90) and g4["level"] == pytest.approx(0.975)
    assert g1["lower_bound"] == round(float(np.percentile(totals, 10)), 2)
    assert g4["lower_bound"] == round(float(np.percentile(totals, 2.5)), 2)
    assert g4["lower_bound"] < g1["lower_bound"]


def test_gate_1_uses_the_calibrated_tail_and_never_a_looser_one():
    diff = np.random.default_rng(3).normal(50, 400, 40)
    totals = diff[block_bootstrap_indices(40, 10_000, 10, 1)].sum(axis=1)
    g = _gates(diff, k=1) | {}
    cal = protocol.gates(diff, np.zeros(40), diff, np.zeros(40), DATES, 1, tail=0.025)
    assert cal["level"] == pytest.approx(0.975) and cal["drafted_level"] == pytest.approx(0.9)
    assert cal["lower_bound"] == round(float(np.percentile(totals, 2.5)), 2) < g["lower_bound"]
    with pytest.raises(ValueError, match="tail"):
        protocol.gates(diff, np.zeros(40), diff, np.zeros(40), DATES, 1, tail=0.2)


def test_calibration_picks_the_loosest_level_within_the_target_and_tightens_skewed_rules():
    rng = np.random.default_rng(5)
    # Skip-filter-like: mostly zero, some small gains, rare large losses; mean about zero.
    u = rng.random(585)
    sparse = np.where(u < 0.05, 400.0, np.where(u < 0.06, -2000.0, 0.0))
    dense = rng.normal(0, 300, 585)
    cs = protocol.calibrate_gate1(sparse, 358, sims=400, reps=1000)
    cd = protocol.calibrate_gate1(dense, 358, sims=400, reps=1000)
    assert cs["false_pass"]["0.1"] > 0.10 and cs["levels"]["1"] < 0.10  # tightened
    for c in (cs, cd):
        levels = [c["levels"][str(k)] for k in range(1, 6)]
        assert levels == sorted(levels, reverse=True)
        for k, lv in enumerate(levels, start=1):
            target = 0.10 / k
            assert lv <= target + 1e-12  # never looser than drafted
            assert not c["reached"][str(k)] or c["false_pass"][f"{lv:g}"] <= target
            looser = [g for g in protocol.CAL_GRID if lv < g <= target + 1e-12]
            assert all(c["false_pass"][f"{g:g}"] > target for g in looser)  # the loosest
        assert c["holdout_sessions"] == 358 and c["development_sessions"] == 585
    assert protocol.calibrate_gate1(sparse, 358, sims=400, reps=1000) == cs  # deterministic
    zeros = protocol.calibrate_gate1(np.zeros(40), 100, sims=50, reps=100)
    assert zeros["levels"] == LEVELS and set(zeros["false_pass"].values()) == {0.0}
    with pytest.raises(ProtocolError, match="too few"):
        protocol.calibrate_gate1(np.zeros(19), 358)


def test_gate_3_removes_the_top_sessions_of_either_arm_from_both():
    base = np.zeros(40)
    base[5] = 5000.0  # the baseline's best session is removed too
    arm = np.full(40, 10.0)
    arm[5] = 5000.0
    g = _gates(arm, base=base)
    assert DATES[5].isoformat() in g["top3_sessions_removed"]
    with pytest.raises(ValueError, match="same sessions"):
        protocol.gates(arm, base[:-1], arm, base, DATES, 1)


# ---------------------------------------------------------------------------
# Checks made before anything is replayed
# ---------------------------------------------------------------------------


def _reg(name, **kw):
    v = CATALOG[name]
    return {"event": "register", "variant": name, "definition_hash": v.definition_hash(),
            "git_sha": "a" * 40, "gate1": {"levels": LEVELS, "reached": REACHED}, **kw}


def test_only_evaluable_registered_catalog_definitions_pass():
    protocol.check_registered([_reg("HLV1"), _reg("HEV1")], CATALOG)
    with pytest.raises(ProtocolError, match="nothing is registered"):
        protocol.check_registered([], CATALOG)
    with pytest.raises(ProtocolError, match="baseline"):
        protocol.check_registered([_reg("E0")], CATALOG)
    with pytest.raises(ProtocolError, match="gate 5"):
        protocol.check_registered([_reg("HSN1")], CATALOG)
    with pytest.raises(ProtocolError, match="not the registered one"):
        protocol.check_registered([{**_reg("HLV1"), "definition_hash": "f" * 64}], CATALOG)
    with pytest.raises(ProtocolError, match="without its fitted values"):
        protocol.check_registered([_reg("HTS1")], CATALOG)
    protocol.check_registered([_reg("HTS1", fitted={"fit_n": 3, "threshold": 0.9})], CATALOG)
    with pytest.raises(ProtocolError, match="gate-1 calibration for k = 1"):
        protocol.check_registered([{**_reg("HLV1"), "gate1": {}}], CATALOG)
    # A level that could not be calibrated to 0.10/k refuses rather than over-passing.
    unreached = {"levels": LEVELS | {"2": 0.001}, "reached": REACHED | {"2": False},
                 "false_pass": {"0.001": 0.061}}
    protocol.check_registered([_reg("HLV1", gate1=unreached)], CATALOG)  # k = 1: fine
    with pytest.raises(ProtocolError, match="cannot be calibrated to 0.10/2.*0.061"):
        protocol.check_registered([_reg("HLV1", gate1=unreached), _reg("HEV1")], CATALOG)


def test_registrations_are_those_up_to_the_unseal_record():
    recs = [_reg("HLV1"), {"event": "evaluate", "variant": "E0"}, _reg("HEV1")]
    assert [r["variant"] for r in protocol.registrations(recs, 1)] == ["HLV1"]
    assert [r["variant"] for r in protocol.registrations(recs, 2)] == ["HLV1", "HEV1"]
    with pytest.raises(ProtocolError, match="more than once"):
        protocol.registrations([_reg("HLV1"), _reg("HLV1")], 1)


def test_the_refit_must_equal_the_registered_value():
    reg = _reg("HTS1", fitted={"fit_n": 3, "threshold": 0.9}, fit_profile="vendor_1m")
    protocol.check_fitted([reg], {"HTS1": {"fit_n": 3, "threshold": 0.9}})
    with pytest.raises(ProtocolError, match="re-fitted"):
        protocol.check_fitted([reg], {"HTS1": {"fit_n": 3, "threshold": 0.91}})
    with pytest.raises(ProtocolError, match="fitted under 'live'"):
        protocol.check_fitted([{**reg, "fit_profile": "live"}],
                              {"HTS1": {"fit_n": 3, "threshold": 0.9}})


def test_a_second_evaluation_is_only_an_exact_reproduction():
    first = [{"event": "evaluate", "scope": "holdout", "run_id": "r1", "variant": n,
              "unseal_seq": 1, "dataset_hash": "d" * 64, "git_sha": "a" * 40}
             for n in ("E0", "HLV1")]
    kw = dict(unseal_seq=1, dataset_hash="d" * 64, variants=["E0", "HLV1"],
              code_unchanged_since=lambda sha: True)
    assert protocol.check_rerun([], **kw) is None
    assert protocol.check_rerun(first, **kw)["run_id"] == "r1"
    for change, match in [({"unseal_seq": 2}, "unseal record"),
                          ({"dataset_hash": "e" * 64}, "dataset"),
                          ({"variants": ["E0", "HLV1", "HEV1"]}, "set of arms"),
                          ({"code_unchanged_since": lambda sha: False}, "code at")]:
        with pytest.raises(ProtocolError, match=match):
            protocol.check_rerun(first, **{**kw, **change})


# ---------------------------------------------------------------------------
# The command, end to end on a synthetic vendor dataset
# ---------------------------------------------------------------------------


@pytest.fixture
def world(tmp_path, monkeypatch):
    days = {d: synthetic_day(d) for d in [*DEV_DAYS, HOLD_DAY]}
    src = FakeSource(days, extra_bars=PRIOR)
    write_history(src, HistoryPlan(DEV_DAYS[0], DEV_DAY, NAME, log=io.StringIO(),
                                   require_quality=False), tmp_path)
    monkeypatch.setattr(cli, "_git", lambda: ("a" * 40, False))
    monkeypatch.setattr(cli, "_code_unchanged_since", lambda sha: True)
    monkeypatch.setattr(protocol, "CAL_SIMS", 40)  # the calibration's size, not its logic
    monkeypatch.setattr(protocol, "CAL_REPS", 100)
    return SimpleNamespace(src=src, root=tmp_path, registry=tmp_path / "registry",
                           out=tmp_path / "out")


def _cli(w, *args) -> int:
    return cli.main(["--dataset", NAME, "--cache", str(w.root), "--registry", str(w.registry),
                     *args])


def _records(w) -> list[dict]:
    return Registry.for_dataset(w.registry, NAME).records()


def _pull_holdout(w, seq: int) -> None:
    unseal = verify_unseal(Registry.for_dataset(w.registry, NAME),
                           Manifest.load(w.root / NAME / "manifest.json"), seq)
    write_history(w.src, HistoryPlan(HOLD_DAY, HOLD_DAY, NAME, unseal=unseal,
                                     log=io.StringIO(), require_quality=False), w.root)


def _holdout(w, seq: int) -> int:
    return _cli(w, "holdout", "--unseal-holdout", str(seq), "--out", str(w.out))


def _no_replay(monkeypatch):
    def refuse(*a, **kw):
        raise AssertionError("a holdout session was replayed before the checks passed")
    monkeypatch.setattr(cli, "run_variants", refuse)


def test_evaluates_the_registered_set_once_and_records_every_look(world, monkeypatch):
    w = world
    assert _cli(w, "register", "--variants", "HLV1,HEV1") == 0
    for rec in _records(w):
        assert rec["gate1"]["holdout_sessions"] == 358
        assert rec["gate1"]["development_sessions"] == len(DEV_DAYS)
        assert set(rec["gate1"]["levels"]) == {"1", "2", "3", "4", "5"}
    with pytest.raises(ProtocolError, match="no holdout sessions"):
        _holdout(w, 1)
    _pull_holdout(w, 1)
    assert _holdout(w, 1) == 0

    runs = [r for r in _records(w) if r.get("scope") == "holdout"]
    assert [r["variant"] for r in runs] == ["E0", "HLV1", "HEV1"]
    assert {r["variant"]: r["stage"] for r in runs} == {"E0": "post", "HLV1": "pre",
                                                        "HEV1": "pre"}
    assert all(r["k"] == 2 and r["unseal_seq"] == 1 and r["reproduction"] is None
               for r in runs)
    assert runs[0]["gates"] is None and set(runs[1]["gates"]) >= {"gate1", "passed"}
    assert runs[1]["gates"]["level"] == pytest.approx(1 - _records(w)[0]["gate1"]["levels"]["2"])
    (results,) = w.out.glob(f"{NAME}/holdout/*/results.json")
    res = json.loads(results.read_text())
    assert res["meta"]["protocol"] == protocol.describe()
    assert res["meta"]["accounting"]["stressed_exit_floor"] == 0.0
    assert res["meta"]["eval"]["bootstrap_block"] == 10
    assert res["meta"]["eval"]["bootstrap_reps"] == 10_000
    assert res["meta"]["eval"]["split"] == "2025-04-30"
    assert res["evaluation"]["first"] == res["evaluation"]["last"] == HOLD_DAY.isoformat()
    report = (results.parent / "report.md").read_text()
    assert "Pre-registered holdout verdict" in report and "floored at $0.00" in report

    # An identical second look is a reproduction, recorded with the first run's id.
    assert _holdout(w, 1) == 0
    again = [r for r in _records(w) if r.get("scope") == "holdout"][3:]
    assert {r["reproduction"]["of"] for r in again} == {runs[0]["run_id"]}
    assert all(r["reproduction"]["same_results"] for r in again)

    # After a code change it is a re-run after edits, refused before any replay.
    monkeypatch.setattr(cli, "_code_unchanged_since", lambda sha: sha != "a" * 40)
    _no_replay(monkeypatch)
    n = len(_records(w))
    with pytest.raises(ProtocolError, match="changed since the registration commit"):
        _holdout(w, 1)
    assert len(_records(w)) == n


def test_refusals_happen_before_any_holdout_session_is_replayed(world, monkeypatch):
    w = world
    _cli(w, "register", "--variants", "HLV1")
    _pull_holdout(w, 0)
    _no_replay(monkeypatch)
    monkeypatch.setattr(cli, "_git", lambda: ("a" * 40, True))
    with pytest.raises(ProtocolError, match="uncommitted"):
        _holdout(w, 0)
    monkeypatch.setattr(cli, "_git", lambda: ("a" * 40, False))
    monkeypatch.setattr(cli, "_code_unchanged_since", lambda sha: False)
    with pytest.raises(ProtocolError, match="changed since the registration commit"):
        _holdout(w, 0)
    with pytest.raises(HoldoutSealedError, match="not a register event"):
        _holdout(w, 5)
    assert not [r for r in _records(w) if r["event"] == "evaluate"]


def test_h_sn1_is_refused_until_gate_5_has_a_statistic(world, monkeypatch):
    w = world
    _cli(w, "register", "--variants", "HSN1")
    _pull_holdout(w, 0)
    _no_replay(monkeypatch)
    with pytest.raises(ProtocolError, match="gate 5"):
        _holdout(w, 0)


def _vix1d(w, ratio: float) -> None:
    table = pd.DataFrame({"date": pd.to_datetime(["2024-06-26", "2024-06-26"]),
                          "index": ["VIX1D", "VIX"], "open": [np.nan, np.nan],
                          "high": [np.nan, np.nan], "low": [np.nan, np.nan],
                          "close": [17.0 * ratio, 17.0]})
    write_aux(w.root / NAME, DAILY_FILE, table, {"kind": "test"}, ["index", "date"])


def test_a_fitted_rule_is_registered_with_its_value_and_checked_at_the_holdout(world,
                                                                              monkeypatch):
    w = world
    # Without the feature the fit fails, and nothing is registered.
    with pytest.raises(ValueError, match="no vix1d_vix observations"):
        _cli(w, "register", "--variants", "HLV1,HTS1")
    assert _records(w) == []

    _vix1d(w, 0.95)
    assert _cli(w, "register", "--variants", "HTS1") == 0
    (rec,) = _records(w)
    assert rec["fit_profile"] == "vendor_1m"
    assert rec["fitted"] == {"fit_n": 1, "threshold": pytest.approx(0.95)}
    _pull_holdout(w, 0)
    assert _holdout(w, 0) == 0

    # A different development feature re-fits to a different value: refused.
    _vix1d(w, 0.90)
    _no_replay(monkeypatch)
    with pytest.raises(ProtocolError, match="re-fitted"):
        _holdout(w, 0)


@pytest.mark.usefixtures("sealed_holdout")
def test_run_still_cannot_open_the_holdout(world):
    w = world
    _cli(w, "register", "--variants", "HLV1")
    _pull_holdout(w, 0)
    with pytest.raises(SystemExit):
        _cli(w, "run", "--variants", "E0", "--unseal-holdout", "0")
    with pytest.raises(HoldoutSealedError):
        _cli(w, "run", "--variants", "E0", "--profile", "vendor_1m", "--no-registry",
             "--no-tieset", "--out", str(w.out))
