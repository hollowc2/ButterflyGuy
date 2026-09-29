# ThetaData data-quality plan and validation amendment (2026-09-28)

**Status: APPROVED by the owner on 2026-09-28** (D1), before any Q1–Q6 metric was computed.
Phase 1 started the same day. No development (2022-01-03 → 2024-06-28) or holdout data is
pulled before Phase 2 passes.

## Principles (the owner's, 2026-09-28)

1. **Data quality comes first.** ThetaData Options Value (OPRA NBBO, 1-minute) is the paid,
   primary source. If our own recorded data (Helios, Schwab snapshots) turns out to be the
   lower-quality source, that is a finding to discuss, not a reason to reject the vendor.
2. **No derived data.** Nothing is computed to stand in for data we do not have: no SPX from
   put-call parity, no computed VIX, no filled or forward-filled bars. A session without
   real SPX and VIX for its minutes is **skipped**, with the reason recorded.
3. **Every value in a vendor dataset is a real observation** from a named source: ThetaData
   for option quotes; the owner's minute files, or our recorded Helios ticks, for SPX and VIX;
   Cboe for official closes.

## What happened (on record, unchanged)

- Validation run `76abde9f881a` (ThetaData `542cdba0` vs Helios `c7fff54a`, 133 sessions
  2026-03-13 → 2026-09-25): **FAIL** on steps 1–3, PASS on step 4. It stays on file.
- **Calibration** run `42ad112d11f4`: our own Helios data, resampled onto the same 1-minute grid,
  was validated against itself at its native timing. It also **fails steps 1 and 2**, with 78%
  quote agreement against ThetaData's 83%. At 1-minute resolution those two steps measure
  the timing gap between the sources, not data quality: Helios snapshots land at random seconds,
  and a 1-minute grid point can be up to 59 s away from them.
- **Same clock** (run `cc8c4fc374df`, and `8c6a9f46fe43` with the real SPX index): compared
  minute for minute with our resampled data, ThetaData's bid/ask spreads are the same
  (median equal in every price bucket) and its mids are within 0–3 cents on average.
  Presence agreement is 99.9%.
- **The strategy's P&L is not a data-quality measure.** On our own 1-minute data, choosing
  among butterflies within $0.10 of each other moves the stressed total anywhere from $4.7k
  to $9.8k over these 133 sessions. ThetaData with the real SPX index gives $4.9k. SPX from
  parity alone cut our own data's result from $9.6k to $6.0k. Replaying the strategy says
  more about the strategy's sensitivity than about either data source. It is reported below
  as a finding, not used as a gate.

**Why changing the gates now is acceptable, and its limits.** The original criteria said
they must not be relaxed after the results. This amendment does change them after the
results, so it is recorded as such:
- the 2026-03-13 → 2026-09-25 window was already seen data, and says nothing about any rule;
- the sealed holdout (2024-07-01 → 2026-03-12) is untouched and stays sealed;
- the new data-quality thresholds below are fixed here, **before** any of those metrics has
  been computed on either source.

## The plan

### Phase 1: code (no data pulled)

1. **Remove the parity fallback.** `history.build_session` skips a session without a real SPX
   level (`no_spx_index`) instead of deriving one, and also a session without a real VIX
   at 10:00 ET (`no_vix`). This reverts today's "band from the close" change. `parity_spot` is
   removed with its tests.
2. **Validation-window SPX and VIX come from our recorded Helios ticks**: real Schwab
   observations, labelled as such in the manifest. This applies only to dates after the
   owner's minute files end, and never inside the holdout. The development and holdout
   pulls use the owner's minute files.
3. **Frozen days stay excluded**: a day with 30 or more identical consecutive minute bars
   (SPX: 2022-02-25, 03-04, 05-06, 2024-05-30, 09-06, 11-20; VIX: 2022-10-25, 10-28,
   2024-01-31, 07-18, 07-25, 08-02) is not served, so the session is skipped. The list is
   pinned in the manifest.
4. **New `quality.py` and a `vendor-quality` command**: the checks in Phase 2, run the same
   way on any dataset (ThetaData or Helios), with a canonical JSON report and run hash, like
   `validate-vendor`.
