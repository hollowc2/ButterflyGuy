# Registration decision package: ThetaData development window (2026-09-29)

**For the owner. Nothing is registered.** Every figure below comes from the development window
(2022-01-03 → 2024-06-28) and is **in-sample**. None of it is evidence of an edge. The sealed
holdout (2024-07-01 → 2026-03-12) was not downloaded, read or evaluated. Sessions from 2026-03-13
onward were not used.

**Revised the same day, after the owner's two decisions on the first version:**
- **D1: do not register yet.**
- **D3: floor stressed exits at $0.** This is Revision 1 of the pre-registration draft, marked
  there. It was made after seeing these results.

Every figure below uses the floored metric (`--floor-stressed-exits`) unless it is marked
"unfloored". The first version's unfloored figures are kept in §3 and §9 for the record.

This supersedes `registration-decision-2026-09.md` for the vendor path. That file still holds
each hypothesis's frozen implementation choices and the 2026 descriptive evidence.

## Conclusions

1. **E0 loses money on the development window.** Stressed net is −$9,685 over 361 trades
   (−$27 a trade, −$17 a session), and the whole fly-choice band is negative (5–95%: −$10.2k to
   −$9.3k). Midpoint accounting shows +$18.4k. The loss is concentrated in 2023 (−$15.1k) and in
   gap-down PUT entries (−$16.8k). Flooring changed six E0 exits and moved E0 by +$3.4k (it was
   −$13,085 unfloored).
2. **Only H-TS1 improves on E0 by more than fly-choice noise.** It gains +$7,402 (+$9,960
   unfloored): positive in both halves, +$7,317 with delayed exits, and better than E0 in 100%
   of fly-choice draws.
   - H-LV1 is worse than E0 (−$1,455): the 2026 pattern it came from reverses here.
   - H-SN1 is much worse (−$12,878), and it swings by $22.5k across its three centers.
   - H-EV1 is flat (+$151).
   - H-EV2 gains +$1,366 from 4 skipped trades but fails gate 2 (its H2 difference is 0).
3. **Even H-TS1 is weak evidence.**
   - In-sample it passes gate 1 only at k = 1 (+$859 at 90%); from k = 2 it fails.
   - Its threshold is fitted on these sessions.
   - Its stage-5 mechanism check was "not supported".
   - Because E0 loses, trading less helps by itself: skipping 69 random E0 trades gains $1.9k
     on average, and 13% of such skips gain as much as H-TS1 did.
   - H-TS1 itself still lost money (−$2,283).
4. **Status: not registered (D1).** If and when you register, the recommendation stays: H-TS1
   alone, k = 1. Its power on the holdout is about 49% if the development effect is
   real, and about 33% if it is half as large. A pass would show that H-TS1 loses less
   than E0, not that it makes money.
5. **Still open before any registration:**
   - D2: what a paired pass means against a losing E0.
   - D4: gate 1 over-passes on skip filters.
   - D5: early closes.
   - D9 (new): the holdout evaluation command does not exist yet.
   - D6 (Indices month) and D7 (ThetaData licence) also remain open.

## 1. Data and integrity

| Check | Result |
|---|---|
| `verify` | OK: dataset `93bbe58eb799c516f2a65bd5b20b7fdbc686e65681378d56c9279c8955a05d30`, 1,429 files; registry chains intact |
| `coverage`, development window | 585 sessions: all have a real SPX level, a 10:00 VIX, an official open and close; median 129 strikes × 390 minutes; missing and crossed rates 0 |
| E0 replay (`vendor_1m`) | 584 of 585 sessions |

**The one session E0 cannot replay is 2023-07-03, an early close (13:00).** E0's fly was still
open when the session's clock ended, and the replay treats a held trade on a clock that ends
before 15:00 as `incomplete_data` (`exits.MIN_END_OF_DAY_DATA_TIME`, inherited from
`SimulationEngine`). This is not missing data. The same rule dropped 2022-11-25 (early close)
from the H-SN1 comparison, because H-SN1 held a trade there. The holdout has five early closes
with data (2024-07-03, 2024-11-29, 2024-12-24, 2025-07-03, 2025-11-28); see D5.

The 625 trading days of the window: 31 had no 0-DTE expiration, 7 are frozen minute-file days,
2 were excluded by the owner, leaving 585, of which E0 replays 584.

