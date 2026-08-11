# Current Schwab Integration

> **Historical baseline — 2026-08-03:** This document records the direct-only integration that
> existed before the read-only gateway deployment. It is not a current topology reference. As of
> 2026-08-10, the gateway runs on Helios with bounded quote, spot, and chain reads, but direct
> Schwab access remains authoritative for every trading decision and all account/order work. XSP's
> shadow canary is installed and default-off. For the current deployment boundary, see
> `schwab-gateway-option-a-deployment.md` and `schwab-gateway-c3-shadow-wiring-plan.md`.
>
> The baseline was verified against commit `de84d91` on 2026-08-03. Statements labelled
> **Assumption** require runtime or Schwab verification.

## Current architecture

```text
                               Schwab Trader API
                                       |
                 +---------------------+---------------------+
                 |                     |                     |
        app_spx / app_ndx /     candidate feed and     host utilities,
        app_xsp (one SDK         candidate read-only    recorder, scans,
        client per process)      SDK client             reports, backtests
                 |                     |                     |
       +---------+----------+          |                     |
       | market/account/    |    candidate HTTP feed         |
       | order operations   |          |                     |
       +---------+----------+    paper evaluators            |
                 |
         TimescaleDB + local cache
                 |
       Prometheus / Grafana / Discord / Telegram

All of the above reuse one app identity and one host token file. There is no shared
OAuth owner, REST gateway, rate-limit coordinator, or shared streaming broker.
```

The primary runtime is `butterfly_guy.scripts.run_live.main()`
(`src/butterfly_guy/scripts/run_live.py:708`). It constructs one concrete
`SchwabClientWrapper`, then injects that same object into `OrderManager`, `TradeService`,
`PositionService`, and `OptionChainCollector` (`run_live.py:739-847`). SPX, NDX, and XSP
containers each repeat this construction.

## Direct SDK construction and imports

Verified direct client-construction locations:

| Location | Owner | Behavior |
|---|---|---|
| `src/butterfly_guy/data/schwab_client.py:27` | `SchwabClientWrapper` | Async `client_from_token_file`; resolves configured account hash on every initialization. |
| `src/butterfly_guy/candidate_fleet/schwab_market_data.py:20` | `ReadOnlySchwabMarketDataClient` | Async `client_from_access_functions`; reads token file once, retains refreshes only in memory, and omits account/order methods. |
| `src/butterfly_guy/backtest/schwab_loader.py:34` | `SchwabDataLoader` | Lazily constructs a separate async token-file client for research history. |
| `tools/schwab_token_keepalive.py:96` | keepalive cron | Constructs a synchronous token-file client and gets an SPX quote to force refresh. |
| `tools/auth_init.py:1` | manual OAuth bootstrap | Calls `easy_client` with callback `https://127.0.0.1:8182`. |
| `src/butterfly_guy/scripts/record_equity_market_data.py:90` | stream recorder | Builds `StreamClient` from the wrapper's raw SDK client and configured account ID. |

`SchwabClientWrapper` is constructed by `run_live.py`, `run_collector.py`,
`backfill_equity_candles.py`, `refresh_equity_universes.py`, `run_morning_scan.py`,
`record_equity_market_data.py`, `report_broker_order_statuses.py`, and
`tools/send_daily_report_card.py`. `run_candidate_feed.py` and
`download_schwab_cache.py` construct the other two client types.

## Authentication and token lifecycle

1. `load_config()` reads YAML, calls `load_dotenv()`, and merges
   `SCHWAB_API_KEY`, `SCHWAB_SECRET_KEY`, `SCHWAB_ACCOUNT_ID`, and optional
   `SCHWAB_TOKEN_PATH` into `SchwabSettings` (`core/config.py:218-250`).
2. `SchwabClientWrapper.initialize()` passes the token path and credentials to
   `schwab.auth.client_from_token_file` (`data/schwab_client.py:35-45`). Token refresh
   and persistence are delegated to `schwab-py`.
3. Initialization calls `get_account_numbers()` directly, outside `_retry`, requires an
   explicit configured account number, and retains its hash (`schwab_client.py:47-65`).
4. `tools/schwab_token_keepalive.py` assumes a seven-day refresh-token lifetime based on
   `creation_timestamp`, alerts within eight hours, and makes an hourly quote request
   (`tools/schwab_token_keepalive.py:29-114`).
5. Manual reauthorization overwrites `tokens.json` via `tools/auth_init.py`.

There is no repository-owned token lock, cross-process refresh coordinator, atomic token
store, permissions check, corruption recovery, auth-health model, or invalid-refresh-token
classification. `SchwabSettings.max_token_age` is configured but not enforced.

The candidate feed intentionally keeps any refreshed access token only in memory
(`candidate_fleet/schwab_market_data.py:41-48`), verified by
`tests/test_candidate_schwab_market_data.py:16`. This avoids a second file writer but still
creates a separate refresh actor whose state disappears on restart.

### Shared-token risk

