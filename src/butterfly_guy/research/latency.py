"""Calibrate the exit-latency stress from recorded paper trades (read-only).

For every closed SPX paper trade with an intraday exit, the live position loop writes one
`monitoring_leg_quotes` snapshot per poll, and on the poll that fires the exit it writes
that snapshot after acting on the signal and then stops. So the trade's last monitoring
timestamp is the chain time of the poll that triggered the exit, and

    latency = butterfly_trades.exit_time - last monitoring timestamp

is the time from trigger to recorded fill. `metadata.pending_exit.signal_time` (recorded
since the pending-exit metadata was added) is reported alongside as a cross-check.
Latencies are converted into collector snapshots with the research dataset: the number
of recorded 0-DTE chain snapshots after the trigger and at or before the fill.

Paper exits fill on a simulated order ladder, so these are lower bounds on live broker
latency. Queries are bounded per session (`trade_date`) and per trade and UTC day, and
run on the read-only `DataSource` used by the export.
"""

from __future__ import annotations

import datetime as dt
import io
import math

import numpy as np
import pandas as pd

from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.export import DataSource, _utc_day, _weekdays


def trades_sql(underlying: str, date: dt.date) -> str:
    return (
        "select id, trade_date, entry_time, exit_time, exit_reason, "
        "metadata->'pending_exit'->>'signal_time' as signal_time "
        f"from butterfly_trades where underlying = '{underlying}' and trade_date = '{date}' "
        "and exit_time is not null and exit_reason is not null "
        "and exit_reason <> 'cash_settled'"
    )


def polls_sql(trade_id: int, date: dt.date) -> str:
    lo, hi = _utc_day(date)
    return (
        "select max(ts) as trigger_ts, min(ts) as first_ts, count(distinct ts) as polls "
        f"from monitoring_leg_quotes where trade_id = {int(trade_id)} "
        f"and ts >= '{lo}' and ts < '{hi}'"
    )


def _csv(data: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(data))


def _us(value: object) -> int | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    ts = pd.Timestamp(value)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return int(ts.value // 1000)


def collect(source: DataSource, start: dt.date, end: dt.date, underlying: str = "SPX"
            ) -> list[dict]:
    """One row per intraday-exited paper trade: trigger poll, fill and signal times (us)."""
    rows = []
    for d in _weekdays(start, end):
        trades = _csv(source.copy_csv(trades_sql(underlying, d)))
        for t in trades.itertuples():
            polls = _csv(source.copy_csv(polls_sql(int(t.id), d)))
            if polls.empty or pd.isna(polls["trigger_ts"][0]):
                continue
            rows.append({
                "trade_id": int(t.id), "date": d.isoformat(), "exit_reason": t.exit_reason,
                "trigger_us": _us(polls["trigger_ts"][0]), "fill_us": _us(t.exit_time),
                "signal_us": _us(t.signal_time), "polls": int(polls["polls"][0]),
                "poll_span_s": (_us(polls["trigger_ts"][0]) - _us(polls["first_ts"][0])) / 1e6,
            })
    return rows


def summarize(rows: list[dict], dataset: Dataset | None = None,
              quantile: float = 0.9) -> dict:
    """Latency distribution in seconds and collector snapshots, and the implied delay."""
    lat = np.array([(r["fill_us"] - r["trigger_us"]) / 1e6 for r in rows])
    sig = np.array([(r["fill_us"] - r["signal_us"]) / 1e6 for r in rows
                    if r["signal_us"] is not None])
    out: dict = {"trades": len(rows)}
    if not len(lat):
        return out
    qs = (0.5, 0.9, 0.99)
    out["latency_s"] = {"min": round(float(lat.min()), 2),
                        **{f"p{int(q * 100)}": round(float(np.quantile(lat, q)), 2)
                           for q in qs}, "max": round(float(lat.max()), 2)}
    if len(sig):
        out["signal_to_fill_s"] = {"n": int(len(sig)),
                                   **{f"p{int(q * 100)}": round(float(np.quantile(sig, q)), 2)
                                      for q in qs}}
    poll = [r["poll_span_s"] / (r["polls"] - 1) for r in rows if r["polls"] > 1]
    out["live_poll_interval_s_median"] = round(float(np.median(poll)), 2) if poll else None
    if dataset is not None:
        sessions = set(dataset.sessions()["date"])
        steps, intervals = [], []
        for r in rows:
            d = dt.date.fromisoformat(r["date"])
            if d not in sessions:
                continue
            ts = dataset.chain(d).ts
            steps.append(int(np.sum((ts > r["trigger_us"]) & (ts <= r["fill_us"]))))
            intervals.append(float(np.median(np.diff(ts))) / 1e6)
        if steps:
            k = np.array(steps)
            out["collector_snapshots_elapsed"] = {
                "n": int(len(k)), "zero": int((k == 0).sum()), "one": int((k == 1).sum()),
                "more": int((k > 1).sum()),
                f"p{int(quantile * 100)}": float(np.quantile(k, quantile))}
            out["collector_interval_s_median"] = round(float(np.median(intervals)), 2)
            out["recommended_exit_delay_snapshots"] = max(1, int(math.ceil(
                np.quantile(k, quantile))))
    return out
