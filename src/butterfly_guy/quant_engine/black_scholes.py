"""Black-Scholes option pricing and Greeks."""

from __future__ import annotations

import math

from scipy.optimize import brentq
from scipy.stats import norm


def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0:
        return 0.0
    return (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))


def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return _d1(S, K, T, r, sigma) - sigma * math.sqrt(T)


def bs_call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes European call price.

    Args:
        S: Spot price
        K: Strike price
        T: Time to expiration in years
        r: Risk-free rate (annualized)
        sigma: Implied volatility (annualized)
    """
    if T <= 0:
        return max(0.0, S - K)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)


def bs_put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes European put price."""
    if T <= 0:
        return max(0.0, K - S)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def bs_delta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CALL"
) -> float:
    """Delta — rate of change of price wrt spot."""
    if T <= 0:
        if option_type == "CALL":
            return 1.0 if S > K else 0.0
        return -1.0 if S < K else 0.0
    d1 = _d1(S, K, T, r, sigma)
    if option_type == "CALL":
        return norm.cdf(d1)
    return norm.cdf(d1) - 1.0


def bs_gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Gamma — rate of change of delta wrt spot."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    return norm.pdf(d1) / (S * sigma * math.sqrt(T))


def bs_theta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CALL"
) -> float:
    """Theta — time decay per calendar day."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
    if option_type == "CALL":
        theta_annual = term1 - r * K * math.exp(-r * T) * norm.cdf(d2)
    else:
        theta_annual = term1 + r * K * math.exp(-r * T) * norm.cdf(-d2)
    return theta_annual / 365.0  # per calendar day


def bs_vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Vega — sensitivity to 1% change in IV."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    return S * norm.pdf(d1) * math.sqrt(T) * 0.01  # per 1% IV move


def implied_vol(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "CALL",
    lo: float = 0.001,
    hi: float = 5.0,
) -> float | None:
    """Back-solve for implied volatility given an option market price.

    Returns None if the price is outside BS no-arbitrage bounds or the
    solver fails to converge (e.g. deep OTM near expiry with near-zero price).
    """
    if T <= 0 or price <= 0:
        return None
    pricer = bs_call_price if option_type == "CALL" else bs_put_price
    intrinsic = max(0.0, S - K) if option_type == "CALL" else max(0.0, K - S)
    if price <= intrinsic:
        return None
    try:
        return brentq(lambda sigma: pricer(S, K, T, r, sigma) - price, lo, hi, xtol=1e-4)
    except ValueError:
        return None