5. **A code gate on the development pull.** `export-history` refuses the development window
   unless the dataset's manifest history shows a passing `vendor-quality` run on the
   validation window, just as the holdout guard refuses the holdout without a registration.
6. Tests for each of the above; the full suite and ruff must pass.

### Phase 2: re-pull the validation window, then check quality

Re-pull 2026-03-13 → 2026-09-25 into `spx_0dte_thetadata` as a fresh dataset: about 20 min,
no parity. Then run `vendor-quality` on **both** ThetaData and Helios. Checks and thresholds,
fixed now:

| # | Check | ThetaData must |
|---|---|---|
| Q1 | **Coverage.** Share of grid cells (09:31 → close, integer strikes within ±200 of SPX) with a quote | ≥ 99% per session, on every session |
| Q2 | **Crossed quotes** (bid > ask) among quoted cells | ≤ 0.1% overall |
| Q3 | **Executable arbitrage** (quotes you could trade against for a riskless profit): a call or put vertical buyable for a credit, `ask(K) < bid(K')` for the richer strike; or a 5-point butterfly buyable for a credit, `ask(K−5) − 2·bid(K) + ask(K+5) < 0` | ≤ 0.1% of checks overall |
| Q4 | **Stale quotes.** A contract within ±50 of SPX whose bid and ask stay unchanged for 30 minutes or more while SPX moves 10 points or more | ≤ 0.1% of contract-sessions |
| Q5 | **Timestamps line up.** For every session, the 1-minute changes of the nearest-to-SPX call's mid correlate best with SPX's 1-minute changes at lag 0 (lags −3..+3 min) | lag 0 on ≥ 95% of sessions, and no session with a best lag beyond ±1 min |
| Q6 | **Official closes** equal Cboe's SPX close (as step 4 today) | 0 mismatches |

Q1–Q4 are also run on Helios and reported side by side, with no pass/fail for Helios. If
Helios is worse on them, that goes to the owner as a separate discussion. It matters because
the live strategy and its current parameters were built on Schwab data.

**Matched-instant comparison (report only).** For Helios snapshots taken 0–5 s after a minute
mark, compare with ThetaData at that minute. Report the share within $0.05, and for each
disagreement which side, if either, breaks a Q2–Q3 rule at that moment. This shows where the
two sources differ and which one is at fault, without a threshold. The two sources never
observe exactly the same instant.

**P&L replay (report only).** `validate-vendor` steps 2–3, plus the 1-minute calibration, are
re-run and reported as a strategy-sensitivity finding. They no longer gate anything.

### Phase 3: development pull (only if Q1–Q6 pass)

1. Pull 2022-01-03 → 2024-06-28 (about 590 sessions, about 2 h).
2. Run `vendor-quality` on it with the same thresholds, plus Q5 on the DST-change weeks
   (2022-03-14, 2022-11-07, 2023-03-13, 2023-11-06, 2024-03-11). That confirms ThetaData's
   timestamps are New York time and the owner's files are Chicago time, which the files'
   first bar at 08:31 CT already indicates.
