"""Offline isolated exit trials; replay mechanics copied from frozen research harness.

No config loader, broker, database, or live mutations. See PLAN.md for fixed scope.
"""

import csv
import datetime as dt
import hashlib
import json
import random
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
from replay import (  # noqa: E402
    ET,
    PositionState,
    ProfitManagementSettings,
    ProfitStateMachine,
    get_time_regime,
    market_close_time,
    metrics,
    path_for,
    timestamp,
)


class ConfirmedMachine:
    """Delay only repeated discretionary drawdown signals, never hard exits."""

    def __init__(self, settings, seconds=0):
        self.machine = ProfitStateMachine(settings)
        self.seconds = seconds
        self.pending_reason = None
        self.since = None
        self.previous = None

    def evaluate(self, pos):
        signal = self.machine.evaluate(pos)
        now = pos.minutes_since_open * 60
        if not signal or not signal.reason.startswith("drawdown_") or not self.seconds:
            self.pending_reason = self.since = self.previous = None
            return signal
        if (
            signal.reason != self.pending_reason
            or self.previous is None
            or now - self.previous > 10
        ):
            self.pending_reason = signal.reason
            self.since = now
            self.previous = now
            return None
        self.previous = now
        return signal if now - self.since >= self.seconds else None


def replay(trade, path, settings, fee, stress="mark", confirmation_seconds=0):
    machine = ConfirmedMachine(settings, confirmation_seconds)
    entry = float(trade["entry_price"])
    peak = entry
    entry_time = timestamp(trade["entry_time"])
    for i, point in enumerate(path):
        t, value = point["time"], point["mark"]
        peak = max(peak, value)
        local = t.astimezone(ET)
        mins = (
            local - local.replace(hour=9, minute=30, second=0, microsecond=0)
        ).total_seconds() / 60
        close = dt.datetime.combine(local.date(), market_close_time(local.date()), tzinfo=ET)
        pos = PositionState(
            entry_price=entry,
            current_value=round(value, 4),
            peak_value=round(peak, 4),
            pnl=round(value - entry, 4),
            drawdown_from_peak=round((peak - value) / peak, 4) if peak else 0.0,
            time_regime=get_time_regime(mins),
            minutes_to_close=(close - t).total_seconds() / 60,
            minutes_since_open=mins,
            position_age_minutes=(t - entry_time).total_seconds() / 60,
            spread_bid=max(0.0, point["bid"]),
            spread_ask=point["ask"],
            bid_to_mark_ratio=round(max(0.0, point["bid"]) / value, 4) if value else None,
        )
        signal = machine.evaluate(pos)
        if signal:
            fill_point = point
            if stress == "next_quote_halfspread_005":
                if i + 1 == len(path):
                    return {"status": "censored_fill_latency"}
                fill_point = path[i + 1]
            fraction, extra = {
                "mark": (0.0, 0.0),
                "quarter_halfspread_005": (0.25, 0.05),
                "halfspread_005": (0.5, 0.05),
                "crossed_010": (1.0, 0.10),
                "next_quote_halfspread_005": (0.5, 0.05),
            }[stress]
            drag = fraction * max(0.0, fill_point["mark"] - fill_point["bid"]) + extra
            price = round(fill_point["mark"] - drag - fee, 2)
            return {
                "status": "exit",
                "exit_time": fill_point["time"].isoformat(),
                "signal_time": t.isoformat(),
                "exit_price": price,
                "reason": signal.reason,
                "peak_replayed": peak,
                "signal_mark": value,
                "signal_bid": point["bid"],
                "signal_ask": point["ask"],
                "fill_mark": fill_point["mark"],
                "fill_bid": fill_point["bid"],
                "fill_ask": fill_point["ask"],
                "pnl": round((price - entry) * 100 * int(trade["quantity"]), 2),
                "minutes": (fill_point["time"] - entry_time).total_seconds() / 60,
                "exit_drag_dollars": round(drag * 100 * int(trade["quantity"]), 2),
            }
    # A recorded cash settlement is a terminal payoff of these identical strikes,
    # not a quoted peak or a fabricated last-quote liquidation. Require near-close path.
    if trade["exit_reason"] == "cash_settled" and path:
        last = path[-1]["time"].astimezone(ET)
        close = dt.datetime.combine(last.date(), market_close_time(last.date()), tzinfo=ET)
        if (close - last).total_seconds() <= 120:
            price = float(trade["exit_price"])
            return {
                "status": "settlement",
                "exit_time": close.isoformat(),
                "exit_price": price,
                "reason": "cash_settled",
                "peak_replayed": peak,
                "pnl": round((price - entry) * 100 * int(trade["quantity"]), 2),
                "minutes": (close - entry_time).total_seconds() / 60,
                "exit_drag_dollars": 0.0,
            }
    return {"status": "censored_no_exit"}