`infra/docker-compose.yml` mounts the same host `tokens.json` writable into SPX, NDX, and
XSP (`:12-16`, `:82-86`, `:117-121`). Host utilities and keepalive also use it. These
processes can refresh concurrently and overwrite each other's state. A read-only mount is
not sufficient: a process may obtain a different access token in memory, lose it on
restart, and cannot persist rotation safely. Sharing a file also distributes application
credentials, account identity, and SDK capability instead of enforcing consumer
permissions.

## Market-data flow

### Primary options runtime

`OptionChainCollector.run_loop()` (`data/collector.py:190`) checks the local market clock,
then calls:

- `get_daily_bars()` for the underlying and SPX-only VIX once per calendar day;
- `get_spot_price()` for the underlying and SPX-only VIX;
- `get_option_chain()` for the current 0-DTE expiration.

`OptionChainCollector._parse_chain_response()` (`collector.py:48`) flattens Schwab's
`callExpDateMap`/`putExpDateMap` into DB rows. `ChainQueries`, `SpotQueries`, and
`DailyBarQueries` write TimescaleDB; `save_snapshot()` also writes a local JSON cache.

`TradeService.attempt_entry()` (`services/trade_service.py:172`) independently requests
spot, intraday bars, and a fresh chain for every price-ladder step (`:221-247`, `:352-370`).
It transforms the raw chain again in `_parse_chain_to_quotes()` (`:956`).

`PositionService.monitor_loop()` requests a full chain every two seconds and extracts only
the three legs (`services/position_service.py:266-316`, `_extract_quotes()` at `:919`).
`OrderManager._fetch_live_spread()` repeats raw-chain traversal for paper and live
repricing (`execution/order_manager.py:254-307`).

### Equity and research paths

`get_equity_quotes()` batches up to 150 symbols and requests SDK `QUOTE` and `EXTENDED`
fields (`data/schwab_client.py:238-270`). `run_morning_scan.py:118` and
`refresh_equity_universes.py:44` consume raw symbol-keyed dictionaries. Scanner-specific
normalization lives in `equity_scan/scanner.py:152`.

Price history is used by live entry/session-open/bias logic, settlement, charts, equity
backfill, average-volume scans, daily reports, and `SchwabDataLoader`. No response cache or
request coalescing exists at the shared-app level.

## Order and account flow

The current client combines market data, accounts, and write capability:

- account numbers/hash: `SchwabClientWrapper.initialize()`;
- account snapshots/positions/balances: `schwab_client.py:336-372`;
- day orders and transactions: `schwab_client.py:293-334`;
- order submit/status/cancel: `schwab_client.py:132-178`.

`ButterflyOrderBuilder` creates Schwab-native dictionaries
(`execution/order_builder.py:13`). `OrderManager.execute_single_attempt()` creates a
durable `broker_order_intent` before a live submit, persists the returned broker ID, polls
status, cancels if needed, and reconciles post-cancel state
(`execution/order_manager.py:399-504`). `place_order()` deliberately submits exactly once
and refuses to retry a response missing `Location` (`data/schwab_client.py:132-155`).

Live startup and the 15-second broker reconciliation loop compare DB trades/intents with
broker positions, orders, and transactions (`run_live.py:287-510`, `:859-878`). Unknown,
partial, or ambiguous states fail closed and gate new entries. These are high-value safety
mechanisms that must be preserved when account and order mediation is eventually moved.

No order endpoint is part of the foundation gateway. Direct order ownership remains the
rollback path until a separately authorized Phase 6.

## Streaming flow

Streaming is not part of `run_live`. `record_equity_market_data.py` is a standalone,
single-symbol recorder. It logs in once, subscribes to chart equity, Level I, and optional
NYSE/Nasdaq books, and loops over `handle_message()` (`:67-145`).

`JsonlStreamRecorder` places raw messages into a bounded nonblocking queue and writes one
JSONL file per service with a receive timestamp (`data/equity_market_data.py:54-147`). It
counts drops and writes a manifest. There is no reconnect, resubscribe, stale-stream
detector, subscription union, consumer tracking, event bus, or stream health endpoint.
The recorder logs out but does not close its `SchwabClientWrapper`.

## Retry and failure behavior

`SchwabClientWrapper._retry()` (`data/schwab_client.py:81-104`) makes three attempts with
1/2/4-second backoff. It retries 429 and every caught exception, including non-retryable
4xx/auth failures, does not honor `Retry-After`, and has no circuit breaker, cache,
deduplication, or explicit wrapper timeout. JSON parsing occurs after `_retry`.

- Authentication failure during initialization aborts startup.
- A runtime 401 becomes a generic retry-exhausted `RuntimeError`; no manual-reauth state is
  exposed.
- Three pure 429 responses can report `last_err=None`.
- Collector failures are logged and notified after three consecutive attempts.
- Entry market-data failure skips or ends the attempt.
- Position market-data failures are logged and retried on the next two-second poll.
- Reconciliation failure blocks live entries while keeping liveness up.
- Order submission is not retried; ambiguous state requires reconciliation.

## Models and SDK coupling

Strategy algorithms mostly consume `OptionQuote`, `ButterflyCandidate`, and `TradeRecord`,
not SDK classes. Coupling is concentrated in orchestration/data/execution:

- constructors type directly against `SchwabClientWrapper` in collector, trade service,
  position service, and order manager;
