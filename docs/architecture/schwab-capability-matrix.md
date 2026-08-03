# Schwab Capability Matrix

This matrix records repository evidence separately from real Schwab behavior. No live
capability probe was run during the foundation. `UNVERIFIED` does not mean unsupported.

Statuses: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `NOT_SUPPORTED`, `UNVERIFIED`, `ERROR`.

| Capability | Status | Repository evidence / required proof |
|---|---|---|
| OAuth request construction | PARTIALLY_SUPPORTED | `tools/auth_init.py` uses `easy_client`; callback lifecycle and revoked-token handling are not probed. |
| Single-symbol quote snapshot | PARTIALLY_SUPPORTED | Used throughout `SchwabClientWrapper`; extended-hours field semantics not proven. |
| Batched equity quotes | PARTIALLY_SUPPORTED | `get_equity_quotes()` requests QUOTE+EXTENDED in batches of 150; maximum/rate behavior unverified. |
| Quote bid/ask and sizes after close | UNVERIFIED | Capture snapshots before/after 1:00 PM Pacific. |
| Quote/trade timestamps | PARTIALLY_SUPPORTED | Scanner reads `tradeTime`; timestamp origin/meaning needs comparison to receive time. |
| Extended-hours last/mark/volume | UNVERIFIED | Scanner consumes `extended`; cumulative versus session volume is not established. |
| Intraday one-minute history | PARTIALLY_SUPPORTED | Multiple callers parse candles. Coverage and truncation require capture. |
| Extended-hours bars in history | UNVERIFIED | `get_intraday_bars_for_day(..., include_extended_hours=True)` sends the flag; content unverified. |
| Regular-session final bar | PARTIALLY_SUPPORTED | Candidate session-close logic expects 15:59 ET evidence; verify early-close and late availability. |
| Option chains and Greeks | SUPPORTED | Current SPX/NDX/XSP runtime and tests parse expected response shapes; limits/freshness still operational concerns. |
| Market hours endpoint | UNVERIFIED | No current wrapper method. |
| Instrument/exchange/status metadata | UNVERIFIED | Needed for AfterHoursLab contract. |
| EXTO/24x5 eligibility metadata | UNVERIFIED | Must not be inferred from symbol or quote presence. |
| Level I equity stream | PARTIALLY_SUPPORTED | Recorder subscribes and archives messages; reconnect/staleness not tested. |
| Chart equity stream | PARTIALLY_SUPPORTED | Recorder subscribes; extended-hours content needs capture. |
| NYSE/Nasdaq Level II | PARTIALLY_SUPPORTED | Recorder has subscriptions; entitlement, field quality, and limits unverified. |
| Stream reconnect/resubscribe | NOT_SUPPORTED | Current recorder exits on stream failure. Target behavior not implemented. |
| Shared subscription union | NOT_SUPPORTED | No broker/reference counting exists. |
| Practical subscription maximum | UNVERIFIED | Probe incrementally without affecting production stream. |
| Account-number/hash lookup | SUPPORTED | Required during wrapper initialization; sensitive and not suitable for scanner clients. |
| Account/position/order reads | SUPPORTED | Current live reconciliation/report paths use them. Gateway mediation not implemented. |
| Order submit idempotency | UNVERIFIED | Current safety policy assumes it cannot be proven and never retries submit. Preserve this. |

## Capability recorder design

Run only after explicit operational approval and after the gateway is the sole token/stream
owner. Proposed window: 12:45 PM–2:45 PM `America/Los_Angeles` on a normal trading day.
Sandbox data may validate request/parsing/auth mechanics only, never behavior or liquidity.

### Schedule

- 12:45–12:59: establish auth/REST/stream health; baseline quote/history/instrument samples.
- 12:59–1:05: high-frequency snapshot and stream capture across regular close.
- 1:05–2:30: after-hours snapshots, history probes, promoted-stream symbols, reconnect drill.
- 2:30–2:45: controlled subscription-size steps, final health, archive/manifest validation.

Use a small, predeclared mix of liquid/illiquid and venue-diverse equities. Do not hardcode
account IDs or option symbols. Do not submit, preview, replace, or cancel orders.

### Evidence per observation

- request ID and internal caller ID;
- symbol, requested fields/session flags;
- provider event/quote/trade timestamp where present;
- gateway receive time and recorder write time;
- bid, ask, sizes, last, last size, mark, volume;
- session/trading status/instrument/EXTO fields where present;
- HTTP status, normalized error, latency, retry count, cache result;
- raw redacted response/message hash and archive location.

The raw archive is local and ignored by Git. Before writing, recursively redact OAuth
fields, API keys, account numbers/hashes, streamer credentials, cookies, authorization
headers, and webhook URLs. Write atomically, mode `0600`, with a manifest containing schema
version, recorder version/SHA, start/end times, counts, drops, and redaction version.

### Probes

1. Quote snapshots before close, 1:00–1:05, and after 1:05 Pacific.
2. Compare quote/trade/provider timestamps to gateway receive timestamps.
3. Compare cumulative volume changes to any extended/session-specific field.
4. Request one-minute history with extended-hours true/false and diff bar timestamps.
5. Record Level I, chart equity, and entitled Level II services.
6. Disconnect the test stream once; measure reconnect, resubscribe, gap, and stale signal.
7. Increase subscription count in conservative predeclared steps; stop on first error,
   latency/staleness breach, or production impact.
8. Capture instrument/trading-status/EXTO metadata without interpreting undocumented fields.

### Output

Generate:

- this human-reviewed document;
- ignored `artifacts/schwab-capability-matrix.json` containing structured results;
- redacted raw archive and manifest.

Each result contains capability ID, status, evidence timestamps, request parameters,
observations, assumptions, error category, artifact hashes, and reviewer note. A capability
becomes `SUPPORTED` only with reproducible real evidence; ambiguous or inconsistent behavior
is `PARTIALLY_SUPPORTED`, and probe failures are `ERROR`, not `NOT_SUPPORTED`.

## Stop conditions

Stop immediately on auth/token anomaly, production quote degradation, rate limiting that
does not clear within the declared budget, unexpected account data in a market response,
redaction failure, archive permission failure, stream conflict, or any order-capable call.
