"""Reproducible run artifacts.

`results.json` and `trades.jsonl` hold only what the data, profile, configuration,
variant definitions and evaluation parameters determine, written canonically, so their
SHA-256 is a regression fingerprint across commits. Provenance (git SHA, time, command,
registry counts) goes to `provenance.json` and `report.md`.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

from butterfly_guy.research.accounting import MODELS
from butterfly_guy.research.market import us_to_datetime
from butterfly_guy.research.simulate import Trade


def dump_canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, indent=1, default=str) + "\n"


def _r(x: float | None, nd: int = 6) -> float | None:
    return None if x is None else round(float(x), nd)


def _iso(ts_us: int | None) -> str | None:
    return None if ts_us is None else us_to_datetime(ts_us).isoformat()


def trade_record(t: Trade) -> dict:
    rec = {
        "date": t.date.isoformat(), "variant": t.variant, "direction": t.fly.direction,
        "lower": t.fly.lower, "center": t.fly.center, "upper": t.fly.upper,
        "width": t.fly.width, "entry_time": _iso(t.entry_ts_us), "entry_cost": _r(t.entry_cost),
        "vix": _r(t.vix), "spot": _r(t.spot), "exit_reason": t.exit_reason,
        "exit_time": _iso(t.exit_ts_us), "exit_value": _r(t.exit_value), "peak": _r(t.peak),
        "settlement": _r(t.settlement),
    }
    if t.history_n is not None:
        rec["history"] = {"n": t.history_n, "last": t.history_last}
    for m in MODELS:
        f = t.fills.fills[m]
        rec[m] = {"status": f.status, "entry": _r(f.entry), "exit": _r(f.exit),
                  "pnl": _r(t.pnl(m), 4), "exit_roll": f.exit_roll,
                  "settlement_fallback": f.settlement_fallback}
    return rec


def write_run(out_dir: Path, results: dict, trades: list[Trade], provenance: dict,
              render: Callable[[dict, dict], str] | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results_text = dump_canonical(results)
    trades_text = "".join(
        json.dumps(trade_record(t), sort_keys=True, default=str) + "\n"
        for t in sorted(trades, key=lambda t: (t.variant, t.date, t.entry_ts_us,
                                               t.fly.direction))
    )
    (out_dir / "results.json").write_text(results_text)
    (out_dir / "trades.jsonl").write_text(trades_text)
    hashes = {
        "results.json": hashlib.sha256(results_text.encode()).hexdigest(),
        "trades.jsonl": hashlib.sha256(trades_text.encode()).hexdigest(),
    }
    provenance = {**provenance, "hashes": hashes}
    (out_dir / "provenance.json").write_text(dump_canonical(provenance))
    (out_dir / "report.md").write_text((render or markdown)(results, provenance))
    return hashes


def _money(x: object) -> str:
    return "—" if x is None else f"{x:,.0f}"


def _ci(vs: dict | None) -> str:
    if not vs:
        return "—"
    if vs["ci90"] is None:
        return "n/a"
    return " / ".join(_money(x) for x in vs["ci90"])


def markdown(results: dict, provenance: dict) -> str:
    ev, meta = results["evaluation"], results["meta"]
    base = meta["baseline"]
    delay = meta.get("accounting", {}).get("exit_delay_snapshots")
    few = ev["sessions"] < meta["eval"].get("min_bootstrap_sessions", 0)
    lines = [
        f"# Research run {provenance['run_id']}",
        "",
        f"- Dataset `{meta['dataset']}` hash `{meta['dataset_hash'][:16]}…`; profile "
        f"`{meta['profile']['name']}`; config sha256 `{meta['config_sha256'][:16]}…`",
        f"- Sessions: {ev['sessions']} ({ev['first']} → {ev['last']}); H1 {ev['h1_sessions']} "
        f"through {meta['eval']['split']}, H2 {ev['h2_sessions']}",
        f"- Git `{provenance['git_sha'][:12]}`{' (dirty)' if provenance['git_dirty'] else ''}; "
        f"command: `{provenance['command']}`",
        f"- Variants tried on this dataset name (registry): "
        f"{provenance['registry']['tried']['dataset']} "
        f"({provenance['registry']['tried']['post_hoc']} post hoc)",
        "",
        "Primary accounting: stressed marketable (ask/bid crossing, +$0.05 per contract per "
        "executed side, $0.65 commission, free cash settlement). P&L in dollars per one-lot "
        "fly; session figures include zeros on no-trade days. CI: paired moving-block "
        f"bootstrap ({meta['eval']['bootstrap_block']}-session blocks, "
        f"{meta['eval']['bootstrap_reps']} reps) of the difference from {base}"
        f"{' (not reported: too few sessions)' if few else ''}.",
        "",
        f"Exit-latency stress (\"Delayed\"): stressed, with every intraday exit filled from "
        f"the snapshot {delay} decision-clock time(s) after the trigger (at least {delay} "
        "recorded snapshot(s) later), rolling forward past unusable markets and falling back "
        "to settlement. Entries, triggers and held trades are unchanged.",
        "",
        "| Variant | Stage | Trades | Net | Exp | PF | Win% | Max DD | Top-3 % | Net ex top-3 "
        "| H1 | H2 | Midpoint net | Δ vs base | 90% CI | P(better) | Delayed net "
        "| Δ delayed |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    stages = provenance.get("stages", {})
    for name, arm in ev["arms"].items():
        s, mid, dl = arm["stressed"], arm["midpoint"], arm["stressed_delayed"]
        vs, dvs = s.get("vs_baseline"), dl.get("vs_baseline")
        p_better = "—" if not vs else ("n/a" if vs["p_better"] is None else vs["p_better"])
        lines.append(
            f"| {name} | {stages.get(name, '—')} | {s.get('n', 0)} | {_money(s.get('net'))} | "
            f"{_money(s.get('expectancy'))} | {s.get('profit_factor') or '—'} | "
            f"{s.get('win_rate', '—')} | {_money(s.get('max_drawdown'))} | "
            f"{s.get('top3_share') or '—'} | {_money(s.get('net_without_top3'))} | "
            f"{_money(s.get('h1_net'))} | {_money(s.get('h2_net'))} | {_money(mid.get('net'))} | "
            f"{_money(vs['net_diff']) if vs else '—'} | {_ci(vs)} | {p_better} | "
            f"{_money(dl.get('net'))} | {_money(dvs['net_diff']) if dvs else '—'} |"
        )
    fitted = {n: a for n, a in ev["arms"].items() if "fit_window" in a}
    if fitted:
        lines += ["", "## Fitted rules", "",
                  "Sessions inside a rule's fit window are in-sample for it; only the figures "
                  "after the window are out of sample.", "",
                  "| Variant | Fit window | Fitted value | n | Sessions in window | Net after "
                  "window | Δ vs base after window |",
                  "|---|---|---:|---:|---:|---:|---:|"]
        for name, arm in fitted.items():
            fit = meta["variants"][name]["definition"]["entry"].get("fitted", {})
            s = arm["stressed"]
            vs = s.get("vs_baseline") or {}
            lines.append(
                f"| {name} | {arm['fit_window'][0]} → {arm['fit_window'][1]} | "
                f"{fit.get('threshold')} | {fit.get('fit_n')} | {arm['sessions_in_fit_window']} | "
                f"{_money(s.get('after_fit_net'))} | {_money(vs.get('after_fit_diff'))} |")
    ties = results.get("tiesets")
    if ties:
        lines += ["", "## Robustness to fly choice (stressed)", "",
                  "| Variant | Tie threshold | Mean tie size | Tie-set avg | Draw 5% | Draw median "
                  "| Draw 95% | Beats base |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for name, by_t in ties.items():
            if "not_applicable" in by_t:
                lines.append(f"| {name} | n/a | — | — | — | — | — | — |")
                continue
            for t, row in by_t.items():
                s = row["stressed"]
                lines.append(
                    f"| {name} | {t} | {row['mean_tie_size']} | {_money(s['tieset_avg'])} | "
                    f"{_money(s['draw_p05'])} | {_money(s['draw_median'])} | "
                    f"{_money(s['draw_p95'])} | {s.get('beats_baseline', '—')} |")
    if ev["skipped_sessions"] or ev["dropped_sessions"]:
        lines += ["", "## Sessions not evaluated", ""]
        for d, why in {**ev["skipped_sessions"], **ev["dropped_sessions"]}.items():
            lines.append(f"- {d}: {why}")
    lines += ["", "## Output hashes", ""]
    for f, h in provenance["hashes"].items():
        lines.append(f"- `{f}`: `{h}`")
    return "\n".join(lines) + "\n"
