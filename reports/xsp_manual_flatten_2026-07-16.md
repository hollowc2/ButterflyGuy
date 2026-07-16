# XSP Manual-Flatten Evidence - 2026-07-16

## Result

The supervised broker-action portion passed. The operator closed the exact
one-contract XSP butterfly as one complex order. Schwab reported the order
`FILLED`, all three legs became flat, and no working XSP order remained.

Post-action application reconciliation is intentionally still pending. The
manual broker order had no bot-owned EXIT intent, so the runtime did not guess
at an exit transition: it retained trade `182` as OPEN, left realized P&L
unchanged, degraded `/ready`, and emitted the reconciliation-failure alert.

## Redacted evidence

- Entry: trade `182`, XSP 744/748/752 PUT butterfly, quantity one.
- Entry fill: `$0.33` net debit at `2026-07-16T14:00:32Z`.
- Before the close, broker legs matched the DB ratio `+1/-2/+1`; the only
  relevant broker order was the filled entry and no exit order was working.
- Operator close: one XSP butterfly, quantity one, `$0.07` net credit,
  `FILLED` at `2026-07-16T16:01:37Z`, zero remaining quantity.
- After the close, Schwab returned zero XSP option positions and both relevant
  same-day complex orders were terminal `FILLED`.
- The redacted generated status artifact is
  `reports/broker_order_statuses_xsp_2026-07-16.json`; it contains no account or
  order identifiers and no full option symbols.

Gross spread P&L is `-$0.26`, or `-$26` for one contract before fees.

## Fail-closed proof

At `2026-07-16T16:01:52Z`, the live reconciler detected that Schwab was flat
while the DB retained one OPEN XSP trade. It emitted the critical reconciliation
alert and changed `/ready` to HTTP 503 with reason
`broker_reconciliation_unsafe`. Repeated checks preserved the unsafe state.

The durable DB checkpoint remained:

- `butterfly_trades.id=182`: `OPEN`, no exit price/time/reason/P&L;
- `daily_risk_state` for XSP on 2026-07-16: trade count one, realized P&L zero;
- `broker_order_intents`: only the terminal filled ENTRY intent; and
- `decision_log`: entry evidence present, no manual-exit audit event.

No database mutation, service restart, deployment, or agent-initiated broker
write was performed while collecting this evidence.

## Remaining controlled actions

1. With explicit authorization, reconcile the verified `$0.07` fill into trade
   `182`, XSP daily risk state, and `decision_log` without inventing evidence.
2. Recreate only XSP from the restored paper-mode repo config.
3. Require zero OPEN XSP trades, zero nonterminal intents, broker flatness,
   `/health` OK, `/ready` ready, restart count zero, and clean reconciliation
   logs before closing the rehearsal.

Broker action and fail-closed response: **PASS**.
Full manual-flatten rehearsal: **PENDING POST-ACTION RECONCILIATION**.
