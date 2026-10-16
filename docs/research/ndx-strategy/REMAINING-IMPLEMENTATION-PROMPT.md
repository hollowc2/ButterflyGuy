# Next-session prompt: remaining NDX implementation

This is a saved task prompt, not evidence of implementation or an operational
approval. The living plan takes precedence over this file if newer decisions
change the scope. Preserve the earlier `NEXT-STEP-PROMPT.md`, which describes the
completed constituent-fidelity task.

Copy the prompt below into the next implementation session.

---

Continue the remaining NDX research implementation from the completed NDX-02
constituent-fidelity audit. **First complete the bounded prospective provenance
specification and its offline verification fixtures.** Map the remaining work
through NDX-06, with explicit prerequisites and evidence requirements.

Proceed autonomously with reversible local specification, schema, fixture,
validation and documentation work. Finish a concrete, reviewable package and
living handoff. Do not stop at a plan. Do not infer permission to activate
capture, change runtime behavior, run economic experiments or deploy from the
existence of the later roadmap stages.

## 1. Read first and establish the starting state

Read:

1. `AGENTS.md` and `README.md`.
2. `docs/research/ndx-strategy-development.md` — authoritative living plan,
   especially current decision, NDX-02 through NDX-06 and promotion criteria.
3. `docs/research/ndx-strategy/README.md` and
   `docs/research/ndx-strategy/NDX-01-reconciliation.md`.
4. `docs/research/ndx-strategy/NDX-02-execution-accounting.md` and
   `docs/research/ndx-strategy/NDX-02-reproduction.md`.
5. `docs/research/ndx-strategy/NDX-02-continuation.md` and its reproduction guide.
6. `docs/research/ndx-strategy/NDX-02-quote-fidelity.md`,
   `docs/research/ndx-strategy/NDX-02-quote-fidelity-reproduction.md` and
   `docs/research/ndx-strategy/NDX-02-causal-minute-specification.md`.
7. `trading-strategy-research` and `market-data-operations` skills, including
   execution-validation guidance. Read the VPS skill before any separately
   necessary read-only server access and the Helios deployment skill before
   preparing any later operational activation.

Inspect Git status and current SHA before changing files. The prior task began
at `49da0284d24814ed2bc0838bbd543444b48019b9`; its implementation and generated graph
work may still be uncommitted. Preserve all existing work. A newer checkout SHA
does not invalidate unchanged pins or establish historical deployment identity.
Read graphify guidance before architecture analysis, preferring its wiki if
available. Keep work surgical and use existing audit patterns.

## 2. Preserve the completed baseline and its evidence boundaries

The following work is already complete and must not be repeated as a new strategy
experiment:

- NDX-01 reproducible historical baseline, with qualified runtime parity.
- NDX-02 execution/accounting attribution for the derived 17 discretionary exits.
- Exact-symbol independent continuation import, cadence and gap audit.
- Constituent quote-fidelity attribution and a bounded causal-use specification.

Frozen private parents:

- `reports/research/ndx-01-20261015/run-03/`.
- `reports/research/ndx-02-20261015/run-02/`.
- `reports/research/ndx-02-continuation-20261015/run-01/`.
- `reports/research/ndx-02-fidelity-20261015/run-01/`.

Local private snapshots:

- `evidence/ndx/ndx-r0-20261014/`.
- `evidence/ndx/ndx-01-supplement-20261015/`.
- `evidence/ndx/ndx-continuation-inventory-20261015/`.
- `evidence/ndx/helios-ndx-source-20261015/`.
- `evidence/ndx/ndx-minute-continuation-20261015-v2/`.

Versioned manifests/contracts/source locks/summaries/verification records are in
`docs/research/ndx-strategy/evidence/2026-10-15/`. Begin with
`ndx02-fidelity-{contract,source-lock,source-trace,summary,verification}.json`
and the copied `ndx02-fidelity-run.json`. Verify applicable input manifests,
required file membership, source pins and parent output hashes before relying on
the results. Use existing verification functions. Missing private evidence must
be reported; fixture-only checks cannot be called private-snapshot verification.

