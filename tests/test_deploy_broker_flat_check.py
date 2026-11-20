"""Historical replacements must not hide active or unknown replacement orders."""
import runpy
from unittest.mock import AsyncMock, Mock, patch

import pytest


def order(status):
    return {
        "status": status,
        "orderLegCollection": [{"instrument": {"symbol": "SPXW  261028C07700000"}}],
    }


@pytest.mark.parametrize("replacement_status", ["FILLED", "WORKING", "NEW_STATE", None])
def test_deploy_gate_checks_replacement_independently(replacement_status):
    replaced = order("REPLACED")
    replaced["childOrderStrategies"] = [order(replacement_status)]
    response = Mock()
    response.json.return_value = [replaced]
    client = Mock(
        initialize=AsyncMock(), close=AsyncMock(),
        _retry=AsyncMock(return_value=response),
        get_account_snapshot=AsyncMock(return_value={}),
    )
    with patch("butterfly_guy.data.schwab_client.SchwabClientWrapper", return_value=client):
        if replacement_status == "FILLED":
            runpy.run_path("tools/deploy_broker_flat_check.py")
        else:
            with pytest.raises(
                RuntimeError, match="Broker has (active|unmapped|missing) SPX order"
            ):
                runpy.run_path("tools/deploy_broker_flat_check.py")
    client.close.assert_awaited_once()


def _held(symbol):
    return {"securitiesAccount": {"positions": [{
        "longQuantity": 1,
        "instrument": {"assetType": "OPTION", "symbol": symbol, "underlyingSymbol": "SPXW"},
    }]}}


@pytest.mark.parametrize(
    ("argv", "symbol", "now", "flat"),
    [
        # Schwab lists 11-19's expired legs until its overnight posting.
        (["-", "--ignore-expired"], "SPXW  261119C07435000", (2026, 11, 19, 16, 15), True),
        (["-", "--ignore-expired"], "SPXW  261119C07435000", (2026, 11, 20, 6, 35), True),
        (["-", "--ignore-expired"], "SPXW  261119C07435000", (2026, 11, 19, 15, 59), False),
        (["-", "--ignore-expired"], "SPXW  261120C07435000", (2026, 11, 19, 16, 15), False),
        (["-", "--ignore-expired"], "NOT-AN-OCC-SYMBOL", (2026, 11, 19, 16, 15), False),
        (["-"], "SPXW  261119C07435000", (2026, 11, 19, 16, 15), False),
    ],
)
def test_close_out_gate_ignores_only_expired_legs(argv, symbol, now, flat):
    import datetime as dt

    from butterfly_guy.core.time_utils import EASTERN

    response = Mock()
    response.json.return_value = []
    client = Mock(
        initialize=AsyncMock(), close=AsyncMock(),
        _retry=AsyncMock(return_value=response),
        get_account_snapshot=AsyncMock(return_value=_held(symbol)),
    )
    with patch("butterfly_guy.data.schwab_client.SchwabClientWrapper", return_value=client), \
         patch("butterfly_guy.core.time_utils.now_eastern",
               return_value=dt.datetime(*now, tzinfo=EASTERN)), \
         patch("sys.argv", argv):
        if flat:
            runpy.run_path("tools/deploy_broker_flat_check.py")
        else:
            with pytest.raises(RuntimeError, match="position"):
                runpy.run_path("tools/deploy_broker_flat_check.py")