**Data change made with the owner's approval (2026-09-29):** `export-vol --cboe` added Cboe's
daily VIX-family closes to the vendor dataset for H-TS1 (`aux/vol_index_daily.parquet`, 18,617
rows, sha256 `7fa50f1c…`; aux_hash `eab136c9eb93b0b410217f5c15b0ed62e9e159a377cba8bd9fc77cfa21b19278`).
The dataset hash did not change. The development-window rows are identical to `spx_0dte`'s
copy. The file also holds holdout-dated closes. They are read only for a session being
replayed, and holdout sessions cannot be replayed without an unseal.

## 2. Baseline E0 (descriptive; do not tune on it)

Run `7d7f91ad9ba5`: 584 sessions, halves split at 2023-04-26 (292 / 292 sessions, fixed by
session count before any result was seen). Stressed accounting with exits floored at $0,
unless noted.

| | Value |
|---|---:|
| Trades / sessions | 361 / 584 (no entry on 223) |
| Stressed net | **−$9,685** (unfloored −$13,085) |
| per trade / per session | −$27 / −$17 |
| Midpoint / delayed-exit stressed | +$18,362 / −$8,281 |
| $0.10 tie-set average, draw 5–95% | −$9,747; −$10,150 … −$9,345 |
| Win rate; median trade; trade SD | 13.6%; −$220; $667 |
| Settled (cash) | 78 trades, 43 winners, +$54,916 |
| Exits floored at $0 | 6 (stressed), 6 (delayed) |
| Top three trades, share of gross wins | 15.1% |

On 1-minute vendor data near-ties are rare (1.04 flies per tie set). With the floor, the
fly-choice band is only $0.8k wide over 584 sessions. On the validation window, unfloored, it
was $4.6k over 126 sessions.

**By year:**

| Year | Sessions | Trades | Stressed | /trade | Tie-set 5–95% | Delayed | Settled |
|---|---:|---:|---:|---:|---|---:|---:|
| 2022 | 213 | 75 | +5,989 | +80 | +6.0k … +6.0k | +6,224 | 15 |
| 2023 | 249 | 175 | **−15,058** | −86 | −15.1k … −14.8k | −14,447 | 36 |
| 2024 (to 06-28) | 122 | 111 | −616 | −6 | −1.1k … −0.6k | −57 | 27 |
| H1 (≤ 2023-04-26) | 292 | 115 | +3,172 | +28 | +3.2k … +3.5k | +3,587 | 24 |
| H2 | 292 | 246 | −12,857 | −52 | −13.3k … −12.8k | −11,867 | 54 |

2022's gain is mostly July (+$5.6k), October (+$2.9k on one trade) and December (+$2.2k).

**By VIX at 10:00** (buckets as in the config, lower bound inclusive):

| VIX | Sessions | Trades | Stressed | /trade | Tie-set 5–95% |
|---|---:|---:|---:|---:|---|
| < 17 | 241 | 225 | −10,662 | −47 | −11.1k … −10.6k |
| 17 – 24.5 | 223 | 130 | −336 | −3 | −0.3k … −0.1k |
| 24.5 – 32 | 104 | 6 | +1,313 | +219 | +1.3k |
| ≥ 32 | 16 | 0 | 0 | — | — |

E0 almost never enters when VIX is 24.5 or higher (6 trades in 120 sessions). Most no-trade
sessions are 2022 high-VIX days (110) and 2023 days at VIX 17–24.5 (61).

**By gap direction** (official open vs prior official close):

| Gap | Sessions | Trades | Stressed | /trade | Tie-set 5–95% | Midpoint |
|---|---:|---:|---:|---:|---|---:|
| Up (CALL) | 305 | 203 | +7,149 | +35 | +7.1k … +7.4k | +21,849 |
| Down (PUT) | 279 | 158 | **−16,834** | −107 | −17.3k … −16.7k | −3,487 |

By entry VIX and direction (unfloored), the low-VIX losses are the puts (−$14,216 over 96
trades), not the calls (+$1,452 over 135). That is the reverse of the 2026 sample that H-LV1
came from. Floored, the low-VIX calls made +$1,455.

**Exit reasons:**

| Exit | Trades | Stressed | Delayed | Midpoint |
|---|---:|---:|---:|---:|
| Cash-settled | 78 | +54,916 | +54,916 | +58,161 |
| Drawdown, morning | 169 | −36,664 | −36,334 | −24,029 |
| Drawdown, late morning | 17 | −5,336 | −5,298 | −4,153 |
| Drawdown, afternoon | 97 | −22,601 | −21,565 | −11,617 |

The delayed-exit model still does a little better than the stressed one (−$8.3k against
−$9.7k): a fill one minute after an afternoon trigger is often better. The monthly equity
curve is in the appendix.

