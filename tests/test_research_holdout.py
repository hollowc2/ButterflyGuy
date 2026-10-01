"""The sealed holdout (2024-07-01 -> 2026-03-12): every request, write and load touching
it raises unless a registry-verified unseal is passed. Synthetic data only."""

from __future__ import annotations

import datetime as dt
import io
import json

import pytest

from butterfly_guy.research.dataset import Dataset, Manifest
from butterfly_guy.research.entry import PROFILES, SessionLoader
from butterfly_guy.research.history import GuardedSource, HistoryPlan, coverage, write_history
from butterfly_guy.research.holdout import (
    DEVELOPMENT,
    HOLDOUT,
    HoldoutSealedError,
    Unseal,
    guard,
    verify_unseal,
)
from butterfly_guy.research.registry import Registry
from tests.research_synth import FakeSource, synthetic_day

DEV_DAY = dt.date(2024, 6, 27)
HOLD_DAY = dt.date(2024, 7, 2)
NAME = "spx_0dte_fake"
PRIOR = [{"date": dt.date(2024, 6, 26), "underlying": u, "open": 1.0, "high": 1.0,
          "low": 1.0, "close": c} for u, c in (("SPX", 5990.0), ("$VIX", 17.0))]


def test_the_split_is_the_drafted_one():
    assert DEVELOPMENT == (dt.date(2022, 1, 3), dt.date(2024, 6, 28))
    assert HOLDOUT == (dt.date(2024, 7, 1), dt.date(2026, 3, 12))


@pytest.mark.parametrize("start,end", [
    ("2024-07-01", "2024-07-01"), ("2026-03-12", "2026-03-12"),
    ("2024-06-28", "2024-07-01"),  # straddles the start
    ("2026-03-12", "2026-03-13"),  # straddles the end
    ("2022-01-03", "2026-09-25"),  # spans it
    ("2025-01-02", "2025-01-31"),  # inside
])
def test_any_range_touching_the_holdout_raises(start, end):
    with pytest.raises(HoldoutSealedError, match="sealed holdout"):
        guard(dt.date.fromisoformat(start), dt.date.fromisoformat(end), what="test")


@pytest.mark.parametrize("start,end", [("2022-01-03", "2024-06-28"),
                                       ("2026-03-13", "2026-09-25")])
def test_ranges_outside_the_holdout_pass(start, end):
    guard(dt.date.fromisoformat(start), dt.date.fromisoformat(end), what="test")


def test_an_unseal_cannot_be_made_by_hand():
    with pytest.raises(TypeError, match="verify_unseal"):
        Unseal(NAME, 0, ("HLV1",))


def test_guarded_source_refuses_before_the_vendor_is_called():
    src = FakeSource({HOLD_DAY: synthetic_day(HOLD_DAY)}, cost=1.0)
    g = GuardedSource(src, NAME, None)
    for call in (lambda: g.quotes(HOLD_DAY, (5600.0, 6400.0)),
                 lambda: g.index_bars(HOLD_DAY, "SPX"),
                 lambda: g.sessions(dt.date(2024, 6, 1), dt.date(2024, 7, 31)),
                 lambda: g.daily_bars(dt.date(2026, 3, 1), dt.date(2026, 3, 20)),
                 lambda: g.cost_estimate(DEV_DAY, HOLD_DAY)):  # a cost preview too
        with pytest.raises(HoldoutSealedError):
            call()
    assert src.calls == [] and g.requests == []


def test_a_pull_touching_the_holdout_raises_before_any_request(tmp_path):
    src = FakeSource({DEV_DAY: synthetic_day(DEV_DAY), HOLD_DAY: synthetic_day(HOLD_DAY)})
    with pytest.raises(HoldoutSealedError):
        write_history(src, HistoryPlan(DEV_DAY, HOLD_DAY, NAME, log=io.StringIO()), tmp_path)
    assert src.calls == [] and not (tmp_path / NAME).exists()


# ---------------------------------------------------------------------------
# Unsealing through the registry
# ---------------------------------------------------------------------------


def _dev_dataset(tmp_path) -> tuple[FakeSource, Manifest]:
    src = FakeSource({DEV_DAY: synthetic_day(DEV_DAY), HOLD_DAY: synthetic_day(HOLD_DAY)},
                     extra_bars=PRIOR)
    # The quality lock has its own tests (test_research_history.py); these test the unseal.
    m = write_history(src, HistoryPlan(DEV_DAY, DEV_DAY, NAME, log=io.StringIO(),
                                       require_quality=False), tmp_path)
    return src, m


