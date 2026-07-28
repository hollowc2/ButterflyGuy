"""Integration test: validate butterfly order JSON structure.

These tests check the order spec matches the Schwab API schema
without actually placing orders.
"""



from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.execution.order_builder import ButterflyOrderBuilder


def make_spx_candidate() -> ButterflyCandidate:
    """Realistic SPX butterfly candidate."""
    return ButterflyCandidate(
        direction="CALL",
        wing_width=10,
        center_strike=5500.0,
        lower_strike=5490.0,
        upper_strike=5510.0,
        cost=0.75,
        max_profit=9.25,
        reward_risk=12.3,
        lower_be=5490.75,
        upper_be=5509.25,
        distance_from_spot=2.0,
        spot_price=5498.0,
        lower_symbol="SPXW  260310C05490000",
        center_symbol="SPXW  260310C05500000",
        upper_symbol="SPXW  260310C05510000",
    )


def test_order_has_required_schwab_fields():
    """Order spec must have all fields Schwab requires."""
    builder = ButterflyOrderBuilder()
    candidate = make_spx_candidate()
    order = builder.build_butterfly_open(candidate, 0.80)

    required = ["orderType", "session", "duration", "price",
                "complexOrderStrategyType", "orderStrategyType", "orderLegCollection"]
    for field in required:
        assert field in order, f"Missing field: {field}"


def test_order_leg_has_required_fields():
    builder = ButterflyOrderBuilder()
    candidate = make_spx_candidate()
    order = builder.build_butterfly_open(candidate, 0.80)
    for leg in order["orderLegCollection"]:
        assert "instruction" in leg
        assert "quantity" in leg
        assert "instrument" in leg
        assert "symbol" in leg["instrument"]
        assert "assetType" in leg["instrument"]
        assert leg["instrument"]["assetType"] == "OPTION"


def test_order_session_and_duration():
    builder = ButterflyOrderBuilder()
    candidate = make_spx_candidate()
    order = builder.build_butterfly_open(candidate, 0.80)
    assert order["session"] == "NORMAL"
    assert order["duration"] == "DAY"


def test_close_order_credit():
    builder = ButterflyOrderBuilder()
    candidate = make_spx_candidate()
    order = builder.build_butterfly_close(candidate, 2.50)
    assert order["orderType"] == "NET_CREDIT"


def test_price_format_is_string():
    """Schwab expects price as a string."""
    builder = ButterflyOrderBuilder()
    candidate = make_spx_candidate()
    order = builder.build_butterfly_open(candidate, 0.85)
    assert isinstance(order["price"], str)
