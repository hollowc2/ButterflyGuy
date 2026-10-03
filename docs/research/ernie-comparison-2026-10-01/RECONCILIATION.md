# Ernie comparison reconciliation — 2026-10-02

**H-TR1 is rejected.** The exploratory improvement on the 2026 Schwab sample did
not generalize to the registered 2022–24 test. The branch contributes historical
research evidence and archived scripts; it supplies no approved strategy change.

## Completed decision

The original plan began as design notes but subsequently accumulated runs. Its
opening “not run” status is stale. Registration commit `b0b7215` preceded the
recorded one-shot run; result commit `06a75d3` records failure of every criterion.
The original registration/result file and plan are retained byte-for-byte.

H-TR1 tested T5: arm the existing peak-value trailer at 1.75 times entry and add a
breakeven floor once that peak is reached. On 537 data sessions from 2022-05-02
through 2024-06-28, 334 sessions traded:

- Baseline stressed net: −$9,541; T5: −$10,749; difference: −$1,208.
- First-half difference: −$647; second-half difference: −$560.
- Difference after removing the three largest positive session differences: −$6,030.
- T5 drawdown was $2,827 deeper than baseline.

Displayed results are rounded; the rounded halves need not sum to the rounded total.
T6 and the cost breakdown were reported diagnostics, not successful registered tests.
The T5 gain of about $6,150 on the earlier 118-trade Schwab sample was exploratory:
those observations helped design the rule.

Placement, trend-indicator direction, and mechanical GEX/round-number trigger
comparisons did not establish a replacement that beat their baseline in both halves.
They do not evaluate Ernie's discretionary trading performance. Width changes and
Time Warp remain proposals in the historical plan, not approved implementations.

## Distinct datasets and source versions

The historical H-TR1 adapter used ThetaData SPXW minute quotes, owner SPX/VIX CSVs
with Chicago bar-end timestamps, and FRED SP500 closes. Its window began
2022-05-02; it excluded 2022-06-02 and skipped missing index evidence. The owner
CSV's original provider is unknown. It produced the recorded 537 data / 334 traded
sessions using the archived 09-25 harness replica.

The later [canonical development completion](../thetadata-backtesting-completion-2026-10-01.md)
uses the broader 2022-01-03 through 2024-06-28 window, explicit eligibility and
quality ledgers, attributed Cboe closes, and normalized dataset
`98434ab47077456d812a17be785e98d2cfc2c94819c986b0c83df6518a4f6b63`.
Its frozen E0 run `f6717f4b6704` has 585 eligible sessions, 362 traded, and 223
no-trade sessions. These counts and accounting outputs do not replace the H-TR1
record or constitute a rerun of its registered experiment.

The old 2026 Schwab comparison records 118 trades with 22 settlements. The
[v2 baseline provenance](../spx-v2-baseline-20260313-20260918.provenance.json)
records 118 trades with 23 settlements, from later database evidence and corrected
harness source. Code-versus-data attribution of that discrepancy has not been
established. Equal trade counts do not demonstrate equal inputs or exit paths.

One arithmetic correction to the historical narrative: the D3 direction table has
97 calls and 14 puts, which is 87.4% calls, rather than the prose's 97%. The original
record is retained; this correction changes no P&L or decision.

## Provenance and access limits

[provenance.json](provenance.json) records original tip `15a8bce`, registration/result
commits, SHA-256 hashes of the original files, the appended journal delta, and
shared harness modules confirmed unchanged on current main. The eight added scripts
and registration are preserved unchanged, including their original path conventions.
Historical reproduction commands may require the old checkout layout.

The historical record does not include a complete content-addressed normalized
dataset manifest or an independently verified input fingerprint. File hashes pin
code and narrative, not the raw vendor observations or the exact reported run.
Reconciliation verifies preserved evidence and syntax; it does not claim fresh
numerical reproduction. Missing provenance must not be filled with invented hashes.

The original claim that 2024-07-01 through 2026-03-12 remained unseen is superseded:
[H-TS1 already evaluated that interval](../thetadata-backtesting-readiness-2026-10-01.md).
Its prior failure remains recorded, and import/replay access guards remain in place.
No protected market payload was opened or evaluated for this reconciliation.

New work belongs in the canonical research core with a fresh definition and
registration on an eligible research window. Neither T5/T6, the width proposal,
nor the diagnostic H-LV2/H-SP1 candidates are promoted here. The retired v1 and
active frozen v2 prospective checkouts remain separate; observations are not pooled.
