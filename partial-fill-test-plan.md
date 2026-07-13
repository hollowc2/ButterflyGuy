# XSP Partial-Fill Evidence Plan

## Purpose

Collect one real Schwab **supervised XSP live-canary** complex-order payload that shows a partial fill and the later terminal outcome. Repo paper mode simulates fills locally and cannot produce this broker evidence. This is an audit test, not a normal strategy trade.

## Current evidence

Trade 177 on 2026-07-13 has already captured:

* a durable entry intent and broker order ID;
* the raw Schwab parent-order payload;
* all three execution-leg prices and quantities;
* a clean `FILLED` entry; and
* live option-chain and position-monitoring records.

Allow its normal exit/settlement to complete. Save that exit payload before running any test order.

## Preconditions

1. Confirm no open XSP strategy trade, no working XSP order, and no XSP risk halt.
2. Complete all synthetic partial/cancel-pending tests before risking a broker order.
3. Confirm the XSP live-canary guards remain one contract per position and `$50` maximum daily loss. A quantity-two partial-fill test therefore requires a separate, explicit owner risk exception before changing or submitting anything.
4. Obtain explicit approval for the test order immediately before submission. Do not reuse a normal strategy entry or alter its exit.
5. Set `paper_trading: false` only for the approved supervised session, then restore `paper_trading: true` and verify the running service afterward.
6. Create a dated, redacted baseline status report:

   ```bash
   uv run python src/butterfly_guy/scripts/report_broker_order_statuses.py \
     --config configs/config_xsp.yaml --underlying XSP --date YYYY-MM-DD
   ```

## Controlled test

1. Use a valid same-day XSP butterfly with **quantity 2 or greater**. A one-lot parent order cannot be partially filled.
2. Submit it only as a separately labelled supervised live-canary test, with a non-marketable limit selected by the operator. Do not modify strategy defaults or risk limits without the explicit exception above.
3. Poll and save the broker payload while it is working. If `filledQuantity` is greater than zero and less than `quantity`, capture the parent payload and every child/leg payload immediately.
4. Cancel any unfilled remainder only after the partial state has been recorded. Then continue polling until Schwab reports a terminal state.
5. If the order fills completely before a partial state is observed, treat it as another clean-fill observation; do not chase a partial fill by repeatedly submitting orders.

## Stop rules

Stop and do not submit another test order if any of these occur:

* an unexpected XSP position or broker/DB mismatch;
* an unknown, missing, or conflicting parent/child status;
* a partial fill whose remaining quantity cannot be confirmed cancelled or filled;
* an application, broker-authentication, or data-freshness error; or
* normal strategy trading needs the XSP lane.

Leave the system fail-closed and investigate from saved records. Do not restart services or manually flatten solely to continue this test.

## Required artifacts

Keep raw broker payloads local under `reports/`; do not commit account identifiers, order IDs, symbols, or payloads containing sensitive data.

* pre-test and post-test redacted `report_broker_order_statuses.py` output;
* the durable `broker_order_intents` row before and after each observed transition;
* redacted raw parent payload, including `status`, `filledQuantity`, `remainingQuantity`, `orderActivityCollection`, and child-order states;
* matching `decision_log`, `butterfly_trades`, and `monitoring_leg_quotes` timestamps; and
* an audit note mapping each observed Schwab status to the runtime category (`working`, `partial`, `cancel_pending`, `filled`, or terminal).

## Done criteria

The partial-fill audit slice is complete when one observed payload proves:

1. a partial parent order (`0 < filledQuantity < quantity`);
2. the persisted intent and broker order ID match that payload;
3. all execution-leg quantities and prices are recorded;
4. the remaining quantity reaches a known terminal outcome; and
5. the runtime blocks further entry on any ambiguous state.

Clean entry/exit evidence may close the happy-path audit independently. Rejected, expired, and cancel-pending cases remain separate evidence targets; do not claim they are proven without observed payloads.
