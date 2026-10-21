# SPX go-live readiness

Owner: Corey. Spec dated 2026-10-20. Scope: frozen SPX E0, one contract,
one trade/day, $500 daily loss limit, $20,000 allocation. NDX, XSP and prospective
cohort v2 remain paper. Quantity support stays in the execution code; sizing up
requires a separate review and guard change.

Status: **NO-GO pending evidence and operational sign-off.** This checklist is
not deployment approval. See the [decision record](research/spx-go-no-go-2026-10-20.md)
and [live runbook](live-runbook.md#spx-live-one-contract).

## Gate A: ready for the first live order

Edge and frozen rules:

- [x] Resolve the deferred 2026-10-19 session in the dedicated frozen v2 checkout.
  Retry recorded the twelfth trade; ledger verification passes. The scheduled
  updater subsequently committed the evidence as `2eaf522` and deferred October 20.
- [ ] Verify the append-only ledgers and complete the registered 20-trade integrity review.
- [ ] Merge an owner-reviewed go/no-go record reconciling the recent cohort with
  losing 2023–2025 replays. The initial decision in this branch is NO-GO.
- [ ] Confirm SPX rules still match the registered E0 configuration hash. A rule
  change requires a new cohort and resets this gate.
- [ ] Assign continued monitoring of the registered 60-trade early-failure review.
  Completing 60 trades is not a first-order gate; failure returns live to paper.
  Keep the original 120-trade/20-settlement/15-winner study endpoint unchanged.

Order path:

- [ ] Confirm Schwab accepts SPX butterfly limits on the $0.05 increment (M4):
  supported order preview, or first approved supervised order, with redacted evidence.
- [ ] Review the retained `entry.live_require_leg_bids=false` choice in the runbook.
- [ ] Check the frozen 4 × $0.10 / 20-second / 300-second ladder against actual
  entry-time SPX spreads and cancellation/fill latency.
- [ ] Prove post-close cash settlement reconciles without manual DB edits (M10).
- [ ] Pass synthetic live-mode partial-fill, cancel-pending, missing/unknown
  status, and unconfirmed cancellation tests on the release commit.

Market data and credentials:

- [ ] Validate the final SPX live Compose overlay after the gateway-paper overlay;
  only SPX changes to direct data and live execution. Verify authenticated startup.
- [ ] Measure the combined shared-credential request budget: gateway traffic
  for paper NDX/XSP and other consumers plus SPX direct collection, scanning,
  position polling, accounts/orders, token checks and broker reconciliation.
  Run the gateway load test in its approved test environment, compare protected
  latency and 429s before/after, and retain measurement duration and headroom.
  Gateway load tests alone do not measure the direct SPX load. If insufficient,
  stay paper and separately review force-fresh chains; do not bypass the guard.
- [ ] Put Saturday 10:00 Pacific reauthorization on the operator's calendar and
  verify the shared token-expiry alert is loaded and routed.

Operations and release:

- [ ] Review and rehearse the SPX runbook, halt command, targeted paper rollback
  and manual SPX flatten. Preserve the July 16 XSP evidence as historical proof only.
- [ ] Test critical-alert delivery to the actual supervision phone and record receipt.
- [ ] Verify account approval for index spreads, $20,000 allocation, independent
  expected-account pin, and named supervisor for the whole holding window.
- [ ] Run `uv run pytest -q` and `uv run ruff check .` on the exact release commit;
  require CI and Database Smoke, reviewed immutable image and rollback baseline.
- [ ] Exercise startup rejection for a wrong account ID, wrong loss cap,
  oversized launch, missing supervision, NDX live and gateway live market data.
- [ ] Prove DB/broker flatness before the first session, including
  `deploy_broker_flat_check.py` exit 0, no open DB trades, no active/unknown
  intents, no monitored trade and no duplicate live runtime.
- [ ] Obtain explicit approval of the named Helios SPX release and first live session.

Some acceptance facts (the first actual broker limit acceptance and actual
cash settlement) cannot be manufactured in offline tests. If no preview exists,
mark limit acceptance as conditional for the first approved supervised order;
failure aborts Stage 1. Synthetic settlement tests do not close the broker M10 gate.

## Gate B: ten supervised trades

Corey supervises all ten. Each trade uses one contract and the frozen rules.
Retain broker execution IDs/timestamps and prices, DB trade/intent references,
settlement evidence, notifications and a cost comparison. Require all ten to
reconcile, no manual DB edits, zero unknown statuses at session end and no
unresolved incidents. Sign and date the gate record before routine Stage 2.

## Gate C: twenty further routine trades

Continue the same one-contract limits with a reachable operator throughout each
holding window. Gate C completes the launch after thirty clean live SPX trades
in total: ten Stage 1 and twenty Stage 2. Every trade must reconcile, zero
unknown orders may remain, and average fill cost must not exceed the registered
stressed model. Write up every stop-rule event and update the runbook to match
what actually happened. Sizing above one contract remains a separate decision.

Any stop-rule trip in either stage latches entries, hands broker control to the
operator, reconciles and returns to paper. Re-entry restarts that stage's count.
Use an append-only stage log recording stage, trade ID, release SHA, date,
clean/incident status, reconciliation evidence, cost comparison and reviewer.
Never count paper trades, historical canaries or manual DB repairs toward a gate.
