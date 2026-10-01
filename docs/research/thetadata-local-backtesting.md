# Offline ThetaData research

Implementation branch: `feat/thetadata-local-replay`, based on
`research/unified-core` at `9ac0fbb`. Worktree:
`/tmp/butterfly-thetadata-implementation`. This extends the existing research
engine, selector, calendar, normalization, exit rules and accounting. It changes
no runtime strategy configuration, services, broker writes or research ledgers.

The older `research/phase1-command-surface` branch at `5d18d94` adds command
consolidation but predates the registrations and subsequent protocol amendments.
It was inspected, not merged over the newer research baseline. The owner's dirty
main checkout and the other worktrees are untouched.

## Baseline and exposure

The cache defaults to `~/.cache/butterfly_guy/research` or
`BUTTERFLY_RESEARCH_CACHE`. Existing schemas 1 and 2 remain readable. Local imports
write schema **3**, distinguishing contract identity and quote observation age.
NumPy/pandas were already locked transitively and PyArrow was already declared in
the development group; no dependency or lockfile changes were necessary.

The existing `spx_0dte` dataset is `c7fff54a…`; the existing vendor dataset is
`spx_0dte_thetadata` at `15ccec37…`. Their manifests and files are unchanged.
The vendor manifest records a passing validation-window quality check and the
owner's two development exclusions, 2022-02-22 and 2022-06-02. `cache-inputs`
preserves those exclusion records in the supporting snapshot; local imports
honor them without deleting raw files.

The protected interval is **2024-07-01 through 2026-03-12**. It has already been
exposed: H-TS1 was registered at sequence 0 (`9051357`, record `06360534…`) and
was evaluated in run `ce91c4a08efd`, recorded at sequences 1–2 (`b95180d`, result
commit `bd53583`). It failed gates 2 and 6. Folder names and old drafts do not
restore unseen status. This implementation performed **no new holdout replay or
registration**. CLI/direct local reads still enforce the existing date policy;
these new commands offer no holdout bypass. Exact reproduction of H-TS1 belongs
in its pinned code/data environment.

Inventory on this implementation run: **23,040 Parquet files, 5,835,648,113 bytes**
across `data/thetadata` and `data/thetadata_sealed`. There are 23,044 catalog
requests, including four `no_data` records for NDXP 2022-12-16. The inventory
artifact groups by root/set/kind/year and checks unprotected Parquet row counts
against the catalog. Protected files are only statted: 6,776 protected Parquet
footers remain deliberately unchecked. A catalog request is not an independently
verified expiration list. Missing weekdays before daily expirations are not
classified as failed downloads.

The owner's minute files are interpreted by the existing loader as
**America/Chicago, bar end**. Stale identical-bar sessions are removed; the final
2025-12-10 SPX tail is stale, leaving 2025-12-09 as the last usable date. The
source/permission of these third-party files remains unknown. The daily Cboe
close, not the last index minute or any option EOD field, is the SPX settlement
input. Recorded index/VIX fallback is restricted to dates after minute coverage
ends and never fills the protected gap.

No NDX/XSP index minute files or normalized research datasets were found locally.
Real NDX/XSP audits therefore report absent index/open/prior-close/settlement
inputs. Their option quotes alone do not make those sessions usable.

## Commands

Run from this worktree with the research dependencies installed. The following
uses private derived storage outside Git. Choose new names for new datasets.
Existing published imports have immutable source/range/mapping identities;
repeating exactly the same request verifies and resumes without rewriting files.
Changed input, mappings or ranges require a new dataset name.