def _register(reg: Registry, dataset_hash: str | None, dirty: bool = False,
              variant: str = "HLV1") -> dict:
    return reg.append("register", variant=variant, definition={"name": variant},
                      definition_hash=f"h-{variant}", note="", git_sha="abc",
                      git_dirty=dirty, dataset_hash=dataset_hash)


def test_verify_unseal_needs_a_clean_registration_on_development_data(tmp_path):
    _, m = _dev_dataset(tmp_path)
    reg = Registry.for_dataset(tmp_path / "registry", NAME)
    with pytest.raises(HoldoutSealedError, match="not a register event"):
        verify_unseal(reg, m, 0)  # nothing registered
    reg.append("evaluate", variant="E0", definition={}, definition_hash="h-E0")
    with pytest.raises(HoldoutSealedError, match="not a register event"):
        verify_unseal(reg, m, 0)
    _register(reg, m.dataset_hash, dirty=True)
    with pytest.raises(HoldoutSealedError, match="clean, committed tree"):
        verify_unseal(reg, m, 1)
    reg2 = Registry.for_dataset(tmp_path / "registry2", NAME)
    _register(reg2, "f" * 64)
    with pytest.raises(HoldoutSealedError, match="development-only"):
        verify_unseal(reg2, m, 0)
    reg3 = Registry.for_dataset(tmp_path / "registry3", NAME)
    _register(reg3, m.dataset_hash)
    rec = _register(reg3, m.dataset_hash, variant="HEV1")
    unseal = verify_unseal(reg3, m, rec["seq"])
    assert unseal.dataset == NAME and unseal.registered == ("HLV1", "HEV1")
    with pytest.raises(HoldoutSealedError, match="not the registry"):
        verify_unseal(Registry.for_dataset(tmp_path / "registry3", "spx_0dte_other"), m, 0)


def test_a_tampered_registry_never_unseals(tmp_path):
    _, m = _dev_dataset(tmp_path)
    reg = Registry.for_dataset(tmp_path / "registry", NAME)
    _register(reg, m.dataset_hash)
    rec = json.loads(reg.path.read_text())
    rec["git_dirty"] = False
    rec["note"] = "edited"
    reg.path.write_text(json.dumps(rec) + "\n")
    with pytest.raises(HoldoutSealedError, match="chain is broken"):
        verify_unseal(reg, m, 0)


def test_after_a_verified_unseal_the_holdout_opens_for_that_dataset_only(tmp_path):
    src, m = _dev_dataset(tmp_path)
    reg = Registry.for_dataset(tmp_path / "registry", NAME)
    unseal = verify_unseal(reg, m, _register(reg, m.dataset_hash)["seq"])
    guard(HOLD_DAY, HOLD_DAY, what="test", dataset=NAME, unseal=unseal)
    with pytest.raises(HoldoutSealedError, match="unseal is for"):
        guard(HOLD_DAY, HOLD_DAY, what="test", dataset="spx_0dte_other", unseal=unseal)

    m2 = write_history(src, HistoryPlan(HOLD_DAY, HOLD_DAY, NAME, unseal=unseal,
                                        log=io.StringIO(), require_quality=False), tmp_path)
    assert m2.history[-1]["holdout_sessions"] == 1
    ds = Dataset.open(NAME, tmp_path)

    sealed = SessionLoader(ds, PROFILES["vendor_1m"])
    assert sealed.dates(DEV_DAY, DEV_DAY) == [DEV_DAY]
    with pytest.raises(HoldoutSealedError):
        sealed.dates()
    with pytest.raises(HoldoutSealedError):
        sealed.load(HOLD_DAY)
    with pytest.raises(HoldoutSealedError):
        coverage(ds)
    opened = SessionLoader(ds, PROFILES["vendor_1m"], unseal)
    assert opened.dates() == [DEV_DAY, HOLD_DAY]
    assert opened.load(HOLD_DAY) is not None
    assert coverage(ds, unseal=unseal)["summary"]["sessions"] == 2

    # A registration made after holdout data landed can never unseal anything.
    _register(reg, m2.dataset_hash, variant="HTS1")
    with pytest.raises(HoldoutSealedError, match="development-only"):
        verify_unseal(reg, Manifest.load(tmp_path / NAME / "manifest.json"), 1)