## 3. The hypotheses on the development window (in-sample)

Each rule is paired with E0 on identical sessions. The draft's bootstrap was used: 10-session
blocks, 10,000 reps, seed 1. Gate 3 removes the union of each arm's three largest sessions. The
skip filters come from run `7d7f91ad9ba5` (584 sessions). H-SN1 and its secondaries come from
run `9971c5db1313` (583 sessions, which also drops 2022-11-25); the skip filters' Δ there is
identical.

| | H-TS1 | H-EV2 | H-EV1 | H-LV1 | H-SN1 |
|---|---:|---:|---:|---:|---:|
| Trades (E0: 361) | 292 | 357 | 316 | 226 | 558 |
| Own stressed net | −2,283 | −8,319 | −9,534 | −11,140 | −22,323 |
| **Δ vs E0 (stressed, floored)** | **+7,402** | +1,366 | +151 | −1,455 | −12,878 |
| Δ, H1 / H2 | +3,517 / +3,885 | +1,366 / 0 | +948 / −797 | +273 / −1,728 | −17,476 / +4,598 |
| Δ, top three of either arm removed | +10,761 | +1,366 | +151 | −1,455 | −19,602 |
| Δ, delayed exits | +7,317 | +1,326 | +116 | −1,787 | −13,437 |
| Bootstrap P(Δ > 0) | 0.925 | 0.985 | 0.501 | 0.398 | 0.158 |
| Lower bound 90% (k = 1) | **+859** | +498 | −5,626 | −10,296 | −29,248 |
| Lower bound 95% (k = 2) | −1,338 | +283 | −7,384 | −12,877 | −33,966 |
| Lower bound 97.5% (k = 4) | −3,001 | +135 | −8,912 | −15,116 | −37,547 |
| Draft gates 1–4 on dev | pass at k = 1; fail g1 at k ≥ 2 | fail g2 (H2 Δ = 0) | fail g1, g2 | fail all | fail all |
| Fly choice: Δ across paired draws, 5–95% | +7.1k … +7.4k | +1.3k … +1.4k | +116 … +151 | −1,465 … −1,455 | n/a |
| Fly choice: share of draws beating E0 | 100% | 100% | 100% | 0% | n/a |
| Exits floored (stressed) | 3 | 4 | 6 | 5 | 14 |
| *Unfloored Δ (first version)* | *+9,960* | *+3,831* | *+151* | *−1,452* | *−9,814* |

**What trading less is worth when E0 loses.** A skip filter gains whenever the trades it drops
are worse than the ones it keeps. When E0 loses on average, dropping any trade gains
something. To compare, E0 trades were drawn at random (20,000 draws of the same number):

| | H-TS1 | H-EV2 | H-EV1 | H-LV1 |
|---|---:|---:|---:|---:|
| E0 trades skipped | 69 | 4 | 45 | 135 |
| Mean stressed P&L, skipped / kept | −107 / −8 | −341 / −23 | −3 / −30 | +11 / −49 |
| Expected gain from a random skip of that size | +1,851 | +107 | +1,207 | +3,622 |
| Share of random skips gaining at least as much | 13% | 1.9% | 62% | 79% |

**Is each result robust to fly-choice noise?**
- **H-TS1:** yes. Its Δ is positive in every fly-choice draw and nine times E0's own 5–95%
  band width ($0.8k).
- **H-LV1:** robustly negative.
- **H-EV1:** robustly near zero.
- **H-EV2:** stable in sign across draws, but it rests on four trades.
- **H-SN1:** the live selector does not choose its flies, so it has no tie-set. Its analogue,
  the spread across centers 1.48σ, 1.58σ and 1.68σ (−$30,209, −$22,323, −$44,852), is $22.5k,
  about 28 times E0's band. Gate 5 fails.

**Per hypothesis:**
- **H-TS1** (skip when the prior-session VIX1D/VIX ≥ 0.9181935615930604).
  - The fit used 528 development sessions with a prior VIX1D. That is the only fitted value,
    and it used the feature alone, never P&L. The floor does not change it.
  - Unfloored, the gain was concentrated in 2023 (+$8.6k of +$10.0k).
  - It gave up 12 settled trades (+$8.2k) to avoid trailer-exit losses.
  - Three of its skipped sessions had exits floored, including 2022-12-14.
  - It never skips before 2022-05-16, where no VIX1D exists.
  - The stage-5 check on Cboe closes found high-ratio sessions moved slightly *more*
    relative to VIX1D, not less. So the P&L result has no supporting mechanism evidence.
