# Research core

`src/butterfly_guy/research/` is the one simulator for SPX 0-DTE butterfly rule
research. It makes paired, stressed, noise-aware comparison the default. The design
rationale is in `docs/reviews/2026-09-27-research-pipeline-review.md` (§2, §3 and §5).
`run_backtest_db.py` and `SimulationEngine` stay the live-parity reference, and nothing
here changes live-trading code.

## Modules

| Module | Responsibility |
|---|---|
| `dataset.py` | Parquet schema, manifest with per-file SHA-256, row counts and export history, hash-checked loading; separately hashed `aux/` files (schema 2) |
| `export.py` | Read-only export (`DataSource`: SSH tunnel via asyncpg, or `docker exec psql`); `--bars-only` settlement refresh |
| `market.py` | Snapshot at or before a time, fly mark and executable-side paths, missing and crossed masks, ATM straddle |
| `accounting.py` | Midpoint, marketable, stressed and delayed-exit stressed fills; imports `execution_accounting` constants |
| `entry.py` | Decision profiles, session loading, entry rules through the live `select_entry_candidate` |
| `learning.py` | Fitted rules (fixed fit window) and learning rules (prior sessions only), with their leakage guards |
| `exits.py` | Exit rules and the monitoring loop; the peak trailer uses the shared `profit_policy` functions |
| `simulate.py` | Variants over sessions (the session is the outer loop, so each is loaded once); fits, histories, exit delay |
| `evaluate.py` | Session vectors, paired moving-block bootstrap, H1/H2, rolling blocks, top-3-removed P&L, fit windows |
| `tieset.py` | Near-tied fly scoring at $0.10 / $0.25 with paired draws, fed from the main replay loop |
| `registry.py` | Append-only, hash-chained variant registry |
| `variants.py` | Named variant catalog: every idea-sweep variant (E0, X1–X5, C1/C2, D1–D4, T1–T6, K1, G1/G2, R1–R5) and HLV1 |
| `shadow.py` | Exploratory paired shadow on an open cohort's recorded sessions (ledger read with `git show`) |
| `latency.py` | Read-only calibration of exit latency from recorded paper trades |
| `event_calendar.py` | The committed, versioned market-event table (`data/market_events_v1.csv`): validation, hash, leakage rule |
| `volindex.py` | Cboe daily VIX-family history and gateway intraday bars as separately hashed `aux/` files; a gateway dump is merged, never replacing bars |
| `features.py` | Pre-entry session features: `events` and the term structure (prior-session closes; completed intraday bars) |
| `diagnose.py` | DESCRIPTIVE E0 breakdowns by event and term structure (no registry record) |
| `holdout.py` | The sealed holdout (2024-07-01 → 2026-03-12) and its registry-verified unseal |
| `history.py` | Vendor history adapter onto the research schema (**no vendor purchased yet**), coverage report |
| `thetadata.py` | ThetaData `HistorySource` (Options Value quotes; SPX/VIX from the owner's minute files and recorded data; Cboe closes) |
| `quality.py` | Data-quality gates Q1–Q6 on a vendor dataset, Helios side by side (`vendor-quality`) |
| `validate.py` | Fidelity validation of a vendor dataset against the Helios export (readiness doc steps 1–4) |
| `hypotheses.py` | Drafted hypothesis rules H-SN1, H-EV1, H-TS1 and optional H-EV2 (catalog `HSN1`, `HEV1`, `HTS1`, `HEV2`; not registered) |
| `mechanism.py` | DESCRIPTIVE H-TS1 mechanism check on Cboe daily closes, development window only (no registry record) |
| `report.py`, `cli.py` | Artifacts and the `python -m butterfly_guy.research` CLI |

## Data

The cache lives outside Git at `$BUTTERFLY_RESEARCH_CACHE`, defaulting to
`~/.cache/butterfly_guy/research/<dataset>/`. The layout is documented in `dataset.py`:

- per session, `chain.parquet` (a dense ts × strike grid for calls and puts, never
  imputed) and `clock.parquet` (the replay's bar clock);
- `sessions.parquet`, `daily_bars.parquet` and `spot_ticks.parquet`;
- `manifest.json`, holding the SHA-256 and row count of every file, a `dataset_hash`
  over them, and a `history` of what each export run changed.

Every file is hash-checked the first time it is read.

```bash
# Through the SSH tunnel (localhost:15432, DSN from .env)
uv run python -m butterfly_guy.research export --start 2026-03-13 --end 2026-09-25
# Or through docker exec on Helios
uv run python -m butterfly_guy.research export --start 2026-03-13 --end 2026-09-25 --source docker
# Re-read only daily_bars, for sessions whose official close had not landed
uv run python -m butterfly_guy.research export --start 2026-03-13 --end 2026-09-25 --bars-only
uv run python -m butterfly_guy.research verify
```

**Read-only export.** Every session runs with `default_transaction_read_only = on` and
a statement timeout. Queries are bounded to one UTC day of `snapshot_time` (or one
week of `spot_prices`), and there is no full-table scan.

**What is kept.** Only sessions with at least 50 0-DTE snapshots are exported. Strikes
are kept within ±400 of the day's spot range, a band wide enough for any strike the
selector or a held position can use. Re-running `export` adds new sessions.

**Pending settlements.** A session whose official close had not yet landed is still
exported; replays hold nothing to settlement on it. `export --bars-only` re-reads
`daily_bars` and nothing else. Each export run appends a `history` entry to the
manifest with:

- the previous and new `dataset_hash`;
- sessions added and refreshed;
- every file whose SHA-256 or row count changed;
- `daily_bars` rows added, removed or changed;
- `settlements_landed` and `pending_settlements`.

A landed close changes `daily_bars.parquet` and therefore the dataset hash. The
registry counts variants by dataset name, so that is expected.

**The 2026-09-27 export** covers 133 sessions from 2026-03-13 to 2026-09-25, is
128 MB, and had dataset hash `dd38a5ecb2cfb08df6e057167c9da06041569da20aab9c30d3bf333e348bc523`.
Two `--bars-only` refreshes on 2026-09-27 (the second in stage 3) found no change, because
Helios `daily_bars` still ended at 2026-09-24.

**2026-09-28 (stage 4): 2026-09-25's official close landed.** A `--bars-only` refresh
changed only `daily_bars.parquet` (292 → 294 rows: the 2026-09-25 SPX bar, O/H/L/C
7709.86 / 7752.07 / 7693.08 / 7743.41, and the `$VIX` bar, close 14.87). No session was
added or refreshed and nothing is pending.

- **Dataset hash now** `b76dc6c9e1c77a4ca15aa2aa4be73bcc86e3c6e5e5314e634d9dacf839ae0f45`.
- The SPX close equals Cboe's published close (7743.41).
- `parity` (the 118-trade frozen comparison, through 2026-09-18) and
  `tests/test_research_sweep_ports.py` (through 2026-09-24) pass unchanged. Neither covers
  2026-09-25, which is now replayable under every profile.
- The cohort's recorded sessions (2026-09-22 → 2026-09-24) are all in this export.

**2026-09-28 (stage 5): no change.** A second `--bars-only` refresh (21:17 UTC) added,
refreshed and changed nothing; the dataset hash stays `b76dc6c9…`. The export still ends
at 2026-09-25.

**2026-09-28 (stage 6): session 2026-09-28 added.** `export --start 2026-03-13 --end
2026-09-28` (tunnel, 23:31 UTC, after the close) exported one new session: 2026-09-28, with
376 snapshots × 158 strikes. Its files are `chain.parquet` (59,408 rows, `cb6f4dbb…`) and
`clock.parquet` (376 rows, `6da9f987…`). `sessions.parquet` went from 133 to 134 rows and
`spot_ticks.parquet` from 109,078 to 109,830.
- **Settlement.** 2026-09-28's official close had not landed, so it is pending. A
  `--bars-only` refresh straight after changed nothing. No other settlement was pending.
- **Dataset hash now** `c7fff54a1ffa7c4ee368a6d341828e792d65f7da6cfe27cd40300fae9e625182`
  (134 sessions, 2026-03-13 → 2026-09-28). It will change again when that close lands.
  `tests/test_research_features.py` pins it, with a comment.
- `parity` (118 trades, 0 mismatches, $17,691.60 / $14,170.60 / $9,890.60) and
  `tests/test_research_sweep_ports.py` pass unchanged. Their windows end at 2026-09-18 and
  2026-09-24.

**Adding another data source.** Implement `DataSource.copy_csv`, or write the same
Parquet schema directly. The simulator never touches the database. For vendor history, see
`docs/research/history-vendor-readiness.md` (adapter spec and validation plan).

### Auxiliary inputs (manifest schema 2)

Feature inputs from sources other than the Helios export live under `aux/` in the same
dataset. They are listed and hashed separately (`aux`, `aux_hash`), so adding or
refreshing one never changes `dataset_hash`: `dd38a5ec…` stays the hash of the chain data.

- A manifest without aux files is still written as schema 1, byte for byte as before.
  One with aux files is schema 2; the loader accepts both.
- Every aux write appends a `history` entry (`mode: aux`) with the rows added, removed
  and revised, and the previous and new `aux_hash`.
- `verify` checks aux files with the rest.

**Recording inputs in a run.** A run records the calendar hash and the aux hash in its
meta **only when it uses them**. Runs that use no features (every catalog variant today)
keep their results unchanged, so the published `results.json` hashes and run ids above
stay valid.

### Event calendar

`src/butterfly_guy/research/data/market_events_v1.csv` is committed. It covers
2022-01-01 → 2026-12-31 (as known on 2026-09-27): FOMC statement days, CPI, NFP (the BLS
Employment Situation) and PCE (BEA Personal Income and Outlays) release days, monthly
OPEX, quarter-end and NYSE early closes.

- **Columns.** Each row carries its `source` and the date that schedule was public
  (`published_on`), with the basis and the page that shows it (`published_source`). The
  full column list is in `event_calendar.py`.
- **Building it.** The table is built by `tools/build_market_events.py`, which caches
  every page it reads (default `~/.cache/butterfly_guy/research/_sources/market_events/`).

**How `published_on` is established:**
- FOMC: the Fed's tentative-schedule press release for the year.
- CPI, NFP and PCE: the previous release, which names the next date
  (`prior_release_notice`).
- The 2025 and 2026 appropriations-lapse reschedules and cancellations, and BEA's 2026
  moves: dated notices, or the earliest archive capture that carries the change.
- Dates after the latest release: the agency schedule page, dated by when it was read.
- OPEX, quarter-end and early closes: the earliest archived NYSE holiday page listing the
  year.

Archive and fetch dates are upper bounds on the real announcement. That can only hide an
event from a session, never reveal one early.

**Leakage rule.** An event is a feature for session S only when all of these hold:
- it is not `unscheduled` (the 2025-08-22 FOMC notation vote is the one such row);
- `published_on < S`;
- it had not been withdrawn before S (`withdrawn_on` empty or `>= S`).

`held` (whether it happened) is never used. A release still expected on S and later
cancelled stays an expected event for S. `features.SessionFeatures.events(S)` returns the
visible event types. `MarketEvent.before(10:00)` is strict, so a 10:00 release does not
count as known at a 10:00 decision.

**Version 1** has 313 rows and sha256
`3185297d2421b53c7d672b85d4a922e41eeddb5c48815477719aed7e58385b93`.

- Each year 2022–2026 has 8 FOMC statement days, 12 OPEX and 4 quarter-ends, and 12 each
  of CPI, NFP and PCE, except where a lapse cancelled or merged a release:
  - 2025: 11 CPI and 11 NFP (October cancelled), 10 PCE (October and November combined
    on 2026-01-22).
- 11 early closes.
- OPEX moved to the Thursday on 2022-04-14 and 2025-04-17 (Good Friday) and on
  2026-06-18 (Juneteenth).
- 17 withdrawn or rescheduled release rows cover the 2025 and 2026 lapses, BEA's
  post-lapse schedule and its 2026-09-30 → 10-06 move.
- One known gap: January 2026 NFP's original 2026-02-06 date has no row. The release
  that announced it (2026-01-09) has no archived copy, so only the rescheduled 2026-02-11
  row (published 2026-02-05) exists.

```bash
uv run python tools/build_market_events.py --today 2026-09-27   # rebuild (network)
uv run python -m butterfly_guy.research verify                  # prints the calendar sha256
```

### Volatility term structure

**Where the history can come from** (checked 2026-09-27):

- **Helios DB:** nothing. `spot_prices` and `daily_bars` hold only SPX, NDX, XSP and
  `$VIX`; `$VIX` daily bars start 2026-03-02.
- **Schwab gateway** `/v1/session-history`: 1-minute regular-session bars for `$VIX`,
  `$VIX9D` and `$VIX3M`, stamped at the **bar start** (`$SPX` returns 390 bars,
  09:30 → 15:59).
  - Retention is about 30 sessions: the earliest bars are from 2026-08-12.
  - `$VIX1D` (and `VIX1D`, `$VIX1D.X`) returns no bars.
  - `/v1/history` rejects `$VIX1D` with 400.
- **Cboe public daily files** (`cdn.cboe.com/api/global/us_indices/daily_prices/<INDEX>_History.csv`,
  no sign-up): OHLC for VIX (1990→), VIX9D (2011-01-04→), VIX3M (2009-09-18→) and
  VIX1D (2022-05-13→).

**What was added to `spx_0dte`:**

| File | Rows | SHA-256 | Source |
|---|---:|---|---|
| `aux/vol_index_daily.parquet` | 18,613 | `048eb3de…` | Cboe daily files, fetched 2026-09-28 06:18 UTC; every index through 2026-09-25 |
| `aux/vol_index_intraday.parquet` | 38,899 | `b8c47604…` | Gateway dumps 2026-08-03 → 2026-09-25 (`699420d1…`) and → 2026-09-28 (`ccf781f6…`), merged |

`aux_hash` is now `cb12502b721efeda92f06f55f35273e26b101ecaa3a847e7339a628445144967` (stage 5;
`b6175510…` in stages 3 and 4, when the intraday file had 37,343 rows, `d4a54490…`).
`dataset_hash` was unchanged by the aux files (`dd38a5ec…` at the time; `b76dc6c9…` after
the 2026-09-25 close landed).

**Refresh on 2026-09-28 (stage 4): no change.**
- `export-vol --cboe` re-read the four Cboe files: 0 rows added, removed or revised.
- The gateway dump was re-run the same way (2026-08-03 → 2026-09-25). Its output is
  byte-identical to stage 3's (sha256 `699420d1…`), because no session had closed since.
  Ingesting it changed nothing.
- `aux_hash` is still `b6175510…`.
- **Ingest replaced, it did not merge** (fixed in stage 5, below).

**Stage 5 (2026-09-28): the intraday ingest merges.** `ingest_intraday` now merges a dump
into the file (`volindex.merge_intraday`):
- bars already in the file and absent from the dump are kept;
- bars only in the dump are added;
- a bar in both with different OHLC takes the dump's value, and the history entry lists it
  under `revised` (old and new);
- a bar with a different `bar_seconds` on the same key raises;
- the write refuses any table that would remove an existing row (`allow_removal=False`),
  before anything is written.

Each history entry also records `dump_sha256`, `dump_rows` and `kept_not_in_dump`. The
file's `source.dumps` lists every dump ingested; stage 3's dump was converted into the first
entry.

**Refresh on 2026-09-28 (stage 5).** The gateway dump was re-run the same way, over
2026-08-03 → 2026-09-28 (the session had closed; dump sha256
`ccf781f6b3181c1d7364122469ced82d717996c2a9a86ae452c48ae93d2624aa`, 164 records, no errors).
- Retention still starts at 2026-08-12 for `$VIX`, `$VIX9D` and `$VIX3M`.
- **`$VIX1D` returned bars for the first time**, for 2026-09-28 only (389 bars, 09:31 →
  15:59 ET); every earlier date still has none.
- The merge added 1,556 bars (2026-09-28, four indices), removed 0, revised 0, and kept 0
  bars that the dump lacked. The file is now 38,899 rows, sha256
  `b8c47604ed1205ba4db84487627dc868d58c2764bd58236cc6f748ea598d532c`.
- `aux_hash` `b6175510…` → `cb12502b…`; `dataset_hash` unchanged (`b76dc6c9…`).
- 2026-09-28 is not an exported session, so no feature on the 133 sessions changed.

**Refresh on 2026-09-28 (stage 6): no change.** The dump was re-run the same way over
2026-08-03 → 2026-09-28, the last completed session (ingested 23:36 UTC).
- **The output is byte-identical to stage 5's:** sha256 `ccf781f6…`, 164 records, no
  errors. No session had completed since.
- **Ingest was a no-op:** 0 bars added, removed or revised, and `kept_not_in_dump` 0.
  Retention still starts at 2026-08-12 (33 sessions), so the merge has not yet had to keep
  a bar the gateway dropped.
- `aux_hash` stays `cb12502b…`; `dataset_hash` is `c7fff54a…` (the new session, above).
- **`$VIX1D` intraday is still 2026-09-28 only.** Whether it now arrives every session
  cannot be told until 2026-09-29 closes; re-check at the next dump.
- Cboe daily files were not re-read in this stage.

**Coverage of the 134 sessions (stage 6):**
- Daily prior-session closes for VIX, VIX9D, VIX3M and VIX1D: 134 of 134. For 2026-09-28
  they are 2026-09-25's (VIX1D/VIX 0.841).
- Intraday VIX, VIX9D and VIX3M at 10:00: 31 sessions (2026-08-12 onward, plus 2026-09-28).
- Intraday VIX1D at 10:00: 1 session, 2026-09-28 (7.88, against VIX 15.83).

The intraday file is shipped for the forward record and future use. It is too short for
any breakdown here, and `$VIX` intraday was already in `spot_ticks`.

**Feature rules (`features.py`):**
- Daily: the close on the previous SPX session only, from the dataset's `daily_bars`.
  - Cboe prints VIX on some NYSE holidays (for example 2026-05-25, 06-19, 07-03 and
    09-07); those rows are not the previous session and are skipped.
  - An index with no row on the previous session is missing.
- Intraday: the close of the last bar complete at or before the decision
  (`ts + bar_seconds <= decision`), at most 5 minutes old.
- Ratios: `vix1d_vix`, `vix9d_vix` and `vix_vix3m`.
- Missing stays missing.

```bash
uv run python -m butterfly_guy.research export-vol --cboe
# where the gateway key lives (read-only GETs), then ingest locally:
ssh billy@helios 'docker exec -i butterfly_spx_app python - 2026-08-03 2026-09-25' \
  < tools/research_gateway_vol_dump.py > vol_dump.jsonl
uv run python -m butterfly_guy.research export-vol --gateway-dump vol_dump.jsonl
```

Because retention is about 30 sessions, a longer intraday record needs the dump re-run
at least monthly. A scheduled job for it would be a new service and is not set up.

### Overnight futures (ES): audit only

- **Helios DB:** no futures data. `bars_1m`, `trades` and `l2_book` are crypto (BTC).
- **Schwab gateway:** `/v1/session-history` for `/ES` with `session=extended` returns
  1-minute bars from 04:00 to 16:59 ET only, so the 18:00–04:00 Globex overnight is
  missing.
  - Retention is shorter than the VIX family: 2026-08-14 has none, 2026-08-21 does.
  - `/v1/history` rejects `/ES` with 400.
  - A prior 16:00 → 09:29 ES move is computable only inside that retention window.
- **Free sources:** none licensed. CME DataMine and Databento `GLBX.MDP3` are paid, and
  unofficial scrapes (for example `ES=F`) were excluded.
- **Nothing was ingested.** A usable overnight signal needs either a paid CME history or
  a forward-only recorder.

## Decision profiles

A profile fixes what a replay could see and when.

| Profile | Clock and spot | Open | Prior close | Other |
|---|---|---|---|---|
| `live` (default) | Replay bars (every SPX snapshot that day) | `daily_bars.open` | `daily_bars` close | ≥ 50 snapshots; VIX and prior VIX close required |
| `frozen_20260921` | Replay bars | First bar at or after 09:30 | Last SPX tick ≤ 16:00 on an earlier day | as `live`; this is `run_backtest_db.py` at `b83c2a18` (the frozen replay and the open cohort) |
| `sweep_20260925` | 0-DTE chain snapshots, 09:30–16:00 | First SPX tick at or after 09:30 | `daily_bars` close | Integer strikes within ±200 of spot; timestamps rounded to whole seconds, as that export's `::bigint` cast did |
| `vendor_1m` | The vendor dataset's 1-minute grid, 09:31 → 16:00 ET (13:00 on early closes), with the vendor SPX index (or a flagged parity spot) | Vendor `daily_bars.open` | Vendor `daily_bars` close | Integer strikes; ≥ 50 grid points; VIX and prior VIX close required. For vendor datasets only (`history.py`) |

Selection goes through the live `select_entry_candidate` wherever a rule uses the
baseline's selector. The straddle-anchored rules (C1/C2, T1–T6) use it too: they pass a
one-bucket config holding the entry VIX's widths, and the VIX whose implied move equals
1.25 × the ATM straddle. The EV selectors (G1/G2) and the ATM fly (D4) choose flies
themselves. R3/R4 rank the live `ButterflyBuilder`'s candidates. The trailer is
`PeakTrailer.from_config`, which reads `configs/config.yaml`.

## Accounting and evaluation

**Accounting** is the 2026-09-21 set:

- Decisions are made on marks.
- Fills use the snapshot recorded at or before the decision.
- Exits roll forward past missing or crossed snapshots, and cash-settle as the fallback.
- Settlement is free, against the official close, via `fly_settlement_value`.
- A missing or crossed entry leaves the trade unpriced; nothing is imputed.
- The midpoint model keeps `paper_exit_price`'s 0.05 exit floor, for parity with the
  reference.

**Stressed-exit floor** (`--floor-stressed-exits`, off by default; the owner's decision of
2026-09-29 for the vendor sweep, Revision 1 of the pre-registration draft):
- An intraday exit in `stressed` and `stressed_delayed` whose net proceeds per fly are below
  $0 is booked at $0. Net proceeds are credit minus commission and stress.
- `trades.jsonl` marks such a fill `exit_floored`.
- The run meta records `accounting.stressed_exit_floor`, which gives the run a new id, and
  the report says so.
- Midpoint, marketable, entries and cash settlement are unchanged.
- Off, nothing changes: the frozen parity `trades.jsonl` is byte-identical
  (`b5b732ad…`). This matters because Helios data has such exits too: 3 of the 118
  frozen-parity trades and 40 exits across the idea-sweep catalog.

**Exit-latency stress** (review §5) adds a fourth model, `stressed_delayed`, shown as
"Delayed" next to the stressed figures:

- It is stressed marketable, with every intraday exit filled from the snapshot at or
  before the decision-clock time `--exit-delay` ticks (default 1) after the trigger.
- The fill is always at least that many recorded snapshots after the trigger's, so a
  clock denser than the chain still delays it.
- From there it rolls forward past unusable markets and falls back to settlement.
- Entries, triggers, held trades and the other models are unchanged.

**Calibration.** `calibrate-latency` reads recorded paper trades read-only. It issues
one `butterfly_trades` query per session and one `monitoring_leg_quotes` aggregate per
trade and UTC day.

- The live loop writes a trade's last monitoring snapshot on the poll that fired the
  exit. So `exit_time` minus that timestamp is the trigger-to-fill latency.
- The run for 2026-03-13 → 2026-09-25 found 67 intraday exits with monitoring rows. The
  earliest is 2026-06-04.
  - Latency: median 0.9 s, p90 67.5 s, maximum 310 s.
  - `pending_exit.signal_time` agrees: median 0.7 s over the 55 trades that have it.
  - The live poll interval is 2.8 s and the collector interval 62 s.
  - Measured in collector snapshots, 49 fills landed before the next snapshot, 14 one
    snapshot later and 4 later still.
- p90 is one snapshot, so the calibrated delay equals the fixed one-snapshot stress.
- The slow tail comes in steps of about 66 s (66, 132, 212 s), which looks like paper
  order-ladder steps.
- Paper exits fill on a simulated ladder, so these latencies are lower bounds on live
  broker latency.

```bash
uv run python -m butterfly_guy.research calibrate-latency --start 2026-03-13 --end 2026-09-25
```

**Evaluation.** Every arm is scored on the same sessions, with zeros on no-trade days.
A session with several trades (D3) counts their sum. If any entry on a session cannot
be replayed without imputing data, that session is dropped for every compared arm.

The difference from the baseline is bootstrapped with one draw of 5-session blocks
applied to both arms (5,000 reps, seed 1, the idea sweep's algorithm). Below 20
sessions no interval is reported. Each run also reports:

- H1/H2 (split 2026-06-18);
- 20-session rolling blocks;
- net P&L with the top three trades removed;
- return on stressed debit;
- for fitted rules, figures after the fit window;
- **tie-set robustness at $0.10 and $0.25, by default** (`--no-tieset` skips it). Rules
  whose flies do not come from the live selector are reported as not applicable.

The full 26-variant catalog, tie-sets included, runs in about 85 s. E0, X1 and R1 alone
take 9 s.

## Rules that learn

**Fitted rules** (K1, R2): `FittedFilter` fits one threshold (the median of a feature
over the base rule's entries) on a fixed window.

- **Fitting.** It happens before the run through a `WindowedLoader`, which raises on any
  session outside `[fit_start, fit_end]`.
- **Recorded definition.** The fit window, fitted value and sample size are part of it,
  under `entry.fitted`.
- **Definition hash.** It covers the procedure (feature, statistic, window, base rule)
  but not the fitted value, so the same registered procedure keeps its identity when it
  is re-fitted. The fitted value is fingerprinted in `results.json`.
- **K1 and R2 are reproduced as published.** They are fitted on H1 and applied to every
  session, so H1 is in-sample for them. Reports carry a "Fitted rules" table giving the
  sessions inside the window and the net and Δ after it. Only the after-window figures
  are out of sample.

| Rule | Fit window | Feature | Fitted value | n |
|---|---|---|---:|---:|
| K1 | 2026-03-13 → 2026-06-18 | (entry ask − mark) / mark | 0.050420168067227066 | 59 |
| R2 | 2026-03-13 → 2026-06-18 | VIX move / (1.25 × ATM straddle) | 2.227506137134594 | 59 |

(Values under `sweep_20260925`; another profile re-fits on its own E0 entries.)

**Learning rules** (G1/G2 `EVSelector`, R3/R4 `EVRankEntry`) learn a settlement
z-distribution from prior sessions.

- The runner keeps one `History` per rule. `decide` receives only the records dated
  before the session.
- A session's own observation (which uses its official close) is appended only after
  every variant has decided on it. `History.append` refuses anything out of date order.
- A learning rule cannot be run without the runner's history.
- Observation starts at the rule's `history_start` (2026-03-13), whatever the
  evaluation window, so a short window such as the cohort shadow still sees the full
  prior history. Sessions before the window are observed, never scored.
- Each learner trade records `history.n` and `history.last`, and `history.last` is
  always before the trade's session.

## Registry

`reports/research/registry/spx_0dte.jsonl` is append-only and hash-chained; `verify`
checks the chain.

- **Stage of an evaluation.** An `evaluate` record is `pre` only when the variant was
  registered beforehand: with `register`, in a `pre` backfill, or by a `port` of one.
  Anything else is `post`.
- **Backfill.** The file was seeded with the 49 variants tried on this data before it
  existed:
  - the 26 in the idea sweep's `REGISTRY.md` (21 pre, 5 post);
  - the 5 MA direction rules;
  - the 18 call-only filters from the 2026-09-25 journal entry. Four of these are
    placeholders, because the journal says eighteen but lists fourteen.
- **Ports.** Sixteen idea-sweep variants were backfilled as descriptions in words, because
  they had no code here yet. A `port` event links each executable definition to its
  placeholder (`ported_from`). It inherits the placeholder's stage (C1 stays pre, R2
  stays post), and the two hashes count as one definition.
- **Variant counts.** Reports show how many distinct definitions have been tried on the
  dataset name.
- **Provenance of registrations.** Since stage 4, a `register` record also stores
  `git_sha`, `git_dirty` and the dataset's current `dataset_hash` (None if the dataset is not
  exported yet). The holdout unseal requires a clean tree and development-only data, so a
  registration without these can never unseal anything.

```bash
uv run python -m butterfly_guy.research register --variants HLV1 --note "before the H-LV1 test"
uv run python -m butterfly_guy.research port --variants C1,C2 --note "ported in stage 2"
```

## Parity with the frozen replay

`frozen_ledger_b83c2a18.json` holds the per-trade output of `run_backtest_db.py` at
`b83c2a18` with `--execution-accounting-report`, regenerated read-only on 2026-09-27.

E0 under `frozen_20260921` reproduces it **trade by trade**, with no tolerance beyond
half a cent per trade for float noise:

| Accounting | Net P&L |
|---|---:|
| Midpoint | $17,691.60 |
| Marketable | $14,170.60 |
| Stressed | $9,890.60 |
| Stressed, exit one snapshot late | $9,408.20 |

- 118 trades: 22 cash-settled and 96 intraday (47 / 15 / 34 by regime).
- 2026-03-13 and 2026-03-16 are skipped for missing prerequisites.
- Expectancy, profit factor, win rate, median, maximum drawdown and top-3 share all
  match the journal.
- The exit-latency stress costs $482.40 over the 96 intraday exits, $5.03 per exit on
  average: 40 worse, 40 better, 16 unchanged. One exit fell back to settlement.

```bash
uv run python -m butterfly_guy.research run --variants E0 --profile frozen_20260921 \
  --start 2026-03-13 --end 2026-09-18
```

Run `251c08553fcb`: `results.json` `86828eced1519f729e1ae69b0cfee641483730b0d62cf427c2882e52049e33b1`,
`trades.jsonl` `b5b732adb3812a1d1933a0a63041c52c63439d48b4c3914aec5bf8aabf536529`.

**Where the old residual came from.** The idea sweep reported $17,634.60 / $9,830.60
(midpoint / stressed) and attributed the gap to the decision clock. Switching the sweep
profile's settings one at a time toward the frozen profile shows the clock was not the
cause:

| Change applied to the sweep profile | Midpoint | Stressed |
|---|---:|---:|
| None (as published) | $17,634.60 | $9,830.60 |
| Exact timestamps, not rounded to whole seconds | $17,603.60 | $9,805.60 |
| Plus all strikes, full-day bar clock, first-bar open | no change | no change |
| Plus the frozen prior close (last SPX tick ≤ 16:00) instead of `daily_bars` | $17,691.60 | $9,890.60 |

The prior-close source flips gap direction on a few sessions and accounts for the
remaining gap. The sweep's second rounding offsets part of it.

The `live` profile reproduces the journal's official-input gap rule (2026-03-13 →
2026-09-25, 123 trades, +$22,720 midpoint).

**Tests:**

- `tests/test_research_parity.py` always runs on a committed six-session fixture
  (`tests/fixtures/research/mini_spx`, rebuilt by `build_fixture.py`).
- When the cache is present, it also runs the full 118-trade comparison
  (`-m research_data`).

## Reproducing the idea sweep

Every variant in `docs/research/spx-idea-sweep-2026-09-25/` (round 1 and the post-hoc
round 2) is in the catalog. Each reproduces its `results.json` / `results_round2.json`
row to the dime, with three documented float ties (below). The fields checked are:

- trade count, stressed net, H1 and H2;
- midpoint net;
- the paired 90% CI against E0 and P(better);
- the settled-exit count.

```bash
uv run python -m butterfly_guy.research run --profile sweep_20260925 \
  --start 2026-03-13 --end 2026-09-24 --variants \
  E0,X1,X2,X3,X4,X5,D1,D2,R1,R5,C1,C2,D3,D4,T1,T2,T3,T4,T5,T6,K1,G1,G2,R2,R3,R4
```

| Variant | Trades | Stressed net | H1 | H2 | Midpoint net | 90% CI vs E0 | P(better) | Delayed net | Tie-set avg ($0.10) | Match |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| E0 | 122 | 10,424 | 17,031 | −6,607 | 18,504 | — | — | 9,947 | 10,982 | exact |
| X1 | 122 | 5,051 | 14,344 | −9,293 | 9,618 | −9,468 / −5,727 / −660 | 0.0318 | 5,051 | 6,111 | exact |
| X2 | 122 | −2,574 | −1,143 | −1,431 | 3,901 | −26,363 / −12,785 / −93 | 0.0492 | −2,939 | −1,282 | exact |
| X3 | 122 | −3,079 | −2,431 | −647 | 4,290 | −28,481 / −13,162 / 252 | 0.0552 | −2,999 | −2,973 | exact |
| X4 | 122 | −625 | 7,489 | −8,114 | 8,303 | −20,764 / −10,956 / −3,652 | 0.0006 | 258 | −858 | exact |
| X5 | 122 | −4,044 | 3,448 | −7,493 | 5,031 | −22,691 / −14,244 / −7,230 | 0.0 | −3,924 | −2,825 | exact |
| C1 | 4 | −150 | 185 | −335 | 1,292 | −27,250 / −10,045 / 4,386 | 0.1372 | −515 | −158 | exact |
| C2 | 4 | 1,292 | 248 | 1,044 | 2,504 | −25,743 / −8,760 / 5,844 | 0.1744 | 1,292 | 1,269 | exact |
| D1 | 123 | 2,505 | 11,208 | −8,703 | 10,521 | −24,149 / −8,092 / 7,414 | 0.1912 | 2,022 | 3,380 | exact |
| D2 | 123 | −7,219 | −2,416 | −4,802 | 1,858 | −37,844 / −17,302 / 1,091 | 0.0622 | −6,564 | −8,902 | float tie |
| D3 | 245 | 3,206 | 14,615 | −11,409 | 20,363 | −16,420 / −7,678 / 2,392 | 0.103 | 3,383 | 2,080 | float tie |
| D4 | 123 | −19,272 | −11,377 | −7,895 | −11,078 | −55,063 / −28,388 / −4,990 | 0.0232 | −19,272 | n/a | exact |
| T1 | 2 | −505 | −275 | −230 | −186 | −27,512 / −10,461 / 3,906 | 0.1272 | −715 | −505 | exact |
| T2 | 2 | −370 | −243 | −128 | −270 | −27,369 / −10,347 / 4,035 | 0.131 | −370 | −370 | exact |
| T3 | 2 | −740 | −525 | −215 | −182 | −27,942 / −10,715 / 3,817 | 0.1262 | −745 | −745 | exact |
| T4 | 2 | −745 | −513 | −233 | −385 | −27,920 / −10,722 / 3,800 | 0.1254 | −745 | −749 | exact |
| T5 | 1 | −780 | −780 | 0 | 112 | −27,866 / −10,763 / 3,982 | 0.1204 | −710 | −780 | exact |
| T6 | 1 | −988 | −988 | 0 | −128 | −28,096 / −11,041 / 3,856 | 0.1156 | −988 | −988 | exact |
| K1 | 48 | 11,560 | 15,474 | −3,914 | 14,521 | −8,490 / 1,965 / 10,287 | 0.6348 | 11,540 | 11,441 | exact |
| G1 | 112 | 12,221 | −346 | 12,567 | 16,428 | −21,946 / 1,825 / 25,489 | 0.5544 | 12,221 | n/a | exact |
| G2 | 112 | 10,084 | −16,122 | 26,206 | 14,480 | −35,308 / 116 / 36,846 | 0.5034 | 10,084 | n/a | float tie |
| R1 | 67 | 12,722 | 17,086 | −4,364 | 17,124 | −3,737 / 3,014 / 8,670 | 0.777 | 12,362 | 13,100 | exact |
| R2 | 55 | 3,700 | 9,298 | −5,598 | 7,467 | −17,521 / −6,263 / 3,165 | 0.149 | 3,480 | 4,561 | exact |
| R3 | 106 | 4,617 | 10,193 | −5,577 | 11,717 | −17,976 / −5,535 / 3,430 | 0.1768 | 4,739 | n/a | exact |
| R4 | 106 | 2,436 | 9,860 | −7,424 | 6,341 | −19,530 / −7,923 / 1,102 | 0.0748 | 2,436 | n/a | exact |
| R5 | 73 | 11,135 | 16,577 | −5,443 | 15,773 | −8,353 / 1,697 / 9,465 | 0.6232 | 11,240 | 11,291 | exact |

This is a reproduction of development research, not new evidence. All 26 were chosen
or examined on these sessions, and K1/R2 are in-sample in H1.

**Output** (run `8202c5a26854`, dataset `dd38a5ec…`, config `d120b63f…`, 85 s; the files
are byte-identical on repeat runs):

- `results.json`: `41404b3ea9998e677f9f6d3a26235af6aa7568f929d5111a69b46988845b5b6e`
- `trades.jsonl`: `f54a7aeb9e7a0b4f960b9e4fd8edcf8cbf9315d43b2c98c2b3bc3f377ef76173`

The artifacts are written under `reports/research/spx_0dte/<run id>/`. Like other
research output, run artifacts are not versioned; the command and hashes above
reproduce them. The registry under `reports/research/registry/` is versioned. The
stage-1 hashes for `--variants E0,X1,R1` (run `1a2bcc31999d`) no longer apply, because
`stressed_delayed` added a model to every file.

**Why the hashes are stable.** Only data-determined content goes into `results.json`
and `trades.jsonl`: the dataset hash, profile, config hash, variant definitions (with
fitted values), exit delay and evaluation parameters. Git SHA, run time and registry
counts go to `provenance.json` and the registry, so the hashes stay the same across
commits unless behavior changes.

**Tests.** `tests/test_research_sweep_ports.py` (`-m research_data`) checks every row
above against the published JSON and pins the three ties. Synthetic unit tests cover the
rule mechanics:

- the EV selector's choice and crossed-leg rule;
- straddle-anchored selection inputs;
- the leakage guards;
- multi-trade pairing;
- delayed fills.

## Shadow on the open cohort

`shadow` scores variants paired against E0 on exactly the sessions the prospective
cohort has recorded. It is exploratory: a handful of sessions, no confidence interval,
and nothing feeds back into the cohort.

- **Reading the ledger.** It reads `daily_runs.jsonl` and `trades.jsonl` with `git show
  <ref>:<path>`, the ref defaulting to `origin/cohort/<id>`. It does not fetch and never
  opens a file in the cohort worktree. Every record hash and trade identity is checked
  with the cohort runner's own `canonical_hash` and `trade_key`.
- **Sessions.** Every recorded `session_date`, traded or not. Deferred sessions are not
  recorded, so they are excluded.
- **Profile.** `frozen_20260921`, which is what the cohort runs. Before any shadow is
  reported, E0 must match the cohort's recorded trades: the fly, the entry time, the
  exit reason and P&L in all three models. The report states the result.
- **History.** Fitted and learning rules use their full history from 2026-03-13; only
  the cohort's sessions are scored.
- **Output.** Only `reports/research/`, with a registry record tagged
  `scope: shadow:<cohort>`.

```bash
uv run python -m butterfly_guy.research shadow --cohort spx-prospective-2026-09-22 \
  --variants E0,HLV1,R1
```

On 2026-09-27 (ledger `70ccb8e`, sessions 2026-09-22 → 2026-09-24), E0 reproduced all
three cohort trades exactly:

| Session | E0 | HLV1 | R1 | HLV1 − E0 | R1 − E0 |
|---|---:|---:|---:|---:|---:|
| 2026-09-22 | −225 | 0 | 0 | +225 | +225 |
| 2026-09-23 | +1,164 | +1,164 | 0 | 0 | −1,164 |
| 2026-09-24 | −270 | −270 | 0 | 0 | +270 |
| Total | +669 | +894 | 0 | +225 | −669 |

Three sessions say nothing about either rule. HLV1 skipped one low-VIX call (09-22),
and R1 skipped all three sessions (entry VIX below 17). Run `b10a02d93d13`:
`results.json` `b1bbdb472184f8a9362cf986996b2ea8a310a6d929ac7c66e7530b8a4e219e93`,
`trades.jsonl` `741e116377b0c2314efcd4a770f5350a993f2dc31a04e68f1a60c9444b3f5e63`. The run id
includes the ledger commit, so it changes as the cohort appends.

**Not re-run in stages 4, 5 or 6.** In stage 6 (2026-09-28, about 23:32 UTC) the ledger read with
`git show` was still `70ccb8e` locally and on the remote, with 2026-09-22 → 2026-09-24
recorded. No session after 2026-09-24 has been recorded, so there is nothing new to shadow.

## Diagnostics (descriptive only)

`diagnose` breaks E0 down by scheduled event and by term-structure bucket.

- **Nothing here evaluates a rule.** It writes no registry record, reports no intervals
  or p-values, and every artifact is headed "DESCRIPTIVE — development data — not a rule
  evaluation".
- **Columns in every cell:** sessions and trades (all/H1/H2), stressed and delayed-exit
  nets (all/H1/H2 and per session), tie-set averages at $0.10/$0.25, settled landings,
  and the RMS and mean |move| after 10:00 in chain-implied σ.
- **Buckets:** term-structure buckets are sample terciles (data-derived; the bounds are
  printed), plus the fixed VIX/VIX3M = 1 split.
- **Inputs recorded:** the run's meta carries the calendar sha256 and the `aux_hash`.

```bash
uv run python -m butterfly_guy.research diagnose   # sweep_20260925, 2026-03-13 → 2026-09-24
```

Run `90673e0c138b` (2026-09-28; dataset `dd38a5ec…`, aux `b6175510…`, calendar
`3185297d…`, config `d120b63f…`):
- `diagnostics.json` `bc651323b5765c3b37715511d4d44a7b80ad8bd1b303d973ec8068b869e94d20`
- `sessions.json` `e8015da40900e5b27fb46d683b4b8db90d21f34c1152c0e9bdc90152b1fc1ee1`

The run reproduces the sweep E0 totals: 132 sessions, 122 trades, stressed $10,424
(H1 $17,031 / H2 −$6,607), delayed $9,947, tie-set $10,982.

Selected cells (stressed; sessions all/H1/H2; per session):

| Cell | Sessions | Stressed | H1 | H2 | /session | Tie $0.10 | Settled | RMS σ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| No scheduled event | 101/50/51 | 10,094 | 13,413 | −3,319 | 100 | 10,104 | 18 | 0.956 |
| Any scheduled event | 31/17/14 | 330 | 3,618 | −3,288 | 11 | 878 | 5 | 1.061 |
| 08:30 release before entry | 17/9/8 | −97 | 1,652 | −1,749 | −6 | 507 | 2 | 1.192 |
| FOMC | 5/3/2 | −961 | −485 | −475 | −192 | −1,003 | 0 | 1.121 |
| CPI | 6/3/3 | −1,594 | −891 | −703 | −266 | −984 | 1 | 0.777 |
| NFP | 4/2/2 | −976 | −515 | −460 | −244 | −967 | 0 | 1.685 |
| PCE | 7/4/3 | 2,472 | 3,058 | −586 | 353 | 2,457 | 1 | 1.136 |
| OPEX | 7/4/3 | −1,549 | −898 | −651 | −221 | −1,649 | 1 | 0.570 |
| VIX1D/VIX prior, low (< 0.693) | 44/20/24 | 6,838 | 6,484 | 354 | 155 | 6,072 | 7 | 1.064 |
| VIX1D/VIX prior, mid | 44/20/24 | 6,948 | 9,605 | −2,657 | 158 | 7,163 | 10 | 0.947 |
| VIX1D/VIX prior, high (≥ 0.828) | 44/27/17 | −3,361 | 942 | −4,303 | −76 | −2,253 | 6 | 0.925 |
| VIX9D/VIX prior, low (< 0.853) | 44/15/29 | −1,940 | −723 | −1,217 | −44 | −1,860 | 4 | 1.140 |
| VIX9D/VIX prior, mid | 44/23/21 | 8,919 | 11,101 | −2,182 | 203 | 8,454 | 11 | 0.855 |
| VIX9D/VIX prior, high (≥ 0.942) | 44/29/15 | 3,446 | 6,654 | −3,208 | 78 | 4,388 | 8 | 0.920 |
| VIX/VIX3M ≥ 1 (backwardation) | 7/7/0 | 1,856 | 1,856 | 0 | 265 | 2,302 | 2 | 0.725 |

- **Thin cells.** Event cells hold 2–7 sessions, so a single cash settlement ($1–4k)
  decides their sign. The sample has no early-close session.
- **Tercile cells hold 44 sessions each** but are confounded with H1/H2 and the VIX level.
- **These are development data** the strategy was built on.

The full tables are in the run's `report.md`.

## Vendor history (ThetaData, subscribed 2026-09-28)

**Status on 2026-09-28: ThetaData Options Value is subscribed ($40/mo)** and
`history.SOURCES` holds `thetadata` (and `recorded`, which resamples our own Helios data onto
the same 1-minute grid for comparisons). Options Value's historical 1-minute quotes reach
2020-01-01. The Indices subscription was not bought.

**The owner's rules** (`vendor-data-quality-plan-2026-09-28.md`, approved 2026-09-28):
- data quality comes first;
- **no derived data**: no SPX from put-call parity, no computed VIX, no filled bars. A
  session without a real SPX level, or without a real VIX print between 09:55 and 10:00 ET,
  is skipped (`no_spx_index`, `no_vix`); an index print older than 120 s is no level.

**Where each input comes from:**
- **Option quotes:** ThetaData, 1-minute (`/option/history/quote`).
- **SPX and VIX intraday, 2022 → 2025-12-09:** the owner's minute files (`data/spx_1min.csv`,
  `data/vix_1min.csv`; gitignored; owner-supplied, added 2026-03-11, original vendor unknown;
  US Central time, bar-end stamped). A day with 30 or more identical consecutive bars is a
  forward-filled fake and is not served. On 2022 → 2025 that is SPX on 7 days and VIX on
  7 days; the list is pinned in the manifest.
