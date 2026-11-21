"""Lightweight Telegram and ButterflyGuy Alertmanager helpers.

Usage:
    from butterfly_guy.notify import send
    send("Something went wrong")

From async code, use ``await send_async(...)`` so the blocking HTTP call runs
in a worker thread instead of stalling the event loop.

Requires env vars:
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
"""

import asyncio
import datetime as dt
import json
import os
import urllib.parse
import urllib.request

import aiohttp

TELEGRAM_HTTP_TIMEOUT_SECONDS = 10


def send(message: str) -> bool:
    """Send a Telegram message. Returns True on success, False on failure."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


async def send_async(message: str) -> bool:
    """Async-safe :func:`send`: runs the blocking request in a worker thread."""
    return await asyncio.to_thread(send, message)


async def send_checked_async(message: str) -> bool:
    """Cancellable, bounded Telegram transport for durable account-alert delivery.

    Keep the existing thread-based helper's behavior for its other callers. DNS,
    connection and response operations here share one aiohttp total deadline.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    timeout = aiohttp.ClientTimeout(total=TELEGRAM_HTTP_TIMEOUT_SECONDS, connect=5, sock_read=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
            ) as response:
                return response.status == 200
    except Exception:
        # Transport exceptions may contain the bot token in the request URL.
        return False


def send_alertmanager(
    url: str,
    condition: str,
    underlying: str,
    *,
    resolved: bool = False,
    instance_role: str | None = None,
) -> bool:
    """Post one stable, identifier-free alert fingerprint to Alertmanager.

    instance_role, when set, is part of the alert's identity, so a paper and a live bot
    on the same underlying never merge or resolve each other's alerts.
    """
    now = dt.datetime.now(dt.timezone.utc)
    alertname = "ButterflyGuy" + "".join(part.title() for part in condition.split("_"))
    labels = {
        "alertname": alertname,
        "condition": condition,
        "underlying": underlying.upper(),
        "project": "butterflyguy",
        "notify": "discord",
        "severity": "critical",
    }
    subject = underlying.upper()
    if instance_role:
        labels["instance_role"] = instance_role
        subject = f"{subject} {instance_role}"
    payload = [
        {
            "labels": labels,
            "annotations": {
                "summary": f"ButterflyGuy {subject} {condition.replace('_', ' ')}",
                "description": (
                    "Condition cleared after safe reconciliation or recovery."
                    if resolved
                    else {
                        "broker_ambiguity": (
                            "Broker order state is ambiguous. Entries stopped; "
                            "manual reconciliation required."
                        ),
                        "reconciliation_failure": (
                            "Broker/database reconciliation failed. Trading is blocked; "
                            "manual review required."
                        ),
                        "settlement_failure": (
                            "Settlement evidence is unavailable. The trade remains open; "
                            "manual review required."
                        ),
                        "token_expiry": (
                            "Schwab refresh token is near expiry or expired. "
                            "Re-authentication is required."
                        ),
                    }.get(condition, "Critical safety condition requires manual review.")
                ),
            },
            "startsAt": (now - dt.timedelta(seconds=1) if resolved else now).isoformat(),
            "endsAt": (now if resolved else now + dt.timedelta(days=365)).isoformat(),
        }
    ]
    request = urllib.request.Request(
        f"{url.rstrip('/')}/api/v2/alerts",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return 200 <= response.status < 300
    except Exception:
        return False
