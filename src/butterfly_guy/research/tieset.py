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

Neighbor tie sets (opt-in through `neighbors`, on in `run`) also rerun selection on the
snapshots next to the entry snapshot, each with its own quotes, clock spot and VIX, and
replay each neighbor's tie set entering at that snapshot. A recorded snapshot is not
what live saw: live fetches its chain between two collector snapshots, and on the
2026-07-22 -> 2026-10-16 live cohort the entry snapshot alone held live's fly within
$0.25 on 37 of 57 days, against 54 with +/-1 neighbors
(`docs/research/neighbor-tieset-2026-10-18.md`). Snapshot +1 is recorded after the
decision, so this is a sensitivity measure, never a tradable rule. Scoring is two-stage:
the per-session average is the mean over neighbors of each neighbor's mean, and a draw
picks a neighbor and then one of its flies, both keyed by (session, direction). Entries
selected with an overridden VIX anchor (the straddle rules) get no neighbor rows.
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
NEIGHBOR_OFFSETS = (-1, 0, 1)


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


def neighbor_entry(s: Session, ctx: RunContext, e: Entry, offset: int) -> Entry | None:
    """`e` re-anchored on the snapshot `offset` steps from its own, with that snapshot's
    clock spot and VIX; None when the snapshot or a fresh VIX is missing."""
    if offset == 0:
        return e
    j = e.index + offset
    if not 0 <= j < len(s.market.ts):
        return None
    ts = int(s.market.ts[j])
    vix = s.vix.at_or_before(ts, max_age_s=ctx.max_vix_age_s)
    if vix is None:
        return None
    spot = float(s.clock_spot[max(s.clock_index(ts), 0)])
    return Entry(e.fly, ts, j, e.cost, e.direction, vix=vix[0], spot=spot,
                 candidate=e.candidate, select_config=e.select_config)


def two_stage_pick(per_neighbor: list[np.ndarray], u_neighbor: np.ndarray,
                   u_fly: np.ndarray) -> np.ndarray:
    """Per draw, the P&L of one fly: a neighbor by `u_neighbor`, then a fly by `u_fly`."""
    which = np.minimum((u_neighbor * len(per_neighbor)).astype(int), len(per_neighbor) - 1)
    out = np.empty(len(u_neighbor))
    for i, pnl in enumerate(per_neighbor):
        mask = which == i
        out[mask] = pnl[np.minimum((u_fly[mask] * len(pnl)).astype(int), len(pnl) - 1)]
    return out


NOT_APPLICABLE = "entries are not chosen by the live selector"


