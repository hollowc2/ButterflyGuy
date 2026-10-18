# Next-session prompt: NDX-02 constituent quote fidelity

Copy the prompt below into the next session. This file is a task instruction,
not evidence that the task has been performed. The living document takes
precedence if newer decisions change the scope.

---

Complete the next bounded NDX-02 task: **attribute constituent quote-quality
anomalies and specify causal use of the independent minute evidence**.

Proceed autonomously with reversible research work. Finish the bounded audit,
verification, artifacts and living handoff. Do not stop at a plan. This task
authorizes no deployment, runtime changes or strategy experiments.

## Read first

1. `AGENTS.md` and `README.md`.
2. `docs/research/ndx-strategy-development.md` — authoritative living handoff;
   follow newer decisions over this prompt.
3. `docs/research/ndx-strategy/README.md` and
   `docs/research/ndx-strategy/NDX-01-reconciliation.md`.
4. `docs/research/ndx-strategy/NDX-02-execution-accounting.md` and
   `docs/research/ndx-strategy/NDX-02-reproduction.md`.
5. `docs/research/ndx-strategy/NDX-02-continuation.md` and
   `docs/research/ndx-strategy/NDX-02-continuation-reproduction.md`.
6. The `trading-strategy-research` and `market-data-operations` skills, including
   execution-validation guidance. Read `vps-server-management` before any
   necessary read-only Helios access.

Inspect Git status and the current source identity before changing anything.
Preserve existing work. A newer checkout commit does not invalidate unchanged
file hashes, and it does not become the historical runtime identity.

## Objective and decision boundary

Explain what produces the observed negative provider composite marks and
provider-mark/midpoint differences **to the extent the evidence permits**.
Separate arithmetic, recorded quote properties, timestamp/source limitations,
source-code behavior, and hypotheses about causes. Then specify what would be
required to use minute observations causally in a future research replay.

This is an evidence-fidelity and mechanics task. Do not optimize parameters,
choose liquidity/freshness thresholds using P&L, calculate a new strategy P&L,
test exit or hold-after-exit rules, rerun rejected variants, or promote a strategy.
Do not turn diagnostic categories into a retrospectively selected trading filter.
Full NDX-02 liquidity calibration remains open.

## Starting evidence and immutable parents

Use local evidence first:

- Original frozen R0 snapshot: `evidence/ndx/ndx-r0-20261014/`.
- Identity/settlement supplement: `evidence/ndx/ndx-01-supplement-20261015/`.
- Original independent continuation inventory:
  `evidence/ndx/ndx-continuation-inventory-20261015/`.
- Saved runtime-source observation:
  `evidence/ndx/helios-ndx-source-20261015/`.
- Frozen NDX-01 parent: `reports/research/ndx-01-20261015/run-03/`.
- Final accounting parent: `reports/research/ndx-02-20261015/run-02/`.
- Failed first continuation extraction:
  `evidence/ndx/ndx-minute-continuation-20261015/` — header only after a fixed
  60-second statement timeout; not usable quote evidence.
- Successful raw continuation snapshot:
  `evidence/ndx/ndx-minute-continuation-20261015-v2/`.
  `prices/extract.csv` holds the original quote JSON and available snapshot
  timing metadata; `schema/extract.csv` records the observed schema.
- Frozen normalized continuation parent:
  `reports/research/ndx-02-continuation-20261015/run-01/`.
  Inspect `observations.jsonl`, `rejected-groups.jsonl`, `coverage.jsonl`,
  `summary.json`, `contract.json`, `source-lock.json`, and `run.json`.
- Versionable manifests, contracts, ledgers and verification records:
  `docs/research/ndx-strategy/evidence/2026-10-15/`, especially
  `ndx02-continuation-{snapshot,contract-v2,source-lock,summary,coverage,verification}`
  with their actual `.json`/`.jsonl` extensions, and the accounting parent records.

Verify applicable manifests, required input hashes, frozen parent outputs and
current source pins before interpreting new results. Raw data and bulk runs are
private, Git-ignored dependencies; Git alone does not recover them. Eros retention
is accepted, but no independent backup has been established.

The acquisition scope was exact recorded NDXP symbols/direction/session expiration
within `(recorded exit, regular-session close]`, using collection `snapshot_time`.
Wrong-expiration database rows were outside that export's scope; do not claim
their absence from the database. The export excluded unrelated omitted-contract
payloads but preserved original quote fields and available snapshot metadata.