```bash
export BUTTERFLY_RESEARCH_CACHE=/tmp/thetadata-cache
ARCHIVE=/mnt/Repos/Trading/Butterflyguy/data/thetadata
OWNER_DATA=/mnt/Repos/Trading/Butterflyguy/data
REPORTS=/tmp/thetadata-artifacts

# Metadata inventory, including protected file counts without opening those files.
uv run python -m butterfly_guy.research --dataset archive_inventory inventory-local \
  --archive "$ARCHIVE" --archive "$OWNER_DATA/thetadata_sealed" --out "$REPORTS"

# Explicit public daily acquisition. This is the only new command needing network.
uv run python -m butterfly_guy.research cache-daily --directory /tmp/thetadata-daily
# The printed JSON receipt pins filenames, URLs, retrieval times and hashes.
DAILY_RECEIPT=/tmp/thetadata-daily/6130b9dcb70e.json  # use your printed receipt

# Explicit snapshot of already cached supporting observations; no DB/Terminal call.
# --cache here is the input cache, while --output-cache is the new snapshot location.
uv run python -m butterfly_guy.research \
  --cache /home/corey/.cache/butterfly_guy/research --dataset local_support_v1 \
  cache-inputs --input-dataset spx_0dte --daily-dataset spx_0dte_thetadata \
  --start 2026-03-13 --end 2026-09-25 \
  --output-cache "$BUTTERFLY_RESEARCH_CACHE" --out "$REPORTS"

# Audit the requested intersection; inspect the resulting input-audit.json.
uv run python -m butterfly_guy.research --dataset spx_0dte_local_final_validation \
  audit-local --archive "$ARCHIVE" --set spxw_0dte --support local_support_v1 \
  --index-minutes "$OWNER_DATA/spx_1min.csv" --vix-minutes "$OWNER_DATA/vix_1min.csv" \
  --daily-cache "$DAILY_RECEIPT" --start 2026-03-19 --end 2026-03-26 --out "$REPORTS"

# Import the validation window, then run the original approved quality gates offline.
uv run python -m butterfly_guy.research --dataset spx_0dte_local_final_validation \
  import-local --archive "$ARCHIVE" --set spxw_0dte --support local_support_v1 \
  --index-minutes "$OWNER_DATA/spx_1min.csv" --vix-minutes "$OWNER_DATA/vix_1min.csv" \
  --daily-cache "$DAILY_RECEIPT" --start 2026-03-13 --end 2026-09-25 --out "$REPORTS"
# CBOE_SPX is the SPX CSV path in DAILY_RECEIPT; never substitute the JSON receipt.
CBOE_SPX=$(uv run python -c 'import json,sys; print(json.load(open(sys.argv[1]))["SPX"]["path"])' "$DAILY_RECEIPT")
uv run python -m butterfly_guy.research vendor-quality \
  --vendor-dataset spx_0dte_local_final_validation \
  --reference /home/corey/.cache/butterfly_guy/research/spx_0dte \
  --cboe-spx "$CBOE_SPX" --out "$REPORTS"

# Single session: trace/accounting verification, with no registry record.
uv run python -m butterfly_guy.research --dataset spx_0dte_local_final_validation \
  replay-local --start 2026-03-19 --end 2026-03-19 --lifecycle 0dte --out "$REPORTS"

# Development import requires that same-source/mapping validation approval.
uv run python -m butterfly_guy.research --dataset spx_0dte_local_development \
  import-local --archive "$ARCHIVE" --set spxw_0dte --support local_support_v1 \
  --index-minutes "$OWNER_DATA/spx_1min.csv" --vix-minutes "$OWNER_DATA/vix_1min.csv" \
  --daily-cache "$DAILY_RECEIPT" --quality-dataset spx_0dte_local_final_validation \
  --start 2023-11-22 --end 2023-11-24 --out "$REPORTS"
uv run python -m butterfly_guy.research --dataset spx_0dte_local_development \
  replay-local --start 2023-11-22 --end 2023-11-24 --lifecycle 0dte --out "$REPORTS"
```

For variant comparisons, existing SPX `run --profile vendor_1m` remains available
on a 0-DTE local dataset. Its existing development-registry semantics apply.
`replay-local` is the infrastructure verification command and never appends to a
registry. DB exports, existing frozen parity, and existing API imports remain on
the original command surface.

```bash
# Explicit 1-DTE research specification, without enabling live 1-DTE trading.
uv run python -m butterfly_guy.research --dataset spx_1dte_local_final \
  import-local --archive "$ARCHIVE" --set spxw_1dte --support local_support_v1 \
  --daily-cache "$DAILY_RECEIPT" --start 2026-03-19 --end 2026-03-19 --out "$REPORTS"
uv run python -m butterfly_guy.research --dataset spx_1dte_local_final \
  replay-local --start 2026-03-19 --end 2026-03-19 --lifecycle intraday \
  --entry-spec borrowed-0dte-controls --out "$REPORTS"
uv run python -m butterfly_guy.research --dataset spx_1dte_local_final \
  replay-local --start 2026-03-19 --end 2026-03-20 --lifecycle carry \
  --entry-spec borrowed-0dte-controls --expiry-dataset spx_0dte_local_final_validation \
  --exit-policy hold-to-expiry --out "$REPORTS"

# Alternate instruments: audit real missing observations first.
uv run python -m butterfly_guy.research --dataset ndx_0dte_local_example \
  audit-local --archive "$ARCHIVE" --set ndxp_0dte --support local_support_v1 \
  --start 2026-03-19 --end 2026-03-19 --out "$REPORTS"
# Once real NDX supporting inputs exist, import-local uses --set ndxp_0dte and
# --support <NDX-support-dataset>; replay-local selects configs/config_ndx.yaml.
# XSP uses --set xsp_0dte, an xsp_0dte_local_<name> output, XSP supporting inputs,
# and configs/config_xsp.yaml. No SPX/NDX prices are relabeled as XSP.
```