- **SPX and VIX intraday after the files end** (the validation window): our recorded Helios
  ticks (`--recorded spx_0dte`), never inside the holdout.
- **Official closes:** Cboe's public `SPX_History.csv` and `VIX_History.csv`. SPX open, high
  and low come from the minute file, then from the recorded `spx_0dte` daily bars.

**Validation.** Run `76abde9f881a` of `validate-vendor` failed steps 1–3; the calibration
and diagnostics that followed are in the plan. Under the approved plan, the data-quality
gates Q1–Q6 (`quality.py`, command `vendor-quality`) replace steps 1–3 as the condition for
earlier pulls. `export-history` refuses any pull before 2026-03-13 until the dataset's
manifest history shows a passing `vendor-quality` run over the whole validation window
(`QualityNotPassedError`).

**Known gap:** 2025-12-10 → 2026-03-12 (about 62 holdout sessions) has no SPX or VIX minute
data, so those sessions are skipped until a real source is found (plan, D3).

**Licence.** ThetaData's individual terms forbid archiving content (§2.1(i)) and require
deleting all copies at termination (§12.2). Whether the local research cache may outlive a
cancelled subscription is still to be confirmed with ThetaData in writing.

**Development-window evaluation (2026-09-29, in-sample).** E0 and the drafted hypotheses
were run on `spx_0dte_thetadata` @ `93bbe58e`, profile `vendor_1m`, 2022-01-03 → 2024-06-28,
halves split at 2023-04-26, with the draft's bootstrap (10-session blocks, 10,000 reps,
seed 1). Results, power and the owner's open decisions are in
`docs/research/registration-decision-2026-09-29.md`.
- **Inputs.** With the owner's approval, `export-vol --cboe` added Cboe's daily VIX-family
  file to the vendor dataset for H-TS1: `aux/vol_index_daily.parquet`, 18,617 rows, sha256
  `7fa50f1c887f0cf305d9d7903a2cacda1883324c1d0acedd4cf0821119d5b21c`, aux_hash
  `eab136c9eb93b0b410217f5c15b0ed62e9e159a377cba8bd9fc77cfa21b19278`. The dataset hash is
  unchanged. Its development-window rows are identical to `spx_0dte`'s copy.
