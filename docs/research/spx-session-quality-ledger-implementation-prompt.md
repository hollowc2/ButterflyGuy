# Implementation prompt: SPX session quality and exclusion ledger

Implement the next historical-data-management step for ButterflyGuy: a repeatable,
offline SPXW 0-DTE session ledger that consolidates existing inventory, eligibility,
exclusion, and quality evidence. Complete the implementation, focused tests, and
generation of both real-data ledgers. Do not stop at a proposal.

The user authorized data organization and cleaning work. This task makes existing
evidence queryable; it does not authorize changing trading behavior, downloading
more history, changing quality thresholds, or running another strategy experiment.

## Read first and establish the checkout

1. Read `AGENTS.md`, `README.md`, `docs/data-management.md`, and the
   `market-data-operations` skill. Follow the repository's graphify instructions
   before making architecture decisions and after changing repository code.
2. Read `docs/research/thetadata-backtesting-completion-2026-10-01.md`.
   The earlier readiness document is historical; its execution follow-through
   points to the completed durable workflow.
3. Inspect Git status, branch, and available worktrees. The inventory documentation
   was committed as `0a3e4b3` on `feat/weekend-review-executable-pnl` and pushed.
   That active checkout has unrelated dirty files and may lack the research package.
4. Use a new isolated implementation worktree/branch from a verified revision
   containing the canonical research package, normally current `origin/main`.
   The existing `.worktrees/thetadata-readiness-2026-10-01` is the frozen execution
   checkout at `02cdec7`; inspect it as a reference, do not edit it. Preserve the
   active checkout, all frozen worktrees, and existing research records. Carry the
   inventory documentation into the new branch if it is absent from its base.
5. State a brief plan naming the implementation location and verification target.
   Use existing research CLI, dataset, calendar, quality, and artifact conventions.
   Do not create a second importer, pricing engine, or general data platform.

## Existing inputs

Repository root in this session:
`/mnt/Repos/Trading/Butterflyguy`.

The private inventory snapshot is:
`reports/data_management/2026-10-01/inventory.json`.
`checksums.json` in that directory checks the inventory artifacts. Remote metadata
is recorded in `helios-database.json` and `helios-files.json`; those do not prove
continuous or backtest-ready remote coverage.

The durable evidence root is:
`reports/thetadata_completion/2026-10-01/`.
The normalized cache beneath it is `thetadata-cache/`. The canonical inputs are:

- `spx_0dte_local_durable_development_20261001`: 585 accepted sessions,
  requested range **2022-01-03 through 2024-06-28 inclusive**; dataset hash
  `98434ab47077456d812a17be785e98d2cfc2c94819c986b0c83df6518a4f6b63`.
- `spx_0dte_local_durable_validation_20261001`: 128 accepted sessions,
  requested range **2026-03-13 through 2026-09-25 inclusive**; dataset hash
  `0f1fbcc08fda0059c044532308871fb6434396d5d73e76f4b9f5d919c276e4d5`.
- `local_support_v1`: supporting index observations and daily inputs.

Do not join these two date ranges into a continuous interval. The intervening
protected period is outside this task.

Relevant evidence under the durable root:

- `eligibility-ledger.json`: 908 development calendar dates, original audit
  reasons, and classifications for eligibility, holidays, weekends, and dates
  before regular weekday expirations.
- `session-ledger.json`: the completed E0 development replay overlay. Its trade
  outcomes are separate from data quality and may be linked without rerunning it.
- Each canonical dataset's `manifest.json`: source mapping, file hashes,
  `history` entries for `local_import` and `vendor_quality`, `raw_inputs`,
  `requested_raw_inputs`, and `sessions_skipped`.
- `artifacts/<development-dataset>/quality/25d9a7474ab2/quality.json` and its
  report/provenance: existing Q1–Q6 assessment.
- `artifacts/<validation-dataset>/quality/b3c6482ea210/quality.json` and its
  report/provenance: Q1–Q4/Q6 pass; Q5 is not evaluable.
