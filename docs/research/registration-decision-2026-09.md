# Registration decision package — 2026-09 (for the owner; nothing is registered)

**Status: written 2026-09-28 (stage 6), before any registration.** This file registers
nothing and changes nothing in `next-sweep-preregistration-draft.md` (the draft). The
registry `reports/research/registry/spx_0dte.jsonl` holds 98 records (49 `backfill`, 33
`evaluate`, 16 `port`) and **no `register` event**. No hypothesis rule has been run on any
real data.

It collects, for H-LV1, H-SN1, H-EV1 and H-TS1:
- the claim and mechanism, quoted from the draft;
- the implementation choices the definition hash freezes, each with its alternative and
  what changing it would do;
- every piece of development evidence seen so far, labelled by kind.

It ends with the choices only the owner can make.

**Kinds of evidence.** None of it is a test of a hypothesis.
- **2026 descriptive:** figures on the 2026-03-13 → 2026-09-24 Helios sessions. The frozen
  strategy was built on these sessions and every sweep has seen them. The draft excludes
  them from evidence.
- **Stage-5 mechanism check:** run `a2b54db81c49` on Cboe daily closes, development window
  2022-05-16 → 2024-06-28 only. It was run for H-TS1 only.
- **Shadow:** a paired, exploratory replay on the open cohort's recorded sessions (three so
  far).

## What the definition hash covers

`register` records `definition_hash` (computed by `Variant.definition_hash`), the full
definition, `git_sha`, `git_dirty` and the dataset hash.

- **The hash covers** the top-level rule class's source (`source_sha256`) and its
  parameters, including the nested E0 base's parameters.
- **The hash does not cover:**
  - the code of nested objects: E0's `BaselineEntry`, and HLV1's predicate
    `_skip_low_vix_calls`, which is looked up by name;
  - `features.py`, `event_calendar.py` and the calendar CSV;
  - `configs/config.yaml`: entry window, VIX buckets, cost caps, `min_debit`, trailer.

  These are frozen only by the register record's `git_sha`. Each run then records the config
  hash and, for feature rules, the calendar and aux hashes. The holdout unseal requires
  `git_dirty: false`, so the `git_sha` is exact.
