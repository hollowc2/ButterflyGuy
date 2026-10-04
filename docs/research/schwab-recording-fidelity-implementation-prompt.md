# Implementation prompt: SPX Schwab recording fidelity (timing, cadence, ThetaData check)

Written 2026-10-04. Paste everything below the line into a fresh Claude Code session at the
repository root.

---

## Goal

Make the SPX recordings the live bot writes to `option_chain_snapshots` and `spot_prices`
good enough to compare with ThetaData minute by minute, and measure how close they get.
Three parts, delivered as **three separate PRs in this order**:

- **C: Daily fidelity check** against ThetaData. Offline, read-only, no live risk. It goes
  first so it can measure the current recordings before anything changes.
- **A: Timing metadata.** Record when each quote was actually made, not just when the
  collector started its loop.
- **B: Fixed cadence.** Collect on a fixed wall-clock minute grid instead of sleeping 60 s
  after each pass.

SPX only. Keep the code generic where it already is (the collector reads
`config.strategy.underlying`), but enable and verify only for `configs/config.yaml`. NDX and
XSP configs must behave exactly as today.

Read `AGENTS.md` first and follow it. This code feeds a running PAPER trading bot on Helios;
treat collector, provider and schema changes as high-impact.

## What is wrong today (verified 2026-10-04 by reading the code)

1. **The snapshot stamp comes before the data.** `OptionChainCollector.collect_snapshot`
   (`src/butterfly_guy/data/collector.py`) sets `snapshot_time = now_eastern()`. It then
   fetches SPX spot, then VIX, then the chain, one after another. Chain fetches have measured
   4.2–5.5 s (2026-09-04 gateway soak), so every chain row is stamped several seconds before
   its quotes were received. Spot and chain come from different moments, but both carry the
   same stamp.
2. **The gateway's timing metadata is thrown away.** `schwab_gateway_sdk` models carry
   `event_timestamp`, `gateway_received_at`, `age_seconds`, `stale`, `source` and
   `data_quality_flags`. They exist on the chain (`OptionChainV1`), each contract
   (`OptionContractV1`) and spot (`SpotV1`). `GatewayAuthoritativeMarketDataProvider._get_option_chain`
   (`src/butterfly_guy/data/providers.py`) converts the chain into a Schwab-shaped dict and
   keeps none of them. It also **silently drops** stale contracts and contracts with no event
   timestamp (`usable_contract`), so the DB never shows they were missing.
3. **Cadence drifts.** `run_loop` does `await asyncio.sleep(interval)` *after* the work, so
   the real period is 60 s plus fetch time (about 65–70 s). Snapshots drift through the
   minute instead of landing at a fixed second, which is why `research/quality.py`
   `matched_instants` (Helios snapshot 0–`MATCH_S`=5 s after a minute mark) matches only a
   small share of snapshots.
4. **The gateway option-chain cache TTL (4 s) is shorter than the fetch latency.** Tuning it
   is **owned by the SchwabGateway repo** (see
   `docs/architecture/schwab-gateway-current-status.md`; the TTL tool was removed from this
   repo in `2bc7739`). It is **out of scope here**. Part A's recorded ages give the evidence
   to size it; say so in the PR, don't change gateway config.

Who reads the stored snapshots, so the blast radius is known:
- `services/trade_service.py` (~line 968): entry-selection parity uses
  `ChainQueries.get_nearest_snapshot_chain(..., max_lag_seconds=60)`, `snapshot_time <= at`.
- `services/position_service.py` (~line 1114): exit-mark parity, same query, 60 s.
- `backtest/` DB loaders (`run_backtest_db.py`) and `research/export.py`
  (`clock_sql`, `chain_sql`) read `snapshot_time`, `spot_price`, bid/ask.
- `backtest/chain_cache.save_snapshot` writes the JSON chain cache on Helios.

Re-verify these with grep before changing anything; don't trust this list blindly.

## Hard constraints

- **Do not change what `snapshot_time` means, or what rows the strategy reads.** Add new
  columns and tables instead. The parity checks, the DB backtest and the frozen research
  datasets all depend on it. If you conclude a semantic change is necessary, stop and ask
  the owner with evidence.
