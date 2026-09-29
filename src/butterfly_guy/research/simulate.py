"""Run named variants over sessions.

Sessions are the outer loop, in date order: each session is loaded once and every
variant is replayed on it, so paired comparisons see identical data. Learning rules get
only earlier sessions' observations, and a session is observed only after every variant
has decided on it (see `learning.py`). Fitted rules are fitted on their own window before
the loop. A session may hold several entries per variant; its P&L is their sum.

Exit latency: every intraday exit is also priced as if it filled `exit_delay` decision-
clock times after the trigger (the `stressed_delayed` model), starting at least that many
recorded snapshots later and rolling forward from there.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import inspect
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np

from butterfly_guy.research.accounting import Costs, Model, TradeFills, price_trade
from butterfly_guy.research.entry import (
    Entry,
    EntryRule,
    RunContext,
    Session,
    SessionLoader,
    cached_entries,
)
from butterfly_guy.research.exits import HELD, INCOMPLETE, ExitRule, config_exit_rules, monitor
from butterfly_guy.research.learning import (
    History,
    LeakageError,
    fit_variant_entry,
    is_fitted,
    is_learning,
)
from butterfly_guy.research.market import Fly

if TYPE_CHECKING:
    from butterfly_guy.research.tieset import TiesetScorer

DEFAULT_EXIT_DELAY = 1  # decision-clock times between an exit trigger and its delayed fill


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
        """Hash of the rule definition. A fitted rule's fitted values are recorded in the
        definition but not hashed: the procedure (window, statistic, feature) is the
        variant, so a registered procedure keeps its identity when it is re-fitted."""
        body = {k: v for k, v in self.definition().items() if k not in {"name", "description"}}
        body["entry"] = {k: v for k, v in body["entry"].items() if k != "fitted"}
        return hashlib.sha256(canonical_json(body).encode()).hexdigest()

    @property
    def fit_window(self) -> tuple[dt.date, dt.date] | None:
        return (self.entry.fit_start, self.entry.fit_end) if is_fitted(self.entry) else None


def _describe(obj: object) -> dict:
    cls = type(obj)
    params = asdict(obj) if is_dataclass(obj) else {}
    try:
        source = inspect.getsource(cls)
    except (OSError, TypeError):
        source = cls.__qualname__
    out = {"rule": f"{cls.__module__}.{cls.__qualname__}", "params": params,
           "source_sha256": hashlib.sha256(source.encode()).hexdigest()}
    fitted = getattr(cls, "FITTED", ())
    if fitted:
        out["fitted"] = {k: params.pop(k) for k in fitted}
    return out


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
    history_n: int | None = None
    history_last: dt.date | None = None

    def pnl(self, model: Model) -> float | None:
        return self.fills.pnl_dollars(model)

    def status(self, model: Model) -> str:
        return self.fills.fills[model].status

    def stressed_debit(self) -> float | None:
        f = self.fills.fills["stressed"]
        return None if f.entry is None else 100.0 * f.entry


@dataclass
class VariantRun:
    variant: Variant  # as run: fitted rules carry their fitted values
    trades: list[Trade] = field(default_factory=list)
    # Data exclusions, first reason per session. Any exclusion drops the whole session
    # from every compared arm, including a multi-entry session's other trades.
    excluded: dict[dt.date, str] = field(default_factory=dict)


@dataclass
class RunResult:
    dates: list[dt.date]
    runs: dict[str, VariantRun]
    skipped: dict[dt.date, str]


def delayed_exit_index(s: Session, trigger_ts_us: int, trigger_index: int, delay: int) -> int:
    """Snapshot where a delayed exit starts looking for a fill: the one at or before the
    decision-clock time `delay` ticks after the trigger, and at least `delay` recorded
    snapshots after the trigger's. At or past the end of the chain when none is left."""
    k = int(np.searchsorted(s.clock_ts, trigger_ts_us, side="left"))
    if k + delay < len(s.clock_ts):
        j = s.market.at_or_before(int(s.clock_ts[k + delay]))
    else:
        j = len(s.market.ts)
    return max(j, trigger_index + delay)


