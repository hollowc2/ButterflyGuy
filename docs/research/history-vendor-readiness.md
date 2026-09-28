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
