"""Shared entry selection for live trading and backtests."""

from __future__ import annotations

from dataclasses import dataclass

from butterfly_guy.core.config import AppConfig
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.butterfly_builder import (
    ButterflyBuilder,
    resolve_wing_widths_for_vix,
    vix_target_center,
)
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.width_selection import select_cross_width_candidate

ENTRY_STRATEGY_VERSION = "live-entry-selection-v1"


@dataclass(frozen=True)
class EntrySelectionResult:
    """Result of a single entry selection pass."""

    candidate: ButterflyCandidate | None
    candidates: tuple[ButterflyCandidate, ...]
    active_widths: tuple[int, ...]
    active_sigmas: tuple[float | None, ...]
    per_width_bests: tuple[ButterflyCandidate, ...]
    selection_method: str


def entry_strategy_snapshot(config: AppConfig) -> dict[str, object]:
    """Serializable live strategy profile used for entry selection."""
    return {
        "version": ENTRY_STRATEGY_VERSION,
        "underlying": config.strategy.underlying,
        "selection_method": config.entry.strike_selection_method,
        "center_tolerance": config.entry.center_tolerance,
        "strategy": config.strategy.model_dump(mode="json"),
    }


def entry_selection_config(
    config: AppConfig,
    *,
    selection_method: str | None = None,
    rr_min: float | None = None,
) -> AppConfig:
    """Return a config for selection with explicit overrides applied."""
    updates: dict[str, object] = {}
    if selection_method is not None:
        updates["entry"] = config.entry.model_copy(
            update={"strike_selection_method": selection_method}
        )
    if rr_min is not None:
        updates["strategy"] = config.strategy.model_copy(update={"rr_min": rr_min})
    if not updates:
        return config
    return config.model_copy(update=updates)


def _active_widths_and_sigmas(
    config: AppConfig,
    vix: float | None,
    wing_widths: list[int] | None,
) -> tuple[list[int], tuple[float | None, ...]]:
    """Resolve the widths to scan and their positional VIX sigmas."""
    if wing_widths is not None:
        return wing_widths, tuple(None for _ in wing_widths)

    if config.entry.strike_selection_method == "VIX" and config.strategy.vix_width_buckets:
        if vix is None:
            return [], ()
        widths, sigmas = resolve_wing_widths_for_vix(vix, config.strategy.vix_width_buckets)
        return widths, sigmas

    widths = config.strategy.wing_widths
    return widths, tuple(None for _ in widths)


def select_entry_candidate(
    *,
    quotes: list[OptionQuote],
    spot: float,
    direction: str,
    vix: float | None,
    config: AppConfig,
    asset: str,
    wing_widths: list[int] | None = None,
) -> EntrySelectionResult:
    """Select the live/backtest entry candidate with shared pure logic."""
    selection_method = config.entry.strike_selection_method
    active_widths, active_sigmas = _active_widths_and_sigmas(config, vix, wing_widths)

    strategy_settings = config.strategy.model_copy(update={"wing_widths": active_widths})
    builder = ButterflyBuilder(strategy_settings)
    selector = ButterflySelector(strategy_settings)
    candidates = builder.build_candidates(quotes, spot, direction)

    per_width_bests: list[ButterflyCandidate] = []
    candidate: ButterflyCandidate | None = None

    if selection_method == "VIX":
        if vix is not None:
            for i, width in enumerate(active_widths):
                sigma_fraction = active_sigmas[i] if i < len(active_sigmas) else None
                target_center = vix_target_center(
                    vix=vix,
                    spot=spot,
                    direction=direction,
                    wing_width=width,
                    sigma_fraction=sigma_fraction,
                )
                width_candidates = [c for c in candidates if c.wing_width == width]
                best = selector.select_best(
                    width_candidates,
                    target_center=target_center,
                    center_tolerance=config.entry.center_tolerance,
                )
                if best:
                    per_width_bests.append(best)
            if per_width_bests:
                candidate = select_cross_width_candidate(
                    per_width_bests,
                    prefer_first_width=(asset == "XSP" or config.strategy.underlying == "XSP"),
                )
    elif selection_method == "TARGET_COST":
        for width in active_widths:
            width_candidates = [c for c in candidates if c.wing_width == width]
            best = selector.select_best_by_target_cost(width_candidates)
            if best:
                per_width_bests.append(best)
        candidate = selector.select_best_by_target_cost(candidates)
    else:
        for width in active_widths:
            width_candidates = [c for c in candidates if c.wing_width == width]
            best = selector.select_best(width_candidates, target_center=None)
            if best:
                per_width_bests.append(best)
        candidate = selector.select_best(candidates, target_center=None)

    if candidate is None:
        candidate = selector.select_best(candidates)

    return EntrySelectionResult(
        candidate=candidate,
        candidates=tuple(candidates),
        active_widths=tuple(active_widths),
        active_sigmas=active_sigmas,
        per_width_bests=tuple(per_width_bests),
        selection_method=selection_method,
    )
