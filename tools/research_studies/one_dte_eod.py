"""Bounded retrospective SPXW overnight butterfly study; offline evidence only.

No runtime imports or configuration changes. Quote grids establish observation
availability, not original last-update times or executable complex-order fills.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from butterfly_guy.research.event_calendar import EventCalendar

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data/thetadata"
DAILY = (
    ROOT
    / "reports/thetadata_completion/2026-10-01/thetadata-daily/SPX_778e5f33f32685473b8e2a1cf5c3ab18286589e310ab7140dd014d65241c3e07.csv"
)
RECEIPT = DAILY.parent / "9f7d847ae966.json"
PERIODS = {"development": ("2023-01-03", "2024-06-28"), "comparison": ("2026-03-13", "2026-09-25")}
SIGNALS = ("neutral", "day_continue", "day_fade", "hour_continue", "hour_fade")
EXITS = ("09:45", "12:00", "settlement")
FEE = 2.60
STRESS = 0.05


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, allow_nan=False, default=str) + "\n")


def snap(x: float, step: float = 5.0) -> float:
    """Nearest strike, lower on ties (also for negative fixture inputs)."""
    return step * math.ceil(x / step - 0.5)


def allowed(day: str) -> bool:
    return not "2024-07-01" <= day <= "2026-03-12"


def next_session(day: str, expiry: str, sessions: list[str]) -> bool:
    """Validate listed expiration against actual Cboe index session dates."""
    i = np.searchsorted(sessions, day)
    return i < len(sessions) - 1 and sessions[i] == day and sessions[i + 1] == expiry


def ts(day: str, time: str) -> pd.Timestamp:
    return pd.Timestamp(f"{day} {time}", tz="America/New_York")


def snapshots(path: Path, day: str, expiry: str, times: tuple[str, ...]) -> tuple[dict, dict]:
    if not allowed(day) or not allowed(expiry):
        raise ValueError("protected quote/expiration dates forbidden")
    if not path.exists():
        return {}, {"path": str(path), "missing": True}
    table = pq.read_table(
        path,
        columns=[
            "symbol",
            "expiration",
            "strike",
            "right",
            "timestamp",
            "bid",
            "ask",
            "bid_size",
            "ask_size",
        ],
        filters=[("timestamp", "in", [ts(day, t).to_pydatetime() for t in times])],
    )
    f = table.to_pandas()
    if len(f):
        if set(f.symbol) != {"SPXW"} or set(f.expiration.astype(str)) != {expiry}:
            raise ValueError(f"wrong contract identity: {path}")
        if f.timestamp.dt.tz is None or set(f.timestamp.dt.date.astype(str)) != {day}:
            raise ValueError("incorrect/naive quote timestamps")
        if f.duplicated(["timestamp", "strike", "right"]).any():
            raise ValueError("duplicate contract snapshots")
    result = {t: f.loc[f.timestamp == ts(day, t)].set_index(["right", "strike"]) for t in times}
    return result, {
        "path": str(path),
        "sha256": sha(path),
        "bytes": path.stat().st_size,
        "selected_rows": len(f),
        "times_et": list(times),
    }


def valid(row: pd.Series, *, buy: bool | None = None, size: int = 1) -> bool:
    prices = (
        np.isfinite(row.bid) and np.isfinite(row.ask) and 0 <= row.bid <= row.ask and row.ask > 0
    )
    if buy is None:
        return bool(prices and row.bid_size >= size and row.ask_size >= size)
    return bool(prices and (row.ask_size if buy else row.bid_size) >= size)


def proxy(q: pd.DataFrame) -> dict | None:
    """Median zero-carry forward from up to five cheapest valid straddles."""
    pairs = []
    for strike in sorted(set(q.index.get_level_values("strike"))):
        if ("CALL", strike) not in q.index or ("PUT", strike) not in q.index:
            continue
        c, p = q.loc[("CALL", strike)], q.loc[("PUT", strike)]
        if not valid(c) or not valid(p):
            continue
        cm, pm = (c.bid + c.ask) / 2, (p.bid + p.ask) / 2
        pairs.append((cm + pm, strike, strike + cm - pm))
    pairs = sorted(pairs)[:5]
    if len(pairs) < 3:
        return None
    forwards = [p[2] for p in pairs]
    dispersion = max(forwards) - min(forwards)
    if dispersion > 2:
        return None
    forward = float(np.median(forwards))
    atm = min(pairs, key=lambda p: (abs(p[1] - forward), p[1]))
    return {
        "forward": forward,
        "straddle": float(atm[0]),
        "pairs": len(pairs),
        "dispersion": float(dispersion),
    }


def fly(q: pd.DataFrame, center: float, width: float, *, entry: bool) -> dict | None:
    legs = []
    for strike, qty in ((center - width, 1), (center, -2), (center + width, 1)):
        key = ("CALL", strike)
        if key not in q.index:
            return None
        row = q.loc[key]
        buy = qty > 0 if entry else qty < 0
        if not valid(row, buy=buy, size=abs(qty)):
            return None
        legs.append(
            {
                "strike": strike,
                "quantity": qty,
                "bid": float(row.bid),
                "ask": float(row.ask),
                "bid_size": int(row.bid_size),
                "ask_size": int(row.ask_size),
            }
        )
    mark = sum(leg["quantity"] * (leg["bid"] + leg["ask"]) / 2 for leg in legs)
    price = sum(
        leg["quantity"] * (leg["ask"] if (leg["quantity"] > 0) == entry else leg["bid"])
        for leg in legs
    )
    return {"price": price, "mark": mark, "legs": legs}


def payoff(settle: float, center: float, width: float) -> float:
    return max(width - abs(settle - center), 0.0)


def cashflow(
    debit: float, terminal: float | None, *, settlement: bool, stress: float = STRESS
) -> float | None:
    if terminal is None:
        return None
    sides = 1 if settlement else 2
    return (terminal - debit - sides * stress) * 100 - sides * FEE


def cells() -> list[dict]:
    return [
        {"signal": signal, "offset": offset, "width": width, "cell": f"{signal}|{offset:g}|{width}"}
        for signal in SIGNALS
        for offset in ((0.0,) if signal == "neutral" else (0.5, 1.0))
        for width in (20, 40)
    ]


def session_job(arg: tuple) -> tuple[list, dict, list]:
    day, expiry, period, close_value, early, expiry_close = arg
    audit = {"date": day, "expiration": expiry, "period": period}
    if early:
        return [], audit | {"status": "excluded_early_close"}, []
    path = ARCHIVE / "spxw_1dte/quote_1m" / day[:4] / f"{day}.parquet"
    snaps, receipt = snapshots(path, day, expiry, ("09:35", "14:45", "15:45", "15:46"))
    receipts = [receipt]
    if not snaps:
        return [], audit | {"status": "missing_entry_file"}, receipts
    proxies = {time: proxy(snaps[time]) for time in ("09:35", "14:45", "15:45")}
    if proxies["15:45"] is None:
        return [], audit | {"status": "missing_decision_proxy"}, receipts
    f = proxies["15:45"]
    exit_path = ARCHIVE / "spxw_0dte/quote_1m" / expiry[:4] / f"{expiry}.parquet"
    exit_snaps, exit_receipt = snapshots(exit_path, expiry, expiry, ("09:45", "12:00"))
    receipts.append(exit_receipt)
    rows = []
    for cell in cells():
        signal = cell["signal"]
        ref = (
            proxies["09:35" if signal.startswith("day") else "14:45"] if signal != "neutral" else f
        )
        base = (
            audit
            | cell
            | {
                "decision_time": ts(day, "15:45").isoformat(),
                "entry_time": ts(day, "15:46").isoformat(),
                "forward": f["forward"],
                "straddle": f["straddle"],
                "dispersion": f["dispersion"],
                "calendar_days": (dt.date.fromisoformat(expiry) - dt.date.fromisoformat(day)).days,
            }
        )
        if ref is None:
            rows.extend(
                base
                | {"exit": e, "policy": cell["cell"] + "|" + e, "status": "missing_signal_proxy"}
                for e in EXITS
            )
            continue
        sign = 0 if signal == "neutral" else int(np.sign(f["forward"] - ref["forward"]))
        if signal.endswith("fade"):
            sign = -sign
        if signal != "neutral" and sign == 0:
            rows.extend(
                base
                | {"exit": e, "policy": cell["cell"] + "|" + e, "status": "no_direction_signal"}
                for e in EXITS
            )
            continue
        center = snap(f["forward"] + sign * cell["offset"] * f["straddle"])
        quote = fly(snaps["15:46"], center, cell["width"], entry=True)
        base |= {"sign": sign, "center": center, "reference_forward": ref["forward"]}
        if quote is None or not 0 < quote["price"] < cell["width"]:
            reason = "missing_entry_legs" if quote is None else "invalid_debit"
            rows.extend(
                base | {"exit": e, "policy": cell["cell"] + "|" + e, "status": reason}
                for e in EXITS
            )
            continue
        base |= {
            "debit": quote["price"],
            "entry_mark": quote["mark"],
            "entry_legs": quote["legs"],
            "initial_risk": quote["price"] * 100 + FEE + STRESS * 100,
        }
        for exit_time in EXITS:
            settle = exit_time == "settlement"
            terminal_quote = (
                None
                if settle
                else fly(
                    exit_snaps.get(
                        exit_time,
                        pd.DataFrame(
                            index=pd.MultiIndex.from_tuples([], names=["right", "strike"])
                        ),
                    ),
                    center,
                    cell["width"],
                    entry=False,
                )
            )
            terminal = (
                payoff(close_value, center, cell["width"])
                if settle and close_value is not None
                else (terminal_quote["price"] if terminal_quote is not None else None)
            )
            mark = (
                terminal
                if settle
                else (terminal_quote["mark"] if terminal_quote is not None else None)
            )
            pnl = cashflow(quote["price"], terminal, settlement=settle)
            rows.append(
                base
                | {
                    "exit": exit_time,
                    "policy": cell["cell"] + "|" + exit_time,
                    "status": "completed" if terminal is not None else "unresolved_exit",
                    "terminal": terminal,
                    "terminal_mark": mark,
                    "exit_time": ts(expiry, expiry_close if settle else exit_time).isoformat(),
                    "settlement_close": close_value if settle else None,
                    "exit_legs": terminal_quote["legs"] if terminal_quote else None,
                    "pnl": pnl,
                    "pnl_component": cashflow(
                        quote["price"], terminal, settlement=settle, stress=0
                    ),
                    "pnl_mid": cashflow(quote["mark"], mark, settlement=settle, stress=0),
                    "risk_r": pnl / base["initial_risk"] if pnl is not None else None,
                }
            )
    return rows, audit | {"status": "processed", "proxies": proxies}, receipts


def metrics(f: pd.DataFrame) -> dict:
    x = f.loc[f.status == "completed"].sort_values("date")
    pnl = x.pnl.astype(float)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    equity = np.r_[0, pnl.cumsum().to_numpy()]
    initial = int(f.status.isin(["completed", "unresolved_exit"]).sum())
    return {
        "attempts": len(f),
        "entries": initial,
        "completed": len(x),
        "unresolved": initial - len(x),
        "excluded": len(f) - initial,
        "completion_rate": len(x) / initial if initial else None,
        "total_pnl": float(pnl.sum()) if len(x) else None,
        "expectancy": float(pnl.mean()) if len(x) else None,
        "win_rate": float((pnl > 0).mean()) if len(x) else None,
        "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
        "avg_win": float(wins.mean()) if len(wins) else None,
        "avg_loss": float(losses.mean()) if len(losses) else None,
        "max_drawdown_terminal": float((np.maximum.accumulate(equity) - equity).max())
        if len(x)
        else None,
        "mean_r": float(x.risk_r.mean()) if len(x) else None,
        "avg_debit_dollars": float(x.debit.mean() * 100) if len(x) else None,
        "mid_expectancy": float(x.pnl_mid.mean()) if len(x) else None,
        "component_expectancy": float(x.pnl_component.mean()) if len(x) else None,
        "stress_cost_per_trade": float((x.pnl_component - x.pnl).mean()) if len(x) else None,
        "spread_cost_per_trade": float((x.pnl_mid - x.pnl_component).mean()) if len(x) else None,
        "top5_pnl": float(pnl.nlargest(5).sum()) if len(x) else None,
        "excluding_top5_total": float(pnl.sum() - pnl.nlargest(5).sum()) if len(x) else None,
        "worst_trade": float(pnl.min()) if len(x) else None,
        "best_trade": float(pnl.max()) if len(x) else None,
        "avg_exposure_hours": float(
            (
                (
                    pd.to_datetime(x.exit_time, utc=True) - pd.to_datetime(x.entry_time, utc=True)
                ).dt.total_seconds()
                / 3600
            ).mean()
        )
        if len(x)
        else None,
        "statuses": f.status.value_counts().to_dict(),
        "months": {
            month: {"n": len(g), "pnl": float(g.pnl.sum())}
            for month, g in x.groupby(x.date.str[:7])
        },
    }


def summarize(f: pd.DataFrame) -> dict:
    out = {}
    for (period, policy), g in f.groupby(["period", "policy"], sort=True):
        m = metrics(g)
        baseline = f.loc[
            (f.period == period)
            & (f.signal == "neutral")
            & (f.width == g.width.iloc[0])
            & (f.exit == g.exit.iloc[0])
            & (f.status == "completed"),
            ["date", "pnl"],
        ]
        paired = g.loc[g.status == "completed", ["date", "pnl"]].merge(
            baseline, on="date", suffixes=("", "_baseline")
        )
        m["paired_baseline_n"] = len(paired)
        m["paired_delta_expectancy"] = (
            float((paired.pnl - paired.pnl_baseline).mean()) if len(paired) else None
        )
        out.setdefault(period, {})[policy] = m
    return out


def run(out: Path, workers: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if (out / "specification.json").exists():
        raise ValueError("Use a new output directory; prior evidence is immutable")
    source_sha_start = sha(Path(__file__))
    spec = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_sha256": source_sha_start,
        "hypothesis": "A directional or neutral EOD 1DTE fly can earn positive net expectancy and improve matched ATM baseline.",
        "periods_inclusive": PERIODS,
        "instrument": "SPXW PM settled",
        "right": "CALL",
        "cells": cells(),
        "exit_policies": EXITS,
        "decision_et": "15:45",
        "execution_et": "15:46 exact, strictly later",
        "entry_signal_times_et": ["09:35", "14:45", "15:45"],
        "proxies": "zero-carry put-call-parity median of <=5 cheapest straddles, >=3 valid pairs, dispersion<=2 SPX points; NOT observed spot",
        "placement": "forward + signal sign * offset * ATM straddle premium points, nearest5 lower tie; straddle is not sigma",
        "fees": "$0.65/contract/side assumed;4contracts/fly; settlement no closing fee",
        "stress": "0.05 net fly point per transaction",
        "selection": "Highest development stressed expectancy among >=100 completed and >=95% completion of admitted entries, policy lexicographic tie-break. Lock before opening comparison quotes. A negative maximum is not a candidate.",
        "falsification": "Reject tested policies with nonpositive development stressed expectancy; refinement only if locked policy positive in both periods, matched baseline improvement, no unresolved material mechanics. No untouched validation or deployability claim.",
        "exclusions": "early closes, protected entry OR expiry, wrong next-session identity; missing signal/entry/exit explicit, no future fallback",
        "calendar": "Cboe SPX daily session-date list",
        "no_trade_benchmark": 0,
        "limitations": [
            "Retrospective contaminated history",
            "18 entry cells x3 exit policies=54 correlated comparisons",
            "No live complex-order fill evidence",
            "No capital or portfolio model; one fly per eligible session per independent cell",
            "No overnight marks; terminal realized drawdown only",
            "Quote update age unknown",
            "No unobserved intraday stops or limits",
            "Funding and additional exchange/exercise fees not modeled",
            "Index parity is a zero-carry forward proxy; borrowing/rates and dividends not modeled",
        ],
    }
    write_json(out / "specification.json", spec)
    daily = pd.read_csv(DAILY)
    daily["date"] = pd.to_datetime(daily.DATE, format="%m/%d/%Y").dt.strftime("%Y-%m-%d")
    closes = dict(zip(daily.date, daily.SPX))
    sessions = sorted(closes)
    cal = EventCalendar()
    early = {e.event_date.isoformat() for e in cal.events if e.event_type == "EARLY_CLOSE"}
    catalog = [json.loads(line) for line in (ARCHIVE / "catalog.jsonl").read_text().splitlines()]
    catalog = {
        r["date"]: r["expiration"]
        for r in catalog
        if r["set"] == "spxw_1dte" and r["kind"] == "quote_1m" and r["status"] == "ok"
    }
    all_rows, audits, inputs = [], [], []
    for period, (start, end) in PERIODS.items():
        jobs = []
        for day, expiry in sorted(catalog.items()):
            if not start <= day <= end:
                continue
            if not allowed(day) or not allowed(expiry):
                audits.append(
                    {
                        "date": day,
                        "expiration": expiry,
                        "period": period,
                        "status": "excluded_protected_boundary",
                    }
                )
                continue
            if not next_session(day, expiry, sessions):
                audits.append(
                    {
                        "date": day,
                        "expiration": expiry,
                        "period": period,
                        "status": "excluded_not_next_session",
                    }
                )
                continue
            jobs.append(
                (
                    day,
                    expiry,
                    period,
                    closes.get(expiry),
                    day in early,
                    "13:00" if expiry in early else "16:00",
                )
            )
        with ProcessPoolExecutor(workers) as pool:
            for i, (rows, audit, receipts) in enumerate(pool.map(session_job, jobs), start=1):
                all_rows.extend(rows)
                audits.append(audit)
                inputs.extend(receipts)
                if i % 50 == 0:
                    print(f"{period}: {i}/{len(jobs)} sessions", flush=True)
        frame = pd.DataFrame(all_rows)
        partial = summarize(frame)
        write_json(out / f"{period}-metrics.json", partial[period])
        if period == "development":
            eligible = [
                (k, m)
                for k, m in partial[period].items()
                if m["completed"] >= 100 and m["completion_rate"] >= 0.95
            ]
            eligible.sort(key=lambda pair: (-pair[1]["expectancy"], pair[0]))
            chosen = eligible[0] if eligible else None
            write_json(
                out / "locked-selection.json",
                {
                    "locked_before_comparison_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "policy": chosen[0] if chosen else None,
                    "development_metrics": chosen[1] if chosen else None,
                    "positive_development": chosen[1]["expectancy"] > 0 if chosen else False,
                    "eligible_policies": len(eligible),
                },
            )
            print("Development choice frozen", flush=True)
    frame = pd.DataFrame(all_rows)
    frame.to_json(out / "journal.jsonl", orient="records", lines=True)
    scalar = frame.drop(columns=["entry_legs", "exit_legs"])
    scalar.to_csv(out / "journal.csv", index=False)
    scalar.to_parquet(out / "journal.parquet", index=False)
    pd.DataFrame(audits).to_json(out / "session-audit.jsonl", orient="records", lines=True)
    summary = summarize(frame)
    selection = json.loads((out / "locked-selection.json").read_text())
    summary["selection"] = selection
    summary["session_counts"] = (
        pd.DataFrame(audits).groupby("period").status.value_counts().to_dict()
    )
    summary["session_counts"] = {"|".join(k): int(v) for k, v in summary["session_counts"].items()}
    summary["benchmark"] = {"policy": "cash/no trade", "pnl": 0, "exposure": 0}
    write_json(out / "summary.json", summary)
    unique = {r["path"]: r for r in inputs}
    if sha(Path(__file__)) != source_sha_start:
        raise ValueError("Source changed during run; evidence needs explicit review")
    manifest = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": " ".join(sys.argv),
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
        "source_sha_start": source_sha_start,
        "source_sha_end": sha(Path(__file__)),
        "python": sys.version,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "source": {
            str(Path(__file__).resolve()): sha(Path(__file__)),
            str(DAILY): sha(DAILY),
            str(RECEIPT): sha(RECEIPT),
            str(cal.path): sha(cal.path),
            str(ARCHIVE / "catalog.jsonl"): sha(ARCHIVE / "catalog.jsonl"),
        },
        "settlement_source_url": "https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv",
        "quote_files": list(unique.values()),
        "outputs": {p.name: sha(p) for p in out.iterdir() if p.is_file()},
    }
    write_json(out / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "out": str(out),
                "rows": len(frame),
                "selection": selection["policy"],
                "session_counts": summary["session_counts"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.out, args.workers)
