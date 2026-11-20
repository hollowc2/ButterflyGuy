"""Bounded quote-only audit; no strategy returns or outcome-based selection."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from tools.research_studies.xsp_independent.common import (
    calendar,
    derive_proxy,
    load_session,
    session_end,
    valid_quotes,
)

SAMPLES = ("2020-01-03", "2023-01-03", "2025-11-28", "2026-01-02", "2026-03-13",
           "2026-07-01", "2026-09-25", "2026-09-28")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = Path("data/thetadata/xsp_0dte")
    support_root = Path("data/research_cache/local_support_v1")
    ticks = pd.read_parquet(support_root / "spot_ticks.parquet")
    daily = pd.read_parquet(support_root / "daily_bars.parquet")
    inventories = {}
    for kind in ("quote_1m", "ohlc_1m", "open_interest", "eod"):
        paths = sorted((root / kind).rglob("*.parquet"))
        inventories[kind] = {"files": len(paths), "first": paths[0].stem,
                             "last": paths[-1].stem,
                             "years": pd.Series([p.parent.name for p in paths]).value_counts().sort_index().to_dict()}
    rows = []
    for day in SAMPLES:
        path = root / "quote_1m" / day[:4] / f"{day}.parquet"
        raw = pd.read_parquet(path)
        quotes = load_session(path)
        proxy = derive_proxy(quotes)
        start = pd.Timestamp(f"{day} 09:31", tz="America/New_York")
        grid = pd.date_range(start, session_end(day) - pd.Timedelta(minutes=1), freq="min")
        valid = valid_quotes(quotes)
        duplicate = raw.duplicated(["timestamp", "strike", "right"])
        row = {"date": day, "path": str(path), "sha256": sha256(path),
               "raw_rows": len(raw), "raw_first": str(raw.timestamp.min()),
               "raw_last": str(raw.timestamp.max()), "raw_schema": str(pq.read_schema(path)),
               "rth_rows": len(quotes), "outside_rth_rows": len(raw) - len(quotes),
               "calendar_close": session_end(day).isoformat(), "expected_minutes": len(grid),
               "observed_minutes": quotes.timestamp.nunique(), "duplicate_rows": int(duplicate.sum()),
               "crossed_rows": int((quotes.ask < quotes.bid).sum()),
               "zero_zero_rows": int(((quotes.ask == 0) & (quotes.bid == 0)).sum()),
               "valid_zero_bid_rows": int(((quotes.bid == 0) & (quotes.ask > 0)).sum()),
               "two_sided_sized_rows": int(valid.sum()), "two_sided_fraction": float(valid.mean()),
               "proxy_minutes": len(proxy), "proxy_missing_minutes": len(grid) - len(proxy)}
        if len(proxy):
            gaps = proxy.timestamp.diff().dt.total_seconds()
            row.update(proxy_first=str(proxy.timestamp.min()), proxy_last=str(proxy.timestamp.max()),
                       proxy_max_gap_seconds=float(gaps.max()),
                       proxy_dispersion_p50=float(proxy.dispersion.median()),
                       proxy_dispersion_p95=float(proxy.dispersion.quantile(.95)),
                       parity_width_p50=float(proxy.parity_width.median()),
                       parity_width_p95=float(proxy.parity_width.quantile(.95)))
            spx = ticks.loc[ticks.underlying == "SPX", ["ts_us", "price"]].copy()
            spx["timestamp"] = pd.to_datetime(spx.ts_us, unit="us", utc=True).dt.tz_convert("America/New_York")
            spx = spx.loc[spx.timestamp.dt.date == start.date()]
            if len(spx):
                comparison = pd.merge_asof(proxy, spx.sort_values("timestamp"), on="timestamp",
                                           tolerance=pd.Timedelta(seconds=120), direction="backward")
                discrepancy = (comparison.forward_proxy - comparison.price / 10).dropna()
                row["spx_comparison_diagnostic"] = {
                    "interpretation": "Approximate quote-implied forward minus prior observed SPX/10; neither is native XSP spot/official settlement",
                    "matched_minutes": len(discrepancy),
                    "median_signed_xsp_points": float(discrepancy.median()) if len(discrepancy) else None,
                    "median_absolute_xsp_points": float(discrepancy.abs().median()) if len(discrepancy) else None,
                    "p95_absolute_xsp_points": float(discrepancy.abs().quantile(.95)) if len(discrepancy) else None}
        rows.append(row)
    support = {"spot_underlyings": sorted(ticks.underlying.unique().tolist()),
               "spot_counts": ticks.groupby("underlying").size().to_dict(),
               "spot_bounds_utc": {symbol: {"first": pd.to_datetime(g.ts_us.min(), unit="us", utc=True).isoformat(),
                                              "last": pd.to_datetime(g.ts_us.max(), unit="us", utc=True).isoformat()}
                                   for symbol, g in ticks.groupby("underlying")},
               "daily_underlyings": sorted(daily.underlying.unique().tolist()),
               "files": {str(support_root / name): sha256(support_root / name)
                         for name in ("manifest.json", "spot_ticks.parquet", "daily_bars.parquet")}}
    result = {"scope": "bounded XSP data/execution feasibility; no strategy outcomes examined",
              "observed_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
              "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
              "source_hashes": {str(Path(__file__)): sha256(Path(__file__)),
                                str(Path(__file__).with_name("common.py")): sha256(Path(__file__).with_name("common.py"))},
              "calendar": calendar().meta(), "versions": {"pandas": pd.__version__, "numpy": np.__version__},
              "inventories": inventories, "support": support, "samples": rows,
              "limitations": ["Sample audit cannot establish all-date session eligibility",
                              "No native XSP spot/official settlement in canonical local support",
                              "Forward proxy uses zero-carry approximation; rates and asynchronous quote updates unmodeled",
                              "NBBO minute observation does not give quote-event freshness or complex-order execution",
                              "No partial-fill simulation; positive displayed sizes do not guarantee execution",
                              "No options IV/Greeks; no interpolated missing prices; fees are provisional research assumptions"]}
    (args.out / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "samples": [{k: r[k] for k in
        ("date", "raw_rows", "outside_rth_rows", "proxy_minutes", "proxy_missing_minutes", "crossed_rows")}
        for r in rows]}, indent=2))


if __name__ == "__main__":
    main()
