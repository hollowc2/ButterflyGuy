# Supervised SPX live test — October 29, 2026

Authorization: Corey requested the live path, recording, supervised test and paper restoration,
and selected October 29. Existing paper position 377 was OPEN during preparation on October 28;
no running service may be replaced until it is closed and the broker/DB checks pass.

## Scope

Only `butterfly_spx_app` changes. Direct Schwab market data and existing direct broker routing;
no gateway live-policy bypass, duplicate bot, changed strategy exits or extended entry window.
One fly, one trade on the dated session, existing width-specific caps plus a hard 4.00 debit
ceiling ($400 plus fees). Existing account allocation and $500 daily-loss confirmation remain.
The debit is the position's defined premium risk; the daily-loss guard is not a guaranteed stop.
No valid fresh candidate means no trade. Normal strategy exits may instead lead to expiration;
settlement cannot validate an exchange closing fill.

The dated entry guard prevents new entries on subsequent dates even if restoration is delayed.
It does not stop monitoring a held position. The test overlay disables automatic container restarts;
a failure requires supervised broker reconciliation before any restart. Do not leave it unattended.

## Manual close override

Bot exit rules run normally. Corey may close the fly in Schwab/ToS at any time; the bot then
hands that trade's exit to him for good and never fights it.

- Close it as **one butterfly order** (all three legs, closing instructions), e.g. right-click the
  position, "Create closing order". Legging out leaves the bot unable to price the close; it
  alerts and the DB row must be closed by hand.
- If a bot exit order is already working, cancel or edit *that* order in ToS (edit = replace).
  The bot treats a cancel/replace it did not make as a handoff and does not resubmit. Sending a
  second, separate closing order while the bot's is working is the one race to avoid.
- Handoff triggers: any working order on the fly's legs that the bot did not place, a leg change,
  or a cancel/replace of the bot's exit order. Before every exit-ladder step the bot re-checks
  holdings and working orders, so it never submits against a close you started.
- After handoff it keeps valuing the fly, logs/posts its first exit signal
  (`manual_exit_signal_suppressed`) for comparison, and every ~10 s checks the account. Once all
  three legs are flat it reads the single FILLED closing fly order and records `manual_close` at
  the broker fill. Handoff is permanent for that trade, even if you cancel your order; an
  unclosed fly is then cash-settled.
- The reconciler leaves a working, edited or filled close of the monitored trade's own legs to
  the monitor; any other unknown SPX order or leg mismatch still blocks trading and alerts.
- If it cannot resolve the close (no single matching filled order, legs partly closed), it
  alerts once and marks `/ready` `manual_close_unresolved`. It still sends no orders.

## Recording and checks

- Selection context is retained in trade metadata and each order has a durable intent.
- Each submission/reprice records per-leg bid/ask, mark, calculated midpoint and provider quote
  timestamp, plus local request/response times, limit, and paper cost assumptions in the intent.
- Quote timestamps must be present, finite, nonfuture and no older than 10 seconds on each leg.
  A stale distant wing can legitimately prevent entry or exit. Missing exit quotes raise the existing
  reconciliation stop; the operator must then supervise and, if needed, close in Schwab.
- Broker acknowledgement and fill detection have local timestamps. Fill detection fetches a new
  quote with a three-second timeout. Such quotes follow execution; they are not execution-time NBBO.
- A pre-submit audit persistence failure prevents submission. A post-fill recording failure is logged
  without converting the confirmed fill to an unknown order outcome. Broker fills remain in intents.
- Broker status payloads retain actual executions; the read-only exporter retrieves fees and cash flows.
  No exact exchange order-book or subsecond wire latency claim is supported.

Verify full pytest, full Ruff, Compose rendering and CI's real TimescaleDB smoke test on the release.
Use the clean pilot branch/snapshot: unrelated workspace changes are excluded. No DB migration is
needed for this change; observations append to existing JSONB intent snapshots.

## Activation and rollback

1. Before the configured October 29 entry window, Corey must be present in Schwab. Confirm
   no open DB trades, no active intents, no in-memory monitors, broker flatness, current token
   access, sufficient buying power and only one intended live service. Use the existing
   `tools/deploy_broker_flat_check.py` read-only check. Preserve account identifiers privately.
2. Pin the tested release by immutable image ID. Record the current SPX image ID and the complete
   original Compose file list, environment-file paths and project name. Prepare an SPX-only image
   rollback override pinning that exact original ID. Never print resolved Compose secrets.
3. Render the original Compose files plus `infra/docker-compose.spx-live-test.yml` LAST, with
   `SPX_LIVE_TEST_IMAGE` set to the tested image and `SPX_LIVE_TEST_DATE=2026-10-29`.
   The overlay changes only SPX, supplies existing account confirmation from its configured account,
   and applies live/recording/date/size guards. It contains no credentials.
4. Recreate only `app_spx` using `up -d --no-deps --no-build --pull never app_spx`.
   Verify its image, direct data mode, live settings/date, single-instance status, health/readiness,
   account reconciliation and logs before the entry window. Never clear today's risk count or
   paper trade history to force an entry.
5. Observe entry and management in Schwab. On partial/unknown/cancel-pending state, stale data,
   reconciliation failure or lost supervision, block entries and follow `docs/live-runbook.md`.
   Stop/restart is not a substitute for checking broker positions and working orders.
6. After the trade closes, export evidence with the read-only tool below. Confirm all legs are flat
   and all orders terminal. Restore the original Compose configuration and pinned SPX image with
   `up -d --no-deps --no-build --pull never app_spx`; confirm paper mode and reconciliation.
   If activation fails, use the same rollback immediately, while retaining manual broker supervision.

The original running SPX image observed October 28 was
`sha256:4771356b52d76788c1e5766b54c6a146ab5600d1e5eac7c2c04c2c98199cad0d`.
Original Compose project: `infra`; files:
`/opt/butterflyguy/infra/docker-compose.yml` and
`/opt/butterflyguy/.rollbacks/schwab-recording-fidelity-20261004/release-image.yml`.
Recheck these immediately before activation; this record is not a reason to overwrite a newer release.

## Evidence export and comparison

Run in the SPX container's authenticated environment; it performs only broker GETs and read-only DB
queries. The output directory must be new. Copy its contents off the container before paper restore:

```bash
docker exec -i butterfly_spx_app python - --date 2026-10-29 \
  --out-dir /tmp/spx-live-test-20261029-evidence < tools/report_spx_live_test.py
```

Use `docker cp` to preserve the output in a new host evidence directory. Re-export after next-day
settlement when applicable. The exporter redacts account/order identifiers and writes a hash manifest.
It includes all SPX orders on that session: distinguish any manual orders from bot intents.

Reconcile signed leg quantities, broker cash flows and fees. Compare actual net debit/credit with
pre-submit midpoint and natural leg market, actual fill timestamps with local submission/acknowledgement,
and identical-strike paper calculations including costs and rounding. Report quote ages explicitly.
If post-fill quotes are absent or stale, retain that gap rather than substituting hindsight prices.
Finish with paper-mode restoration proof. One trade is execution evidence, not strategy validation.
