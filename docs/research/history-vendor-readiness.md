# SPX 0-DTE history vendors: readiness comparison, adapter spec and validation plan

Status: documentation only (2026-09-27). Nothing has been bought, no account was
created, and no credential was handled. Every figure below comes from the vendors' public
pages or a public third-party comparison, as cited; prices change and must be re-checked
at purchase.

**Update 2026-09-28:** nothing has been bought. The owner will likely buy ThetaData, from
2022 forward. The adapter framework, the holdout
guard and the validation harness below are built and tested on synthetic data
(`history.py`, `holdout.py`, `validate.py`; see `research-core.md`, "Vendor history").
Only a provider's own `HistorySource` is missing.

**Update 2026-09-28 (stage 5):** ThetaData's public documentation was read and a stub
source added (`research/thetadata.py`, not in `SOURCES`). See "ThetaData: public-docs
findings and purchase checklist" below.

Why: the review's power analysis (`docs/reviews/2026-09-27-research-pipeline-review.md`
§2) needs about 400 trades to separate the measured edge from zero. Our own chain history
starts 2026-03-13 (133 sessions). SPXW has had daily expirations since 2022, so vendor
history could add roughly 1,050 sessions (2022-01-03 → 2026-03-12).

## What the research core needs

From `research-core.md` and the replay code:

- **Per session:** a dense 0-DTE SPXW grid (timestamp × strike × call/put) of bid, ask
  and mark. `mark` in our Helios data is exactly `(bid + ask) / 2` (363,688 of 363,688
  quotes checked on 2026-04-01, 06-10 and 09-24). The live selector
  (`select_entry_candidate`) never reads `iv` or `delta`, so greeks are optional.
- **SPX spot on the decision clock:** used for selection, the gap open and the ATM
  straddle.
- **VIX at the entry time:** the bucket widths and the VIX anchor. Also the prior VIX
  close.
- **SPX official open and close:** gap direction under the `live` profile, and cash
  settlement against the official close.

## Vendors

| | ThetaData | Databento `OPRA.PILLAR` | Cboe DataShop Option Quotes |
|---|---|---|---|
| **SPXW 0-DTE intraday from 2022** | Yes, within plan depth: Value 4 years (today that reaches about 2022-09, so Jan–Aug 2022 are missing), Standard 8 years, Pro 12 years | `cbbo-1m` from 2013-04-01 (ten years added 2025-06). SPXW is the `SPXW.OPT` parent (SPX monthlies are `SPX.OPT`) | January 2012 → present. `^SPX` covers SPX and SPXW together |
| **Granularity** | Every OPRA NBBO (Standard/Pro), or interval aggregation from `10ms` to `1h`. With an interval, each row is "the last quote at the interval's timestamp". Value plan: 1-minute intervals | `cbbo-1m`: event-driven 1-minute consolidated BBO, with a record only when the BBO or a trade changes (quiet minutes have no row). Tick schemas (`tbbo`, `mbp-1`) also exist | A row per contract every minute (or N minutes), repeating the quote in quiet minutes |
| **Fields** | Bid, ask, sizes, exchange and condition. IV and 1st–3rd order greeks (Standard/Pro) computed from option and underlying midpoints. OHLC, open interest | Bid, ask, sizes, last trade. No IV, no greeks, no underlying | NBBO bid/ask/size, OHLC, volume. Optional "Calcs": active underlying price, IV, delta, gamma, theta, vega, rho. Optional open interest |
| **SPX index level** | Separate Indices subscription (index price, OHLC, EOD) | **Not available.** OPRA carries options only | **Only with a Cboe Global Indices Feed licence** (fees from $1,000/month). Historical full-market purchases exclude it; a "complimentary run" can be requested |
| **VIX intraday** | Indices subscription | Not available | Not available (index level) |
| **Daily bars / settlement** | Index EOD (Indices subscription) | None | None for index levels |
| **Licensing (private research)** | Individual plans: "personal use only, no redistribution or business use" | Licence agreements managed in the portal; historical data is usage-billed. Check the non-professional terms at sign-up | Per-purchase DataShop terms; check at purchase |
| **Format and access** | Local Java "Theta Terminal" serving REST (CSV/JSON); flat files. Multi-day requests limited to one month | API or batch download in DBN, CSV or JSON. `metadata.get_cost` quotes a request's price before download | Zipped CSV per day, download or SFTP |
| **Cost** | Options: Value $40/mo, Standard $80/mo, Pro $160/mo. Indices priced separately | Usage-based. A third-party comparison (Concretum, 2026-09-08, windows ending 2026-08-27) found 12 months of SPX+SPXW `cbbo-1m` at $423 and 13 years at about $6,123. The Standard plan ($199/mo) includes the last 12 months of L1 | Priced by date window, then capped. `^SPX` 1-minute: $550 per year, capped at $2,200 from year four without Calcs, or $3,385 with Calcs (same source) |

