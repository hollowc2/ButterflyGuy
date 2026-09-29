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
  DST-change weeks. **This is a correction to the approved plan; the owner is asked to
  confirm it.**
- **The quality lock:** `write_history` refuses any pull before 2026-03-13 unless the
  manifest history holds a `vendor_quality` entry with `pass: true` over exactly
  2026-03-13 → 2026-09-25. Such an entry carries no `holdout_sessions` key, so it can never
  count towards an unseal.

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
