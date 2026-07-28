import json

from butterfly_guy.scripts.report_broker_order_statuses import (
    _build_payload,
    _status_category,
    _summarize,
)


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
                "childOrderStrategies": [{"status": "PARTIALLY_FILLED"}],
            },
        ],
    }

    summary = _summarize(order)

    assert summary["status_category"] == "rejected"
    assert summary["child_statuses"] == ["FILLED", "PENDING_CANCEL", "PARTIALLY_FILLED"]
    assert summary["child_status_categories"] == [
        "filled",
        "cancel_pending",
        "partial",
    ]
    assert summary["symbol_roots"] == ["SPXW"]
    assert "order_id" not in summary
    assert "symbols" not in summary


def test_payload_counts_parent_and_descendant_statuses():
    payload = _build_payload(
        [
            {
                "status": "WORKING",
                "orderLegCollection": [
                    {"instrument": {"symbol": "SPXW  260711C06000000"}}
                ],
                "childOrderStrategies": [
                    {
                        "status": "FILLED",
                        "childOrderStrategies": [
                            {"status": "NEW_BROKER_STATE"},
                            {},
                        ],
                    }
                ],
            }
        ],
        "2026-07-11",
    )

    assert payload["status_counts"] == {
        "WORKING": 1,
        "FILLED": 1,
        "NEW_BROKER_STATE": 1,
        "<missing>": 1,
    }
    assert payload["status_category_counts"] == {
        "working": 1,
        "filled": 1,
        "unknown": 1,
        "missing": 1,
    }
    json.dumps(payload, sort_keys=True)


def test_payload_excludes_non_spx_orders():
    payload = _build_payload(
        [
            {
                "status": "WORKING",
                "orderLegCollection": [
                    {"instrument": {"symbol": "SPXW  260711C06000000"}}
                ],
            },
            {
                "status": "FILLED",
                "orderLegCollection": [{"instrument": {"symbol": "AAPL"}}],
            },
            {
                "status": "REJECTED",
                "orderLegCollection": [
                    {"instrument": {"symbol": "XSP  260711C00600000"}}
                ],
            },
        ],
        "2026-07-11",
    )

    assert payload["status_counts"] == {"WORKING": 1}
    assert len(payload["orders"]) == 1
    assert "raw_orders" not in payload


def test_payload_filters_explicit_xsp_underlying():
    payload = _build_payload(
        [
            {
                "status": "WORKING",
                "orderLegCollection": [
                    {"instrument": {"symbol": "XSP  260713C00600000"}}
                ],
            },
            {
                "status": "FILLED",
                "orderLegCollection": [
                    {"instrument": {"symbol": "SPXW  260713C06000000"}}
                ],
            },
            {
                "status": "REJECTED",
                "orderLegCollection": [{"instrument": {"symbol": "AAPL"}}],
            },
        ],
        "2026-07-13",
        underlying="XSP",
    )

    assert payload["status_counts"] == {"WORKING": 1}
    assert payload["orders"][0]["symbol_roots"] == ["XSP"]
