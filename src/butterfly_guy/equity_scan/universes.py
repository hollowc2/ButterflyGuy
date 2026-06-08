"""Universe loaders for S&P 500, Nasdaq-100, and custom watchlists."""

from __future__ import annotations

import csv
import io
import json
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


def fetch_sp500_rows() -> list[dict[str, str]]:
    """Download S&P 500 constituents with GICS sector metadata."""
    req = urllib.request.Request(SP500_CSV_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode()
    return list(csv.DictReader(io.StringIO(text)))


def fetch_sp500_tickers() -> list[str]:
    """Download the current S&P 500 constituents list."""
    rows = fetch_sp500_rows()
    return sorted({row["Symbol"].strip().upper() for row in rows if row.get("Symbol")})


def fetch_sp500_sectors() -> dict[str, str]:
    """Map S&P 500 tickers to GICS sector names."""
    sectors: dict[str, str] = {}
    for row in fetch_sp500_rows():
        symbol = (row.get("Symbol") or "").strip().upper()
        sector = (row.get("GICS Sector") or "").strip()
        if symbol and sector:
            sectors[symbol] = sector
    return sectors


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


def write_sector_map(path: Path, sectors: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(sorted(sectors.items())), indent=2) + "\n")


def load_sector_map(universe_dir: str | Path) -> dict[str, str]:
    """Load symbol -> GICS sector mapping written by refresh_equity_universes."""
    path = Path(universe_dir) / "sectors.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        return {}
    return {str(symbol).upper(): str(sector) for symbol, sector in data.items()}


def lookup_sector(symbol: str, sector_map: dict[str, str]) -> str:
    return sector_map.get(symbol.upper(), "Unknown")


def refresh_builtin_universes(universe_dir: str | Path) -> dict[str, int]:
    """Refresh sp500.txt, nq100.txt, and sectors.json from public sources."""
    base = Path(universe_dir)
    sp500 = fetch_sp500_tickers()
    nq100 = fetch_nq100_tickers()
    sectors = fetch_sp500_sectors()
    write_universe_file(base / "sp500.txt", sp500)
    write_universe_file(base / "nq100.txt", nq100)
    write_sector_map(base / "sectors.json", sectors)
    return {"sp500": len(sp500), "nq100": len(nq100), "sectors": len(sectors)}