- **Where the evaluations are recorded.** `register` refuses a definition already present in
  the dataset's registry, so development runs are recorded in a separate hash-chained file,
  `reports/research/registry/development/spx_0dte_thetadata.jsonl` (owner-confirmed). The
  registration registry `reports/research/registry/spx_0dte_thetadata.jsonl` does not exist
  yet. The unseal reads only the latter.
- **Runs:** `9eccee6a6aa5` (E0, HLV1, HEV1, HEV2, HTS1; `results.json` `2c042505…`) and
  `da7a9163c0fa` (E0, HLV1, HSN1, HSN1_c148, HSN1_c168, HEV1, HEV2; `results.json`
  `429d0829…`).
- **Early closes.** The replay marks a trade still held when a shortened session's clock
  ends (13:00) as `incomplete_data` (`MIN_END_OF_DAY_DATA_TIME` is 15:00), so the session
  is dropped from every compared arm: 2023-07-03 for E0, and 2022-11-25 for HSN1.

```bash
T="--provider thetadata --spx-minutes ../Butterflyguy/data/spx_1min.csv \
  --vix-minutes ../Butterflyguy/data/vix_1min.csv"
uv run python -m butterfly_guy.research export-history $T --recorded spx_0dte \
  --start 2026-03-13 --end 2026-09-25
uv run python -m butterfly_guy.research vendor-quality --vendor-dataset spx_0dte_thetadata
# Opens only after a passing vendor-quality run on the whole validation window:
uv run python -m butterfly_guy.research export-history $T --start 2022-01-03 --end 2024-06-28
uv run python -m butterfly_guy.research vendor-quality --vendor-dataset spx_0dte_thetadata \
  --start 2022-01-03 --end 2024-06-28
```

