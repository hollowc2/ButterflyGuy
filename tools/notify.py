"""Lightweight Telegram and ButterflyGuy Alertmanager helpers.

Usage:
    from notify import send
    send("Something went wrong")

Requires env vars:
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
"""

import datetime as dt
import json
import os
import urllib.parse
import urllib.request


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


def send_alertmanager(
    url: str,
    condition: str,
    underlying: str,
    *,
    resolved: bool = False,
) -> bool:
    """Post one stable, identifier-free alert fingerprint to Alertmanager."""
    now = dt.datetime.now(dt.timezone.utc)
    alertname = "ButterflyGuy" + "".join(part.title() for part in condition.split("_"))
    payload = [
        {
            "labels": {
                "alertname": alertname,
                "condition": condition,
                "underlying": underlying.upper(),
                "project": "butterflyguy",
                "notify": "discord",
                "severity": "critical",
            },
            "annotations": {
                "summary": f"ButterflyGuy {underlying.upper()} {condition.replace('_', ' ')}",
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
