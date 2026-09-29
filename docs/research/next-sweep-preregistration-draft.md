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
  *[Revision 2, 2026-09-29, marked: raw holdout files were downloaded before registration
  into a sealed folder; see the revision block below]*

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

> **[Fact update, 2026-09-29, marked; no hypothesis, split, metric or gate changed]**
> - **Development-window results exist** (in-sample; ThetaData `spx_0dte_thetadata` @
>   `93bbe58e`, `vendor_1m`, 2022-01-03 → 2024-06-28). They are in
>   `registration-decision-2026-09-29.md`, which also lists the owner's open decisions.
>   Anything in this draft that is changed from here on is made after seeing those results
>   and must be marked as a revision.
> - **Usable development sessions:** 585; E0 replays 584 (2023-07-03, an early close, is
>   `incomplete_data`). *[Revision 3, 2026-09-29, marked: E0 now replays all 585; see the
>   revision block below]*
> - **H-TS1's fitted threshold:** 0.9181935615930604 (n = 528 sessions with a prior VIX1D).
> - **Built for the development runs:** optional H-EV2 as `HEV2` (`b0c670c0…`, FOMC statement
>   days at any time) and H-SN1's noise secondary as `HSN1_c148` / `HSN1_c168`.
> - **Holdout size from the calendar:** 358 usable sessions (H1 204 / H2 154) without an
>   Indices month, 421 (204 / 217) with one.

> **[REVISION 1, 2026-09-29, marked: the owner's decision, made AFTER seeing the
> development-window results]**
> - **Primary metric, accounting.** In the stressed-marketable model, and in its
>   delayed-exit form used by gate 4, an intraday exit is booked at $0 when its net
>   proceeds per fly are below $0. Net proceeds are the bid/ask-crossing credit, minus
>   commission, minus the $0.05 stress.
> - **Why.** A butterfly is never worth less than zero. Legging out across blown-out quotes
>   made the model pay to close.
>   - The worst case was on the 2022-12-14 FOMC statement minute: $22.53 a fly to close a
>     20-point fly.
>   - Six of E0's 361 development exits were priced below zero
>     (`registration-decision-2026-09-29.md` §6.1).
> - **Implementation.** `--floor-stressed-exits` (`Costs.stressed_exit_floor = 0.0`). Every
>   vendor-sweep run must use it, the holdout evaluation included. Each run records
>   `accounting.stressed_exit_floor: 0.0` and says so in its report.
> - **Unchanged.** Midpoint, marketable, entries and cash settlement. The flag is off by
>   default, so the Helios parity and idea-sweep reproductions still match the frozen
>   replay exactly. Hypotheses, split, halves, bootstrap, the k rule and gates 1–5 are
>   unchanged.
> - **Owner's decision D1, same day:** nothing is registered yet.

> **[Fact update, 2026-09-29, marked; no hypothesis, split, metric or gate changed]**
> - **The holdout evaluation is built:** `holdout --unseal-holdout SEQ` (`protocol.py`,
>   commit `6f02a86`). It is the only command that replays holdout sessions.
>   - It evaluates exactly the variants registered up to `SEQ` against E0.
>   - Every choice fixed above is a constant, not a parameter.
>   - Every evaluation is recorded.
> - **Details this draft leaves open, fixed in that code** (the owner should review them
>   before registering, since the register record's `git_sha` freezes them):
>   - **Gate 3's "either arm"** is the union of each arm's three largest-P&L sessions,
>     removed from both.
>   - **Gate 5 still has no statistic**, so a registered H-SN1 is refused, not evaluated.
>   - **"No re-runs after edits"** means a second evaluation is refused unless it exactly
>     reproduces the first: same unseal, dataset hash, arms, and `src/`/`configs/`. An exact
>     reproduction is allowed and recorded as another look.
>   - **The code must be the registration commit's:** `src/` and `configs/` are unchanged
>     since it, and the tree is clean.
>   - **A fitted rule's registered value is checked.** `register` now fits it on its window
>     and records the value. The holdout run re-fits and refuses on any difference. HTS1 on
>     `spx_0dte_thetadata` @ `93bbe58e` fits to 0.9181935615930604 (n = 528).

> **[REVISION 2, 2026-09-29, marked: the owner's decision; no hypothesis, split, metric or
> gate changed]**
> - **What changed.** Raw ThetaData option history (SPXW 0DTE and 1DTE, NDXP 0DTE and
>   XSP 0DTE, 2020-01-01 onward) was downloaded before registration by
>   `tools/thetadata_download.py` on `main`. Trade dates inside the holdout went to a
>   separate, gitignored `data/thetadata_sealed/` in the main checkout.
> - **Why.** To secure the data in case the subscription ends before registration.
> - **The seal.** Nothing in either checkout reads that folder, and the tool prints row
>   counts only, never prices. Nobody opens, charts or backtests those files until
>   registration.
> - **Unchanged.** The research pipeline still builds its holdout dataset only through the
>   guarded pull after a registry-verified unseal, and it still records that dataset's file
>   hashes before the first evaluation.

> **[REVISION 3, 2026-09-29, marked: the owner's decision D5, made AFTER seeing the
> development-window results; no hypothesis, split, metric or gate changed]**
> - **What changed.** A trade still held when a 13:00 early-close session ends now settles on
>   that session's official close, like any held trade. Before, the replay required data up
>   to 15:00 ET for every session. Such a trade was `incomplete_data`, and the rule "sessions
>   any arm cannot replay … are dropped from every arm" removed the session.
> - **Why.** Nothing is missing: the session closes at 13:00 and SPXW settles on that close,
>   so settling it imputes nothing.
> - **Rule.** The data must reach one hour before the session's scheduled close: 15:00 on a
>   regular day, unchanged (`SimulationEngine`'s rule), and 12:00 on an early close. The
>   scheduled close is the vendor dataset's `session_close_et`, from calendar v1's early-close
>   rows. Commit `6891317`.
> - **Effect.**
>   - On development, 2023-07-03 (E0, a held put, −$238) and 2022-11-25 (H-SN1) are now
>     evaluated, and all 585 sessions replay (`registration-decision-2026-09-29.md` §6.4).
>   - On the holdout, its five early closes with data can no longer drop.
> - **Unchanged.** Helios datasets record no scheduled close, so their replays and the
>   frozen-replay parity are unchanged. So are the hypotheses, split, halves, metric,
>   bootstrap, the k rule and the gates.

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
  - Downloaded only after registration. *[Revision 2, 2026-09-29, marked: raw vendor
    files were downloaded before registration into a sealed folder; see the revision block
    above]*
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
  - *[Revision 1, 2026-09-29, marked: see the revision block above]* An intraday exit's
    net proceeds are floored at $0 (`--floor-stressed-exits`).
  - Sessions any arm cannot replay without imputing data are dropped from every arm, as
    the core does now. *[Revision 3, 2026-09-29, marked: a trade held on an early close is
    not missing data; it settles on that day's official close]*
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
