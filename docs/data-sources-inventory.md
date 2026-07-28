# ButterflyGuy data sources and data types

Generated: 2026-07-13

This is an inventory of data ButterflyGuy can read, store, derive, or expose. It is
based on the current repository and a read-only inspection of the running
`butterfly_guy` TimescaleDB schema. All examples below are fabricated and redacted;
none are copied from a real Schwab account, order, position, transaction, or token.

## At a glance

| Area | Sources | Main formats |
|---|---|---|
| Broker and market data | Charles Schwab API | JSON |
| Research market data | Yahoo Finance through `yfinance` | DataFrame/series normalized to Python records |
| Equity universes | GitHub dataset, Wikipedia, Nasdaq Trader, local lists | CSV, HTML, pipe-delimited text, plain text, JSON |
| News and events | SEC, Alpha Vantage, Forex Factory | JSON, CSV, HTML, XML |
| Durable data | PostgreSQL/TimescaleDB | SQL rows with JSONB metadata/payloads |
| Backtest inputs | TimescaleDB, CSV files, local JSON caches, synthetic chains | SQL, CSV, JSON, Python dataclasses |
| Configuration and secrets | YAML, environment variables, OAuth token file | YAML, strings/numbers/booleans, secret JSON |
| Observability | Prometheus endpoints, health endpoints, structured logs | Prometheus text, JSON, JSON Lines |
| Reports and charts | Local report files and notification payloads | Markdown, HTML, JSON, PNG, Discord/Telegram text |

Status terms used below:

- **Live path**: used by the trading/collector services.
- **Scheduled/on-demand**: used by a script or report workflow, but not necessarily
  by every running app container.
- **Optional**: requires configuration, credentials, or an explicit command.
- **Derived**: calculated from another source rather than independently observed.

## 1. Charles Schwab API

Schwab is the primary external source. Authentication uses the local OAuth token
file plus API credentials. The examples show response shape only.

### 1.1 Account-number resolution

- Status: **Live path**, during client initialization.
- Data: account number and Schwab account hash.
- Types: JSON object; strings.
- Sensitivity: private account identity. The account hash is used for later account
  and order requests.

```json
[{"accountNumber": "***1234", "hashValue": "<redacted-account-hash>"}]
```

### 1.2 Option chains

- Status: **Live path** for SPX, NDX, and XSP 0-DTE chains.
- Data: underlying price; expiration/strike maps; call and put contracts; bid, ask,
  mark, last, sizes, volume, open interest, implied volatility, Greeks, intrinsic
  value, time value, moneyness, multiplier, and theoretical value.
- Types: nested JSON; strings, dates, floats, integers, booleans.

```json
{
  "underlyingPrice": 6312.42,
  "callExpDateMap": {
    "2026-07-13:0": {
      "6315.0": [{
        "symbol": "SPXW  260713C06315000",
        "bid": 7.10,
        "ask": 7.40,
        "mark": 7.25,
        "last": 7.20,
        "bidSize": 12,
        "askSize": 9,
        "totalVolume": 184,
        "openInterest": 521,
        "volatility": 18.42,
        "delta": 0.47,
        "gamma": 0.031,
        "theta": -6.81,
        "vega": 0.72,
        "rho": 0.01,
        "intrinsicValue": 0.0,
        "timeValue": 7.25,
        "inTheMoney": false,
        "daysToExpiration": 0,
        "multiplier": 100,
        "theoreticalOptionValue": 7.23
      }]
    }
  },
  "putExpDateMap": {"2026-07-13:0": {"6315.0": [{"bid": 9.60, "ask": 9.90}]}}
}
```

### 1.3 Single-symbol spot/index quotes

- Status: **Live path** for `$SPX`, `$NDX`, `$XSP`, and `$VIX`-style symbols.
- Data: last price, mark, or close price; the client uses the first available value.
- Types: nested JSON and float.

```json
{"$SPX": {"quote": {"lastPrice": 6312.42, "mark": 6312.35, "closePrice": 6294.11}}}
```

### 1.4 Batched equity quotes

- Status: **Scheduled/on-demand** for the morning equity scan and liquid-universe
  refresh.
- Data: regular and extended-hours price, bid/ask, close, percent change, trade
  timestamp, and volume fields for batches of stock symbols.
