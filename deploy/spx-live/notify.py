"""Post one message to the live SPX Discord channel (decision D6: never paper's webhook)."""
import json
import sys
import urllib.request

from dotenv import dotenv_values

url = dotenv_values("/opt/butterflyguy/.env").get("DISCORD_WEBHOOK_URL_SPX_LIVE")
if not url:
    sys.exit("DISCORD_WEBHOOK_URL_SPX_LIVE missing")
request = urllib.request.Request(
    url,
    data=json.dumps({"content": sys.argv[1][:2000]}).encode(),
    headers={"Content-Type": "application/json", "User-Agent": "butterflyguy-spx-live"},
)
urllib.request.urlopen(request, timeout=15)
