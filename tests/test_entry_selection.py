from __future__ import annotations

import datetime as dt

from butterfly_guy.core.config import AppConfig, EntrySettings, StrategySettings, VixWidthBucket
from butterfly_guy.data.schemas import OptionQuote
from butterfly_guy.strategy.entry_selection import (
    ENTRY_STRATEGY_VERSION,
    entry_selection_config,
    entry_strategy_snapshot,
    select_entry_candidate,
)


def _quote(strike: float, price: float) -> OptionQuote:
    return OptionQuote(
        symbol=f"XSP{strike:.0f}",
        underlying="XSP",
        expiration=dt.date(2026, 6, 19),
        strike=strike,
        option_type="PUT",
        bid=price,
        ask=price,
        mark=price,
    )


def test_vix_entry_selection_prefers_first_width_for_xsp() -> None:
    config = AppConfig(
        strategy=StrategySettings(
            underlying="XSP",
            wing_widths=[10, 20],
            vix_width_buckets=[VixWidthBucket(vix_max=9999.0, widths=[10, 20])],
            spot_range=100,
            rr_min=1.0,
            rr_max=20.0,
            rr_target=10.0,
            max_cost_per_width={10: 2.0, 20: 2.0},
        ),
        entry=EntrySettings(
            strike_selection_method="VIX",
            center_tolerance=15.0,
        ),
    )

    quotes = [
        _quote(175, 1.0),
        _quote(188, 1.0),
        _quote(195, 0.5),
        _quote(198, 0.5),
        _quote(208, 1.0),
        _quote(215, 1.0),
    ]

    result = select_entry_candidate(
        quotes=quotes,
        spot=200.0,
        direction="PUT",
        vix=50.0,
        config=config,
        asset="XSP",
    )

    assert result.candidate is not None
    assert result.candidate.wing_width == 10
    assert result.active_widths == (10, 20)
    assert [c.wing_width for c in result.per_width_bests] == [10, 20]


def test_vix_entry_selection_does_not_fallback_outside_center_tolerance() -> None:
    config = AppConfig(
        strategy=StrategySettings(
            underlying="XSP",
            wing_widths=[10],
            vix_width_buckets=[VixWidthBucket(vix_max=9999.0, widths=[10])],
            spot_range=100,
            rr_min=1.0,
            rr_max=20.0,
            rr_target=10.0,
            max_cost_per_width={10: 2.0},
        ),
        entry=EntrySettings(
            strike_selection_method="VIX",
            center_tolerance=1.0,
        ),
    )

    result = select_entry_candidate(
        quotes=[_quote(175, 1.0), _quote(185, 0.5), _quote(195, 1.0)],
        spot=200.0,
        direction="PUT",
        vix=80.0,
        config=config,
        asset="XSP",
    )

    assert result.candidate is None
    assert result.per_width_bests == ()


def test_entry_selection_config_applies_only_explicit_overrides() -> None:
    config = AppConfig(
        strategy=StrategySettings(rr_min=8.0),
        entry=EntrySettings(strike_selection_method="VIX"),
    )

    resolved = entry_selection_config(
        config,
        selection_method="BEST_RR",
        rr_min=6.5,
    )

    assert config.entry.strike_selection_method == "VIX"
    assert config.strategy.rr_min == 8.0
    assert resolved.entry.strike_selection_method == "BEST_RR"
    assert resolved.strategy.rr_min == 6.5


def test_entry_strategy_snapshot_records_live_selection_profile() -> None:
    config = AppConfig(
        strategy=StrategySettings(
            underlying="SPX",
            wing_widths=[20, 30, 40],
            rr_min=7.5,
        ),
        entry=EntrySettings(
            strike_selection_method="VIX",
            center_tolerance=12.0,
        ),
    )

    snapshot = entry_strategy_snapshot(config)

    assert snapshot["version"] == ENTRY_STRATEGY_VERSION
    assert snapshot["underlying"] == "SPX"
    assert snapshot["selection_method"] == "VIX"
    assert snapshot["center_tolerance"] == 12.0
    assert snapshot["strategy"]["wing_widths"] == [20, 30, 40]
    assert snapshot["strategy"]["rr_min"] == 7.5
