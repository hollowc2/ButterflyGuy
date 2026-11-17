# Live exit order pricing: Phase 2 results (Step 1, Set A)

Run 2026-11-16 evening PT under the owner-approved plan
(`docs/research/exit-ladder-pricing-plan.md`). **Exploratory:** Set A uses stand-in signals,
not real exits, and every fill model rests on 5 real fills.

**Reproduce:**

```bash
uv run python tools/research_studies/exit_ladder_pricing_study.py extract   # read-only
uv run python tools/research_studies/exit_ladder_pricing_study.py run --set A
```

Code:
- `src/butterfly_guy/core/exit_pricing.py`: the limit rules, for live and research alike;
- `src/butterfly_guy/research/exit_pricing.py`: the fill models, replay and decision rule;
- `tests/test_exit_pricing.py`: 25 tests, including that the default reproduces today's
  limits on every step and the restart.

Outputs are written to `reports/research/exit-ladder-pricing/`.

## Decision

**Step 1 selects R3 (`mid_walk`, 20 s steps).** It starts at mid, walks to the fly bid by
+60 s, then holds at the bid. All three candidates passed criteria 1–5. R1 had the highest
primary mean ($3.31 against R3's $2.84), but the two are within $1. The pre-registered tie
rule then prefers the smaller change, and R2 was more than $1 behind.

**Next: Step 2 (confirmation on Set B).** It runs on the first 30 SPX paper exits with
post-exit polls from 2026-11-17, read as they accrue. Set B had **0 trades** at this run.
Until it passes, R3 is only an opt-in setting. The default stays R0 (today's ladder).

## Data

Set A:
- **Trades:** 69 SPX paper trades, 2026-08-03 to 2026-11-13. Live trade 415 is excluded
  and replayed separately.
- **Signals:** **349 stand-in signals**, each a poll where the drawdown from peak first rose
  through 30%. Each has 90 s of monitor polls after it with no gap over 30 s; none were
  dropped.
- **Spread at signal:** median $0.25, p90 $0.45, and 25 signals (7%) over $0.60. Real SPX
  exits have a median of $0.25 with 8% over $0.60, so the stand-ins resemble real exits.
- **Horizon:** 90 s. Anything still unfilled is valued at the fly bid at +90 s.

## Results: paired difference against R0, $ per exit

Each session's signals are averaged, then sessions are block-bootstrapped (block 5, 5,000
resamples, seed 20261117). mid50 is the primary model.

| Candidate | Model | Mean | Lower 90% | 95% CI | Worst exit | Qualifies |
|---|---|---|---|---|---|---|
| R2 mid-capped | touch | −0.67 | −1.77 | [−2.33, 1.72] | −20 | |
| | **mid50** | **1.35** | −0.05 | [−0.75, 3.52] | −20 | yes |
| | mid100 | 1.03 | −0.98 | [−1.89, 3.89] | −20 | |
| **R3 mid walk, 20 s** | touch | −0.10 | −1.61 | [−2.46, 3.32] | −140 | |
| | **mid50** | **2.84** | **0.82** | [−0.12, 6.33] | −20 | **yes, selected** |
| | mid100 | 3.34 | 0.66 | [−0.41, 7.54] | −20 | |
| R1 mid walk, 10 s | touch | 0.50 | −1.33 | [−2.33, 4.04] | −60 | |
| | **mid50** | **3.31** | 1.25 | [0.18, 6.91] | −20 | yes |
| | mid100 | 3.34 | 0.66 | [−0.41, 7.54] | −20 | |

Without the one signal with a negative fly bid (reported, not decided on), R3 is +$2.60
under mid50 with a lower bound of +$0.57.

### Speed: expected fill time after the signal

| | R0 today | R2 | R3 | R1 |
|---|---|---|---|---|
| mid50 | 28.1 s | 11.0 s | 10.2 s | 6.6 s |
| touch | 40.0 s | 33.7 s | 34.4 s | 22.9 s |
| P(filled by 90 s), touch | 0.89 | 0.92 | 0.96 | 1.00 |

### Where the difference comes from (mid50 mean, $ per exit)

| | n | R2 | R3 | R1 |
|---|---|---|---|---|
| Spread ≤ $0.60 | 324 | +0.71 | +0.09 | +0.52 |
| Spread > $0.60 | 25 | 0.00 | **+28.76** | +29.51 |
| Aug–Sep | 213 | −0.27 | +0.99 | +1.08 |
| Oct–Nov | 136 | +2.11 | +3.95 | +4.98 |
| VIX < 17 | 259 | −0.55 | +0.48 | +0.54 |
| VIX 17–24.5 | 90 | +4.11 | +6.95 | +8.54 |
| 10–12 PT | 50 | +1.61 | +6.84 | +7.79 |
| 12–13 PT | 19 | −0.26 | +4.69 | +8.45 |

Under the touch model, R3 is −$1.62 on narrow spreads and +$12.60 on wide ones.

What this means:

- **On narrow spreads (93%), the rule changes speed, not price.** R3 gets the same money as
  R0 (+$0.09) but fills about 18 s sooner under mid50. R0's first limit sits above the ask and
  only reaches mid at +40 s. Drift over that time averages zero, so the time saved is less
  exposure on a stop, not dollars.
- **Nearly all the dollar gain is the 25 wide-spread signals.** R0 starts at bid + 0.30 and
  fills there; R3 starts at mid. This is the 415 pattern, and it is exactly where p (the
  chance a limit at mid fills) is an assumption. It also explains why the gain is larger in
  Oct–Nov, at VIX 17–24.5 and late in the day.
- **R2 cannot help where it matters.** On wide spreads it is identical to R0 by
  construction.

### The 10 signals most affected (R3 − R0, mid50)

| Trade | Date | Time | Spread | Bid / mid | R3 − R0 |
|---|---|---|---|---|---|
| 291 | 09-16 | 10–12 PT | 4.65 | −0.10 / 2.23 | +180.00 |
| 393 | 11-05 | < 08 PT | 3.30 | 2.20 / 3.85 | +135.00 |
| 262 | 08-27 | 10–12 PT | 2.25 | 6.10 / 7.22 | +85.00 |
| 405 | 11-11 | 08–10 | 0.35 | 5.80 / 5.98 | +65.63 |
| 366 | 10-22 | 10–12 PT | 0.35 | 12.30 / 12.48 | +62.50 |
| 393 | 11-05 | < 08 PT | 2.00 | 2.80 / 3.80 | +52.50 |
| 372 | 10-26 | 08–10 | 0.35 | 7.85 / 8.02 | +51.25 |
| 405 | 11-11 | 10–12 PT | 0.45 | 19.90 / 20.12 | +50.00 |
| 405 | 11-11 | 10–12 PT | 0.35 | 19.55 / 19.73 | +45.00 |
| 366 | 10-22 | 12–13 PT | 0.35 | 15.15 / 15.32 | +42.50 |

The narrow-spread entries (405, 366, 372) are falling flies. R0 rested above the ask for
40 s while the bid dropped, and R3 filled at the start. Every one of the 10 favors R3. Under
mid50, R3's worst single exit is −$20.

## Trade 415 replay (illustration only, sparse real path)

The path starts at the order's own quote (bid 1.00, mid 1.85), then uses the broker quote at
+4 s and 1-minute collector points.

| Model | R0 | R2 | R3 | R1 |
|---|---|---|---|---|
| touch | 1.10 | 1.10 | 1.30 | 0.80 |
| mid50 | 1.20 | 1.20 | 1.64 | 1.56 |
| mid100 | **1.30** (the real fill) | 1.30 | 1.85 | 1.85 |

What the replay shows:
- **The real fill rules out the touch model.** Touch values R0 at 1.10, but the real order
  filled at 1.30, above a 1.00 bid, in about 1 s.
- **R3 was worth $34–55 more on 415 under the mid models.** That depends on a limit at mid
  having filled, which has never been tested on a wide spread.

## Caveats

- **Stand-in signals are not real exits.** Real exits fire on a deeper drawdown (60–90%
  thresholds), and their post-exit path is what Set B measures.
- **Oct–Nov polls are 75–78% exact repeats** (the gateway's 4 s cache), so they carry less
  information than Aug–Sep. The gain is positive in both eras, and larger in Oct–Nov.
- **The 5 real fills are all at the limit,** 4 of them at mid on spreads ≤ $0.20. **No
  wide-spread limit at mid has ever been tried.** R3's dollar case rests on that assumption.
  Its speed case does not.
- **The analysis is post hoc** on already-seen data. Step 2 (Set B) is the first test on
  unseen exits.

## Proposed design (Phase 3, pending owner approval)

**One new setting:** `execution.exit_pricing`, a `Literal["bid_ladder",
"mid_capped_ladder", "mid_walk"]`, default **`bid_ladder`**. R3 uses today's
`retry_interval_seconds` (20 s), so no interval setting is needed.

**`execute_exit` changes:**
- **Shared limit function:** it calls `core.exit_pricing.exit_limit` with a step counter
  that keeps counting across cycles, so `mid_walk` holds at the bid while `bid_ladder`
  restarts exactly as today.
- **Mid anchor:** a second 3-long deque of fly mids, next to the existing bid deque (L12
  protection unchanged).
- **No quote available:** both anchors fall back to the signal mark, as the bid anchor
  does today.

**Unchanged:**
- `round_credit_limit` increments;
- the operator-takeover checks before each step;
- the 300 s timeout and the `None` return, followed by a retry on the next signal;
- the live-test fresh-quote requirement.

**Tests:**
- the default reproduces today's limits over every step and the restart (as in
  `tests/test_exit_pricing.py`);
- a parity test that `execute_exit`'s submitted limits equal `exit_limit` for each rule;
- the config validation rejects unknown values.

**Paper reporting (approved, separate PR):** paper exits record `live_rule_first_limit` and
`live_rule_estimate` (mid50 on the exit-time quote) in `exit_execution_diagnostics`. P&L is
unchanged.

**Rollout:**
- the default stays R0 everywhere;
- in paper, the setting only exercises the plumbing;
- R3 goes live only in the supervised pilot's compose override, after Set B passes or if the
  owner opts in earlier;
- NDX and XSP are untouched.
