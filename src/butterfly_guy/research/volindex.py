"""VIX-family volatility indices as separately hashed auxiliary dataset files.

Daily history comes from Cboe's public files (no sign-up):
`https://cdn.cboe.com/api/global/us_indices/daily_prices/<INDEX>_History.csv`. Columns
DATE (MM/DD/YYYY), OPEN, HIGH, LOW, CLOSE. VIX1D starts 2022-05-13, VIX9D 2011-01-04,
VIX3M 2009-09-18, VIX 1990.

Intraday history comes from the Schwab gateway's `/v1/session-history` (regular session,
1-minute candles stamped at the bar start), dumped where the gateway key lives by
`tools/research_gateway_vol_dump.py` and ingested here from its JSONL. Schwab keeps
about 30 sessions of minute history and returns nothing for `$VIX1D`.

Both land under `aux/` with their own manifest entries, so `dataset_hash` (the exported
chain data) never changes. Each refresh appends a manifest `history` entry listing the
rows added, removed and revised.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa

from butterfly_guy.research.dataset import Manifest, default_cache_root, write_table

CBOE_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{index}_History.csv"
CBOE_INDICES = ("VIX", "VIX1D", "VIX9D", "VIX3M")
DAILY_FILE = "aux/vol_index_daily.parquet"
INTRADAY_FILE = "aux/vol_index_intraday.parquet"
OHLC = ("open", "high", "low", "close")


def parse_cboe_csv(data: bytes, index: str) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(data))
    df.columns = [c.strip().upper() for c in df.columns]
    if list(df.columns) != ["DATE", "OPEN", "HIGH", "LOW", "CLOSE"]:
        raise ValueError(f"{index}: unexpected Cboe columns {list(df.columns)}")
    out = pd.DataFrame({
        "date": pd.to_datetime(df["DATE"], format="%m/%d/%Y"),
        "index": index,
        **{c: pd.to_numeric(df[c.upper()], errors="coerce").astype("float64") for c in OHLC},
    })
    if out["date"].duplicated().any():
        raise ValueError(f"{index}: duplicate dates in the Cboe file")
    return out


def fetch_cboe(indices: tuple[str, ...] = CBOE_INDICES) -> dict[str, tuple[str, bytes]]:
    """{index: (url, raw bytes)}. Public data; redirects to cdn-api.cboe.com are followed."""
    import httpx

    out = {}
    with httpx.Client(follow_redirects=True, timeout=60.0,
                      headers={"User-Agent": "butterfly-guy-research"}) as client:
        for index in indices:
            url = CBOE_URL.format(index=index)
            resp = client.get(url)
            resp.raise_for_status()
            out[index] = (url, resp.content)
    return out


def daily_table(raw: dict[str, tuple[str, bytes]]) -> pd.DataFrame:
    frames = [parse_cboe_csv(data, index) for index, (_, data) in sorted(raw.items())]
    return pd.concat(frames, ignore_index=True).sort_values(["index", "date"],
                                                            ignore_index=True)


def intraday_table(dump_lines: list[str]) -> tuple[pd.DataFrame, list[dict]]:
    """Rows from a gateway dump (one JSON object per symbol and date) and a coverage list.

    Candles keep the gateway's bar-start timestamp; `bar_seconds` says when the bar was
    complete. Nothing is filled for a date the gateway returned no bars for.
    """
    rows, coverage = [], []
    for line in dump_lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        index = rec["symbol"].lstrip("$")
        candles = rec.get("candles") or []
        coverage.append({"index": index, "date": rec["date"], "bars": len(candles),
                         "flags": rec.get("flags", []), "error": rec.get("error")})
        for c in candles:
            ts = pd.Timestamp(c["ts"])
            if ts.tzinfo is None:
                raise ValueError(f"{index} {rec['date']}: naive candle timestamp {c['ts']}")
            rows.append({"ts_us": int(ts.value // 1000), "index": index,
                         "bar_seconds": int(rec.get("bar_seconds", 60)),
                         **{k: float(c[k]) for k in OHLC}})
    df = pd.DataFrame(rows, columns=["ts_us", "index", "bar_seconds", *OHLC])
    df = df.astype({"ts_us": "int64", "bar_seconds": "int64"})
    if df.duplicated(["index", "ts_us"]).any():
        raise ValueError("duplicate (index, ts) candles in the gateway dump")
    return df.sort_values(["index", "ts_us"], ignore_index=True), coverage


def _row_changes(old: pd.DataFrame | None, new: pd.DataFrame, keys: list[str]) -> dict:
    """Rows added, removed and revised between two versions of an aux table."""
    if old is None:
        return {"rows_added": len(new), "rows_removed": 0, "revised": []}
    a, b = old.set_index(keys), new.set_index(keys)
    added = b.index.difference(a.index)
    removed = a.index.difference(b.index)
    both = a.index.intersection(b.index)
    revised = []
    for key in both:
        x, y = a.loc[key, list(OHLC)], b.loc[key, list(OHLC)]
        diff = {c: [float(x[c]), float(y[c])] for c in OHLC
                if not (x[c] == y[c] or (np.isnan(x[c]) and np.isnan(y[c])))}
        if diff:
            k = key if isinstance(key, tuple) else (key,)
            revised.append({**{n: str(v.date() if hasattr(v, "date") else v)
                               for n, v in zip(keys, k, strict=True)}, **diff})
    return {"rows_added": len(added), "rows_removed": len(removed), "revised": revised}


def write_aux(root: Path, rel: str, table: pd.DataFrame, source: dict, keys: list[str],
              log=None) -> Manifest:
    """Write one aux file into an existing dataset and record the change in its manifest."""
    manifest_path = root / "manifest.json"
    manifest = Manifest.load(manifest_path)
    path = root / rel
    old = pd.read_parquet(path) if rel in manifest.aux and path.exists() else None
    prev_aux = manifest.aux_hash
    entry = write_table(pa.Table.from_pandas(table, preserve_index=False), path)
    manifest.aux[rel] = {**entry, "source": source}
    changes = _row_changes(old, table, keys)
    manifest.history.append({
        "at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "mode": "aux",
        "file": rel,
        "dataset_hash": manifest.dataset_hash,
        "previous_aux_hash": prev_aux,
        "aux_hash": manifest.aux_hash,
        **changes,
    })
    manifest.save(manifest_path)
    if log is not None:
        print(f"{rel}: {entry['rows']} rows, sha256 {entry['sha256']}; added "
              f"{changes['rows_added']}, removed {changes['rows_removed']}, revised "
              f"{len(changes['revised'])}; aux_hash {manifest.aux_hash}; dataset_hash "
              f"{manifest.dataset_hash} (unchanged)", file=log)
    return manifest


def export_daily(dataset: str, cache_root: Path | None = None, *, raw=None, log=None
                 ) -> Manifest:
    root = (cache_root or default_cache_root()) / dataset
    fetched_at = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    raw = raw if raw is not None else fetch_cboe()
    table = daily_table(raw)
    source = {
        "kind": "cboe_public_daily",
        "fetched_at": fetched_at,
        "files": {index: {"url": url, "sha256": hashlib.sha256(data).hexdigest(),
                          "bytes": len(data)}
                  for index, (url, data) in sorted(raw.items())},
        "coverage": {index: [str(g["date"].min().date()), str(g["date"].max().date()), len(g)]
                     for index, g in table.groupby("index")},
    }
    return write_aux(root, DAILY_FILE, table, source, ["index", "date"], log)


def ingest_intraday(dataset: str, dump: Path, cache_root: Path | None = None, *, log=None
                    ) -> Manifest:
    root = (cache_root or default_cache_root()) / dataset
    data = dump.read_bytes()
    table, coverage = intraday_table(data.decode().splitlines())
    source = {
        "kind": "schwab_gateway_session_history",
        "dump_sha256": hashlib.sha256(data).hexdigest(),
        "ingested_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "timestamp": "bar start; complete at ts + bar_seconds",
        "coverage": coverage,
    }
    return write_aux(root, INTRADAY_FILE, table, source, ["index", "ts_us"], log)
