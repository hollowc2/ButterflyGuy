# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "pyarrow>=15"]
# ///
"""Download raw ThetaData option history for the 0DTE/1DTE sets into Parquet under data/.

Run with `uv run tools/thetadata_download.py [--dry-run]`. It is resumable: a day's file that
already exists, or a day the vendor answered "no data" for, is not requested again.

Sets (PM-settled roots only; the AM-settled SPX/NDX monthlies stop trading the day before
expiry, so they have no 0DTE session):

- `spxw_0dte`, `ndxp_0dte`, `xsp_0dte`: each expiration, on its expiration day.
- `spxw_1dte`: each SPXW expiration, on the session before it (a Monday expiry is
  pulled on the Friday before).

Kinds, one Parquet file per set, kind and trade date, with the vendor's columns unchanged:

- `quote_1m`: NBBO at each minute 09:30-16:15 ET (`/option/history/quote`, interval 1m).
  A bid 0 / ask 0 row means no quote yet; a zero bid with a real ask is a real quote.
- `ohlc_1m`: trade bars per minute (`/option/history/ohlc`). A minute with no trades
  has volume 0 and OHLC 0.0.
- `open_interest`: the day's opening open interest (`/option/history/open_interest`).
- `eod`: the vendor's end-of-day summary (`/option/history/eod`).

`timestamp`, `created` and `last_trade` are stored as America/New_York datetimes and
`expiration` as a date. Greeks, IV and trade ticks need the Options Standard plan and are
not pulled; the Options Value plan starts at 2020-01-01.

Layout: `data/thetadata/<set>/<kind>/<YYYY>/<YYYY-MM-DD>.parquet`, plus `catalog.jsonl`
(one line per request: status, rows, strikes). The 2024-07-01 -> 2026-03-12 research holdout
was once kept apart in `data/thetadata_sealed/`; H-TS1 spent it on 2026-09-30 and it now
lives here with everything else. This tool never prints prices.

Trading sessions come from Cboe's official SPX daily file. The Theta Terminal must be
running locally; Options Value allows 2 concurrent requests, which is the worker default.
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import io
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

BASE_URL = "http://127.0.0.1:25503/v3"  # 127.0.0.1, not localhost: the terminal pins the IP
CBOE_SPX = "https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OPEN_DIR = DATA_DIR / "thetadata"
VALUE_START = dt.date(2020, 1, 1)
SETS = {"spxw_0dte": ("SPXW", 0), "spxw_1dte": ("SPXW", 1),
        "ndxp_0dte": ("NDXP", 0), "xsp_0dte": ("XSP", 0)}
KINDS = ("quote_1m", "ohlc_1m", "open_interest", "eod")
TIME_COLUMNS = ("timestamp", "created", "last_trade")
RETRY_STATUS = {429, 474, 500, 502, 503, 504}
NO_DATA = 472
LARGE_REQUEST = 570


class LargeRequestError(Exception):
    """The terminal asked for a smaller request (570); calls and puts are fetched apart."""


def _get(path: str) -> bytes | None:
    """GET from the terminal; None on 472 no data. Retries rate limits, 5xx and drops."""
    for attempt in range(8):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/{path}", timeout=900) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == NO_DATA:
                return None
            if e.code == LARGE_REQUEST:
                raise LargeRequestError from e
            if e.code not in RETRY_STATUS:
                raise RuntimeError(f"HTTP {e.code} for {path}: {e.read()[:200]!r}") from e
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(min(60, 2 ** attempt))
    raise RuntimeError(f"gave up after 8 attempts: {path}")


def _path(kind: str, symbol: str, exp: dt.date, d: dt.date, right: str) -> str:
    q = f"symbol={symbol}&expiration={exp:%Y%m%d}&strike=*&right={right}"
    if kind in ("quote_1m", "ohlc_1m"):
        return (f"option/history/{kind.removesuffix('_1m')}?{q}&date={d:%Y%m%d}"
                "&interval=1m&start_time=09:30:00&end_time=16:15:00")
    if kind == "open_interest":
        return f"option/history/open_interest?{q}&date={d:%Y%m%d}"
    return f"option/history/eod?{q}&start_date={d:%Y%m%d}&end_date={d:%Y%m%d}"


def fetch(kind: str, symbol: str, exp: dt.date, d: dt.date) -> pd.DataFrame | None:
    try:
        bodies = [_get(_path(kind, symbol, exp, d, "both"))]
    except LargeRequestError:
        bodies = [_get(_path(kind, symbol, exp, d, right)) for right in ("call", "put")]
    frames = [f for f in (pd.read_csv(io.BytesIO(b)) for b in bodies if b) if not f.empty]
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    df["expiration"] = pd.to_datetime(df["expiration"]).dt.date
    df = df[df["expiration"] == exp].reset_index(drop=True)
    for col in TIME_COLUMNS:
        if col in df:
            df[col] = pd.to_datetime(df[col], format="ISO8601").dt.tz_localize("America/New_York")
    return df if not df.empty else None


def file_path(set_name: str, kind: str, d: dt.date) -> Path:
    return OPEN_DIR / set_name / kind / f"{d:%Y}" / f"{d.isoformat()}.parquet"


def run_job(set_name: str, symbol: str, exp: dt.date, d: dt.date, kinds: list[str]) -> list[dict]:
    records = []
    for kind in kinds:
        t0 = time.time()
        df = fetch(kind, symbol, exp, d)
        rec = {"set": set_name, "date": d.isoformat(), "expiration": exp.isoformat(), "kind": kind}
        if df is None:
            rec.update(status="no_data", rows=0)
        else:
            path = file_path(set_name, kind, d)
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            df.to_parquet(tmp, compression="zstd", index=False)
            tmp.replace(path)
            rec.update(status="ok", rows=len(df), strikes=int(df["strike"].nunique()))
        rec["seconds"] = round(time.time() - t0, 1)
        records.append(rec)
    return records


def cboe_sessions() -> list[dt.date]:
    req = urllib.request.Request(CBOE_SPX, headers={"User-Agent": "butterfly-guy-research"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        df = pd.read_csv(io.BytesIO(resp.read()))
    df.columns = [c.strip().upper() for c in df.columns]
    return sorted(pd.to_datetime(df["DATE"], format="%m/%d/%Y").dt.date)


def expirations(symbol: str) -> list[dt.date]:
    body = _get(f"option/list/expirations?symbol={symbol}")
    return sorted({dt.date.fromisoformat(e) for e in pd.read_csv(io.BytesIO(body))["expiration"]})


def plan(set_name: str, sessions: list[dt.date], start: dt.date, end: dt.date) -> list[tuple]:
    """(expiration, trade date) pairs for `set_name` with the trade date in start..end."""
    symbol, dte = SETS[set_name]
    session_set = set(sessions)
    pairs = []
    for exp in expirations(symbol):
        if exp not in session_set:
            continue
        i = bisect.bisect_left(sessions, exp) - dte
        if i < 0:
            continue
        d = sessions[i]
        if start <= d <= end:
            pairs.append((exp, d))
    return pairs


def load_no_data() -> set[tuple[str, str, str]]:
    seen = set()
    catalog = OPEN_DIR / "catalog.jsonl"
    if catalog.exists():
        for line in catalog.read_text().splitlines():
            r = json.loads(line)
            if r["status"] == "no_data":
                seen.add((r["set"], r["date"], r["kind"]))
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sets", nargs="+", choices=list(SETS), default=list(SETS))
    ap.add_argument("--start", type=dt.date.fromisoformat, default=VALUE_START)
    ap.add_argument("--end", type=dt.date.fromisoformat,
                    help="last trade date (default: the last Cboe session before today)")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true", help="print the plan and exit")
    args = ap.parse_args()

    sessions = cboe_sessions()
    last = max(s for s in sessions if s < dt.date.today())
    end = min(args.end or last, last)
    start = max(args.start, VALUE_START)
    no_data = load_no_data()

    jobs, summary = [], []
    for set_name in args.sets:
        pairs = plan(set_name, sessions, start, end)
        todo = 0
        for exp, d in pairs:
            kinds = [k for k in KINDS if not file_path(set_name, k, d).exists()
                     and (set_name, d.isoformat(), k) not in no_data]
            if kinds:
                jobs.append((set_name, SETS[set_name][0], exp, d, kinds))
                todo += 1
        summary.append(f"{set_name:10} {len(pairs):5} sessions, {todo} to fetch")
    print(f"trade dates {start} -> {end}")
    print("\n".join(summary), flush=True)
    if args.dry_run or not jobs:
        return 0

    jobs.sort(key=lambda j: (j[3], j[0]))
    failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_job, *job): job for job in jobs}
        for n, fut in enumerate(as_completed(futures), 1):
            set_name, _, _, d, _ = futures[fut]
            try:
                records = fut.result()
            except Exception as e:  # noqa: BLE001 - keep going; a re-run retries this day
                failed += 1
                print(f"[{n}/{len(jobs)}] {set_name} {d} FAILED: {e}", flush=True)
                continue
            OPEN_DIR.mkdir(parents=True, exist_ok=True)
            with (OPEN_DIR / "catalog.jsonl").open("a") as fh:
                for rec in records:
                    fh.write(json.dumps(rec) + "\n")
            parts = " ".join(f"{r['kind']}={r['rows'] if r['status'] == 'ok' else 'none'}"
                             for r in records)
            print(f"[{n}/{len(jobs)}] {set_name} {d} {parts}", flush=True)
    print(f"done: {len(jobs) - failed} sessions fetched, {failed} failed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
