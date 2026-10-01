"""Exploratory shadow evaluation on the sessions an open prospective cohort has recorded.

The cohort ledger is read only through `git show <ref>:<path>` from the cohort branch;
no file in the cohort worktree is opened, and nothing is written outside the research
reports. Every ledger record's hash and trade identity are checked with the cohort
runner's own `canonical_hash` and `trade_key`.

Shadow results are paired against E0 on exactly the cohort's recorded sessions. The
sample is a handful of sessions, so they are labeled exploratory, carry no confidence
interval, and must never feed back into the cohort (its rules are frozen).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from butterfly_guy.backtest.prospective_execution import canonical_hash, trade_key
from butterfly_guy.research.entry import REPO_ROOT
from butterfly_guy.research.report import trade_record
from butterfly_guy.research.simulate import Trade

COHORT_PROFILE = "frozen_20260921"  # the cohort runs the frozen replay (snapshot gap inputs)
BANNER = ("EXPLORATORY SHADOW. {n} session(s): far too few to support any conclusion. "
          "Nothing here feeds back into the cohort, whose rules stay frozen.")
_COHORT_ID = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
MODEL_KEYS = (("midpoint", "corrected_midpoint"), ("marketable", "marketable"),
              ("stressed", "stressed_marketable"))

Runner = Callable[..., subprocess.CompletedProcess]


class LedgerError(RuntimeError):
    pass


@dataclass
class CohortLedger:
    cohort_id: str
    ref: str
    commit: str
    runs: list[dict]
    trades: list[dict]

    @property
    def sessions(self) -> list[dt.date]:
        """Every session the cohort has recorded, traded or not. Deferred sessions are
        never recorded, so they are not included."""
        return sorted(dt.date.fromisoformat(r["session_date"]) for r in self.runs)


def default_ref(cohort_id: str) -> str:
    return f"origin/cohort/{cohort_id}"


def _git(args: list[str], run: Runner) -> str:
    proc = run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True,
               check=False)
    if proc.returncode != 0:
        raise LedgerError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


def _jsonl(text: str, label: str) -> list[dict]:
    try:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        raise LedgerError(f"{label}: malformed record ({exc})") from exc


def check_records(cohort_id: str, runs: list[dict], trades: list[dict]) -> None:
    """Raise on any foreign, duplicated, tampered or unlinked ledger record."""
    for label, records, key in (("daily_runs.jsonl", runs, "session_date"),
                                ("trades.jsonl", trades, "trade_id")):
        seen = set()
        for rec in records:
            ident = rec.get(key)
            if ident in seen:
                raise LedgerError(f"{label}: duplicate {key}={ident}")
            seen.add(ident)
            if rec.get("cohort_id") != cohort_id:
                raise LedgerError(f"{label}: foreign cohort_id for {key}={ident}")
            body = {k: v for k, v in rec.items() if k != "record_hash"}
            if rec.get("record_hash") != canonical_hash(body):
                raise LedgerError(f"{label}: record hash mismatch for {key}={ident}")
    by_date = {r["session_date"]: r for r in runs}
    for t in trades:
        run = by_date.get(t["session_date"])
        if run is None or run.get("trade_id") != t["trade_id"]:
            raise LedgerError(f"trades.jsonl: {t['trade_id']} has no matching daily run")
        expected = trade_key(cohort_id, dt.date.fromisoformat(t["session_date"]),
                             dt.datetime.fromisoformat(t["decision_time"]), t["direction"],
                             (t["lower_strike"], t["center_strike"], t["upper_strike"]))
        if expected != t["trade_id"]:
            raise LedgerError(f"trades.jsonl: trade id {t['trade_id']} does not match its "
                              "contents")


def read_cohort_ledger(cohort_id: str, ref: str | None = None,
                       run: Runner = subprocess.run) -> CohortLedger:
    """Read a cohort ledger from its branch with `git show` (read-only; no fetch)."""
    if not _COHORT_ID.match(cohort_id):
        raise LedgerError(f"unexpected cohort id {cohort_id!r}")
    ref = ref or default_ref(cohort_id)
    if not ref.startswith(("origin/cohort/", "cohort/")):
        raise LedgerError(f"{ref!r} is not a cohort branch")
    commit = _git(["rev-parse", "--verify", f"{ref}^{{commit}}"], run).strip()
    base = f"reports/prospective_execution/{cohort_id}"
    runs = _jsonl(_git(["show", f"{commit}:{base}/daily_runs.jsonl"], run), "daily_runs")
    trades = _jsonl(_git(["show", f"{commit}:{base}/trades.jsonl"], run), "trades")
    check_records(cohort_id, runs, trades)
    return CohortLedger(cohort_id, ref, commit, runs, trades)


def compare_with_cohort(e0: list[Trade], ledger: CohortLedger, tolerance: float = 0.005
                        ) -> list[dict]:
    """Differences between the core's E0 and the cohort's recorded trades, per session."""
    ours = {t.date.isoformat(): trade_record(t) for t in e0}
    theirs = {t["session_date"]: t for t in ledger.trades}
    out = []
    for d in sorted({r["session_date"] for r in ledger.runs}):
        a, b = ours.get(d), theirs.get(d)
        if a is None and b is None:
            continue
        if a is None or b is None:
            out.append({"date": d, "issue": "traded only in " + ("cohort" if a is None
                                                                 else "research core")})
            continue
        issues = []
        if (a["direction"], a["lower"], a["center"], a["upper"]) != (
                b["direction"], b["lower_strike"], b["center_strike"], b["upper_strike"]):
            issues.append("fly differs")
        if dt.datetime.fromisoformat(a["entry_time"]) != dt.datetime.fromisoformat(
                b["decision_time"]):
            issues.append(f"entry {a['entry_time']} vs {b['decision_time']}")
        if a["exit_reason"] != b["exit_reason"]:
            issues.append(f"exit {a['exit_reason']} vs {b['exit_reason']}")
        for ours_key, their_key in MODEL_KEYS:
            pa, pb = a[ours_key]["pnl"], b["accounting"][their_key]["net_pnl"]
            if pa is None or pb is None or abs(pa - pb) > tolerance:
                issues.append(f"{ours_key} {pa} vs {pb}")
        if issues:
            out.append({"date": d, "issue": "; ".join(issues)})
    return out


def session_rows(result, names: list[str], dates: list[dt.date], baseline: str) -> list[dict]:
    """Per-session stressed P&L of each arm and its difference from the baseline."""
    rows = []
    for d in dates:
        row = {"date": d.isoformat()}
        for name in names:
            trades = [t for t in result.runs[name].trades if t.date == d]
            pnl = [t.pnl("stressed") for t in trades]
            row[name] = round(sum(p for p in pnl if p is not None), 2)
            row[f"{name}_delayed"] = round(sum(t.pnl("stressed_delayed") or 0.0
                                               for t in trades), 2)
            row[f"{name}_trades"] = [
                f"{t.fly.direction} {t.fly.lower:g}/{t.fly.center:g}/{t.fly.upper:g} "
                f"{t.exit_reason}" for t in trades]
        for name in names:
            if name != baseline:
                row[f"{name}_vs_{baseline}"] = round(row[name] - row[baseline], 2)
        rows.append(row)
    return rows


def markdown(ledger: CohortLedger, results: dict, provenance: dict) -> str:
    sh = results["shadow"]
    names = list(results["evaluation"]["arms"])
    base = results["meta"]["baseline"]
    lines = [
        f"# Shadow on cohort {ledger.cohort_id} ({provenance['run_id']})",
        "",
        f"**{BANNER.format(n=len(sh['sessions']))}**",
        "",
        f"- Ledger: `{ledger.ref}` @ `{ledger.commit[:12]}`, read with `git show` "
        f"(record hashes verified); sessions {', '.join(sh['sessions'])}",
        f"- Profile `{results['meta']['profile']['name']}`; dataset "
        f"`{results['meta']['dataset_hash'][:16]}…`; git `{provenance['git_sha'][:12]}`"
        f"{' (dirty)' if provenance['git_dirty'] else ''}",
        "- E0 versus the cohort's recorded trades: "
        + ("identical (fly, entry time, exit reason, P&L in all three models)"
           if not sh["e0_vs_cohort"] else f"{len(sh['e0_vs_cohort'])} difference(s), below"),
        "",
        "Stressed marketable P&L per session (dollars, one-lot); `Delayed` is the exit-latency "
        "stress. Differences are paired against the baseline on the same session.",
        "",
        "| Session | " + " | ".join(names) + " | "
        + " | ".join(f"{n} − {base}" for n in names if n != base) + " | "
        + " | ".join(f"{n} delayed" for n in names) + " |",
        "|---|" + "---:|" * (2 * len(names) + len(names) - 1),
    ]
    for row in sh["rows"]:
        lines.append(
            f"| {row['date']} | " + " | ".join(_m(row[n]) for n in names) + " | "
            + " | ".join(_m(row[f'{n}_vs_{base}']) for n in names if n != base) + " | "
            + " | ".join(_m(row[f'{n}_delayed']) for n in names) + " |")
    totals = {n: results["evaluation"]["arms"][n]["stressed"] for n in names}
    lines.append("| **Total** | " + " | ".join(_m(totals[n].get("net", 0)) for n in names)
                 + " | " + " | ".join(_m(totals[n]["vs_baseline"]["net_diff"])
                                      for n in names if n != base)
                 + " | " + " | ".join(
                     _m(results["evaluation"]["arms"][n]["stressed_delayed"].get("net", 0))
                     for n in names) + " |")
    lines += ["", "## Trades", ""]
    for row in sh["rows"]:
        for n in names:
            lines.append(f"- {row['date']} {n}: {', '.join(row[f'{n}_trades']) or 'no trade'}")
    if sh["e0_vs_cohort"]:
        lines += ["", "## E0 versus the cohort ledger", ""]
        lines += [f"- {m['date']}: {m['issue']}" for m in sh["e0_vs_cohort"]]
    lines += ["", "## Output hashes", ""]
    lines += [f"- `{f}`: `{h}`" for f, h in provenance["hashes"].items()]
    return "\n".join(lines) + "\n"


def _m(x: float | None) -> str:
    return "—" if x is None else f"{x:,.0f}"
