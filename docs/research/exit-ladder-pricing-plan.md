# Live exit order pricing: plan and pre-registration

Written 2026-11-16, after Phase 0 of `exit-ladder-pricing-prompt.md`. **Approved by the owner
2026-11-16** with the answers recorded under "Open questions". Nothing below had been run on
post-signal data that a decision will use when it was approved.

Order pricing is order routing. No live or paper order behavior changes until the owner
approves the Phase 2 design. Every new rule ships opt-in, with a default that reproduces
today's ladder exactly.

## Amendment 1 (owner, 2026-11-16, after Step 1, before any Set B trade existed)

**Why:** Set B re-checks quote paths under the same assumed fill model. It cannot test whether
a limit at mid fills on a wide spread, which is the open question for R3. Wide spreads are
about 7% of exits, so 30 trades (about six weeks) would contain about 2. The owner does not
want to wait that long.

**Change:**

- **Step 2 is no longer a gate.** Set B is still extracted and reported as it accrues, using
  the same criteria, but it does not block live use. Trades 31–60 stay unread until the
  cadence confirmation run.
- **Confirmation is the supervised live pilot (section 5).**
  - **Setting:** R3 (`mid_walk`) is set only in the pilot's compose override, on sessions
    the owner approves.
  - **Stop and revert to R0** on the existing stop rules: an exit still unfilled when its
    natural step is due (+60 s), or 2 of the first 5 exits filling later than R0 would have
    under FM-touch.
  - **Default:** after 10 pilot exits, re-estimate p by spread bucket from the real fills and
    re-run Step 1 with it. Making R3 the default still needs owner approval.

Everything else is unchanged.

## Phase 0 findings this plan relies on

Code and pilot:

- **Pilot code matches main.** The pilot image (`24726176`) and `main` (`a283610`) have the
  same `execute_exit` and SPX `execution` settings: step 0.10, 4 steps, 20 s, 300 s.
- **Today's ladder.** Each step's limit is
  `round_credit_limit(max(0.05, median(last 3 fly bids) + (3 − i) × 0.10))`, so bid + 0.30,
  +0.20, +0.10, +0.00, 20 s apart.
- **No forced cross.** After step 3 the cycle **restarts at bid + 0.30** and repeats until
  300 s. Then `execute_exit` returns `None`; the position stays open, and the monitor retries
  on the next signal.
- **Urgency is not used.** Every drawdown exit has `urgency="high"`, and only `end_of_day`
  has `"immediate"` (1 SPX exit with quotes). The ladder ignores urgency.
- **415's 2.00 entry limit** was the ask (2.60), capped at `max_cost_per_width[20]`. The
  pilot's `live_test_max_debit` (4.0) did not bind.

Spreads and ladder cost (SPX, 104 exits with a valid fly bid, May–Nov 2026):

- The median fly spread at exit is $0.25; 8% of exits are wider than $0.60.
- `min(mid, bid + 0.30)` costs **$4.81 per exit** against mid. It is $0 on 92% of exits; the
  cost sits in about 8 wide-spread exits, which cluster 12–13 PT and at VIX 17–24.5.
- **The model misses the time cost.** On 77% of SPX drawdown exits, today's first limit is
  **above the fly ask**. On 90 of 103, the ladder only reaches mid at step 2, 40 s after the
  signal. It waits when the spread is narrow and fills well below mid when it is wide.

Drift after the signal (SPX drawdown exits, 1-minute collector, against the quote the order
was priced on):

- The mean is ≈ 0, and the 95% CI includes 0 at every horizon up to 6 min.
- The left tail grows with time: p10 is −$18 by about 30 s, −$29 at 1–2 min and −$58 at
  4–5 min.

Real fills (5 in total):

- **Trade 415, exit:** filled at bid + 0.30 (1.30) in about 1 s with mid at 1.85. The fly
  then recovered: mid 2.10 at +34 s and 3.55 at +274 s.
- **10-19 manual tests:** two exits at mid filled in 1 s and 5 s. Mid + 0.05 rested 82 s
  unfilled. Two entries at mid filled in 4–9 s.
- **Price improvement:** none on 415. Schwab's `orderActivityCollection` gives leg execution
  prices at 1 s resolution, with no NBBO at execution.

Data on hand:

- **`post_exit_leg_quotes` had 0 rows** at the end of the 2026-11-16 session.

## 1. Candidate rules

Notation, per step:

