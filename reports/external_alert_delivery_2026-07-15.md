# Critical External-Alert Delivery Proof - 2026-07-15

## Scope

The owner approved a supervised external-delivery test after market close. The
test covered broker ambiguity, broker/database reconciliation failure,
settlement-evidence failure, and Schwab token expiry. All payloads were synthetic
and identifier-free. No broker write, database mutation, or app-service restart
was performed.

## Implementation reviewed

- The app posts fixed, redacted critical conditions to the shared Alertmanager.
- Stable labels include only the condition, underlying, project, notification
  route, severity, and derived alert name. Repeated processes and container
  restarts therefore share one server-side fingerprint.
- Broker ambiguity and settlement failures stop entry processing; reconciliation
  failures preserve degraded readiness; failed recovery notifications remain
  pending and retry on later healthy reconciliations.
- Token expiry uses the same central route. The keepalive still attempts its
  read-only quote refresh, but exits nonzero if alert delivery was not accepted.
- The shared Alertmanager runs non-root as `1001:1001` with supplemental group
  `65534`. UID `1001` owns and can read the mode-0600 webhook files; the
  supplemental group preserves write access to `/alertmanager` storage. Its
  readiness endpoint and loaded configuration passed.

## Supervised delivery and deduplication result

The baseline Discord notification counter was `5`; every Discord failure counter
was `0`. Each of the four production label fingerprints was submitted twice,
with annotations explicitly marked as a synthetic test. All eight Alertmanager
API calls returned HTTP 200.

After the configured 30-second group wait:

- the Discord notification counter was `9`, a delta of exactly four rather than
  eight;
- all Discord failure counters remained `0`;
- Alertmanager exposed one active fingerprint for each of the four conditions;
- a temporary exact-condition silence was installed, then all four fingerprints
  were resolved without generating recovery-message noise; and
- the active ButterflyGuy alert count returned to zero.

This proves Alertmanager API acceptance, central deduplication, and successful
Discord transport. It does not claim that a human visually acknowledged each
message in the Discord client.

Local verification after the final reviewer fixes: `434 passed, 1 skipped`;
targeted Ruff and both ButterflyGuy and monitoring Compose renders passed.

External alert-delivery and deduplication result: **PASS**.
