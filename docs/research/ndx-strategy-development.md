# NDX strategy development — living research plan

Last updated: **2026-10-15**. Evidence covers sessions through **2026-10-14**.

This is the canonical cross-session record for developing the NDX strategy.
Keep the current decision, next action, experiment history, and handoff here.
Dated evidence packages remain immutable; append new evidence rather than
replacing an earlier result. Runtime configuration and source remain the
authority for what the bot actually does.

## Current decision

**Refine execution and data fidelity first. Do not promote any of the six tested
exit variants.** There is no validated replacement strategy or approved deployment
from this review. The existing paper strategy was left unchanged.

The initial suggestion to tighten exits broadly did not survive testing. Some
settings improved midpoint results on the broader comparison, but every tested
candidate underperformed the baseline under marketable-price stress. All six
also underperformed under both accounting models on uninterrupted quote paths.

**NDX-01 reference baseline and evidence audit are complete, with explicit
limitations.** The named snapshot reproduces the historical approximation offline;
complete runtime parity and official settlement are not established. See the
[NDX-01 reproduction guide](ndx-strategy/README.md) and
[reconciliation report](ndx-strategy/NDX-01-reconciliation.md).

**NDX-02 execution/accounting attribution is complete for the derived 17-exit
cohort; the rest of NDX-02 remains open.** See the
[audit and bounded execution model](ndx-strategy/NDX-02-execution-accounting.md).
Recorded paper accounting, leg-market estimates and unknown broker execution are
separate. Ten exits lack independent signal events; precise quote freshness and
signal-to-fill latency remain unestablished.

**Continuation import/cadence/gap audit complete; replay eligibility remains
false.** The [new independent snapshot audit](ndx-strategy/NDX-02-continuation.md)
reconciles all 17 inventory records but exposes cadence gaps, incomplete leg
groups, negative provider composites and limited constituent timing evidence.
It does not extend R0 or establish a causal quote path.

**Constituent quote-quality attribution and causal minute specification complete;
causal minute replay remains unsupported.** The
[fidelity report](ndx-strategy/NDX-02-quote-fidelity.md) explains exact leg arithmetic,
rounding-compatible differences and recorded event dispersion, with historical
root causes explicitly unresolved. The
[causal-use specification](ndx-strategy/NDX-02-causal-minute-specification.md)
requires consumer availability and attested timing semantics that are missing.
All 17 trades remain ineligible for R0 continuation and minute replay.

**Prospective provenance specification and offline fixtures complete.**
[NDX-provenance-v1](ndx-strategy/NDX-02-prospective-provenance.md) specifies separate
DB and collector-local receipt channels, strict schema, append-only publication,
clock/age semantics and failure evidence. Its checker validates provenance only;
18 synthetic records add zero historical coverage. Full NDX-02 remains open.

**Native gateway-body preservation and PostgreSQL research integration implemented;
activation remains disabled.** The [new integration](ndx-strategy/NDX-02-native-postgres-integration.md)
uses the pinned SDK's client= injection, exact buffered native gateway bytes,
separate asyncpg research tables and actual PostgreSQL transaction/receipt checks.
The earlier SQLite package remains preserved. All 164 private/real-engine checks
pass. Gateway-normalized bytes do not establish original provider data or missing
upstream age-reference/build/clock evidence.

**Next action: finalize the concrete one-shot observer capture plan**: exact real
capture context, release/secret/role/connectivity choices and storage reserve/
retention review. The subsequently authorized read-only broker audit passed for
its current-session order scope; see the
[broker supplement](ndx-strategy/NDX-02-observer-broker-flatness.md). Exact-image
compatibility, target synthetic resources, schema restore and separate image
packaging/roundtrip now pass; see the
[completed operational review](ndx-strategy/NDX-02-observer-operational-review.md).
Upstream freshness-reference/build/provider-body gaps remain separate. The
[remaining-stage gates](ndx-strategy/NDX-remaining-roadmap.md) still apply. No capture,
replay, threshold selection, promotion or deployment is activated; prior prompts
and failed/superseded evidence remain preserved.

The [next-stage implementation prompt](ndx-strategy/NEXT-STAGE-TIMESCALE-OBSERVER-PROMPT.md)
scopes exact-image validation, least-privilege roles, default-off observer lifecycle,
resource/drop/retention checks and an activation review package. It authorizes no
live activation or economic experiments.

**Default-off observer, exact target, resource/restore and runtime image checks
complete; live activation review remains incomplete.** The
[latest review](ndx-strategy/NDX-02-observer-operational-review.md) supersedes earlier
bootstrap-only image evidence. The corrected harness proves completed image
initialization and exact PG 16.11/TimescaleDB 2.25.2: compatibility run-07 passed
**50 tests, zero skips**. Target resource/restore run-02 passed with nine exact
restored publications, nine new restricted-reader receipts and one preserved
unpublished/unacknowledged synthetic attempt. A separate local default-off image
passed disabled/spied packaging checks and one enabled synthetic image-to-target
roundtrip. The earlier 186-test private-enabled result is retained; repeated
subsets and synthetic smoke cases are not summed as new unique historical coverage.

Read-only Helios review found healthy endpoints, zero DB OPEN/nonterminal intent
rows, no installed observer schema/roles/process, preserved dirty source/config,
about 22.10 GB free. After explicit authorization for the normal authentication/
refresh scope, the broker supplement records zero tracked option positions,
zero October 16 queried orders and zero OPEN/nonterminal DB rows; one normal
persistence callback was observed without inspecting token values. Orders outside
that date window are not covered. The intended observer image is local only.
No deployment, live DDL/grant or real capture occurred. **Next bounded action:**
name the one-shot real context and review release/role/secret/connectivity/storage
choices, with an appropriately fresh activation preflight. No operational capture
approval is requested from an incomplete named-target package.

## Intended finished system

Develop an NDX-specific, reproducible research and paper-observation workflow that:

- Separates strategy midpoint P&L, execution stress, and actual broker fills.
- Uses causal NDX observations, exact option roots/expirations, and attributed
  settlement data; measures missing or stale inputs explicitly.
- Evaluates entry selection, liquidity, exits, costs, and portfolio risk-state
  feedback together after isolated hypotheses pass initial checks.
- Preserves a frozen baseline, all attempted variants, coverage exclusions,
  uncertainty, and out-of-sample decisions across sessions.
- Produces a reviewable candidate and observation plan before any activation.

Completion means the workflow and evidence meet the decision criteria below. It
does not mean a profitable strategy must be found; rejecting an unsupported
strategy is a valid outcome.

## Scope and operating boundaries

Research concerns the deployed NDX 0-DTE butterfly strategy and its NDXP inputs
where applicable. Confirm instrument/root/settlement identity for every dataset;
do not assume all contracts labelled NDX have the same settlement convention.

This plan authorizes no changes to running services, trading limits, sizing,
paper/live mode, account guards, routing, or credentials. Offline research should
preserve the recorded position size and current limits unless a separately stated
experiment requires otherwise. A research decision of `paper-trade candidate`
does not activate a bot. Live-service changes require the repository's deployment
workflow and the owner's explicit authorization.

## Evidence from the initial review

The [dated evidence snapshot](ndx-strategy/evidence/2026-10-14/summary.json)
preserves the numerical findings below. The
[source manifest](ndx-strategy/evidence/2026-10-14/source-manifest.json) records
source identities and hashes. Treat these as a historical snapshot, not a current
health check.

- **113 closed paper trades**, 2026-03-30 through 2026-10-14. Aggregate recorded
  P&L was **−$9,832.40**. This spans different configurations and fill conventions
  and is not a homogeneous strategy backtest.
- **75 trades with held-leg recordings**. The extraction contained 514,551 grouped
  observations; 4,377 incomplete observations were excluded. The remaining
  510,174 complete three-leg observations reconciled to recorded composite marks.
- **53 newer `mark_v1` trades**, 2026-07-22 through 2026-10-14. Recorded P&L was
  **+$9,254.84**, including commissions embedded in fill prices.
- For the same 53 trades, stored marketable-entry and exit estimates produced
  **−$30,978.16**. Median entry-cost premium over the paper fill was **$455 per
  fly**. These leg-market estimates are execution stress, not observed fills of
  the complex order and not proof that midpoint fills are impossible.
- **Eight winners out of 53 trades**. Removing the three largest gains leaves
  **−$13,733.83** in recorded P&L. Rare large payoffs dominate this sample.
- Newer width exposure was **49 trades at 100 points and four at 80 points**;
  no 150-point trades occurred in that sample. No width ranking is justified.
- Full-history drawdowns and newer-sample drawdowns are measured from completed
  trades, not intraday equity. There is no capital denominator for portfolio
  return, annualization, or normalized risk claims.

Two useful examples illustrate competing failure modes:

- **October 1, trade 323:** entry 7.93; recorded peak mark 67.20, with a leg-market
  bid of 55.30 at that observation; final settlement zero. This supports studying
  late gains given back, but the peak is not an available hindsight exit rule.
- **October 8, trade 336:** recorded gain $8,814.46. The tested 50%-of-cost stop
  would have exited before the eventual recovery. Earlier protection can remove
  the winners on which the strategy depends.

### Accounting and replay facts to retain

- `mark_v1` already embeds commission in entry and exit fill prices. Do not
  subtract it a second time. The reviewed model uses $0.65 per option contract,
  four contracts per fly per side, with price rounding; settlement has no exit
  commission. Those are dated study assumptions, not instructions to change fees.
- Candidate exits used the next observed quote within 30 seconds, or a recorded
  terminal exit diagnostic within that interval. Trailing confirmations were
  reset across gaps above 30 seconds.
