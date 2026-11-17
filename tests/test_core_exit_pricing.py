import math

import numpy as np
import pytest

from butterfly_guy.core.entry_pricing import round_credit_limit
from butterfly_guy.core.exit_pricing import EXIT_PRICING_RULES, exit_limit

KW = dict(ladder_step=0.10, ladder_steps=4, underlying="SPX")


def _today(step: int, bid: float) -> float:
    """The limit `OrderManager.execute_exit` computes today (main a283610)."""
    i = step % 4
    return round_credit_limit(max(0.05, bid + (4 - 1 - i) * 0.10), "SPX")


@pytest.mark.parametrize("bid", [-1.55, 0.0, 0.03, 1.0, 1.02, 2.37, 6.95])
def test_bid_ladder_reproduces_todays_limits_including_the_restart(bid):
    for step in range(10):
        assert exit_limit("bid_ladder", step, bid, bid + 0.4, **KW) == _today(step, bid)


def test_trade_415_first_limit():
    assert exit_limit("bid_ladder", 0, 1.00, 1.85, **KW) == 1.30
    assert exit_limit("mid_capped_ladder", 0, 1.00, 1.85, **KW) == 1.30
    assert exit_limit("mid_walk", 0, 1.00, 1.85, **KW) == 1.85


def test_mid_capped_never_exceeds_the_rounded_mid_and_equals_today_on_wide_spreads():
    for step in range(8):
        assert exit_limit("mid_capped_ladder", step, 1.35, 1.45, **KW) <= 1.45
        assert exit_limit("mid_capped_ladder", step, 1.00, 1.85, **KW) == _today(step, 1.00)


def test_mid_walk_walks_from_mid_to_bid_then_holds():
    limits = [exit_limit("mid_walk", s, 1.00, 1.90, **KW) for s in range(7)]
    assert limits == [1.90, 1.60, 1.30, 1.00, 1.00, 1.00, 1.00]


@pytest.mark.parametrize("rule", EXIT_PRICING_RULES)
def test_limits_are_valid_increments_and_never_below_the_bid(rule):
    for bid in np.arange(0.0, 3.0, 0.07):
        for spread in (0.0, 0.15, 0.4, 1.7):
            for step in range(8):
                lim = exit_limit(rule, step, bid, bid + spread / 2, **KW)
                assert lim >= bid - 1e-9 and lim >= 0.05
                assert math.isclose(round(lim / 0.05) * 0.05, lim, abs_tol=1e-9)


def test_crossed_anchors_never_price_below_the_bid():
    assert exit_limit("mid_capped_ladder", 3, 1.20, 1.10, **KW) == 1.20
    assert exit_limit("mid_walk", 0, 1.20, 1.10, **KW) == 1.20


def test_unknown_rule_is_refused():
    with pytest.raises(ValueError):
        exit_limit("mid", 0, 1.0, 1.1, **KW)


def test_static_quote_estimate_matches_the_mid50_model_by_hand():
    from butterfly_guy.core.exit_pricing import static_quote_estimate

    # bid ladder, narrow: 1.30 and 1.20 above the mid (no fill), 1.10 at mid (p .5), 1.00
    assert static_quote_estimate("bid_ladder", 1.00, 1.10, **KW) == pytest.approx(1.05)
    # mid walk, narrow: 1.10, 1.10, 1.05 at or below mid (p .5 each), then 1.00
    assert static_quote_estimate("mid_walk", 1.00, 1.10, **KW) == pytest.approx(
        0.5 * 1.10 + 0.25 * 1.10 + 0.125 * 1.05 + 0.125 * 1.00
    )
    # trade 415's quote: today's ladder starts below the 1.85 mid
    assert static_quote_estimate("bid_ladder", 1.00, 1.85, **KW) == pytest.approx(
        0.5 * 1.30 + 0.25 * 1.20 + 0.125 * 1.10 + 0.125 * 1.00
    )
    assert static_quote_estimate("mid_walk", 1.00, 1.85, p_mid=1.0, **KW) == 1.85
