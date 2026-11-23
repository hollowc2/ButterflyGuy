"""Hand-calculated mark_v1 accounting; quantity changes aggregate dollars only."""

from unittest.mock import AsyncMock, patch

import pytest

from butterfly_guy.execution.order_manager import LiveSpread
from butterfly_guy.reports.live_performance import trade_pnl_dollars
from tests.test_order_manager import make_candidate, make_order_manager, make_settings


@pytest.mark.parametrize("quantity,side_fee,net_pnl", [(1, 4.60, -37), (2, 9.20, -74),
                                                   (3, 13.80, -111)])
async def test_mark_fills_and_aggregate_dollars(quantity, side_fee, net_pnl):
    # Four contracts per fly at $1.15 each = $4.60 per fly per side = .046 pts.
    # Entry mark 3.70 + .046 -> 3.75. Exit mark 3.43 - .046 -> 3.38.
    # After rounding: -.37 points = -$37/fly. Raw modeled round-trip fee $9.20/fly;
    # rounding makes the embedded drag $10/fly. Do not subtract either again.
    manager, broker = make_order_manager(make_settings(
        paper_trading=True, paper_commission_per_contract=1.15,
        paper_slippage_per_spread=2.0,
    ), underlying="SPX")
    candidate = make_candidate(7320, 7360, 7400, 3.70)
    spread = LiveSpread(bid=3.0, mark=3.70, ask=4.0)
    with patch.object(manager, "_fetch_live_spread", new=AsyncMock(return_value=spread)):
        entry = await manager.execute_single_attempt(candidate, limit_price=4, quantity=quantity)
        exit_fill = await manager.execute_exit(candidate, current_value=3.43, quantity=quantity)
    assert entry["fill_price"] == 3.75
    assert exit_fill["fill_price"] == 3.38
    assert manager._commission() * 100 * quantity == pytest.approx(side_fee)
    assert trade_pnl_dollars(
        exit_fill["fill_price"] - entry["fill_price"], quantity,
    ) == pytest.approx(net_pnl)
    assert (3.75 - 3.70 + 3.43 - 3.38) * 100 * quantity == pytest.approx(10 * quantity)
    broker.place_order.assert_not_awaited()
