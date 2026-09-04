from tools.gateway_cutover_flatness_audit import _redacted_order_audit


def _order(status: str | None, symbol: str, order_id: str) -> dict:
    return {
        "orderId": order_id,
        "status": status,
        "orderLegCollection": [{"instrument": {"symbol": symbol}}],
    }


def test_redacted_audit_treats_replaced_as_historical_terminal() -> None:
    result = _redacted_order_audit(
        [_order("REPLACED", "NDXP  260831C26400000", "one")], "NDX"
    )

    assert result == {
        "top_level_orders": 1,
        "order_nodes": 1,
        "active_order_nodes": 0,
        "missing_status_nodes": 0,
        "unmapped_statuses": [],
        "replaced_terminal_nodes": 1,
        "duplicate_order_ids": 0,
    }


def test_redacted_audit_reports_active_unknown_missing_and_duplicate_nodes() -> None:
    parent = _order("WORKING", "SPXW  260831C06400000", "same")
    parent["childOrderStrategies"] = [
        _order("NEW_STATE", "SPXW  260831C06410000", "same"),
        _order(None, "SPXW  260831C06420000", "child"),
    ]

    result = _redacted_order_audit([parent], "SPX")

    assert result["active_order_nodes"] == 1
    assert result["missing_status_nodes"] == 1
    assert result["unmapped_statuses"] == ["NEW_STATE"]
    assert result["duplicate_order_ids"] == 1


def test_redacted_audit_excludes_other_underlyings() -> None:
    result = _redacted_order_audit(
        [_order("WORKING", "XSP  260831C00640000", "one")], "SPX"
    )

    assert result["top_level_orders"] == 0
    assert result["active_order_nodes"] == 0
