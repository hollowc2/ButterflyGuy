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
"""

from __future__ import annotations

import datetime as dt
import zlib

import numpy as np

from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.research.accounting import Costs, Model
from butterfly_guy.research.entry import Entry, RunContext, Session, SessionLoader, selection_span
from butterfly_guy.research.market import Fly
from butterfly_guy.research.simulate import Trade, Variant, entries_for, simulate_entry
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
    config = ctx.config
    quotes = s.market.quotes_at(e.index, e.direction, near=e.spot, span=selection_span(config))
    result = select_entry_candidate(quotes=quotes, spot=e.spot, direction=e.direction,
                                    vix=e.vix, config=config, asset=ctx.asset)
    winner = result.candidate
    if winner is None:
        return []
    pool = selector_pool(
        list(result.candidates), vix=e.vix, spot=e.spot, direction=e.direction,
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


def run_tiesets(
    loader: SessionLoader, variants: list[Variant], ctx: RunContext, dates: list[dt.date], *,
    thresholds: tuple[float, ...] = THRESHOLDS, models: tuple[Model, ...] = ("stressed",),
    draws: int = 5000, seed: int = 7, costs: Costs | None = None,
) -> dict[str, dict[str, dict]]:
    """Per variant and threshold: tie sets per session and paired draw totals."""
    costs = costs or Costs(ctx.config.execution.paper_commission_per_contract)
    n = len(dates)
    # [variant][threshold][model] -> (draws,) totals, tie-set average total, tie sizes
    totals = {v.name: {t: {m: np.zeros(draws) for m in models} for t in thresholds}
              for v in variants}
    avg = {v.name: {t: {m: 0.0 for m in models} for t in thresholds} for v in variants}
    sizes = {v.name: {t: [] for t in thresholds} for v in variants}
    for d in dates:
        s = loader.load(d)
        if s is None:
            continue
        for v in variants:
            rules = v.exit_rules(ctx)
            for e in entries_for(s, ctx, v.entry):
                u = draw_keys(d, e.direction, draws, seed)
                for t in thresholds:
                    ties = tied_candidates(s, ctx, e, t)
                    trades: list[Trade] = []
                    for c in ties:
                        alt = Entry(Fly.from_candidate(c), e.ts_us, e.index, c.cost,
                                    e.direction, vix=e.vix, spot=e.spot, candidate=c)
                        out = simulate_entry(s, ctx, alt, rules, v.name, costs)
                        if isinstance(out, Trade):
                            trades.append(out)
                    if not trades:
                        continue
                    sizes[v.name][t].append(len(trades))
                    pick = np.minimum((u * len(trades)).astype(int), len(trades) - 1)
                    for m in models:
                        pnl = np.array([tr.pnl(m) or 0.0 for tr in trades])
                        totals[v.name][t][m] += pnl[pick]
                        avg[v.name][t][m] += float(pnl.mean())
    out: dict[str, dict[str, dict]] = {}
    base = variants[0].name
    for v in variants:
        out[v.name] = {}
        for t in thresholds:
            row = {"sessions": n, "mean_tie_size": round(float(np.mean(sizes[v.name][t])), 2)
                   if sizes[v.name][t] else None}
            for m in models:
                tot = totals[v.name][t][m]
                lo, med, hi = np.percentile(tot, [5, 50, 95])
                row[m] = {
                    "tieset_avg": round(avg[v.name][t][m], 2),
                    "draw_median": round(float(med), 2),
                    "draw_p05": round(float(lo), 2),
                    "draw_p95": round(float(hi), 2),
                }
                if v.name != base:
                    row[m]["beats_baseline"] = round(
                        float((tot > totals[base][t][m]).mean()), 4)
            out[v.name][f"{t:.2f}"] = row
    return out
