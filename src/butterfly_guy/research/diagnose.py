"""Descriptive breakdowns of E0 by scheduled event and volatility term structure.

DESCRIPTIVE, on development data. Nothing here evaluates a rule: there are no
intervals, no p-values and no registry records. Every cell reports its session and
trade counts (all / H1 / H2) next to every figure, so thin cells are visible as such.

For each session the E0 replay (the chosen profile, default `sweep_20260925`) gives:

- stressed and delayed-exit stressed P&L (zero on no-trade days);
- the tie-set average at $0.10 and $0.25 (mean over near-tied flies, summed over entries);
- settled landings;
- the move after 10:00 ET in chain-implied sigma: (close - spot) / (1.25 x ATM straddle)
  at the snapshot at or before 10:00, as in the 2026-09-25 journal entry.

Session features come from `features.SessionFeatures` and obey its leakage rules. Term
structure buckets use sample terciles of each ratio (data-derived, stated with their
boundaries) plus the fixed VIX/VIX3M = 1 split.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from butterfly_guy.research.entry import PROFILES, RunContext, SessionLoader
from butterfly_guy.research.evaluate import common_dates, session_vector
from butterfly_guy.research.exits import HELD
from butterfly_guy.research.features import RATIOS, SessionFeatures
from butterfly_guy.research.market import et_us
from butterfly_guy.research.simulate import run_variants
from butterfly_guy.research.tieset import THRESHOLDS, TiesetScorer
from butterfly_guy.research.variants import resolve

LABEL = "DESCRIPTIVE — development data — not a rule evaluation"
ENTRY_TIME = dt.time(10, 0)  # start of the configured entry window (07:00 PT)
PRE_ENTRY_RELEASES = ("CPI", "NFP", "PCE")
MODELS = ("stressed", "stressed_delayed")


@dataclass
class SessionRow:
    date: dt.date
    h1: bool
    pnl: dict[str, float]  # model -> session P&L
    tie: dict[str, float]  # "0.10:stressed" -> session tie-set average
    trades: int
    settled: int
    z: float | None  # move after 10:00 in implied sigma
    events: tuple[str, ...]
    releases_before_entry: bool
    ts: dict = field(default_factory=dict)


def _session_z(loader: SessionLoader, d: dt.date) -> float | None:
    s = loader.load(d)
    if s is None or s.close is None:
        return None
    i = s.market.at_or_before(et_us(d, 10, 0))
    if i < 0:
        return None
    straddle = s.market.atm_straddle(i)
    if straddle is None or straddle <= 0:
        return None
    return (s.close - float(s.market.spot[i])) / (1.25 * straddle)


def session_rows(features: SessionFeatures, ds, profile: str, start: dt.date | None,
                 end: dt.date | None, split: dt.date, exit_delay: int
                 ) -> tuple[list[SessionRow], dict]:
    from butterfly_guy.research.entry import load_spx_config

    ctx = RunContext(load_spx_config())
    loader = SessionLoader(ds, PROFILES[profile])
    scorer = TiesetScorer(models=MODELS)
    result = run_variants(loader, resolve(["E0"]), ctx, start=start, end=end,
                          exit_delay=exit_delay, tieset=scorer)
    dates, dropped = common_dates(result, ["E0"])
    trades = result.runs["E0"].trades
    vec = {m: session_vector(trades, dates, m) for m in MODELS}
    ties: dict[tuple[str, dt.date], float] = {}
    for t in THRESHOLDS:
        for d, _direction, pnl in scorer.rows.get(("E0", t), []):
            for m in MODELS:
                key = (f"{t:.2f}:{m}", d)
                ties[key] = ties.get(key, 0.0) + float(pnl[m].mean())
    z_loader = SessionLoader(ds, PROFILES[profile])
    rows = []
    for i, d in enumerate(dates):
        day = [t for t in trades if t.date == d]
        visible = features.calendar.events_for(d)
        rows.append(SessionRow(
            date=d, h1=d <= split,
            pnl={m: float(vec[m][i]) for m in MODELS},
            tie={f"{t:.2f}:{m}": ties.get((f"{t:.2f}:{m}", d), 0.0)
                 for t in THRESHOLDS for m in MODELS},
            trades=len(day), settled=sum(t.exit_reason == HELD for t in day),
            z=_session_z(z_loader, d),
            events=features.events(d),
            releases_before_entry=any(e.event_type in PRE_ENTRY_RELEASES and e.before(ENTRY_TIME)
                                      for e in visible),
            ts=features.term_structure(d, et_us(d, 10, 0)),
        ))
    info = {"sessions": len(dates), "trades": len(trades),
            "dropped": {d.isoformat(): r for d, r in sorted(dropped.items())},
            "skipped": {d.isoformat(): r for d, r in sorted(result.skipped.items())}}
    return rows, info


def _half(values: list[float], rows: list[SessionRow]) -> tuple[float, float, float]:
    a = np.array(values)
    h1 = np.array([r.h1 for r in rows], dtype=bool)
    return (float(a.sum()), float(a[h1].sum()) if len(a) else 0.0,
            float(a[~h1].sum()) if len(a) else 0.0)


def _r(x: float | None, nd: int = 2) -> float | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, nd)


def cell(rows: list[SessionRow]) -> dict:
    """Figures for one cell; all sums are over sessions, zeros on no-trade days."""
    n = len(rows)
    n1 = sum(r.h1 for r in rows)
    out: dict = {"sessions": [n, n1, n - n1],
                 "trades": [sum(r.trades for r in rows), sum(r.trades for r in rows if r.h1),
                            sum(r.trades for r in rows if not r.h1)],
                 "settled": sum(r.settled for r in rows)}
    for m in MODELS:
        tot, h1, h2 = _half([r.pnl[m] for r in rows], rows)
        out[m] = {"net": _r(tot), "h1": _r(h1), "h2": _r(h2),
                  "per_session": _r(tot / n) if n else None}
    out["delayed_minus_stressed"] = _r(out["stressed_delayed"]["net"] - out["stressed"]["net"])
    for key in (f"{t:.2f}:{m}" for t in THRESHOLDS for m in MODELS):
        tot, h1, h2 = _half([r.tie[key] for r in rows], rows)
        out[f"tieset_{key}"] = {"net": _r(tot), "h1": _r(h1), "h2": _r(h2)}
    zs = np.array([r.z for r in rows if r.z is not None])
    some = len(zs) > 0
    out["move_after_10"] = {
        "n": len(zs),
        "rms_sigma": _r(float(np.sqrt((zs ** 2).mean())), 3) if some else None,
        "mean_abs_sigma": _r(float(np.abs(zs).mean()), 3) if some else None,
    }
    return out


def _terciles(values: list[float]) -> tuple[float, float]:
    lo, hi = np.quantile(np.array(values), [1 / 3, 2 / 3])
    return float(lo), float(hi)


def breakdowns(rows: list[SessionRow]) -> dict:
    groups: dict[str, dict[str, Callable[[SessionRow], bool]]] = {}
    ev: dict[str, Callable[[SessionRow], bool]] = {"all sessions": lambda r: True}
    for t in ("FOMC", "CPI", "NFP", "PCE", "OPEX", "QUARTER_END", "EARLY_CLOSE"):
        ev[t] = lambda r, t=t: t in r.events
        ev[f"not {t}"] = lambda r, t=t: t not in r.events
    ev["08:30 release (CPI/NFP/PCE), before entry"] = lambda r: r.releases_before_entry
    ev["any scheduled event"] = lambda r: bool(r.events)
    ev["no scheduled event"] = lambda r: not r.events
    groups["events"] = ev

    ts: dict[str, Callable[[SessionRow], bool]] = {}
    bounds = {}
    for name in RATIOS:
        key = f"{name}_prior"
        vals = [r.ts.get(key) for r in rows if r.ts.get(key) is not None]
        if len(vals) < 3:
            continue
        lo, hi = _terciles(vals)
        bounds[key] = [round(lo, 4), round(hi, 4)]
        ts[f"{key} low (< {lo:.3f})"] = lambda r, k=key, lo=lo: (r.ts.get(k) is not None
                                                                 and r.ts[k] < lo)
        ts[f"{key} mid"] = lambda r, k=key, lo=lo, hi=hi: (r.ts.get(k) is not None
                                                           and lo <= r.ts[k] < hi)
        ts[f"{key} high (>= {hi:.3f})"] = lambda r, k=key, hi=hi: (r.ts.get(k) is not None
                                                                   and r.ts[k] >= hi)
        ts[f"{key} missing"] = lambda r, k=key: r.ts.get(k) is None
    ts["vix_vix3m_prior < 1 (contango)"] = lambda r: (r.ts.get("vix_vix3m_prior") is not None
                                                      and r.ts["vix_vix3m_prior"] < 1)
    ts["vix_vix3m_prior >= 1 (backwardation)"] = lambda r: (
        r.ts.get("vix_vix3m_prior") is not None and r.ts["vix_vix3m_prior"] >= 1)
    groups["term_structure"] = ts
    out = {g: {label: cell([r for r in rows if pred(r)]) for label, pred in preds.items()}
           for g, preds in groups.items()}
    out["tercile_bounds"] = bounds
    return out


def coverage(rows: list[SessionRow]) -> dict:
    keys = sorted({k for r in rows for k in r.ts if k != "prior_session"})
    return {k: sum(r.ts.get(k) is not None for r in rows) for k in keys}


def session_table(rows: list[SessionRow]) -> list[dict]:
    return [{"date": r.date.isoformat(), "h1": r.h1, "trades": r.trades, "settled": r.settled,
             **{m: _r(v) for m, v in r.pnl.items()},
             **{f"tieset_{k}": _r(v) for k, v in r.tie.items()},
             "z_after_10": _r(r.z, 4), "events": list(r.events),
             "releases_before_entry": r.releases_before_entry,
             **{k: (_r(v, 6) if isinstance(v, float) else v) for k, v in r.ts.items()}}
            for r in rows]


def _money(x: float | None) -> str:
    return "—" if x is None else f"{x:,.0f}"


def markdown(results: dict, provenance: dict) -> str:
    meta = results["meta"]
    lines = [
        f"# E0 diagnostics {provenance['run_id']}",
        "",
        f"**{LABEL}.** No rule is evaluated here; a feature-based rule must be registered "
        "before it is tested.",
        "",
        f"- Dataset `{meta['dataset']}` hash `{meta['dataset_hash'][:16]}…`; aux "
        f"`{(meta['inputs']['aux_hash'] or 'none')[:16]}…`; calendar "
        f"`{meta['inputs']['event_calendar']['file']}` sha256 "
        f"`{meta['inputs']['event_calendar']['sha256'][:16]}…`",
        f"- Profile `{meta['profile']}`, {meta['start']} → {meta['end']}, H1 through "
        f"{meta['split']}; config sha256 `{meta['config_sha256'][:16]}…`; exit delay "
        f"{meta['exit_delay_snapshots']} snapshot(s)",
        f"- Git `{provenance['git_sha'][:12]}`{' (dirty)' if provenance['git_dirty'] else ''}; "
        f"command: `{provenance['command']}`",
        f"- {results['sessions']['sessions']} sessions, {results['sessions']['trades']} E0 "
        "trades. Cells overlap (a session can have several events).",
        "",
        "Columns: sessions and trades as all/H1/H2; stressed and delayed nets (all, H1, H2) "
        "and per session; tie-set averages at $0.10/$0.25 (stressed); settled landings; RMS "
        "and mean |move| after 10:00 in implied sigma.",
    ]
    head = ("| Cell | Sessions | Trades | Stressed | H1 | H2 | /session | Delayed | H1 | H2 "
            "| Tie $0.10 | Tie $0.25 | Settled | RMS σ | mean abs σ |")
    rule = "|---|---|---|" + "---:|" * 12
    for group, title in (("events", "By scheduled event"),
                         ("term_structure", "By term-structure bucket (prior-session closes)")):
        lines += ["", f"## {title}", "", head, rule]
        for label, c in results["breakdowns"][group].items():
            s, d = c["stressed"], c["stressed_delayed"]
            lines.append(
                f"| {label} | {'/'.join(map(str, c['sessions']))} | "
                f"{'/'.join(map(str, c['trades']))} | {_money(s['net'])} | {_money(s['h1'])} | "
                f"{_money(s['h2'])} | {_money(s['per_session'])} | {_money(d['net'])} | "
                f"{_money(d['h1'])} | {_money(d['h2'])} | "
                f"{_money(c['tieset_0.10:stressed']['net'])} | "
                f"{_money(c['tieset_0.25:stressed']['net'])} | {c['settled']} | "
                f"{c['move_after_10']['rms_sigma'] or '—'} | "
                f"{c['move_after_10']['mean_abs_sigma'] or '—'} |")
    lines += ["", "Tercile bounds (sample-derived): "
              + ", ".join(f"`{k}` {v[0]} / {v[1]}"
                          for k, v in results["breakdowns"]["tercile_bounds"].items()),
              "", "## Feature coverage (sessions with a value)", ""]
    lines += [f"- `{k}`: {v}" for k, v in results["coverage"].items()]
    lines += ["", "## Artifact hashes", ""]
    lines += [f"- `{f}`: `{h}`" for f, h in provenance["hashes"].items()]
    return "\n".join(lines) + "\n"