### The adapter (`history.py`)

The adapter writes the existing Parquet schema into its own dataset, `spx_0dte_<vendor>`.
It refuses to write into `spx_0dte`, or into any name that does not start with `spx_0dte_`.
The mapping follows the readiness doc's spec:

- **Clock.** A 1-minute grid from 09:31 to 16:00 ET. On the calendar's early closes it
  ends at 13:00 (210 points instead of 390).
- **Quotes.** The vendor's quote state is carried within the session only, with its age
  in the new optional `{C,P}_quote_age_s` columns. Helios chains have no such columns, so
  their bytes and hashes are unchanged.
- **Missing, crossed and zero-bid quotes** stay as the vendor gave them (NaN, crossed or
  zero); nothing is repaired.
- **Mark** is `(bid + ask) / 2`.
- **Strikes** are integers within ±400 of the session's spot range.
- **Spot** is the real SPX index level at each grid point (its last print, at most 120 s
  old). A session without one is skipped; nothing is derived.
- **Official open and close** come from the source's daily bars (ThetaData: Cboe closes).

**Every pull appends a manifest `history` entry** with:
- the source description;
- every vendor call with its parameters;
- the cost estimate;
- the added and skipped sessions;
- `holdout_sessions`, the dataset's count of holdout-dated sessions.

