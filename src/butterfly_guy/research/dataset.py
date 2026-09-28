"""Per-session dense option-chain arrays stored as Parquet, with a hashed manifest.

Layout under a dataset root (outside Git):

    manifest.json               schema, source, export parameters, {path: {rows, sha256}},
                                and `history`: what each export run changed
    sessions.parquet            one row per exported session
    daily_bars.parquet          date, underlying, open, high, low, close
    spot_ticks.parquet          ts_us, underlying, price (spot_prices rows)
    sessions/<date>/chain.parquet
        Dense grid flattened ts-major: n_ts x n_strike rows with columns ts_us, strike,
        spot, and {C,P}_{bid,ask,mark} (float64) and {C,P}_{iv,delta} (float32).
        A quote the source did not record is NaN in every field; nothing is imputed.
    sessions/<date>/clock.parquet
        ts_us, spot, spot_min, spot_max: every underlying snapshot time that day, as the
        DB replay's bar query returns it (the reference decision clock).
    aux/vol_index_daily.parquet     date, index, open, high, low, close (Cboe VIX family)
    aux/vol_index_intraday.parquet  ts_us (bar start), index, bar_seconds, open, high, low,
                                    close

Auxiliary (`aux/`) files are feature inputs from other sources. They are listed and hashed
separately in the manifest (`aux`, `aux_hash`, schema 2), so adding or refreshing one never
changes `dataset_hash`, which covers the exported chain data only. A manifest without aux
files is written as schema 1, exactly as before.

Timestamps are integer microseconds since the Unix epoch (UTC).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA_VERSION = 2
SUPPORTED_SCHEMAS = (1, 2)  # 1: no aux files; 2 adds `aux` and `aux_hash`
OPTION_TYPES = ("C", "P")
PRICE_FIELDS = ("bid", "ask", "mark")
GREEK_FIELDS = ("iv", "delta")
DEFAULT_DATASET = "spx_0dte"


def default_cache_root() -> Path:
    """Research cache root: `$BUTTERFLY_RESEARCH_CACHE` or ~/.cache/butterfly_guy/research."""
    env = os.environ.get("BUTTERFLY_RESEARCH_CACHE")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".cache" / "butterfly_guy" / "research"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def session_dir(date: dt.date) -> str:
    return f"sessions/{date.isoformat()}"


@dataclass
class SessionChain:
    """One session's recorded 0-DTE chain as dense (n_ts, n_strike) arrays."""

    date: dt.date
    ts: np.ndarray  # int64 us, ascending
    strikes: np.ndarray  # float64, ascending
    spot: np.ndarray  # float64 per snapshot (chain spot_price)
    fields: dict[str, np.ndarray]  # "C_bid" -> (n_ts, n_strike)

    def column(self, strike: float) -> int | None:
        j = int(np.searchsorted(self.strikes, strike))
        if j < len(self.strikes) and self.strikes[j] == strike:
            return j
        return None


@dataclass
class SessionClock:
    """The reference decision clock: snapshot times and their underlying spot."""

    ts: np.ndarray  # int64 us, ascending
    spot: np.ndarray  # float64


def chain_to_table(chain: SessionChain) -> pa.Table:
    n_ts, n_k = len(chain.ts), len(chain.strikes)
    cols: dict[str, np.ndarray] = {
        "ts_us": np.repeat(chain.ts.astype(np.int64), n_k),
        "strike": np.tile(chain.strikes.astype(np.float64), n_ts),
        "spot": np.repeat(chain.spot.astype(np.float64), n_k),
    }
    for t in OPTION_TYPES:
        for f in PRICE_FIELDS:
            cols[f"{t}_{f}"] = chain.fields[f"{t}_{f}"].astype(np.float64).ravel()
        for f in GREEK_FIELDS:
            cols[f"{t}_{f}"] = chain.fields[f"{t}_{f}"].astype(np.float32).ravel()
    return pa.table(cols)


