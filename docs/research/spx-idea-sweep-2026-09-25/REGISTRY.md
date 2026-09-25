# SPX idea sweep — registry (written 2026-09-25 before any variant was run)

Sample: every SPX session 2026-03-13 → 2026-09-24 with a recorded 0-DTE chain and an official
close in daily_bars. Halves: H1 = sessions through 2026-06-18, H2 = 2026-06-19 onward.
All history is already-seen development data (the baseline was built on it); nothing here is a
holdout in the pre-registration sense. H2 is used as a pseudo-holdout only for rules whose one
free parameter is fitted on H1 (K1) or on prior sessions only (G1/G2).

Primary metric: stressed-marketable net P&L and expectancy (ask/bid crossing + $0.05/contract
adverse + $0.65/contract commission; cash settlement free). Required for "interesting":
stressed net > baseline in BOTH halves, and the paired day-block bootstrap 90% CI of the
per-session difference vs baseline excludes zero or is at least mostly positive. Everything is
reported, including failures. ~20 variants => expect ~1 false "pass" at 90% by chance.

Harness parity: baseline replica 2026-03-13→09-18 = 118 trades (22 settled / 96 trail),
mid $17,634.6 vs published $17,691.60; stress $9,830.6 vs $9,890.60.

## Variants
E0  baseline (gap direction, VIX anchor, 10:00-10:45 ET, peak trailer 60/90/75)
Exit ablations on E0 entries:
X1  hold to settlement (no intraday exit)
X2  take profit at mark >= 3x entry, else settle
X3  take profit at mark >= 2x entry, else settle
X4  stop at mark <= 50% of entry, else settle
X5  trailer, but flat at 15:00 ET (no settlement exposure)
Center anchor:
C1  ATM-straddle-implied remaining move (1.25 x straddle) replaces VIX move; trailer
C2  C1 selection, hold to settlement
Direction:
D1  momentum: CALL if 10:00 spot >= 09:30 open else PUT (VIX anchor, trailer)
D2  gap fade: opposite of baseline direction (trailer)
D3  both sides: baseline-style call fly AND put fly each day (trailer), per-day sum
D4  ATM call fly at nearest-to-spot center, width = middle width of VIX bucket, hold to settle
Entry time (straddle anchor, since a full-day VIX move is wrong late in the session):
T1  11:30 ET trailer     T2  11:30 ET settle
T3  13:00 ET trailer     T4  13:00 ET settle
T5  14:30 ET trailer     T6  14:30 ET settle
Cost gate:
K1  E0 but skip if (entry ask - mark)/mark > threshold; threshold = median of H1 E0 trades
Expected-value selection (leakage-safe, prior sessions only, >= 20 sessions of history):
G1  10:00 ET: z = (settle - S_t)/straddle_t from prior sessions at the same clock time,
    Gaussian kernel bw 0.3; score every fly (C and P, widths 10/15/20/25/30/40/50, centers
    within 100, mark cost >= 0.30) as E[payoff] - stressed ask; trade the max if > 0; settle.
G2  same at 13:00 ET.
Diagnostic only (not a candidate): FOMC-day split of E0 (2026-03-18, 04-29, 06-17, 07-29, 09-16).

## Round 2 — POST-HOC (written after seeing round-1 results; exploratory only)
Motivation: E0 loses when VIX < 17 and in H2; VIX-move / chain-sigma ratio rose in H2.
R1  E0, skip session if VIX at entry < 17.0 (config's existing bucket boundary)
R2  E0, skip if VIX-move / (1.25 x ATM straddle) > H1 median of that ratio on E0 trades
R3  E0 candidate set (gap direction, bucket widths, RR>=8, cost caps) ranked by prior-session
    EV (same z model as G1) instead of VIX anchor + RR; trailer exit
R4  R3 held to settlement
R5  E0 calls only (CALL-gap days only)
Also report return on stressed debit (net / sum of stressed entry debits) for every variant.
