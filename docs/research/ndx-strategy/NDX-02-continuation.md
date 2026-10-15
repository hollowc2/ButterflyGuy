# NDX-02 continuation import and cadence audit — 2026-10-15

**Import/audit complete; replay eligibility remains false.** The independent
minute evidence is now preserved and normalized under a new snapshot. It is not
a continuation of R0 monitor polls. No signals, P&Ls, longer-hold rules, rejected
variants, parameter searches, liquidity thresholds or deployments were evaluated.
Broader NDX-02 execution/liquidity calibration remains incomplete.

## Evidence and declared contract

Parent evidence: the verified [execution ledger](evidence/2026-10-15/ndx02-execution-ledger.jsonl),
NDX-02/run-02, NDX-01/run-03, and
[original continuation inventory](evidence/2026-10-15/continuation-inventory-manifest.json).
All prior raw snapshot/supplement/inventory manifests, parent outputs and 140
source pins were verified before acquisition. The current local source remains
at HEAD `6a33d170c09f7ff68d7edb733b74c087b27c0227`, with prior dirty work preserved.
New source/test hashes and the actual environment are in the new run manifest.

The [initial contract](evidence/2026-10-15/ndx02-continuation-contract.json) was
written before inspecting continuation prices. The [extraction revision](evidence/2026-10-15/ndx02-continuation-contract-v2.json)
retains the same cohort, windows, numerical/timing tolerances and eligibility.
It adds literal per-session expiration predicates after the original dynamic
query exceeded its fixed 60-second timeout. The failed header-only extraction,
query, contract and [attempt manifest](evidence/2026-10-15/ndx02-continuation-attempt01.json)
are preserved at `evidence/ndx/ndx-minute-continuation-20261015/`. No timeout was
increased and no failed extraction was reused as data.

Successful raw snapshot:
`evidence/ndx/ndx-minute-continuation-20261015-v2/`; its
[manifest](evidence/2026-10-15/ndx02-continuation-snapshot.json) hashes 11 files.
`prices/extract.csv` preserves 3,364 original leg rows, including incomplete
groups; `schema/extract.csv` preserves the observed table schema. Exact symbols,
strikes, directions and dates came from the verified cohort, not a live trade
query. Query scope is each trade's **`(recorded exit, regular-session close]`**,
using timezone-aware `snapshot_time`, NDX underlying and exact session expiration.
Wrong-expiration database rows are outside this export's scope; their absence
from the database is not attested.

The source is historical ButterflyGuy Schwab chain captures in Helios TimescaleDB
tables `option_chain_snapshots` and `chain_snapshot_meta`. The timed rows label
their source `schwab_rest_option_chain`. Read-only acquisition ran from
**20:19:52.965265 to 20:20:00.296467 UTC** on October 15. The
[versioned SQL](sql/continuation-prices-v2.sql) selects original quote JSON and
snapshot timing metadata without filtering prices, duplicates or completeness.
Unrelated `omitted`-contract payloads were excluded. Database schema columns,
including every actually available timestamp and size field, remain in the raw
extract. Dates range July 23–October 13; no additional trading window was added.

Helios identity, repository existence, healthy database container and available
disk were checked read-only. No credentials, account data or runtime settings were
inspected or changed. Retention is the accepted Eros-backed NFS filesystem;
independent backup remains unestablished.

## Normalization and inventory reconciliation

New offline output: `reports/research/ndx-02-continuation-20261015/run-01/`.
Versionable [coverage ledger](evidence/2026-10-15/ndx02-continuation-coverage.jsonl),
[summary](evidence/2026-10-15/ndx02-continuation-summary.json),
[rejections](evidence/2026-10-15/ndx02-continuation-rejected-groups.jsonl), and
[run manifest](evidence/2026-10-15/ndx02-continuation-run-01.json) link the source
to the result. Bulk normalized observations and raw rows stay outside Git.

The audit groups exact symbol/time keys and independently checks NDXP OCC root,
encoded expiration/type/strike, stored expiration/type/strike, lifecycle boundaries,
finite nonnegative leg bid/ask/mark, and uncrossed leg markets. Duplicates,
incomplete groups and inconsistent metadata are reported rather than repaired.
The historical inventory's weaker SQL predicate is separately recomputed; it does
not silently adopt the new normalization test.

- **All 17** original inventory counts and first/last timestamps match to the
  predeclared one-microsecond tolerance; the cohort membership also matches.
- **1,125 raw timestamp groups** contain **1,114 complete observations** and
  **11 incomplete groups**, each with two legs. The latter account for 22 retained
  raw rows. Five belong to trade **317**, six to **346**.
- No duplicate keys, wrong imported identity, nonfinite/crossed/negative leg
  prices or metadata conflicts were found in the complete groups.
- `observations.jsonl` retains original legs, provider marks, raw composite
  bid/ask and all available metadata. Here `eligible` means **passes structural
  leg normalization**, not eligible for strategy replay. Every observation and
  per-trade ledger explicitly sets R0 and minute-replay eligibility false.

No row was interpolated, forward-filled, synthesized, clipped, assigned a missing
timestamp or substituted into R0. `rejected-groups.jsonl` identifies every rejected
timestamp; originals remain in the hashed raw extract.

## Cadence and source boundaries

Predeclared diagnostics were nominal 60-second cadence and strict gaps above
30/60/90/120 seconds. These are measurement bins, not tuned eligibility thresholds.
p95 uses nearest rank. Full expected minute buckets start at `ceil(exit)` and end
strictly before close; the partial exit minute and an exact-close observation are
counted separately. This avoids treating a partial minute as a full missing bar.

For **1,097 adjacent complete-observation intervals**:

- Minimum **61.131032 s**, median **63.101178 s**, p95 **64.264143 s**, maximum
  **264.102769 s**. Every interval exceeds both 30 and 60 seconds.