def table_to_chain(table: pa.Table, date: dt.date) -> SessionChain:
    ts_all = table.column("ts_us").to_numpy()
    strike_all = table.column("strike").to_numpy()
    ts = np.unique(ts_all)
    strikes = np.unique(strike_all)
    n_ts, n_k = len(ts), len(strikes)
    if len(ts_all) != n_ts * n_k:
        raise ValueError(f"{date}: chain table is not a dense ts x strike grid")
    fields = {}
    for t in OPTION_TYPES:
        for f in (*PRICE_FIELDS, *GREEK_FIELDS):
            name = f"{t}_{f}"
            fields[name] = table.column(name).to_numpy(zero_copy_only=False).reshape(n_ts, n_k)
    spot = table.column("spot").to_numpy().reshape(n_ts, n_k)[:, 0]
    return SessionChain(date=date, ts=ts, strikes=strikes, spot=spot, fields=fields)


def dense_chain_from_rows(rows: pd.DataFrame, date: dt.date) -> SessionChain:
    """Build dense arrays from long rows (ts_us, strike, t, bid, ask, mark, iv, delta, spot).

    A (ts, strike, type) with no row stays NaN. Duplicate rows keep the last one.
    """
    ts = np.sort(rows["ts_us"].unique())
    strikes = np.sort(rows["strike"].unique())
    ti = np.searchsorted(ts, rows["ts_us"].to_numpy())
    ki = np.searchsorted(strikes, rows["strike"].to_numpy())
    fields: dict[str, np.ndarray] = {}
    for t in OPTION_TYPES:
        m = (rows["t"] == t).to_numpy()
        for f in (*PRICE_FIELDS, *GREEK_FIELDS):
            dtype = np.float64 if f in PRICE_FIELDS else np.float32
            a = np.full((len(ts), len(strikes)), np.nan, dtype=dtype)
            a[ti[m], ki[m]] = rows[f].to_numpy(dtype=dtype)[m]
            fields[f"{t}_{f}"] = a
    spot_by_ts = rows.groupby("ts_us")["spot"].first().reindex(ts).to_numpy(dtype=np.float64)
    return SessionChain(date=date, ts=ts, strikes=strikes, spot=spot_by_ts, fields=fields)


