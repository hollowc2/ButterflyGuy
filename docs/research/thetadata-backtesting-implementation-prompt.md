# Implementation prompt: finish local ThetaData backtesting support

Prepared 2026-09-30. This is an implementation specification, not authorization to
change live trading, register a hypothesis, or run a new holdout experiment.

## Objective

Make the downloaded ThetaData Parquet archive usable through Butterfly Guy's
existing research workflow, with an offline option-data path, reproducible input
manifests, explicit coverage exclusions, and verified execution accounting.

Deliver SPXW 0-DTE first. Then add research support for SPXW 1-DTE, NDXP 0-DTE,
and XSP 0-DTE. A supported mode must produce a verified replay when its required
inputs exist and report specific missing inputs when they do not. Do not imply
that having option quotes makes every downloaded session backtestable.

Implement the work, run the appropriate verification, and document working
commands. Proceed through independent work even if some market inputs are missing.
Do not stop after a design or a partial adapter.

## Start from the work that already exists

The active checkout was `feat/weekend-review-executable-pnl` when this prompt was
prepared. It has unrelated uncommitted edits. It is not the complete research
implementation. Inspect current branch and worktree state before choosing a base.

Relevant existing worktrees and branches:

- `/mnt/Repos/Trading/Butterflyguy-research`, `research/unified-core`: research
  engine, ThetaData API adapter, normalized Parquet datasets, vendor-quality
  checks, development runs, registry, and holdout evaluation.
- `/mnt/Repos/Trading/Butterflyguy-unify`, `research/phase1-command-surface`:
  research command consolidation. Read its workflow-unification plan and inspect
  its divergence from `research/unified-core` before selecting or integrating work.
- `/mnt/Repos/Trading/Butterflyguy-thetadata`, `feat/thetadata-download`: raw
  download work. The archive itself is in the main checkout's `data/` directory.

These are discovery pointers, not instructions to switch a dirty checkout, merge
branches indiscriminately, or alter another ongoing task. Use a dedicated branch
or worktree when needed. Preserve the owner's edits and existing research ledgers.
Do not create a second research engine or rebuild functionality already present.

Read repository `AGENTS.md`, `README.md`, and `graphify-out/GRAPH_REPORT.md`.
Use the graph wiki if present. In the selected research baseline, read:

- `docs/research/research-core.md`
- `docs/research/workflow-unification-plan.md`, when present
- `docs/research/vendor-data-quality-plan-2026-09-28.md`, including amendments
- `docs/research/next-sweep-preregistration-draft.md`, including revisions
- `docs/research/registration-decision-2026-09-29.md`, including dated updates
- `src/butterfly_guy/research/{dataset,history,thetadata,quality,holdout,registry,protocol,market,simulate,cli}.py`
- Relevant research tests and frozen parity fixtures
- `src/butterfly_guy/backtest/{data_loader,chain_cache,execution_accounting}.py`
- `src/butterfly_guy/scripts/run_backtest_db.py` and the existing live selection
  and settlement functions used by the research implementation

Use the market-data-operations skill for inventory and validation and the
trading-strategy-research skill for replay and accounting work. This task is
infrastructure work; do not tune strategies or search for profitable parameters.

## Facts and constraints to carry forward

Raw storage:

```text
/mnt/Repos/Trading/Butterflyguy/data/thetadata/
  <set>/<kind>/<YYYY>/<YYYY-MM-DD>.parquet
  catalog.jsonl
  download.log

/mnt/Repos/Trading/Butterflyguy/data/thetadata_sealed/
  <set>/<kind>/<YYYY>/<YYYY-MM-DD>.parquet
  catalog.jsonl
```

- Sets: `spxw_0dte`, `spxw_1dte`, `ndxp_0dte`, `xsp_0dte`.
- Kinds: `quote_1m`, `ohlc_1m`, `open_interest`, `eod`.
- Files are Zstandard-compressed Parquet, preserving vendor columns. Partition
  filenames represent **trade dates**, not necessarily expiration dates.
- Inventory on 2026-09-30: about 5.5 GiB on disk and 23,040 Parquet files across
  both roots. The completed batch reported 5,754 fetched sessions and zero failures;
  some sessions had been downloaded before that batch. Recompute inventory rather
  than hardcoding these totals.
- 0-DTE archive ends 2026-09-28; SPXW 1-DTE trade dates end 2026-09-25, for
  2026-09-28 expiration. NDXP/XSP 1-DTE were not downloaded.