- **Fitted values are not hashed** (H-TS1's threshold). They are fingerprinted in each
  run's `results.json`.

| Variant | Rule | Definition hash (checked 2026-09-28, stage 6) |
|---|---|---|
| `HLV1` | `FilteredEntry(E0, skip_low_vix_calls, 17.0)` | `6ed12752c07aeda2b857e3c7a04129f85e02bbdf5be40b2ab46e4feade2ed6d6` |
| `HSN1` | `SigmaPlacedEntry()` | `4589760a17440ebc01b86451b52f2dae18905eebb13270497476a468c2988147` |
| `HEV1` | `ReleaseSkipEntry(E0)` | `9180c56d9a7deb480778906bd3c199b164150e8389e6e089bdb1eb9ba23d660f` |
| `HTS1` | `PriorRatioFilter(E0, "vix1d_vix", 2022-01-03, 2024-06-28)` | `fab8bf3e0ab10805d8b6d8ee19617df7013c0fa776ed6fbf86314c6238ff69c6` |

> **[Fact fix, stage 6, marked]** Stage 4 documented HTS1 as `2ec8c008…`. The committed
> code gives `fab8bf3e…`: the same value at `82aed43` and at `0d440b8`, where
> `hypotheses.py` and `simulate.py` are unchanged. `2ec8c008…` was never the hash of
> committed code (most likely taken before a last edit to `PriorRatioFilter`). The other
> three match. `tests/test_research_hypotheses.py` now pins all four, so a code change that
> moves a hash fails loudly instead of silently changing what `register` would record.

Any change to an implementation choice below gives a new hash. It must happen before
registration, and the draft requires a change made after seeing the diagnostics to be
marked there.

---

## H-LV1 — skip low-VIX calls (`HLV1`)

**Claim and mechanism (draft):**
> Skip CALL-direction entries when the entry VIX is below 17.0.
> - As registered in the journal on 2026-09-25 for a future test.
> - Derived post hoc on 2026 data, which is outside both vendor periods.

The journal's two proposed mechanisms (2026-09-25, "Low-VIX diagnosis"):
- **Cost drag:** about $66 per fly, which is 28.8% of a low-VIX debit.
- **Smaller upward excursion after 10:00 at VIX < 17.**

**Choices the hash freezes:**

| Choice | Alternative | Effect of changing it |
|---|---|---|
| "Entry VIX" is the VIX E0's entry used: the tick at or before the entry snapshot, fresh within the live age limit | Prior-close VIX, or VIX at 10:00 | Only sessions with VIX near 17 would differ; a prior-close rule becomes a pre-open session filter |
| Strictly below 17.0: VIX = 17.00 keeps the call | At or below 17.0 | Negligible (VIX has two decimals) |
| Calls only; low-VIX puts are kept | Skip every low-VIX entry | That is `R1`, already tried post hoc (registry seq 21) |
| A skipped call is a no-trade session, with no switch to a put and no later entry | Take the put fly instead | A different hypothesis (a direction rule) |
| An entry without a VIX is kept | Skip it | Unreachable: E0 never enters without a fresh VIX |
| The threshold 17.0 is fixed, not re-fitted | Refit on development data | A fitted rule with a new hash; 17.0 came from 2026 data |

**Development evidence:**

- **2026 descriptive** (journal 2026-09-25; idea-sweep harness, stressed accounting,
  2026-03-13 → 2026-09-24):
  - E0 by entry VIX: below 17, −$2,578 over 56 trades; 17–24.5, +$8,061 over 55; above
    24.5, +$4,941 over 11.
  - The low-VIX trades HLV1 would skip, the calls, lost in both halves: −$1,617 over 8
    (H1) and −$3,633 over 27 (H2). The low-VIX puts it keeps won in both: +$1,282 over 5
    and +$1,390 over 16.
  - **This is confounded with time.** In an OLS of stressed dollars per trade, the VIX < 17
    coefficient is −$54 (t −0.29) and the H2 coefficient −$368 (t −2.00). 43 of the 56
    low-VIX trades are in H2.
  - Upward minus downward favourable excursion at VIX < 17: −0.34σ in H1 (n = 14) and
    −0.17σ in H2 (n = 45). Both 90% intervals include zero.
  - The call-only filter table (journal 2026-09-25, second entry; per-contract mark
    accounting, not stressed) shows the same sign: calls at VIX < 17, 54 trades, −$2,661.
  - The hypothesis was derived from these same trades.
- **Stage-5 mechanism check:** not applicable. It cannot be checked with close-only index
  data.
- **Shadow** (run `b10a02d93d13`, ledger `70ccb8e`, 2026-09-22 → 09-24):
  - HLV1 − E0 = +$225. It skipped one low-VIX call on 2026-09-22 (−$225) and matched E0
    on the other two sessions.
  - Three sessions carry no information.
  - The ledger has recorded no session since, so the shadow was not re-run in stage 6.
  - The registry holds this as an `evaluate` record (seq 96, stage `post`, scope
    `shadow:…`).
- **Standing in the power analysis** (review §2): H-LV1 sits inside the ±$2–3k fly-choice
  noise band measured on 2026. A forward test of it alone cannot resolve it.

---

## H-SN1 — σ-normalised selector (`HSN1`)

**Claim and mechanism (draft):**
> Replace the reward/risk-nearest-10 selector with a deterministic placement:
> - σ = 1.25 × the 10:00 ATM straddle (chain-implied remaining move);
> - center = spot ± 1.58σ in the gap direction, at the nearest listed strike;
> - width = 0.88σ, rounded to the nearest 5 points (minimum 5);
> - the same cost caps; no RR filter.
> - 1.58σ and 0.88σ are E0's mean placement measured on the 2026 sample (journal,
>   2026-09-25) and are fixed, not re-fitted.
> - Claim: at least E0's expectancy with lower selection noise.
> - The noise secondary compares the $0.10 tie-set draw band of E0 with H-SN1's P&L
>   spread across center multipliers 1.48/1.58/1.68 (its analogue of near ties).

**Choices the hash freezes:**

