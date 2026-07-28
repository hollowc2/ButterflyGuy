import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from butterfly_guy.db.queries import TradeQueries


@pytest.mark.asyncio
async def test_close_trade_only_closes_an_open_trade_once() -> None:
    pool = AsyncMock()
    pool.execute.side_effect = ["UPDATE 1", "UPDATE 0", "UPDATE 2"]
    queries = TradeQueries(SimpleNamespace(pool=pool))
    args = (7, 1.25, dt.datetime.now(dt.timezone.utc), "target", 0.25, 1.5)

    assert await queries.close_trade(*args) is True
    assert await queries.close_trade(*args) is False
    assert await queries.close_trade(*args) is False
    assert "status = 'OPEN'" in pool.execute.await_args_list[0].args[0]