Git alone does not recover the raw snapshots or bulk runs. Eros retention was
accepted, but independent backup remains unestablished. Preserve the failed
header-only first extraction and all superseded runs unchanged.

## 3. Established findings: verify rather than hardcode membership

The derived cohort is closed `mark_v1` records excluding `cash_settled`, reconciled
against identity/lifecycle evidence. All 17 recorded quantities are one.

- 3,364 raw leg rows; 1,114 complete groups / 3,342 complete-group legs.
- Eleven incomplete groups, retaining 22 legs: five on 317, six on 346.
- 157 negative provider composites, 635 negative composite bids and 816
  reportable composite mark/midpoint differences; 103 groups overlap the two
  mark-anomaly sets.
- No complete-group individual mark is outside its own recorded market. All
  leg mark/midpoint residuals lie within ±0.005 points; weighted residuals
  explain composite differences exactly. This is rounding-compatible, not proof
  of a provider rounding implementation. The same 157 groups also have negative
  midpoints, so rounding does not explain their negative signs.
- Timing coverage: 148 complete groups / 444 legs on 339/343/346; 966 groups /
  2,898 legs on the other 14 trades lack constituent timing.
- Timed event dispersion reaches 268.471 seconds. There are 145 events after
  pass start, none after recorded local fetch completion. Age-reference clock
  semantics and synchronization remain unattested.
- Consumer availability is missing for every observation. Fetch completion is
  a collector timestamp, not proof another consumer could then read the data.
- Collection is irregular; all 1,097 complete-group intervals exceed 60 seconds.
  Four gaps exceed 120 seconds; 67 full-minute buckets are missing.
- All 17 trades remain ineligible for both R0 continuation and minute replay.

Retain the prior 0.00011-point reporting and one-microsecond timestamp-equality
tolerances for reproducing those findings. Neither is a trading or physical
clock-synchronization threshold. Any new tolerance needs an ex-ante purpose and
justification; do not widen tolerances to achieve agreement.

The previous focused suite passed 82 tests with private snapshots enabled; lint
passed and graphify AST update completed. Its recorded optional SQL-parser and
stale-label warnings are graph limitations, not failed Python audit checks.

## 4. Immediate deliverable: prospective provenance contract

Create a new named, versioned specification linked to the frozen fidelity and
accounting parents. Distinguish existing observations, required future fields,
provisional modeling choices and unavailable historical facts. Do not silently
promote the prior causal-use proposals to active eligibility rules.

### 4.1 Identify the actual consumer and causal boundary

Choose and justify a concrete intended research consumer/channel for the
specification, using local architecture evidence. Distinguish a collector-local
direct-response consumer from a DB-backed consumer. If more than one channel is
needed, specify each separately; do not treat their availability timestamps as
interchangeable.

Describe the complete sequence: request, response receipt, normalization,
persistence/publication, consumer read/receipt, potential decision and potential
later fill observation. Separate what local source demonstrates from what the
historical evidence attests. Record unresolved ownership across ButterflyGuy,
SchwabGateway and the provider; do not guess remote implementation details.

### 4.2 Specify the minimal record and field semantics

For each field, define type, units, timezone, clock owner, observation point,
nullability, provenance, consumer and the claims it can/cannot support. Include
only fields necessary for causal attribution and reproducible validation:

- Stable snapshot/version, acquisition/pass/request/response and instrument
  identity; exact root, symbol, expiry, type, strike and multiplier.
- Original response identity/hash and a scoped preservation/redaction policy.
  Preserve market values and provider precision without retaining credentials,
  account identifiers, authorization headers or unrelated sensitive responses.
- Recorded bid/ask/provider mark/sizes and per-contract event/age/source/flags.
  Keep chain-wide and per-contract metadata separate.
- Age calculation semantics: reference instant, reference clock, event clock,
  rounding/precision, missing-field behavior and any normalization/defaults.
- Scheduled deadline, pass start, local request start/completion, gateway receipt
  and constituent events, each separately nullable and attributed.
- Wall-clock and monotonic-clock relationships, process/boot scope, clock source,
  synchronization observations/uncertainty and discontinuity/restart handling.
  Monotonic values from different processes/hosts are not globally comparable.
