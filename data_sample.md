# ButterflyGuy data sources — representative samples

Generated: 2026-07-14

This is the complete input inventory found in the current codebase. Samples are
representative and redacted: no token, account, broker-order, position, or live
financial data is copied here. "Runtime" means a running service can use it;
"tooling" means an explicit research, scan, or reporting command uses it.

## External sources

| Source | Used by | Sample |
|---|---|---|
| Charles Schwab account-number API | Runtime initialization | `[{"accountNumber":"***1234","hashValue":"<redacted>"}]` |
| Charles Schwab option-chain API | Runtime collector, entry, monitoring, settlement | `{"underlyingPrice":6312.42,"callExpDateMap":{"2026-07-13:0":{"6315.0":[{"bid":7.10,"ask":7.40,"mark":7.25,"delta":0.47,"volatility":18.42}]}}}` |
| Charles Schwab single quote API | Runtime spot/VIX pricing | `{"$SPX":{"quote":{"lastPrice":6312.42,"mark":6312.35,"closePrice":6294.11}}}` |
| Charles Schwab batched equity-quote API | Equity morning scan and liquid-universe refresh | `{"AAPL":{"quote":{"lastPrice":228.15,"totalVolume":18420123},"extended":{"lastPrice":229.02,"bidPrice":228.98,"askPrice":229.05}}}` |
| Charles Schwab price-history API | Runtime trend/settlement; daily-bar collector; backtests | `{"candles":[{"datetime":1783953000000,"open":6310.10,"high":6314.80,"low":6308.55,"close":6312.42,"volume":12345}]}` |
| Charles Schwab market-movers API | Optional morning-scan enrichment | `[{"symbol":"XYZ","lastPrice":42.18,"netPercentChange":9.64,"volume":1875000}]` |
| Charles Schwab account snapshot API | Runtime account/risk reconciliation; daily card | `{"securitiesAccount":{"currentBalances":{"liquidationValue":100425.50,"buyingPowerNonMarginableTrade":25000.00},"positions":[{"marketValue":725.00,"instrument":{"assetType":"OPTION","symbol":"<redacted>"}}]}}` |
| Charles Schwab orders API | Runtime reconciliation and status reporting | `[{"orderId":"<redacted>","status":"FILLED","price":0.85,"quantity":1,"orderLegCollection":[{"instruction":"BUY_TO_OPEN"}]}]` |
| Charles Schwab transactions API | Daily-card reconstruction and expiration settlement | `[{"type":"TRADE","time":"2026-07-13T18:45:00Z","netAmount":142.50,"orderId":"<redacted>"}]` |
| Yahoo Finance via `yfinance` | Backtest calibration, paper replay, entry analysis | `Date,Open,High,Low,Close,Volume\n2026-07-10,6280.40,6310.70,6268.10,6294.11,0` |
| S&P 500 constituents, GitHub dataset | Universe refresh | `Symbol,Security,GICS Sector\nAAPL,Apple Inc.,Information Technology` |
| Nasdaq-100 Wikipedia page | Universe refresh | `['AAPL', 'ADBE', 'AMD']` |
| Nasdaq Trader `nasdaqlisted.txt` | Liquid-universe seed | `Symbol|Security Name|Market Category|Test Issue|ETF\nABCD|Example Common Stock|Q|N|N` |
| Nasdaq Trader `otherlisted.txt` | Liquid-universe seed | `ACT Symbol|Security Name|Exchange|ETF|Test Issue\nWXYZ|Example NYSE Common Stock|N|N|N` |
| SEC ticker map | Optional equity catalyst scan | `{"0":{"cik_str":123456,"ticker":"ABCD","title":"Example Corp"}}` |
| SEC company-submissions API | Optional equity catalyst scan | `{"filings":{"recent":{"form":["8-K"],"filingDate":["2026-07-13"],"primaryDocDescription":["Current report"]}}}` |
| Alpha Vantage earnings calendar | Optional equity catalyst scan; requires API key | `symbol,name,reportDate,fiscalDateEnding\nABCD,Example Corp,2026-07-16,2026-06-30` |
| Alpha Vantage news sentiment | Optional equity catalyst scan; requires API key | `{"feed":[{"title":"Example Corp announces results","topics":[{"topic":"earnings"}],"ticker_sentiment":[{"ticker":"ABCD","relevance_score":"0.91"}]}]}` |
| Forex Factory calendar HTML | Calendar helper; no active caller in this checkout | `USD | CPI m/m | 8:30am | High | Fcst 0.2% | Prev 0.1%` |
| Forex Factory calendar XML fallback | Calendar helper; no active caller in this checkout | `<event><title>CPI m/m</title><country>USD</country><impact>High</impact></event>` |

