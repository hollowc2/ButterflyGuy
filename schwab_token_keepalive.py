"""Keep the Schwab OAuth token alive by making a lightweight API call.

Run this via cron on weekends/holidays to prevent the 7-day refresh token
from expiring due to inactivity. On trading days the live bot handles this.

Cron example (runs 9am Saturday and Sunday):
  0 9 * * 6,0 /opt/butterflyguy/.venv/bin/python /opt/butterflyguy/schwab_token_keepalive.py
"""

import sys
from pathlib import Path
from dotenv import dotenv_values
from schwab.auth import client_from_token_file

ROOT = Path(__file__).parent
env = dotenv_values(ROOT / ".env")

TOKEN_PATH = ROOT / "tokens.json"
API_KEY = env.get("SCHWAB_API_KEY")
SECRET_KEY = env.get("SCHWAB_SECRET_KEY")

if not TOKEN_PATH.exists():
    print(f"ERROR: token file not found at {TOKEN_PATH}")
    sys.exit(1)

if not API_KEY or not SECRET_KEY:
    print("ERROR: SCHWAB_API_KEY / SCHWAB_SECRET_KEY not found in .env")
    sys.exit(1)

try:
    client = client_from_token_file(
        token_path=str(TOKEN_PATH),
        api_key=API_KEY,
        app_secret=SECRET_KEY,
        asyncio=False,
        enforce_enums=False,
    )
    # Lightweight call — just enough to trigger an access token refresh
    resp = client.get_quote("$SPX")
    resp.raise_for_status()
    print(f"OK: token refreshed, SPX quote fetched (status {resp.status_code})")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
