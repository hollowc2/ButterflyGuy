"""Live entry stop signals and the operator's session supervision attestation."""

from __future__ import annotations

import datetime as dt
import os

from butterfly_guy.core.time_utils import EASTERN, market_close_time, now_eastern


class LiveSafetyError(RuntimeError):
    """Stop entries for this runtime; keep position monitoring running."""


def require_spx_supervision(now: dt.datetime | None = None) -> None:
    """Require a named operator through today's cash close, renewed each session.

    This is an operator attestation, not a check of physical phone availability.
    It expires by date even if someone accidentally supplies a far-future time.
    """
    current = (now or now_eastern()).astimezone(EASTERN)
    try:
        until = dt.datetime.fromisoformat(os.getenv("LIVE_SUPERVISION_UNTIL", ""))
    except ValueError as exc:
        raise LiveSafetyError("LIVE_SUPERVISION_UNTIL must be an aware ISO timestamp") from exc
    close = dt.datetime.combine(current.date(), market_close_time(current.date()), tzinfo=EASTERN)
    if (
        not os.getenv("LIVE_SUPERVISOR", "").strip()
        or until.tzinfo is None
        or until.astimezone(EASTERN).date() != current.date()
        or until < max(current, close)
    ):
        raise LiveSafetyError("SPX requires a named reachable supervisor through today's close")