Schwab order placement and cancellation are intentionally excluded: those are
state-changing actions, not data sources.

## Local durable data

The application reads these PostgreSQL/TimescaleDB tables. The first ten are
ButterflyGuy-owned; the final seven are visible to the configured database role
but are not consumed by ButterflyGuy code.

| Table | Sample |
|---|---|
| `option_chain_snapshots` | `{"snapshot_time":"2026-07-13T14:30:00Z","underlying":"SPX","expiration":"2026-07-13","strike":6315.0,"option_type":"CALL","bid":7.10,"ask":7.40,"mark":7.25,"iv":18.42,"delta":0.47,"spot_price":6312.42}` |
| `spot_prices` | `{"ts":"2026-07-13T14:30:00Z","underlying":"SPX","price":6312.42,"source":"schwab"}` |
| `butterfly_candidates` | `{"scan_time":"2026-07-13T14:31:00Z","underlying":"SPX","direction":"CALL","wing_width":20,"center_strike":6330.0,"cost":1.85,"reward_risk":9.81,"selected":true}` |
| `butterfly_trades` | `{"id":101,"trade_date":"2026-07-13","underlying":"SPX","entry_price":1.85,"exit_price":3.20,"pnl":1.35,"status":"CLOSED","metadata":{"paper":true}}` |
| `decision_log` | `{"id":9001,"ts":"2026-07-13T14:31:01Z","underlying":"SPX","event_type":"entry_blocked","data":{"reason":"chain_snapshot_stale","age_seconds":241}}` |
| `daily_risk_state` | `{"trade_date":"2026-07-13","underlying":"SPX","trade_count":1,"realized_pnl":135.00,"max_loss_hit":false,"halted":false}` |
| `daily_bars` | `{"date":"2026-07-10","underlying":"SPX","open":6280.40,"high":6310.70,"low":6268.10,"close":6294.11,"volume":0}` |
| `tent_boundaries` | `{"ts":"2026-07-13T16:00:00Z","underlying":"SPX","lower_tent":6315.25,"upper_tent":6344.75}` |
| `monitoring_leg_quotes` | `{"ts":"2026-07-13T15:00:00Z","trade_id":101,"strike":6330.0,"option_type":"CALL","mark":11.30,"fly_mark":3.40,"drawdown_pct":0.1707}` |
| `broker_order_intents` | `{"id":501,"underlying":"SPX","trade_date":"2026-07-13","side":"ENTRY","status":"FILLED","broker_order_id":"<redacted>","order_spec":{"orderType":"NET_DEBIT"}}` |
| `bars_1m` (shared) | `{"ts":"2026-07-13T14:30:00Z","coin":"BTC","open":118000.0,"close":118050.0,"volume":12.4}` |
| `l2_book` (shared) | `{"ts":"2026-07-13T14:30:00Z","coin":"BTC","side":"B","level":0,"price":118049.0,"size":1.25}` |
| `trades` (shared) | `{"ts":"2026-07-13T14:30:01Z","coin":"BTC","price":118050.0,"size":0.05,"side":"B"}` |
| `polymarket_ohlcv` (shared) | `{"asset":"BTC","timeframe":"5m","market":"example-market","close":0.53,"volume":1000}` |
| `polymarket_trades` (shared) | `{"id":"example","strategy":"example","asset":"BTC","direction":"YES","entry_price":0.53,"pnl":2.10,"paper":true}` |
| `polymarket_trade_archive` (shared) | `{"id":"example","strategy":"example","fill_price":0.54,"settlement_status":"resolved","raw_json":{}}` |
| `strategies` (shared) | `{"name":"example-strategy","is_active":true}` |

