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
rows added, removed and revised. Cboe files are full history and replace the daily file;
a gateway dump is merged into the intraday file, which never loses a row.
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

from butterfly_guy.research.dataset import Dataset, Manifest, default_cache_root, write_table

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
              log=None, *, allow_removal: bool = True, extra: dict | None = None) -> Manifest:
    """Write one aux file into an existing dataset and record the change in its manifest.

    With `allow_removal=False`, a table missing any existing row raises before anything is
    written. `extra` is added to the history entry."""
    manifest_path = root / "manifest.json"
    manifest = Manifest.load(manifest_path)
    path = root / rel
    old = Dataset(root).aux_table(rel) if rel in manifest.aux and path.exists() else None
    changes = _row_changes(old, table, keys)
    if changes["rows_removed"] and not allow_removal:
        raise ValueError(f"{rel}: the new table would remove {changes['rows_removed']} "
                         "existing rows; nothing was written")
    prev_aux = manifest.aux_hash
    entry = write_table(pa.Table.from_pandas(table, preserve_index=False), path)
    manifest.aux[rel] = {**entry, "source": source}
    manifest.history.append({
        "at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "mode": "aux",
        "file": rel,
        "dataset_hash": manifest.dataset_hash,
        "previous_aux_hash": prev_aux,
        "aux_hash": manifest.aux_hash,
        **changes,
        **(extra or {}),
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


INTRADAY_KEYS = ["index", "ts_us"]
INTRADAY_DTYPES = {"ts_us": "int64", "index": "object", "bar_seconds": "int64",
                   **dict.fromkeys(OHLC, "float64")}


def merge_intraday(old: pd.DataFrame | None, new: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """The existing bars merged with a dump's.

    A bar only in the dump is added. A bar in both takes the dump's OHLC (`write_aux`
    records it as revised, old and new). A bar the dump does not contain is kept, so a dump
    taken after the gateway's retention has rolled never removes older bars. Returns the
    merged table and the number of bars kept that the dump did not contain."""
    cols = list(INTRADAY_DTYPES)
    new = new[cols].astype(INTRADAY_DTYPES)
    if old is None:
        return new.sort_values(INTRADAY_KEYS, ignore_index=True), 0
    old = old[cols].astype(INTRADAY_DTYPES)
    both = old.merge(new[[*INTRADAY_KEYS, "bar_seconds"]], on=INTRADAY_KEYS,
                     suffixes=("", "_dump"))
    clash = both[both["bar_seconds"] != both["bar_seconds_dump"]]
    if not clash.empty:
        r = clash.iloc[0]
        raise ValueError(f"{r['index']} ts_us {r['ts_us']}: bar_seconds {r['bar_seconds']} in "
                         f"the file, {r['bar_seconds_dump']} in the dump")
    in_dump = pd.MultiIndex.from_frame(new[INTRADAY_KEYS])
    kept = old[~pd.MultiIndex.from_frame(old[INTRADAY_KEYS]).isin(in_dump)]
    merged = pd.concat([kept, new], ignore_index=True).sort_values(INTRADAY_KEYS,
                                                                   ignore_index=True)
    return merged.astype(INTRADAY_DTYPES), len(kept)


def ingest_intraday(dataset: str, dump: Path, cache_root: Path | None = None, *, log=None
                    ) -> Manifest:
    """Merge a gateway dump into the intraday aux file (see `merge_intraday`). Every dump
    ingested is listed in the file's `source.dumps`; the file never loses a row."""
    root = (cache_root or default_cache_root()) / dataset
    data = dump.read_bytes()
    table, coverage = intraday_table(data.decode().splitlines())
    prev = Manifest.load(root / "manifest.json").aux.get(INTRADAY_FILE)
    old = Dataset(root).aux_table(INTRADAY_FILE) if prev is not None else None
    merged, kept = merge_intraday(old, table)

    dumps = list((prev or {}).get("source", {}).get("dumps", []))
    if prev is not None and not dumps and "dump_sha256" in prev["source"]:
        # A file written before merging existed: its one dump becomes the first entry.
        dumps = [{k: prev["source"][k] for k in ("dump_sha256", "ingested_at", "coverage")
                  if k in prev["source"]}]
    dump_sha = hashlib.sha256(data).hexdigest()
    dumps.append({"dump_sha256": dump_sha,
                  "ingested_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                  "coverage": coverage})
    source = {
        "kind": "schwab_gateway_session_history",
        "timestamp": "bar start; complete at ts + bar_seconds",
        "merge": "existing bars kept; dump bars added; a bar in both takes the dump's OHLC",
        "dumps": dumps,
    }
    return write_aux(root, INTRADAY_FILE, merged, source, INTRADAY_KEYS, log,
                     allow_removal=False,
                     extra={"dump_sha256": dump_sha, "dump_rows": len(table),
                            "kept_not_in_dump": kept})
