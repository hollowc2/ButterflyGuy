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

**Next action: bounded constituent quote-quality attribution and causal minute
evidence specification.** Attribute the 157 negative composite marks and
provider-mark/midpoint differences, beginning with the timed subset 339/343/346;
state what remains unknowable for the 14 untimed trades. Specify evidence-based
availability, cadence and gap/quality treatment before any economic evaluation.
Do not test hold-after-exit rules, optimize parameters, rerun rejected settings,
select thresholds from P&L or deploy. Full NDX-02 liquidity calibration remains open.

Use the [detailed next-session prompt](ndx-strategy/NEXT-STEP-PROMPT.md) to carry
out that bounded task; it is an instruction, not a completed audit or permission
to begin economic replay.

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