class TiesetScorer:
    """Collects tie sets per variant, threshold and entry during the replay."""

    def __init__(self, thresholds: tuple[float, ...] = THRESHOLDS,
                 models: tuple[Model, ...] = ("stressed",), draws: int = 5000,
                 seed: int = 7, neighbors: tuple[int, ...] = ()) -> None:
        self.thresholds, self.models, self.draws, self.seed = thresholds, models, draws, seed
        self.neighbors = neighbors
        # (variant, threshold) -> [(date, direction, {model: per-tied-fly pnl})]
        self.rows: dict[tuple[str, float], list[tuple[dt.date, str, dict]]] = {}
        # (variant, threshold) -> [(date, direction, {model: [per-tied-fly pnl per neighbor]})]
        self.neighbor_rows: dict[tuple[str, float], list[tuple[dt.date, str, dict]]] = {}
        self.not_applicable: set[str] = set()

    def params(self) -> dict:
        params = {"thresholds": list(self.thresholds), "draws": self.draws, "seed": self.seed}
        if self.neighbors:  # recorded only when set, so runs without them keep their ids
            params["neighbor_offsets"] = list(self.neighbors)
        return params

    def _replay_ties(self, s: Session, ctx: RunContext, anchor: Entry, threshold: float,
                     rules: tuple[ExitRule, ...], variant: str, costs: Costs,
                     exit_delay: int) -> list[Trade]:
        trades: list[Trade] = []
        for c in tied_candidates(s, ctx, anchor, threshold):
            alt = Entry(Fly.from_candidate(c), anchor.ts_us, anchor.index, c.cost,
                        anchor.direction, vix=anchor.vix, spot=anchor.spot, candidate=c)
            out = simulate_entry(s, ctx, alt, rules, variant, costs, exit_delay)
            if isinstance(out, Trade):
                trades.append(out)
        return trades

    def _pnl(self, trades: list[Trade]) -> dict[str, np.ndarray]:
        return {m: np.array([tr.pnl(m) or 0.0 for tr in trades]) for m in self.models}

    def add(self, s: Session, ctx: RunContext, variant: str, e: Entry, rules: tuple[ExitRule, ...],
            costs: Costs, exit_delay: int) -> None:
        if e.candidate is None:
            self.not_applicable.add(variant)
            return
        anchors = {}
        if e.select_vix is None:
            anchors = {o: a for o in self.neighbors
                       if (a := neighbor_entry(s, ctx, e, o)) is not None}
        for t in self.thresholds:
            trades = self._replay_ties(s, ctx, e, t, rules, variant, costs, exit_delay)
            if trades:
                self.rows.setdefault((variant, t), []).append(
                    (s.date, e.direction, self._pnl(trades)))
            per_neighbor = [
                trades if o == 0
                else self._replay_ties(s, ctx, a, t, rules, variant, costs, exit_delay)
                for o, a in anchors.items()
            ]
            per_neighbor = [p for p in per_neighbor if p]
            if per_neighbor:
                pnls = [self._pnl(p) for p in per_neighbor]
                self.neighbor_rows.setdefault((variant, t), []).append(
                    (s.date, e.direction, {m: [p[m] for p in pnls] for m in self.models}))

    def summary(self, names: list[str], dates: list[dt.date]) -> dict[str, dict]:
        """Per variant and threshold over `dates` (the compared sessions); the first name
        is the baseline for `beats_baseline`. Neighbor rows, when collected, follow under
        `nbr <threshold>`."""
        keep = set(dates)
        totals: dict[tuple[str, str, str], np.ndarray] = {}
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
                    row[m] = self._draw_stats(totals, names, name, f"{t:.2f}", m, tot, avg)
                out[name][f"{t:.2f}"] = row
            for t in self.thresholds if self.neighbors else ():
                rows = [r for r in self.neighbor_rows.get((name, t), []) if r[0] in keep]
                if not rows:
                    continue
                first = [r[2][self.models[0]] for r in rows]
                row = {"sessions": len(dates),
                       "mean_neighbors": round(float(np.mean([len(p) for p in first])), 2),
                       "mean_tie_size": round(float(np.mean(
                           [sum(len(x) for x in p) for p in first])), 2)}
                for m in self.models:
                    tot = np.zeros(self.draws)
                    avg = 0.0
                    for d, direction, pnl in rows:
                        u_fly = draw_keys(d, direction, self.draws, self.seed)
                        u_neighbor = draw_keys(d, f"{direction}:neighbor", self.draws, self.seed)
                        tot += two_stage_pick(pnl[m], u_neighbor, u_fly)
                        avg += float(np.mean([x.mean() for x in pnl[m]]))
                    row[m] = self._draw_stats(totals, names, name, f"nbr {t:.2f}", m, tot, avg)
                out[name][f"nbr {t:.2f}"] = row
        return out

    def _draw_stats(self, totals: dict[tuple[str, str, str], np.ndarray], names: list[str],
                    name: str, label: str, model: str, tot: np.ndarray, avg: float) -> dict:
        totals[(name, label, model)] = tot
        lo, med, hi = np.percentile(tot, [5, 50, 95])
        stats = {"tieset_avg": round(avg, 2), "draw_median": round(float(med), 2),
                 "draw_p05": round(float(lo), 2), "draw_p95": round(float(hi), 2)}
        base = totals.get((names[0], label, model))
        if name != names[0] and base is not None:
            stats["beats_baseline"] = round(float((tot > base).mean()), 4)
        return stats
