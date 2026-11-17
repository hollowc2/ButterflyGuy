"""Opt-in startup guard for running a paper SPX bot and a live SPX bot side by side.

BUTTERFLY_INSTANCE_ROLE is unset by default, and then nothing here runs. When it is set,
startup refuses a container whose mode or database does not match its role, before any
Schwab call or database write. See docs/operations/concurrent-paper-live-spx-design.md §6.
"""

from __future__ import annotations

import os
from typing import Any

from butterfly_guy.core.config import AppConfig

ROLE_ENV = "BUTTERFLY_INSTANCE_ROLE"
ROLES = ("paper", "live", "live_rehearsal")
# The paper bot's database. A live or rehearsal bot must never write to it.
PAPER_DATABASE_NAME = "butterfly_guy"


class InstanceRoleError(RuntimeError):
    """The container's configuration contradicts its declared instance role."""


def instance_role() -> str | None:
    """Return the declared role, None when unset or empty; refuse unknown values."""
    role = os.environ.get(ROLE_ENV, "").strip()
    if not role:
        return None
    if role not in ROLES:
        raise InstanceRoleError(f"{ROLE_ENV}={role!r} is not one of {', '.join(ROLES)}")
    return role


def check_config(config: AppConfig, role: str | None) -> None:
    """Refuse a role whose paper/live mode or database name is wrong."""
    if role is None:
        return
    paper = config.execution.paper_trading
    if role == "paper" and not paper:
        raise InstanceRoleError("role=paper but execution.paper_trading is false")
    if role == "live" and paper:
        raise InstanceRoleError("role=live but execution.paper_trading is true")
    if role == "live_rehearsal" and not paper:
        raise InstanceRoleError("role=live_rehearsal but execution.paper_trading is false")
    if role in ("live", "live_rehearsal") and config.database.name == PAPER_DATABASE_NAME:
        raise InstanceRoleError(
            f"role={role} must not use the paper database {PAPER_DATABASE_NAME!r}"
        )


async def check_database(pool: Any, role: str | None) -> None:
    """Refuse a live bot whose database holds any paper trade.

    Read-only, and run before migrations: a brand-new database has no trades table yet.
    """
    if role != "live":
        return
    if not await pool.fetchval("SELECT to_regclass('public.butterfly_trades') IS NOT NULL"):
        return
    paper_rows = await pool.fetchval(
        "SELECT count(*) FROM butterfly_trades WHERE metadata ? 'paper_fill_model'"
    )
    if paper_rows:
        raise InstanceRoleError(
            f"role=live but the database holds {paper_rows} paper trade(s) "
            "(metadata.paper_fill_model)"
        )