| Choice | Alternative | Effect of changing it |
|---|---|---|
| σ is taken once, from the straddle at the snapshot at or before 10:00, and held for the session | Recompute σ at each window time | σ shrinks as the day decays, so later entries would sit closer to spot |
| No straddle at 10:00 means no entry | Fall back to E0's fly, or the next straddle | 8 of the 133 Helios sessions have no 10:00 straddle (2026-03-13, 03-18, 04-27, 05-04, 05-18, 06-02, 08-25, 09-08); H-SN1 would not trade them. The vendor clock's rate is unknown |
| If nothing qualifies at 10:00, later window times reuse the 10:00 σ with the current spot | Only 10:00 | Fewer trades |
| Center at the nearest listed strike, the lower one on an exact tie; it must be out of the money, or that time is skipped | Round to 5 or 10 points; allow ATM | Small shifts in the center; allowing ATM moves toward D4 (ATM fly, −$19,272 on 2026) |
| Width is 0.88σ to the nearest 5 points, at least 5 | Snap to the configured widths | Odd widths (15, 35, 60 …) would disappear, and so would the cost-cap question below |
| Debit (mark) at least `min_debit` ($0.05) and at most the configured cap for the width; for an unconfigured width, $0.10 × width (the single rate all configured caps share) | Skip unconfigured widths; or no cap | Skipping gives fewer trades; no cap admits expensive flies (compare G1's ~4× risk) |
| The fly must be executable (both sides quoted, not crossed) at the snapshot | Mark only | Would enter unexecutable markets |
| A fresh VIX is required at the decision, as in E0, although placement does not use VIX | Drop it | Would trade sessions E0 skips (e.g. 2026-03-16), which breaks pairing |
| Gap direction, first qualifying time in the configured window (10:00–10:45 ET) | — | Same as E0 |
| No tie-set (the live selector does not choose the fly) | — | The noise secondary replaces it |

**Not built: the noise secondary.** Gate 5 needs H-SN1 run at center 1.48σ and 1.68σ.
Those are two more parameterisations of `SigmaPlacedEntry`, and neither is in the catalog.
Before registering H-SN1 the owner should decide:
- whether they are registered with it as its secondary (not counted in k), which is how
  the draft reads;
- how "P&L spread" is measured against E0's draw band. The draft gives no statistic; the
  5–95% draw range is the obvious one for E0, but a three-point spread is not the same kind
  of quantity.

**Development evidence:**

- **2026 descriptive:**
  - The constants are E0's own mean placement on 2026: center 1.58 / 1.56 / 1.64σ and width
    0.88 / 0.89 / 0.92σ by VIX regime, and a 1.579σ center in both halves (journal
    2026-09-25).
  - E0's fly-choice noise on 2026: a 5–95% draw range of about ±$2–3k at $0.10 (journal,
    near-tied flies). E0's tie-set average is $10,982 against $10,424 for the selected fly
    (sweep profile): the selector's specific pick is not an edge.
  - The straddle-anchored rules C1/C2 and T1–T6 made 1–4 trades each. That was because of
    their RR ≥ 8 filter, which H-SN1 does not have, so they are not a precedent for its
    trade count.
- **Stage-5 mechanism check:** not applicable.
- **Shadow:** none. HSN1 has never been run on real data (synthetic unit tests only).

---

## H-EV1 — skip pre-entry releases (`HEV1`)

**Claim and mechanism (draft):**
> Skip sessions with a CPI, NFP or PCE release scheduled before 10:00 ET.
> - Mechanism: the 10:00 chain still prices post-release event premium that decays through
>   the session, so realized movement after 10:00 falls short of implied and the tent is
>   reached less often.
> - Uses the event calendar's leakage rule (published before the session, not withdrawn
>   before it, never unscheduled).

**Choices the hash freezes** (the calendar itself, v1 `3185297d…`, is frozen by `git_sha`
and recorded in each run):

| Choice | Alternative | Effect of changing it |
|---|---|---|
| Types: CPI, NFP, PCE only | Add PPI, GDP, retail sales, jobless claims … | Not in calendar v1; it would need a new calendar version and more skipped sessions |
| Release strictly before 10:00 ET | At or before 10:00, or before the window's end (10:45) | **Calendar v1 has four PCE releases at 10:00, all in the holdout:** 2024-11-27, 2025-04-30, 2025-12-05 and 2026-01-22. As frozen, H-EV1 trades them; with "at or before 10:00" it would skip them. Every other CPI/NFP/PCE row is at 08:30 |
| Visibility: `published_on` before the session, not withdrawn before it; `held` never used; a release withdrawn *on* the session still counts | Use `held` (what happened) | Leaks: cancellations during the 2025 lapse were known only later |
| The whole session is skipped | Enter after the release has been digested | A different rule (compare the later-entry T1–T6) |
| Unscheduled rows never count | — | Only the 2025-08-22 FOMC notation vote, not a CPI/NFP/PCE row |

Calendar v1's one known gap (January 2026 NFP's original 2026-02-06 date has no row) should
not affect any session under the leakage rule: the reschedule to 2026-02-11 was published
2026-02-05, before the original date.

**Development evidence:**