- Types: symbol-keyed JSON; floats, integers, epoch milliseconds.

```json
{
  "AAPL": {
    "quote": {
      "lastPrice": 228.15,
      "mark": 228.12,
      "closePrice": 224.80,
      "netPercentChange": 1.49,
      "totalVolume": 18420123,
      "tradeTime": 1783946400000
    },
    "extended": {
      "lastPrice": 229.02,
      "bidPrice": 228.98,
      "askPrice": 229.05,
      "totalVolume": 524110,
      "tradeTime": 1783960200000
    }
  }
}
```

### 1.5 Price-history candles

- Status: **Live/scheduled/on-demand**.
- Data: one-minute intraday candles and daily OHLCV candles for indices, ETFs, VIX,
  and equity-trade charts.
- Types: JSON list; epoch milliseconds, floats, integer volume.

```json
{"candles": [{"datetime": 1783953000000, "open": 6310.10, "high": 6314.80, "low": 6308.55, "close": 6312.42, "volume": 12345}]}
```

### 1.6 Market movers

- Status: **Optional**; supported by the morning scan, currently disabled in the
  checked-in equity-scan configuration.
- Data: top movers by exchange/index bucket, direction, and frequency.
- Types: JSON list; symbols, price changes, percentages, volume.

```json
[{"symbol": "XYZ", "description": "Example Corp", "lastPrice": 42.18, "netChange": 3.71, "netPercentChange": 9.64, "volume": 1875000}]
```

### 1.7 Account snapshot, balances, and positions

- Status: **Live path** for risk guards; **scheduled/on-demand** for the daily
  report card.
- Data: account type, initial/current balances, liquidation value, buying power,
  available funds, maintenance requirements, and positions with instrument,
  quantity, market value, and open P&L.
- Types: nested JSON; strings, floats, lists.
- Sensitivity: private financial/account data.

```json
{
  "securitiesAccount": {
    "type": "MARGIN",
    "initialBalances": {"liquidationValue": 100000.00},
    "currentBalances": {
      "liquidationValue": 100425.50,
      "buyingPowerNonMarginableTrade": 25000.00,
      "availableFunds": 26000.00,
      "maintenanceRequirement": 1200.00
    },
    "positions": [{
      "longQuantity": 1,
      "marketValue": 725.00,
      "currentDayProfitLoss": 85.00,
      "instrument": {"assetType": "OPTION", "symbol": "<redacted-option-symbol>"}
    }]
  }
}
```

### 1.8 Orders and order status

- Status: **Live path** for submission/status/cancel/recovery; **scheduled/on-demand**
  for reporting and reconciliation.
- Data: order ID, status, timestamps, price, quantity, legs, child orders, fills,
  rejection/cancel details, and raw broker payload.
- Types: nested JSON; strings, floats, integers, lists.
- Important: reading status is safe; placing or cancelling an order changes broker
  state and is not a data-only operation.

```json
{
  "orderId": "<redacted-order-id>",
  "status": "FILLED",
  "enteredTime": "2026-07-13T14:01:20Z",
  "closeTime": "2026-07-13T14:01:31Z",
  "price": 0.85,
  "quantity": 1,
  "filledQuantity": 1,
  "orderLegCollection": [{
    "instruction": "BUY_TO_OPEN",
    "quantity": 1,
    "instrument": {"assetType": "OPTION", "symbol": "<redacted-option-symbol>"}
  }]
}
```

### 1.9 Account transactions

- Status: **Scheduled/on-demand** for daily report-card reconstruction.
- Data: transaction type, time, net amount, order ID, fees, and transfer items with
  instruments, quantities, and opening/closing position effects.
- Types: nested JSON; strings, floats, lists.
- Sensitivity: private trading and cash-movement history.

```json
{
  "type": "TRADE",
  "time": "2026-07-13T18:45:00Z",
  "netAmount": 142.50,
  "orderId": "<redacted-order-id>",
  "transferItems": [{
    "amount": 1,
    "positionEffect": "CLOSING",
    "instrument": {"assetType": "OPTION", "symbol": "<redacted-option-symbol>"}
  }]
}
```

## 2. Other external and public sources

### 2.1 Yahoo Finance (`yfinance`)

