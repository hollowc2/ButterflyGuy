"""Tests for Black-Scholes pricing and Greeks."""

import math

from butterfly_guy.quant_engine.black_scholes import (
    bs_call_price,
    bs_delta,
    bs_gamma,
    bs_put_price,
    bs_theta,
    bs_vega,
)


def test_bs_call_atm():
    """ATM call price should be approximately S * sigma * sqrt(T/2pi)."""
    S, K, T, r, sigma = 5500.0, 5500.0, 1 / 365, 0.05, 0.20
    price = bs_call_price(S, K, T, r, sigma)
    assert price > 0
    assert price < 50  # sanity: 1-day ATM call is not huge


def test_bs_put_call_parity():
    """Put-call parity: C - P = S - K * exp(-rT)."""
    S, K, T, r, sigma = 5500.0, 5500.0, 30 / 365, 0.05, 0.18
    call = bs_call_price(S, K, T, r, sigma)
    put = bs_put_price(S, K, T, r, sigma)
    lhs = call - put
    rhs = S - K * math.exp(-r * T)
    assert abs(lhs - rhs) < 0.01


def test_bs_call_deep_itm():
    """Deep ITM call should be approximately S - K * exp(-rT)."""
    S, K, T, r, sigma = 5500.0, 5000.0, 1 / 365, 0.05, 0.20
    price = bs_call_price(S, K, T, r, sigma)
    intrinsic = S - K
    assert price >= intrinsic * 0.95


def test_bs_put_deep_itm():
    """Deep ITM put should be approximately K - S."""
    S, K, T, r, sigma = 5500.0, 6000.0, 1 / 365, 0.05, 0.20
    price = bs_put_price(S, K, T, r, sigma)
    assert price > 490


def test_bs_call_expired():
    """Expired call should equal intrinsic value."""
    assert bs_call_price(5500, 5400, 0, 0.05, 0.20) == 100.0
    assert bs_call_price(5500, 5600, 0, 0.05, 0.20) == 0.0


def test_bs_put_expired():
    assert bs_put_price(5500, 5600, 0, 0.05, 0.20) == 100.0
    assert bs_put_price(5500, 5400, 0, 0.05, 0.20) == 0.0


def test_delta_call_range():
    S, K, T, r, sigma = 5500.0, 5500.0, 7 / 365, 0.05, 0.18
    d = bs_delta(S, K, T, r, sigma, "CALL")
    assert 0.0 < d < 1.0


def test_delta_put_range():
    S, K, T, r, sigma = 5500.0, 5500.0, 7 / 365, 0.05, 0.18
    d = bs_delta(S, K, T, r, sigma, "PUT")
    assert -1.0 < d < 0.0


def test_delta_call_plus_put_parity():
    """Put-call delta parity: call_delta - put_delta = 1."""
    S, K, T, r, sigma = 5500.0, 5500.0, 7 / 365, 0.05, 0.18
    c_delta = bs_delta(S, K, T, r, sigma, "CALL")
    p_delta = bs_delta(S, K, T, r, sigma, "PUT")
    # c_delta ≈ 0.5, p_delta ≈ -0.5 → difference ≈ 1
    assert abs(c_delta - p_delta - 1.0) < 0.005


def test_gamma_positive():
    S, K, T, r, sigma = 5500.0, 5500.0, 1 / 365, 0.05, 0.20
    assert bs_gamma(S, K, T, r, sigma) > 0


def test_theta_negative_calls():
    S, K, T, r, sigma = 5500.0, 5500.0, 7 / 365, 0.05, 0.18
    assert bs_theta(S, K, T, r, sigma, "CALL") < 0


def test_vega_positive():
    S, K, T, r, sigma = 5500.0, 5500.0, 7 / 365, 0.05, 0.18
    assert bs_vega(S, K, T, r, sigma) > 0