- **Do not change what the strategy sees.** Stale contracts must still be excluded from the
  chain the trading code uses. Record their *count* and identity in metadata; don't add
  them to `option_chain_snapshots`.
- No deploys, container restarts, Helios writes, cron installs, or Schwab write API calls.
  Hand the owner paste-ready deploy steps in the PR description. Migrations run at app
  startup (`run_live.py` → `run_migrations`), so a merged migration takes effect on the
  next restart. Say that explicitly in the PR.
- No changes to trading limits, paper/live mode, order routing, token handling, entry/exit
  rules, or NDX/XSP behavior.
- `option_chain_snapshots` is a TimescaleDB hypertable. Before writing the migration, check
  whether compression is enabled. Use
  `SELECT * FROM timescaledb_information.compression_settings WHERE hypertable_name='option_chain_snapshots'`,
  through a read-only path the owner approves, or state that it couldn't be checked.
  Keep new columns nullable with no default so the `ALTER` is metadata-only.
- Never commit ThetaData data or derived quote traces (personal licence). Outputs go under
  the gitignored `reports/`.
- The 2024-07-01 → 2026-03-12 window is spent holdout data. Part C doesn't need it; don't
  read it.

---

## Part C: daily Schwab-vs-ThetaData fidelity check (PR 1)

### Build on what exists

- `research/quality.py`: `matched_instants`, `_bad_cells`, Q1–Q4 cell rules, `BAND`, `TOL`.
- `research/export.py`: exports Helios DB sessions into the `spx_0dte` dataset
  (`--source tunnel|docker`).
- `research/local.py` / `thetadata.py`: `import-local` of `data/thetadata/spxw_0dte/quote_1m`
  into a normalized dataset.
- `tools/thetadata_download.py`: resumable download of a date range (terminal at
  `127.0.0.1:25503`, never `localhost`).
- The validation dataset `spx_0dte_local_durable_validation_20261001`
  (2026-03-13 → 2026-09-25, under `data/research_cache/`) already has ThetaData sessions
  overlapping the recorded Helios `spx_0dte` dataset. Use it for the baseline.

### Deliver

A research CLI subcommand `schwab-fidelity` in `research/cli.py`, with logic in a new
`research/fidelity.py`. It reads a recorded Helios dataset and a ThetaData dataset for one
date or a range, and writes one content-addressed artifact per run under
`reports/data_management/schwab_fidelity/<run date>/<dataset>/<hash>/` containing
`summary.json`, `sessions.jsonl`, `provenance.json` and `report.md`. Follow
`research/session_ledger.py`: deterministic output, hashes, and byte-identical reruns on
unchanged inputs.

Per session, report:

1. **Matching.** Pair each Schwab snapshot with ThetaData's row for the minute that
   contains its quote time. Use the recorded quote event time when Part A's columns exist;
   otherwise use `snapshot_time` and label the result `timing_basis: snapshot_time`. Report
   pair counts, and the share of snapshots that matched a minute by lateness bucket (0–5,
   5–15, 15–30, 30–60 s).
2. **Price agreement** on integer strikes within ±`BAND` of spot, split by moneyness bucket
   (|K−S| ≤ 25, 25–50, 50–100, 100–200) and by time of day (open, midday, last hour):
   - median and p95 of |Δmid|, and of signed Δmid (Schwab − ThetaData);
   - median and p95 of Δspread;
   - share agreeing within `TOL` on both bid and ask.
3. **Coverage.** Strikes present in ThetaData but missing or unquoted in Schwab within ±100
   of spot (`strategy.spot_range`) for each matched minute, plus scheduled minutes with no
   Schwab snapshot at all.
4. **Quality.** Q2/Q3 violation counts on each side for matched rows, reusing `_bad_cells`.
5. **Spot.** Recorded SPX spot against SPX implied by put–call parity from ThetaData mids at
   the strike where |C−P| is smallest (`K + C − P`), at matched minutes. Report median and
   p95 |Δ|. Also report VIX observations per session and the largest gap between them.
