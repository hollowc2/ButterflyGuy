# ThetaData option history (raw)

Raw 1-minute option history from ThetaData (Options Value plan), downloaded by
`uv run tools/thetadata_download.py`. The files are gitignored: the vendor licence is personal,
non-commercial use, so they must never be committed or shared.

## Sets

| Set | Option root | What it holds |
|---|---|---|
| `spxw_0dte` | SPXW | Each SPXW expiration, on its expiration day |
| `spxw_1dte` | SPXW | Each SPXW expiration, on the trading session before it |
| `ndxp_0dte` | NDXP | Each NDXP (PM-settled NDX) expiration, on its expiration day |
| `xsp_0dte` | XSP | Each XSP expiration, on its expiration day |

Coverage starts at 2020-01-01, the Options Value limit. Expirations were not daily at first:
SPXW until 2022-05, NDXP until 2022-09 and XSP until 2022-10. Days with no expiration have no file.

## Layout

`<set>/<kind>/<YYYY>/<YYYY-MM-DD>.parquet`, where the date is the **trade date**.

| Kind | Content |
|---|---|
| `quote_1m` | NBBO at each minute 09:30–16:15 ET: `bid`, `ask`, sizes, exchanges, conditions |
| `ohlc_1m` | Trade bars per minute: `open`, `high`, `low`, `close`, `volume`, `count`, `vwap` |
| `open_interest` | Opening open interest per contract |
| `eod` | Vendor end-of-day summary: day OHLC, volume, closing bid/ask |

`catalog.jsonl` has one line per request: set, date, expiration, kind, status (`ok` or
`no_data`), rows and strikes. `download.log` is the run log.

## Conventions

- **Time:** `timestamp`, `created` and `last_trade` are America/New_York datetimes.
- **Types:** `expiration` is a date. `right` is `CALL` or `PUT`.
- **No quote:** a `quote_1m` row with bid 0 and ask 0 means no quote yet (every contract at
  09:30). A zero bid with a real ask is a genuine quote.
- **No trades:** an `ohlc_1m` minute with no trades has volume 0 and OHLC 0.0.
- **Not included:** there are no greeks, IV or underlying index levels. Greeks, IV and trade
  ticks need the Standard plan, and index levels need the Indices plan.

## The spent holdout (2024-07-01 to 2026-03-12)

These trade dates were the research holdout and were kept apart in `data/thetadata_sealed/`
until H-TS1 was registered. H-TS1 then used them for its one evaluation (run
`ce91c4a08efd`, 2026-09-30, FAIL), so they now live here with everything else and can be
read. Any result on them is post hoc: it can never be presented as an unseen test.
`catalog.holdout-20261003.jsonl` keeps the sealed folder's catalog byte for byte, for
reproducing records that cite it. `catalog.jsonl` holds every request, including these.

## Reading

```python
import pandas as pd
df = pd.read_parquet("data/thetadata/spxw_0dte/quote_1m/2024/2024-01-03.parquet")
```

```sql
-- duckdb: a whole year at once
SELECT * FROM 'data/thetadata/spxw_0dte/quote_1m/2023/*.parquet';
```