def variants(base):
    result = {"baseline": (base.model_copy(deep=True), 0)}
    for percent in (60, 50, 70):
        cfg = base.model_copy(deep=True)
        cfg.regimes["late_morning"].drawdown_threshold = percent / 100
        result[f"trail_{percent}"] = (cfg, 0)
    for percent in (50, 40, 60):
        cfg = base.model_copy(deep=True)
        cfg.use_absolute_loss_stop = True
        cfg.max_loss_from_cost = percent / 100
        result[f"stop_{percent}"] = (cfg, 0)
    for seconds in (5, 2, 10):
        result[f"confirm_{seconds}"] = (base.model_copy(deep=True), seconds)
    return result


def stats(rows):
    result = metrics(rows)
    pnl = [r["pnl"] for r in rows]
    sd = statistics.stdev(pnl) if len(pnl) > 1 else None
    positive = [p for p in pnl if p > 0]
    result.update(
        pnl_sample_sd=sd,
        trade_mean_over_sd=statistics.mean(pnl) / sd if sd else None,
        largest_winner_share=max(positive) / sum(positive) if positive else None,
        net_after_additional_520_fee=sum(pnl) - 5.20 * len(pnl),
        exit_drag_dollars=sum(r["exit_drag_dollars"] for r in rows),
    )
    return result


def compare(baseline, candidate):
    b = {r["id"]: r for r in baseline if "pnl" in r}
    c = {r["id"]: r for r in candidate if "pnl" in r}
    ids = sorted(b.keys() & c.keys())
    b_rows, c_rows = [b[i] for i in ids], [c[i] for i in ids]
    top = sorted(b, key=lambda i: b[i]["pnl"], reverse=True)
    top = [i for i in top if b[i]["pnl"] > 0][:5]
    top_complete = all(i in c for i in top)
    denominator = sum(b[i]["pnl"] for i in top)
    return {
        "attempted": len(baseline),
        "baseline_resolved": len(b),
        "candidate_resolved": len(c),
        "paired_count": len(ids),
        "complete": len(ids) == len(baseline),
        "paired_ids": ids,
        "candidate_unresolved_ids": [r["id"] for r in candidate if "pnl" not in r],
        "paired_baseline": stats(b_rows),
        "paired_candidate": stats(c_rows),
        "paired_delta_pnl": sum(c[i]["pnl"] - b[i]["pnl"] for i in ids),
        "baseline_top5_ids": top,
        "top5_all_resolved": top_complete,
        "same_id_top5_retention": (
            sum(c[i]["pnl"] for i in top) / denominator
            if denominator and top_complete else None
        ),
    }


