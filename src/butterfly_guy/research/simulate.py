"""Run named variants over sessions.

Sessions are the outer loop, in date order: each session is loaded once and every
variant is replayed on it, so paired comparisons see identical data and stateful rules
(which may only learn from earlier sessions) stay leakage-safe.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import inspect
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Literal

from butterfly_guy.research.accounting import Costs, Model, TradeFills, price_trade
from butterfly_guy.research.entry import Entry, EntryRule, RunContext, Session, SessionLoader
from butterfly_guy.research.exits import HELD, INCOMPLETE, ExitRule, config_exit_rules, monitor
from butterfly_guy.research.market import Fly


@dataclass(frozen=True)
class Variant:
    name: str
    entry: EntryRule
    exits: tuple[ExitRule, ...] | Literal["config"] = "config"
    description: str = ""

    def exit_rules(self, ctx: RunContext) -> tuple[ExitRule, ...]:
        return config_exit_rules(ctx.config) if self.exits == "config" else self.exits

    def definition(self) -> dict:
        """Canonical, JSON-able definition (rule classes, parameters, rule source hashes)."""
        exits = "config" if self.exits == "config" else [_describe(r) for r in self.exits]
        return {"name": self.name, "entry": _describe(self.entry), "exits": exits,
                "description": self.description}

    def definition_hash(self) -> str:
        body = {k: v for k, v in self.definition().items() if k not in {"name", "description"}}
        return hashlib.sha256(canonical_json(body).encode()).hexdigest()


def _describe(obj: object) -> dict:
    cls = type(obj)
    params = asdict(obj) if is_dataclass(obj) else {}
    try:
        source = inspect.getsource(cls)
    except (OSError, TypeError):
        source = cls.__qualname__
    return {"rule": f"{cls.__module__}.{cls.__qualname__}", "params": params,
            "source_sha256": hashlib.sha256(source.encode()).hexdigest()}


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


@dataclass
class Trade:
    date: dt.date
    variant: str
    fly: Fly
    entry_ts_us: int
    entry_index: int
    entry_cost: float
    vix: float | None
    spot: float | None
    tag: str
    exit_reason: str
    exit_ts_us: int | None
    exit_index: int | None
    exit_value: float | None
    peak: float
    settlement: float | None
    fills: TradeFills

    def pnl(self, model: Model) -> float | None:
        return self.fills.pnl_dollars(model)

    def status(self, model: Model) -> str:
        return self.fills.fills[model].status

    def stressed_debit(self) -> float | None:
        f = self.fills.fills["stressed"]
        return None if f.entry is None else 100.0 * f.entry


@dataclass
class VariantRun:
    variant: Variant
    trades: list[Trade] = field(default_factory=list)
    excluded: dict[dt.date, str] = field(default_factory=dict)  # data exclusions


@dataclass
class RunResult:
    dates: list[dt.date]
    runs: dict[str, VariantRun]
    skipped: dict[dt.date, str]


def simulate_entry(s: Session, ctx: RunContext, e: Entry, rules: tuple[ExitRule, ...],
                   variant: str, costs: Costs) -> Trade | str:
    """Replay one entry to its exit and price it; returns a data-exclusion reason instead
    when the replay cannot be completed without imputing data."""
    path = s.market.fly_path(e.fly)
    if path is None:
        return "fly_not_listed"
    entry_price = e.cost + costs.commission
    decision = monitor(date=s.date, clock_ts=s.clock_ts, snapshot_ts=s.market.ts, path=path,
                       entry_ts_us=e.ts_us, entry_price=entry_price, rules=rules)
    if decision.reason == INCOMPLETE:
        return INCOMPLETE
    settlement = e.fly.settlement_value(s.close) if s.close is not None else None
    held = decision.reason == HELD
    if held and settlement is None:
        return "missing_settlement"
    fills = price_trade(
        path, entry_index=e.index, entry_mark=e.cost,
        exit_index=None if held else decision.index,
        exit_mark=decision.value, settlement=settlement, costs=costs,
    )
    peak = max(decision.peak, settlement) if held else decision.peak
    return Trade(
        date=s.date, variant=variant, fly=e.fly, entry_ts_us=e.ts_us, entry_index=e.index,
        entry_cost=e.cost, vix=e.vix, spot=e.spot, tag=e.tag, exit_reason=decision.reason,
        exit_ts_us=decision.ts_us, exit_index=decision.index, exit_value=decision.value,
        peak=peak, settlement=settlement, fills=fills,
    )


def entries_for(s: Session, ctx: RunContext, rule: EntryRule) -> list[Entry]:
    """Entries are cached per session and (hashable) rule, so variants sharing an entry
    rule share the exact same decisions."""
    key = ("entries", rule)
    if key not in s.cache:
        s.cache[key] = rule.entries(s, ctx)
    return s.cache[key]


def run_variants(
    loader: SessionLoader,
    variants: list[Variant],
    ctx: RunContext,
    *,
    start: dt.date | None = None,
    end: dt.date | None = None,
    costs: Costs | None = None,
) -> RunResult:
    costs = costs or Costs(ctx.config.execution.paper_commission_per_contract)
    dates = loader.dates(start, end)
    runs = {v.name: VariantRun(v) for v in variants}
    rules = {v.name: v.exit_rules(ctx) for v in variants}
    evaluated = []
    for d in dates:
        s = loader.load(d)
        if s is None:
            continue
        evaluated.append(d)
        for v in variants:
            for e in entries_for(s, ctx, v.entry):
                out = simulate_entry(s, ctx, e, rules[v.name], v.name, costs)
                if isinstance(out, str):
                    runs[v.name].excluded[d] = out
                else:
                    runs[v.name].trades.append(out)
    skipped = {d: r for d, r in loader.skipped.items() if (not start or d >= start)
               and (not end or d <= end)}
    return RunResult(dates=evaluated, runs=runs, skipped=skipped)
