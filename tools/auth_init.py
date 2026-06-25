"""Run once to generate tokens.json via Schwab OAuth flow."""
from dotenv import dotenv_values
from schwab.auth import easy_client

env = dotenv_values(".env")
c = easy_client(
    env["SCHWAB_API_KEY"],
    env["SCHWAB_SECRET_KEY"],
    "https://127.0.0.1:8182",
    "tokens.json",
)
print("tokens.json created successfully")