def bootstrap_mean_delta(baseline, candidate):
    """Resample paired session blocks; descriptive development uncertainty only."""
    c = {r["id"]: r for r in candidate}
    days = defaultdict(list)
    for r in baseline:
        days[r["date"]].append(c[r["id"]]["pnl"] - r["pnl"])
    blocks = list(days.values())
    rng = random.Random(20260913)
    means = []
    for _ in range(10000):
        sample = [x for block in rng.choices(blocks, k=len(blocks)) for x in block]
        means.append(statistics.mean(sample))
    means.sort()
    return {"lower_025": means[249], "upper_975": means[9749], "day_blocks": len(days)}


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((PARENT / "manifest.json").read_text())
    for relative, expected in manifest["files"].items():
        assert sha(PARENT / relative) == expected, f"Changed frozen evidence: {relative}"
    hashes = json.loads((PARENT / "source-hashes.json").read_text())
    for relative, expected in hashes.items():
        assert sha(PARENT / "frozen" / "butterfly_guy" / relative) == expected, relative
    with (PARENT / "raw/export.jsonl").open() as f:
        raw_baseline = json.loads(next(f))
        trades = json.loads(next(f))["rows"]
    trades = {t["id"]: t for t in trades if t["fill_model"] == "mark_v1"}
    assert len(trades) == 33
    assert min(t["trade_date"] for t in trades.values()) == "2026-07-22"
    assert max(t["trade_date"] for t in trades.values()) == "2026-09-11"
    assert all(int(t["quantity"]) == 1 for t in trades.values())
    base = ProfitManagementSettings(**raw_baseline["effective"]["profit_management"])
    assert base.strategy == "peakvaluetrailer" and not base.use_absolute_loss_stop
    assert [r.drawdown_threshold for r in base.regimes.values()] == [0.6, 0.9, 0.75]
    assert not base.quote_quality.enabled
    assert base.peak_tracking.confirmation_polls == 1
    assert not base.peak_tracking.require_quote_quality
    assert base.peak_tracking.max_jump_ratio is None
    assert base.peak_tracking.max_jump_abs is None
    fee = raw_baseline["effective"]["execution"]["paper_commission_per_contract"] * 4 / 100
    configs = variants(base)
    stresses = ("mark", "quarter_halfspread_005", "halfspread_005", "crossed_010",
                "next_quote_halfspread_005")
    results, coverage = [], []
    with (PARENT / "raw/monitor.jsonl").open() as f:
        for line in f:
            record = json.loads(line)
            if record["trade_id"] not in trades:
                continue
            trade = trades[record["trade_id"]]
            path, audit = path_for(trade, record["rows"])
            coverage.append({"id": trade["id"], "date": trade["trade_date"], **audit})
            for name, (cfg, seconds) in configs.items():
                for stress in stresses:
                    result = replay(trade, path, cfg, fee, stress, seconds)
                    results.append({
                        "id": trade["id"], "date": trade["trade_date"],
                        "direction": trade["direction"], "variant": name,
                        "stress": stress, **result,
                    })
    assert len(coverage) == 33 and len({r["id"] for r in coverage}) == 33
    original = list(csv.DictReader((PARENT / "results/trade_results.csv").open()))
    original = {(int(r["id"]), r["stress"]): r for r in original
                if r["source"] == "monitor" and r["fill_model"] == "mark_v1"
                and r["policy"] == "peakvaluetrailer"}
    for r in results:
        if r["variant"] != "baseline":
            continue
        prior = original[r["id"], r["stress"]]
        assert r["status"] == prior["status"]
        if "pnl" in r:
            assert r["pnl"] == float(prior["pnl"])
            assert r["reason"] == prior["reason"]
            assert r["exit_time"] == prior["exit_time"]
        if r["stress"] == "mark":
            t = trades[r["id"]]
            assert abs(r["pnl"] - float(t["pnl"]) * 100) < 0.01
            assert r["reason"] == t["exit_reason"]
    comparisons, breakdowns = [], []
    for name in configs:
        if name == "baseline":
            continue
        for stress in stresses:
            b = [r for r in results if r["variant"] == "baseline" and r["stress"] == stress]
            c = [r for r in results if r["variant"] == name and r["stress"] == stress]
            comparison = {"variant": name, "stress": stress, **compare(b, c)}
            if comparison["complete"] and name in ("trail_60", "stop_50", "confirm_5"):
                comparison["bootstrap_mean_delta"] = bootstrap_mean_delta(b, c)
            comparisons.append(comparison)
            for dimension in ("month", "direction"):
                key = (lambda r: r["date"][:7]) if dimension == "month" else (
                    lambda r: r["direction"])
                for value in sorted({key(r) for r in b}):
                    comp = compare([r for r in b if key(r) == value],
                                   [r for r in c if key(r) == value])
                    breakdowns.append({"variant": name, "stress": stress,
                                       "dimension": dimension, "value": value, **comp})
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    write_csv(out / "trade_results.csv", results)
    write_csv(out / "coverage.csv", coverage)
    (out / "comparisons.json").write_text(json.dumps(comparisons, indent=2) + "\n")
    (out / "breakdowns.json").write_text(json.dumps(breakdowns, indent=2) + "\n")
    frozen_configs = {name: {"profit_management": cfg.model_dump(),
                             "confirmation_seconds": seconds,
                             "confirmation_max_gap_seconds": 10}
                      for name, (cfg, seconds) in configs.items()}
    (HERE / "configs.json").write_text(json.dumps(frozen_configs, indent=2) + "\n")
    provenance = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "python": sys.version, "provider": manifest["provider"],
        "original_acquisition_utc": manifest["created_utc"],
        "range": ["2026-07-22", "2026-09-11"],
        "source": "monitor only; irregular chronological observations, UTC offsets",
        "display_timezone": "America/New_York", "account_sharpe": "unavailable",
        "command": ".venv/bin/python docs/research/spx-exits-2026-09-12/exit_trials/run_trials.py",
        "environment_variables": "none required or overridden",
        "exit_commission_points": fee,
        "input_hashes": {str(path.relative_to(PARENT)): sha(path) for path in (
            PARENT / "raw/export.jsonl", PARENT / "raw/monitor.jsonl",
            PARENT / "results/trade_results.csv", PARENT / "source-hashes.json",
            PARENT / "replay.py", HERE / "PLAN.md", HERE / "run_trials.py")},
        "lock_sha256": sha(PARENT.parents[2] / "uv.lock"),
        "output_hashes": {str(p.relative_to(HERE)): sha(p) for p in sorted(out.iterdir())},
        "baseline_parity": "33 ledger P/L/reasons; 165 prior replay statuses and resolved exits",
    }
    (HERE / "manifest.json").write_text(json.dumps(provenance, indent=2) + "\n")
    for r in comparisons:
        if r["stress"] == "mark":
            print(r["variant"], "paired", r["paired_count"],
                  "P/L", r["paired_baseline"]["net_pnl"], r["paired_candidate"]["net_pnl"],
                  "delta", r["paired_delta_pnl"],
                  "unresolved", r["candidate_unresolved_ids"])


if __name__ == "__main__":
    main()