- NDXP 2022-12-16 returned vendor `no_data` for all four kinds.
- Missing expiration weekdays before daily expirations began are not automatically
  download failures. Compare with actual expirations and the session calendar.
- Option `timestamp`, `created`, and `last_trade` are timezone-aware New York
  datetimes. The research engine uses UTC microseconds.
- A bid/ask pair of 0/0 is absent quote state. A zero bid with a positive ask is
  valid. Trade bars with volume zero and OHLC zero mean no trades, not a tradable
  price. The archive has no index levels, Greeks, or IV.
- Preserve raw files. Derived datasets and manifests belong in separate storage.
  Vendor data and owner CSVs must stay out of Git and public artifacts.
- Existing research treats `data/spx_1min.csv` and `data/vix_1min.csv` as
  **America/Chicago, bar-end timestamps**. The older `CsvDataLoader` describes them
  as Eastern; do not reuse that interpretation for this archive. The research
  branch excludes stale runs and identifies 2025-12-09 as the last usable date;
  raw tail rows alone do not establish usable coverage. Audit and explain this.
- The minute files' original third-party source is unknown. Preserve that provenance
  limitation. Index minute bars are not authoritative expiration settlement values.
- The owner previously chose not to buy an Indices month, accepted missing index
  sessions, and chose to keep the local data. Do not reopen those decisions or
  purchase a subscription as an implementation prerequisite.

Research state must be established from current evidence. At preparation time,
`research/unified-core` had H-TS1 registered at sequence 0 and a completed holdout
evaluation, recorded in commits `a33b3db` and `bd53583`. Therefore neither the
word "sealed" in a folder name nor an old draft proves the interval is still
unseen. Check the current registry and evaluation metadata before any replay.
Preserve existing records and do not expose price data merely to inspect status.

Boundaries:

- No changes to runtime strategy parameters, risk limits, paper/live mode, account
  guards, order routing, credentials, deployment, timers, or the prospective cohort.
- Do not call broker write APIs or place orders. Do not restart services.
- No blanket holdout bypass, no automatic registration, and no rewriting historical
  manifests or results. Existing registrations freeze code and data; implement on
  a separate branch without making the frozen evaluation unreproducible.
- Keep missing observations missing. No parity-derived SPX, computed VIX,
  interpolated prices, synthetic chains, ETF scaling presented as index data, or
  forward-filled missing market bars.

## Phase 1 — establish the actual remaining work

Produce a short implementation baseline identifying what is already complete,
what is missing, and which branch contains the authoritative implementation.

1. Inventory raw catalog entries against files and Parquet metadata. Distinguish
   expected expirations, fetched requests, successful files, `no_data`, incomplete
   files, and usable replay sessions. Summarize by set, kind, and year.
2. Audit SPX/VIX minute coverage, existing daily-close caches, recorded research
   datasets, and any existing NDX/XSP inputs. Inspect local evidence first. Remote
   server inspection is optional and requires the server-management skill; do not
   make a live database connection necessary for offline replay.
3. Establish the existing research cache root, manifest versions, registry state,
   quality approvals, exclusions, and frozen source commits.
4. Identify actual dependencies in the chosen branch. Add only missing dependencies
   needed for Parquet support; the research branch already uses pandas, NumPy, and
   PyArrow. Update dependency declarations and lockfile together if necessary.
5. Record the protected interval, 2024-07-01 through 2026-03-12, and its current
   exposure status. Do not open protected raw files for general inventory or schema
   discovery. Use unprotected examples and existing metadata instead.

Acceptance: an attributable baseline and concrete list of work remaining; no raw
changes, no new evaluation, and no claims of complete index coverage based on
first/last CSV rows alone.

## Phase 2 — local raw-Parquet source and normalization

Extend the existing `HistorySource`/dataset pipeline with a local ThetaData source.
Reuse existing source-independent normalization and validation wherever possible.
Do not first import the archive into live TimescaleDB, and do not serialize it into
the legacy JSON chain cache.

Required behavior:

1. Accept an explicit archive root, set, inclusive date range, and separate output
   dataset. Discover only requested files. Project necessary columns and process
   bounded sessions rather than loading the entire archive at once.
2. Validate contract identity using root, expiration, strike, and right. SPXW maps
   to SPX, NDXP to NDX, XSP to XSP; preserve the option root as provenance. Never
   relabel an NDX/SPX observation as XSP or conflate trade date with expiration.