- Status: **Research/on-demand**, not the primary live trading feed.
- Symbols used include `^GSPC`, `^NDX`, `^VIX`, and in one analysis mapping `SPX`.
- Data: daily open/high/low/close/volume history, SPX previous close, VIX daily
  close, and SPY-to-SPX calibration inputs.
- Types: pandas `DataFrame` with timestamp index and numeric columns.

```text
Date,Open,High,Low,Close,Volume
2026-07-10,6280.40,6310.70,6268.10,6294.11,0
```

### 2.2 S&P 500 constituent dataset on GitHub

- Status: **On-demand** universe refresh.
- Data: ticker symbol and GICS sector metadata.
- Format: CSV.

```csv
Symbol,Security,GICS Sector,GICS Sub-Industry
AAPL,Apple Inc.,Information Technology,Technology Hardware
```

### 2.3 Wikipedia Nasdaq-100 page

- Status: **On-demand** universe refresh.
- Data: Nasdaq-100 constituent ticker symbols parsed from HTML table cells.
- Format: HTML normalized to a list of strings.

```json
["AAPL", "ADBE", "AMD"]
```

### 2.4 Nasdaq Trader symbol directories

- Status: **On-demand** liquid-universe refresh.
- Endpoints: `nasdaqlisted.txt` for NASDAQ and `otherlisted.txt` for NYSE/common
  listings.
- Data: symbols, security names, exchange code, ETF flag, test-issue flag, and
  other directory metadata. ButterflyGuy removes ETFs, test issues, preferreds,
  warrants, and units before Schwab price/volume validation.
- Format: pipe-delimited text.

```text
Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
ABCD|Example Common Stock|Q|N|N|100|N|N
```

```text
ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
WXYZ|Example NYSE Common Stock|N|WXYZ|N|100|N|WXYZ
```

### 2.5 SEC company ticker map and submissions

- Status: **Scheduled/on-demand** catalyst scan when the SEC provider is enabled.
- Data: ticker-to-CIK mapping plus recent filing form, filing date, and document
  description. Relevant forms include 8-K, 10-Q, 10-K, S-1, S-3, SC 13D/G, and
  proxy statements.
- Format: JSON.

```json
{"0": {"cik_str": 123456, "ticker": "ABCD", "title": "Example Corp"}}
```

```json
{
  "cik": "0000123456",
  "filings": {
    "recent": {
      "form": ["8-K"],
      "filingDate": ["2026-07-13"],
      "primaryDocDescription": ["Current report"]
    }
  }
}
```

### 2.6 Alpha Vantage earnings calendar and news sentiment

- Status: **Optional**; requires `ALPHA_VANTAGE_API_KEY`.
- Data: upcoming earnings dates and fiscal periods; news headline, topics, ticker
  relevance, and sentiment metadata.
- Formats: earnings CSV and news JSON.

```csv
symbol,name,reportDate,fiscalDateEnding,estimate,currency
ABCD,Example Corp,2026-07-16,2026-06-30,1.24,USD
```

```json
{
  "feed": [{
    "title": "Example Corp announces quarterly results",
    "topics": [{"topic": "earnings"}],
    "ticker_sentiment": [{
      "ticker": "ABCD",
      "relevance_score": "0.91",
      "ticker_sentiment_score": "0.35"
    }]
  }]
}
```

### 2.7 Forex Factory economic calendar

- Status: **Parser available but not wired into an active caller in this checkout**.
- Data: USD event title, date, time, impact, forecast, and previous value.
- Formats: HTML primary source; XML fallback.

```xml
<event>
  <title>CPI m/m</title><country>USD</country><date>07-15-2026</date>
  <time>8:30am</time><impact>High</impact><forecast>0.2%</forecast><previous>0.1%</previous>
</event>
```

### 2.8 Local market calendar and clock

- Status: **Live path**.
- Data: UTC/Eastern/Pacific timestamps, US market holidays, early closes, market
  open/close windows, premarket windows, minutes to close, and time regimes.
- Source: Python standard-library datetime/zoneinfo plus repository holiday rules;
  this is not an exchange API feed.

```json
{"session_date": "2026-07-13", "market_open_et": "09:30", "market_close_et": "16:00", "is_trading_day": true}
```