6. **Strategy-relevant summary.** For every butterfly the live config could select (both
   directions, every width in `strategy` config, centers within `spot_range`) at matched
   minutes, report the fly mid difference: median, p95, and share with |Δ| > $0.05 and
   > $0.10. This is the number that drove the $8k Schwab-vs-ThetaData gap. Optionally
   report whether entry selection (`research/entry.py` or the existing selection code)
   picks the same fly on both sources at the configured entry times. Include it only if it
   reuses existing selection code without new strategy logic.

All of it is report-only. **No pass/fail thresholds.** Thresholds need a written plan the
owner approves before metrics are computed, like `vendor-data-quality-plan-2026-09-28.md`.
Leave a `thresholds: null` field and a TODO naming that plan.

Also add `tools/run_schwab_fidelity_daily.sh`, a wrapper for one date (default: the
previous trading session, from the exchange calendar, not `time_utils.is_trading_day`,
which has known holiday bugs). It:
1. downloads that day's `spxw_0dte quote_1m` with `tools/thetadata_download.py`;
2. imports it into a dated local vendor dataset;
3. exports the Helios session (`research export --source tunnel`);
4. runs `schwab-fidelity`;
5. sends a one-line Telegram summary through the existing notifier only if a flag is
   passed.

Don't install it in cron. Put the suggested crontab line in the PR description.

### Baseline (required in PR 1)

Run `schwab-fidelity` over the whole validation window (2026-03-13 → 2026-09-25) and put the
headline numbers in `docs/research/schwab-fidelity-baseline-<date>.md`. These are the
"before" numbers for Parts A and B. Keep the expectation honest: with
`timing_basis: snapshot_time` the matching is approximate, and the doc must say so.

### Tests

Synthetic sessions in `tests/test_research_fidelity.py`, in the style of
`tests/test_research_quality.py`: exact-match agreement, a one-minute timestamp shift being
detected, missing strikes, and determinism (rerun gives identical hashes).

---

## Part A: timing metadata (PR 2)

### Provider

Add a collector-only method to `GatewayAuthoritativeMarketDataProvider`, e.g.
`get_option_chain_observed(symbol, expiration) -> (chain_dict, ChainObservation)`. Make
`get_option_chain` call it and return only the dict, so every existing consumer gets a
byte-identical result. `ChainObservation` (a frozen dataclass) holds:
- chain: `event_timestamp`, `gateway_received_at`, `age_seconds`, `source`, `stale`,
  `data_quality_flags`;
- per kept contract, keyed by symbol: `event_timestamp`, `age_seconds`;
- contracts delivered, contracts kept, and the symbols and flags of omitted contracts.

Do the same for spot (`get_spot_observed`). Keep the existing validation and fail-closed
behavior exactly as is. Check the `CollectorMarketDataProvider` protocol and the direct
(non-gateway) provider: the direct path has no gateway metadata, so it returns
`None`/empty observations and records `source='schwab_direct'`.

### Schema (migration `011_snapshot_timing.sql`, idempotent like 004)

- `option_chain_snapshots`: add nullable `quote_event_ts TIMESTAMPTZ` and
  `quote_age_s REAL`.
- New table `chain_snapshot_meta`, one row per snapshot:
  - `snapshot_time` (PK together with `underlying` and `expiration`), `underlying`,
    `expiration`;
  - `scheduled_at`, filled by Part B and NULL until then;
  - `fetch_started_at` and `fetch_completed_at` for spot, VIX and chain;
  - `chain_gateway_received_at`, `chain_event_ts`, `chain_age_s`, `chain_source`,
    `chain_flags TEXT[]`;
  - `spot_event_ts`, `spot_age_s`, `vix_event_ts`, `vix_age_s`;
  - `contracts_delivered`, `contracts_stored`, `contracts_omitted`, `omitted JSONB`;
  - `strikes_within_spot_range`.
- `spot_prices`: add nullable `event_ts TIMESTAMPTZ` and `age_s REAL`.

### Collector

Fill the new fields in `collect_snapshot`. Measure `fetch_*` timestamps with a wall clock
read immediately around each await. Write the meta row in the same flow as the chain
insert; a meta-write failure must log and alert, but must never block the chain insert or
trading. Extend `ChainQueries.bulk_insert_snapshot` to carry the two new columns; check
every caller.

