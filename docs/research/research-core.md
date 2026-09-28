# Research core

`src/butterfly_guy/research/` is the one simulator for SPX 0-DTE butterfly rule
research. It makes paired, stressed, noise-aware comparison the default. The design
rationale is in `docs/reviews/2026-09-27-research-pipeline-review.md` (§2, §3 and §5).
`run_backtest_db.py` and `SimulationEngine` stay the live-parity reference, and nothing
here changes live-trading code.

## Modules

| Module | Responsibility |
|---|---|
| `dataset.py` | Parquet schema, manifest with per-file SHA-256, row counts and export history, hash-checked loading |
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
128 MB, and has dataset hash `dd38a5ecb2cfb08df6e057167c9da06041569da20aab9c30d3bf333e348bc523`.
A `--bars-only` refresh on 2026-09-27 found no change. 2026-09-25's official close is
still missing from `daily_bars` (the history entry lists it under
`pending_settlements`), so the hash is unchanged. The cohort's recorded sessions
(2026-09-22 → 2026-09-24) are all in this export.

**Adding another data source.** Implement `DataSource.copy_csv`, or write the same
Parquet schema directly. The simulator never touches the database.

## Decision profiles

A profile fixes what a replay could see and when.

| Profile | Clock and spot | Open | Prior close | Other |
|---|---|---|---|---|
| `live` (default) | Replay bars (every SPX snapshot that day) | `daily_bars.open` | `daily_bars` close | ≥ 50 snapshots; VIX and prior VIX close required |
| `frozen_20260921` | Replay bars | First bar at or after 09:30 | Last SPX tick ≤ 16:00 on an earlier day | as `live`; this is `run_backtest_db.py` at `b83c2a18` (the frozen replay and the open cohort) |
| `sweep_20260925` | 0-DTE chain snapshots, 09:30–16:00 | First SPX tick at or after 09:30 | `daily_bars` close | Integer strikes within ±200 of spot; timestamps rounded to whole seconds, as that export's `::bigint` cast did |

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
