# Monitor cadence and exit confirmation: development-set results

Run 2026-11-16 under the pre-registration in `monitor-cadence-exit-design-plan.md`
(commit 3f2a43e). **Exploratory: every trade here was looked at before registration.** The
confirmation set has not been read; none of it exists yet.

Command:

```
uv run python tools/research_studies/monitor_replay_study.py --data <11-16 extraction> --set dev
```

Output: `reports/research/spx-monitor-cadence-exit/dev/` (`summary.json`, `trades.csv`).

## Outcome under the registered rule

**No arm is selected.** Every primary candidate has a negative development mean under all
three pricing models. Section 4 of the plan then says: keep current values and ship only the
plumbing.

**The development set cannot measure any arm that changes an exit.** That outcome is
therefore a statement about the data, not evidence that the arms are worse. See
[Why](#why-the-development-set-cannot-score-these-arms).

## Data

- 70 SPX trades with monitor polls from 2026-08-01 to 2026-11-16. 69 matched the as-live
  replay (same reason, within 10 s); 1 was excluded.
- Era: Aug–Sep 38 trades, Oct–Nov 31.
- By A0 exit: morning 38, afternoon 19, late morning 4, settled 8.
- A0 totals: mid +$3,141; ladder +$2,804; natural +$2,025.
- Trade 415, the live pilot trade, is included. Its peak is one of the 2 one-poll spike
  peaks.

## Results

Paired difference, arm minus A0, in $ per trade, 1-lot. CIs come from a block bootstrap
(block 5, 5,000 reps). The changed, settle and minute columns count trades.

| Arm | Rule | Ladder mean [95% CI] | Lower 90% | Mid mean | Natural mean | Changed | Settle | Scored on minute data | Worst |
|---|---|---|---|---|---|---|---|---|---|
| C1 | T = 5 s | −12.9 [−24.3, −4.2] | −21.5 | −12.2 | −12.3 | 61 | 9 | 60 | −180 |
| C2 | T = 10 s | −14.2 [−25.7, −5.1] | −23.0 | −13.5 | −13.6 | 61 | 9 | 60 | −180 |
| C3 | T = 20 s | −3.0 [−27.6, 34.3] | −24.3 | −2.3 | −2.1 | 61 | 10 | 59 | −180 |
| C4 | peak median 10 s | −2.5 [−4.5, −0.5] | −3.7 | −2.7 | −2.2 | 11 | 8 | 11 | −58 |
| C5 | C4 + T = 10 s | −15.2 [−26.7, −6.3] | −24.1 | −14.8 | −14.4 | 61 | 9 | 60 | −180 |
| C6 | leg filter | −3.4 [−7.3, −0.5] | −5.8 | −3.6 | −3.4 | 4 | 8 | 4 | −111 |

Diagnostics:

| Arm | Ladder mean [95% CI] | Changed | Scored on minute data |
|---|---|---|---|
| cad5 | −2.9 [−14.4, 5.5] | 36 | 35 |
| cad10 | −7.7 [−17.1, 1.8] | 48 | 46 |
| cad15 | −2.3 [−16.5, 12.5] | 56 | 54 |
| cad30 | −1.0 [−24.4, 36.7] | 55 | 51 |
| cad60 | +17.8 [−14.3, 62.8] | 60 | 53 |
| conf2 | −9.6 [−20.2, −1.5] | 61 | 60 |
| conf3 | −8.1 [−32.1, 28.1] | 61 | 58 |
| med10both | −6.9 [−17.1, 1.8] | 60 | 59 |

Per regime, ladder model:

- C4: morning −1.4 (n 38), afternoon −6.2 (n 19), late morning and settled 0.
- C6: morning −0.3, afternoon −5.9, settled −13.9 (n 8), late morning 0.

Request load: SPX monitor chain requests per held position are 23/min at 2.6 s, 12 at 5 s,
6 at 10 s and 1 at 60 s. The rule arms add none.

## Why the development set cannot score these arms

The monitor stops polling at the recorded exit. Any arm that exits **later**, whether by
confirming for T seconds, keeping a lower peak, or skipping polls, runs past the last
recorded poll. It then continues on the 1-minute collector snapshot, which comes 0–60 s
later.

The "scored on minute data" column shows this decides almost every changed trade:

- **C1–C5:** 60 of 61 changed exits were scored on minute data. A 5 s confirmation is
  scored as "exit at the next collector minute" (median hold change about 1 minute), not
  "exit 5 s later".
- **C4 and C6:** all 11 and all 4 changed exits continued on minute data. Their small
  negatives come from a handful of afternoon trades (274, 315, 415) valued 0–60 s late on
  1-minute marks.
- **Cadence diagnostics are not usable either.** The sign flips with the subsampling
  phase:
  - The 11-16 study's "minute" variant kept the last poll of each clock minute. That
    always includes the recorded exit poll, and it gave −$15/trade.
  - Here `cad60` subsamples from the first poll and usually skips the exit poll. It gives
    **+$17.8/trade** (CI −14 to +63).
  - The −$15/trade cadence cost quoted in the brief is therefore an artifact of the same
    truncation, not a measured cost of slower polling.

The excluded-from-minute-continuation subsets are too small to read: C1–C5 keep 9–10
trades, all held to settlement with identical outcomes.

Only data that continues past the exit at full cadence can score these arms: the
post-exit polls recorded since 2026-11-16 15:20 PT (PR #80).

## Trades the arms change

C4 changed 11 trades, all exiting later on 1-minute data; ladder difference in $:

- 218 (−5), 223 (−2), 241 (−20), 251 (−50, spike peak), 264 (−5), 270 (+34),
  274 (−58), 291 (−5), 303 (−4), 315 (−35), 415 (−20, spike peak).

C6 changed 4: 251 (−12), 274 (−58), 315 (−35), 415 (−20).

## What this means for the decision

1. **As registered: ship plumbing only.** Poll interval into config, unchanged defaults.
   The leg-quote fetch follows the Tuesday probe under its own pre-set criteria.
2. **The study question is still open, and it is answerable only on post-exit data.** No
   confirmation trade has been read, so the protocol can still be amended without bias.
   For example, use the first 30 post-exit trades as the development set and the next 30
   as the confirmation set: about 12 weeks at one trade a session. That change is the
   owner's decision; it is not made here.
3. **Correction to the brief:** "fast polling helps, −$15/trade at the backtest cadence"
   is not supported. The existing data cannot measure cadence.
