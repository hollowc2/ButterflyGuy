"""ThetaData as a `history.HistorySource`: **STUB — NOT PURCHASED (2026-09-28).**

The owner will likely buy ThetaData history from 2022 forward. Until the subscription is
active, every data method raises and this source is **not** in `history.SOURCES`, so
`export-history` still stops before any request. The purchase checklist and the pull order
are in `docs/research/history-vendor-readiness.md`.

Everything below comes from ThetaData's public pages, read 2026-09-28 (no account, no
terminal install). "To confirm at purchase" marks what those pages do not settle.

Access
------
- The local Theta Terminal (v3, Java 21+) serves REST at `http://127.0.0.1:25503/v3`.
  Always use `127.0.0.1`: switching to `localhost` mid-session gives error 476 WRONG_IP.
- The terminal holds the credential: an API key from `--api-key`, the
  `THETADATA_API_KEY` environment variable or a `.env` beside the jar, or email and
  password in `creds.txt`. Requests to the local server carry no credential, so **this
  module never reads one**. Keep the key in a mode-600 `.env` outside the repo, not on the
  command line (visible in the process list).
- Concurrency is account-wide at the highest tier held (Value 2, Standard 4, Pro 8); there
  is no rate limit. Pulls here run sequentially.

Endpoints (v3)
--------------
- `GET /option/list/expirations?symbol=SPXW` -> `symbol, expiration` (all dates; updated
  overnight).
- `GET /option/list/strikes?symbol=SPXW&expiration=YYYYMMDD` -> `symbol, strike` (dollars).
- `GET /option/history/quote?symbol=SPXW&expiration=D&date=D&strike=*&right=both
  &interval=1m&start_time=09:30:00&end_time=16:00:00&format=ndjson`
  -> `symbol, expiration, strike, right, timestamp, bid_size, bid_exchange, bid,
  bid_condition, ask_size, ask_exchange, ask, ask_condition`. With an interval, "the quote
  for each interval represents the last quote at the interval's timestamp". Multi-day
  requests are limited to one month and must name an expiration.
- `GET /index/history/price?symbol=SPX|VIX&date=D&interval=1m` -> `timestamp, price`, "the
  price at the exact time of each timestamp". Unchanged prices are not re-reported.
  Multi-day requests are limited to one month.
- `GET /index/history/eod?symbol=SPX|VIX&start_date=&end_date=` -> `created, last_trade,
  open, high, low, close, ...`. ThetaData generates this report itself at 17:15 ET, since
  the index feeds publish no national EOD.
- Errors worth handling: 472 NO_DATA (record the session as skipped), 474 DISCONNECTED and
  429 OS_LIMIT (retry), 570 LARGE_REQUEST (split the request).

Timestamps: `YYYY-MM-DDTHH:mm:ss.SSS` with no offset. ThetaData's Python library types the
same field `datetime[ms, America/New_York]`, so rows are read as ET wall-clock time and
converted to UTC microseconds (`history.HistorySource` convention).

To confirm at purchase
----------------------
- History depth. The docs give Options Value 1-minute from 2020-01-01, the pricing page
  "4 years" (about 2022-09). Indices Standard: docs from 2022-01-01, pricing "3 years"
  (about 2023-09). Options Standard (2016-01-01 / 8 years) and Indices Pro (2017-01-01 /
  7 years) reach 2022-01-03 under either reading.
- The timestamp zone, on a DST-change day (the validation window has none; check the first
  development sessions after 2022-03-13 and 2022-11-06).
- Whether "the last quote at the interval's timestamp" includes that instant, and whether
  a contract with no quote yet returns a 0/0 row (which must become NaN, not a zero bid).
- Whether the EOD `open` and `close` equal the official SPX open and close (step 4 of the
  validation checks closes against Helios and Cboe; development closes can be checked
  against Cboe's public `SPX_History.csv`; no free source checks the opens).
- The SPXW expiration list before 2022-05-16 (ThetaData: quoted Monday, Wednesday and
  Friday only), which sets the development session count.

Request plan (per pull; the holdout guard wraps every call through `GuardedSource`)
---------------------------------------------------------------------------------
- `sessions`: one expirations call, filtered at once to the pull's dates (only dates cross
  the wire for the rest; no prices).
- Per session, four calls: the strikes list; all-strike 1-minute quotes for that day's
  expiration (single-day, so the one-month rule never binds; about 200-250k rows), filtered
  locally to integer strikes within +/-400 of the day's SPX range; SPX price; VIX price.
  Index prices stay per session so that no batch can reach past the pull's range into the
  sealed holdout (a March batch would include 2026-03-01 -> 03-12).
- `daily_bars`: index EOD for SPX and VIX, in chunks of at most one calendar month inside
  the range the guard has already checked.

Estimates (latency is unmeasured; the validation pull measures it first):

| Pull | Sessions | Calls | Sequential time | Parquet |
|---|---:|---:|---|---|
| Validation 2026-03-13 -> 2026-09-25 | 133 | ~550 | 20-40 min | ~130 MB |
| Development 2022-01-03 -> 2024-06-28 | ~590 | ~2,420 | 1-2.5 h | ~0.6 GB |
| Holdout 2024-07-01 -> 2026-03-12 (after registration) | ~425 | ~1,750 | 0.7-1.8 h | ~0.45 GB |

Sources (read 2026-09-28): https://www.thetadata.net/pricing ;
https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html ;
https://thetadata.net/docs/Articles/Getting-Started/Getting-Started.html ;
https://thetadata.net/docs/operations/option_history_quote.html ;
https://thetadata.net/docs/operations/option_list_expirations.html ;
https://thetadata.net/docs/operations/option_list_strikes.html ;
https://thetadata.net/docs/operations/index_history_price.html ;
https://thetadata.net/docs/operations/index_history_eod.html ;
https://thetadata.net/docs/Articles/Data-And-Requests/Making-Requests.html ;
https://thetadata.net/docs/Articles/Data-And-Requests/Concurrent-Requests.html ;
https://thetadata.net/docs/Articles/Data-And-Requests/Request-Sizing.html ;
https://thetadata.net/docs/Articles/Data-And-Requests/Data-Issues.html ;
https://thetadata.net/docs/openapiv3.yaml ; https://thetadata.net/terms-and-conditions
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

BASE_URL = "http://127.0.0.1:25503/v3"
NOT_PURCHASED = (
    "ThetaData not purchased yet: this source is a stub and is not in history.SOURCES. "
    "See the purchase checklist in docs/research/history-vendor-readiness.md."
)


class ThetaDataSource:
    """`HistorySource` for ThetaData through the local Theta Terminal. Stub: every data
    method raises until the subscription is active (see the module docstring)."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url

    def describe(self) -> dict:
        """Static description; no network, no credential."""
        return {
            "vendor": "ThetaData",
            "status": "not purchased (stub)",
            "product": "SPXW option quotes (1-minute intervals); SPX and VIX index price and EOD",
            "plan": "to choose at purchase: Options Standard; Indices Standard or Pro",
            "licence": "individual: personal, non-commercial use (terms read 2026-09-28)",
            "access": f"Theta Terminal v3 REST at {self.base_url}",
        }

    def sessions(self, start: dt.date, end: dt.date) -> list[dt.date]:
        raise NotImplementedError(f"{NOT_PURCHASED} (sessions {start}..{end})")

    def quotes(self, d: dt.date, strikes: tuple[float, float]) -> pd.DataFrame:
        raise NotImplementedError(f"{NOT_PURCHASED} (quotes {d})")

    def index_bars(self, d: dt.date, symbol: str) -> pd.DataFrame:
        raise NotImplementedError(f"{NOT_PURCHASED} (index_bars {symbol} {d})")

    def daily_bars(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        raise NotImplementedError(f"{NOT_PURCHASED} (daily_bars {start}..{end})")

    def cost_estimate(self, start: dt.date, end: dt.date) -> float | None:
        raise NotImplementedError(f"{NOT_PURCHASED} (cost_estimate {start}..{end})")
