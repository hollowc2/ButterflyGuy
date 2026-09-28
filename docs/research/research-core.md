# Research core

`src/butterfly_guy/research/` is the one simulator for SPX 0-DTE butterfly rule
research. It makes paired, stressed, noise-aware comparison the default. The design
rationale is in `docs/reviews/2026-09-27-research-pipeline-review.md` (§2, §3 and §5).
`run_backtest_db.py` and `SimulationEngine` stay the live-parity reference, and nothing
here changes live-trading code.

## Modules

| Module | Responsibility |
|---|---|
| `dataset.py` | Parquet schema, manifest with per-file SHA-256 and row counts, hash-checked loading |
| `export.py` | Read-only export (`DataSource`: SSH tunnel via asyncpg, or `docker exec psql`) |
| `market.py` | Snapshot at or before a time, fly mark and executable-side paths, missing and crossed masks |
| `accounting.py` | Midpoint, marketable and stressed fills; imports `execution_accounting` constants |
| `entry.py` | Decision profiles, session loading, entry rules through the live `select_entry_candidate` |
| `exits.py` | Exit rules and the monitoring loop; the peak trailer uses the shared `profit_policy` functions |
| `simulate.py` | Variants over sessions (the session is the outer loop, so each is loaded once) |
| `evaluate.py` | Session vectors, paired moving-block bootstrap, H1/H2, rolling blocks, top-3-removed P&L |
| `tieset.py` | Near-tied fly scoring at $0.10 / $0.25 with paired draws |
| `registry.py` | Append-only, hash-chained variant registry |
| `variants.py` | Named variant catalog (E0, X1–X5, D1, D2, R1, R5, HLV1) |
| `report.py`, `cli.py` | Artifacts and the `python -m butterfly_guy.research` CLI |

## Data

The cache lives outside Git at `$BUTTERFLY_RESEARCH_CACHE`, defaulting to
`~/.cache/butterfly_guy/research/<dataset>/`. The layout is documented in `dataset.py`:

- per session, `chain.parquet` (a dense ts × strike grid for calls and puts, never
  imputed) and `clock.parquet` (the replay's bar clock);
- `sessions.parquet`, `daily_bars.parquet` and `spot_ticks.parquet`;
- `manifest.json`, holding the SHA-256 and row count of every file and a `dataset_hash`
  over them.

Every file is hash-checked the first time it is read.

```bash
# Through the SSH tunnel (localhost:15432, DSN from .env)
uv run python -m butterfly_guy.research export --start 2026-03-13 --end 2026-09-25
# Or through docker exec on Helios
uv run python -m butterfly_guy.research export --start 2026-03-13 --end 2026-09-25 --source docker
uv run python -m butterfly_guy.research verify
```

**Read-only export.** Every session runs with `default_transaction_read_only = on` and
a statement timeout. Queries are bounded to one UTC day of `snapshot_time` (or one
week of `spot_prices`), and there is no full-table scan.

**What is kept.** Only sessions with at least 50 0-DTE snapshots are exported. Strikes
are kept within ±400 of the day's spot range, a band wide enough for any strike the
selector or a held position can use. Re-running `export` adds new sessions. A session
whose official close had not yet landed is still exported; its settlement is picked up
from `daily_bars` on the next export.

**Adding another data source.** Implement `DataSource.copy_csv`, or write the same
Parquet schema directly. The simulator never touches the database.

**The 2026-09-27 export** covers 133 sessions from 2026-03-13 to 2026-09-25, is
128 MB, and has dataset hash `dd38a5ecb2cfb08df6e057167c9da06041569da20aab9c30d3bf333e348bc523`.

## Decision profiles

A profile fixes what a replay could see and when.

| Profile | Clock and spot | Open | Prior close | Other |
|---|---|---|---|---|
| `live` (default) | Replay bars (every SPX snapshot that day) | `daily_bars.open` | `daily_bars` close | ≥ 50 snapshots; VIX and prior VIX close required |
| `frozen_20260921` | Replay bars | First bar at or after 09:30 | Last SPX tick ≤ 16:00 on an earlier day | as `live`; this is `run_backtest_db.py` at `b83c2a18` (the frozen replay and the open cohort) |
| `sweep_20260925` | 0-DTE chain snapshots, 09:30–16:00 | First SPX tick at or after 09:30 | `daily_bars` close | Integer strikes within ±200 of spot; timestamps rounded to whole seconds, as that export's `::bigint` cast did |

Selection always goes through the live `select_entry_candidate`. The trailer is
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

**Evaluation.** Every arm is scored on the same sessions, with zeros on no-trade days.
The difference from the baseline is bootstrapped with one draw of 5-session blocks
applied to both arms (5,000 reps, seed 1, the idea sweep's algorithm). Each run also
reports:

- H1/H2 (split 2026-06-18);
- 20-session rolling blocks;
- net P&L with the top three trades removed;
- return on stressed debit.

`--tieset` adds fly-choice robustness at $0.10 and $0.25.

## Registry

`reports/research/registry/spx_0dte.jsonl` is append-only and hash-chained; `verify`
checks the chain.

- **Stage of an evaluation.** An `evaluate` record is `pre` only when the variant was
  registered beforehand, either with `register` or in a `pre` backfill. Anything else is
  `post`.
- **Backfill.** The file was seeded with the 49 variants tried on this data before it
  existed:
  - the 26 in the idea sweep's `REGISTRY.md` (21 pre, 5 post);
  - the 5 MA direction rules;
  - the 18 call-only filters from the 2026-09-25 journal entry. Four of these are
    placeholders, because the journal says eighteen but lists fourteen.
- **Variant counts.** Reports show how many distinct definitions have been tried on the
  dataset name.

```bash
uv run python -m butterfly_guy.research register --variants HLV1 --note "before the H-LV1 test"
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

- 118 trades: 22 cash-settled and 96 intraday (47 / 15 / 34 by regime).
- 2026-03-13 and 2026-03-16 are skipped for missing prerequisites.
- Expectancy, profit factor, win rate, median, maximum drawdown and top-3 share all
  match the journal.

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

The idea sweep's E0 and X1 (round 1) and R1 (round 2) reproduce from the CLI to the
dime: net, H1/H2, midpoint net and the paired 90% CI all match `results.json` and
`results_round2.json`.

```bash
uv run python -m butterfly_guy.research run --variants E0,X1,R1 --baseline E0 \
  --profile sweep_20260925 --start 2026-03-13 --end 2026-09-24
```

| Variant | Trades | Stressed net | H1 | H2 | Midpoint net | 90% CI vs E0 | P(better) |
|---|---:|---:|---:|---:|---:|---|---:|
| E0 | 122 | $10,424.4 | $17,031.2 | −$6,606.8 | $18,504.4 | — | — |
| X1 | 122 | $5,050.8 | $14,343.6 | −$9,292.8 | $9,617.8 | −9,468 / −5,727 / −660 | 0.032 |
| R1 | 67 | $12,721.8 | $17,086.0 | −$4,364.2 | $17,123.8 | −3,737 / 3,014 / 8,670 | 0.777 |

**Output** (run `1a2bcc31999d`, dataset `dd38a5ec…`, config `d120b63f…`; the files
are byte-identical on repeat runs):

- `results.json`: `d3d66586cdb89670d13d12dc636165005a3f0bc9e7d6ca78af4d4be95a2a3a41`
- `trades.jsonl`: `28d6fc7b1ccecf6452999bd92a321521ecd7c62db7f0a57c249f4e3db86ecad7`

The artifacts are in `reports/research/spx_0dte/1a2bcc31999d/`. Like other research
output, run artifacts are not versioned; the command and hashes above reproduce them.
The registry under `reports/research/registry/` is versioned.

**Why the hashes are stable.** Only data-determined content goes into `results.json`
and `trades.jsonl`: the dataset hash, profile, config hash, variant definitions and
parameters. Git SHA and run time go to `provenance.json` and the registry, so the
hashes stay the same across commits unless behavior changes.

**Other variants.** X2–X5, D1 and R5 also match exactly with `--variants
E0,X1,X2,X3,X4,X5,D1,D2,R1,R5`; D2 is covered under Known differences below. `sim.py`
itself, fed the new cache (timestamps rounded to seconds, ±200 band), reproduces its
published figures exactly. That confirms the export holds the same data the sweep used.

## Known differences

- **D2 (gap fade) is $25 off `sim.py` on 2026-07-09.** That session's drawdown is
  exactly the 60% threshold (5.55 → 2.22). The trailer fires in float64, which is what
  the reference engine and this core use. `sim.py` stores prices as float32, where it
  narrowly does not. Every other variant matches `sim.py` exactly.
- **The frozen profile uses today's selector.** On `main`, the selector also rejects
  crossed leg quotes (#27). No selection on this sample depends on that.
- **Idea-sweep variants not yet ported:** C1/C2, D3, D4, T1–T6, K1, G1/G2 and R2–R4.
  Their results remain in that folder.