3. Preserve strikes without unjustified integer coercion; validate against the
   instrument's listed grid. Preserve timezone offsets and convert to UTC without
   localizing already-aware timestamps a second time.
4. Map observed bid/ask to midpoint `(bid + ask) / 2`. Represent absent 0/0 quote
   state and missing IV/Greeks as missing in the normalized research schema, not
   as genuine zero prices or zero Greeks. Existing float defaults in `OptionQuote`
   do not justify enabling Greek-dependent strategies on missing data.
5. Retain quote sizes and useful source fields where existing execution/quality
   consumers need them. Join opening open interest by full contract identity only
   under the existing availability convention. Do not attach EOD volume or closing
   fields to morning decisions. Bar aggregates become available at their actual
   interval end, not at a guessed start time.
6. Preserve crossed quotes for diagnostics while rejecting them for executable
   pricing. Reuse existing quote validity and age rules. A minute quote-state row
   is not proof that the quote just changed; distinguish grid observation time
   from last-update time if the archive does not provide the latter.
7. All decision lookups must be causal: observation time at or before decision
   time, within documented freshness bounds, and never across sessions. Existing
   within-session state reconstruction must retain age and must not conceal gaps.
8. Write separately hashed derived datasets with an explicit schema version, raw
   SHA-256 references, source identity, range, mapping rules, input dependencies,
   and tool version. Keep raw catalog records unchanged.
9. Make exports resumable and deterministic. Atomic output publication must avoid
   corrupt partial manifests; retries must not duplicate sessions. Changed raw
   input must be detected rather than silently accepted under an old dataset hash.
10. Use the existing holdout/registry guard before resolving or opening protected
    files. CLI, direct Python calls, globs, and alternate archive paths must all
    obey the same date policy. Local import is not an exception to existing quality
    gates or registration provenance checks.

Use a new derived dataset identity for new imports unless equivalence with an
existing dataset is explicitly established. Do not append raw imports to an
already registered dataset simply to avoid another name.

Acceptance: an unprotected local SPXW session normalizes without a Theta Terminal,
broker, or live DB, passes schema checks, and produces identical semantic results
on repeat export. Protected access fails before any raw file is opened.

## Phase 3 — supporting observations and coverage policy

Provide offline, source-attributed inputs for the selected instrument:

- Intraday index observations used by entry signals and monitoring.
- Prior-session close and historical closes required by enabled filters.
- Official opening observation, or explicitly labeled first-bar-open proxy if that
  is the approved research profile's convention.
- Official PM expiration close/settlement input for positions held to expiration.
- Intraday and prior-session VIX observations required by the configured strategy.

Reuse the research branch's Central-time minute loader, stale-day exclusions,
Cboe daily observations, and recorded-data fallback rules. Preserve historical
decisions: a recorded fallback must not silently fill the protected index gap, and
the owner-approved absence of an Indices subscription is not a code failure.

Cache public daily inputs so a complete replay can run offline. Acquisition and
refresh must be explicit, separate from evaluation, and record source URL, retrieval
time, source hash, symbol, timezone, and actual availability. Do not refresh inputs
implicitly during an otherwise reproducible backtest.

Use the calendar and each instrument's trading/settlement conventions. Support
holidays and scheduled early closes. The raw option archive extends to 16:15;
that does not mean the strategy should monitor an expiring PM contract past its
settlement cutoff. Preserve the approved early-close handling already implemented.

Do not substitute option EOD marks or last intraday index ticks for missing official
settlement. For NDX/XSP, validate instrument-specific opening/settlement sources;
do not assume SPX functions or a constant index ratio provide equivalent evidence.
If source conventions are uncertain, verify primary documentation during
implementation and record the interpretation.

Add a per-session input audit with statuses such as usable, absent option data,
missing index observations, stale input, missing prior close, missing VIX,
missing settlement, incomplete required interval, or protected access. Distinguish
a legitimate strategy no-trade from a data exclusion. List exclusions and their
effect on the eligible sample. Do not skip an entire session merely because an
unused optional feature is missing.

Strategies needing Greeks/IV must fail a capability check with a clear reason;
observed-data strategies may proceed without them. Estimating Greeks or buying
additional data is a separate task, not a hidden fallback.

Acceptance: the audit reports the exact intersection of option and supporting
coverage, including accepted gaps. Missing inputs give actionable reasons and
never fabricated observations.

## Phase 4 — SPXW 0-DTE integration and execution verification

