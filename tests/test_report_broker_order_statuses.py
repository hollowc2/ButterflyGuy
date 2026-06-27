from butterfly_guy.scripts.report_broker_order_statuses import _status_category, _summarize


def test_status_category_maps_known_broker_statuses():
    assert _status_category("FILLED") == "filled"
    assert _status_category("REJECTED") == "rejected"
    assert _status_category("EXPIRED") == "expired"
    assert _status_category("WORKING") == "working"
    assert _status_category("NOT_IN_OUR_MATRIX") == "unknown"
    assert _status_category(None) == "missing"
    for status in ("PARTIAL", "PARTIAL_FILL", "PARTIALLY_FILLED"):
        assert _status_category(status) == "partial"
    for status in ("CANCEL_PENDING", "PENDING_CANCEL", "CANCEL_REQUESTED"):
        assert _status_category(status) == "cancel_pending"


def test_summarize_walks_child_orders_and_classifies_child_statuses():
    order = {
        "orderId": "parent",
        "status": "REJECTED",
        "orderLegCollection": [
            {"instrument": {"symbol": "SPXW  260626P06000000"}},
        ],
        "childOrderStrategies": [
            {
                "status": "FILLED",
                "orderLegCollection": [
                    {"instrument": {"symbol": "SPXW  260626P05950000"}},
                ],
            },
            {
                "status": "PENDING_CANCEL",
                "orderLegCollection": [
                    {"instrument": {"symbol": "SPXW  260626P05900000"}},
                ],
            },
        ],
    }

    summary = _summarize(order)

    assert summary["status_category"] == "rejected"
    assert summary["child_statuses"] == ["FILLED", "PENDING_CANCEL"]
    assert summary["child_status_categories"] == ["filled", "cancel_pending"]
    assert summary["symbols"] == [
        "SPXW  260626P06000000",
        "SPXW  260626P05950000",
        "SPXW  260626P05900000",
    ]
