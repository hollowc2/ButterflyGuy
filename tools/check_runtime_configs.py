"""Validate the checkout's runtime configs against the checkout's own code.

The SPX/NDX containers bind-mount configs from /opt/butterflyguy, and the cron
jobs load them with the checkout's code. A deploy that adds a config key without
also updating the checkout breaks every cron job in load_config(). Run this
every morning under tools/cron_guard.py so that drift alerts hours before the
evening Discord jobs would fail. See infra/cron/runtime_config_check.cron.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from butterfly_guy.core.config import load_config  # noqa: E402
from butterfly_guy.reports.daily_report_card_config import (  # noqa: E402
    load_daily_report_card_config,
)

APP_CONFIGS = ("config.yaml", "config_ndx.yaml", "config_xsp.yaml")


def main(config_dir: Path = ROOT / "configs") -> int:
    failures = 0
    for name in APP_CONFIGS:
        path = config_dir / name
        try:
            if not path.is_file():
                raise FileNotFoundError(path)
            load_config(str(path))
        except Exception as exc:
            failures += 1
            print(f"FAIL {name}: {exc}")
        else:
            print(f"ok   {name}")
    try:
        load_daily_report_card_config(str(config_dir / "daily_report_card.yaml"))
    except Exception as exc:
        failures += 1
        print(f"FAIL daily_report_card.yaml: {exc}")
    else:
        print("ok   daily_report_card.yaml")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