- Persistence/publication identity and evidence; distinguish request/insert/
  transaction start, commit acknowledgement, visibility and consumer receipt.
  Do not label a timestamp taken before COMMIT as the commit time. A local
  post-commit acknowledgement is a bound/observation, not an exact server event.
- Consumer identity/build, query/read interval, returned snapshot identity and
  receipt completion; distinguish observed receipt from earliest possible
  availability. Preserve consistent complete-snapshot visibility semantics.
- Collector/adapter/gateway/schema/config/dependency build identities and the
  effective non-secret settings needed to attribute normalization and clocks.

Do not derive a missing timestamp by subtracting quote age. Do not reconstruct
original payloads from DB rows. Specify how metadata-write failure and quote
success are represented without falsely claiming an atomic complete publication.

### 4.3 Storage, failure behavior and feasibility

Specify append-only identities, overwrite refusal, ordering, deduplication,
correlation, schema versions, parent links and partial-write recovery. Cover
missing payloads, absent timestamps, dropped records, duplicate delivery,
out-of-order receipt, consumer read failure, clock reversal and process restart.

Separate a failed provenance record from a missing market observation. Do not
imply that recording failures should change trading/risk behavior. Runtime
coupling, fail-open/fail-closed choices, resource budgets and deployment belong
in a later separately reviewed integration proposal.

Map each requirement to one of:

- already recorded and verified;
- obtainable through a proposed local implementation;
- dependent on upstream SDK/gateway/provider changes or external evidence;
- historically irrecoverable or otherwise unavailable.

For cross-repository requirements, name the boundary and evidence needed without
modifying another repository or claiming it is implemented. Read-only local
inspection is preferred. Remote acquisition is unnecessary unless it can resolve
a specific material question; follow the relevant skills if justified. No
credential scanning, new capture activation or widened historical trading window.

## 5. Offline verification and fixtures

Provide a machine-readable contract/schema and an independently understandable
fixture package. Add the smallest offline validation/check command necessary to
make the proposed semantics executable and reviewable, following existing patterns.
It must have explicit input/config/output paths, no broker/network dependency,
new output directories, input/config/source hashes and actionable rejection or
unknown reasons. Do not build a replay engine or speculative general framework.

Validate **provenance/evidence sufficiency**, not strategy profitability. Historical
rows with missing required evidence must remain explicitly insufficient. Synthetic
fixtures may demonstrate future recording semantics, but must be unmistakably
synthetic and never merged with historical evidence or counted as new coverage.

Include focused independent fixtures for:

1. A complete synthetic direct-consumer receipt chain.
2. A complete synthetic DB publication/read/receipt chain.
3. Pass start preceding constituent events that precede fetch completion.
4. Fetch completion with no consumer receipt: availability remains unknown.
5. Only some constituent event/age references known; null differs from zero.
6. An old zero-bid-size leg alongside recent legs; chain-wide flags cannot label
   the selected leg automatically.
7. Marks differing from midpoint, negative composite mark and signed negative
   leg-market bid, all preserved without substitution or flooring.
8. Incomplete, duplicate, mismatched identity and out-of-order records.
9. Quote write succeeding while metadata/publication recording fails.
10. A transaction timestamp that cannot establish commit/consumer visibility.
11. Restart/clock discontinuity and incompatible monotonic clock domains.
12. Consumer receipt after close, a gap and no later eligible observation;
    no invented decision/fill is produced.

Do not select freshness, dispersion, gap or price thresholds from P&L. Where a
numerical bound needs independent mechanism/clock evidence, leave it unresolved
and demonstrate the resulting insufficient-evidence category.

## 6. Remaining implementation roadmap and explicit gates

Document these subsequent stages as pending work. **This invocation does not
authorize executing them merely because they appear in the roadmap.** Give each
stage concrete inputs, deliverables, verification and completion criteria.

### Stage B — Prospective instrumentation implementation and activation

