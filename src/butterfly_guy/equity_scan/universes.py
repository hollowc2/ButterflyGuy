"""Universe loaders for S&P 500, Nasdaq-100, and custom watchlists."""

from __future__ import annotations

import csv
import io
import re
import urllib.request
from pathlib import Path

SP500_CSV_URL = (
    "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
)
NQ100_WIKI_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"
USER_AGENT = "butterflyguy-equity-scan/1.0"


def _read_ticker_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    tickers: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip().upper()
        if line:
            tickers.append(line)
    return tickers


def load_universe(name: str, *, universe_dir: Path, custom_path: Path) -> list[str]:
    """Load tickers for a named universe."""
    if name == "custom":
        return _read_ticker_file(custom_path)
    path = universe_dir / f"{name}.txt"
    return _read_ticker_file(path)


def load_universes(
    names: list[str],
    *,
    universe_dir: str | Path,
    custom_watchlist: str | Path,
) -> dict[str, list[str]]:
    """Load all requested universes."""
    base = Path(universe_dir)
    custom_path = Path(custom_watchlist)
    return {name: load_universe(name, universe_dir=base, custom_path=custom_path) for name in names}


def build_symbol_map(universes: dict[str, list[str]]) -> dict[str, set[str]]:
    """Map each symbol to the universes it belongs to."""
    symbol_map: dict[str, set[str]] = {}
    for universe_name, tickers in universes.items():
        for ticker in tickers:
            symbol_map.setdefault(ticker, set()).add(universe_name)
    return symbol_map


def fetch_sp500_tickers() -> list[str]:
    """Download the current S&P 500 constituents list."""
    req = urllib.request.Request(SP500_CSV_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode()
    rows = csv.DictReader(io.StringIO(text))
    return sorted({row["Symbol"].strip().upper() for row in rows if row.get("Symbol")})


def fetch_nq100_tickers() -> list[str]:
    """Download the current Nasdaq-100 constituents from Wikipedia."""
    req = urllib.request.Request(NQ100_WIKI_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode()

    tickers = re.findall(r"<td>([A-Z][A-Z0-9.]*)</td>", html)
    ordered: list[str] = []
    seen: set[str] = set()
    for ticker in tickers:
        if ticker in seen:
            continue
        seen.add(ticker)
        ordered.append(ticker)
    return ordered


def write_universe_file(path: Path, tickers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(tickers) + "\n")


def refresh_builtin_universes(universe_dir: str | Path) -> dict[str, int]:
    """Refresh sp500.txt and nq100.txt from public sources."""
    base = Path(universe_dir)
    sp500 = fetch_sp500_tickers()
    nq100 = fetch_nq100_tickers()
    write_universe_file(base / "sp500.txt", sp500)
    write_universe_file(base / "nq100.txt", nq100)
    return {"sp500": len(sp500), "nq100": len(nq100)}