**Cost.** Before any data is requested, `cost_estimate` is checked. A usage-billed pull
estimated above `--max-cost` (none approved means $0) stops with `CostNotApprovedError`.

**Consequence for the validation window.** 2026-03-12 is the last day of the holdout. The
daily-bar lookback for a pull starting 2026-03-13 is therefore clipped at the holdout's
end, and the history entry records that. The vendor replay will have no prior close for
2026-03-13 and will skip that session. The frozen replay skips it anyway (missing
prerequisites).

### The sealed holdout (`holdout.py`)

- **Development:** 2022-01-03 → 2024-06-28.
- **Holdout:** 2024-07-01 → 2026-03-12.

`guard` raises `HoldoutSealedError` for any range touching the holdout. It is applied at
every level:
- every vendor call, cost previews included, through `GuardedSource`, *before* the vendor
  is called;
- every pull (`write_history`);
- every `SessionLoader.dates` and `load`, on any dataset;
- `coverage`.

The only way past it is an `Unseal`, which only `verify_unseal` can build. It checks, for
`--unseal-holdout <seq>`:
- the registry chain is intact;
- record `<seq>` is a `register` event;
- every `register` record up to it has `git_dirty: false`;
- each was made on a dataset hash that the dataset's manifest history shows with
  `holdout_sessions == 0`.