After the provenance contract is reviewed, prepare the smallest code/integration
change for the actual channel and repositories. Preserve trading schedules,
limits, execution, token handling and paper/live mode. Validate recording and
failure behavior in isolation, resource impact and retention. Produce a concrete
reviewable diff and an activation/rollback/validation plan before any operational
approval request. Capture activation, migrations against live DBs, service
restarts and deployments require separately scoped authorization and skills.
A fixture or planned field is not an operationally observed record.

### Stage C — Complete NDX-02 evidence and liquidity calibration

Audit real prospectively captured provenance, coverage and recovery before
claiming freshness or eligibility. Separate midpoint accounting, signed leg-market
stress and actual complex-order fills/order states. Attribute partials, cancels,
rejects and costs only where observed. No live orders to calibrate execution.
Produce a documented execution model, explicit unknowns and one bounded
liquidity-filter hypothesis whose inputs and thresholds have independent
justification. Unknown quantities can remain unknown; do not manufacture an
eligible cohort. Actual execution and official XQC remain separate gaps.

### Stage D — NDX-03 entry-liquidity comparison

Require the full eligible entry opportunity set, including rejected candidates
and skipped/no-trade sessions; the selected 53 trades alone are insufficient.
Register one comparison, fixed definitions/thresholds, execution assumptions,
window and decision rule before evaluation. Hold other entry schedules, size,
risk and exits fixed. This requires a separate explicit research instruction.

### Stage E — NDX-04 late-session protection

Require causal post-exit evidence under a separately reviewed replay contract.
Freeze activation, peak basis, protection rule, quality/confirmation, fill timing
and settlement treatment before testing one hypothesis. Compare costs and lost
rare-winner exposure. Do not rerun or rename the six rejected settings without
new rationale and authorization. Inspected sessions are development evidence.

### Stage F — NDX-05 volatility/width research

Keep deferred until execution/data prerequisites are satisfied. Audit actual VXN
or same-expiry option-implied observations and timestamps before registering one
anchor change. Do not invent history, substitute SPX for NDX or infer unobserved
width performance. External vendor acquisition requires its own scope/budget.

### Stage G — NDX-06 integrated replay and fresh observation

Integrate only independently supported candidates, with skipped days, position
lifecycle, fees, settlement, daily/weekly risk-state feedback and relevant restart
recovery. Validate the integrated mechanics independently. Freeze a prospective
window, candidate, exposure, trial budget and evaluation rule before inspecting
fresh results. Paper observation and eventual deployment each require their own
operational authorization. A successful mechanics test is not an edge claim.

## 7. Verification, immutable artifacts and handoff

For the immediate offline package:

- Register the contract before evaluating fixtures/evidence; use new named run
  directories and preserve unsuccessful/superseded attempts.
- Record parent hashes, source copies, exact invocation, Git SHA/dirty state,
  Python/dependencies/platform, UTC creation, input/config/output hashes and any
  corrections. Never rewrite dated contracts, source locks or frozen outputs.
- Use focused tests for the new semantics and the existing private NDX suite
  where relevant; use the reproduction guide's explicit evidence environment
  variables. Report skips and missing dependencies exactly.
- Run repository lint and `git diff --check`. If code changes, run graphify's AST
  update using the available installed binary; record optional parser/label
  limitations without installing unrelated dependencies or semantic API work.
- Preserve the all-17 historical ineligibility decision. A new contract must not
  retroactively relabel prior runs. Do not calculate new strategy P&L.
- Update the living handoff with this portion's status, concrete file paths,
  exact commands, checks, source identities, limitations, failed attempts,
  remaining gates and the exact next bounded action. Preserve prior evidence.

Finish with a reviewable provenance specification, machine-readable schema,
offline fixtures/checker, feasibility/gap ledger, verification/run record and
remaining-stage roadmap. The immediate task is complete when those semantics
are concrete and testable, even if current historical evidence cannot satisfy
them. Do not call all of NDX-02 or the NDX strategy implementation complete.

Final response: state what was saved/implemented, verification results, unresolved
evidence and the exact next action. No orders, credential changes, live DB
mutations, capture activation, service restarts, deployments, strategy experiments
or promotion are authorized by this prompt.
