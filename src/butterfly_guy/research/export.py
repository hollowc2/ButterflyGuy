"""Read-only export of recorded SPX 0-DTE data into a research dataset.

Every query is bounded to one session (a UTC-day `snapshot_time` range) or one calendar
chunk, and runs with `default_transaction_read_only = on` and a statement timeout. A
source only has to answer `COPY (<select>) TO STDOUT WITH CSV HEADER`, so a vendor
feed can be plugged in later by implementing `DataSource.copy_csv` for its own SQL
store or by writing the same Parquet schema directly.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import io
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd
import pyarrow as pa

from butterfly_guy.research.dataset import (
    DEFAULT_DATASET,
    Manifest,
    SessionChain,
    chain_to_table,
    default_cache_root,
    dense_chain_from_rows,
    session_dir,
    write_table,
)

STATEMENT_TIMEOUT_MS = 120_000
MIN_SESSION_SNAPSHOTS = 50  # run_backtest_db.discover_dates qualification
DEFAULT_STRIKE_MARGIN = 400.0  # strikes kept within the day's spot range +/- this
SPOT_UNDERLYINGS = ("SPX", "$VIX")
_SAFE_UNDERLYING = re.compile(r"^\$?[A-Z]{1,6}$")


class DataSource(Protocol):
    """Anything that can stream `COPY (<sql>) TO STDOUT WITH CSV HEADER` as bytes."""

    def describe(self) -> dict: ...

    def copy_csv(self, sql: str) -> bytes: ...

    def close(self) -> None: ...


class PostgresSource:
    """asyncpg over the existing SSH tunnel (DSN from `.env` via `load_config`)."""

    def __init__(self, dsn: str | None = None) -> None:
        import asyncpg

        from butterfly_guy.core.config import load_config

        self._dsn = dsn or load_config().database.dsn
        self._loop = asyncio.new_event_loop()
        self._conn = self._loop.run_until_complete(
            asyncpg.connect(
                self._dsn,
                server_settings={
                    "default_transaction_read_only": "on",
                    "statement_timeout": str(STATEMENT_TIMEOUT_MS),
                },
            )
        )
        self.timezone = self._loop.run_until_complete(self._conn.fetchval("show timezone"))
        read_only = self._loop.run_until_complete(
            self._conn.fetchval("show default_transaction_read_only")
        )
        if read_only != "on":
            raise RuntimeError("could not make the research export session read-only")

    def describe(self) -> dict:
        host = re.sub(r"//[^@]*@", "//", self._dsn).split("?")[0]
        return {"kind": "postgres", "dsn_host": host, "timezone": self.timezone}

    def copy_csv(self, sql: str) -> bytes:
        buf = io.BytesIO()
        self._loop.run_until_complete(
            self._conn.copy_from_query(sql, output=buf, format="csv", header=True)
        )
        return buf.getvalue()

    def close(self) -> None:
        self._loop.run_until_complete(self._conn.close())
        self._loop.close()


class DockerExecSource:
    """`psql` inside the TimescaleDB container over ssh (see the idea-sweep README)."""

    def __init__(
        self,
        host: str = "billy@helios",
        container: str = "butterfly_timescaledb",
        user: str = "butterfly",
        database: str = "butterfly_guy",
    ) -> None:
        self.host, self.container, self.user, self.database = host, container, user, database
        self.timezone = self._run("show timezone;", csv=False).decode().strip()

    def _run(self, statement: str, *, csv: bool = True) -> bytes:
        script = (
            "set default_transaction_read_only = on;\n"
            f"set statement_timeout = {STATEMENT_TIMEOUT_MS};\n"
            + (f"copy ({statement}) to stdout with csv header;\n" if csv else statement)
        )
        cmd = [
            "ssh", "-F", "/dev/null", "-o", "BatchMode=yes", self.host,
            f"docker exec -i {self.container} psql -U {self.user} -d {self.database} "
            "-q -t -A -v ON_ERROR_STOP=1",
        ]
        proc = subprocess.run(cmd, input=script.encode(), capture_output=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode(errors="replace").strip())
        out = proc.stdout
        # `set` echoes nothing under -q; strip any leading blank lines.
        return out.lstrip(b"\n")

    def describe(self) -> dict:
        return {"kind": "docker_exec", "host": self.host, "container": self.container,
                "timezone": self.timezone}

    def copy_csv(self, sql: str) -> bytes:
        return self._run(sql)

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Bounded queries (UTC-day ranges on snapshot_time, as the DB replay's ::date casts
# resolve under the database's UTC session time zone)
# ---------------------------------------------------------------------------


def _utc_day(date: dt.date) -> tuple[str, str]:
    lo = dt.datetime(date.year, date.month, date.day, tzinfo=dt.UTC)
    return lo.isoformat(), (lo + dt.timedelta(days=1)).isoformat()


def _underlying(u: str) -> str:
    if not _SAFE_UNDERLYING.match(u):
        raise ValueError(f"unexpected underlying {u!r}")
    return u


def snapshot_count_sql(underlying: str, date: dt.date) -> str:
    lo, hi = _utc_day(date)
    return (
        "select count(distinct snapshot_time) as n from option_chain_snapshots "
        f"where underlying = '{_underlying(underlying)}' and expiration = '{date}' "
        f"and snapshot_time >= '{lo}' and snapshot_time < '{hi}'"
    )


def clock_sql(underlying: str, date: dt.date) -> str:
    """The DB replay's `load_bars_from_db` query, with its ::date cast as a range.

    DISTINCT ON keeps one arbitrary row's spot per snapshot, exactly as the replay does;
    spot_min/spot_max expose any disagreement between rows of the same snapshot.
    """
    lo, hi = _utc_day(date)
    u = _underlying(underlying)
    return (
        "select b.snapshot_time, b.spot_price as spot, a.spot_min, a.spot_max from ("
        "select distinct on (snapshot_time) snapshot_time, spot_price "
        f"from option_chain_snapshots where underlying = '{u}' "
        f"and snapshot_time >= '{lo}' and snapshot_time < '{hi}' "
        "and spot_price is not null and spot_price > 0 order by snapshot_time) b join ("
        "select snapshot_time, min(spot_price) as spot_min, max(spot_price) as spot_max "
        f"from option_chain_snapshots where underlying = '{u}' "
        f"and snapshot_time >= '{lo}' and snapshot_time < '{hi}' "
        "and spot_price is not null and spot_price > 0 group by snapshot_time) a "
        "using (snapshot_time) order by b.snapshot_time"
    )


def chain_sql(underlying: str, date: dt.date, strike_lo: float, strike_hi: float) -> str:
    lo, hi = _utc_day(date)
    return (
        "select snapshot_time, strike, left(option_type, 1) as t, bid, ask, mark, iv, delta, "
        "spot_price as spot from option_chain_snapshots "
        f"where underlying = '{_underlying(underlying)}' and expiration = '{date}' "
        f"and snapshot_time >= '{lo}' and snapshot_time < '{hi}' "
        f"and strike >= {strike_lo:.2f} and strike <= {strike_hi:.2f}"
    )


def spot_ticks_sql(start: dt.date, end: dt.date) -> str:
    lo = dt.datetime(start.year, start.month, start.day, tzinfo=dt.UTC).isoformat()
    hi = dt.datetime(end.year, end.month, end.day, tzinfo=dt.UTC).isoformat()
    names = ", ".join(f"'{_underlying(u)}'" for u in SPOT_UNDERLYINGS)
    return (
        "select ts, underlying, price from spot_prices "
        f"where underlying in ({names}) and ts >= '{lo}' and ts < '{hi}'"
    )


def daily_bars_sql(start: dt.date, end: dt.date) -> str:
    names = ", ".join(f"'{_underlying(u)}'" for u in SPOT_UNDERLYINGS)
    return (
        "select date, underlying, open, high, low, close from daily_bars "
        f"where underlying in ({names}) and date >= '{start}' and date <= '{end}'"
    )


def _read_csv(data: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(data), keep_default_na=True)


def _ts_us(series: pd.Series) -> np.ndarray:
    ts = pd.to_datetime(series, utc=True, format="ISO8601")
    return ts.astype("datetime64[us, UTC]").astype("int64").to_numpy()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


@dataclass
class ExportPlan:
    start: dt.date
    end: dt.date
    underlying: str = "SPX"
    dataset: str = DEFAULT_DATASET
    strike_margin: float = DEFAULT_STRIKE_MARGIN
    refresh: bool = False
    daily_lookback_days: int = 400
    spot_lookback_days: int = 10
    log: object = field(default=sys.stderr)


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parent,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def export_session(
    source: DataSource, underlying: str, date: dt.date, strike_margin: float
) -> tuple[SessionChain, pd.DataFrame] | None:
    clock = _read_csv(source.copy_csv(clock_sql(underlying, date)))
    if clock.empty:
        return None
    clock_df = pd.DataFrame({
        "ts_us": _ts_us(clock["snapshot_time"]),
        "spot": clock["spot"].astype("float64"),
        "spot_min": clock["spot_min"].astype("float64"),
        "spot_max": clock["spot_max"].astype("float64"),
    })
    k_lo = float(np.floor(clock_df["spot_min"].min() - strike_margin))
    k_hi = float(np.ceil(clock_df["spot_max"].max() + strike_margin))
    rows = _read_csv(source.copy_csv(chain_sql(underlying, date, k_lo, k_hi)))
    if rows.empty:
        return None
    rows = pd.DataFrame({
        "ts_us": _ts_us(rows["snapshot_time"]),
        "strike": rows["strike"].astype("float64"),
        "t": rows["t"].astype(str),
        "bid": pd.to_numeric(rows["bid"], errors="coerce").astype("float64"),
        "ask": pd.to_numeric(rows["ask"], errors="coerce").astype("float64"),
        "mark": pd.to_numeric(rows["mark"], errors="coerce").astype("float64"),
        "iv": pd.to_numeric(rows["iv"], errors="coerce").astype("float32"),
        "delta": pd.to_numeric(rows["delta"], errors="coerce").astype("float32"),
        "spot": pd.to_numeric(rows["spot"], errors="coerce").astype("float64"),
    })
    return dense_chain_from_rows(rows, date), clock_df


def _weekdays(start: dt.date, end: dt.date) -> list[dt.date]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def run_export(source: DataSource, plan: ExportPlan, cache_root: Path | None = None) -> Manifest:
    """Export (or extend) a dataset. Existing sessions are kept unless `refresh`."""
    root = (cache_root or default_cache_root()) / plan.dataset
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    export_params = {
        "underlying": plan.underlying,
        "strike_margin": plan.strike_margin,
        "min_session_snapshots": MIN_SESSION_SNAPSHOTS,
        "spot_underlyings": list(SPOT_UNDERLYINGS),
    }
    if manifest_path.exists():
        manifest = Manifest.load(manifest_path)
        if manifest.export != export_params:
            raise ValueError(
                f"existing dataset was exported with {manifest.export}; use a new dataset name"
            )
    else:
        manifest = Manifest(
            dataset=plan.dataset, underlying=plan.underlying,
            source=source.describe(), export=export_params,
        )
    manifest.source = source.describe()
    log = plan.log

    sessions_path = root / "sessions.parquet"
    if sessions_path.exists() and "sessions.parquet" in manifest.files:
        sessions = pd.read_parquet(sessions_path)
        sessions["date"] = pd.to_datetime(sessions["date"]).dt.date
    else:
        sessions = pd.DataFrame(
            columns=["date", "snapshots", "chain_snapshots", "strikes", "strike_lo",
                     "strike_hi", "clock_spot_disagreements"]
        )
    known = set(sessions["date"]) if not plan.refresh else set()

    for date in _weekdays(plan.start, plan.end):
        if date in known:
            continue
        n = int(_read_csv(source.copy_csv(snapshot_count_sql(plan.underlying, date)))["n"][0])
        if n < MIN_SESSION_SNAPSHOTS:
            print(f"  {date}: {n} snapshots, skipped", file=log)
            continue
        result = export_session(source, plan.underlying, date, plan.strike_margin)
        if result is None:
            print(f"  {date}: no rows, skipped", file=log)
            continue
        chain, clock = result
        rel = session_dir(date)
        manifest.files[f"{rel}/chain.parquet"] = write_table(
            chain_to_table(chain), root / rel / "chain.parquet"
        )
        manifest.files[f"{rel}/clock.parquet"] = write_table(
            pa.Table.from_pandas(clock, preserve_index=False), root / rel / "clock.parquet"
        )
        disagreements = int((clock["spot_min"] != clock["spot_max"]).sum())
        row = {
            "date": date, "snapshots": n, "chain_snapshots": len(chain.ts),
            "strikes": len(chain.strikes), "strike_lo": float(chain.strikes[0]),
            "strike_hi": float(chain.strikes[-1]), "clock_spot_disagreements": disagreements,
        }
        sessions = pd.concat(
            [sessions[sessions["date"] != date], pd.DataFrame([row])], ignore_index=True
        )
        print(f"  {date}: {len(chain.ts)} snapshots x {len(chain.strikes)} strikes", file=log)

    if sessions.empty:
        raise RuntimeError("no sessions exported")
    sessions = sessions.sort_values("date").reset_index(drop=True)
    sessions["date"] = pd.to_datetime(sessions["date"])
    manifest.files["sessions.parquet"] = write_table(
        pa.Table.from_pandas(sessions.astype({"snapshots": "int64", "chain_snapshots": "int64",
                                              "strikes": "int64",
                                              "clock_spot_disagreements": "int64"}),
                             preserve_index=False),
        sessions_path,
    )
    first, last = sessions["date"].min().date(), sessions["date"].max().date()

    bars = _read_csv(source.copy_csv(daily_bars_sql(
        first - dt.timedelta(days=plan.daily_lookback_days), last)))
    bars = pd.DataFrame({
        "date": pd.to_datetime(bars["date"]),
        "underlying": bars["underlying"].astype(str),
        **{c: bars[c].astype("float64") for c in ("open", "high", "low", "close")},
    }).sort_values(["underlying", "date"])
    manifest.files["daily_bars.parquet"] = write_table(
        pa.Table.from_pandas(bars, preserve_index=False), root / "daily_bars.parquet"
    )

    tick_frames = []
    chunk_start = first - dt.timedelta(days=plan.spot_lookback_days)
    while chunk_start <= last:
        chunk_end = min(chunk_start + dt.timedelta(days=7), last + dt.timedelta(days=1))
        df = _read_csv(source.copy_csv(spot_ticks_sql(chunk_start, chunk_end)))
        if not df.empty:
            tick_frames.append(pd.DataFrame({
                "ts_us": _ts_us(df["ts"]),
                "underlying": df["underlying"].astype(str),
                "price": df["price"].astype("float64"),
            }))
        chunk_start = chunk_end
    ticks = pd.concat(tick_frames, ignore_index=True).sort_values(
        ["underlying", "ts_us"], kind="stable")
    manifest.files["spot_ticks.parquet"] = write_table(
        pa.Table.from_pandas(ticks, preserve_index=False), root / "spot_ticks.parquet"
    )

    manifest.updated_at = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    manifest.exporter_git_sha = _git_sha()
    manifest.save(manifest_path)
    print(f"dataset {plan.dataset}: {len(sessions)} sessions {first} -> {last}, "
          f"hash {manifest.dataset_hash}", file=log)
    return manifest
