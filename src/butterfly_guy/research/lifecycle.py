"""Single-fly offline lifecycle verification using the existing selector/exit/accounting.

Decisions stay on midpoint cash flows. Executable prices reprice those frozen decisions;
this is not an executable portfolio simulation. No overlapping-position capital model.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, fields

import numpy as np

from butterfly_guy.research.accounting import MODELS, Costs, price_trade
from butterfly_guy.research.entry import BaselineEntry, RunContext, Session, SessionLoader
from butterfly_guy.research.exits import (
    HELD,
    INCOMPLETE,
    MonitorState,
    PreCloseExit,
    config_exit_rules,
    monitor,
)
from butterfly_guy.research.market import FlyPath


def capability_check(required: tuple[str, ...] = ()) -> None:
    supported = {"bid", "ask", "midpoint", "quote_sizes", "observed_bid_ask"}
    missing = {c.lower() for c in required} - supported
    if missing:
        raise ValueError("local archive lacks required capabilities: " + ", ".join(sorted(missing)))


def _legs(s: Session, e, i: int) -> list[dict]:
    t = "C" if e.direction == "CALL" else "P"
    out = []
    for k, quantity in zip((e.fly.lower, e.fly.center, e.fly.upper), (1, -2, 1), strict=True):
        j = s.market.chain.column(k)
        out.append({"root": s.market.chain.option_root, "underlying": s.market.underlying,
                    "expiration": str(s.market.expiration), "strike": k,
                    "right": e.direction, "quantity": quantity,
                    "observation_ts_us": int(s.market.ts[i]),
                    **{f: float(s.market.chain.fields[f"{t}_{f}"][i, j])
                       for f in ("bid", "ask", "mark", "observation_age_s")}})
    return out


def replay_position(loader: SessionLoader, d: dt.date, ctx: RunContext, *, lifecycle: str,
                    expiry_loader: SessionLoader | None = None, end: dt.date | None = None,
                    costs: Costs | None = None, required: tuple[str, ...] = (),
                    entry_rule=None, rules=None) -> dict:
    """One position / one fly; preserves peak and all trailer memo state across sessions.

    Intraday 1-DTE adds a mandatory five-minute preclose exit. Without an observed market
    it remains unresolved. Carry uses entry-day and expiry-day snapshots only, preserving
    elapsed wall time for min-hold rules and local-session time for regime rules.
    """
    capability_check(required)
    if lifecycle not in {"0dte", "intraday", "carry"}:
        raise ValueError("unknown lifecycle")
    if ctx.asset != loader.dataset.manifest.underlying:
        raise ValueError("configuration and dataset underlying mismatch")
    s = loader.load(d)
    if s is None:
        return {"date": str(d), "status": "excluded", "reason": loader.skipped[d]}
    expiration = s.market.expiration
    if (lifecycle == "0dte") != (expiration == d):
        raise ValueError("lifecycle and expiration mismatch")
    entries = (entry_rule or BaselineEntry()).entries(s, ctx)
    if not entries:
        return {"date": str(d), "expiration": str(expiration), "status": "no_trade"}
    e = entries[0]
    costs = costs or Costs(ctx.config.execution.paper_commission_per_contract)
    rules = config_exit_rules(ctx.config) if rules is None else rules
    if lifecycle == "intraday":
        rules = (*rules, PreCloseExit(5))
    state = MonitorState()
    path = s.market.fly_path(e.fly)
    if path is None:
        return {"date": str(d), "status": "excluded", "reason": "fly_not_listed"}
    entry_legs = _legs(s, e, e.index)
    decision = monitor(date=d, clock_ts=s.clock_ts, snapshot_ts=s.market.ts, path=path,
                       entry_ts_us=e.ts_us, entry_price=e.cost + costs.commission,
                       rules=rules, session_close=s.scheduled_close, state=state)
    offset, current, paths = 0, s, [path]
    reason = None
    if decision.reason == INCOMPLETE:
        reason = INCOMPLETE
    elif decision.reason == HELD and lifecycle == "intraday":
        reason = "unresolved_intraday_exit"
    elif decision.reason == HELD and lifecycle == "carry":
        if end is not None and end < expiration:
            reason = "range_ends_before_expiration"
        elif expiry_loader is None:
            reason = "missing_expiration_dataset"
        elif expiration not in expiry_loader.dates(expiration, expiration):
            reason = "missing_expiration_session"
        else:
            current = expiry_loader.load(expiration)
            if current is None:
                reason = expiry_loader.skipped[expiration]
            elif current.market.expiration != expiration or current.market.underlying != ctx.asset:
                raise ValueError("expiry contract identity mismatch")
            else:
                expiry_path = current.market.fly_path(e.fly)
                if expiry_path is None:
                    reason = "missing_expiration_strikes"
                else:
                    offset = len(path.mark)
                    paths.append(expiry_path)
                    decision = monitor(date=expiration, clock_ts=current.clock_ts,
                                       snapshot_ts=current.market.ts, path=expiry_path,
                                       entry_ts_us=e.ts_us, entry_price=e.cost + costs.commission,
                                       rules=rules, session_close=current.scheduled_close,
                                       state=state)
                    if decision.reason == INCOMPLETE:
                        reason = INCOMPLETE
    rec = {"date": str(d), "expiration": str(expiration), "lifecycle": lifecycle,
           "entry_time_us": e.ts_us, "entry_legs": entry_legs,
           "trading_sessions_to_expiry": int(expiration != d),
           "calendar_days_to_expiry": (expiration - d).days,
           "fly": asdict(e.fly), "peak": state.peak, "observations": state.observations,
           "overnight_marks": "unobserved", "quantity": 1,
           "capital_model": "single-fly dollar P&L; no portfolio returns",
           "accounting": "frozen midpoint decisions repriced at observed leg NBBO; "
                         "complex-order fill is an assumption"}
    if reason:
        return {**rec, "status": "unresolved", "reason": reason}
    held = decision.reason == HELD
    settlement = (e.fly.settlement_value(current.close)
                  if current.close is not None and current.date == expiration else None)
    if held and settlement is None:
        return {**rec, "status": "unresolved", "reason": "missing_settlement"}
    combined = FlyPath(**{f.name: np.concatenate([getattr(p, f.name) for p in paths])
                          for f in fields(FlyPath)})
    exit_index = None if held else offset + decision.index
    # One-grid-tick delayed stress, same convention as the research simulator.
    fills = price_trade(combined, entry_index=e.index, entry_mark=e.cost,
                        exit_index=exit_index, exit_mark=decision.value,
                        settlement=settlement, costs=costs,
                        delayed_exit_index=None if held else exit_index + 1)
    execution_legs = {}
    for model in MODELS:
        i = fills.fills[model].exit_index
        execution_legs[model] = [] if i is None else (
            _legs(current, e, i - offset) if i >= offset else _legs(s, e, i))
    rec.update(exit_execution_legs=execution_legs, status="resolved",
               exit_reason=decision.reason, exit_time_us=decision.ts_us,
               settlement=settlement if held else None,
               exit_legs=[] if held else _legs(current, e, decision.index),
               fills={m: {**asdict(fills.fills[m]), "pnl_dollars": fills.pnl_dollars(m),
                          "expiration": str(expiration)} for m in MODELS},
               floor_uses=sum(f.exit_floored for f in fills.fills.values()))
    if any(f.pnl is None for f in fills.fills.values()):
        rec["status"] = "unpriceable"
    return rec
