"""Refresh S&P 500 and Nasdaq-100 universe files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.equity_scan.config import load_equity_scan_config
from butterfly_guy.equity_scan.universes import refresh_builtin_universes


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh sp500.txt and nq100.txt")
    parser.add_argument(
        "--scan-config",
        default="configs/equity_scan.yaml",
        help="Equity scan config",
    )
    args = parser.parse_args()

    scan_config = load_equity_scan_config(args.scan_config)
    counts = refresh_builtin_universes(scan_config.universe_dir)
    print(f"Refreshed universes in {scan_config.universe_dir}: {counts}")


if __name__ == "__main__":
    main()
