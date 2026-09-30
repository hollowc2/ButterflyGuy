# Registration decision package: ThetaData development window (2026-09-29)

**For the owner. Nothing is registered.** Every figure below comes from the development window
(2022-01-03 → 2024-06-28) and is **in-sample**. None of it is evidence of an edge. The sealed
holdout (2024-07-01 → 2026-03-12) was not downloaded, read or evaluated. Sessions from 2026-03-13
onward were not used.

**Revised the same day, after the owner's decisions on the first version:**
- **D1: do not register yet.**
- **D3: floor stressed exits at $0.** This is Revision 1 of the pre-registration draft, marked
  there. It was made after seeing these results.
- **D5: settle held trades on early closes** instead of dropping the session (code `6891317`).
  This is Revision 3.
- **D4: calibrate gate 1's level on development data at registration** (code `b18ca94`,
  `c59e6bd`). This is Revision 4.
- **D2: add gate 6.** A rule's own stressed P&L on the holdout must be above zero (code
  `362a728`). This is Revision 5.
- **D6: no Indices month.** The holdout is 358 sessions, and the intraday VIX cross-check stays
  undone.
- **D9: the `holdout` command is built** (commit `6f02a86`, §6.5).
- D3, D5, D4 and D2 were all decided after seeing these results.

Every figure below uses the floored metric (`--floor-stressed-exits`) and the early-close fix,
unless it is marked "unfloored". The first version's unfloored figures are kept in §3 and §9
for the record.

This supersedes `registration-decision-2026-09.md` for the vendor path. That file still holds
each hypothesis's frozen implementation choices and the 2026 descriptive evidence.

## Conclusions

1. **E0 loses money on the development window.** Stressed net is −$9,922 over 362 trades
   (−$27 a trade, −$17 a session), and the whole fly-choice band is negative (5–95%: −$10.4k to
   −$9.6k). Midpoint accounting shows +$18.2k. The loss is concentrated in 2023 (−$15.3k) and in
   gap-down PUT entries (−$17.1k).
   - Flooring changed six E0 exits, a gain of +$3.4k (unfloored it was −$13,085).
   - The early-close fix added one held trade, 2023-07-03, which settled at −$238.
2. **Only H-TS1 improves on E0 by more than fly-choice noise.** It gains +$7,639 (+$9,960
   unfloored): positive in both halves, +$7,554 with delayed exits, and better than E0 in 100%
   of fly-choice draws.
   - H-LV1 is worse than E0 (−$1,455): the 2026 pattern it came from reverses here.
   - H-SN1 is much worse (−$12,736), and it swings by $22.5k across its three centers.
   - H-EV1 is flat (+$151).
   - H-EV2 gains +$1,366 from 4 skipped trades but fails gate 2 (its H2 difference is 0).
3. **Even H-TS1 is weak evidence.**
   - In-sample it fails gate 1 at its calibrated level: its 97.5% lower bound is −$2,916. It
     passes only at the drafted 90% (+$1,078), which over-passes rules like it (§6.2).
   - Its threshold is fitted on these sessions.
   - Its stage-5 mechanism check was "not supported".
   - Because E0 loses, trading less helps by itself: skipping 70 random E0 trades gains $1.9k
     on average, and 12% of such skips gain as much as H-TS1 did.
   - H-TS1 itself still lost money (−$2,283).
4. **Status: not registered (D1).** If and when you register, the recommendation stays: H-TS1
   alone, k = 1.
   - Its gate 1 is then the 97.5% bound, calibrated so that gate 1 alone passes a no-effect
     H-TS1 about 10% of the time.
   - A pass now means H-TS1 beat E0 **and** made money on the holdout (gate 6, Revision 5).
   - Power with all gates is about 18% if the development effect is real, and 8% if it is
     half as large.
   - A rule with no mechanism, while E0 loses, passes about 5% of the time.
   - At k ≥ 3 its gate 1 cannot be calibrated at all, and the holdout command refuses.
