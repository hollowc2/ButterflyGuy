"""Development-window studies behind the 2026-09-29 registration package (§3, §4, §6.2, §6.3).

Reads per-session stressed P&L from a committed run's `trades.jsonl` (zeros on no-trade
days, sessions from the dataset's development window) and applies protocol.py's own
`calibrate_gate1` and `gates`. Nothing is replayed, and no holdout session is read: the
session list is cut to `holdout.DEVELOPMENT` before anything else.

    uv run python tools/research_studies/dev_studies.py check
    uv run python tools/research_studies/dev_studies.py calibrate --rule HTS1 --sessions 358
    uv run python tools/research_studies/dev_studies.py power --rule HTS1 --sessions 358
    uv run python tools/research_studies/dev_studies.py random-skip --rule HTS1
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np

from butterfly_guy.research import protocol
from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.holdout import DEVELOPMENT

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "reports" / "research" / "spx_0dte_thetadata"
DEFAULT_RUN = "7d7f91ad9ba5"
H1_SESSIONS = {358: 204, 421: 204}  # draft halves on the holdout calendar (package §4)


def load(run: str) -> tuple[list[dt.date], dict[str, dict[str, np.ndarray]], dict[str, list]]:
    """Development dates; per variant, per-session `stressed` and `stressed_delayed` P&L;
    per variant, the (date, stressed P&L) of each trade."""
    ds = Dataset.open("spx_0dte_thetadata")
    dates = [d for d in ds.sessions()["date"] if DEVELOPMENT[0] <= d <= DEVELOPMENT[1]]
    pos = {d: i for i, d in enumerate(dates)}
    vec: dict[str, dict[str, np.ndarray]] = {}
    trades: dict[str, list] = {}
    for line in (RUNS / run / "trades.jsonl").open():
        t = json.loads(line)
        d = dt.date.fromisoformat(t["date"])
        if d not in pos:
            raise SystemExit(f"{run}: trade on {d} outside the development window")
        v = vec.setdefault(t["variant"], {m: np.zeros(len(dates))
                                          for m in ("stressed", "stressed_delayed")})
        for m in v:
            p = (t.get(m) or {}).get("pnl")
            if p is not None:
                v[m][pos[d]] += p
        p = (t.get("stressed") or {}).get("pnl")
        if p is not None:
            trades.setdefault(t["variant"], []).append((d, p))
    return dates, vec, trades


def cmd_check(a: argparse.Namespace) -> None:
    dates, vec, _ = load(a.run)
    print(f"{a.run}: {len(dates)} development sessions")
    for name, v in vec.items():
        print(f"  {name:10s} stressed {v['stressed'].sum():>10,.0f}  "
              f"delayed {v['stressed_delayed'].sum():>10,.0f}")


def cmd_calibrate(a: argparse.Namespace) -> None:
    _, vec, _ = load(a.run)
    diff = vec[a.rule]["stressed"] - vec[protocol.BASELINE]["stressed"]
    print(json.dumps(protocol.calibrate_gate1(diff, a.sessions, sims=a.sims), indent=1))


def cmd_power(a: argparse.Namespace) -> None:
    """Simulated holdouts: 10-session moving blocks of development pairs, resampled to
    `--sessions`, then protocol.gates at the calibrated level for `--k`.

    Scenarios shift the paired difference by a constant per session (package §9):
    `dev` keeps it, `half` removes half its mean, `none` all of it; `none-flat` also shifts
    E0 to break even. Gate 6 is the rule's own P&L, E0 + difference."""
    _, vec, _ = load(a.run)
    base, base_d = vec[protocol.BASELINE]["stressed"], vec[protocol.BASELINE]["stressed_delayed"]
    diff = vec[a.rule]["stressed"] - base
    diff_d = vec[a.rule]["stressed_delayed"] - base_d
    cal = protocol.calibrate_gate1(diff, a.sessions, sims=a.cal_sims)
    tail = cal["levels"][str(a.k)] if cal["reached"][str(a.k)] else None
    if tail is None:
        raise SystemExit(f"{a.rule}: gate 1 cannot be calibrated at k = {a.k}")
    n1 = H1_SESSIONS.get(a.sessions, round(a.sessions * 204 / 358))
    dates = [protocol.SPLIT] * n1 + [protocol.SPLIT + dt.timedelta(days=1)] * (a.sessions - n1)
    rng = np.random.default_rng(a.seed)
    idx = protocol._blocks(rng, len(diff), a.sessions, a.sims)
    m = diff.mean()
    print(f"{a.rule}, k = {a.k}, {a.sessions} sessions, gate-1 tail {tail}, {a.sims} sims")
    for name, shift, flat in (("dev", 0.0, False), ("half", m / 2, False),
                              ("none", m, False), ("none-flat", m, True)):
        b = base - base.mean() if flat else base
        bd = base_d - base.mean() if flat else base_d
        g14 = all6 = 0
        for s in range(a.sims):
            i = idx[s]
            g = protocol.gates(b[i] + diff[i] - shift, b[i], bd[i] + diff_d[i] - shift, bd[i],
                               dates, a.k, tail)
            ok = g["gate1"] and g["gate2"] and g["gate3"] and g["gate4"]
            g14 += ok
            all6 += ok and g["gate6"]
        print(f"  {name:10s} gates 1-4 {g14 / a.sims:6.1%}   all gates {all6 / a.sims:6.1%}")


def cmd_random_skip(a: argparse.Namespace) -> None:
    """Random skips of E0 trades, the same number the rule skips (package §3)."""
    _, vec, trades = load(a.run)
    e0 = np.array([p for _, p in trades[protocol.BASELINE]])
    rule_days = {d for d, _ in trades[a.rule]}
    n = sum(d not in rule_days for d, _ in trades[protocol.BASELINE])
    gain = float(vec[a.rule]["stressed"].sum() - vec[protocol.BASELINE]["stressed"].sum())
    rng = np.random.default_rng(a.seed)
    draws = np.array([-e0[rng.choice(len(e0), n, replace=False)].sum() for _ in range(a.draws)])
    print(f"{a.rule}: skips {n} E0 trades, Δ {gain:,.0f}; random skip mean "
          f"{draws.mean():,.0f}, share ≥ Δ {(draws >= gain).mean():.1%}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--run", default=DEFAULT_RUN)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    c = sub.add_parser("calibrate")
    c.add_argument("--rule", required=True)
    c.add_argument("--sessions", type=int, default=358)
    c.add_argument("--sims", type=int, default=protocol.CAL_SIMS)
    c.set_defaults(fn=cmd_calibrate)
    w = sub.add_parser("power")
    w.add_argument("--rule", required=True)
    w.add_argument("--sessions", type=int, default=358)
    w.add_argument("--k", type=int, default=1)
    w.add_argument("--sims", type=int, default=1000)
    w.add_argument("--cal-sims", type=int, default=protocol.CAL_SIMS)
    w.add_argument("--seed", type=int, default=1)
    w.set_defaults(fn=cmd_power)
    r = sub.add_parser("random-skip")
    r.add_argument("--rule", required=True)
    r.add_argument("--draws", type=int, default=20_000)
    r.add_argument("--seed", type=int, default=1)
    r.set_defaults(fn=cmd_random_skip)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
