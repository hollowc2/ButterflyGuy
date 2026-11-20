"""Research-only scan coverage and filtering order invariants."""

import datetime as dt
import importlib.util
from pathlib import Path

import pytest

from butterfly_guy.core.config import StrategySettings
from butterfly_guy.data.schemas import OptionQuote

spec = importlib.util.spec_from_file_location(
    "ndx_entry_coverage", Path(__file__).resolve().parents[1]
    / "tools/research_studies/ndx_entry_coverage.py",
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def fly(center, cost, half_spread):
    return [OptionQuote(
        symbol=f"NDXP-{strike}", underlying="NDX", expiration=dt.date(2026, 11, 9),
        strike=strike, option_type="CALL", bid=mark-half_spread,
        ask=mark+half_spread, mark=mark,
    ) for strike, mark in ((center-150, 100), (center, 60), (center+150, 20+cost))]


def settings():
    return StrategySettings(underlying="NDX", wing_widths=[150], spot_range=250,
                            max_cost_per_width={150: 12}, rr_min=8)


def select(quotes, **kwargs):
    return study.select_candidate(quotes, 27656.78, "CALL", 21.41,
                                  settings(), 100, **kwargs)


def test_complete_target_recovers_center_beyond_fixed_scan_without_mutating_settings():
    quotes = fly(28030, 10.8, 1.3)
    cfg = settings()
    assert select(quotes)[0] is None
    candidate, count = study.select_candidate(
        quotes, 27656.78, "CALL", 21.41, cfg, 100, complete_target=True,
    )
    assert count == 1
    assert candidate.center_strike == 28030
    assert cfg.spot_range == 250


def test_filter_before_ranking_selects_affordable_alternative():
    quotes = fly(28030, 10.8, 1.3) + fly(28020, 8, .9)
    original, _ = select(quotes, complete_target=True)
    filtered, count = select(quotes, complete_target=True, require_ask=True)
    assert original.center_strike == 28030
    assert original.ask > 12
    assert filtered.center_strike == 28020
    assert filtered.ask == pytest.approx(11.6)
    assert count == 1


def test_no_fallback_to_over_cap_candidate_and_cap_boundary_is_inclusive():
    assert select(fly(28030, 10.8, 1.3), complete_target=True, require_ask=True)[0] is None
    candidate, _ = select(fly(28030, 8, 1), complete_target=True, require_ask=True)
    assert candidate.ask == pytest.approx(12)


def test_complete_target_still_enforces_price_and_target_constraints():
    assert select(fly(28030, 12.1, .1), complete_target=True)[0] is None
    assert select(fly(28050, 8, .1), complete_target=True)[0] is None


def test_baseline_can_select_a_center_inside_existing_range():
    candidate, _ = select(fly(27900, 10, .1))
    assert candidate.center_strike == 27900
    assert candidate.distance_from_spot <= 250