3. **Minute-file cross-check**, with no derivation: the files' daily high and low against an
   independent daily source (Cboe's VIX OHLC; a free SPX daily OHLC), and their closes
   against Cboe (already done for 2022 → 2025: calendar exact, VIX close median |Δ| 0.01).
4. Coverage report (`coverage`), labelled "in-sample development data".

### Phase 4: registration, then holdout (unchanged)

The owner's registration from a clean, committed tree; then the holdout pull with
`--unseal-holdout`. The holdout guard enforces the order.

## Phase 1 implementation notes (2026-09-28)

Built in `history.py`, `thetadata.py`, `quality.py` and `cli.py`, with tests (1024 passing).
Details the plan left open, fixed in code before any Q metric was computed:

- **An index level is a real print at most 120 s old** at the grid minute
  (`INDEX_MAX_AGE_S`). A session needs a VIX print between 09:55 and 10:00 ET.
- **Q1 "a quote"** is a finite bid and ask whose recorded age, where the dataset has one,
  is at most 60 s.
- **Q3** skips crossed cells, which Q2 already counts, and allows 1e-9 of float slack.
- **Q5 needs SPX prints exactly on the minute.** The owner's bar-end files have them. In the
  validation window SPX comes from Schwab ticks at random seconds, and with 1-minute option
  data lags 0 and +1 would then tie on average. So Q5 reports `n/a` there and gates
  nothing; it becomes a hard gate on the development data (Phase 3), including the
  DST-change weeks. This correction to the approved plan was **confirmed by the owner on
  2026-09-28.**
- **The quality lock:** `write_history` refuses any pull before 2026-03-13 unless the
  manifest history holds a `vendor_quality` entry with `pass: true` over exactly
  2026-03-13 → 2026-09-25. Such an entry carries no `holdout_sessions` key, so it can never
  count towards an unseal.

## Phase 2 result (2026-09-28): FAIL on Q4

Re-pull `spx_0dte_thetadata` @ `a2b83101`: 128 sessions, 8 skipped for a missing real SPX or
10:00 VIX, all because our recorder missed them (2026-03-13, 03-16, 03-18, 04-27, 05-04,
05-18, 06-01, 06-02). Quality run `47d6ff416e7a`:

| Gate | ThetaData | Helios (report only) | Result |
|---|---|---|---|
| Q1 coverage | min 99.998% per session | min 95.5% | PASS |
| Q2 crossed | 0.0000% | 0.0000% | PASS |
| Q3 arbitrage | 0.0001% of 23.2M checks | 0.0002% of 23.9M | PASS |
| Q4 stale | 0.80% of 8,364 contract-sessions | 0.63% of 8,605 | **FAIL** |
| Q5 timestamps | n/a (no exact-minute SPX in this window) | — | n/a |
| Q6 closes | 128 compared, 0 mismatches | — | PASS |

The lock on earlier pulls stays closed.

**What Q4 caught.** Every one of the 67 flagged contract-sessions is an out-of-the-money
option 26–50 points from SPX, quoted at or next to the minimum price (bid $0.00–0.10, ask
$0.05–0.15), 53 of them in the last hour. Helios flags 54 cases of exactly the same kind,
50 of them the same contract on the same day. No near-the-money or in-the-money contract is
flagged in either source. A quote pinned at the minimum tick legitimately stays put while
SPX moves 10 points, so Q4 as written measures that, not stale data. The definition was
at fault, not the data.

**Matched instants (report only):** 48.8% of 528,874 pairs agree within $0.05, and no
disagreement has either side breaking a Q2/Q3 rule. By moneyness:

| Zone (points from SPX) | Agree within $0.05 | Median price | Median mid difference |
|---|---|---|---|
| OTM 150–200 | 99.9% | 0.08 | 0.00 |
| OTM 50–150 | 96.5% | 0.12 | 0.00 |
| OTM 10–50 | 65.3% | 1.52 | 0.025 |
| ATM ±10 | 17.4% | 9.75 | 0.15 |
| ITM 10–50 | 7.7% | 32.80 | 0.25 |
| ITM > 50 | 11.0% | 124.40 | 0.25 |

The differences grow with the option's price and sensitivity to SPX, which is what a few
seconds of timing difference between the two sources produces. Helios' in-the-money
spreads are wider ($1.10 vs $1.00 median beyond 50 points).

**Amendment 2 (approved by the owner on 2026-09-28, after seeing this result):** Q4 counts
only contracts quoted with an ask of at least $0.50 at the start of the unchanged run, so
that a 10-point SPX move must move the quote by at least one tick. Thresholds unchanged.
Under this definition none of today's flags remain (the largest flagged ask was $0.15), so
this amendment is plainly post hoc. Its justification is the evidence above, which holds
for both sources.

## Phase 2 re-run and Phase 3 result (2026-09-28)

**Validation window, after amendment 2:** quality run `3fdb10e54a38` PASSED: Q1, Q2, Q3,
Q4 and Q6 passed, and Q5 was n/a. It is recorded in the manifest and opened the
development pull.

**Development pull:** `spx_0dte_thetadata` @ `8f3617ae`, 715 sessions in total. That is
587 development sessions (2022-01-03 → 2024-06-28), with 7 skipped on the owner's
files' frozen days (SPX: 2022-02-25, 03-04, 05-06, 2024-05-30; VIX: 2022-10-25, 10-28,
2024-01-31). Coverage report: every session has a real SPX level, a 10:00 VIX, and an
official open and close.

