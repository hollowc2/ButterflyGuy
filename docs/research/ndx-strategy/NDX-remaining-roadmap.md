# Remaining NDX implementation gates

The immediate Stage A deliverable is [NDX-provenance-v1](NDX-02-prospective-provenance.md):
proposed receipt semantics, schema, synthetic fixtures and offline checks. It
completes the bounded specification task only. Full NDX-02 and NDX-03–06 remain
open. The following stages are pending and require their stated scope; this
roadmap grants no operational or economic-experiment authorization.

## Stage B — Implement prospective recording, then separately approve activation

Inputs: reviewed v1 contract, chosen DB consumer and ownership agreement for
ButterflyGuy/SchwabGateway/provider boundaries; accessible upstream clock/age
semantics; non-secret payload preservation policy. Resolve whether the conservative
same-domain protocol suffices or register a reviewed cross-domain proof first.

Deliverables: smallest local integration diff and separate upstream requests;
immutable snapshot/manifest publication and receipt logging; append-only partial
failure/drop/retry handling; resource and retention measurements; migration and
activation/rollback/validation plans. Preserve schedules, size, limits, routing,
execution, credentials, token handling and paper/live mode. No speculative trading
coupling. Read VPS and Helios deployment skills before operational preparation.

Verification: isolated recording tests with quote-success/meta-failure, crash during
write/commit, duplicate/restart/recovery, consistent consumer reads, precision and
redaction checks; measured latency, disk and CPU budget and retention review.
Complete implementation review before requesting separately scoped capture,
live-DB migration, restart or deployment authorization. Done only when a reviewed
change and authorized activation have independently observed real records; fixtures
and source fields alone do not satisfy activation or coverage.

## Stage C — Finish NDX-02 evidence and liquidity calibration

Inputs: real prospectively recorded bodies/publication/receipts, verified build/clock
semantics, coverage/drop/recovery audit and preserved historical accounting parents.

Deliverables: evidence sufficiency ledger with explicit unknowns, a documented
execution model separating midpoint accounting, signed leg-market stress and actual
complex-order order states/fills. Attribute partials, cancel/reject/unfilled outcomes,
fees and costs only where observed. Official XQC remains separate. Register one
bounded liquidity-filter hypothesis with independent mechanism/clock-based inputs
and bounds. Do not force an eligible cohort or use P&L to select thresholds.

Verification/completion: raw-to-record/source/identity reconciliation, representative
independent execution/accounting examples, coverage and recovery checks, and a
written supported/unknown decision. No live orders to obtain execution calibration.
Missing upstream quantities may remain unknown; receipt checks alone do not finish
NDX-02 or qualify an economic experiment.

## Stage D — NDX-03 entry-liquidity comparison

Inputs: satisfied NDX-01/02 prerequisites and the full eligible opportunity set,
including rejected candidates and skipped/no-trade sessions. The selected 53 trades
cannot supply that set. Requires a separate explicit research instruction.

Deliverables: one preregistered comparison with fixed input definitions, thresholds,
execution assumptions, window and decision rule; hold entry schedules, size, risk and
exits fixed. Verification: independent opportunity accounting, selection/fill timing,
exclusions, costs and stability. Done when the registered comparison yields a
reproducible reject/refine/insufficient-evidence/candidate decision; fewer trades
alone is not improvement. Reviewed sessions remain development evidence.

## Stage E — NDX-04 late-session protection

Inputs: causal post-exit evidence and a separately reviewed replay contract.
Deliverables: freeze one hypothesis's activation, peak basis, protection rule,
quality/confirmation, fill timing and settlement policy before testing. Register
window, costs and decision rule under separate research authorization.
Verification: causal signal/fill/gap/terminal fixtures and paired comparison of gains
preserved, costs and rare winners lost. Done when those mechanics and economics
support a written decision. Do not rerun or rename the six rejected settings without
new rationale and authorization. Already inspected sessions are development data.

## Stage F — NDX-05 volatility and width

Deferred until execution/data prerequisites are satisfied. Inputs: actual VXN or
same-expiry NDX option-implied observations with audited timestamps and source.
Deliverables: one registered anchor change with unchanged other mechanics, under
separate research scope. Verification: source/timing/coverage, implied calculation
where used, fixed execution and evaluation protocol. Done when a reproducible
bounded comparison supports a decision. Do not invent history, use SPX as NDX,
or infer width performance absent observations. Vendor scope/budget is separate.

## Stage G — NDX-06 integrated replay and fresh observation

Inputs: independently supported candidates, complete opportunity/lifecycle/cost/
settlement data, daily/weekly risk-state and relevant restart/recovery semantics.
Deliverables: integrated replay including skipped days, positions, fees and feedback;
independent mechanics validation; a frozen prospective candidate, exposure, window,
trial budget, uncertainty and evaluation rule before fresh inspection.

Verification: calendars/roots, causal fills, partials where supported, terminal
settlement, recovery and risk feedback, compared with a concurrent frozen baseline.
Done when the registered evaluation supports a written decision with limitations;
mechanics success is not an edge claim. Paper observation activation and eventual
deployment each require separate operational authorization. No automatic promotion.

## Exact next bounded action

Stage B status (2026-10-18): recording implemented and reviewed (PR #53), observer
installed disabled on Helios (2026-10-17), and its background `market_data:read`
gateway consumer registered and loaded (2026-10-18). Nothing has been captured.

Next: on a trading day, build a fresh real NDXP session context (never reuse an
expired one) and obtain separately scoped approval for one bounded manual capture.
Its real records then feed Stage C. Capture remains inactive until authorized.