## 3. ButterflyGuy-owned TimescaleDB data

The running database currently exposes the following ten ButterflyGuy tables.
Examples are representative rows, not live values.

### 3.1 `option_chain_snapshots`

- Purpose: historical full-chain snapshots; Timescale hypertable.
- Types: `timestamptz`, `date`, `text`, `numeric`, `integer`, `boolean`.

```json
{"snapshot_time":"2026-07-13T14:30:00Z","underlying":"SPX","expiration":"2026-07-13","strike":6315.0,"option_type":"CALL","bid":7.10,"ask":7.40,"mark":7.25,"last":7.20,"volume":184,"open_interest":521,"iv":18.42,"delta":0.47,"gamma":0.031,"theta":-6.81,"vega":0.72,"symbol":"SPXW  260713C06315000","spot_price":6312.42,"bid_size":12,"ask_size":9,"rho":0.01,"intrinsic_value":0.0,"time_value":7.25,"in_the_money":false,"days_to_expiration":0,"multiplier":100,"theoretical_value":7.23}
```

### 3.2 `spot_prices`

- Purpose: collector-interval underlying/VIX observations; Timescale hypertable.
- Types: `timestamptz`, `text`, `numeric`.

```json
{"ts":"2026-07-13T14:30:00Z","underlying":"SPX","price":6312.42,"source":"schwab"}
```

### 3.3 `butterfly_candidates`

- Purpose: every scanned butterfly candidate, including whether it was selected;
  Timescale hypertable.
- Types: `timestamptz`, `text`, `integer`, `numeric`, `boolean`.

```json
{"scan_time":"2026-07-13T14:31:00Z","underlying":"SPX","direction":"CALL","wing_width":20,"center_strike":6330.0,"lower_strike":6310.0,"upper_strike":6350.0,"cost":1.85,"max_profit":18.15,"reward_risk":9.81,"lower_be":6311.85,"upper_be":6348.15,"distance_from_spot":17.58,"spot_price":6312.42,"selected":true}
```

### 3.4 `butterfly_trades`

- Purpose: full local trade lifecycle and analytics source of truth.
- Types: `integer`, `date`, `timestamptz`, `text`, `numeric`, `jsonb`.

```json
{"id":101,"trade_date":"2026-07-13","underlying":"SPX","direction":"CALL","wing_width":20,"center_strike":6330.0,"lower_strike":6310.0,"upper_strike":6350.0,"entry_price":1.85,"entry_time":"2026-07-13T14:31:20Z","exit_price":3.20,"exit_time":"2026-07-13T16:05:00Z","exit_reason":"drawdown_morning","pnl":1.35,"peak_value":4.10,"lower_symbol":"<redacted>","center_symbol":"<redacted>","upper_symbol":"<redacted>","quantity":1,"status":"CLOSED","metadata":{"entry_spot":6312.42,"paper":true}}
```

### 3.5 `decision_log`

- Purpose: event-by-event explanation of system decisions and state changes.
- Current live schema includes a nullable `underlying` column in addition to the
  repository's base event fields.
- Types: `integer`, `timestamptz`, `text`, `jsonb`.

```json
{"id":9001,"ts":"2026-07-13T14:31:01Z","underlying":"SPX","event_type":"entry_blocked","data":{"reason":"chain_snapshot_stale","age_seconds":241,"limit_seconds":180}}
```

### 3.6 `daily_risk_state`

- Purpose: daily per-underlying trade count, realized P&L, loss-limit state, and
  halt state.
- Types: `date`, `text`, `integer`, `numeric`, `boolean`.

```json
{"trade_date":"2026-07-13","underlying":"SPX","trade_count":1,"realized_pnl":135.00,"max_loss_hit":false,"halted":false}
```

### 3.7 `daily_bars`

- Purpose: daily OHLCV for SPX/NDX/XSP/VIX and previous-close/trend lookups.
- Types: `date`, `text`, `numeric`, `bigint`.

```json
{"date":"2026-07-10","underlying":"SPX","open":6280.40,"high":6310.70,"low":6268.10,"close":6294.11,"volume":0}
```

### 3.8 `tent_boundaries`

- Purpose: time series of the dynamic lower/upper profit-tent boundaries;
  Timescale hypertable.
