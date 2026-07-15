from unittest.mock import Mock

from butterfly_guy.core.metrics import (
    _MetricsHandler,
    clear_readiness,
    readiness_snapshot,
    set_readiness,
)


def test_readiness_tracks_degraded_reason():
    set_readiness(None)
    set_readiness("broker_reconciliation_unsafe")
    assert readiness_snapshot() == (False, "broker_reconciliation_unsafe")

    set_readiness(None)
    assert readiness_snapshot() == (True, None)


def test_readiness_recovery_clears_only_its_own_reason():
    set_readiness(None)
    set_readiness("entry_loop_repeated_failures")
    set_readiness("settlement_evidence_unavailable")

    clear_readiness("entry_loop_repeated_failures")

    assert readiness_snapshot() == (False, "settlement_evidence_unavailable")
    set_readiness(None)


def test_health_stays_live_while_ready_reports_degraded():
    handler = object.__new__(_MetricsHandler)
    handler._send_json = Mock()
    set_readiness("broker_reconciliation_unsafe")

    handler.path = "/health"
    handler.do_GET()
    assert handler._send_json.call_args.args[0] == 200

    handler.path = "/ready"
    handler.do_GET()
    assert handler._send_json.call_args.args == (
        503,
        {"status": "not_ready", "reason": "broker_reconciliation_unsafe"},
    )
    set_readiness(None)