def write_table(table: pa.Table, path: Path) -> dict[str, object]:
    """Write deterministically and return the manifest entry for the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    pq.write_table(table, tmp, compression="zstd", write_statistics=False)
    tmp.replace(path)
    return {"rows": table.num_rows, "sha256": sha256_file(path)}


def dataset_hash(files: dict[str, dict]) -> str:
    lines = "".join(f"{p} {files[p]['sha256']}\n" for p in sorted(files))
    return hashlib.sha256(lines.encode()).hexdigest()


@dataclass
class Manifest:
    dataset: str
    underlying: str
    source: dict
    export: dict
    files: dict[str, dict] = field(default_factory=dict)
    updated_at: str = ""
    exporter_git_sha: str = ""
    history: list[dict] = field(default_factory=list)  # one entry per export run
    aux: dict[str, dict] = field(default_factory=dict)  # separately hashed feature inputs

    @property
    def dataset_hash(self) -> str:
        return dataset_hash(self.files)

    @property
    def aux_hash(self) -> str | None:
        return dataset_hash(self.aux) if self.aux else None

    @property
    def schema_version(self) -> int:
        return SCHEMA_VERSION if self.aux else 1

    def to_json(self) -> str:
        body = {
            "schema_version": self.schema_version,
            "dataset": self.dataset,
            "underlying": self.underlying,
            "source": self.source,
            "export": self.export,
            "updated_at": self.updated_at,
            "exporter_git_sha": self.exporter_git_sha,
            "dataset_hash": self.dataset_hash,
            "files": {p: self.files[p] for p in sorted(self.files)},
        }
        if self.aux:
            body["aux_hash"] = self.aux_hash
            body["aux"] = {p: self.aux[p] for p in sorted(self.aux)}
        if self.history:
            body["history"] = self.history
        return json.dumps(body, indent=1, sort_keys=False) + "\n"

    @classmethod
    def load(cls, path: Path) -> Manifest:
        body = json.loads(path.read_text())
        if body.get("schema_version") not in SUPPORTED_SCHEMAS:
            raise ValueError(f"unsupported dataset schema {body.get('schema_version')}")
        m = cls(
            dataset=body["dataset"],
            underlying=body["underlying"],
            source=body["source"],
            export=body["export"],
            files=body["files"],
            updated_at=body.get("updated_at", ""),
            exporter_git_sha=body.get("exporter_git_sha", ""),
            history=body.get("history", []),
            aux=body.get("aux", {}),
        )
        if body.get("dataset_hash") != m.dataset_hash:
            raise ValueError("manifest dataset_hash does not match its file list")
        if body.get("aux_hash") != m.aux_hash:
            raise ValueError("manifest aux_hash does not match its aux file list")
        return m

    def save(self, path: Path) -> None:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(self.to_json())
        tmp.replace(path)


class Dataset:
    """Read access to an exported dataset. Files are hash-checked on first read."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.manifest = Manifest.load(self.root / "manifest.json")
        self._verified: set[str] = set()

    @classmethod
    def open(cls, name: str = DEFAULT_DATASET, cache_root: Path | None = None) -> Dataset:
        return cls((cache_root or default_cache_root()) / name)

    @property
    def name(self) -> str:
        return self.manifest.dataset

    @property
    def hash(self) -> str:
        return self.manifest.dataset_hash

    @property
    def aux_hash(self) -> str | None:
        return self.manifest.aux_hash

    def has_aux(self, rel: str) -> bool:
        return rel in self.manifest.aux

    def _path(self, rel: str) -> Path:
        entry = self.manifest.files.get(rel) or self.manifest.aux.get(rel)
        if entry is None:
            raise FileNotFoundError(f"{rel} is not in the dataset manifest")
        path = self.root / rel
        if rel not in self._verified:
            actual = sha256_file(path)
            if actual != entry["sha256"]:
                raise ValueError(f"{rel}: sha256 {actual} does not match the manifest")
            self._verified.add(rel)
        return path

    def verify(self) -> list[str]:
        """Return a list of problems (missing files, hash or row-count mismatches)."""
        problems = []
        for rel, entry in sorted({**self.manifest.files, **self.manifest.aux}.items()):
            path = self.root / rel
            if not path.exists():
                problems.append(f"missing {rel}")
                continue
            if sha256_file(path) != entry["sha256"]:
                problems.append(f"sha256 mismatch {rel}")
                continue
            rows = pq.ParquetFile(path).metadata.num_rows
            if rows != entry["rows"]:
                problems.append(f"row count {rows} != {entry['rows']} for {rel}")
        return problems

    def sessions(self) -> pd.DataFrame:
        df = pq.read_table(self._path("sessions.parquet")).to_pandas()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df.sort_values("date").reset_index(drop=True)

    @lru_cache(maxsize=1)
    def daily_bars(self) -> pd.DataFrame:
        df = pq.read_table(self._path("daily_bars.parquet")).to_pandas()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df.sort_values(["underlying", "date"]).reset_index(drop=True)

    @lru_cache(maxsize=4)
    def spot_ticks(self, underlying: str) -> tuple[np.ndarray, np.ndarray]:
        table = pq.read_table(
            self._path("spot_ticks.parquet"), filters=[("underlying", "=", underlying)]
        )
        order = np.argsort(table.column("ts_us").to_numpy(), kind="stable")
        return (
            table.column("ts_us").to_numpy()[order],
            table.column("price").to_numpy()[order],
        )

    def chain(self, date: dt.date) -> SessionChain:
        return table_to_chain(pq.read_table(self._path(f"{session_dir(date)}/chain.parquet")), date)

    def clock(self, date: dt.date) -> SessionClock:
        table = pq.read_table(self._path(f"{session_dir(date)}/clock.parquet"))
        return SessionClock(ts=table.column("ts_us").to_numpy(),
                            spot=table.column("spot").to_numpy())

    @lru_cache(maxsize=2)
    def aux_table(self, rel: str) -> pd.DataFrame:
        """An auxiliary file (hash-checked like every other file)."""
        return pq.read_table(self._path(rel)).to_pandas()
