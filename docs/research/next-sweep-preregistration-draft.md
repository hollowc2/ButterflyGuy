# Next SPX sweep on vendor history — pre-registration DRAFT (not registered)

**Status: DRAFT, 2026-09-27.** Nothing here is registered, and nothing is run. The owner
decides which hypotheses, if any, to `register`, and may edit them first.

- **Timing.** This draft was written before the stage-3 descriptive diagnostics were run,
  and before any vendor data exists locally.
  - The diagnostics were run afterwards (run `90673e0c138b`), and no hypothesis was
    changed.
  - On the 2026 development sample, E0 lost in the high VIX1D/VIX tercile (−$3,361 over
    44 sessions), which is the direction H-TS1 predicts. That is not evidence for H-TS1:
    those sessions are seen development data, and the tercile is confounded with H2.
- **Revisions.** Any change made after the owner has seen the diagnostics must be marked
  as such in this file before registration.
- **Registration.** It happens with
  `python -m butterfly_guy.research register --dataset <vendor dataset> ...` from a clean,
  committed tree, **before any holdout-period vendor data is downloaded**.

> **[Fact update, 2026-09-28, marked; no hypothesis, split or gate changed]**
> - **No vendor data has been bought yet.** The owner will likely buy ThetaData, from 2022
>   forward. Until then no `spx_0dte_<vendor>` dataset exists, and this sweep cannot run
>   as drafted. *(Corrected 2026-09-28, marked: an earlier wording of this bullet said the
>   owner had decided not to buy vendor history. That was wrong.)*
> - **The rules exist in the catalog** as `HSN1` (`4589760a…`), `HEV1` (`9180c56d…`) and
>   `HTS1` (`fab8bf3e…`), alongside the existing `HLV1` (`6ed12752…`). None is registered.
>   *(Corrected 2026-09-28 (stage 6), marked: this bullet gave HTS1 as `2ec8c008…`, which
>   was never the hash of the committed code; `fab8bf3e…` is what `register` would record.)*
> - **Details this draft leaves open** were fixed in the implementation and are listed in
>   `research-core.md` ("Hypothesis rules"). The owner should review them before
>   registering: the hash freezes them.
> - **Registration** now records the git state and the dataset hash. The holdout opens
>   only through a registry-verified unseal (`holdout.py`).

> **[Fact update, 2026-09-28 (stage 5), marked; no hypothesis, split or gate changed]**
> - **Development session count.** ThetaData's public docs say SPXW was quoted only on
>   Mondays, Wednesdays and Fridays before 2022-05-16, so the development period has about
>   590 SPXW 0-DTE sessions, not "about 625" as written below. The vendor's expiration list
>   will fix the exact number.
> - **Likely vendor:** ThetaData, from 2022 forward; not purchased. The purchase checklist
>   and the enforced pull order are in `history-vendor-readiness.md`.

Style follows `docs/research/spx-idea-sweep-2026-09-25/REGISTRY.md`. Design rationale:
`docs/reviews/2026-09-27-research-pipeline-review.md` §2 (power) and §3 (paired, stressed
evaluation; fly-choice noise).

## Data and split (fixed now, before any vendor data is seen)

- **Dataset.** SPXW 0-DTE quotes from one vendor that passed the validation plan in
  `docs/research/history-vendor-readiness.md`, written as a separate research dataset
  (for example `spx_0dte_<vendor>`) under the `vendor_1m` decision profile.
- **Development period: 2022-01-03 → 2024-06-28** (about 625 sessions).
  - All exploration, debugging, threshold fitting (H-TS1) and harness checks happen here.
  - It spans 2022's bear market and 2023's low volatility.
- **Holdout period: 2024-07-01 → 2026-03-12** (about 430 sessions, about the 400 trades
  the power analysis asks for).
  - Downloaded only after registration.
  - Its file hashes go into the registry record before the first evaluation.
  - It is evaluated once per registered hypothesis, with no re-runs after edits.
  - It includes the 2025 tariff shock.
- **Excluded from evidence: 2026-03-13 onward** (Helios-recorded sessions). The frozen
  strategy was built on these and every earlier sweep saw them. They are used only for
  vendor fidelity checks.
- **Halves within the holdout:** H1 = 2024-07-01 → 2025-04-30, H2 = 2025-05-01 →
  2026-03-12.

