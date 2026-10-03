# Historical data management

This is the entry point for locating historical market data and its validation
evidence. Raw coverage, normalized coverage, and research eligibility are distinct.
The dated machine inventory is a snapshot, not a promise about later downloads.

## Current inventory

The 2026-10-01 inventory is under the private, gitignored directory
[`../reports/data_management/2026-10-01/`](../reports/data_management/2026-10-01/).
Its [`inventory.json`](../reports/data_management/2026-10-01/inventory.json)
lists dataset roles, requested ranges, session counts, hashes, supporting inputs,
preserved imports, and known limitations. The archive reconciliation is a separate
content-addressed `inventory.json` beneath `market_data_inventory/inventory/`.

The snapshot also includes read-only Helios database timestamp bounds and remote
file metadata, in `helios-database.json` and `helios-files.json`. File counts and
timestamp bounds do not prove continuous coverage. Large-table row counts are
planner estimates; stale statistics and compressed chunks can undercount them.
Exact per-instrument session continuity is a separate audit.

This pass reconciled 23,040 ThetaData files against 23,044 requests, including
four vendor `no_data` responses. There were no catalog conflicts, missing
successful files, incomplete unprotected files, or files without a successful
catalog request. Row counts were checked for 16,264 unprotected files; the 6,776
protected files received metadata checks only. The three canonical datasets'
1,434 manifest-listed files passed hash and row-count verification, and eight
supporting-input checksum comparisons passed. These are integrity findings,
not a fresh computation of quality gates or a full raw-file checksum baseline.

## Sources and ownership

- **ThetaData raw options:** `data/thetadata/`, including the spent 2024-07-01
  through 2026-03-12 holdout, which was kept in `data/thetadata_sealed/` until
  2026-10-03. See the [archive guide](../data/thetadata/README.md)
  for the four sets, file kinds, source timezone, and no-quote/no-trade conventions.
  The catalogs record successful and `no_data` requests; absent calendar dates
  do not independently prove a missing expiration or a failed download.
- **Owner SPX/VIX minute files:** `data/spx_1min.csv` and `data/vix_1min.csv`.
  The recorded original provider is unknown. The research mapping treats their
  timestamps as America/Chicago bar ends and excludes documented stale sessions.
  Last usable date in the existing source description is 2025-12-09. Preserve
  that qualification when using these files; do not relabel them as broker data.
- **Attributed daily closes:** the active receipt is
  `reports/thetadata_completion/2026-10-01/thetadata-daily/9f7d847ae966.json`.
  It identifies the preserved Cboe SPX/VIX CSVs, retrieval times, source URLs,
  and hashes. Daily closing observations are usable as prior-session features
  only on later sessions; historical publication times are not recorded.
- **Recorded supporting observations:** dataset `local_support_v1` in the
  canonical cache below. Its manifest identifies the upstream snapshot and
  supporting-input mapping.
- **Legacy local data:** `data/schwab/`, `data/chains/`, and
  `data/spy_1min_2008_2021_cleaned.csv`. Inventorying these files does not validate
  their price quality, full session coverage, adjustments, or compatibility with
  the observed-price research workflow. Keep the legacy SPY source separate from
  SPX index observations.
- **Operational database:** Schwab option snapshots, spot prices, daily bars,
  decisions, and monitored leg quotes. The [schema inventory](data-sources-inventory.md)
  describes these sources, but its historical counts are not a current audit.
- **Helios chain caches:** `/opt/butterflyguy/data/chains/{SPX,NDX,XSP}/`.
  The snapshot found 100 daily JSON files per instrument, dated 2026-05-06
  through 2026-10-01, totaling 13,211,831,888 bytes. These are recorded cache
  files; their prices, snapshot cadence, and session gaps were not revalidated.
- **Helios equity and gateway exports:** four equity symbol/session directories
  under `/opt/butterflyguy/data/equity_market_data/`, and four minute-export
  JSONL files for 2026-09-29 and 2026-10-01 under
  `/opt/butterflyguy/data/gateway_minute/`. See the private file inventory for
  exact locations. Presence does not establish a complete recorded session.
- **Captured depth evidence:** five run directories in
  `/opt/schwab-order-book-evidence/`. These are venue-specific captures, not
  consolidated historical depth. Received/written/dropped counts and continuity
  must be audited before strategy use.

Vendor raw data and quote traces remain private and untracked. Gitignore is not
a backup or an access-control mechanism.

## Canonical normalized datasets

The stable cache root is [`data/research_cache/`](../data/research_cache/README.md).
It holds only the canonical datasets below, plus the `spx_0dte` quality reference,
as symlinks into the durable cache
`reports/thetadata_completion/2026-10-01/thetadata-cache/`. The dated records cite
that path, so nothing was moved. Set
`BUTTERFLY_RESEARCH_CACHE=$PWD/data/research_cache` to make it the default.

- `spx_0dte_local_durable_development_20261001`: 585 accepted SPXW 0-DTE
  sessions, requested range 2022-01-03 through 2024-06-28. Existing quality
  assessment `25d9a7474ab2` passes Q1–Q6.
- `spx_0dte_local_durable_spent_holdout_20261003`: 357 accepted sessions,
  requested range 2024-07-01 through 2026-03-12, the spent H-TS1 holdout
  (`holdout_sessions: 357`; post hoc only). Built 2026-10-03 from commit `b7c249d`
  with the development dataset's inputs. 68 sessions were skipped for missing
  index data, 63 of them after the minute files end on 2025-12-09. The first
  assessment, `6de96a50ba75`, failed Q1 on 2025-11-28 only (98.15%: near-the-money
  quotes missing 09:31–09:54 on the post-Thanksgiving half-day). The owner excluded
  that session (`exclude-sessions`; hash `f7077252…` → `8dabf04a…`). Assessment
  `4fef1dbe585d` then passes Q1–Q6. Artifacts are under
  `reports/data_management/2026-10-03/`.