## Mapping and access

The adapter reads only requested per-session quote partitions, projects contract,
timestamp, bid/ask and size columns, and uses the existing within-session
at-or-before reconstruction. Quotes with bid=ask=0 are absent; bid=0/ask>0 is valid.
Midpoints are computed from observed sides. Crossed quotes remain diagnostic
observations and are unpriceable in executable accounting. IV/delta are NaN, and
Greek/IV-dependent capability requests fail explicitly. Trade bars, opening OI and
EOD fields are unused by this observed-price profile, so their absence does not
exclude a session or introduce morning EOD information.

A minute quote row establishes **grid observation time**, not the quote's original
last-update time. `observation_age_s` records elapsed time from the last grid row;
`quote_age_s` is NaN. Observations older than 120 seconds lose executable prices;
existing vendor-quality checks impose their original 60-second freshness bound
on observation age and independently diagnose stagnant markets. Sizes are kept.
Quotes are never carried across sessions or repaired from later/EOD/synthetic data.

Aware New York timestamps convert directly to UTC microseconds. Option root,
underlying, expiration and fractional strikes survive serialization. SPXW/NDXP
use a minimum 5-point listed grid; XSP weekly series may use 0.5 points. Invalid
roots, rights, mixed expirations, duplicate contract timestamps, naive timestamps,
incorrect dates and off-grid strikes are rejected. Trade date is never assumed
to equal expiration in a 1-DTE dataset. Public daily calendars validate Friday /
Monday and holiday gaps as one trading session.

Imports hash every requested raw quote file, including files belonging to excluded
sessions, and preserve those hashes plus supporting identities, schema/mapping
versions, source and range. Staged output is verified before atomic directory
publication. Process locks release on process death; abandoned stages are private
and can be retried without duplicating published sessions. Published datasets are
immutable; resumption checks both raw and normalized hashes. Validation approval
must match source/mapping, current normalized hash and current raw validation
inputs. It cannot be borrowed from the frozen API dataset merely because both
sources are ThetaData.

Date guards run before path resolution and Parquet access, including direct Python
calls, requested-date discovery, alternate roots, symlinks and cataloged protected
expirations on a preceding unprotected trade date. No new command accepts an unseal
flag. An `Unseal` passed to direct source calls still obeys the existing verified
registry/dataset policy; import plans must carry the matching proof themselves.

## Lifecycles, accounting and limits

Each replay independently verifies **one fly**, using the existing live pure entry
selector and existing exit rules. There is no capital, overlap, daily-counter or
portfolio-return model. An overnight loss is reported on that position's ledger;
it is not fed into a fabricated portfolio's next-day sizing or risk budget.

1-DTE is an explicit mechanics experiment: `borrowed-0dte-controls` acknowledges
that the configured intraday VIX anchoring is borrowed from 0-DTE, not a validated
total time-to-expiration model. Intraday adds a mandatory five-minute preclose
exit. Failure to observe a usable exit is unresolved, never settlement against
that day's index close. Carry uses the same expiration/strikes in the entry-day
1-DTE and expiry-day 0-DTE datasets. Peak, trailer/protector memo and confirmation
state persist overnight. Monitoring uses only available daytime observations;
minimum holding age includes elapsed wall time, while regimes use each session's
own clock. No overnight marks are invented. Missing expiry data or a range ending
before expiration leaves an explicit unresolved ledger entry.

`--exit-policy hold-to-expiry` explicitly disables discretionary research exits for
carry mechanics, allowing verification of both sessions and authoritative
settlement. The default retains configured exits. Expiration is recorded on the
position, leg traces, normalized sessions and each accounting fill.

Accounting reprices frozen midpoint decisions; changing executable cash flows does
not resimulate sizing/exit decisions. Midpoint retains the existing paper model,
including its five-cent net exit floor. Marketable entry is lower ask + upper ask
minus twice center bid; exit uses inverse sides. Fees are four contracts per side
at the configured per-contract commission, with multiplier $100 for all three
verified products. Stress is $0.05 per executed contract leg (four times per side).
Cash settlement uses the common intrinsic function and has no exit execution,
stress or closing commission. The one-grid-tick delayed stress and existing
roll-forward accounting remain explicit. Trace artifacts include decision and
actual execution leg quotes, making any roll distinguishable from a trigger.