- `b̃` is the median of the last 3 fly bids (today's L12 protection, kept unchanged). `m̃`
  is the median of the last 3 fly mids, with mid = (bid + ask) / 2.
- `R(x)` = `round_credit_limit(max(0.05, x), underlying)`: rounded **up** to $0.05 for SPX,
  so the order never accepts less than the rule computes.
- The ladder never prices below `b̃`.

| Id | Setting value | Limit at step i | Step interval | After the last step |
|---|---|---|---|---|
| **R0** | `bid_ladder` (default) | `R(b̃ + (3 − i) × 0.10)` | 20 s | restart at step 0 until 300 s (today) |
| **R2** | `mid_capped_ladder` | `min(R(m̃), R(b̃ + (3 − i) × 0.10))` | 20 s | same as R0 |
| **R3** | `mid_walk` | `R(m̃ − (i / 3) × (m̃ − b̃))` | 20 s | hold at `R(b̃)`, re-anchored each step, until 300 s |
| **R1** | `mid_walk`, 10 s | as R3 | 10 s | as R3 |

What each candidate changes:

- **R2 changes only narrow spreads.** It removes today's above-the-ask start and is
  identical to R0 whenever the spread is over $0.60. This is where real evidence exists:
  limits at mid filled 4 times out of 4.
- **R3 changes wide spreads too.** It starts at mid at today's pace and reaches the natural
  at the same time as R0, at +60 s. It is the candidate the 415 case is about. Its evidence
  is weakest, because no wide-spread limit at mid has ever been tried.
- **R1 is R3 at twice the speed.** It reaches the natural at +30 s and tests whether moving
  faster pays.

**Giving up and crossing.** "Cross" means a limit at the natural `R(b̃)`. Every candidate
offers the natural no later than R0 does (+60 s), so no candidate holds a stop longer than
today before offering the natural. This is a code property, checked by a unit test.

**Hard timeout.** Unchanged at 300 s, then `None` and a retry on the next signal.

**Dropped:**
- An urgency rule: urgency does not separate drawdown exits.
- `bid + k × spread` with k fitted: R2 and R3 already span the two ends, and fitting k to
  about 100 exits invites overfitting.

## 2. Fill model

Paper fills cannot show whether a resting limit fills. Each step's fill is modelled from the
**quote path** after the signal: fly bid and mid at every poll. A fill is always at the limit
L, with no improvement (as on 415 and every manual fill).

| Model | Rule while L rests (from its submission to the next step) | Rests on |
|---|---|---|
| **FM-touch (floor)** | Fills only when an observed fly bid ≥ L | Quote data only. **415 rules it out as a central case**: it filled 0.30 above the natural in 1 s. Kept as the pessimistic bound. |
| **FM-mid(p), primary p = 0.5** | Fills for certain if bid ≥ L. Otherwise, if an observed rounded mid ≥ L, fills with probability p (once per step) | 4/4 mid fills (2 exits, 2 entries, all on spreads ≤ $0.20); 0/1 at mid + 0.05; 415 at bid + 0.30. p = 0.5 is deliberately below the observed 4/4. |
| **FM-mid(1) (optimistic)** | As above, with p = 1 | Upper bound |

Expected credit is computed exactly over the step outcomes, with no simulation noise:
`E = Σ_i P(first fill at step i) × L_i`. The unfilled remainder is valued at the worst-case
bound below.

**Limits of the model:**
- Every mid-fill observation is from narrow spreads. On wide spreads, p is an assumption and
  every result is reported separately for spreads ≤ $0.60 and > $0.60.
- None of the model is fitted to P&L.
- When at least 10 bot exits exist, p is re-estimated by spread bucket and the analysis is
  re-run. This matches the cadence study's refit trigger.

**Worst-case bound, per exit.** No fill until the timeout: valued at the fly natural at
+300 s, the same for every candidate. A second, tighter bound is reported too: no fill until
the candidate's first natural step, then a fill at that step's natural.

## 3. Data

### Set A: exploratory stand-in signals (available now; selection)

The monitor's 2.6 s polls end at the exit, so real exits have no sub-minute path after the
signal. Set A uses stand-in signals inside holds instead:

- **Trades:** SPX trades 2026-08-01 to 2026-11-16 with monitor polls. This is the cadence
  study's *pilot* set, already seen and never used for its decisions.
- **Stand-in signal:** a poll where the drawdown from peak first rises through 30%. The
  smallest regime threshold is 60%, so this keeps falling-fly moments.
- **Requirements:** at least 90 s of polls after the stand-in signal and before the trade's
  real exit. At most one stand-in signal per trade per 5 min.
- **Gateway repeats:** in Oct–Nov, 75–78% of gateway-era polls repeat the previous one (4 s
  cache). Results are shown for Aug–Sep and Oct–Nov separately.

Set A is post hoc and its stand-in signals are not real exits, so it is labelled
**exploratory**. It is used to select one candidate.

### Set B: real post-exit polls (confirmation)

These are the post-exit polls of the cadence study's **development trades 1–30**: 2.6 s
quotes from the exit onward, on direct data. Coordination with
`research/monitor-cadence-exit` (Amendment 1):

- **Trades 1–30:** read only after the cadence development run (about end of December), or
  earlier if the owner allows it. That study's selection rule is fixed and mechanical, so
  reading the trades cannot change its result, but its plan does not grant other studies
  access.
- **Trades 31–60 are not read** before the cadence confirmation run (about mid-February).
  Its arms delay exits by T seconds, and post-signal drift is exactly that quantity.
- **Live-pilot exits** are reported separately and never pooled, as that plan requires.
- **Shipping a rule here does not change the cadence study's pre-registered pricing models.**
  Its ladder model stays `min(mid, natural + 0.30)` and may report the shipped rule as a
  diagnostic.

## 4. Metric and decision rule (fixed in advance)

**Metric.** The paired per-exit difference in expected credit, candidate minus R0, in $ per
1-lot SPX contract, under **FM-mid(0.5)**. Commission is identical across arms and drops
out. CIs use `block_bootstrap_indices` from `butterfly_guy.research.evaluate`:

- block 5, 5,000 resamples, seed 20261117;
- resampled over sessions, with each session's exits averaged so that a session with many
  stand-in signals does not dominate.

**Step 1, selection on Set A.** A candidate qualifies if all of the following hold:

1. FM-mid(0.5): mean ≥ 0, and lower one-sided 90% bound > −$5;
2. FM-mid(1): mean ≥ 0;
3. FM-touch: mean ≥ −$10;
4. worst single-exit difference under FM-mid(0.5) ≥ −$50;
5. it offers the natural no later than R0 (unit test; true for R1–R3 by construction).

Pick the qualifying candidate with the highest FM-mid(0.5) mean. If means are within $1,
prefer the smaller change: R2, then R3, then R1. **If none qualifies, keep R0** and consider
only the paper-reporting change (section 6).

**Step 2, confirmation of the one selected candidate (k = 1) on Set B.** Re-check criteria
1, 3 and 4 on its 30 exits. If they pass, the candidate becomes **eligible** as the
supervised live pilot's setting. Making it the default still needs owner approval and live
evidence (section 5). If they fail, revert to R0.

**Why so permissive, and what would justify adoption with so few real fills.**

- A P&L win cannot be shown here. The fill question rests on 5 observations. Over 1–2 min,
  drift barely differs from zero in either direction.
- The rule therefore asks that a candidate is **not clearly worse** under conservative fill
  assumptions and is never slower to cross.
- The case for adoption is the mechanism: today's first limit is above the ask on 77% of
  exits, so today's ladder waits 40 s on a stop for no reason, and crosses hardest exactly
  when the spread is widest.
- Under that rule, R2 is close to a free improvement on the 92% of exits with narrow spreads.
  R3 and R1 are bets on wide-spread mid fills, and those need live evidence.

**Reported, never used for the decision:**
- results by spread bucket, regime, VIX bucket and time of day;
- the 10 most affected exits;
- signal-to-fill time per candidate;
- 415 replayed under every candidate and model.

## 5. Live evidence needed, and a proposed supervised protocol

**Not run unless the owner asks.**

What needs live evidence:
- whether a wide-spread (> $0.60) limit at or near mid fills, and how fast (p on wide
  spreads);
- the time to fill at mid on narrow spreads in a falling fly.

Proposed protocol, only when the owner resumes the pilot:

- **Setting:** the selected candidate, set only in the pilot's compose override. The image
  default stays R0.
- **Recording:** existing `execution_observations` and `exit_ladder_steps`, plus each step's
  submit and cancel time and the quote at cancel (small additions in Phase 3).
- **Supervision:** Corey watches every exit. The operator-takeover path already hands the
  exit over on any manual action in thinkorswim.
- **Stop, revert to R0 and review if:** any exit is still unfilled when the natural step is
  due under R0's timing, or 2 of the first 5 exits fill later than R0 would have under
  FM-touch.
- **Refit:** after 10 bot exits, re-estimate p by spread bucket and re-run Step 1.

## 6. Paper reporting (review item L8)

Recommendation:

- **Keep** canonical paper P&L at the signal mark. That is the project convention, and the
  cadence and research ledgers depend on it.
- **Add** to `exit_execution_diagnostics` the first limit the configured live rule would
  submit (`live_rule_first_limit`), and its FM-mid(0.5) expected credit
  (`live_rule_estimate`).
- **Report** "paper at mark" alongside "paper at live-rule estimate" in the daily and weekly
  reports.

This is metadata only, with no change to fills or P&L. It is a separate owner decision and
can ship even if R0 is kept.

## 7. Phase 2 deliverables (after approval)

- **Pure functions** under `src/butterfly_guy/research/`, each with tests:
  - the rule as a function of `(rule, step, b̃, m̃, params, underlying)`;
  - the three fill models;
  - the stand-in signal extraction and the expected-credit scorer.
- **One limit function** used by both `execute_exit` and research when Phase 3 ships, with a
  parity test over every step.
- **Results document:** `docs/research/exit-ladder-pricing-results.md`.
- **Proposed settings:**
  - `execution.exit_pricing: bid_ladder | mid_capped_ladder | mid_walk`, default
    `bid_ladder`;
  - `execution.exit_step_interval_seconds`, defaulting to `retry_interval_seconds`.
- **Unchanged:** NDX and XSP keep R0. Their numbers are reported for scale only.

## Out of scope, noted

**Entries have the mirror-image issue.** The first entry limit is the ask (415: 2.60 against
a 2.10 mid), stepping up, and only the width cap made 415 bid 2.00. That is a separate study
if wanted.

## Owner decisions (2026-11-16)

1. Candidates R2, R3 and R1, the fill models and the decision rule: **approved as written.**
2. Set B (cadence development trades 1–30): **read as they accrue.** Trades 31–60 stay
   unread until the cadence confirmation run.
3. Paper-reporting addition (section 6): **approved**, independent of the pricing decision.
