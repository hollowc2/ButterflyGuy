# XSP Manual-Flatten Evidence - 2026-07-16

## Result

The supervised broker-action portion passed. The operator closed the exact
one-contract XSP butterfly as one complex order. Schwab reported the order
`FILLED`, all three legs became flat, and no working XSP order remained.

The manual broker order had no bot-owned EXIT intent, so the runtime correctly
did not guess at an exit transition: it retained trade `182` as OPEN, left
realized P&L unchanged, degraded `/ready`, and emitted the reconciliation-failure
alert until the verified fill was reconciled under supervision.

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
write was performed during the broker-action evidence phase.

## Post-action reconciliation and paper restore

After fresh read-only proof that Schwab remained flat with two terminal `FILLED`
orders, only XSP was stopped so its in-memory monitor could not act during
reconciliation. One atomic DB operation then:

- closed trade `182` at `$0.07` and `2026-07-16T16:01:37Z` with reason
  `manual_broker_close`, spread P&L `-$0.26`, and redacted fill metadata;
- changed XSP daily realized P&L from `$0` to `-$26`; and
- inserted one `manual_trade_exit_reconciled` decision event.

Preconditions required the exact OPEN XSP trade, one-contract 744/748/752
structure, `$0.33` entry, zero realized P&L, and zero nonterminal XSP intents.
Any mismatch would have aborted the operation.

Only XSP was then rebuilt/recreated. Final runtime proof:

- `paper_trading=true`, `allow_live_trading=false`, `LIVE_XSP_CANARY=false`;
- trade `182` CLOSED at `$0.07`, spread P&L `-$0.26`, XSP realized P&L `-$26`;
- zero OPEN XSP trades and zero nonterminal XSP intents;
- Schwab XSP positions empty and both same-day orders terminal `FILLED`;
- `/health` OK, `/ready` ready, restart count `0`; and
- no unsafe/error/traceback startup log.

Full manual-flatten rehearsal: **PASS**.
