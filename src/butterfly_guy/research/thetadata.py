"""ThetaData SPXW option quotes, plus local SPX/VIX minute files, as a `history.HistorySource`.

**Plan (2026-09-28): ThetaData Options Value only ($40/mo).** Its historical 1-minute
quotes reach 2020-01-01, which is all `vendor_1m` needs. The Indices subscription is not
bought, so the three things it would have supplied come from elsewhere:

- **Intraday SPX and VIX:** the owner's minute files (`spx_1min.csv`, `vix_1min.csv`;
  gitignored, passed as paths; owner-supplied, added 2026-03-11 in commit 7417014, original
  vendor unknown). Columns `ts, close, high, low, open`, US Central wall-clock
  time, stamped at the bar **end** (first bar 08:31 CT = 09:31 ET, last regular bar
  15:00 CT, early closes 12:00 CT). The bar close is the level at its timestamp.
  Checked 2026-09-28 against Cboe for 2022-01-03 -> 2025-12-10: the trading days match
  exactly, and the VIX last bar equals the Cboe close (median |diff| 0.01). The files end
  2025-12-09. A day with a run of `STALE_RUN` identical bars inside 09:31-16:00 ET is a
  forward-filled fake (for example SPX 2022-02-25, VIX 2022-10-25). Such a day is not
  served for that symbol and is listed in `describe()["index_files"]`; `history.build_session`
  then skips the session. Nothing is derived to replace it.
- **After the files end** (the validation window, 2026-03-13 onward), SPX and `$VIX` come
  from our recorded Helios dataset's ticks (real Schwab observations) and the SPX open, high
  and low from its `daily_bars`, when a `recorded` dataset is given. Never inside the
  holdout.
- **Official daily bars:** Cboe's public `SPX_History.csv` (close only) and
  `VIX_History.csv` (OHLC). SPX open, high and low are the minute file's first-bar open,
  high and low, and NaN on a missing or stale day. The SPX minute file's last bar is *not*
  the official close (median $0.41 off), so settlement always uses Cboe's close.

Access
------
- The local Theta Terminal (v3, Java 21+) serves REST at `http://127.0.0.1:25503/v3`.
  Always use `127.0.0.1`: switching to `localhost` mid-session gives error 476 WRONG_IP.
- The terminal holds the credential (`THETADATA_API_KEY`, or a mode-600 `.env` beside the
  jar, kept outside the repo). Requests to the local server carry no credential, so **this
  module never reads one**.
- Options Value allows 2 concurrent requests; pulls here run sequentially.

Requests (every one goes through `history.GuardedSource`, which checks the holdout first)
----------------------------------------------------------------------------------------
- `sessions`: `GET /option/list/expirations?symbol=SPXW`, filtered at once to the pull's
  dates (dates only, no prices).
- `quotes`: `GET /option/history/quote?symbol=SPXW&expiration=D&date=D&strike=*&right=both
  &interval=1m&start_time=09:30:00&end_time=16:00:00`, one day at a time (about 250k CSV
  rows), filtered locally to the requested integer strikes. With an interval, each row is
  "the last quote at the interval's timestamp", so a row's timestamp is the grid time.
- Errors: 472 NO_DATA -> empty (the session is recorded as skipped); 429, 474 and 5xx or a
  dropped connection -> retried with backoff; 570 LARGE_REQUEST -> calls and puts fetched
  separately.

Row mapping (checked on ThetaData's 2025-08-19 sample)
-----------------------------------------------------
- Timestamps are `YYYY-MM-DDTHH:mm:ss[.SSS]` ET wall-clock time with no offset; they become
  UTC microseconds.
- `right` is `CALL`/`PUT` -> `C`/`P`.
- A 0/0 row means no quote (every contract's 09:30:00 row in the sample): bid and ask
  become NaN, so the carried state is empty, not a zero bid. A zero bid with a real ask is
  a genuine quote and is kept.

Still to confirm once the terminal runs
---------------------------------------
- The timestamp zone on a DST-change day (first development sessions after 2022-03-13 and
  2022-11-06).
- The SPXW expiration list before 2022-05-16 (ThetaData: Monday, Wednesday and Friday
  only), which sets the development session count.
- Licence (Terms §2.1(i) and §12.2): whether a local Parquet cache may be kept, and whether
  cancelling counts as termination. Ask ThetaData in writing.

Sources (read 2026-09-28): https://www.thetadata.net/pricing ;
https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html ;
https://thetadata.net/docs/operations/option_history_quote.html ;
https://thetadata.net/docs/operations/option_list_expirations.html ;
https://thetadata.net/docs/openapiv3.yaml ; https://thetadata.net/terms-and-conditions
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from butterfly_guy.research.dataset import Dataset, sha256_file
from butterfly_guy.research.holdout import in_holdout
from butterfly_guy.research.market import et_us

BASE_URL = "http://127.0.0.1:25503/v3"
CBOE_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{index}_History.csv"
FILE_TZ = "America/Chicago"
STALE_RUN = 30  # identical consecutive minute bars that mark a forward-filled day
RETRY_STATUS = {429, 474, 500, 502, 503, 504}
NO_DATA = 472
LARGE_REQUEST = 570
QUOTE_COLUMNS = ["ts_us", "strike", "t", "bid", "ask"]


class ThetaDataError(RuntimeError):
    """The Theta Terminal answered with an error that retrying will not fix."""


def _ymd(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


def _et_to_utc_us(ts: pd.Series) -> np.ndarray:
    t = pd.to_datetime(ts, format="ISO8601").dt.tz_localize("America/New_York")
    return t.dt.tz_convert("UTC").astype("datetime64[us, UTC]").astype("int64").to_numpy()


def parse_quotes(text: str, d: dt.date, strikes: tuple[float, float]) -> pd.DataFrame:
    """ThetaData quote CSV -> `ts_us, strike, t, bid, ask` for `d`'s expiration, integer
    strikes in `strikes`; 0/0 rows become NaN/NaN."""
    df = pd.read_csv(io.StringIO(text))
    if df.empty:
        return pd.DataFrame(columns=QUOTE_COLUMNS)
    df = df[(pd.to_datetime(df["expiration"]).dt.date == d)
            & df["strike"].between(strikes[0], strikes[1])
            & (df["strike"] == np.round(df["strike"]))]
    t = df["right"].str.upper().map({"CALL": "C", "PUT": "P"})
    if t.isna().any():
        raise ThetaDataError(f"unexpected right values {sorted(df['right'][t.isna()].unique())}")
    bid = df["bid"].to_numpy(dtype="float64", copy=True)
    ask = df["ask"].to_numpy(dtype="float64", copy=True)
    none = (bid == 0) & (ask == 0)
    bid[none] = np.nan
    ask[none] = np.nan
    return pd.DataFrame({"ts_us": _et_to_utc_us(df["timestamp"]),
                         "strike": df["strike"].astype("float64").to_numpy(),
                         "t": t.to_numpy(), "bid": bid, "ask": ask})


def load_minute_file(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """An owner minute file -> (rows `date, ts_us, price, open, high, low` inside
    09:31-16:00 ET with stale days removed, the stale dates). `price` is the bar close at
    its end-stamped timestamp."""
    raw = pd.read_csv(path, usecols=["ts", "open", "high", "low", "close"])
    local = pd.to_datetime(raw["ts"], format="%Y-%m-%d %H:%M:%S").dt.tz_localize(FILE_TZ)
    et = local.dt.tz_convert("America/New_York")
    hm = et.dt.hour * 60 + et.dt.minute
    keep = (hm >= 9 * 60 + 31) & (hm <= 16 * 60)
    raw, et = raw[keep], et[keep]
    date = et.dt.date
    ohlc = raw[["open", "high", "low", "close"]]
    same = (ohlc == ohlc.groupby(date).shift()).all(axis=1)
    run = same.groupby([date, (~same).cumsum()]).cumsum()
    longest = run.groupby(date).max()
    stale = sorted(d.isoformat() for d in longest[longest >= STALE_RUN].index)
    out = pd.DataFrame({
        "date": date.to_numpy(),
        "ts_us": et.dt.tz_convert("UTC").astype("datetime64[us, UTC]").astype("int64").to_numpy(),
        "price": raw["close"].astype("float64").to_numpy(),
        "open": raw["open"].astype("float64").to_numpy(),
        "high": raw["high"].astype("float64").to_numpy(),
        "low": raw["low"].astype("float64").to_numpy(),
    })
    stale_set = {dt.date.fromisoformat(s) for s in stale}
    return out[~out["date"].isin(stale_set)].reset_index(drop=True), stale


def fetch_cboe(index: str) -> bytes:
    import httpx

    with httpx.Client(follow_redirects=True, timeout=60.0,
                      headers={"User-Agent": "butterfly-guy-research"}) as client:
        resp = client.get(CBOE_URL.format(index=index))
        resp.raise_for_status()
        return resp.content


def parse_cboe(data: bytes, index: str) -> pd.DataFrame:
    """Cboe daily file -> `date` plus lower-case OHLC columns (SPX has `close` only)."""
    df = pd.read_csv(io.BytesIO(data))
    df.columns = [c.strip().upper() for c in df.columns]
    expected = {"SPX": ["DATE", "SPX"], "VIX": ["DATE", "OPEN", "HIGH", "LOW", "CLOSE"]}[index]
    if list(df.columns) != expected:
        raise ValueError(f"{index}: unexpected Cboe columns {list(df.columns)}")
    out = pd.DataFrame({"date": pd.to_datetime(df["DATE"], format="%m/%d/%Y").dt.date})
    for c in expected[1:]:
        out["close" if c == "SPX" else c.lower()] = pd.to_numeric(df[c], errors="coerce")
    return out


class ThetaDataSource:
    """`HistorySource`: ThetaData Options Value quotes through the local Theta Terminal,
    SPX/VIX levels from the owner's minute files, official bars from Cboe."""

    def __init__(self, spx_minutes: Path | str, vix_minutes: Path | str,
                 base_url: str = BASE_URL, *, recorded: Dataset | None = None, transport=None,
                 cboe: Callable[[str], bytes] = fetch_cboe,
                 sleep: Callable[[float], None] = time.sleep, retries: int = 5) -> None:
        self.base_url, self.recorded = base_url, recorded
        self.paths = {"SPX": Path(spx_minutes), "$VIX": Path(vix_minutes)}
        for p in self.paths.values():
            if not p.is_file():
                raise FileNotFoundError(f"index minute file not found: {p}")
        self._transport, self._cboe_fetch, self._sleep = transport, cboe, sleep
        self.retries = retries
        self._client = None
        self._minutes: dict[str, pd.DataFrame] = {}
        self._stale: dict[str, list[str]] = {}
        self._cboe: dict[str, tuple[str, pd.DataFrame]] = {}

    # -- inputs --------------------------------------------------------------

    def _minute(self, symbol: str) -> pd.DataFrame:
        if symbol not in self._minutes:
            self._minutes[symbol], self._stale[symbol] = load_minute_file(self.paths[symbol])
        return self._minutes[symbol]

    def _daily(self, index: str) -> pd.DataFrame:
        if index not in self._cboe:
            data = self._cboe_fetch(index)
            self._cboe[index] = (hashlib.sha256(data).hexdigest(), parse_cboe(data, index))
        return self._cboe[index][1]

    def _http(self):
        if self._client is None:
            import httpx

            self._client = httpx.Client(base_url=self.base_url, timeout=180.0,
                                        transport=self._transport)
        return self._client

    def _get(self, path: str, params: dict) -> str | None:
        """CSV body, or None on 472 NO_DATA. Retries transient failures."""
        import httpx

        for attempt in range(self.retries + 1):
            try:
                resp = self._http().get(path, params={**params, "format": "csv"})
            except httpx.TransportError as exc:
                if attempt == self.retries:
                    raise ThetaDataError(f"{path}: terminal unreachable ({exc})") from exc
            else:
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code == NO_DATA:
                    return None
                if resp.status_code not in RETRY_STATUS or attempt == self.retries:
                    raise ThetaDataError(f"{path} {params}: HTTP {resp.status_code} "
                                         f"{resp.text[:200]}")
            self._sleep(min(2 ** attempt, 30))
        raise AssertionError("unreachable")

    # -- HistorySource -------------------------------------------------------

    def describe(self) -> dict:
        """Plan, licence and input hashes; loads the local files and the Cboe daily files
        so the manifest pins exactly what was used. Never a credential."""
        for s in self.paths:
            self._minute(s)
        for index in ("SPX", "VIX"):
            self._daily(index)
        return {
            "vendor": "ThetaData",
            "status": "subscribed",
            "product": "SPXW option quotes, 1-minute intervals (/option/history/quote)",
            "plan": "Options Value",
            "licence": "individual: personal, non-commercial use (terms read 2026-09-28)",
            "access": f"Theta Terminal v3 REST at {self.base_url}",
            "index_files": {
                s: {"path": str(p), "sha256": sha256_file(p), "tz": FILE_TZ,
                    "stamp": "bar end", "price": "bar close",
                    "stale_run_minutes": STALE_RUN, "stale_days_excluded": self._stale[s]}
                for s, p in self.paths.items()},
            "recorded": None if self.recorded is None else {
                "dataset": self.recorded.name, "dataset_hash": self.recorded.hash,
                "used_for": "SPX and $VIX ticks, SPX open/high/low, after the minute files end "
                            "(never in the holdout)"},
            "daily_bars": {
                "SPX": {"url": CBOE_URL.format(index="SPX"), "sha256": self._cboe["SPX"][0],
                        "close": "Cboe official",
                        "open_high_low": "SPX minute file, then the recorded dataset"},
                "$VIX": {"url": CBOE_URL.format(index="VIX"), "sha256": self._cboe["VIX"][0],
                         "ohlc": "Cboe official"},
            },
        }

    def sessions(self, start: dt.date, end: dt.date) -> list[dt.date]:
        text = self._get("/option/list/expirations", {"symbol": "SPXW"})
        if text is None:
            return []
        exp = pd.to_datetime(pd.read_csv(io.StringIO(text))["expiration"]).dt.date
        return sorted(d for d in set(exp) if start <= d <= end)

    def quotes(self, d: dt.date, strikes: tuple[float, float]) -> pd.DataFrame:
        base = {"symbol": "SPXW", "expiration": _ymd(d), "date": _ymd(d), "strike": "*",
                "interval": "1m", "start_time": "09:30:00", "end_time": "16:00:00"}
        try:
            texts = [self._get("/option/history/quote", {**base, "right": "both"})]
        except ThetaDataError as exc:
            if f"HTTP {LARGE_REQUEST}" not in str(exc):
                raise
            texts = [self._get("/option/history/quote", {**base, "right": r})
                     for r in ("call", "put")]
        frames = [parse_quotes(t, d, strikes) for t in texts if t]
        if not frames:
            return pd.DataFrame(columns=QUOTE_COLUMNS)
        return pd.concat(frames, ignore_index=True)

    def _recorded_ticks(self, d: dt.date, symbol: str) -> pd.DataFrame:
        ts, px = self.recorded.spot_ticks(symbol)
        lo = np.searchsorted(ts, et_us(d, 9, 30), side="left")
        hi = np.searchsorted(ts, et_us(d, 16, 0), side="right")
        return pd.DataFrame({"ts_us": ts[lo:hi].astype("int64"),
                             "price": px[lo:hi].astype("float64")})

    def index_bars(self, d: dt.date, symbol: str) -> pd.DataFrame:
        m = self._minute(symbol)
        day = m.loc[m["date"] == d, ["ts_us", "price"]].reset_index(drop=True)
        if (day.empty and self.recorded is not None and d > m["date"].max()
                and not in_holdout(d)):
            return self._recorded_ticks(d, symbol)
        return day

    def daily_bars(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        spx = self._daily("SPX")
        spx = spx[(spx["date"] >= start) & (spx["date"] <= end)]
        m = self._minute("SPX")
        m = m[(m["date"] >= start) & (m["date"] <= end)]
        g = m.groupby("date")
        intraday = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(),
                                 "low": g["low"].min()})
        if self.recorded is not None:
            rec = self.recorded.daily_bars()
            after = max(self._minute("SPX")["date"].max() + dt.timedelta(days=1), start)
            rec = rec[(rec["underlying"] == "SPX") & (rec["date"] >= after)
                      & (rec["date"] <= end) & ~rec["date"].map(in_holdout)].set_index("date")
            intraday = pd.concat([intraday, rec[["open", "high", "low"]]])
        spx = spx.join(intraday, on="date").assign(underlying="SPX")
        vix = self._daily("VIX")
        vix = vix[(vix["date"] >= start) & (vix["date"] <= end)].assign(underlying="$VIX")
        cols = ["date", "underlying", "open", "high", "low", "close"]
        return pd.concat([spx[cols], vix[cols]], ignore_index=True)

    def cost_estimate(self, start: dt.date, end: dt.date) -> float | None:
        return None  # flat-rate subscription
