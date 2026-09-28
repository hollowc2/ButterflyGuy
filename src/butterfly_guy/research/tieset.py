"""Robustness to fly choice: score every near-tied fly the selector could have picked.

The live selector takes the candidate whose reward/risk is nearest the target, so a
few cents of mark can flip the chosen width or center. At each entry decision this
rebuilds the selector's candidate pools (per-width center tolerance around the VIX
target, then the rr_max filter) and keeps every candidate that a combined mark shift of
at most `threshold` option points could promote over the winner. The required shift is
the gap in reward/risk distance divided by both flies' reward/risk sensitivity to cost
(width / cost^2), as in the journal's 2026-09-25 "Robustness to fly choice" method.

Each tied fly is replayed with the variant's own exits from the same entry snapshot.
Per session the tie-set average is the mean over tied flies; random draws pick one tied
fly per session uniformly, with the draw keyed by (session, direction) so every rule
sees the same draw for the same session and side (paired across rules).

`TiesetScorer` is fed from the main replay loop (no second pass over the data). Rules
whose entries do not come from the live selector (for example the EV learners and the
ATM fly) have no tie set and are reported as not applicable.
"""

from __future__ import annotations

import datetime as dt
import zlib

import numpy as np

from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.research.accounting import Costs, Model
from butterfly_guy.research.entry import Entry, RunContext, Session, selection_span
from butterfly_guy.research.exits import ExitRule
from butterfly_guy.research.market import Fly
from butterfly_guy.research.simulate import Trade, simulate_entry
from butterfly_guy.strategy.butterfly_builder import vix_target_center
from butterfly_guy.strategy.entry_selection import select_entry_candidate

THRESHOLDS = (0.10, 0.25)


def promotion_shift(c: ButterflyCandidate, winner: ButterflyCandidate, rr_target: float) -> float:
    """Combined mark shift (option points) needed for `c` to tie `winner` on RR distance."""
    gap = abs(c.reward_risk - rr_target) - abs(winner.reward_risk - rr_target)
    if gap <= 0:
        return 0.0
    sensitivity = c.wing_width / c.cost**2 + winner.wing_width / winner.cost**2
    return gap / sensitivity


def selector_pool(
    candidates: list[ButterflyCandidate], *, vix: float, spot: float, direction: str,
    widths: tuple[int, ...], sigmas: tuple[float | None, ...], center_tolerance: float,
    rr_max: float,
) -> list[ButterflyCandidate]:
    """Every candidate the VIX-anchored selector compares before choosing."""
    pool: list[ButterflyCandidate] = []
    for i, width in enumerate(widths):
        target = vix_target_center(vix=vix, spot=spot, direction=direction, wing_width=width,
                                   sigma_fraction=sigmas[i] if i < len(sigmas) else None)
        near = [c for c in candidates if c.wing_width == width
                and abs(c.center_strike - target) <= center_tolerance]
        pool += [c for c in near if c.reward_risk <= rr_max] or near
    return pool


def tied_candidates(s: Session, ctx: RunContext, e: Entry, threshold: float
                    ) -> list[ButterflyCandidate]:
    config = e.select_config or ctx.config
    vix = e.select_vix if e.select_vix is not None else e.vix
    quotes = s.market.quotes_at(e.index, e.direction, near=e.spot, span=selection_span(config))
    result = select_entry_candidate(quotes=quotes, spot=e.spot, direction=e.direction,
                                    vix=vix, config=config, asset=ctx.asset)
    winner = result.candidate
    if winner is None:
        return []
    pool = selector_pool(
        list(result.candidates), vix=vix, spot=e.spot, direction=e.direction,
        widths=result.active_widths, sigmas=result.active_sigmas,
        center_tolerance=config.entry.center_tolerance, rr_max=config.strategy.rr_max,
    )
    rr_target = config.strategy.rr_target
    ties = [c for c in pool
            if promotion_shift(c, winner, rr_target) <= threshold + 1e-12]
    keyed = {(c.lower_strike, c.center_strike, c.upper_strike): c for c in [winner, *ties]}
    return list(keyed.values())


def draw_keys(d: dt.date, direction: str, draws: int, seed: int) -> np.ndarray:
    key = zlib.crc32(f"{seed}:{d.isoformat()}:{direction}".encode())
    return np.random.default_rng(key).random(draws)


NOT_APPLICABLE = "entries are not chosen by the live selector"


class TiesetScorer:
    """Collects tie sets per variant, threshold and entry during the replay."""

    def __init__(self, thresholds: tuple[float, ...] = THRESHOLDS,
                 models: tuple[Model, ...] = ("stressed",), draws: int = 5000,
                 seed: int = 7) -> None:
        self.thresholds, self.models, self.draws, self.seed = thresholds, models, draws, seed
        # (variant, threshold) -> [(date, direction, {model: per-tied-fly pnl})]
        self.rows: dict[tuple[str, float], list[tuple[dt.date, str, dict]]] = {}
        self.not_applicable: set[str] = set()

    def params(self) -> dict:
        return {"thresholds": list(self.thresholds), "draws": self.draws, "seed": self.seed}

    def add(self, s: Session, ctx: RunContext, variant: str, e: Entry, rules: tuple[ExitRule, ...],
            costs: Costs, exit_delay: int) -> None:
        if e.candidate is None:
            self.not_applicable.add(variant)
            return
        for t in self.thresholds:
            trades: list[Trade] = []
            for c in tied_candidates(s, ctx, e, t):
                alt = Entry(Fly.from_candidate(c), e.ts_us, e.index, c.cost, e.direction,
                            vix=e.vix, spot=e.spot, candidate=c)
                out = simulate_entry(s, ctx, alt, rules, variant, costs, exit_delay)
                if isinstance(out, Trade):
                    trades.append(out)
            if trades:
                pnl = {m: np.array([tr.pnl(m) or 0.0 for tr in trades]) for m in self.models}
                self.rows.setdefault((variant, t), []).append((s.date, e.direction, pnl))

    def summary(self, names: list[str], dates: list[dt.date]) -> dict[str, dict]:
        """Per variant and threshold over `dates` (the compared sessions); the first name
        is the baseline for `beats_baseline`."""
        keep = set(dates)
        totals: dict[tuple[str, float, str], np.ndarray] = {}
        out: dict[str, dict] = {}
        for name in names:
            if name in self.not_applicable:
                out[name] = {"not_applicable": NOT_APPLICABLE}
                continue
            out[name] = {}
            for t in self.thresholds:
                rows = [r for r in self.rows.get((name, t), []) if r[0] in keep]
                sizes = [len(r[2][self.models[0]]) for r in rows]
                row = {"sessions": len(dates),
                       "mean_tie_size": round(float(np.mean(sizes)), 2) if sizes else None}
                for m in self.models:
                    tot = np.zeros(self.draws)
                    avg = 0.0
                    for d, direction, pnl in rows:
                        u = draw_keys(d, direction, self.draws, self.seed)
                        pick = np.minimum((u * len(pnl[m])).astype(int), len(pnl[m]) - 1)
                        tot += pnl[m][pick]
                        avg += float(pnl[m].mean())
                    totals[(name, t, m)] = tot
                    lo, med, hi = np.percentile(tot, [5, 50, 95])
                    row[m] = {"tieset_avg": round(avg, 2), "draw_median": round(float(med), 2),
                              "draw_p05": round(float(lo), 2), "draw_p95": round(float(hi), 2)}
                    base = totals.get((names[0], t, m))
                    if name != names[0] and base is not None:
                        row[m]["beats_baseline"] = round(float((tot > base).mean()), 4)
                out[name][f"{t:.2f}"] = row
        return out