The owner-approved SPX vendor stressed-exit floor remains opt-in via
`--floor-stressed-exits`; its uses are counted. It is refused for NDX/XSP and is
not a claim that a complex order can close for free. Crossing recorded leg NBBO
is an execution assumption, not proof of a complex-order fill. A one-minute clock
cannot establish intraminute order, fills or trailer paths.

NDXP requires an authoritative **XQC** settlement observation, and XSP requires
an attributed **XSP** settlement input. Their supporting source manifest must
identify `settlement.<asset>.symbol` and `source_url`; an unlabelled daily index
close is not accepted as settlement. Local real audits remain unvalidated until
instrument-specific intraday/open/prior-close/settlement inputs exist. Greeks,
index synthesis, ETF scaling and extra subscriptions are separate tasks.

Contract conventions were verified against primary documentation:
[Nasdaq NDXP factsheet](https://www.nasdaq.com/NDXP-factsheet),
[Cboe XSP specifications](https://www.cboe.com/tradable_products/sp_500/mini_spx_options/specifications),
[Cboe SPX specifications](https://www.cboe.com/zh_CN/tradable_products/sp_500/spx_options/specifications/).
Expiring PM contracts stop monitoring at 16:00 ET (13:00 on scheduled early
closes), even when the raw archive extends to 16:15. XSP's documented settlement
formula does not authorize relabeling SPX intraday levels as XSP observations.

## Verification artifacts

Private artifacts are under `/tmp/thetadata-artifacts`; derived inputs are under
`/tmp/thetadata-cache`; public daily receipts/CSVs are under
`/tmp/thetadata-daily`. They are intentionally not committed. Reports have separate
inventory, supporting-input, normalization, quality, input-audit and replay
identities, source/config/dependency/code hashes and provenance. Nothing writes
vendor prices or owner CSVs into Git.

The real SPXW example on 2026-03-19 resolved a 6505-centered, 50-point PUT fly with
an observed morning drawdown exit; stressed dollar P&L was -190.20 for one fly.
A real 1-DTE 2026-03-19 entry carried to 2026-03-20 settled at 38.52 points, with
750 observed monitoring samples across both sessions. These are mechanics checks,
not an experiment supporting a trading edge. Intraday 1-DTE also produced a
resolved real-data trace. Fixtures verify weekday/holiday gaps, an expiry-day
trailer exit, state persistence, missing second-day data and settlement.

A full-window local vendor-quality run on 128 normalized validation sessions
passed Q1–Q4 and Q6 (final schema-3 run `6da7b68181e8`; the earlier
implementation check was `4089fd0d80a7`). Q5 was not evaluable because recorded
index ticks do not fall on exact minutes, as allowed by the existing approved
protocol; Q5 remains a development check. Different counts from the old 133-session
API validation are explicit supporting-data exclusions, not selection-parity claims.
The final validation import excluded 2026-03-13, 03-16, 03-18, 04-27, 05-04,
05-18 and 06-02 for missing VIX, and 2026-06-01 for missing SPX observations.
The same-source approved development import and replay of 2023-11-22 / 11-24
worked offline. Its quality run `eaa62d419951` passed all six checks, including
Q5 at lag zero on both sessions. That small mechanics sample does not validate
all development dates or restore any holdout. The modest 2026-03-19 → 03-26 replay
resolved six real trades, including three intrinsic settlements; an eleven-point
index-clock gap on 03-25 was disclosed and did not require inventing observations.

Initial timing: a single-session import took 5.13 s, peak RSS 298,252 KiB; six
sessions took 16.49 s, peak RSS 384,388 KiB. Raw quote processing remains bounded
per session. The existing minute-file loader, when explicitly used, loads its
CSV supporting series in memory; archive quotes are never loaded as one full
archive. No performance target or engine rewrite was introduced.
Full-window unchanged-input resumption with both owner minute CSVs loaded took
47.29 s, peak RSS 1,048,680 KiB, and preserved normalized hashes. Its higher memory
reflects those whole supporting CSV series, not loading the raw archive together.

The full suite, focused local tests, frozen 118-trade parity, lint and graph update
are recorded in [the implementation verification log](thetadata-local-verification.md). No new holdout look was run.