- Types: `timestamptz`, `text`, `numeric`.

```json
{"ts":"2026-07-13T16:00:00Z","underlying":"SPX","lower_tent":6315.25,"upper_tent":6344.75}
```

### 3.9 `monitoring_leg_quotes`

- Purpose: high-frequency quotes for the three legs of an open trade without
  storing an entire chain every monitor poll; Timescale hypertable.
- Types: `timestamptz`, `integer`, `date`, `text`, `numeric`.

```json
{"ts":"2026-07-13T15:00:00Z","trade_id":101,"underlying":"SPX","expiration":"2026-07-13","strike":6330.0,"option_type":"CALL","bid":11.10,"ask":11.50,"mark":11.30,"symbol":"<redacted>","spot_price":6325.20,"fly_mark":3.40,"peak_value":4.10,"drawdown_pct":0.1707}
```

### 3.10 `broker_order_intents`

- Purpose: durable entry/exit intent, broker reconciliation, and restart recovery.
- Types: `bigint`, `integer`, `date`, `timestamptz`, `text`, `numeric`, `jsonb`.
- Sensitivity: order specifications and raw broker payloads can contain private
  account/trading details.

```json
{"id":501,"underlying":"SPX","trade_date":"2026-07-13","trade_id":101,"side":"ENTRY","status":"FILLED","broker_order_id":"<redacted>","limit_price":1.85,"quantity":1,"order_spec":{"orderType":"NET_DEBIT","complexOrderStrategyType":"BUTTERFLY"},"candidate_snapshot":{"center_strike":6330.0,"cost":1.85},"last_broker_status":"FILLED","raw_broker_payload":{"orderId":"<redacted>","status":"FILLED"},"created_at":"2026-07-13T14:31:18Z","updated_at":"2026-07-13T14:31:31Z"}
```

## 4. Shared database tables visible to the same DB account

These seven tables are currently readable in the same `public` schema, but they
belong to other projects and ButterflyGuy code does not consume them. Treat them
as accessible shared infrastructure, not ButterflyGuy-owned data.

| Table | Data | Representative example |
|---|---|---|
| `bars_1m` | Crypto minute OHLCV | `{"ts":"2026-07-13T14:30:00Z","coin":"BTC","open":118000.0,"high":118100.0,"low":117950.0,"close":118050.0,"volume":12.4}` |
| `l2_book` | Crypto L2 order-book level | `{"ts":"2026-07-13T14:30:00Z","coin":"BTC","side":"B","level":0,"price":118049.0,"size":1.25}` |
| `trades` | Crypto trade tape | `{"ts":"2026-07-13T14:30:01Z","coin":"BTC","price":118050.0,"size":0.05,"side":"B","trade_id":"example"}` |
| `polymarket_ohlcv` | Polymarket OHLCV plus source provenance | `{"asset":"BTC","timeframe":"5m","market":"example-market","ts":"2026-07-13T14:30:00Z","open":0.51,"high":0.54,"low":0.50,"close":0.53,"volume":1000,"source_file":"example.json"}` |
| `polymarket_trades` | Compact Polymarket strategy trade records | `{"id":"example","ts":"2026-07-13T14:30:00Z","strategy":"example","asset":"BTC","direction":"YES","amount":10.0,"entry_price":0.53,"pnl":2.10,"won":true,"paper":true}` |
| `polymarket_trade_archive` | Extended archived trade, execution, bankroll, and raw JSON fields | `{"id":"example","strategy":"example","fill_price":0.54,"slippage_pct":0.01,"settlement_status":"resolved","raw_json":{}}` |
| `strategies` | Shared strategy activation registry | `{"name":"example-strategy","is_active":true}` |

## 5. Local files and backtest inputs

### 5.1 Application YAML configuration

- Files: `configs/config.yaml`, `config_ndx.yaml`, `config_xsp.yaml`,
  `equity_scan.yaml`, and `daily_report_card.yaml`.
- Data: strategy widths/costs, entry windows, execution mode, paper-fill settings,
  risk limits, collector interval, database connection settings, monitoring port,
  scan filters, provider settings, and report thresholds.
- Types: nested mappings/lists with strings, numbers, booleans, and nulls.