## Repository and runtime inputs

| Source | Used by | Sample |
|---|---|---|
| `configs/config*.yaml` | Runtime strategy/execution/risk/collector/database settings | `strategy: {underlying: SPX, wing_widths: [10, 20, 30]}\nexecution: {paper_trading: true}` |
| `configs/equity_scan.yaml` | Morning equity scan settings and provider enablement | `news: {enabled: true, providers: [sec, alpha_vantage]}\nfilters: {min_price: 10.0}` |
| `configs/daily_report_card.yaml` | Daily report-card settings | `report_dir: reports/daily_report_cards` |
| `.env` and environment variables | Credentials, endpoints, feature flags, notification destinations | `SCHWAB_API_KEY=<redacted>\nALLOW_LIVE_TRADING=false` |
| `tokens.json` | Schwab OAuth client authentication | `<opaque secret OAuth JSON; intentionally not sampled>` |
| `configs/universes/{sp500,nq100,liquid,custom}.txt` | Equity scan symbol universes | `AAPL\nMSFT\nNVDA` |
| `configs/universes/sectors.json` | Equity scan sector enrichment | `{"AAPL":"Information Technology","JPM":"Financials"}` |
| `configs/universes/liquid_meta.json` | Liquid-universe quote/volume provenance | `{"AAPL":{"price":228.15,"avg_volume_20d":51230000.0,"exchange":"NASDAQ"}}` |
| `data/{spx,ndx,xsp,vix}_1min.csv` | Optional `CsvDataLoader` research input | `ts,open,high,low,close\n2026-07-13 09:30:00,6300.00,6304.25,6298.75,6302.50` |
| `data/schwab/YYYY-MM-DD.json` | Optional cached Schwab/yfinance backtest day | `{"date":"2026-07-13","vix":17.8,"prev_close":6294.11,"bars":[{"ts":"2026-07-13T13:30:00Z","close":6302.5}]}` |
| `data/chains/[UNDERLYING/]YYYY-MM-DD.json` | Local option-chain backtest cache | `{"date":"2026-07-13","snapshots":{"2026-07-13T14:30:00Z":{"spot":6312.42,"quotes":[{"strike":6315.0,"type":"CALL","mark":7.25}]}}}` |
| `data/results/*.csv` | Previously generated research results; not a runtime feed | `date,asset,wing_width,pnl\n2026-07-13,SPX,20,1.35` |
| `reports/**/*.json` and `reports/**/*.md` | Previously generated scan/broker/report artifacts; not a trading feed | `{"generated_at":"2026-07-13T13:00:00Z","scanned_symbols":2100}` |
| Python clock, `zoneinfo`, and repository market-holiday rules | Runtime session, early-close, and trading-day decisions | `{"session_date":"2026-07-13","market_open_et":"09:30","market_close_et":"16:00","is_trading_day":true}` |
| Local `/health` endpoints | `tools/health_monitor.py` only | `{"status":"ok"}` |
| Prometheus `/metrics` endpoints and structured container logs | Operations/observability, not trading decisions | `butterfly_schwab_api_calls_total{endpoint="get_quote"} 42` |

## Not data inputs

Discord, Telegram, generated HTML/PNG reports, and Grafana consume ButterflyGuy
data for notification or display; they are outputs, not inputs to strategy or
risk decisions. Test fixtures are also excluded because production code does not
read them.
