# XSP Opportunistic Partial-Fill Evidence Plan

## Decision

A real Schwab complex-order partial fill cannot be produced deterministically
without adding unnecessary live risk. Changing quantity, repeatedly submitting
orders, or manipulating limits solely to manufacture that state is prohibited.

Synthetic parent/child partial-fill and cancel-pending coverage is the pre-live
safety evidence: the runtime persists the broker state, stops further entry,
degrades readiness, and requires manual reconciliation. A real broker payload is
useful opportunistic evidence, not a prerequisite for the supervised one-lot XSP
canary or manual-flatten rehearsal.

## Current evidence

Trade 177 captured a durable broker intent, raw parent payload, all execution-leg
prices and quantities, a clean `FILLED` entry, monitoring records, and cash
settlement evidence. Focused synthetic tests cover partial-fill, cancel-pending,
missing, unknown, and contradictory parent/child states and fail closed.

No real partial-fill or cancel-pending Schwab payload has been observed. Do not
claim otherwise.

## If one occurs naturally

1. Stop new entry and maintain direct Schwab supervision.
2. Save the broker payload before taking action. Keep raw payloads local and
   redact account identifiers, order IDs, and full option symbols from retained
   summaries.
3. Confirm `filledQuantity`, `remainingQuantity`, every child status, and the
   exact broker position independently of the database.
4. Cancel a confirmed unfilled remainder only with explicit operator approval,
   then poll until every parent and child reaches a known terminal state.
5. Do not restart, resubmit, or manually flatten until the exact filled position
   and remaining order state are known.
6. Reconcile `broker_order_intents`, `butterfly_trades`, `decision_log`, and
   `monitoring_leg_quotes` without editing the database to force agreement.

## Required artifacts

- Pre-event and post-event redacted broker-status reports.
- The durable intent row before and after each observed transition.
- A redacted parent/child summary containing statuses and filled/remaining
  quantities.
- An audit note mapping observed Schwab statuses to `working`, `partial`,
  `cancel_pending`, `filled`, or terminal runtime categories.

## Completion

Opportunistic evidence is complete only when an observed payload proves a real
partial or cancel-pending state, matches the persisted intent, reaches a verified
terminal remainder, and demonstrates that further entry stayed blocked.

Until then, record this item as unobserved but nonblocking. Never manufacture it.