## Established findings to verify, not hardcode as cohort logic

The completed audit reported:

- 17 newer discretionary exits, derived from verified closed `mark_v1` records
  excluding `cash_settled`; all recorded quantities are one.
- All original inventory memberships, complete-timestamp counts and first/last
  timestamps reconcile.
- 3,364 raw leg rows across 1,125 timestamp groups: 1,114 complete three-leg
  groups and 11 incomplete two-leg groups (five on 317, six on 346).
- 635 negative raw composite bids and **157 negative provider composite marks**;
  composite marks range −13.97 to 10.04 points. No clipping or midpoint replacement
  was applied. Structural normalization is not economic/replay eligibility.
- **816** provider composite marks differ from the composite bid/ask midpoint by
  more than the predeclared 0.00011-point reporting tolerance. Do not assume this
  set is disjoint from, or identical to, the negative-mark set.
- Event/age and snapshot metadata cover **148 complete groups / 444 legs** on
  trades **339 (23 groups), 343 (24), 346 (101)**. The other 14 trades / 966 groups /
  2,898 legs lack constituent timing evidence. Do not infer freshness for them.
- Timed-subset reported quote ages span 0.504256–269.157070 seconds. There are
  145 events after the start-of-pass snapshot stamp, none after recorded local
  chain-fetch completion. Start-to-fetch-completion lag is 1.048414–2.789879 s.
  Those observations do not attest clock synchronization or consumer availability.
- All 1,097 complete-group intervals exceed 60 seconds: median 63.101178 s,
  p95 64.264143 s, range 61.131032–264.102769 s. Four gaps exceed 120 seconds;
  67 of 1,171 expected full minute buckets are missing. This is not a fixed
  minute-close bar series or R0's 30-second monitor stream.
- Sizes are recorded on all complete-group legs; displayed size is not proof
  of simultaneous constituent liquidity or complex-order fills/capacity.
- R0 and minute-replay eligibility remain **false for all 17 trades**.

The existing 72-test verification includes the baseline, accounting and
continuation audits with their private snapshots. It is a mechanics check, not
evidence of a profitable or deployable strategy.

## Required work

### 1. Freeze this audit's scope and mechanics before assessing causes

Create a new named audit contract/run, linked to the continuation and accounting
parents. Derive the complete universe, anomaly masks and timed subset from the
verified records. Reconcile the counts above without using constants to define
membership. Preserve all incomplete groups as exclusions with reasons.

Predeclare justified numerical, timestamp-equality and clock-comparison tolerances.
Retain the earlier 0.00011-point reporting and one-microsecond timestamp-equality
definitions when reproducing their counts. Any additional comparison needs a
stated purpose and justification; do not widen tolerances to obtain agreement.
This is not permission to select a freshness threshold from the observed outcomes.
These sessions are inspected development evidence, not an untouched holdout.

### 2. Build attributable observation and leg-level anomaly ledgers

For the complete universe and each anomaly, retain:

- Trade/session, exact symbols, option roots/expirations/types, strikes and widths.
- Collection snapshot time and each actually recorded quote-event time/age.
- Raw leg bid, ask, provider mark, individual midpoint and mark-minus-midpoint.
  Include recorded last/theoretical/intrinsic/time-value fields only when they
  help attribute an observation; label their recorded meaning and missingness.
- Raw `+1/−2/+1` provider composite mark, raw leg-market composite bid/ask,
  composite midpoint, provider-mark-minus-midpoint, and signed anomaly magnitude.
- Original metadata source/flags and actual fetch/gateway/chain times, with nulls
  preserved. Do not turn `snapshot_time` into an event or availability timestamp.
- Explicit structural, price-sanity, timing-coverage and attribution categories,
  keeping unknown separate from clean, invalid and zero.

Use independent arithmetic and trace representative examples to exact raw rows.
Include the most negative mark, near-zero negatives, material differences, and
timed/untimed examples where present. Selection is for explaining mechanics,
not economic winners/losers. Count overlap between anomaly sets and report
denominators per trade, date and timing-coverage subset.

### 3. Attribute what is observable without inventing a root cause

Investigate whether individual provider marks differ from their own bid/ask
midpoints or lie outside their own recorded markets; distinguish those facts
from merely having a negative butterfly composite. Preserve raw quotes and
provider-mark precision. A negative leg-market bid can be a legitimate diagnostic
cost to close; it must not be silently treated as a zero-valued observation.