A registration made after holdout data landed can never unseal anything.

**What the guard does not cover.** The Cboe daily VIX-family file in `aux/` (public index
closes, fetched in stage 3) spans 1990 → today, holdout dates included. It is read only
through `features.SessionFeatures`, for a session being replayed, and holdout sessions
cannot be replayed without an unseal. H-TS1's threshold is fitted through a
`WindowedLoader` confined to the development window.

### Fidelity validation (`validate.py`)

This implements steps 1–4 of the readiness doc. The pass criteria are copied verbatim
(`tests/test_research_validate.py` checks that they still match the doc). Where the plan
leaves a detail open, the module fixes it:

- **σ** is 1.25 × the Helios ATM straddle at the snapshot at or before 10:00 ET. The OTM
  region is 1.0–2.5 σ from the Helios spot at each snapshot.
- **A pair agrees** when both sides quote it and both its bid and its ask are within
  $0.05. The 95% is measured at offset 0.
- **The offset scan** runs from −180 to +180 s in 15 s steps.
- **Step 2** uses a derived dataset: vendor quotes at the Helios timestamps, with the Helios
  clock, spot, VIX and bars. A disagreement is *explained* by the first quote difference at
  a decision snapshot on or before it.
- **Step 3** must pass against both Helios profiles.
- **Step 4** requires every vendor close on a compared session to equal the Helios
  `daily_bars` close and Cboe's published SPX close, to the cent.

