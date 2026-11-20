"""Monitor cadence and exit-confirmation study (pre-registered in
docs/research/monitor-cadence-exit-design-plan.md, commit 3f2a43e).

The live position monitor values the fly from REST polls (about 2.6 s on direct data) and
stores each poll's three legs in `monitoring_leg_quotes`. This replays the runtime
`PeakTrailer` (research.exits, the same rule code and config) over the stored polls of
closed SPX trades, for the current rule (A0) and each pre-registered arm (Amendment 1:
selection on qualifying post-exit trades 1-30, confirmation on 31-60):

- time-based confirmation: exit once the value has stayed beyond the threshold for T s;
- quality peak: the peak follows the causal median of the last W s of fly marks;
- leg filter: drop polls with a crossed leg or a leg-spread blowout;
- diagnostics: decision cadence by subsampling, 2/3-poll confirmation, median on both.

Each exit is priced at mid, at the fly's natural credit, and at the live exit ladder's first
step, min(mid, natural + 0.30) (the primary model). After the recorded exit an arm still
holding continues on post-exit polls (`post_exit_leg_quotes`). Only the exploratory pilot
set (Aug-Nov 2026) falls back to 1-minute collector snapshots, and says so; the development
and confirmation sets refuse them.

Input: a directory with trades.csv.gz, polls.csv.gz, minute.csv.gz and optionally
post_exit.csv.gz, extracted with the SQL in the plan (section 1). Reads only those files.

    uv run python tools/research_studies/monitor_replay_study.py --data DIR --set pilot
    uv run python tools/research_studies/monitor_replay_study.py --data DIR --set dev
    uv run python tools/research_studies/monitor_replay_study.py --data DIR \
        --set confirmation --arm C2      # once, after 60 qualifying trades
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from butterfly_guy.research.entry import load_spx_config
from butterfly_guy.research.evaluate import block_bootstrap_indices
from butterfly_guy.research.exits import Observation, PeakTrailer

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "reports/research/spx-monitor-cadence-exit"
ET = ZoneInfo("America/New_York")
COMMISSION = 4 * 1.15 / 100  # per fly side, points (paper_commission_per_contract)
LADDER_OFFSET = 0.30  # live execute_exit first step: natural + (steps - 1) x 0.10
LEG_SPREAD_FLOOR, LEG_SPREAD_MULT, LEG_HISTORY = 0.50, 4.0, 30
MATCH_SECONDS = 10.0
PILOT_START, PILOT_END = dt.date(2026, 8, 1), dt.date(2026, 11, 16)
POST_EXIT_START, SET_TRADES = dt.date(2026, 11, 17), 30
MAX_POST_EXIT_GAP = 30.0
BOOT_REPS, BOOT_BLOCK, BOOT_SEED = 5000, 5, 20261117
NI_MARGIN, WORST_TRADE = -20.0, -300.0  # $ per 1-lot
PRICING = ("mid", "natural", "ladder")


@dataclasses.dataclass(frozen=True)
class Arm:
    confirm_seconds: float = 0.0
    peak_window_seconds: float = 0.0
    value_window_seconds: float = 0.0
    leg_filter: bool = False
    cadence_seconds: float = 0.0
    confirmation_polls: int = 1


PRIMARY = {
    "C1": Arm(confirm_seconds=5),
    "C2": Arm(confirm_seconds=10),
    "C3": Arm(confirm_seconds=20),
    "C4": Arm(peak_window_seconds=10),
    "C5": Arm(peak_window_seconds=10, confirm_seconds=10),
    "C6": Arm(leg_filter=True),
}
DIAGNOSTIC = {
    **{f"cad{c}": Arm(cadence_seconds=c) for c in (5, 10, 15, 30, 60)},
    "conf2": Arm(confirmation_polls=2),
    "conf3": Arm(confirmation_polls=3),
    "med10both": Arm(peak_window_seconds=10, value_window_seconds=10),
}
ARMS = {"A0": Arm(), **PRIMARY, **DIAGNOSTIC}


def legs_wide(df: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    """One row per (trade, ts) with lower/center/upper bid/ask/mark."""
    t = trades.set_index("id")
    df = df.join(t[["lower_strike", "center_strike", "upper_strike"]], on="trade_id")
    df["leg"] = np.select(
        [df.strike == df.lower_strike, df.strike == df.center_strike,
         df.strike == df.upper_strike], ["lo", "ce", "up"], "x")
    df = df[df.leg != "x"]
    w = df.pivot_table(index=["trade_id", "ts"], columns="leg",
                       values=["bid", "ask", "mark"], aggfunc="last")
    w.columns = [f"{leg}_{f}" for f, leg in w.columns]
    spot = df.groupby(["trade_id", "ts"]).spot_price.last()
    w = w.join(spot).reset_index().dropna(subset=[f"{x}_{f}" for x in ("lo", "ce", "up")
                                                  for f in ("bid", "ask", "mark")])
    w["mark"] = w.lo_mark + w.up_mark - 2 * w.ce_mark
    w["credit"] = w.lo_bid + w.up_bid - 2 * w.ce_ask
    for x in ("lo", "ce", "up"):
        w[f"{x}_spr"] = w[f"{x}_ask"] - w[f"{x}_bid"]
    return w.sort_values(["trade_id", "ts"])


def leg_filter_ok(p: pd.DataFrame) -> np.ndarray:
    """Causal: reject a poll when any leg is crossed or its spread exceeds
    max(floor, mult x median of that leg's previous accepted spreads)."""
    ok = np.ones(len(p), bool)
    hist: dict[str, list[float]] = {"lo": [], "ce": [], "up": []}
    for i, row in enumerate(p.itertuples(index=False)):
        bad = False
        for x in ("lo", "ce", "up"):
            s = getattr(row, f"{x}_spr")
            if s < 0:
                bad = True
            elif len(hist[x]) >= 5:
                if s > max(LEG_SPREAD_FLOOR, LEG_SPREAD_MULT * float(np.median(hist[x]))):
                    bad = True
        ok[i] = not bad
        if not bad:
            for x in ("lo", "ce", "up"):
                hist[x] = (hist[x] + [getattr(row, f"{x}_spr")])[-LEG_HISTORY:]
    return ok


def to_us(ts: pd.Series) -> np.ndarray:
    return ts.dt.as_unit("us").astype("int64").to_numpy()


def subsample(ts_us: np.ndarray, seconds: float) -> np.ndarray:
    """Keep a poll only once `seconds` have passed since the last kept poll."""
    keep = np.zeros(len(ts_us), bool)
    last = None
    for i, t in enumerate(ts_us):
        if last is None or t - last >= seconds * 1e6:
            keep[i], last = True, t
    return keep


def causal_median(ts_us: np.ndarray, values: np.ndarray, seconds: float) -> np.ndarray:
    """Median of the values in (t - seconds, t] at each t."""
    if seconds <= 0 or not len(values):
        return values
    s = pd.Series(values, index=pd.to_datetime(ts_us, unit="us"))
    return s.rolling(f"{int(seconds * 1000)}ms").median().to_numpy(float)


def exit_prices(value: float, credit: float) -> dict[str, float]:
    natural = max(float(credit), 0.0)
    return {"mid": value, "natural": natural,
            "ladder": min(value, max(0.05, float(credit) + LADDER_OFFSET))}


def decide(ts_us: np.ndarray, marks: np.ndarray, credits: np.ndarray, *, entry: float,
           entry_us: int, open_us: int, close_us: int, rule: PeakTrailer,
           arm: Arm) -> dict | None:
    """First exit of `arm` over an already filtered observation sequence, else None.

    Time-based confirmation: the rule (run at one-poll confirmation) must report the same
    reason on every observation since the first breach, for at least `confirm_seconds`.
    """
    rule = dataclasses.replace(rule, confirmation_polls=arm.confirmation_polls)
    peak_in = causal_median(ts_us, marks, arm.peak_window_seconds)
    value_in = causal_median(ts_us, marks, arm.value_window_seconds)
    memo: dict = {}
    peak = entry
    breach: tuple[str, int] | None = None
    for ts, raw, v, pv, credit in zip(ts_us, marks, value_in, peak_in, credits, strict=True):
        if ts > close_us or not np.isfinite(v):
            continue
        value = max(0.0, float(v))
        peak = max(peak, max(0.0, float(pv)))
        obs = Observation(ts_us=int(ts), minutes_since_open=(ts - open_us) / 60e6,
                          minutes_to_close=(close_us - ts) / 60e6,
                          entry_age_minutes=(ts - entry_us) / 60e6,
                          value=value, peak=peak, entry_price=entry)
        why = rule.reason(obs, memo)
        if why is None:
            breach = None
            continue
        if breach is None or breach[0] != why:
            breach = (why, int(ts))
        if ts - breach[1] >= arm.confirm_seconds * 1e6:
            # Priced at the poll's own mark: a smoothed value triggers, the market fills.
            return {"reason": why, "ts_us": int(ts), "peak": peak,
                    "value": max(0.0, float(raw)), "credit": float(credit)}
    return None


def settlement(tr, spot: float) -> float:
    lo, ce, up = tr.lower_strike, tr.center_strike, tr.upper_strike
    if tr.direction == "PUT":
        v = max(lo - spot, 0) - 2 * max(ce - spot, 0) + max(up - spot, 0)
    else:
        v = max(spot - lo, 0) - 2 * max(spot - ce, 0) + max(spot - up, 0)
    return max(0.0, v)


def session_bounds(tr) -> tuple[int, int, int]:
    d = pd.Timestamp(tr.entry_time).tz_convert(ET).date()
    us = lambda h, m: int(dt.datetime(d.year, d.month, d.day, h, m, tzinfo=ET)  # noqa: E731
                          .timestamp() * 1e6)
    return pd.Timestamp(tr.entry_time).value // 1000, us(9, 30), us(16, 0)


def replay(tr, polls: pd.DataFrame, cont: pd.DataFrame, cont_src: str, rule: PeakTrailer,
           arm: Arm) -> dict:
    """Replay one arm over the recorded polls, then the continuation after them."""
    entry_us, open_us, close_us = session_bounds(tr)
    last_poll = polls.ts.iloc[-1].value // 1000
    cont = cont[to_us(cont.ts) > last_poll] if len(cont) else cont
    seq = pd.concat([polls.assign(src="poll"), cont.assign(src=cont_src)], ignore_index=True)
    ts = to_us(seq.ts)
    keep = np.ones(len(seq), bool)
    if arm.leg_filter:
        keep &= leg_filter_ok(seq)
    if arm.cadence_seconds:
        keep &= subsample(ts, arm.cadence_seconds)
    seq, ts = seq[keep].reset_index(drop=True), ts[keep]
    entry = float(tr.entry_price)
    hit = decide(ts, seq.mark.to_numpy(float), seq.credit.to_numpy(float), entry=entry,
                 entry_us=entry_us, open_us=open_us, close_us=close_us, rule=rule, arm=arm)
    if hit is not None:
        src = seq.src.iloc[int(np.searchsorted(ts, hit["ts_us"]))]
        px = exit_prices(hit["value"], hit["credit"])
        return {"reason": hit["reason"], "ts_us": hit["ts_us"], "src": src,
                "peak": hit["peak"], "exit_mark": hit["value"],
                **{f"pnl_{k}": v - entry - COMMISSION for k, v in px.items()}}
    s = settlement(tr, float(seq.spot_price.iloc[-1]))
    return {"reason": "cash_settled", "ts_us": None, "src": "settle", "peak": None,
            "exit_mark": s, **{f"pnl_{k}": s - entry for k in PRICING}}


def post_exit_covered(tr, pe: pd.DataFrame) -> bool:
    """Post-exit polls from the recorded exit to the close with no gap over 30 s."""
    if tr.exit_reason == "cash_settled":
        return True
    if not len(pe):
        return False
    _, _, close_us = session_bounds(tr)
    ts = np.r_[pd.Timestamp(tr.exit_time).value // 1000,
               to_us(pe.ts)]
    return bool(np.diff(ts).max() <= MAX_POST_EXIT_GAP * 1e6
                and close_us - ts[-1] <= MAX_POST_EXIT_GAP * 1e6)


def spike_peak(p: pd.DataFrame) -> bool:
    """Is the raw peak poll an isolated spike vs its +/-3 neighbours?"""
    m = p.mark.to_numpy(float)
    if len(m) < 7:
        return False
    i = int(np.nanargmax(m))
    nb = np.r_[m[max(0, i - 3):i], m[i + 1:i + 4]]
    ref = float(np.nanmax(nb)) if len(nb) else m[i]
    return bool(m[i] - ref > max(0.30, 0.15 * ref))


def paired(diff: np.ndarray, idx: np.ndarray) -> dict:
    boot = diff[idx].mean(axis=1) if len(diff) else np.zeros(1)
    return {"n": len(diff), "mean": round(float(diff.mean()), 2) if len(diff) else None,
            "ci95": [round(float(np.percentile(boot, q)), 1) for q in (2.5, 97.5)],
            "lower90_one_sided": round(float(np.percentile(boot, 10)), 1),
            "worst": round(float(diff.min()), 1) if len(diff) else None,
            "total": round(float(diff.sum()))}


def arm_summary(m: pd.DataFrame, name: str) -> dict:
    out: dict = {}
    idx = block_bootstrap_indices(len(m), BOOT_REPS, BOOT_BLOCK, seed=BOOT_SEED)
    for k in PRICING:
        diff = (m[f"{name}_pnl_{k}"] - m[f"A0_pnl_{k}"]).to_numpy(float) * 100
        out[k] = paired(diff, idx)
    held = lambda c: m[c].fillna(m.close_us)  # noqa: E731
    hold = (held(f"{name}_ts_us") - held("A0_ts_us")) / 60e6
    changed = hold != 0
    out["exits_changed"] = int(changed.sum())
    out["hold_change_min"] = {"median_changed": round(float(hold[changed].median()), 2)
                              if changed.any() else 0.0,
                              "max": round(float(hold.max()), 1)}
    out["held_to_settle"] = int((m[f"{name}_reason"] == "cash_settled").sum())
    out["continued_on_minute_data"] = int((m[f"{name}_src"] == "minute").sum())
    clean = m[(m[f"{name}_src"] != "minute") & (m["A0_src"] != "minute")]
    if len(clean) < len(m):
        cidx = block_bootstrap_indices(len(clean), BOOT_REPS, BOOT_BLOCK, seed=BOOT_SEED)
        out["ladder_without_minute_continuation"] = paired(
            (clean[f"{name}_pnl_ladder"] - clean["A0_pnl_ladder"]).to_numpy(float) * 100, cidx)
    for col, groups in (("era", ("Aug-Sep", "Oct-Nov")),
                        ("a0_regime", ("morning", "late_morning", "afternoon", "settled"))):
        out[f"by_{col}"] = {}
        for g in groups:
            s = m[m[col] == g]
            d = (s[f"{name}_pnl_ladder"] - s["A0_pnl_ladder"]).to_numpy(float) * 100
            out[f"by_{col}"][g] = {"n": len(s), "mean": round(float(d.mean()), 1) if len(s)
                                   else None, "total": round(float(d.sum()))}
    return out


def select_arm(summary: dict) -> str | None:
    """Plan section 4, step 1: dev mean >= 0 under all three prices, best ladder mean."""
    ok = {a: summary[a]["ladder"]["mean"] for a in PRIMARY
          if all(summary[a][k]["mean"] >= 0 for k in PRICING)}
    return max(ok, key=ok.get) if ok else None


def confirm(s: dict) -> dict:
    """Plan section 4, step 2, for the one selected arm."""
    checks = {"mean_ge_0": s["ladder"]["mean"] >= 0,
              "lower90_gt_margin": s["ladder"]["lower90_one_sided"] > NI_MARGIN,
              "worst_trade_ge_limit": s["ladder"]["worst"] >= WORST_TRADE,
              "natural_mean_ge_0": s["natural"]["mean"] >= 0}
    return {"checks": checks, "adopt": all(checks.values())}


def changed_trades(m: pd.DataFrame, name: str) -> list[dict]:
    rows = []
    for r in m.itertuples(index=False):
        a0, arm = getattr(r, "A0_ts_us"), getattr(r, f"{name}_ts_us")
        if (pd.isna(a0) and pd.isna(arm)) or a0 == arm:
            continue
        hhmm = lambda us: "settle" if pd.isna(us) else pd.Timestamp(  # noqa: E731
            int(us), unit="us", tz="UTC").tz_convert(ET).strftime("%H:%M:%S ET")
        rows.append({"trade_id": r.trade_id, "date": r.date,
                     "A0": f"{hhmm(a0)} @ {r.A0_exit_mark:.2f}",
                     name: f"{hhmm(arm)} @ {getattr(r, f'{name}_exit_mark'):.2f}",
                     "ladder_diff": round((getattr(r, f"{name}_pnl_ladder")
                                           - r.A0_pnl_ladder) * 100, 1)})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--set", choices=("pilot", "dev", "confirmation"), required=True)
    ap.add_argument("--arm", choices=sorted(PRIMARY),
                    help="the dev-selected arm (required with --set confirmation)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()
    conf = a.set == "confirmation"
    post_exit_only = a.set != "pilot"
    # Qualifying post-exit trades in date order: 1-30 develop, 31-60 confirm.
    skip = SET_TRADES if conf else 0
    if conf and not a.arm:
        ap.error("--set confirmation needs --arm (the dev-selected arm)")
    trades = pd.read_csv(a.data / "trades.csv.gz", parse_dates=["entry_time", "exit_time"])
    trades["trade_date"] = pd.to_datetime(trades.trade_date).dt.date
    lo, hi = (POST_EXIT_START, dt.date.max) if post_exit_only else (PILOT_START, PILOT_END)
    trades = trades[(trades.trade_date >= lo) & (trades.trade_date <= hi)]
    trades = trades.sort_values(["trade_date", "id"])
    if trades.empty:
        sys.exit(f"no {a.set} trades in the extraction yet")
    polls = legs_wide(pd.read_csv(a.data / "polls.csv.gz", parse_dates=["ts"]), trades)
    post_path = a.data / "post_exit.csv.gz"
    post = (legs_wide(pd.read_csv(post_path, parse_dates=["ts"]), trades)
            if post_path.exists() else polls.iloc[0:0])
    # The confirmation set never reads 1-minute data.
    minute = (polls.iloc[0:0] if post_exit_only else
              legs_wide(pd.read_csv(a.data / "minute.csv.gz", parse_dates=["ts"]), trades))
    rule = PeakTrailer.from_config(load_spx_config())
    arms = {"A0": ARMS["A0"], a.arm: ARMS[a.arm]} if conf else ARMS

    rows, excluded = [], {"few_polls": 0, "no_match": 0, "post_exit_gap": 0}
    for tr in trades.itertuples(index=False):
        p = polls[polls.trade_id == tr.id].reset_index(drop=True)
        if len(p) < 10:
            excluded["few_polls"] += 1
            continue
        pe = post[post.trade_id == tr.id].reset_index(drop=True)
        if post_exit_only and not post_exit_covered(tr, pe):
            excluded["post_exit_gap"] += 1
            continue
        if len(pe):
            cont, src = pe, "post_exit"
        else:
            cont, src = minute[minute.trade_id == tr.id].reset_index(drop=True), "minute"
        entry_us, open_us, close_us = session_bounds(tr)
        row = {"trade_id": tr.id, "date": str(tr.trade_date), "entry": tr.entry_price,
               "db_reason": tr.exit_reason, "db_exit": str(tr.exit_time), "polls": len(p),
               "close_us": close_us, "peak_spike": spike_peak(p),
               "era": "Aug-Sep" if tr.trade_date < dt.date(2026, 10, 1) else "Oct-Nov",
               "a0_regime": ("settled" if tr.exit_reason == "cash_settled"
                             else tr.exit_reason.removeprefix("drawdown_"))}
        for name, arm in arms.items():
            r = replay(tr, p, cont, src, rule, arm)
            row.update({f"{name}_{k}": v for k, v in r.items()})
        db_us = pd.Timestamp(tr.exit_time).value // 1000 if pd.notna(tr.exit_time) else None
        matched = row["A0_reason"] == tr.exit_reason and (
            row["A0_ts_us"] is None if tr.exit_reason == "cash_settled"
            else abs(row["A0_ts_us"] - db_us) <= MATCH_SECONDS * 1e6)
        if not matched:
            excluded["no_match"] += 1
            continue
        if skip:
            skip -= 1
            continue
        rows.append(row)
        if post_exit_only and len(rows) == SET_TRADES:
            break
    m = pd.DataFrame(rows)
    out = a.out / a.set
    out.mkdir(parents=True, exist_ok=True)
    s: dict = {"set": a.set, "window": [str(lo), None if post_exit_only else str(hi)],
               "trades_used": len(m), "excluded": excluded,
               "arms": {k: dataclasses.asdict(v) for k, v in arms.items()},
               "request_load_per_min": {k: round(60 / (v.cadence_seconds or 2.6), 1)
                                        for k, v in arms.items()}}
    if post_exit_only and len(m) < SET_TRADES:
        # Counts only: a partial set's results are never written or printed.
        s["status"] = f"NOT RUN: {len(m)} of {SET_TRADES} qualifying trades in this set"
        (out / "summary.json").write_text(json.dumps(s, indent=2))
        print(json.dumps(s, indent=2))
        return
    m.to_csv(out / "trades.csv", index=False)
    s["peak_is_one_poll_spike"] = int(m.peak_spike.sum())
    for name in arms:
        if name != "A0":
            s[name] = arm_summary(m, name)
    a0 = m[[f"A0_pnl_{k}" for k in PRICING]].sum() * 100
    s["A0_totals"] = {k: round(float(a0[f"A0_pnl_{k}"])) for k in PRICING}
    chosen = a.arm if conf else select_arm(s)
    s["selected_arm"] = chosen
    if chosen:
        s["changed_trades"] = changed_trades(m, chosen)
    if conf:
        s["decision"] = confirm(s[chosen])
    (out / "summary.json").write_text(json.dumps(s, indent=2, default=str))
    print(json.dumps(s, indent=2, default=str))


if __name__ == "__main__":
    main()
