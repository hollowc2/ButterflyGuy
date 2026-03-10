"""Builds butterfly spread orders for Schwab API."""

from __future__ import annotations

from typing import Any

from butterfly_guy.core.logging import get_logger
from butterfly_guy.data.schemas import ButterflyCandidate

log = get_logger(__name__)


class ButterflyOrderBuilder:
    """Constructs Schwab-compatible butterfly order JSON."""

    def build_butterfly_open(
        self, candidate: ButterflyCandidate, limit_price: float, quantity: int = 1
    ) -> dict[str, Any]:
        """Build a butterfly BUY_TO_OPEN order."""
        return self._build_order(
            candidate=candidate,
            limit_price=limit_price,
            quantity=quantity,
            open_close="OPEN",
            instruction_outer="BUY_TO_OPEN",
            instruction_center="SELL_TO_OPEN",
        )

    def build_butterfly_close(
        self, candidate: ButterflyCandidate, limit_price: float, quantity: int = 1
    ) -> dict[str, Any]:
        """Build a butterfly SELL_TO_CLOSE order."""
        return self._build_order(
            candidate=candidate,
            limit_price=limit_price,
            quantity=quantity,
            open_close="CLOSE",
            instruction_outer="SELL_TO_CLOSE",
            instruction_center="BUY_TO_CLOSE",
        )

    def _build_order(
        self,
        candidate: ButterflyCandidate,
        limit_price: float,
        quantity: int,
        open_close: str,
        instruction_outer: str,
        instruction_center: str,
    ) -> dict[str, Any]:
        order = {
            "orderType": "NET_DEBIT" if open_close == "OPEN" else "NET_CREDIT",
            "session": "NORMAL",
            "duration": "DAY",
            "price": str(round(limit_price, 2)),
            "complexOrderStrategyType": "BUTTERFLY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": instruction_outer,
                    "quantity": quantity,
                    "instrument": {
                        "symbol": candidate.lower_symbol,
                        "assetType": "OPTION",
                    },
                },
                {
                    "instruction": instruction_center,
                    "quantity": quantity * 2,
                    "instrument": {
                        "symbol": candidate.center_symbol,
                        "assetType": "OPTION",
                    },
                },
                {
                    "instruction": instruction_outer,
                    "quantity": quantity,
                    "instrument": {
                        "symbol": candidate.upper_symbol,
                        "assetType": "OPTION",
                    },
                },
            ],
        }

        log.info(
            "order_built",
            type=open_close,
            center=candidate.center_strike,
            width=candidate.wing_width,
            price=limit_price,
        )
        return order
