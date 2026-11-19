"""The concurrent live SPX service is isolated from paper and keeps today's pilot limits."""

from pathlib import Path

import yaml

BASE = yaml.safe_load(Path("infra/docker-compose.yml").read_text())
LIVE_FILE = Path("infra/docker-compose.spx-live.yml")
REHEARSAL_FILE = Path("infra/docker-compose.spx-live-rehearsal.yml")


class _ResetLoader(yaml.SafeLoader):
    """Read compose's `!reset` tag as a marker."""


_ResetLoader.add_constructor("!reset", lambda loader, node: "!reset")

LIVE = yaml.load(LIVE_FILE.read_text(), Loader=_ResetLoader)
REHEARSAL = yaml.load(REHEARSAL_FILE.read_text(), Loader=_ResetLoader)
PAPER = BASE["services"]["app_spx"]
SERVICE = LIVE["services"]["app_spx_live"]
TOOL = LIVE["services"]["spx_live_db_tool"]
TOKEN_DIR = "${SCHWAB_GATEWAY_TOKEN_DIR:?set the host token directory}"

# The replace-paper pilot override's values (infra/docker-compose.spx-live-test.yml,
# 2026-11-11 onward). The concurrent pilot must not change any of them.
PILOT_LIMITS = {
    "SCHWAB_ACCESS_MODE": "direct",
    "SCHWAB_GATEWAY_SHADOW_READS": "false",
    "EXECUTION__PAPER_TRADING": "false",
    "EXECUTION__ALLOW_LIVE_TRADING": "true",
    "ALLOW_LIVE_TRADING": "true",
    "EXECUTION__LIVE_TEST_DATE": "${SPX_LIVE_TEST_DATE:?set supervised session YYYY-MM-DD}",
    "EXECUTION__LIVE_TEST_MAX_DEBIT": "4.0",
    "EXECUTION__RECORD_LIVE_EXECUTION": "true",
    "EXECUTION__LIVE_TEST_QUOTE_MAX_AGE_SECONDS": "10",
    "RISK__MAX_POSITION_SIZE": "1",
    "RISK__MAX_TRADES_PER_DAY": "1",
    "LIVE_ACCOUNT_ALLOCATION": "20000",
    "LIVE_MAX_ACCOUNT_DAILY_LOSS": "500",
}


def test_live_service_is_its_own_project_and_identity():
    assert LIVE["name"] == "butterfly-spx-live"
    assert SERVICE["container_name"] == "butterfly_spx_live_app"
    assert SERVICE["restart"] == "on-failure:3"
    assert SERVICE["ports"] == ["127.0.0.1:8002:8000"]
    assert SERVICE["pull_policy"] == "never" and "build" not in SERVICE
    assert "app_spx_live" not in BASE["services"]
    assert "spx-live" not in Path("infra/docker-compose.yml").read_text()


def test_live_service_uses_its_own_database_role_and_chain_journal():
    env = SERVICE["environment"]
    assert env["BUTTERFLY_INSTANCE_ROLE"] == "live"
    assert env["DATABASE__NAME"] == "butterfly_guy_spx_live"
    assert PAPER["environment"]["DATABASE__NAME"] == "butterfly_guy"
    assert "../data/chains-live:/app/data/chains" in SERVICE["volumes"]
    assert "../data/chains:/app/data/chains" in PAPER["volumes"]
    assert not any(v.startswith("../data/chains:") for v in SERVICE["volumes"])


def test_live_limits_are_unchanged_from_the_pilot():
    env = SERVICE["environment"]
    assert {key: env[key] for key in PILOT_LIMITS} == PILOT_LIMITS
    assert "EXECUTION__EXIT_PRICING" not in env  # mid_walk stays on hold


def test_live_discord_posts_never_use_papers_webhook():
    command = SERVICE["command"][-1]
    assert "DISCORD_WEBHOOK_URL=\"$${DISCORD_WEBHOOK_URL_SPX_LIVE:?" in command
    assert "DISCORD_WEBHOOK_URL" not in SERVICE["environment"]
    assert command.rstrip().endswith(
        "exec python -m butterfly_guy.scripts.run_live --config configs/config.yaml"
    )


def test_live_service_has_papers_hardening_and_token_directory_bind():
    for key in ("read_only", "tmpfs", "security_opt", "cap_drop", "networks"):
        assert SERVICE[key] == PAPER[key], key
    assert f"{TOKEN_DIR}:{TOKEN_DIR}" in SERVICE["volumes"]
    assert SERVICE["environment"]["SCHWAB_TOKEN_PATH"] == f"{TOKEN_DIR}/tokens.json"
    assert LIVE["networks"] == BASE["networks"]


def test_db_tool_never_mounts_tokens_or_starts_with_up():
    assert TOOL["profiles"] == ["tools"]
    assert "volumes" not in TOOL and "ports" not in TOOL
    assert TOOL["image"] == SERVICE["image"]
    for key in ("read_only", "tmpfs", "security_opt", "cap_drop", "networks"):
        assert TOOL[key] == PAPER[key], key


def test_rehearsal_is_paper_on_its_own_database_with_no_live_settings():
    override = REHEARSAL["services"]["app_spx_live"]
    env = override["environment"]
    assert env["BUTTERFLY_INSTANCE_ROLE"] == "live_rehearsal"
    assert env["DATABASE__NAME"] == "butterfly_guy_spx_live_rehearsal"
    assert env["EXECUTION__PAPER_TRADING"] == "true"
    assert env["ALLOW_LIVE_TRADING"] == env["EXECUTION__ALLOW_LIVE_TRADING"] == "false"
    live_only = set(PILOT_LIMITS) - {
        "SCHWAB_ACCESS_MODE",
        "SCHWAB_GATEWAY_SHADOW_READS",
        "EXECUTION__PAPER_TRADING",
        "EXECUTION__ALLOW_LIVE_TRADING",
        "ALLOW_LIVE_TRADING",
    }
    assert {key for key, value in env.items() if value == "!reset"} == live_only
    assert override["volumes"] == ["../data/chains-live-rehearsal:/app/data/chains"]


def test_mid_walk_overlay_sets_only_the_exit_rule():
    overlay = yaml.safe_load(Path("infra/docker-compose.spx-live-mid-walk.yml").read_text())
    assert overlay == {
        "services": {"app_spx_live": {"environment": {"EXECUTION__EXIT_PRICING": "mid_walk"}}}
    }
    # The base live service never sets an exit rule: an unset EXIT_PRICING runs the default.
    assert "EXECUTION__EXIT_PRICING" not in SERVICE["environment"]
