# XSP Flat-Runtime Restart Proof - 2026-07-14

## Scope

The owner approved the supervised post-close restart. Only `app_xsp` was
restarted. No broker-write command was run, and the running XSP configuration
remained `paper_trading=True`.

## Preconditions

- Market time was 16:11 EDT.
- `butterfly_trades` had zero `OPEN` rows.
- `broker_order_intents` had zero nonterminal rows.
- The redacted Schwab baseline had zero XSP orders and zero XSP option
  positions. See `broker_order_statuses_xsp_2026-07-14.json`.

## Restart and verification

- Restarted only `app_xsp`; the container restarted at
  `2026-07-14T20:39:44Z` with restart count `0`.
- `/health` returned `200` with service `XSP`.
- `/ready` returned `200` with no not-ready reason.
- `schema_migrations` contained all nine repository migrations through
  `009_broker_order_intents.sql`.
- Post-restart DB checks still had zero `OPEN` trades and zero nonterminal
  broker intents.
- The runtime's shared read-only XSP broker/DB reconciliation check passed
  after restart with no positions, unknown working orders, partial fills, or
  cancel-pending orders.
- Startup logs showed successful Schwab authentication and
  `market_closed_waiting`; the post-restart log scan found no error, exception,
  traceback, migration failure, unsafe reconciliation, unknown-order,
  partial-fill, cancel-pending, or restart-loop event.

Result: **PASS**.
