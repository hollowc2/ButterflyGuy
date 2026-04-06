"""Keep the Schwab OAuth token alive and alert before refresh token expiry.

Schwab refresh tokens have a hard 7-day expiry from issue date.
This script sends a Telegram alert 8 hours before expiry and every hour after.
Also sends a weekly Sunday evening reminder to re-auth before the new week.

Cron: run hourly + dedicated Sunday 6:50 PM PDT run
  0 * * * * /opt/butterflyguy/.venv/bin/python /opt/butterflyguy/schwab_token_keepalive.py >> /opt/butterflyguy/keepalive.log 2>&1
  50 1 * * 1 /opt/butterflyguy/.venv/bin/python /opt/butterflyguy/schwab_token_keepalive.py --sunday-reminder >> /opt/butterflyguy/keepalive.log 2>&1
"""

import json
import sys
import time
from pathlib import Path
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).parent))
from notify import send as notify

SUNDAY_REMINDER = "--sunday-reminder" in sys.argv

ROOT = Path(__file__).parent
env = dotenv_values(ROOT / ".env")

TOKEN_PATH = ROOT / "tokens.json"
API_KEY = env.get("SCHWAB_API_KEY")
SECRET_KEY = env.get("SCHWAB_SECRET_KEY")

REFRESH_TOKEN_TTL = 7 * 24 * 3600  # 7 days in seconds
WARN_BEFORE = 8 * 3600              # start alerting 8 hours before expiry

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

if SUNDAY_REMINDER:
    notify(f"📅 Weekly reminder: re-auth Schwab before market open tomorrow.\nRefresh token expires in {hours_remaining:.1f}h.\ncd /opt/butterflyguy && .venv/bin/python auth_init.py")
    print(f"SUNDAY REMINDER: sent, refresh token expires in {hours_remaining:.1f}h")

if seconds_remaining <= 0:
    notify(f"🚨 Schwab refresh token has EXPIRED. Re-auth required immediately: cd /opt/butterflyguy && .venv/bin/python auth_init.py")
    print(f"ALERT: refresh token expired {abs(hours_remaining):.1f}h ago")
elif seconds_remaining <= WARN_BEFORE:
    notify(f"⏰ Schwab refresh token expires in {hours_remaining:.1f} hours. Re-auth soon: cd /opt/butterflyguy && .venv/bin/python auth_init.py")
    print(f"ALERT: refresh token expires in {hours_remaining:.1f}h")

# Always try to refresh the access token
try:
    from schwab.auth import client_from_token_file
    client = client_from_token_file(
        token_path=str(TOKEN_PATH),
        api_key=API_KEY,
        app_secret=SECRET_KEY,
        asyncio=False,
        enforce_enums=False,
    )
    resp = client.get_quote("$SPX")
    resp.raise_for_status()
    print(f"OK: token refreshed, SPX quote fetched (status {resp.status_code}), refresh token expires in {hours_remaining:.1f}h")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