**Development quality run `7139b93acd39`:**

| Gate | Result |
|---|---|
| Q1 coverage | **FAIL on 2 of 587 sessions**; median 100% |
| Q2 crossed | 0.0000%: PASS |
| Q3 arbitrage | 0.0008% of 102M checks: PASS |
| Q4 stale (amendment 2) | 0.006% of 33,113: PASS |
| Q5 timestamps | lag 0 on 587 of 587, including every DST-change-week session: PASS |
| Q6 closes | 587 of 587 equal Cboe: PASS |

What the two Q1 failures are:
- **2022-02-22:** ThetaData reports no quote (0/0) on 87 strikes, including those near SPX,
  from 09:31 to 11:35. This is a gap in the vendor's data. The day's minimum coverage is
  67.9%.
- **2022-06-02:** 11 odd strikes (4055, 4065, …) have no quote until 14:56, most likely because
  they were listed during the day.

**Minute-file cross-check (report only):**
- **SPX:** the file's daily high and low match Yahoo `^GSPC` (median |Δ| 0.0001), with
  one day of 621 over 0.5% (2022-06-13, 0.55%).
- **VIX:** closes match Cboe (checked earlier, median |Δ| 0.01), but the file's daily
  range is always inside Cboe's. On 194 of 625 days its high is more than 0.5% below Cboe's,
  and on 90 its low is more than 0.5% above, with a median miss of about 1.6%. Neither
  Cboe's 16:00–16:15 tail nor the opening print explains it (the open accounts for only 17
  and 11 of those days). The file probably was not built from every VIX print, so short-lived
  extremes are smoothed. The strategy reads VIX as a level at about 10:00, not an extreme.
  How far a smoothed level can be off at that moment cannot be measured without an
  independent intraday VIX source.

**Owner's decisions (2026-09-29):**
- **The two Q1 sessions are excluded** (`exclude-sessions`, evidence `7139b93acd39`). Their
  files moved to `excluded/`, nothing was deleted, and later pulls skip them. The dataset
  is now `spx_0dte_thetadata` @ `93bbe58e`: 713 sessions, 585 of them development.
- **Indices on hold.** The VIX file stays in use, with its smoothed intraday range recorded
  above as a known limitation. D3 (the Dec 2025 → Mar 2026 gap) and a real intraday VIX
  cross-check remain open until an Indices month is bought.

## Decisions for the owner

- **D1: approve this plan and amendment** (the gates in Phase 2 replace validation steps 1–3
  as the condition for the development pull).
- **D2: where did `spx_1min.csv` and `vix_1min.csv` come from?** The vendor and licence go in
  the manifest. If a fresher copy can be downloaded from the same place, it also fills D3.
- **D3: the index gap, 2025-12-10 → 2026-03-12** (about 62 holdout sessions with no SPX or
  VIX minutes). Without derived data, the choices are:
  - (a) refresh the minute files from their source (see D2);
  - (b) ThetaData Indices Standard ($50) for one month at holdout time: real 1-minute SPX and
    VIX, which could also cross-check the owner's files over 2022-09 → 2025-12;
  - (c) leave those sessions out: the holdout shrinks from about 425 to about 363 sessions.
  Needed before registration, not before Phase 1–3.
- **Still open**: ThetaData's written answer on keeping a local cache after cancelling (Terms
  §2.1(i), §12.2).

## Artifacts referenced

Datasets (research cache): `spx_0dte_thetadata` @ `542cdba0` (made with parity SPX; replaced
in Phase 2), `spx_0dte_recorded` @ `48993551`, diagnostics `spx_0dte_diag_rec_parity` and
`spx_0dte_diag_theta_index` (to delete once this is approved). Reports under
`reports/research/<dataset>/validation/`: `76abde9f881a`, `42ad112d11f4`, `cc8c4fc374df`,
`e64e602f7dfd`, `cdb4f1b9f989`, `8c6a9f46fe43`.