- **2026 descriptive** (diagnostics run `90673e0c138b`, sweep profile, 2026-03-13 →
  2026-09-24). The cell "08:30 release (CPI/NFP/PCE), before entry" uses exactly H-EV1's
  types and 10:00 cutoff:
  - 17 sessions (9 H1, 8 H2): E0 stressed −$97 (H1 +$1,652, H2 −$1,749), tie-set $0.10
    +$507, 2 settled landings.
  - **The move after 10:00 on these sessions was larger, not smaller:** RMS 1.192
    chain-implied σ, against 0.956 on sessions with no scheduled event. That is the
    opposite of the mechanism's "realized falls short of implied". By type: CPI 0.777
    (6 sessions), NFP 1.685 (4), PCE 1.136 (7).
  - In event cells a single cash settlement decides the sign.
- **Stage-5 mechanism check:** not applicable. Close-to-close data includes the 08:30
  release itself.
- **Shadow:** none. No cohort session so far has had a pre-entry release.

---

## H-TS1 — rich one-day implied (`HTS1`)

**Claim and mechanism (draft):**
> Skip sessions whose prior-session VIX1D/VIX is at or above the development period's
> upper tercile of that ratio.
> - The threshold is fitted once on development sessions only, and frozen in the
>   registered definition.
> - Mechanism: a rich one-day implied relative to 30-day means a larger one-day variance
>   premium, so the fly's tail is overpriced relative to the likely move.
> - Sessions without a prior VIX1D close (before 2022-05-16) are never skipped.

**Its mechanism check came out "not supported".** High-ratio sessions did not move less
relative to VIX1D. They moved slightly more, in both halves (details below).

**Choices the hash freezes:**

| Choice | Alternative | Effect of changing it |
|---|---|---|
| The ratio is VIX1D/VIX from Cboe closes on the previous SPX session only (Cboe prints on NYSE holidays are skipped) | A 10:00 intraday ratio; VIX9D/VIX | Intraday VIX1D exists only from 2026-09-28 (gateway), so a historical intraday fit is impossible without vendor VIX1D. VIX9D/VIX was not monotone on 2026 |
| Threshold `numpy.quantile(…, 2/3)` (linear interpolation) over the development sessions the profile qualifies (`vendor_1m`: ≥ 50 grid points, VIX and prior VIX) that have a prior VIX1D | Another quantile; fit over all Cboe sessions instead of qualifying vendor sessions | The exact value is set by the vendor's session list; about 0.918 on the Cboe calendar (below) |
| Fit window 2022-01-03 → 2024-06-28 (effectively 2022-05-16 onward) | Fit on 2026 Helios sessions; an expanding (learning) quantile | 2026 gives 0.828 and flags far more sessions; an expanding quantile is a new rule class |
| Skip at or above the threshold | Strictly above | Negligible |
| No prior VIX1D means never skipped | Skip | Only affects development sessions before 2022-05-16; every holdout session has VIX1D |
| The fitted value is not in the hash | — | Re-fitting the same procedure keeps the identity; the value is fingerprinted per run |

**Development evidence:**

- **Threshold.** The development-window 2/3 bound would be about **0.918** (mechanism run,
  533 Cboe sessions 2022-05-16 → 2024-06-28), against the 2026 sample's **0.828**.
  - Applied to the 132 evaluable 2026 sessions, 0.918 flags 23 (17 in H1, 6 in H2); the
    2026 tercile flags 44.
  - This is a count of the feature only, no P&L: the rule was not run.
  - So the 2026 cells below describe a larger, different set of sessions than the
    registered rule would skip.
- **Stage-5 mechanism check** (run `a2b54db81c49`; decision rule fixed before the run):
  - **Not supported.**
  - Top-tercile mean `|ln move| / (VIX1D/√252)` was 0.741 against 0.715 for the rest:
    +0.026, 90% interval [−0.058, +0.101].
  - H1 +0.025 [−0.070, +0.132]; H2 +0.013 [−0.108, +0.142].
  - The one-day implied was rich on average (mean r 0.724 against ≈0.80 for a move priced
    exactly), but not richer when VIX1D/VIX was high.
  - Close-to-close is a proxy (it includes the overnight move and the morning before
    entry), not a test of H-TS1.
- **2026 descriptive** (diagnostics `90673e0c138b`; terciles fitted on 2026):
  - High tercile (≥ 0.828), 44 sessions (27 H1, 17 H2): E0 stressed −$3,361 (H1 +$942,
    H2 −$4,303), tie-set $0.10 −$2,253, RMS after 10:00 0.925σ. Low tercile: +$6,838,
    1.064σ.
  - That is the direction H-TS1 predicts, but it is confounded with H2 and the VIX level.
  - The draft's own note says it is not evidence.