For the timed subset, measure constituent event-time dispersion, oldest/newest
leg ages, and event-to-local-fetch-completion differences. Compare reported
ages to recorded clock evidence only when their reference clocks and semantics
are known. Record missing references and synchronization uncertainty; do not
label an event after start-of-pass as future information relative to a later
fetch completion. Separate collection cadence from constituent quote freshness.

Trace relevant parser/collector/database/metadata behavior using current local
source and the saved runtime-source evidence where available. Verify provenance
before claiming provider error, parser defaults, stale legs, asynchronous updates,
timestamp skew or deployment-specific behavior. Source code can demonstrate a
possible mechanism without proving it generated a historical row. Database
records are not original provider response payloads. If payloads or per-trade
deployment history are unavailable, state exactly which causes remain unresolved.

Use only minimal, separately attributed read-only acquisition if local evidence
cannot resolve a material question. Follow the VPS/data skills, verify the
host/path/disk/scope, use a new snapshot and fixed bounded read-only queries,
and preserve failed attempts. Do not scan credentials or widen the trading window.

### 4. Write a bounded causal minute-evidence specification

Specify each distinct time and what it can establish: collector pass start,
constituent quote event, gateway receive, local fetch start/completion, scheduled
time, persistence/commit and consumer availability. Missing fields stay missing.
Local fetch completion is evidence about the collector, not automatic proof that
a different consumer could read the snapshot at that time. Do not backdate a
decision to pass start or derive a missing timestamp by subtracting an age.

Define what future research would require for observation availability, decision
cadence, next-observation fills, incomplete groups, gaps, missing constituent
freshness and negative provider composites. Clearly separate supported assumptions,
provisional modeling choices and additional evidence requirements. Explain
whether the current data can satisfy the proposed contract at all; `insufficient
evidence` is an acceptable result. No replay implementation or economic evaluation
is authorized merely because a specification can be written.

Do not resample to a fabricated regular grid, interpolate, forward-fill, replace
provider marks with midpoints, floor negatives, merge independent minute rows
into R0, or retroactively change historical eligibility. Preserve the all-17
R0/minute replay ineligibility decision in frozen parents. Any future eligibility
policy must be a separate, reviewable contract rather than a rewrite of prior runs.

### 5. Make the audit reusable and independently verifiable

Produce an offline command with explicit evidence, manifest, config and output
paths. Verify source/input/config hashes and parent outputs; record Git SHA/dirty
state, source copies, Python/dependency/platform information, exact invocation,
UTC creation time, and output hashes. Refuse existing output paths. Preserve raw
and prior derived evidence. Corrections require a new run identity and parent
link, with an explanation; never overwrite a dated contract or source lock.

Reuse the existing audit patterns and keep changes surgical. Add focused
independent tests for any new arithmetic, anomaly accounting, timestamp handling,
coverage/unknown categories and eligibility mechanics. Include fixtures where
marks and midpoints differ, only some leg clocks are known, start-of-pass precedes
events, an illiquid leg is old, and metadata cannot establish consumer availability.
Run the relevant private-snapshot tests, repository lint and graphify update if
code changes. Do not broaden to broker-connected tests or runtime activation.

## Deliverables and completion criteria

- Machine-readable per-observation/per-leg anomaly and attribution ledgers,
  with coverage, overlap counts, missingness, examples and input provenance.
- A concise sourced reconciliation report distinguishing observed facts,
  supported deductions and unresolved hypotheses. No P&L-selected filter claims.
- A bounded causal minute-evidence specification with supported assumptions,
  unsupported assumptions, and the exact additional evidence needed.
- Reusable offline command, immutable contract/run manifest, independent focused
  verification and preserved failed/superseded attempts.
- Update `docs/research/ndx-strategy-development.md`: status of this portion only,
  exact commands, inspected evidence, source identities, findings, limitations,
  any failed attempts, and the next bounded action. Keep full NDX-02 liquidity
  calibration and strategy promotion explicitly incomplete.

The task is complete when the anomalies are reproducibly explained or explicitly
bounded by unavailable evidence, and the causal-use specification is reviewable.
It does not require finding a usable replay cohort or approving a trading rule.
Finish with what changed, verification results, remaining limitations and the
exact next action. No orders, service restarts, deployments, credential changes
or capture-service activation are authorized.
