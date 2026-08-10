"""Keep the Schwab OAuth token alive and alert before refresh token expiry.

Schwab refresh tokens have a hard 7-day expiry from issue date.
This script raises one centrally deduplicated alert starting 24 hours before expiry.
Also sends a weekly reminder the day before, so the re-auth can be planned.

The re-auth cadence is Saturday: each new expiry is exactly 7 days after the moment of
re-authorization, so re-authorizing on a Saturday keeps every future deadline on a
Saturday. The reminder therefore fires Friday, and the alert window has to be wide
enough to open before that Saturday morning.

Cron: run hourly plus a dedicated Friday 07:00 PDT reminder.
  0 * * * * /opt/butterflyguy/.venv/bin/python /opt/butterflyguy/tools/schwab_token_keepalive.py >> /opt/butterflyguy/keepalive.log 2>&1
  0 14 * * 5 /opt/butterflyguy/.venv/bin/python /opt/butterflyguy/tools/schwab_token_keepalive.py --weekly-reminder >> /opt/butterflyguy/keepalive.log 2>&1
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import dotenv_values

from butterfly_guy.notify import send as notify
from butterfly_guy.notify import send_alertmanager

# "--sunday-reminder" is the pre-2026-08-09 spelling, still accepted so that a host whose
# crontab has not been updated yet keeps sending reminders instead of silently sending none.
WEEKLY_REMINDER = "--weekly-reminder" in sys.argv or "--sunday-reminder" in sys.argv

ROOT = Path(__file__).parent.parent
env = dotenv_values(ROOT / ".env")

TOKEN_PATH = Path(
    os.getenv("SCHWAB_TOKEN_PATH") or env.get("SCHWAB_TOKEN_PATH") or "tokens.json"
)
if not TOKEN_PATH.is_absolute():
    TOKEN_PATH = ROOT / TOKEN_PATH
ALERTMANAGER_URL = os.getenv("ALERTMANAGER_URL", "http://127.0.0.1:9093")
API_KEY = env.get("SCHWAB_API_KEY")
SECRET_KEY = env.get("SCHWAB_SECRET_KEY")

REFRESH_TOKEN_TTL = 7 * 24 * 3600  # 7 days in seconds
# 24h, not 8h: at 8h the window opened at 07:05 PDT on the Saturday the token died, which
# is the same morning the re-auth has to happen. A day of warning covers the Friday too.
WARN_BEFORE = 24 * 3600             # start alerting 24 hours before expiry
LOCK_TIMEOUT = 30.0                 # wait out a gateway write before giving up

if not TOKEN_PATH.exists():
    print(f"ERROR: token file not found at {TOKEN_PATH}")
    sys.exit(1)

if not API_KEY or not SECRET_KEY:
    print("ERROR: SCHWAB_API_KEY / SCHWAB_SECRET_KEY not found in .env")
    sys.exit(1)

# Check refresh token expiry
with open(TOKEN_PATH) as f:
    token_data = json.load(f)

creation_ts = token_data.get("creation_timestamp", 0)
expiry_ts = creation_ts + REFRESH_TOKEN_TTL
now = time.time()
seconds_remaining = expiry_ts - now
hours_remaining = seconds_remaining / 3600


if WEEKLY_REMINDER:
    expiry_utc = time.strftime("%a %Y-%m-%d %H:%MZ", time.gmtime(expiry_ts))
    notify(
        "📅 Weekly reminder: re-authorize Schwab tomorrow (Saturday), early in the day.\n"
        f"Refresh token expires {expiry_utc}, in {hours_remaining:.1f}h.\n"
        "Run auth_init.py in a real terminal on zeus, not through an agent session.\n"
        "Checklist: docs/runbooks/ (reauthorization-*-checklist.md)",
    )
    print(
        f"WEEKLY REMINDER: sent, refresh token expires {expiry_utc} "
        f"({hours_remaining:.1f}h)"
    )

if seconds_remaining <= 0:
    alert_accepted = send_alertmanager(
        ALERTMANAGER_URL,
        "token_expiry",
        "ALL",
    )
    alert_result = "sent" if alert_accepted else "failed"
    print(
        f"TOKEN ALERT: {alert_result}; refresh token expired "
        f"{abs(hours_remaining):.1f}h ago"
    )
elif seconds_remaining <= WARN_BEFORE:
    alert_accepted = send_alertmanager(
        ALERTMANAGER_URL,
        "token_expiry",
        "ALL",
    )
    alert_result = "sent" if alert_accepted else "failed"
    print(
        f"TOKEN ALERT: {alert_result}; refresh token expires in "
        f"{hours_remaining:.1f}h"
    )
else:
    alert_accepted = send_alertmanager(
        ALERTMANAGER_URL,
        "token_expiry",
        "ALL",
        resolved=True,
    )
    alert_result = "resolved" if alert_accepted else "failed"
    print(f"TOKEN ALERT: {alert_result}; refresh token is healthy")

# Always try to refresh the access token. The gateway writes this same document, so the
# whole read-refresh-write has to be one critical section: the two writers would otherwise
# interleave and the later write would clobber the earlier one's access token.
#
# Schwab does NOT rotate the refresh token on an ordinary access-token refresh -- verified
# 2026-08-08, where the same value survived both a gateway refresh and a keepalive firing.
# The lock is still required for the reason above; it is not guarding a consumable token.
try:
    from schwab.auth import client_from_token_file

    from butterfly_guy.schwab_gateway.token_manager import (
        AtomicFileTokenStore,
        TokenLockTimeoutError,
    )
    try:
        with AtomicFileTokenStore(TOKEN_PATH).locked(LOCK_TIMEOUT):
            client = client_from_token_file(
                token_path=str(TOKEN_PATH),
                api_key=API_KEY,
                app_secret=SECRET_KEY,
                asyncio=False,
                enforce_enums=False,
            )
            resp = client.get_quote("$SPX")
    except TokenLockTimeoutError:
        print(f"ERROR: token lock held by another writer after {LOCK_TIMEOUT:.0f}s")
        sys.exit(1)
    resp.raise_for_status()
    print(
        f"OK: token refreshed, SPX quote fetched (status {resp.status_code}), "
        f"refresh token expires in {hours_remaining:.1f}h"
    )
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

if not alert_accepted:
    sys.exit(1)