- Stress used the stored marketable-entry estimate and bid-side exit less
  slippage/commission. Negative exit proceeds were floored at zero. That floor
  makes stress more favorable than paying to close at a negative quoted credit;
  it must be disclosed, counted, and challenged in future NDX accounting work.
- Recorded paper settlements used the final regular-session one-minute index
  close. Official NDXP **XQC** settlement was not independently verified. See the
  [Nasdaq settlement-symbol notice](https://nasdaqtrader.com/MicroNews.aspx?id=OTA2019-02).
- Historical held-leg recordings end at the actual exit. An alternative that
  would hold longer needs independent continuation evidence or must be censored.
- The complete common comparison contained **49 of 53 newer trades**. The
  uninterrupted common subset contained **32**, with no observation gap above
  30 seconds. Complete-case selection can bias results; neither subset is a full
  portfolio replay.
- The baseline replay resolved 51 newer paths. One exit-reason mismatch remained
  on August 6, trade 222; that gapped path was excluded from the uninterrupted
  subset. Other fill differences arose from next-observation versus actual
  order-time prices. Perfect runtime parity was not established.
- All reviewed sessions are development evidence. There is no untouched holdout.
  A chronological split of these sessions does not make them unseen again.

## Experiment and decision log

Study **NDX-R0**, completed in the session spanning October 14–15. Entries,
quantities, directions, and strikes stayed fixed. Six candidates plus the baseline
were specified; no expanded search was used to find a winner.

The baseline on the 49-trade common cohort returned **+$7,969.59** under paper
accounting and **−$29,848.41** under stress. Candidate differences below are
relative to that cohort's baseline, not the full 53-trade recorded result:

- **R0-T70:** cap permitted peak-value drawdown at 70% in every regime.
  Stress difference **−$8,267.68**. Decision: reject this tested setting.
- **R0-T60:** cap drawdown at 60%. Stress difference **−$6,418.27**. Reject.
- **R0-T50:** cap drawdown at 50%. Paper difference **+$5,410.73**, but stress
  difference **−$4,743.27**. On 32 uninterrupted paths, paper difference was
  **−$2,023.27** and stress difference **−$9,168.27**. Reject.
- **R0-PP:** existing `profitprotector` defaults. Stress difference
  **−$14,840.27**. Reject.
- **R0-F2:** after a 2× entry-value peak, exit at or below 1.25× entry value,
  subject to quote quality and two consecutive observations. Stress difference
  **−$5,450.12**. Reject.
- **R0-S50:** absolute 50%-of-entry-cost loss stop. Stress difference
  **−$22,684.73**. Reject.

These decisions apply to the specified settings and evidence. They do not prove
that every possible exit rule fails. Do not silently reintroduce a rejected
setting with a different name; record why any retest is warranted.

The initial study corrected terminal-fill censoring and duplicate commission
deductions before the final results. Files named `pre-terminal-fix` and
`pre-accounting-fix` are preserved superseded outputs and must not be reported as
final evidence. The historical `recorded_gross` JSON key also contains the
commission-inclusive `mark_v1` result; use the accounting definition, not that key
name, when interpreting it.

## Work plan

Work through dependencies in order. Each task ends with evidence and a decision,
not an automatic deployment. Proposed experiments below are **not registered or
tested** unless their status is explicitly updated.

### NDX-00 — Initial audit: complete, with limitations

The recorded-trade review and fixed-entry exit experiments are complete. Retain
the conclusions above and the known parity, coverage, and settlement limitations.
Historical verification: 28 state-machine/position-manager tests passed; hand
accounting and causal-fill checks passed. This is not full simulator validation.

### NDX-01 — Reproducible baseline and usable data: complete, qualified

- Preserve the raw extracts and frozen source/config identity in durable evidence
  storage; verify hashes after copying. Keep bulk files out of Git and preserve
  their originals. Record a recoverable location rather than relying on `/tmp`.
- Make the offline study runnable from an explicit input/output directory, without
  machine-specific or temporary script dependencies. Extraction must create a new
  snapshot, not overwrite an earlier one. Separate extraction from offline replay.
- Reconcile the deployed baseline, packaged source, effective settings, recorded
  signal times and fill times. Explain trade 222's mismatch and bound the effect
  of remaining price differences. Historical and current baselines are separate.
- Build a per-session coverage ledger for entry observations, held legs, gaps,
  post-exit continuation, and settlement provenance. Define eligibility before
  candidate runs. Missing evidence is not a zero quote or a zero-P&L session.
- Distinguish quote event time, collection time, and availability where recorded;
  disclose where historical timestamps cannot establish freshness.

Done when a fresh checkout can verify a named evidence snapshot and reproduce
the baseline with explicit exclusions, no network/broker dependency, and no
unexplained material accounting differences. Report irrecoverable gaps instead
of reconstructing observations that never existed.

### NDX-02 — Execution calibration and liquidity: accounting portion complete

The 2026-10-15 execution/accounting audit is complete for the derived 17 newer
discretionary exits. [Results/specification](ndx-strategy/NDX-02-execution-accounting.md)
and [offline command](ndx-strategy/NDX-02-reproduction.md) preserve the frozen
baseline and distinguish verified mechanics from missing execution evidence.
Liquidity calibration, causal quote freshness, complex-order execution evidence,
and any filter hypothesis/threshold remain incomplete. The bullets below remain
the broader NDX-02 scope; this audit does not mark all of them satisfied.

- Audit the stored diagnostics: entry mark/bid/ask, spread width, sizes where
  observed, quote age, limit, latency, slippage, commission and rounding.
- Keep midpoint, leg-market stress, and any actual complex-order fill evidence
  as separate models. Treat unfilled orders as unfilled, not hypothetical fills.
  Quote sizes alone do not prove a complex order could execute.
- Measure entry and exit cost separately, including the cost of more frequent
  exits. Attribute partial fills, cancels and rejected orders where available.
- Use existing read-only evidence first. Do not place live orders to calibrate
  fills. Any new capture service or runtime instrumentation needs its own
  implementation and operational authorization before activation.

Done when the model's costs and unknowns are attributable and representative
examples reconcile independently. Output a documented execution model and a
bounded liquidity-filter hypothesis; do not choose a threshold by maximizing the
already-inspected sample's P&L.

### NDX-03 — Entry liquidity experiment: pending NDX-01/02

Compare the frozen entry policy with one explicitly specified liquidity-aware
alternative. Candidate inputs may include executable cost relative to width,
spread relative to mark, and quote freshness; their exact definitions and
thresholds remain to be specified before evaluation.

Use the full eligible entry opportunity set, including skipped/no-trade sessions,
and record accepted and rejected candidates. Filtering only the existing 53
trades cannot establish how the revised selector would behave. Preserve current
entry windows, size, risk limits and exit policy to isolate the change.

Done when the registered comparison either survives costs and stability checks
or is rejected with a stated reason. A reduction in trade count alone is not an
improvement.

### NDX-04 — Late-session profit protection: hypothesis only

Test whether protecting gains later in the session preserves early recovery
opportunities. Specify the activation time, peak basis, activation amount, floor
or trail, quote-quality gates, confirmation, signal-to-fill delay, and settlement
handling before running. Numerical choices are unresolved, not implied approval
of an existing `profitprotector` configuration.

Run one bounded comparison with entries fixed. Measure gains preserved and rare
winners cut short under both execution models. Combine with a successful entry
change only after each isolated contribution is understood. October 1 and
October 8 are inspected examples, not validation cases or optimal tuning targets.

### NDX-05 — NDX-specific volatility and width: deferred

The current anchor uses VIX; VIX represents SPX volatility, while VXN represents
Nasdaq-100 volatility. A VXN or same-expiry NDX option-implied anchor is a research
hypothesis, not an assumed correction. See [Cboe index products](https://www.cboe.com/us/indices/indicesproducts/).

First audit availability, timing, index observations and settlement support.
Compare one anchor change at a time with unchanged entry/exit mechanics. Do not
invent VXN history, substitute SPX prices for NDX, or infer 150-wide performance
from the existing trade ledger. Broader vendor-history work must satisfy the
[NDXP data requirements](thetadata-local-backtesting.md) first.

### NDX-06 — Integrated replay and fresh observation: pending candidates

- Integrate only candidates that pass their individual checks. Replay skipped
  days, position lifecycle, fees, settlement, and actual daily/weekly risk-state
  feedback; a fixed-entry study cannot validate those interactions.
- Verify session calendars, option roots, fill causality, partial fills where
  supported, and restart/position recovery mechanics relevant to the change.
- Before inspecting new sessions, freeze the candidate, execution assumptions,
  date window, exposure, trial budget, uncertainty method, and decision rule.
  Do not declare October 15 or any later date unseen without checking prior use.
- Run a defined research observation plan against a concurrent frozen baseline.
  Log opportunities, exclusions, signals and hypothetical fills consistently.
  Runtime activation remains a separate decision.

Done when a written decision says `reject`, `refine`, `insufficient evidence`, or
`paper-trade candidate`, with reproducible evidence and remaining limitations.

## Experiment contract and promotion criteria

Before each new experiment, append an ID and specify:

1. Parent baseline, exact rule change, mechanism, and falsification criterion.
2. Source/config hashes and dirty state; dataset identity, observed features,
   coverage, time zones and exclusions; known prior inspection.
3. Development and evaluation windows, costs and fill timing, capital/exposure
   assumptions, trial bounds and stopping rule. Use subsequent uninspected data
   for fresh evaluation; stop calling it untouched once it influences a change.
4. Primary net metric, paired comparison, chronological splits, day-block
   uncertainty method where appropriate, concentration and drawdown checks.
5. Exact reproduction command, outputs, decision, and next action. Log failures
   as well as favorable trials. A post-result revision starts a new experiment.

Hard prerequisites are correct accounting, causal signals/fills, attributable
settlement, and sufficient coverage for the claimed result. A mechanics test is
not evidence of profitability.

For an economic candidate, predeclare the required net improvement, acceptable
drawdown/exposure, cost stresses and uncertainty before evaluation. Require an
advantage that survives credible costs and is not explained by one exceptional
trade or a missing-data exclusion. Report absolute net profitability as well as
relative improvement: losing less than the baseline does not establish an edge.
Evaluate the top-three-removed paired improvement without pretending a naturally
rare-payoff strategy must win on every small subset. If uncertainty or dependence
prevents a defensible claim, choose `insufficient evidence` and define the next
observation window; do not tune until it passes.

No sample-size threshold or new trading limit is authorized by this document.
Activation requires a separate reviewed deployment record, explicit approval,
rollback procedure, and the applicable [live runbook](../live-runbook.md).

## Evidence locations and reproduction

Durable small records intended for Git:

- [Summary and full candidate comparisons](ndx-strategy/evidence/2026-10-14/summary.json).
- [Source/file hashes](ndx-strategy/evidence/2026-10-14/source-manifest.json).
- [Frozen deployed YAML](ndx-strategy/evidence/2026-10-14/deployed-config.yaml).
- [Historical verification](ndx-strategy/evidence/2026-10-14/verification.json).

The full local bundle is `reports/research/ndx-review-2026-10-14/`. It contains the
raw CSVs, extraction SQL, scripts, final report, metrics, coverage and superseded
outputs. It is Git-ignored and will not appear in a fresh checkout. Check its
presence and hashes before use; do not treat the small summary as a replacement
for the quote paths. Its verified recovery copy is now
`/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014/`
on Eros-backed NFS. The owner accepted retention on Eros; this shares the same
filesystem as the original bundle and is **not an independent backup**. Snapshot
identity, checksums, commands and actual protection are recorded in the
[NDX-01 guide](ndx-strategy/README.md).

Historical offline reproduction, from the repository root when that bundle and
its Python environment are present:

```bash
PYTHONPATH=src .venv/bin/python reports/research/ndx-review-2026-10-14/replay.py
PYTHONPATH=src .venv/bin/python reports/research/ndx-review-2026-10-14/describe.py
PYTHONPATH=src .venv/bin/python reports/research/ndx-review-2026-10-14/build_report.py
```

These are historical scripts with machine-specific paths and output rewrites,
not the finished reusable runner. Preserve the bundle before rerunning. Do not
run extraction scripts against existing evidence until overwrite protection is
implemented or a distinct output path is verified. Exact reproduction also needs
the recorded source/settings; a changed checkout is a new run identity.

## Session handoff

At the start of a session:

1. Read this document and `AGENTS.md`; check the most recent decision and next ID.
2. Inspect Git status without disturbing existing work. Compare actual source and
   runtime identity with the dated snapshot before interpreting new results.
3. Check which evidence is present and verified. Use the server skill for any
   remote access; do not infer current bot health from this historical document.
4. State the bounded task and its verification step. Continue from the next
   incomplete task rather than restarting the initial review.

At the end, update the current decision/next action and append a dated entry:

- Task/experiment ID and status; concrete change or finding.
- Evidence path, source/config/dataset identity, and reproduction command.
- Verification completed or skipped with reason; limitations and failed trials.
- New data inspected, outstanding decisions, and the exact next action.
- Whether runtime state changed; link separately authorized deployment evidence
  if it did. Never write credentials or account identifiers here.

Suggested new-session prompt:

> Continue the NDX strategy work from `docs/research/ndx-strategy-development.md`.
> Read its current decision and handoff, verify available evidence, and complete
> the next bounded task with its stated checks. Update the living document and
> experiment record. Preserve runtime settings and existing evidence.

### 2026-10-15 — Living plan established

Initial review complete; six tested exit alternatives rejected. Preserved the
small evidence snapshot and this roadmap for future sessions. No strategy or
runtime changes. Historical verification is recorded separately; this session's
work is documentation and evidence retention. Next: **NDX-01**, reproducible
baseline, evidence recovery location, and coverage/parity audit.


### 2026-10-15 — NDX-01 reproducible reference and coverage audit

**Status: complete for the qualified reference baseline and evidence audit.**
No full-runtime-parity, official-settlement or strategy-promotion claim. The
recorded-policy/deployment history, exchange-event freshness and official XQC
remain unavailable evidence, not implicitly satisfied checks. Runtime strategy,
services, risk settings, routing, mode, tokens and credentials were unchanged.

Preserved the entire original bundle and starting dirty source/config/docs/graph
state under `evidence/ndx/ndx-r0-20261014/`. Verified all 29 historical final-file
and 15 input hashes before copying; the new 347-file snapshot is identified by
[its manifest](ndx-strategy/evidence/2026-10-15/snapshot.json). Retention is on
Eros-backed NFS, as accepted by the owner, with no independently verified backup
or storage snapshot policy. The original bundle remains unchanged.

Added reusable offline commands in `butterfly_guy.research.ndx_evidence` and
`butterfly_guy.research.ndx_baseline`: explicit evidence/config/output paths,
hash/source checks, overwrite refusal, normalized complete observations, a
baseline-only replay, coverage/accounting/metrics outputs, environment and exact
commands. The [final contract](ndx-strategy/evidence/2026-10-15/r0-reproduction-final.json)
pins the source, dependencies, parent, assumptions and fixed tolerances. Bulk CSVs
and runs remain ignored. Use a new output path for every reproduction:

```bash
uv sync --frozen
uv run --offline --frozen python -m butterfly_guy.research.ndx_evidence verify \
  --evidence evidence/ndx/ndx-r0-20261014 \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/snapshot.json
uv run --offline --frozen python -m butterfly_guy.research.ndx_baseline \
  --evidence evidence/ndx/ndx-r0-20261014 \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/snapshot.json \
  --config docs/research/ndx-strategy/evidence/2026-10-15/r0-reproduction-final.json \
  --supplement evidence/ndx/ndx-01-supplement-20261015 \
  --supplement-manifest docs/research/ndx-strategy/evidence/2026-10-15/supplement-manifest.json \
  --output reports/research/ndx-01-20261015/my-new-reproduction
```

Final evidence is `reports/research/ndx-01-20261015/run-03/`;
[small versionable records](ndx-strategy/evidence/2026-10-15/summary.json) link to
[138 sessions](ndx-strategy/evidence/2026-10-15/sessions.jsonl) and
[all 113 trades](ndx-strategy/evidence/2026-10-15/coverage.jsonl).
Reproduced 514,551 groups / 4,377 incomplete exclusions / 510,174 complete marks,
53-trade +$9,254.84 recorded and −$30,978.16 stored stress, 51 resolved modern
baseline paths, and the 49/32 historical common/uninterrupted cohorts. Every
archived baseline row reconciles within predeclared numerical/timing tolerances.
No variants were rerun. The failed first port (post-close terminal-tick condition)
and the second reproduction remain preserved separately with source/contracts.

Trade 222 is isolated: logs indicate monitor state reinitialization below entry
with a retained peak, consistent with the historical restart bug that cleared
"ever in profit." Later complete marks never regain entry. R0 retains that state
and exits 1,144.244997 seconds early, adding $150 paper / $47 stress relative to
recorded settlement. Exact process cause/deployment history remains unattested.
Three other modern price differences (+$16, −$35, −$20) reconcile to signal-mark
paper fills versus later terminal diagnostics. There is no unexplained material
commission/rounding difference. Complete runtime parity remains unestablished;
see [the reconciliation report](ndx-strategy/NDX-01-reconciliation.md).

New read-only evidence inspected: original grouped observations and event logs;
Helios contract symbols, held-table identity/continuation bounds, settlement
source timestamps and August 6 state transitions; selected current NDX container
source/config/lock files and installed versions; and exact-symbol independent
minute-chain continuation counts. Host Git source, container source, local source
and historical replay dependencies are explicitly distinguished. No credentials
or environment secret values were inspected.

Eligibility: 53 selected-entry diagnostics; no full entry-opportunity set; 32
strictly complete resolved observed paths; zero eligible R0 post-exit paths;
49 attributable **paper proxy** settlements and zero verified official XQC
settlements. Ten early contract identities and 13 old settlement sources remain
missing. Held quote-event and availability timestamps were not stored. All 17
modern discretionary exits have recoverable independent minute observations,
which have not been imported, substituted, or declared replay-eligible. The
[recovery ledger](ndx-strategy/evidence/2026-10-15/recovery-ledger.jsonl) records
these distinctions per session. Missing/censored results remain null.

Verification: 44 focused/existing tests passed, including full-snapshot replay
with network sockets blocked and external commands restricted to local Git.
An isolated clone of starting HEAD plus the proposed files reproduced run-03
using explicit snapshot paths and the locked existing environment. Full repository
lint passed. A fresh empty-cache dependency installation was not repeated;
broker-connected tests and service restarts were unnecessary and not performed.
[Verification and graph refresh](ndx-strategy/evidence/2026-10-15/verification.json)
records final checks.

**Next bounded task: NDX-02**, audit signal versus diagnostic timing/prices and
mark-fallback execution stress on the 17 discretionary exits. Before evaluating
hold-after-exit rules, normalize the inventoried minute continuations into a new
snapshot with explicit cadence/gap/freshness eligibility. Do not optimize exits,
rerun rejected variants, or deploy. Official settlement acquisition and historical
full policy attribution remain separate evidence limitations.

### 2026-10-15 — NDX-02 bounded execution/accounting attribution

**Status: this execution/accounting portion complete; NDX-02 liquidity work is
not complete. Decision: refine data/execution evidence.** No strategy experiment,
parameter optimization, rejected-variant replay, runtime change, remote access,
credential inspection, order or deployment occurred. Existing dirty work and
historical artifacts were preserved. Accepted Eros retention still provides no
established independent backup.

Added the reusable offline `butterfly_guy.research.ndx_execution_audit` command,
[reconciliation and bounded execution-model specification](ndx-strategy/NDX-02-execution-accounting.md),
[command guide](ndx-strategy/NDX-02-reproduction.md), independent tests, and
[versionable per-trade ledger](ndx-strategy/evidence/2026-10-15/ndx02-execution-ledger.jsonl).
Final run: `reports/research/ndx-02-20261015/run-02/`; parent evidence remains
`reports/research/ndx-01-20261015/run-03/`. The new run retains its source,
contract, environment, exact invocation, input/source/config/output hashes,
Git identity/dirty status and correction-parent link.

Inspected and verified locally: all 347 files in `evidence/ndx/ndx-r0-20261014/`
(including raw trades/events/held paths); all four supplement files in
`evidence/ndx/ndx-01-supplement-20261015/`; both files in
`evidence/ndx/ndx-continuation-inventory-20261015/`; both saved runtime-source
files in `evidence/ndx/helios-ndx-source-20261015/` (including selected container
order-manager/position-service source); all 12 parent run outputs; and all 138
NDX-01 source pins against current HEAD `6a33d170c09f7ff68d7edb733b74c087b27c0227`.
Applicable manifests and current local source identity match. Saved October 15
container evidence is not a fresh server inspection or full historical runtime
attestation. No new continuation prices were inspected/imported/substituted.

The cohort is derived from closed `mark_v1` non-cash-settlement records, then
reconciled by ID/session/exit timestamp and identity with NDX-01 coverage and
inventory; the result is 17 trades, all quantity one. Predeclared tolerances
were fixed before assessment: 0.00011 unrounded points, 0.000001 rounded-price
points, $0.01 per trade and one microsecond for timestamp equality. Missing
signal/diagnostic quote times remain null; telemetry writes and final monitor
polls are not used to invent latency. See the immutable initial
[contract](ndx-strategy/evidence/2026-10-15/ndx02-execution-contract.json) and
[final revision](ndx-strategy/evidence/2026-10-15/ndx02-execution-final.json).

All 17 entry fills, 17 stored entry estimates, 17 stored exit estimates and
recorded P&Ls reconcile. Seven independent exit signal events reconcile to the
rounded paper fills; the other ten remain unknown against an independent signal
mark. Recorded P&L is **−$9,316**, stored stress **−$20,060**; entry drag **$9,017**
and exit drag **$1,727** independently explain the **$10,744** difference. Entry
median spread is 8.00 points (17 observations); exit median is 1.85 (16).
Trade 194 is the sole exit mark fallback (1/17); its bid/ask are missing and the
3.92 mark is supplied-mark fallback evidence, not a separately fetched quote.
No proceeds floor is exercised (0/17 exits; 0/53 modern context exits), but raw
negative bids and flooring are retained/countable and independently tested.
Embedded commissions/rounding are preserved; settlement has no closing fee.
The 53-trade context reproduces +$9,254.84 paper / −$30,978.16 stored stress.

Trades 294/306/316 independently verify signal marks 1.32/3.74/2.82 → paper fills
1.29/3.71/2.79 versus diagnostic marks 1.48/3.39/2.62. Using the diagnostics as
paper marks would change P&L by +$16/−$35/−$20, total −$39. This is observation
attribution, not another fee. All seven exit-event marks and fills agree within
the fixed tolerances. No available numerical check has an unresolved discrepancy.

Timing limitations: 17 recorded entry/exit fill timestamps and held-collection
bounds; seven attributable entry-selection collection/limit records and seven
independent exit signal-mark events. No independently recorded exit signal
observation time, paper-diagnostic collection time, constituent quote-event or
availability time. Seven exit-event writes follow fills by 11.814–93.679 ms;
`exit_signal_fired` writes occur before four fills and after three. Those are
write offsets, not fill latency. DB snapshot times/lags remain separately labelled.
Actual complex-order fills, size/capacity, partials/cancels/rejects, complete
historical deployment policy and official XQC remain unsupported evidence.

Exact final command (already executed; repeat only with a new output path):

```bash
uv run --offline --frozen python -m butterfly_guy.research.ndx_execution_audit \
  --evidence evidence/ndx/ndx-r0-20261014 \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/snapshot.json \
  --supplement evidence/ndx/ndx-01-supplement-20261015 \
  --supplement-manifest docs/research/ndx-strategy/evidence/2026-10-15/supplement-manifest.json \
  --inventory evidence/ndx/ndx-continuation-inventory-20261015 \
  --inventory-manifest docs/research/ndx-strategy/evidence/2026-10-15/continuation-inventory-manifest.json \
  --runtime-source evidence/ndx/helios-ndx-source-20261015 \
  --runtime-manifest docs/research/ndx-strategy/evidence/2026-10-15/runtime-source-manifest.json \
  --parent reports/research/ndx-01-20261015/run-03 \
  --config docs/research/ndx-strategy/evidence/2026-10-15/ndx02-execution-final.json \
  --source-lock docs/research/ndx-strategy/evidence/2026-10-15/ndx02-execution-source-lock-final.json \
  --previous-run reports/research/ndx-02-20261015/run-01 \
  --output reports/research/ndx-02-20261015/run-02
NDX_EXECUTION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014 \
NDX_SUPPLEMENT=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015 \
uv run --offline --frozen pytest tests/test_ndx_execution_audit.py \
  tests/test_ndx_baseline.py tests/test_state_machine.py tests/test_position_manager.py -q
uv run --offline --frozen ruff check .
/home/corey/.cache/uv/archive-v0/Yo1tT0lFfjWucooJ/bin/graphify update .
```

Verification: **57 passed** (13 audit, 44 existing), including full private-data
operation with network sockets blocked and subprocesses restricted to local Git.
Repository lint passed. Graphify AST update completed; missing optional SQL parser
and stale community labels remain graph limitations, not skipped Python accounting
checks. Run-01 remains preserved: the first full offline integration test exposed
`platform.platform()` spawning `uname`; run-02 uses process-free environment fields
and a new source lock/explicit correction-parent hash. Ledger and summary outputs
are byte-identical across runs. An initial fixture's exact binary-float comparison
was changed to `approx`; no production tolerances changed. No broker-connected
checks or fresh dependency installation were needed. See
[verification](ndx-strategy/evidence/2026-10-15/ndx02-verification.json).

**Exact next task:** register a new attributed continuation snapshot/cadence
contract, import original exact-symbol three-leg minute rows only in
`(recorded exit, regular close]` for this derived cohort, reconcile inventory
counts/bounds, and audit duplicates/incomplete/invalid legs, provider marks,
minute buckets, every adjacent interval, 30/60/90/120-second gaps, first/tail
coverage, timestamps/freshness and cross-source boundaries. Preserve raw negative
composite bids and missing times; no interpolation or R0 substitution. Publish
coverage/exclusions with R0 30-second continuation eligibility false. Any later
minute replay needs a separately specified causal signal/fill/gap policy and
eligibility decision. Do not evaluate holds or tune liquidity/exit thresholds
in the import audit. Full NDX-02 liquidity calibration remains open.

### 2026-10-15 — NDX-02 independent minute continuation import/cadence audit

**Status: bounded import/cadence/gap audit complete; causal replay eligibility
not established; full NDX-02 liquidity calibration remains open.** Decision:
refine constituent quote fidelity. No hold-after-exit evaluation, strategy P&L,
parameter search, rejected-variant replay, liquidity threshold selection or
runtime activation occurred. No credentials/account data or runtime settings
were inspected. Read-only SSH/psql acquisition was the only remote operation.
Accepted Eros retention still has no independently established backup.

Verified original R0/supplement/inventory manifests, NDX-02/run-02 outputs and
140 existing source pins before acquisition. Starting HEAD remains
`6a33d170c09f7ff68d7edb733b74c087b27c0227`; pre-existing dirty work is preserved.
Read the market-data, trading-strategy-research and VPS skills; confirmed Helios,
`/opt/butterflyguy`, healthy database container and sufficient local/remote disk.
A read-only schema extract established the actually available quote-event/age
columns and snapshot metadata table. No local continuation prices existed.

Registered the [initial pre-price contract](ndx-strategy/evidence/2026-10-15/ndx02-continuation-contract.json),
freezing cohort/symbols/strikes/dates from the verified execution ledger,
`(recorded exit, regular close]` windows, nominal 60-second cadence,
30/60/90/120-second gap diagnostics, microsecond timestamp reconciliation,
price tolerances and explicit R0/minute replay ineligibility. The first dynamic
symbol/time query exceeded its unchanged 60-second DB timeout; preserved its
header-only file, query, contract and failure manifest at
`evidence/ndx/ndx-minute-continuation-20261015/`. The
[revision contract](ndx-strategy/evidence/2026-10-15/ndx02-continuation-contract-v2.json)
adds literal session-expiration/time predicates for partition/index pruning and
links that failed attempt. No timing/price tolerance or timeout was widened.
Wrong-expiration database rows are outside the exact-expiration export scope;
the audit does not attest their absence elsewhere.

Successful new snapshot:
`evidence/ndx/ndx-minute-continuation-20261015-v2/`,
[11-file manifest](ndx-strategy/evidence/2026-10-15/ndx02-continuation-snapshot.json).
Read-only export ran 20:19:52.965265–20:20:00.296467 UTC on October 15 and retained
3,364 original quote rows, including invalid/incomplete candidates, original
sizes/timestamps and available snapshot timing metadata. Raw sources are
`option_chain_snapshots` and `chain_snapshot_meta`; timed source label is
`schwab_rest_option_chain`. Captured schema, frozen cohort, query, contract,
acquisition timestamps, preflight and raw hashes are retained. Source/input/
config/parent/output hashes and the observed environment are recorded in
`reports/research/ndx-02-continuation-20261015/run-01/run.json`.

Added reusable offline `butterfly_guy.research.ndx_continuation`, focused tests,
[findings/eligibility specification](ndx-strategy/NDX-02-continuation.md),
[reproduction guide](ndx-strategy/NDX-02-continuation-reproduction.md), and
[versionable coverage ledger](ndx-strategy/evidence/2026-10-15/ndx02-continuation-coverage.jsonl).
All 17 inventory memberships, counts and first/last timestamps reconcile.
There are 1,125 raw groups: **1,114 complete groups** and **11 incomplete two-leg
groups** (five on trade 317, six on 346). Original rows remain intact; no repairs,
interpolation, forward fills, clipping, invented timestamps or R0 substitutions.
No complete imported group has duplicate keys, wrong identity, nonfinite/crossed/
negative leg quotes or inconsistent metadata. Structural normalization does not
confer economic/replay eligibility.

Cadence: all 1,097 complete-group intervals exceed 60 seconds; median
**63.101178 s**, p95 **64.264143 s**, range **61.131032–264.102769 s**. Four gaps
exceed 90 and 120 seconds on 317/346, spanning incomplete groups. **67 of 1,171
full minute buckets** are missing; none is multiply occupied. Partial exit
minutes are separate. Exit-to-first collection is 4.189141–56.114927 seconds;
last collection-to-close is 7.437138–61.752376 seconds. Collection-source boundary
gaps are explicitly recorded and are not fill latency or constituent quote age.

Price/timing limits: **635 negative composite bids** and **157 negative provider
composite marks** remain signed; 816 provider marks differ from composite
bid/ask midpoints beyond 0.00011 points. Mark range is −13.97–10.04 points.
All 3,342 complete-group legs have displayed sizes, which do not prove complex
order execution/capacity. Timing metadata and constituent event/age evidence
exist on **148 complete groups / 444 legs**, across 339/343/346; **14 trades /
966 complete groups / 2,898 legs** lack them. Reported ages range
0.504256–269.157070 seconds; no freshness cutoff was selected. 145 events occur
after their snapshot's start-of-pass stamp but none after local fetch completion.
Recorded start-to-fetch-completion lag is 1.048414–2.789879 seconds. Scheduled,
publication, DB commit and consumer-availability times remain missing where not
recorded; no age/lag was used to invent one. This timing evidence belongs only to
this new source; earlier monitor/paper-diagnostic timestamps remain unavailable.

**Eligibility remains 0/17 for R0 continuation and 0/17 for minute replay.** R0
and all historical outputs are unchanged. Negative composite provider marks,
missing/incomplete groups, drifting cadence, partial constituent freshness and
unrecorded consumer availability require an explicit causal minute evidence
policy before economic interpretation. No official XQC evidence was acquired.

Exact offline command (already executed; repeat only with a new output path):

```bash
uv run --offline --frozen python -m butterfly_guy.research.ndx_continuation \
  --evidence evidence/ndx/ndx-minute-continuation-20261015-v2 \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/ndx02-continuation-snapshot.json \
  --inventory evidence/ndx/ndx-continuation-inventory-20261015 \
  --inventory-manifest docs/research/ndx-strategy/evidence/2026-10-15/continuation-inventory-manifest.json \
  --execution-parent reports/research/ndx-02-20261015/run-02 \
  --baseline-parent reports/research/ndx-01-20261015/run-03 \
  --config docs/research/ndx-strategy/evidence/2026-10-15/ndx02-continuation-contract-v2.json \
  --source-lock docs/research/ndx-strategy/evidence/2026-10-15/ndx02-continuation-source-lock.json \
  --output reports/research/ndx-02-continuation-20261015/run-01
NDX_CONTINUATION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-minute-continuation-20261015-v2 \
NDX_EXECUTION_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx \
NDX_EVIDENCE=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-r0-20261014 \
NDX_SUPPLEMENT=/mnt/Repos/Trading/Butterflyguy/evidence/ndx/ndx-01-supplement-20261015 \
uv run --offline --frozen pytest tests/test_ndx_continuation.py \
  tests/test_ndx_execution_audit.py tests/test_ndx_baseline.py \
  tests/test_state_machine.py tests/test_position_manager.py -q
uv run --offline --frozen ruff check .
/home/corey/.cache/uv/archive-v0/Yo1tT0lFfjWucooJ/bin/graphify update .
```

Verification: **72 passed** (15 continuation, previous 57); private snapshots
fully exercised with sockets blocked and subprocesses restricted to local Git.
Repository lint passed; graphify AST update completed with its optional SQL-parser
and stale community-label warnings. Final manifest/source/output and document-link
checks are in [verification](ndx-strategy/evidence/2026-10-15/ndx02-continuation-verification.json).
No new dependency installation or broker-connected tests were needed.

**Exact next task:** bounded constituent quote-quality attribution and causal
minute evidence specification. Attribute the 157 negative provider composite
marks and mark/midpoint differences to original legs and available event/age
metadata, beginning with 339/343/346. Explain what cannot be determined on the
14 untimed trades. Specify observation availability, cadence and gap/incomplete/
negative-mark treatment with independent fixtures before any economic evaluation,
or retain insufficient evidence. No hold-after-exit replay, parameter optimization,
P&L-selected thresholds, new capture-service activation or deployment in that task.
Full NDX-02 liquidity calibration remains incomplete.

### 2026-10-15 — NDX-02 constituent fidelity and causal-use specification

**Status: bounded attribution/specification complete; insufficient evidence for
causal replay; full liquidity calibration and strategy promotion incomplete.**
Added `butterfly_guy.research.ndx_quote_fidelity`, focused independent fixtures,
a second direct raw-JSON verification, machine-readable complete/leg/exclusion/
overlap/example ledgers, the [fidelity report](ndx-strategy/NDX-02-quote-fidelity.md),
[causal specification](ndx-strategy/NDX-02-causal-minute-specification.md) and
[reproduction guide](ndx-strategy/NDX-02-quote-fidelity-reproduction.md).

Starting HEAD `49da0284d24814ed2bc0838bbd543444b48019b9`, initially clean. Verified
all five local snapshot manifests, required inputs, all three frozen parents'
outputs and existing source pins before attribution; unchanged file hashes remain
valid across the newer checkout. Saved October 15 runtime source is an observation
of selected execution/position modules, not historical collector/gateway identity.
No original provider responses or complete per-session deployment history exist
in the inspected bundle. No additional acquisition or remote access was needed.

Immutable contract/source lock and frozen run:
`reports/research/ndx-02-fidelity-20261015/run-01/`. This adds no P&L or strategy
trial. It derives the 17-trade cohort from closed non-settled `mark_v1` records,
rebuilds 1,114 complete groups and eleven excluded groups (22 retained legs),
reconciles the inventory/parent records, and independently computes decimal
constituent/composite prices without clipping or replacement. Reporting tolerances
remain 0.00011 points and one microsecond. A predeclared 0.005-point individual
rounding-compatibility bound is a precision diagnostic, not a trading filter.

Findings: 157 negative marks, 635 negative bids, 816 reportable midpoint
differences; **103** observations overlap the negative-mark/difference sets.
None of 3,342 complete-group leg marks is outside its recorded market. All leg
mark/midpoint residuals are within ±0.005 points; weighted residuals exactly
explain composite discrepancies of −0.015 to +0.020 points. This is consistent
with cent rounding but does not prove the provider's implementation. The same
157 groups have negative midpoints independently of rounding. Negative composites
are attributable to recorded cross-strike prices, not to negative individual
marks; signed cost-to-close diagnostics remain signed.

Timed subset: 148 groups / 444 legs on 339/343/346, 12 negative marks, 105
midpoint differences, eight overlapping mark anomalies. Untimed subset: 966
groups / 2,898 legs on 14 trades, 145 negatives, 711 differences, 95 overlapping.
Event dispersion 0.001–268.471 seconds, median 9.378, p95 138.629; oldest reported
leg age maximum 269.157070 seconds. 145 events follow pass start, zero follow
local fetch completion. Age-reference semantics and clock synchronization remain
unattested. Chain-wide stale flags cannot identify individual selected stale legs.
No consumer availability is recorded; no age subtraction invents a timestamp.
Existing cadence gaps, incomplete groups and all-17 ineligibility remain intact.

Source trace: local collector forwards marks, gateway adapter validates/copies
individual markets and maps clocks, database copies supplied columns, metadata
writes are separate, and unaligned collection sleeps after work. These are
possible mechanisms, not proof of a historical deployment. Saved container tar
contains no collector/provider/database insertion source or gateway implementation.
Provider fault, upstream normalization, timing causation, historical adapter and
per-trade deployment remain unresolved. No clean/fresh assumption is assigned
to the 14 untimed trades. Raw snapshots and all failed/superseded parents remain
unchanged. Eros retention still has no established independent backup.

Exact executed audit command (choose a new output for repetition):

```bash
uv run --offline --frozen python -m butterfly_guy.research.ndx_quote_fidelity \
  --evidence-root evidence/ndx \
  --manifest docs/research/ndx-strategy/evidence/2026-10-15/ndx02-continuation-snapshot.json \
  --continuation-parent reports/research/ndx-02-continuation-20261015/run-01 \
  --execution-parent reports/research/ndx-02-20261015/run-02 \
  --baseline-parent reports/research/ndx-01-20261015/run-03 \
  --config docs/research/ndx-strategy/evidence/2026-10-15/ndx02-fidelity-contract.json \
  --source-lock docs/research/ndx-strategy/evidence/2026-10-15/ndx02-fidelity-source-lock.json \
  --output reports/research/ndx-02-fidelity-20261015/run-01
```

Verification: **82 passed, zero skipped** with all private-snapshot environment
variables set (ten new fidelity/raw checks plus the prior 72). Repository lint
and `git diff --check` passed. Graphify AST update completed; optional SQL parser
is unavailable and community labels require a separate semantic refresh. No
broker-connected tests or fresh dependency installation were needed.

Full verification command and environment paths are in the reproduction guide;
[verification](ndx-strategy/evidence/2026-10-15/ndx02-fidelity-verification.json)
preserves results and source/output hashes. Initial fixture development found a
missing-symbol root-extraction `IndexError` (four failures); fixed before the
source lock and first audit run. Eight unit fixtures then passed with the private
check explicitly skipped; full private verification subsequently passed. No
failed frozen fidelity run or overwritten contract/source lock was needed.

**Exact next action:** specify prospective provenance fields and storage/receipt
semantics with fixtures and explicit feasibility; do not activate acquisition.
Current evidence fails the proposed causal availability contract for all 17
trades. No new strategy P&L, exit replay, thresholds, orders, runtime settings,
credentials, services or deployments were changed.


## 2026-10-15 — Prospective provenance contract and offline checker

The bounded specification portion is complete; instrumentation and full NDX-02
remain pending. See [specification/feasibility](ndx-strategy/NDX-02-prospective-provenance.md),
[reproduction](ndx-strategy/NDX-02-provenance-reproduction.md) and
[Stages B–G](ndx-strategy/NDX-remaining-roadmap.md). Registered inputs are in
`docs/research/ndx-strategy/provenance-v1/`; frozen private run is
`reports/research/ndx-02-provenance-20261015/run-01/`. Small run, summary and
verification copies are under `ndx-strategy/evidence/2026-10-15/ndx02-provenance-*`.

Starting HEAD `49da0284d24814ed2bc0838bbd543444b48019b9`, with existing dirty
fidelity, living-plan/index and graph work preserved. New source is
`src/butterfly_guy/research/ndx_provenance.py`; focused checks are
`tests/test_ndx_provenance.py`. Source/config/fixture/schema/parent hashes and
Python/dependency/platform identities are recorded in run.json and source-lock.json.
The command verifies all five private snapshots, required manifest membership,
four frozen parents and source pins using existing verification functions.

All twelve requested fixture scenarios are covered by 18 synthetic records:
six sufficient asserted receipt chains, eight insufficient and four rejected.
Sufficiency concerns the receipt record only. Every result has false freshness
and replay eligibility, null earliest availability and no decision/fill. The
historical-shaped fixture is explicitly synthetic. No new historical cohort,
physical timing bound, liquidity threshold or P&L is created. Current source
shows separate quote and metadata writes; proposed complete publication is not
implemented in the collector or database. Cross-domain causal ordering remains
conservatively insufficient. All 17 historical paths remain ineligible.

Verification: 31 new checks and the prior 82 private-enabled checks pass; exact
combined check, lint, diff and graph results are recorded in the new verification
record. Original responses, historical age/clock semantics, consumer receipts,
full producer deployments, actual complex-order evidence and official XQC remain
missing. Eros retention is unchanged; independent backup remains unestablished.
Preparatory Path-type/lint corrections occurred before contract registration;
no frozen provenance run failed or was overwritten. Previous failed/superseded
extractions and runs remain untouched.

**Exact next bounded action:** review v1 meanings, DB complete-snapshot protocol,
upstream ownership, safe response boundary and resource/retention requirements;
then request separately scoped Stage B implementation of the smallest recording
diff with isolated failure tests and an activation/rollback plan. This task did
not authorize capture activation, migrations, service operations, economic
experiments or promotion. NDX-03 requires the full opportunity/skip set and its
own research instruction; later gates remain as documented in the roadmap.


## 2026-10-15 — Stage B local recording implementation and source review

Reviewable preparation is implemented in
`src/butterfly_guy/research/ndx_recording.py`, `tools/check_ndx_recording.py` and
`tests/test_ndx_recording.py`. The standalone research SQLite schema is outside
runtime migrations. Existing collector/providers/queries and all prior source
pins are unchanged. Read the
[implementation/reproduction/activation checklist](ndx-strategy/NDX-02-recording-implementation.md)
and [pinned upstream supplement](ndx-strategy/NDX-02-recording-upstream-review.md).
Full Stage B integration/activation and full NDX-02 remain incomplete.

The recorder publishes copied quote/provenance/manifest rows in one transaction,
observes commit acknowledgement only afterward, reads one exact complete snapshot,
then records actual consumer receipt. Missing bytes/clock evidence and lost ack
remain unknown. Duplicate deliveries refuse overwrite; corrections require a
previous provenance hash. Failure/drop evidence stays separate from quote presence.
No automatic pruning or trading coupling is introduced. There is no active bot
import, broker call, migration against live DBs, observer or deployment.

The source-locked run-02 used 25 entirely synthetic observations on local tmpfs;
all published and journaled receipt. Closed DB size was 446,464 bytes, total measured
publish/read CPU 0.0484 s, p95 wall time 0.002153 s. These small selected-leg samples
exclude export writes and cannot establish production budgets, native full-chain
capacity, TimescaleDB behavior or NFS durability. The checkout is nfs4; closed
run artifacts were copied and hash-verified under
`reports/research/ndx-02-recording-20261015/run-02/`. Do not operate a shared
live SQLite journal on this NFS archive. Independent backup remains unestablished.

Registered config/source locks and synthetic inputs are in
`docs/research/ndx-strategy/recording-v1/`. Run-01 and its original files remain
unchanged; run-02 links/verifies it as a correction parent after test-only lint
line wrapping, correction-parent verification and documentation updates. Recording
semantics did not change. Starting HEAD remains
`49da0284d24814ed2bc0838bbd543444b48019b9`; all earlier dirty work is preserved.
Exact invocation and source/input/output/environment identities are in each
run.json. Small run/summary/verification copies use `ndx02-recording-*` under
the October 15 versioned evidence directory.

Verification: **136 passed, zero skipped** with private evidence enabled (23 real
SQLite recording checks plus the prior 113). Tests include actual metadata/commit
failure rollback, cross-connection invisibility, append-only constraints, lost
post-commit acknowledgement, receipt/failure-journal failure, restart, correction
parents and an abruptly exiting child process before COMMIT. Ruff and whitespace
checks pass; graphify AST update completed with optional SQL parser and stale-label
limitations. PostgreSQL/TimescaleDB tests were not run: no local executables or
running Docker daemon were available. No daemon was started or packages installed.

Read-only Git inspection of SchwabGateway's ButterflyGuy-pinned revision
`0d0125e51266740de0f43c72b540002a4dcfc25d` established a prospective code-level
age formula and cache refresh behavior. Event selection takes the latest positive
quote/trade epoch-millisecond field; age is max(0, reference-event). Cache hits
recompute age at a new gateway evaluation instant while retaining the original
gateway receipt. The exact reference must be recorded separately. This is not
historical server/deployment or synchronization evidence and does not repair
any of the 17 ineligible historical paths. The other repository was not modified.

**Exact next bounded action:** implement/review the actual native-response boundary
and target DB/consumer adapter with explicit reference/build/cache provenance;
validate on isolated target storage with real-size inputs and resource/drop budgets.
No capture activation is ready for approval yet. A named-target preflight,
concrete release/rollback plan and separate operational authorization still precede
activation. Economic stages and the full opportunity-set requirement remain gated.


## 2026-10-15 — Native gateway preservation and asyncpg research integration

The [native/PG implementation record](ndx-strategy/NDX-02-native-postgres-integration.md)
owns the protocol, reproduction, target-engine limits and next gates. New files:
`src/butterfly_guy/research/ndx_native_response.py`,
`src/butterfly_guy/research/ndx_postgres_recording.py`,
`tools/check_ndx_postgres_recording.py` and the two corresponding new test files.
SQL, native synthetic fixture/universe, body schema and preregistered contract/
source lock are under `docs/research/ndx-strategy/postgres-v1/`. No previously
frozen source/contract/output or other-repository file was rewritten.

The existing pinned SDK supports client= injection. The optional research HTTP
client therefore preserves its normal buffered GET response before SDK parsing,
without modifying the SDK, making another request, or changing active bot wiring.
Only the successful native option-chain schema is accepted; unknown/sensitive
fields, duplicate JSON keys, wrong identities and unbuffered/oversized responses
refuse recording. Original buffered gateway body bytes, including lexical number
precision, remain intact. This is gateway-normalized HTTP-decoded body scope,
not original provider wire data. Missing multiplier/flags/age-reference remain
missing; chain flags do not label selected legs. Recording failures are counted/
journaled separately while the SDK receives its unchanged response. Cancellation
propagates. Recording is awaited only on this explicit research path; it is not
approved as an inline delay on the trading path.

The asyncpg adapter writes selected quote copies, producer metadata/BYTEA body
and a complete manifest in one real PostgreSQL transaction. Schema installation
is explicit, additive and outside automatic runtime migrations. Publication binds
installation UUID, actual transaction ID, exact snapshot/version/symbols and
content hashes. Acknowledgement is observed only after COMMIT returns; consumer
read/receipt and persistence are separate. One exact-key joined SQL statement
reads the complete committed snapshot and observed acknowledgement consistently.
A lost COMMIT reply produces unknown outcome until recovery observes publication
presence; it does not invent a past commit acknowledgement. All results retain
insufficient evidence, false replay eligibility and no decision/fill.

Temporary test-only pgserver==0.1.4 executables supplied PostgreSQL 16.2. Python
3.13 package resolution was unsupported, so a separate Python 3.12 uv environment
was used; project dependency files/pins are unchanged. All test clusters were
new private /tmp Unix-socket instances with TCP disabled and were stopped explicitly.
No Docker/system/remote service was started or changed. Cluster/logs are retained.
The TimescaleDB extension was not present, so deployment-version/extension/pool/
role/load parity remains unverified. Actual source and timing evidence are not
inferred from this test engine.

Frozen synthetic resource run:
`reports/research/ndx-02-native-postgres-20261015/run-01/`, copied byte-for-byte from
its closed local /tmp output with all output hashes verified. Five small native
4-contract responses and three 5,000-contract responses all completed SDK → PG
publication → receipt, using one mock HTTP GET per sample and real local DB I/O.
The larger bodies were 1,295,450 bytes; maximum measured complete cycle was
0.317701 s, versus 0.011259 s for the small body. Peak Python RSS was 77,392 KiB;
DB growth 352,256 bytes reflects compressible synthetic content and is not a real
retention estimate. Export writes are excluded. No production latency/resource
budget or trading-path coupling is approved by these measurements. No new market
coverage or strategy economics are produced.

Run artifacts preserve a custom-format research-schema pg_dump, exact native body
and receipt/manifest samples, source copies, invocation, UTC/environment/dependencies,
PostgreSQL binary hashes/version, parent/input/config/source/output hashes and
recovery inventory. Small run/summary/verification copies use
`ndx02-native-postgres-*` in the October 15 versioned evidence directory. Starting
Git SHA is still `49da0284d24814ed2bc0838bbd543444b48019b9`, with earlier dirty
work preserved. No frozen native/PG run failed or was overwritten. Preparatory
line-wrap/import lint corrections occurred before registration.

Verification: **164 passed, zero skipped** in the combined private-enabled suite
(28 new native/real-PG checks plus the prior 136). Checks include deferred server
COMMIT failure, actual backend termination before commit, cross-connection
uncommitted invisibility, lost acknowledgement/receipt, append-only/TRUNCATE refusal,
correction/schema identity, injected COMMIT-reply loss after a real commit and
end-to-end pinned SDK/body roundtrip. Repository Ruff and whitespace checks pass;
AST graph refresh completed with the documented optional SQL-parser/stale-label
limitations. Frozen SDK schema, source/config and archived run outputs match hashes.

**Exact next bounded action:** establish the intended deployed TimescaleDB version
read-only and validate the additive schema/permissions/adapter on an isolated
matching environment; prepare a default-off research observer factory with bounded
pool/drop accounting, explicit capture universe/window, real resource/retention
budgets and release/rollback validation. Upstream original-provider body, actual
freshness-reference instant, gateway build and clock synchronization remain
unattested; preserve unknowns until separately evidenced. Named-target live DDL,
capture activation, service changes and later economic research still require
their scoped authorization. All 17 historical continuation paths remain ineligible;
full NDX-02 and NDX-03–06 are not complete. Eros archival retention is preserved;
independent backup remains unestablished.


### Post-registration target identity supplement

Read-only Helios metadata subsequently confirmed hostname/repository and a healthy
`butterfly_timescaledb` using `timescale/timescaledb:latest-pg16`. Inside an explicit
READ ONLY transaction with a 5 s timeout, version metadata reported PostgreSQL
**16.11** and TimescaleDB **2.25.2**. Running image ID/RepoDigest was
`sha256:0af03ecf697825f6ddae76fd275d16bf46007bed6d00eb3d754779cb7db96fa6`.
The [target record](ndx-strategy/evidence/2026-10-15/ndx02-native-postgres-target-readonly.json)
preserves exact scope/SQL and distinguishes this observation from engine testing.
No credentials, market data, positions/orders, application release or migration
state were inspected; this was not a full activation preflight. No DDL/DML,
capture, service restart or deployment occurred. The remaining compatibility
check is now specifically an **isolated instance of that observed image**,
not a mutation of the live container. Current local tests remain PostgreSQL 16.2
without the extension; the read-only observation does not retroactively validate
the target image or alter any frozen run/config/source lock.

## Default-off observer implementation and exact-target gate — 2026-10-15

Implemented `research/ndx_observer.py` and `ndx_observer_cli.py` as a separate,
caller-driven, one-acquisition consumer. Default-off factory/CLI do not read
secrets/context, connect, request, parse/copy or start workers. Enabled research
uses the pinned SDK's client injection and existing native/asyncpg protocols,
with no active trading-path import, polling, retry or queue. Explicit identities,
calendar close and build/config artifact hashes precede acquisition. One leased
observer per research DB admits one request and uses a separate max-three pool;
body/storage pause and lifecycle time budgets are resource proposals, not strategy
thresholds. HTTP buffering and synchronous parsing remain outside hard async/body
allocation bounds; busy/journal-failed memory counters cannot prove completeness
across a crash.

The [review package](ndx-strategy/NDX-02-timescale-observer-review.md) contains
NOLOGIN ownership/recorder/reader grants outside automatic migrations, the disabled
review-only overlay, one-shot traffic scope, drop/recovery definitions, retention/
restore and startup/validation/rollback procedures. Operational target identities,
current release/image/health/disk/positions/orders, independent backup, storage
quota/reserve, target capacity/restore and missing upstream facts remain open.
No current operational preflight or activation approval is claimed or requested.

Parent output hashes, required private snapshot membership (347/4/2/2/11 files),
applicable source pins and retained upstream source copies verified. Extending
`tests/test_ndx_postgres_recording.py` for the task-owned exact-image fixture is
explicit drift from the old postgres-v1 test pin; its archived original remains
available. All earlier contracts/source locks/evidence stay unchanged. Observer-v1
resource run-01 failed at helper import before starting a DB/request. It and the
original source copies were preserved; revision 2 preregistered the invocation
path correction before successful resource evaluation. The correction changes
verification helper loading only. A preparatory restart test's subprocess pipe
capture timeout was corrected before registration by directing server output to
the owned fixture log; its subsequent focused suite passed all 22 checks.

Verification: full private-enabled native/PostgreSQL/observer/provenance/fidelity/
continuation/accounting/baseline/state/position suite **186 passed, zero skipped,
28.99 s**. The 22 new observer checks cover disabled factory/CLI, explicit identity,
restricted roles, one-request success, duplicate/refused correction, native/SDK
rejection, oversized/busy/storage admission, unavailable gateway/DB/journal,
pool/lock pressure, bounded pending shutdown/cancellation, hard observer-process
crash, dead-lease refusal, real owned-DB restart and reconnect/reconciliation.
Repository ruff and whitespace checks passed. Graphify AST refresh completed:
10,697 nodes, 23,345 edges, 374 communities; optional SQL parser absent (24 SQL
files omitted), three symbol-free files, 58 unclassified files and stale community
labels disclosed. No semantic/API work or parser installation occurred.

Both exact-target runs preserved an **incomplete** gate at Docker version lookup:
no running local daemon/socket. Zero target tests executed; this is not a skipped
fixture counted as a pass, a failed image pull, resolved manifest or extension
proof. No fixture container was created. The harness pins the observed repository
digest/amd64 identity, verifies actual PG 16.11/TimescaleDB 2.25.2 in every new test
DB, and will run the actual adapter/role/lifecycle checks only on that isolated
image. It never substitutes plain PG for the exact-target gate.

Independent resource run-02 used a new private Unix-socket-only local /tmp PG 16.2
cluster, then stopped it before archiving outputs on Eros. Twelve synthetic SDK/
observer acquisitions: nine publications, nine acknowledgements and nine consumer
receipts; three oversized-recording rejections with SDK success retained. Twelve
additional SDK-only baseline calls were timed separately. Varied 5,000-contract
body: 1,800,259 bytes; full cycle max 0.376067 s versus SDK-only max 0.060684 s.
Exact 2,097,152-byte padded body accepted; one byte over rejected for preservation.
Peak retained recording body 2 MiB, zero queued items, two sampled connections
(max allowed three), Python process peak RSS 117,916 KiB, DB growth 1,843,200 bytes,
clean shutdown max 0.003850 s. DB CPU/RSS are endpoint samples, not peaks; padding
and seeded random flag/price variation do not establish real compression, durable
storage, production throughput or a safe trading delay. No economic result follows.

Immutable bulk archive:
`reports/research/ndx-02-observer-20261015/{target-run-01,target-run-02,resources-run-01,resources-run-02}/`.
All copies and run output hashes verified. Versioned summary/run/verification
records are `ndx-strategy/evidence/2026-10-15/ndx02-observer-*.json`.
Read the [revision-2 commands](ndx-strategy/observer-v1/REVISION-2.md); use **new**
output directories. The exact next command, after providing an available isolated
runtime, is:

```bash
uv run --offline --frozen python tools/check_ndx_timescale.py \
  --config docs/research/ndx-strategy/observer-v1/contract-v2.json \
  --source-lock docs/research/ndx-strategy/observer-v1/source-lock-v2.json \
  --output /tmp/ndx-timescale-observer-target/run-04
```

Overall stage remains incomplete. All 17 historical paths remain ineligible;
full NDX-02, actual complex execution/XQC and NDX-03–06 retain their separate gates.
No live DDL/grants, capture, service change, credentials, account/routing/limit
change, order, paper observation, new P&L or exit-variant experiment occurred.


### Exact-target verification retry — run-03

Retried the unchanged revision-2 harness after the owner requested verification
again. Source/config and all parent output hashes passed. Docker version lookup
still failed because `/var/run/docker.sock` does not exist; no image pull,
container creation or target tests occurred. No alternative supported isolated
runtime was established. The stage remains incomplete; no daemon or live service
was started. Closed run-03 was archived with byte-for-byte and manifest verification
at `reports/research/ndx-02-observer-20261015/target-run-03/`; see
[the retry record](ndx-strategy/evidence/2026-10-15/ndx02-observer-target-retry-03.json).
Next attempt must use a new `run-04` output after a supported isolated runtime
is available. Prior 186-test and resource results are unchanged, not rerun here.


### Exact-image validation passed — run-04

After the owner explicitly authorized starting local Docker, `systemctl start
docker` succeeded and the unchanged revision-2 exact-image harness completed.
The pinned digest/amd64 identity resolved; server PG 16.11 and extension 2.25.2
were verified, including each newly created test DB. Native/adapter/observer
checks passed **50 tests, zero failures/errors/skips in 12.41 s**. Restricted-role
publication/receipt, transaction/MVCC/commit-fault, immutable/duplicate/correction,
crash/restart/reconnect, bounded resources and disabled construction checks passed.
The 50 are a subset rerun of the earlier 186, not additional unique coverage.

The task-owned container was confirmed stopped, with no network exposure and
registered resource limits; local Docker remains running as authorized. Helios
was not contacted or changed. Run-04 source/config/parent/output and archive-copy
hashes verified. See [the exact-image supplement](ndx-strategy/observer-v1/EXACT-TARGET-RUN-04.md)
and [versioned verification](ndx-strategy/evidence/2026-10-15/ndx02-observer-target-verification-04.json).
Closed evidence is `reports/research/ndx-02-observer-20261015/target-run-04/`.
Earlier unavailable-runtime and failed resource records remain unchanged.

The runtime/image compatibility blocker is resolved. Target resource/restore
validation, storage reserve/quota and current named-target operational preflight
remain before activation review can be called ready. The old implementation
review's unavailable-runtime section is historical and superseded by run-04.
Capture and live DDL/grants remain disabled; no strategy, routing, account, token,
limit, fill, historical eligibility or economic-experiment change occurred.


## Exact-target resources, restore and runtime artifact — 2026-10-15

Completed the next authorized local preparation and read-only operational review.
The [final review](ndx-strategy/NDX-02-observer-operational-review.md) and
[verification record](ndx-strategy/evidence/2026-10-15/ndx02-observer-target-resource-restore-verification.json)
are the current handoff. Earlier packages remain immutable and their limitations
are not silently rewritten.

The resource fixture exposed a weakness in the first exact harness: it could run
checks on a temporary bootstrap server while image initialization failed its
psql socket. Resource run-01 and compatibility run-05 were stopped and archived.
Exact-image entrypoint source shows PGHOST is deliberately cleared; preserving
the default container-only socket alongside /socket fixed initialization. Run-06
then reached the final server but had 20 passing tests and 30 setup errors because
fully initialized template1 already includes TimescaleDB. The fixture now uses
IF NOT EXISTS followed by strict PG/extension version assertions. Registered
observer-target-v1 revisions 1–4 preserve each parent/correction and source copy;
no quote, permission or evidence constraint was weakened.

Final compatibility run-07 passed 50 tests with zero failures/errors/skips in
6.36 s on a fully initialized exact image. Target resource/restore run-02 passed:
12 synthetic acquisitions, nine publications/acks/receipts and three oversized
recording rejections preserving SDK success; nine original publications restored
byte-for-byte with complete table/journal/installation fingerprints unchanged,
nine new restricted-reader receipts, original acknowledgement stamps/counts
preserved, and one intentionally unpublished synthetic attempt still unresolved.
Dump 1,165,646 bytes; export 1.098118 s; restore 0.228080 s. Varied 5,000-contract
full cycle max 0.375659 s; Python peak RSS 112,556 KiB; DB growth 1,818,624 bytes.
Namespaced backend CPU/RSS are endpoint samples, not production peaks. Same-
container tmpfs restore is not independent backup or production capacity. All
new fixture containers were stopped.

A separate default-off Dockerfile fixes missing SQL asset/source-root packaging
without altering the active app image or configs. A source-only 164-file/2.39 MB
staged build produced local immutable image
`sha256:e55ee57b97aa8a1a624677876853574831fb83f8b6ea77bf1ca8228978669a99`.
Two bounded disabled checks and one enabled synthetic mock-SDK-to-target check
passed in that actual image under UID 1001/Python 3.12.15. The enabled check made
exactly one synthetic GET, published/read/recorded receipt under the restricted
role and preserved exact body/-4.0200 arithmetic with replay eligibility false.
Unsupported legacy-builder flag and interrupted broad-context attempts remain
archived; no project dependency lock or source strategy changed. The image was
not pushed, transferred, deployed or enabled on Helios.

Read-only Helios review: /opt/butterflyguy main HEAD 288d6cb321e611a94acc819fa96fc5e429ff836e
with existing tracked source/config edits preserved; this does not attest app
image source. Current NDX infra/app_ndx image 1fbc1ab3aed0aec85bcccab9e5009679789baab10fc333cfd0e4636ef1e7cc61
was running on loopback 8001; DB monitoring/timescaledb matches the tested image.
All three strategy health/readiness endpoints returned 200. DB OPEN trades and
nonterminal intents were zero, observer schema/roles absent, matching observer
CLI process count zero. NDX-only recent log summary: 11 lines, zero errors or
warnings, no raw messages retained. An earlier SPX log read timeout and missing
app-healthcheck template diagnostics are preserved. Broker positions/orders are
not verified: the existing helper can refresh/write tokens and was not invoked
under the no-token-change constraint. No live DDL/DML, token/account access,
real market request, service restart or capture occurred.

Closed evidence is under reports/research/ndx-02-observer-20261015/: target-run-05/06/07,
target-resources-restore-run-01/02, target-entrypoint-source-review/run-01,
image-build-run-01/02/03, image-enabled-smoke-run-01 and helios-readonly-review-run-01/02.
All manifest members and archive copies verify. Existing Eros retention remains
accepted; independent backup unestablished. Use observer-target-v1/contract-v4.json
and source-lock-v4.json for any new target runs, with new output directories.
Overall activation remains incomplete pending the named decisions in the final
review. All 17 historical paths, full NDX-02 and NDX-03–06 retain their gates.


### Authorized read-only broker audit — 2026-10-16 05:50 UTC

After Corey explicitly approved the audit including normal token refresh, the
existing helper ran through the NDX container's configured environment. Deployed
read-method source was checked first; transient pool settings forced DB sessions
read-only, and redacted output suppressed all raw logs/account/auth context.
The audit passed: zero SPX/NDX/XSP option positions, zero returned orders for its
October 16 entry-date window, zero OPEN DB trades and zero nonterminal intents.
One normal token-write callback was invoked; no token values were inspected and
no manual rotation or reauthorization occurred. This does not prove that all
older/GTC orders are absent. The helper's exact original date arguments and the
scope limit are recorded, without invented timezone attribution.

See the [broker supplement](ndx-strategy/NDX-02-observer-broker-flatness.md) and
[versioned redacted audit](ndx-strategy/evidence/2026-10-15/ndx02-observer-broker-flatness-20261016T0550Z.json).
Closed source/probe/wrapper/output hashes verified under
reports/research/ndx-02-observer-20261015/broker-flatness-run-01/. No orders, live
DDL/grants, market capture, deployment or service restart occurred. Next: finalize
the concrete one-shot real context and release/role/secret/connectivity/storage
choices before separately scoped live schema/capture approval. Earlier read-only
reviews and test records remain immutable; no Python source changed this step.

### Concrete observer activation proposal — 2026-10-16 15:56 UTC

Prepared [observer-activation-v1](ndx-strategy/observer-activation-v1/README.md)
with a real preselected three-leg context for NDX paper trade 355, immutable
observer image ID, policy digest, disabled standalone Compose, proposed dedicated
login/key references, verified network aliases and explicit admission/rollback.
The deployed calendar returned 20:00 UTC cash close. Context constructor, identity,
source/policy hashes and Compose static validation pass; no code changed.

Read-only Helios evidence now shows trade 355 OPEN, entered 14:00:15 UTC. This
supersedes the earlier DB-flat snapshot. Broker state was not queried again;
no fresh broker-flat claim is made. Live changes remain on hold pending a safe
fresh preflight, named approval and reviewed storage/backup and provisioning.
This session-specific context expires at close and must never be automatically
rolled over or replayed later. No gateway capture, orders, live DDL/grants,
credentials, image transfer or service restart occurred. Historical research
eligibility and all later NDX gates remain unchanged.

### Authorized disabled Helios installation — 2026-10-17 UTC

Corey approved the named weekend preparation. The
[installation record](ndx-strategy/observer-weekend-install-v1/README.md) binds
preflight/broker audit, transactional research-only DDL and new restricted login,
private new credentials, verified image transfer/load, actual disabled Compose
execution and read-only connectivity/permission checks. Postflight confirms
unchanged image/start identities for all trading apps and gateway, healthy app
endpoints and zero active observer containers. No market capture ran and the
expired context was not installed. Research evidence tables remain empty.

Free disk after image/archive retention: 20.62 GB; observed WAL 512 MiB before
installation. Empty research schema/identity export is hash-verified in the
accepted Eros-backed archive, not an independent full DB backup. No retention
cleanup or unlimited collection was enabled. The fresh broker helper audit
passed its tracked-root/current-day scope; older GTC orders remain outside it.

The dedicated background/read-only gateway key is generated and its proposed
merged principal validates, but the live registry is unchanged. The deployed
authenticator loads once; registering this new key and restarting the separately
named gateway still requires approval. See the concrete gateway restart review.
No existing credential was rotated, no existing service restarted, and no remote
Git/configuration dirt was changed. A fresh market-session context and capture
approval remain necessary after gateway registration. Historical eligibility
and later research gates remain unchanged.