**Agreement between vendors.** The Concretum comparison joined DataShop and Databento
1-minute SPX/SPXW data for May 2023 (about 155 million quote rows). Bid, ask and size
agreed on 99.999% of joined rows. The row counts differed only because `cbbo-1m` omits
quiet minutes.

**Sources:**
- [ThetaData pricing](https://www.thetadata.net/pricing)
- ThetaData [quote history](https://docs.thetadata.us/operations/option_history_quote.html)
  and [first-order greeks](https://docs.thetadata.us/operations/option_history_greeks_first_order.html) docs
- [Databento OPRA.PILLAR](https://databento.com/datasets/OPRA.PILLAR) and its
  [2025-06-03 pricing post](https://databento.com/blog/introducing-new-opra-pricing-plans)
- [Cboe DataShop Option Quotes](https://datashop.cboe.com/option-quote-intervals)
- [Concretum Research, "SPX Options Database: Databento vs. Cboe DataShop"](https://concretumgroup.substack.com/p/spx-options-database-databento-vs)

### Assessment

- **Options quotes alone are not enough.** Every vendor needs a second source for the
  SPX level and intraday VIX, both of which the selector uses. Only ThetaData sells all
  three (options, SPX, VIX) under one account.
- **Cheapest complete path: ThetaData Standard plus Indices**, for one or two months
  (about $80/mo plus the Indices tier). It covers 2018 onward, has tick NBBO and 1-minute
  interval quotes, and its individual licence fits private research. Its data quality is
  unmeasured, which is what the validation plan below is for.
- **Reference-quality alternative: DataShop `^SPX` 1-minute with Calcs** ($3,385, 2012
  onward), plus a separate SPX/VIX index source. Its quotes are the academic 0-DTE
  standard, and it has a complete row per minute.
- **Databento suits a partial or cross-check pull** (for example, one month to validate
  another vendor), not the full history, because it lacks the index levels.
- **Settlement.** SPXW is PM-settled on the official SPX close. The vendor era needs
  official closes and opens for 2022 → 2026-03, because our `daily_bars` start 2026-03-02.
  ThetaData index EOD provides them. Otherwise an S&P-licensed daily source is needed,
  cross-checked against Cboe's settlement values, as the 2026-09-21 settlement parity did.

The choice is the owner's. The adapter and the validation plan below apply to any of them.

## ThetaData: public-docs findings and purchase checklist (2026-09-28)

**Status: not purchased.** The owner will likely buy ThetaData, from 2022 forward.
`research/thetadata.py` is a stub (every data method raises; not in `history.SOURCES`) that
holds the endpoints and the request plan below. Everything here was read on 2026-09-28 from
ThetaData's public pages, with no account, sign-up or terminal install. "To confirm at
purchase" marks what the pages do not settle.

### Plans and prices (as read)

| Plan | Pricing page | Subscriptions doc | Reaches 2022-01-03? |
|---|---|---|---|
| Options Value, $40/mo | 4 years, 1-minute intervals | 1-minute from 2020-01-01 | **Conflict: to confirm at purchase** |
| Options Standard, $80/mo | 8 years, tick level | tick level from 2016-01-01 | Yes |
| Options Pro, $160/mo | 12 years, tick level | from 2012-06-01 | Yes |
| Indices Value, $30/mo | 2 years, 15-minute intervals, 1-day delayed | 1-minute from 2023-01-01, 15-minute delay | No |
| Indices Standard, $50/mo | 3 years, 1-minute intervals, real-time SPX & VIX | "lowest reported by venues" from 2022-01-01 | **Conflict: to confirm at purchase** |
| Indices Pro, $100/mo | 7 years, tick level, real-time SPX, VIX & NDX | from 2017-01-01 | Yes |

*(Correction, marked: the vendor table above says Value reaches "about 2022-09". That
follows the pricing page; the docs say 2020-01-01. Either way the choice below is safe.)*

- **Safe choice for 2022 → 2026-03:** Options Standard + Indices Pro, $180/month. With
  Indices Standard, $130/month, if ThetaData confirms it reaches 2022-01-03 at 1 minute.
- **What the Indices tier gives:** intraday SPX and VIX (`/index/history/price`), and an
  index EOD report with open, high, low and close (`/index/history/eod`), which ThetaData
  generates itself at 17:15 ET. Whether that open and close equal the official S&P values is
  **to confirm at purchase** (validation step 4 checks the closes; development closes can be
  checked against Cboe's public `SPX_History.csv`; no free source checks the opens).
- **Concurrency** is account-wide at the highest tier held (Value 2, Standard 4, Pro 8).
  There is no rate limit.

### Licence (individual plans)

- Pricing page: "Personal use only, no redistribution or business use".
- Terms & Conditions §1.1: a limited, revocable licence "solely for the personal,
  non-commercial use" of the subscriber; no use "in connection with any trade, business,
  professional or other commercial activities".
- §2.1(i): the subscriber shall not "archive, download, reproduce … create derivative
  works" of the content.
- §12.2: on termination, remove all services and content, destroy copies, and certify it in
  writing within 30 days.
- **To confirm with ThetaData in writing before paying:** whether a personal subscriber may
  keep a local Parquet cache for personal research, and whether cancelling the subscription
  counts as termination under §12.2. If the data must be deleted on cancelling, the
  subscription must stay active for as long as the vendor datasets are used. (This is a
  reading of the published terms, not legal advice.)

### Access, credential and timestamps

- The local Theta Terminal v3 (Java 21+) serves REST at `http://127.0.0.1:25503/v3`. Use
  `127.0.0.1` only (error 476 on switching to `localhost`).
- **Credential.** The terminal holds it: an API key from `--api-key`, the
  `THETADATA_API_KEY` environment variable or a `.env` beside the jar, or email and password
  in `creds.txt`. Requests to the local server carry no credential, so **our code never
  reads it**. Keep it in a mode-600 `.env` outside the repo, not on the command line.
- **Timestamps.** Rows carry `YYYY-MM-DDTHH:mm:ss.SSS` with no offset; ThetaData's Python
  library types them as `America/New_York`, so the adapter reads ET wall-clock time. To
  confirm at purchase on a DST-change day (none falls in the validation window; check the
  first development sessions after 2022-03-13 and 2022-11-06).
- **Interval rows.** "The quote for each interval represents the last quote at the
  interval's timestamp"; index prices are "the price at the exact time of each timestamp".
  To confirm at purchase: whether that instant is included, and whether a contract with no
  quote yet returns a 0/0 row (which the adapter must map to NaN, not a zero bid).
- **Limits.** Multi-day requests are capped at one month (option quotes must also name an
  expiration); responses should stay under about 1M rows.
- **Sessions.** ThetaData says SPXW was quoted only Monday, Wednesday and Friday before
  2022-05-16, so the development window has about 590 sessions, not the draft's 625. The
  expirations list will settle the exact count.

### Endpoints and request plan

| Need | Endpoint (v3) | Plan |
|---|---|---|
| Sessions | `/option/list/expirations?symbol=SPXW` | once per pull; filtered at once to the pull's dates |
| Strikes | `/option/list/strikes?symbol=SPXW&expiration=D` | once per session |
| Quotes | `/option/history/quote?symbol=SPXW&expiration=D&date=D&strike=*&right=both&interval=1m` | once per session (single day, ~200–250k rows); kept within ±400 of the day's SPX range |
| SPX, VIX intraday | `/index/history/price?symbol=SPX\|VIX&date=D&interval=1m` | once per session each, so no batch can reach into the holdout |
| Official bars | `/index/history/eod?symbol=SPX\|VIX&start_date=&end_date=` | chunks of at most one month inside the guarded range |

| Pull | Sessions | Calls | Sequential time (est.) | Parquet (est.) |
|---|---:|---:|---|---|
| Validation 2026-03-13 → 2026-09-25 | 133 | ~550 | 20–40 min | ~130 MB |
| Development 2022-01-03 → 2024-06-28 | ~590 | ~2,420 | 1–2.5 h | ~0.6 GB |
| Holdout 2024-07-01 → 2026-03-12 | ~425 | ~1,750 | 0.7–1.8 h | ~0.45 GB |

Latency per call is unmeasured; the validation pull measures it before the others.

### Purchase checklist

1. **Confirm in writing** (ThetaData support): the licence question above; the history
   start of Options Value and Indices Standard; the EOD open/close definition.
2. **Choose the plans:** Options Standard ($80/mo) and Indices Pro ($100/mo), or Indices
   Standard ($50/mo) if it is confirmed to reach 2022-01-03 at 1 minute.
3. **Expected subscription length:** at least one month, covering the validation and
   development pulls, the owner's review and registration, and the holdout pull. Longer if
   registration slips, or if the licence requires deleting the data on cancelling (then for
   as long as the vendor datasets are in use).
4. **Implement** `ThetaDataSource`, add it to `history.SOURCES`, and only then install and
   start the terminal with the credential kept outside the repo.
5. **Pull in the order the holdout guard enforces:**
   1. the validation window, **2026-03-13 → 2026-09-25**, then `validate-vendor`;
   2. only if every validation step passes, the development window, **2022-01-03 →
      2024-06-28**;
   3. the owner's registration (`register` from a clean, committed tree);
   4. only then the holdout, **2024-07-01 → 2026-03-12**, with `--unseal-holdout <seq>`.

**A single "2022 → today" download is not allowed.** It would touch the sealed holdout
before registration; the guard refuses it before any request is made, and a registration
made after holdout data landed can never unseal anything.

Sources (read 2026-09-28):
[pricing](https://www.thetadata.net/pricing),
[subscriptions](https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html),
[getting started](https://thetadata.net/docs/Articles/Getting-Started/Getting-Started.html),
[option quote history](https://thetadata.net/docs/operations/option_history_quote.html),
[expirations](https://thetadata.net/docs/operations/option_list_expirations.html),
[strikes](https://thetadata.net/docs/operations/option_list_strikes.html),
[index price history](https://thetadata.net/docs/operations/index_history_price.html),
[index EOD](https://thetadata.net/docs/operations/index_history_eod.html),
[making requests](https://thetadata.net/docs/Articles/Data-And-Requests/Making-Requests.html),
[concurrent requests](https://thetadata.net/docs/Articles/Data-And-Requests/Concurrent-Requests.html),
[request sizing](https://thetadata.net/docs/Articles/Data-And-Requests/Request-Sizing.html),
[data issues](https://thetadata.net/docs/Articles/Data-And-Requests/Data-Issues.html),
[OpenAPI spec](https://thetadata.net/docs/openapiv3.yaml),
[terms and conditions](https://thetadata.net/terms-and-conditions).

## `DataSource` adapter spec

A vendor adapter writes the **existing research Parquet schema** (`dataset.py`) directly,
into a **new dataset name** (for example `spx_0dte_<vendor>`), so it never touches
`spx_0dte`. Suggested interface:

```python
class HistorySource(Protocol):
    def describe(self) -> dict: ...                      # vendor, product, plan, licence
    def sessions(self, start: date, end: date) -> list[date]:  # SPXW expiring that day
    def quotes(self, d: date, strikes: tuple[float, float]) -> pd.DataFrame:
        # long rows: ts_us, strike, t (C/P), bid, ask, mark, iv, delta, spot
    def index_bars(self, d: date, symbol: str) -> pd.DataFrame:  # SPX, VIX: ts_us, price
    def daily_bars(self, start: date, end: date) -> pd.DataFrame:  # official OHLC
```

`export.py`'s `dense_chain_from_rows`, `write_table` and the manifest/history code are
reused unchanged. Mapping rules:

- **Timestamps.** Every row's `ts_us` is the UTC microsecond at which the quote state
  applied.
  - ThetaData interval rows: the interval timestamp ("last quote at the interval's
    timestamp"), in ET milliseconds → UTC.
  - DataShop: `quote_datetime` (ET) → UTC.
  - Databento `cbbo-1m`: `ts_recv` of the record.
- **Decision clock.** `clock.parquet` becomes the vendor's 1-minute grid from 09:31 to
  16:00 ET (16:00 → 13:00 on early closes). The timestamp of each grid point, not a bar
  start, is what the replay compares with the decision time. A new decision profile
  (`vendor_1m`) is needed; the Helios profiles stay as they are.
- **Quote state in quiet minutes.** DataShop repeats unchanged quotes and ThetaData
  intervals return the last quote. For `cbbo-1m`, the last record's BBO remains the
  quote until the next record. This is the vendor's own quote state, not imputation.
  It is only carried within a session, and each carried row records its age
  (`quote_age_s`, a new optional column). Nothing is carried across sessions or from
  before the first quote of the day.
- **Missing quotes.** No quote state means NaN in every field. A zero bid is a real
  quote and is kept. A crossed quote stays crossed; `market.py` already treats it as
  unexecutable. Nothing is interpolated or modelled.
- **Mark.** `(bid + ask) / 2`, the same as Schwab's `mark` in our data. Recorded as
  `mark_source = "mid"` in the manifest.
- **Greeks.** Vendor IV and delta where supplied (ThetaData Standard/Pro, DataShop
  Calcs), else NaN. They are never computed by us. The selector does not use them.
- **Strike band.** The same as `export.py`: integer SPXW strikes within ±400 of the day's
  spot range.
- **Spot.**
  - Preferred: the vendor's SPX index price at each grid timestamp.
  - Fallback, flagged `spot_source = "parity"`: the put-call-parity forward from the
    nearest-ATM call/put mids at the same timestamp. For 0-DTE the carry is negligible.
    Its error must be measured in the validation before use.
- **VIX.** Intraday index level at the grid timestamp, from an index source. The prior
  close comes from Cboe's public daily file (already in `aux/vol_index_daily.parquet`).
- **Manifest.** `source` records the vendor, product, plan, request parameters and
  licence. Each vendor file is hashed as today, and `history` logs every pull.

## Validation plan (before any sweep uses vendor data)

Re-derive our own recorded sessions, 2026-03-13 → 2026-09-25, from the vendor, then
compare against the Helios export (`dd38a5ec…`). The pass criteria below are fixed now,
before any vendor data is seen.

1. **Quote level**, at every Helios chain timestamp, for every strike in the ±200 band.
   Take the vendor quote as of that timestamp (last state at or before it).
   - Report the share of bid/ask pairs within $0.05, the median absolute difference, and
     presence agreement (quoted in one source, missing in the other).
   - Also report the timestamp offset that maximises agreement, since Schwab's snapshot
     time is our collector's request time, not the quote time.
   - *Pass:* at least 95% of bid/ask pairs within $0.05 in the 1.0–2.5σ OTM region where
     the strategy trades. The best offset is within one minute.
2. **Replay on the Helios clock.** Sample vendor quotes at Helios timestamps. Run E0 under
   `frozen_20260921` and `sweep_20260925`, and compare trade by trade with the Helios
   replay: fly, entry time, exit reason, and P&L in all four accounting models.
   - This isolates quote differences from clock differences.
   - *Pass:* the same fly on at least 90% of entries. Stressed total within the larger
     of ±5% and ±$750. Each disagreement explained by a quote difference at a decision
     snapshot.
3. **Replay on the vendor clock** (`vendor_1m`), with vendor spot and VIX. Same
   comparison as step 2, plus tie-set averages at $0.10 and $0.25.
   - Here the clock differs, so the check is at the level of distributions: stressed
     total, per-trade median and the settled count.
   - *Pass:* the stressed total's difference from the Helios replay is inside the
     $0.10 tie-set draw band of the Helios replay.
4. **Spot and settlement.**
   - Vendor or parity SPX at each Helios timestamp against Helios `spot`: report
     median |Δ| and p99.
   - Official closes against our `daily_bars` and Cboe settlement values: they must be
     identical, since settlement-dependent P&L relies on them.

A vendor that fails any step is not used for the sweep until the cause is understood. All
validation output goes to `reports/research/` with its own run hashes. It uses sessions
already seen, so it says nothing about any rule.
