"""Tests for Discord trade notifications."""

from __future__ import annotations

import datetime as dt
import json
import runpy
import sys
import types
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from butterfly_guy.services.notifier import AlertmanagerNotifier, DiscordNotifier

EASTERN = ZoneInfo("America/New_York")


@pytest.mark.parametrize(
    "condition,alertname",
    [
        ("broker_ambiguity", "ButterflyGuyBrokerAmbiguity"),
        ("reconciliation_failure", "ButterflyGuyReconciliationFailure"),
        ("settlement_failure", "ButterflyGuySettlementFailure"),
        ("token_expiry", "ButterflyGuyTokenExpiry"),
    ],
)
def test_alertmanager_payload_has_stable_redacted_fingerprint(
    monkeypatch, condition, alertname
):
    namespace = runpy.run_path("tools/notify.py")
    requests = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def urlopen(request, timeout):
        requests.append(request)
        assert timeout == 5
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)

    for resolved in (False, False, True):
        assert namespace["send_alertmanager"](
            "http://alertmanager:9093",
            condition,
            "xsp",
            resolved=resolved,
        )

    payloads = [json.loads(request.data)[0] for request in requests]
    assert payloads[0]["labels"] == payloads[1]["labels"] == payloads[2]["labels"]
    assert payloads[0]["labels"] == {
        "alertname": alertname,
        "condition": condition,
        "underlying": "XSP",
        "project": "butterflyguy",
        "notify": "discord",
        "severity": "critical",
    }
    assert "XSP" in payloads[0]["annotations"]["summary"]
    assert all(
        sensitive not in json.dumps(payloads).lower()
        for sensitive in ("account", "order_id", "trade_id", "credential")
    )
    assert payloads[2]["endsAt"] < payloads[0]["endsAt"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "condition",
    ["reconciliation_failure", "broker_ambiguity", "settlement_failure"],
)
async def test_alertmanager_failed_resolution_retries_until_accepted(
    monkeypatch, condition
):
    results = iter((False, True))
    calls = []

    def send_alertmanager(*args, **kwargs):
        calls.append((args, kwargs))
        return next(results)

    monkeypatch.setitem(
        sys.modules,
        "notify",
        types.SimpleNamespace(send_alertmanager=send_alertmanager),
    )

    async def to_thread(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(
        "butterfly_guy.services.notifier.asyncio.to_thread",
        to_thread,
    )
    notifier = AlertmanagerNotifier("http://alertmanager:9093", "spx")

    assert not await notifier.resolve_critical(condition)
    await notifier.retry_pending_resolutions()

    assert len(calls) == 2
    assert all(call[1] == {"resolved": True} for call in calls)
    assert not notifier._pending_resolutions


@pytest.mark.asyncio
async def test_alertmanager_new_firing_cancels_stale_pending_resolution(monkeypatch):
    calls = []

    def send_alertmanager(*args, **kwargs):
        calls.append((args, kwargs))
        return False if kwargs.get("resolved") else True

    monkeypatch.setitem(
        sys.modules,
        "notify",
        types.SimpleNamespace(send_alertmanager=send_alertmanager),
    )

    async def to_thread(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(
        "butterfly_guy.services.notifier.asyncio.to_thread",
        to_thread,
    )
    notifier = AlertmanagerNotifier("http://alertmanager:9093", "spx")

    assert not await notifier.resolve_critical("reconciliation_failure")
    assert await notifier.notify_critical("reconciliation_failure")
    await notifier.retry_pending_resolutions()

    assert [kwargs for _args, kwargs in calls] == [{"resolved": True}, {}]
    assert not notifier._pending_resolutions


@pytest.mark.asyncio
async def test_notify_entry_includes_trade_stats():
    notifier = DiscordNotifier("https://example.com/webhook")
    posted: list[str] = []

    async def capture(content: str, **kwargs: object) -> None:
        posted.append(content)

    entry_time = dt.datetime(2026, 6, 6, 10, 15, 30, tzinfo=dt.timezone.utc)

    with patch.object(notifier, "_post", side_effect=capture):
        await notifier.notify_entry(
            trade_id=42,
            underlying="SPX",
            direction="CALL",
            expiration=dt.date(2026, 6, 6),
            lower_strike=6000,
            center_strike=6010,
            upper_strike=6020,
            wing_width=10,
            entry_price=1.25,
            spot=6005.5,
            order_id="PAPER",
            entry_time=entry_time,
            mark_price=1.20,
            ask_price=1.30,
            selected_rr=9.2,
            vix=14.2,
            selection_method="VIX",
            entry_step=1,
            distance_from_spot=4.5,
        )

    assert len(posted) == 1
    msg = posted[0]
    assert "SPX BUTTERFLY ENTERED" in msg
    assert "#42" in msg
    assert "`PAPER`" in msg
    assert "6000 / **6010** / 6020" in msg
    assert "±10 pts" in msg
    assert "Mark $1.20" in msg
    assert "Ask $1.30" in msg
    assert "Fill **$1.25**" in msg
    assert "Spot: 6005.50" in msg
    assert "Center dist: 4.5 pts" in msg
    assert "R/R: 7.0x (scan 9.2x)" in msg
    assert "Breakevens: 6001.25 – 6018.75" in msg
    assert "VIX: 14.20" in msg
    assert "Ladder step: 1" in msg
    assert "Method: VIX" in msg
    assert "Entry: 06:15:30 ET" in msg


@pytest.mark.asyncio
async def test_notify_exit_formats_contract_pnl_as_dollars():
    notifier = DiscordNotifier("https://example.com/webhook")
    posted: list[str] = []

    async def capture(content: str, **kwargs: object) -> None:
        posted.append(content)

    with patch.object(notifier, "_post", side_effect=capture):
        await notifier.notify_exit(
            trade_id=42,
            underlying="SPX",
            direction="CALL",
            exit_reason="cash_settled",
            entry_price=2.0,
            exit_price=3.5,
            pnl=1.5,
            peak_value=4.0,
            quantity=2,
        )

    assert "P&L: **+$300.00** (+75%)" in posted[0]
