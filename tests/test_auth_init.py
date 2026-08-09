import runpy
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize(
    "process_env,dotenv_value,expected",
    [
        (None, None, "tokens.json"),
        (None, "/srv/schwab/tokens.json", "/srv/schwab/tokens.json"),
        ("/srv/schwab/tokens.json", "tokens.json", "/srv/schwab/tokens.json"),
    ],
)
def test_auth_init_honours_schwab_token_path(
    monkeypatch, capsys, process_env, dotenv_value, expected
):
    """SCHWAB_TOKEN_PATH picks the write target, process env winning over .env."""
    easy_client = MagicMock()
    dotenv = {"SCHWAB_API_KEY": "key", "SCHWAB_SECRET_KEY": "secret"}
    if dotenv_value is not None:
        dotenv["SCHWAB_TOKEN_PATH"] = dotenv_value

    monkeypatch.delenv("SCHWAB_TOKEN_PATH", raising=False)
    if process_env is not None:
        monkeypatch.setenv("SCHWAB_TOKEN_PATH", process_env)
    monkeypatch.setattr("dotenv.dotenv_values", lambda _path: dotenv)
    monkeypatch.setattr("schwab.auth.easy_client", easy_client)

    runpy.run_path("tools/auth_init.py", run_name="__main__")

    assert easy_client.call_args.args[3] == expected
    assert f"{expected} created successfully" in capsys.readouterr().out
