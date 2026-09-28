"""Cohort-session selection from a ledger read only through `git show`."""

from __future__ import annotations

import datetime as dt
import json
import subprocess

import pytest

from butterfly_guy.backtest.prospective_execution import canonical_hash, trade_key
from butterfly_guy.research.shadow import (
    LedgerError,
    compare_with_cohort,
    read_cohort_ledger,
)

COHORT = "spx-prospective-2026-09-22"
BASE = f"reports/prospective_execution/{COHORT}"


def _hashed(rec: dict) -> dict:
    return {**rec, "record_hash": canonical_hash(rec)}


def _trade(day: str) -> dict:
    decision = f"{day}T14:00:09.446491+00:00"
    strikes = (7765.0, 7815.0, 7865.0)
    tid = trade_key(COHORT, dt.date.fromisoformat(day), dt.datetime.fromisoformat(decision),
                    "CALL", strikes)
    return _hashed({"cohort_id": COHORT, "session_date": day, "trade_id": tid,
                    "decision_time": decision, "direction": "CALL", "lower_strike": strikes[0],
                    "center_strike": strikes[1], "upper_strike": strikes[2],
                    "exit_reason": "cash_settled", "accounting": {}})


def _ledger(extra_run: dict | None = None, tamper: bool = False):
    trades = [_trade("2026-09-22"), _trade("2026-09-24")]
    runs = [
        _hashed({"cohort_id": COHORT, "session_date": "2026-09-22", "status": "traded",
                 "trade_id": trades[0]["trade_id"]}),
        _hashed({"cohort_id": COHORT, "session_date": "2026-09-23", "status": "no_entry",
                 "trade_id": None}),
        _hashed({"cohort_id": COHORT, "session_date": "2026-09-24", "status": "traded",
                 "trade_id": trades[1]["trade_id"]}),
    ]
    if extra_run:
        runs.append(_hashed(extra_run))
    if tamper:
        runs[1]["status"] = "traded"
    return runs, trades


class FakeGit:
    def __init__(self, runs, trades):
        self.files = {f"c0ffee:{BASE}/daily_runs.jsonl": runs,
                      f"c0ffee:{BASE}/trades.jsonl": trades}
        self.calls: list[list[str]] = []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        verb, arg = cmd[3], cmd[-1]
        if verb == "rev-parse":
            out = "c0ffee\n"
        elif verb == "show" and arg in self.files:
            out = "".join(json.dumps(r) + "\n" for r in self.files[arg])
        else:
            return subprocess.CompletedProcess(cmd, 128, "", f"bad object {arg}")
        return subprocess.CompletedProcess(cmd, 0, out, "")


def test_sessions_are_every_recorded_session_traded_or_not():
    git = FakeGit(*_ledger())
    ledger = read_cohort_ledger(COHORT, run=git)
    assert ledger.commit == "c0ffee" and ledger.ref == f"origin/cohort/{COHORT}"
    assert ledger.sessions == [dt.date(2026, 9, 22), dt.date(2026, 9, 23), dt.date(2026, 9, 24)]
    # Only read-only plumbing, pinned to the resolved commit.
    assert [c[3] for c in git.calls] == ["rev-parse", "show", "show"]
    assert all(c[-1].startswith("c0ffee:") for c in git.calls[1:])


@pytest.mark.parametrize("case", ["tamper", "foreign", "duplicate"])
def test_a_bad_ledger_is_refused(case):
    if case == "tamper":
        runs, trades = _ledger(tamper=True)
    elif case == "foreign":
        runs, trades = _ledger({"cohort_id": "other", "session_date": "2026-09-25"})
    else:
        runs, trades = _ledger({"cohort_id": COHORT, "session_date": "2026-09-23",
                                "status": "no_entry", "trade_id": None})
    with pytest.raises(LedgerError):
        read_cohort_ledger(COHORT, run=FakeGit(runs, trades))


def test_a_trade_whose_identity_does_not_match_is_refused():
    runs, trades = _ledger()
    trades[0] = _hashed({**{k: v for k, v in trades[0].items() if k != "record_hash"},
                         "center_strike": 7820.0})
    with pytest.raises(LedgerError, match="does not match"):
        read_cohort_ledger(COHORT, run=FakeGit(runs, trades))


@pytest.mark.parametrize("cohort,ref", [(COHORT, "main"), (COHORT, "origin/main"),
                                        ("../x", None)])
def test_only_cohort_branches_are_read(cohort, ref):
    git = FakeGit(*_ledger())
    with pytest.raises(LedgerError):
        read_cohort_ledger(cohort, ref, run=git)
    assert git.calls == []


def test_e0_is_checked_against_the_cohort_trades():
    ledger = read_cohort_ledger(COHORT, run=FakeGit(*_ledger()))
    issues = compare_with_cohort([], ledger)
    assert issues == [{"date": "2026-09-22", "issue": "traded only in cohort"},
                      {"date": "2026-09-24", "issue": "traded only in cohort"}]
