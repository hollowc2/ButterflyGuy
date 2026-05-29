from __future__ import annotations

import datetime as dt

from butterfly_guy.core.config import AppConfig, EntrySettings, StrategySettings, VixWidthBucket
from butterfly_guy.data.schemas import OptionQuote
from butterfly_guy.strategy.entry_selection import select_entry_candidate


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
