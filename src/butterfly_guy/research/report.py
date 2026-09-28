"""Reproducible run artifacts.

`results.json` and `trades.jsonl` hold only what the data, profile, configuration,
variant definitions and evaluation parameters determine, written canonically, so their
SHA-256 is a regression fingerprint across commits. Provenance (git SHA, time, command,
registry counts) goes to `provenance.json` and `report.md`.
"""

from __future__ import annotations

import hashlib
import json
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
    for m in MODELS:
        f = t.fills.fills[m]
        rec[m] = {"status": f.status, "entry": _r(f.entry), "exit": _r(f.exit),
                  "pnl": _r(t.pnl(m), 4), "exit_roll": f.exit_roll,
                  "settlement_fallback": f.settlement_fallback}
    return rec


def write_run(out_dir: Path, results: dict, trades: list[Trade], provenance: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results_text = dump_canonical(results)
    trades_text = "".join(
        json.dumps(trade_record(t), sort_keys=True, default=str) + "\n"
        for t in sorted(trades, key=lambda t: (t.variant, t.date, t.entry_ts_us))
    )
    (out_dir / "results.json").write_text(results_text)
    (out_dir / "trades.jsonl").write_text(trades_text)
    hashes = {
        "results.json": hashlib.sha256(results_text.encode()).hexdigest(),
        "trades.jsonl": hashlib.sha256(trades_text.encode()).hexdigest(),
    }
    provenance = {**provenance, "hashes": hashes}
    (out_dir / "provenance.json").write_text(dump_canonical(provenance))
    (out_dir / "report.md").write_text(markdown(results, provenance))
    return hashes


def _money(x: object) -> str:
    return "—" if x is None else f"{x:,.0f}"


def markdown(results: dict, provenance: dict) -> str:
    ev, meta = results["evaluation"], results["meta"]
    base = meta["baseline"]
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
        f"{meta['eval']['bootstrap_reps']} reps) of the difference from {base}.",
        "",
        "| Variant | Stage | Trades | Net | Exp | PF | Win% | Max DD | Top-3 % | Net ex top-3 "
        "| H1 | H2 | Midpoint net | Δ vs base | 90% CI | P(better) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    stages = provenance.get("stages", {})
    for name, arm in ev["arms"].items():
        s, mid = arm["stressed"], arm["midpoint"]
        vs = s.get("vs_baseline")
        ci = "—" if not vs else " / ".join(_money(x) for x in vs["ci90"])
        lines.append(
            f"| {name} | {stages.get(name, '—')} | {s.get('n', 0)} | {_money(s.get('net'))} | "
            f"{_money(s.get('expectancy'))} | {s.get('profit_factor') or '—'} | "
            f"{s.get('win_rate', '—')} | {_money(s.get('max_drawdown'))} | "
            f"{s.get('top3_share') or '—'} | {_money(s.get('net_without_top3'))} | "
            f"{_money(s.get('h1_net'))} | {_money(s.get('h2_net'))} | {_money(mid.get('net'))} | "
            f"{_money(vs['net_diff']) if vs else '—'} | {ci} | "
            f"{vs['p_better'] if vs else '—'} |"
        )
    ties = results.get("tiesets")
    if ties:
        lines += ["", "## Robustness to fly choice (stressed)", "",
                  "| Variant | Tie threshold | Mean tie size | Tie-set avg | Draw 5% | Draw median "
                  "| Draw 95% | Beats base |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for name, by_t in ties.items():
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
