"""Run once to generate tokens.json via Schwab OAuth flow."""
import os

from dotenv import dotenv_values
from schwab.auth import easy_client

env = dotenv_values(".env")
token_path = (
    os.getenv("SCHWAB_TOKEN_PATH") or env.get("SCHWAB_TOKEN_PATH") or "tokens.json"
)
c = easy_client(
    env["SCHWAB_API_KEY"],
    env["SCHWAB_SECRET_KEY"],
    "https://127.0.0.1:8182",
    token_path,
)
print(f"{token_path} created successfully")