- **H-LV1** (skip CALL entries at VIX < 17).
  - It skips 135 trades, 37% of E0's, which earned +$1,455.
  - The 2026 signal it came from was already confounded with H2. On 2022–24 its direction
    reverses.
- **H-SN1** (σ-placed fly).
  - It trades on 558 of 583 sessions, against E0's 360, because it has no reward/risk
    filter and enters at high VIX, where E0 rarely does.
  - Its expectancy is −$40 a trade against E0's −$26, and its placement noise is far larger.
    Both of the draft's claims fail in-sample.
- **H-EV1** (skip a CPI, NFP or PCE release before 10:00).
  - 45 skipped trades averaged −$3, against −$30 for the trades kept. It does worse than a
    random skip of the same size would be expected to.
- **H-EV2** (skip FOMC statement days; built 2026-09-29, `EventDaySkipEntry`).
  - E0 traded on only 4 of the 19 development FOMC sessions: 2022-07-27, 2022-12-14,
    2023-02-01 and 2023-03-22. The 20th FOMC day, 2024-01-31, is a frozen VIX day.
  - All four are in H1, so gate 2 fails.
  - About 11 FOMC days fall in the usable holdout, so expect 2–3 E0 trades.

## 4. Holdout size and power

**Size.** These counts come from the exchange calendar and the known gaps only. No holdout data
was read.

