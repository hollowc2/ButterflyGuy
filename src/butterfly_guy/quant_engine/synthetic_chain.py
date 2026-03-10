"""Synthetic option chain generator using Black-Scholes + VIX IV model."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.data.schemas import OptionQuote
from butterfly_guy.quant_engine.black_scholes import (
    bs_call_price,
    bs_delta,
    bs_gamma,
    bs_put_price,
    bs_theta,
    bs_vega,
)
from butterfly_guy.quant_engine.iv_model import IVModel

MINUTES_PER_YEAR = 525_600
RISK_FREE_RATE = 0.05  # 5% risk-free rate
MIN_SPREAD = 0.05
SPREAD_PCT = 0.02  # 2% of option price as bid/ask spread


class SyntheticChainGenerator:
    """Generates a synthetic SPX option chain from spot + VIX."""

    def __init__(self) -> None:
        self.iv_model = IVModel()

    def generate_chain(
        self,
        spot: float,
        vix: float,
        expiration: dt.date,
        snapshot_time: dt.datetime,
        strike_min: float | None = None,
        strike_max: float | None = None,
        strike_step: float = 5.0,
    ) -> list[OptionQuote]:
        """Generate full synthetic option chain for one expiration.

        Args:
            spot: Underlying spot price
            vix: VIX index value (e.g. 18.5)
            expiration: Option expiration date
            snapshot_time: Reference time for DTE calculation
            strike_min: Lowest strike (defaults to spot - 100)
            strike_max: Highest strike (defaults to spot + 100)
            strike_step: Strike increment (default 5.0)
        """
        # Time to expiration in years
        snap_date = snapshot_time.date() if hasattr(snapshot_time, "date") else snapshot_time
        minutes_remaining = self._minutes_remaining(expiration, snapshot_time)
        T = minutes_remaining / MINUTES_PER_YEAR

        # ATM IV from VIX
        atm_iv = self.iv_model.vix_to_0dte_iv(vix)

        # Strike range
        smin = strike_min if strike_min is not None else round(spot - 100, 0)
        smax = strike_max if strike_max is not None else round(spot + 100, 0)

        quotes: list[OptionQuote] = []
        strike = smin
        while strike <= smax:
            for option_type in ("CALL", "PUT"):
                iv = self.iv_model.skew_adjusted_iv(
                    atm_iv, spot, strike, option_type, minutes_remaining
                )

                if option_type == "CALL":
                    price = bs_call_price(spot, strike, T, RISK_FREE_RATE, iv)
                    delta = bs_delta(spot, strike, T, RISK_FREE_RATE, iv, "CALL")
                else:
                    price = bs_put_price(spot, strike, T, RISK_FREE_RATE, iv)
                    delta = bs_delta(spot, strike, T, RISK_FREE_RATE, iv, "PUT")

                gamma = bs_gamma(spot, strike, T, RISK_FREE_RATE, iv)
                theta = bs_theta(spot, strike, T, RISK_FREE_RATE, iv, option_type)
                vega = bs_vega(spot, strike, T, RISK_FREE_RATE, iv)

                spread = max(MIN_SPREAD, price * SPREAD_PCT)
                bid = max(0.0, price - spread / 2)
                ask = price + spread / 2
                mark = price

                quotes.append(
                    OptionQuote(
                        symbol=f"SYNTH_{option_type[0]}{int(strike)}",
                        underlying="SPX",
                        expiration=expiration,
                        strike=strike,
                        option_type=option_type,  # type: ignore[arg-type]
                        bid=round(bid, 2),
                        ask=round(ask, 2),
                        mark=round(mark, 4),
                        iv=round(iv, 6),
                        delta=round(delta, 6),
                        gamma=round(gamma, 6),
                        theta=round(theta, 6),
                        vega=round(vega, 6),
                    )
                )
            strike = round(strike + strike_step, 2)

        return quotes

    def _minutes_remaining(
        self, expiration: dt.date, snapshot_time: dt.datetime
    ) -> float:
        """Minutes until market close on expiration day."""
        from zoneinfo import ZoneInfo

        eastern = ZoneInfo("America/New_York")
        close_dt = dt.datetime(
            expiration.year, expiration.month, expiration.day, 16, 0, tzinfo=eastern
        )
        snap_et = snapshot_time.astimezone(eastern)
        delta = close_dt - snap_et
        return max(1.0, delta.total_seconds() / 60.0)
