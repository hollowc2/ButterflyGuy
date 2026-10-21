# Snapshot-neighbor tie sets (2026-10-18)

Status: **implemented** in `research/tieset.py` (`TiesetScorer(neighbors=...)`), on by
default in `run`. Approved by the owner on 2026-10-18.

## Problem

SPX research results depend on which butterfly the selector picks at entry, and the pick
is fragile. Over the live paper cohort 2026-07-22 → 2026-10-16 (57 SPX trades), the
DB replay picked the same width and center as live on only 14 days. About $1,780 of the
$2,350 gap between replay and live came from days with a different fly. P&L depends on
about six settled winners per quarter, so one flipped winner moves a period by $1,000+.

The research core already scores robustness to fly choice (`research/tieset.py`). It
replays every fly that a mark shift of at most $0.10 / $0.25 could promote over the
winner. That covers near-ties in reward/risk at **one** snapshot. It does not cover a
different spot, VIX or quote state, which moves the VIX target center and the cost
filters. A recorded snapshot differs from what live saw because:

- the collector stamps a snapshot before fetching, and the stamps drift through the minute
  (see `schwab-fidelity-baseline-2026-10-04.md`);
- live fetches its chain at about 10:00:13 ET, between two collector snapshots;
- the replay's entry snapshot was stamped 40–60 s after live's decision on 39 of 57 days.

## Evidence

For each live SPX trade, whether live's fly is the replay winner or in its tie set,
with selection rerun at neighboring recorded snapshots (each with its own spot, VIX and
quotes):

| Snapshots searched | Exact | Within $0.10 | Within $0.25 |
|---|---:|---:|---:|
| Entry snapshot only (today's tie set) | 14 | 32 | 37 |
| Entry and next | 24 | 39 | 42 |
| **Previous, entry, next (±1)** | **41** | **53** | **54** |
| ±2 | 47 | 55 | 55 |

Of 57. Still uncovered at ±2 / $0.25: 2026-07-24 (−$129) and 2026-09-29 (−$200). At ±1
there is one more day, not yet identified.
At the entry snapshot only, the uncovered days included the 09-23 (+$944) and 10-05
(+$1,720) winners; ±1 covers both.

Scripts (scratch, not committed): `tiecover.py` and `neighbor.py`, built on
`run_backtest_db` loaders, `select_entry_candidate`, `selector_pool` and `promotion_shift`.

## Proposal

Add a **neighbor tie set** next to the existing one in `research/tieset.py`:

1. For each entry, take snapshots `index-1`, `index` and `index+1`, skipping any outside
   the session. They are **not** limited to the entry window: the entry snapshot is
   usually the first one stamped after 10:00, so `index-1` is stamped just before 10:00,
   and it is often the closer one to live's 10:00:13 fetch.
2. At each neighbor `j`, rerun the live `select_entry_candidate` with snapshot `j`'s own
   quotes, spot and VIX (the same VIX lookup the entry uses). Then build the existing
   $0.10 / $0.25 tie set around that neighbor's winner.
3. Replay each tied fly with the variant's own exits, entering at snapshot `j` (entry
   cost from `j`, monitoring from `j` onward).
4. Score in two stages, so a neighbor with many ties does not dominate. The per-session
   average is the mean over neighbors of the mean over that neighbor's flies. A random
   draw picks a neighbor, then a fly, keyed by (session, direction) as today, so draws
   stay paired across rules.
5. Report it as new rows (`nbr±1 @ $0.10`, `nbr±1 @ $0.25`) beside the current tie-set
   rows. The current rows stay unchanged, so past reports remain comparable.
   `meta.tieset` records the offsets.
6. Turn it on by default in `run`, with the existing tie set (`--no-tieset` skips both).
   `holdout`, `validate` and `diagnose` build their scorer without neighbors, so their
   output and run ids are unchanged. `meta.tieset.neighbor_offsets` is recorded only
   when neighbors are on, so `run` ids change, as they should, because the output does.

## What it does not change

- Variant decisions, the main replay, the registry, holdout protocol constants and the
  gates. This is a reported robustness figure, not a gate. Using it as a gate in a
  future registration would have to be pre-registered there.
- Live trading code.

## Caveats

- Snapshot `index+1` is recorded after the decision time. That is look-ahead for a
  tradable rule, but this is only a sensitivity measure, and live's own chain usually
  lies between `index` and `index+1`. The report labels it as such.
- Rules whose flies are not chosen by the live selector stay "not applicable", as today.
- Separate issue (not in scope): the replays decide on the first clock tick at or after
  10:00. The clock is the snapshot times, so this is the first snapshot stamped after
  10:00, often about 50 s after live decided at a fixed 10:00:13. This holds for both
  `run_backtest_db` and the research core's `frozen_20260921` / `live` profiles. The
  neighbor rows measure how much this matters. They do not change it.

## Verification plan

- Unit tests: neighbor dedupe, window edges, two-stage draw determinism and pairing.
- Rerun the coverage check through the new scorer and confirm about 53–54/57 at ±1.
- Run the catalog and record the runtime and how far the nbr±1 rows sit from today's
  tie-set rows for E0.

## First results (2026-10-18)

`run --variants X1 --baseline E0` on `spx_0dte`, stressed. The evaluation, trades and
existing tie-set rows are byte-identical to the run without neighbors. Run time went
from 9 s to 11 s.

| Variant | Rows | Mean tie size | Tie-set avg | Draw 5% | Draw median | Draw 95% | Beats E0 |
|---|---|---:|---:|---:|---:|---:|---:|
| E0 | $0.10 | 1.82 | 14,718 | 12,660 | 14,636 | 17,131 | — |
| E0 | nbr $0.10 | 5.6 | 11,778 | 7,039 | 11,927 | 16,160 | — |
| X1 | $0.10 | 1.82 | 11,137 | 8,344 | 10,892 | 14,928 | 0.048 |
| X1 | nbr $0.10 | 5.6 | 11,736 | 7,850 | 11,563 | 16,154 | 0.449 |

- E0's average falls by about $2,900 (20%), and its 5% draw falls from $12,660 to $7,039.
  The single-snapshot tie set understated how much E0's result depends on snapshot
  timing.
- At one snapshot, X1 beat E0 in 4.8% of draws, a clear loss. With neighbors it is 44.9%,
  close to a coin flip. A difference between rules that only shows at one snapshot
  should not be read as a real difference.