- **Shadow:** none (HTS1 was not in the shadow set).

---

## Optional H-EV2 — skip FOMC statement days (not implemented)

**The draft:**
> Optional, for the owner to keep or drop: **H-EV2**, skip FOMC statement days. The
> statement is at 14:00, after entry. The direction of the effect is not well motivated, so
> it is listed only in case the diagnostics or other evidence justify it before
> registration.

- **No catalog entry exists.** `ReleaseSkipEntry` with `("FOMC",)` would skip nothing,
  because its cutoff is "before 10:00" and the statement is at 14:00. Keeping H-EV2 needs a
  new definition (and a new hash).
- **2026 descriptive:** FOMC cell, 5 sessions (3 H1, 2 H2): stressed −$961, tie-set $0.10
  −$1,003, 0 settled, RMS 1.121σ. A single settlement would flip it.
- **Mechanism check and shadow:** none.

---

## Decisions only the owner can make

1. **Which hypotheses to register, if any, and in which form.** Any subset, or none.
   - Changing any choice in the tables above gives a new hash, and must happen before
     `register`.
   - The draft requires marking any change made after seeing the diagnostics.
   - Specific open points:
     - H-SN1's noise secondary: register 1.48σ/1.68σ with it, and fix its statistic.
     - H-EV1's treatment of the four 10:00 PCE releases.
   - Relevant facts:
     - H-TS1's mechanism check was **not supported**.
     - H-EV1's release sessions moved *more* after 10:00 on 2026, not less.
     - H-LV1's 2026 signal is confounded with H2.
     - H-SN1 has no development evidence beyond the calibration of its constants.
2. **k and its Bonferroni level.** Family α = 0.10, one-sided; each hypothesis passes gate 1
   only if its bootstrap lower bound at 1 − 0.10/k is above zero:

   | k | Per-test α | Lower-bound level |
   |---:|---:|---:|
   | 1 | 0.100 | 90% |
   | 2 | 0.050 | 95% |
   | 3 | 0.033 | 96.7% |
   | 4 (as drafted) | 0.025 | 97.5% |
   | 5 (with H-EV2) | 0.020 | 98% |

   - A larger k makes every registered hypothesis harder to pass on the same holdout. The
     review's power estimate (§2: about 400 trades to separate $85 per trade from zero at
     t ≈ 2) was for a single test.
   - Whether H-SN1's secondary runs count toward k is part of this decision. The draft
     implies they do not.
3. **Whether to keep optional H-EV2.** It needs a new definition. Its only evidence is five
   2026 sessions, and the draft calls its direction not well motivated.
4. **If ThetaData is not bought: the fallback, a forward (Helios-only) holdout.** Not
   pre-registered; built only if chosen. What it would mean:
   - **Evidence accrues only from sessions after registration.** E0 trades on about 92% of
     sessions (122 of 132), so the ~400 trades the review asks for take about 1.7 years.
   - **H-TS1 cannot be fitted as defined.** Its fit reads development-window sessions from
     the dataset, and `spx_0dte` has none before 2026-03-13 (the fit raises "no
     observations").
     - It would need a new definition: for example, a threshold fixed at registration from
       Cboe daily closes 2022-05-16 → 2024-06-28 (≈0.918), or from the 2026 Helios
       sessions (0.828).
     - Either is a new hash.
   - **No sealed-window machinery exists for a forward holdout.** `holdout.py` seals
     2024-07-01 → 2026-03-12 only. A forward pre-registration must fix its first session
     (after the register record) and its endpoint in writing.
   - **Registration would be on `spx_0dte`, not a vendor dataset.** That dataset name already
     carries 49 backfilled definitions and a `post` shadow evaluation of HLV1.
   - **Forward sessions are the open cohort's market days.** A paired shadow on them does not
     touch the cohort, but it is not independent evidence from it.

**Not a choice: the order for the vendor path.** If ThetaData is bought, registration comes
after the development pull and before the holdout pull, from a clean committed tree, on
`spx_0dte_thetadata`. The unseal accepts only such records. Before buying, ThetaData must
confirm in writing:
- the licence question;
- the history depth of Options Value and Indices Standard;
- the EOD open/close definition.

See `history-vendor-readiness.md` for the purchase checklist.