- raw Schwab dictionaries escape the wrapper for chains, bars, quotes, accounts, orders,
  and transactions;
- chain normalization is duplicated in collector, trade, position, candidate feed,
  order repricing, and DB replay;
- `OptionQuote` (`data/schemas.py:11`) has no event/receive timestamps, source, staleness,
  or quality flags and frequently represents missing fields as numeric zero.

The duplicate parsers are behaviorally different. They must not be consolidated during
the foundation without golden parity data because changing missing-value treatment could
change strategy decisions.

## Configuration, secrets, and deployment assumptions

- YAML under `configs/` contains token paths and behavior, while credentials/account ID
  come from `.env` or environment.
- `.env`, token JSON, `secrets/`, captures, logs, and generated runtime are ignored by Git.
- There is no `.dockerignore`; repository-root build contexts can transmit ignored local
  secrets/data to the Docker daemon, although current Dockerfiles copy only explicit files.
- Primary containers run non-root with read-only root filesystems, dropped capabilities,
  `no-new-privileges`, and loopback-only metrics ports. Preserve these controls.
- The Compose file expects an external `monitoring_net` with TimescaleDB and Alertmanager;
  it does not create those services.
- Production automation assumes a self-hosted runner and `/opt/butterflyguy`. Manual
  deployment checks DB/broker flatness, fast-forwards an exact SHA, rebuilds the three app
  containers, and polls `/ready` (`.github/workflows/deploy.yml`).
- Paper mode is the checked-in default. The app still initializes an account-capable
  client and resolves an account hash in paper mode.

## Database and messaging dependencies

TimescaleDB/PostgreSQL is the durable source for chains, spot, daily bars, trades, risk,
decision logs, order intents, monitoring legs, and candidate archives. The shared candidate
feed already uses aiohttp request/response plus an in-memory condition and Timescale archive.

No Redis, NATS, ZeroMQ, PostgreSQL `LISTEN/NOTIFY`, or internal WebSocket event bus is used.
REST-first and deferring an event bus is therefore the lowest-operational-risk foundation.

## Discord and operational dependencies

`DiscordNotifier` posts trading/scanner/report output directly through webhooks
(`services/notifier.py:70`). Telegram and Alertmanager cover other warnings. Discord is not
a source of truth, but there is no DB/event-backed Discord bot today. Raw exception strings
can reach logs or notification messages; logging has no central redaction processor.

The gateway foundation does not change Discord. The future bot must receive normalized
scanner events and must never receive Schwab credentials.

## Reusable components

- Candidate `MarketDataProvider`, `HttpMarketDataProvider`, freshness models, atomic store,
  HTTP health/readiness/metrics, and fake-heavy tests.
- `ReadOnlySchwabMarketDataClient` as evidence that account/order-free SDK use is possible;
  its token ownership is not the target design.
- `iter_chain_options()` for raw-chain traversal.
- `OptionQuote` and current parsers as compatibility models during strangling.
- `DatabasePool`, Timescale schema patterns, Prometheus stack, and structured logging.
- `JsonlStreamRecorder` envelope/queue/drop accounting after redaction and reconnect work.
- Order intents, fill validation, ambiguity errors, broker reconciliation, and no-submit-
  retry invariant.

## Extraction boundaries

Extract to the gateway over time:

- client construction, OAuth callback, token store/locking/health;
- Schwab REST retry/rate/cache/error policy;
- streaming connection and subscription ownership;
- raw market-data recording and upstream audit fields;
- account mapping and account/order mediation;
- caller identity, capability checks, and gateway audit logging.

Remain ButterflyGuy-specific:

- 0-DTE expiration/entry schedule and direction filters;
- VIX anchoring, butterfly construction/selection, paper mark convention;
- risk rules, profit state machine, position valuation, settlement policy;
- ButterflyGuy DB trade lifecycle, selection parity, charts, and notifications.

## Security review

Verified concerns:

1. Multiple writable token-file consumers and independent refresh actors.
2. Full `.env` and account-capable client reach read-only services unnecessarily.
3. No central secret/error redaction; raw exceptions may reach logs or Discord.
4. Candidate feed HTTP routes are unauthenticated on a shared Docker network.
5. Optional daily report raw dumps can contain complete account/order/transaction payloads.
6. No `.dockerignore`; base Python and `uv:latest` images are not digest-pinned.

A safe local filename/pattern history review found no tracked `.env`, token JSON, private
key, or obvious hard-coded credential. Secret values were never read or printed. This was
not a forensic scan because `gitleaks` is unavailable.

## Assumptions requiring verification

- **Assumption:** Schwab refresh-token lifetime and rotation semantics match the keepalive
  script's seven-day interpretation.
- **Assumption:** one upstream stream can support the planned union and practical symbol
  counts; no limit is encoded in this repository.
- **Assumption:** extended-hours history/session/EXTO fields behave as anticipated. The
  current code requests extended hours but does not establish a capability matrix.
- **Assumption:** the eventual host/private-network topology is Helios/Eros/Zeus as proposed;
  the repository only verifies `/opt/butterflyguy` and `monitoring_net`.
