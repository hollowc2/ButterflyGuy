"""Midpoint, marketable and stressed-marketable fills for one butterfly trade.

These are the 2026-09-21 accounting models, identical to
`backtest/execution_accounting.py` (whose constants are imported, not copied):

- midpoint: entry at the fly mark plus commission on four contracts; an intraday exit at
  the mark minus commission, floored at 0.05 as `SimulationParams.paper_exit_price`
  does; cash settlement is free.
- marketable: entry buys the outer legs at ask and sells two centers at bid, at the
  snapshot recorded at or before the decision; an exit uses the inverse sides. If the
  exit snapshot is missing or crossed, the exit rolls forward to the next executable
  snapshot, and with none left the fly cash-settles against the official close.
  Cash settlement has no order, commission or stress.
- stressed: marketable with every contract fill $0.05 worse on each executed side.

A missing or crossed entry market leaves the trade unpriced in the executable models;
no quote is ever imputed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from butterfly_guy.backtest.execution_accounting import (
    CONTRACTS_PER_BUTTERFLY,
    STRESSED_LEG_SLIPPAGE,
)
from butterfly_guy.research.market import FlyPath

Model = Literal["midpoint", "marketable", "stressed"]
MODELS: tuple[Model, ...] = ("midpoint", "marketable", "stressed")
MIN_PAPER_EXIT = 0.05
SETTLED = "cash_settled"


@dataclass(frozen=True)
class Costs:
    commission_per_contract: float = 0.65

    @property
    def commission(self) -> float:
        """Per-fly commission for one executed side, in option points."""
        return CONTRACTS_PER_BUTTERFLY * self.commission_per_contract / 100

    @property
    def stress(self) -> float:
        """Per-fly adverse stress for one executed side, in option points."""
        return CONTRACTS_PER_BUTTERFLY * STRESSED_LEG_SLIPPAGE


@dataclass
class Fill:
    """One accounting model's view of a trade (option points per fly)."""

    status: str = "priced"  # priced | missing_entry_market | crossed_entry_market
    entry: float | None = None
    exit: float | None = None
    exit_index: int | None = None
    exit_roll: int = 0  # snapshots skipped rolling the exit forward
    settlement_fallback: bool = False

    @property
    def pnl(self) -> float | None:
        if self.entry is None or self.exit is None:
            return None
        return self.exit - self.entry


@dataclass
class TradeFills:
    fills: dict[str, Fill] = field(default_factory=dict)

    def pnl_dollars(self, model: Model) -> float | None:
        p = self.fills[model].pnl
        return None if p is None else 100.0 * p


def price_trade(
    path: FlyPath,
    *,
    entry_index: int,
    entry_mark: float,
    exit_index: int | None,
    exit_mark: float | None,
    settlement: float | None,
    costs: Costs,
) -> TradeFills:
    """Price one trade whose decisions are already made.

    `entry_index` is the snapshot at or before the entry decision; `exit_index` the
    snapshot at or before the exit decision, or None when the fly is held to settlement
    (then `settlement` must be the cash-settlement value).
    """
    out = TradeFills()
    held = exit_index is None
    if held and settlement is None:
        raise ValueError("a held trade needs its settlement value")

    mid = Fill(entry=entry_mark + costs.commission)
    if held:
        mid.exit = settlement
    else:
        mid.exit = max(MIN_PAPER_EXIT, exit_mark - costs.commission)
        mid.exit_index = exit_index
    out.fills["midpoint"] = mid

    for model in ("marketable", "stressed"):
        stress = costs.stress if model == "stressed" else 0.0
        fill = Fill()
        out.fills[model] = fill
        if path.missing[entry_index]:
            fill.status = "missing_entry_market"
            continue
        if path.crossed[entry_index]:
            fill.status = "crossed_entry_market"
            continue
        fill.entry = float(path.debit[entry_index]) + costs.commission + stress
        if held:
            fill.exit = settlement
            continue
        usable = np.flatnonzero(path.executable[exit_index:])
        if len(usable):
            j = exit_index + int(usable[0])
            fill.exit = float(path.credit[j]) - costs.commission - stress
            fill.exit_index = j
            fill.exit_roll = j - exit_index
        elif settlement is not None:
            fill.exit = settlement
            fill.settlement_fallback = True
            fill.exit_roll = len(path.executable) - exit_index
        else:
            fill.status = "missing_exit_market"
    return out