def simulate_entry(s: Session, ctx: RunContext, e: Entry, rules: tuple[ExitRule, ...],
                   variant: str, costs: Costs, exit_delay: int = DEFAULT_EXIT_DELAY
                   ) -> Trade | str:
    """Replay one entry to its exit and price it; returns a data-exclusion reason instead
    when the replay cannot be completed without imputing data."""
    path = s.market.fly_path(e.fly)
    if path is None:
        return "fly_not_listed"
    entry_price = e.cost + costs.commission
    decision = monitor(date=s.date, clock_ts=s.clock_ts, snapshot_ts=s.market.ts, path=path,
                       entry_ts_us=e.ts_us, entry_price=entry_price, rules=rules,
                       session_close=s.scheduled_close)
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
        delayed_exit_index=None if held else delayed_exit_index(
            s, decision.ts_us, decision.index, exit_delay),
    )
    peak = max(decision.peak, settlement) if held else decision.peak
    return Trade(
        date=s.date, variant=variant, fly=e.fly, entry_ts_us=e.ts_us, entry_index=e.index,
        entry_cost=e.cost, vix=e.vix, spot=e.spot, tag=e.tag, exit_reason=decision.reason,
        exit_ts_us=decision.ts_us, exit_index=decision.index, exit_value=decision.value,
        peak=peak, settlement=settlement, fills=fills, history_n=e.history_n,
        history_last=e.history_last,
    )


def entries_for(s: Session, ctx: RunContext, rule: EntryRule,
                histories: dict[object, History] | None = None) -> list[Entry]:
    """Entries are cached per session and (hashable) rule, so variants sharing an entry
    rule share the exact same decisions. A learning rule decides from its history before
    this session only."""
    if not is_learning(rule):
        return cached_entries(s, ctx, rule)
    key = ("entries", rule)
    if key not in s.cache:
        if histories is None or rule not in histories:
            raise LeakageError("a learning rule needs the runner's history")
        s.cache[key] = rule.decide(s, ctx, histories[rule].before(s.date))
    return s.cache[key]


def fit_variants(variants: list[Variant], loader: SessionLoader, ctx: RunContext
                 ) -> list[Variant]:
    """Fit every unfitted rule on its own window (see `learning.WindowedLoader`)."""
    out = []
    for v in variants:
        fitted = fit_variant_entry(v.entry, loader, ctx)
        out.append(v if fitted is v.entry else Variant(v.name, fitted, v.exits, v.description))
    return out


def run_variants(
    loader: SessionLoader,
    variants: list[Variant],
    ctx: RunContext,
    *,
    start: dt.date | None = None,
    end: dt.date | None = None,
    costs: Costs | None = None,
    exit_delay: int = DEFAULT_EXIT_DELAY,
    tieset: TiesetScorer | None = None,
) -> RunResult:
    costs = costs or Costs(ctx.config.execution.paper_commission_per_contract)
    variants = fit_variants(variants, loader, ctx)
    dates = loader.dates(start, end)
    runs = {v.name: VariantRun(v) for v in variants}
    rules = {v.name: v.exit_rules(ctx) for v in variants}
    histories: dict[object, History] = {
        v.entry: History() for v in variants if is_learning(v.entry)}

    def observe(s: Session) -> None:
        for rule, history in histories.items():
            if s.date >= rule.history_start:
                value = rule.observe(s, ctx)
                if value is not None:
                    history.append(s.date, value)

    if histories and dates:
        # Warm-up: observe (never score) sessions from the earliest history start up to
        # the first evaluated session, through a separate loader.
        first = min(rule.history_start for rule in histories)
        if first < dates[0]:
            warm = SessionLoader(loader.dataset, loader.profile, loader.unseal)
            for d in warm.dates(first, dates[0] - dt.timedelta(days=1)):
                s = warm.load(d)
                if s is not None:
                    observe(s)

    evaluated = []
    for d in dates:
        s = loader.load(d)
        if s is None:
            continue
        evaluated.append(d)
        for v in variants:
            for e in entries_for(s, ctx, v.entry, histories):
                out = simulate_entry(s, ctx, e, rules[v.name], v.name, costs, exit_delay)
                if isinstance(out, str):
                    runs[v.name].excluded.setdefault(d, out)
                else:
                    runs[v.name].trades.append(out)
                if tieset is not None:
                    tieset.add(s, ctx, v.name, e, rules[v.name], costs, exit_delay)
        observe(s)  # only after every variant has decided on this session
    skipped = {d: r for d, r in loader.skipped.items() if (not start or d >= start)
               and (not end or d <= end)}
    return RunResult(dates=evaluated, runs=runs, skipped=skipped)
