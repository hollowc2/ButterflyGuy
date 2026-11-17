"""Exit order pricing study (pre-registered in docs/research/exit-ladder-pricing-plan.md).

`extract` reads the Helios DB read-only (research `PostgresSource`) into --data:

- Set A (exploratory selection): SPX trades 2026-08-01..2026-11-16 with monitor polls.
- Set B (confirmation): the first 30 SPX trades from 2026-11-17 with post-exit polls (the
  monitor-cadence study's development trades 1-30). Later trades are never queried.
- Trade 415, the first real-money exit: its signal poll, broker-time quotes and the
  1-minute collector afterwards (illustration only).

`run --set A|B` replays every candidate under every fill model and applies the decision rule.

    uv run python tools/research_studies/exit_ladder_pricing_study.py extract --data DIR
    uv run python tools/research_studies/exit_ladder_pricing_study.py run --data DIR --set A
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
from pathlib import Path as FsPath
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from butterfly_guy.research import exit_pricing as ep

ROOT = FsPath(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "reports/research/exit-ladder-pricing"
PT = ZoneInfo("America/Los_Angeles")
SET_A = (dt.date(2026, 8, 1), dt.date(2026, 11, 16))
SET_B_START, SET_B_TRADES = dt.date(2026, 11, 17), 30
HORIZON = {"A": 90.0, "B": 300.0}  # Set A paths end at the trade's real exit
MAX_GAP = 30.0
WIDE = 0.60
LIVE_TRADES = (415,)

TRADE_COLS = (
    "id, trade_date, direction, wing_width, lower_strike, center_strike, upper_strike, "
    "exit_time, exit_reason, (metadata->>'vix')::float as vix"
)


def _csv(data: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(data))


def _polls_sql(table: str, trade_id: int, extra: str = "") -> str:
    dd = ", drawdown_pct" if table == "monitoring_leg_quotes" else ""
    return (f"select trade_id, ts, strike, bid, ask{dd} from {table} "
            f"where trade_id = {int(trade_id)} {extra} order by ts, strike")


def cmd_extract(a: argparse.Namespace) -> None:
    from butterfly_guy.research.export import PostgresSource

    out = FsPath(a.data)
    out.mkdir(parents=True, exist_ok=True)
    src = PostgresSource()
    try:
        trades_a = _csv(src.copy_csv(
            f"select {TRADE_COLS} from butterfly_trades t where underlying = 'SPX' "
            f"and status = 'CLOSED' and trade_date between '{SET_A[0]}' and '{SET_A[1]}' "
            "and exists (select 1 from monitoring_leg_quotes q where q.trade_id = t.id) "
            "order by id"))
        polls = [_csv(src.copy_csv(_polls_sql("monitoring_leg_quotes", i)))
                 for i in trades_a.id]
        trades_a.to_csv(out / "A_trades.csv.gz", index=False)
        pd.concat(polls).to_csv(out / "A_polls.csv.gz", index=False)

        # Set B: never select beyond the first SET_B_TRADES trades with post-exit polls.
        trades_b = _csv(src.copy_csv(
            f"select {TRADE_COLS} from butterfly_trades t where underlying = 'SPX' "
            f"and status = 'CLOSED' and trade_date >= '{SET_B_START}' "
            "and exists (select 1 from post_exit_leg_quotes p where p.trade_id = t.id) "
            f"order by trade_date, id limit {SET_B_TRADES}"))
        sig, post = [], []
        for i in trades_b.id:
            sig.append(_csv(src.copy_csv(_polls_sql(
                "monitoring_leg_quotes", i,
                f"and ts = (select max(ts) from monitoring_leg_quotes where trade_id = {i})"))))
            post.append(_csv(src.copy_csv(_polls_sql("post_exit_leg_quotes", i))))
        trades_b.to_csv(out / "B_trades.csv.gz", index=False)
        cols = ["trade_id", "ts", "strike", "bid", "ask"]
        (pd.concat(sig) if sig else pd.DataFrame(columns=cols)).to_csv(
            out / "B_signal.csv.gz", index=False)
        (pd.concat(post) if post else pd.DataFrame(columns=cols)).to_csv(
            out / "B_post.csv.gz", index=False)

        t415 = _csv(src.copy_csv(f"select {TRADE_COLS} from butterfly_trades where id = 415"))
        sig415 = _csv(src.copy_csv(_polls_sql(
            "monitoring_leg_quotes", 415,
            "and ts = (select max(ts) from monitoring_leg_quotes where trade_id = 415)")))
        minute415 = _csv(src.copy_csv(
            "select 415 as trade_id, s.snapshot_time as ts, s.strike, s.bid, s.ask "
            "from option_chain_snapshots s join butterfly_trades t on t.id = 415 "
            "where s.underlying = 'SPX' and s.expiration = t.trade_date "
            "and s.option_type = t.direction "
            "and s.strike in (t.lower_strike, t.center_strike, t.upper_strike) "
            "and s.snapshot_time > t.exit_time "
            "and s.snapshot_time <= t.exit_time + interval '6 minutes' order by 2, 3"))
        obs415 = _csv(src.copy_csv(
            "select o->>'phase' as phase, o->'quote'->>'received_at' as ts, "
            "(o->'quote'->'spread'->>'bid')::float as bid, "
            "(o->'quote'->'spread'->>'ask')::float as ask "
            "from broker_order_intents, "
            "jsonb_array_elements(candidate_snapshot->'execution_observations') o "
            "where trade_id = 415 and side = 'EXIT'"))
        t415.to_csv(out / "T415_trade.csv", index=False)
        pd.concat([sig415, minute415]).to_csv(out / "T415_legs.csv", index=False)
        obs415.to_csv(out / "T415_broker_quotes.csv", index=False)
        meta = {"extracted_at": dt.datetime.now(dt.UTC).isoformat(), "source": src.describe(),
                "set_a_trades": len(trades_a), "set_b_trades": len(trades_b)}
        (out / "extract.json").write_text(json.dumps(meta, indent=2))
        print(json.dumps(meta, indent=2))
    finally:
        src.close()


def _read(path: FsPath) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df.ts, utc=True, format="ISO8601")
    return df


def _tod(ts: pd.Timestamp) -> str:
    h = ts.tz_convert(PT).hour + ts.tz_convert(PT).minute / 60
    return "<08 PT" if h < 8 else "08-10" if h < 10 else "10-12" if h < 12 else "12-13 PT"


def _vix_bucket(v: float) -> str:
    if not np.isfinite(v):
        return "n/a"
    return "<17" if v < 17 else "17-24.5" if v < 24.5 else ">=24.5"


def build_exits(set_name: str, data: FsPath) -> tuple[list[dict], dict]:
    """One record per usable signal: meta plus its quote path."""
    trades = _read(data / f"{set_name}_trades.csv.gz")
    trades = trades[~trades.id.isin(LIVE_TRADES)]  # live exits are reported, never pooled
    if set_name == "A":
        flies = ep.fly_quotes(_read(data / "A_polls.csv.gz"), trades)
        signals = ep.stand_in_signals(flies)
    else:
        legs = pd.concat([_read(data / "B_signal.csv.gz"), _read(data / "B_post.csv.gz")])
        if legs.empty:
            return [], {"no_trades_yet": True}
        flies = ep.fly_quotes(legs, trades)
        signals = flies.groupby("trade_id", as_index=False).ts.min()
    info = trades.set_index("id")
    horizon = HORIZON[set_name]
    exits, dropped = [], {"gap": 0, "short": 0}
    for row in signals.itertuples(index=False):
        path = ep.path_from(flies[flies.trade_id == row.trade_id], row.ts)
        if path.t[-1] < horizon - MAX_GAP:
            dropped["short"] += 1
            continue
        if ep.max_gap(path, horizon) > MAX_GAP:
            dropped["gap"] += 1
            continue
        t = info.loc[row.trade_id]
        spread = float(np.round((path.mid[0] - path.bid[0]) * 2, 4))
        exits.append({
            "trade_id": int(row.trade_id), "trade_date": str(t.trade_date), "ts": row.ts,
            "era": "Aug-Sep" if str(t.trade_date) < "2026-10-01" else "Oct-Nov",
            "tod": _tod(row.ts), "vix": _vix_bucket(float(t.vix)), "width": int(t.wing_width),
            "spread": spread, "wide": spread > WIDE, "bid0": float(path.bid[0]),
            "mid0": float(path.mid[0]), "path": path,
        })
    return exits, dropped


def score(exits: list[dict], horizon: float) -> pd.DataFrame:
    rows = []
    for e in exits:
        for model, p in ep.FILL_MODELS.items():
            for name, cand in ep.CANDIDATES.items():
                o = ep.simulate(e["path"], cand, p, horizon=horizon)
                rows.append({**{k: v for k, v in e.items() if k != "path"}, "model": model,
                             "cand": name, "credit": o.expected_credit * 100,
                             "p_filled": o.p_filled, "fill_s": o.expected_fill_seconds,
                             "first_limit": o.limits[0]})
    df = pd.DataFrame(rows)
    base = df[df.cand == "R0"].set_index(["trade_id", "ts", "model"]).credit
    df["diff"] = df.credit - df.join(base.rename("base"), on=["trade_id", "ts", "model"]).base
    return df


def _summ(g: pd.DataFrame) -> ep.Summary:
    return ep.summarize(g.trade_date, g["diff"])


def report(df: pd.DataFrame, set_name: str, dropped: dict, out: FsPath) -> dict:
    res: dict = {"set": set_name, "horizon_s": HORIZON[set_name], "dropped": dropped,
                 "n_exits": int(df[(df.cand == "R0") & (df.model == "mid50")].shape[0]),
                 "candidates": {}}
    passing = {}
    for name in ("R2", "R3", "R1"):
        sums = {m: _summ(df[(df.cand == name) & (df.model == m)]) for m in ep.FILL_MODELS}
        crit = ep.qualifies(sums["mid50"], sums["mid100"], sums["touch"])
        crit["5_natural_no_later_than_R0"] = True  # tests/test_exit_pricing.py
        res["candidates"][name] = {
            "summaries": {m: s.__dict__ for m, s in sums.items()}, "criteria": crit,
            "qualifies": all(crit.values())}
        if all(crit.values()):
            passing[name] = sums["mid50"].mean
    res["selected"] = ep.select(passing)

    lines = [f"# Set {set_name}: {res['n_exits']} signals, horizon {HORIZON[set_name]:.0f} s, "
             f"dropped {dropped}", ""]
    lines.append("## Paired difference vs R0, $ per exit (session-block bootstrap)")
    for name in ("R2", "R3", "R1"):
        for m in ep.FILL_MODELS:
            s = res["candidates"][name]["summaries"][m]
            lines.append(f"{name} {m:6s} n={s['n_exits']:4d} sessions={s['n_sessions']:3d} "
                         f"mean={s['mean']:7.2f} lower90={s['lower90']:7.2f} "
                         f"ci95=[{s['ci95'][0]:7.2f},{s['ci95'][1]:7.2f}] "
                         f"worst={s['worst']:8.2f}")
        lines.append(f"   criteria: {res['candidates'][name]['criteria']}")
    lines.append(f"\nSELECTED: {res['selected']}\n")

    prim = df[df.model == "mid50"]
    lines.append("## Expected credit and fill time by candidate (mid50; touch)")
    for m in ("mid50", "touch", "mid100"):
        g = df[df.model == m].groupby("cand", sort=False)
        lines.append(f"[{m}]\n" + g.agg(credit=("credit", "mean"), p_filled=("p_filled", "mean"),
                                        fill_s=("fill_s", "mean")).round(2).to_string())
    for col in ("wide", "era", "tod", "vix"):
        lines.append(f"\n## mid50 mean diff by {col}")
        t = prim[prim.cand != "R0"].pivot_table(index=col, columns="cand", values="diff",
                                                 aggfunc="mean").round(2)
        t["n"] = prim[prim.cand == "R0"].groupby(col).size()
        lines.append(t.to_string())
    lines.append("\n## Touch-model mean diff by spread")
    tt = df[(df.model == "touch") & (df.cand != "R0")]
    lines.append(tt.pivot_table(index="wide", columns="cand", values="diff",
                                aggfunc="mean").round(2).to_string())
    lines.append("\n## Sensitivity (reported only): signals with a negative fly bid removed")
    ok = df[df.bid0 >= 0]
    for name in ("R2", "R3", "R1"):
        for m in ep.FILL_MODELS:
            s = _summ(ok[(ok.cand == name) & (ok.model == m)])
            lines.append(f"{name} {m:6s} n={s.n_exits} mean={s.mean:6.2f} "
                         f"lower90={s.lower90:6.2f}")
    lines.append("\n## Spread at signal")
    sp = prim[prim.cand == "R0"].spread
    lines.append(sp.describe(percentiles=[.5, .75, .9]).round(2).to_string())
    lines.append("\n## 10 signals most affected (|R3 - R0|, mid50)")
    top = prim[prim.cand == "R3"].assign(a=lambda x: x["diff"].abs()).nlargest(10, "a")
    lines.append(top[["trade_id", "trade_date", "tod", "spread", "bid0", "mid0", "diff"]]
                 .round(2).to_string(index=False))
    text = "\n".join(lines)
    (out / f"results_{set_name}.txt").write_text(text)
    (out / f"results_{set_name}.json").write_text(json.dumps(res, indent=2, default=str))
    df.drop(columns=[]).to_csv(out / f"scores_{set_name}.csv.gz", index=False)
    print(text)
    return res


def replay_415(data: FsPath) -> str:
    """Illustration: trade 415 on its sparse real path (signal poll, broker quotes, minutes)."""
    trade = _read(data / "T415_trade.csv")
    legs = _read(data / "T415_legs.csv")
    flies = ep.fly_quotes(legs, trade)[["ts", "bid", "mid"]]
    broker = _read(data / "T415_broker_quotes.csv").dropna().drop_duplicates("ts")
    broker = broker.assign(mid=(broker.bid + broker.ask) / 2)[["ts", "bid", "mid"]]
    q = pd.concat([flies, broker]).sort_values("ts", ignore_index=True)
    # Live step 0 prices on its own fetch (before_submit), not on the signal poll.
    t0 = broker.ts.min()
    q = q[q.ts >= t0]
    path = ep.Path(t=(q.ts - t0).dt.total_seconds().to_numpy(), bid=q.bid.to_numpy(),
                   mid=q.mid.to_numpy())
    lines = ["# Trade 415 replay (sparse path; illustration only)",
             "t_s   bid   mid", *(f"{t:6.1f} {b:5.2f} {m:5.2f}"
                                  for t, b, m in zip(path.t, path.bid, path.mid))]
    for model, p in ep.FILL_MODELS.items():
        for name, cand in ep.CANDIDATES.items():
            o = ep.simulate(path, cand, p, horizon=90)
            lines.append(f"{model:6s} {name}: credit {o.expected_credit:.3f} "
                         f"p_filled {o.p_filled:.2f} limits {o.limits[:5]}")
    return "\n".join(lines)


def cmd_run(a: argparse.Namespace) -> None:
    data = FsPath(a.data)
    exits, dropped = build_exits(a.set, data)
    if not exits:
        print(f"Set {a.set}: no usable signals yet ({dropped}).")
        return
    report(score(exits, HORIZON[a.set]), a.set, dropped, data)
    if a.set == "A" and (data / "T415_trade.csv").exists():
        text = replay_415(data)
        (data / "replay_415.txt").write_text(text)
        print("\n" + text)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(required=True)
    e = sub.add_parser("extract")
    e.add_argument("--data", default=str(DEFAULT_DATA))
    e.set_defaults(func=cmd_extract)
    r = sub.add_parser("run")
    r.add_argument("--data", default=str(DEFAULT_DATA))
    r.add_argument("--set", choices=("A", "B"), required=True)
    r.set_defaults(func=cmd_run)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
