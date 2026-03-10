"""Implied volatility model with VIX scaling and skew adjustment."""

from __future__ import annotations


# Empirical: 0-DTE IV tends to run ~15% above VIX due to intraday vol premium
VIX_0DTE_SCALAR = 1.15

# Skew parameters: OTM puts have higher IV, OTM calls have lower
PUT_SKEW_SLOPE = 0.0015   # IV increase per point OTM for puts
CALL_SKEW_SLOPE = 0.0005  # IV decrease per point OTM for calls

# Steepening factor as DTE approaches 0
DTE_STEEPEN_FACTOR = 1.25  # multiply skew by this when DTE < 30 min


class IVModel:
    """Models implied volatility with VIX scaling and volatility skew."""

    def vix_to_0dte_iv(self, vix: float) -> float:
        """Convert VIX index value to 0-DTE ATM IV estimate.

        VIX is the 30-day implied vol index. 0-DTE IV is typically higher.
        """
        return (vix / 100.0) * VIX_0DTE_SCALAR

    def skew_adjusted_iv(
        self,
        atm_iv: float,
        spot: float,
        strike: float,
        option_type: str,
        minutes_remaining: float,
    ) -> float:
        """Compute skew-adjusted IV for a given strike.

        OTM puts have elevated IV (negative skew), OTM calls have lower IV.
        The skew steepens as expiration approaches.
        """
        moneyness = strike - spot  # positive = above spot (OTM call / ITM put)

        # Steepen skew for very short DTE
        steepen = DTE_STEEPEN_FACTOR if minutes_remaining < 30 else 1.0

        if option_type == "PUT":
            if moneyness < 0:
                # OTM put: strike < spot → add skew premium
                otm_pts = abs(moneyness)
                skew = PUT_SKEW_SLOPE * otm_pts * steepen
            else:
                # ITM put: small skew reduction
                skew = -CALL_SKEW_SLOPE * abs(moneyness) * steepen
        else:  # CALL
            if moneyness > 0:
                # OTM call: strike > spot → lower IV
                skew = -CALL_SKEW_SLOPE * abs(moneyness) * steepen
            else:
                # ITM call: small premium
                skew = PUT_SKEW_SLOPE * abs(moneyness) * steepen * 0.5

        return max(0.01, atm_iv + skew)