```yaml
strategy:
  underlying: SPX
  wing_widths: [10, 20, 30]
execution:
  paper_trading: true
collector:
  snapshot_interval_seconds: 60
```

### 5.2 Environment variables and `.env`

- Data: Schwab API credentials/account selection, DB password/overrides, live-trade
  allow flag, Discord/Telegram destinations, SEC user agent, and optional Alpha
  Vantage key.
- Types: strings parsed into strings, numbers, or booleans by settings code.
- Sensitivity: secrets. Never copy `.env` values into analysis artifacts.

```dotenv
SCHWAB_API_KEY=<redacted>
SCHWAB_ACCOUNT_ID=<redacted>
DATABASE_PASSWORD=<redacted>
ALLOW_LIVE_TRADING=false
```

### 5.3 `tokens.json`

- Data: an opaque Schwab OAuth token document managed by `schwab-py`.
- Type: secret JSON file.
- Sensitivity: critical credential material. Its contents are intentionally not
  summarized or exemplified here.

```json
{"tokens.json":"<secret OAuth document; contents intentionally omitted>"}
```

### 5.4 Universe and metadata files

- Plain-text symbol lists: `sp500.txt`, `nq100.txt`, `liquid.txt`, `custom.txt`.
- JSON metadata: `sectors.json` and `liquid_meta.json`.

```text
AAPL
MSFT
NVDA
```

```json
{"AAPL":{"price":228.15,"avg_volume_20d":51230000.0,"exchange":"NASDAQ"}}
```

```json
{"AAPL":"Information Technology","JPM":"Financials"}
```

### 5.5 Historical minute CSVs

- Status: **Optional research input** for `CsvDataLoader`.
- Expected files: SPX and VIX one-minute CSVs.
- Required fields: `ts`, `open`, `high`, `low`, `close`; source volume is absent
  and becomes `0`.
- Timestamps are interpreted as naive US/Eastern and converted to UTC.

```csv
ts,open,high,low,close
2026-07-13 09:30:00,6300.00,6304.25,6298.75,6302.50
```

### 5.6 Local daily bar cache

- Path pattern: `data/schwab/YYYY-MM-DD.json`.
- Data: a date, VIX value, prior close, underlying minute bars, and optional VIX
  minute bars.
- Source: Schwab SPY minute candles scaled to SPX levels plus Yahoo daily inputs.

```json
{
  "date":"2026-07-13",
  "vix":17.8,
  "prev_close":6294.11,
  "bars":[{"ts":"2026-07-13T13:30:00+00:00","open":6300.0,"high":6304.25,"low":6298.75,"close":6302.5,"volume":1000}],
  "vix_bars":[]
}
```

### 5.7 Local option-chain cache

- Path pattern: `data/chains/<UNDERLYING>/YYYY-MM-DD.json` with a legacy
  un-namespaced fallback.
- Data: timestamp-keyed spot and option quote snapshots.

```json
{
  "date":"2026-07-13",
  "snapshots":{
    "2026-07-13T14:30:00+00:00":{
      "spot":6312.42,
      "quotes":[{"strike":6315.0,"type":"CALL","bid":7.10,"ask":7.40,"mark":7.25,"iv":0.1842,"delta":0.47,"gamma":0.031,"symbol":"<redacted>","bid_size":12,"ask_size":9}]
    }
  }
}
```

## 6. Canonical and derived analytical data types

These are the main normalized records available to code and analysis after raw
source data is parsed.

