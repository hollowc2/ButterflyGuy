# H-TR1 registration — trail armed at +75% with a breakeven floor

Registered 2026-10-01, before any run on the test data. Branch `research/ernie-comparison`.
The run happens once, with `htr1_run.py` at the commit that adds this file. Parameters,
data window and pass criteria must not change after that run.

## Hypothesis

With every other frozen rule unchanged, the **T5 exit** improves stressed-marketable net
P&L relative to the **baseline exit (B)**, on the same entries, over unseen sessions.

- **B (baseline):** the trail arms at any profit (peak mark > entry). It exits when the mark
  is 60% / 90% / 75% below its peak value in the first 120 min / next 120 min / rest of the
  session (minutes after 09:30 ET). Otherwise the fly is held to settlement.
- **T5:** the trail arms only once the peak mark reaches 1.75 × entry, with the same drawdown
  schedule. Once the peak has reached 1.75 × entry, it also exits when the mark falls to
  the entry price or below. Otherwise the fly is held to settlement.

Origin: Coach Ernie (@0DTE) starts profit management at about +75% unrealized. The
breakeven floor was added after seeing the 2026-03-13 → 2026-09-18 Schwab results
(journal, 2026-10-01). Those sessions informed the rule and are not part of this test.

## Entries (frozen, unchanged from the 09-25 harness replica)

Gap direction (open vs prior close). First qualifying chain snapshot 10:00–10:45 ET. Width
buckets and sigma anchors as in `sim.py` (`VIX_BUCKETS` = the current live config, not Ernie's
proposed widths). Center within ±15 pts of the VIX-sigma target; RR ≥ 8; cost caps; risk/reward
closest to 10. One fly per session.

## Data

- **Options:** local ThetaData SPXW 0DTE minute NBBO (`data/thetadata/spxw_0dte/quote_1m`),
  through `thetadata_prep.py`. Mark is the mid; bid 0 with ask 0 counts as no quote.
- **Index and VIX:** owner minute CSVs (America/Chicago bar end, converted to ET; the
  16:01–16:15 ET filler is dropped).
- **Settlement and prior close:** FRED SP500 official closes.
- **Window:** every SPXW 0DTE session with a file from **2022-05-02 to 2024-06-28**,
  excluding the owner's development exclusion 2022-06-02 and any session the adapter skips
  for missing index minutes. The sealed holdout (2024-07-01 → 2026-03-12) is not read; the
  adapter refuses that range.
- **Accounting:** the 09-25 models (midpoint; marketable; stressed = marketable with $0.05
  worse per contract fill; $0.65 per contract; free cash settlement).

Adapter check on the overlap (2026-03-13 → 2026-09-18), against the Schwab harness on the
same sessions: direction matched on 100% of sessions, entry minute on 92%, exact fly on 42%
(near-tied flies). Stressed T5 − B was +$6,150 (Schwab) and +$6,795 (ThetaData). Absolute
levels differ, so the test compares exits on the same entries rather than against Schwab
figures.

## Pass criteria (all must hold; stressed accounting; per one-lot)

1. T5 − B > 0 over the full window.
2. T5 − B > 0 in each chronological half (split at the median session date).
3. T5 − B > 0 after removing the 3 sessions with the largest positive T5 − B differences.
4. T5's maximum drawdown ≤ B's maximum drawdown.

Before registering, a runner smoke test on the already-used 2026 overlap gave:
- **Criterion 3 with ThetaData quotes:** −$2,004, a FAIL.
- **Criterion 3 with Schwab quotes:** +$2,413.
- **Criteria 1, 2 and 4:** passed on both sources.

The owner chose to keep criterion 3 unchanged as the robustness bar, knowing it may fail.
The 2022–24 window had not been read when this was decided.

## Reported but not gating

Midpoint and marketable results; T6 (any-profit start plus the breakeven floor after
+75%); results by VIX bucket and by year; floor-exit count and average; per-session CSV.

## Run

```bash
cd docs/research/spx-idea-sweep-2026-09-25
python thetadata_prep.py 2022-05-02 2024-06-28 data_theta/htr1   # fred_sp500.csv copied in first
SWEEP_DATA=data_theta/htr1 python htr1_run.py 2022-05-02 2024-06-28
```

Needs pandas and pyarrow. The data directory is ThetaData-derived, gitignored, and must
never be committed.
