"""One explicitly requested research acquisition; disabled without an exact opt-in.

No polling, order client, automatic DDL or active configuration import. The
context file is predeclared non-secret research identity, not selected by hindsight.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from butterfly_guy.research.ndx_observer import Acquisition, create_observer


async def main():
    if os.environ.get("NDX_OBSERVER_ENABLED", "false") != "true":
        return {"status": "disabled"}
    raw = json.loads(Path(os.environ["NDX_OBSERVER_CONTEXT_FILE"]).read_text())
    raw["expected_symbols"] = tuple(raw["expected_symbols"])
    context = Acquisition(**raw)
    observer = create_observer(enabled=True,
        connection_factory=lambda: {"dsn": os.environ["NDX_OBSERVER_DATABASE_DSN"]},
        gateway_url=os.environ["NDX_OBSERVER_GATEWAY_URL"],
        gateway_api_key=os.environ["NDX_OBSERVER_GATEWAY_KEY"])
    try:
        await observer.start()
        result = await observer.acquire(context)
        return {"quote_status": result.quote_status, "recording_status": result.recording_status,
                "receipt_journaled": bool(result.receipt and result.receipt["receipt_journaled"])}
    finally:
        await observer.close()


if __name__ == "__main__":
    # No exception/HTTP/auth context is printed by this research executable.
    try:
        print(json.dumps(asyncio.run(main())))
    except Exception:
        print(json.dumps({"status": "observer_failed", "details": "categorical_only"}))
        raise SystemExit(1) from None