The output goes to `reports/research/<vendor>/validation/<run id>/`: `validation.json`,
`report.md` (one PASS/FAIL row per criterion, then the details) and `provenance.json`.

**Harness self-check** on 2026-09-28, with the Helios export `b76dc6c9…` as both sides and
all 133 sessions:
- Step 1 passed: share 1.0 over 1,166,201 region pairs, best offset 0 s.
- Step 2 passed with no disagreements: frozen $10,319.20 and sweep $10,259.20 stressed on
  both sides.
- Step 4 passed: all 133 official closes equal Cboe's, and the spot difference is 0.
- The three steps took 38 s.
- Eight sessions have no ATM straddle at the 10:00 snapshot, so they add nothing to step
  1's region: 2026-03-13, 03-18, 04-27, 05-04, 05-18, 06-02, 08-25 and 09-08.

This proves the harness runs at scale, not that any vendor is good.

**Coverage baseline** for comparing a vendor later (`coverage` on `spx_0dte`):
- 133 sessions with a median of 154 strikes and 375 timestamps.
- Median missing and crossed rates within ±200 of spot: 0 and 0.
- Median zero-bid share: 0.18 for calls, 0.06 for puts.
- Official open and close on all 133 sessions.
- A VIX tick between 09:55 and 10:00 on 126 sessions.

### Hypothesis rules (implemented, not registered)

These are new classes in `hypotheses.py`. No existing rule class was edited. The catalog
entries use the runtime trailer, as E0 does. Definition hashes on 2026-09-28:

| Variant | Rule | Definition hash |
|---|---|---|
| `HSN1` | `SigmaPlacedEntry()` | `4589760a17440ebc01b86451b52f2dae18905eebb13270497476a468c2988147` |
| `HEV1` | `ReleaseSkipEntry(E0)` | `9180c56d9a7deb480778906bd3c199b164150e8389e6e089bdb1eb9ba23d660f` |
| `HTS1` | `PriorRatioFilter(E0, "vix1d_vix", 2022-01-03, 2024-06-28)` | `fab8bf3e0ab10805d8b6d8ee19617df7013c0fa776ed6fbf86314c6238ff69c6` |
| `HLV1` (existing) | `FilteredEntry(E0, skip_low_vix_calls, 17.0)` | `6ed12752c07aeda2b857e3c7a04129f85e02bbdf5be40b2ab46e4feade2ed6d6` |

*(Corrected in stage 6, marked: this table gave HTS1 as `2ec8c008…`, which was never the
hash of committed code. `tests/test_research_hypotheses.py` now pins all four.)*

Added on 2026-09-29 for the development-window runs (not registered; the four hashes above
did not move):