- **Four** intervals exceed both 90 and 120 seconds: trade 317 at
  19:25:57.467463→19:30:21.570232 (**264.102769 s**) and
  19:42:10.522294→19:45:21.776195 (**191.253901 s**) on September 29;
  trade 346 at 19:37:08.563196→19:41:14.421936 (**245.858740 s**) and
  19:45:19.602425→19:49:25.468008 (**245.865583 s**) on October 13. All times UTC.
  The intervening incomplete groups explain the lost complete-quote coverage.
- **67 missing full minute buckets** out of **1,171 expected**, with zero
  multiply occupied buckets. Ten observations occur in partial exit buckets.
  Slow collection cadence can skip a clock minute without an exceptional
  inter-observation outage; bucket gaps and long intervals are distinct measures.
- Exit-to-first collection is **4.189141–56.114927 s**; final collection-to-close
  is **7.437138–61.752376 s**. Trade 194 has one observation, so its interval
  statistics remain missing rather than zero.

The per-trade ledger includes both raw and complete-only cadence, every interval,
all missing bucket timestamps, and first/tail gaps. The last R0 held-monitor
collection to first independent collection gap is **5.098176–57.244304 s**.
The sources have no post-exit overlap under this extraction's boundaries. This
is a collection-stream boundary, not a fill-latency or quote-freshness estimate.
The minute observations are not fixed minute-bar closes or a validated 30-second
monitor path. R0 and its historical results remain unchanged.

## Price and timestamp findings

Composite values preserve `+1/−2/+1` **provider leg marks**, outer bids minus
twice center ask for raw bid, and outer asks minus twice center bid for raw ask.
They are not asserted executable complex-order prices.

- **635/1,114 negative composite bids** and **157/1,114 negative provider
  composite marks** remain signed. Composite marks range **−13.97 to 10.04**
  points; bids range **−40.00 to 6.30**. Zero marks exceed wing width and zero
  composite markets cross. No floor is applied to these observations.
- Provider composite mark differs from the composite bid/ask midpoint by more
  than 0.00011 points on **816 observations**. Replacing marks with midpoints
  would change the evidence. Negative marks need constituent-quality attribution
  before economic use; they are not negative intrinsic settlement observations.
- All **3,342 complete-group leg rows** have recorded bid/ask sizes. These are
  source displays, not evidence of complex-order capacity or fills.

Actually recorded timestamp coverage is limited:

- **148 complete observations** across trades **339 (23), 343 (24), 346 (101)**
  have metadata and **444/3,342** constituent quote-event timestamps/ages. The
  other **14 trades / 966 complete observations / 2,898 leg rows** lack them.
- Reported quote ages range **0.504256–269.157070 s**, with no negative reported
  ages. Per-trade reported median/p95/max are **6.310886/65.241120/82.004760 s**
  (339), **2.786403/84.371440/200.551220 s** (343), and
  **1.993752/48.860020/269.157070 s** (346). These describe only the timed subset;
  no freshness threshold or retrospective filter was selected.
- Recorded snapshot start-to-chain-fetch completion ranges **1.048414–2.789879 s**.
  **145** constituent event times occur after the snapshot's start-of-pass stamp;
  none occurs after its recorded local fetch completion. None of the timed events
  precedes that trade's recorded exit or exceeds regular close, and no recorded
  chain fetch completes after close. A start-of-pass stamp is therefore not an
  availability timestamp. Clock synchronisation was not independently attested.
- Metadata retains fetch start/end, gateway-receive and chain-event times/ages.
  `scheduled_at` is null for every imported complete observation. Publication,
  database write/commit and consumer-availability timestamps were not recorded
  here and remain null. The audit never reverse-engineers them from reported ages.

New timing evidence does not repair the earlier held-monitor or paper-diagnostic
timestamp gaps. It belongs to this separate minute source and snapshot only.

## Eligibility decision and exact next task

**0/17 R0 continuation paths and 0/17 minute-replay paths are eligible.** The
structural import is complete; cadence, missing/incomplete groups, negative
provider composites, incomplete constituent freshness and unrecorded consumer
availability prevent treating it as an established causal execution path. No
new P&L was calculated. Official settlement remains a separate evidence limit.

**Next bounded task: constituent quote-quality attribution and a causal minute
evidence specification.** Audit the 157 negative provider composite marks and
provider-mark/midpoint differences against original per-leg prices, exact
symbols and available event/age metadata. Begin with the attributable timed
subset (339/343/346), and report what remains unknowable for the 14 untimed trades.
Specify when a minute observation could become usable, its signal/fill cadence,
gap/incomplete/negative-mark treatment and required freshness evidence, or retain
`insufficient evidence`. Predeclare any quality rules and validation fixtures
before evaluating their economics. Do not choose thresholds using P&L, run
hold-after-exit experiments, optimize parameters or activate instrumentation.
Full NDX-02 liquidity calibration remains open.

## Reproduction and verification

See [exact offline and acquisition commands](NDX-02-continuation-reproduction.md).
The offline command requires explicit evidence/manifest/config/parent/output
paths, verifies hashes and source pins, refuses overwrites, and records source
copies, environment, commands, parent links and output hashes. Acquisition is a
separate explicitly read-only command and must always use a new snapshot path.

**72 tests passed**: 15 continuation tests (including the full private snapshot
with network blocked and subprocesses restricted to local Git) and the previous
57 accounting/baseline/state-machine/position-manager tests. Repository Ruff
passed; graphify AST update completed. Its optional SQL parser and community-label
limitations remain documented in [verification](evidence/2026-10-15/ndx02-continuation-verification.json).
No broker-connected tests, live orders, runtime changes or deployments occurred.
