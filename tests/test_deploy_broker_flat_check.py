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