- `frozen-supporting-inputs.json`, the active Cboe receipt
  `thetadata-daily/9f7d847ae966.json`, `experiment-plan.json`, and
  `completion-summary.json`: supporting identities and provenance.
- `data/thetadata/catalog.jsonl` and `data/thetadata_sealed/catalog.jsonl`:
  request metadata. Reading catalog metadata does not authorize opening protected
  partitions.

Verify current input identities before reusing evidence. If a required file is
absent or changed, report the precise discrepancy. Do not replace it, silently
use a similarly named prior import, or edit the published manifest to make it pass.

## Deliverable and scope

Add the smallest maintainable entry point to the existing research CLI for
building this ledger. A name such as `session-quality-ledger` is suitable; inspect
existing commands before selecting the final name. Require an explicit dataset
and inclusive start/end range. Make evidence locations explicit or resolve them
from established dataset/artifact conventions with validation.

Produce, outside Git and outside `/tmp`:

- A machine-readable ledger, preferably JSONL, sorted by exchange session date.
- A summary JSON containing reconciled counts and unresolved evidence issues.
- Provenance recording code revision/dirty state, input paths and SHA-256 hashes,
  dataset identity, schema/mapping version, requested range, and source evidence.
- A short Markdown report with exclusions, unknown checks, and reproduction commands.

Use a new private directory such as `reports/data_management/session_quality/`.
Follow the existing content-addressed artifact conventions. Make ledger and
summary content deterministic; put generation timestamps in separate provenance
so repeating identical inputs does not change the result identity. Preserve an
existing artifact on an unchanged rerun rather than replacing its provenance.

Generate separate artifacts for the two canonical ranges. Do not move, delete,
deduplicate, or rewrite raw data, normalized datasets, quality records, or registries.

## Ledger behavior

Create one record per requested calendar date for the selected dataset. Every
record must identify its instrument, option root, lifecycle, exchange date,
dataset identity, and evidence references. Use America/New_York for session
classification and retain source timezone/bar-stamp semantics in provenance.

Keep the following dimensions separate:

- **Calendar:** trading session, weekend, holiday, and scheduled early close.
- **Option availability:** successful request, vendor `no_data`, missing file,
  not requested, or independently supported non-expiration classification.
- **Supporting inputs:** availability of the required SPX observations, VIX,
  opening/prior-close inputs, and attributed settlement, where existing audit
  evidence establishes them. Unchecked fields must remain unknown.
- **Normalization:** accepted session, excluded session, absent normalized
  session, or unresolved conflict between evidence sources.
- **Quality:** dataset-level assessment and any genuinely available per-session
  measurements, with evidence scope stated explicitly.
- **Research outcome:** optional linked E0 trade/no-trade outcome, separate from
  all eligibility and quality fields. Its absence is not a failed data check.

Store exclusion reasons as a list, preserve the original reason text and evidence
location, and add stable reason codes only where they clarify existing categories.
Do not invent extra requirements or data-quality thresholds.

Important interpretation rules:

1. A dataset-level quality pass must not become a claim that every individual
   session passed every independently computed check. Label the assessment scope
   and attach per-session metrics only when the existing evidence provides them.
2. Preserve `not_evaluable` for validation Q5, rather than converting null to pass
   or fail. Distinguish it from a check that was never assessed.
3. Match quality evidence to the exact dataset hash and applicable range. Do not
   attach a result for another import or a differently mapped supporting source.
4. Preserve approved exclusions for 2022-02-22 and 2022-06-02 and the missing
   SPX/VIX observations recorded by the importer. Do not re-admit sessions because
   an option file exists or because a partial day has some prices.
5. A non-expiration weekday is not a failed download. Use the existing calendar,
   catalog, and documented expiration-rollout evidence. Do not blanket-classify
   weekday absences using a rule that discards EOM or holiday-shift expirations.
   The absence of an independent full expiration-list snapshot remains a limitation.