Expose local archive import/audit and replay through the selected unified research
command surface. Preserve existing DB/frozen replay behavior. Do not extend a
legacy runner into a competing research workflow solely for this source.

Reuse live entry selection, approved research profiles, normalized chain access,
existing exit models, execution accounting, and the common cash-settlement
function. Confirm every path selects the intended underlying and expiration.

Accounting must state exactly what it represents:

- Midpoint: paper-convention research comparison.
- Marketable long 1/-2/1 fly entry: lower ask + upper ask − 2 × center bid.
- Marketable exit: lower bid + upper bid − 2 × center ask.
- Stressed pricing: the existing adverse adjustment per contract leg, with the
  center quantity counted twice; apply commissions per contract per side and the
  correct instrument multiplier.
- Cash settlement: intrinsic fly value at the authoritative PM settlement input,
  with no invented exit execution or closing commission.

Preserve existing semantics for frozen decisions repriced after replay versus a
simulation whose execution model changes cash flows, sizing, or exit decisions.
Label these separately. Do not claim a post-processing accounting comparison is
a complete executable-strategy simulation.

The research branch has an owner-approved stressed-exit floor for a particular
vendor protocol. Retain its provenance and explicit applicability. Do not apply
it universally, infer guaranteed free closes, or change registered accounting.
Report how often a configured floor is used.

Missing, crossed, or excessively old leg markets must produce explicit pricing
failures. Do not repair them using midpoint, EOD prices, later observations, or
synthetic quotes. NBBO leg crossing is an assumption, not proof that a complex
order could fill; record that limitation. Preserve the existing delayed-exit
stress model and describe the one-minute clock's limits.

Acceptance: replay an eligible unprotected session with traceable leg quotes,
entry, monitoring, exit/settlement, costs, and P&L. Compare with existing source
and frozen fixtures where appropriate; explain differences in observation timing
instead of requiring unrelated vendor snapshots to produce identical selections.

## Phase 5 — SPXW 1-DTE

Add explicit trade-date/expiration support without treating every expiry as the
session date. Reuse contracts and cash-flow functions; extend dataset structures
only where they truly assume a same-day expiry.

The archive's `1dte` means **one trading session before expiration**. Friday to
Monday and holiday gaps are valid; do not select by calendar-day subtraction.
Record both trading-session distance and actual calendar/time-to-expiration
where required by a model.

Implement two clearly specified research lifecycles:

1. Intraday: enter on the pre-expiry session and close during that same session.
   Never settle an unexpired contract using the trade date's index close. An exit
   without a usable recorded market is unresolved/unpriceable, not cash settlement.
2. Carry to expiry: load the same expiration and strikes from `spxw_1dte` on the
   entry day and `spxw_0dte` on expiration day. Carry actual position state across
   the overnight gap, monitor only during available sessions, and close or settle
   against the expiration day's observations.

Record expiration on positions, fills, and traces. Preserve peak/trailer state
according to the documented lifecycle; do not silently reset it overnight. Do
not invent overnight option marks, liquidation fills, or P&L paths. State overnight
valuation limitations. A range ending before an open position resolves must be
reported as unresolved, never dropped from the ledger as if it did not trade.

Start verification with one position/one fly so mechanics do not depend on an
invented portfolio. Then document how any existing research sizing/risk rules
handle overlapping positions, capital usage, daily counters, and an overnight loss.
Do not claim portfolio returns without a defined capital model. Do not broaden
runtime 0-DTE risk logic to enable live 1-DTE trading.

Do not represent the current 0-DTE strategy as automatically appropriate for
1-DTE. Expose an explicit research specification using existing controls where
meaningful, with unsupported time-to-expiry assumptions rejected or labeled.
No optimization is needed to verify the lifecycle.

Acceptance: fixtures cover Friday/Monday, a holiday gap, an intraday exit, an
expiry-day exit, overnight state, missing second-day data, and expiry settlement.
When verified, the available real archive can drive both lifecycle modes on
eligible unprotected sessions with full contract identity preserved.

## Phase 6 — NDXP and XSP 0-DTE

Generalize only genuinely SPX-specific research assumptions: underlying identity,
option root, strike grid, tick size, multiplier, calendar, settlement input,
supporting data, and configured strategy capabilities. Derive values from the
existing instrument configuration and verified contract conventions rather than
copying SPX constants.

Do not reuse SPX index prices for NDX/XSP. If existing research has no valid
instrument-specific index data, complete adapter, schema, lifecycle, and fixture
support, then document the exact acquisition gap. Do not buy data, use ETF
scaling, or claim a successful historical validation without actual observations.
NDXP/XSP 1-DTE are outside this archive's scope.

