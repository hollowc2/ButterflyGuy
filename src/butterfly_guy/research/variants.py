"""Named variant catalog.

Codes follow `docs/research/spx-idea-sweep-2026-09-25/REGISTRY.md` where a variant
already exists there. Definitions are declarative so each has a stable hash for the
registry; changing a rule's parameters or its class source changes the hash.
"""

from __future__ import annotations

import datetime as dt

from butterfly_guy.research.entry import (
    ATMEntry,
    BaselineEntry,
    BothSides,
    FilteredEntry,
    StraddleAnchoredEntry,
)
from butterfly_guy.research.exits import PeakTrailer, StopLoss, TakeProfit, TimeExit
from butterfly_guy.research.holdout import DEVELOPMENT
from butterfly_guy.research.hypotheses import PriorRatioFilter, ReleaseSkipEntry, SigmaPlacedEntry
from butterfly_guy.research.learning import EVRankEntry, EVSelector, FittedFilter
from butterfly_guy.research.simulate import Variant

BASE = BaselineEntry()
STRADDLE = StraddleAnchoredEntry()
H1 = (dt.date(2026, 3, 13), dt.date(2026, 6, 18))  # the idea sweep's first half
EV_RANK = EVRankEntry()


def _late(hh: int, mm: int) -> StraddleAnchoredEntry:
    return StraddleAnchoredEntry(BaselineEntry(start_et=(hh, mm)))

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
        Variant("C1", STRADDLE, "config",
                "Centers anchored on 1.25 x the ATM straddle (chain-implied remaining move) "
                "instead of the VIX move; runtime trailer."),
        Variant("C2", STRADDLE, (), "C1 selection held to settlement."),
        Variant("D3", BothSides(), "config",
                "Both sides: the baseline call fly and the baseline put fly every session "
                "(trailer); session P&L is their sum."),
        Variant("D4", ATMEntry(), (),
                "ATM call fly (center nearest spot, middle width of the VIX bucket), held "
                "to settlement."),
        *[Variant(code, _late(hh, mm), exits, f"Straddle-anchored entry from {hh}:{mm:02d} "
                  f"ET; {'runtime trailer' if exits == 'config' else 'held to settlement'}.")
          for code, (hh, mm), exits in [
              ("T1", (11, 30), "config"), ("T2", (11, 30), ()), ("T3", (13, 0), "config"),
              ("T4", (13, 0), ()), ("T5", (14, 30), "config"), ("T6", (14, 30), ())]],
        Variant("K1", FittedFilter(BASE, "entry_spread_ratio", *H1, if_undefined="keep"),
                "config", "E0, skipping entries whose (ask - mark) / mark exceeds the median "
                "over E0 entries in H1 (fitted on 2026-03-13..2026-06-18)."),
        Variant("G1", EVSelector(10, 0), (),
                "10:00 ET prior-session EV selector over all flies, held to settlement."),
        Variant("G2", EVSelector(13, 0), (), "G1 at 13:00 ET."),
        Variant("R2", FittedFilter(BASE, "vix_straddle_ratio", *H1), "config",
                "E0, skipping entries whose VIX move / (1.25 x ATM straddle) exceeds the "
                "median over E0 entries in H1 (post hoc; fitted on 2026-03-13..2026-06-18)."),
        Variant("R3", EV_RANK, "config",
                "E0 candidate set ranked by prior-session EV instead of the VIX anchor and "
                "reward/risk; runtime trailer (post hoc)."),
        Variant("R4", EV_RANK, (), "R3 held to settlement (post hoc)."),
        # Drafted in next-sweep-preregistration-draft.md; NOT registered, not run on vendor
        # data. The owner decides whether to register them.
        Variant("HSN1", SigmaPlacedEntry(), "config",
                "H-SN1: center at spot +/- 1.58 sigma in the gap direction, width 0.88 sigma "
                "(nearest 5), sigma = 1.25 x the 10:00 ATM straddle; live cost caps, no RR "
                "filter; runtime trailer."),
        Variant("HEV1", ReleaseSkipEntry(BASE), "config",
                "H-EV1: E0, skipping sessions with a CPI, NFP or PCE release scheduled "
                "before 10:00 ET (calendar leakage rule)."),
        Variant("HTS1", PriorRatioFilter(BASE, "vix1d_vix", *DEVELOPMENT), "config",
                "H-TS1: E0, skipping sessions whose prior-session VIX1D/VIX is at or above "
                "its upper tercile over the development period (fitted on "
                "2022-01-03..2024-06-28)."),
    ]
}


def resolve(names: list[str]) -> list[Variant]:
    missing = [n for n in names if n not in CATALOG]
    if missing:
        raise KeyError(f"unknown variants: {', '.join(missing)}; known: {', '.join(CATALOG)}")
    return [CATALOG[n] for n in names]