6. A valid no-trade session is not an excluded data session. The ledger must be
   useful before and independently of strategy evaluation.
7. Unknown provider attribution remains unknown. The owner SPX/VIX CSVs use
   America/Chicago bar-end timestamps; their documented last usable date is
   2025-12-09. Do not label these files as Schwab or ThetaData index data.
8. Retain the existing zero-quote/no-trade conventions. This task consolidates
   cleaning evidence; it does not fill price gaps, infer Greeks, or transform
   zero bids into missing values indiscriminately.

If valid evidence conflicts, preserve both references and report the conflict.
Do not silently pick a source merely to reproduce the expected count. A blocked
or conflicted status must not be advertised as ready for backtesting.

## Reconciliation targets

Derive these counts from input evidence and verify them; do not hardcode them
into production logic:

- Development: 908 requested calendar dates = 258 weekends + 25 holidays +
  31 documented non-expiration weekdays + 594 available option sessions.
  Of the 594, seven lack supporting observations and two are approved quality
  exclusions, leaving **585 accepted sessions**.
- When linking the existing development replay: **362 traded + 223 no-trade =
  585 eligible**; nine exclusions, 31 non-expiration dates, and 283 non-session
  dates complete the calendar ledger. No strategy replay is required to read this
  existing overlay.
- Validation: **136 requested candidate option sessions = 128 accepted + eight
  excluded**. Seven exclusions lack VIX (2026-03-13, 03-16, 03-18, 04-27,
  05-04, 05-18, and 06-02); 2026-06-01 lacks SPX observations. Classify other
  requested calendar dates from evidence and the existing market calendar.

Make summaries mutually exclusive for their primary classification, while
allowing multiple exclusion reasons. Missing-source or inconsistent-source
counts must be explicit. Source file counts must not be reported as session counts.

## Verification and completion criteria

Add focused tests using small fabricated fixtures, including:

- Calendar/expiration classification, an early close, a missing input, and an
  accepted no-trade session.
- Multiple exclusion reasons and preservation of an approved quality exclusion.
- Quality assessment scope, dataset-hash mismatch, and Q5 `not_evaluable`.
- A protected-range request rejected before any protected payload is opened.
- Deterministic generation, unchanged-input resumption, and changed input identity.
- Reconciliation conflicts that remain visible rather than being silently dropped.

Use the existing dataset verifier before and after real-data generation to establish
that the original canonical datasets are unchanged. Verify both ledger artifacts
against their provenance, run the narrow relevant tests and lint, and refresh
graphify after code edits. Broaden tests only if the implementation changes shared
behavior. Include the exact commands, counts, and check results in the handoff.

The task is complete when the CLI exists, both real ledgers reconcile, exclusions
and unknown checks remain explicit, unchanged reruns reproduce the result hashes,
focused checks pass, and documentation links to the private outputs and explains
their interpretation. Do not claim a completed quality assessment for checks that
were merely inherited or not evaluable.

## Boundaries

Keep all work offline. Do not restart or deploy services, alter runtime configs,
call Schwab write APIs, run new strategy sweeps, acquire more vendor data, or
schedule a job on Helios. Never expose secrets or account identifiers. Keep vendor
prices, quote traces, and private ledgers untracked.

The protected **2024-07-01 through 2026-03-12** interval was already evaluated in
H-TS1 and remains guarded. Do not open, unseal, chart, replay, hash protected raw
payloads, or label that interval unseen. Metadata inspection is not unseal approval.

Per-session Helios database continuity, NDX/XSP readiness, independent backups and
restore drills, automatic scheduling, and broader archive imports are later tasks.
List those as follow-ups without expanding this implementation to include them.

Finish by reporting the implementation branch/commit if one was created, files
changed, reproduction commands, ledger locations and hashes, reconciled counts,
tests/lint/graph results, and any evidence limitations. Do not push to `main`.
