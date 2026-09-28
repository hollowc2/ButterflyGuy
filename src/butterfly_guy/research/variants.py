"""Named variant catalog.

Codes follow `docs/research/spx-idea-sweep-2026-09-25/REGISTRY.md` where a variant
already exists there. Definitions are declarative so each has a stable hash for the
registry; changing a rule's parameters or its class source changes the hash.
"""

from __future__ import annotations

from butterfly_guy.research.entry import BaselineEntry, FilteredEntry
from butterfly_guy.research.exits import PeakTrailer, StopLoss, TakeProfit, TimeExit
from butterfly_guy.research.simulate import Variant

BASE = BaselineEntry()

CATALOG: dict[str, Variant] = {
    v.name: v
    for v in [
        Variant("E0", BASE, "config",
                "Frozen baseline: gap direction, VIX-anchored live selection in the "
                "configured window, runtime peak trailer, else cash settlement."),
        Variant("X1", BASE, (), "E0 entries held to settlement (no intraday exit)."),
        Variant("X2", BASE, (TakeProfit(3.0),), "E0 entries; take profit at mark >= 3x "
                "entry, else settle."),
        Variant("X3", BASE, (TakeProfit(2.0),), "E0 entries; take profit at mark >= 2x "
                "entry, else settle."),
        Variant("X4", BASE, (StopLoss(0.5),), "E0 entries; stop at mark <= 50% of entry, "
                "else settle."),
        Variant("X5", BASE, (TimeExit(15, 0), PeakTrailer()),
                "E0 entries; 60/90/75 peak trailer, flat at 15:00 ET."),
        Variant("D1", BaselineEntry(direction="momentum"), "config",
                "Momentum direction: CALL if spot at the window start >= session open."),
        Variant("D2", BaselineEntry(direction="fade"), "config",
                "Gap fade: the opposite of the baseline direction."),
        Variant("R1", FilteredEntry(BASE, "vix_at_least", (("level", 17.0),)), "config",
                "E0, skipping sessions whose entry VIX is below 17.0 (post hoc)."),
        Variant("R5", FilteredEntry(BASE, "call_only"), "config",
                "E0 call entries only (post hoc)."),
        Variant("HLV1", FilteredEntry(BASE, "skip_low_vix_calls", (("level", 17.0),)),
                "config", "H-LV1: E0, skipping CALL entries when entry VIX is below 17.0."),
    ]
}


def resolve(names: list[str]) -> list[Variant]:
    missing = [n for n in names if n not in CATALOG]
    if missing:
        raise KeyError(f"unknown variants: {', '.join(missing)}; known: {', '.join(CATALOG)}")
    return [CATALOG[n] for n in names]
