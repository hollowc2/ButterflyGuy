"""Exit transport contracts and channel selection; no network or broker calls."""

import datetime as dt
from unittest.mock import AsyncMock, MagicMock

import pytest

from butterfly_guy.services.exit_notifications import trade_notifier
from butterfly_guy.services.notifier import DiscordNotifier


@pytest.mark.parametrize("status,accepted", [(200, True), (204, True), (400, False),
                                            (429, False), (500, False)])
async def test_exit_reports_transport_acceptance(monkeypatch, status, accepted):
    response = MagicMock(status=status)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    session.post.return_value = response
    monkeypatch.setattr("butterfly_guy.services.notifier.aiohttp.ClientSession",
                        MagicMock(return_value=session))
    notifier = DiscordNotifier("https://invalid.example/isolated")
    assert await notifier.notify_exit(1, "SPX", "CALL", "end_of_day", 3.75, 3.38,
                                      -0.37, 3.83) is accepted
    assert session.post.call_args.kwargs["timeout"].total == 10


async def test_exit_timeout_redacts_exception_details(monkeypatch):
    logger = MagicMock()
    monkeypatch.setattr("butterfly_guy.services.notifier.log", logger)
    monkeypatch.setattr("butterfly_guy.services.notifier.aiohttp.ClientSession",
                        MagicMock(side_effect=TimeoutError("secret-webhook-and-credentials")))
    assert not await DiscordNotifier("private").notify_exit(
        1, "SPX", "CALL", "end_of_day", 3.75, 3.38, -0.37, 3.83,
    )
    logger.error.assert_called_once_with("discord_error", error_type="TimeoutError")


@pytest.mark.parametrize("role,expected", [(None, "paper"), ("paper", "paper"),
                                          ("live", "live"), ("live_rehearsal", "live")])
def test_trade_channel_role_routing(role, expected):
    notifier = trade_notifier("SPX", role, "paper", "live")
    assert notifier.webhook_url == expected
    assert trade_notifier("NDX", role, "paper", "live") is None
    assert trade_notifier("XSP", role, "paper", "live") is None
    if role in {"live", "live_rehearsal"}:
        assert trade_notifier("SPX", role, "paper", "") is None


def test_standalone_live_without_declared_role_uses_live_channel():
    assert trade_notifier("SPX", None, "paper", "live", paper_trading=False).webhook_url == "live"
    assert trade_notifier("SPX", None, "paper", "", paper_trading=False) is None


async def test_reconstructed_exit_uses_persisted_time_quantity_and_role():
    notifier = DiscordNotifier("unused")
    notifier._post = AsyncMock(return_value=True)
    assert await notifier.notify_exit(
        100001, "SPX", "CALL", "end_of_day", 3.75, 3.38, -0.37, 3.83,
        entry_time=dt.datetime(2026, 11, 23, 16, 0, tzinfo=dt.timezone.utc),
        exit_time=dt.datetime(2026, 11, 23, 16, 7, tzinfo=dt.timezone.utc),
        quantity=3, instance_role="live_rehearsal",
    )
    message = notifier._post.await_args.args[0]
    assert "-$111.00" in message
    assert "11:07:00 ET | Held: 7m" in message
    assert "[LIVE_REHEARSAL] SPX" in message