| Type | Important fields | Representative example |
|---|---|---|
| `OptionQuote` | symbol, underlying, expiration, strike, type, bid/ask/mark/last, volume/OI, IV/Greeks, sizes, intrinsic/time value | `OptionQuote(strike=6315, option_type="CALL", bid=7.10, ask=7.40, mark=7.25, delta=0.47)` |
| `ButterflyCandidate` | direction, three strikes, width, cost/ask, max profit, R/R, breakevens, spot distance, leg quotes | `ButterflyCandidate(direction="CALL", wing_width=20, center_strike=6330, cost=1.85, reward_risk=9.81)` |
| `TradeRecord` | entry/exit lifecycle, P&L, peak, symbols, quantity, status | `TradeRecord(trade_id=101, entry_price=1.85, exit_price=3.20, pnl=1.35, status="CLOSED")` |
| `MinuteBar` | UTC timestamp, OHLC, volume | `MinuteBar(ts="2026-07-13T13:30:00Z", open=6300, high=6304.25, low=6298.75, close=6302.5, volume=1000)` |
| `DayData` | date, underlying bars, VIX, previous close, VIX bars, recent closes | `DayData(date="2026-07-13", bars=[...], vix=17.8, prev_close=6294.11)` |
| `EquitySnapshot` | symbol, live/prior prices, prior move/gap, volumes, RVOL, sector/universes, quote age/quality, news | `EquitySnapshot(symbol="ABCD", price=42.18, prior_day_pct=4.2, session_gap_pct=3.1, rvol=0.18, sector="Industrials")` |
| `NewsImpact` | symbol, score, reasons, headlines, upcoming events, SEC forms, providers | `NewsImpact(symbol="ABCD", score=6.0, reasons=("recent SEC filing",), sec_forms=("8-K",), providers=("sec",))` |
| `OpeningFocusItem` | equity snapshot, composite score, reasons | `OpeningFocusItem(snapshot=ABCD, score=8.4, reasons=("premarket gap", "catalyst"))` |
| `MarketContext` | index/ETF symbol, price, percent change | `MarketContext(symbol="$SPX", price=6312.42, change_pct=0.29)` |
| `ScanResults` | focus/catalyst/gainer/loser buckets, movers, market context, counts, rejects | `ScanResults(scanned_symbols=2100, matched_symbols=43, opening_focus=[...])` |
| `ForexEvent` | title, country, date, time, impact, forecast, previous | `ForexEvent(title="CPI m/m", country="USD", event_date="2026-07-15", time_str="8:30am", impact="High")` |
| `AccountBalances` | starting/ending liquidation, buying power, funds, maintenance, account type | `AccountBalances(starting_liquidation=100000, ending_liquidation=100425.50, buying_power=25000, account_type="MARGIN")` |
| `TradeResult` / `TradeLeg` | normalized Schwab transaction/order round trip and component legs | `TradeResult(label="ABCD", pnl=142.50, quantity=10, asset_type="EQUITY")` |
| `OpenPosition` | symbol, asset type, quantity, market value, open P&L, 0-DTE flag | `OpenPosition(symbol="<redacted>", asset_type="OPTION", quantity=1, market_value=725, open_pnl=85, is_zero_dte=true)` |
| `DailyReportCard` | balances, activity, normalized trades, positions, rejects, cash movement, problems | `DailyReportCard(report_date="2026-07-13", activity={"trade_count":3,"win_rate":66.7}, problems=[])` |
| `DayResult` | backtest entry/exit, P&L, strikes, path/state, and outcome fields | `DayResult(date="2026-07-13", traded=true, pnl=1.35, exit_reason="drawdown_morning")` |
| `TradePoint`, `ReportStats`, `DrawdownPoint` | performance-series trades, aggregate statistics, and equity drawdown | `ReportStats(total_pnl=1250.0, win_rate=60.0, average=62.5, best=400.0, worst=-225.0, profit_factor=1.8, max_drawdown=400.0, trade_count=20)` |

### Synthetic option-chain data

When a real cached/DB chain is unavailable in research, ButterflyGuy can derive a
synthetic chain from spot, VIX, expiration, and time using Black-Scholes plus an IV
skew model. Synthetic quotes include theoretical price, bid/ask spread, IV, delta,
gamma, theta, and vega. They are model output, not observed market quotes.

```json
{"symbol":"SYNTH_C6315","underlying":"SPX","expiration":"2026-07-13","strike":6315.0,"option_type":"CALL","bid":7.17,"ask":7.33,"mark":7.25,"iv":0.1842,"delta":0.47,"gamma":0.031,"theta":-6.81,"vega":0.72}
```

## 7. Operational and observability data

### 7.1 Prometheus metrics

- Status: **Live path**, served on `/metrics`; SPX, NDX, and XSP are scraped every
  15 seconds.
- Data types: counters, gauges, and histograms with endpoint/underlying/direction/
  outcome labels.
- Families include chain collection, candidate scans, trade counts/P&L, position
  value/peak/P&L, entry details, orders, and Schwab API calls/errors.