### Research export

When the new columns exist, make `research/export.py` `chain_sql` also select
`quote_age_s` and write it as the dataset's optional `AGE_FIELD`. `dataset.py` already
supports it, and Q1 then applies `FRESH_S`. Gate this on column presence, and make sure
re-exporting old sessions produces the same files (no age column, so the hash is
unchanged). Update `schwab-fidelity` to use `quote_event_ts` as its timing basis when
present.

### Tests

Extend `tests/test_market_data_providers.py`: the observed method returns metadata, and
`get_option_chain`'s dict is unchanged, including that omitted contracts stay omitted. Add
collector tests: meta row contents, and a meta failure that doesn't block the chain insert.
Add a migration idempotency test if the suite already has a pattern for it.

---

## Part B: fixed minute cadence (PR 3)

### Behavior

- New config keys under `collector`: `align_to_minute: bool` and `align_offset_seconds:
  float`. Defaults (`false`, 0) keep today's behavior for anything that doesn't set them.
  Set `align_to_minute: true` in `configs/config.yaml` (SPX) only.
- The aligned loop schedules ticks at `HH:MM:00 + offset` ET and computes each sleep from an
  absolute deadline using wall clock plus monotonic time. It never sleeps a fixed interval
  after the work. If a pass overruns its slot, **skip** the missed tick (no burst catch-up),
  count it, and record it. First and last ticks follow `is_market_open()` and early closes.
- Record `scheduled_at` in `chain_snapshot_meta`. Add Prometheus metrics for tick lateness
  (`fetch_started_at − scheduled_at`) and missed ticks. Alert through the existing notifier
  when ticks are missed N times in a row; reuse the `consecutive_failures` pattern.
- **Fetch order.** Default to the chain first, then spot and VIX, so the chain's quote time
  is closest to the minute mark that ThetaData's row represents. Record spot and VIX times
  so any skew can be measured. Whether to fetch concurrently (`asyncio.gather`) is a
  decision to make **with evidence**. The gateway has a bounded protected/background queue,
  and one collector pass shouldn't consume three slots at once without checking. Leave it
  sequential unless the Part C numbers show spot/chain skew matters, and say so in the PR.
- Choosing `align_offset_seconds`: from Part A data, if available, pick the offset that
  puts the median `quote_event_ts` closest to the minute mark. Otherwise default to 0 and
  document how to tune it.

### Check the impact on live reads

Entry and exit parity look for a snapshot within 60 s at or before their own fetch time.
With a fixed grid there is always one at most ~60 s + fetch latency old. Verify that this
doesn't push parity into `no_db_snapshot_within_60s` more often than today. If it might,
report it; don't widen the window without owner approval. Confirm the collector's timing
doesn't change entry timing: entry runs on its own schedule in `run_live.py`.

### Tests

Deterministic scheduler tests with a fake clock: alignment, overrun → skip, no burst after
a stall, early-close stop, and default config keeping the old loop.

---

## Verification for every PR

- `uv run pytest` for the touched areas, then the full `uv run pytest`; `uv run ruff check .`.
- `graphify update .` after code changes (AST-only).
- Part C: baseline run over the validation window, with the artifact paths in the PR.
- Parts A and B: there is no live verification in this session. Write a post-deploy check
  the owner runs after one session: a read-only SQL query for `chain_snapshot_meta`
  lateness and age percentiles, plus `schwab-fidelity` on that day compared with the
  baseline doc. **The success measure is that Part C's numbers improve on a real session**,
  in particular match share, fly-mid |Δ| p95, and the age distribution.
- Each PR description ends with what was not verified and why, the deploy steps for the
  owner, and the rollback (config flag off for B; A's columns are nullable and unused by
  trading).

## Out of scope

Gateway TTL and fetch latency (SchwabGateway repo), SPX/VIX index gap filling and the
minute-backfill job, NDX/XSP, order-fill calibration, threshold gates for `schwab-fidelity`,
and any strategy change.
