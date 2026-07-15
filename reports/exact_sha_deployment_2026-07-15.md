# Exact-SHA Deployment Proof - 2026-07-15

## Scope

The owner approved rebuilding and restarting all three paper-trading services.
The manual deployment workflow built and recreated SPX, NDX, and XSP from
commit `ce3b785c8736e1b1291bfcf595eb80c28ef13840`. No broker-write command was
run, and all three runtime configurations remained `paper_trading: true`.

## Preconditions and validation

- The local checkout was clean and matched `origin/main` at the deployed SHA.
- The full local suite passed: `421 passed, 1 skipped`; the skip requires the
  isolated CI TimescaleDB service.
- Push validation passed in workflow run `29450707863`.
- The real-Timescale migration and critical-query smoke test passed in workflow
  run `29450707723`.
- Manual deployment run `29450955030` passed the flat-runtime gate: zero open
  DB trades, zero nonterminal broker intents, no active or unknown relevant
  Schwab orders, and no SPX, NDX, or XSP broker-position mismatch.

## Deployment and verification

- The workflow verified the checked-out SHA, rebuilt `app_spx`, `app_ndx`, and
  `app_xsp`, and required `/ready` success on ports 8000, 8001, and 8003.
- All containers started at approximately `2026-07-15T21:12:52Z` with restart
  count `0`.
- Direct in-container `/health` checks returned `status: ok` for SPX, NDX, and
  XSP. Direct `/ready` checks returned `status: ready` with no reason.
- `schema_migrations` contained all nine repository migrations.
- Post-deployment DB checks still showed zero open trades and zero nonterminal
  intents.
- Latest stored chain snapshots were from the final market-hour collection:
  SPX `2026-07-15T19:59:17Z`, NDX `2026-07-15T19:59:34Z`, and XSP
  `2026-07-15T19:59:44Z`.
- Startup logs showed successful DB initialization, Schwab authentication,
  realized-PnL synchronization, collector startup, and the expected
  `market_closed_waiting` state. No startup error or restart loop appeared.

Deployment result: **PASS**.

The rollback half of the operational drill was not authorized or performed, so
the combined deployment-and-rollback task remains open.