| | Without Indices | With an Indices month (gap filled) |
|---|---:|---:|
| Trading days 2024-07-01 → 2026-03-12 | 426 | 426 |
| Gap 2025-12-10 → 2026-03-12 (no SPX/VIX minutes) | −63 | 0 |
| Frozen minute-file days (2024-07-18, 07-25, 08-02, 09-06, 11-20) | −5 | −5 |
| **Usable sessions** | **358** | **421** |
| Draft halves: H1 (→ 2025-04-30) / H2 | 204 / 154 | 204 / 217 |
| Early closes that may drop (D5) | 0–5 | 0–5 |
| E0 trades at the development trade rate (61.7%) | ≈ 221 | ≈ 260 |
| H-TS1 skipped trades at the development rate (19% of E0's) | ≈ 42 | ≈ 50 |

The trade rate depends on VIX: E0 barely trades at 24.5 or above. The holdout's rate will differ.

**Power, from the development-window paired vectors** (floored metric).
- Simulated holdouts resample development sessions in 10-session blocks.
- Each simulated holdout then gets the draft's percentile bootstrap (2,000 reps) at the level
  for k, plus gates 2–4.
- There are 1,000 simulations per cell, so each figure is good to about ±1.5 points.
- All of this assumes 2022–24 is representative of 2024–26.

Full gate set, 358 sessions:

| Hypothesis | Scenario | k = 1 | k = 2 | k = 3 | k = 4 | k = 5 |
|---|---|---:|---:|---:|---:|---:|
| H-TS1 | development effect is real (+$12.67/session) | 49% | 40% | 34% | 33% | 31% |
| H-TS1 | half the development effect | 33% | 25% | 22% | 20% | 18% |
| H-TS1 | no effect (false pass) | 18% | 14% | 11% | 10% | 9.2% |
| H-TS1 | no mechanism, E0 negative as on dev (random skip) | 25% | 19% | 16% | 15% | 14% |
| H-EV1 | development effect (≈ none) | 15% | 9.5% | 6.8% | 6.0% | 5.6% |
| H-LV1 | development effect (negative) | 9.4% | 5.5% | 3.6% | 2.7% | 2.2% |
| H-EV2 | development effect (4 trades; unreliable) | 38% | 36% | 22% | 20% | 19% |
| H-EV2 | half the development effect | 16% | 9.0% | 5.5% | 3.8% | 2.8% |
| H-SN1 | development effect (negative) | 1.3% | 0.8% | 0.5% | 0.3% | 0.1% |

**An Indices month (421 sessions) buys no measurable power.** H-TS1 is at 50% at k = 1 and
32% at k = 4, against 49% and 33%, which is within simulation error. A real effect grows the
total with n but the noise with √n, so 63 more sessions change little. The month would buy data
quality and the VIX cross-check, not power.

H-EV2's development-effect row overstates it: its four trades are all in development H1, but
resampling spreads them across both simulated halves.

**Minimum detectable total effect** (80% power, gate 1 alone, normal approximation from the
development dispersion):

| | k = 1 | k = 4 | k = 5 | Development effect scaled to 358 sessions |
|---|---:|---:|---:|---:|
| H-TS1 | $8.2k ($23/session) | $10.9k | $11.2k | $4.5k |
| H-EV1 | $6.9k | $9.2k | $9.5k | $0.1k |
| H-LV1 | $10.8k | $14.2k | $14.7k | −$0.9k |
| H-EV2 | $1.2k | $1.6k | $1.7k | $0.8k |
| H-SN1 | $21.3k | $28.2k | $29.1k | −$7.9k |

H-TS1's in-sample effect is about half its minimum detectable effect at k = 1, and in-sample
winners usually shrink out of sample.

## 5. VIX-smoothing sensitivity

The owner's VIX file misses brief intraday highs and lows (median 1.6%). The strategy reads VIX
as a level at the entry minute, about 10:00. How far that level is off cannot be measured
without an independent intraday source.

| Where VIX decides something | E0 entries within ±0.25 | Within ±0.50 |
|---|---:|---:|
| Width bucket at 17.0 | 16 | 28 |
| Width bucket at 24.5 | 8 | 11 |
| Width bucket at 32.0 | 0 | 0 |
| **Any bucket edge** | **24 of 361 (6.6%)**: net +$5,012, gross absolute P&L $13,804 | 39 (10.8%): net +$3,427 |
| H-LV1's 17.0 call threshold | 7 calls, net −$1,434 | 14 calls, net −$3,398 |

- A bucket flip changes the candidate widths, not whether E0 trades. The P&L at risk is at
  most what those trades made or lost.
- Between buckets VIX sets the center target continuously. A 1.6% level error moves the
  widest-anchor offset by 0.54 points (median; 95th percentile 0.73), against a 5-point strike
  grid and 15-point tolerance. It rarely changes the chosen fly.
- **H-TS1 is not affected:** it reads Cboe's official daily closes, which match the file's
  closes. H-EV1 and H-EV2 read the event calendar. H-SN1 uses VIX only to require a fresh print.
- **Holdout exposure at the development rate:** about 15 E0 entries near a bucket edge, and
  about 4 H-LV1 calls near 17.

## 6. Findings that affect the test itself

### 6.1 Stressed exits below zero: decided, now floored (D3, draft Revision 1)

A butterfly is never worth less than $0. The unfloored stressed model crossed each leg's quoted
spread separately, so in a minute when spreads blew out it "paid" to close. Six E0 trades on
the development window did this: −$5,476 stressed, against −$514 at midpoint.

| Date | Fly | Exit (ET) | Midpoint exit | Unfloored stressed exit | Unfloored P&L |
|---|---|---|---:|---:|---:|
| 2022-12-14 (FOMC) | PUT 20-wide, $1.75 | 14:00 | 0.05 | −22.53 | −2,535 |
| 2023-12-20 | PUT 30-wide, $2.78 | 16:00 | 3.37 | −8.28 | −1,140 |
| 2023-03-17 | PUT 20-wide, $1.20 | 15:48 | 1.27 | −0.93 | −675 |
| 2022-07-27 (FOMC) | CALL 20-wide, $0.65 | 15:05 | 0.82 | −2.13 | −575 |
| 2023-04-20 | PUT 30-wide, $2.73 | 13:06 | 0.17 | −0.13 | −320 |
| 2024-05-28 | CALL 30-wide, $1.88 | 13:30 | 0.30 | −0.03 | −230 |

**What was done.**
- `--floor-stressed-exits` books such an exit at $0 of net proceeds, in the stressed and
  delayed models only.
- It is off by default. Helios data has such exits too (3 of the 118 frozen-parity trades,
  40 exits across the idea-sweep catalog), so the frozen-replay parity and the idea-sweep
  reproductions are left exactly as they were.
- With the flag off, the parity check still gives 118 trades and 0 mismatches, and the parity
  `trades.jsonl` is byte-identical (`b5b732ad…`).
- Every vendor-sweep run, the holdout evaluation included, must pass the flag. The run records
  it in its meta and report, and marks each floored fill `exit_floored` in `trades.jsonl`.

The floor is conservative: it books $0, not the settlement value the fly could still have
reached if held.

### 6.2 Gate 1 passes skip filters too often under the null (D4, open)

The draft expects a per-test false-pass rate of α/k. With a skip filter the paired difference is
zero on most sessions, and a few large settled winners dominate it. In that case the percentile
block bootstrap's lower bound is too optimistic. Simulated with the exact bootstrap at 358
sessions, floored, with no true effect:

| Gate 1 alone, no effect | k = 1 (nominal 10%) | k = 4 (nominal 2.5%) |
|---|---:|---:|
| H-TS1 | 19% | 10% |
| H-EV1 | 15% | 6.1% |
| H-LV1 | 13% | 5.1% |
| H-SN1 (dense difference) | 9.4% | 2.0% |

- Gates 2–4 trim this only a little: H-TS1's all-gates false-pass rate is 18% at k = 1
  and 10% at k = 4.
- If all five were registered and none had a real effect, the chance that at least one passes
  would be up to about 21% (union bound at k = 5), not the draft's "at most about 10%".
- If E0 also loses in the holdout as it did here, skip filters with no real mechanism would
  pass even more often (the random-skip rows in §4). The union bound then reaches about 33%.

### 6.3 A paired pass against a losing baseline (D2, open)

The primary metric is the paired difference from E0. With E0 negative, any rule that trades
less gains something without a mechanism. The draft's gates have no check on the rule's own
P&L, so a pass would mean "loses less than E0". H-TS1's own in-sample stressed net is −$2,283.

### 6.4 Early closes (D5, open)

See §1. On the holdout up to five early-close sessions can drop from every arm. The drop is
symmetric across arms, but it removes sessions where a trade was held, and held trades carry
most of the P&L.

### 6.5 There is no holdout evaluation command yet (D9, new)

`run` has no `--unseal-holdout` option: today only `export-history` and `coverage` accept one.
So no command can evaluate a registered rule on holdout sessions yet. It has to be built,
tested and committed before registration, because `register` freezes the `git_sha`. It must
also run with `--floor-stressed-exits`.

## 7. Recommendation and frozen definitions

**Status: not registered (owner's decision D1, 2026-09-29).**

**If and when you register: H-TS1 alone, k = 1.**
- Gate 1 is then the 90% one-sided lower bound.
- Gates 2–4 as drafted, on the floored metric.
- Holdout halves as drafted: H1 2024-07-01 → 2025-04-30, H2 2025-05-01 → 2026-03-12.

**Drop:**
- H-LV1: sign reversed in-sample.
- H-SN1: worse, and fails its noise secondary.
- H-EV1: no effect, and its 2026 mechanism was contradicted.
- H-EV2: 4 trades, all in one half; about 2–3 expected on the holdout; no power.

Registering any of them adds nothing likely to pass and lowers H-TS1's power (§4).

**H-TS1 as it would be registered** (from run `7d7f91ad9ba5`; the rule itself is unchanged by
the floor):

| Field | Value |
|---|---|
| Variant | `HTS1` |
| Rule | `butterfly_guy.research.hypotheses.PriorRatioFilter(E0, "vix1d_vix", 2022-01-03, 2024-06-28, quantile = 2/3)` |
| Definition hash | `fab8bf3e0ab10805d8b6d8ee19617df7013c0fa776ed6fbf86314c6238ff69c6` |
| Rule source sha256 | `e6405132a2b00eaa45b93677daeb8a22bd80a5991f81645f14de406519c1e997` |
| **Frozen threshold** | **0.9181935615930604** (skip at or above) |
| Fit sample | 528 development sessions with a prior VIX1D (`numpy.quantile`, linear) |
| Base (E0) | `BaselineEntry(direction="gap")`, runtime trailer; E0 hash `b2c766d25acd1ebe9756428592b62e71e01d5cee5a6dab04490af988cc560e48` |
| **Accounting** | stressed marketable with `--floor-stressed-exits` (run meta `accounting.stressed_exit_floor: 0.0`) |
| Feature input | `aux/vol_index_daily.parquet` sha256 `7fa50f1c887f0cf305d9d7903a2cacda1883324c1d0acedd4cf0821119d5b21c`, aux_hash `eab136c9eb93b0b410217f5c15b0ed62e9e159a377cba8bd9fc77cfa21b19278` |
| Config | `configs/config.yaml` sha256 `d120b63fd4e12ed812cc2742d602f9e531a1f5ca38e28c30628ab149f5d1b397` |
| Dataset | `spx_0dte_thetadata` @ `93bbe58eb799c516f2a65bd5b20b7fdbc686e65681378d56c9279c8955a05d30` (manifest shows `holdout_sessions: 0`) |
| Profile | `vendor_1m` |

**What the hash does not cover.** The threshold, the accounting flag, E0's code, `features.py`
and the config are frozen only by the register record's `git_sha`, the note, and each run's
recorded meta. The holdout run re-fits the threshold on the development window. **It must
reproduce 0.9181935615930604 exactly**, and its meta must show `stressed_exit_floor: 0.0`. Any
change to the replay code (D5, D9) must be committed before `register`.

**The other rules' hashes, for the record:** HLV1 `6ed12752…`, HSN1 `4589760a…`, HSN1_c148
`844e32da…`, HSN1_c168 `f0967c75…`, HEV1 `9180c56d…`, HEV2 `b0c670c0…` (full values in
`research-core.md`).

**The multiple-testing k.** The draft sets k to the number actually registered. The
recommendation gives k = 1. Each extra hypothesis raises k by one and costs H-TS1 power (§4).
The variant count on this dataset (8, §9) is reported alongside; it is not k.

**How to register, if and when you decide to** (from a clean, committed tree, after D9 is
built, and before any holdout pull):

```bash
uv run python -m butterfly_guy.research --dataset spx_0dte_thetadata register --variants HTS1 \
  --note "H-TS1 alone, k=1; threshold 0.9181935615930604 (n=528); --floor-stressed-exits; halves 2025-04-30; <D2/D4/D5/D6 choices>"
```

This writes the first record of `reports/research/registry/spx_0dte_thetadata.jsonl`. The
development registry is a separate file and is never read by the unseal.

## 8. Owner decisions

| # | Decision | Status and options | Before |
|---|---|---|---|
| D1 | Register now, or not yet? | **Decided 2026-09-29: not yet.** When you do: H-TS1 alone, k = 1 is recommended. Only what is registered before the holdout pull can ever be tested on it | — |
| D3 | Stressed exits below zero | **Decided 2026-09-29: floor at $0** (draft Revision 1; `--floor-stressed-exits`; §6.1) | done |
| D8 | Development registry | **Confirmed 2026-09-29:** development runs are recorded in `registry/development/` | done |
| D2 | Meaning of a pass against a losing E0 | Open. Accept that a pass means "loses less than E0", or add the rule's own stressed P&L as a reported (or gating) secondary. A new gate is a marked revision of the draft | registration |
| D4 | Gate 1 on skip filters (§6.2) | Open. Accept and state the real false-pass rates, or change the test (for example a random-skip null of the same size). A marked revision | registration |
| D5 | Early closes (§6.4) | Open. Accept the symmetric drop (0–5 holdout sessions), or let a held trade settle on a shortened session's close (code change; moves E0 on 2 development sessions) | registration |
| D9 | Holdout evaluation command (§6.5) | Open. Build `run --unseal-holdout` (with tests), always with `--floor-stressed-exits` | registration |
| D6 | ThetaData Indices month ($50) | Open. Fills the 63-session gap: 358 → 421 sessions, H2 154 → 217 (no measurable power gain, §4). Gives a real intraday VIX to check the smoothing (§5; H-TS1 is not affected) and cross-checks the owner's files. The gap pull is holdout data, so it can happen only after registration, but whether the holdout includes those sessions should be fixed in the register note | registration |
| D7 | ThetaData licence | Open. Terms §2.1(i) and §12.2: may the local cache outlive a cancelled subscription? The holdout result's reproducibility and any later audit depend on the answer | holdout pull |

## 9. Variant count and provenance

- **On `spx_0dte_thetadata`: 8 distinct definitions, all tried post hoc on development data:**
  E0, HLV1, HSN1, HSN1_c148, HSN1_c168, HEV1, HEV2, HTS1.
  - They are recorded in `reports/research/registry/development/spx_0dte_thetadata.jsonl`:
    25 `evaluate` records over five runs, chain intact.
  - Record 0 is an E0 run (`9bc6b6fc2187`) with a placeholder split (2023-04-01). It was
    superseded by the 2023-04-26 split before any result was read.
  - The floor is an accounting option, not a new definition, so the count stays 8.
  - The validation-window replays (runs `17304d08065e`, `b41290589484`) used E0 only and wrote
    no registry record.
- **For context:** 49 definitions were tried on the Helios dataset `spx_0dte`, 2026 sessions.

| Run | Accounting | Git | Variants | `results.json` | `trades.jsonl` |
|---|---|---|---|---|---|
| **`7d7f91ad9ba5`** | floored (primary) | `7b1f229` | E0, HLV1, HEV1, HEV2, HTS1 | `f361f0f16d61fb62fdc67a4517f114b071dcd18d6c6a1e86b7a826c9b4233339` | `1b58160a0c5b11ec5600587b30f3ab1fa3440e4c802351937409c7d1ca614bfc` |
| **`9971c5db1313`** | floored (primary) | `7b1f229` | E0, HLV1, HSN1, HSN1_c148, HSN1_c168, HEV1, HEV2 | `415a3b2d441457175289576b23dddba016efd525b3eea7423b1ce6e4bc4e0605` | `cc5d9429a2376080528cc77e29d05e7a31cf71436c1689ebe2555b706a726566` |
| `9eccee6a6aa5` | unfloored (first version) | `a36b110` | E0, HLV1, HEV1, HEV2, HTS1 | `2c04250527580e0f2fbcf3af79cfeccba7c3a71637e78237a72147e035f6a7d5` | `4d781b44b6f71fb74177b9038287e870ba956fe3eb4a41ee851751b430a5765f` |
| `da7a9163c0fa` | unfloored (first version) | `a36b110` | E0, HLV1, HSN1, HSN1_c148, HSN1_c168, HEV1, HEV2 | `429d0829fce337efac6728b5ce9d58fd6d46a4a00d23de896caaa3810ee74ebe` | `91087b5696760deda7e9639e60562cb37768d6e8c2c880adf477025d65377567` |

```bash
uv run python -m butterfly_guy.research --dataset spx_0dte_thetadata \
  --registry reports/research/registry/development run --variants E0,HLV1,HEV1,HEV2,HTS1 \
  --baseline E0 --profile vendor_1m --start 2022-01-03 --end 2024-06-28 --split 2023-04-26 \
  --block 10 --reps 10000 --floor-stressed-exits
uv run python -m butterfly_guy.research --dataset spx_0dte_thetadata \
  --registry reports/research/registry/development run \
  --variants E0,HLV1,HSN1,HSN1_c148,HSN1_c168,HEV1,HEV2 --baseline E0 --profile vendor_1m \
  --start 2022-01-03 --end 2024-06-28 --split 2023-04-26 --block 10 --reps 10000 \
  --floor-stressed-exits
```

**Ad hoc analysis** was not committed: the breakdowns, the random-skip comparison and the power
simulation. They are scratch scripts that read the same runs in-process with the same
accounting. The in-process replay matched every CLI run's totals exactly.
- The power simulation draws 10-session blocks from the development pairs to 358 or 421
  sessions.
- It applies the draft's percentile bootstrap (2,000 reps) and gates 2–4, with 1,000
  simulations per cell.
- For "no effect" and "half effect" it shifts the paired difference by a constant per session.

## Appendix: E0 monthly equity curve (stressed, floored, development window)

| Month | Sessions | Trades | Net | Cumulative |
|---|---:|---:|---:|---:|
| 2022-01 | 13 | 7 | −1,231 | −1,231 |
| 2022-02 | 10 | 3 | −1,063 | −2,294 |
| 2022-03 | 13 | 7 | −1,134 | −3,428 |
| 2022-04 | 14 | 10 | −326 | −3,754 |
| 2022-05 | 18 | 1 | −375 | −4,129 |
| 2022-06 | 20 | 2 | −760 | −4,889 |
| 2022-07 | 20 | 6 | +5,640 | +751 |
| 2022-08 | 23 | 15 | −369 | +382 |
| 2022-09 | 21 | 2 | −470 | −88 |
| 2022-10 | 19 | 1 | +2,914 | +2,826 |
| 2022-11 | 21 | 10 | +947 | +3,773 |
| 2022-12 | 21 | 11 | +2,217 | +5,990 |
| 2023-01 | 20 | 8 | +1,493 | +7,483 |
| 2023-02 | 19 | 7 | −2,489 | +4,994 |
| 2023-03 | 23 | 10 | −813 | +4,181 |
| 2023-04 | 19 | 17 | −1,438 | +2,743 |
| 2023-05 | 22 | 17 | −2,316 | +427 |
| 2023-06 | 21 | 20 | +2,198 | +2,625 |
| 2023-07 | 19 | 18 | −3,696 | −1,071 |
| 2023-08 | 23 | 21 | −3,418 | −4,489 |
| 2023-09 | 20 | 14 | −275 | −4,764 |
| 2023-10 | 22 | 6 | −259 | −5,023 |
| 2023-11 | 21 | 20 | −234 | −5,257 |
| 2023-12 | 20 | 17 | −3,811 | −9,068 |
| 2024-01 | 20 | 19 | +1,263 | −7,805 |
| 2024-02 | 20 | 20 | −1,696 | −9,501 |
| 2024-03 | 20 | 19 | +691 | −8,810 |
| 2024-04 | 22 | 16 | −342 | −9,152 |
| 2024-05 | 21 | 19 | +836 | −8,316 |
| 2024-06 | 19 | 18 | −1,368 | −9,685 |