| Variant | Rule | Definition hash |
|---|---|---|
| `HEV2` | `EventDaySkipEntry(E0, ("FOMC",))`: skip a session with a visible FOMC statement, at any time | `b0c670c064c05f2a155d079b9e2a2475196ac60e9a8a9f818889e78e5274b477` |
| `HSN1_c148` | `SigmaPlacedEntry(center_sigma=1.48)`: H-SN1's noise secondary | `844e32da34d7571893500c943f451dd4203a8f90c62d582afb1d8ba65e195ecf` |
| `HSN1_c168` | `SigmaPlacedEntry(center_sigma=1.68)`: H-SN1's noise secondary | `f0967c75c1a6ef506f68d13a1511477db3f0d50035ceb8cc848b4e76acdd87ad` |

The hash covers the top-level rule class's source and its parameters. Nested code (E0's
`BaselineEntry`, HLV1's predicate), `features.py`, the calendar and `configs/config.yaml` are
frozen only by the register record's `git_sha`. The registration decision package,
`docs/research/registration-decision-2026-09.md`, collects each hypothesis's frozen
choices, alternatives and development evidence for the owner.

The draft leaves some details open. **The owner should review these choices before
registering**, because the hash freezes them:

- **H-SN1**
  - σ is fixed from the 10:00 straddle for the whole session. If no fly qualifies at
    10:00, later window times reuse that σ with the current spot.
  - The center is the nearest listed strike, the lower one on an exact tie. It must be
    out of the money.
  - The fly must be executable at the snapshot.
  - The debit must be at least `min_debit` ($0.05) and at most the configured cap for its
    width. For a width the config has no cap for (5, 15, 35, 60 …), the cap is the single
    $0.10-per-point rate all configured caps share.
  - Like E0, it requires a fresh VIX at the decision.
  - There is no tie-set, because the live selector does not choose the fly.
- **H-EV1**
  - It counts CPI, NFP or PCE events visible under the calendar's leakage rule with a
    release strictly before 10:00 ET.
  - An event withdrawn *on* the session is still expected, as the calendar's rule says.
- **H-TS1**
  - The threshold is `numpy.quantile(…, 2/3)` (linear interpolation) of the prior-session
    VIX1D/VIX over the development sessions the profile qualifies.
  - It skips at or above that value. A session with no prior VIX1D close is never skipped.
  - It needs the Cboe daily aux file on the vendor dataset
    (`export-vol --cboe --dataset spx_0dte_<vendor>`).

**Leakage guards.**
- Rules that read features take them from `RunContext.features`, and a run then records
  the calendar and aux hashes in its meta. Runs without such rules are unchanged, so
  every published hash above still holds.
- H-TS1 fits only through `WindowedLoader` and raises `LeakageError` on any date outside
  its window.
- The unit tests cover calendar visibility, prior-session-only term structure (including
  a Cboe print on an exchange holiday), fit-window confinement and the placement
  mechanics.

## Mechanism check for H-TS1 (descriptive only)

`mechanism` asks whether SPX moves less than VIX1D implied on sessions whose prior-close
VIX1D/VIX is high. It uses only Cboe's public daily files, on the development window, and
**informs whether H-TS1 is registered; it evaluates no rule, writes no registry record and
changes nothing in the pre-registration draft.** Every artifact is headed "DESCRIPTIVE —
development window — not a rule evaluation".

- **Inputs.** Cboe's `SPX_History.csv` (`DATE,SPX`, closes only; fetched, or `--spx-csv`)
  and the dataset's `aux/vol_index_daily.parquet` (VIX1D and VIX).
- **Window.** Scored sessions 2022-05-16 → 2024-06-28. Both inputs are cut to the SPX
  session before 2022-05-16 through 2024-06-28 before anything is computed; `holdout.guard`
  is called on the range, and a range outside the development period raises.
- **Statistic.** `r_t = |ln(SPX_close_t / SPX_close_{t-1})| / (VIX1D_close_{t-1} / 100 /
  sqrt(252))`, priors on the previous SPX session through `features.DailyVol`.
- **Decision rule (fixed before running).** Split at `numpy.quantile(prior VIX1D/VIX, 2/3)`
  over the same sessions (top: ≥, as in `HTS1`). Statistic: mean r in the top tercile minus
  mean r in the rest. Moving-block bootstrap, 10-session blocks, 10,000 reps, seed 1,
  membership fixed per session. "Supported" only if the 90% interval lies entirely below
  zero. Halves split at 2023-06-01 are reported, not tested.
- **Limits.** Close-to-close includes the overnight move and the morning before entry, so
  it is a proxy for the 10:00 → close exposure, not a test of H-TS1. H-EV1, H-SN1 and H-LV1
  cannot be checked with close-only index data.
- **Output.** `reports/research/mechanism/<run id>/`: `mechanism.json`, `sessions.csv`,
  `report.md`, `provenance.json`. The run id hashes the in-window inputs and the rule, not
  the raw Cboe file, which grows daily.

```bash
uv run python -m butterfly_guy.research mechanism
```

Run `a2b54db81c49` (2026-09-28 21:20 UTC; git `82aed43` plus the uncommitted stage-5 code):
- `SPX_History.csv` from `cdn.cboe.com`, sha256
  `cfab26ca71a640bc3f31210015684de3a800bb386dc4b16523ef91844c5670b5` (292,895 bytes);
  in-window rows 534, sha256 `3127b07dc6c8771e9c44e570b902361c95fc762c0c55ba95e00773e316c8bd25`.
- `aux/vol_index_daily.parquet` sha256 `048eb3de…` (aux_hash `cb12502b…`); in-window rows
  2,152, sha256 `f2634e48f041288d5e1612df14ab8772dfc34d58a8dd567bb99a4f291aa556da`. Latest
  input date 2024-06-28.
- `mechanism.json` `210c585b6222eccd4fef6db7d3e90d5ee85674faf7d32b51e9e5f7cde7c17b5b`,
  `sessions.csv` `242d88b6db95e92017e55fddeb9d432469f2a2b1d2f552c89013352c8d33f516`.

**Result: not supported.** 533 sessions scored, none excluded. Tercile bounds of the prior
VIX1D/VIX: 0.801 and 0.918.

| Part | Sessions | Top n | Top mean r | Rest n | Rest mean r | Top − rest | 90% interval |
|---|---:|---:|---:|---:|---:|---:|---|
| All | 533 | 178 | 0.741 | 355 | 0.715 | +0.026 | [−0.058, +0.101] |
| H1 (< 2023-06-01) | 262 | 107 | 0.762 | 155 | 0.737 | +0.025 | [−0.070, +0.132] |
| H2 (≥ 2023-06-01) | 271 | 71 | 0.711 | 200 | 0.698 | +0.013 | [−0.108, +0.142] |

- High-ratio sessions moved slightly *more* relative to VIX1D, not less, in both halves.
- Over all sessions, mean r is 0.724, below the ≈0.80 of a normal move priced exactly by
  VIX1D: one-day implied was rich on average, but not more so when VIX1D/VIX was high.
- The development-window 2/3 bound (0.918) is well above the 2026 sample's (0.828), so a
  threshold fitted on 2022–2024 would flag fewer 2026 sessions.

## Known differences

- **Float ties with the numpy harness.** `sim.py` stores prices as float32; this core
  works in float64.
  - **D2 (gap fade), and D3's put leg, 2026-07-09: +$25 stressed.** That session's
    drawdown is exactly the 60% threshold (5.55 → 2.22). The trailer fires in float64,
    which is what the reference engine and this core use. In float32 it narrowly does
    not.
  - **G2, 2026-09-23: +$15 midpoint, stressed identical.** The 7630/7680/7730 call and
    put flies both cost exactly $22.55 in stressed debit and have the same settlement
    payoff, so their expected-value scores tie. Float64 rounding picks the call and
    float32 the put.

  Every other variant matches `sim.py` exactly. The comparison was made against the
  original 2026-09-25 export as well as the new cache.
- **The frozen profile uses today's selector.** On `main`, the selector also rejects
  crossed leg quotes (#27). No selection on this sample depends on that.
- **R2 on an undefined feature.** `sim.py` would fail on an entry without an ATM
  straddle; `FittedFilter` skips it (`if_undefined="skip"`). No E0 entry on this sample
  lacks one. K1 keeps an entry whose market is not executable, as `sim.py` did.