```text
butterfly_chain_snapshot_rows{underlying="SPX"} 487
butterfly_daily_pnl_dollars{underlying="SPX"} 135.0
butterfly_schwab_api_calls_total{endpoint="get_option_chain"} 1242
```

### 7.2 Health and readiness endpoints

- `/health`: service name, UTC timestamp, uptime.
- `/ready`: ready/not-ready plus reason.
- Format: JSON over HTTP.

```json
{"status":"ok","service":"SPX","timestamp":"2026-07-13T18:00:00","uptime_seconds":79200.0}
```

```json
{"status":"not_ready","reason":"initializing_schwab"}
```

### 7.3 Structured application logs

- Status: **Live path**, written as JSON to stdout/container logs by default.
- Data: timestamp, level, logger, event name, and event-specific fields.

```json
{"underlying":"SPX","rows":487,"event":"snapshot_collected","logger":"butterfly_guy.data.collector","level":"info","timestamp":"2026-07-13T14:30:02Z"}
```

## 8. Reports, archives, charts, and outbound destinations

These are derived outputs rather than independent source feeds, but they are data
available for later analysis.

| Output | Format | Example/content |
|---|---|---|
| Morning equity scan archive | Markdown plus JSON | human report plus machine-readable focus, catalysts, gainers/losers, market context, counts, and data-quality rejects |
| Daily report card archive | Markdown | balances, effective daily P&L, trades, transfers, watchlist |
| Optional raw daily report dump | JSON | redacted account snapshot, transactions, and orders |
| Live performance report | HTML plus embedded JSON | equity curve, statistics, no-trade days, drawdown series |
| Trade/performance charts | PNG | spot path, strikes, entry/exit, tent boundaries, performance |
| Grafana dashboards | SQL/PromQL rendered as panels | live state and historical TimescaleDB/Prometheus analysis |
| Discord webhooks | text/JSON plus optional PNG multipart attachment | entries, exits, errors, reports, scans, charts |
| Telegram notifier | text | risk warnings through the installed `notify` helper |

Example archived report fragment:

```markdown
📋 **Daily Report Card — Mon Jul 13, 2026**
Start: $100,000.00 → End: $100,425.50
**+$425.50 (+0.43%)**
```

## 9. Practical limitations and safety notes

- Schwab API access is credentialed, rate-limited, and account-specific. The
  repository supports broker writes, so analysis should use read-only methods unless
  order placement/cancellation is explicitly intended.
- Alpha Vantage data is unavailable without its API key. SEC access should use a
  descriptive `SEC_USER_AGENT`.
- Yahoo Finance is a research convenience, not the live trading source of truth.
- Forex Factory parsing exists, but no active production caller was found.
- CSV and JSON cache sources only exist for dates/files previously supplied or
  downloaded.
- Synthetic chains are estimates and must never be treated as observed quotes.
- The shared database tables in section 4 are visible to the DB account but are not
  owned, validated, or used by ButterflyGuy.
- Secrets and private broker/account payloads should stay out of committed reports.

## 10. Repository evidence map

- Schwab surfaces: `src/butterfly_guy/data/schwab_client.py`
- Chain normalization/storage: `src/butterfly_guy/data/collector.py`,
  `src/butterfly_guy/data/schemas.py`
- Current DB schema definitions: `src/butterfly_guy/db/migrations/`,
  `src/butterfly_guy/db/queries.py`
- Backtest sources/caches: `src/butterfly_guy/backtest/`
- Equity universes/news: `src/butterfly_guy/equity_scan/`
- Yahoo analysis paths: `src/butterfly_guy/backtest/schwab_loader.py`,
  `src/butterfly_guy/scripts/run_entry_analysis.py`,
  `src/butterfly_guy/scripts/run_paper_replay.py`,
  `src/butterfly_guy/scripts/run_backtest_db.py`
- Economic calendar: `src/butterfly_guy/services/forex_calendar.py`
- Account report normalization: `src/butterfly_guy/reports/daily_report_card.py`
- Configuration: `src/butterfly_guy/core/config.py`, `configs/`
- Metrics/health/logs: `src/butterfly_guy/core/metrics.py`,
  `src/butterfly_guy/core/logging.py`, `infra/prometheus.yml`
- Dashboards and data-source provisioning: `infra/grafana/`