- `spx_0dte_local_durable_validation_20261001`: 128 accepted sessions,
  requested range 2026-03-13 through 2026-09-25. Existing assessment
  `b3c6482ea210` passes Q1–Q4 and Q6; Q5 is not evaluable on the irregular
  recorded index observations.
- `local_support_v1`: supporting index observations and daily inputs. It is
  not a standalone options strategy dataset.

The [completion record](research/thetadata-backtesting-completion-2026-10-01.md)
owns the exact dataset identities, experiment freeze, eligibility ledger, quality
evidence, and reproduction commands. Other imports in the cache are preserved
references or prior imports, not interchangeable aliases for these datasets.
Hidden interrupted-import directories are unpublished staging, not datasets.
Nothing has been deleted or deduplicated as part of this inventory.

## Session quality and exclusion ledger

The [session-ledger implementation and reproduction record](research/spx-session-quality-ledger-2026-10-02.md)
links the private development and validation JSONL artifacts. The research CLI's
`session-quality-ledger` command consolidates immutable inventory/import/audit
and quality evidence, with an optional existing E0 overlay. Dataset-level gates,
per-session measurements, exclusions, and unknown checks remain distinct.
Both canonical ranges reconcile without changing source data or recomputing gates.

## Storage and cleaning conventions

Use the existing locations as three logical layers; migration is not required
to establish ownership:

1. **Raw evidence:** unchanged vendor partitions, broker captures, and original
   supporting files. Preserve source and retrieval metadata and checksums.
2. **Normalized data:** immutable datasets with a manifest, mapping version,
   source references, eligible sessions, exclusions, and quality evidence.
3. **Research output:** experiment plan, code/config hashes, dataset identity,
   registry, results, and traces. Keep outputs associated with their original
   input identity.

Normalized research timestamps already use UTC epoch microseconds. Preserve the
original timezone and bar-start/bar-end meaning in source metadata, and interpret
the exchange session date using America/New_York. Expiration dates and trade dates
are distinct for 1-DTE. Use the exchange calendar for holidays and early closes.

Cleaning must produce a new derived dataset or explicit exclusion record, never
rewrite the raw source. Retain zero bids with positive asks when valid; mark
zero-bid/zero-ask rows as unavailable quotes. Zero-volume, zero-OHLC trade minutes
are no-trade observations. Do not invent prices across gaps or merge providers
without attribution. Record duplicate, crossed, stale, or invalid observations
with their affected source/session and rule. Keep an excluded data session
distinct from a valid session on which the strategy did not trade.

The archive lacks underlying index levels, IV, and Greeks. NDXP/XSP research
requires instrument-specific supporting observations and attributed settlement;
SPX levels and scaled ETFs are not substitutes.

## Refresh and verify

The research package is on `main`. Run these commands from the repository root
of a checkout of `main`. Each command is offline and reads existing inputs.
Choose a new dated output directory for a new inventory snapshot.

```bash
uv run python -m butterfly_guy.research --dataset market_data_inventory \
  inventory-local --archive data/thetadata --out reports/data_management/<date>

uv run python -m butterfly_guy.research \
  --cache reports/thetadata_completion/2026-10-01/thetadata-cache \
  --dataset spx_0dte_local_durable_development_20261001 verify

uv run python -m butterfly_guy.research \
  --cache reports/thetadata_completion/2026-10-01/thetadata-cache \
  --dataset spx_0dte_local_durable_validation_20261001 verify
```

Exact reproduction of a dated record still uses the code it names. For example,
the 2026-10-01 completion record names `.worktrees/thetadata-readiness-2026-10-01`.

Archive reconciliation checks catalog consistency and Parquet row counts for
every partition that is not sealed. Canonical dataset verification
checks manifest-listed hashes and row counts. Neither operation recomputes the
quality gates or proves independent vendor expiration coverage. Update the
consolidated inventory when canonical identities or supporting sources change;
the raw archive command alone does not refresh its dataset/supporting-input entries.

## The spent holdout

The 2024-07-01 through 2026-03-12 holdout was evaluated once, by H-TS1 (run
`ce91c4a08efd`, 2026-09-30, FAIL). Since 2026-10-03 its data is readable:
`holdout.SEALED` is `None`, and the raw files moved into `data/thetadata/`.
`holdout.HOLDOUT` remains its label. Manifests count its sessions as
`holdout_sessions`, so a dataset containing them can never back a registry unseal.
Any result on this window is post hoc and cannot be presented as an unseen test.
A future holdout is sealed by setting `holdout.SEALED`; the guard and its tests
are unchanged.

## Next milestones

1. Expand the metadata inventory into per-instrument session coverage for the
   operational database and remote captures before claiming continuous history.
2. Extend the completed SPXW session quality/exclusion ledger to other instruments
   only after their supporting observations and quality evidence are established.
3. Automate refreshes with explicit source scope, immutable outputs, and alerts
   for changed inputs or coverage failures. Scheduling on a live host is a
   separate operational change.
4. Choose an independent private backup destination, preserve data and provenance
   together, and verify a restore plus replay. Current persistent storage is not
   evidence of an independent backup.
5. Prioritize missing index/settlement observations before broadening options
   imports. Keep any acquisition window explicit and retain provider boundaries.