## Baseline

E0 exactly as in the research core: gap direction (official open vs prior close),
VIX-anchored live selection in the configured window, runtime peak trailer, cash
settlement on the official close. Replayed on the same vendor sessions. Every hypothesis
is a paired comparison against E0 on identical sessions.

## Hypotheses

Every rule leaves everything else in E0 unchanged. "Skip" means no trade that session
(P&L 0).

**H-LV1 (low-VIX calls).** Skip CALL-direction entries when the entry VIX is below 17.0.
- As registered in the journal on 2026-09-25 for a future test.
- Derived post hoc on 2026 data, which is outside both vendor periods.

**H-SN1 (σ-normalised selector, review §3.3).** Replace the reward/risk-nearest-10
selector with a deterministic placement:
- σ = 1.25 × the 10:00 ATM straddle (chain-implied remaining move);
- center = spot ± 1.58σ in the gap direction, at the nearest listed strike;
- width = 0.88σ, rounded to the nearest 5 points (minimum 5);
- the same cost caps; no RR filter.
- 1.58σ and 0.88σ are E0's mean placement measured on the 2026 sample (journal,
  2026-09-25) and are fixed, not re-fitted.
- Claim: at least E0's expectancy with lower selection noise.
- The noise secondary compares the $0.10 tie-set draw band of E0 with H-SN1's P&L
  spread across center multipliers 1.48/1.58/1.68 (its analogue of near ties).

**H-EV1 (pre-entry releases).** Skip sessions with a CPI, NFP or PCE release scheduled
before 10:00 ET.
- Mechanism: the 10:00 chain still prices post-release event premium that decays through
  the session, so realized movement after 10:00 falls short of implied and the tent is
  reached less often.
- Uses the event calendar's leakage rule (published before the session, not withdrawn
  before it, never unscheduled).

**H-TS1 (rich one-day implied).** Skip sessions whose prior-session VIX1D/VIX is at or
above the development period's upper tercile of that ratio.
- The threshold is fitted once on development sessions only, and frozen in the
  registered definition.
- Mechanism: a rich one-day implied relative to 30-day means a larger one-day variance
  premium, so the fly's tail is overpriced relative to the likely move.
- Sessions without a prior VIX1D close (before 2022-05-16) are never skipped.

Optional, for the owner to keep or drop: **H-EV2**, skip FOMC statement days. The
statement is at 14:00, after entry. The direction of the effect is not well motivated, so
it is listed only in case the diagnostics or other evidence justify it before
registration.

## Primary metric and gate

- **Metric:** stressed-marketable P&L per holdout session (zeros on no-trade days),
  paired against E0.
  - Stressed-marketable: ask/bid crossing, +$0.05 per contract adverse, $0.65 per
    contract commission, free cash settlement against the official close.
  - Sessions any arm cannot replay without imputing data are dropped from every arm, as
    the core does now.
- **Test:** the moving-block bootstrap of the total paired difference.
  - 10-session blocks, 10,000 reps, one index draw applied to both arms, seed 1.
- **Multiple testing:** k = the number of hypotheses actually registered (4 as drafted; 5
  with H-EV2). Bonferroni at family α = 0.10, one-sided.
- **A hypothesis passes only if all of these hold:**
  1. the bootstrap lower bound at 1 − 0.10/k is above 0 (97.5% for k = 4);
  2. the paired difference is positive in both holdout halves;
  3. the paired difference is still positive with the three largest-P&L sessions of
     either arm removed;
  4. the delayed-exit stressed model's point estimate is also positive;
  5. for H-SN1 only, the noise secondary is lower than E0's.
- **Reporting:** everything is reported whatever the result, including the development
  figures (labelled in-sample), the cumulative variant count on the vendor dataset, and
  the 49 definitions already tried on `spx_0dte` for context.
- **Expected false positives:** with k = 4 and a Bonferroni family α of 0.10, at most
  about a 10% chance that any one of the four passes by luck alone.

## Out of scope for this sweep

- Any change to the frozen strategy or the open cohort.
- Survivors are not deployed. A survivor becomes a candidate for a new prospective
  cohort or a paired shadow on the open cohort's sessions, which are exploratory.
- Tuning after the holdout is opened. Any re-run with a changed definition is a new
  post-hoc variant.