Acceptance: deterministic instrument-specific fixtures pass; asset/expiration
isolation is tested; a real replay runs wherever actual supporting data exists.
Unsupported datasets report missing inputs and remain explicitly unvalidated.

## Phase 7 — reproducibility, tests, and handoff

Write separate artifacts for raw inventory, input quality, normalization provenance,
replay runs, and exclusions using existing research artifact conventions. Each run
must identify:

- Command, inclusive range, dataset/set, profile and lifecycle.
- Git commit and dirty state, dependency versions, strategy/config hashes.
- Raw and normalized data hashes, supporting-input hashes, feature availability.
- Accounting model, commissions, slippage, quote freshness, latency, any exit floor.
- Requested, available, eligible, evaluated, excluded, no-trade, and unresolved
  counts, with reasons and denominators.
- Trade records and reproducible cash flows; P&L, drawdown, trade count, win rate,
  expectancy, profit factor, average win/loss, exposure, and cost drag where defined.
  Label returns or percentages only when capital assumptions make them meaningful.

Use synthetic fixtures for malformed or edge-case markets and small unprotected
real samples for integration. Do not commit vendor rows as test fixtures. Add
focused regression tests before changing existing behavior where practical:

- Timezones, DST boundaries, bar-end availability, causal lookup and freshness.
- Full contract identity, underlying isolation, and actual expiration retention.
- 0/0 absence versus genuine zero bid, crossed/invalid quotes, and no-trade bars.
- Duplicate/conflicting rows, schema mismatch, malformed files, partial export,
  unchanged-input resumption, and changed-input detection.
- No morning use of EOD observations; no future VIX/prior-close leakage.
- Holdout denial before I/O, token/dataset mismatch, guarded local import, and
  refusal to silently modify registered source/data identities.
- Known exclusions and scheduled early closes.
- Accounting arithmetic, multiplier, center-leg quantity, fees, stress, configured
  floor, and settlement.
- Both 1-DTE lifecycles and unsupported capability rejection.
- Existing frozen research parity and command compatibility.

Run narrow tests while implementing; run the full suite for shared behavioral
changes and `uv run ruff check .` at completion. Separate pre-existing failures
from regressions. Record unavailable checks and their exact dependency/data reason.
After code modifications, run `graphify update .` using the repository-prescribed
binary/tool and report whether it completed.

Measure time and peak memory for a single session and a modest unprotected range.
Demonstrate bounded per-session processing and resume behavior. Do not introduce
a speculative speed target or rework the engine for performance without evidence.

Proposed user workflow to document with the **actual implemented command names**:

1. Audit raw archive and required supporting inputs.
2. Import an unprotected date range into a separate normalized local dataset.
3. Run existing vendor-quality checks and preserve approved exclusions.
4. Replay one session and inspect its trace/accounting.
5. Replay a development range with full exclusions and provenance.
6. Run supported 1-DTE or alternate-instrument modes explicitly.

This list describes required operations, not CLI flags that already exist. Prefer
extending `python -m butterfly_guy.research` and its existing subcommands. Make the
normal import/replay path work with the network disabled after inputs are cached.

Do not automatically re-run the registered H-TS1 holdout after source changes.
An exact reproduction belongs to its pinned code/data environment. New experiments
on previously evaluated dates are exploratory and need a separately documented
research design; they cannot restore the interval's unseen status. This task may
verify guard behavior with fixtures without performing another holdout look.

## Completion checklist

- Existing research work reused; unrelated edits, live services, and ledgers preserved.
- Raw archive remains unchanged and private.
- Local SPXW 0-DTE import and eligible replay work offline, without Theta Terminal.
- Existing quality/holdout controls apply to local file access as well as API access.
- Supporting-data gaps are enumerated, with no fabricated prices or hidden fallbacks.
- SPXW 1-DTE intraday and carry lifecycles are implemented and verified.
- NDXP/XSP 0-DTE support is verified with fixtures and with real data wherever available;
  remaining external-data blockers are specific and reproducible.
- Shared regressions and frozen parity are checked; completed tests/lint are reported.
- Documentation provides executable commands, source assumptions, limitations, and
  a small example run with artifacts.

The final handoff should state what works now, what was tested, where the artifacts
live, and any specific missing real-world input. Do not equate infrastructure
completion or a positive backtest with authorization to deploy or an established
trading edge.