5. **Still open before any registration:**
   - D9: the holdout evaluation command is **built** (`holdout`, commit `6f02a86`, §6.5).
     Review the details it fixes (gate 3's reading, the re-run rule) before registering.
   - D7 (ThetaData licence) remains open. D6 is decided: no Indices month.
   - **Keep Options Value until the holdout is pulled** (owner, 2026-09-29; §7). The pull
     goes through the live ThetaData API, and nothing imports the raw sealed files.
   - D5 (early closes), D4 (gate-1 calibration) and D2 (gate 6) are fixed (§6.4, §6.2, §6.3).

## 1. Data and integrity

| Check | Result |
|---|---|
| `verify` | OK: dataset `93bbe58eb799c516f2a65bd5b20b7fdbc686e65681378d56c9279c8955a05d30`, 1,429 files; registry chains intact |
| `coverage`, development window | 585 sessions: all have a real SPX level, a 10:00 VIX, an official open and close; median 129 strikes × 390 minutes; missing and crossed rates 0 |
| E0 replay (`vendor_1m`) | 585 of 585 sessions (since the early-close fix, D5) |

**Early closes are replayed (D5, fixed 2026-09-29).**
- **Before.** The replay required data up to 15:00 ET before holding a trade to the official
  close, a rule inherited from `SimulationEngine`. On a 13:00 early close, a held trade became
  `incomplete_data` and the session dropped from every arm. That dropped 2023-07-03 (E0) and
  2022-11-25 (H-SN1).
- **Now.** The data must reach one hour before the session's scheduled close: 15:00 on a
  regular day, as before, and 12:00 on an early close. The scheduled close is the vendor
  dataset's `session_close_et`. A held trade on 2023-07-03 or 2022-11-25 now settles on that
  day's official 13:00 close.
- **The holdout.** Its five early closes with data (2024-07-03, 2024-11-29, 2024-12-24,
  2025-07-03, 2025-11-28) can no longer drop.

The 625 trading days of the window: 31 had no 0-DTE expiration, 7 are frozen minute-file days,
2 were excluded by the owner, leaving 585. E0 replays all of them.

**Data change made with the owner's approval (2026-09-29):** `export-vol --cboe` added Cboe's
daily VIX-family closes to the vendor dataset for H-TS1 (`aux/vol_index_daily.parquet`, 18,617
rows, sha256 `7fa50f1c…`; aux_hash `eab136c9eb93b0b410217f5c15b0ed62e9e159a377cba8bd9fc77cfa21b19278`).
The dataset hash did not change. The development-window rows are identical to `spx_0dte`'s
copy. The file also holds holdout-dated closes. They are read only for a session being
replayed, and holdout sessions cannot be replayed without an unseal.

## 2. Baseline E0 (descriptive; do not tune on it)

Run `7d7f91ad9ba5` (git `6891317`): 585 sessions, halves split at 2023-04-26 (292 / 293
sessions, fixed by session count before any result was seen). Stressed accounting with exits floored at $0,
unless noted.

| | Value |
|---|---:|
| Trades / sessions | 362 / 585 (no entry on 223) |
| Stressed net | **−$9,922** (first version, unfloored, 584 sessions: −$13,085) |
| per trade / per session | −$27 / −$17 |
| Midpoint / delayed-exit stressed | +$18,167 / −$8,518 |
| $0.10 tie-set average, draw 5–95% | −$9,985; −$10,387 … −$9,582 |
| Win rate; median trade; trade SD | 13.5%; −$220; $666 |
| Settled (cash) | 79 trades, 43 winners, +$54,679 |
| Exits floored at $0 | 6 (stressed), 6 (delayed) |
| Top three trades, share of gross wins | 15.1% |

On 1-minute vendor data near-ties are rare (1.04 flies per tie set). With the floor, the
fly-choice band is only $0.8k wide over 585 sessions. On the validation window, unfloored, it
was $4.6k over 126 sessions.

**By year:**

| Year | Sessions | Trades | Stressed | /trade | Tie-set 5–95% | Delayed | Settled |
|---|---:|---:|---:|---:|---|---:|---:|
| 2022 | 213 | 75 | +5,989 | +80 | +6.0k … +6.0k | +6,224 | 15 |
| 2023 | 250 | 176 | **−15,295** | −87 | −15.3k … −15.0k | −14,685 | 37 |
| 2024 (to 06-28) | 122 | 111 | −616 | −6 | −1.1k … −0.6k | −57 | 27 |
| H1 (≤ 2023-04-26) | 292 | 115 | +3,172 | +28 | +3.2k … +3.5k | +3,587 | 24 |
| H2 | 293 | 247 | −13,094 | −53 | −13.6k … −13.0k | −12,105 | 55 |

2022's gain is mostly July (+$5.6k), October (+$2.9k on one trade) and December (+$2.2k).

**By VIX at 10:00** (buckets as in the config, lower bound inclusive):

| VIX | Sessions | Trades | Stressed | /trade | Tie-set 5–95% |
|---|---:|---:|---:|---:|---|
| < 17 | 242 | 226 | −10,900 | −48 | −11.4k … −10.8k |
| 17 – 24.5 | 223 | 130 | −336 | −3 | −0.3k … −0.1k |
| 24.5 – 32 | 104 | 6 | +1,313 | +219 | +1.3k |
| ≥ 32 | 16 | 0 | 0 | — | — |

E0 almost never enters when VIX is 24.5 or higher (6 trades in 120 sessions). Most no-trade
sessions are 2022 high-VIX days (110) and 2023 days at VIX 17–24.5 (61).

**By gap direction** (official open vs prior official close):

| Gap | Sessions | Trades | Stressed | /trade | Tie-set 5–95% | Midpoint |
|---|---:|---:|---:|---:|---|---:|
| Up (CALL) | 305 | 203 | +7,149 | +35 | +7.1k … +7.4k | +21,849 |
| Down (PUT) | 280 | 159 | **−17,072** | −107 | −17.6k … −17.0k | −3,682 |

By entry VIX and direction (unfloored), the low-VIX losses are the puts (−$14,216 over 96
trades), not the calls (+$1,452 over 135). That is the reverse of the 2026 sample that H-LV1
came from. Floored, the low-VIX calls made +$1,455.

**Exit reasons:**

| Exit | Trades | Stressed | Delayed | Midpoint |
|---|---:|---:|---:|---:|
| Cash-settled | 79 | +54,679 | +54,679 | +57,966 |
| Drawdown, morning | 169 | −36,664 | −36,334 | −24,029 |
| Drawdown, late morning | 17 | −5,336 | −5,298 | −4,153 |
| Drawdown, afternoon | 97 | −22,601 | −21,565 | −11,617 |

The delayed-exit model still does a little better than the stressed one (−$8.5k against
−$9.9k): a fill one minute after an afternoon trigger is often better. The monthly equity
curve is in the appendix.

## 3. The hypotheses on the development window (in-sample)

Each rule is paired with E0 on identical sessions. The draft's bootstrap was used: 10-session
blocks, 10,000 reps, seed 1. Gate 3 removes the union of each arm's three largest sessions. The
skip filters come from run `7d7f91ad9ba5` and H-SN1 and its secondaries from run
`9971c5db1313` (both at git `6891317`, 585 sessions each, none dropped); the skip filters' Δ is
identical in both.

| | H-TS1 | H-EV2 | H-EV1 | H-LV1 | H-SN1 |
|---|---:|---:|---:|---:|---:|
| Trades (E0: 362) | 292 | 358 | 317 | 227 | 560 |
| Own stressed net | −2,283 | −8,557 | −9,771 | −11,377 | −22,658 |
| **Δ vs E0 (stressed, floored)** | **+7,639** | +1,366 | +151 | −1,455 | −12,736 |
| Δ, H1 / H2 | +3,517 / +4,122 | +1,366 / 0 | +948 / −797 | +273 / −1,728 | −17,399 / +4,663 |
| Δ, top three of either arm removed | +10,999 | +1,366 | +151 | −1,455 | −19,459 |
| Δ, delayed exits | +7,554 | +1,326 | +116 | −1,787 | −13,290 |
| Bootstrap P(Δ > 0) | 0.927 | 0.984 | 0.503 | 0.403 | 0.158 |
| Lower bound 90% (drafted level, k = 1) | **+1,078** | +498 | −5,696 | −10,253 | −29,136 |
| Lower bound 95% (drafted level, k = 2) | −1,074 | +283 | −7,451 | −12,838 | −33,925 |
| Lower bound 97.5% (drafted k = 4; H-TS1's calibrated k = 1) | −2,916 | +135 | −8,869 | −15,129 | −37,385 |
| Calibrated gate-1 level at k = 1 (358 sessions; Revision 4) | 2.5% | 10% | 5% | 6% | — |
| Draft gates 1–4 on dev, gate 1 at the calibrated level | fail g1 (97.5% bound −2,916) | fail g2 (H2 Δ = 0) | fail g1, g2 | fail all | fail all |
| Gate 6 on dev: own stressed net > 0 (Revision 5) | fail (−2,283) | fail (−8,557) | fail (−9,771) | fail (−11,377) | fail (−22,658) |
| Fly choice: Δ across paired draws, 5–95% | +7.4k … +7.6k | +1.3k … +1.4k | +116 … +151 | −1,465 … −1,455 | n/a |
| Fly choice: share of draws beating E0 | 100% | 100% | 100% | 0% | n/a |
| Exits floored (stressed) | 3 | 4 | 6 | 5 | 14 |
| *Unfloored Δ, before the early-close fix (first version)* | *+9,960* | *+3,831* | *+151* | *−1,452* | *−9,814* |

**What trading less is worth when E0 loses.** A skip filter gains whenever the trades it drops
are worse than the ones it keeps. When E0 loses on average, dropping any trade gains
something. To compare, E0 trades were drawn at random (20,000 draws of the same number):

| | H-TS1 | H-EV2 | H-EV1 | H-LV1 |
|---|---:|---:|---:|---:|
| E0 trades skipped | 70 | 4 | 45 | 135 |
| Mean stressed P&L, skipped / kept | −109 / −8 | −341 / −24 | −3 / −31 | +11 / −50 |
| Expected gain from a random skip of that size | +1,919 | +110 | +1,233 | +3,700 |
| Share of random skips gaining at least as much | 12% | 1.8% | 62% | 79% |

**Is each result robust to fly-choice noise?**
- **H-TS1:** yes. Its Δ is positive in every fly-choice draw and about 9.5 times E0's own
  5–95% band width ($0.8k).
- **H-LV1:** robustly negative.
- **H-EV1:** robustly near zero.
- **H-EV2:** stable in sign across draws, but it rests on four trades.
- **H-SN1:** the live selector does not choose its flies, so it has no tie-set. Its analogue,
  the spread across centers 1.48σ, 1.58σ and 1.68σ (−$30,514, −$22,658, −$45,127), is $22.5k,
  about 28 times E0's band. Gate 5 fails.

**Per hypothesis:**
- **H-TS1** (skip when the prior-session VIX1D/VIX ≥ 0.9181935615930604).
  - The fit used 528 development sessions with a prior VIX1D. That is the only fitted value,
    and it used the feature alone, never P&L. The floor does not change it.
  - Unfloored, the gain was concentrated in 2023 (+$8.6k of +$10.0k).
  - Its 70 skipped trades include 13 held to settlement (7 of them winners), 2023-07-03
    among them; the rest are trailer-exit losses it avoided.
  - Three of its skipped sessions had exits floored, including 2022-12-14.
  - It never skips before 2022-05-16, where no VIX1D exists.
  - The stage-5 check on Cboe closes found high-ratio sessions moved slightly *more*
    relative to VIX1D, not less. So the P&L result has no supporting mechanism evidence.
- **H-LV1** (skip CALL entries at VIX < 17).
  - It skips 135 trades, 37% of E0's, which earned +$1,455.
  - The 2026 signal it came from was already confounded with H2. On 2022–24 its direction
    reverses.
- **H-SN1** (σ-placed fly).
  - It trades on 560 of 585 sessions, against E0's 362, because it has no reward/risk
    filter and enters at high VIX, where E0 rarely does.
  - Its expectancy is −$40 a trade against E0's −$27, and its placement noise is far larger.
    Both of the draft's claims fail in-sample.
- **H-EV1** (skip a CPI, NFP or PCE release before 10:00).
  - 45 skipped trades averaged −$3, against −$31 for the trades kept. It does worse than a
    random skip of the same size would be expected to.
- **H-EV2** (skip FOMC statement days; built 2026-09-29, `EventDaySkipEntry`).
  - E0 traded on only 4 of the 19 development FOMC sessions: 2022-07-27, 2022-12-14,
    2023-02-01 and 2023-03-22. The 20th FOMC day, 2024-01-31, is a frozen VIX day.
  - All four are in H1, so gate 2 fails.
  - About 11 FOMC days fall in the usable holdout, so expect 2–3 E0 trades.

## 4. Holdout size and power

**Size.** These counts come from the exchange calendar and the known gaps only. No holdout data
was read.

| | Without Indices (**decided, D6**) | With an Indices month (not bought) |
|---|---:|---:|
| Trading days 2024-07-01 → 2026-03-12 | 426 | 426 |
| Gap 2025-12-10 → 2026-03-12 (no SPX/VIX minutes) | −63 | 0 |
| Frozen minute-file days (2024-07-18, 07-25, 08-02, 09-06, 11-20) | −5 | −5 |
| **Usable sessions** | **358** | **421** |
| Draft halves: H1 (→ 2025-04-30) / H2 | 204 / 154 | 204 / 217 |
| Early closes dropped by the replay | none (D5 fixed) | none (D5 fixed) |
| E0 trades at the development trade rate (61.9%) | ≈ 222 | ≈ 261 |
| H-TS1 skipped trades at the development rate (19% of E0's) | ≈ 43 | ≈ 50 |

The trade rate depends on VIX: E0 barely trades at 24.5 or above. The holdout's rate will differ.

**Power, from the development-window paired vectors** (floored metric, early closes settled).
- Simulated holdouts resample development sessions in 10-session blocks.
- Each simulated holdout then gets the draft's percentile bootstrap (2,000 reps) plus gates
  2–4.
- H-TS1's gate 1 is at its calibrated level for each k (Revision 4, §6.2). The other rules'
  rows use the drafted 0.10/k and omit gate 6, because they are not recommended.
- There are 1,000 simulations per cell, so each figure is good to about ±1.5 points.
- All of this assumes 2022–24 is representative of 2024–26.

H-TS1 alone (k = 1) at its calibrated gate-1 level (97.5% bound for 358 sessions, 96% for
421), with and without gate 6 (Revision 5):

| Scenario | 358: gates 1–4 | 358: **all gates** | 421: gates 1–4 | 421: **all gates** |
|---|---:|---:|---:|---:|
| development effect is real (+$13.06/session) | 36% | **18%** | 42% | **22%** |
| half the effect (half the skip pattern replaced by an unrelated one) | 27% | **8%** | 33% | **10%** |
| no mechanism, E0 losing as on development | 16% | **4.7%** | 16% | **4.3%** |
| no mechanism, E0 breaking even | 13% | 13% | 12% | 12% |

About these figures:
- They come from one simulation run. A separate run gave 33% (358) and 40% (421) for gates
  1–4 at the development effect, so read them as ±2–3 points.
- **Gate 1's calibration target.** Under the paired null, gate 1 alone passes a no-effect
  H-TS1 10.6% of the time (target 10%), or 9.3% at 421 sessions.
- **The no-mechanism rows** run above that, partly because of how those scenarios are resampled
  (the same block-boundary effect as in §6.2).
- **At k = 2** (99.75% bound) gates 1–4 give 19% at the development effect. At k ≥ 3 H-TS1's
  gate 1 cannot be calibrated (§6.2), so the holdout command refuses it.

The other rules at the drafted levels, full gate set, 358 sessions:

| Hypothesis | Scenario | k = 1 | k = 2 | k = 3 | k = 4 | k = 5 |
|---|---|---:|---:|---:|---:|---:|
| H-EV1 | development effect (≈ none) | 14% | 9.7% | 7.2% | 6.3% | 5.7% |
| H-LV1 | development effect (negative) | 8.9% | 5.6% | 4.1% | 3.5% | 3.0% |
| H-EV2 | development effect (4 trades; unreliable) | 39% | 36% | 23% | 21% | 20% |
| H-EV2 | half the development effect | 17% | 9.1% | 5.8% | 4.7% | 3.0% |
| H-SN1 | development effect (negative) | 1.2% | 0.4% | 0.3% | 0.1% | 0.1% |

*(D6: no Indices month will be bought, so every 421-session figure in this section is for the
record only; 358 is the only live option.)*

**For the record: with the calibration, an Indices month would have bought power.** H-TS1's
gates 1–4 go from 36% to 42% at the development effect in the table above (33% to 40% in the
second run).
- At the drafted level, 63 more sessions changed little: 51% → 52%.
- The skewness that forces the tighter level shrinks with more sessions, so the calibrated
  level loosens from the 97.5% bound to the 96% bound.

H-EV2's development-effect row overstates it: its four trades are all in development H1, but
resampling spreads them across both simulated halves.

**Minimum detectable total effect** (80% power, gate 1 alone, normal approximation from the
development dispersion):

| | k = 1 | k = 4 | k = 5 | Development effect scaled to 358 sessions |
|---|---:|---:|---:|---:|
| H-TS1 | $8.2k ($23/session) | $10.9k | $11.2k | $4.7k |
| H-TS1 at its calibrated k = 1 level (97.5% bound; 96% with 421 sessions) | $10.9k ($30/session) | — | — | $4.7k ($5.5k at 421) |
| H-EV1 | $6.9k | $9.1k | $9.4k | $0.1k |
| H-LV1 | $10.8k | $14.2k | $14.7k | −$0.9k |
| H-EV2 | $1.2k | $1.6k | $1.7k | $0.8k |
| H-SN1 | $21.2k | $28.0k | $29.0k | −$7.8k |

At its calibrated level, H-TS1's in-sample effect is under half its minimum detectable effect,
and in-sample winners usually shrink out of sample.

## 5. VIX-smoothing sensitivity

The owner's VIX file misses brief intraday highs and lows (median 1.6%). The strategy reads VIX
as a level at the entry minute, about 10:00. How far that level is off cannot be measured
without an independent intraday source.

| Where VIX decides something | E0 entries within ±0.25 | Within ±0.50 |
|---|---:|---:|
| Width bucket at 17.0 | 16 | 28 |
| Width bucket at 24.5 | 8 | 11 |
| Width bucket at 32.0 | 0 | 0 |
| **Any bucket edge** | **24 of 362 (6.6%)**: net +$5,012, gross absolute P&L $13,804 | 39 (10.8%): net +$3,427 |
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

### 6.2 Gate 1 passed skip filters too often under the null: decided, now calibrated (D4, draft Revision 4)

The draft expects a per-test false-pass rate of α/k. With a skip filter the paired difference is
zero on most sessions, and a few large settled winners dominate it. In that case the percentile
block bootstrap's lower bound is too optimistic. Simulated with the exact bootstrap at 358
sessions, floored, with no true effect:

| Gate 1 alone, no effect | k = 1 (nominal 10%) | k = 4 (nominal 2.5%) |
|---|---:|---:|
| H-TS1 | 19% | 11% |
| H-EV1 | 14% | 6.2% |
| H-LV1 | 13% | 5.1% |
| H-SN1 (dense difference) | 8.7% | 2.0% |

- Gates 2–4 trim this only a little: H-TS1's all-gates false-pass rate is 18% at k = 1
  and 11% at k = 4.
- If all five were registered and none had a real effect, the chance that at least one passes
  would be up to about 22% (union bound at k = 5), not the draft's "at most about 10%".
- If E0 also loses in the holdout as it did here, skip filters with no real mechanism would
  pass even more often (the random-skip rows in §4). The union bound then reaches about 33%.

**What was done (Revision 4, commits `b18ca94` and `c59e6bd`).** Gate 1 keeps the draft's
statistic and null, but at a level calibrated per rule.
- **At registration.** `register` replays E0 and each rule on the development window under the
  protocol's settings. It shifts the paired difference to mean zero, resamples it in 10-session
  blocks to holdouts of the planned size (`--holdout-sessions`), and runs the percentile test at
  every level of a fixed grid: 2,000 simulated holdouts, 10,000 reps each, seed 1.
- **What it records.** For each k = 1..5, the loosest level whose simulated false-pass rate is
  at most 0.10/k, never looser than 0.10/k, together with the whole curve.
- **At the holdout.** The command uses the recorded level for its k. It refuses a registration
  with no calibration, or one whose target could not be reached for that k.

Computed in-process on this dataset, with nothing registered:

| Rule | Passes with no effect at the drafted 10% | Calibrated level: k = 1 | k = 2 | k ≥ 3 |
|---|---:|---:|---:|---|
| H-TS1, 358 sessions | 17.7% | **2.5%** | 0.25% | cannot be calibrated |
| H-TS1, 421 sessions | 16.3% | **4.0%** | 0.5% | cannot be calibrated |
| H-EV1, 358 | 14.4% | 5.0% | 1.5% | 0.25% at k = 3; not at 4–5 |
| H-LV1, 358 | 13.2% | 6.0% | 2.5% | 1.5%, 1.0%, 0.75% |
| H-EV2, 358 | 5.7% | 10% (drafted) | 5% | drafted |

- At H-TS1's calibrated k = 1 level, gate 1 alone passes a no-effect H-TS1 10.6% of the time
  (target 10%; §4). Gates 2–4 and 6 then trim it further.
- The 17.7% here and the 19% in the first table are two simulations of the same quantity at
  the drafted level; read both as about 18%.
- The calibration assumes the holdout's paired difference is shaped like the development
  window's.
- The negative-baseline effect of §6.3 is handled separately, by gate 6 (D2).

### 6.3 A paired pass against a losing baseline: decided, gate 6 added (D2, draft Revision 5)

The primary metric is the paired difference from E0. With E0 negative, any rule that trades
less gains something without a mechanism, and the drafted gates never checked the rule's own
P&L. A pass therefore meant only "loses less than E0". H-TS1's own in-sample stressed net is
−$2,283.

**What was done (Revision 5, commit `362a728`).** Gate 6: a registered rule also needs its own
stressed P&L over the evaluated holdout sessions above zero. It is a point estimate, like gate 4.

**Alternatives looked at before the decision** (in-sample simulation, H-TS1 alone, k = 1,
calibrated gate 1, 358 sessions):
- **"Beats a random skip of the same size"** (the skipped trades lost more than E0's average)
  changed no verdict. To clear the calibrated gate 1, the skipped trades already have to be
  much worse than average.
- **With gate 1 calibrated, trading less by itself adds only about 2.5 points of false
  passes:** 16% with E0 losing against 13% with E0 breaking even.
- **So the choice was about meaning, not mechanism.** Gate 6 halves power (36% → 18% at the
  development effect) and makes a pass mean "beat E0 and made money".

### 6.4 Early closes: decided, now fixed (D5)

See §1. A trade held on a 13:00 early close now settles on that day's official close, so no
early-close session drops from the comparison.
- **Regular sessions keep `SimulationEngine`'s 15:00 rule.** A test pins the equality.
- **Helios datasets record no scheduled close.** Their replays and the frozen-replay parity
  are unchanged: 118 trades, 0 mismatches.
- **Effect on development.** E0 gains 2023-07-03 (−$238, a held put), and H-SN1 gains
  2022-11-25 (−$163).
- `PreCloseExit`'s minutes-to-close still counts to 16:00. It is disabled in the config, so it
  affects nothing today.

### 6.5 The holdout evaluation command (D9, built 2026-09-29)

`holdout --unseal-holdout SEQ` (`protocol.py`, commit `6f02a86`) is the only command that
replays holdout sessions; `run` still cannot.
- **What it evaluates.** Exactly the variants registered up to `SEQ`, each paired with E0.
- **Fixed, not parameters:** every choice the draft fixes (Revision 1 included). That is the
  floor, `vendor_1m`, the bootstrap, the halves, k, gates 1–4 and, since Revision 5,
  gate 6.
- **Recording.** Every evaluation is recorded, and there is no `--no-registry`.
- **Refusals, all before any holdout session is replayed:**
  - a registered definition that no longer matches the catalog;
  - H-SN1 registered, because gate 5 has no statistic;
  - a dirty tree, or `src/`/`configs/` changed since the registration commit;
  - no holdout sessions pulled;
  - a fitted rule whose re-fit differs from its registered value;
  - a second evaluation that is not an exact reproduction of the first.
- **Fitted values are now recorded at registration.** `register` fits a fitted rule on its
  window and records the value. On this dataset HTS1 fits to 0.9181935615930604 (n = 528),
  checked in-process with nothing registered.

**Details the draft left open, now fixed in code. Review them before registering, because
the `git_sha` freezes them:**
- Gate 3's "either arm" is the union of each arm's top three sessions, removed from both. It
  is the reading used in §3 and §4.
- A second evaluation is allowed only as an exact reproduction (same unseal, dataset, arms
  and code), and it is recorded as another look.

The command was tested on a synthetic vendor dataset only. Nothing real was registered,
unsealed or pulled.

## 7. Recommendation and frozen definitions

**Status: not registered (owner's decision D1, 2026-09-29).**

**If and when you register: H-TS1 alone, k = 1.**
- Gate 1 is then the lower bound at H-TS1's calibrated level (Revision 4), recorded by
  `register`: the 97.5% bound at 358 sessions (D6: no Indices month).
- Gates 2–4 as drafted, and gate 6 (own stressed P&L above zero, Revision 5), on the floored
  metric.
- Holdout halves as drafted: H1 2024-07-01 → 2025-04-30, H2 2025-05-01 → 2026-03-12.

**Drop:**
- H-LV1: sign reversed in-sample.
- H-SN1: worse, and fails its noise secondary.
- H-EV1: no effect, and its 2026 mechanism was contradicted.
- H-EV2: 4 trades, all in one half; about 2–3 expected on the holdout; no power.

Registering any of them adds nothing likely to pass and lowers H-TS1's power (§4).

**H-TS1 as it would be registered** (from run `7d7f91ad9ba5` at git `6891317`; the rule itself
is unchanged by the floor and the early-close fix):

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
| Gate-1 level (Revision 4) | calibrated at registration for 358 holdout sessions: k = 1 gives 2.5%; recorded as `gate1` in the register record |
| Replay | early-close sessions settle held trades (D5, `6891317`) |

**What the hash does not cover.** E0's code, `features.py` and the config are frozen by the
register record's `git_sha`: the `holdout` command refuses if `src/` or `configs/` differ from
that commit. The threshold is recorded by `register` itself (`fitted`). The holdout run re-fits
it on the development window and refuses unless it reproduces 0.9181935615930604 exactly. The
floor is a constant of the `holdout` command. Any further change to the replay code must be
committed before `register`.

**The other rules' hashes, for the record:** HLV1 `6ed12752…`, HSN1 `4589760a…`, HSN1_c148
`844e32da…`, HSN1_c168 `f0967c75…`, HEV1 `9180c56d…`, HEV2 `b0c670c0…` (full values in
`research-core.md`).

**The multiple-testing k.** The draft sets k to the number actually registered. The
recommendation gives k = 1. Each extra hypothesis raises k by one and costs H-TS1 power:
under calibration its gate-1 level falls to 0.25% at k = 2, and it cannot be calibrated at
k ≥ 3 (§6.2).
The variant count on this dataset (8, §9) is reported alongside; it is not k.

**How to register and evaluate, if and when you decide to.** Register from a clean,
committed tree, before any holdout pull. Then pull the holdout with the same unseal, and
evaluate once:

```bash
uv run python -m butterfly_guy.research --dataset spx_0dte_thetadata register --variants HTS1 \
  --holdout-sessions 358 --note "H-TS1 alone, k=1; halves 2025-04-30; no Indices month (358 sessions)"
# (the holdout pull: export-history ... --unseal-holdout <SEQ>, as research-core documents)
uv run python -m butterfly_guy.research --dataset spx_0dte_thetadata holdout --unseal-holdout <SEQ>
```

This writes the first record of `reports/research/registry/spx_0dte_thetadata.jsonl`. The
development registry is a separate file and is never read by the unseal.

**The pull needs a live subscription.** `export-history` builds the holdout dataset only
through the Theta Terminal. The raw sealed archive (`data/thetadata_sealed/`, main checkout)
has no import path. **Decided 2026-09-29: keep Options Value until registration and the pull
are done.** An import from the raw files was the alternative. It would have to be built,
validated on the development window against dataset `93bbe58e…`, and allowed by D7.

## 8. Owner decisions

| # | Decision | Status and options | Before |
|---|---|---|---|
| D1 | Register now, or not yet? | **Decided 2026-09-29: not yet.** When you do: H-TS1 alone, k = 1 is recommended. Only what is registered before the holdout pull can ever be tested on it | — |
| D3 | Stressed exits below zero | **Decided 2026-09-29: floor at $0** (draft Revision 1; `--floor-stressed-exits`; §6.1) | done |
| D8 | Development registry | **Confirmed 2026-09-29:** development runs are recorded in `registry/development/` | done |
| D2 | Meaning of a pass against a losing E0 | **Decided 2026-09-29: gate 6, own stressed P&L above zero** (draft Revision 5; `362a728`; §6.3) | done |
| D4 | Gate 1 on skip filters (§6.2) | **Decided 2026-09-29: calibrate the level on development data at registration** (draft Revision 4; `b18ca94`, `c59e6bd`) | done |
| D5 | Early closes (§6.4) | **Decided 2026-09-29: settle held trades on the early close** (`6891317`) | done |
| D9 | Holdout evaluation command (§6.5) | **Built 2026-09-29** (`holdout`, `6f02a86`). Review its two fixed readings (gate 3 union; exact-reproduction re-run rule) | registration |
| D6 | ThetaData Indices month ($50) | **Decided 2026-09-29: not bought.** The holdout is 358 sessions (H1 204 / H2 154). The 63 gap sessions are skipped under the no-derived-data rule, and the intraday VIX cross-check stays undone (§5; H-TS1 is not affected). Register with `--holdout-sessions 358` (the default) | done |
| D10 | Holdout pull path | **Decided 2026-09-29: keep the Options Value subscription until the holdout is pulled** (live API; no import from the raw sealed files is built; §7) | cancelling |
| D11 | Minute-file provenance | **Partly answered 2026-09-29:** `spx_1min.csv`/`vix_1min.csv` are **not** the owner's Schwab capture (that has run about six months). The owner downloaded them from a third-party source, not yet named. Vendor and licence still open | registration |
| D7 | ThetaData licence | Open. Terms §2.1(i) and §12.2: may the local cache outlive a cancelled subscription? The holdout result's reproducibility and any later audit depend on the answer | holdout pull |

## 9. Variant count and provenance

- **On `spx_0dte_thetadata`: 8 distinct definitions, all tried post hoc on development data:**
  E0, HLV1, HSN1, HSN1_c148, HSN1_c168, HEV1, HEV2, HTS1.
  - They are recorded in `reports/research/registry/development/spx_0dte_thetadata.jsonl`:
    37 `evaluate` records over seven runs, chain intact.
  - Record 0 is an E0 run (`9bc6b6fc2187`) with a placeholder split (2023-04-01). It was
    superseded by the 2023-04-26 split before any result was read.
  - The floor and the early-close fix change accounting and replay, not definitions, so the
    count stays 8.
  - A run id hashes the data, profile, config and definitions, not the git commit. So the
    early-close re-runs kept the floored runs' ids and replaced their local artifacts. The
    registry holds both versions' results hashes, each with its commit.
  - The validation-window replays (runs `17304d08065e`, `b41290589484`) used E0 only and wrote
    no registry record.
- **For context:** 49 definitions were tried on the Helios dataset `spx_0dte`, 2026 sessions.

| Run | Accounting | Git | Variants | `results.json` | `trades.jsonl` |
|---|---|---|---|---|---|
| **`7d7f91ad9ba5`** | floored, early closes settled (primary) | `6891317` | E0, HLV1, HEV1, HEV2, HTS1 | `346a9f8244610a74167a93bdec6258f2f46c04b58b1ad3158ab523d51921b593` | `b95aeae62570d51a63188bc3e490d548f00c2a5fc2aa347fc6face430d7054cb` |
| **`9971c5db1313`** | floored, early closes settled (primary) | `6891317` | E0, HLV1, HSN1, HSN1_c148, HSN1_c168, HEV1, HEV2 | `4a64d80928a6f63a5f900a5456459d4d362d43268df22ca6e4085a93be2ba8a3` | `9c2d58cab201bb0e1264cb7cdc73329a3dc4954ca8dc340ce1adc1cc6f6daa68` |
| `7d7f91ad9ba5` | floored, before the early-close fix | `7b1f229` | E0, HLV1, HEV1, HEV2, HTS1 | `f361f0f16d61fb62fdc67a4517f114b071dcd18d6c6a1e86b7a826c9b4233339` | `1b58160a0c5b11ec5600587b30f3ab1fa3440e4c802351937409c7d1ca614bfc` |
| `9971c5db1313` | floored, before the early-close fix | `7b1f229` | E0, HLV1, HSN1, HSN1_c148, HSN1_c168, HEV1, HEV2 | `415a3b2d441457175289576b23dddba016efd525b3eea7423b1ce6e4bc4e0605` | `cc5d9429a2376080528cc77e29d05e7a31cf71436c1689ebe2555b706a726566` |
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

**Ad hoc analysis.** The random-skip comparison, the gate-1 calibration curves and the power
simulation are now reproducible with `tools/research_studies/dev_studies.py`. The calibration and
random-skip figures match exactly. The power tool's null rows come out lower than §4's, because
the original scenarios were built differently (see its README). The breakdowns and the original
power runs were scratch scripts that read the same runs in-process with the same
accounting. The in-process replay matched every CLI run's totals exactly.
- The power simulation draws 10-session blocks from the development pairs to 358 or 421
  sessions.
- It applies the draft's percentile bootstrap (2,000 reps) and gates 2–4, with 1,000
  simulations per cell.
- For "no effect" and "half effect" it shifts the paired difference by a constant per session.

## Appendix: E0 monthly equity curve (stressed, floored, early closes settled, development window)

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
| 2023-07 | 20 | 19 | −3,933 | −1,308 |
| 2023-08 | 23 | 21 | −3,418 | −4,726 |
| 2023-09 | 20 | 14 | −275 | −5,001 |
| 2023-10 | 22 | 6 | −259 | −5,260 |
| 2023-11 | 21 | 20 | −234 | −5,494 |
| 2023-12 | 20 | 17 | −3,811 | −9,305 |
| 2024-01 | 20 | 19 | +1,263 | −8,042 |
| 2024-02 | 20 | 20 | −1,696 | −9,738 |
| 2024-03 | 20 | 19 | +691 | −9,047 |
| 2024-04 | 22 | 16 | −342 | −9,389 |
| 2024-05 | 21 | 19 | +836 | −8,553 |
| 2024-06 | 19 | 18 | −1,368 | −9,922 |
