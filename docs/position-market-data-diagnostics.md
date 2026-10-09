# Held-position market-data diagnostics

The October 7, 2026 XSP trade 334 and NDX trade 333 incidents showed missing held
legs in the usable chain. Rejected-leg timestamps were not retained, so those
records cannot prove whether Schwab omitted the legs or the gateway classified
their quotes as stale. This change collects that evidence before changing any
valuation or exit policy.

## Behavior

- The position monitor uses the same chain and filtering policy for valuation.
  Failure and recovery events now include the outage duration. Failures retain
  each held leg's symbol, strike, rejection reason, bid/ask/mark, quote timestamp,
  age and quality flags, plus the chain's gateway receipt time.
- The alert identifies the underlying and affected strikes and states that
  valuation-dependent exits are suspended. Prolonged outages generate a reminder
  after 60 seconds, at 300 seconds, and every 300 seconds thereafter. Reminders
  report the total valuation outage duration, current blocking legs and latest
  targeted recovery result (or that recovery is disabled). Missed reminder
  intervals do not generate a burst of alerts. Reminder DB writes and each
  notification have a three-second timeout; failures do not stop monitoring.
  Recovery reports the outage duration and resets the reminder schedule.
  Recovery means usable valuation returned; it does not mean the position closed.
- XSP/NDX enable `collector.record_timing`, using the existing migration 011
  columns and `chain_snapshot_meta`. Rejected-contract metadata also retains
  prices and the event timestamp. Raw historical snapshots are unchanged.
- XSP/NDX enable `position_data.shadow_held_quotes`. Every 60 seconds, at most
  one background sample requests the three recorded option symbols through
  `/v1/quotes?allow_partial=true`. Both the quote request and the evidence write
  time out after 3 seconds. Shadow reads have no retries and do not change
  readiness. The task is cancelled when monitoring ends or is cancelled.
- The `position_held_quote_shadow` event is written to structured logs and the
  existing `decision_log`. It includes chain and targeted leg evidence,
  separately timestamped observations, source usability, and comparable fly
  marks when all three quotes are usable. The marks are observational, not
  synchronized execution prices. Shadow results never update valuation, peaks,
  signals or orders, including when the chain is unavailable.
- Default configs keep the sampler disabled; direct-market-data mode does not
  run it. No entry/risk parameters or paper/live settings are changed.

The gateway accepts strictly padded 21-character OCC option symbols on the
quote route only. It preserves the spaces when forwarding the request to
Schwab. Targeted option quotes use the option-contract 300-second freshness
policy and quote timestamps, not a newer last trade; successful retrieval never
renews their timestamp. Equity quote freshness and other routes are unchanged.
ButterflyGuy pins SDK 0.8.0 for the partial-quote response and missing-symbol list.

## Deployment and verification

Prepare and review the gateway and consumer changes together. Deployment requires
the existing live deployment approval and rollback procedure. Deploy the gateway
option-symbol support before enabling consumer shadow sampling. Confirm migration
011 exists in the consumer DB before enabling timing capture. An older gateway
may reject option symbols; that is recorded as a shadow request failure without
changing trading decisions.

Collect at least three complete paper sessions, extending the window until a
quiet/stale held-leg event is observed. Review:

```sql
SELECT ts, underlying, event_type, data
FROM decision_log
WHERE ts >= CURRENT_DATE
  AND event_type IN ('position_held_quote_shadow',
                     'position_market_data_unavailable',
                     'position_market_data_recovered',
                     'position_market_data_outage_prolonged')
ORDER BY ts;
```

Compare which endpoint omitted each contract, quote ages and timestamps, request
failures, stale periods, and mark differences. A fresh response with an old
contract timestamp remains stale. A newer last trade is not proof of a current
bid/ask. Do not infer avoided losses from this observational evidence.

The follow-up decision is whether targeted quotes supply better validated held-leg
coverage. Activating them for valuation, defining prolonged-outage escalation,
and separating time-based exit intent from price-dependent decisions are later
behavioral changes that need dedicated tests and review. This stage does not
relax freshness, fabricate missing-leg values, or alter the cash-settlement path.

## October 9 coverage investigation

Trade 341 held the XSP 780/784/788 call butterfly. Its three valuation outages
lasted 304.2, 88.5 and 157.9 seconds. During each, both chain and targeted quote
responses retained the same old 788 quote timestamp, with bid 0 and ask 0.01;
the other held legs continued updating. All 18 targeted recovery attempts were
rejected as unusable. The trade subsequently closed at 17:19:08 UTC through the
existing drawdown exit. This evidence does not establish the upstream reason
for the unchanged timestamps or prove an exit was missed.

The current gateway/consumer implementation has no level-one option streaming
path. Schwab-py's [streaming documentation](https://schwab-py.readthedocs.io/en/latest/streaming.html)
supports `level_one_option_subs`, option bid/ask fields and `QUOTE_TIME_MILLIS`.
This makes streaming a candidate for a shadow coverage comparison, not a proven
solution: another response carrying the same old quote time remains stale.

A gateway-owned shadow capture should subscribe to the three exact held symbols
and compare timestamp age, complete usable bid/ask coverage and outage duration
against both existing REST paths. Preserve per-symbol timestamps across partial
stream updates and reconnects; receipt time or another contract's update must
never renew a leg's quote time. First check the gateway's existing stream-session
ownership to avoid disrupting its active equity/order-book subscriptions. No
new stream connection, production subscription or valuation source is activated
by this consumer alert change.
